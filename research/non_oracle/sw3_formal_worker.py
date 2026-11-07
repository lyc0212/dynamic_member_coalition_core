"""Public-only AppContainer transport, shared by artificial and production adapters."""
import json
import os
from pathlib import Path

from .sw3_formal_core import sha, write


class AppContainerWorker:
    def __init__(self, sid, sid_text, workspace, receipts, transport):
        self.sid,self.sid_text=sid,sid_text
        self.workspace,self.receipts=Path(workspace),Path(receipts)
        self.transport=transport
        self.receipts.mkdir(exist_ok=False)
        self.calls=0
        self.exited=False

    def trust_identity(self):
        return dict(writer="trusted-coordinator",sid=self.sid_text)

    def invoke(self, job, name):
        from scripts.run_a2_prediction_sw3_test import minimal_environment
        from scripts.run_a2_prediction_sw3_dev import read
        root=self.workspace
        (root/"input/job.json").write_text(json.dumps(job),encoding="utf-8")
        (root/"output/receipt.json").unlink(missing_ok=True)
        self.exited=False
        env=minimal_environment(root)|{"LOCALAPPDATA":os.environ["LOCALAPPDATA"]}
        self.calls+=1
        result=self.transport(self.sid,root/"python.exe",["-I","-B","-S","-c",
            "import runpy,sys;sys.path.append('Lib/site-packages');runpy.run_path('worker.py',run_name='__main__')"],
            root,env,stdout=self.receipts/f"{self.calls}_{name}_stdout.log",
            stderr=self.receipts/f"{self.calls}_{name}_stderr.log",
            empty_stdin=root/"diagnostic_empty_stdin")
        write(self.receipts/f"{self.calls}_{name}_PROCESS.json",dict(sid=self.sid_text,**result))
        if result["timed_out"] or result["exit_code"]!=0:
            raise ValueError("Restricted worker failed")
        self.exited=True
        receipt=read(root/"output/receipt.json")
        write(self.receipts/f"{self.calls}_{name}_RECEIPT.json",dict(sid=self.sid_text,**receipt))
        return receipt

    def predict(self, public, identities, pins):
        from scripts.run_a2_prediction_sw3_dev import read
        keys={s:f"fi{self.calls+1}slot{s}" for s in public}
        for key in keys.values():
            for m in ("M0","M1","M2"):
                if (self.workspace/"output"/f"{key}_{m}.json").exists():
                    raise ValueError("Stale prediction output")
        self.invoke(dict(inputs={keys[s]:public[s]["D60"] for s in public},probes={}),"prediction")
        files={}
        wrapped=self.receipts/"wrapped_predictions";wrapped.mkdir(exist_ok=False)
        for identity in identities:
            s=identity["evaluation_slot"]
            for m in ("M0","M1","M2"):
                raw=self.workspace/"output"/f"{keys[s]}_{m}.json"
                payload=read(raw)
                payload.update(source_pins=pins,evaluation_slot=s,
                               actual_family_id=identity["actual_family_id"],raw_sha256=sha(raw))
                target=wrapped/f"{s}_{m}.json";write(target,payload)
                files[f"{s}_{m}"]=target
        return files

    def verify_write_denial(self, manifest):
        self.verify_seal_permissions("predictions",manifest)

    def verify_seal_permissions(self, gate, manifest):
        before={key:sha(v["path"]) for key,v in manifest.items()}
        receipt=self.invoke(dict(inputs={},probes={key:[v["path"],"FILE_WRITE_DATA"]
                              for key,v in manifest.items()}),f"deny_{gate}")
        if set(receipt["probes"])!=set(manifest):
            raise ValueError("Missing permission probe")
        for key,r in receipt["probes"].items():
            if (r["allowed"] or r["winerror"]!=5 or r["access_mask"]!=2
                    or r["share_mode"]!=7 or r["disposition"]!=3
                    or sha(manifest[key]["path"])!=before[key]):
                raise PermissionError("Protected seal write was not denied")
