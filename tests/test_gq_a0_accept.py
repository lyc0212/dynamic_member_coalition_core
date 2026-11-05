import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.gq_windows.a0_plans import catalogue,plans,verify_selection,competition
from scripts.gq_windows.a0_accept import accept
ROOT=Path(__file__).resolve().parents[1]
class AcceptanceTests(unittest.TestCase):
 def setUp(self):
  s=json.loads((ROOT/'configs/gq_windows_two_target_a0.json').read_text());self.cp=dict(config=copy.deepcopy(s['config']),positions=s['positions_initial'],targets=s['targets'],assignment=s['initial_assignment']);self.cp['config']['change_cost']=.125
  self.keys=catalogue(self.cp);self.rows=[dict(absolute_O=.5,baseline=0.,v=.5) for _ in self.keys]
  self.table=plans(self.cp,self.keys,self.rows)
  # Manual: idle=0; all 12 single-team plans=.5-2*.125=1/4.
  # Mask3 beats masks5/6. Within mask3 retain first target/role => index0.
  self.saved=dict(independent_plans=copy.deepcopy(self.table),legal_plan_count=13,tied_optima=12,exact_table_value='1/4',selected_indices=[0],actions=[dict(target=0,role='dual_neg45'),dict(target=0,role='dual_pos45'),dict(target=None,role='none')],assignment_change_count=2,B64=0.)
 def check(self):return verify_selection(self.cp,self.keys,self.rows,self.saved)
 def test_manual_tie(self):
  self.assertEqual(len(self.keys),12);self.assertEqual(len(self.table),13)
  self.assertEqual({p['exact_value'] for p in self.table},{'0','1/4'})
  r=self.check();self.assertTrue(r['structural_competition']);self.assertTrue(r['competition']['activated'])
 def test_missing_plan(self):
  self.saved['independent_plans'].pop()
  with self.assertRaisesRegex(ValueError,'coverage'):self.check()
 def test_duplicate_resource(self):
  self.saved['independent_plans'].append(dict(selected=[0,6],actions=[],changes=4,exact_value='1/2'))
  with self.assertRaisesRegex(ValueError,'coverage'):self.check()
 def test_bad_roles(self):
  self.keys[0]['roles']=['dual_neg45']*2
  with self.assertRaisesRegex(ValueError,'catalogue'):self.check()
 def test_false_optimum(self):
  self.saved['exact_table_value']='1/2'
  with self.assertRaisesRegex(ValueError,'exact_table_value'):self.check()
 def test_false_count(self):
  self.saved['legal_plan_count']=14
  with self.assertRaisesRegex(ValueError,'legal_plan_count'):self.check()
 def test_false_change_cost(self):
  self.saved['independent_plans'][1]['exact_value']='3/8'
  with self.assertRaisesRegex(ValueError,'coverage'):self.check()
 def test_false_changes(self):
  self.saved['assignment_change_count']=1
  with self.assertRaisesRegex(ValueError,'assignment_change_count'):self.check()
 def test_wrong_tie(self):
  self.saved['selected_indices']=[1]
  with self.assertRaisesRegex(ValueError,'selected_indices'):self.check()
 def test_zero_gain_keeps_idle(self):
  for r in self.rows:r.update(absolute_O=.25,v=.25)
  self.saved.update(independent_plans=plans(self.cp,self.keys,self.rows),exact_table_value='0',tied_optima=13,selected_indices=[],actions=self.cp['assignment'],assignment_change_count=0)
  self.assertEqual(self.check()['selected_indices'],[])
 def test_global_smallest_mask(self):
  for i,r in enumerate(self.rows):r.update(absolute_O=.5 if i in (2,4) else 0.,v=.5 if i in (2,4) else 0.)
  # index2 uses mask5; index4 mask6. Equal 1/4 -> mask5 wins.
  self.saved.update(independent_plans=plans(self.cp,self.keys,self.rows),tied_optima=2,selected_indices=[2],actions=[dict(target=0,role='dual_neg45'),dict(target=None,role='none'),dict(target=0,role='dual_pos45')])
  self.assertEqual(self.check()['selected_indices'],[2])
 def test_one_positive_target(self):
  for r in self.rows[6:]:r.update(absolute_O=0.,v=0.)
  r=competition(self.cp,self.keys,self.rows);self.assertFalse(r['activated']);self.assertEqual(r['margins'],{'0':'1/4','1':'-1/4'})
 def test_pair_failure_stops(self):
  with patch('scripts.gq_windows.a0_accept.compare',return_value={'status':'FAIL'}),patch('scripts.gq_windows.a0_accept.Reader') as reader:
   r=accept('FIXTURE',source_type='FIXTURE');reader.assert_not_called();self.assertEqual(r['PLAN_OPTIMALITY']['status'],'NOT_EVALUATED');self.assertEqual(r['COMPETITION']['real_multitarget_episode'],'NOT_EVALUATED')
 def test_positive_margins_without_resource_conflict(self):
  cp=copy.deepcopy(self.cp);cp['config']['robots']=4;cp['positions'].append([2.,3.]);cp['assignment'].append(dict(target=None,role='none'))
  keys=catalogue(cp);rows=[dict(absolute_O=.5,baseline=0.,v=.5) for _ in keys]
  result=competition(cp,keys,rows);self.assertFalse(result['resource_exclusive']);self.assertFalse(result['activated'])
if __name__=='__main__':unittest.main()
