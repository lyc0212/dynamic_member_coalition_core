import copy,hashlib,json,unittest
from pathlib import Path
from scripts.gq_windows.a0_identity import checkpoint,request,manifest,IdentityMap
from scripts.gq_windows.a0_evidence import EvidenceError
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/a0_identity_request.json'
class IdentityTests(unittest.TestCase):
 def setUp(self):self.req=json.loads(FIXTURE.read_text())['request']
 def reject(self,call,path):
  with self.assertRaises(EvidenceError) as caught:call()
  self.assertEqual(caught.exception.status,'INVALID_EVIDENCE');self.assertEqual(caught.exception.path,path)
 def test_valid(self):
  checkpoint(self.req['checkpoint']);request(self.req)
 def test_checkpoint_digest(self):
  self.req['checkpoint']['positions'][0][0]+=1
  self.reject(lambda:checkpoint(self.req['checkpoint']),'/checkpoint/checkpoint_id')
 def test_request_digest(self):
  self.req['evaluation_request_id']='0'*64
  self.reject(lambda:request(self.req),'/request/evaluation_request_id')
 def test_wrong_reference(self):
  cp=copy.deepcopy(self.req['checkpoint']);cp['positions'][0][0]+=1
  self.reject(lambda:request(self.req,cp),'/request/checkpoint')
 def test_unknown_field(self):
  self.req['unexpected_identity']='x'
  self.reject(lambda:request(self.req),'/request')
 def test_mapping(self):
  m=IdentityMap()
  m.register('work',('pair','D0','object'),'/operation/work_instance_id','R','S',{'tick':0},{'tick':0})
  self.reject(lambda:m.register('work',('pair','D0','object'),'/operation/work_instance_id','R','other',{'tick':0},{'tick':0}),'/operation/work_instance_id')
 def test_unregistered_mapping(self):
  self.reject(lambda:IdentityMap().register('work',('pair','D0','object'),'/unknown','R','S',{}, {}),'/unknown')
 def test_different_scientific_object(self):
  self.reject(lambda:IdentityMap().register('work',('pair','D0','object'),'/operation/work_instance_id','R','S',{'tick':0},{'tick':20}),'/operation/work_instance_id/scientific_object')
if __name__=='__main__':unittest.main()
