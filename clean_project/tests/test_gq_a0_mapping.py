import unittest
from scripts.gq_windows.a0_identity import IdentityMap
from scripts.gq_windows.a0_mapping import namespace,RULES,VERSION
from scripts.gq_windows.a0_evidence import EvidenceError
class MappingTests(unittest.TestCase):
 def reject(self,call,path):
  with self.assertRaises(EvidenceError) as c:call()
  self.assertEqual(c.exception.status,'INVALID_EVIDENCE');self.assertEqual(c.exception.path,path)
 def test_policy_readonly(self):
  with self.assertRaises(TypeError):RULES['operation']['/x']='work'
  self.assertTrue(VERSION.endswith('v1'))
 def test_array_policy(self):
  self.assertEqual(namespace('manifest','/candidates/12/candidate_id'),'candidate')
  self.reject(lambda:namespace('manifest','/candidates/-1/candidate_id'),'/candidates/-1/candidate_id')
 def test_scientific_field_not_mappable(self):
  for path in ['/positions/0/0','/per_target/0/v','/frame/records/0/bearing','/events/0/type','/assignment/0/target']:
   with self.subTest(path=path):self.reject(lambda:namespace('fusion',path),path)
 def test_unknown_identity(self):
  self.reject(lambda:namespace('fusion','/result/new_world_id'),'/result/new_world_id')
 def test_namespace_mismatch(self):
  self.reject(lambda:IdentityMap().register('candidate',('p','D0','c'),'/operation/work_instance_id','a','b',{},{}),'/operation/work_instance_id')
 def test_reverse_conflict(self):
  m=IdentityMap();args=('work',('p','D0','c'),'/operation/work_instance_id')
  m.register(*args,'a','b',{'tick':0},{'tick':0})
  self.reject(lambda:m.register(*args,'c','b',{'tick':0},{'tick':0}),args[2])
 def test_scopes_separate(self):
  m=IdentityMap()
  for d,right in [('D0','b'),('D1','c')]:m.register('work',('p',d,'c'),'/operation/work_instance_id','a',right,{'tick':0},{'tick':0})
  self.assertEqual(len(m.records),2)
 def test_science_change(self):
  for field,value in [('bearing',.1),('progress',1.),('v',.2),('assignment',[1])]:
   self.reject(lambda:IdentityMap().register('work',('p','D0','c'),'/operation/work_instance_id','a','b',{field:0.},{field:value}),'/operation/work_instance_id/scientific_object')
 def test_dynamic_allowlist_removed(self):
  with self.assertRaises(TypeError):IdentityMap().register('work',('p','D0','c'),'/x','a','b',{}, {},allowed_paths={'/x'})
if __name__=='__main__':unittest.main()
