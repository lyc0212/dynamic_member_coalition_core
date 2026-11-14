from unittest import TestCase
from unittest.mock import patch
from copy import deepcopy
from fractions import Fraction
import numpy as np
from pursuit_v2.observation_geometry import offset
from research.non_oracle.stfbs_d1a_replay import recover,read
from research.non_oracle.stfbs_d1a_model import Branch,Budget,nominal_world
from research.non_oracle.stfbs_d1a_audit import audit
from research.non_oracle.stfbs_d1a_plan import select

class PhysicsTests(TestCase):
    def make(self):
        v,s,_=recover('runs/a2_switch_episode_001');v=deepcopy(v)
        # Explicit artificial static world, not the registered nominal H1.
        for j,b in v['beliefs'].items():b.update(position_estimate=[7.+j,7.],velocity_estimate=[0.,0.],estimate_tick=60)
        w=nominal_world(v);b=Branch(v,s,w,'ARTIFICIAL',Budget())
        b.frozen=deepcopy(v['beliefs'])
        for i,a in enumerate(b.actions):
            if a['target'] is not None:b.positions[i]=np.array([7.,7.])+offset(a['role'],b.cfg)
        v['positions']=b.positions.tolist();b.view=deepcopy(v)
        def ideal(j,segment,tick):return dict(tick=tick,G=True,quality=dict(status='PASS'))
        b.fuse=ideal
        return b,v
    def test_keep_left_endpoint_and_clock(self):
        b,v=self.make();old=deepcopy(b.segment(0)['latest_endpoint']);p=b.segment(0)['latest_clock']['intervals']
        b.assign(b.actions);self.assertEqual(b.segment(0)['latest_endpoint'],old)
        b.advance();self.assertEqual(b.segment(0)['latest_clock']['intervals'],p+1)
    def test_failed_interval_reset(self):
        b,_=self.make();b.fuse=lambda *a:dict(tick=b.tick,G=False,quality=dict(status='PASS'))
        b.assign(b.actions);b.advance();self.assertEqual(b.segment(0)['latest_clock']['intervals'],0)
    def test_withdraw_and_new_team(self):
        b,_=self.make();actions=[dict(target=1,role='dual_neg45'),dict(target=1,role='dual_pos45'),dict(target=None,role='none')]
        b.assign(actions);self.assertIsNone(b.segment(0));self.assertEqual(b.segment(1)['latest_clock']['intervals'],0)
    def test_escape_and_free_release(self):
        b,_=self.make();b.world['motion'][0]['position']=[20.,7.];b.assign(b.actions);fees=b.change_cost;b.advance()
        self.assertEqual(b.status[0],'escaped');self.assertEqual(b.change_cost,fees);self.assertTrue(all(a['target']!=0 for a in b.actions))
    def test_complete_release(self):
        b,_=self.make();b.targets[0]['service_duration']=.65;b.assign(b.actions);b.advance()
        self.assertEqual(b.status[0],'completed');self.assertTrue(all(a['target']!=0 for a in b.actions))
    def test_full_artificial_ledger_and_tamper(self):
        b,v=self.make();b.budget.choose=lambda view:dict(actions=deepcopy(view['assignment']))
        # Freeze is still real belief consumption, but synthetic endpoint fusion has no observations.
        r=b.run(deepcopy(b.actions));self.assertEqual(audit(r,v)['status'],'PASS')
        for key in ('flow','late','effort','terminal'):
            x=deepcopy(r);x['components'][key]+=.01
            with self.assertRaises(ValueError):audit(x,v)
        x=deepcopy(r);x['frames'][0]['energy']+=1
        with self.assertRaises(ValueError):audit(x,v)
        x=deepcopy(r);x['boundaries'][0]['cost']+=.01
        with self.assertRaises(ValueError):audit(x,v)
    def test_forced_negative_and_tie(self):
        v,_,_=recover('runs/a2_switch_episode_001');c=read('runs/a2_switch_episode_001/R_D60.json')['choice']
        for row in c['rows']:
            row['absolute_O']=row['baseline']-10.;row['v']=float(row['absolute_O']-row['baseline'])
        p=select(v,c);self.assertEqual(p['legal_switch_count'],6);self.assertEqual(p['full_plan_count'],13)
        self.assertLess(Fraction(p['switch_score']),0)
