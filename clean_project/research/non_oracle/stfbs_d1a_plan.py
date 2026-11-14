from copy import deepcopy
from fractions import Fraction
from scripts.gq_windows.a0_plans import plans

def select(view,choice):
    rows=choice['rows'];base=0.
    for j in sorted({r['key']['target'] for r in rows}):base+=next(r['baseline'] for r in rows if r['key']['target']==j)
    options=[]
    for i,row in enumerate(rows):
        key=row['key']
        if key['target']!=1:continue
        actions=[dict(target=None,role='none') for _ in view['assignment']]
        for robot,role in zip(key['robots'],key['roles']):actions[robot]=dict(target=1,role=role)
        n=sum(a!=b for a,b in zip(actions,view['assignment']))
        score=Fraction(base)+Fraction(row['v'])-Fraction(view['config']['change_cost'])*n
        options.append(dict(actions=actions,selected=[i],score=score,mask=sum(1<<r for r in key['robots'])))
    if not options:raise ValueError('SWITCH_NOT_APPLICABLE')
    best=min(options,key=lambda p:(-p['score'],p['mask'],p['selected']))
    reference=plans(view,[r['key'] for r in rows],rows)
    legal=[p for p in reference if len(p['selected'])==1 and rows[p['selected'][0]]['key']['target']==1]
    expected=min(legal,key=lambda p:(-Fraction(p['exact_value']),sum(1<<r for r in rows[p['selected'][0]]['key']['robots']),p['selected']))
    if best['actions']!=expected['actions'] or best['score']!=Fraction(expected['exact_value']):raise ValueError('Constrained optimum audit')
    return dict(KEEP=deepcopy(view['assignment']),SWITCH=best['actions'],switch_score=str(best['score']),selected=best['selected'],legal_switch_count=len(legal),full_plan_count=len(reference),rule='D1A_FORCED_SWITCH_MASK_THEN_CANONICAL_INDEX_V1')
