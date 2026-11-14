"""Inventory primitives only; these tests never grant scientific acceptance."""
import json
from pathlib import Path
import unittest
import uuid
from scripts.gq_windows.a0_evidence import Reader, EvidenceError, inventory

ROOT=Path(__file__).resolve().parents[1]

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.root=ROOT/'reports/a0_i_fixture_tests'/uuid.uuid4().hex
        self.root.mkdir(parents=True)
        (self.root/'FIXTURE.json').write_text(json.dumps({'source_type':'FIXTURE'}))

    def reject(self, call, status, reason):
        with self.assertRaises(EvidenceError) as caught:
            call()
        self.assertEqual(caught.exception.status,status)
        self.assertIn(reason,caught.exception.reason)

    def test_missing_evidence(self):
        self.reject(lambda:inventory(self.root),'INCOMPLETE','missing artifact')

    def test_path_escape(self):
        self.reject(lambda:Reader(self.root).read('../outside.json'),'INVALID_EVIDENCE','outside run directory')

    def test_wrong_reference(self):
        self.reject(lambda:Reader(self.root).read('FIXTURE.json','EXPECTED.json'),'INVALID_EVIDENCE','wrong artifact reference')

    def test_duplicate_key(self):
        (self.root/'bad.json').write_text('{"x":1,"x":2}')
        self.reject(lambda:Reader(self.root).read('bad.json'),'INVALID_EVIDENCE','duplicate JSON member')

    def test_nonfinite(self):
        (self.root/'bad.json').write_text('{"x":NaN}')
        self.reject(lambda:Reader(self.root).read('bad.json'),'INVALID_EVIDENCE','NaN')

    def test_valid_repeated_reference(self):
        r=Reader(self.root)
        self.assertEqual(r.read('FIXTURE.json'),r.read('FIXTURE.json','FIXTURE.json'))
        self.assertEqual(len(r.files),1)

if __name__=='__main__':unittest.main()
