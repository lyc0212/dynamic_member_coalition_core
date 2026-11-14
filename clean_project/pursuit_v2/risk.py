"""Online forecasts. Inputs are observations only; scenario turns stay private to Environment."""
from __future__ import annotations

from pursuit_v2.service import reject_service

from dataclasses import replace
import math

import numpy as np

from .physics import candidate_benefit, rollout_target
from .motion import motion_step
from .types import Observation, Target, complete_roles, role_offset


def forecast_paths(obs: Observation, target: Target, horizon: int,
                   samples: int | None = None) -> tuple[Target, ...]:
    reject_service(obs.config)
    cfg = obs.config
    if cfg.motion_model == "continuous_turn":
        end = min(cfg.end_time, obs.time + horizon * cfg.stage_dt)
        index = max(1, math.ceil((obs.time - target.birth) / cfg.turn_interval - 1e-10))
        first = target.birth + index * cfg.turn_interval
        times = np.arange(first, end, cfg.turn_interval)
        tick = round(obs.time / cfg.step_dt)
        rng = np.random.default_rng(np.random.SeedSequence([target.id, tick, 271828]))
        speed_rng = np.random.default_rng(np.random.SeedSequence([target.id, tick, 271829]))
        paths = []
        for _ in range(cfg.risk_samples if samples is None else samples):
            angle = math.atan2(target.velocity[1], target.velocity[0])
            speed = float(np.linalg.norm(target.velocity))
            rates = []
            for time in times:
                event_index = round((time - target.birth) / cfg.turn_interval)
                next_angle, speed, _, _ = motion_step(
                    cfg, angle, speed, 0.0, event_index, rng, speed_rng)
                rates.append((float(time), (next_angle - angle) / cfg.turn_interval))
                angle = next_angle
            if end > max(obs.time, target.birth) + 1e-10:
                rates.append((float(end), 0.0))
            paths.append(replace(target, arc_rates=tuple(rates)))
        return tuple(paths)
    if cfg.turn_max_angle == 0 and cfg.speed_delta_max == 0:
        return (target,)
    end = min(cfg.end_time, obs.time + horizon * cfg.stage_dt)
    first = target.birth + (math.floor((obs.time - target.birth) / cfg.turn_interval) + 1) * cfg.turn_interval
    times = np.arange(first, end, cfg.turn_interval)
    tick = round(obs.time / cfg.step_dt)
    rng = np.random.default_rng(np.random.SeedSequence([target.id, tick, 271828]))
    speed_rng = np.random.default_rng(np.random.SeedSequence([target.id, tick, 271829]))
    initial_speed = float(np.linalg.norm(target.velocity))
    initial_angle = math.atan2(target.velocity[1], target.velocity[0])
    paths = []
    for _ in range(cfg.risk_samples if samples is None else samples):
        angle = initial_angle
        speed = initial_speed
        increment = target.turn_increment
        turns = []
        for time in times:
            index = round((time - target.birth) / cfg.turn_interval)
            angle, speed, increment, velocity = motion_step(
                cfg, angle, speed, increment, index, rng, speed_rng)
            turns.append((float(time), *velocity))
        paths.append(replace(target, turns=tuple(turns)))
    return tuple(paths)


def risk_horizon(obs: Observation, target: Target) -> int:
    remaining = obs.config.max_stages - obs.stage
    until_deadline = max(0, math.ceil((target.deadline - obs.time) / obs.config.stage_dt))
    return min(remaining, max(obs.config.prediction_stages, until_deadline))


def travel_certificate(obs: Observation, target: Target, group, roles) -> dict:
    """Sufficient next-check capture test for sampled, unsaturated TRAVEL dynamics.

    Requires exact current state, complete roles held until the next future check,
    target speed <= configured bound, and turns aligned with step_dt. Environment
    validates speed and turn alignment. The check must be within cfg.end_time.
    In stepwise_instant this is a capture-time UPPER bound, never the earliest
    capture-time estimate. The same fixed check remains a global detection tick.
    """
    reject_service(obs.config)
    cfg = obs.config
    phase_start = math.floor(obs.time / cfg.stage_dt) * cfg.stage_dt
    check = phase_start + cfg.capture_check
    if check <= obs.time + 1e-10:
        check += cfg.stage_dt
    duration = check - obs.time
    count = round(duration / cfg.step_dt)
    offsets = np.array([role_offset(role, cfg) for role in roles])
    error = obs.positions[list(group)] - (target.position(obs.time)[None, :] +
                                          offsets)
    largest = float(np.linalg.norm(error, axis=-1).max())
    ratio = 1 - cfg.travel_gain * cfg.step_dt
    if cfg.motion_model == "continuous_turn":
        acceleration_bound = cfg.target_speed_max * cfg.turn_max_angle / cfg.turn_interval
        one_step_error = 0.5 * acceleration_bound * cfg.step_dt ** 2
        accumulated = (one_step_error * (1 - ratio ** count) / (1 - ratio)
                       if 0 <= ratio < 1 else math.inf)
        largest_during_travel = max(largest, one_step_error / (1 - ratio)) \
            if 0 <= ratio < 1 else math.inf
    else:
        accumulated = 0.0
        largest_during_travel = largest
    speed_margin = (cfg.max_speed - cfg.target_speed_max -
                    cfg.travel_gain * largest_during_travel)
    endpoint_margin = (cfg.capture_radius - max(0.0, ratio) ** count * largest -
                       accumulated)
    escape_margin = cfg.side - target.position(obs.time)[0] - cfg.target_speed_max * duration
    valid_clock = math.isclose(count * cfg.step_dt, duration, abs_tol=1e-9)
    within_episode = check <= cfg.end_time + 1e-10
    certified = bool((cfg.turn_max_angle > 0 or cfg.speed_delta_max > 0 or
                      cfg.motion_model == "continuous_turn")
                     and complete_roles(target, roles)
                     and len(group) == len(roles)
                     and len(set(group)) == target.required_robots
                     and valid_clock and within_episode and 0 <= ratio < 1
                     and speed_margin >= -1e-10 and endpoint_margin >= -1e-10
                     and escape_margin > 1e-10)
    result = {"certified_next_check": certified,
              "certified_on_time": certified and check <= target.deadline + 1e-10,
              "next_check": check, "speed_margin": speed_margin,
              "endpoint_margin": endpoint_margin, "escape_margin": escape_margin,
              "curvature_error_bound": accumulated}
    if cfg.capture_mode == "stepwise_instant":
        result["capture_time_upper_bound"] = check if certified else None
        result["certificate_semantics"] = "capture_by_fixed_check_if_assignment_held"
    return result


def assess_options(obs: Observation, target: Target, options, horizon: int,
                   samples: int | None = None):
    """Joint success: every robot in the candidate shares each sampled target path."""
    reject_service(obs.config)
    if not options:
        return []
    cfg = obs.config
    prediction_cfg = replace(cfg, step_dt=cfg.risk_prediction_dt)
    positions = np.array([obs.positions[list(group)] for group, _ in options])
    offsets = np.array([[role_offset(role, cfg) for role in roles] for _, roles in options])
    complete = np.array([complete_roles(target, roles) and
                         len(group) == len(roles) and
                         len(set(group)) == target.required_robots
                         for group, roles in options], dtype=bool)
    scores, on_time, completed, waits, efforts, peaks, captures = [], [], [], [], [], [], []
    for path in forecast_paths(obs, target, horizon, samples):
        result = rollout_target(prediction_cfg, path, positions, offsets,
                                complete, obs.time, horizon)
        scores.append(candidate_benefit(cfg, path, result, obs.time, horizon))
        completed.append(np.isfinite(result.capture_times))
        on_time.append(np.isfinite(result.capture_times) &
                       (result.capture_times <= target.deadline + 1e-10))
        waits.append(result.partner_wait)
        efforts.append(result.effort)
        peaks.append(result.peak_speed)
        captures.append(result.capture_times)
    values = []
    for i in range(len(options)):
        successful = [row[i] for row in captures if np.isfinite(row[i])]
        values.append({
            "benefit": float(np.mean([row[i] for row in scores])),
            "on_time_probability": float(np.mean([row[i] for row in on_time])),
            "completion_probability": float(np.mean([row[i] for row in completed])),
            "capture_time": float(np.mean(successful)) if successful else None,
            "partner_wait": float(np.mean([row[i] for row in waits])),
            "effort": float(np.mean([row[i] for row in efforts])),
            "peak_speed": float(np.max([row[i] for row in peaks])),
            **travel_certificate(obs, target, *options[i]),
        })
    return values
