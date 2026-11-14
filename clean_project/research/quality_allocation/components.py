"""Independent TRAVEL components, with reference-order coalition reductions."""
from __future__ import annotations

from pursuit_v2.service import reject_service

from dataclasses import dataclass
import math
import numpy as np

from pursuit_v2.allocation import Candidate
from pursuit_v2.physics import Rollout, candidate_benefit, rollout_target
from pursuit_v2.risk import travel_certificate
from pursuit_v2.types import role_offset


@dataclass
class Evaluation:
    candidates: list
    rollouts: list
    scores: np.ndarray
    robot_control_substeps: int
    robot_position_updates: int
    components: int
    reused_component_requests: int


def _candidates(obs, world, specs, rollouts, scores):
    result = []
    for i, spec in enumerate(specs):
        captures = [r.capture_times[i] for r in rollouts if np.isfinite(r.capture_times[i])]
        result.append(Candidate(spec.target, spec.robots, spec.roles,
            float(np.mean([row[i] for row in scores])),
            float(np.mean(captures)) if captures else None, None,
            float(np.mean([r.effort[i] for r in rollouts])), (),
            float(np.mean([np.isfinite(r.capture_times[i]) and
                           r.capture_times[i] <= world.target.deadline+1e-10 for r in rollouts])),
            float(np.mean([np.isfinite(r.capture_times[i]) for r in rollouts])),
            float(np.mean([r.partner_wait[i] for r in rollouts])),
            **{k: v for k, v in travel_certificate(obs, world.target, spec.robots, spec.roles).items()
               if k in ('certified_next_check', 'certified_on_time', 'speed_margin',
                        'endpoint_margin', 'escape_margin', 'capture_time_upper_bound')}))
    return result


def reference_evaluate(obs, world, specs, account=True):
    reject_service(obs.config)
    cfg = obs.config
    positions = np.asarray([obs.positions[list(s.robots)] for s in specs])
    offsets = np.asarray([[role_offset(role, cfg) for role in s.roles] for s in specs])
    rollouts, scores = [], []
    work, updates = 0, 0
    for sample, path in enumerate(world.paths):
        r = rollout_target(cfg, path, positions, offsets, np.ones(len(specs), bool),
                           obs.time, world.horizon)
        rollouts.append(r)
        scores.append(candidate_benefit(cfg, path, r, obs.time, world.horizon))
        if account:
            # The timed M0 skips this otherwise unnecessary second coordinate grid.
            grid = world.grid(sample)
            robots = len(specs[0].robots)
            work += max(0, len(grid.times)-1)*len(specs)*robots
            stops = np.where(np.isfinite(r.capture_times), r.capture_times,
                             np.minimum(grid.end, grid.escape))
            updates += int(np.sum(grid.times[:-1, None] < stops[None, :]-1e-10))*robots
    return Evaluation(_candidates(obs, world, specs, rollouts, scores), rollouts,
                      np.asarray(scores), work, updates, 0, 0)


def _component_arrays(obs, world, sample, keys):
    reject_service(obs.config)
    cfg, grid = obs.config, world.grid(sample)
    times = grid.times
    missing = [key for key in keys if (sample, key) not in world._components]
    work = 0
    if missing:
        offsets = np.asarray([role_offset(role, cfg) for _, role in missing])
        pos = np.array([obs.positions[k] for k, _ in missing], copy=True)
        positions = [pos.copy()]
        squares, speeds, ready_before = [], [], []
        ready_capture = []

        def capture_ready(at):
            anchor = grid.positions[at][None, :] + offsets
            return np.linalg.norm(pos-anchor, axis=-1) <= cfg.capture_radius+1e-10

        ready_capture.append(capture_ready(0))
        for step, (lo, hi) in enumerate(zip(times[:-1], times[1:])):
            anchor = grid.positions[step][None, :] + offsets
            ready_before.append(np.linalg.norm(pos-anchor, axis=-1) <= cfg.capture_radius)
            if grid.escape > lo+1e-10:
                command = grid.velocities[step] + cfg.travel_gain*(anchor-pos)
                speed = np.linalg.norm(command, axis=-1, keepdims=True)
                command *= np.minimum(1.0, cfg.max_speed/np.maximum(speed, 1e-15))
            else:
                command = np.zeros_like(pos)
            squares.append(command**2)
            speeds.append(np.linalg.norm(command, axis=-1))
            if grid.escape > lo+1e-10:
                pos += command*(hi-lo)
                work += len(missing)
            positions.append(pos.copy())
            ready_capture.append(capture_ready(step+1))
        arrays = {'positions': np.asarray(positions), 'squares': np.asarray(squares),
                  'speeds': np.asarray(speeds), 'ready_before': np.asarray(ready_before),
                  'ready_capture': np.asarray(ready_capture)}
        if len(times) == 1:
            arrays['squares'] = np.zeros((0, len(missing), 2))
            arrays['speeds'] = np.zeros((0, len(missing)))
            arrays['ready_before'] = np.zeros((0, len(missing)), bool)
        for i, key in enumerate(missing):
            world._components[(sample, key)] = {name: array[:, i].copy()
                                                for name, array in arrays.items()}
    combined = {name: np.stack([world._components[(sample, key)][name] for key in keys], axis=1)
                for name in ('positions', 'squares', 'speeds', 'ready_before', 'ready_capture')}
    return combined, work, len(missing)


def shared_evaluate(obs, world, specs):
    reject_service(obs.config)
    cfg = obs.config
    keys = sorted({(k, role) for s in specs for k, role in zip(s.robots, s.roles)})
    lookup = {key: i for i, key in enumerate(keys)}
    indices = np.asarray([[lookup[key] for key in zip(s.robots, s.roles)] for s in specs])
    count, robots = len(specs), len(specs[0].robots)
    rollouts, scores, work, computed = [], [], 0, 0
    for sample, path in enumerate(world.paths):
        grid = world.grid(sample)
        times = grid.times
        arrays, batch_work, new_components = _component_arrays(obs, world, sample, keys)
        work += batch_work
        computed += new_components
        ready_capture = arrays['ready_capture']
        joint = np.all(ready_capture[:, indices], axis=2) & grid.legal[:, None]
        any_capture = joint.any(axis=0)
        first = np.where(any_capture, joint.argmax(axis=0), len(times)-1)
        captures = np.where(any_capture, times[first], np.nan)
        escaped = np.where(~any_capture & (grid.escape <= grid.end+1e-10), grid.escape, np.nan)
        stop = np.where(any_capture, captures, np.minimum(grid.end, grid.escape))
        alive = (times[:-1, None] < stop[None, :]-1e-10)
        if len(times) > 1:
            # Contiguous [steps, candidates, robots, xy] gives exactly
            # the reference coalition reduction; cumsum retains step order.
            energy_steps = np.sum(np.ascontiguousarray(arrays['squares'][:, indices]),
                                  axis=(2, 3))*np.diff(times)[:, None]
            effort = np.cumsum(energy_steps*alive, axis=0)[-1]
            ready = arrays['ready_before'][:, indices]
            wait_steps = ready.sum(axis=2)*(~ready.all(axis=2))*alive*np.diff(times)[:, None]
            wait = np.cumsum(wait_steps, axis=0)[-1]
            peak = np.max(arrays['speeds'][:, indices].max(axis=2)*alive, axis=0)
        else:
            effort, wait, peak = np.zeros(count), np.zeros(count), np.zeros(count)
        final_indices = np.where(any_capture, first,
            np.searchsorted(times, np.minimum(grid.end, grid.escape), side='left'))
        final_indices = np.clip(final_indices, 0, len(times)-1)
        final = arrays['positions'][final_indices[:, None], indices]
        r = Rollout(final, captures, escaped, effort, peak, wait,
                    np.full(count, np.nan), [], [], np.zeros(count, int))
        rollouts.append(r)
        scores.append(candidate_benefit(cfg, path, r, obs.time, world.horizon))
    return Evaluation(_candidates(obs, world, specs, rollouts, scores), rollouts,
                      np.asarray(scores), work, work, computed,
                      count*robots*len(world.paths)-computed)

