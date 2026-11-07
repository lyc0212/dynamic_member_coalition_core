import json
import sys
from functools import partial
import subprocess
from pathlib import Path
from scripts import run_a2_prediction_sw3_test as deployment
from scripts import sw3_test_appcontainer as native
from research.non_oracle.sw3_formal_core import Coordinator,sha
from research.non_oracle.sw3_formal_adapter import ProductionAdapter
from research.non_oracle.sw3_formal_worker import AppContainerWorker
from research.non_oracle.sw3_release_scope import _authorized_scope

def run(args):
    root,output=Path(args.workspace).resolve(),Path(args.output).resolve()
    if root.exists() or output.exists():
        raise ValueError("Formal output or workspace exists")
    pins=json.loads(Path(args.pins).read_bytes())
    if not pins or any(sha(p)!=h for p,h in pins.items()):
        raise ValueError("Release pins mismatch")
    with _authorized_scope():
        repo=deployment.REPO
        modules=sorted({Path(m.__file__).resolve() for k,m in sys.modules.copy().items()
            if (k.startswith(("research","pursuit_v2")) or k=="scripts.gq_windows.a0_plans")
            and getattr(m,"__file__",None) and Path(m.__file__).resolve().is_relative_to(repo)
            and not k.startswith(("research.non_oracle.sw3_c1_","research.non_oracle.sw3_physical",
                "research.non_oracle.sw3_formal","research.non_oracle.sw3_release"))
            and k!="research.non_oracle.environment"})
        root.mkdir()
        deployment.stage(root,modules)
        for name in ("input","output","private","sealed"):
            (root/name).mkdir()
        (root/"diagnostic_empty_stdin").touch()
        (root/"input/job.json").write_text('{"inputs":{},"probes":{}}')
        output.parent.mkdir(parents=True,exist_ok=True)
        world=json.loads(Path(args.world).read_bytes())
        ann=json.loads(Path(args.announcements).read_bytes())
        with native.profile() as (sid,text):
            deployment.acl(root,text,"(RX)")
            for child in root.iterdir():
                if child.name in ("private","sealed"):
                    continue
                rights="(OI)(CI)(M)" if child.name=="output" else ("(OI)(CI)(RX)" if child.is_dir() else "(RX)")
                deployment.acl(child,text,rights)
            worker=AppContainerWorker(sid,text,root,output.parent/(output.name+"_worker_receipts"),
                                      partial(native.run,timeout_ms=1800000))
            write_pins={str(p.relative_to(root)):sha(p) for p in root.rglob("*") if p.is_file()}
            from research.non_oracle.sw3_formal_core import write
            write(worker.receipts/"STAGED_RUNTIME_PINS.json",write_pins)
            # Current-run, real restricted read-denial evidence, before any sampling.
            canary=root/"private/access_canary.json"
            write(canary,dict(purpose="formal isolation canary; no scientific data"))
            before=sha(canary)
            receipt=worker.invoke(dict(inputs={},probes={
                "absolute_private":[str(canary),"rb"],
                "relative_private":["private/access_canary.json","rb"]}),"private_denial")
            if not receipt.get("probes") or any(r.get("allowed") or
                    r.get("exception")!="PermissionError" or r.get("errno")!=13
                    for r in receipt["probes"].values()) or sha(canary)!=before:
                raise PermissionError("Current-run private denial failed")
            write(worker.receipts/"PRIVATE_CANARY.json",dict(path=str(canary),sha256=before,sid=text))
            adapter=ProductionAdapter(world,ann,output,worker,pins)
            coordinator=Coordinator(output,"FORMAL_RUN",adapter)
            result=coordinator.run()
            # All evidence below is derived from this run's sealed originals.
            labels=json.loads((output/"labels/MANIFEST.json").read_bytes())
            private=json.loads((output/"private_sealed/MANIFEST.json").read_bytes())
            prefix=sum(sum(c["wls"] for c in json.loads(Path(e["path"]).read_bytes())["prefix_cost"])
                       for e in private.values())
            window=sum(sum(c["wls"] for c in json.loads(Path(e["path"]).read_bytes())["evidence"]["costs"])
                       for e in labels.values())
            descriptor=coordinator.events[-1]["trusted_index"]
            write(output/"TRUSTED_INDEX_DESCRIPTOR.json",descriptor)
            evidence=dict(commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),
                source_pins=pins,worker_receipts=[str(p) for p in sorted(worker.receipts.glob("*_PROCESS.json"))],
                permission_receipts=[str(p) for p in sorted(worker.receipts.glob("*_RECEIPT.json"))
                    if json.loads(p.read_bytes()).get("probes")],
                resource_ledger=dict(T0_PREFIX_ACTUAL=prefix,T1_WINDOW_ACTUAL=window,TOTAL_ACTUAL=prefix+window),
                precheck={str(k):v for k,v in coordinator.events[0]["prechecks"].items()})
            write(output/"RUN_EVIDENCE.json",evidence)
            from scripts.check_sw3_method_validity import method_validity
            write(output/"INDEPENDENT_METHOD_VALIDITY.json",method_validity(
                output,descriptor,mode="FORMAL_RUN",run_evidence=evidence))
            return result
