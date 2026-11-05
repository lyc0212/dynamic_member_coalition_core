import copy,json,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from scripts.gq_windows import a0_compare as c,a0_identity as ident,a0_evidence as evidence
from scripts.gq_windows.a0_identity import IdentityMap
from scripts.gq_windows.a0_evidence import EvidenceError
ORIGIN='D:/1st/gq_windows_release_verification/both_360_validation_001'
class VirtualReader:
 raw={}
 def __init__(self,root):self.files={}
 def relative(self,name,expected=None):
  s=str(name).replace('\\','/');s=s[len(ORIGIN)+1:] if s.startswith(ORIGIN+'/') else s
  if s.startswith('/') or '..' in s.split('/') or ':' in s:raise EvidenceError('INVALID_EVIDENCE',s,'outside run directory')
  if expected is not None and s!=expected:raise EvidenceError('INVALID_EVIDENCE',s,'wrong artifact reference')
  if s not in self.raw:raise EvidenceError('INCOMPLETE',s,'missing artifact')
  return s
 def read(self,name,expected=None):
  s=self.relative(name,expected);self.files[s]='fixture';return json.loads(self.raw[s])
 def path(self,name,expected=None):
  raw=self.raw[self.relative(name,expected)]
  class Bytes:
   def read_bytes(self):return raw
  return Bytes()
class IntegrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with zipfile.ZipFile(Path(__file__).parent/'fixtures/a0_ib_both.zip') as z:cls.base={n:z.read(n) for n in z.namelist()}
 def setUp(self):VirtualReader.raw=dict(self.base)
 def run_compare(self):
  with patch.object(c,'Reader',VirtualReader),patch.object(ident,'Reader',VirtualReader),patch.object(evidence,'Reader',VirtualReader):return c.compare('FIXTURE',source_type='FIXTURE')
 def change(self,name,mutate):
  v=json.loads(VirtualReader.raw[name]);mutate(v);VirtualReader.raw[name]=json.dumps(v).encode()
 def test_full_positive(self):
  r=self.run_compare();self.assertEqual(r['status'],'PASS',r);self.assertEqual(r['source_type'],'FIXTURE');self.assertGreater(len(r['mappings']),0)
 def test_missing_mode(self):
  del VirtualReader.raw['S_NEW/EPISODE_INDEX.json'];r=self.run_compare();self.assertEqual(r['status'],'INCOMPLETE');self.assertIn('EPISODE_INDEX',r['path'])
 def test_swap_candidates(self):
  VirtualReader.raw['S_NEW/D0/PREDICT/B0/C0.json']=VirtualReader.raw['S_NEW/D0/PREDICT/B0/C1.json']
  r=self.run_compare();self.assertEqual(r['status'],'INVALID_EVIDENCE');self.assertIn('C0',r['path'])
 def test_final_settlement(self):
  self.change('S_NEW/FINAL_METRICS.json',lambda v:v.update(return_with_changes=123.))
  r=self.run_compare();self.assertNotEqual(r['status'],'PASS');self.assertIn('FINAL_METRICS',r['path'])
 def test_changed_prediction_position(self):
  self.change('S_NEW/D0/PREDICT/B0/C0.json',lambda v:v['frames'][-1]['positions'][0].__setitem__(0,999.))
  r=self.run_compare();self.assertNotEqual(r['status'],'PASS');self.assertIn('positions',r['path'])
 def test_runtime_recipe_and_conflict(self):
  a={'action_metadata':{'transitions':[{'stream_id':'X_R:T0:first0'}]}};b=copy.deepcopy(a);b['action_metadata']['transitions'][0]['stream_id']='foreign:T0:first0'
  with self.assertRaises(EvidenceError) as caught:c.admitted_pair(a,b,'selection','X',0,({},{}),IdentityMap())
  self.assertIn('recipe',caught.exception.reason)
 def test_actual_step_changed(self):
  self.change('S_NEW/D0/STEP.json',lambda v:v.update(end_tick=19))
  r=self.run_compare();self.assertNotEqual(r['status'],'PASS');self.assertIn('STEP',r['path'])
 def test_unknown_runtime_difference(self):
  self.change('S_NEW/D0/SELECTION.json',lambda v:v.update(scope='unregistered runtime identity'))
  r=self.run_compare();self.assertEqual(r['status'],'INVALID_EVIDENCE');self.assertEqual(r['path'],'/scope');self.assertEqual(r['context']['artifact'],'SELECTION')
 def test_mapping_conflict(self):
  m=IdentityMap();args=('stream',('X','0','selection'),'/action_metadata/transitions/0/stream_id')
  m.register(*args,'X_R:T0:first0','X_S_NEW:T0:first0',{}, {},artifact='selection')
  with self.assertRaises(EvidenceError) as caught:m.register(*args,'X_R:T0:first0','X_S_NEW:T1:first0',{}, {},artifact='selection')
  self.assertIn('conflict',caught.exception.reason)
 def test_scientific_changes(self):
  for field,a,b in [('bearing',.1,.2),('Q','PASS','FAIL'),('progress',1.,2.),('v',.1,.2),('assignment',[{'target':0}],[{'target':1}]),('control',[[1.,0.]],[[2.,0.]])]:
   with self.subTest(field=field):
    with self.assertRaises(EvidenceError) as caught:c.strict_pair({field:a},{field:b},'candidate')
    self.assertIn('/'+field,caught.exception.path)
if __name__=='__main__':unittest.main()
