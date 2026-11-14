"""Shared vectorized physics for real execution and candidate predictions.

Only TRAVEL uses forward Euler. COMMIT uses the exact capped-gain trajectory,
with an analytic energy integral and endpoint speed bound.
"""
from __future__ import annotations

from pursuit_v2.service import reject_service

from dataclasses import dataclass
import math
import numpy as np

from .config import Config
from .types import Target


class TrackingController:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def residual(self, s: float) -> float:
        c, tp, eps = self.cfg.time_gain, self.cfg.capture_check, self.cfg.singularity_epsilon
        if s < -1e-10 or s > self.cfg.stage_dt + 1e-10:
            raise ValueError("Local time outside stage")
        s = max(0.0, s)
        if s > tp:
            return self.residual(tp) * math.exp(-self.cfg.hold_gain * (s - tp))
        if s <= tp - eps:
            return ((tp - s) / tp) ** (2 * c)
        return (eps / tp) ** (2 * c) * math.exp(-2 * c * (s - tp + eps) / eps)

    def alpha(self, s: float, hold_start: bool = False) -> float:
        cfg = self.cfg
        if s > cfg.capture_check or hold_start:
            return cfg.hold_gain * self.residual(s)
        return 2 * cfg.time_gain / max(cfg.capture_check - s, cfg.singularity_epsilon) * self.residual(s)

    def peak(self, error: np.ndarray, velocity: np.ndarray) -> np.ndarray:
        """Return exact per-robot peaks [batch, robots], to floating accuracy."""
        cfg = self.cfg
        points = (0.0, cfg.capture_check - cfg.singularity_epsilon,
                  cfg.capture_check, cfg.stage_dt)
        multipliers = [self.alpha(s) for s in points]
        multipliers.append(self.alpha(cfg.capture_check, hold_start=True))
        peaks = [np.linalg.norm(velocity - a * error, axis=-1) for a in multipliers]
        return np.maximum.reduce(peaks)

    def _alpha_square_integral(self, lo: float, hi: float) -> float:
        cfg = self.cfg
        c, tp, eps = cfg.time_gain, cfg.capture_check, cfg.singularity_epsilon
        cut = tp - eps
        total = 0.0
        a, b = lo, min(hi, cut)
        if b > a:
            power = 4 * c - 1
            total += 4 * c * c / tp ** (4 * c) * (
                (tp - a) ** power - (tp - b) ** power) / power
        a, b = max(lo, cut), min(hi, tp)
        if b > a:
            rate = 2 * c / eps
            amplitude = rate * (eps / tp) ** (2 * c)
            total += amplitude ** 2 / (2 * rate) * (
                math.exp(-2 * rate * (a - cut)) - math.exp(-2 * rate * (b - cut)))
        a, b = max(lo, tp), hi
        if b > a:
            rate = cfg.hold_gain
            amplitude = rate * self.residual(tp)
            total += amplitude ** 2 / (2 * rate) * (
                math.exp(-2 * rate * (a - tp)) - math.exp(-2 * rate * (b - tp)))
        return total

    def energy(self, error: np.ndarray, velocity: np.ndarray, lo: float, hi: float):
        axes = tuple(range(1, error.ndim))
        count = np.prod(error.shape[1:-1])
        cross = np.sum(error * velocity, axis=axes)
        squared = np.sum(error * error, axis=axes)
        result = (count * float(np.dot(velocity, velocity)) * (hi - lo)
                  - 2 * cross * (self.residual(lo) - self.residual(hi))
                  + squared * self._alpha_square_integral(lo, hi))
        return np.maximum(0.0, result)

    def interval_peak(self, error, velocity, lo, hi):
        points = [lo, hi]
        cfg = self.cfg
        if lo < cfg.capture_check < hi:
            points += [cfg.capture_check]
        values = [self.alpha(s, hold_start=(s == lo and lo >= cfg.capture_check))
                  for s in points]
        if lo <= cfg.capture_check < hi:
            values += [self.alpha(cfg.capture_check, hold_start=True)]
        return np.maximum.reduce([
            np.linalg.norm(velocity - a * error, axis=-1).max(axis=1) for a in values
        ])


@dataclass
class Rollout:
    positions: np.ndarray
    capture_times: np.ndarray
    escape_times: np.ndarray
    effort: np.ndarray
    peak_speed: np.ndarray
    partner_wait: np.ndarray
    first_commit_times: np.ndarray
    stages: list[dict]
    frames: list[tuple[float, np.ndarray]]
    mismatch_count: np.ndarray


def _stepwise_checks(cfg: Config, start: float, end: float):
    """Global detection ticks; extra integration endpoints are not capture ticks."""
    return [round(index * cfg.step_dt, 10)
            for index in range(math.floor(start / cfg.step_dt) + 1,
                               math.floor((end + 1e-10) / cfg.step_dt) + 1)
            if start + 1e-10 < index * cfg.step_dt <= end + 1e-10]


def _is_stepwise_check(cfg: Config, time: float):
    return math.isclose(time, round(time / cfg.step_dt) * cfg.step_dt,
                        rel_tol=0.0, abs_tol=1e-10)


def _capture_success(cfg, target, pos, offsets, complete, alive, time):
    anchor = target.position(time)[None, None, :] + offsets
    return (alive & complete &
            (np.linalg.norm(pos - anchor, axis=-1)
             .max(axis=1) <= cfg.capture_radius + 1e-10))


def rollout_target(cfg: Config, target: Target, positions: np.ndarray, offsets: np.ndarray,
                   complete: np.ndarray, start: float, stages: int = 1,
                   trace: bool = False, until: float | None = None) -> Rollout:
    """Batch candidates for ONE target, shape [batch, participating robots, xy].

    Each batch element is an independent counterfactual. No births, assignment
    changes, or access to an Environment occur during this function.
    """
    reject_service(cfg)
    if cfg.turn_max_angle > 0 or cfg.speed_delta_max > 0 or \
            cfg.motion_model == "continuous_turn":
        return rollout_turning_target(cfg, target, positions, offsets, complete, start,
                                      stages, trace, until)
    pos = np.array(positions, dtype=float, copy=True)
    offsets = np.asarray(offsets, dtype=float)
    batch, robots, dimension = pos.shape
    if dimension != 2 or robots < 1 or offsets.shape != (batch, robots, 2):
        raise ValueError("Invalid batch or offset shape")
    complete = np.asarray(complete, dtype=bool)
    if complete.shape != (batch,):
        raise ValueError("Invalid completion mask")
    controller = TrackingController(cfg)
    velocity = target.velocity_at(start)
    captured = np.full(batch, np.nan)
    escaped = np.full(batch, np.nan)
    effort = np.zeros(batch)
    peak_speed = np.zeros(batch)
    wait = np.zeros(batch)
    first_commit = np.full(batch, np.nan)
    mismatches = np.zeros(batch, dtype=int)
    summaries, frames = [], []
    escape_at = target.escape_time(cfg.side)
    instant = cfg.capture_mode == "stepwise_instant"
    end = min(cfg.end_time, start + stages * cfg.stage_dt if until is None else until)
    if trace:
        frames.append((start, pos.copy()))

    for stage_index in range(stages):
        now = start + stage_index * cfg.stage_dt
        if instant and now >= end - 1e-10:
            break
        stage_end = min(now + cfg.stage_dt, end) if instant else now + cfg.stage_dt
        alive = np.isnan(captured) & np.isnan(escaped)
        escaped[alive & (escape_at <= now + 1e-10)] = escape_at
        alive &= np.isnan(escaped)
        if instant:
            success = _capture_success(cfg, target, pos, offsets, complete, alive, now)
            captured[success] = now
            alive &= ~success
        anchor0 = target.position(now)[None, None, :] + offsets
        error0 = pos - anchor0
        guard_peak = controller.peak(error0, velocity)
        residual_error = np.linalg.norm(error0, axis=-1).max(axis=1) * controller.residual(cfg.capture_check)
        commit = (alive & complete & (cfg.turn_max_angle == 0) & (not target.turns)
                  & (not target.arc_rates)
                  & (escape_at > now + cfg.capture_check + 1e-10)
                  & (guard_peak.max(axis=1) <= cfg.max_speed + 1e-10)
                  & (residual_error <= cfg.capture_radius + 1e-10))
        first_commit[commit & np.isnan(first_commit)] = now
        modes = np.where(alive, np.where(commit, "COMMIT", "TRAVEL"), "HOLD")
        stage_effort = np.zeros(batch)
        stage_peak = np.zeros(batch)
        times = [i * cfg.step_dt for i in range(round(cfg.stage_dt / cfg.step_dt) + 1)]
        checks = _stepwise_checks(cfg, now, stage_end) if instant else [now + cfg.capture_check]
        if instant:
            times = [s for s in times if s <= stage_end - now + 1e-10]
            times.append(stage_end - now)
            times.extend(check - now for check in checks)
        if now < escape_at < stage_end:
            times.append(escape_at - now)
        times.extend(turn_time - now for turn_time, _, _ in target.turns
                     if now < turn_time < stage_end)
        times = sorted(set(round(s, 12) for s in times))

        for lo, hi in zip(times[:-1], times[1:]):
            duration = hi - lo
            if duration <= 0:
                continue
            alive = np.isnan(captured) & np.isnan(escaped)
            anchor = target.position(now + lo)[None, None, :] + offsets
            ready = np.linalg.norm(pos - anchor, axis=-1) <= cfg.capture_radius
            waiting = ready.sum(axis=1) * (~(ready.all(axis=1) & complete)) * alive
            wait += waiting * duration

            analytic = alive & commit
            if np.any(analytic):
                peaks = controller.interval_peak(error0, velocity, lo, hi)
                bad = analytic & (peaks > cfg.max_speed + 1e-8)
                if np.any(bad):
                    commit[bad] = False
                    modes[bad] = "FALLBACK"
                    mismatches[bad] += 1
                analytic &= ~bad
                if np.any(analytic):
                    new_anchor = target.position(now + hi)[None, None, :] + offsets
                    analytic_positions = new_anchor + controller.residual(hi) * error0
                    pos[analytic] = analytic_positions[analytic]
                    energy = controller.energy(error0, velocity, lo, hi)
                    stage_effort[analytic] += energy[analytic]
                    stage_peak[analytic] = np.maximum(stage_peak[analytic], peaks[analytic])

            numerical = alive & ~commit
            if np.any(numerical):
                current_velocity = target.velocity_at(now + lo)
                command = current_velocity + cfg.travel_gain * (anchor - pos)
                speed = np.linalg.norm(command, axis=-1, keepdims=True)
                command *= np.minimum(1.0, cfg.max_speed / np.maximum(speed, 1e-15))
                pos[numerical] += command[numerical] * duration
                energy = np.sum(command ** 2, axis=(1, 2)) * duration
                speeds = np.linalg.norm(command, axis=-1).max(axis=1)
                stage_effort[numerical] += energy[numerical]
                stage_peak[numerical] = np.maximum(stage_peak[numerical], speeds[numerical])

            # Escape has precedence, including an exact tie with the capture check.
            if escape_at <= now + hi + 1e-10:
                escaped[alive] = escape_at
            is_check = (_is_stepwise_check(cfg, now + hi) if instant else
                        math.isclose(hi, cfg.capture_check, abs_tol=1e-10))
            if is_check:
                success = _capture_success(cfg, target, pos, offsets, complete,
                                           alive & np.isnan(escaped), now + hi)
                captured[success] = now + hi
            if trace:
                frames.append((now + hi, pos.copy()))
        effort += stage_effort
        peak_speed = np.maximum(peak_speed, stage_peak)
        summaries.append({"time": now, "modes": modes, "guard_peaks": guard_peak,
                          "effort": stage_effort, "peak_speed": stage_peak})
    return Rollout(pos, captured, escaped, effort, peak_speed, wait, first_commit,
                   summaries, frames, mismatches)


def rollout_turning_target(cfg: Config, target: Target, positions: np.ndarray,
                           offsets: np.ndarray, complete: np.ndarray, start: float,
                           stages: int, trace: bool, until: float | None) -> Rollout:
    """Feedback execution; the selected capture clock is shared by every caller."""
    reject_service(cfg)
    pos = np.array(positions, dtype=float, copy=True)
    offsets = np.asarray(offsets, dtype=float)
    complete = np.asarray(complete, dtype=bool)
    if pos.ndim != 3 or pos.shape[2:] != (2,) or offsets.shape != pos.shape[:2] + (2,):
        raise ValueError("Invalid batch or offset shape")
    batch, robots = pos.shape[:2]
    if complete.shape != (batch,):
        raise ValueError("Invalid completion mask")
    end = min(cfg.end_time, start + stages * cfg.stage_dt if until is None else until)
    captured, escaped = np.full(batch, np.nan), np.full(batch, np.nan)
    effort, peak, wait = np.zeros(batch), np.zeros(batch), np.zeros(batch)
    escape_at = target.escape_time(cfg.side)
    alive_at_start = escape_at > start + 1e-10
    if not alive_at_start:
        escaped[:] = escape_at
    instant = cfg.capture_mode == "stepwise_instant"
    if instant and start < cfg.end_time - 1e-10:
        success = _capture_success(cfg, target, pos, offsets, complete,
                                   np.isnan(escaped), start)
        captured[success] = start
    frames = [(start, pos.copy())] if trace else []
    grid = [start + i * cfg.step_dt for i in range(round((end - start) / cfg.step_dt) + 1)]
    grid.append(end)
    if start < escape_at < end:
        grid.append(escape_at)
    grid.extend(t for t, _, _ in target.turns if start < t < end)
    grid.extend(t for t, _ in target.arc_rates if start < t < end)
    checks = [n * cfg.stage_dt + cfg.capture_check
              for n in range(math.floor(start / cfg.stage_dt),
                              math.ceil(end / cfg.stage_dt) + 1)]
    if instant:
        checks = _stepwise_checks(cfg, start, end)
    grid.extend(t for t in checks if start < t <= end + 1e-10)
    times = sorted(set(round(t, 10) for t in grid if start - 1e-10 <= t <= end + 1e-10))
    for lo, hi in zip(times[:-1], times[1:]):
        duration = hi - lo
        if duration <= 0:
            continue
        alive = np.isnan(captured) & np.isnan(escaped)
        anchor = target.position(lo)[None, None, :] + offsets
        ready = np.linalg.norm(pos - anchor, axis=-1) <= cfg.capture_radius
        wait += ready.sum(axis=1) * (~(ready.all(axis=1) & complete)) * alive * duration
        command = target.velocity_at(lo) + cfg.travel_gain * (anchor - pos)
        speed = np.linalg.norm(command, axis=-1, keepdims=True)
        command *= np.minimum(1.0, cfg.max_speed / np.maximum(speed, 1e-15))
        pos[alive] += command[alive] * duration
        effort[alive] += np.sum(command[alive] ** 2, axis=(1, 2)) * duration
        interval_peak = np.linalg.norm(command, axis=-1).max(axis=1)
        peak[alive] = np.maximum(peak[alive], interval_peak[alive])
        if escape_at <= hi + 1e-10:
            escaped[alive] = escape_at
        is_check = (_is_stepwise_check(cfg, hi) if instant else
                    any(math.isclose(hi, check, abs_tol=1e-9) for check in checks))
        if is_check:
            success = _capture_success(cfg, target, pos, offsets, complete,
                                       alive & np.isnan(escaped), hi)
            captured[success] = hi
        if trace:
            frames.append((hi, pos.copy()))
    modes = "TRAVEL" if alive_at_start else "HOLD"
    return Rollout(pos, captured, escaped, effort, peak, wait, np.full(batch, np.nan),
                   [{"time": start, "modes": np.full(batch, modes),
                     "guard_peaks": np.zeros((batch, robots)), "effort": effort,
                     "peak_speed": peak}], frames, np.zeros(batch, dtype=int))


def candidate_benefit(cfg: Config, target: Target, result: Rollout, start: float, stages: int,
                      until: float | None = None):
    """Incremental finite-horizon reward versus leaving this task unattended."""
    reject_service(cfg)
    end = min(cfg.end_time, start + stages * cfg.stage_dt if until is None else until)
    unattended_stop = min(end, target.escape_time(cfg.side))
    stop = np.where(np.isfinite(result.capture_times), result.capture_times, unattended_stop)
    flow_saved = target.weight * np.maximum(0.0, unattended_stop - stop)
    late_origin = max(start, target.birth, target.deadline)
    late_saved = target.weight * (max(0.0, unattended_stop - late_origin)
                                  - np.maximum(0.0, stop - late_origin))
    success = np.isfinite(result.capture_times)
    score = (target.weight * success / cfg.weight_reference
             + cfg.flow_weight * flow_saved / (cfg.weight_reference * cfg.stage_dt)
             + cfg.late_weight * late_saved / (cfg.weight_reference * cfg.stage_dt)
             - cfg.control_weight * result.effort / cfg.effort_reference)
    if end >= cfg.end_time - 1e-9:
        score += cfg.unfinished_weight * target.weight * success / cfg.weight_reference
    return score
