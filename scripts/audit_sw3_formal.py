"""Independent artifact auditor. No shared evaluator formulas."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


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
    states=[read(path)["after"] for path in sorted((folder/"events").glob("*.json"))]
    if states!=["PRECHECK_VERIFIED","GATE1_VERIFIED","GATE2_VERIFIED","GATE3_VERIFIED","GATE4_VERIFIED"]:
        raise ValueError("Invalid gate order")
    differences=[];coverage={"M1":0,"M2":0}
    for s in range(8):
        losses={}
        for m in ("M0","M1","M2"):
            payload=read(p[f"{s}_{m}"]["path"])
            if payload["method"]!=m:
                raise ValueError("Wrong method")
            pred=payload["prediction"];classes=pred["predicted_completion_status_set"]
            if classes not in ([False],[True],[False,True]):
                raise ValueError("Invalid classes")
            if pred["cost"]["wls"]>41*(1 if m=="M0" else 3):
                raise ValueError("WLS budget")
            total=Fraction(0)
            for w in range(4):
                label=read(y[f"{s}_{w}"]["path"])
                if (label["slot"],label["world"])!=(s,w):
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
    return dict(mean_D=str(delta),improved_families=wins,coverage=coverage,verified=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--trusted-index-descriptor",required=True)
    args=parser.parse_args()
    print(json.dumps(audit(args.folder,read(args.trusted_index_descriptor)),indent=2))
