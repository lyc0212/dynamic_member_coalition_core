from __future__ import annotations

from pursuit_v2.service import reject_service

from dataclasses import dataclass, field
import math
import numpy as np

from pursuit_v2.physics import _stepwise_checks, _is_stepwise_check
from pursuit_v2.risk import forecast_paths, risk_horizon
from .candidates import identity


def validate_model(obs):
    reject_service(obs.config)
    cfg = obs.config
    if cfg.capture_mode != 'stepwise_instant' or cfg.motion_model != 'continuous_turn':
        raise ValueError('First version requires continuous_turn / stepwise_instant')
    if cfg.step_dt != 0.05 or cfg.risk_prediction_dt != 0.05:
        raise ValueError('Execution and prediction must both use 0.05')
    if any(t.turns or t.arc_rates for t in obs.targets):
        raise ValueError('Public observations must not contain private future trajectories')
    if obs.positions.shape != (cfg.robots, 2) or len(obs.assignment) != cfg.robots:
        raise ValueError('Expected independent robot positions and assignments')
    if not np.all(np.isfinite(obs.positions)):
        raise ValueError('Non-finite public positions')


@dataclass
class Grid:
    times: np.ndarray
    positions: np.ndarray
    velocities: np.ndarray
    legal: np.ndarray
    escape: float
    end: float


def make_grid(obs, path, horizon):
    cfg, start = obs.config, obs.time
    end = min(cfg.end_time, start + horizon * cfg.stage_dt)
    escape = path.escape_time(cfg.side)
    grid = [start + i * cfg.step_dt for i in range(round((end-start)/cfg.step_dt)+1)]
    grid.append(end)
    if start < escape < end:
        grid.append(escape)
    grid.extend(t for t, _, _ in path.turns if start < t < end)
    grid.extend(t for t, _ in path.arc_rates if start < t < end)
    grid.extend(_stepwise_checks(cfg, start, end))
    times = np.asarray(sorted(set(round(t, 10) for t in grid
                                  if start-1e-10 <= t <= end+1e-10)))
    if path.arc_rates:
        position_rows, velocity_rows = [], []
        for i, t in enumerate(times):
            position, velocity = path._arc_state(t)
            position_rows.append(position)
            if i < len(times)-1:
                velocity_rows.append(velocity)
        positions = np.asarray(position_rows)
        velocities = np.asarray(velocity_rows)
    else:
        positions = np.asarray([path.position(t) for t in times])
        velocities = np.asarray([path.velocity_at(t) for t in times[:-1]])
    legal = np.asarray([bool((i == 0 and start < cfg.end_time-1e-10) or
                             (i > 0 and _is_stepwise_check(cfg, float(t))))
                        and escape > t+1e-10 for i, t in enumerate(times)])
    return Grid(times, positions, velocities, legal, escape, end)


@dataclass
class TargetWorlds:
    obs: object
    target: object
    horizon: int
    paths: tuple
    _grids: dict = field(default_factory=dict)
    _components: dict = field(default_factory=dict)

    def grid(self, sample):
        if sample not in self._grids:
            self._grids[sample] = make_grid(self.obs, self.paths[sample], self.horizon)
        return self._grids[sample]


def freeze_worlds(obs):
    validate_model(obs)
    result = {}
    for target in obs.targets:
        horizon = risk_horizon(obs, target)
        paths = forecast_paths(obs, target, horizon)
        result[target.id] = TargetWorlds(obs, target, horizon, paths)
    fingerprint = identity([[j, w.horizon, [p.to_dict() for p in w.paths]]
                            for j, w in result.items()])
    return result, fingerprint

