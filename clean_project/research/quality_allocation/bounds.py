"""Optimistic zero-control rewards on a conservative synchronous reachability grid."""
from __future__ import annotations

from pursuit_v2.service import reject_service

from dataclasses import dataclass
import math
import numpy as np

from pursuit_v2.physics import Rollout, candidate_benefit
from pursuit_v2.types import role_offset


@dataclass
class Bounds:
    values: list[float]
    by_world: dict
    metadata: dict


def geometric_margin(obs, grid):
    """A deliberately loose gamma envelope, valid in the declared bounded domain.

    No transcendental accuracy assumption is needed: grid anchor binary64 values
    are exactly the values used by the reference controller/capture predicate.
    Each norm, clipped displacement and position update uses <32 elementary
    operations per coordinate. 4096 per substep dominates their error envelopes,
    propagation through coordinate sums, capture/distance norms and clock ulps.
    Outside this finite, non-overflow domain the caller falls back to a generic UB.
    """
    reject_service(obs.config)
    cfg = obs.config
    scale = max(1.0, float(np.abs(obs.positions).max()), float(np.abs(grid.positions).max()),
                cfg.max_speed*(grid.end-obs.time), cfg.capture_radius, cfg.anchor_offset)
    n = max(1, len(grid.times))
    if (not math.isfinite(scale) or not np.all(np.isfinite(grid.positions)) or
            not np.all(np.isfinite(grid.velocities)) or scale > 1e6 or cfg.max_speed > 1e6 or
            cfg.travel_gain > 1e6 or (grid.velocities.size and np.abs(grid.velocities).max() > 1e6) or
            cfg.capture_radius < 1e-6 or n > 100000):
        return math.inf
    coefficient = 4096*np.finfo(float).eps*(n+1)
    return 1e-10 + coefficient*(8*scale+8)/(1-coefficient)


def reward_grid(obs, world, sample):
    reject_service(obs.config)
    grid, path = world.grid(sample), world.paths[sample]
    n = len(grid.times)
    dummy = Rollout(np.zeros((n, 1, 2)), grid.times.copy(), np.full(n, np.nan),
                    np.zeros(n), np.zeros(n), np.zeros(n), np.full(n, np.nan), [], [], np.zeros(n, int))
    rewards = candidate_benefit(obs.config, path, dummy, obs.time, world.horizon)
    # Apply exactly the original zero-energy score; outward round the stored UB.
    return np.nextafter(rewards, np.inf)


def construct_bounds(obs, worlds, specs, synchronous):
    reject_service(obs.config)
    values = [0.0]*len(specs)
    by_world, metadata = {}, {'mask_checks': 0, 'excluded_ticks': 0,
                             'allowed_ticks': 0, 'fallback_worlds': 0,
                             'max_geometry_margin': 0.0}
    for target_id, world in worlds.items():
        local = [s for s in specs if s.target == target_id]
        keys = sorted({(k, role) for s in local for k, role in zip(s.robots, s.roles)})
        lookup = {key: i for i, key in enumerate(keys)}
        indices = np.asarray([[lookup[key] for key in zip(s.robots, s.roles)] for s in local])
        offsets = np.asarray([role_offset(role, obs.config) for _, role in keys])
        initial = np.asarray([obs.positions[k] for k, _ in keys])
        sample_bounds = []
        for sample in range(len(world.paths)):
            grid = world.grid(sample)
            rewards = reward_grid(obs, world, sample)
            allowed = np.broadcast_to(grid.legal[:, None], (len(grid.times), len(local))).copy()
            if synchronous:
                margin = geometric_margin(obs, grid)
                if math.isfinite(margin):
                    metadata['max_geometry_margin'] = max(metadata['max_geometry_margin'], margin)
                    anchors = grid.positions[:, None, :]+offsets[None, :, :]
                    distance = np.linalg.norm(initial[None, :, :]-anchors, axis=-1)
                    reach = (distance <= (obs.config.max_speed*(grid.times-obs.time)+
                                               obs.config.capture_radius+margin)[:, None])
                    joint = reach[:, indices].all(axis=2)
                    metadata['mask_checks'] += int(distance.size)
                    metadata['excluded_ticks'] += int(np.sum(allowed & ~joint))
                    allowed &= joint
                else:
                    metadata['fallback_worlds'] += 1
            metadata['allowed_ticks'] += int(allowed.sum())
            scores = np.max(np.where(allowed, rewards[:, None], -np.inf), axis=0)
            scores = np.where(np.isfinite(scores), scores, 0.0)
            sample_bounds.append(scores)
        rows = np.asarray(sample_bounds)
        by_world[target_id] = rows
        for i, spec in enumerate(local):
            values[spec.index] = (0.0 if np.all(rows[:, i] == 0.) else
                                  float(np.nextafter(np.mean(rows[:, i]), np.inf)))
    return Bounds(values, by_world, metadata)

