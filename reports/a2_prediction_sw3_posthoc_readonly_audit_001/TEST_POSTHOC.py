"""Artificial-only numerical tests and separate sealed-file tests."""
from pathlib import Path
from fractions import Fraction
import json
import math
import os
from copy import deepcopy
import unittest

from POSTHOC_NUMERIC import numeric_method,check_saved_totals,main_criteria
from POSTHOC_AUDITOR import verify_files,audit
from POSTHOC_METHOD_VALIDITY import verify_permission_receipts
from research.non_oracle.sw3_formal_core import seal,write,sha
from research.non_oracle.sw3_formal_trust import Trust,verify_anchor

OUT=Path(__file__).resolve().parent

class NumericTests(unittest.TestCase):
    def calc(self):return numeric_method([[False,True]]*6+[[False]]*2,[[False]*4 for _ in range(8)])
    def test_01_known_rounding(self):
        c=self.calc();self.assertEqual(c['exact_total']['0.1'],Fraction(3,40))
        self.assertEqual(c['float_total']['0.1'],0.07500000000000001)
        check_saved_totals(c,dict(c['float_total']))
    def test_02_binary_and_decimal_fraction(self):
        self.assertEqual(Fraction(.1),Fraction(3602879701896397,36028797018963968))
        self.assertEqual(Fraction('0.1'),Fraction(1,10))
        self.assertNotEqual(Fraction(.1),Fraction('0.1'))
    def test_03_all_lambdas(self):
        self.assertEqual(self.calc()['exact_total'],{'0.0':Fraction(0),'0.1':Fraction(3,40),'0.25':Fraction(3,16),'0.5':Fraction(3,8)})
    def test_04_missing_class_penalty(self):
        c=numeric_method([[True]]*8,[[False]*4 for _ in range(8)])
        self.assertTrue(all(v==1 for v in c['exact_total'].values()))
    def test_05_mixed_penalty(self):
        c=numeric_method([[False,True]]*8,[[True,False,True,False] for _ in range(8)])
        self.assertEqual(c['exact_family'][0]['0.1'],Fraction(1,10))
    def test_06_four_world_mean(self):
        c=numeric_method([[False]]*8,[[True,False,False,False] for _ in range(8)])
        self.assertEqual(c['exact_family'][0]['0.25'],Fraction(1,4))
    def test_07_eight_family_equal_mean(self):
        c=numeric_method([[False]]*8,[[True]*4]+[[False]*4 for _ in range(7)])
        self.assertEqual(c['exact_total']['0.25'],Fraction(1,8))
    def test_08_strict_saved_float(self):
        c=self.calc();saved=dict(c['float_total']);saved['0.1']=.075
        with self.assertRaisesRegex(ValueError,'Numeric mismatch'):check_saved_totals(c,saved)
    def test_09_single_ulp_corruption_rejected(self):
        c=self.calc();saved=dict(c['float_total']);saved['0.1']=math.nextafter(saved['0.1'],math.inf)
        with self.assertRaisesRegex(ValueError,'Numeric mismatch'):check_saved_totals(c,saved)
    def test_10_material_loss_corruption_rejected(self):
        c=self.calc();saved=dict(c['float_total']);saved['0.25']+=.25
        with self.assertRaisesRegex(ValueError,'Numeric mismatch'):check_saved_totals(c,saved)
    def test_11_wrong_family_weight_rejected(self):
        c=numeric_method([[False]]*8,[[True]*4]+[[False]*4 for _ in range(7)])
        saved=dict(c['float_total']);saved['0.25']=.25
        with self.assertRaisesRegex(ValueError,'Numeric mismatch'):check_saved_totals(c,saved)
        with self.assertRaisesRegex(ValueError,'four-world'):numeric_method([[False]]*8,[[False]*3]*8)
    def test_12_unknown_nan_rejected(self):
        c=self.calc();saved=dict(c['float_total']);saved['0.25']=float('nan')
        with self.assertRaisesRegex(ValueError,'Numeric mismatch'):check_saved_totals(c,saved)
    def test_13_main_thresholds_exact(self):
        self.assertEqual(main_criteria([Fraction(1,20)]*8,32,32),[True,True,True])
        self.assertEqual(main_criteria([Fraction(1,20)-Fraction(1,10**20)]*8,32,32),[False,True,True])
        self.assertEqual(main_criteria([Fraction(1)]*4+[Fraction(0)]*4,32,32),[True,False,True])
        self.assertEqual(main_criteria([Fraction(1)]*8,32,31),[True,True,False])


def fixture(name,wrong_family=False,wrong_world=False):
    root=OUT/'artificial_integrity'/name;root.mkdir(parents=True,exist_ok=False)
    ps={};ys={};private={}
    for s in range(8):
        for w in range(4):
            k=f'{s}_{w}';f=root/f'private_raw/{k}.json'
            write(f,dict(identity=dict(evaluation_slot=s,actual_family_id=s),world=w,public=dict(public_sha256=f'public{s}')));private[k]=f
            f=root/f'label_raw/{k}.json';write(f,dict(slot=s,world=99 if wrong_world and (s,w)==(0,0) else w,
                actual_family_id=s,label=dict(completed_by_H=False,completion_tick=None)));ys[k]=f
        for m in ('M0','M1','M2'):
            k=f'{s}_{m}';f=root/f'prediction_raw/{k}.json';write(f,dict(method=m,evaluation_slot=s,
                actual_family_id=99 if wrong_family and s==0 else s,selection=dict(public_sha256=f'public{s}'),
                prediction=dict(predicted_completion_status_set=[False],cost=dict(wls=0))));ps[k]=f
    manifests=[seal(v,list(v),root/f) for v,f in ((private,'private_sealed'),(ps,'predictions'),(ys,'labels'))]
    trust=Trust(root/'trusted','artificial','trusted-test','artificial-sid')
    previous=None
    for gate,(manifest,folder) in enumerate(zip(manifests,('private_sealed','predictions','labels')),1):
        anchor=trust.fix(gate,gate,root/folder/'MANIFEST.json',manifest,previous)
        previous=anchor['receipt_sha256']
    descriptor=trust.export()
    for n,status in enumerate(('PRECHECK_VERIFIED','GATE1_VERIFIED','GATE2_VERIFIED','GATE3_VERIFIED','GATE4_VERIFIED')):
        write(root/f'events/{n}.json',dict(after=status))
    return root,manifests,trust,descriptor


class SealTests(unittest.TestCase):
    def test_prediction_tamper(self):
        root,ms,_,_=fixture('prediction_tamper');Path(ms[1]['0_M0']['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'Tampered'):verify_files(root/'predictions',24)
    def test_label_tamper(self):
        root,ms,_,_=fixture('label_tamper');Path(ms[2]['0_0']['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'Tampered'):verify_files(root/'labels',32)
    def test_sha_mismatch(self):
        root,ms,_,_=fixture('sha_mismatch');ms[1]['0_M0']['sha256']='0'*64
        (root/'predictions/MANIFEST.json').write_text(json.dumps(ms[1]))
        with self.assertRaisesRegex(ValueError,'Tampered'):verify_files(root/'predictions',24)
    def test_file_identity_mismatch(self):
        root,ms,_,_=fixture('file_identity');p=Path(ms[1]['0_M0']['path']);q=p.with_suffix('.replacement');q.write_bytes(p.read_bytes());os.replace(q,p)
        with self.assertRaisesRegex(ValueError,'Replaced'):verify_files(root/'predictions',24)
    def test_gate_receipt_tamper(self):
        root,_,trust,_=fixture('gate_receipt');Path(trust.expected[1]['receipt_path']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'Trusted receipt'):verify_anchor(trust.expected[1])
    def test_trusted_index_tamper(self):
        root,_,_,descriptor=fixture('trusted_index');Path(descriptor['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'Trusted index'):audit(root,descriptor)
    def test_family_identity_mismatch(self):
        root,_,_,descriptor=fixture('family_identity',wrong_family=True)
        with self.assertRaisesRegex(ValueError,'Wrong method'):audit(root,descriptor)
    def test_world_identity_mismatch(self):
        root,_,_,descriptor=fixture('world_identity',wrong_world=True)
        with self.assertRaisesRegex(ValueError,'Wrong label identity'):audit(root,descriptor)
    def test_permission_receipt_rejected(self):
        folder=OUT/'artificial_integrity/permission';folder.mkdir(parents=True,exist_ok=False)
        p=folder/'receipt.json'
        for value,reason in ((dict(probes={}), 'Empty permission'),
                (dict(probes={'x':dict(allowed=True)}),'Unexpected private'),
                (dict(probes={'x':dict(allowed=False,mode='FILE_WRITE_DATA',winerror=32)}),'Write denial'),
                (dict(probes={'x':dict(allowed=False,mode='rb',exception='FileNotFoundError',errno=2)}),'Read denial')):
            p.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,reason):verify_permission_receipts([p])

if __name__=='__main__':unittest.main(verbosity=2)
