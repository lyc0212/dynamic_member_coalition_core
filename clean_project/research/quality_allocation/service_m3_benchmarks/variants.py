"""Common request contract; independent/full/shared/lazy research adapters."""
import math
import time
from research.quality_allocation.service_m3_angular.worlds import public_request
from research.quality_allocation.service_m3_angular.model import candidates
from research.quality_allocation.service_m3_angular.reference import benefit, mean_score
from research.quality_allocation.service_m3_angular.additive import dp, assignment
from pursuit_v2.service import rollout_fixed_service, DT
from .shared import SharedEvaluator
from .lazy import lazy


def independent(case,spec):
    rows=[]; count=0
    for w in range(len(case.worlds)):
        path=case.path(w,spec.target)
        r=rollout_fixed_service(case.obs.config,path,case.obs.positions[list(spec.robots)],
            tuple(zip(spec.robots,spec.roles)),case.obs.time,case.until,
            dict(case.obs.service_states)[spec.target],trace=False)
        stop=r.completion_time if r.completion_time is not None else (
            r.escape_time if r.escape_time is not None else case.until)
        count+=max(0,math.ceil((stop-case.obs.time)/DT-1e-8))*len(spec.robots)
        rows.append((r,benefit(case,path,r.completion_time,r.effort)))
    return rows,count


def solve(obs,method,budget=None):
    if method not in ('F0','F1','L0','L1'): raise ValueError('Unknown mechanism')
    begin=time.process_time_ns(); case=public_request(obs); specs=candidates(case)
    setup=time.process_time_ns()-begin
    if method.startswith('L'):
        result=lazy(case,specs,budget=budget,bound_kind=method)
    else:
        if budget is not None: raise ValueError('Full evaluation has no batch budget')
        begin=time.process_time_ns(); count=0
        ev=SharedEvaluator(case,specs) if method=='F1' else None
        scores=[]
        for spec in specs:
            if ev: rows=ev.one(spec)
            else:
                rows,n=independent(case,spec); count+=n
            scores.append(mean_score(rows))
        eval_ns=time.process_time_ns()-begin
        begin=time.process_time_ns(); selected,L=dp(case,specs,scores)
        result=dict(selected=selected,L=L,U=L,known=scores,total=len(specs),exact=len(specs),
            components=len(ev.components) if ev else 0,component_cache_hits=ev.cache_hits if ev else 0,
            robot_control_substeps=ev.control_substeps if ev else count,dp_calls=1,
            full_target_batches=0,partial_incumbents=[],accuracy_met=True,stop_reason='accuracy',
            bound_cpu_ns=0,evaluation_cpu_ns=eval_ns,dp_cpu_ns=time.process_time_ns()-begin)
    actions=assignment(case,tuple(specs[i].key for i in result['selected']))
    result.update(method=method,setup_cpu_ns=setup,actions=[a.to_dict() for a in actions],
        observation_identity=case.observation_identity,request_identity=case.identity,
        dp_state_expansions='not_measured',candidate_count=len(specs),budget=budget)
    return result
