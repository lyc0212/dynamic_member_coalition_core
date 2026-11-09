"""Review this one saved execution; never runs a branch, estimator or physics STEP."""
import sys,json,math,time,hashlib,subprocess,traceback
from pathlib import Path
from copy import deepcopy
from fractions import Fraction
from contextlib import ExitStack
from unittest.mock import patch
cpu0=time.process_time();wall0=time.monotonic()
sys.path.insert(0,str(Path.cwd()))
from research.non_oracle import stfbs_d1a_model as model,policy
from research.cooperative_sensing import estimator
from research.information_service_bridge.public_stream import BridgeFrameProcessor
from research.information_service_online.execution import OnlineEnvironment
from research.non_oracle.stfbs_d1a_audit_registration import verified_registration
from research.non_oracle.stfbs_d1a_replay import recover,digest
from research.non_oracle.stfbs_d1a_audit_input import audit_input
from research.non_oracle.stfbs_d1a_verify import verify
from research.non_oracle.stfbs_d1a_history_audit import audit_histories
from research.non_oracle.stfbs_d1a_watchdog_support import verify_watchdog_receipt
from research.non_oracle.stfbs_d1a_preflight import check_source_lock
from research.information_service_online.public import seal_slot
from research.information_service_bridge.common import digest as bridge_digest

OUT=Path(__file__).resolve().parent
AUTH=Path('reports/stfbs_lite_d1a_h1_authorization_001')
WATCH=Path('reports/stfbs_lite_d1a_h1_revalidation_001_watchdog')
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,v):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
counts={}
def forbidden(name):
    counts[name]=0
    def fail(*a,**k):
        counts[name]+=1;raise AssertionError('Forbidden during read-only audit: '+name)
    return fail

def economics(raw,view):
    """Recompute recorded binary64 increments in original task order; JSON IDs stay strings."""
    cfg=view['config'];wr=4*cfg['task_count'];er=cfg['robots']*cfg['stage_dt']*cfg['control_reference']**2
    totals={k:0. for k in ('completion','flow','late','effort','terminal')};rational={k:Fraction(0) for k in totals}
    targets={t['id']:t for t in view['targets']}
    ends={e['target']:e for e in raw['events'] if e['kind'] in ('completed','escaped','unfinished')}
    assert set(ends)==set(targets)
    fees=0.;fee_exact=Fraction(0);last=view['positions'];prior={j:'active' for j in targets}
    for b in raw['boundaries']:
        changed=sum(a!=c for a,c in zip(b['before'],b['after']));fee=cfg['change_cost']*changed
        assert b['changes']==changed and b['cost']==fee
        fees+=fee;fee_exact+=Fraction(fee)
    for f in raw['frames']:
        assert f['before']==last
        for i,(p,u,dt) in enumerate(zip(f['before'],f['control'],f['elapsed'])):
            assert [p[k]+u[k]*dt for k in range(2)]==f['positions'][i]
            assert math.hypot(*u)<=cfg['max_speed']+1e-12  # Existing frozen physical-audit speed bound.
        increment=-cfg['control_weight']*f['energy']/er
        totals['effort']+=increment;rational['effort']+=Fraction(increment)
        lo=(f['tick']-1)*.05;hi=f['tick']*.05
        rows={r['target']:r for r in f['running']}
        assert set(rows)=={j for j in targets if prior[j]=='active'}
        for j,t in targets.items():
            if prior[j]!='active':continue
            stop=min(hi,ends[j]['time']);flow=t['weight']*max(0.,stop-max(lo,t['birth']))
            late=t['weight']*max(0.,stop-max(lo,t['birth'],t['deadline']))
            assert rows[j]==dict(target=j,stop=stop,flow=flow,late=late)
            for key,weight,val in (('flow',cfg['flow_weight'],flow),('late',cfg['late_weight'],late)):
                increment=-weight*val/(wr*cfg['stage_dt']);totals[key]+=increment;rational[key]+=Fraction(increment)
        last=f['positions'];prior={int(j):s for j,s in f['status'].items()}
    for j,event in ends.items():
        assert event['release_change_cost']==0. and event['processed_tick']==event['tick']
        assert raw['status'][str(j)]=={'completed':'completed','escaped':'escaped','unfinished':'unfinished'}[event['kind']]
        if event['kind']=='completed':
            value=targets[j]['weight']/wr;totals['completion']+=value;rational['completion']+=Fraction(value)
    totals['terminal']=-cfg['unfinished_weight']*math.fsum(t['weight'] for j,t in targets.items() if raw['status'][str(j)]!='completed')/wr
    rational['terminal']=Fraction(totals['terminal'])
    assert raw['frames'][-1]['tick']==120 and totals==raw['components'] and fees==raw['change_cost']
    net=sum(totals.values())-fees;assert net==raw['net']
    exact=sum(rational.values())-fee_exact
    return dict(status='PASS',components=totals,fees=fees,net=net,exact_binary64_increment_sum=str(exact),rounding_residual=str(Fraction(net)-exact))

def policy_wls(raw):
    rows=[]
    for d in raw['decisions']:
        count=0
        for row in d['choice']['rows']:
            assert all(d['view']['sensor_profiles'][i]['health']=='available' for i in row['key']['robots'])
            if not row['kept_history']:
                relevant=[s for s in d['view']['current_slots'] if s['slot_key']['target_id']==row['key']['target'] and s['slot_key']['robot_id'] in row['key']['robots']]
                assert all(s['state']!='MISSING' for s in relevant)
                count+=1
            terminal=next((e for e in row['events'] if e['kind'] in ('COMPLETED','ESCAPED')),None)
            count+=sum(terminal is None or f['tick']<terminal['tick'] or (terminal['kind']=='COMPLETED' and f['tick']==terminal['tick']) for f in row['frames'])
        rows.append(dict(tick=d['view']['tick'],WLS=count))
    return rows

def review():
    approval=read(AUTH/'APPROVAL.json');precheck=read(AUTH/'PRECHECK.json')
    assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==approval['head']
    check_source_lock(Path.cwd(),approval['source_pins'])
    assert all(sha(p)==s for p,s in precheck['protected_before'].items())
    assert read(OUT/'APPROVAL.json')==approval
    receipt=read(WATCH/'WATCHDOG_RECEIPT.json');launch=read(WATCH/'LAUNCH.json')
    resource_check=verify_watchdog_receipt(receipt)
    assert launch['child_pid']==receipt['child_pid'] and launch['watchdog_pid']==receipt['watchdog_pid']
    assert launch['approval_sha256']==sha(AUTH/'APPROVAL.json') and receipt['attempts']==1
    assert '-I' in receipt['command'] and receipt['terminated_processes']==0
    assert not receipt.get('descendant_cleanup')
    view,seed,contexts,registration=verified_registration()
    _,_,replay=recover('runs/a2_switch_episode_001')
    assert registration==read(OUT/'EXTERNAL_REGISTRATION.json')==precheck['source_registration']
    assert read(OUT/'PLAN_SELECTION.json')==approval['frozen_plan']
    assert read(OUT/'H1_CONTRACT.json')['world']['world_digest']==approval['world_digest']
    assert read(OUT/'H1_COMPATIBILITY.json')['status']=='COMPATIBILITY_CHECKED_WITH_LIMITATIONS'
    save('BELIEF_PREFIX_REPLAY.json',replay);save('BELIEF_REPLAY_SEED.json',seed)
    results={};economies={};detail={};resource={};prior_counts=None
    for name in ('KEEP','SWITCH'):
        raw=read(OUT/(name+'_RAW.json'));audits=read(OUT/(name+'_AUDITS.json'));ledger=read(OUT/(name+'_RESOURCE.json'))
        assert all(a['status']=='PASS' for a in audits.values())
        assert raw['branch']==name and raw['provenance']=='SIMULATED' and raw['observation_origin']=='MODEL'
        assert raw['world']['world_digest']==approval['world_digest'] and raw['world']['public_digest']==approval['public_digest']
        assert [f['tick'] for f in raw['frames']]==list(range(61,121))
        assert [b['tick'] for b in raw['boundaries']]==[60,80,100]
        assert raw['boundaries'][0]['after']==approval['frozen_plan'][name]
        normalized=audit_input(raw,view)
        independent_verify=verify(normalized,view,seed,audit_context=contexts[name])
        history=[]
        for d in raw['decisions']:
            v=d['view'];active={t['id']:'active' for t in v['targets']}
            history.append(audit_histories({h['target_id']:h for h in v['histories']},v['assignment'],active,v['tick'],context=contexts[name]))
            assert set(('kind','tick','end_tick','config','positions','assignment','sensor_profiles','targets','beliefs','histories','current_slots','first_policy_visible_ticks'))<=set(v)
            assert set(v)==set(view)  # No internal recovery fields leak to the policy interface.
            boundary=next(b for b in raw['boundaries'] if b['tick']==v['tick'])
            assert boundary['after']==d['choice']['actions']
        observation=0;rawslots={};streams=set()
        for f in raw['feedback']:
            assert f['branch']==name and f['endpoint']['branch']==name
            assert f['endpoint']['provenance']=='SIMULATED' and f['endpoint']['observation_origin']=='MODEL'
            assert f['frame']['stream_id'].startswith(name+':') and f['result']['stream_id']==f['frame']['stream_id']
            assert f['endpoint']['quality']==f['result']['quality']
            assert bridge_digest(f['result']['payload'])==f['result']['payload_sha256']
            observation+=int(f['result']['estimator_called']);streams.add(f['frame']['stream_id'])
            for slot in f['slots']:
                assert seal_slot(slot)==slot
                key=slot['slot_key'];identity=(name,key['target_id'],key['robot_id'],key['tick'])
                if identity in rawslots:assert rawslots[identity]==slot
                else:rawslots[identity]=slot
        assert len(raw['feedback'])==raw['endpoint_fusions']==ledger['endpoint_fusions']
        assert len(rawslots)==raw['raw_counts']['new'] and raw['raw_counts']['conflicts']==0
        decisions=policy_wls(raw);policy_total=sum(d['WLS'] for d in decisions)
        assert observation==ledger['delta']['MODEL_OBSERVATION_WLS'] and policy_total==ledger['delta']['MODEL_POLICY_EVALUATION_WLS']
        assert ledger['delta']['ACTUAL_WLS']==0
        assert all(ledger['after'][k]-ledger['before'][k]==ledger['delta'][k] for k in ledger['before'])
        if prior_counts is not None:assert ledger['before']==prior_counts
        else:assert all(v==0 for v in ledger['before'].values())
        prior_counts=ledger['after'];resource[name]=dict(ledger=ledger,independent_policy_WLS=decisions,independent_observation_WLS=observation,unique_raw_slots=len(rawslots))
        economies[name]=economics(raw,view)
        assert economies[name]['rounding_residual']==audits['physical_economic']['rounding_residual']
        detail[name]=dict(runtime_audits=audits,saved_view_reaudit=history,independent_verify=independent_verify,streams=sorted(streams),events=raw['events'],raw_counts=raw['raw_counts'],endpoint_fusions=raw['endpoint_fusions'],decision_ticks=[d['view']['tick'] for d in raw['decisions']])
        results[name]=raw
    pair=read(OUT/'MODEL_PAIR_RESULT.json');cost=read(OUT/'COST.json')
    assert cost['MODEL_OBSERVATION_WLS']==prior_counts['MODEL_OBSERVATION_WLS']<=1000
    assert cost['MODEL_POLICY_EVALUATION_WLS']==prior_counts['MODEL_POLICY_EVALUATION_WLS']<=4000
    assert cost['MODEL_TOTAL_WLS']==sum(prior_counts.values())<=5000 and cost['ACTUAL_WLS']==0
    assert cost['cpu_seconds']<=600 and cost['wall_seconds']<=900
    delta=results['SWITCH']['net']-results['KEEP']['net'];assert delta==pair['delta']
    exact=Fraction(results['SWITCH']['net'])-Fraction(results['KEEP']['net'])
    assert str(exact)==pair['exact_binary64_net_difference']
    component_exact=sum(Fraction(results['SWITCH']['components'][k])-Fraction(results['KEEP']['components'][k]) for k in results['KEEP']['components'])-(Fraction(results['SWITCH']['change_cost'])-Fraction(results['KEEP']['change_cost']))
    save('READ_ONLY_INDEPENDENT_REVIEW.json',dict(status='PASS',registration=registration,branches=detail,economics=economies,paired_net_exact=str(exact),paired_component_exact=str(component_exact),binary64_net_vs_component_residual=str(exact-component_exact),paired_float_delta=delta,resource=resource,watchdog_resource_necessary_check=resource_check,source_identity='45/45 match external expected pins; HEAD unchanged',original_archive_preserved=len(precheck['protected_before']),note='No reconstructed Branch substitutes the completed live object. Final Branch audit is the runtime independent audit in each *_AUDITS. This offline pass re-audits persisted D80/D100 histories and complete frame/feedback/belief/financial records.'))
    # Reuse pinned historical deterministic negative evidence; do not rerun experiments/tests.
    pins=read('reports/stfbs_lite_d1a_001/PRE_MAIN_SOURCE_PINS.json')
    unchanged={p:sha(p.replace('\\','/'))==s for p,s in pins.items() if p.replace('\\','/') in ('research/non_oracle/stfbs_d1a_state.py','research/non_oracle/stfbs_d1a_plan.py','research/non_oracle/stfbs_d1a_audit.py','tests/test_stfbs_d1a_state.py','tests/test_stfbs_d1a_physics.py')}
    assert all(unchanged.values())
    save('REGISTERED_TEST_EVIDENCE_REUSE.json',dict(status='PASS',unchanged_historical_tested_math_sources=unchanged,logs=['reports/stfbs_lite_d1a_001/FINAL_TESTS.log','reports/stfbs_lite_d1a_001/ADDITIONAL_ACCEPTANCE_TESTS.log'],current_repaired_history_and_interfaces=['reports/stfbs_lite_d1a_g3_history_repair_001','reports/stfbs_lite_d1a_g3_supplement_001','reports/stfbs_lite_d1a_g3_audit_hardening_001','reports/stfbs_lite_d1a_h1_revalidation_prep_001','reports/stfbs_lite_d1a_h1_preflight_lock_001'],boundary='Historical synthetic math/cache/negative evidence is reused as authorized, not reported as newly run tests or as proof of this new H1. Actual G3/4 rely on the new runtime independent audits and this read-only record verification. Original old H1 failed-history verdict is preserved.'))
    return pair,cost,receipt,precheck

with ExitStack() as guards:
    for owner,name in ((model,'estimate'),(policy,'estimate'),(estimator,'estimate'),(BridgeFrameProcessor,'process'),(OnlineEnvironment,'step'),(model.Branch,'run'),(model.Branch,'advance')):
        guards.enter_context(patch.object(owner,name,forbidden(owner.__name__+'.'+name)))
    try:
        pair,cost,receipt,precheck=review()
    except Exception as error:
        save('READ_ONLY_REVIEW_FAILURE.json',dict(error=repr(error),traceback=traceback.format_exc(),status='NOT_VERIFIED',no_rerun=True))
        raise
    finally:
        save('READ_ONLY_AUDIT_COST.json',dict(forbidden_call_counts=counts,MODEL_WLS=0,ACTUAL_WLS=0,physics_advance=0,cpu_seconds=time.process_time()-cpu0,wall_seconds=time.monotonic()-wall0,scope='Separate offline review, not folded into measured H1 watchdog process'))
print('Read-only independent review PASS. No model rerun, WLS or ACTUAL STEP.')
