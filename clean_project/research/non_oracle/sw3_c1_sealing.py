"""Public handoff, equality checks and content seals. No labels are generated here."""
from copy import deepcopy
import hashlib
import json

from .sw3_public_hypotheses import public_fingerprint, public_input

PRIVATE = {"position_at_birth","position_now","velocity_now","physical_environment_id",
           "work_instance_id","world_id","world_number","seed","label","future_wls","private_path"}


def _reject_private(x, path=""):
    if isinstance(x,dict):
        for k,v in x.items():
            field=f"{path}/{k}"
            if k in PRIVATE:
                raise ValueError(f"Private field at {field}")
            _reject_private(v,field)
    elif isinstance(x,(tuple,list)):
        for i,v in enumerate(x):
            _reject_private(v,f"{path}/{i}")


def public_handoff(view):
    _reject_private(view)
    clean,_,_=public_input(view)
    return dict(D60=clean,public_sha256=public_fingerprint(clean))


def _compare(a,b,path=""):
    if type(a) is type(b) is dict:
        if set(a)==set(b):
            for k in sorted(a,key=str):
                _compare(a[k],b[k],f"{path}/{k}")
            return
    elif type(a) is type(b) is list:
        if len(a)==len(b):
            for i,(x,y) in enumerate(zip(a,b)):
                _compare(x,y,f"{path}/{i}")
            return
    elif type(a) is type(b) and (a==b if type(a) is not float else a.hex()==b.hex() or a==b==0.):
        return
    raise ValueError(f"Public mismatch at {path or '/'}: {a!r} != {b!r}")


def compare_family(views):
    if len(views)<2:
        raise ValueError("At least two public views required")
    # Compare before the second schema pass so mismatched evidence gets a path.
    first = public_handoff(views[0])
    for v in views[1:]:
        other=public_handoff(v)
        _compare(first["D60"],other["D60"])
        if first["public_sha256"]!=other["public_sha256"]:
            raise ValueError("Public fingerprint mismatch after field comparison")
    return first


def _content_sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,
        separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest()


def seal_prediction(view,method,summary,*,sequence):
    if method not in ("M0","M1","M2") or type(sequence) is not int or sequence<0:
        raise ValueError("Invalid public seal metadata")
    if set(summary)!={"predicted_completion_status_set","predicted_completion_ticks",
                      "completion_time_envelope","noncompletion_possible"}:
        raise ValueError("Only the public prediction summary can be sealed here")
    _reject_private(summary)
    body=dict(public_sha256=public_handoff(view)["public_sha256"],method=method,
              summary=deepcopy(summary),sequence=sequence)
    return dict(body=body,seal_sha256=_content_sha(body))


def archive_private(world,label):
    if label.get("source")!="ACTUAL":
        raise ValueError("Private label must be ACTUAL")
    return dict(world_sha256=_content_sha(world),label_sha256=_content_sha(label))


def verify_prediction_seal(view,sealed):
    body=sealed["body"]
    expected=seal_prediction(view,body["method"],body["summary"],sequence=body["sequence"])
    _compare(expected,sealed,"/seal")
    return body["public_sha256"]


def association_receipt(view,sealed,private_archive,*,sequence):
    public_sha = verify_prediction_seal(view,sealed)
    if type(sequence) is not int or sequence<=sealed["body"]["sequence"]:
        raise ValueError("Association must follow prediction seal")
    if set(private_archive)!={"world_sha256","label_sha256"} or any(
        type(v) is not str or len(v)!=64 or any(c not in "0123456789abcdef" for c in v)
        for v in private_archive.values()
    ):
        raise ValueError("Expected private archive digests")
    return dict(public_sha256=public_sha,prediction_seal_sha256=sealed["seal_sha256"],
                private_archive=deepcopy(private_archive),sequence=sequence)
