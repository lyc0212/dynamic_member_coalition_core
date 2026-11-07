from pathlib import Path
import json
import tempfile
from unittest import TestCase
from unittest.mock import patch

from scripts.check_sw3_method_validity import method_validity


class AuthorizedReleaseTests(TestCase):
    def test_formal_proof_interface_on_mock_evidence(self):
        # Pure synthetic evidence: no world generation, STEP, prediction or WLS.
        with tempfile.TemporaryDirectory(dir="reports") as tmp:
            root=Path(tmp).resolve()
            def put(name,value):
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_text(json.dumps(value));return str(path)
            row=dict(slot=0,world=0,actual_family_id=3,
                label=dict(source="ACTUAL",service_diagnostics={"mock":True}),
                evidence=dict(environment_object_id=123,D60_checkpoint="mock-checkpoint",
                    identity=dict(evaluation_slot=0,actual_family_id=3),world_number=0,
                    costs=[dict(wls=7)]))
            label=put("label.json",row)
            private=put("private.json",dict(prefix_cost=[dict(wls=11)]))
            put("labels/MANIFEST.json",{"0_0":{"path":label}})
            put("private_sealed/MANIFEST.json",{"0":{"path":private}})
            worker=put("worker.json",dict(created=True,exit_code=0,sid="MOCK"))
            permission=put("permission.json",dict(probes={"p":dict(allowed=False,
                mode="rb",exception="PermissionError",errno=13)}))
            from research.non_oracle.sw3_formal_core import TEST
            proof=dict(commit="mock",source_pins={},worker_receipts=[worker],
                permission_receipts=[permission],precheck={str(n):dict(status="PASS") for n in TEST},
                resource_ledger=dict(T0_PREFIX_ACTUAL=11,T1_WINDOW_ACTUAL=7,TOTAL_ACTUAL=18))
            with patch("scripts.check_sw3_method_validity.audit",return_value={}),patch(
                    "research.non_oracle.sw3_formal_diagnostics.sealed_diagnostics",return_value={"mock":True}):
                self.assertTrue(method_validity(root,{},mode="FORMAL_RUN",run_evidence=proof)["METHOD_VALID"])
                proof["resource_ledger"]={"prefix":11,"window":7,"total":18}
                with self.assertRaisesRegex(ValueError,"ledger mismatch"):
                    method_validity(root,{},mode="FORMAL_RUN",run_evidence=proof)
                proof["resource_ledger"]=dict(T0_PREFIX_ACTUAL=11,T1_WINDOW_ACTUAL=7,TOTAL_ACTUAL=18)
                put("permission.json",dict(probes={}))
                with self.assertRaisesRegex(ValueError,"Empty permission"):
                    method_validity(root,{},mode="FORMAL_RUN",run_evidence=proof)

    def test_live_scope_and_invalid_adapter_modes(self):
        from research.non_oracle.sw3_release_scope import check_scope,_authorized_scope
        from research.non_oracle.sw3_formal_core import Coordinator
        with self.assertRaises(PermissionError):check_scope()
        with _authorized_scope():self.assertIsNone(check_scope())
        with self.assertRaises(PermissionError):check_scope()
        for mode,kind in (("IMPLEMENTATION_TEST","PRODUCTION"),("FORMAL_RUN","ARTIFICIAL")):
            with self.assertRaises(PermissionError):
                Coordinator("unused",mode,type("Adapter",(),dict(kind=kind))())
