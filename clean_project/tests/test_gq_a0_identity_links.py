"""FIXTURE-only linkage tests; no episode, estimator, controller or selector."""
import copy,json,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from scripts.gq_windows import a0_identity as mod
from scripts.gq_windows.a0_evidence import EvidenceError
ROOT=Path(__file__).resolve().parents[1]
ORIGIN='D:/1st/gq_windows_release_verification/both_360_validation_001'
class MemoryReader:
 data={}
 def __init__(self,root):self.files={}
 def read(self,name,expected=None):
  raw=str(name).replace('\\','/');rel=raw[len(ORIGIN)+1:] if raw.startswith(ORIGIN+'/') else raw
  if expected is not None and rel!=expected:raise EvidenceError('INVALID_EVIDENCE','/'+rel,'wrong artifact reference')
  if rel not in self.data:raise EvidenceError('INCOMPLETE','/'+rel,'missing artifact')
  self.files[rel]='fixture';return copy.deepcopy(self.data[rel])
class LinkTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with zipfile.ZipFile(ROOT/'tests/fixtures/a0_ia2_single_mode.zip') as z:cls.base={n:json.loads(z.read(n)) for n in z.namelist()}
 def setUp(self):MemoryReader.data=copy.deepcopy(self.base)
 def run_chain(self):
  with patch.object(mod,'Reader',MemoryReader):return mod.mode_chain('FIXTURE','R')
 def reject(self,path):
  with self.assertRaises(EvidenceError) as c:self.run_chain()
  self.assertEqual(c.exception.status,'INVALID_EVIDENCE');self.assertEqual(c.exception.path,path)
 def test_positive(self):
  self.assertEqual(self.base['FIXTURE.json']['source_type'],'FIXTURE')
  self.assertEqual(self.base['R/D0/SELECTION.json']['selected_indices'],[0])
  self.assertEqual(self.base['R/D0/STEP.json']['end_tick'],20)
  self.assertEqual(self.run_chain()['status'],'SINGLE_MODE_LINKS_VALIDATED')
 def test_assignment(self):
  commit=MemoryReader.data['R/D0/STEP.json']['action_commit'];commit['assignment'][0]=dict(target=None,role='none')
  commit['action_commit_id']=mod.digest({k:v for k,v in commit.items() if k!='action_commit_id'})
  MemoryReader.data['R/D0/STEP.json']['action_commit_id']=commit['action_commit_id']
  self.reject('/R/D0/STEP/action_commit/assignment')
 def test_commit_digest(self):
  MemoryReader.data['R/D0/STEP.json']['action_commit']['action_commit_id']='0'*64
  self.reject('/R/D0/STEP/action_commit/action_commit_id')
 def test_wrong_checkpoint(self):
  commit=MemoryReader.data['R/D0/STEP.json']['action_commit'];commit['checkpoint_id']='0'*64
  commit['action_commit_id']=mod.digest({k:v for k,v in commit.items() if k!='action_commit_id'})
  MemoryReader.data['R/D0/STEP.json']['action_commit_id']=commit['action_commit_id']
  self.reject('/R/D0/STEP/action_commit/checkpoint_id')
 def test_chain(self):
  MemoryReader.data['R/D1/BINDING.json']=copy.deepcopy(MemoryReader.data['R/D0/BINDING.json'])
  self.reject('/R/D1/BINDING/public_checkpoint')
 def test_index(self):
  MemoryReader.data['R/EPISODE_INDEX.json']['decisions'][0]['selection_file']=ORIGIN+'/R/D1/SELECTION.json'
  self.reject('/R/D1/SELECTION.json')
 def test_audit(self):
  MemoryReader.data['R/D0/SELECTION_AUDIT/decision_audit.json']['candidate_count']=5
  self.reject('/R/D0/SELECTION_AUDIT/candidate_count')
 def test_payload_resealed(self):
  row=MemoryReader.data['R/D0/PREDICT/C0.json']['sensing_results'][0]['result'];row['payload']['bearings'][0]+=.01
  row['payload_sha256']=mod.digest(row['payload']);row['quality']['payload_sha256']=row['payload_sha256']
  self.reject('/R/D0/PREDICT/C0/sensing_results/0/result/payload')
 def test_quality_digest(self):
  MemoryReader.data['R/D0/PREDICT/C0.json']['sensing_results'][0]['result']['quality']['payload_sha256']='0'*64
  self.reject('/R/D0/PREDICT/C0/sensing_results/0/result/quality/payload_sha256')
 def test_missing_nested(self):
  del MemoryReader.data['R/D0/PREDICT/C0.json']['sensing_results'][0]['result']['payload']
  self.reject('/R/D0/PREDICT/C0/sensing_results/0/result/payload')
 def test_repeated_reference(self):
  r=MemoryReader('FIXTURE');self.assertEqual(r.read(ORIGIN+'/R/D0/SELECTION.json','R/D0/SELECTION.json'),r.read('R/D0/SELECTION.json'))
if __name__=='__main__':unittest.main()
