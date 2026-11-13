from copy import deepcopy
import os
from research.non_oracle.local_dev.journal import LocalJournal
from research.non_oracle.stfbs_lite_real_d60_source import DurableResourceLedger
LIMITS={'ACTUAL_POLICY_WLS':2574,'ACTUAL_OBSERVATION_WLS':126,'ACTUAL_SOLVER_START':24300}
MAP={'ACTUAL_POLICY_WLS':'POLICY_WLS','ACTUAL_OBSERVATION_WLS':'OBSERVATION_WLS','ACTUAL_SOLVER_START':'SOLVER'}
ALLOW={None:{'R','STEP'},'R':{'POLICY_WLS','ASSIGNMENT'},'STEP':{'OBSERVATION_WLS'},'POLICY_WLS':{'SOLVER'},'OBSERVATION_WLS':{'SOLVER'},'SOLVER':set(),'ASSIGNMENT':set()}
class ResourceStop(BaseException):pass
def need(x,m):
 if not x:raise RuntimeError(m)
class ActualJournal:
 def __init__(self,path,task,attempt,storage):
  self.local=LocalJournal(path,task,attempt,storage);self.stack=[];self.parent={};self.types={};self.ordinal=0;self.halted=False;self.runtime={'R':0,'ASSIGNMENT':0};self.ledger=DurableResourceLedger(LIMITS,self)
  self.steps=0;self.physical=0;self.boundaries=0;self.returned_frames=0
 @property
 def sequence(self):return self.local.sequence
 def check(self):
  if self.halted:raise ResourceStop('ACTUAL_RESOURCE_FAIL_STOP')
  try:
   self.local.check();used=self.local.committed_counts()
   need(all(used[MAP[k]]==v for k,v in self.ledger.counts.items()),'WLS_COMMITTED_RUNTIME')
   need(all(used[k]==v for k,v in self.runtime.items()),'INDEPENDENT_COMMITTED_RUNTIME')
  except BaseException as exc:self.halted=True;raise ResourceStop(str(exc)) from exc
 def append(self,event):
  event=deepcopy(event)
  try:
   if event.get('kind')=='WLS':
    event.update(event_kind='RESOURCE_CALL',call_type=MAP[event['category']],scientific_execution='LOCAL_DEV_ACTUAL')
   if event.get('event_kind')=='RESOURCE_CALL':
    cid=event['call_id'];typ=event['call_type'];status=event['status']
    if status in ('STARTED','REJECTED'):
     need(cid not in self.parent,'DUPLICATE_CALL_ID')
     parent=self.stack[-1] if self.stack else None
     need(typ in ALLOW.get(self.types.get(parent),set()),'ACTUAL_CALL_GRAPH')
     self.parent[cid]=parent;self.types[cid]=typ
    event['parent_call_id']=self.parent[cid]
    if status in ('RETURNED','FAILED'):need(self.stack and self.stack[-1]==cid,'ACTUAL_CALL_LIFO')
   row=self.local.append(event)
   if event.get('event_kind')=='RESOURCE_CALL':
    if event['status']=='STARTED':self.stack.append(event['call_id'])
    elif event['status'] in ('RETURNED','FAILED'):self.stack.pop()
    if event['status'] in ('FAILED','REJECTED'):self.halted=True
   return row
  except BaseException as exc:self.halted=True;raise ResourceStop('ACTUAL_JOURNAL/'+str(exc)) from exc
 def independent(self,kind,fn,*args,**kwargs):
  self.check();need(kind in self.runtime and self.runtime[kind]<6,'INDEPENDENT_QUOTA')
  self.ordinal+=1;cid=self.local.attempt_id+':'+kind+':'+str(self.ordinal);before=dict(self.runtime);self.runtime[kind]+=1
  self.append(dict(kind=kind,event_kind='RESOURCE_CALL',call_type=kind,status='STARTED',call_id=cid,budget_before=before,budget_after=dict(self.runtime),scientific_execution='LOCAL_DEV_ACTUAL'))
  try:
   result=fn(*args,**kwargs);self.check()
  except BaseException as exc:
   self.halted=True
   if not self.local.invalid:self.append(dict(kind=kind,event_kind='RESOURCE_CALL',call_type=kind,status='FAILED',call_id=cid,budget_before=before,budget_after=dict(self.runtime),scientific_execution='LOCAL_DEV_ACTUAL',exception_type=type(exc).__name__,exception_message=str(exc)))
   raise
  self.append(dict(kind=kind,event_kind='RESOURCE_CALL',call_type=kind,status='RETURNED',call_id=cid,budget_before=before,budget_after=dict(self.runtime),scientific_execution='LOCAL_DEV_ACTUAL'))
  return result
 def start_step(self,tick,request,checkpoint):
  self.check();need(not self.stack,'STEP_WHILE_RESOURCE_ACTIVE')
  self.step_id=request;self.parent[request]=None;self.types[request]='STEP';self.stack.append(request)
  self.append(dict(kind='STEP_REQUEST',tick=tick,request_id=request,checkpoint_id=checkpoint))
 def complete_step(self,result):
  self.append(dict(kind='STEP_RESULT',result=result))
  self.append(dict(kind='STEP_COMPLETE',start_tick=result['start_tick'],end_tick=result['end_tick'],checkpoint_id=result['checkpoint_after']['checkpoint_id'],request_id=self.step_id))
  need(self.stack==[self.step_id],'UNCLOSED_STEP_RESOURCES');self.stack.pop()
  self.steps+=1;self.physical+=20;self.boundaries+=1;self.returned_frames+=21
 def finalize(self):
  self.local.freeze_writes();rows=self.local.records();active=[];seen={};counts=dict.fromkeys(self.local.committed_counts(),0);steps=[];pending=None
  for row in rows:
   e=row['event']
   if e.get('kind')=='STEP_REQUEST':
    need(not active and pending is None,'STEP_NESTING');pending=e['request_id'];active.append(pending);seen[pending]='STEP'
   elif e.get('kind')=='STEP_COMPLETE':
    need(active==[pending] and e['request_id']==pending,'STEP_UNCLOSED');active.pop();steps.append(e['end_tick']);pending=None
   elif e.get('event_kind')=='RESOURCE_CALL':
    cid=e['call_id'];typ=e['call_type'];status=e['status']
    if status=='STARTED':
     need(cid not in seen,'DUPLICATE_DISK_CALL');parent=active[-1] if active else None;need(e['parent_call_id']==parent and typ in ALLOW.get(seen.get(parent),set()),'DISK_CALL_GRAPH')
     seen[cid]=typ;active.append(cid);counts[typ]+=1
     if e['kind']=='WLS':
      cat=e['category'];need(MAP[cat]==typ and e['budget_after'][cat]==e['budget_before'][cat]+1,'IRREVERSIBLE_CHARGE')
    else:
     need(status=='RETURNED' and active and active[-1]==cid,'FAILED_OR_UNCLOSED_DISK_CALL');active.pop()
  need(not active and pending is None and not self.halted,'UNCLOSED_OR_HALTED')
  runtime={MAP[k]:v for k,v in self.ledger.counts.items()};runtime.update(self.runtime)
  committed=self.local.committed_counts();need(counts==committed==runtime,'FINAL_THREE_WAY_COUNTS')
  need(self.steps==self.boundaries==6 and self.physical==120 and self.returned_frames==126 and steps==[20,40,60,80,100,120],'PHYSICAL_COVERAGE')
  need(self.runtime=={'R':6,'ASSIGNMENT':6},'INDEPENDENT_COVERAGE')
  self.local.seal();self.local.close()
  return dict(state='FINALIZED_PASS',disk=counts,committed=committed,runtime=runtime,calls=len(seen)-6,unclosed=[],STEP=6,physical_steps=120,decision_frames=6,total_frames=126)
