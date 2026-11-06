import copy
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from research.non_oracle.belief import Beliefs
from research.non_oracle.environment import NonOracleEnvironment
from research.non_oracle.shadow_feedback_prediction import WorldHypothesis, consume_model, predict_feedback
from research.information_service_online.execution import ActualMeasurementCache, OnlineEnvironment


def view60():
    p = Path("runs/a2_switch_episode_001/R_D60.json")
    view = json.loads(p.read_bytes())["policy_input"]
    view["beliefs"] = {int(k):v for k,v in view["beliefs"].items()}
    return view


def receipt(tick, point, **kwargs):
    wls = dict(estimate=point,has_accepted_estimate=True,optimizer_converged=True,
               numerical_ill_conditioned=False,ambiguity_detected=False,boundary_active=False,
               numeric_contract_violation=False)
    return dict(provenance="SIMULATED",observation_origin="MODEL",receipt_id=str(tick),
                tick=tick,available_tick=tick,wls=wls) | kwargs


class FeedbackTests(TestCase):
    def test_equivalence_latency_admission_and_speed_cap(self):
        view = view60()
        target = view["targets"][1]
        q = [receipt(60,[9.,10.]),receipt(61,[float("nan"),10.]),receipt(65,[10.,10.]),
             receipt(65,[11.,10.]),receipt(80,[12.,10.],available_tick=81)]
        ref = Beliefs([target])
        for r in q:
            ref.enqueue(dict(source="ACTUAL",target_id=1,measurement_tick=r["tick"],
                             available_tick=r["available_tick"],estimate=r["wls"]))
        mirror,hist,decisions = consume_model(q,view["beliefs"][1],target["speed_limit"])
        self.assertEqual(mirror,ref.freeze(80)[1])
        self.assertEqual(hist,ref.history[1])
        self.assertEqual([r["accepted"] for r in decisions],[True,False,True,False,False])
        self.assertEqual(mirror["velocity_estimate"],[.8,0.])

    def test_provenance_boundaries(self):
        view = view60()
        ref = Beliefs([view["targets"][1]])
        with self.assertRaises(ValueError):
            ref.enqueue(dict(source="SIMULATED"))
        r = receipt(60,[9.,10.])
        for forged in (dict(r,source="ACTUAL"),dict(r,observation_origin="ACTUAL")):
            with self.assertRaises(ValueError):
                consume_model([forged],view["beliefs"][1],.8)
        mirror,*_ = consume_model([r],view["beliefs"][1],.8)
        self.assertEqual(mirror["source"],"ACTUAL_WLS")
        for obj in (mirror,r):
            with self.assertRaises((KeyError,ValueError)):
                ref.enqueue(obj)
            with self.assertRaises(ValueError):
                consume_model([obj],view["beliefs"][1],.8) if obj is mirror else consume_model([dict(obj,source="ACTUAL")],view["beliefs"][1],.8)
        self.assertEqual(ref.pending,[])

    def test_zero_production_calls_and_branch_independence(self):
        view = view60()
        before = copy.deepcopy(view)
        with (patch.object(Beliefs,"enqueue",side_effect=AssertionError) as enqueue,
              patch.object(OnlineEnvironment,"step",side_effect=AssertionError) as step,
              patch.object(NonOracleEnvironment,"_fuse",side_effect=AssertionError) as fusion,
              patch.object(ActualMeasurementCache,"query",side_effect=AssertionError) as sampler):
            a = predict_feedback(view,WorldHypothesis("nominal",(9.,10.3),(0.,0.)))
            b = predict_feedback(view,WorldHypothesis("offline",(9.2,10.1),(.4,0.),True))
        for mock in (enqueue,step,fusion,sampler):
            mock.assert_not_called()
        self.assertEqual(view,before)
        self.assertEqual(len(a["prefix"]["rows"]),21)
        for branch in ("F0","F1"):
            self.assertEqual(a[branch]["first_new_fusion_tick"],81)
            self.assertTrue(all(r["segment_id"]==a["segment"]["segment_id"] for r in a[branch]["rows"]))
        a["F0"]["rows"][0]["positions"][0][0] = -1
        self.assertNotEqual(a["F1"]["rows"][0]["positions"][0][0],-1)
        self.assertNotEqual(a["prefix"]["rows"][-1]["positions"][0][0],-1)
        for x,y in zip(a["prefix"]["rows"],b["prefix"]["rows"],strict=True):
            self.assertEqual(x["control"],y["control"])
            self.assertEqual(x["positions"],y["positions"])
            self.assertNotEqual(x["result"]["stream_id"],y["result"]["stream_id"])
        decisions = b["feedback"]["consumption"]
        self.assertEqual(sum(d["accepted"] and r["Q"]=="FAIL"
                             for d,r in zip(decisions,b["prefix"]["rows"],strict=True)),10)
        a["feedback"]["internal_science_mirror"]["position_estimate"][0] = -1
        self.assertNotEqual(b["feedback"]["internal_science_mirror"]["position_estimate"][0],-1)
        self.assertEqual(view,before)
