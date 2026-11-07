from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import inspect
import json

from research.non_oracle.sw3_formal_adapter import ProductionAdapter,check_predictions
from research.non_oracle.sw3_formal_core import Coordinator,TEST,slots,seal,write
from research.non_oracle.sw3_formal_evaluation import evaluate
from research.non_oracle.sw3_formal_physics import ProductionPhysics
from research.non_oracle.sw3_formal_trust import Trust
from scripts.run_a2_prediction_sw3_test import fixture
from research.non_oracle.sw3_c1_manifest import CENTERS
from research.non_oracle.sw3_c1_sealing import public_handoff


def make_views():
    original=fixture()
    output={}
    for s,n in enumerate(TEST):
        v=deepcopy(original)
        v["targets"][1]["coarse_position"]=list(CENTERS[n])
        v["beliefs"][1]["position_estimate"]=list(CENTERS[n])
        output[s]=public_handoff(v)
    return output


def predictions(classes):
    ticks=[100] if True in classes else []
    return dict(predicted_completion_status_set=classes,predicted_completion_ticks=ticks,
                completion_time_envelope=[100,100] if ticks else None,noncompletion_possible=False in classes)


class CompletionTests(TestCase):
    def test_prepare_failure_stops_all_later_calls(self):
        class Failing:
            kind="ARTIFICIAL"
            def global_precheck(self):pass
            def public_prechecks(self):return {n:dict(status="PASS") for n in TEST}
            def reserve_precheck(self):raise AssertionError("Unexpected reserve")
            def prepare(self,identities):
                self.accepted=[object(),object()]
                raise ValueError(self.failure)
            def predict(self,public):raise AssertionError("Prediction after failure")
            def finish(self,private):raise AssertionError("Continuation after failure")
        with TemporaryDirectory(dir=Path("reports").resolve()) as tmp:
            for i,reason in enumerate(("EXHAUSTED_ALL_PHYSICAL","EXHAUSTED_MIXED","UNKNOWN_CONSTRUCTOR","WORLD_LOST")):
                a=Failing();a.failure=reason
                c=Coordinator(Path(tmp)/str(i),"IMPLEMENTATION_TEST",a)
                with self.assertRaisesRegex(ValueError,reason):c.run()
                self.assertEqual(c.state,"BLOCKED")
                self.assertEqual(len(a.accepted),2)
                self.assertTrue((Path(tmp)/str(i)/"FAILURE.json").exists())

    def test_prediction_mapping_and_fault_matrix(self):
        archive=Path("reports/a2_prediction_sw3_formal_implementation_001/final_completion/os/wrapped_predictions")
        if not archive.exists():
            self.fail("Required artificial OS artifacts missing")
        views=make_views()
        identities=[dict(evaluation_slot=s,actual_family_id=n,center=list(CENTERS[n])) for s,n in enumerate(TEST)]
        raw={p.stem:json.loads(p.read_bytes()) for p in archive.glob("*.json")}
        pins=raw["0_M0"]["source_pins"]
        with TemporaryDirectory(dir=Path("reports").resolve()) as tmp:
            root=Path(tmp)
            files={}
            for key,data in raw.items():
                files[key]=root/(key+".json");write(files[key],data)
            check_predictions(views,files,identities,pins,True)
            with self.assertRaises(ValueError):check_predictions(views,files,identities,pins,False)
            missing=dict(files);missing.pop("0_M0")
            with self.assertRaises(ValueError):check_predictions(views,missing,identities,pins,True)
            swapped=dict(files);swapped["0_M0"],swapped["1_M0"]=swapped["1_M0"],swapped["0_M0"]
            with self.assertRaises(ValueError):check_predictions(views,swapped,identities,pins,True)
            mutations=(
                lambda p:p.update(actual_family_id=10),
                lambda p:p.update(method="M1"),
                lambda p:p.update(source_pins={}),
                lambda p:p["selection"].update(public_sha256="forged"),
                lambda p:p["selection"].update(screening_wls=1),
                lambda p:p["selection"].update(geometry_endpoints=1231),
                lambda p:p["prediction"]["cost"].update(wls=999),
                lambda p:p["prediction"].update(predicted_completion_status_set=[]),
                lambda p:p["prediction"]["results"][0].update(offline_diagnostic=True),
            )
            for i,mutate in enumerate(mutations):
                with self.subTest(case=i):
                    p=deepcopy(raw["0_M0"]);mutate(p)
                    files["0_M0"].write_text(json.dumps(p))
                    with self.assertRaises((ValueError,KeyError)):
                        check_predictions(views,files,identities,pins,True)
                    files["0_M0"].write_text(json.dumps(raw["0_M0"]))

    def test_label_completeness_and_identity(self):
        with TemporaryDirectory(dir=Path("reports").resolve()) as tmp:
            root=Path(tmp);files={}
            adapter=object.__new__(ProductionAdapter)
            identities=[dict(evaluation_slot=s,actual_family_id=n) for s,n in enumerate(TEST)]
            for s,n in enumerate(TEST):
                for w in range(4):
                    p=root/f"{s}_{w}.json"
                    write(p,dict(slot=s,world=w,actual_family_id=n,
                        label=dict(source="ACTUAL",completed_by_H=False,completion_tick=None)))
                    files[f"{s}_{w}"]=p
            adapter.verify_labels(files,identities)
            with self.assertRaises(ValueError):adapter.verify_labels({k:v for k,v in files.items() if k!="0_0"},identities)
            for mutate in (lambda r:r.update(actual_family_id=7),lambda r:r.update(world=1),
                           lambda r:r["label"].update(source="MOCK")):
                row=json.loads(files["0_0"].read_bytes());mutate(row)
                files["0_0"].write_text(json.dumps(row))
                with self.assertRaises(ValueError):adapter.verify_labels(files,identities)
                files["0_0"].write_text(json.dumps(dict(slot=0,world=0,actual_family_id=3,
                    label=dict(source="ACTUAL",completed_by_H=False,completion_tick=None))))

    def test_production_interfaces_and_lock(self):
        methods=("global_precheck","public_prechecks","reserve_precheck","prepare","verify_pauses",
                 "seal_private_manifest","predict","verify_predictions","trust_identity",
                 "verify_write_denial","verify_seal_permissions","finish","verify_labels","associate")
        self.assertTrue(all(callable(getattr(ProductionAdapter,n,None)) for n in methods))
        source=inspect.getsource(ProductionPhysics)
        self.assertIn('sample(self.world, "test"',source)
        self.assertNotIn("private_world(",source)
        with patch("research.non_oracle.sw3_formal_physics.sample",side_effect=AssertionError):
            p=ProductionPhysics({}, {})
            with self.assertRaises(PermissionError):p.prepare([],formal_authorized=True)
            with self.assertRaises(PermissionError):p.finish([],formal_authorized=True)

    def test_eight_different_legal_public_views(self):
        v=make_views()
        self.assertEqual(len({r["public_sha256"] for r in v.values()}),8)
        for s,n in enumerate(TEST):
            self.assertEqual(v[s]["D60"]["targets"][1]["coarse_position"],list(CENTERS[n]))

    def test_v2_failure_matrix(self):
        good={n:dict(status="PASS") for n in TEST}
        for status in ("EXHAUSTED","BLOCKED","UNKNOWN"):
            p=deepcopy(good);p[3]=dict(status=status)
            with self.subTest(status=status),self.assertRaises((ValueError,KeyError)):
                slots(p,lambda:dict(status="PASS"))
        for kind in ("PUBLIC_SCHEMA","MOTION_DOMAIN","FIXED_PHYSICAL_ADMISSION"):
            p=deepcopy(good);p[10]=dict(status="FAMILY_PRECHECK_FAILED",kind=kind,basis="mock pre-draw")
            result=slots(p,lambda:dict(status="PASS"))
            self.assertEqual(result[1],dict(evaluation_slot=1,actual_family_id=7,replaces_family_id=10,split="test"))
            with self.assertRaises(ValueError):slots(p,lambda:dict(status="BLOCKED"))
        p=deepcopy(good)
        for n in (3,10):p[n]=dict(status="FAMILY_PRECHECK_FAILED",kind="PUBLIC_SCHEMA",basis="mock")
        with self.assertRaises(ValueError):slots(p,lambda:dict(status="PASS"))
        with patch("research.non_oracle.sw3_c1_private_worlds.hash_unit",return_value=("mock",0,.5)) as call:
            from research.non_oracle.sw3_c1_private_worlds import draw_component
            draw_component("test",7,0,0,0,replaces=3)
            call.assert_called_once_with("SW3-V1|world|test|7|0|0|0")

    def test_every_invalid_transition(self):
        states=("NEW","PRECHECK_VERIFIED","GATE1_VERIFIED","GATE2_VERIFIED","GATE3_VERIFIED","GATE4_VERIFIED")
        class Adapter:kind="ARTIFICIAL"
        with TemporaryDirectory(dir=Path("reports").resolve()) as tmp:
            for i,before in enumerate(states):
                for j,after in enumerate(states):
                    if j==i+1:continue
                    c=Coordinator(Path(tmp)/f"{i}_{j}","IMPLEMENTATION_TEST",Adapter())
                    c.state=before
                    with self.assertRaises(ValueError):c.advance(before,after)

    def test_time_denominators_and_recovery(self):
        p={s:dict(M0=predictions([False]),M1=predictions([True]),M2=predictions([False,True])) for s in range(8)}
        y={s:[dict(completed_by_H=True,completion_tick=100)]*4 for s in range(8)}
        r=evaluate(p,y)
        self.assertEqual(r["methods"]["M1"]["pessimistic_recovery"]["value"],1)
        self.assertEqual(r["methods"]["M0"]["empty_time"]["value"],1)
        self.assertEqual(r["methods"]["M0"]["discrete_hit"]["value"],0)
        self.assertEqual(r["time_common"]["n"],32)
        self.assertEqual(r["time_common"]["means"]["M1"]["median_error"],0)
        self.assertIsNone(r["methods"]["M0"]["optimistic_recovery"]["value"])

    def test_win_threshold(self):
        for wins,expected in ((4,"NO_DEMONSTRATED_GAIN"),(5,"PREDICTIVE_GAIN_OBSERVED")):
            p={s:dict(M0=predictions([False]),M1=predictions([False]),
                      M2=predictions([True]) if s<wins else predictions([False])) for s in range(8)}
            y={s:[dict(completed_by_H=True,completion_tick=100)]*4 for s in range(8)}
            r=evaluate(p,y)
            self.assertEqual(r["result"],expected)

    def test_anchor_swaps_and_stale_receipts(self):
        with TemporaryDirectory(dir=Path("reports").resolve()) as tmp:
            root=Path(tmp);write(root/"raw.json",dict(x=1))
            m=seal({"x":root/"raw.json"},["x"],root/"sealed")
            trust=Trust(root/"trust","mock","trusted","mock")
            first=trust.fix(1,1,root/"sealed/MANIFEST.json",m)
            with self.assertRaises(ValueError):trust.fix(2,2,root/"sealed/MANIFEST.json",m,"wrong")
            with self.assertRaises(ValueError):trust.fix(1,1,root/"sealed/MANIFEST.json",m)
            Path(first["receipt_path"]).unlink()
            with self.assertRaises(FileNotFoundError):trust.verify(1)
