"""Isolated G/GQ replay clocks. No estimator, allocation, or Environment writes."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
import math

import numpy as np

from pursuit_v2 import observation_geometry as geometry
from pursuit_v2.service import (TOL, advance_clock, canonical_team, initial_state,
                                restore_state, tick as service_tick)
from .common import CONTRACT_ID, DT, ContractError, digest


SNAPSHOT_VERSION = 'information_service_shadow_v1'
QUALITY_STATES = ('PASS', 'FAIL', 'UNKNOWN')


def _finite(value, label, *, minimum=None, positive=False):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.number)):
        raise ContractError(label + ' must be numeric')
    result = float(value)
    if not math.isfinite(result) or (minimum is not None and result < minimum) or (positive and result <= 0):
        raise ContractError('Invalid ' + label)
    return result


def _tick(value):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < 0:
        raise ContractError('tick must be a nonnegative integer')
    return int(value)


def _team(cfg, team):
    try:
        normalized = canonical_team(team)
    except (TypeError, ValueError) as error:
        raise ContractError(str(error)) from error
    if any(i >= cfg.robots for i, _ in normalized):
        raise ContractError('Robot identity outside configured resources')
    return normalized


def _require_config(cfg):
    if (cfg.capture_mode != 'stepwise_service' or cfg.geometry_mode != 'angular_standoff_v1'
            or cfg.step_dt != DT or cfg.risk_prediction_dt != DT):
        raise ContractError('Shadow service requires angular service and the original .05 grid')


def physical_valid(cfg, q, team, target_position, positions):
    """Original full-team angular position test; positions contains all X robots.

    This function has no ledger state, so an earlier G-ledger completion cannot
    disable the common physical input to the separate GQ ledger. External birth
    and escape are lifecycle inputs handled by the caller/ledger.
    """
    _require_config(cfg)
    if isinstance(q, bool) or not isinstance(q, (int, np.integer)) or q not in (1, 2, 3):
        raise ContractError('Invalid physical task demand')
    normalized = _team(cfg, team)
    try:
        complete = geometry.validate_roles(int(q), [r for _, r in normalized], cfg)
    except ValueError as error:
        raise ContractError(str(error)) from error
    try:
        pos = np.asarray(positions, dtype=float)
        target = np.asarray(target_position, dtype=float)
    except (TypeError, ValueError) as error:
        raise ContractError('Invalid physical coordinates') from error
    if pos.shape != (cfg.robots, 2) or target.shape != (2,) or not np.isfinite(pos).all() or not np.isfinite(target).all():
        raise ContractError('Physical input requires finite positions[X,2] and target[2]')
    if not complete:
        return False
    offsets = np.array([geometry.offset(r, cfg) for _, r in normalized])
    selected = pos[[i for i, _ in normalized]]
    return bool(np.all(np.linalg.norm(selected - target - offsets, axis=1) <= geometry.radius(cfg)))


class ShadowLedger:
    """One virtual ledger; fixed trajectory inputs never change on completion.

    Powers are per-robot squared control magnitudes held on the immediately
    preceding interval. Prefix accounting begins at start_tick, not at birth
    when a synthetic continuation starts later. initial_progress is an explicit
    history fixture; its pre-start control cost is intentionally not invented.
    """

    def __init__(self, cfg, team, duration, stream_id='shadow_stream', end_time=3.,
                 birth=0., deadline=2., mode='GQ', start_tick=0,
                 initial_progress=0., escape_time=None):
        _require_config(cfg)
        self.cfg = cfg
        self.config_payload = cfg.to_dict()
        self.config_identity = digest(self.config_payload)
        self.geometry_identity = deepcopy(geometry.identity(cfg))
        self.fixed_team = _team(cfg, team)
        if len(self.fixed_team) not in (2, 3):
            raise ContractError('Minimal information-service ledger requires fixed q=2/3')
        try:
            complete = geometry.validate_roles(len(self.fixed_team), [r for _, r in self.fixed_team], cfg)
        except ValueError as error:
            raise ContractError(str(error)) from error
        if not complete:
            raise ContractError('A complete fixed role team is required')
        if mode not in ('G', 'GQ'):
            raise ContractError('Unknown shadow mode')
        if not isinstance(stream_id, str) or not stream_id:
            raise ContractError('An input stream identity is required')
        self.mode, self.stream_id = mode, stream_id
        self.duration = _finite(duration, 'duration', positive=True)
        self.birth = _finite(birth, 'birth', minimum=0.)
        self.deadline = _finite(deadline, 'deadline', minimum=self.birth)
        self.end_time = _finite(end_time, 'end_time', positive=True)
        self.start_tick = _tick(start_tick)
        self.accounting_start_time = self.start_tick * DT
        try:
            self.end_tick = service_tick(self.end_time)
            service_tick(self.birth)
        except ValueError as error:
            raise ContractError(str(error)) from error
        self.end_time = self.end_tick * DT
        if (self.end_time > cfg.end_time + TOL or self.accounting_start_time < self.birth - TOL
                or self.start_tick > self.end_tick):
            raise ContractError('Invalid shadow replay interval')
        self.initial_progress = _finite(initial_progress, 'initial_progress', minimum=0.)
        if (self.initial_progress >= self.duration
                or self.initial_progress > self.accounting_start_time - self.birth + TOL):
            raise ContractError('Invalid active history progress')
        self.escape_time = None if escape_time is None else _finite(escape_time, 'escape_time', minimum=self.birth)
        self.inner_service_state = replace(initial_state(cfg), base=self.initial_progress,
                                           intervals=0, team=self.fixed_team)
        self.status = 'ACTIVE'
        self.last_tick = None
        self.last_G = None
        self.last_Q_status = None
        self.last_valid = None
        self.completion_time = None
        self.completion_tick = None
        self.completion_window_ticks = []
        self.completion_window_initial_progress = 0.
        self.window_ticks = []
        self.window_initial_progress = self.initial_progress
        self.effort_by_robot = [0.] * cfg.robots
        self.occupied_seconds_by_robot = [0.] * cfg.robots
        self.occupied_robot_seconds = 0.
        self.total_valid_time = 0.
        self.events = []
        self.releases = []
        self._input_hashes = {}
        self._frames = {}

    @property
    def progress(self):
        return self.inner_service_state.progress

    @property
    def occupied_robot_ids(self):
        return [i for i, _ in self.fixed_team] if self.status == 'ACTIVE' else []

    @property
    def control_effort(self):
        return math.fsum(self.effort_by_robot)

    def _check_identity(self):
        if digest(self.cfg.to_dict()) != self.config_identity or geometry.identity(self.cfg) != self.geometry_identity:
            raise ContractError('Configuration/geometry changed during replay')

    def _invalid_reasons(self, left_g, left_q, right_g, right_q):
        result = []
        if not (left_g and right_g):
            result.append('physical_invalid')
        if self.mode == 'GQ':
            if 'FAIL' in (left_q, right_q):
                result.append('quality_threshold')
            if 'UNKNOWN' in (left_q, right_q):
                result.append('quality_unavailable')
        return result

    def _finish(self, status, at, tick_index, new_events, new_releases):
        self.status = status
        reason = {'COMPLETED': 'completed', 'ESCAPED': 'escaped', 'UNFINISHED': 'window_end'}[status]
        event = dict(type={'COMPLETED': 'completion', 'ESCAPED': 'escape', 'UNFINISHED': 'termination'}[status],
                     reason=reason, time=at, tick=tick_index, progress=self.progress)
        new_events.append(event)
        release = dict(time=at, reason=reason, robots=[i for i, _ in self.fixed_team], virtual=True)
        new_releases.append(release)
        if status == 'COMPLETED':
            self.completion_time = at
            self.completion_tick = tick_index
            self.completion_window_ticks = list(self.window_ticks)
            self.completion_window_initial_progress = self.window_initial_progress

    def consume(self, tick, G, Q_status, powers):
        self._check_identity()
        tick = _tick(tick)
        if not isinstance(G, (bool, np.bool_)) or Q_status not in QUALITY_STATES:
            raise ContractError('G must be boolean and Q_status must be PASS/FAIL/UNKNOWN')
        G = bool(G)
        try:
            powers = [_finite(v, 'control power', minimum=0.) for v in powers]
        except TypeError as error:
            raise ContractError('Control powers must be an X-element sequence') from error
        if len(powers) != self.cfg.robots or any(v > self.cfg.max_speed ** 2 + 1e-7 for v in powers):
            raise ContractError('Invalid control-power length or speed bound')
        payload = dict(tick=tick, G=G, Q_status=Q_status, powers=powers)
        input_hash = digest(payload)
        key = str(tick)
        if key in self._input_hashes:
            if self._input_hashes[key] != input_hash:
                raise ContractError('Conflicting replay of a previously consumed endpoint')
            return deepcopy(self._frames[key])
        expected = self.start_tick if self.last_tick is None else self.last_tick + 1
        if tick != expected or tick > self.end_tick:
            raise ContractError('Missing, out-of-order, or out-of-window endpoint')
        at = tick * DT
        effective = G and (self.mode == 'G' or Q_status == 'PASS')
        new_events, new_releases = [], []
        interval_valid = False
        elapsed = 0.
        if self.status == 'ACTIVE':
            if self.last_tick is None:
                if self.escape_time is not None and self.escape_time <= at + TOL:
                    self._finish('ESCAPED', self.escape_time, self._event_tick(self.escape_time), new_events, new_releases)
                else:
                    if not effective and self.progress > 0:
                        new_events.append(dict(type='interruption', reason='observation_invalid', raw_reason='observation_invalid',
                                               time=at, tick=tick, progress_before=self.progress,
                                               diagnostic_reasons=self._invalid_reasons(G, Q_status, G, Q_status)))
                        self.inner_service_state = replace(self.inner_service_state, base=0., intervals=0)
                        self.window_initial_progress = 0.
                    self.window_ticks = [tick] if effective else []
                    if tick == self.end_tick:
                        self._finish('UNFINISHED', at, tick, new_events, new_releases)
            else:
                lo = self.last_tick * DT
                stop = min(at, self.escape_time) if self.escape_time is not None else at
                elapsed = max(0., stop - lo)
                for robot, _ in self.fixed_team:
                    self.effort_by_robot[robot] = math.fsum((self.effort_by_robot[robot], powers[robot] * elapsed))
                    self.occupied_seconds_by_robot[robot] = math.fsum((self.occupied_seconds_by_robot[robot], elapsed))
                self.occupied_robot_seconds = math.fsum(self.occupied_seconds_by_robot)
                if self.escape_time is not None and self.escape_time <= at + TOL:
                    self._finish('ESCAPED', self.escape_time, self._event_tick(self.escape_time), new_events, new_releases)
                else:
                    interval_valid = bool(self.last_valid and effective)
                    prior = self.progress
                    self.inner_service_state, done, clock_events = advance_clock(
                        self.inner_service_state, self.duration, self.fixed_team, interval_valid, at)
                    for event in clock_events:
                        new_events.append(dict(event, type='interruption', raw_reason=event['reason'],
                                               tick=self._event_tick(event['time']),
                                               diagnostic_reasons=self._invalid_reasons(self.last_G, self.last_Q_status, G, Q_status)))
                    if interval_valid:
                        self.total_valid_time = math.fsum((self.total_valid_time, DT))
                        if prior == 0:
                            self.window_ticks = [self.last_tick, tick]
                            self.window_initial_progress = 0.
                        else:
                            if not self.window_ticks:
                                self.window_ticks = [self.last_tick]
                            self.window_ticks.append(tick)
                    else:
                        self.window_ticks = [tick] if effective else []
                        self.window_initial_progress = 0.
                    if done:
                        self._finish('COMPLETED', at, tick, new_events, new_releases)
                    elif tick == self.end_tick:
                        self._finish('UNFINISHED', at, tick, new_events, new_releases)
        self.events.extend(new_events)
        self.releases.extend(new_releases)
        self.last_tick, self.last_G, self.last_Q_status, self.last_valid = tick, G, Q_status, effective
        occupied = self.occupied_robot_ids
        frame = dict(contract_id=CONTRACT_ID, mode=self.mode, stream_id=self.stream_id,
                     tick=tick, time=at, G=G, Q_status=Q_status, endpoint_valid=effective,
                     interval_valid=interval_valid, charged_interval_duration=elapsed,
                     progress=self.progress, status=self.status,
                     completion_time=self.completion_time, completion_tick=self.completion_tick,
                     completion_window_ticks=list(self.completion_window_ticks),
                     completion_window_initial_progress=self.completion_window_initial_progress,
                     on_time=(self.completion_time <= self.deadline + TOL) if self.completion_time is not None else None,
                     fixed_team=[list(p) for p in self.fixed_team], occupied_robot_ids=occupied,
                     idle_robot_ids=[i for i in range(self.cfg.robots) if i not in occupied],
                     effort_by_robot=list(self.effort_by_robot), prefix_effort_by_robot=list(self.effort_by_robot),
                     control_effort=self.control_effort, occupied_robot_seconds=self.occupied_robot_seconds,
                     total_valid_time=self.total_valid_time, events=deepcopy(new_events),
                     release_events=deepcopy(new_releases), input_sha256=input_hash,
                     accounting_start_time=self.accounting_start_time)
        self._input_hashes[key] = input_hash
        self._frames[key] = deepcopy(frame)
        return frame

    @staticmethod
    def _event_tick(at):
        try:
            return service_tick(at)
        except ValueError:
            return None

    def snapshot(self):
        self._check_identity()
        body = dict(version=SNAPSHOT_VERSION, contract_id=CONTRACT_ID,
                    config=deepcopy(self.config_payload), config_identity=self.config_identity,
                    geometry_identity=deepcopy(self.geometry_identity),
                    fixed_team=[list(p) for p in self.fixed_team], duration=self.duration,
                    stream_id=self.stream_id, end_time=self.end_time, birth=self.birth,
                    deadline=self.deadline, mode=self.mode, start_tick=self.start_tick,
                    initial_progress=self.initial_progress, escape_time=self.escape_time,
                    status=self.status, last_tick=self.last_tick, last_G=self.last_G,
                    last_Q_status=self.last_Q_status, last_valid=self.last_valid,
                    inner_service_state=asdict(self.inner_service_state),
                    completion_time=self.completion_time, completion_tick=self.completion_tick,
                    completion_window_ticks=list(self.completion_window_ticks),
                    completion_window_initial_progress=self.completion_window_initial_progress,
                    window_ticks=list(self.window_ticks), window_initial_progress=self.window_initial_progress,
                    effort_by_robot=list(self.effort_by_robot),
                    occupied_seconds_by_robot=list(self.occupied_seconds_by_robot),
                    occupied_robot_seconds=self.occupied_robot_seconds, total_valid_time=self.total_valid_time,
                    events=deepcopy(self.events), releases=deepcopy(self.releases),
                    input_hashes=deepcopy(self._input_hashes), frames=deepcopy(self._frames))
        # Convert tuple-valued geometry/state fields to their on-disk JSON form.
        import json
        body = json.loads(json.dumps(body, allow_nan=False))
        return dict(body, snapshot_sha256=digest(body))

    @classmethod
    def from_snapshot(cls, cfg, snapshot):
        data = deepcopy(snapshot)
        expected_hash = data.pop('snapshot_sha256', None)
        if expected_hash != digest(data):
            raise ContractError('Snapshot identity mismatch')
        if data.get('version') != SNAPSHOT_VERSION or data.get('contract_id') != CONTRACT_ID:
            raise ContractError('Snapshot contract mismatch')
        if data.get('config_identity') != digest(cfg.to_dict()) or data.get('config') != cfg.to_dict():
            raise ContractError('Snapshot configuration mismatch')
        if digest(data.get('geometry_identity')) != digest(geometry.identity(cfg)):
            raise ContractError('Snapshot geometry mismatch')
        ledger = cls(cfg, data['fixed_team'], data['duration'], stream_id=data['stream_id'],
                     end_time=data['end_time'], birth=data['birth'], deadline=data['deadline'],
                     mode=data['mode'], start_tick=data['start_tick'],
                     initial_progress=data['initial_progress'], escape_time=data['escape_time'])
        try:
            inner = restore_state(cfg, data['inner_service_state'])
        except (TypeError, ValueError) as error:
            raise ContractError('Invalid inner clock snapshot') from error
        if inner.team != ledger.fixed_team:
            raise ContractError('Snapshot team differs from fixed input team')
        if data['status'] not in ('ACTIVE', 'COMPLETED', 'ESCAPED', 'UNFINISHED'):
            raise ContractError('Unknown snapshot status')
        if (inner.progress > ledger.duration or
                (data['status'] == 'COMPLETED') != (inner.progress == ledger.duration)):
            raise ContractError('Snapshot progress/terminal mismatch')
        last = data['last_tick']
        expected_keys = [] if last is None else [str(n) for n in range(ledger.start_tick, _tick(last) + 1)]
        if last is not None and last > ledger.end_tick:
            raise ContractError('Snapshot exceeds replay window')
        if set(data['input_hashes']) != set(expected_keys) or set(data['frames']) != set(expected_keys):
            raise ContractError('Snapshot endpoint history is incomplete')
        if any(data['frames'][k]['input_sha256'] != data['input_hashes'][k] for k in expected_keys):
            raise ContractError('Snapshot frame/input identity mismatch')
        for field in ('effort_by_robot', 'occupied_seconds_by_robot'):
            if len(data[field]) != cfg.robots:
                raise ContractError('Snapshot resource vector length mismatch')
            for v in data[field]:
                _finite(v, field, minimum=0.)
        if abs(math.fsum(data['occupied_seconds_by_robot']) - data['occupied_robot_seconds']) > 1e-12:
            raise ContractError('Snapshot occupancy accounting mismatch')
        if len(data['releases']) != int(data['status'] != 'ACTIVE'):
            raise ContractError('Snapshot terminal release count mismatch')
        ledger.inner_service_state = inner
        for name in ('status', 'last_tick', 'last_G', 'last_Q_status', 'last_valid',
                     'completion_time', 'completion_tick', 'completion_window_ticks',
                     'completion_window_initial_progress', 'window_ticks', 'window_initial_progress',
                     'effort_by_robot', 'occupied_seconds_by_robot', 'occupied_robot_seconds',
                     'total_valid_time', 'events', 'releases'):
            setattr(ledger, name, deepcopy(data[name]))
        ledger._input_hashes, ledger._frames = deepcopy(data['input_hashes']), deepcopy(data['frames'])
        return ledger
