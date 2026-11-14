"""Research-only target-batch lazy gate. No offline reference score input/cache."""
from fractions import Fraction
from .shared import SharedEvaluator
from .reference import mean_score
from .additive import dp
from .bounds import all_bounds


def lazy(case,specs,epsilon=0.,budget=None):
    from .domain import require_angular
    require_angular(case)
    import math
    from .model import check_specs
    check_specs(case,specs)
    if not math.isfinite(epsilon) or epsilon<0:
        raise ValueError('Negative quality gap')
    if budget is not None and (isinstance(budget,bool) or not isinstance(budget,int) or budget<0):
        raise ValueError('Budget is a nonnegative count of complete target batches')
    upper_values,detail=all_bounds(case,specs)
    known=[None]*len(specs)
    evaluator=SharedEvaluator(case)
    requests=[]; partial=[]; complete=set(); history=[]
    dp_calls=0

    def refine(j,indices,kind):
        batch=[specs[i] for i in indices if known[i] is None]
        if not batch:
            return
        rows=evaluator.evaluate(batch)
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
                stop_reason=stop_reason,known=known,bounds=upper_values,bound_details=detail)
