"""Twelve deterministic Release contracts; never imports/runs either G1 entry."""
from unittest import TestCase
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import ast,json,hashlib,math,sys
import numpy as np
from dataclasses import asdict
from research.non_oracle.stfbs_d1b_qm_scenario import build_fixture,validate_fixture
from research.non_oracle.stfbs_d1b_qm_model import QMBranch,initial_team,changed_team
from research.non_oracle.stfbs_d1b_qm_budget import D1BBudget,CallJournal,inspect_journal,BudgetRejected
from research.non_oracle.stfbs_d1b_qm_execution import DynamicSchedule,ProbeSchedule,PROBES,SPECIAL_IDS
from research.non_oracle.stfbs_d1b_qm_run_release import (ApprovalExpectation,REQUIRED_BINDINGS,AUTHORITY_PATH,validate_approval_bytes,
    authorize_policy,runtime_scope,require_run_g1,freeze_admission,execute_test_plan)
from research.non_oracle.stfbs_d1b_qm_run_evidence import (coordinate_batch,create_test_source,result_from_branch,records_from_branch,
    serial_records,read_verified_source,candidate_from_sources,independent_gq)
from research.non_oracle.stfbs_d1b_qm_run_specials import (verify_special_source,inherited_cache,special_frame,run_special,
    validate_special_frame,validate_pending_identity)
from research.non_oracle.stfbs_d1b_qm_independent_audit import register_fixture,audit_registered
from research.non_oracle.stfbs_d1b_qm_run_audit import active_registry,save,sha
from research.non_oracle.stfbs_d1a_replay import digest
from research.information_service_online.public import seal_slot
from research.information_service.public_quality import prepare_frame,assess_quality
from pursuit_v2.observation_geometry import offset,radius

ROOT=Path(__file__).resolve().parents[1];REPORT=ROOT/'reports/stfbs_lite_d1b_qm_run_release_001';LABEL='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'
SOURCES=0;ENDPOINT_CALLS=[]

def pins():return json.loads((REPORT/'RUN_POLICY.json').read_bytes())['source_pins']

def ticket():
    f=build_fixture();p=json.loads((REPORT/'RUN_POLICY.json').read_bytes())
    return dict(status='APPROVED_FOR_ONE_D1B_RUN_G1',task='D1-B-QM-1B-RUN-G1',batch_id='SYNTHETIC_ONLY',source_pins=p['source_pins'],
        fixture_digest=digest(dict(view=f.view,seed=f.seed,identity=f.identity)),world_digest=f.world['world_digest'],motion_rule=f.world['motion_rule'],
        special_protocol='F2_B1_LEFT80_U0_U2__F3_B0_RIGHT80_B1_LEFT80_V1',branch_ids=list(PROBES)+['QM_B0_KEEP','QM_B1_MEMBER_CHANGE','QM_B3_UNKNOWN']+list(SPECIAL_IDS),
        outer_limit=292,inner_limit=2628,category_limits=dict(MODEL_OBSERVATION_WLS=289,MODEL_SPECIAL_TEST_WLS=3,MODEL_POLICY_EVALUATION_WLS=0,MODEL_INDEPENDENT_AUDIT_WLS=0,ACTUAL_WLS=0),
        cpu_limit=480,wall_limit=600,output_dir=str(ROOT/'runs/SYNTHETIC_NEVER_CREATE'),attempt_id='TEST_ONLY',audit_version='D1B_RELEASE_AUDIT_V1',
        stop_rule='ONE_ATTEMPT_STOP_ON_ANY_CONTRACT_FAILURE',main_script_sha256=sha(ROOT/'scripts/stfbs_d1b_qm_run_g1.py'),watchdog_script_sha256=sha(ROOT/'scripts/stfbs_d1b_qm_run_g1_watchdog.py'),
        runtime_pins={p['python']:p['python_sha256']},evidence_kind=LABEL)

def expectation_for_bytes(raw):return ApprovalExpectation(hashlib.sha256(raw).hexdigest(),'INDEPENDENT_TEST_EXPECTATION',LABEL)

def solver_stub(value):return value
solver_stub.evidence_kind=LABEL

def estimate_stub(payload):return {'has_accepted_estimate':False,'evidence_kind':LABEL}
estimate_stub.evidence_kind=LABEL

def fake_endpoint(b,j,segment,tick):
    active_registry().note_double('complete synthetic packet/frame/estimate result; pure Q algebra only')
    target=[9.+.4*((tick-60)*.05),10.];stream=f'{b.name}:T{j}:first{segment["first_fusion_tick"]}';fid=stream+':tick'+str(tick)
    packets=[];slots=[]
    for member in segment['team']:
        i=member['robot_id'];profile=b._sensor_authority.physical_profile_at(tick)[i];pos=b.positions[i].tolist()
        packet=dict(sensor_id='U'+str(i),position=pos,bearing=(math.atan2(target[1]-pos[1],target[0]-pos[0])+math.pi)%(2*math.pi)-math.pi,
                    sigma=profile['sigma'],measurement_tick=tick,available_tick=tick,status='ok')
        slot=seal_slot(dict(slot_key=dict(target_id=j,robot_id=i,tick=tick),state='VALID',packet=packet,slot_digest=None))
        slot=b.cache.query(b.name,j,i,tick,dict(position=pos,sigma=profile['sigma'],health=profile['health']),lambda:deepcopy(slot))
        slots.append(slot);packets.append(dict(slot['packet'],packet_id=fid+':U'+str(i)))
    frame=dict(contract_id='STAGE2A5B-A-MINIMAL-v0.2',stream_id=stream,frame_id=fid,target_id=j,tick=tick,measurement_time=tick*.05,available_time=tick*.05,records=packets)
    prepared=prepare_frame(frame,[x['sensor_id'] for x in packets])
    estimate=dict(has_accepted_estimate=True,estimate=target,optimizer_converged=True,numerical_ill_conditioned=False,ambiguity_detected=False,boundary_active=False,branch_guard_triggered=False,numeric_contract_violation=False,starts=[],evidence_kind=LABEL)
    quality=assess_quality(prepared['payload'],estimate);quality['frame_id']=fid
    G=all(float(np.linalg.norm(b.positions[m['robot_id']]-target-offset(m['role'],b.cfg)))<=radius(b.cfg) for m in segment['team'])
    endpoint=dict(tick=tick,target_id=j,team=deepcopy(segment['team']),G=G,quality=quality,provenance='SIMULATED',observation_origin='MODEL',branch=b.name)
    result=dict(prepared,frame_id=fid,stream_id=stream,target_id=j,tick=tick,start_tick=segment['first_fusion_tick'],estimate_result=estimate,quality=quality,estimator_called=False,skipped=False,duplicate=False,execution_contract_id='SYNTHETIC_TEST_DOUBLE')
    b.consumer.enqueue(dict(target_id=j,measurement_tick=tick,available_tick=tick,estimate=estimate,provenance='SIMULATED',observation_origin='MODEL'))
    b.feedback.append(dict(frame=frame,result=result,endpoint=deepcopy(endpoint),slots=slots));ENDPOINT_CALLS.append((b.name,tick))
    return endpoint
fake_endpoint.evidence_kind=LABEL

def synthetic_source(name='QM_B1_MEMBER_CHANGE',sigma=.16):
    global SOURCES
    SOURCES+=1;f=build_fixture();b=QMBranch(f,name=name,degraded_sigma=sigma)
    b.budget=D1BBudget(test_cap=0,test_estimator=estimate_stub)
    selected={'research/non_oracle/stfbs_d1b_qm_scenario.py':pins()['research/non_oracle/stfbs_d1b_qm_scenario.py']}
    reg=register_fixture(f,name,selected)
    with active_registry().fake_scope('synthetic committed history and MODEL-like evidence, no physical ticks',fake_endpoint):
        with b.budget.for_branch(name):b.assign(initial_team())
        b.tick=80;b.positions[:,0]+=.4
        for h in b.histories.values():h['cutoff_tick']=80
        b.segment(0)['latest_endpoint']=fake_endpoint(b,0,b.segment(0),80)
        if name=='QM_B1_MEMBER_CHANGE':
            b._sensor_authority.publish_from_executor(80);b.policy_view()
            with b.budget.for_branch(name):b.assign(changed_team())
    audit=audit_registered(b,reg);records=records_from_branch(b);records['positions'][80]=b.positions.tolist()
    records['physical_profiles'][79]=b._sensor_authority.physical_profile_at(79)
    payload=dict(batch_id='SYNTHETIC_BATCH',branch_id=name,result=result_from_branch(b),records=serial_records(records),external_history_audit=audit,evidence_kind=LABEL)
    source=create_test_source(payload,reg,REPORT/f'synthetic_source_{SOURCES}.json')
    return source,b,f

class SyntheticPort:
    evidence_kind=LABEL
    def __init__(self,b):self.b=b;self._sensor_authority=SimpleNamespace(publish_from_executor=lambda t:self.b._sensor_authority.publish_from_executor(t))
    def __getattr__(self,key):return getattr(self.b,key)
    def policy_view(self):return self.b.policy_view()
    def assign(self,actions):self.b.assign(actions)
    def advance(self):
        n=80 if self.b.tick==60 else 100;self.b.tick=n
        self.b.positions[:,0]+=.4
        for h in self.b.histories.values():h['cutoff_tick']=n
        self.b.segment(0)['latest_endpoint']=fake_endpoint(self.b,0,self.b.segment(0),n)

class FakeProcessor:
    def __init__(self,ids,tick,stream,target,*,estimator_fn):self.ids=ids;self.stream=stream;self.estimator=estimator_fn
    def process(self,frame):
        active_registry().note_double('one fake special processor, no BridgeFrameProcessor.process')
        prepared=prepare_frame(frame,self.ids);r=self.estimator(prepared['payload'])
        return dict(prepared,estimate_result=r,estimator_called=True,frame_id=frame['frame_id'],stream_id=self.stream,evidence_kind=LABEL)
FakeProcessor.evidence_kind=LABEL

class SyntheticOps:
    evidence_kind=LABEL
    def __init__(self,fail=False):self.calls=[];self.fail=fail
    def probe(self,name):self.calls.append(name);return name
    def old_quality(self,source):return dict(G=True,Q='PASS')
    def candidate(self,old,new,sigma):return dict(old_G=True,new_G=True,old_Q='PASS',new_Q='PASS' if self.fail or sigma<.16 else 'FAIL',sigma=sigma)
    def candidate_values(self,row):return row
    def admit(self,rows):self.calls.append('ADMIT');return rows
    def dynamic(self,name,sigma,admission):self.calls.append(name);return name
    def dynamic_realized(self,*args):return True
    def b3(self):self.calls.append('QM_B3_UNKNOWN');return 'B3'
    def f1(self,b1):self.calls.append('F1')
    def special(self,name,source):self.calls.append(name)
    def final_science(self,*args):return dict(evidence_kind=LABEL)

class ReleaseTests(TestCase):
    def test_release_denies_missing_or_forged_authorization(self):
        t=ticket();raw=json.dumps(t,sort_keys=True).encode();expected=expectation_for_bytes(raw)
        with self.assertRaisesRegex(PermissionError,'APPROVAL_NOT_VERIFIED'):validate_approval_bytes(raw,None,t)
        inside=dict(t,expected_sha256=hashlib.sha256(raw).hexdigest())
        with self.assertRaises(PermissionError):validate_approval_bytes(json.dumps(inside).encode(),None,t)
        changed=dict(t,outer_limit=293);changed['self_sha256']=hashlib.sha256(json.dumps(changed).encode()).hexdigest()
        with self.assertRaises(PermissionError):validate_approval_bytes(json.dumps(changed).encode(),expected,t)
        self.assertEqual(validate_approval_bytes(raw,expected,t)['status'],'PURE_VALIDATION_PASS')
        for field,value in [('source_pins',{}),('fixture_digest','bad'),('outer_limit',293),('inner_limit',2629),('cpu_limit',481),('wall_limit',601),('output_dir','wrong'),('attempt_id','wrong')]:
            bad=dict(t);bad[field]=value;data=json.dumps(bad).encode()
            with self.assertRaisesRegex(PermissionError,'binding mismatch'):validate_approval_bytes(data,expectation_for_bytes(data),t)
        self.assertFalse(AUTHORITY_PATH.exists())
        with self.assertRaisesRegex(PermissionError,'independent user channel absent'):authorize_policy(REPORT/'no_approval_exists.json')

    def test_release_context_and_real_port_gate_with_doubles(self):
        t=ticket();raw=json.dumps(t).encode();check=validate_approval_bytes(raw,expectation_for_bytes(raw),t)
        self.assertEqual(execute_test_plan(check,SyntheticOps())['status'],'EXECUTED_AWAITING_FINAL_AUDIT')
        with self.assertRaises(PermissionError):
            with runtime_scope(check,dict(actual_windows_job=True,attempt_id=t['attempt_id'])):pass
        f=build_fixture();b=QMBranch(f,name='QM_B0_KEEP');b.budget=D1BBudget()
        with self.assertRaises(PermissionError):execute_test_plan(check,b)
        with self.assertRaisesRegex(PermissionError,'APPROVAL_NOT_VERIFIED'):DynamicSchedule(b,b.name).start()
        with self.assertRaises(PermissionError):D1BBudget.from_release(check,REPORT/'must_not_exist.jsonl')
        self.assertFalse((REPORT/'must_not_exist.jsonl').exists());self.assertEqual(b.boundaries,[]);self.assertEqual(b.fusions,0)
        with self.assertRaises(PermissionError):b.budget.bind_real_estimator(check)

    def test_probe_and_dynamic_dispatch_without_science(self):
        active_registry().note_double('complete batch with synthetic operation port, no physical executor')
        ops=SyntheticOps();result=coordinate_batch(ops)
        self.assertEqual(result['selected_sigma'],.16)
        self.assertEqual(ops.calls,['QM_PROBE_OLD','QM_PROBE_DEGRADED_1','QM_PROBE_DEGRADED_2','QM_PROBE_DEGRADED_3','ADMIT','QM_B0_KEEP','QM_B1_MEMBER_CHANGE','QM_B3_UNKNOWN','F1','QM_F2_VALID_HISTORY','QM_F3_STREAM_A','QM_F3_STREAM_B'])
        fail=SyntheticOps(True);stopped=coordinate_batch(fail);self.assertEqual(stopped['status'],'NO_Q_ONLY_FAIL_FOUND');self.assertTrue(all(v=='NOT_EXECUTED_GATE_NOT_MET' for v in stopped['stages'].values()));self.assertEqual(len(fail.calls),5)
        for script in ('stfbs_d1b_qm_run_g1.py','stfbs_d1b_qm_run_g1_watchdog.py'):
            tree=ast.parse((ROOT/'scripts'/script).read_text());self.assertTrue(any(isinstance(n,ast.FunctionDef) and n.name=='main' for n in tree.body))
        with active_registry().fake_scope('transaction-owned left60 and left80 synthetic endpoints',fake_endpoint):
            f=build_fixture();b=QMBranch(f,name='QM_B1_MEMBER_CHANGE');b.budget=D1BBudget(test_cap=0,test_estimator=estimate_stub);start=len(ENDPOINT_CALLS)
            s=DynamicSchedule(SyntheticPort(b),b.name);s.start();s.advance_one();s.advance_one()
            self.assertEqual([n for name,n in ENDPOINT_CALLS[start:]],[60,80,80,100])

    def test_outer_wls_cap_and_failure_journal(self):
        path=REPORT/'outer_calls.jsonl';observed=[]
        def fake(payload):
            rows=[json.loads(x) for x in path.read_text().splitlines()];observed.append(rows[-1]['status']);return payload
        fake.evidence_kind=LABEL
        b=D1BBudget(test_cap=1,test_estimator=fake,journal_path=path)
        with b.for_frame('QM_B0_KEEP:T0:test:tick80'):
            cb=b.estimator('MODEL_OBSERVATION_WLS',branch_id='QM_B0_KEEP');cb({})
            with self.assertRaisesRegex(BudgetRejected,'OUTER_CAP'):cb({})
        self.assertEqual(observed,['STARTED']);self.assertEqual(b.accounting['outer_wls_started'],1);self.assertEqual(b.accounting['budget_rejected'],1)
        b.journal.close();self.assertEqual(inspect_journal(path)['status'],'COMPLETE')
        def broken(payload):raise ArithmeticError('synthetic outer failure')
        broken.evidence_kind=LABEL
        f=D1BBudget(test_cap=1,test_estimator=broken,journal_path=REPORT/'outer_failure.jsonl')
        with f.for_frame('failure'):
            with self.assertRaises(ArithmeticError):f.estimator('MODEL_SPECIAL_TEST_WLS',branch_id='QM_F2_VALID_HISTORY')({})
        self.assertEqual(f.accounting['outer_wls_failed'],1);self.assertEqual(f.counts['MODEL_SPECIAL_TEST_WLS'],1);f.journal.close()

    def test_inner_solver_alias_cap_and_failure_journal(self):
        holder={};entered=[]
        def solver(value):
            entered.append(value);rows=[json.loads(x) for x in holder['path'].read_text().splitlines()];self.assertEqual(rows[-1]['status'],'STARTED');self.assertEqual(rows[-1]['level'],'INNER');return value
        solver.evidence_kind=LABEL;module=SimpleNamespace(least_squares=solver)
        def estimate(payload):return [module.least_squares(k) for k in range(9)]
        estimate.evidence_kind=LABEL
        def outer(payload):return holder['b'].invoke_alias(module,estimate,payload)
        outer.evidence_kind=LABEL
        path=REPORT/'inner_calls.jsonl';b=D1BBudget(test_cap=1,test_estimator=outer,test_inner_cap=9,journal_path=path);holder.update(b=b,path=path)
        with b.for_frame('nine'):b.estimator('MODEL_OBSERVATION_WLS',branch_id='QM_B0_KEEP')({})
        self.assertIs(module.least_squares,solver);self.assertEqual(b.accounting['outer_wls_started'],1);self.assertEqual(b.accounting['least_squares_started'],9);b.journal.close()
        path=REPORT/'inner_cap.jsonl';limited=D1BBudget(test_cap=1,test_estimator=outer,test_inner_cap=2,journal_path=path);holder.update(b=limited,path=path);before=len(entered)
        with limited.for_frame('limited'):
            with self.assertRaisesRegex(BudgetRejected,'INNER_CAP'):limited.estimator('MODEL_OBSERVATION_WLS',branch_id='QM_B0_KEEP')({})
        self.assertEqual(len(entered)-before,2);self.assertIs(module.least_squares,solver);self.assertEqual(limited.accounting['outer_wls_failed'],1);limited.journal.close()
        def fail_solver(value):raise ArithmeticError('synthetic inner failure')
        fail_solver.evidence_kind=LABEL;failed_module=SimpleNamespace(least_squares=fail_solver)
        def fail_estimate(payload):return failed_module.least_squares(1)
        fail_estimate.evidence_kind=LABEL
        def failed_outer(payload):return failed.invoke_alias(failed_module,fail_estimate,payload)
        failed_outer.evidence_kind=LABEL
        failed=D1BBudget(test_cap=1,test_estimator=failed_outer,journal_path=REPORT/'inner_failure.jsonl')
        with failed.for_frame('failure'):
            with self.assertRaises(ArithmeticError):failed.estimator('MODEL_SPECIAL_TEST_WLS',branch_id='QM_F3_STREAM_A')({})
        self.assertEqual(failed.accounting['least_squares_failed'],1);self.assertIs(failed_module.least_squares,fail_solver);failed.journal.close()

    def test_shared_budget_clone_and_special_identities(self):
        b=D1BBudget(test_cap=3,test_estimator=estimate_stub);f=build_fixture();branch=QMBranch(f,name='QM_B0_KEEP');branch.budget=b
        self.assertIs(branch._transaction_clone().budget,b)
        for name in SPECIAL_IDS:
            with b.for_branch(name),b.for_frame(name+':test'):
                cb=b.estimator('MODEL_SPECIAL_TEST_WLS');self.assertEqual(cb.branch_id,name);cb({})
            with self.assertRaisesRegex(ValueError,'special category'):b.estimator('MODEL_OBSERVATION_WLS',branch_id=name)
        self.assertEqual(b.counts['MODEL_SPECIAL_TEST_WLS'],3)
        path=REPORT/'unfinished_started.jsonl';journal=CallJournal(path,'TEST')
        journal.append(level='OUTER',status='STARTED',outer_call_id='O1',inner_call_id=None);journal.close()
        self.assertEqual(inspect_journal(path)['status'],'RESOURCE_LEDGER_INCOMPLETE')

    def test_f2_trusted_valid_history_source_and_inheritance(self):
        source,b,_=synthetic_source();bundle=verify_special_source('QM_F2_VALID_HISTORY',source,test=True)
        self.assertEqual(json.loads(bundle.source_json)['source_verification'],'BEFORE_HISTORY_CACHE_INITIALIZATION')
        cache=inherited_cache(bundle,test=True);frame=special_frame(bundle,cache)
        self.assertEqual(cache.counts['new'],0);self.assertEqual(cache.counts['inherited_reuses'],2)
        self.assertEqual([x['sensor_id'] for x in frame['records']],['U0','U2'])
        original=json.loads(bundle.slots_json)
        for item,record in zip(original,frame['records']):
            copied=dict(record);copied.pop('packet_id');self.assertEqual(copied,item['slot']['packet'])
        budget=D1BBudget(test_cap=1,test_estimator=estimate_stub);result=run_special('QM_F2_VALID_HISTORY',source,budget,test_processor_factory=FakeProcessor)
        self.assertEqual(budget.counts['MODEL_SPECIAL_TEST_WLS'],1);self.assertEqual(result['raw_counts']['new'],0)
        for field,value in [('sigma',.2),('health','missing'),('position',[0.,0.])]:
            context=dict(original[0]['context']);context[field]=value
            with self.assertRaisesRegex(ValueError,'Historical raw context conflict'):cache.query('QM_F2_VALID_HISTORY',0,0,80,context,lambda:None)
        wrong,_,_=synthetic_source('QM_B0_KEEP')
        with self.assertRaisesRegex(ValueError,'F2_SOURCE_NOT_AVAILABLE'):verify_special_source('QM_F2_VALID_HISTORY',wrong,test=True)
        data=Path(source.path).read_bytes();Path(source.path).write_bytes(data+b' ')
        with self.assertRaisesRegex(ValueError,'SOURCE_FILE_HASH_MISMATCH'):verify_special_source('QM_F2_VALID_HISTORY',source,test=True)

    def test_f2_unqueried_fixture_contract_preserved(self):
        f=build_fixture();before=deepcopy(f.view)
        save(REPORT/'FULL_FIXTURE_IDENTITY.json',dict(fixture_digest=digest(dict(view=f.view,seed=f.seed,identity=f.identity)),world_digest=f.world['world_digest'],motion_rule=f.world['motion_rule'],fixture_identity=f.identity,scope='STRUCTURAL_UNFUSED_MODEL_ONLY'))
        self.assertTrue(all(s['state']=='UNQUERIED' for s in f.view['current_slots']));self.assertFalse(f.identity['fused'])
        source,_,_=synthetic_source();verify_special_source('QM_F2_VALID_HISTORY',source,test=True)
        self.assertEqual(f.view,before);self.assertEqual(validate_fixture(f)['status'],'STRUCTURALLY_VALIDATED_UNFUSED_MODEL_FIXTURE')
        bad=deepcopy(f);bad.view['current_slots'][0]['state']='VALID'
        with self.assertRaisesRegex(ValueError,'unfused/unassigned'):validate_fixture(bad)
        with self.assertRaises(PermissionError):inherited_cache(verify_special_source('QM_F2_VALID_HISTORY',source,test=True))

    def test_f3_independent_stream_positive_and_negative_contract(self):
        a,_,_=synthetic_source('QM_B0_KEEP');b,_,_=synthetic_source();shared=D1BBudget(test_cap=2,test_estimator=estimate_stub)
        ra=run_special('QM_F3_STREAM_A',a,shared,test_processor_factory=FakeProcessor);rb=run_special('QM_F3_STREAM_B',b,shared,test_processor_factory=FakeProcessor)
        self.assertNotEqual(ra['frame']['stream_id'],rb['frame']['stream_id']);self.assertEqual(shared.counts['MODEL_SPECIAL_TEST_WLS'],2)
        bundle=verify_special_source('QM_F3_STREAM_A',a,test=True);cache=inherited_cache(bundle,test=True)
        cache.history[0]['slot']['packet']['bearing']+=.1
        with self.assertRaisesRegex(ValueError,'Inherited measurement changed'):special_frame(bundle,cache)
        cache=inherited_cache(bundle,test=True);cache.branch='QM_F3_STREAM_B'
        with self.assertRaisesRegex(ValueError,'cache branch mismatch'):special_frame(bundle,cache)
        packet_bad=deepcopy(ra['frame']);packet_bad['records'][0]['sigma']*=2
        with self.assertRaisesRegex(ValueError,'verified raw source'):validate_special_frame(packet_bad,'QM_F3_STREAM_A',bundle)
        for result in (ra,rb):
            self.assertEqual(result['raw_counts']['new'],0)
            frame=deepcopy(result['frame']);frame['stream_id']='QM_F3_STREAM_A:wrong'
            with self.assertRaises(ValueError):validate_special_frame(frame,result['special_id'])
            pending=dict(branch_id=result['special_id'],target_id=0,stream_id=result['frame']['stream_id'])
            self.assertTrue(validate_pending_identity(pending,result['special_id']))
            for field,value in [('branch_id','wrong'),('target_id',1),('stream_id','wrong')]:
                bad=dict(pending);bad[field]=value
                with self.assertRaises(ValueError):validate_pending_identity(bad,result['special_id'])
        with self.assertRaisesRegex(ValueError,'F3_SOURCE_NOT_AVAILABLE'):verify_special_source('QM_F3_STREAM_A',b,test=True)
        self.assertEqual(shared.counts['MODEL_SPECIAL_TEST_WLS'],2)

    def test_admission_requires_trusted_raw_frame_wls_evidence(self):
        old,_,_=synthetic_source('QM_PROBE_OLD',.02);new,_,_=synthetic_source('QM_PROBE_DEGRADED_3',.16)
        candidate=candidate_from_sources(old,new,.16,test=True);row=json.loads(candidate.row_json)
        self.assertTrue(row['old_G']);self.assertTrue(row['new_G']);self.assertEqual(row['old_Q'],'PASS');self.assertEqual(row['new_Q'],'FAIL')
        with self.assertRaises(PermissionError):freeze_admission([candidate],'SYNTHETIC_BATCH')
        with self.assertRaises(PermissionError):freeze_admission([dict(old_G=True,new_G=True,old_Q='PASS',new_Q='FAIL')],'SYNTHETIC_BATCH')
        with self.assertRaises(PermissionError):candidate_from_sources(old,new,.16)

    def test_independent_g_q_recomputation_contract(self):
        source,_,_=synthetic_source('QM_PROBE_OLD',.02);_,r,records=read_verified_source(source,test=True)
        row=next(x for x in records['feedback'] if x['endpoint']['tick']==80);ep=row['endpoint']
        check=independent_gq(ep,records,r['world'],r['view']['config'],source.registration,side='RIGHT');self.assertEqual(check['Q'],'PASS')
        wrong=deepcopy(records);bad=deepcopy(ep);bad['G']=not ep['G'];wrong['feedback'][-1]['endpoint']=bad
        with self.assertRaisesRegex(ValueError,'INDEPENDENT_G_MISMATCH'):independent_gq(bad,wrong,r['world'],r['view']['config'],source.registration,side='RIGHT')
        wrong=deepcopy(records);bad=deepcopy(ep);bad['quality']['radius_proxy']*=2
        wrong['feedback'][-1]['endpoint']=bad;wrong['feedback'][-1]['result']['quality']=deepcopy(bad['quality'])
        with self.assertRaisesRegex(ValueError,'INDEPENDENT_Q_MISMATCH'):independent_gq(bad,wrong,r['world'],r['view']['config'],source.registration,side='RIGHT')

    def test_release_freeze_manifest_and_no_run_authorization(self):
        manifest=json.loads((REPORT/'RUN_G1_FREEZE_CANDIDATE.json').read_bytes())
        self.assertEqual(manifest['status'],'PROPOSED_NOT_AUTHORIZED');self.assertIsNone(manifest['real_approval_sha256'])
        self.assertEqual(manifest['outer_wls_proposal'],292);self.assertEqual(manifest['inner_solver_proposal'],2628)
        for file,wanted in manifest['source_pins'].items():self.assertEqual(sha(ROOT/file),wanted)
        for name in ('scripts.stfbs_d1b_qm_run_g1','scripts.stfbs_d1b_qm_run_g1_watchdog'):self.assertNotIn(name,sys.modules)
        self.assertFalse(AUTHORITY_PATH.exists());self.assertFalse((ROOT/'runs/SYNTHETIC_NEVER_CREATE').exists())
        with self.assertRaisesRegex(PermissionError,'APPROVAL_NOT_VERIFIED'):require_run_g1(True)
        save(REPORT/'PURE_APPROVAL_TEST_RESULT.json',dict(status='PASS',real_permission=False,independent_root_present=False,evidence_kind=LABEL,formal_g1_scripts_executed=False))
