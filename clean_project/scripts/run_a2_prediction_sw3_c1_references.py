"""Only the two named historical C1 mechanism references, ending at tick100."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import numpy as np

from research.non_oracle.sw3_c1_actual_labels import run_reference
from research.non_oracle.sw3_c1_sealing import compare_family, public_handoff, _compare

OUT = Path("reports/a2_prediction_sw3_c1_001")
ROOTS = ("a2_switch_episode_001","a2_value2_open_001")


def read(path):
    return json.loads(Path(path).read_bytes().decode("utf-8-sig"))


def save(name,data):
    (OUT/(name+".json")).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")


def compare_step(new,old,tick):
    for key in ("policy_input","consumed"):
        if key in old:
            _compare(json.loads(json.dumps(new[key])),old[key],f"/D{tick}/{key}")
    a,b=new["step"],old["step"]
    for k in ("status","start_tick","end_tick","events","ended_ids","new_ids"):
        _compare(a[k],b[k],f"/D{tick}/{k}")
    _compare(a["action_commit"]["transitions"],b["action_commit"]["transitions"],f"/D{tick}/transitions")
    errors=dict(control=0.,positions=0.,bearings=0.,estimate=0.)
    def close(x,y,key,path):
        np.testing.assert_allclose(x,y,rtol=0,atol=1e-10,err_msg=path)
        if np.size(x):
            errors[key]=max(errors[key],float(np.max(np.abs(np.asarray(x)-np.asarray(y)))))
    for x,y in zip(a["frames"],b["frames"],strict=True):
        cut=f"/D{tick}/frames/{x['tick']}"
        for k in ("tick","phase","assignment","statuses","progress","active_segment_ids","actual_endpoints","events"):
            _compare(x[k],y[k],f"{cut}/{k}")
        for k in ("positions","control"):
            close(x[k],y[k],k,f"{cut}/{k}")
    for x,y in zip(a["fusion_records"],b["fusion_records"],strict=True):
        f,g=x["frame"],y["frame"]
        for k in ("tick","target_id","measurement_time","available_time"):
            _compare(f[k],g[k],f"/D{tick}/fusion/{k}")
        for r,s in zip(f["records"],g["records"],strict=True):
            for k in ("sensor_id","sigma","measurement_tick","available_tick","status"):
                _compare(r[k],s[k],f"/D{tick}/packet/{k}")
            close(r["bearing"],s["bearing"],"bearings",f"/D{tick}/bearing")
        p,q=x["result"],y["result"]
        _compare(p["quality"]["status"],q["quality"]["status"],f"/D{tick}/Q")
        if p["estimate_result"] is not None:
            for k in ("has_accepted_estimate","optimizer_converged","numerical_ill_conditioned",
                      "ambiguity_detected","boundary_active","numeric_contract_violation"):
                _compare(p["estimate_result"][k],q["estimate_result"][k],f"/D{tick}/WLS/{k}")
            if p["estimate_result"]["has_accepted_estimate"]:
                close(p["estimate_result"]["estimate"],q["estimate_result"]["estimate"],"estimate",f"/D{tick}/WLS")
    return errors


def main():
    manifest=read(OUT/"SOURCE_PINS.json")
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest["pins"].items())
    views,summary=[],{}
    for i,name in enumerate(ROOTS,1):
        root=Path("runs")/name
        world,ann=read(root/"WORLD_INPUT.json"),read(root/"PUBLIC_INPUT.json")
        def public_gate(view):
            views.append(view)
            handoff=compare_family([view,read(root/"R_D60.json")["policy_input"]])
            save(f"VALUE{i}_PUBLIC_D60",handoff)
        errors={}
        def record(tick,r):
            save(f"VALUE{i}_D{tick}",r)
            errors[str(tick)]=compare_step(r,read(root/f"R_D{tick}.json"),tick)
            historic=read(root/"R.json")["observations_consumed"]
            _compare(r["consumed"],[v for v in historic if v["consumed_tick"]<=tick],f"/D{tick}/consumed")
        try:
            result=run_reference(world,ann,"C1_REFERENCE_"+str(i),public_gate=public_gate,record=record)
            assert result["label"]["completion_tick"]==(95 if i==2 else None)
            save(f"VALUE{i}_LABEL",result)
        except Exception as exc:
            save("FIRST_DIVERGENCE",dict(reference=i,error=repr(exc)))
            raise
        summary[f"VALUE{i}"]=dict(label=result["label"],prefix_wls=result["prefix_wls"],window_wls=result["window_wls"],
                                 counts=result["counts"],cpu=result["cpu"],wall=result["wall"],errors=errors)
    handoff=compare_family(views)
    save("REFERENCE_COMPARISON",dict(physical_references=2,common_public_sha256=handoff["public_sha256"],results=summary))
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest["pins"].items())


if __name__=="__main__":
    main()
