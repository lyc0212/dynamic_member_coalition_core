"""Ordered A/B/C/D audits. Later gates execute only after earlier assertions pass."""
from dataclasses import asdict
from fractions import Fraction
import numpy as np
from pursuit_v2.types import role_offset
from pursuit_v2.service import DT,TOL,tick
from .fixtures import candidates
from .reference import evaluate,mean_score,environment_value,physical_baseline
from .additive import independent_plans,table_value,enumerate_optimum,dp,Q
from .shared import SharedEvaluator
from .bounds import all_bounds
from .lazy_gate import lazy


def audit_a(cases):
    output=[]; references={}
    for case in cases:
        specs=candidates(case)
        rows={s.index:evaluate(case,s) for s in specs}
        scores={s.key:mean_score(rows[s.index]) for s in specs}
        by_key={s.key:s for s in specs}
        plans=[]; max_difference=0.
        for keys in independent_plans(case):
            predicted=table_value(case,keys,scores)
            actual,traces=environment_value(case,[by_key[k] for k in keys])
            difference=abs(float(predicted)-actual)
            assert difference<=1e-12,(case.name,keys,actual,float(predicted),difference)
            max_difference=max(max_difference,difference)
            plans.append(dict(keys=keys,table_value=str(predicted),environment_value=actual,
                              absolute_difference=difference,environment_steps=traces))
        references[case.name]=(specs,rows)
        output.append(dict(case=case.name,input_sha256=case.identity,baseline=physical_baseline(case),
                           max_accounting_difference=max_difference,legal_plans=len(plans),plans=plans,
                           candidates=[dict(spec=asdict(s),initial_state=asdict(dict(case.obs.service_states)[s.target]),
                                            world_id=case.identity,world_scores=[v for _,v in rows[s.index]],
                                            mean_score=scores[s.key],rollouts=[asdict(r) for r,_ in rows[s.index]])
                                       for s in specs]))
    return output,references


def audit_b(cases,references):
    output=[]
    for case in cases:
        specs,ref=references[case.name]
        evaluator=SharedEvaluator(case)
        shared=evaluator.evaluate(specs)
        differences=[]; completion_groups={}
        for spec in specs:
            for w,((actual,value),(expected,ref_value)) in enumerate(zip(shared[spec.index],ref[spec.index])):
                assert actual.completion_time==expected.completion_time
                assert actual.escape_time==expected.escape_time
                assert actual.state==expected.state
                assert actual.termination_reason==expected.termination_reason
                assert actual.interruptions==expected.interruptions
                assert len(actual.frames)==len(expected.frames)
                assert value==ref_value,(case.name,spec.index,w,'binary64 score mismatch',value,ref_value)
                max_position=max_energy=max_command=0.
                for a,b in zip(actual.frames,expected.frames):
                    assert (a['time'],a['valid'],a['legal_check'])==(b['time'],b['valid'],b['legal_check'])
                    assert a['progress']==b['progress']
                    max_position=max(max_position,float(np.max(np.abs(np.array(a['positions'])-b['positions']))))
                    max_energy=max(max_energy,abs(a['effort']-b['effort']))
                    if not b['legal_check']:
                        continue
                    stop=expected.completion_time if expected.completion_time is not None else expected.escape_time
                    at=b['time']
                    if at>=case.until-TOL or (stop is not None and at>=stop-TOL):
                        continue
                    path=case.path(w,spec.target)
                    pos=np.array(b['positions'])
                    offsets=np.array([role_offset(r,case.obs.config) for r in spec.roles])
                    command=path.velocity_at(at)+case.obs.config.travel_gain*(path.position(at)+offsets-pos)
                    speed=np.linalg.norm(command,axis=1)
                    command*=np.minimum(1.,case.obs.config.max_speed/np.maximum(speed,1e-15))[:,None]
                    k=tick(at)-tick(case.obs.time)
                    rebuilt=np.stack([evaluator.components[(w,spec.target,i,r)]['commands'][k]
                                      for i,r in zip(spec.robots,spec.roles)])
                    max_command=max(max_command,float(np.max(np.abs(command-rebuilt))))
                assert max(max_position,max_energy,max_command)<=1e-12
                differences.append(dict(candidate=spec.index,world=w,max_position=max_position,
                                        max_energy=max_energy,max_command=max_command,score_bitwise_equal=True))
                if actual.completion_time is not None:
                    for i,r in zip(spec.robots,spec.roles):
                        completion_groups.setdefault((w,spec.target,i,r),set()).add(actual.completion_time)
        varied=[dict(component=key,completion_times=sorted(v)) for key,v in completion_groups.items() if len(v)>1]
        output.append(dict(case=case.name,input_sha256=case.identity,comparisons=differences,
                           components=len(evaluator.components),robot_control_substeps=evaluator.control_substeps,
                           components_used_with_different_completion_times=varied,
                           component_data=[dict(key=k,**v) for k,v in evaluator.components.items()]))
    assert any(r['components_used_with_different_completion_times'] for r in output), 'No differing stop-prefix witness'
    return output


def audit_c(cases,references):
    output=[]; optima={}
    for case in cases:
        specs,rows=references[case.name]
        scores=[mean_score(rows[s.index]) for s in specs]
        keys,optimum,plans=enumerate_optimum(case,specs,scores)
        selected,solved=dp(case,specs,scores)
        assert solved==optimum
        chosen=tuple(specs[i].key for i in selected)
        mapping={s.key:v for s,v in zip(specs,scores)}
        assert table_value(case,chosen,mapping)==solved
        assert chosen in [p for p,_ in plans]
        optima[case.name]=optimum
        output.append(dict(case=case.name,input_sha256=case.identity,dp_selected=selected,
                           dp_value=str(solved),independent_optimum=str(optimum),independent_selected=keys,
                           plans=[dict(keys=k,value=str(v)) for k,v in plans]))
    return output,optima


def audit_d(cases,references,optima):
    output=[]
    for case in cases:
        specs,rows=references[case.name]
        upper,details=all_bounds(case,specs)
        margins=[]
        for spec in specs:
            for w,(_,score) in enumerate(rows[spec.index]):
                u=details[spec.index][w]['value']
                assert u>=score,(case.name,spec.index,w,u,score)
                margins.append(u-score)
            assert upper[spec.index]>=mean_score(rows[spec.index])
        # A fresh lazy evaluator has no access to the offline rows above.
        result=lazy(case,specs,epsilon=0.)
        optimum=optima[case.name]
        assert result['L']<=optimum<=result['U']
        for row in result['history']:
            assert Fraction(row['L'])<=optimum<=Fraction(row['U'])
        assert result['U']==result['L']==optimum
        assert len(set(i for q in result['requests'] for i in q['candidates']))==result['exact']
        if case.expectation=='skip':
            assert result['exact']<len(specs),'PREDEFINED skip_v1 did not skip; preserve this counterexample'
            assert any(mean_score(rows[s.index])>0 for s in specs)
        if case.expectation=='full':
            assert result['exact']==len(specs),'PREDEFINED full_v1 did not require full target batch'
        result['L'],result['U']=str(result['L']),str(result['U'])
        result['independent_optimum']=str(optimum)
        output.append(dict(case=case.name,input_sha256=case.identity,min_world_margin=min(margins),
                           lazy=result,offline_audit_candidates=len(specs),offline_audit_counted_in_lazy=False))
    return output
