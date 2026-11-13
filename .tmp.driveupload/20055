"""Execute only fixed-team conditional windows and independently audit frozen references."""
import hashlib
import json
from pathlib import Path
from time import perf_counter, process_time

import numpy as np

from research.non_oracle.belief import Beliefs
from research.non_oracle.shadow_feedback_prediction import WorldHypothesis, predict_feedback
from scripts.gq_windows.a0_identity import exact_tree

OUT = Path(__file__).parent
SW1 = Path("reports/a2_prediction_shadow_sw1_001")
POST = Path("reports/a2_prediction_shadow_sw1_post_audit_001")
RUNS = {"VALUE1_ORACLE_DIAGNOSTIC":"a2_switch_episode_001",
        "VALUE2_ORACLE_DIAGNOSTIC":"a2_value2_open_001"}
ATOL = 1e-10  # Model coordinate/velocity units; accommodates WLS roundoff, far below .15 geometry threshold.
FLAGS = ("has_accepted_estimate","optimizer_converged","numerical_ill_conditioned",
         "ambiguity_detected","boundary_active","numeric_contract_violation")


def read(p):
    return json.loads(Path(p).read_bytes().decode("utf-8-sig"))


def save(n,data):
    (OUT/(n+".json")).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def numeric(a,b,path):
    assert (a is None)==(b is None), path
    if a is None:
        return 0.
    np.testing.assert_allclose(a,b,atol=ATOL,rtol=0,err_msg=path)
    return float(np.max(np.abs(np.asarray(a)-np.asarray(b))))


def step(root,tick):
    return read(root/f"R_D{tick}.json")


def admission_reference(target, estimates):
    """Isolated in-memory reference; no production environment is constructed."""
    ref = Beliefs([target])
    accepted, consumed = [], []
    for tick,available,e in estimates:
        ref.enqueue(dict(source="ACTUAL",target_id=1,measurement_tick=tick,available_tick=available,estimate=e))
        old = len(ref.history[1])
        belief = ref.freeze(80)[1]
        consumed.append((tick,available,available<=80))
        accepted.append(len(ref.history[1])>old)
    return belief,ref.history[1],accepted,consumed


def compare_actual(result,root,view):
    d60,d80 = step(root,60),step(root,80)
    world = read(root/"WORLD_INPUT.json")
    assert world["measurement_model"]["angle_perturbation"]==0
    assert world["config"]["step_dt"]==.05
    assert d60["policy_input"]["config"]==d80["policy_input"]["config"]==view["config"]
    t = world["targets"][1]
    assert not t["turns"] and all(when>=5 and rate==0 for when,rate in t["arc_rates"])
    team = result["segment"]["team"]
    expected_actions = [dict(target=1,role=m["role"]) for m in team]+[dict(target=None,role="none")]
    for d in (d60,d80):
        assert d["choice"]["actions"]==expected_actions
        assert d["step"]["status"]=="COMMITTED"
        assert d["step"]["frames"][0]["statuses"][1]=="active"
        assert [{k:v for k,v in s.items() if k!="observed_tick"} for s in d["policy_input"]["sensor_profiles"]]==[
            {k:v for k,v in s.items() if k!="observed_tick"} for s in view["sensor_profiles"]]
    target = view["targets"][1]
    model = result["prefix"]["rows"]
    model_estimates = [(r["tick"],r["tick"],r["result"]["estimate_result"]) for r in model]
    historical = [f for f in d60["step"]["fusion_records"] if f["frame"]["target_id"]==1]
    historic_estimates = [(f["frame"]["tick"],f["frame"]["tick"],f["result"]["estimate_result"]) for f in historical]
    mirror = result["feedback"]["internal_science_mirror"]
    model_ref,model_hist,model_admitted,model_order = admission_reference(target,model_estimates)
    historical_ref,historical_hist,historical_admitted,historical_order = admission_reference(target,historic_estimates)
    exact_tree(mirror,model_ref,"/reference/model_mirror")
    exact_tree(result["feedback"]["accepted_history"],model_hist,"/reference/model_history")
    assert [r["accepted"] for r in result["feedback"]["consumption"]]==model_admitted==historical_admitted
    assert [(r["measurement_tick"],r["available_tick"],r["consumed"]) for r in result["feedback"]["consumption"]]==model_order==historical_order
    saved_consumed = [r for r in read(root/"R.json")["observations_consumed"] if r["target_id"]==1 and r["consumed_tick"]==80]
    assert [(r["measurement_tick"],r["available_tick"],True) for r in saved_consumed]==historical_order
    actual_belief = d80["policy_input"]["beliefs"]["1"]
    exact_tree(historical_ref,actual_belief,"/reference/history_mirror")
    for k in ("estimate_tick","last_observation_tick","available_tick","status","source","velocity_source"):
        exact_tree(mirror[k],actual_belief[k],"/belief/"+k)
    belief_errors = {k:numeric(mirror[k],actual_belief[k],"/belief/"+k)
                     for k in ("position_estimate","velocity_estimate")}
    assert [t for t,_ in model_hist]==[t for t,_ in historical_hist]
    history_error = numeric([p for _,p in model_hist],[p for _,p in historical_hist],"/accepted_history")
    for a in FLAGS:
        assert mirror["diagnostics"][a]==actual_belief["diagnostics"][a]
    assert result["segment"]["segment_id"]==d80["policy_input"]["histories"][1]["active_segment_id"]
    assert result["F1"]["first_new_fusion_tick"]==81
    physical = []
    for part,raw in (("prefix",d60),("F1",d80)):
        step_result = raw["step"]
        predictions = result[part]["rows"]
        expected = {f["tick"]:f for f in step_result["frames"]}
        expected_fusion = {f["frame"]["tick"]:f for f in step_result["fusion_records"] if f["frame"]["target_id"]==1}
        assert set(expected_fusion)=={x["tick"] for x in predictions}
        for row in predictions:
            tick = row["tick"]
            f = expected[tick]
            ep = f["actual_endpoints"]["1"]
            assert row["segment_id"]==expected_fusion[tick]["actual_endpoint"].get("segment_id",result["segment"]["segment_id"])
            assert (row["G"],row["Q"],row["progress"])==(ep["G"],ep["quality"]["status"],f["progress"]["1"]),tick
            actual_result = expected_fusion[tick]["result"]
            a,b = row["result"]["estimate_result"],actual_result["estimate_result"]
            assert all(a[k]==b[k] for k in FLAGS),tick
            assert [x["progress_before"] for x in row["resets"]]==[
                x["progress_before"] for x in f["events"] if x["kind"]=="INTERRUPTED" and x["target_id"]==1],tick
            completed = any(x["kind"]=="COMPLETED" and x["target_id"]==1 for x in f["events"])
            assert row["completed"]==completed,tick
            if completed:
                assert row["released"]==[0,1] and all(x["target"] is None for x in f["assignment"])
            physical.append(dict(part=part,tick=tick,G=row["G"],Q=row["Q"],progress=row["progress"],
                control_error=numeric(row["control"],f["control"],f"/{part}/{tick}/control"),
                position_error=numeric(row["positions"],f["positions"],f"/{part}/{tick}/positions"),
                representative_error=numeric(a["estimate"],b["estimate"],f"/{part}/{tick}/WLS"),
                radius_error=numeric(row["result"]["quality"]["radius_proxy"],actual_result["quality"]["radius_proxy"],f"/{part}/{tick}/Q"),
                wls_internal_exact=a==b,completed=completed,released=row["released"],resets=row["resets"]))
    return dict(belief_errors=belief_errors,accepted_history_error=history_error,
        mirror=mirror,actual_belief=actual_belief,accepted_count=sum(model_admitted),consumption=result["feedback"]["consumption"],
        physical=physical)


def main():
    frozen = read(POST/"EVIDENCE_MAP.json")["source_pins"]
    frozen.update({p.as_posix():sha(p) for root in (SW1,POST) for p in root.iterdir() if p.is_file()})
    for name in RUNS.values():
        for file in ("R_D60.json","R_D80.json","R.json","WORLD_INPUT.json"):
            p = Path("runs")/name/file
            frozen.setdefault(p.as_posix(),sha(p))
    assert all(sha(p)==s for p,s in frozen.items())
    save("EVIDENCE_MAP",dict(frozen=frozen,tolerance=ATOL))
    root = Path("runs")/RUNS["VALUE1_ORACLE_DIAGNOSTIC"]
    view = step(root,60)["policy_input"]
    view["beliefs"]={int(k):v for k,v in view["beliefs"].items()}
    old = read(SW1/"ENDPOINTS.json")
    scenarios = [WorldHypothesis("nominal",(9.,10.3),(0.,0.))]
    for label,name in RUNS.items():
        # Driver reads only private physical initial conditions, never future observations.
        t = read(Path("runs")/name/"WORLD_INPUT.json")["targets"][1]
        scenarios.append(WorldHypothesis(label,tuple(t["position_at_birth"]),tuple(t["velocity"]),True))
    results, timing, prefix, comparisons = {}, {}, {}, {}
    for h in scenarios:
        def check(frozen_prefix):
            errors = []
            for a,b in zip(frozen_prefix["rows"],old[h.label]["frames"],strict=True):
                assert [a[k] for k in ("tick","G","Q","progress")]==[b[k] for k in ("tick","G","Q","progress")]
                errors.append(max(numeric(a[k],b[k],"/prefix/"+k) for k in ("positions","control")))
            assert [(r["tick"],e["progress_before"]) for r in frozen_prefix["rows"] for e in r["resets"]]==[
                (e["tick"],e["progress_before"]) for e in old[h.label]["resets"]]
            prefix[h.label]=dict(endpoints=len(errors),intervals=len(errors)-1,max_control_or_position_error=max(errors))
        cpu,wall=process_time(),perf_counter()
        r=predict_feedback(view,h,prefix_check=check)
        timing[h.label]=dict(cpu=process_time()-cpu,wall=perf_counter()-wall,
            calls={k:r[k]["estimator_calls"] for k in ("prefix","F0","F1")},
            intervals={k:len(r[k]["rows"])-(k=="prefix") for k in ("prefix","F0","F1")})
        results[h.label]=r
    save("SIMULATED_WLS_HISTORY",results)
    save("SW1_PREFIX_COMPARISON",prefix)
    save("TIMING",timing)
    effects={}
    for label,r in results.items():
        f0,f1=r["F0"]["rows"],r["F1"]["rows"]
        effects[label]=dict(F0=dict(end_tick=f0[-1]["tick"],progress=f0[-1]["progress"],completed=f0[-1]["completed"]),
            F1=dict(end_tick=f1[-1]["tick"],progress=f1[-1]["progress"],completed=f1[-1]["completed"]),
            max_shared_tick_control_delta=max(float(np.max(np.abs(np.array(a["control"])-b["control"]))) for a,b in zip(f0,f1)))
    save("F0_F1_COMPARISON",effects)
    for i,(label,name) in enumerate(RUNS.items(),1):
        c=compare_actual(results[label],Path("runs")/name,view)
        comparisons[label]=c
        save(f"VALUE{i}_PHYSICS_COMPARISON",c["physical"])
    save("TICK80_BELIEF_COMPARISON",{k:{a:b for a,b in v.items() if a!="physical"} for k,v in comparisons.items()})
    save("NUMERICAL_PROPAGATION",{k:dict(belief=v["belief_errors"],accepted_history_error=v["accepted_history_error"],
        physical_max={name:max(x[name] for x in v["physical"]) for name in (
            "control_error","position_error","representative_error","radius_error")},
        nonidentical_wls_internal_endpoints=sum(not x["wls_internal_exact"] for x in v["physical"])) for k,v in comparisons.items()})
    assert all(sha(p)==s for p,s in frozen.items())


if __name__=="__main__":
    main()
