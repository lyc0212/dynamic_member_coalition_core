"""Single in-process coordinator and trusted immutable-copy manifests."""
from pathlib import Path
import hashlib
import json
import shutil
from time import perf_counter, process_time

from .sw3_formal_evaluation import evaluate

TEST = (3, 10, 5, 1, 8, 2, 0, 9)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def slots(prechecks, reserve_check):
    if set(prechecks) != set(TEST):
        raise ValueError("Invalid TEST precheck identities")
    bad = [n for n in TEST if prechecks[n]["status"] != "PASS"]
    if len(bad) > 1:
        raise ValueError("Multiple family precheck failures")
    if bad:
        evidence = prechecks[bad[0]]
        if (evidence["status"] != "FAMILY_PRECHECK_FAILED" or
                evidence["kind"] not in ("PUBLIC_SCHEMA","MOTION_DOMAIN","FIXED_PHYSICAL_ADMISSION")
                or evidence.get("basis") is None or reserve_check()["status"] != "PASS"):
            raise ValueError("Reserve eligibility not established")
    return [dict(evaluation_slot=i, actual_family_id=7 if n in bad else n,
                 replaces_family_id=n if n in bad else None, split="test")
            for i,n in enumerate(TEST)]


def seal(files, expected, folder):
    if len(files) != len(expected) or set(files) != set(expected):
        raise ValueError("Incomplete or duplicate seal inventory")
    folder = Path(folder)
    folder.mkdir(exist_ok=False)
    manifest = {}
    for key in expected:
        source = Path(files[key])
        target = folder / (key + ".json")
        shutil.copyfile(source, target)
        if sha(source) != sha(target):
            raise ValueError("Copy changed content")
        manifest[key] = dict(path=str(target.resolve()), sha256=sha(target),
                             file_id=target.stat().st_ino)
    write(folder / "MANIFEST.json", manifest)
    return manifest


def verify(manifest):
    for entry in manifest.values():
        path = Path(entry["path"])
        if sha(path) != entry["sha256"] or path.stat().st_ino != entry["file_id"]:
            raise ValueError("Sealed content or object identity changed")


class Coordinator:
    def __init__(self, output, mode, adapter):
        if mode != "IMPLEMENTATION_TEST":
            raise PermissionError("FORMAL_RUN requires a subsequent explicit authorization release")
        if adapter.kind != "ARTIFICIAL":
            raise PermissionError("Implementation mode accepts artificial adapters only")
        self.output, self.adapter = Path(output), adapter
        self.output.mkdir(exist_ok=False)
        self.state, self.events, self.paused = "NEW", [], []
        self.anchors = {}

    def anchor(self, gate, manifest, manifest_path):
        from .sw3_formal_trust import Trust
        if not hasattr(self,"trust"):
            identity=self.adapter.trust_identity()
            self.trust=Trust(self.output.parent/(self.output.name+"_trusted"),
                             self.output.name,identity["writer"],identity["sid"])
        previous=self.anchors[gate-1]["receipt_sha256"] if gate>1 else None
        anchor=self.trust.fix(gate,len(self.events),manifest_path,manifest,previous)
        receipt=Path(anchor["receipt_path"])
        protected=dict(manifest)
        for key,path in (("trusted_receipt",receipt),("global_manifest",Path(manifest_path))):
            protected[key]=dict(path=str(path),sha256=sha(path),file_id=path.stat().st_ino)
        self.adapter.verify_seal_permissions(gate,protected)
        self.trust.verify(gate)
        self.anchors[gate]=anchor
        return anchor

    def advance(self, before, after, **evidence):
        order = ("NEW","PRECHECK_VERIFIED","GATE1_VERIFIED","GATE2_VERIFIED",
                 "GATE3_VERIFIED","GATE4_VERIFIED")
        if self.state != before or before not in order[:-1] or order[order.index(before)+1] != after:
            raise ValueError("Invalid gate transition")
        self.events.append(dict(sequence=len(self.events), before=before, after=after, **evidence))
        write(self.output / "events" / f"{len(self.events):02d}.json", self.events[-1])
        self.state = after

    def run(self):
        cpu, wall = process_time(), perf_counter()
        try:
            a = self.adapter
            a.global_precheck()
            identities = slots(a.public_prechecks(), a.reserve_precheck)
            self.advance("NEW", "PRECHECK_VERIFIED", slots=identities)
            public, private = a.prepare(identities)
            self.paused = private
            if len(private) != 32 or len({id(p) for p in private}) != 32 or set(public) != set(range(8)):
                raise ValueError("Incomplete paused population")
            held = tuple(id(p) for p in private)
            a.verify_pauses(private)
            a.seal_private_manifest(private, self.output)
            raw=self.output/"PRIVATE_MANIFEST.json"
            records=json.loads(raw.read_bytes())
            if not isinstance(records,list) or len(records)!=32:
                raise ValueError("Expected 32 private identity records")
            private_files={}
            for i,record in enumerate(records):
                path=self.output/"private_records"/f"{i}.json"
                write(path,record)
                private_files[str(i)]=path
            private_seal=seal(private_files,list(map(str,range(32))),self.output/"private_sealed")
            anchor=self.anchor(1,private_seal,self.output/"private_sealed/MANIFEST.json")
            self.advance("PRECHECK_VERIFIED", "GATE1_VERIFIED",anchor=anchor)
            predictions = a.predict(public)
            a.verify_predictions(public, predictions)
            expected = [f"{slot}_{m}" for slot in range(8) for m in ("M0","M1","M2")]
            prediction_seal = seal(predictions, expected, self.output / "predictions")
            a.verify_write_denial(prediction_seal)
            verify(prediction_seal)
            anchor=self.anchor(2,prediction_seal,self.output/"predictions/MANIFEST.json")
            self.advance("GATE1_VERIFIED", "GATE2_VERIFIED",anchor=anchor)
            if held != tuple(id(p) for p in self.paused):
                raise ValueError("Paused environments replaced")
            a.verify_pauses(private)
            labels = a.finish(private)
            a.verify_labels(labels, identities)
            label_seal = seal(labels, [f"{s}_{w}" for s in range(8) for w in range(4)],
                              self.output / "labels")
            verify(label_seal)
            anchor=self.anchor(3,label_seal,self.output/"labels/MANIFEST.json")
            self.advance("GATE2_VERIFIED", "GATE3_VERIFIED",anchor=anchor)
            verify(prediction_seal)
            verify(label_seal)
            for gate in (1,2,3):
                self.trust.verify(gate)
            index=self.trust.export()
            a.verify_seal_permissions(3,dict(trusted_index=index))
            p, y = a.associate(prediction_seal, label_seal)
            result = evaluate(p, y)
            write(self.output / "EVALUATION.json", result)
            self.advance("GATE3_VERIFIED", "GATE4_VERIFIED",
                         trusted_index=index,cpu=process_time()-cpu, wall=perf_counter()-wall)
            return result
        except Exception as error:
            if callable(getattr(self.adapter,"failure_evidence",None)):
                write(self.output/"FAILURE_EVIDENCE.json",self.adapter.failure_evidence())
            write(self.output / "FAILURE.json", dict(state=self.state,error=repr(error)))
            self.state = "BLOCKED"
            raise
