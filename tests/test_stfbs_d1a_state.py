from unittest import TestCase
from copy import deepcopy
from research.non_oracle.belief import Beliefs,trajectory
from research.non_oracle.stfbs_d1a_replay import recover,digest
from research.non_oracle.stfbs_d1a_state import ModelBeliefConsumer,ModelRawCache

class StateTests(TestCase):
    def test_historical_replay(self):
        _,_,audit=recover('runs/a2_switch_episode_001');self.assertTrue(audit['consumed_order_equal'])
    def test_raw_identity_matrix(self):
        key=dict(target_id=1,robot_id=0,tick=60);slot=dict(slot_key=key,state='MISSING',packet=None)
        a=ModelRawCache('KEEP');b=ModelRawCache('SWITCH');ctx=dict(position=[0,0],sigma=.02,health='missing');calls=[]
        def produce():calls.append(1);return deepcopy(slot)
        self.assertEqual(a.query('KEEP',1,0,60,ctx,produce),slot)
        for stream in ('segmentA','segmentB','role_changed','new_flow'):
            self.assertEqual(a.query('KEEP',1,0,60,ctx,produce),slot)
        self.assertEqual(len(calls),1)
        for field,value in (('position',[1,0]),('sigma',.03),('health','available')):
            changed=deepcopy(ctx);changed[field]=value
            with self.assertRaises(ValueError):a.query('KEEP',1,0,60,changed,produce)
        b.query('SWITCH',1,0,60,ctx,produce);self.assertEqual(len(calls),2)
        with self.assertRaises(ValueError):a.query('SWITCH',1,0,60,ctx,produce)
        a.rows[('KEEP',1,0,60)]['slot']['state']='VALID'
        with self.assertRaises(ValueError):a.query('KEEP',1,0,60,ctx,produce)
        self.assertEqual(b.rows[('SWITCH',1,0,60)]['slot']['state'],'MISSING')
    def test_inherited_slots(self):
        slot=dict(slot_key=dict(target_id=0,robot_id=0,tick=60),state='MISSING',packet=None);ctx=dict(position=[0,0],sigma=.02,health='missing')
        c=ModelRawCache('b',[dict(slot=slot,context_digest=digest(ctx))])
        def forbidden():raise AssertionError('Historical slot resampled')
        self.assertEqual(c.query('b',0,0,60,ctx,forbidden),slot);self.assertEqual(c.counts['new'],0)
    def test_model_belief_differential(self):
        _,seed,_=recover('runs/a2_switch_episode_001');ref=Beliefs(seed['announcements'],deferred=True)
        model=ModelBeliefConsumer(seed)
        for attr in ('states','history','pending','consumed','accepted_receipts'):setattr(ref,attr,deepcopy(getattr(model,attr)))
        estimate=dict(has_accepted_estimate=True,optimizer_converged=True,numerical_ill_conditioned=False,ambiguity_detected=False,boundary_active=False,numeric_contract_violation=False,estimate=[9.,10.])
        for tick in (60,64,65,65,70):
            r=dict(source='ACTUAL',target_id=1,measurement_tick=tick,available_tick=tick,estimate=estimate)
            ref.enqueue(r);r.update(source='MODEL',provenance='SIMULATED',observation_origin='MODEL');model.enqueue(r)
        self.assertEqual(model.freeze(80),ref.freeze(80));self.assertEqual(model.history,ref.history)
        frozen=model.freeze(120);self.assertEqual(frozen[1]['status'],'DEGRADED');self.assertEqual(model.states[1]['status'],'OBSERVED')
        with self.assertRaises(ValueError):model.enqueue(dict(source='ACTUAL'))
