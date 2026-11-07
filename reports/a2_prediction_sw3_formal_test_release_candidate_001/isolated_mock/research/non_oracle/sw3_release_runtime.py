import json
import sys
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
            worker=AppContainerWorker(sid,text,root,output.parent/(output.name+"_worker_receipts"),native.run)
            adapter=ProductionAdapter(world,ann,output,worker,pins)
            return Coordinator(output,"FORMAL_RUN",adapter).run()
