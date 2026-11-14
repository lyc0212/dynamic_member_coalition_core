from copy import deepcopy
import json
import math
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import numpy as np

from pursuit_v2.observation_geometry import offset, radius
from research.information_service_online.execution import ActualMeasurementCache, OnlineEnvironment
from research.information_service_online.measurements import assemble_left_state
from research.non_oracle.belief import Beliefs
from research.non_oracle.environment import NonOracleEnvironment
from research.non_oracle.shadow_feedback_prediction import TEAM, WorldHypothesis, consume_model, predict_feedback
from research.non_oracle.sw3_f1_prediction import aggregate, outcome, predict_f1
from research.non_oracle.sw3_public_hypotheses import digest, library, margin, pick_m1, pick_m2, public_input, score, select_hypotheses

RUN = Path("runs/a2_switch_episode_001")
ATOL = 1e-10


def read(p):
    return json.loads(Path(p).read_bytes())


def public_view():
    return read(RUN/"R_D60.json")["policy_input"]


def compare_reference(view,h):
    native = predict_feedback(public_input(view)[0],h)
    from contextlib import ExitStack
    with ExitStack() as stack:
        probes = [stack.enter_context(patch.object(cls,name,side_effect=AssertionError(name))) for cls,name in (
            (Beliefs,"enqueue"),(OnlineEnvironment,"step"),(NonOracleEnvironment,"_fuse"),(ActualMeasurementCache,"query"))]
        result = predict_f1(view,h)
        assert all(p.call_count==0 for p in probes)
    assert result["segment"]==native["segment"]
    left,right = result["feedback"],native["feedback"]
    fields = ("internal_science_mirror","accepted_history")
    assert all(left[k]==right[k] for k in fields)
    stripped = lambda rows:[{k:v for k,v in row.items() if k!="receipt_id"} for row in rows]
    assert stripped(left["consumption"])==stripped(right["consumption"])
    errors = dict(control=0.,positions=0.,bearings=0.)
    differences = []
    for part in ("prefix","F1"):
        x,y = result[part],native[part]
        assert x["first_new_fusion_tick"]==y["first_new_fusion_tick"]==(60 if part=="prefix" else 81)
        assert x["estimator_calls"]==y["estimator_calls"]
        for a,b in zip(x["rows"],y["rows"],strict=True):
            for k in ("tick","G","Q","progress","resets","completed","released","segment_id"):
                assert a[k]==b[k],(h.label,part,a["tick"],k,a[k],b[k])
            assert a["provenance"]["observation_origin"]=="MODEL" and not a["assembly"]["actual"]
            assert a["result"]["stream_id"]!=b["result"]["stream_id"]
            for row in (a,b):
                r = row["result"]
                assert r["frame_id"]==f'{r["stream_id"]}:tick{row["tick"]}'
                assert all(p["packet_id"]==f'{r["frame_id"]}:{p["sensor_id"]}' for p in row["assembly"]["frame"]["records"])
            for k,l,r in (("control",a["control"],b["control"]),("positions",a["positions"],b["positions"]),
                          ("bearings",a["result"]["payload"]["bearings"],b["result"]["payload"]["bearings"])):
                np.testing.assert_allclose(l,r,atol=ATOL,rtol=0,err_msg=f"{h.label}/{part}/{a['tick']}/{k}")
                errors[k]=max(errors[k],float(np.max(np.abs(np.asarray(l)-np.asarray(r)))))
            if a["result"]["estimate_result"]!=b["result"]["estimate_result"]:
                differences.append(dict(part=part,tick=a["tick"]))
            left_est,right_est = (r["result"]["estimate_result"] for r in (a,b))
            assert (left_est is None)==(right_est is None)
            if left_est is not None:
                for k in ("has_accepted_estimate","optimizer_converged","numerical_ill_conditioned",
                          "ambiguity_detected","boundary_active","numeric_contract_violation"):
                    assert left_est[k]==right_est[k],(h.label,part,a["tick"],k)
                if left_est["has_accepted_estimate"]:
                    np.testing.assert_allclose(left_est["estimate"],right_est["estimate"],rtol=0,atol=ATOL)
    assert result["cost"]["wls"]<=41 and "F0" not in result
    return result,dict(max_errors=errors,internal_wls_differences=differences,
                       sw2_calls=sum(native[k]["estimator_calls"] for k in ("prefix","F0","F1")),
                       sw2_f1_calls=sum(native[k]["estimator_calls"] for k in ("prefix","F1")))


class PublicSelectionTests(TestCase):
    def test_library_and_selection(self):
        v = public_view()
        for method,expected in (("M0",["N/N"]),("M1",["N/N","X+/E","Y−/NE"]),
                                ("M2",["N/N","Y−/N","Y+/北"])):
            with patch("research.non_oracle.policy.estimate",side_effect=AssertionError):
                r = select_hypotheses(v,method)
            self.assertEqual(len(r["all_candidates"]),30)
            self.assertEqual([h.label for h in r["all_candidates"][:6]],["N/N","N/E","N/NE","N/SE","N/北","N/南"])
            self.assertEqual([h.label for h in r["selected"]],expected)
        self.assertEqual(digest([-0.]),digest([0.]))
        v2 = deepcopy(v)
        v2["beliefs"]={int(k):b for k,b in v2["beliefs"].items()}
        v2["beliefs"][0]["diagnostics"]={"unread_diagnostic":1}
        self.assertEqual(select_hypotheses(v,"M2")["public_sha256"],select_hypotheses(v2,"M2")["public_sha256"])

    def test_invalid_public_input(self):
        for mutation in (lambda v:v.update(tick=61),lambda v:v.update(private_world={}),
                         lambda v:v["targets"][1].update(velocity_prior=[.1,0.]),
                         lambda v:v["targets"][1].update(design_error_bound=math.inf),
                         lambda v:v["positions"][0].__setitem__(0,math.nan),
                         lambda v:v["targets"][1].update(position_at_birth=[9.,10.])):
            v=public_view()
            mutation(v)
            with self.assertRaises((ValueError,TypeError)):
                select_hypotheses(v,"M0")

    def test_filter_dedup_and_ties(self):
        _,cfg,t = public_input(public_view())
        _,legal = library(dict(t,coarse_position=[19.5,10.]),cfg)
        self.assertNotIn("X+/E",[h.label for h in legal])
        self.assertEqual(pick_m1(legal)[1],legal[1])
        _,dedup = library(dict(t,design_error_bound=1e-100),cfg)
        self.assertEqual(len(dedup),6)
        self.assertEqual(pick_m2(dedup,{h.label:(1,0,0.) for h in dedup}),dedup[:3])
        with self.assertRaisesRegex(ValueError,"BLOCKED"):
            library(dict(t,coarse_position=[20.,10.]),cfg)

    def test_geometry_and_quantization(self):
        v,cfg,_ = public_input(public_view())
        point=[0.,0.]
        team=[dict(robot_id=i,role=r) for i,r in TEAM]
        slots=[s for s in v["current_slots"] if s["slot_key"]["target_id"]==1]
        base=np.array([offset(r,cfg) for _,r in TEAM])
        for i in (0,1):
            for error in (.01,.3,radius(cfg),np.nextafter(radius(cfg),0),np.nextafter(radius(cfg),math.inf)):
                pos=base.copy()
                pos[i,0]+=error
                official=assemble_left_state(tick=60,target_id=1,target_position=point,
                    positions=pos.tolist()+[[2.,2.]],sensor_profiles=v["sensor_profiles"],current_slots=slots,
                    team=team,stream_id="SW3:model-test",actual=False)
                self.assertEqual(margin(pos,point,cfg)>=0,official["G"])
        self.assertEqual(score([1.]*22+[-1.]*19)[:2],(21,10**12))
        self.assertEqual(score([1/8192]*41)[1],122070312)


class FeedbackTests(TestCase):
    def test_boundary_and_aggregation(self):
        self.assertEqual(outcome({"tick":100,"completed":True})["completion_tick"],100)
        self.assertEqual(outcome({"tick":100,"completed":False})["terminal_status"],"ACTIVE_AT_H")
        r=lambda t,c:dict(public_sha256="cut",offline_diagnostic=False,Y_H=outcome(dict(tick=t,completed=c)),
                         cost=dict(wls=0,frames=0,intervals=0,wall=0,cpu=0))
        both=aggregate([r(91,True),r(97,True),r(91,True),r(100,False)])
        self.assertEqual(both["predicted_completion_ticks"],[91,97])
        self.assertEqual(both["completion_time_envelope"],[91,97])
        self.assertTrue(both["noncompletion_possible"])
        self.assertIsNone(aggregate([r(100,False)])["completion_time_envelope"])
        self.assertEqual(aggregate([r(100,False)])["predicted_completion_ticks"],[])
        fixture=r(91,True)
        cloned=aggregate([fixture,fixture])
        cloned["results"][0]["Y_H"]["completion_tick"]=1
        self.assertEqual(fixture["Y_H"]["completion_tick"],91)
        separate=r(91,True)
        cloned=aggregate([fixture,separate])
        cloned["results"][0]["Y_H"]["completion_tick"]=1
        self.assertEqual(cloned["results"][1]["Y_H"]["completion_tick"],91)
        with self.assertRaises(ValueError):
            aggregate([dict(fixture,offline_diagnostic=True)])

    def test_unchanged_input_and_forged_source(self):
        v=public_view()
        with self.assertRaises(ValueError):
            consume_model([dict(source="ACTUAL")],v["beliefs"]["1"],.8)
        a=deepcopy(v)
        result=predict_f1(v,select_hypotheses(v,"M0")["selected"][0])
        self.assertEqual(result["actual_simulation_end_tick"],97)
        self.assertEqual(result["F1"]["rows"][-1]["tick"],97)
        self.assertEqual(result["F1"]["rows"][-1]["released"],[0,1])
        self.assertEqual(result["Y_H"]["observation_end_tick"],100)
        production=Beliefs([v["targets"][1]])
        mirror=result["feedback"]["internal_science_mirror"]
        self.assertEqual(mirror["source"],"ACTUAL_WLS")
        with self.assertRaises(ValueError):
            production.enqueue(mirror)
        self.assertEqual(production.pending,[])
        result["prefix"]["rows"][0]["positions"][0][0]=-1
        self.assertEqual(v,a)
        self.assertNotEqual(result["F1"]["rows"][0]["positions"][0][0],-1)
