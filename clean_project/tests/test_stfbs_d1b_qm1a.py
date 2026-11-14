"""Only the twelve canonical QM1A interface tests; never a physical experiment."""
from unittest import TestCase
from copy import deepcopy
from pathlib import Path
import json,pickle
from research.non_oracle.stfbs_d1b_qm_scenario import build_fixture,validate_fixture,FIXTURE_STATUS,TEST_DOUBLE
from research.non_oracle.stfbs_d1b_qm_model import QMBranch,SensorAuthority,PublicQueryRejected,initial_team,changed_team,preset_action,admit_substitute,CandidateAdmissionRejected
from research.non_oracle.stfbs_d1b_qm_audit import active_registry,assert_public_surface,save
from research.non_oracle.stfbs_d1a_state import ModelRawCache
from research.information_service_online.public import seal_slot

def fake_fuse(self,j,segment,tick):
    active_registry().note_double('synthetic endpoint at '+str(tick)+'; no cache sampling, WLS or belief observation')
    return dict(tick=tick,target_id=j,team=deepcopy(segment['team']),branch=self.name,G=True,
                quality=dict(status='PASS',evidence_kind=TEST_DOUBLE),provenance='SIMULATED',observation_origin='MODEL',evidence_kind=TEST_DOUBLE)
fake_fuse.evidence_kind=TEST_DOUBLE

def snapshot(b):return pickle.dumps({k:v for k,v in b.__dict__.items() if k!='budget'})

def synthetic_cut80(b):
    """A labelled pure-state fixture, not an integration from 60 to 80."""
    active_registry().note_double('synthetic old interval (79,80] and empty-queue freeze80; no physical intervals executed')
    b.tick=80;b._sensor_authority.publish_from_executor(80)
    for h in b.histories.values():h['cutoff_tick']=80
    old=b.segment(0);old['latest_endpoint']=fake_fuse(b,0,old,80)
    old['latest_clock']['intervals']=20  # Explicit synthetic clock, not physical service.
    b.frozen=b.consumer.freeze(80);b._last_public_cut=80

def synthetic_packet(sigma=.02):
    return seal_slot(dict(slot_key=dict(target_id=0,robot_id=0,tick=80),state='VALID',packet=dict(sensor_id='U0',position=[1.,2.],bearing=0.,sigma=sigma,measurement_tick=80,available_tick=80,status='ok'),slot_digest=None))

class QM1ATests(TestCase):
    def test_fixture_static_config(self):
        f=build_fixture();self.assertEqual(validate_fixture(f)['status'],FIXTURE_STATUS)
        self.assertEqual((f.view['config']['robots'],f.view['config']['task_count'],f.view['tick'],f.view['end_tick']),(3,1,60,120))
        self.assertEqual(f.view['targets'][0]['service_duration'],1.05)
        self.assertAlmostEqual(f.view['positions'][2][0]-f.view['positions'][1][0],.70)
        self.assertEqual(f.view['positions'][2][1],f.view['positions'][1][1])
        save(Path(__file__).resolve().parents[1]/'reports/stfbs_lite_d1b_qm1a_001/FIXTURE_IDENTITY.json',dict(f.identity,initial_policy_view=f.view,seed_source=f.seed['provenance'],test_id=self.id()))

    def test_fixture_public_prior_provenance(self):
        f=build_fixture();self.assertEqual(f.seed['observation_origin'],'MODEL');self.assertEqual(f.seed['internal_states_at_D60'][0]['source'],'PUBLIC_PRIOR')
        self.assertEqual(f.seed['pending_observations'],[]);self.assertEqual(f.seed['accepted_receipts'],{})
        self.assertEqual(f.view['histories'][0]['events'][0]['observation_origin'],'MODEL')
        bad=deepcopy(f);bad.seed['provenance']='ACTUAL'
        with self.assertRaisesRegex(ValueError,'provenance'):validate_fixture(bad)

    def test_fixture_unfused_boundary(self):
        f=build_fixture();b=QMBranch(f)
        self.assertIsNone(f.identity['initial_endpoint']);self.assertIsNone(f.identity['Q'])
        self.assertFalse(f.identity['physical_validation']);self.assertEqual(b.fusions,0)
        self.assertEqual(b.feedback,[]);self.assertEqual(b.streams,{});self.assertEqual(b.cache.rows,{})
        self.assertEqual(b.histories[0]['segments'],[]);self.assertIsNone(b.histories[0]['active_segment_id'])
        self.assertTrue(all(v==0 for v in b.budget.counts.values()))

    def test_profile_79_80(self):
        a=SensorAuthority(.08)
        self.assertEqual(a.physical_profile_at(79)[1]['sigma'],.02)
        self.assertEqual(a.physical_profile_at(80)[1]['sigma'],.08)
        self.assertTrue(all(p['health']=='available' for p in a.physical_profile_at(80)))
        a.publish_from_executor(79);old=a.public_snapshot();self.assertEqual(old.public_profile_at(79)[1]['sigma'],.02)
        a.publish_from_executor(80);self.assertEqual(a.public_snapshot().public_profile_at(80)[1]['sigma'],.08)
        self.assertEqual(old.watermark,79)

    def test_public_future_query_denied(self):
        a=SensorAuthority(.16);public=a.public_snapshot();before=public.to_public_dict()
        with self.assertRaisesRegex(PublicQueryRejected,'PUBLIC_QUERY_REJECTED_AS_FUTURE'):public.public_profile_at(80)
        self.assertEqual(public.to_public_dict(),before);self.assertEqual(a.public_snapshot().watermark,60)
        with self.assertRaises(AttributeError):public._watermark=80
        a.publish_from_executor(80);self.assertEqual(a.public_snapshot().public_profile_at(80)[1]['sigma'],.16)
        with self.assertRaises(PublicQueryRejected):public.public_profile_at(80)

    def test_private_schedule_absent_from_policy_inputs(self):
        f=build_fixture();left=QMBranch(f,'B0',.04);right=QMBranch(f,'B1',.32)
        a=left.public_inputs();b=right.public_inputs()
        assert_public_surface(a);assert_public_surface(b);assert_public_surface(f.seed)
        self.assertEqual(a['policy_view'],b['policy_view'])
        self.assertEqual(a['public_profiles'].to_public_dict(),b['public_profiles'].to_public_dict())
        self.assertNotIn('_schedule',json.dumps(a['policy_view']))
        bad=dict(a,unexpected_owner=left._sensor_authority)
        with self.assertRaisesRegex(ValueError,'PRIVATE_EXECUTOR_REACHABLE'):assert_public_surface(bad)
        bad=dict(a,callback=lambda hidden=left._sensor_authority:hidden)
        with self.assertRaisesRegex(ValueError,'CALLABLE_OR_CLOSURE'):assert_public_surface(bad)
        with self.assertRaisesRegex(ValueError,'PRIVATE_EXECUTOR_REACHABLE'):assert_public_surface(dict(model=left))

    def test_cache_context_conflict_counters(self):
        registry=active_registry();registry.note_double('synthetic legal packet producer; no sensor sampling')
        c=ModelRawCache('B0');ctx=dict(position=[1.,2.],sigma=.02,health='available');produced=[]
        def producer():produced.append(1);return synthetic_packet()
        first=c.query('B0',0,0,80,ctx,producer)
        self.assertEqual(c.query('B0',0,0,80,ctx,producer),first);self.assertEqual(len(produced),1)
        before=deepcopy(c.rows);counts=deepcopy(c.counts);scientific_result=dict(label=TEST_DOUBLE,unchanged=True)
        with self.assertRaisesRegex(ValueError,'MODEL raw context conflict'):c.query('B0',0,0,80,dict(ctx,sigma=.08),producer)
        self.assertEqual(c.rows,before);self.assertEqual(len(produced),1);self.assertTrue(scientific_result['unchanged'])
        self.assertEqual(c.counts['requests'],counts['requests']+1);self.assertEqual(c.counts['conflicts'],counts['conflicts']+1)
        self.assertEqual(c.counts['new'],counts['new']);self.assertEqual(c.counts['reuses'],counts['reuses'])

    def test_counterfactual_branch_isolation(self):
        active_registry().note_double('independent OLD/DEGRADED synthetic packet caches, no WLS')
        old=ModelRawCache('OLD');degraded=ModelRawCache('DEGRADED')
        ctx=dict(position=[1.,2.],sigma=.02,health='available')
        old.query('OLD',0,0,80,ctx,lambda:synthetic_packet())
        degraded.query('DEGRADED',0,0,80,dict(ctx,sigma=.08),lambda:synthetic_packet(.08))
        before=deepcopy(degraded.rows);old.rows[('OLD',0,0,80)]['slot']['packet']['bearing']=1.
        self.assertEqual(degraded.rows,before);self.assertIsNot(old.rows,degraded.rows)
        with self.assertRaisesRegex(ValueError,'Foreign MODEL branch'):old.query('DEGRADED',0,0,80,ctx,lambda:synthetic_packet())

    def test_assign_fake_fuse_atomicity(self):
        registry=active_registry();b=QMBranch(build_fixture(),'B1')
        with registry.fake_scope('atomicity synthetic assignment',fake_fuse):
            b.assign(initial_team());synthetic_cut80(b);before=snapshot(b)
            def fail(staged,phase):
                if phase=='after_fusion':
                    staged.consumer.pending.append(dict(label=TEST_DOUBLE))
                    staged.cache.rows[('B1',0,2,80)]=dict(label=TEST_DOUBLE)
                    raise RuntimeError('synthetic preparation failure')
            with self.assertRaisesRegex(RuntimeError,'synthetic preparation failure'):b.assign(changed_team(),prepare_fault=fail)
            self.assertEqual(snapshot(b),before)
            b.assign(changed_team());self.assertEqual(b.actions,changed_team())
            self.assertEqual(b.histories[0]['segments'][0]['closure']['reason'],'TEAM_CHANGED')
            self.assertEqual(b.segment(0)['latest_clock']['intervals'],0)
            self.assertTrue(any(e['kind']=='TEAM_CHANGED' for e in b.histories[0]['events']))

    def test_member_change_two_entries_cost(self):
        registry=active_registry()
        for kappa in (.01,.025):
            b=QMBranch(build_fixture(change_cost=kappa),'B1')
            with registry.fake_scope('two-entry cost at '+str(kappa),fake_fuse):
                b.assign(initial_team());synthetic_cut80(b);before=b.change_cost
                decision=preset_action(b.policy_view(),'B1')
                self.assertNotIn('exact_value',decision);self.assertEqual(decision['source'],'EXPERIMENT_PRESET_NOT_AUTONOMOUS')
                b.assign(decision['actions']);self.assertEqual(b.boundaries[-1]['changes'],2)
                self.assertEqual(b.boundaries[-1]['cost'],2*kappa);self.assertAlmostEqual(b.change_cost-before,2*kappa)

    def test_service_clock_left_boundary_with_fake_endpoints(self):
        registry=active_registry();b=QMBranch(build_fixture(),'B1')
        with registry.fake_scope('synthetic left80 transaction, no actual service intervals',fake_fuse):
            b.assign(initial_team());synthetic_cut80(b);old=deepcopy(b.segment(0))
            self.assertEqual(preset_action(b.policy_view(),'B0')['actions'],initial_team())
            b.assign(changed_team());new=b.segment(0)
            self.assertEqual(old['latest_endpoint']['tick'],80);self.assertEqual(new['start_tick'],80)
            self.assertEqual(new['latest_endpoint']['tick'],80);self.assertEqual(new['latest_endpoint']['evidence_kind'],TEST_DOUBLE)
            self.assertEqual((new['latest_clock']['base'],new['latest_clock']['intervals']),(0.,0))
            interval=dict(left_tick=80,right_tick=81,evidence_kind=TEST_DOUBLE)
            self.assertEqual(interval['right_tick']-interval['left_tick'],1)
            b.tick=100;b._sensor_authority.publish_from_executor(100)
            b.histories[0]['cutoff_tick']=100;b.segment(0)['latest_endpoint']=fake_fuse(b,0,b.segment(0),100)
            v=b.policy_view();self.assertEqual(preset_action(v,'B1')['actions'],changed_team())

    def test_B2_two_robot_admission_rejection(self):
        state=dict(robots=(0,1),team=(0,1),assignment=[dict(target=0,role='dual_neg45'),dict(target=0,role='dual_pos45')],history=[],fees=0.)
        before=deepcopy(state)
        with self.assertRaisesRegex(CandidateAdmissionRejected,'PUBLIC_CANDIDATE_ADMISSION_REJECTED_AS_EXPECTED'):
            admit_substitute(state['robots'],state['team'])
        self.assertEqual(state,before)
