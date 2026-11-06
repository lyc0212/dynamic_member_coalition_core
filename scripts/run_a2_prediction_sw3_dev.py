"""Run only the three preregistered SW3 development families."""
from dataclasses import asdict, is_dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter, process_time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import numpy as np

from pursuit_v2.config import Config
from research.non_oracle.environment import StaggeredEnvironment
from research.non_oracle.policy import command
from research.non_oracle.sw3_c1_actual_labels import actions, extract_label
from research.non_oracle.sw3_c1_manifest import announcements_for, manifest
from research.non_oracle.sw3_c1_private_worlds import private_world
from research.non_oracle.sw3_c1_sealing import (
    archive_private, association_receipt, compare_family, public_handoff,
    seal_prediction, verify_prediction_seal,
)
from research.non_oracle.sw3_f1_prediction import predict_method
from scripts.run_a1 import Sensing

ROOT = Path("reports/a2_prediction_sw3_dev_001")
FAMILIES = (11,6,4)
METHODS = ("M0","M1","M2")
HEAD = "181c53af651dda73fb0f82cde88702bc10f22b80"
SUMMARY_KEYS = ("predicted_completion_status_set","predicted_completion_ticks",
                "completion_time_envelope","noncompletion_possible")


def read(path):
    return json.loads(Path(path).read_bytes().decode("utf-8-sig"))


def encode_special(value):
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value,np.ndarray):
        return value.tolist()
    if isinstance(value,np.generic):
        return value.item()
    raise TypeError(f"Unsupported scientific output type: {type(value)!r}")


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("xb") as f:
        f.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False,
                           default=encode_special).encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require_family(n):
    if type(n) is not int or n not in FAMILIES:
        raise ValueError("Only the preregistered DEV families 11, 6, 4 are enabled")


def clocks():
    return process_time(),perf_counter()


def elapsed(start):
    cpu,wall=clocks()
    return dict(cpu=cpu-start[0],wall=wall-start[1])


def commit(env,tick,target):
    before=env.metrics()
    cp=env.observe_public()
    if env.tick!=tick or env.decision_tick!=tick:
        raise ValueError(f"Unexpected commit cut {tick}")
    result=env.step(actions(target),cp["checkpoint_id"],tick,f"sw3-dev-D{tick}")
    if result["status"]!="COMMITTED" or result["end_tick"]!=tick+20 or result["replayed"]:
        raise ValueError(f"Invalid transaction at {tick}: {result.get('status')}")
    after=env.metrics()
    if result["frames"][0]["assignment"]!=actions(target):
        raise ValueError(f"Wrong fixed assignment at {tick}")
    return result,dict(tick=tick,wls=after["reported_estimator_calls"]-before["reported_estimator_calls"],
        fusions=len(result["fusion_records"]),samples=after["actual_sampling_attempts"]-before["actual_sampling_attempts"])


def prepare_family(n,path,world_template,ann_template,*,sample=None):
    require_family(n)
    announcements=announcements_for(ann_template,n)
    save(path/"public"/"announcements.json",announcements)
    prepared,worlds=[],[]
    for w in range(4):
        t=clocks()
        folder=path/"private"/f"world_{w}"
        sampled=(sample or private_world)(world_template,"dev",n,w,worlds)
        save(folder/"draw.json",sampled)
        if sampled["status"]!="ACCEPTED":
            raise ValueError(f"Exhausted DEV {n}/{w}")
        world=sampled["world"]
        worlds.append(world)
        env=StaggeredEnvironment(world,Sensing(),f"SW3_DEV_{n}_{w}",announcements["announcements"])
        counts=[]
        for tick in (0,20,40):
            view=env.prepare_decision()
            if [t["id"] for t in view["targets"]]!=[0] or 1 in view["beliefs"]:
                raise ValueError("T1 visible before tick60")
            step,count=commit(env,tick,0)
            save(folder/f"D{tick}.json",dict(policy_input=view,step=step,cost=count))
            if any(r["frame"]["target_id"]==1 for r in step["fusion_records"]):
                raise ValueError("T1 sampled before allocation")
            counts.append(count)
        view=env.prepare_decision()
        cp=env.observe_public()["checkpoint_id"]
        if env.tick!=60 or env.decision_tick!=60 or view["assignment"]!=actions(0):
            raise ValueError("World did not pause before C6")
        if sum(c["wls"] for c in counts)>61:
            raise ValueError("Prefix WLS budget exceeded")
        public_handoff(view)
        save(folder/"D60_PUBLIC_CUT.json",view)
        prepared.append(dict(env=env,world=world,view=view,cp=cp,folder=folder,
                             prefix=counts,prefix_timing=elapsed(t)))
    return prepared


def verify_seals(public_dir,view):
    seals=read(public_dir/"PREDICTIONS_SEALED.json")
    if list(seals)!=list(METHODS):
        raise ValueError("Missing complete three-method seal")
    for m,seal in seals.items():
        p=public_dir/f"{m}_prediction.json"
        if sha(p)!=seal["content_sha256"]:
            raise ValueError(f"Prediction content changed: {m}")
        verify_prediction_seal(view,seal["summary"])
        payload=read(p)
        if (payload["method"]!=m or seal["summary"]["body"]["method"]!=m or
                {k:payload["prediction"][k] for k in SUMMARY_KEYS}!=seal["summary"]["body"]["summary"]):
            raise ValueError(f"Summary/content binding mismatch: {m}")
    return seals


def predict_and_seal(public_dir,view,pins,predict=predict_method):
    seals={}
    for index,m in enumerate(METHODS,1):
        # Round-trip a public-only file; each method receives its own decoded object.
        cut=read(public_dir/"D60.json")
        payload=predict(cut["D60"],m)
        selection,prediction=payload["selection"],payload["prediction"]
        k=1 if m=="M0" else 3
        if (selection["public_sha256"]!=cut["public_sha256"] or len(selection["selected"])!=k
                or len(prediction["results"])!=k or prediction["cost"]["wls"]>41*k
                or selection["geometry_endpoints"]>(1230 if m=="M2" else 0) or selection["screening_wls"]!=0):
            raise ValueError(f"Prediction provenance or budget mismatch: {m}")
        summary=seal_prediction(view,m,{k:prediction[k] for k in SUMMARY_KEYS},sequence=index)
        payload["source_pins"]=pins
        target=public_dir/f"{m}_prediction.json"
        save(target,payload)
        seals[m]=dict(content_sha256=sha(target),summary=summary)
    save(public_dir/"PREDICTIONS_SEALED.json",seals)
    return verify_seals(public_dir,view)


def transition(step,target):
    row, = [x for x in step["action_commit"]["transitions"] if x["target_id"]==target]
    return row


def finish(prepared, public_dir, view):
    verify_seals(public_dir,view)
    t=clocks()
    env=prepared["env"]
    if env.tick!=60 or env.decision_tick!=60 or env.observe_public()["checkpoint_id"]!=prepared["cp"]:
        raise ValueError("D60 pause identity changed")
    first,c60=commit(env,60,1)
    save(prepared["folder"]/"D60_STEP.json",first)
    opened=transition(first,1)
    if opened["kind"]!="FIRST_ASSIGNMENT" or transition(first,0)["kind"]!="WITHDRAW":
        raise ValueError("C6 did not open a new T1 segment")
    d80=env.prepare_decision()
    consumed=[r for r in env.beliefs.consumed if r["target_id"]==1]
    ticks=[f["frame"]["tick"] for f in first["fusion_records"] if f["frame"]["target_id"]==1]
    if (ticks!=list(range(60,81)) or [r["measurement_tick"] for r in consumed]!=ticks
            or any(r["available_tick"]!=r["measurement_tick"] or r["consumed_tick"]!=80 for r in consumed)):
        raise ValueError("Incorrect D80 WLS consumption")
    second,c80=commit(env,80,1)
    save(prepared["folder"]/"D80.json",dict(policy_input=d80,step=second,consumed=consumed))
    keep=transition(second,1)
    if (keep["kind"]!="KEEP" or keep["new_segment_id"]!=opened["new_segment_id"]
            or keep["old_segment_id"]!=opened["new_segment_id"]
            or second["frames"][0]["progress"]["1"]!=first["frames"][-1]["progress"]["1"]
            or second["frames"][0]["actual_endpoints"]["1"]!=first["frames"][-1]["actual_endpoints"]["1"]):
        raise ValueError("KEEP changed the service state")
    if c60["wls"]+c80["wls"]>41:
        raise ValueError("Label-window WLS budget exceeded")
    state=env.private_snapshot()["state"]
    label=extract_label(second,state)
    end=label["completion_tick"] or 100
    frames=second["fusion_records"]
    if ([f["frame"]["tick"] for f in frames]!=list(range(81,end+1))
            or any(f["start_tick"]!=81 or f["frame"]["stream_id"]==first["fusion_records"][-1]["frame"]["stream_id"] for f in frames)
            or c80["samples"]!=2*len(frames)):
        raise ValueError("KEEP flow restarted early or sampled after release")
    for step,b in ((first,prepared["view"]["beliefs"][1]),(second,d80["beliefs"][1])):
        cfg=Config(**d80["config"])
        for f in step["frames"][1:]:
            if any(f["control_elapsed_by_robot"][:2]):
                expected=command(b,f["tick"]-1,f["positions_start"][:2],["dual_neg45","dual_pos45"],cfg)
                np.testing.assert_allclose(f["control"][:2],expected,rtol=0,atol=1e-10)
    result=dict(label=label,archive=archive_private(prepared["world"],label),
                counts=prepared["prefix"]+[c60,c80],prefix_timing=prepared["prefix_timing"],window_timing=elapsed(t),
                diagnostics=diagnose(first,second,consumed,prepared["view"]["beliefs"][1],d80["beliefs"][1]))
    save(prepared["folder"]/"LABEL.json",result)
    return result


def diagnose(first,second,consumed,prior,updated):
    # One endpoint per tick. The KEEP left endpoint is already settled.
    frames=first["frames"]+second["frames"][1:]
    rows=[]
    for f in frames:
        ep=f["actual_endpoints"].get("1")
        if ep:
            rows.append(dict(tick=f["tick"],G=ep["G"],Q=ep["quality"]["status"],progress=f["progress"]["1"]))
    streak=longest=good=0
    for a,b in zip(rows,rows[1:]):
        valid=b["tick"]==a["tick"]+1 and a["G"] and b["G"] and a["Q"]==b["Q"]=="PASS"
        streak=streak+1 if valid else 0
        good+=int(valid)
        longest=max(longest,streak)
    return dict(endpoints=rows,g_bad=sum(not r["G"] for r in rows),
        q_fail=sum(r["Q"]=="FAIL" for r in rows),q_unknown=sum(r["Q"]=="UNKNOWN" for r in rows),
        g_and_q_bad=sum(not r["G"] and r["Q"]!="PASS" for r in rows),
        valid_intervals=good,longest_intervals=longest,
        resets=[e for step in (first,second) for e in step["events"] if e["target_id"]==1 and e["kind"]=="INTERRUPTED"],
        tick80_consumed=len(consumed),accepted=sum(
            e is not None and e["has_accepted_estimate"] and e["optimizer_converged"] and not any(
                e[k] for k in ("numerical_ill_conditioned","ambiguity_detected","boundary_active","numeric_contract_violation"))
            and len(e["estimate"])==2 and np.isfinite(e["estimate"]).all()
            for e in (r["result"]["estimate_result"] for r in first["fusion_records"])),
        prior=prior,updated=updated,first_post_feedback_control=second["frames"][1]["control"])


def evaluate(seals,labels):
    rows=[]
    nominal=seals["M0"]["summary"]["body"]["summary"]["predicted_completion_status_set"]==[True]
    for i,result in enumerate(labels):
        y=result["label"]["completed_by_H"]
        tick=result["label"]["completion_tick"]
        methods={}
        for m,s in seals.items():
            p=s["summary"]["body"]["summary"]
            classes,ts,env=p["predicted_completion_status_set"],p["predicted_completion_ticks"],p["completion_time_envelope"]
            miss=int(y not in classes)
            mixed=int(len(classes)==2)
            methods[m]=dict(covered=not miss,mixed=bool(mixed),classes=classes,
                losses={str(l):miss+l*mixed for l in (0.,.1,.25,.5)},
                discrete_hit=tick in ts if y else None,
                envelope_hit=bool(env and env[0]<=tick<=env[1]) if y else None,
                envelope_width=env[1]-env[0] if env else None,
                lower_median_error=abs(ts[(len(ts)-1)//2]-tick) if y and ts else None,
                nearest_error=min(abs(t-tick) for t in ts) if y and ts else None,
                risk_alert=nominal and False in classes)
        rows.append(dict(world=i,actual=result["label"],methods=methods))
    means={m:{str(l):sum(r["methods"][m]["losses"][str(l)] for r in rows)/4 for l in (0.,.1,.25,.5)}
           for m in METHODS}
    return dict(worlds=rows,loss_means=means,M1_minus_M2={k:means["M1"][k]-means["M2"][k] for k in means["M1"]})


def run_family(n,path,world,ann,*,prepare=None):
    events=[]
    def mark(event,**fields):
        events.append(dict(sequence=len(events)+1,event=event,**fields))
        save(path/"order"/f"{len(events):02d}.json",events[-1])
    p=(prepare or prepare_family)(n,path,world,ann)
    mark("FOUR_D60_PAUSED",ticks=[w["env"].tick for w in p])
    handoff=compare_family([w["view"] for w in p])
    motion={(tuple(w["world"]["targets"][1]["position_at_birth"]),tuple(w["world"]["targets"][1]["velocity"])) for w in p}
    if len(motion)!=4:
        raise ValueError("Expected four different private motions")
    public=path/"public"
    save(public/"D60.json",handoff)
    mark("PUBLIC_EQUALITY_PASS",public_sha256=handoff["public_sha256"])
    pins={p:sha(p) for p in ("research/non_oracle/sw3_public_hypotheses.py","research/non_oracle/sw3_f1_prediction.py",
                             "docs/A2_PRED_SW3_METHOD_SPEC_V1.md")}
    seals=predict_and_seal(public,handoff["D60"],pins)
    mark("ALL_PREDICTIONS_SEALED",digests={m:s["content_sha256"] for m,s in seals.items()})
    labels=[]
    for w,x in enumerate(p):
        labels.append(finish(x,public,handoff["D60"]))
        mark("ACTUAL_LABEL",world=w)
    seals=verify_seals(public,handoff["D60"])
    links=[{m:association_receipt(handoff["D60"],s["summary"],v["archive"],sequence=len(events)+1)
            for m,s in seals.items()} for v in labels]
    save(path/"ASSOCIATION.json",links)
    mark("ASSOCIATED")
    metrics=evaluate(seals,labels)
    save(path/"METRICS.json",metrics)
    mark("EVALUATED")
    return metrics


def main():
    if subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()!=HEAD:
        raise ValueError("Unexpected baseline HEAD")
    c1=Path("reports/a2_prediction_sw3_c1_001")
    pins=read(c1/"SOURCE_PINS.json")["pins"]|read(c1/"SHA256.json")
    if not all(sha(p)==h for p,h in pins.items()):
        raise ValueError("Frozen input changed")
    if tuple(r["n"] for r in manifest() if r["split"]=="dev")!=FAMILIES:
        raise ValueError("Frozen DEV split changed")
    ROOT.mkdir(exist_ok=False)
    save(ROOT/"SOURCE_PINS.json",dict(head=HEAD,pins=pins))
    family=None
    try:
        world=read("configs/a2_value2_two_target_v1.json")
        ann=read("configs/a2_value2_public_announcements_v1.json")
        results={}
        for family in FAMILIES:
            results[str(family)]=run_family(family,ROOT/f"family_{family}",world,ann)
        save(ROOT/"DEV_METRICS.json",results)
        if not all(sha(p)==h for p,h in pins.items()):
            raise ValueError("Frozen files changed during DEV")
    except Exception as e:
        save(ROOT/"FAILURE.json",dict(status="SW3_DEV_BLOCKED",family=family,error=repr(e)))
        raise


if __name__=="__main__":
    main()
