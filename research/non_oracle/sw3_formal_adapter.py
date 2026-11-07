"""Production composition and shared artifact validation for SW3."""
from copy import deepcopy
import json
from pathlib import Path

from .sw3_c1_sealing import public_handoff
from .sw3_formal_core import TEST, sha, write, verify
from .sw3_formal_evaluation import validate_prediction
from .sw3_formal_physics import ProductionPhysics

METHODS = ("M0","M1","M2")


def read(path):
    return json.loads(Path(path).read_bytes())


def check_predictions(public, files, identities, pins, exited):
    expected={f"{s}_{m}" for s in range(8) for m in METHODS}
    if set(files)!=expected or len(files)!=24 or exited is not True:
        raise ValueError("Incomplete predictions or worker still running")
    for identity in identities:
        s=identity["evaluation_slot"]
        view=public_handoff(public[s]["D60"])
        if view["public_sha256"]!=public[s]["public_sha256"]:
            raise ValueError("Invalid public fingerprint")
        announcement=view["D60"]["targets"][1]
        if announcement["coarse_position"]!=identity["center"]:
            raise ValueError("Family announcement mismatch")
        for m in METHODS:
            payload=read(files[f"{s}_{m}"])
            if (payload["method"]!=m or payload["source_pins"]!=pins
                    or payload["evaluation_slot"]!=s or payload["actual_family_id"]!=identity["actual_family_id"]
                    or payload["selection"]["public_sha256"]!=view["public_sha256"]):
                raise ValueError("Prediction identity or source mismatch")
            selection,p=payload["selection"],payload["prediction"]
            k=1 if m=="M0" else 3
            if (len(selection["selected"])!=k or len(p["results"])!=k
                    or selection["screening_wls"]!=0
                    or selection["geometry_endpoints"]>(1230 if m=="M2" else 0)):
                raise ValueError("Hypothesis or screening budget")
            validate_prediction(p)
            outcomes=[r["Y_H"] for r in p["results"]]
            classes=sorted({r["completed_by_H"] for r in outcomes})
            ticks=sorted({r["completion_tick"] for r in outcomes if r["completed_by_H"]})
            if classes!=p["predicted_completion_status_set"] or ticks!=p["predicted_completion_ticks"]:
                raise ValueError("Hypothesis outcomes do not match aggregation")
            calls=0
            for h,r in zip(selection["selected"],p["results"],strict=True):
                if (r["hypothesis"]!=h["label"] or r["public_sha256"]!=view["public_sha256"]
                        or r["offline_diagnostic"] or r["provenance"]!="SIMULATED"
                        or type(r["cost"]["wls"]) is not int or not 0<=r["cost"]["wls"]<=41):
                    raise ValueError("Invalid hypothesis result")
                calls+=r["cost"]["wls"]
            if p["cost"]["wls"]!=calls or calls>41*k:
                raise ValueError("WLS accounting mismatch")


class ProductionAdapter:
    """All Coordinator interfaces are bound; physics is closed by its own release guard."""
    kind="PRODUCTION"

    def __init__(self, world, announcements, output, worker, pins, physics=None):
        self.physics=physics or ProductionPhysics(world,announcements)
        self.output=Path(output)
        self.worker=worker
        self.pins=dict(pins)
        self.identities=[]

    def global_precheck(self):
        if not self.pins or any(sha(p)!=h for p,h in self.pins.items()):
            raise ValueError("Frozen source pin mismatch")
        self.physics.global_precheck()

    def failure_evidence(self):
        return dict(admission_records=getattr(self.physics,"admission_records",[]))

    def public_prechecks(self):
        return self.physics.public_prechecks()

    def reserve_precheck(self):
        from .sw3_c1_manifest import announcements_for
        declaration=announcements_for(self.physics.announcements,7)
        return dict(status="PASS",announcement=declaration,basis="Frozen announcement contract")

    def prepare(self, identities):
        from .sw3_c1_manifest import CENTERS
        self.identities=[dict(r,center=list(CENTERS[r["actual_family_id"]])) for r in identities]
        public,private=self.physics.prepare(identities)
        self.public=public
        return public,private

    def verify_pauses(self, private):
        self.physics.verify_pauses(private)

    def seal_private_manifest(self, private, output):
        records=[]
        for item in private:
            records.append(dict(identity=item["identity"],world=item["world_number"],
                draw=item["draw"],environment_object=id(item["env"]),
                checkpoint=item["checkpoint"],public=public_handoff(item["view"]),
                prefix_cost=[cost for _,cost in item["prefix"]]))
        write(Path(output)/"PRIVATE_MANIFEST.json",records)

    def predict(self, public):
        files=self.worker.predict(deepcopy(public),deepcopy(self.identities),dict(self.pins))
        return files

    def verify_predictions(self, public, files):
        check_predictions(public,files,self.identities,self.pins,self.worker.exited)

    def trust_identity(self):
        return self.worker.trust_identity()

    def verify_write_denial(self, manifest):
        self.worker.verify_write_denial(manifest)

    def verify_seal_permissions(self, gate, manifest):
        self.worker.verify_seal_permissions(gate,manifest)

    def finish(self, private):
        rows=self.physics.finish(private)
        files={}
        for r in rows:
            s,w=r["identity"]["evaluation_slot"],r["world_number"]
            path=self.output/"raw_labels"/f"{s}_{w}.json"
            write(path,dict(slot=s,world=w,actual_family_id=r["identity"]["actual_family_id"],
                            label=r["label"],evidence=r))
            files[f"{s}_{w}"]=path
        return files

    def verify_labels(self, files, identities):
        if set(files)!={f"{s}_{w}" for s in range(8) for w in range(4)}:
            raise ValueError("Incomplete label identities")
        for identity in identities:
            s=identity["evaluation_slot"]
            for w in range(4):
                r=read(files[f"{s}_{w}"])
                if (r["slot"],r["world"],r["actual_family_id"])!=(s,w,identity["actual_family_id"]):
                    raise ValueError("Label family mismatch")
                expected_source="MOCK" if self.kind=="ARTIFICIAL" else "ACTUAL"
                if r["label"]["source"]!=expected_source:
                    raise ValueError("Production label is not ACTUAL")

    def associate(self, predictions, labels):
        verify(predictions);verify(labels)
        p,y={},{}
        for s in range(8):
            p[s]={}
            for m in METHODS:
                payload=read(predictions[f"{s}_{m}"]["path"])
                result=payload["prediction"]
                result["implementation_cost"]=dict(K=len(payload["selection"]["selected"]),
                    high_fidelity_calls=len(result["results"]),
                    geometry_endpoints=payload["selection"]["geometry_endpoints"],
                    screening_wls=payload["selection"]["screening_wls"],
                    end_to_end=payload["end_to_end"])
                p[s][m]=result
            y[s]=[]
            for w in range(4):
                row=read(labels[f"{s}_{w}"]["path"])
                label=row["label"]
                evidence=row["evidence"]
                if "first" in evidence and "second" in evidence:
                    from scripts.run_a2_prediction_sw3_dev import diagnose
                    label["service_diagnostics"]=diagnose(evidence["first"],evidence["second"],
                        evidence["consumed"],{}, {})
                else:
                    label["service_diagnostics"]=None
                y[s].append(label)
        return p,y
