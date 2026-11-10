"""Four nonphysical regression groups. No physical execution is permitted."""
import ast,json,sys
from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from scripts.stfbs_d1b_qm_b3_minimal_patch_test_entry import active_registry,REPORT,ROOT,save,read,sha
from research.non_oracle.stfbs_d1b_qm_budget import D1BBudget,inspect_journal
from research.non_oracle.stfbs_d1b_qm_scenario import build_fixture
from research.non_oracle.stfbs_d1b_qm_model import QMBranch,initial_team,PublicQueryRejected
from research.non_oracle import stfbs_d1b_qm_execution as execution
from research.non_oracle import stfbs_d1b_qm_run_release as release
from research.non_oracle.stfbs_d1b_qm_run_audit import SourceAnchor,register_verified_fixture
from research.non_oracle.stfbs_d1a_replay import digest
from research.information_service_online.public import seal_slot
from research.information_service_bridge.public_stream import BridgeFrameProcessor
LABEL='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'


def synthetic_estimator(payload):return dict(evidence_kind=LABEL,result='SYNTHETIC_RETURN_ONLY')
synthetic_estimator.evidence_kind=LABEL


def stable(budget):
    d=deepcopy(budget.snapshot())
    d.pop('cpu_seconds');d.pop('wall_seconds')
    return d


def used_budget(tag):
    b=D1BBudget(test_cap=3,test_estimator=synthetic_estimator,journal_path=REPORT/(tag+'.jsonl'),batch_id='B3_PATCH_ENGINEERING_ONLY')
    with b.for_branch('QM_PROBE_OLD'),b.for_frame(tag+':synthetic60'):
        b.estimator('MODEL_OBSERVATION_WLS')({'evidence_kind':LABEL})
    assert b.accounting['outer_wls_started']==b.accounting['outer_wls_returned']==1
    assert b.accounting['least_squares_started']==0 and not b.real_ready
    assert inspect_journal(b.journal.path)['status']=='COMPLETE'
    return b


def registration(fixture):
    pins=read(REPORT/'RUN_POLICY.json')['source_pins']
    return register_verified_fixture(ROOT,fixture,'QM_B3_UNKNOWN',pins,SourceAnchor('ENGINEERING_TEST_ONLY_NOT_REAL_SCIENCE',json.dumps(pins,sort_keys=True)))


def state(b):
    return dict(tick=b.tick,fusions=b.fusions,cache_rows=len(b.cache.rows),cache_counts=dict(b.cache.counts),
                streams=len(b.streams),feedback=len(b.feedback),pending=len(b.consumer.pending),measurements=len(b.consumer.model_measurements),
                actions=deepcopy(b.actions),segments=sum(len(h['segments']) for h in b.histories.values()),boundaries=len(b.boundaries))


class PatchTests(TestCase):
    def create_b3(self,tag):
        fixture=build_fixture();shared=used_budget(tag);before=stable(shared);reg=registration(fixture)
        calls=[]
        def trace(frame,event,arg):
            if event=='call' and frame.f_code.co_filename.endswith(('stfbs_d1b_qm_execution.py','stfbs_d1b_qm_run_release.py','stfbs_d1b_qm_run_audit.py')):
                name=frame.f_code.co_name
                if name in ('prepare_b3_branch','prepare_branch','bind_shared_budget','verify_verified_registration','verify_source_pins'):
                    calls.append(dict(function=name,file=frame.f_code.co_filename,line=frame.f_code.co_firstlineno,
                                      matching_shared_budget=frame.f_locals.get('budget') is shared,
                                      provided_pins_match=frame.f_locals.get('provided')==read(REPORT/'RUN_POLICY.json')['source_pins'] if name=='verify_source_pins' else None))
        previous=sys.getprofile()
        try:
            sys.setprofile(trace)
            b=release.prepare_b3_branch(fixture,shared,reg)
        finally:sys.setprofile(previous)
        self.assertIs(b.budget,shared);self.assertEqual(stable(shared),before)
        self.assertEqual(sum(x['function']=='bind_shared_budget' for x in calls),1)
        self.assertEqual(sum(x['function']=='prepare_b3_branch' for x in calls),1)
        self.assertEqual(sum(x['function']=='verify_verified_registration' for x in calls),1)
        self.assertTrue(any(x['function']=='verify_source_pins' and x['provided_pins_match'] for x in calls))
        self.assertEqual(state(b),dict(tick=60,fusions=0,cache_rows=0,cache_counts=dict(requests=0,new=0,reuses=0,conflicts=0,inherited_reuses=0),streams=0,feedback=0,pending=0,measurements=0,actions=[dict(target=None,role='none') for _ in range(3)],segments=0,boundaries=0))
        self.assertIs(type(b._sensor_authority),release.MissingSensorAuthority)
        authority=b._sensor_authority
        self.assertEqual(authority.physical_profile_at(79)[1]['health'],'available')
        self.assertEqual(authority.physical_profile_at(80)[1]['health'],'missing')
        self.assertEqual(authority.public_snapshot().watermark,60)
        with self.assertRaises(PublicQueryRejected):authority.public_snapshot().public_profile_at(80)
        slot=release.missing_slot_structure(authority,80)
        self.assertEqual((slot['state'],slot['packet']),('MISSING',None))
        authority.publish_from_executor(80)
        self.assertEqual(authority.public_snapshot().public_profile_at(80)[1]['health'],'missing')
        evidence=dict(evidence_kind=LABEL,calls=calls,synthetic_shared_budget_history_calls=1,real_scientific_calls=0,
                      budget_before=before,budget_after=stable(shared),initial_state=state(b),registration_digest=reg.registration.registration_digest,
                      source_anchor=reg.anchor.source_version,patched_source_sha256=sha(ROOT/'research/non_oracle/stfbs_d1b_qm_run_release.py'),
                      missing_slot=slot,public_watermark_before=60,public_watermark_after=80)
        return b,shared,evidence

    def test_T1_real_b3_used_budget(self):
        b,shared,e=self.create_b3('T1');shared.journal.close();save(REPORT/'T1_EVIDENCE.json',e)

    def test_T2_polluted_branch_rejected(self):
        shared=used_budget('T2_shared');before=stable(shared);f=build_fixture();rows=[]
        historical=read(ROOT/'runs/stfbs_lite_d1b_qm_run_g1_20261110_001/QM_B0_KEEP.json')['result']
        cases=('tick','cache_rows','cache_requests','feedback','pending','assignment','segments','streams','boundaries','model_measurements','fusions','local_budget')
        for case in cases:
            b=QMBranch(f,name='QM_B3_UNKNOWN');local=b.budget;owned=None
            if case=='tick':b.tick=61
            elif case=='cache_rows':
                slot=seal_slot(dict(slot_key=dict(target_id=0,robot_id=1,tick=80),state='MISSING',packet=None,slot_digest=None))
                context=dict(position=b.positions[1].tolist(),sigma=.02,health='missing')
                b.cache.rows[(b.name,0,1,80)]=dict(context_digest=digest(context),slot=slot,slot_digest=digest(slot))
            elif case=='cache_requests':b.cache.counts['requests']=1
            elif case=='feedback':b.feedback=[deepcopy(historical['feedback'][0])]
            elif case in ('pending','model_measurements'):
                row=dict(target_id=0,measurement_tick=60,available_tick=60,position=[9.,10.],provenance='SIMULATED',observation_origin='MODEL')
                if case=='pending':b.consumer.pending=[row]
                else:b.consumer.model_measurements=[row]
            elif case=='assignment':b.actions=initial_team()
            elif case=='segments':b.histories[0]=deepcopy(historical['histories']['0']) if isinstance(historical['histories'],dict) else deepcopy(historical['histories'][0])
            elif case=='streams':b.streams['QM_B3_UNKNOWN:T0:first60']=BridgeFrameProcessor(['U0','U1'],60,'QM_B3_UNKNOWN:T0:first60',0)
            elif case=='boundaries':b.boundaries=[deepcopy(historical['boundaries'][0])]
            elif case=='fusions':b.fusions=1
            elif case=='local_budget':owned=used_budget('T2_local');b.budget=owned;local=owned
            pre=state(b);local_before=stable(local) if isinstance(local,D1BBudget) else None
            with self.assertRaisesRegex(ValueError,'^Unsafe late budget takeover$'):execution.bind_shared_budget(b,shared)
            self.assertIs(b.budget,local);self.assertEqual(state(b),pre);self.assertEqual(stable(shared),before)
            if local_before is not None:self.assertEqual(stable(local),local_before)
            rows.append(dict(case=case,status='PASS',before=pre,after=state(b),budget_identity_preserved=True,shared_budget_unchanged=True))
            if owned:owned.journal.close()
        shared.journal.close();save(REPORT/'T2_EVIDENCE.json',dict(cases=rows,evidence_kind=LABEL))

    def test_T3_repeat_takeover_rejected(self):
        b,shared,e=self.create_b3('T3');before=stable(shared);pre=state(b)
        with self.assertRaisesRegex(ValueError,'^Unsafe late budget takeover$'):execution.bind_shared_budget(b,shared)
        self.assertIs(b.budget,shared);self.assertEqual(stable(shared),before);self.assertEqual(state(b),pre)
        shared.journal.close();e['repeat_takeover_rejected']=True;save(REPORT/'T3_EVIDENCE.json',e)

    def test_T4_static_and_guards(self):
        tree=ast.parse((ROOT/'research/non_oracle/stfbs_d1b_qm_run_release.py').read_text())
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare_b3_branch')
        names=[n.func.id for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        self.assertEqual(names.count('prepare_branch'),1);self.assertNotIn('bind_shared_budget',names)
        self.assertIn('verify_verified_registration',names);self.assertIn('MissingSensorAuthority',names)
        core=ast.parse((ROOT/'research/non_oracle/stfbs_d1b_qm_run_evidence.py').read_text())
        node=next(n for n in core.body if isinstance(n,ast.FunctionDef) and n.name=='coordinate_batch')
        calls=sorted((n.lineno,n.func.attr,[a.value for a in n.args if isinstance(a,ast.Constant)]) for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='ops' and n.func.attr in ('b3','f1','special','final_science'))
        self.assertEqual([x[1] for x in calls],['b3','f1','special','special','special','final_science'])
        self.assertEqual([x[2][0] for x in calls if x[1]=='special'],['QM_F2_VALID_HISTORY','QM_F3_STREAM_A','QM_F3_STREAM_B'])
        special=(ROOT/'research/non_oracle/stfbs_d1b_qm_run_specials.py').read_text()
        st=ast.parse(special)
        specs=next(n.value for n in st.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SPECS' for t in n.targets))
        self.assertEqual(ast.literal_eval(specs),{'QM_F2_VALID_HISTORY':('QM_B1_MEMBER_CHANGE','LEFT',(0,2)),'QM_F3_STREAM_A':('QM_B0_KEEP','RIGHT',(0,1)),'QM_F3_STREAM_B':('QM_B1_MEMBER_CHANGE','LEFT',(0,2))})
        self.assertIn("budget.estimator('MODEL_SPECIAL_TEST_WLS')",special)
        source=(ROOT/'research/non_oracle/stfbs_d1b_qm_run_evidence.py').read_text()
        self.assertIn("extra_wls=0",source)
        self.assertIn("if budget.real_ready:",(ROOT/'research/non_oracle/stfbs_d1b_qm_execution.py').read_text())
        base=read(REPORT/'BASELINE.json');policy=read(REPORT/'RUN_POLICY.json')
        for path,want in base['source_pins'].items():
            if path!='research/non_oracle/stfbs_d1b_qm_run_release.py':self.assertEqual(sha(ROOT/path),want)
        reg=active_registry();reg.integrity('T4 all installed guards')
        ledger=reg.ledger();self.assertFalse(reg.calls);self.assertFalse(ledger['ever_overwritten']);self.assertTrue(all(x['guard_installed'] for x in ledger['installed_entries']))
        self.assertTrue(any(x['attribute']=='assign' for x in ledger['installed_entries']))
        self.assertTrue(any(x['attribute']=='least_squares' for x in ledger['installed_entries']))
        save(REPORT/'T4_EVIDENCE.json',dict(status='PASS',static_call_sequence=calls,guard_entries=len(ledger['installed_entries']),forbidden_attempts=0,real_scientific_calls=0,evidence_kind=LABEL))
