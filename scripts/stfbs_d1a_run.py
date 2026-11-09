"""Frozen H1 driver: default invocation refuses execution."""
import sys,json,math,time,argparse,subprocess,hashlib,traceback
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.non_oracle.stfbs_d1a_replay import read,digest
from research.non_oracle.stfbs_d1a_model import Branch,Budget,nominal_world,point
from research.non_oracle.stfbs_d1a_plan import select
from research.non_oracle.stfbs_d1a_audit import audit,service_audit
from research.non_oracle.stfbs_d1a_verify import verify
from research.non_oracle.stfbs_d1a_audit_registration import verified_registration
from research.non_oracle.stfbs_d1a_history_audit import audit_branch_independent
from research.non_oracle.stfbs_d1a_audit_input import audit_input
from pursuit_v2.config import Config
from pursuit_v2.observation_geometry import offset,radius
from research.non_oracle.stfbs_d1a_preflight import check_source_lock
from research.non_oracle.stfbs_d1a_watchdog_support import require_watchdog

ROOT=Path(__file__).resolve().parents[1]
LIMITS=dict(MODEL_OBSERVATION_WLS=1000,MODEL_POLICY_EVALUATION_WLS=4000,MODEL_TOTAL_WLS=5000,ACTUAL_WLS=0,cpu_seconds=600,wall_seconds=900)

def authorize(args):
    if not args.execute_frozen_h1 or not args.approval_manifest or not args.output_dir:
        raise ValueError('Explicit execution, external approval and new output directory required')
    approval=read(args.approval_manifest)
    if approval.get('status')!='APPROVED_FOR_ONE_H1_REVALIDATION' or approval.get('experiment')!='D1_A_FROZEN_H1' or not approval.get('authorized_by'):
        raise ValueError('Invalid external approval record')
    if approval.get('limits')!=LIMITS:raise ValueError('Approval budget mismatch')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if approval.get('head')!=head:raise ValueError('Approval HEAD mismatch')
    pins=approval.get('source_pins',{})
    check_source_lock(ROOT,pins)
    output=Path(args.output_dir).resolve()
    if output.exists():raise ValueError('Output already exists; no reuse allowed')
    if not output.is_relative_to(ROOT/'reports') or any(x.startswith('stfbs_lite_d1a_001') or x.startswith('stfbs_lite_d1a_g3_') for x in output.relative_to(ROOT/'reports').parts):
        raise ValueError('Output conflicts with historical archive')
    if Path(approval.get('output_dir','')).resolve()!=output:raise ValueError('Approval output mismatch')
    return output,approval

def frozen_registration():
    view,seed,contexts,manifest=verified_registration()
    if set(contexts)!={'KEEP','SWITCH'}:raise ValueError('Missing external contexts')
    world=nominal_world(view)
    old=read('reports/stfbs_lite_d1a_001/H1_CONTRACT.json')
    if digest(world)!=digest(old['world']) or digest(seed)!=old['seed_digest'] or digest(view)!=old['public_digest']:
        raise ValueError('Frozen H1 source mismatch')
    choice=read('runs/a2_switch_episode_001/R_D60.json')['choice'];plans=select(view,choice)
    frozen_plan=dict(plans,public_digest=digest(view),table_digest=digest(choice['rows']),world_digest=world['world_digest'],continuation='policy.decide R at D80,D100',historical_table_reused=True)
    if frozen_plan!=read('reports/stfbs_lite_d1a_001/PLAN_SELECTION.json'):raise ValueError('Frozen plan mismatch')
    return view,seed,contexts,manifest,world,plans,frozen_plan

def require_pass(value):
    if not isinstance(value,dict) or value.get('status')!='PASS':raise ValueError('Required audit did not PASS')
    return value

def run_pair(view,seed,contexts,world,plans,budget,save,progress):
    results={};checks={}
    for name in ('KEEP','SWITCH'):
        progress.update(branch=name,stage='construct',audits={k:'NOT_RUN' for k in ('history','verify','service','physical_economic')})
        if name not in contexts:raise ValueError('Missing external context')
        before=deepcopy(budget.counts)
        branch=Branch(view,seed,world,name,budget)
        progress['stage']='run'
        try:
            result=branch.run(plans[name])
        except Exception:
            save(name+'_PARTIAL.json',dict(status='INCOMPLETE_NOT_VALIDATED',branch=name,frames=branch.frames,events=branch.events,feedback=branch.feedback,decisions=branch.decisions,boundaries=branch.boundaries,histories=branch.histories,counts=deepcopy(budget.counts)))
            raise
        save(name+'_RAW.json',result)
        checks[name]={}
        def checked(label,call):
            progress['stage']=label
            try:
                value=require_pass(call())
            except Exception:
                progress['audits'][label]={'status':'FAIL'}
                raise
            progress['audits'][label]=deepcopy(value)
            return value
        checks[name]['history']=checked('history',lambda:audit_branch_independent(branch,context=contexts[name]))
        progress['stage']='audit_input'
        normalized=audit_input(result,view)
        for label,call in (
            ('verify',lambda:verify(normalized,view,seed,audit_context=contexts[name])),
            ('service',lambda:service_audit(normalized,view)),
            ('physical_economic',lambda:audit(normalized,view))):
            checks[name][label]=checked(label,call)
        budget.check()
        save(name+'_AUDITS.json',checks[name])
        save(name+'_RESOURCE.json',dict(before=before,after=deepcopy(budget.counts),delta={k:budget.counts[k]-before[k] for k in before},raw=result.get('raw_counts'),endpoint_fusions=result.get('endpoint_fusions')))
        results[name]=result
    budget.check()
    delta=results['SWITCH']['net']-results['KEEP']['net']
    pair=dict(status='PAIR_AUDITS_PASS_PENDING_G0_G5_REVIEW',provenance='SIMULATED',observation_origin='MODEL',J_KEEP=results['KEEP']['net'],J_SWITCH=results['SWITCH']['net'],delta=delta,exact_binary64_net_difference=str(Fraction(results['SWITCH']['net'])-Fraction(results['KEEP']['net'])),component_differences={k:results['SWITCH']['components'][k]-results['KEEP']['components'][k] for k in results['KEEP']['components']},change_cost_difference=results['SWITCH']['change_cost']-results['KEEP']['change_cost'])
    return pair,checks

def main(argv=None):
    parser=argparse.ArgumentParser(description='Frozen H1: separate explicit research authorization required')
    parser.add_argument('--execute-frozen-h1',action='store_true');parser.add_argument('--approval-manifest');parser.add_argument('--output-dir')
    parser.add_argument('--watchdog-ticket')
    args=parser.parse_args(argv)
    require_watchdog(args.watchdog_ticket,args.approval_manifest)
    output,approval=authorize(args)
    if Path.cwd().resolve()!=ROOT:raise ValueError('Run from registered repository root')
    budget=Budget()
    view,seed,contexts,manifest,world,plans,frozen_plan=frozen_registration()
    budget.check()
    output.mkdir(exist_ok=False)
    def save(name,value):
        def encode(v):
            if hasattr(v,'tolist'):return v.tolist()
            raise TypeError(type(v))
        with (output/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,default=encode,allow_nan=False)
    progress=dict(branch=None,stage='compatibility',audits={})
    try:
        save('APPROVAL.json',approval);save('EXTERNAL_REGISTRATION.json',manifest)
        execute_registered(view,seed,contexts,manifest,world,plans,frozen_plan,budget,save,progress)
    except Exception as e:
        save('MAIN_FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc(),progress=progress,counts=budget.counts,cpu_seconds=time.process_time()-budget.cpu,wall_seconds=time.monotonic()-budget.wall,unexecuted='Later branches/checks not resumed; no automatic retry',status='BLOCKED'))
        raise

def execute_registered(view,seed,contexts,manifest,world,plans,frozen_plan,budget,save,progress):
    cfg=Config(**view['config']);checks=[]
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
    save('PLAN_SELECTION.json',frozen_plan)
    save('STATIC_BUDGET.json',dict(observation_upper=126,policy_upper=2*12*(41+21),D60_new_WLS=0,total_upper=1614,within_budget=True))
    pair,checks=run_pair(view,seed,contexts,world,plans,budget,save,progress)
    save('COST.json',dict(budget.counts,MODEL_TOTAL_WLS=sum(budget.counts.values()),cpu_seconds=time.process_time()-budget.cpu,wall_seconds=time.monotonic()-budget.wall))
    save('ALL_AUDITS.json',checks)
    save('MODEL_PAIR_RESULT.json',pair)

if __name__=='__main__':
    main()
