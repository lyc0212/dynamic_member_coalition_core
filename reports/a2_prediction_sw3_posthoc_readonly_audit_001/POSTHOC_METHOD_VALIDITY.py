"""Evidence-based validity separate from the evaluator's convenience flag."""
from pathlib import Path
import hashlib
import json

from POSTHOC_AUDITOR import audit
from POSTHOC_NUMERIC import model_wls_audit

EXPECTED_COMMIT="e04cf534d1408b8dcd8034f2ea7039c0b0824bd4"


def read(path):
    return json.loads(Path(path).read_bytes())


def method_validity(folder, trusted_descriptor, *, mode, run_evidence=None):
    folder=Path(folder)
    if mode=="FORMAL_RUN" and (not run_evidence or run_evidence.get("commit")!=EXPECTED_COMMIT):
        raise ValueError("Original execution commit mismatch")
    if mode=="FORMAL_RUN" and len(run_evidence.get("source_pins",{}))!=2259:
        raise ValueError("Original 2259 source pins required")
    statistics=audit(folder,trusted_descriptor)
    labels=read(folder/"labels/MANIFEST.json")
    records=[read(r["path"]) for r in labels.values()]
    if mode=="IMPLEMENTATION_TEST":
        if any(r["label"]["source"]!="MOCK" for r in records):
            raise ValueError("Artificial audit requires explicitly mock labels")
        return dict(artificial_evidence_valid=True,METHOD_VALID=None,
                    formal_status="NOT_RUN",statistics=statistics)
    if mode!="FORMAL_RUN" or not run_evidence:
        raise ValueError("Missing formal execution proof")
    required={"commit","source_pins","worker_receipts","permission_receipts","resource_ledger","precheck"}
    if not required<=set(run_evidence):
        raise ValueError("Incomplete formal execution proof")
    for path,expected in run_evidence["source_pins"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:
            raise ValueError("Execution source changed")
    if not run_evidence["commit"] or len(run_evidence["worker_receipts"])==0:
        raise ValueError("Missing worker execution identity")
    from research.non_oracle.sw3_formal_core import TEST
    checks=run_evidence["precheck"]
    if set(map(int,checks))!=set(TEST):
        raise ValueError("Missing original family prechecks")
    failures=[n for n in TEST if checks[str(n)]["status"]!="PASS"]
    if len(failures)>1:
        raise ValueError("Multiple precheck failures")
    if failures and (checks[str(failures[0])]["status"]!="FAMILY_PRECHECK_FAILED"
                     or not checks[str(failures[0])].get("before_private_sampling")):
        raise ValueError("Invalid reserve eligibility")
    for path in run_evidence["worker_receipts"]:
        receipt=read(path)
        if not receipt.get("created") or receipt.get("exit_code")!=0 or not receipt.get("sid"):
            raise ValueError("Invalid restricted worker execution")
    verify_permission_receipts(run_evidence["permission_receipts"])
    for r in records:
        if r["label"]["source"]!="ACTUAL":
            raise ValueError("Actual execution labels required")
        evidence=r["evidence"]
        if (type(evidence.get("environment_object_id")) is not int
                or evidence["environment_object_id"]<=0
                or not isinstance(evidence.get("D60_checkpoint"),str)
                or not evidence["D60_checkpoint"]):
            raise ValueError("Missing original paused-environment identity")
        from research.non_oracle.sw3_formal_diagnostics import sealed_diagnostics
        if sealed_diagnostics(evidence)!=r["label"]["service_diagnostics"]:
            raise ValueError("Sealed diagnostics disagree with source")
        if (r["slot"],r["world"],r["actual_family_id"])!=(
                evidence["identity"]["evaluation_slot"],evidence["world_number"],
                evidence["identity"]["actual_family_id"]):
            raise ValueError("Cross-world evidence")
    # Resource evidence is mandatory and independently summed from per-world costs.
    private=read(folder/"private_sealed/MANIFEST.json")
    prefix=0
    for entry in private.values():
        row=read(entry["path"])
        calls=sum(c["wls"] for c in row["prefix_cost"])
        if calls>61:raise ValueError("Prefix budget exceeded")
        prefix+=calls
    window=0
    for r in records:
        calls=sum(c["wls"] for c in r["evidence"]["costs"])
        if calls>41:raise ValueError("Actual window budget exceeded")
        window+=calls
    if run_evidence["resource_ledger"]!={"T0_PREFIX_ACTUAL":prefix,"T1_WINDOW_ACTUAL":window,"TOTAL_ACTUAL":prefix+window}:
        raise ValueError("Actual WLS ledger mismatch")
    model=model_wls_audit(folder)
    return dict(METHOD_VALID=True,statistics=statistics,actual_wls=prefix+window,model_wls=model)


def verify_permission_receipts(permission_receipts):
    if not permission_receipts:
        raise ValueError("Missing independent permission evidence")
    for path in permission_receipts:
        receipt=read(path)
        probes=receipt.get("probes",{})
        if not probes:
            raise ValueError("Empty permission evidence")
        for result in probes.values():
            if result.get("allowed"):
                raise ValueError("Unexpected private access")
            if result.get("mode")=="FILE_WRITE_DATA":
                if result.get("winerror")!=5:
                    raise ValueError("Write denial not established")
            elif result.get("exception")!="PermissionError" or result.get("errno")!=13:
                raise ValueError("Read denial not established")
