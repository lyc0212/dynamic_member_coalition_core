"""One registered H1 MODEL pair; never calls an ACTUAL execution entry."""
import sys,json,math,time
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
import hashlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.non_oracle.stfbs_d1a_replay import recover,read,digest
from research.non_oracle.stfbs_d1a_model import Branch,Budget,nominal_world,point
from research.non_oracle.stfbs_d1a_plan import select
from research.non_oracle.stfbs_d1a_audit import audit,service_audit
from pursuit_v2.config import Config
from pursuit_v2.observation_geometry import offset,radius

OUT=Path('reports/stfbs_lite_d1a_001')
def save(name,value):
    def encode(v):
        if hasattr(v,'tolist'):return v.tolist()
        raise TypeError(type(v))
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,default=encode,allow_nan=False)

def main():
    budget=Budget()
    view,seed,replay=recover('runs/a2_switch_episode_001')
    world=nominal_world(view);cfg=Config(**view['config']);checks=[]
    for slot in view['current_slots']:
        if slot['state']=='VALID':
            j=slot['slot_key']['target_id'];p=point(world,j,60);r=slot['packet']['position']
            angle=math.atan2(float(p[1]-r[1]),float(p[0]-r[0]));bearing=(angle+math.pi)%(2*math.pi)-math.pi
            checks.append(dict(kind='zero_perturbation_bearing',key=slot['slot_key'],equal=bearing==slot['packet']['bearing']))
    for h in view['histories']:
        s=next((s for s in h['segments'] if s['segment_id']==h['active_segment_id']),None)
        if s:
            import numpy as np
            g=all(np.linalg.norm(np.asarray(view['positions'][m['robot_id']])-point(world,h['target_id'],60)-offset(m['role'],cfg))<=radius(cfg) for m in s['team'])
            checks.append(dict(kind='inherited_G',target=h['target_id'],equal=bool(g)==s['latest_endpoint']['G']))
    status='COMPATIBILITY_CHECKED_WITH_LIMITATIONS' if all(c['equal'] for c in checks) else 'COMPATIBILITY_CONTRADICTED'
    contract=dict(world=world,rule='Public D60 constant velocity; zero perturbation; current sensor declaration held; no private future',public_digest=digest(view),seed_digest=digest(seed),checks=checks,status=status,limitations='No statistical coverage claim; only current known endpoints and acquired bearings checked')
    save('H1_CONTRACT.json',contract);save('H1_COMPATIBILITY.json',dict(status=status,checks=checks))
    if status!='COMPATIBILITY_CHECKED_WITH_LIMITATIONS':raise ValueError('H1 incompatible; no pair started')
    choice=read('runs/a2_switch_episode_001/R_D60.json')['choice'];plans=select(view,choice)
    save('PLAN_SELECTION.json',dict(plans,public_digest=digest(view),table_digest=digest(choice['rows']),world_digest=world['world_digest'],continuation='policy.decide R at D80,D100',historical_table_reused=True))
    save('STATIC_BUDGET.json',dict(observation_upper=126,policy_upper=2*12*(41+21),D60_new_WLS=0,total_upper=1614,within_budget=True))
    results={};audits={};physical={}
    for name in ('KEEP','SWITCH'):
        branch=Branch(view,seed,world,name,budget);result=branch.run(plans[name]);save(f'{name}_RAW.json',result)
        audits[name]=audit(result,view);physical[name]=service_audit(result,view);results[name]=result
    delta=results['SWITCH']['net']-results['KEEP']['net'];component_delta={k:results['SWITCH']['components'][k]-results['KEEP']['components'][k] for k in results['KEEP']['components']}
    exact=Fraction(results['SWITCH']['net'])-Fraction(results['KEEP']['net'])
    save('MODEL_PAIR_RESULT.json',dict(provenance='SIMULATED',observation_origin='MODEL',J_KEEP=results['KEEP']['net'],J_SWITCH=results['SWITCH']['net'],delta=delta,exact_binary64_net_difference=str(exact),component_differences=component_delta,change_cost_difference=results['SWITCH']['change_cost']-results['KEEP']['change_cost']))
    save('ACCOUNTING_AUDIT.json',audits);save('PHYSICAL_AUDIT.json',physical)
    save('RAW_MEASUREMENT_AUDIT.json',{n:r['raw_counts'] for n,r in results.items()})
    budget.check();save('COST.json',dict(budget.counts,MODEL_TOTAL_WLS=sum(budget.counts.values()),cpu_seconds=time.process_time()-budget.cpu,wall_seconds=time.monotonic()-budget.wall,raw={n:r['raw_counts'] for n,r in results.items()},endpoint_fusions={n:r['endpoint_fusions'] for n,r in results.items()}))

if __name__=='__main__':
    try:main()
    except Exception as e:
        import traceback
        save('MAIN_FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc()))
        raise
