import copy
import json
from pathlib import Path
import unittest

import numpy as np

from research.non_oracle.shadow_service_prediction import Hypothesis, predict_windows
from scripts.gq_windows.a0_identity import exact_tree

ROOTS = [Path("runs")/p for p in ("a2_switch_episode_001","a2_value2_open_001")]


def load(root):
    row = json.loads((root/"R_D60.json").read_bytes())
    return row


def inputs(row):
    view = copy.deepcopy(row["policy_input"])
    view["beliefs"] = {int(j):b for j,b in view["beliefs"].items()}
    return view,row["choice"]["rows"][6]["key"]


def compare_frames(predicted, expected, *, actual):
    if len(predicted)!=len(expected):
        raise AssertionError("Frame count")
    for a,b in zip(predicted,expected):
        tick = a["tick"]
        endpoint = b["actual_endpoints"]["1"] if actual else b
        q = endpoint["quality"]["status"] if actual else endpoint["Q"]
        p = b["progress"]["1"] if actual else b["progress"]
        exact_tree([tick,a["G"],a["Q"],a["progress"]],[b["tick"],endpoint["G"],q,p],f"/tick/{tick}")
        for k in ("positions","control"):
            np.testing.assert_allclose(a[k],b[k],rtol=0,atol=1e-12,err_msg=f"tick {tick} {k}")


class ShadowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not all((p/"R_D60.json").is_file() for p in ROOTS):
            raise unittest.SkipTest("Local frozen VALUE evidence is required")
        cls.rows = [load(p) for p in ROOTS]
        cls.view, cls.key = inputs(cls.rows[0])
        cls.hypotheses = [Hypothesis((9.,10.3),(0.,0.)),Hypothesis((9.2,10.1),(.4,0.)),
                          Hypothesis((9.03,10.29),(.02,0.))]

    def test_a_nominal(self):
        for k in ("policy_input","choice","evidence"):
            exact_tree(self.rows[0][k],self.rows[1][k],"/"+k)
        a, = predict_windows(self.view,self.key,self.hypotheses[:1])
        old = self.rows[0]["choice"]["rows"][6]
        compare_frames(a["frames"][1:],old["frames"][:20],actual=False)
        resets = [{"kind":"RESET",**{k:v for k,v in r.items() if k not in ("tick","reasons")}}
                  for r in a["resets"]]
        exact_tree(resets,[e for e in old["events"] if e["kind"]=="RESET" and e["time"]<=4],"/reset")

    def test_b_value1(self):
        a, = predict_windows(self.view,self.key,self.hypotheses[1:2])
        compare_frames(a["frames"],self.rows[0]["step"]["frames"],actual=True)
        self.assertEqual(a["final_progress"],0.)
        self.assertEqual([(r["tick"],r["reasons"],r["progress_before"]) for r in a["resets"]],
                         [(62,["GEOMETRY_INVALID"],.05)])

    def test_c_value2(self):
        a, = predict_windows(self.view,self.key,self.hypotheses[2:])
        compare_frames(a["frames"],self.rows[1]["step"]["frames"],actual=True)
        self.assertEqual((a["first_qualified_tick"],a["longest_intervals"],a["resets"]),(74,6,[]))
        self.assertAlmostEqual(a["final_progress"],.30)

    def test_d_shared_control_is_exact_and_view_unchanged(self):
        before = copy.deepcopy(self.view)
        shared = predict_windows(self.view,self.key,self.hypotheses)
        independent = predict_windows(self.view,self.key,self.hypotheses,share_control=False)
        self.assertEqual(shared,independent)
        self.assertEqual(before,self.view)
        for a,b in zip(shared[1]["frames"],shared[2]["frames"]):
            self.assertEqual(a["control"],b["control"])
            self.assertEqual(a["positions"],b["positions"])
        self.assertNotEqual(shared[1]["final_progress"],shared[2]["final_progress"])

    def test_e_escaping_hypothesis_refused(self):
        with self.assertRaisesRegex(ValueError,"escape"):
            predict_windows(self.view,self.key,[Hypothesis((19.9,10.),(.4,0.))])
