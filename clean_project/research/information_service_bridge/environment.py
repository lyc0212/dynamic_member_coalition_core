"""Explicit GQ execution, with real lifecycle and no autonomous allocator.

The short motion expression follows the frozen service controller's operation
order. This new executor never calls the old G-only rollout to stop its motion.
The sensing callback receives only public frames, not this private environment.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
import json
import math

import numpy as np

from pursuit_v2.config import Config
from pursuit_v2.environment import Environment
from pursuit_v2.types import Assignment, IDLE, Scenario, Target
from pursuit_v2 import observation_geometry as geometry
from pursuit_v2.service import TOL, advance_clock, canonical_team, initial_state, restore_state
from research.information_service.common import CONTRACT_ID as MEASUREMENT_CONTRACT
from research.information_service.public_quality import prepare_frame
from .common import CONTRACT_ID, DT, ContractError, canonical_actions, digest


DRIVER = 'scripted_fixed_team_bridge_v1'
DECISION_TICKS = 20


def _json(value):
    return json.loads(json.dumps(value, allow_nan=False))


def _integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContractError(name + ' must be a nonnegative integer')
    return value


class GQExecutionEnvironment:
    """Construct from a frozen case dict and a public-only sensing callback.

    sense_callback(frame, allowed_sensor_ids, start_tick) returns the old public
    FrameProcessor result shape, with matching tick/target/stream/frame identity,
    payload_sha256, and quality.status. Test callbacks are explicitly injected.
    """

    def __init__(self, case_dict, sense_callback, *, attempt_id='bridge',
                 environment_id=None, driver=DRIVER):
        if driver != DRIVER:
            raise ContractError('Only the explicit scripted fixed-team driver is supported; old M3 is not GQ-certified')
        if not isinstance(case_dict, dict) or not callable(sense_callback):
            raise ContractError('A frozen case dictionary and sensing callback are required')
        self.cfg = Config(**deepcopy(case_dict['config']))
        cfg = self.cfg
        if (cfg.capture_mode != 'stepwise_service' or cfg.geometry_mode != 'angular_standoff_v1'
                or cfg.motion_model != 'continuous_turn' or cfg.stage_dt != 3.
                or cfg.turn_interval != 1. or cfg.step_dt != DT or cfg.risk_prediction_dt != DT):
            raise ContractError('Bridge requires the frozen angular service/one-second/.05 contract')
        self.targets = tuple(Target(**deepcopy(t)) for t in case_dict['targets'])
        positions = np.array(case_dict['positions_initial'], dtype=float, copy=True)
        # Original construction guards are reused without executing a step.
        Environment(cfg, Scenario(positions, self.targets))
        if any(t.required_robots not in (2, 3) for t in self.targets):
            raise ContractError('Bridge v1.1 covers fixed two/three-robot tasks')
        self.attempt_id = str(attempt_id)
        self.environment_id = environment_id or str(case_dict.get('case_id', 'case')) + ':gq'
        if not self.attempt_id or not isinstance(self.environment_id, str) or not self.environment_id:
            raise ContractError('Nonempty attempt and environment identities are required')
        self.case_id = str(case_dict.get('case_id', 'case'))
        self.sense_callback = sense_callback
        self.driver = driver
        teams = case_dict.get('fixed_teams', {})
        self.fixed_teams = []
        for target in self.targets:
            supplied = teams.get(str(target.id), teams.get(target.id))
            if supplied is None:
                supplied = tuple(zip(range(target.required_robots), geometry.required_roles(target.required_robots, cfg)))
            try:
                team = canonical_team(supplied)
                complete = geometry.validate_roles(target.required_robots, [r for _, r in team], cfg)
            except (ValueError, TypeError) as error:
                raise ContractError('Invalid declared fixed team') from error
            if not complete or any(i >= cfg.robots for i, _ in team):
                raise ContractError('Declared team must be complete and within robot resources')
            self.fixed_teams.append(team)
        self.disturbance = deepcopy(case_dict.get('disturbance', dict(
            target_id=0, mode='normal', start_tick=0, end_tick_exclusive=0,
            sigma_base=.02, sigma_degraded=.08, noise_perturbation=0.)))
        d = self.disturbance
        if d['mode'] not in ('normal', 'sigma_x4', 'missing_U1', 'missing_U2'):
            raise ContractError('Unknown frozen disturbance mode')
        for name in ('start_tick', 'end_tick_exclusive', 'target_id'):
            _integer(d[name], name)
        if d['end_tick_exclusive'] < d['start_tick']:
            raise ContractError('Reversed disturbance interval')
        if (any(not math.isfinite(float(d[k])) or float(d[k]) <= 0 for k in ('sigma_base', 'sigma_degraded'))
                or d.get('noise_perturbation', 0.) != 0.):
            raise ContractError('Bridge main cases require positive sigmas and frozen zero perturbation')
        self._source = _json(dict(case_id=self.case_id, config=cfg.to_dict(),
                                 positions_initial=positions.tolist(), targets=[t.to_dict() for t in self.targets],
                                 fixed_teams={str(j): list(team) for j, team in enumerate(self.fixed_teams)},
                                 disturbance=d))
        self.case_identity = digest(self._source)
        self.config_identity = digest(cfg.to_dict())
        self.end_tick = round(cfg.end_time / DT)
        self._escape = [t.escape_time(cfg.side) for t in self.targets]
        self._state = dict(
            tick=0, positions=positions, status=['active' if t.birth <= TOL else 'hidden' for t in self.targets],
            assignment=(IDLE,) * cfg.robots, locks=[None] * cfg.task_count,
            clocks=[initial_state(cfg) for _ in self.targets], last_points=[None] * cfg.task_count,
            streams=[None] * cfg.task_count, windows=[[] for _ in self.targets],
            completion_windows=[[] for _ in self.targets], completion_times=[None] * cfg.task_count,
            escape_times=[None] * cfg.task_count, effort_by_robot=[0.] * cfg.robots,
            occupied_by_robot=[0.] * cfg.robots, total_effort=0., peak_speed=0., flow=0., late=0.,
            components={k: 0. for k in ('completion', 'flow', 'late', 'effort', 'terminal')},
            changes=0, change_cost=0., new_ids=[t.id for t in self.targets if t.birth <= TOL],
            ended_ids=[], measurement_requests=0, reported_estimator_calls=0, terminal_settled=False)
        self.frames, self.events, self.steps = [], [], []
        self._cache = {}
        self._inflight = None
        self._pending_sense = None
        self.failed = False
        self.failure = None

    @property
    def tick(self):
        return self._state['tick']

    @property
    def time(self):
        return self.tick * DT

    @property
    def done(self):
        return self.tick >= self.end_tick

    @property
    def positions(self):
        return self._state['positions'].copy()

    @property
    def status(self):
        return tuple(self._state['status'])

    @property
    def last_assignment(self):
        return self._state['assignment']

    def _check_identity(self):
        if digest(self.cfg.to_dict()) != self.config_identity:
            raise ContractError('Configuration changed after construction')

    def _metrics(self, state):
        cfg = self.cfg
        weights = [t.weight for t in self.targets]
        completed = [s == 'completed' for s in state['status']]
        escaped = [s == 'escaped' for s in state['status']]
        on_time = [at is not None and at <= t.deadline + TOL
                   for t, at in zip(self.targets, state['completion_times'])]
        total = math.fsum(state['components'].values())
        busy = math.fsum(state['occupied_by_robot'])
        return dict(completion_rate=sum(completed) / len(completed),
                    weighted_on_time_rate=sum(w for w, ok in zip(weights, on_time) if ok) / sum(weights),
                    unfinished_weight_fraction=sum(w for w, ok in zip(weights, completed) if not ok) / sum(weights),
                    escaped_weight_fraction=sum(w for w, ok in zip(weights, escaped) if ok) / sum(weights),
                    completed_count=sum(completed), escaped_count=sum(escaped),
                    **{'return': total}, return_without_changes=total,
                    return_with_changes=total-state['change_cost'], reward_components=dict(state['components']),
                    control_effort=state['total_effort'], control_integral=state['total_effort'],
                    effort_by_robot=list(state['effort_by_robot']), peak_speed=state['peak_speed'],
                    assignment_changes=state['changes'], change_cost=state['change_cost'],
                    occupied_robot_seconds=busy, idle_robot_seconds=cfg.robots * state['tick'] * DT - busy,
                    flow=state['flow'], late=state['late'], measurement_requests=state['measurement_requests'],
                    reported_estimator_calls=state['reported_estimator_calls'])

    def metrics(self):
        return _json(self._metrics(self._state))

    def _observe(self, state):
        return _json(dict(
            execution_contract_id=CONTRACT_ID, attempt_id=self.attempt_id, environment_id=self.environment_id,
            case_id=self.case_id, case_identity=self.case_identity, tick=state['tick'], time=state['tick']*DT,
            positions=state['positions'].tolist(), status=list(state['status']),
            last_assignment=[a.to_dict() for a in state['assignment']],
            service_progress=[s.progress for s in state['clocks']],
            completion_times=state['completion_times'], escape_times=state['escape_times'],
            new_ids=state['new_ids'], ended_ids=state['ended_ids'],
            tasks=[dict(target=t.id, status=state['status'][t.id], fixed_team=self.fixed_teams[t.id],
                        locked_team=state['locks'][t.id], service_state=asdict(state['clocks'][t.id]),
                        stream_id=None if state['streams'][t.id] is None else state['streams'][t.id]['stream_id'],
                        stream_start_tick=None if state['streams'][t.id] is None else state['streams'][t.id]['start_tick'],
                        window_ticks=state['windows'][t.id], completion_window_ticks=state['completion_windows'][t.id])
                   for t in self.targets], metrics=self._metrics(state), failed=self.failed))

    def observe_execution(self):
        self._check_identity()
        return self._observe(self._state)

    def _validate_actions(self, raw):
        actions = tuple(Assignment(**a) for a in canonical_actions(raw, self.cfg.robots))
        state = self._state
        by_target = {}
        for robot, action in enumerate(actions):
            if action.target is None:
                continue
            j = action.target
            if j >= len(self.targets) or state['status'][j] != 'active':
                raise ContractError('Cannot assign hidden, completed, escaped or unknown task')
            by_target.setdefault(j, []).append((robot, action.role))
        for j, supplied in by_target.items():
            if tuple(supplied) != self.fixed_teams[j]:
                raise ContractError('Nonempty assignment must equal the complete predeclared team and roles')
        for j, locked in enumerate(state['locks']):
            if locked is not None and state['status'][j] == 'active' and tuple(by_target.get(j, ())) != locked:
                raise ContractError('Active fixed team cannot be withdrawn, replaced, or have roles changed')
        return actions

    def _public_frame(self, state, j, tick):
        stream = state['streams'][j]
        truth = self.targets[j].position(tick * DT)
        d = self.disturbance
        intervened = j == d['target_id'] and d['start_tick'] <= tick < d['end_tick_exclusive']
        sigma = float(d['sigma_degraded'] if intervened and d['mode'] == 'sigma_x4' else d['sigma_base'])
        records = []
        for robot, _ in state['locks'][j]:
            sensor = 'U' + str(robot)
            if intervened and d['mode'] == 'missing_' + sensor:
                continue
            p = state['positions'][robot]
            angle = math.atan2(float(truth[1]-p[1]), float(truth[0]-p[0]))
            angle = (angle + math.pi) % (2*math.pi) - math.pi
            records.append(dict(sensor_id=sensor, position=p.tolist(), bearing=angle, sigma=sigma,
                                packet_id=f"{stream['stream_id']}:tick{tick}:{sensor}",
                                measurement_tick=tick, available_tick=tick, status='ok'))
        return dict(contract_id=MEASUREMENT_CONTRACT, stream_id=stream['stream_id'],
                    frame_id=f"{stream['stream_id']}:tick{tick}", tick=tick, target_id=j,
                    measurement_time=tick*DT, available_time=tick*DT, records=records)

    def _endpoint(self, state, j, tick):
        team = state['locks'][j]
        allowed = ['U' + str(i) for i, _ in team]
        frame = self._public_frame(state, j, tick)
        prepared = prepare_frame(frame, allowed)
        sent = deepcopy(frame)
        sent_hash = digest(sent)
        self._pending_sense = dict(target=j, tick=tick, public_frame=deepcopy(frame),
                                   payload_sha256=prepared['payload_sha256'],
                                   candidate_positions=state['positions'].tolist())
        result = self.sense_callback(sent, allowed, state['streams'][j]['start_tick'])
        if digest(sent) != sent_hash:
            raise ContractError('Sensing callback mutated its public request')
        if not isinstance(result, dict):
            raise ContractError('Sensing callback must return a public result')
        for key in ('frame_id', 'target_id', 'stream_id', 'tick'):
            if result.get(key) != frame[key]:
                raise ContractError('Sensing response identity mismatch: ' + key)
        quality = result.get('quality')
        if (not isinstance(quality, dict) or quality.get('status') not in ('PASS', 'FAIL', 'UNKNOWN')
                or result.get('payload_sha256') != prepared['payload_sha256']
                or quality.get('payload_sha256') != prepared['payload_sha256']):
            raise ContractError('Sensing response quality or payload identity mismatch')
        offsets = np.array([geometry.offset(role, self.cfg) for _, role in team])
        pos = state['positions'][[i for i, _ in team]]
        G = bool(np.all(np.linalg.norm(pos-self.targets[j].position(tick*DT)-offsets, axis=1)
                        <= geometry.radius(self.cfg)))
        point = dict(tick=tick, G=G, Q=quality['status'])
        state['last_points'][j] = point
        state['measurement_requests'] += 1
        state['reported_estimator_calls'] += int(result.get('estimator_called') is True)
        return dict(target=j, tick=tick, start_tick=state['streams'][j]['start_tick'], G=G,
                    public_frame=frame, payload_sha256=prepared['payload_sha256'], quality=_json(quality))

    def _frame(self, state, phase, before, control, stop_times, measures, events, lo=None, effort_delta=None):
        current = {str(j): p for j, p in enumerate(state['last_points'])
                   if p is not None and p['tick'] == state['tick']}
        return _json(dict(phase=phase, tick=state['tick'], time=state['tick']*DT,
                          lo_time=lo, hi_time=state['tick']*DT,
                          positions_start=before.tolist(), positions=state['positions'].tolist(),
                          control=np.asarray(control).tolist(), control_stop_times=stop_times,
                          assignment=[a.to_dict() for a in state['assignment']],
                          G={j: p['G'] for j, p in current.items()}, Q={j: p['Q'] for j, p in current.items()},
                          progress=[s.progress for s in state['clocks']], status=state['status'],
                          energy=state['total_effort'], effort_by_robot=state['effort_by_robot'],
                          effort_delta_by_robot=effort_delta or [0.]*self.cfg.robots,
                          measurements=measures, events=events, metrics=self._metrics(state)))

    def _commit(self, state, frame, events):
        self._state = state
        self.frames.append(deepcopy(frame))
        self.events.extend(deepcopy(events))
        self._pending_sense = None

    def _boundary(self, actions):
        state = deepcopy(self._state)
        events, measures = [], []
        changed = [i for i, (a, b) in enumerate(zip(actions, state['assignment'])) if a != b]
        if changed:
            events.append(dict(type='assignment', time=self.time, tick=self.tick, robots=changed,
                               before=[a.to_dict() for a in state['assignment']],
                               after=[a.to_dict() for a in actions], change_cost=self.cfg.change_cost*len(changed)))
        state['changes'] += len(changed)
        state['change_cost'] += self.cfg.change_cost * len(changed)
        state['assignment'] = actions
        for j in sorted({a.target for a in actions if a.target is not None}):
            if state['locks'][j] is None:
                state['locks'][j] = self.fixed_teams[j]
                state['clocks'][j] = replace(initial_state(self.cfg), team=self.fixed_teams[j])
                stream_id = f'{self.attempt_id}:{self.environment_id}:target{j}:start{self.tick}'
                state['streams'][j] = dict(stream_id=stream_id, start_tick=self.tick)
            point = state['last_points'][j]
            if point is None:
                measures.append(self._endpoint(state, j, self.tick))
                point = state['last_points'][j]
                state['windows'][j] = [self.tick] if point['G'] and point['Q'] == 'PASS' else []
            elif point['tick'] != self.tick:
                raise ContractError('Retained task has no current left endpoint')
        frame = self._frame(state, 'decision', state['positions'], np.zeros_like(state['positions']),
                            [self.time]*self.cfg.robots, measures, events)
        self._commit(state, frame, events)

    def _finish_task(self, state, j, kind, at, events):
        if state['status'][j] != 'active':
            raise ContractError('Duplicate terminal settlement')
        state['status'][j] = kind
        target = self.targets[j]
        if kind == 'completed':
            state['completion_times'][j] = at
            state['completion_windows'][j] = list(state['windows'][j])
            state['components']['completion'] += target.weight/self.cfg.weight_reference
            event_type = 'completion'
        elif kind == 'escaped':
            state['escape_times'][j] = at
            event_type = 'escape'
        else:
            event_type = 'window_end'
        event_tick = round(at/DT) if math.isclose(at, round(at/DT)*DT, abs_tol=TOL, rel_tol=0) else None
        events.append(dict(type=event_type, target=j, time=at, event_tick=event_tick,
                           progress=state['clocks'][j].progress))
        robots = [i for i, a in enumerate(state['assignment']) if a.target == j]
        if robots:
            events.append(dict(type='release', target=j, time=at, event_tick=event_tick,
                               robots=robots, reason=kind, virtual=False))
            state['assignment'] = tuple(IDLE if a.target == j else a for a in state['assignment'])
        state['ended_ids'].append(j)

    def _advance_tick(self):
        cfg = self.cfg
        state = deepcopy(self._state)
        n = state['tick'] + 1
        lo, hi = state['tick']*DT, n*DT
        before = state['positions'].copy()
        control = np.zeros_like(before)
        stops = [lo]*cfg.robots
        energy_delta = [0.]*cfg.robots
        events, measures = [], []
        state['new_ids'], state['ended_ids'] = [], []
        for j in [i for i, status in enumerate(state['status']) if status == 'active']:
            target = self.targets[j]
            escape = self._escape[j]
            robots = [i for i, a in enumerate(state['assignment']) if a.target == j]
            stop = min(hi, escape)
            elapsed = max(0., stop-lo)
            if robots:
                team = state['locks'][j]
                if tuple(robots) != tuple(i for i, _ in team):
                    raise ContractError('Locked team/resource mismatch')
                offsets = np.array([geometry.offset(role, cfg) for _, role in team])
                pos = state['positions'][robots].copy()
                # Frozen original control expression and reduction order.
                command = target.velocity_at(lo) + cfg.travel_gain*(target.position(lo)+offsets-pos)
                speeds = np.linalg.norm(command, axis=1)
                command *= np.minimum(1., cfg.max_speed/np.maximum(speeds, 1e-15))[:, None]
                pos += command*elapsed
                effort = float(np.sum(command**2))*elapsed
                state['positions'][robots] = pos
                state['total_effort'] += effort
                state['components']['effort'] -= cfg.control_weight*effort/cfg.effort_reference
                state['peak_speed'] = max(state['peak_speed'], float(np.linalg.norm(command, axis=1).max()))
                for local, robot in enumerate(robots):
                    control[robot] = command[local]
                    stops[robot] = stop
                    energy_delta[robot] = float(np.sum(command[local]**2))*elapsed
                    state['effort_by_robot'][robot] += energy_delta[robot]
                    state['occupied_by_robot'][robot] += elapsed
            if escape <= hi + TOL:
                self._finish_task(state, j, 'escaped', escape, events)
                cost_stop = escape
            else:
                cost_stop = hi
                if robots:
                    left = deepcopy(state['last_points'][j])
                    if left is None or left['tick'] != n-1:
                        raise ContractError('Missing service left endpoint')
                    measures.append(self._endpoint(state, j, n))
                    right = state['last_points'][j]
                    valid = left['G'] and left['Q'] == 'PASS' and right['G'] and right['Q'] == 'PASS'
                    prior = state['clocks'][j].progress
                    clock, done, interruptions = advance_clock(state['clocks'][j], target.service_duration,
                                                               state['locks'][j], valid, hi)
                    state['clocks'][j] = clock
                    for row in interruptions:
                        reasons = []
                        if not left['G'] or not right['G']:
                            reasons.append('physical_invalid')
                        if 'FAIL' in (left['Q'], right['Q']):
                            reasons.append('quality_threshold')
                        if 'UNKNOWN' in (left['Q'], right['Q']):
                            reasons.append('quality_unavailable')
                        events.append(dict(row, type='interruption', target=j,
                                           diagnostic_reasons=reasons))
                    if valid:
                        state['windows'][j] = ([n-1, n] if prior == 0 else state['windows'][j] + [n])
                    else:
                        state['windows'][j] = [n] if right['G'] and right['Q'] == 'PASS' else []
                    if done:
                        self._finish_task(state, j, 'completed', hi, events)
            flow = target.weight*max(0., cost_stop-max(lo, target.birth))
            late = target.weight*max(0., cost_stop-max(lo, target.birth, target.deadline))
            state['flow'] += flow
            state['late'] += late
            state['components']['flow'] -= cfg.flow_weight*flow/(cfg.weight_reference*cfg.stage_dt)
            state['components']['late'] -= cfg.late_weight*late/(cfg.weight_reference*cfg.stage_dt)
        state['tick'] = n
        for target in self.targets:
            if state['status'][target.id] == 'hidden' and target.birth <= hi + TOL:
                state['status'][target.id] = 'active'
                state['new_ids'].append(target.id)
                events.append(dict(type='birth', target=target.id, time=target.birth, event_tick=n))
        if n == self.end_tick:
            if state['terminal_settled']:
                raise ContractError('Duplicate terminal penalty')
            for j in [i for i, status in enumerate(state['status']) if status == 'active']:
                self._finish_task(state, j, 'unfinished', hi, events)
            state['components']['terminal'] -= cfg.unfinished_weight*sum(
                t.weight for t in self.targets if state['status'][t.id] != 'completed')/cfg.weight_reference
            state['terminal_settled'] = True
        frame = self._frame(state, 'physical', before, control, stops, measures, events,
                            lo=lo, effort_delta=energy_delta)
        self._commit(state, frame, events)

    def step_fixed_assignment(self, actions, *, expected_start_tick, request_id):
        self._check_identity()
        expected_start_tick = _integer(expected_start_tick, 'expected_start_tick')
        if not isinstance(request_id, str) or not request_id:
            raise ContractError('Nonempty step request_id required')
        normalized = canonical_actions(actions, self.cfg.robots)
        fingerprint = digest(dict(attempt_id=self.attempt_id, environment_id=self.environment_id,
                                  execution_contract_id=CONTRACT_ID, request_id=request_id,
                                  expected_start_tick=expected_start_tick, assignment=normalized))
        if request_id in self._cache:
            cached = self._cache[request_id]
            if cached['fingerprint'] != fingerprint:
                raise ContractError('Conflicting successful step request')
            result = deepcopy(cached['result'])
            result['replayed'] = True
            return result
        if self._inflight is not None:
            if self._inflight['request_id'] == request_id:
                if self._inflight['fingerprint'] != fingerprint:
                    raise ContractError('Conflicting in-flight step request')
                return dict(status='IN_PROGRESS', request_id=request_id, fingerprint=fingerprint,
                            execution_contract_id=CONTRACT_ID)
            raise ContractError('BUSY: another step is in progress')
        if self.failed or self.done:
            raise ContractError('New execution request after terminal/failed episode')
        if expected_start_tick != self.tick or self.tick % DECISION_TICKS:
            raise ContractError('Stale, skipped or nondecision start boundary')
        validated = self._validate_actions(normalized)
        self._inflight = dict(request_id=request_id, fingerprint=fingerprint, expected_start_tick=expected_start_tick)
        first_frame, first_event = len(self.frames), len(self.events)
        end_tick = min(self.end_tick, self.tick + DECISION_TICKS)
        try:
            self._boundary(validated)
            while self.tick < end_tick:
                self._advance_tick()
            result = dict(status='COMMITTED', execution_contract_id=CONTRACT_ID,
                          request_id=request_id, fingerprint=fingerprint,
                          commit_id=digest(dict(environment=self.environment_id, request=fingerprint, end_tick=self.tick)),
                          start_tick=expected_start_tick, end_tick=self.tick, replayed=False,
                          assignment_requested=normalized, frames=deepcopy(self.frames[first_frame:]),
                          events=deepcopy(self.events[first_event:]),
                          release_events=[deepcopy(e) for e in self.events[first_event:] if e['type'] == 'release'],
                          state_after=self.observe_execution(), metrics=self.metrics())
            self._cache[request_id] = dict(fingerprint=fingerprint, result=deepcopy(result))
            self.steps.append(deepcopy(result))
            return result
        except BaseException as error:
            self.failed = True
            self.failure = dict(type=type(error).__name__, message=str(error), request_id=request_id,
                                expected_start_tick=expected_start_tick, last_committed_tick=self.tick,
                                uncommitted_sensing=deepcopy(self._pending_sense))
            raise
        finally:
            self._inflight = None

    def snapshot(self):
        self._check_identity()
        state = deepcopy(self._state)
        state['positions'] = state['positions'].tolist()
        state['assignment'] = [a.to_dict() for a in state['assignment']]
        state['clocks'] = [asdict(s) for s in state['clocks']]
        body = _json(dict(version=CONTRACT_ID, case=self._source, case_identity=self.case_identity,
                          attempt_id=self.attempt_id, environment_id=self.environment_id, driver=self.driver,
                          state=state, frames=self.frames, events=self.events, steps=self.steps,
                          cache=self._cache, inflight=self._inflight, pending_sense=self._pending_sense,
                          failed=self.failed, failure=self.failure))
        return dict(body, snapshot_sha256=digest(body))

    @classmethod
    def from_snapshot(cls, snapshot, sense_callback):
        """Caller must retain/restore the matching sensing streams as well."""
        data = deepcopy(snapshot)
        checksum = data.pop('snapshot_sha256', None)
        if checksum != digest(data) or data.get('version') != CONTRACT_ID:
            raise ContractError('Invalid bridge snapshot identity')
        if data.get('inflight') is not None:
            raise ContractError('An in-flight execution cannot be resumed automatically')
        env = cls(data['case'], sense_callback, attempt_id=data['attempt_id'],
                  environment_id=data['environment_id'], driver=data['driver'])
        if env.case_identity != data['case_identity']:
            raise ContractError('Snapshot source identity differs')
        state = data['state']
        state['positions'] = np.array(state['positions'], dtype=float)
        state['assignment'] = tuple(Assignment(**a) for a in state['assignment'])
        state['clocks'] = [restore_state(env.cfg, s) for s in state['clocks']]
        state['locks'] = [None if team is None else canonical_team(team) for team in state['locks']]
        if state['positions'].shape != (env.cfg.robots, 2) or not np.isfinite(state['positions']).all():
            raise ContractError('Invalid restored positions')
        if not 0 <= _integer(state['tick'], 'tick') <= env.end_tick:
            raise ContractError('Invalid restored time')
        env._state = state
        env.frames, env.events, env.steps = data['frames'], data['events'], data['steps']
        env._cache, env.failed, env.failure = data['cache'], data['failed'], data['failure']
        env._pending_sense = data.get('pending_sense')
        return env
