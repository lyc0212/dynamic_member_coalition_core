"""C: exact dyadic table optimization and independently generated joint choices."""
from fractions import Fraction
from itertools import combinations, product, permutations

from pursuit_v2.types import Assignment,IDLE
from research.quality_allocation.certified_solver import solve,SCALE
from .reference import physical_baseline

Q = Fraction.from_float


def independent_plans(case):
    from .domain import require_angular
    require_angular(case)
    """No candidate generator/DP outputs define this Cartesian search space."""
    choices=[]
    for target in case.obs.targets:
        options=[None]
        for group in combinations(range(case.obs.config.robots),target.required_robots):
            # Independent explicit role catalog, not production candidate generation.
            catalog={1:('solo_0',),2:('dual_neg45','dual_pos45'),3:('tri_0','tri_120','tri_240')}
            rolesets=list(permutations(catalog[target.required_robots]))
            options.extend((target.id,group,roles) for roles in rolesets)
        choices.append(options)
    for plan in product(*choices):
        selected=tuple(c for c in plan if c is not None)
        identities=[i for _,robots,_ in selected for i in robots]
        if len(identities)==len(set(identities)):
            yield selected


def assignment(case, keys):
    from .domain import require_angular
    require_angular(case)
    actions=[IDLE]*case.obs.config.robots
    for target,robots,roles in keys:
        for i,r in zip(robots,roles):
            if actions[i]!=IDLE:
                raise ValueError('Conflicting robots')
            actions[i]=Assignment(target,r)
    return tuple(actions)


def table_value(case, keys, scores):
    from .domain import require_angular
    require_angular(case)
    actions=assignment(case,keys)
    changes=sum(a!=b for a,b in zip(actions,case.obs.assignment))
    return Q(float(physical_baseline(case)))+sum((Q(float(scores[k])) for k in keys),Fraction())-Q(case.obs.config.change_cost)*changes


def enumerate_optimum(case, specs, values):
    from .domain import require_angular
    require_angular(case)
    scores={s.key:v for s,v in zip(specs,values)}
    rows=[]
    for keys in independent_plans(case):
        rows.append((keys,table_value(case,keys,scores)))
    keys,value=max(rows,key=lambda r:r[1])
    return keys,value,rows


def dp(case,specs,values):
    from .domain import require_angular
    require_angular(case)
    selected,units=solve(case.obs,specs,values)
    value=Q(float(physical_baseline(case)))+Fraction(units,SCALE)
    return selected,value
