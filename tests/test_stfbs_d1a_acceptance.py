from unittest import TestCase
from unittest.mock import patch
from copy import deepcopy
from fractions import Fraction
from research.non_oracle.belief import Beliefs
from research.non_oracle.stfbs_d1a_replay import recover,digest,read
from research.non_oracle.stfbs_d1a_model import Budget,nominal_world,Branch
from research.non_oracle.stfbs_d1a_state import ModelBeliefConsumer
from research.non_oracle.stfbs_d1a_plan import select
from tests.test_stfbs_d1a_physics import PhysicsTests

class AcceptanceTests(TestCase):
    def test_missing_invalid_delayed_and_degraded_recovery(self):
        _,seed,_=recover('runs/a2_switch_episode_001');ref=Beliefs(seed['announcements'],deferred=True);m=ModelBeliefConsumer(seed)
        for attr in ('states','history','pending','consumed','accepted_receipts'):setattr(ref,attr,deepcopy(getattr(m,attr)))
        self.assertEqual(m.freeze(100),ref.freeze(100));self.assertEqual(m.states[0]['status'],'OBSERVED')
        good=dict(has_accepted_estimate=True,optimizer_converged=True,numerical_ill_conditioned=False,ambiguity_detected=False,boundary_active=False,numeric_contract_violation=False,estimate=[10.,10.])
        for tick,available,estimate in ((101,101,None),(102,102,dict(good,optimizer_converged=False)),(103,121,good),(104,104,good)):
            r=dict(source='ACTUAL',target_id=0,measurement_tick=tick,available_tick=available,estimate=estimate);ref.enqueue(r)
            r.update(source='MODEL',provenance='SIMULATED',observation_origin='MODEL');m.enqueue(r)
        self.assertEqual(m.freeze(120),ref.freeze(120));self.assertEqual(m.states,ref.states);self.assertEqual(len(m.pending),1)
    def test_budget_guards_before_solver(self):
        b=Budget();b.counts['MODEL_OBSERVATION_WLS']=1000
        with self.assertRaises(RuntimeError):b.estimator('MODEL_OBSERVATION_WLS')({})
        b=Budget();b.cpu-=601
        with self.assertRaises(RuntimeError):b.check()
        b=Budget();b.wall-=901
        with self.assertRaises(RuntimeError):b.check()
    def test_unknown_and_fail_quality_reset(self):
        for q in ('UNKNOWN','FAIL'):
            b,_=PhysicsTests().make();b.fuse=lambda *a:dict(tick=b.tick,G=True,quality=dict(status=q));b.assign(b.actions);b.advance()
            self.assertEqual(b.segment(0)['latest_clock']['intervals'],0)
    def test_constrained_tie_and_history_permission(self):
        v,seed,_=recover('runs/a2_switch_episode_001');choice=read('runs/a2_switch_episode_001/R_D60.json')['choice'];v['config']['change_cost']=0.
        for row in choice['rows']:row.update(absolute_O=row['baseline'],v=0.)
        p=select(v,choice);self.assertEqual(p['selected'],[6])
        changed=deepcopy(seed);changed['accepted_position_history'][0]=[]
        # Recovery auxiliary state has no parameter in the selection API.
        self.assertEqual(p,select(v,choice))
    def test_model_current_history_digest(self):
        b,_=PhysicsTests().make();b.tick=80;view=b.policy_view()
        for h in view['histories']:
            self.assertEqual(h['contract_id'],'D1A_MODEL_TASK_HISTORY_V1');saved=h['history_digest'];x=deepcopy(h);x.pop('history_digest');self.assertEqual(saved,digest(x))
    def test_control_and_escape_priority(self):
        b,_=PhysicsTests().make();b.targets[0]['service_duration']=.65;b.world['motion'][0]['position']=[20.,7.]
        b.assign(b.actions);b.advance();self.assertEqual(b.status[0],'escaped');self.assertEqual(b.components['completion'],0)
    def test_wrong_world_identity(self):
        v,s,_=recover('runs/a2_switch_episode_001');w=nominal_world(v);w['motion'][0]['position'][0]+=.1
        with self.assertRaises(ValueError):Branch(v,s,w,'bad',Budget())
