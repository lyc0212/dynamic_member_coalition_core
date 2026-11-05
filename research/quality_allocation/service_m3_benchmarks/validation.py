"""Offline, excluded from all measured solve CPU and Lazy query counts."""
from fractions import Fraction
from dataclasses import asdict
import math
import time
import numpy as np
from pursuit_v2.service_m3 import make_service_m3_policy
from research.quality_allocation.service_m3_angular.model import candidates
from research.quality_allocation.service_m3_angular.worlds import public_request
from research.quality_allocation.service_m3_angular.reference import evaluate,mean_score,physical_baseline
from research.quality_allocation.service_m3_angular.shared import SharedEvaluator as OriginalShared
from research.quality_allocation.service_m3_angular.additive import independent_plans,assignment
from research.quality_allocation.service_m3_angular.lazy import lazy as original_lazy
from .shared import SharedEvaluator
from .bounds import all_bounds
from .variants import solve,independent
from .fixtures import restore,digest


def check_case(case,with_policy=False):
    specs=candidates(case); lightweight=SharedEvaluator(case,specs); old=OriginalShared(case)
    values=[]; world_scores=[]
    for s in specs:
        ref=evaluate(case,s); lean,_=independent(case,s)
        shared=lightweight.one(s); original=old.one(s)
        for a,b,c,d in zip(ref,lean,shared,original):
            assert a[1].hex()==b[1].hex()==c[1].hex()==d[1].hex(),(case.name,s.index,'score')
            for row in (b,c,d):
                assert a[0].completion_time==row[0].completion_time
                assert a[0].escape_time==row[0].escape_time
                assert a[0].effort.hex()==row[0].effort.hex()
                assert a[0].state==row[0].state
                assert np.array_equal(a[0].positions,row[0].positions)
                assert a[0].termination_reason==row[0].termination_reason
        values.append(mean_score(ref));world_scores.append([v for _,v in ref])
    loose,ld=all_bounds(case,specs,'L0'); clock,cd=all_bounds(case,specs,'L1')
    for s,v in zip(specs,values):
        assert v<=clock[s.index]<=loose[s.index]
        for w,value in enumerate(world_scores[s.index]):
            assert value<=cd[s.index][w]['value']<=ld[s.index][w]['value']
    upper=math.prod(1+math.perm(case.obs.config.robots,t.required_robots) for t in case.obs.targets)
    if upper>30000: raise RuntimeError('Independent Cartesian cap exceeded; no truncation')
    scores={s.key:Fraction.from_float(v) for s,v in zip(specs,values)}
    baseline=Fraction.from_float(float(physical_baseline(case))); fee=Fraction.from_float(case.obs.config.change_cost)
    optimum=None; legal=0
    # independent_plans builds combinations/permutations itself, never uses DP plans.
    for keys in independent_plans(case):
        actions=assignment(case,keys)
        cost=fee*sum(a!=b for a,b in zip(actions,case.obs.assignment))
        value=baseline+sum((scores[k] for k in keys),Fraction())-cost
        legal+=1
        if optimum is None or value>optimum: optimum=value
    for kind in ('L0','L1'):
        from .lazy import lazy
        for budget in (None,0,1,2):
            r=lazy(case,specs,budget=budget,bound_kind=kind)
            assert r['L']<=optimum<=r['U']
            selected=tuple(specs[i].key for i in r['selected'])
            actions=assignment(case,selected)
            actual=baseline+sum((scores[k] for k in selected),Fraction())-fee*sum(a!=b for a,b in zip(actions,case.obs.assignment))
            assert actual==r['L']
            assert all(r['known'][i] is not None for i in r['selected'])
            if budget is None: assert r['L']==r['U']==optimum
            if kind=='L1':
                orig=original_lazy(case,specs,budget=budget)
                for key in ('L','U','selected','exact','full_target_batches','partial_incumbents','requests'):
                    assert orig[key]==r[key],(case.name,key)
    if with_policy:
        for method in ('F0','F1','L0','L1'):
            r=solve(case.obs,method); assert r['L']==r['U']==optimum
        policy=make_service_m3_policy('M3_service_angular_v1').decide(case.obs)
        assert Fraction(policy.log['certificate']['L'])==optimum
    return dict(candidates=len(specs),world_candidate_pairs=len(specs)*len(case.worlds),
                cartesian_upper=upper,legal_plans=legal,Jstar=str(optimum),
                candidate_manifest=[dict(**asdict(s),mask=s.mask) for s in specs],
                candidate_manifest_sha256=digest([dict(**asdict(s),mask=s.mask) for s in specs]),
                world_manifest_sha256=digest([[p.to_dict() for p in w] for w in case.worlds]),
                values_hex=[v.hex() for v in values],passed=True)


def validate_main(rows):
    results=[]
    for row in rows:
        case=public_request(restore(row['observation']))
        assert len(candidates(case))==row['expected_candidates']
        result=check_case(case,with_policy=True); result['id']=row['id']; results.append(result)
        print('Correctness passed:',row['id'],flush=True)
    return results
