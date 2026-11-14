import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from research.non_oracle.belief import Beliefs,trajectory
from research.non_oracle.environment import NonOracleEnvironment
from research.non_oracle.policy import command,evaluate,decide
from research.information_service_online.execution import OnlineEnvironment
from pursuit_v2.config import Config
from scripts.run_a1 import Sensing
ROOT=Path(__file__).resolve().parents[1]
def accepted(p):return dict(has_accepted_estimate=True,optimizer_converged=True,numerical_ill_conditioned=False,ambiguity_detected=False,boundary_active=False,numeric_contract_violation=False,estimate=p)
class A1Tests(unittest.TestCase):
 def setUp(self):
  self.world=json.loads((ROOT/'configs/gq_windows_two_target_a0.json').read_text());self.ann=json.loads((ROOT/'configs/a1_public_announcements.json').read_text())['announcements']
 def obs(self,b,t,p,available=None):b.enqueue(dict(source='ACTUAL',target_id=0,measurement_tick=t,available_tick=t if available is None else available,estimate=accepted(p)))
 def env(self,world=None):return NonOracleEnvironment(copy.deepcopy(world or self.world),Sensing(),'A1_TEST',self.ann)
 def test_prior(self):
  b=Beliefs(self.ann);s=b.freeze(0);self.assertEqual(s[0]['status'],'PRIOR_ONLY');self.assertIsNone(s[0]['last_observation_tick']);self.assertEqual(s[0]['position_estimate'],[7.8,9.8])
 def test_position_not_velocity(self):
  b=Beliefs(self.ann);self.obs(b,0,[8.,10.]);s=b.freeze(0);self.assertEqual(s[0]['velocity_estimate'],[0.,0.])
  self.assertEqual(s[0]['velocity_source'],'PUBLIC_PRIOR')
 def test_mid_decision_expiry_shared_control(self):
  env=self.env();self.obs(env.beliefs,0,[8.,10.]);self.obs(env.beliefs,8,[8.16,10.]);env._state['tick']=20;env.frozen=env.beliefs.freeze(20);env.decision_tick=20
  cfg=env.cfg;pos=np.array([[8.4,9.6]]);roles=['dual_neg45']
  from pursuit_v2.observation_geometry import offset
  for tick in (27,28,29,39):
   env._state['tick']=tick
   actual=env._control_command(0,tick*.05,pos,np.array([offset(roles[0],cfg)]));speeds=np.linalg.norm(actual,axis=1);actual*=np.minimum(1.,cfg.max_speed/np.maximum(speeds,1e-15))[:,None]
   np.testing.assert_array_equal(actual,command(env.frozen[0],tick,pos,roles,cfg))
 def test_model_evaluation_no_actual_mutation(self):
  env=self.env();v=env.prepare_decision();v['end_tick']=1;before=copy.deepcopy(env.beliefs.states)
  a=decide(v,'R');b=decide(v,'S_NEW');self.assertEqual(a,b);self.assertEqual(env.beliefs.states,before);self.assertEqual(env.beliefs.pending,[])
 def test_velocity_and_expiry(self):
  b=Beliefs(self.ann);self.obs(b,0,[8.,10.]);self.obs(b,8,[8.16,10.]);s=b.freeze(20)[0]
  p,v=trajectory(s,28);q,w=trajectory(s,29);self.assertEqual(p,q);self.assertNotEqual(v,[0.,0.]);self.assertEqual(w,[0.,0.]);self.assertEqual(b.freeze(29)[0]['status'],'DEGRADED')
 def test_speed_limit(self):
  b=Beliefs(self.ann);self.obs(b,0,[8.,10.]);self.obs(b,5,[10.,10.]);self.assertAlmostEqual(np.linalg.norm(b.freeze(5)[0]['velocity_estimate']),.8)
 def test_available_consume(self):
  b=Beliefs(self.ann);self.obs(b,0,[8.,10.],20);self.assertEqual(b.freeze(0)[0]['status'],'PRIOR_ONLY');self.assertEqual(b.freeze(20)[0]['status'],'OBSERVED');self.assertEqual(b.consumed[-1]['consumed_tick'],20)
 def test_snapshot_no_backfill(self):
  b=Beliefs(self.ann);old=b.freeze(0);self.obs(b,0,[8.,10.]);self.assertEqual(old[0]['status'],'PRIOR_ONLY');new=b.freeze(20);self.assertEqual(new[0]['status'],'OBSERVED');self.assertEqual(old[0]['position_estimate'],[7.8,9.8])
 def test_model_rejected(self):
  b=Beliefs(self.ann)
  with self.assertRaises(ValueError):b.enqueue(dict(source='MODEL',measurement_tick=0,available_tick=0))
 def test_failed_estimate(self):
  b=Beliefs(self.ann);b.enqueue(dict(source='ACTUAL',target_id=0,measurement_tick=0,available_tick=0,estimate=None));self.assertEqual(b.freeze(0)[0]['status'],'PRIOR_ONLY')
 def test_ill_estimate(self):
  b=Beliefs(self.ann);e=accepted([8.,10.]);e['numerical_ill_conditioned']=True;b.enqueue(dict(source='ACTUAL',target_id=0,measurement_tick=0,available_tick=0,estimate=e));self.assertEqual(b.freeze(0)[0]['status'],'PRIOR_ONLY')
 def test_causal_control(self):
  b=Beliefs(self.ann);before=b.freeze(0);self.obs(b,0,[8.,10.]);after=b.freeze(0);cfg=Config(**self.world['config']);pos=[[8.,9.5]]
  self.assertFalse(np.array_equal(command(before[0],1,pos,['dual_neg45'],cfg),command(after[0],1,pos,['dual_neg45'],cfg)))
  self.assertNotEqual(trajectory(before[0],1)[0],trajectory(after[0],1)[0])
 def test_truth_isolation(self):
  changed=copy.deepcopy(self.world);changed['targets'][0]['position_at_birth']=[12.,12.];changed['targets'][0]['velocity']=[.6,0.]
  a=self.env();b=self.env(changed);va=a.prepare_decision();vb=b.prepare_decision();self.assertEqual(va,vb);self.assertNotIn('position_now',str(va));self.assertNotIn('velocity_now',str(va))
  va['end_tick']=1;vb['end_tick']=1;self.assertEqual(decide(va),decide(vb))
  cfg=Config(**va['config']);offsets=np.array([[.4,-.4]]);pos=np.array([[8.,9.5]])
  np.testing.assert_array_equal(a._control_command(0,0.,pos,offsets),b._control_command(0,0.,pos,offsets))
 def test_modes_first_assignment(self):
  v=self.env().prepare_decision();v['end_tick']=22
  with patch('research.non_oracle.policy.endpoint',return_value=(True,'PASS')):
   a=decide(v,'R');b=decide(v,'S_NEW')
  self.assertEqual(a,b);self.assertTrue(a['selected_indices'])
 def test_modes_across_expiry(self):
  v=self.env().prepare_decision();v['tick']=20;v['end_tick']=40;v['beliefs'][0].update(estimate_tick=8,last_observation_tick=8,position_estimate=[8.,10.],velocity_estimate=[.4,0.])
  key=dict(target=0,robots=[0,1],roles=['dual_neg45','dual_pos45'])
  with patch('research.non_oracle.policy.endpoint',return_value=(False,'PASS')):self.assertEqual(evaluate(v,key),evaluate(v,key,{}))
 def test_no_same_tick_refreeze(self):
  env=self.env();env.prepare_decision()
  with self.assertRaisesRegex(ValueError,'already frozen'):env.prepare_decision()
 def test_legacy_input_rejected(self):
  with self.assertRaises(ValueError):decide(self.world)
 def test_keep_no_truth_geometry_assertion(self):
  v=self.env().prepare_decision();v['end_tick']=1;key=dict(target=0,robots=[0,1],roles=['dual_neg45','dual_pos45']);h=v['histories'][0]
  h.update(active_segment_id='test',segments=[dict(segment_id='test',team=[dict(robot_id=0,role='dual_neg45'),dict(robot_id=1,role='dual_pos45')],latest_clock=dict(base=.5,intervals=0),latest_endpoint=dict(G=True,quality={'status':'PASS'}))]);original=copy.deepcopy(v)
  with patch('research.non_oracle.policy.endpoint',return_value=(False,'PASS')):r=evaluate(v,key)
  self.assertTrue(r['kept_history']);self.assertEqual(r['frames'][0]['progress'],0.);self.assertEqual(v,original)
  with patch('research.non_oracle.policy.endpoint',return_value=(True,'PASS')):r=evaluate(v,key)
  self.assertAlmostEqual(r['frames'][0]['progress'],.55)
 def test_changed_team_resets(self):
  v=self.env().prepare_decision();v['end_tick']=1;v['histories'][0].update(active_segment_id='old',segments=[dict(segment_id='old',team=[dict(robot_id=0,role='dual_neg45'),dict(robot_id=2,role='dual_pos45')],latest_clock=dict(base=.5,intervals=0),latest_endpoint=dict(G=True,quality={'status':'PASS'}))])
  with patch('research.non_oracle.policy.endpoint',return_value=(True,'PASS')):r=evaluate(v,dict(target=0,robots=[0,1],roles=['dual_neg45','dual_pos45']))
  self.assertFalse(r['kept_history']);self.assertAlmostEqual(r['frames'][0]['progress'],.05)
 def test_service_quality_fail_can_update_position(self):
  b=Beliefs(self.ann);row=dict(source='ACTUAL',target_id=0,measurement_tick=0,available_tick=0,estimate=accepted([8.,10.]),service_quality='FAIL');b.enqueue(row)
  self.assertEqual(b.freeze(0)[0]['source'],'ACTUAL_WLS')
 def test_recovery_after_expiry(self):
  b=Beliefs(self.ann);self.obs(b,0,[8.,10.]);self.assertEqual(b.freeze(21)[0]['status'],'DEGRADED');self.obs(b,22,[8.4,10.]);self.assertEqual(b.freeze(22)[0]['status'],'OBSERVED')
 def test_actual_feedback_one_second_not_episode(self):
  env=self.env();view=env.prepare_decision();cp=env.observe_public();actions=[dict(target=0,role='dual_neg45'),dict(target=0,role='dual_pos45'),dict(target=None,role='none')]
  result=env.step(actions,cp['checkpoint_id'],0,'test0');self.assertEqual(result['end_tick'],20);self.assertFalse(env.done);self.assertEqual(view['beliefs'][0]['status'],'PRIOR_ONLY');self.assertTrue(env.beliefs.pending)
  next_view=env.prepare_decision();self.assertEqual(next_view['beliefs'][0]['source'],'ACTUAL_WLS');self.assertEqual(next_view['beliefs'][1]['status'],'PRIOR_ONLY')
 def test_oracle_control_preserved(self):
  env=OnlineEnvironment(copy.deepcopy(self.world),Sensing(),'ORACLE_TEST');pos=np.array([[8.,9.5]]);off=np.array([[.4,-.4]]);t=env.targets[0]
  np.testing.assert_array_equal(env._control_command(0,.5,pos,off),t.velocity_at(.5)+env.cfg.travel_gain*(t.position(.5)+off-pos))
if __name__=='__main__':unittest.main()
