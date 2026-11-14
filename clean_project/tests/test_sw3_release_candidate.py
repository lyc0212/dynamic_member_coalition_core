from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import ast
import json
import types
from contextlib import contextmanager
import hashlib
import sys

from research.non_oracle.sw3_c1_sealing import public_handoff
from research.non_oracle.sw3_formal_diagnostics import sealed_diagnostics
from research.non_oracle.sw3_formal_core import seal,verify
from research.non_oracle.sw3_formal_physics import ProductionPhysics
from scripts.run_a2_prediction_sw3_dev import read

OUT=Path("reports/a2_prediction_sw3_formal_test_release_candidate_001")


def record():
    base=Path("reports/a2_prediction_sw3_c1_001")
    d60=read(base/"VALUE2_D60.json")
    d80=read(base/"VALUE2_D80.json")
    return dict(D60=d60["policy_input"],D80=d80["policy_input"],
                first=d60["step"],second=d80["step"],
                prior_belief=deepcopy(d60["policy_input"]["beliefs"]["1"]),
                updated_belief=deepcopy(d80["policy_input"]["beliefs"]["1"]),
                consumed=[r for r in d80["consumed"] if r["target_id"]==1],
                D60_public_sha256=public_handoff(d60["policy_input"])["public_sha256"])


class CandidateTests(TestCase):
    def test_real_dev_diagnostic_sources(self):
        r=record()
        d=sealed_diagnostics(r)
        self.assertEqual(d["prior"],r["prior_belief"])
        self.assertEqual(d["updated"],r["updated_belief"])
        self.assertEqual(d["tick80_consumed"],21)
        for field in ("prior_belief","updated_belief"):
            bad=deepcopy(r);bad[field]={}
            with self.assertRaises(ValueError):sealed_diagnostics(bad)
        bad=deepcopy(r);bad["updated_belief"]["position_estimate"][0]+=1
        with self.assertRaises(ValueError):sealed_diagnostics(bad)
        bad=deepcopy(r);bad["consumed"][0]["available_tick"]+=1
        with self.assertRaises(ValueError):sealed_diagnostics(bad)

    def test_diagnostic_tamper_is_sealed(self):
        d=sealed_diagnostics(record())
        with TemporaryDirectory(dir=Path("reports").resolve()) as tmp:
            root=Path(tmp);source=root/"raw.json"
            source.write_text(json.dumps(dict(service_diagnostics=d)))
            sealed=seal({"label":source},["label"],root/"sealed")
            p=Path(sealed["label"]["path"])
            row=json.loads(p.read_bytes());row["service_diagnostics"]["prior"]={}
            p.write_text(json.dumps(row))
            with self.assertRaises(ValueError):verify(sealed)

    def test_production_finish_seals_diagnostics_before_association(self):
        from research.non_oracle.sw3_formal_adapter import ProductionAdapter
        r=record()
        r.update(identity=dict(evaluation_slot=0,actual_family_id=3),world_number=0,
                 label=dict(source="ACTUAL",completed_by_H=True,completion_tick=95))
        class HistoricalFixturePhysics:
            def finish(self,paused):
                return [r]
        with TemporaryDirectory(dir=Path("reports").resolve()) as tmp:
            a=object.__new__(ProductionAdapter)
            a.physics=HistoricalFixturePhysics();a.output=Path(tmp)
            paths=a.finish([])
            row=read(paths["0_0"])
            self.assertEqual(row["label"]["completion_tick"],95)
            self.assertEqual(row["label"]["service_diagnostics"]["prior"],r["prior_belief"])
            self.assertEqual(row["label"]["service_diagnostics"]["updated"],r["updated_belief"])

    def test_association_has_no_diagnostic_computation(self):
        from research.non_oracle.sw3_formal_adapter import ProductionAdapter
        import inspect
        self.assertNotIn("diagnose(",inspect.getsource(ProductionAdapter.associate))
        self.assertIn("sealed_diagnostics",inspect.getsource(ProductionAdapter.finish))

    def test_candidate_mode_matrix_with_fake_dependencies(self):
        file=OUT/"isolated_mock/research/non_oracle/sw3_formal_core.py"
        tree=ast.parse(file.read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=="Coordinator")
        ns=dict(Path=Path)
        exec(compile(ast.Module(body=[cls],type_ignores=[]),str(file),"exec"),ns)
        with TemporaryDirectory(dir=Path("reports").resolve()) as tmp:
            for i,(mode,kind,valid) in enumerate((
                ("FORMAL_RUN","PRODUCTION",True),("IMPLEMENTATION_TEST","ARTIFICIAL",True),
                ("FORMAL_RUN","ARTIFICIAL",False),("IMPLEMENTATION_TEST","PRODUCTION",False),
                ("INVALID","PRODUCTION",False))):
                adapter=types.SimpleNamespace(kind=kind)
                if valid:
                    self.assertEqual(ns["Coordinator"](Path(tmp)/str(i),mode,adapter).state,"NEW")
                else:
                    with self.assertRaises(PermissionError):
                        ns["Coordinator"](Path(tmp)/str(i),mode,adapter)

    def test_isolated_candidate_scope_does_not_accept_bool(self):
        source=OUT/"isolated_mock/research/non_oracle/sw3_release_scope.py"
        ns={}
        exec(compile(source.read_text(),str(source),"exec"),ns)
        with self.assertRaises(PermissionError):ns["check_scope"]()
        with ns["_authorized_scope"]():
            self.assertIsNone(ns["check_scope"]())
        with self.assertRaises(PermissionError):ns["check_scope"]()

    def test_current_physics_stays_closed(self):
        p=ProductionPhysics({}, {})
        with patch("research.non_oracle.sw3_formal_physics.sample",side_effect=AssertionError):
            with self.assertRaises(PermissionError):p.prepare([],formal_authorized=True)
            with self.assertRaises(PermissionError):p.finish([],formal_authorized=True)

    def test_isolated_candidate_runtime_with_fake_backends(self):
        file=OUT/"isolated_mock/research/non_oracle/sw3_release_runtime.py"
        tree=ast.parse(file.read_text())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="run")
        calls=[]
        @contextmanager
        def scope():
            calls.append("scope");yield
        @contextmanager
        def profile():
            yield 123,"MOCK_SID"
        def stage(root,modules):
            calls.append("stage")
        class FakeCoordinator:
            def __init__(self,output,mode,adapter):
                self.output=output
                if mode!="FORMAL_RUN":raise AssertionError(mode)
            def run(self):
                calls.append("coordinator")
                return "MOCK_COMPLETE"
        with TemporaryDirectory(dir=Path("reports").resolve()) as tmp:
            root=Path(tmp)
            (root/"world.json").write_text("{}")
            (root/"ann.json").write_text("{}")
            digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
            (root/"pins.json").write_text(json.dumps({str(root/"world.json"):digest(root/"world.json")}))
            namespace=dict(Path=Path,json=json,sys=sys,sha=digest,_authorized_scope=scope,
                deployment=types.SimpleNamespace(REPO=Path.cwd(),stage=stage,acl=lambda *a:None),
                native=types.SimpleNamespace(profile=profile,run=lambda *a:None),
                AppContainerWorker=lambda *a:object(),ProductionAdapter=lambda *a:object(),
                Coordinator=FakeCoordinator)
            exec(compile(ast.Module(body=[function],type_ignores=[]),str(file),"exec"),namespace)
            args=types.SimpleNamespace(workspace=str(root/"workspace"),output=str(root/"output"),
                pins=str(root/"pins.json"),world=str(root/"world.json"),announcements=str(root/"ann.json"))
            self.assertEqual(namespace["run"](args),"MOCK_COMPLETE")
            self.assertEqual(calls,["scope","stage","coordinator"])

    def test_independent_validity_is_not_evaluator_constant(self):
        from scripts.check_sw3_method_validity import method_validity
        root=Path("reports/a2_prediction_sw3_formal_implementation_001/final_completion")
        descriptor=read(root/"TRUSTED_INDEX_DESCRIPTOR.json")
        result=method_validity(root/"chain",descriptor,mode="IMPLEMENTATION_TEST")
        self.assertTrue(result["artificial_evidence_valid"])
        self.assertIsNone(result["METHOD_VALID"])
        with self.assertRaises(ValueError):
            method_validity(root/"chain",descriptor,mode="FORMAL_RUN",run_evidence={})
