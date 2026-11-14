"""Independent finite-table checks. No selector or physical simulation imports."""
from fractions import Fraction
from itertools import combinations, permutations, product
import math

ROLES = ('dual_neg45', 'dual_pos45')

def catalogue(checkpoint):
    result = []
    for target in checkpoint['targets']:
        if target['required_robots'] != 2:
            raise ValueError('A0 supports q2 only')
        for robots in combinations(range(checkpoint['config']['robots']), 2):
            for roles in permutations(ROLES):
                result.append(dict(target=target['id'], robots=list(robots), roles=list(roles)))
    return result

def plans(checkpoint, keys, rows):
    if keys != catalogue(checkpoint) or len(rows) != len(keys):
        raise ValueError('Incomplete canonical catalogue')
    baselines = {}
    for key, row in zip(keys, rows):
        for field in ('absolute_O', 'baseline', 'v'):
            if type(row[field]) is not float or not math.isfinite(row[field]):
                raise ValueError('Expected finite binary64')
        if row['v'].hex() != float(row['absolute_O']-row['baseline']).hex():
            raise ValueError('Increment arithmetic')
        old = baselines.setdefault(key['target'], row['baseline'])
        if old.hex() != row['baseline'].hex():
            raise ValueError('Inconsistent baseline')
    base = 0.0
    for target in sorted(baselines):
        base += baselines[target]
    choices = [[None]+[i for i,k in enumerate(keys) if k['target']==t['id']]
               for t in checkpoint['targets']]
    result = []
    for option in product(*choices):
        selected = [i for i in option if i is not None]
        robots = [r for i in selected for r in keys[i]['robots']]
        if len(robots) != len(set(robots)):
            continue
        actions = [dict(target=None, role='none') for _ in checkpoint['positions']]
        for i in selected:
            for robot,role in zip(keys[i]['robots'],keys[i]['roles']):
                actions[robot] = dict(target=keys[i]['target'],role=role)
        changes = sum(a != b for a,b in zip(actions,checkpoint['assignment']))
        value = Fraction.from_float(base)+sum((Fraction.from_float(rows[i]['v']) for i in selected),Fraction())-Fraction.from_float(checkpoint['config']['change_cost'])*changes
        result.append(dict(selected=selected,actions=actions,changes=changes,exact_value=str(value)))
    return result

def check_saved(expected, saved):
    def key(plan):
        if set(plan) != {'selected','actions','changes','exact_value'}:
            raise ValueError('Unknown plan fields')
        return tuple(plan['selected'])
    left = {key(p):p for p in expected}
    right = {key(p):p for p in saved}
    if len(right)!=len(saved) or left!=right:
        raise ValueError('Plan coverage or values differ')

def competition(checkpoint, keys, rows):
    table = plans(checkpoint,keys,rows)
    idle = Fraction(next(p['exact_value'] for p in table if not p['selected']))
    margins = {}
    for target in checkpoint['targets']:
        values = [Fraction(p['exact_value']) for p in table if len(p['selected'])==1 and keys[p['selected'][0]]['target']==target['id']]
        margins[str(target['id'])] = str(max(values)-idle) if values else None
    exclusive=len(margins)==2 and not any(len(p['selected'])==2 for p in table)
    return dict(margins=margins,resource_exclusive=exclusive,activated=exclusive and all(v is not None and Fraction(v)>0 for v in margins.values()))

def canonical_choice(checkpoint, keys, rows, table):
    """Replay frozen tie priority using Fractions, checked against enumeration.

    This is an independent receipt checker, not an import of production solve.
    Mask insertion order matters to later equal-score transitions.
    """
    idle=next(p for p in table if not p['selected'])
    base=Fraction(idle['exact_value']);states={0:(base,())}
    cost=Fraction.from_float(checkpoint['config']['change_cost'])
    assignment=checkpoint['assignment']
    for target in sorted({k['target'] for k in keys}):
        prior=list(states.items());updated=dict(states)
        for i,k in enumerate(keys):
            if k['target']!=target:continue
            delta=sum(int(assignment[r]!=dict(target=None,role='none'))-int(assignment[r]!=dict(target=target,role=role)) for r,role in zip(k['robots'],k['roles']))
            gain=Fraction.from_float(rows[i]['v'])+cost*delta
            if gain<=0:continue
            used=sum(1<<r for r in k['robots'])
            for occupied,(value,chosen) in prior:
                if occupied&used:continue
                mask=occupied|used;score=value+gain
                if mask not in updated or score>updated[mask][0]:updated[mask]=(score,chosen+(i,))
        states=updated
    best=min(states,key=lambda mask:(-states[mask][0],mask))
    chosen=list(states[best][1])
    optimum=max(Fraction(p['exact_value']) for p in table)
    if states[best][0]!=optimum:raise ValueError('Tie replay differs from exhaustive optimum')
    return chosen

def verify_selection(checkpoint,keys,rows,saved):
    table=plans(checkpoint,keys,rows);check_saved(table,saved['independent_plans'])
    optimum=max(Fraction(p['exact_value']) for p in table)
    selected=canonical_choice(checkpoint,keys,rows,table)
    plan=next(p for p in table if p['selected']==selected)
    expectations=dict(legal_plan_count=len(table),tied_optima=sum(Fraction(p['exact_value'])==optimum for p in table),exact_table_value=str(optimum),selected_indices=selected,actions=plan['actions'],assignment_change_count=plan['changes'])
    for field,value in expectations.items():
        if type(saved[field]) is not type(value) or saved[field]!=value:raise ValueError('Selection mismatch: '+field)
    baseline=0.
    for target in sorted({k['target'] for k in keys}):baseline+=next(r['baseline'] for k,r in zip(keys,rows) if k['target']==target)
    if saved['B64'].hex()!=baseline.hex():raise ValueError('Selection mismatch: B64')
    dual=len(checkpoint['positions'])==3 and len(checkpoint['targets'])==2 and all(t['required_robots']==2 for t in checkpoint['targets'])
    structural=dual and len(keys)==12 and len(table)==13 and all(len(p['selected'])<=1 for p in table)
    return dict(status='PASS',legal_plan_count=len(table),exact_optimum=str(optimum),tied_optima=expectations['tied_optima'],selected_indices=selected,structural_competition=structural,competition=competition(checkpoint,keys,rows))
