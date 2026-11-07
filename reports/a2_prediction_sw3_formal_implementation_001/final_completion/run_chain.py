from pathlib import Path
import sys,json,os
repo=Path.cwd();sys.path.insert(0,str(repo));sys.path.insert(0,str(repo/"tests"))
from test_sw3_formal_completion import make_views
from research.non_oracle.sw3_formal_core import Coordinator,TEST,write,sha
from research.non_oracle.sw3_formal_adapter import ProductionAdapter
from research.non_oracle.sw3_formal_worker import AppContainerWorker
from scripts import run_a2_prediction_sw3_test as t
from scripts import sw3_test_appcontainer as c
out=repo/"reports/a2_prediction_sw3_formal_implementation_001/final_completion"
root=repo/".sw3_fi_os_handoff_001"
views=make_views()
class FakePhysics:
 def global_precheck(self):pass
 def public_prechecks(self):return {n:dict(status="PASS") for n in TEST}
 def prepare(self,identities):
  self.paused=[dict(identity=i,world_number=w,draw=dict(source="MOCK"),env=object(),view=views[i["evaluation_slot"]]["D60"],checkpoint=f"mock{i['evaluation_slot']}/{w}",prefix=[]) for i in identities for w in range(4)]
  return views,self.paused
 def verify_pauses(self,paused):
  assert paused is self.paused and len({id(p["env"]) for p in paused})==32
 def finish(self,paused):
  assert paused is self.paused
  return [dict(identity=p["identity"],world_number=p["world_number"],label=dict(source="MOCK",completed_by_H=p["world_number"]%2==0,completion_tick=100 if p["world_number"]%2==0 else None)) for p in paused]
class ArtificialAdapter(ProductionAdapter):kind="ARTIFICIAL"
pins={p:sha(repo/p) for p in ("research/non_oracle/sw3_f1_prediction.py","research/non_oracle/sw3_public_hypotheses.py","docs/A2_PRED_SW3_C_RESERVE_ADMISSION_CONTRACT_V2.md")}
with c.profile() as (sid,text):
 write(out/"PROFILE.json",dict(sid=text,capabilities=[],cwd=str(root)))
 t.acl(root,text,"(RX)")
 for child in root.iterdir():
  if child.name in {"input","private","sealed","HANDOFF_REQUEST.json","HANDOFF_RECEIPT.json","PREPARATION_SHA256.json"}:continue
  t.acl(child,text,"(OI)(CI)(M)" if child.name=="output" else ("(OI)(CI)(RX)" if child.is_dir() else "(RX)"))
 t.acl(root/"input",text,"(RX)")
 for p in (root/"input/job.json",root/"input/D60.json",root/"input/allowed.json"):t.acl(p,text,"(RX)")
 worker=AppContainerWorker(sid,text,root,out/"os",c.run)
 adapter=ArtificialAdapter({}, {},out/"chain",worker,pins,physics=FakePhysics())
 coord=Coordinator(out/"chain","IMPLEMENTATION_TEST",adapter)
 result=coord.run()
 write(out/"CHAIN_PASS.json",dict(state=coord.state,distinct_public_sha256=[p["public_sha256"] for p in views.values()],sid=text))
