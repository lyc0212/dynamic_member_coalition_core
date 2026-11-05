import copy,hashlib,json,unittest
from pathlib import Path
from scripts.gq_windows.a0_plans import catalogue,plans,check_saved,competition
ROOT=Path(__file__).resolve().parents[1]
class A0Tests(unittest.TestCase):
 def setUp(self):
  self.scene=json.loads((ROOT/'configs/gq_windows_two_target_a0.json').read_text())
  self.cp=dict(config=self.scene['config'],targets=self.scene['targets'],positions=self.scene['positions_initial'],assignment=self.scene['initial_assignment'])
 def test_freeze(self):
  old=json.loads((ROOT/'configs/gq_windows_single_target.json').read_text());new=copy.deepcopy(self.scene);new['config']['task_count']=1;new['targets'].pop();self.assertEqual(new,old)
  p=ROOT/'configs/gq_windows_two_target_a0.json';meta=json.loads(p.with_suffix('.provenance.json').read_text());self.assertEqual(meta['sha256'],hashlib.sha256(p.read_bytes()).hexdigest())
 def test_structure(self):
  for targets,n,legal in [(self.scene['targets'],12,13),(self.scene['targets'][1:],6,7),([],0,1)]:
   self.cp['targets']=targets;keys=catalogue(self.cp);self.assertEqual(len(keys),n)
   table=plans(self.cp,keys,[dict(absolute_O=.5,baseline=0.,v=.5) for _ in keys]);self.assertEqual(len(table),legal);self.assertEqual(table[0]['selected'],[])
   for p in table:self.assertLessEqual(len(p['selected']),1)
 def test_plan_injection(self):
  keys=catalogue(self.cp);rows=[dict(absolute_O=.5,baseline=0.,v=.5) for _ in keys];table=plans(self.cp,keys,rows);check_saved(table,copy.deepcopy(table));self.assertTrue(competition(self.cp,keys,rows)['activated'])
  bad=[]
  bad.append(table[1:]);bad.append(table+[table[0]]);bad.append(table[:-1])
  for field,value in [('exact_value','999'),('changes',99),('actions',[])]:
   altered=copy.deepcopy(table);altered[1][field]=value;bad.append(altered)
  altered=copy.deepcopy(table);altered[0]['unknown']=True;bad.append(altered)
  for altered in bad:
   with self.subTest(altered=altered):
    with self.assertRaises(ValueError):check_saved(table,altered)
 def test_invalid_values(self):
  keys=catalogue(self.cp);rows=[dict(absolute_O=.5,baseline=0.,v=.5) for _ in keys];rows[0]['v']=.6
  with self.assertRaises(ValueError):plans(self.cp,keys,rows)
 def test_no_competition(self):
  keys=catalogue(self.cp);rows=[dict(absolute_O=0.,baseline=0.,v=0.) for _ in keys];self.assertFalse(competition(self.cp,keys,rows)['activated'])
if __name__=='__main__':unittest.main()
