from pathlib import Path
import sys,json,os,stat,shutil
repo=Path.cwd();sys.path.insert(0,str(repo))
from scripts import run_a2_prediction_sw3_test as t
from scripts import sw3_test_appcontainer as c
from scripts import run_a2_prediction_sw3_dev as d
out=repo/"reports/a2_prediction_sw3_test_007";t.REPORT=out
root=repo/".sw3_r1b_handoff_001";h=d.read(root/"HANDOFF.json")
def check():
 link=root/"input/private_link";file=root/"private/world.json"
 assert link.lstat().st_reparse_tag==stat.IO_REPARSE_TAG_MOUNT_POINT
 assert link.resolve()==root/"private"
 assert (root/h["relative_request"]).samefile(file)
 assert file.stat().st_ino==h["file_id"] and d.sha(file)==h["sha256"]
 return dict(target=str(link.resolve()),tag=link.lstat().st_reparse_tag,file_id=file.stat().st_ino,sha256=d.sha(file))
try:
 d.save(out/"J0_JUNCTION.json",check())
 old=d.read(repo/"reports/a2_prediction_sw3_test_006/DEPENDENCIES.json")
 assert all(d.sha(root/k)==v for k,v in old.items())
 d.save(out/"DEPENDENCIES.json",old)
 view=t.fixture();ref={m:t.predict_method(view,m) for m in d.METHODS}
 for name in ("execution_state","trajectory","future_wls","label","draw_manifest","association"):
  p=root/"private"/(name+".json")
  with p.open("xb") as f:f.write(b'{"artificial":true}\n')
 (root/"sealed_joint_007").mkdir()
 probes={p.stem:[str(p),"rb"] for p in (root/"private").glob("*.json")}
 probes.update(relative=["private/world.json","rb"],sampler=[str(repo/"research/non_oracle/sw3_c1_private_worlds.py"),"rb"],admissibility=[str(repo/"research/non_oracle/sw3_physical_admissibility_v1.py"),"rb"],repository=[str(repo/"docs/A2_PRED_SW3_EVALUATION_SPEC_V1.md"),"rb"])
 with c.profile() as (sid,sid_text):
  d.save(out/"PROFILE_OPEN.json",dict(sid=sid_text,capabilities=[],cwd=str(root)))
  t.acl(root,sid_text,"(RX)")
  for child in root.iterdir():
   if child.name in {"private","input","HANDOFF.json","sealed_joint_007"}:continue
   t.acl(child,sid_text,"(OI)(CI)(M)" if child.name=="output" else ("(OI)(CI)(RX)" if child.is_dir() else "(RX)"))
  t.acl(root/"input",sid_text,"(RX)")
  for child in (root/"input/allowed.json",root/"input/job.json"):t.acl(child,sid_text,"(RX)")
  env=t.minimal_environment(root)|{"LOCALAPPDATA":os.environ["LOCALAPPDATA"]}
  t.probe_run(root,sid,sid_text,"R1_A",{"fixture":view},probes,env)
  seals={}
  for m in d.METHODS:
   p=root/"output"/f"fixture_{m}.json"
   mismatch=t.difference(t.normalize(ref[m]),t.normalize(d.read(p)))
   if mismatch:
    d.save(out/"SCIENCE_DIFFERENCE.json",mismatch);raise RuntimeError("scientific difference")
   seals[p.name]=d.sha(p)
   shutil.copyfile(p,out/p.name)
  d.save(out/"SCIENCE_PASS.json",dict(sid=sid_text,hashes=seals))
  d.save(out/"J3_BEFORE.json",check())
  result=t.probe_run
  # Positive public read is allowed; evaluate both actual results explicitly.
  job=dict(inputs={},probes=dict(positive=["input/allowed.json","rb"],reparse=[h["relative_request"],"rb"]))
  (root/"input/job.json").write_text(json.dumps(job),encoding="utf-8")
  launch=t.launch_record(root,sid,sid_text,"R1_B",env)
  assert launch and launch["exit_code"]==0
  b=d.read(root/"output/receipt.json");d.save(out/"R1_B_ACCESS.json",dict(sid=sid_text,**b))
  assert b["probes"]["positive"]["allowed"]
  r=b["probes"]["reparse"]
  assert not r["allowed"] and r["exception"]=="PermissionError" and r["errno"]==13
  d.save(out/"J3_AFTER.json",check())
  t.probe_run(root,sid,sid_text,"R1_C_POSITIVE",{}, {n:[str(root/"output"/n),"FILE_WRITE_DATA"] for n in seals},env,allow=True)
  objects={}
  for n,sha in seals.items():
   source=root/"output"/n;target=root/"sealed_joint_007"/n
   shutil.copyfile(source,target)
   assert d.sha(source)==d.sha(target)==sha
   objects[n]=dict(source_id=source.stat().st_ino,sealed_id=target.stat().st_ino,sha256=sha)
  d.save(out/"SEAL.json",dict(sid=sid_text,objects=objects))
  t.probe_run(root,sid,sid_text,"R1_C_NEGATIVE",{}, {n:[str(root/"sealed_joint_007"/n),"FILE_WRITE_DATA"] for n in seals},env)
  assert all(d.sha(root/"sealed_joint_007"/n)==sha for n,sha in seals.items())
  d.save(out/"PROFILE_LAST_GATE.json",dict(sid=sid_text,all_gates_passed=True))
 d.save(out/"PROFILE_CLOSED.json",dict(sid=sid_text,profile_context_exited=True))
 d.save(out/"ACCEPTANCE.json",dict(SAME_SESSION_A_B_C="PASS",TEST_0_ISOLATION="PASS",TEST_0_R1_A="PASS",TEST_0_R1_B="PASS",TEST_0_R1_C="PASS",PREDICTION_SEAL="NOT_RUN",ACTUAL_LABELS="NOT_RUN",TEST_EVALUATION="NOT_RUN",formal_worlds=0,formal_predictions=0,actual_labels=0))
except Exception as error:
 d.save(out/"FAILURE.json",dict(error=repr(error)));raise
