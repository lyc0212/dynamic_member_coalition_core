"""Research episode runner with the unchanged production online CPU boundary."""
from __future__ import annotations

from pursuit_v2.service import reject_service

import time
import numpy as np
from pursuit_v2.environment import TimedEnvironment
from pursuit_v2.io import clean_json
from pursuit_v2.scenario import scenario_hash
from pursuit_v2.timing import measured_decision, ONLINE_CPU_BOUNDARY
from pursuit_v2.types import complete_roles
from .serialization import serialize
from .candidates import identity
from .policy import make_policy, trigger_state


def percentiles(values):
    return dict(p90=float(np.quantile(values, .90)), p95=float(np.quantile(values, .95)),
                maximum=float(max(values))) if values else dict(p90=0., p95=0., maximum=0.)


def scientific(value):
    """Remove measurement diagnostics only; physical time and cost remain."""
    if isinstance(value, dict):
        return {k: scientific(v) for k, v in value.items()
                if (not k.endswith('_seconds') or k == 'partner_wait_robot_seconds') and k not in
                ('cpu_parts', 'cpu_tail', 'wall_tail', 'worker_pid', 'cpu_boundary')}
    if isinstance(value, (tuple, list)):
        return [scientific(v) for v in value]
    return value


def legal_assignment(obs, actions):
    if len(actions) != obs.config.robots:
        raise AssertionError('Assignment length')
    targets = {t.id: t for t in obs.targets}
    grouped = {}
    for a in actions:
        if a.target is None:
            if a.role != 'none':
                raise AssertionError('Invalid idle role')
            continue
        if a.target not in targets:
            raise AssertionError('Assignment to unavailable target')
        grouped.setdefault(a.target, []).append(a.role)
    for target, roles in grouped.items():
        if not complete_roles(targets[target], roles):
            raise AssertionError('Incomplete or illegal coalition')


def run_episode(cfg, scenario, mode, seed, heartbeat=None):
    reject_service(cfg)
    env, policy = TimedEnvironment(cfg, scenario), make_policy(mode)
    initial_policy = trigger_state(policy)
    rows = []
    wall_start = time.perf_counter()
    while not env.done:
        before = trigger_state(policy)
        obs, decision, cpu = measured_decision(env, policy)
        # All snapshots, validation, hashing and persistence are outside online timing.
        public = serialize(obs)
        legal_assignment(obs, decision.assignment)
        if any(t.turns or t.arc_rates for t in obs.targets):
            raise AssertionError('Private future in policy observation')
        result = env.step(decision.assignment, trace=False)
        expected_changes = sum(a != b for a, b in zip(obs.assignment, decision.assignment))
        if result.info['changed_robots'] != expected_changes:
            raise AssertionError('Environment change count differs from decision')
        log = dict(decision.log, **cpu)
        row = dict(public=public, public_id=identity(public), policy_before=before,
                   policy_after=trigger_state(policy), actions=[a.to_dict() for a in decision.assignment],
                   log=log, result=result.info, reward=result.reward)
        rows.append(clean_json(row))
        if heartbeat:
            heartbeat(len(rows), env.time, cfg.end_time, sum(r['log']['online_cpu_seconds'] for r in rows))
    metrics = env.metrics()
    if metrics['peak_speed'] > cfg.max_speed+1e-7 or metrics['model_mismatches']:
        raise AssertionError('Physical execution guard failed')
    metrics.update(online_cpu_seconds=sum(r['log']['online_cpu_seconds'] for r in rows),
        online_observation_cpu_seconds=sum(r['log']['online_observation_cpu_seconds'] for r in rows),
        online_policy_cpu_seconds=sum(r['log']['online_policy_cpu_seconds'] for r in rows),
        episode_wall_seconds=time.perf_counter()-wall_start,
        replans=sum(r['log']['replanned'] for r in rows),
        local_repairs=sum('repair_scope' in r['log'] for r in rows),
        global_fallbacks=sum(r['log'].get('fallback_global', False) for r in rows))
    if abs(metrics['online_cpu_seconds']-metrics['online_observation_cpu_seconds']-
           metrics['online_policy_cpu_seconds']) > 1e-8:
        raise AssertionError('Online CPU accounting identity failed')
    outcomes = [dict(target=t.id, status=env.status[t.id], capture_time=env.capture_times[t.id],
                     escape_time=env.escape_times[t.id]) for t in scenario.targets]
    record = clean_json(dict(seed=seed, policy=mode, scenario_sha256=scenario_hash(scenario),
        trajectories_id=identity([t.to_dict() for t in scenario.targets]),
        initial_policy_state=initial_policy, metrics=metrics, outcomes=outcomes, rows=rows,
        cpu_tail=percentiles([r['log']['online_cpu_seconds'] for r in rows]),
        wall_tail=percentiles([r['log']['decision_seconds'] for r in rows]),
        cpu_boundary=ONLINE_CPU_BOUNDARY))
    record['scientific_id'] = identity(scientific(record))
    return record
