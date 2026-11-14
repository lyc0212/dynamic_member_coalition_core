# Isolated research driver: same lazy order/DP; interchangeable bounds and lightweight traces.
"""Research-only target-batch lazy gate. No offline reference score input/cache."""
from fractions import Fraction
from .shared import SharedEvaluator
from research.quality_allocation.service_m3_angular.reference import mean_score
from research.quality_allocation.service_m3_angular.additive import dp as production_dp
from .bounds import all_bounds


def lazy(case,specs,epsilon=0.,budget=None,*,bound_kind="L1"):
    import time
    dp_cpu_ns=0
    evaluation_cpu_ns=0
    def dp(*args):
        nonlocal dp_cpu_ns
        start=time.process_time_ns()
        value=production_dp(*args)
        dp_cpu_ns+=time.process_time_ns()-start
        return value
    from research.quality_allocation.service_m3_angular.domain import require_angular
    require_angular(case)
    import math
    if not math.isfinite(epsilon) or epsilon<0:
        raise ValueError('Negative quality gap')
    if budget is not None and (isinstance(budget,bool) or not isinstance(budget,int) or budget<0):
        raise ValueError('Budget is a nonnegative count of complete target batches')
    bound_start=time.process_time_ns()
    upper_values,detail=all_bounds(case,specs,bound_kind)
    bound_cpu_ns=time.process_time_ns()-bound_start
    known=[None]*len(specs)
    evaluator=SharedEvaluator(case,specs)
    requests=[]; partial=[]; complete=set(); history=[]
    dp_calls=0

    def refine(j,indices,kind):
        nonlocal evaluation_cpu_ns
        batch=[specs[i] for i in indices if known[i] is None]
        if not batch:
            return
        eval_start=time.process_time_ns()
        rows=evaluator.evaluate(batch)
        evaluation_cpu_ns+=time.process_time_ns()-eval_start
        for spec in batch:
            value=mean_score(rows[spec.index])
            if value>upper_values[spec.index]:
                raise ArithmeticError('Service upper bound violated during lazy evaluation')
            known[spec.index]=value
        requests.append(dict(target=j,kind=kind,candidates=[s.index for s in batch]))
        if kind=='incumbent':
            partial.extend(s.index for s in batch)
        if all(known[s.index] is not None for s in specs if s.target==j):
            complete.add(j)

    for spec in specs:
        if all(case.obs.assignment[i].target==spec.target and case.obs.assignment[i].role==r
               for i,r in zip(spec.robots,spec.roles)):
            refine(spec.target,[spec.index],'incumbent')
    previous_upper=None
    full_batches=0
    stop_reason='accuracy'
    for _ in range(len(specs)+1):
        optimistic=[v if v is not None else upper_values[i] for i,v in enumerate(known)]
        upper_plan,U=dp(case,specs,optimistic)
        selected,L=dp(case,specs,known)
        dp_calls+=2
        U=U if previous_upper is None else min(previous_upper,U)
        if U<L:
            raise ArithmeticError('Inverted service certificate')
        history.append(dict(L=str(L),U=str(U),gap=str(U-L),exact=sum(v is not None for v in known)))
        previous_upper=U
        if U-L<=Fraction.from_float(float(epsilon)):
            break
        if budget is not None and full_batches>=budget:
            stop_reason='budget'
            break
        pending=sorted({specs[i].target for i in upper_plan if known[i] is None})
        if not pending:
            raise ArithmeticError('No refinable optimistic candidate')
        for j in pending[:1]:
            refine(j,[s.index for s in specs if s.target==j],'target_batch')
            full_batches+=1
    else:
        raise ArithmeticError('Lazy did not terminate')
    return dict(selected=selected,L=L,U=U,history=history,exact=sum(v is not None for v in known),
                total=len(specs),full_targets=sorted(complete),partial_incumbents=partial,
                requests=requests,components=len(evaluator.components),
                robot_control_substeps=evaluator.control_substeps,dp_calls=dp_calls,
                component_cache_hits=evaluator.cache_hits,full_target_batches=full_batches,budget=budget,
                accuracy_met=U-L<=Fraction.from_float(float(epsilon)),
                stop_reason=stop_reason,known=known,bounds=upper_values,bound_details=detail,
                bound_cpu_ns=bound_cpu_ns,evaluation_cpu_ns=evaluation_cpu_ns,dp_cpu_ns=dp_cpu_ns)
