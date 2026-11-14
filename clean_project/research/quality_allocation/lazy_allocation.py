from __future__ import annotations

from pursuit_v2.service import reject_service

from dataclasses import asdict
from time import process_time, perf_counter

from pursuit_v2.allocation import allocate as native_allocate
from pursuit_v2.types import Assignment
from .candidates import enumerate_specs, actions_from, identity
from .worlds import freeze_worlds
from .components import reference_evaluate, shared_evaluate
from .bounds import construct_bounds
from .certified_solver import solve, objective, baseline, units, display


def allocate(obs, method='M3', epsilon=0.001, budget=None):
    """No oracle/state file inputs. Cache exists only within this call."""
    reject_service(obs.config)
    if method not in ('M0_native', 'M0', 'M1', 'M2', 'M3'):
        raise ValueError('Unknown method')
    if epsilon < 0 or (budget is not None and budget < 0):
        raise ValueError('Negative epsilon/budget')
    started = process_time()
    if method == 'M0_native':
        actions, log = native_allocate(obs, risk=True)
        elapsed = process_time()-started
        return actions, {'method': method, 'cpu_seconds': elapsed, 'native_log': log}
    parts = {k: 0.0 for k in ('setup', 'sampling', 'bounds', 'control_and_combine',
                              'dp', 'certificate')}
    mark = process_time()
    specs = enumerate_specs(obs)
    candidate_id = identity([s.key for s in specs])
    parts['setup'] += process_time()-mark
    mark = process_time()
    worlds, world_id = freeze_worlds(obs)
    parts['sampling'] += process_time()-mark
    mark = process_time()
    bound = construct_bounds(obs, worlds, specs, method == 'M3') if method in ('M2', 'M3') else None
    parts['bounds'] += process_time()-mark
    values = [None]*len(specs)
    exact, evaluations, history = {}, {}, []
    work, updates, components, reuse, dp_calls = 0, 0, 0, 0, 0
    lower, upper, incumbent = baseline(obs), None, ()

    def refine(target_id, subset=None):
        nonlocal work, updates, components, reuse
        local = [s for s in specs if s.target == target_id] if subset is None else subset
        mark = process_time()
        evaluated = (reference_evaluate(obs, worlds[target_id], local, account=False)
                     if method == 'M0' else shared_evaluate(obs, worlds[target_id], local))
        parts['control_and_combine'] += process_time()-mark
        for spec, candidate in zip(local, evaluated.candidates):
            values[spec.index] = candidate.benefit
            exact[spec.index] = candidate
            if bound is not None and candidate.benefit > bound.values[spec.index]:
                raise ArithmeticError('Candidate upper bound violated')
        evaluations[target_id] = evaluated
        work += evaluated.robot_control_substeps
        updates += evaluated.robot_position_updates
        components += evaluated.components
        reuse += evaluated.reused_component_requests

    def timed_solve(scores):
        nonlocal dp_calls
        mark = process_time()
        answer = solve(obs, specs, scores)
        parts['dp'] += process_time()-mark
        dp_calls += 1
        return answer

    if method in ('M0', 'M1'):
        for target_id in worlds:
            refine(target_id)
        incumbent, lower = timed_solve(values)
        upper = lower
        reason = 'accuracy'
    else:
        # All-idle is exact, including charges for released incumbent robots.
        # Incumbent-first target batches are skipped if setup has spent the budget.
        for target_id in worlds:
            local = [s for s in specs if s.target == target_id]
            present = [s for s in local if all(obs.assignment[k] == Assignment(s.target, role)
                                             for k, role in zip(s.robots, s.roles))]
            if present and (budget is None or process_time()-started < budget):
                refine(target_id, present)
        previous_upper = None
        while True:
            optimistic = [values[i] if values[i] is not None else bound.values[i]
                          for i in range(len(specs))]
            plan, upper_now = timed_solve(optimistic)
            feasible, lower_now = timed_solve(values)
            if lower_now > lower:
                incumbent, lower = feasible, lower_now
            upper = upper_now if previous_upper is None else min(previous_upper, upper_now)
            if upper < lower:
                raise ArithmeticError('Inverted quality bounds')
            history.append({'lower_units': str(lower), 'upper_units': str(upper),
                            'evaluated': len(exact)})
            previous_upper = upper
            if upper-lower <= units(epsilon):
                reason = 'accuracy'
                break
            if budget is not None and process_time()-started >= budget:
                reason = 'budget'
                break
            pending = sorted({specs[i].target for i in plan if values[i] is None})
            if not pending:
                reason = 'numerical_limit'
                break
            # One target batch per DP update; sharing still serves all its candidates.
            refine(pending[0])
    mark = process_time()
    actions = actions_from(specs, incumbent, obs.config.robots)
    gap = upper-lower
    log = {'method': method, 'candidate_id': candidate_id, 'world_id': world_id,
           'candidate_count': len(specs), 'selected_indices': list(incumbent),
           'selected': [exact[i].to_dict() for i in incumbent],
           'lower_units': str(lower), 'upper_units': str(upper), 'binary_exponent': -1074,
           'L_safe_display': display(lower, -1), 'U_safe_display': display(upper, 1),
           'gap_safe': display(gap, 1), 'epsilon': epsilon, 'accuracy_met': gap <= units(epsilon),
           'stop_reason': reason, 'fully_evaluated': len(exact) == len(specs),
           'exact_candidate_count': len(exact), 'targets_refined': len(evaluations),
           'components': components, 'reused_component_requests': reuse,
           'component_cache_bytes': sum(array.nbytes for world in worlds.values()
               for component in world._components.values() for array in component.values()),
           'robot_control_substeps': work, 'robot_position_updates': updates,
           'dp_calls': dp_calls, 'history': history,
           'bound_metadata': bound.metadata if bound else None,
           'numeric_contract': 'reference-order binary64 scores; exact dyadic joint objective'}
    parts['certificate'] += process_time()-mark
    log['cpu_parts'] = parts
    log['cpu_seconds'] = process_time()-started
    log['budget_seconds'] = budget
    log['budget_overrun'] = max(0.0, log['cpu_seconds']-budget) if budget is not None else 0.0
    return actions, log

