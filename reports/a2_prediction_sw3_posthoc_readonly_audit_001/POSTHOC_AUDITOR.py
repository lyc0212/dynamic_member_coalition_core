"""Independent artifact auditor. No shared evaluator formulas."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from POSTHOC_NUMERIC import check_sensitivity, dual_audit, secondary_audit


def read(path):
    return json.loads(Path(path).read_bytes())


def verify_files(folder, count):
    manifest = read(folder/"MANIFEST.json")
    if len(manifest)!=count:
        raise ValueError("Incomplete manifest")
    for entry in manifest.values():
        path=Path(entry["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest()!=entry["sha256"]:
            raise ValueError("Tampered sealed file")
        if path.stat().st_ino!=entry["file_id"]:
            raise ValueError("Replaced sealed object")
    return manifest


def audit(folder, trusted_index=None):
    folder=Path(folder)
    if trusted_index is None:
        raise ValueError("External protected trusted index required")
    index_path=Path(trusted_index["path"])
    if (hashlib.sha256(index_path.read_bytes()).hexdigest()!=trusted_index["sha256"]
            or index_path.stat().st_ino!=trusted_index["file_id"]):
        raise ValueError("Trusted index changed")
    from research.non_oracle.sw3_formal_trust import verify_anchor
    index=read(index_path)
    prior=None
    for gate in (1,2,3):
        anchor=index["anchors"][str(gate)]
        manifest=verify_anchor(anchor)
        receipt=read(anchor["receipt_path"])
        if receipt["gate"]!=gate or receipt["previous_receipt_sha256"]!=prior:
            raise ValueError("Trusted gate linkage mismatch")
        prior=anchor["receipt_sha256"]
        required=folder/("private_sealed" if gate==1 else "predictions" if gate==2 else "labels")/"MANIFEST.json"
        if Path(receipt["manifest_path"]).resolve()!=required.resolve():
            raise ValueError("Wrong trusted manifest")
    p=verify_files(folder/"predictions",24)
    y=verify_files(folder/"labels",32)
    private=verify_files(folder/"private_sealed",32)
    identities={}
    for entry in private.values():
        record=read(entry["path"])
        identity=record["identity"]
        slot=identity["evaluation_slot"]
        fingerprint=record["public"]["public_sha256"]
        value=(identity["actual_family_id"],fingerprint)
        if slot in identities and identities[slot]!=value:
            raise ValueError("Private mapping disagrees within family")
        identities[slot]=value
    if set(identities)!=set(range(8)):
        raise ValueError("Incomplete trusted family map")
    states=[read(path)["after"] for path in sorted((folder/"events").glob("*.json"))]
    if states!=["PRECHECK_VERIFIED","GATE1_VERIFIED","GATE2_VERIFIED","GATE3_VERIFIED","GATE4_VERIFIED"]:
        raise ValueError("Invalid gate order")
    differences=[];coverage={"M1":0,"M2":0}
    for s in range(8):
        losses={}
        for m in ("M0","M1","M2"):
            payload=read(p[f"{s}_{m}"]["path"])
            if (payload["method"]!=m or payload["evaluation_slot"]!=s
                    or payload["actual_family_id"]!=identities[s][0]
                    or payload["selection"]["public_sha256"]!=identities[s][1]):
                raise ValueError("Wrong method")
            pred=payload["prediction"];classes=pred["predicted_completion_status_set"]
            if classes not in ([False],[True],[False,True]):
                raise ValueError("Invalid classes")
            if pred["cost"]["wls"]>41*(1 if m=="M0" else 3):
                raise ValueError("WLS budget")
            total=Fraction(0)
            for w in range(4):
                label=read(y[f"{s}_{w}"]["path"])
                if (label["slot"],label["world"],label["actual_family_id"])!=(s,w,identities[s][0]):
                    raise ValueError("Wrong label identity")
                actual=label["label"]["completed_by_H"]
                total+=Fraction(int(actual not in classes))+Fraction(int(len(classes)==2),4)
                if m in coverage:coverage[m]+=int(actual in classes)
            losses[m]=total/4
        differences.append(losses["M1"]-losses["M2"])
    delta=sum(differences)/8
    wins=sum(d>0 for d in differences)
    result=delta>=Fraction(1,20) and wins>=5 and coverage["M2"]>=coverage["M1"]
    saved=read(folder/"EVALUATION.json")
    if float(delta)!=saved["mean_D"] or wins!=saved["improved_families"] or result!=(saved["result"]=="PREDICTIVE_GAIN_OBSERVED"):
        raise ValueError("Evaluation mismatch")
    secondary={}
    actual=[read(y[f"{s}_{w}"]["path"])["label"] for s in range(8) for w in range(4)]
    for m in ("M0","M1","M2"):
        counts=dict(covered=0,optimistic_n=0,optimistic_hit=0,pessimistic_n=0,pessimistic_hit=0,
                    false_alarm_n=0,false_alarm_hit=0,completed_n=0,empty=0,discrete=0,envelope=0)
        medians=[];nearest=[];widths=[];class_counts=[0,0,0];sens={str(l):Fraction(0) for l in (0.,.1,.25,.5)}
        for s in range(8):
            payload=read(p[f"{s}_{m}"]["path"]);pred=payload["prediction"]
            nominal=read(p[f"{s}_M0"]["path"])["prediction"]["predicted_completion_status_set"]
            classes=pred["predicted_completion_status_set"];ticks=pred["predicted_completion_ticks"]
            class_counts[([False],[True],[False,True]).index(classes)]+=4
            if ticks:widths.extend([ticks[-1]-ticks[0]]*4)
            for w in range(4):
                label=actual[4*s+w];truth=label["completed_by_H"];tick=label["completion_tick"]
                counts["covered"]+=int(truth in classes)
                for l in (0.,.1,.25,.5):
                    sens[str(l)]+=Fraction(int(truth not in classes))+Fraction(str(l))*int(len(classes)==2)
                if nominal==[True] and not truth:
                    counts["optimistic_n"]+=1;counts["optimistic_hit"]+=int(False in classes)
                if nominal==[False] and truth:
                    counts["pessimistic_n"]+=1;counts["pessimistic_hit"]+=int(True in classes)
                if nominal==[True] and truth:
                    counts["false_alarm_n"]+=1;counts["false_alarm_hit"]+=int(False in classes)
                if truth:
                    counts["completed_n"]+=1;counts["empty"]+=int(not ticks)
                    counts["discrete"]+=int(tick in ticks)
                    counts["envelope"]+=int(bool(ticks and ticks[0]<=tick<=ticks[-1]))
                    if ticks:
                        medians.append(abs(ticks[(len(ticks)-1)//2]-tick))
                        nearest.append(min(abs(t-tick) for t in ticks))
        summary=saved["methods"][m]
        if summary["coverage"]["numerator"]!=counts["covered"]:
            raise ValueError("Secondary coverage mismatch")
        for prefix,key in (("optimistic","optimistic_recovery"),("pessimistic","pessimistic_recovery"),("false_alarm","false_alarm")):
            if (summary[key]["numerator"],summary[key]["denominator"])!=(counts[prefix+"_hit"],counts[prefix+"_n"]):
                raise ValueError("Recovery denominator mismatch")
        for k,n in (("empty_time","empty"),("discrete_hit","discrete"),("envelope_hit","envelope")):
            if (summary[k]["numerator"],summary[k]["denominator"])!=(counts[n],counts["completed_n"]):
                raise ValueError("Completed-class denominator mismatch")
        for key,values in (("median_error",medians),("nearest_error",nearest),("width",widths)):
            expected=sum(values)/len(values) if values else None
            if summary["errors"][key]!=dict(n=len(values),mean=expected):
                raise ValueError("Time error mismatch")
        check_sensitivity(m,p,y,saved)
        for classes,count in zip(([False],[True],[False,True]),class_counts):
            if summary["sets"][str(classes)]["numerator"]!=count:
                raise ValueError("Prediction-set distribution mismatch")
        secondary[m]=dict(counts=counts,loss={k:str(v/32) for k,v in sens.items()},class_counts=class_counts)
    common=[]
    for s in range(8):
        ticks={m:read(p[f"{s}_{m}"]["path"])["prediction"]["predicted_completion_ticks"] for m in ("M1","M2")}
        for w in range(4):
            label=actual[4*s+w]
            if label["completed_by_H"] and all(ticks.values()):
                tick=label["completion_tick"]
                common.append({m:dict(median_error=abs(ts[(len(ts)-1)//2]-tick),
                                      nearest_error=min(abs(t-tick) for t in ts))
                               for m,ts in ticks.items()})
    expected_common=dict(n=len(common),excluded=sum(r["completed_by_H"] for r in actual)-len(common),
        means={m:{k:sum(r[m][k] for r in common)/len(common) if common else None
                  for k in ("median_error","nearest_error")} for m in ("M1","M2")})
    if expected_common!=saved["time_common"]:
        raise ValueError("Paired time denominator mismatch")
    dual=dual_audit(p,y,saved)
    secondary_details=secondary_audit(p,y,saved)
    return dict(mean_D=str(delta),improved_families=wins,coverage=coverage,secondary=secondary,verified=True,dual_numeric=dual,secondary_details=secondary_details)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--trusted-index-descriptor",required=True)
    args=parser.parse_args()
    print(json.dumps(audit(args.folder,read(args.trusted_index_descriptor)),indent=2))
