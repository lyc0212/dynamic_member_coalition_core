"""FIXTURE receipt consistency only, not independent algorithm correctness."""
import copy,json,unittest,zipfile
from pathlib import Path
from scripts.gq_windows import a0_identity as m
from scripts.gq_windows.a0_evidence import EvidenceError
class ReceiptTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with zipfile.ZipFile(Path(__file__).parent/'fixtures/a0_ia2_single_mode.zip') as z:cls.base={n:json.loads(z.read(n)) for n in z.namelist()}
 def setUp(self):
  self.req=copy.deepcopy(self.base['R/D0/REQUEST.json']);self.row=copy.deepcopy(self.base['R/D0/PREDICT/C0.json']);self.spec=copy.deepcopy(self.base['R/D0/MANIFEST.json']['candidates'][0]);self.saved=copy.deepcopy(self.base['R/D0/PREDICT/C0/PREDICTION_AUDIT.json'])
 def check(self):return m.prediction_receipt(self.req,self.row,self.spec,self.saved,'/audit')
 def reject(self,call,path):
  with self.assertRaises(EvidenceError) as c:call()
  self.assertEqual(c.exception.status,'INVALID_EVIDENCE');self.assertEqual(c.exception.path,path)
 def test_receipt_positive(self):
  self.assertEqual(self.saved['prediction']['counts']['requests'],28)
  self.assertEqual(self.saved['prediction']['counts']['starts'],252)
  self.check()
 def test_wrong_candidate_receipt(self):
  self.saved=copy.deepcopy(self.base['R/D0/PREDICT/C1/PREDICTION_AUDIT.json'])
  self.reject(self.check,'/audit/fusion_checks')
 def test_same_shape_wrong_fusion(self):
  self.saved['fusion_checks'][0]['radius']+=.001
  self.reject(self.check,'/audit/fusion_checks/0/radius')
 def test_same_shape_other_candidate(self):
  other=self.base['R/D0/PREDICT/C1/PREDICTION_AUDIT.json']['fusion_checks']
  original=self.saved['fusion_checks']
  i=next(i for i in range(min(len(other),len(original))) if other[i].get('radius')!=original[i].get('radius'))
  self.saved['fusion_checks'][i]['radius']=other[i]['radius']
  self.assertEqual(len(self.saved['fusion_checks']),28)
  self.reject(self.check,f'/audit/fusion_checks/{i}/radius')
 def test_prediction_counts(self):
  self.saved['prediction']['counts']['requests']=29
  self.reject(self.check,'/audit/prediction/counts/requests')
 def test_unknown(self):
  self.saved['foreign_identity']='x';self.reject(self.check,'/audit/foreign_identity')
 def test_missing(self):
  del self.saved['prediction'];self.reject(self.check,'/audit/prediction')
 def test_wrong_type(self):
  self.saved['prediction']['counts']['requests']='28';self.reject(self.check,'/audit/prediction/counts/requests')
 def test_missing_nested_sensor(self):
  del self.row['sensing_results'][0]['frame']['records'][0]['bearing']
  self.reject(lambda:m.candidate(self.row,self.spec,self.req,'/candidate'),'/candidate/sensing_results/0/frame/records/0/bearing')
 def test_array_element(self):
  self.row['sensing_results'][0]['frame']['records'][0]=None
  self.reject(lambda:m.candidate(self.row,self.spec,self.req,'/candidate'),'/candidate/sensing_results/0/frame/records/0')
 def test_changed_audited_value(self):
  # radius is derived solely from saved Jacobian singular values by audit_fusion.
  self.row['sensing_results'][0]['result']['quality']['radius_proxy']+=.01
  self.reject(self.check,'/audit/evidence/sensing_results/0/result/quality/radius_proxy')
 def test_pointer_escaping_and_signed_zero(self):
  self.reject(lambda:m.exact_tree({'a/b':1},{},'/x'),'/x/a~1b')
  self.reject(lambda:m.exact_tree(-0.,0.,'/x'),'/x')
if __name__=='__main__':unittest.main()

