from pathlib import Path
import sys,stat,json,os,shutil,hashlib
repo=Path.cwd()
sys.path.insert(0,str(repo))
from scripts import run_a2_prediction_sw3_test as t
from scripts import sw3_test_appcontainer as c
from scripts import run_a2_prediction_sw3_dev as d
out=repo/"reports/a2_prediction_sw3_test_006"
t.REPORT=out
root=repo/".sw3_r1b_handoff_001"
handoff=d.read(root/"HANDOFF.json")
link=root/"input/private_link"
file=root/"private/world.json"
def check():
 assert root==Path(handoff["worker_cwd"])
 assert link.lstat().st_reparse_tag==stat.IO_REPARSE_TAG_MOUNT_POINT
 assert link.resolve()==root/"private"
 relative=root/handoff["relative_request"]
 assert relative.samefile(file)
 assert file.stat().st_ino==handoff["file_id"]
 assert d.sha(file)==d.sha(relative)==handoff["sha256"]
 return dict(tag=link.lstat().st_reparse_tag,target=str(link.resolve()),file_id=file.stat().st_ino,sha256=d.sha(file),cwd=str(root),relative=handoff["relative_request"])
try:
 d.save(out/"B1.json",check())
 modules=sorted({Path(m.__file__).resolve() for k,m in sys.modules.copy().items()
   if (k.startswith(("research","pursuit_v2")) or k=="scripts.gq_windows.a0_plans")
   and getattr(m,"__file__",None) and Path(m.__file__).resolve().is_relative_to(repo)
   and not k.startswith(("research.non_oracle.sw3_c1_","research.non_oracle.sw3_physical"))
   and k!="research.non_oracle.environment"})
 t.stage(root,modules)
 (root/"output").mkdir()
 (root/"diagnostic_empty_stdin").touch(exist_ok=False)
 public=root/"input/allowed.json"
 public.write_bytes(b'{"artificial_public":true}\n')
 job=root/"input/job.json"
 job.write_text(json.dumps(dict(inputs={},probes=dict(positive=["input/allowed.json","rb"],reparse=["input/private_link/world.json","rb"]))),encoding="utf-8")
 with c.profile() as (sid,sid_text):
  t.acl(root,sid_text,"(RX)")
  for child in root.iterdir():
   if child.name in {"private","input","HANDOFF.json"}:continue
   t.acl(child,sid_text,"(OI)(CI)(M)" if child.name=="output" else ("(OI)(CI)(RX)" if child.is_dir() else "(RX)"))
  # No recursive grant through input/private_link.
  t.acl(root/"input",sid_text,"(RX)")
  for child in (public,job):t.acl(child,sid_text,"(RX)")
  d.save(out/"IDENTITY.json",dict(sid=sid_text,capabilities=[],cwd=str(root),acl_policy="TEST004 RX runtime, M output, no grant private; nonrecursive RX input"))
  env=t.minimal_environment(root)|{"LOCALAPPDATA":os.environ["LOCALAPPDATA"]}
  result=t.launch_record(root,sid,sid_text,"B2",env)
  if result is None or result["exit_code"]!=0:raise RuntimeError("worker failed")
  receipt=d.read(root/"output/receipt.json")
  d.save(out/"B2_RECEIPT.json",receipt)
  d.save(out/"B2_AFTER.json",check())
  p=receipt["probes"]
  if p["reparse"]["allowed"]:raise RuntimeError("FAIL: private reparse access allowed")
  assert p["positive"]["allowed"]
  assert p["reparse"]["exception"]=="PermissionError" and p["reparse"]["errno"]==13
  assert p["reparse"]["path"]=="input/private_link/world.json" and p["reparse"]["mode"]=="rb"
 d.save(out/"RESULT.json",dict(R1_B_STANDALONE="PASS",SAME_SESSION_A_B_C="NOT_VERIFIED",TEST_0_ISOLATION="BLOCKED_PENDING_SAME_SESSION_A_B_C"))
except Exception as error:
 d.save(out/"FAILURE.json",dict(error=repr(error)))
 raise
