from pathlib import Path
import sys,json,os,shutil
repo=Path.cwd();sys.path.insert(0,str(repo))
from scripts import run_a2_prediction_sw3_test as t
from scripts import sw3_test_appcontainer as c
from scripts import run_a2_prediction_sw3_dev as d
from research.non_oracle.sw3_formal_core import Coordinator,TEST,write,verify
from research.non_oracle.sw3_c1_sealing import public_handoff
from research.non_oracle.sw3_formal_evaluation import validate_prediction
out=repo/"reports/a2_prediction_sw3_formal_implementation_001"
work=out/"anchored_chain";t.REPORT=out/"anchored_os_evidence";t.REPORT.mkdir(exist_ok=False)
root=repo/".sw3_fi_os_handoff_001"
view=t.fixture()
reference={m:t.predict_method(view,m) for m in d.METHODS}
class Artificial:
 kind="ARTIFICIAL"
 def __init__(self,sid,text):self.sid,self.text=sid,text;self.env=t.minimal_environment(root)|{"LOCALAPPDATA":os.environ["LOCALAPPDATA"]}
 def trust_identity(self):return dict(writer="trusted-coordinator",sid=self.text)
 def verify_seal_permissions(self,gate,manifest):
  t.probe_run(root,self.sid,self.text,f"ANCHOR_DENIAL_{gate}_{len(manifest)}",{}, {k:[v["path"],"FILE_WRITE_DATA"] for k,v in manifest.items()},self.env)
 def global_precheck(self):
  assert d.sha(repo/"docs/A2_PRED_SW3_C_RESERVE_ADMISSION_CONTRACT_V2.md")=="90291aaf8b0f637e0a2d86168d1f91666c151748cc84e99637f8dc54cd314d7f"
 def public_prechecks(self):return {n:dict(status="PASS") for n in TEST}
 def reserve_precheck(self):raise AssertionError("No reserve should be called")
 def prepare(self,identities):
  self.identities=identities
  self.pauses=[dict(slot=s,world=w,tick=60,prepares=1,identity=object()) for s in range(8) for w in range(4)]
  return {s:public_handoff(view) for s in range(8)},self.pauses
 def verify_pauses(self,pauses):
  assert pauses is self.pauses and all(p["tick"]==60 and p["prepares"]==1 for p in pauses)
 def seal_private_manifest(self,pauses,folder):
  write(folder/"PRIVATE_MANIFEST.json",[dict(slot=p["slot"],world=p["world"],object_id=id(p),tick=p["tick"]) for p in pauses])
 def predict(self,public):
  self.public=public
  job=dict(inputs={f"anchor{s}":v["D60"] for s,v in public.items()},probes=dict(direct=[str(root/"private/world.json"),"rb"],reparse=["input/private_link/world.json","rb"]))
  (root/"input/job.json").write_text(json.dumps(job),encoding="utf-8")
  launch=t.launch_record(root,self.sid,self.text,"PREDICT",self.env)
  assert launch and launch["exit_code"]==0
  receipt=d.read(root/"output/receipt.json")
  write(t.REPORT/"PREDICTION_RECEIPT.json",dict(sid=self.text,**receipt))
  assert all(not r["allowed"] and r["exception"]=="PermissionError" and r["errno"]==13 for r in receipt["probes"].values())
  self.files={f"{s}_{m}":root/"output"/f"anchor{s}_{m}.json" for s in public for m in d.METHODS}
  return self.files
 def verify_predictions(self,public,files):
  assert len(files)==24
  for s in public:
   for m in d.METHODS:
    payload=d.read(files[f"{s}_{m}"])
    assert payload["method"]==m and payload["selection"]["public_sha256"]==public[s]["public_sha256"]
    assert len(payload["selection"]["selected"])==(1 if m=="M0" else 3)
    assert payload["prediction"]["cost"]["wls"]<=41*(1 if m=="M0" else 3)
    validate_prediction(payload["prediction"])
    assert t.difference(t.normalize(reference[m]),t.normalize(payload)) is None
 def verify_write_denial(self,manifest):
  t.probe_run(root,self.sid,self.text,"WRITE_POSITIVE",{}, {k:[str(v),"FILE_WRITE_DATA"] for k,v in self.files.items()},self.env,allow=True)
  t.probe_run(root,self.sid,self.text,"WRITE_NEGATIVE",{}, {k:[v["path"],"FILE_WRITE_DATA"] for k,v in manifest.items()},self.env)
 def finish(self,pauses):
  assert pauses is self.pauses
  files={}
  for p in pauses:
   s,w=p["slot"],p["world"]
   label=dict(completed_by_H=w%2==0,completion_tick=100 if w%2==0 else None,source="MOCK")
   path=work/"mock_raw_labels"/f"{s}_{w}.json";write(path,dict(slot=s,world=w,label=label));files[f"{s}_{w}"]=path
   p["tick"]=100
  return files
 def verify_labels(self,files,identities):
  assert len(files)==32
  for key,path in files.items():
   row=d.read(path);assert key==f'{row["slot"]}_{row["world"]}'
 def associate(self,predictions,labels):
  verify(predictions);verify(labels)
  p={s:{m:d.read(predictions[f"{s}_{m}"]["path"])["prediction"] for m in d.METHODS} for s in range(8)}
  y={s:[d.read(labels[f"{s}_{w}"]["path"])["label"] for w in range(4)] for s in range(8)}
  return p,y
try:
 with c.profile() as (sid,text):
  write(t.REPORT/"PROFILE.json",dict(sid=text,capabilities=[],cwd=str(root)))
  (root/"diagnostic_empty_stdin").touch(exist_ok=False)
  t.acl(root,text,"(RX)")
  for child in root.iterdir():
   if child.name in {"input","private","sealed","HANDOFF_REQUEST.json","HANDOFF_RECEIPT.json","PREPARATION_SHA256.json"}:continue
   t.acl(child,text,"(OI)(CI)(M)" if child.name=="output" else ("(OI)(CI)(RX)" if child.is_dir() else "(RX)"))
  t.acl(root/"input",text,"(RX)")
  for p in (root/"input/job.json",root/"input/D60.json",root/"input/allowed.json"):t.acl(p,text,"(RX)")
  coordinator=Coordinator(work,"IMPLEMENTATION_TEST",Artificial(sid,text))
  result=coordinator.run()
 write(out/"ANCHORED_CHAIN_PASS.json",dict(state=coordinator.state,formal_actual_wls=0,artificial_prediction_wls=sum(d.read(v)["prediction"]["cost"]["wls"] for v in coordinator.adapter.files.values())))
except Exception as error:
 write(out/"ANCHORED_CHAIN_FAILURE.json",dict(error=repr(error)));raise
