from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from research.non_oracle.sw3_formal_core import Coordinator, TEST, slots, seal, verify, write
from research.non_oracle.sw3_formal_evaluation import evaluate, validate_prediction


def prediction(classes, ticks):
    return dict(predicted_completion_status_set=classes, predicted_completion_ticks=ticks,
                completion_time_envelope=[ticks[0],ticks[-1]] if ticks else None,
                noncompletion_possible=False in classes)


class CoreTests(TestCase):
    def test_v2(self):
        good={n:dict(status="PASS") for n in TEST}
        self.assertEqual([r["actual_family_id"] for r in slots(good,lambda:None)],list(TEST))
        good[3]=dict(status="FAMILY_PRECHECK_FAILED",kind="PUBLIC_SCHEMA",basis="fixture")
        self.assertEqual(slots(good,lambda:dict(status="PASS"))[0]["actual_family_id"],7)
        for reason in ("EXHAUSTED","UNKNOWN"):
            bad=dict(good);bad[3]=dict(status=reason)
            with self.assertRaises((ValueError,KeyError)):slots(bad,lambda:dict(status="PASS"))
        good[10]=dict(status="FAMILY_PRECHECK_FAILED",kind="PUBLIC_SCHEMA",basis="fixture")
        with self.assertRaises(ValueError):slots(good,lambda:dict(status="PASS"))

    def test_seal_and_tamper(self):
        with TemporaryDirectory(dir=Path("reports").resolve()) as folder:
            root=Path(folder)
            write(root/"raw.json",dict(test=True))
            files={"0_M0":root/"raw.json"}
            with self.assertRaises(ValueError):seal(files,["0_M0","0_M1"],root/"missing")
            manifest=seal(files,["0_M0"],root/"sealed")
            verify(manifest)
            (root/"sealed/0_M0.json").write_text("{}")
            with self.assertRaises(ValueError):verify(manifest)

    def test_authorization_and_transition(self):
        class Artificial:kind="ARTIFICIAL"
        with TemporaryDirectory(dir=Path("reports").resolve()) as folder:
            with self.assertRaises(PermissionError):Coordinator(Path(folder)/"a","FORMAL_RUN",Artificial())
            c=Coordinator(Path(folder)/"b","IMPLEMENTATION_TEST",Artificial())
            with self.assertRaises(ValueError):c.advance("GATE1_VERIFIED","GATE2_VERIFIED")

    def test_evaluation(self):
        p={s:{m:prediction([True],[100]) for m in ("M0","M1","M2")} for s in range(8)}
        y={s:[dict(completed_by_H=True,completion_tick=100) for _ in range(4)] for s in range(8)}
        for s in range(8):p[s]["M1"]=prediction([False],[])
        result=evaluate(p,y)
        self.assertEqual(result["mean_D"],1)
        self.assertEqual(result["result"],"PREDICTIVE_GAIN_OBSERVED")
        self.assertEqual(result["methods"]["M1"]["empty_time"]["value"],1)
        self.assertEqual(result["time_common"]["n"],0)
        self.assertIsNone(result["methods"]["M0"]["optimistic_recovery"]["value"])
        with self.assertRaises(ValueError):validate_prediction(prediction([],[]))
