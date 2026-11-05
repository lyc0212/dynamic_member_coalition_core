"""Independent risk-event adapters; production policies and allocators stay frozen."""
from __future__ import annotations

from pursuit_v2.service import reject_service

import time
from pursuit_v2.policies import Decision, Policy, incumbent_risks
from pursuit_v2.types import IDLE
from .lazy_allocation import allocate
from .worlds import validate_model


STRATEGIES = ('risk_event', 'shared_event', 'quality_event', 'risk_local')


class QualityEventPolicy:
    def __init__(self, mode):
        if mode not in ('shared_event', 'quality_event'):
            raise ValueError('Unknown research policy')
        self.mode = mode
        self.method = 'M1' if mode == 'shared_event' else 'M3'
        self.last_replan_stage = -10**9
        self.last_global_fallback_stage = -10**9

    def decide(self, obs):
        reject_service(obs.config)
        start = time.perf_counter()
        validate_model(obs)
        if not obs.targets:
            return Decision((IDLE,)*obs.config.robots, {
                'replanned': False, 'reasons': ['no_active_tasks'],
                'candidate_count': 0, 'selected': [], 'prediction_seconds': 0.,
                'solver_seconds': 0., 'trigger_seconds': 0.,
                'decision_seconds': time.perf_counter()-start, 'risk_checked': False,
                'allocation_cpu_seconds': 0., 'allocation_wall_seconds': 0.,
                'wall_breakdown_available': True})
        reasons, reports, risky = [], [], ()
        risk_checked = False
        if obs.stage == 0 and obs.time == 0:
            reasons.append('initial')
        if obs.new_ids:
            reasons.append('birth')
        if obs.ended_ids:
            reasons.append('task_ended')
        if obs.stage-self.last_replan_stage >= obs.config.max_plan_age:
            reasons.append('max_plan_age')
        if not reasons:
            risk_checked = True
            reports, risky = incumbent_risks(obs)
            reasons.extend(f'low_joint_success:{i}' for i in risky)
        triggered = time.perf_counter()
        log = dict(replanned=bool(reasons), reasons=reasons or ['maintain'],
                   trigger_seconds=triggered-start, risk_checked=risk_checked,
                   incumbent_risks=reports)
        if reasons:
            allocation_start = time.perf_counter()
            actions, detail = allocate(obs, self.method, epsilon=0., budget=None)
            allocation_wall = time.perf_counter()-allocation_start
            if not detail['accuracy_met'] or detail['stop_reason'] != 'accuracy':
                raise ArithmeticError('Unbudgeted epsilon=0 allocation did not converge')
            log.update(detail)
            # Existing scientific allocator measures CPU components, not wall components.
            # The research runner accepts nullable unmeasured wall fields explicitly.
            log.update(prediction_seconds=None, solver_seconds=None,
                       wall_breakdown_available=False, solver='exact_dyadic',
                       allocation_cpu_seconds=detail['cpu_seconds'],
                       allocation_wall_seconds=allocation_wall)
            self.last_replan_stage = obs.stage
        else:
            actions = obs.assignment
            log.update(candidate_count=0, selected=[], prediction_seconds=0.,
                       solver_seconds=0., solver='exact_dyadic',
                       allocation_cpu_seconds=0., allocation_wall_seconds=0.,
                       wall_breakdown_available=True)
        log['decision_seconds'] = time.perf_counter()-start
        return Decision(actions, log)


def make_policy(mode):
    if mode not in STRATEGIES:
        raise ValueError('Unknown closed-loop study policy')
    return (Policy(mode) if mode in ('risk_event', 'risk_local')
            else QualityEventPolicy(mode))


def trigger_state(policy):
    return dict(last_replan_stage=policy.last_replan_stage,
                last_global_fallback_stage=policy.last_global_fallback_stage)
