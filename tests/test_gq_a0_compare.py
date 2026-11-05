import unittest
from scripts.gq_windows.a0_compare import strict_pair,compare
from scripts.gq_windows.a0_evidence import EvidenceError
class CompareTests(unittest.TestCase):
 def reject(self,left,right,path,status='FAIL'):
  with self.assertRaises(EvidenceError) as c:strict_pair(left,right,'selection')
  self.assertEqual(c.exception.path,path);self.assertEqual(c.exception.status,status)
 def test_equal(self):strict_pair({'positions':[[1.,2.]],'Q':'PASS'},{'positions':[[1.,2.]],'Q':'PASS'},'candidate')
 def test_position(self):self.reject({'positions':[[1.,2.]]},{'positions':[[1.,2.1]]},'/positions/0/1')
 def test_bearing(self):self.reject({'bearing':.1},{'bearing':.2},'/bearing')
 def test_progress(self):self.reject({'progress':1.},{'progress':2.},'/progress')
 def test_value(self):self.reject({'v':.1},{'v':.2},'/v')
 def test_final_metrics(self):self.reject({'return_with_changes':.1},{'return_with_changes':.2},'/return_with_changes')
 def test_signed_zero(self):self.reject(0.,-0.,'')
 def test_type(self):self.reject({'tick':1},{'tick':1.},'/tick')
 def test_unknown_identity(self):self.reject({'unknown_id':'a'},{'unknown_id':'b'},'/unknown_id','INVALID_EVIDENCE')
 def test_selection_policy_gap(self):
  self.reject({'action_metadata':{'transitions':[{'stream_id':'RUN_R:T0:first0'}]}},{'action_metadata':{'transitions':[{'stream_id':'RUN_S_NEW:T0:first0'}]}},'/action_metadata/transitions/0/stream_id','INVALID_EVIDENCE')
if __name__=='__main__':unittest.main()
