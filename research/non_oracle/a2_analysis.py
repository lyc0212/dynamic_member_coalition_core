"""Per-cut scientific records, separate from policy inputs and objective."""
from fractions import Fraction
from scripts.gq_windows.a0_plans import plans, canonical_choice
from .belief import trajectory

def decision_evidence(view, choice, accepted_receipts):
    rows=choice['rows'];keys=[row['key'] for row in rows];table=plans(view,keys,rows)
    optimum=max(Fraction(p['exact_value']) for p in table)
    chosen=canonical_choice(view,keys,rows,table)
    selected=next(p for p in table if p['selected']==chosen)
    if Fraction(choice['exact_value'])!=optimum or choice['selected_indices']!=chosen or choice['actions']!=selected['actions']:
        raise ValueError('A2 choice disagrees with independent plan verification')
    idle=Fraction(next(p['exact_value'] for p in table if not p['selected']));targets=[]
    for a in view['targets']:
        j=a['id'];b=view['beliefs'][j];tick=view['tick'];last=b['last_observation_tick']
        candidates=[p for p in table if len(p['selected'])==1 and keys[p['selected'][0]]['target']==j]
        best=max(candidates,key=lambda p:Fraction(p['exact_value']))
        record=accepted_receipts.get(j) if last is not None else None
        if last is not None and (record is None or record['measurement_tick']!=last or record['available_tick']!=b['available_tick']):
            raise ValueError('A2 belief observation has no matching accepted receipt')
        p,v=trajectory(b,tick)
        first_visible=view['first_policy_visible_ticks'][j]
        if first_visible!=a['announcement_tick']:
            raise ValueError('A2 first policy visibility differs from announcement tick')
        targets.append(dict(target_id=j,birth_tick=round(a['birth']/.05),announcement_tick=a['announcement_tick'],first_policy_visible_tick=first_visible,initial_belief_tick=a['announcement_tick'],announcement_age_ticks=tick-a['announcement_tick'],last_observation_tick=last,observation_age_ticks=None if last is None else tick-last,last_available_tick=None if record is None else record['available_tick'],corresponding_consumed_tick=None if record is None else record['consumed_tick'],status=b['status'],source=b['source'],diagnostics=b['diagnostics'],frozen_position=p,frozen_velocity=v,best_single_target_plan=best,net_margin=str(Fraction(best['exact_value'])-idle)))
    exclusive=len(targets)==2 and not any(len(p['selected'])==2 for p in table)
    return dict(tick=view['tick'],targets=targets,candidate_count=len(keys),legal_plan_count=len(table),exact_optimum=str(optimum),selected_plan=selected,resource_exclusive=exclusive,positive_margin_competition=exclusive and all(Fraction(t['net_margin'])>0 for t in targets),reward_scope='PREDICTED_FINITE_TABLE')
