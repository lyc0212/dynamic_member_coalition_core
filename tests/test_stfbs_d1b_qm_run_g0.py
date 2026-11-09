"""Ten RUN-G0 nonphysical tests, with explicit synthetic provenance."""
from unittest import TestCase
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import ast,json,hashlib
from research.non_oracle.stfbs_d1b_qm_scenario import build_fixture,TEST_DOUBLE
from research.non_oracle.stfbs_d1b_qm_execution import ProbeSchedule,DynamicSchedule,PROBES,selector
from research.non_oracle.stfbs_d1b_qm_budget import D1BBudget
from research.non_oracle.stfbs_d1b_qm_run_release import (prepare_probe_branch,prepare_dynamic_branch,prepare_b3_branch,
    freeze_admission,verify_admission,MissingSensorAuthority,missing_slot_structure,execute_probe,execute_dynamic)
from research.non_oracle.stfbs_d1b_qm_run_audit import (SourceAnchor,register_verified_fixture,verify_verified_registration,
    verify_source_pins,endpoint_join,EndpointEvidenceError,active_registry,save)
from research.non_oracle.stfbs_d1b_qm_independent_audit import audit_registered
from research.non_oracle.stfbs_d1a_replay import digest
from research.information_service_online.public import seal_slot
from research.information_service.public_quality import prepare_frame

ROOT=Path(__file__).resolve().parents[1];REPORT=ROOT/'reports/stfbs_lite_d1b_qm_run_g0_001'
CALLS=[]

def policy_anchor():
    p=json.loads((REPORT/'RUN_POLICY.json').read_bytes());return p['source_pins'],SourceAnchor(p['head']+':RUN_G0_SOURCE_MANIFEST',json.dumps(p['source_pins'],sort_keys=True))

def registration(fixture,name):
    pins,anchor=policy_anchor();return register_verified_fixture(ROOT,fixture,name,pins,anchor)

def admission(sigma=.16):
    rows=[]
    for index,value in enumerate((.04,.08,.16,.32)):
        rows.append(dict(probe_id='QM_PROBE_DEGRADED_'+str(index+1),sigma=value,old_G=True,new_G=True,old_Q='PASS',new_Q='FAIL' if value==sigma else 'PASS',evidence_kind=TEST_DOUBLE))
        if value==sigma:break
    return freeze_admission(rows,'SYNTHETIC_G0_NOT_A_REAL_RUN')

def make(name='QM_B0_KEEP',budget=None):
    f=build_fixture();reg=registration(f,name);budget=D1BBudget() if budget is None else budget
    if name in PROBES:b=prepare_probe_branch(f,name,budget,reg)
    elif name=='QM_B3_UNKNOWN':b=prepare_b3_branch(f,budget,reg)
    else:b=prepare_dynamic_branch(f,name,budget,reg,selected_sigma=.16,admission=admission())
    return b,reg,f

def fake_fuse(b,j,s,tick):
    active_registry().note_double('transaction-owned synthetic left endpoint, no real fusion')
    cb=b.budget.estimator('MODEL_OBSERVATION_WLS');assert cb.ledger_id==b.budget.ledger_id and cb.branch_id==b.name
    CALLS.append((b.name,tick))
    b.consumer.enqueue(dict(target_id=j,measurement_tick=tick,available_tick=tick,estimate=None,label='LEFT'+str(tick),provenance='SIMULATED',observation_origin='MODEL',evidence_kind=TEST_DOUBLE))
    return dict(branch=b.name,tick=tick,target_id=j,team=deepcopy(s['team']),G=True,quality=dict(status='PASS',evidence_kind=TEST_DOUBLE),provenance='SIMULATED',observation_origin='MODEL',evidence_kind=TEST_DOUBLE)
fake_fuse.evidence_kind=TEST_DOUBLE

class SyntheticPort:
    evidence_kind=TEST_DOUBLE
    def __init__(self,b):
        self.b=b;self.trace=[];self.frozen_inputs={}
        self._sensor_authority=SimpleNamespace(publish_from_executor=self.publish)
    def __getattr__(self,n):return getattr(self.b,n)
    def publish(self,tick):self.trace.append(('PUBLIC',tick));self.b._sensor_authority.publish_from_executor(tick)
    def policy_view(self):
        if self.b.tick!=self.b._last_public_cut:
            self.frozen_inputs[self.b.tick]=[x['label'] for x in self.b.consumer.pending];self.trace.append(('FREEZE',self.b.tick))
        return self.b.policy_view()
    def assign(self,actions):self.trace.append(('ASSIGN',self.b.tick));self.b.assign(actions)
    def advance(self):
        # Pure synthetic cut, not a Branch.advance invocation or a trajectory.
        b=self.b;b.tick=80 if b.tick==60 else 100
        for h in b.histories.values():h['cutoff_tick']=b.tick
        s=b.segment(0);s['latest_endpoint']=dict(tick=b.tick,target_id=0,team=deepcopy(s['team']),branch=b.name,G=True,quality=dict(status='PASS',evidence_kind=TEST_DOUBLE),provenance='SIMULATED',observation_origin='MODEL',evidence_kind=TEST_DOUBLE)
        b.consumer.enqueue(dict(target_id=0,measurement_tick=b.tick,available_tick=b.tick,estimate=None,label='RIGHT'+str(b.tick),provenance='SIMULATED',observation_origin='MODEL',evidence_kind=TEST_DOUBLE))
        self.trace.extend([('OLD_RIGHT',b.tick),('SETTLE',b.tick)])

def evidence(name='QM_B0_KEEP',team=None,start=60):
    active_registry().note_double('complete synthetic raw/frame/result/history cross-record evidence, not a Q result')
    team=team or [dict(robot_id=0,role='dual_neg45'),dict(robot_id=1,role='dual_pos45')]
    stream=name+':T0:first'+str(start);fid=stream+':tick80'
    positions=[[9.,10.],[10.,10.],[11.,10.]]
    profiles=[dict(sensor_id='U'+str(i),sigma=.16 if i==1 else .02,health='available',observed_tick=80) for i in range(3)]
    cache={};slots=[];packets=[]
    for member in team:
        i=member['robot_id'];packet=dict(sensor_id='U'+str(i),position=positions[i],bearing=.1*i,sigma=profiles[i]['sigma'],measurement_tick=80,available_tick=80,status='ok')
        slot=seal_slot(dict(slot_key=dict(target_id=0,robot_id=i,tick=80),state='VALID',packet=packet,slot_digest=None));slots.append(slot)
        context=dict(position=positions[i],sigma=profiles[i]['sigma'],health='available')
        cache[(name,0,i,80)]=dict(slot=deepcopy(slot),slot_digest=digest(slot),context_digest=digest(context))
        packets.append(dict(packet,packet_id=stream+':tick80:U'+str(i)))
    frame=dict(contract_id='STAGE2A5B-A-MINIMAL-v0.2',stream_id=stream,frame_id=fid,target_id=0,tick=80,measurement_time=4.,available_time=4.,records=packets)
    prepared=prepare_frame(frame,[x['sensor_id'] for x in packets])
    quality=dict(status='PASS',frame_id=fid,evidence_kind=TEST_DOUBLE)
    endpoint=dict(branch=name,tick=80,target_id=0,team=deepcopy(team),G=True,quality=quality,provenance='SIMULATED',observation_origin='MODEL')
    result=dict(prepared,execution_contract_id='SYNTHETIC_G0',frame_id=fid,stream_id=stream,target_id=0,tick=80,start_tick=start,estimate_result=dict(evidence_kind=TEST_DOUBLE),quality=deepcopy(quality),skipped=False,estimator_called=False,duplicate=False)
    segment=dict(segment_id=name+':synthetic-segment'+str(start),target_id=0,segment_index=0,previous_segment_id=None,start_tick=start,team=deepcopy(team),closure=None,model_branch_id=name,latest_endpoint=deepcopy(endpoint),events=[],provenance='SIMULATED',observation_origin='MODEL',evidence_kind=TEST_DOUBLE)
    records=dict(feedback=[dict(frame=frame,result=result,endpoint=deepcopy(endpoint),slots=slots)],histories={0:dict(segments=[segment])},cache=cache,physical_profiles={80:profiles},positions={80:positions})
    f=build_fixture();reg=registration(f,name)
    return endpoint,records,reg.registration,segment['segment_id']

class RunG0Tests(TestCase):
    def test_probe_schedule_independent_identities(self):
        shared=D1BBudget();branches=[];start=len(CALLS)
        with active_registry().fake_scope('five independent prefix schedules, zero physical ticks',fake_fuse):
            for name in PROBES:
                b,reg,_=make(name,shared);p=SyntheticPort(b);out=ProbeSchedule(p,name).run_to_80()
                self.assertEqual(out['tick'],80);self.assertFalse(out['terminal_penalty_applied']);self.assertEqual(b.components['terminal'],0)
                self.assertEqual(len([x for x in CALLS[start:] if x==(name,60)]),1)
                self.assertEqual(len(b.boundaries),1);self.assertIs(b.budget,shared);self.assertEqual(audit_registered(b,reg.registration)['status'],'PASS');branches.append(b)
                with self.assertRaisesRegex(ValueError,'Probe'):selector(name)
        self.assertEqual(len({id(b.cache) for b in branches}),5);self.assertEqual(len({id(b.consumer) for b in branches}),5)
        self.assertEqual(shared.snapshot()['total'],0)

    def test_probe_same_geometry_and_no_dynamic_substitution(self):
        with active_registry().fake_scope('synthetic common geometry; not actual equality of independent physical prefixes',fake_fuse):
            points=[]
            for name in PROBES:
                b,_,_=make(name);ProbeSchedule(SyntheticPort(b),name).run_to_80();points.append(b.positions.tolist())
                self.assertEqual(b.world['motion_rule'],'constant_velocity_from_public_D60_v1')
            self.assertTrue(all(p==points[0] for p in points))
        old,records,_,_=evidence('QM_PROBE_OLD');_,_,dynamic,_=evidence()
        relabel=deepcopy(old);relabel['branch']='QM_B0_KEEP'
        with self.assertRaisesRegex(EndpointEvidenceError,'scientific identity conflict'):endpoint_join(relabel,records,dynamic)

    def test_selected_sigma_explicitly_binds_b0_b1(self):
        a=admission(.16);results=[]
        for name in ('QM_B0_KEEP','QM_B1_MEMBER_CHANGE'):
            f=build_fixture();reg=registration(f,name)
            with self.assertRaises(TypeError):prepare_dynamic_branch(f,name,D1BBudget(),reg,admission=a)
            with self.assertRaisesRegex(ValueError,'mismatch'):prepare_dynamic_branch(f,name,D1BBudget(),reg,selected_sigma=.08,admission=a)
            b=prepare_dynamic_branch(f,name,D1BBudget(),reg,selected_sigma=.16,admission=a)
            self.assertEqual(b._sensor_authority.physical_profile_at(79)[1]['sigma'],.02)
            b._sensor_authority.publish_from_executor(80)
            self.assertEqual(b._sensor_authority.public_snapshot().public_profile_at(80)[1]['sigma'],.16)
            ep,records,ctx,sid=evidence(name);self.assertEqual(endpoint_join(ep,records,ctx,segment_id=sid,side='RIGHT')['status'],'PASS');results.append(b)
        self.assertIsNot(results[0].cache,results[1].cache)
        with self.assertRaisesRegex(ValueError,'mismatch'):verify_admission(a,.08)

    def test_b3_missing_authority_and_slot_structure(self):
        b,_,_=make('QM_B3_UNKNOWN');normal,_,_=make()
        self.assertEqual(b._sensor_authority.physical_profile_at(79)[1]['health'],'available')
        p=b._sensor_authority.physical_profile_at(80);self.assertEqual(p[1]['health'],'missing');self.assertEqual(p[1]['sigma'],.02)
        self.assertTrue(all(p[i]['health']=='available' for i in (0,2)))
        with self.assertRaisesRegex(ValueError,'FUTURE'):b._sensor_authority.public_snapshot().public_profile_at(80)
        slot=missing_slot_structure(b._sensor_authority,80)
        self.assertEqual(slot['state'],'MISSING');self.assertIsNone(slot['packet']);self.assertEqual(b.cache.rows,{})
        b._sensor_authority.publish_from_executor(80);self.assertEqual(b._sensor_authority.public_snapshot().public_profile_at(80)[1]['health'],'missing')
        self.assertEqual(normal._sensor_authority.physical_profile_at(80)[1]['health'],'available')
        tree=ast.parse((ROOT/'research/non_oracle/stfbs_d1b_qm_run_release.py').read_text())
        node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MissingSensorAuthority')
        self.assertNotIn('UNKNOWN',ast.unparse(node));self.assertNotIn('quality',ast.unparse(node))

    def test_endpoint_cross_record_positive_and_relabel_rejection(self):
        outcomes=[]
        for name in ('QM_B0_KEEP','QM_B1_MEMBER_CHANGE'):
            ep,records,reg,sid=evidence(name);self.assertEqual(endpoint_join(ep,records,reg,segment_id=sid,side='RIGHT')['status'],'PASS')
            old,old_records,_,_=evidence('QM_PROBE_OLD');tampered=deepcopy(old);tampered['branch']=name
            with self.assertRaisesRegex(EndpointEvidenceError,'feedback endpoint scientific identity conflict') as caught:endpoint_join(tampered,old_records,reg)
            self.assertEqual(set(tampered),set(old));self.assertEqual({k:v for k,v in old.items() if k!='branch'},{k:v for k,v in tampered.items() if k!='branch'})
            outcomes.append(dict(branch=name,result='REJECTED',reason=str(caught.exception),mutation='endpoint.branch only',old_endpoint=old,relabelled_endpoint=tampered,evidence_kind=TEST_DOUBLE))
        save(REPORT/'ENDPOINT_PROVENANCE_NEGATIVE_TESTS.json',dict(status='PASS',cases=outcomes))

    def test_endpoint_raw_frame_conflict_and_ambiguity_rejection(self):
        ep,records,reg,sid=evidence();self.assertEqual(endpoint_join(ep,records,reg,segment_id=sid)['status'],'PASS')
        mutations=[]
        bad=deepcopy(records);key=next(iter(bad['cache']));row=bad['cache'].pop(key);bad['cache'][('QM_PROBE_OLD',*key[1:])]=row;mutations.append(('raw key scientific identity',ep,bad))
        bad=deepcopy(records);bad['feedback'][0]['result']['stream_id']='QM_PROBE_OLD:T0:first60';mutations.append(('fusion result/quality',ep,bad))
        bad=deepcopy(records);bad['feedback'][0]['frame']['records'][1]['sigma']=.08;mutations.append(('normalized WLS input',ep,bad))
        bad=deepcopy(records);key=next(iter(bad['cache']));bad['cache'][key]['context_digest']='changed';mutations.append(('raw context',ep,bad))
        wrong=deepcopy(ep);wrong['tick']=79;mutations.append(('scientific identity conflict',wrong,records))
        wrong=deepcopy(ep);wrong['team']=list(reversed(ep['team']));mutations.append(('scientific identity conflict',wrong,records))
        bad=deepcopy(records);bad['histories'][0]['segments'].append(dict(deepcopy(bad['histories'][0]['segments'][0]),segment_id='second'));mutations.append(('service segment ambiguity',ep,bad))
        for reason,endpoint,raw in mutations:
            with self.assertRaisesRegex(EndpointEvidenceError,reason):endpoint_join(endpoint,raw,reg)
        # Two legitimate streams may reuse U0 raw, but their packet IDs differ.
        newteam=[dict(robot_id=0,role='dual_neg45'),dict(robot_id=2,role='dual_pos45')]
        new,newrecords,_,newsid=evidence('QM_B1_MEMBER_CHANGE',newteam,80)
        old,oldrecords,ctx,oldsid=evidence('QM_B1_MEMBER_CHANGE')
        oldrecords['histories'][0]['segments'][0]['closure']=dict(at=dict(time_seconds=4.))
        oldrecords['histories'][0]['segments'].extend(newrecords['histories'][0]['segments'])
        oldrecords['feedback'].extend(newrecords['feedback']);oldrecords['cache'].update(newrecords['cache'])
        self.assertEqual(endpoint_join(old,oldrecords,ctx,segment_id=oldsid,side='RIGHT')['status'],'PASS')
        self.assertEqual(endpoint_join(new,oldrecords,ctx,segment_id=newsid,side='LEFT')['status'],'PASS')
        self.assertNotEqual(oldrecords['feedback'][0]['frame']['records'][0]['packet_id'],oldrecords['feedback'][1]['frame']['records'][0]['packet_id'])

    def test_source_pins_real_bytes_and_frozen_anchor(self):
        pins,anchor=policy_anchor();results=verify_source_pins(ROOT,pins,anchor);self.assertTrue(all(x['match'] for x in results))
        data=(ROOT/'research/non_oracle/stfbs_d1b_qm_run_release.py').read_bytes();copy=REPORT/'source_copy.py.txt';copy.write_bytes(data)
        relative=copy.relative_to(ROOT).as_posix();expected={relative:hashlib.sha256(data).hexdigest()};fixed=SourceAnchor('PRE_MUTATION_TEST_COPY',json.dumps(expected))
        self.assertEqual(len(verify_source_pins(ROOT,expected,fixed)),1)
        copy.write_bytes(data+b'\n# synthetic corruption\n')
        with self.assertRaisesRegex(ValueError,'SOURCE_BYTES_MISMATCH'):verify_source_pins(ROOT,expected,fixed)
        changed={relative:hashlib.sha256(copy.read_bytes()).hexdigest()}
        with self.assertRaisesRegex(ValueError,'SOURCE_ANCHOR_MISMATCH'):verify_source_pins(ROOT,changed,fixed)
        absent={relative+'.absent':expected[relative]}
        with self.assertRaisesRegex(ValueError,'MISSING'):verify_source_pins(ROOT,absent,SourceAnchor('test',json.dumps(absent)))
        bad={'../outside':expected[relative]}
        with self.assertRaisesRegex(ValueError,'PATH_REJECTED'):verify_source_pins(ROOT,bad,SourceAnchor('test',json.dumps(bad)))
        save(REPORT/'SOURCE_PINS_VERIFICATION.json',dict(status='PASS',verified=results,test_copy_negative_cases=['changed bytes','self-rehash differs from frozen anchor','missing copy','path traversal'],real_sources_modified=False))

    def test_external_registration_tamper_rejection(self):
        b,verified,f=make();self.assertEqual(audit_registered(b,verified.registration)['status'],'PASS')
        b._audit_context=None;self.assertEqual(audit_registered(b,verified.registration)['status'],'PASS')
        with self.assertRaisesRegex(ValueError,'mismatch'):verify_verified_registration(ROOT,f,'QM_B1_MEMBER_CHANGE',verified)
        b.histories[0]['events'][0]['reasons']=['tampered']
        with self.assertRaisesRegex(ValueError,'prefix modified'):audit_registered(b,verified.registration)
        wrong=deepcopy(f);wrong.seed['provenance']='ACTUAL'
        with self.assertRaises(ValueError):verify_verified_registration(ROOT,wrong,b.name,verified)

    def test_budget_proposal_and_fail_closed_estimator(self):
        active_registry().note_double('outer estimator and nine inner solver simulations; no real estimate/least_squares')
        holder={}
        def solver(x):return x
        solver.evidence_kind=TEST_DOUBLE
        def fake(payload):
            for k in range(9):holder['budget'].record_solver(solver,k)
            return {'synthetic':True}
        fake.evidence_kind=TEST_DOUBLE
        budget=D1BBudget(test_cap=1,test_estimator=fake);holder['budget']=budget
        callback=budget.estimator('MODEL_OBSERVATION_WLS',branch_id='QM_B0_KEEP');callback({})
        a=budget.snapshot()['accounting'];self.assertEqual(a['outer_wls_started'],1);self.assertEqual(a['least_squares_started'],9)
        self.assertEqual(a['outer_wls_returned'],1);self.assertEqual(a['least_squares_returned'],9)
        with self.assertRaisesRegex(RuntimeError,'SHARED_CAP'):callback({})
        self.assertEqual(budget.accounting['budget_rejected'],1);self.assertEqual(budget.counts['MODEL_OBSERVATION_WLS'],1)
        def failing_solver(x):raise ArithmeticError('synthetic solver failure')
        failing_solver.evidence_kind=TEST_DOUBLE
        def fail(payload):
            failure.record_solver(solver,0);failure.record_solver(failing_solver,1)
        fail.evidence_kind=TEST_DOUBLE
        failure=D1BBudget(test_cap=2,test_estimator=fail);b,_,_=make(budget=failure);staged=b._transaction_clone()
        with self.assertRaisesRegex(ArithmeticError,'synthetic'):staged.budget.estimator('MODEL_SPECIAL_TEST_WLS',branch_id=b.name)({})
        self.assertIs(staged.budget,failure);self.assertEqual(failure.accounting['outer_wls_failed'],1)
        self.assertEqual(failure.accounting['least_squares_started'],2);self.assertEqual(failure.accounting['least_squares_failed'],1)
        self.assertEqual(failure.accounting['least_squares_returned'],1);self.assertEqual(sum(failure.counts.values()),failure.accounting['outer_wls_started'])
        empty=D1BBudget()
        with self.assertRaisesRegex(RuntimeError,'NO_APPROVED'):empty.estimator('MODEL_SPECIAL_TEST_WLS',branch_id=b.name)({})
        with self.assertRaisesRegex(PermissionError,'RUN_G1_NOT_AUTHORIZED'):empty.bind_real_estimator(True)
        self.assertEqual(empty.accounting['outer_wls_started'],0);self.assertEqual(empty.accounting['least_squares_started'],0)
        proposal=json.loads((REPORT/'RUN_G1_BUDGET_PROPOSAL.json').read_bytes());self.assertEqual(proposal['main_outer_upper_bound'],289)
        self.assertEqual(proposal['status'],'PROPOSED_NOT_AUTHORIZED');self.assertFalse(proposal['run_g1_authorized'])
        save(REPORT/'BUDGET_ACCOUNTING_TEST_EVIDENCE.json',dict(success=budget.snapshot(),failed=failure.snapshot(),unapproved=empty.snapshot(),evidence_kind=TEST_DOUBLE))

    def test_tick80_transaction_ownership_and_no_run_authorization(self):
        start=len(CALLS)
        with active_registry().fake_scope('D60 once; D80 old-right then single transaction-left; D100 KEEP',fake_fuse):
            for name in ('QM_B0_KEEP','QM_B1_MEMBER_CHANGE'):
                b,reg,f=make(name);p=SyntheticPort(b);s=DynamicSchedule(p,name);s.start();s.advance_one()
                self.assertEqual(len([x for x in CALLS[start:] if x==(name,60)]),1)
                self.assertEqual(len([x for x in CALLS[start:] if x==(name,80)]),int(name=='QM_B1_MEMBER_CHANGE'))
                self.assertEqual(p.trace[:5],[('ASSIGN',60),('OLD_RIGHT',80),('SETTLE',80),('PUBLIC',80),('FREEZE',80)])
                self.assertEqual(p.frozen_inputs[80],['LEFT60','RIGHT80'])
                self.assertEqual([x['label'] for x in b.consumer.pending],['LEFT80'] if name=='QM_B1_MEMBER_CHANGE' else [])
                s.advance_one();self.assertFalse(any(x==(name,100) for x in CALLS[start:]));self.assertEqual(audit_registered(b,reg.registration)['status'],'PASS')
        b,reg,f=make();probe,pr,pf=make('QM_PROBE_OLD')
        for credential in (None,True,{'approved':True,'task':'RUN-G1'}):
            with self.assertRaisesRegex(PermissionError,'RUN_G1_NOT_AUTHORIZED'):execute_probe(pf,probe.name,probe.budget,pr,approval=credential)
            with self.assertRaisesRegex(PermissionError,'RUN_G1_NOT_AUTHORIZED'):execute_dynamic(f,b.name,b.budget,reg,selected_sigma=.16,admission=admission(),approval=credential)
        with self.assertRaisesRegex(PermissionError,'RUN_G1_NOT_AUTHORIZED'):ProbeSchedule(probe,probe.name).start()
        with self.assertRaisesRegex(PermissionError,'RUN_G1_NOT_AUTHORIZED'):DynamicSchedule(b,b.name).start()
        self.assertEqual(active_registry().calls,[])
        for path in ('research/non_oracle/stfbs_d1b_qm_execution.py','research/non_oracle/stfbs_d1b_qm_run_release.py'):
            tree=ast.parse((ROOT/path).read_text());self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='fuse' for n in ast.walk(tree)))
