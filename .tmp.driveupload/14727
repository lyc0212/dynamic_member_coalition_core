"""Supplement SW1 using production model-frame assembly and a private Bridge per probe."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter, process_time

import numpy as np

from pursuit_v2.service import ServiceState, advance_clock
from research.information_service_bridge.public_stream import BridgeFrameProcessor
from research.information_service_bridge.common import ContractError
from research.information_service_online.measurements import assemble_left_state
from research.information_service_online.public import IDS
from scripts.gq_windows.a0_identity import exact_tree

OUT = Path(__file__).parent
OLD = Path("reports/a2_prediction_shadow_sw1_001")
ROOTS = {
    "VALUE1_ORACLE_DIAGNOSTIC": Path("runs/a2_switch_episode_001"),
    "VALUE2_ORACLE_DIAGNOSTIC": Path("runs/a2_value2_open_001"),
}


def read(path):
    return json.loads(Path(path).read_bytes().decode("utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, data):
    (OUT/(name+".json")).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")


def difference(a,b,path=""):
    if type(a)!=type(b):
        return [path]
    if isinstance(a,dict):
        return [path+"/"+k for k in sorted(a.keys()^b.keys())]+[
            item for k in sorted(a.keys()&b.keys()) for item in difference(a[k],b[k],path+"/"+k)]
    if isinstance(a,list):
        return ([path] if len(a)!=len(b) else [
            item for i,(x,y) in enumerate(zip(a,b)) for item in difference(x,y,f"{path}/{i}")])
    if isinstance(a,float):
        return [] if np.isclose(a,b,rtol=1e-9,atol=1e-11) else [path]
    return [] if a==b else [path]


def verify_stream(label, hypothesis, saved, view, team, actual=None):
    j = 1
    stream = "SW1_POST_AUDIT:MODEL:"+label
    allowed = ["U"+str(m["robot_id"]) for m in team]
    bridge = BridgeFrameProcessor(allowed,60,stream,j)
    clock = ServiceState(team=tuple((m["robot_id"],m["role"]) for m in team))
    left, resets, records = None, [], []
    diagnostics = Counter()
    original_view = json.dumps(view,sort_keys=True)
    for tick, frame in zip(range(60,81),saved["frames"],strict=True):
        assert frame["tick"]==tick
        profiles = [dict(p,observed_tick=tick) for p in view["sensor_profiles"]]
        slots = [dict(slot_key=dict(target_id=j,robot_id=i,tick=tick),state="UNQUERIED",packet=None,
                      contract_id=IDS["measurement_slot"],slot_digest=None) for i in range(len(profiles))]
        if tick==60:
            exact_tree(slots,[s for s in view["current_slots"] if s["slot_key"]["target_id"]==j],"/left_slots")
        p,v = hypothesis
        point = [x+u*((tick-60)*.05) for x,u in zip(p,v)]
        assembled = assemble_left_state(tick=tick,target_id=j,target_position=point,
            positions=frame["positions"],sensor_profiles=profiles,current_slots=slots,team=team,
            stream_id=stream,actual=False)
        f = assembled["frame"]
        assert not assembled["actual"] and assembled["real_sampling_calls"]==0
        assert f["frame_id"]==f"{stream}:tick{tick}" and f["tick"]==tick and f["stream_id"]==stream
        assert all(s["source"]=="MODEL" and s["observed_slot_digest"] is None for s in assembled["source_slots"])
        for packet in f["records"]:
            assert packet["packet_id"]==f"{stream}:tick{tick}:{packet['sensor_id']}"
            assert packet["measurement_tick"]==packet["available_tick"]==tick
        if tick==60:
            bad = BridgeFrameProcessor(allowed,60,stream,j)
            for invalid in (dict(f,stream_id=stream+":foreign"),dict(f,tick=61,measurement_time=3.05,available_time=3.05)):
                try:
                    bad.process(invalid)
                except ContractError:
                    assert bad.estimator_calls==0 and bad.last_tick is None
                else:
                    raise AssertionError("Invalid frame was accepted")
        result = bridge.process(f)
        gq = (assembled["G"],result["quality"]["status"])
        exact_tree(list(gq),[frame["G"],frame["Q"]],f"/{label}/{tick}/GQ")
        if left is not None:
            clock,done,events = advance_clock(clock,1.05,clock.team,left==gq==(True,"PASS"),tick*.05)
            assert not done
            reasons = []
            if not left[0] or not gq[0]:
                reasons.append("GEOMETRY_INVALID")
            if "FAIL" in (left[1],gq[1]):
                reasons.append("QUALITY_FAIL")
            if "UNKNOWN" in (left[1],gq[1]):
                reasons.append("QUALITY_UNKNOWN")
            resets.extend(dict(tick=tick,reasons=reasons,**e) for e in events)
        left = gq
        exact_tree(clock.progress,frame["progress"],f"/{label}/{tick}/progress")
        drift = {}
        if actual is not None:
            expected = actual[tick]["result"]
            for k in ("payload","estimate_result"):
                drift[k] = difference(result[k],expected[k])
            quality_fields = ("status","reasons","estimate","J","I","singular_values","radius_proxy",
                              "estimator_diagnostics","representative_guard")
            drift["quality"] = difference({k:result["quality"][k] for k in quality_fields},
                                          {k:expected["quality"][k] for k in quality_fields})
            assert not drift["payload"], (label,tick,drift["payload"])
            assert gq==(actual[tick]["actual_endpoint"]["G"],expected["quality"]["status"])
            critical = ("has_accepted_estimate","optimizer_converged","numerical_ill_conditioned",
                        "ambiguity_detected","boundary_active","numeric_contract_violation","estimate")
            assert not difference({k:result["estimate_result"][k] for k in critical},
                                  {k:expected["estimate_result"][k] for k in critical}), (label,tick)
            diagnostics.update(k for k,v in drift.items() if v)
        records.append(dict(tick=tick,source="MODEL",G=gq[0],Q=gq[1],progress=clock.progress,
                            assembly=assembled,result=result,diagnostic_differences=drift))
    exact_tree(resets,saved["resets"],"/resets")
    assert bridge.last_tick==80 and bridge.estimator_calls==21
    assert json.dumps(view,sort_keys=True)==original_view
    return dict(records=records,resets=resets,estimator_calls=bridge.estimator_calls,
                start_records=bridge.start_records,diagnostic_difference_counts=diagnostics)


def main():
    historical = read("reports/a2_factorial_preflight_001/HISTORICAL_PINS.json")
    sw1 = read(OLD/"ACCEPTANCE.json")
    assert all(sha(path)==value for path,value in (historical|sw1["sha256"]).items())
    pins = historical|sw1["sha256"]|{p.as_posix():sha(p) for p in OLD.iterdir() if p.is_file()}
    def git(*args):
        return subprocess.check_output(["git",*args],text=True).strip()
    save("EVIDENCE_MAP",dict(head=git("rev-parse","HEAD"),git_status=git("status","--short"),
         original_status=sw1["status"],original=str(OLD),source_pins=pins,
         original_records={k:str(v/"R_D60.json") for k,v in ROOTS.items()}))
    original = read(OLD/"ENDPOINTS.json")
    rows = {k:read(p/"R_D60.json") for k,p in ROOTS.items()}
    v1,v2 = rows.values()
    view = v1["policy_input"]
    for k in ("policy_input","choice","evidence"):
        exact_tree(v1[k],v2[k],"/"+k)
    candidate = v1["choice"]["rows"][6]["key"]
    team = [dict(robot_id=i,role=r) for i,r in zip(candidate["robots"],candidate["roles"])]
    nominal = v1["choice"]["rows"][6]["frames"][:20]
    exact_tree(original["nominal"]["frames"][1:],nominal,"/nominal")
    report, timing = {}, {}
    for label in original:
        actual = None
        if label in ROOTS:
            world = read(ROOTS[label]/"WORLD_INPUT.json")
            assert world["measurement_model"]["angle_perturbation"]==0
            t = world["targets"][1]
            hypothesis = (t["position_at_birth"],t["velocity"])
            step = rows[label]["step"]
            actual = {r["frame"]["tick"]:r for r in step["fusion_records"]}
            assert all(r["frame"]["target_id"]==1 for r in actual.values())
            for saved,observed in zip(original[label]["frames"],step["frames"],strict=True):
                exact_tree(saved["progress"],observed["progress"]["1"],"/physical/progress")
                for k in ("positions","control"):
                    np.testing.assert_allclose(saved[k],observed[k],rtol=0,atol=1e-12)
            exact_tree([(e["at"]["event_tick"],e["reasons"],e["progress_before"]) for e in step["events"] if e["kind"]=="INTERRUPTED"],
                       [(e["tick"],e["reasons"],e["progress_before"]) for e in original[label]["resets"]],"/physical/resets")
        else:
            b = view["beliefs"]["1"]
            hypothesis = (b["position_estimate"],b["velocity_estimate"])
        cpu, wall = process_time(),perf_counter()
        report[label] = verify_stream(label,hypothesis,original[label],view,team,actual)
        timing[label] = dict(cpu=process_time()-cpu,wall=perf_counter()-wall,
                             estimator_calls=report[label]["estimator_calls"])
        save("SENSOR_STREAM_AUDIT",report)
    assert all(sha(path)==value for path,value in pins.items())
    save("SUPPLEMENT_TEST_RESULTS",dict(streams=3,endpoint_count=63,intervals_per_stream=20,
         negative_identity_or_order_checks=6,elapsed=timing,original_timing=str(OLD/"TIMING.json"),
         pins_checked=len(pins),audit_script_sha256=sha(__file__)))


if __name__=="__main__":
    main()
