"""Shared service accounting adapter for stage and timed environments."""
import math
import numpy as np

from .service import DT, TOL, rollout_fixed_service, tick
from .types import IDLE


def step_service(env, actions, trace):
    from .environment import StepResult
    cfg, start = env.cfg, env.time
    span = cfg.turn_interval if hasattr(env, "_time") else cfg.stage_dt
    end = min(cfg.end_time, start + span)
    old, active = env.clean_assignment(), env.active_ids
    changes = sum(a != b for a, b in zip(actions, old))
    before = env.positions.copy()
    results = {}
    # Prepare every result before mutating Environment (invalid inputs are atomic).
    for j in active:
        robots = [i for i, a in enumerate(actions) if a.target == j]
        team = tuple((i, actions[i].role) for i in robots)
        results[j] = (robots, rollout_fixed_service(
            cfg, env.scenario.targets[j], before[robots], team, start, end,
            env._service_states[j], trace=trace))
    completed, escaped, release, interruptions = [], [], [], []
    effort = peak = 0.0
    for j, (robots, result) in results.items():
        env.positions[robots] = result.positions
        env._service_states[j] = result.state
        env.service_progress[j] = result.state.progress
        env.service_team[j] = result.state.team
        effort += result.effort
        peak = max(peak, result.peak_speed)
        interruptions.extend(dict(event, target=j) for event in result.interruptions)
        if result.completion_time is not None:
            env.status[j] = "completed"
            env.completion_times[j] = result.completion_time
            completed.append(j)
            stop, reason = result.completion_time, "completed"
        elif result.escape_time is not None:
            env.status[j] = "escaped"
            env.escape_times[j] = result.escape_time
            escaped.append(j)
            stop, reason = result.escape_time, "escaped"
        else:
            continue
        if robots:
            release.append(dict(target=j, time=stop, reason=reason, robots=robots))
    flow = late = 0.0
    for j in active:
        target = env.scenario.targets[j]
        stop = (env.completion_times[j] if j in completed else
                env.escape_times[j] if j in escaped else end)
        flow += target.weight * max(0.0, stop - max(start, target.birth))
        late += target.weight * max(0.0, stop - max(start, target.birth, target.deadline))
    gain = sum(env.scenario.targets[j].weight for j in completed) / cfg.weight_reference
    components = dict(
        completion=gain, flow=-cfg.flow_weight * flow / (cfg.weight_reference * cfg.stage_dt),
        late=-cfg.late_weight * late / (cfg.weight_reference * cfg.stage_dt),
        effort=-cfg.control_weight * effort / cfg.effort_reference,
        terminal=-(cfg.unfinished_weight * sum(t.weight for t in env.scenario.targets
                    if env.status[t.id] != "completed") / cfg.weight_reference
                    if end >= cfg.end_time - TOL else 0.0))
    reward, cost = sum(components.values()), cfg.change_cost * changes
    env.total_reward += reward
    env.total_change_cost += cost
    env.total_changes += changes
    env.total_effort += effort
    env.peak_speed = max(env.peak_speed, peak)
    info = dict(stage=env.stage, start=start, end=end, visible_ids=list(active),
                new_ids=list(env.new_ids), assignment=[a.to_dict() for a in actions],
                coalition_changes=env._coalition_log(old, actions), changed_robots=changes,
                positions_start=before.tolist(), positions_end=env.positions.tolist(),
                completed=completed, escaped=escaped,
                completion_events=[dict(target=j, time=float(env.completion_times[j])) for j in completed],
                escape_events=[dict(target=j, time=float(env.escape_times[j])) for j in escaped],
                release_events=sorted(release, key=lambda e: (e['time'], e['reason'] != 'escaped', e['target'])),
                service_progress=env.service_progress.tolist(), interruptions=interruptions,
                flow=flow, late=late, effort=effort, peak_speed=peak, model_mismatches=0,
                reward=reward, change_cost=cost, reward_with_changes=reward-cost,
                reward_components=components)
    if trace:
        info['service_traces'] = {j: r.frames for j, (_, r) in results.items()}
        rows = {j: {tick(f['time']): f for f in r.frames if f['legal_check']}
                for j, (_, r) in results.items()}
        frames = []
        for n in range(tick(start), tick(end) + 1):
            positions = before.copy()
            progress = env.service_progress.copy()
            modes = ['IDLE'] * cfg.robots
            cumulative = 0.0
            for j, (robots, r) in results.items():
                f = rows[j][n]
                positions[robots] = np.asarray(f['positions']).reshape((-1, 2))
                progress[j] = f['progress']
                cumulative += f['effort']
                stop = r.completion_time if r.completion_time is not None else r.escape_time
                for i in robots:
                    modes[i] = 'HOLD' if stop is not None and n*DT >= stop-TOL else 'TRAVEL'
            frames.append(dict(time=n*DT, positions=positions.tolist(), modes=modes,
                               assignment=info['assignment'], service_progress=progress.tolist(),
                               effort=cumulative))
        info['frames'] = frames
    env.last_assignment = actions
    env.last_assignment = env.clean_assignment()
    env.ended_ids = tuple(completed + escaped)
    if hasattr(env, '_time'):
        env._time = end
        env.stage = min(cfg.max_stages, math.floor((end+TOL)/cfg.stage_dt))
    else:
        env.stage += 1
    env.new_ids = env._activate()
    return StepResult(float(reward), env.done, info)


def service_metrics(env):
    weights = np.array([t.weight for t in env.scenario.targets])
    done = np.isfinite(env.completion_times)
    escaped = np.isfinite(env.escape_times)
    on_time = done & (env.completion_times <= np.array([t.deadline for t in env.scenario.targets])+TOL)
    result = dict(return_with_changes=float(env.total_reward-env.total_change_cost),
                **{'return': float(env.total_reward)}, completion_rate=float(done.mean()),
                completed_count=int(done.sum()), escaped_count=int(escaped.sum()),
                weighted_on_time_rate=float(weights @ on_time / weights.sum()),
                unfinished_weight_fraction=float(weights @ (~done) / weights.sum()),
                escaped_weight_fraction=float(weights @ escaped / weights.sum()),
                control_effort=env.total_effort, peak_speed=env.peak_speed,
                assignment_changes=env.total_changes, capture_mode=env.cfg.capture_mode,
                service_progress=env.service_progress.tolist(),
                outcomes=[dict(target=j, status=('unfinished' if env.done and s == 'active' else s),
                               progress=float(env.service_progress[j]),
                               completion_time=float(env.completion_times[j]) if done[j] else None,
                               escape_time=float(env.escape_times[j]) if escaped[j] else None)
                          for j, s in enumerate(env.status)])
    if env.cfg.geometry_mode != 'legacy_anchor':
        from .observation_geometry import identity
        result['geometry_identity'] = identity(env.cfg)
    return result
