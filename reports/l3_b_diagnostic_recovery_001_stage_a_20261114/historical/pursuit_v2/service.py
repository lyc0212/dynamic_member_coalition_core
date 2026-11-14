"""2A-1 fixed-team position service; known-path rollout, not an allocator.

Only global 0.05-second endpoints establish service. A private known trajectory
is accepted here for physics verification; it is never added to Observation.
"""
from dataclasses import dataclass, replace
import math
import numpy as np

from .types import complete_roles, role_offset
from . import observation_geometry as geometry

DT = 0.05
TOL = 1e-10


def reject_service(cfg):
    if cfg.capture_mode == "stepwise_service":
        raise ValueError("stepwise_service: instantaneous reward/risk/M3 is not adapted; use fixed-service physics")


def tick(time):
    if not math.isfinite(time) or time < 0:
        raise ValueError("Service time must be finite and nonnegative")
    index = round(time / DT)
    if not math.isclose(time, index * DT, rel_tol=0, abs_tol=TOL):
        raise ValueError("Service endpoints must align with the global 0.05 grid")
    return index


def canonical_team(team):
    pairs = tuple(team)
    if any(isinstance(i, bool) or not isinstance(i, (int, np.integer)) or i < 0
           or r not in geometry.ALL_ROLES for i, r in pairs):
        raise ValueError("Invalid robot identity or role")
    if len({i for i, _ in pairs}) != len(pairs):
        raise ValueError("Duplicate robot identity")
    return tuple(sorted((int(i), r) for i, r in pairs))


@dataclass(frozen=True)
class ServiceState:
    """Immutable restart clock. base + integer intervals avoids repeated dt sums."""
    base: float = 0.0
    intervals: int = 0
    team: tuple = ()

    def __post_init__(self):
        if (isinstance(self.base, bool) or not math.isfinite(self.base) or self.base < 0
                or isinstance(self.intervals, bool) or not isinstance(self.intervals, int)
                or self.intervals < 0):
            raise ValueError("Invalid service clock")
        object.__setattr__(self, "team", canonical_team(self.team))

    @property
    def progress(self):
        return math.fsum((self.base, self.intervals * DT))


@dataclass(frozen=True)
class GeometryServiceState(ServiceState):
    geometry_identity: tuple = ()

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.geometry_identity, tuple) or not self.geometry_identity:
            raise ValueError('Immutable angular geometry identity required')


def initial_state(cfg):
    signature = geometry.identity(cfg)
    return ServiceState() if signature is None else GeometryServiceState(geometry_identity=signature)


def restore_state(cfg, payload):
    """Restore a JSON clock without silently reinterpreting its geometry."""
    def freeze(value):
        return tuple(freeze(x) for x in value) if isinstance(value, (list, tuple)) else value
    values = dict(payload)
    signature = freeze(values.pop('geometry_identity', None))
    if signature != geometry.identity(cfg):
        raise ValueError('Service geometry identity mismatch')
    return (ServiceState(**values) if signature is None else
            GeometryServiceState(**values, geometry_identity=signature))


def advance_clock(state, duration, team, valid, at):
    """One *complete* global interval; callers settle escape before this call."""
    team = canonical_team(team)
    events = []
    if team != state.team:
        if state.progress > 0:
            events.append({"time": at - DT, "reason": "team_changed", "progress_before": state.progress})
        state = replace(state, base=0., intervals=0, team=team)
    if not valid:
        if state.progress > 0:
            events.append({"time": at, "reason": "observation_invalid", "progress_before": state.progress})
        return replace(state, base=0., intervals=0, team=team), False, events
    state = replace(state, intervals=state.intervals + 1, team=team)
    done = state.progress >= duration - TOL
    if done:
        state = replace(state, base=duration, intervals=0, team=team)
    return state, done, events


@dataclass
class ServiceRollout:
    positions: np.ndarray
    state: ServiceState
    completion_time: float | None
    escape_time: float | None
    effort: float
    peak_speed: float
    frames: list
    interruptions: list
    termination_reason: str


def rollout_fixed_service(cfg, target, positions, team, start, until, state=None, trace=True):
    """Pure known-path prediction in the supplied position/team order.

    Empty/incomplete teams are permitted (no service); malformed identities are
    rejected. Active input progress must be strictly below H. Terminal states
    belong to Environment and are not passed back as active predictions.
    """
    if cfg.capture_mode != "stepwise_service":
        raise ValueError("Fixed-service rollout requires stepwise_service")
    duration = target.service_duration
    if duration is None:
        raise ValueError("Every service target requires service_duration")
    first, last = tick(start), tick(until)
    if last < first or until > cfg.end_time + TOL or start < target.birth - TOL:
        raise ValueError("Invalid service prediction interval")
    start, until = first * DT, last * DT
    if any(not math.isclose(dt, DT, rel_tol=0, abs_tol=1e-12)
           for dt in (cfg.step_dt, cfg.risk_prediction_dt)):
        raise ValueError("Service execution/prediction require 0.05")
    supplied = tuple(team)
    normalized = canonical_team(supplied)
    if any(i >= cfg.robots for i, _ in normalized):
        raise ValueError("Robot identity outside configured resources")
    pos = np.array(positions, dtype=float, copy=True)
    if pos.shape != (len(supplied), 2) or not np.isfinite(pos).all():
        raise ValueError("Service positions must be [participating robots, xy]")
    for time in [t for t, _, _ in target.turns] + [t for t, _ in target.arc_rates]:
        tick(time)
    state = initial_state(cfg) if state is None else state
    if getattr(state, 'geometry_identity', None) != geometry.identity(cfg):
        raise ValueError('Service geometry identity mismatch')
    if not isinstance(state, ServiceState) or state.progress >= duration:
        raise ValueError("Active service progress must be below service_duration")
    roles = [r for _, r in supplied]
    complete = geometry.validate_roles(target.required_robots, roles, cfg)
    offsets = np.array([geometry.offset(r, cfg) for r in roles]).reshape((-1, 2))
    interruptions, frames = [], []
    effort = peak = 0.0
    completion = escaped = None
    escape_at = target.escape_time(cfg.side)
    reason = "episode_end" if until >= cfg.end_time - TOL else "horizon_truncated"

    def valid(at):
        return bool(complete and len(pos) == target.required_robots and
                    np.all(np.linalg.norm(pos - target.position(at) - offsets, axis=1)
                           <= geometry.radius(cfg)))

    if state.team != normalized:
        if state.progress > 0:
            interruptions.append({"time": start, "reason": "team_changed", "progress_before": state.progress})
        state = replace(state, base=0., intervals=0, team=normalized)
    left = valid(start)
    if escape_at <= start + TOL:
        escaped, reason = escape_at, "escaped"
    elif not left and state.progress > 0:
        interruptions.append({"time": start, "reason": "observation_invalid", "progress_before": state.progress})
        state = replace(state, base=0., intervals=0, team=normalized)

    def frame(at, effective, legal=True):
        if trace:
            frames.append({"time": at, "positions": pos.copy().tolist(),
                           "valid": bool(effective), "progress": min(duration, state.progress),
                           "effort": effort, "legal_check": legal})
            if cfg.geometry_mode != 'legacy_anchor':
                frames[-1]['geometry'] = geometry.diagnostics(cfg, target.position(at), pos, roles)
                frames[-1]['team'] = supplied
                frames[-1]['geometry_identity'] = geometry.identity(cfg)

    frame(first * DT, left and escaped is None)
    for index in range(first, last):
        lo, hi = index * DT, (index + 1) * DT
        if completion is not None or escaped is not None:
            frame(hi, False)
            continue
        stop = min(hi, escape_at)
        elapsed = max(0.0, stop - lo)
        command = target.velocity_at(lo) + cfg.travel_gain * (target.position(lo) + offsets - pos)
        speeds = np.linalg.norm(command, axis=1)
        command *= np.minimum(1.0, cfg.max_speed / np.maximum(speeds, 1e-15))[:, None]
        pos += command * elapsed
        effort += float(np.sum(command ** 2)) * elapsed
        peak = max(peak, float(np.linalg.norm(command, axis=1).max()) if len(pos) else 0.0)
        if escape_at <= hi + TOL:
            escaped, reason = escape_at, "escaped"
            if escape_at < hi - TOL:
                frame(escape_at, False, False)
            frame(hi, False)
            if trace and cfg.geometry_mode != 'legacy_anchor':
                frames[-1]['control'] = command.tolist()
                frames[-1]['control_interval'] = [lo, stop]
            continue
        right = valid(hi)
        state, done, events = advance_clock(state, duration, normalized, left and right, hi)
        interruptions.extend(events)
        if done:
            completion, reason = hi, "completed"
        frame(hi, right)
        if trace and cfg.geometry_mode != 'legacy_anchor':
            frames[-1]['control'] = command.tolist()
            frames[-1]['control_interval'] = [lo, stop]
        left = right
    return ServiceRollout(pos, state, completion, escaped, effort, peak, frames,
                          interruptions, reason)
