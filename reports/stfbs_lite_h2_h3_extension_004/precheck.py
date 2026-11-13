import sys,pathlib,types,importlib.util,importlib.abc,json,hashlib,traceback
ROOT=pathlib.Path(__file__).resolve().parent;REPO=pathlib.Path(r'D:\1st\dynamic_member_coalition_core');sys.path.insert(0,str(REPO))
DENIED={'research.cooperative_sensing.estimator','research.non_oracle.policy','research.non_oracle.stfbs_d1a_model','scipy.optimize'}
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  if name in DENIED:raise ImportError('REAL_SCIENCE_BLOCKED/'+name)
sys.meta_path.insert(0,Block())
def mod(name,package=False):
 m=types.ModuleType(name);m.__file__=__file__;m.__spec__=importlib.util.spec_from_loader(name,None,origin=__file__)
 if package:m.__path__=[]
 sys.modules[name]=m;return m
mod('scipy',True);opt=mod('scipy.optimize');sys.modules['scipy'].optimize=opt;mod('research.cooperative_sensing',True)
est=mod('research.cooperative_sensing.estimator');pol=mod('research.non_oracle.policy');model=mod('research.non_oracle.stfbs_d1a_model')
calls=dict(R=0,WLS=0,SOLVER=0,ASSIGNMENT=0)
def solver(*a,**k):calls['SOLVER']+=1;return {'stub':True}
def estimate(*a,**k):calls['WLS']+=1;return est.least_squares(None)
def assignment(*a,**k):calls['ASSIGNMENT']+=1;return {'stub':True}
def decide(*a,**k):calls['R']+=1;pol.estimate(None);pol.solve(None);return {'stub':True}
opt.least_squares=est.least_squares=solver;est.estimate=pol.estimate=model.estimate=estimate;pol.decide=decide;pol.solve=assignment
from research.non_oracle.local_dev import resources as Q,journal as J
from research.non_oracle.stfbs_lite_real_d60_source import ResourceLedger
need=lambda v,m:None if v else (_ for _ in ()).throw(RuntimeError(m))
def save(p,x):
 with pathlib.Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
def rejection(fn,code=None):
 try:fn()
 except BaseException as e:
  if code:need(code in str(e),'WRONG_REJECTION/'+str(e))
  return dict(type=type(e).__name__,message=str(e))
 raise RuntimeError('EXPECTED_REJECTION_ABSENT')
def context(name):
 d=ROOT/'checks'/name;d.mkdir(parents=True);return d,Q.initialized_budget(d/'journal.jsonl','EXT004_PRECHECK','SYNTH_'+name,lambda b,t:dict(stub=True,tick=t))
results={}
try:
 need(Q.AuditedDurableResourceLedger.__bases__==(ResourceLedger,),'REAL_LEDGER_REQUIRED')
 d,c=context('S1')
 with c as b:
  with b.solver_guard():
   b.choose({'tick':80});b.estimator('MODEL_OBSERVATION_WLS')(None)
  count=b.counts
 need(count==dict(MODEL_POLICY_EVALUATION_WLS=1,MODEL_OBSERVATION_WLS=1,MODEL_SOLVER_START=2,R_CALLS=1,ASSIGNMENT_EXACT_SOLVER=1,ACTUAL_WLS=0,ACTUAL_STEP=0),'S1_COUNTS')
 rows=b.local.records();need(len(rows)==len(b.nested._credentials)==12 and sum(r['event']['status']=='STARTED' for r in rows)==6,'S1_EVENTS')
 need(b.state==b.nested.state==b.finalization_report['state']=='FINALIZED_PASS','S1_FINAL')
 need(b.nested.local is b.local and b.model.nested is b.nested and b.r.nested is b.nested and b.assignment.nested is b.nested,'SINGLE_JOURNAL')
 results['S1']=dict(status='PASS',counts=count,stub_counts=dict(calls),call_ids=[r['event']['call_id'] for r in rows],finalization=b.finalization_report)
 save(ROOT/'S1.json',results['S1'])
 d=ROOT/'checks/S2';d.mkdir();j=J.LocalJournal(d/'invalid_entry.jsonl','EXT004_PRECHECK','SYNTH_S2_ENTRY',65536);n=J.NestedJournal(j);h=n.allocate('R');error=rejection(lambda:n.event(dict(h),'STARTED',{},{}),'UNALLOCATED_CALL_HANDLE');need(j.sequence==0 and n.poisoned,'S2_ENTRY');j.close()
 j=J.LocalJournal(d/'direct.jsonl','EXT004_PRECHECK','SYNTH_S2_DIRECT',65536);n=J.NestedJournal(j);j.append(dict(event_kind='RESOURCE_CALL',call_id='ILLEGAL'));j.records();direct=rejection(n.audit,'COMMIT_CREDENTIAL_COUNT');j.close()
 j=J.LocalJournal(d/'swap.jsonl','EXT004_PRECHECK','SYNTH_S2_SWAP',65536);n=J.NestedJournal(j);a=n.allocate('OBSERVATION_WLS','ACTUAL_OBSERVATION_WLS','MODEL_OBSERVATION_WLS');z=n.allocate('OBSERVATION_WLS','ACTUAL_OBSERVATION_WLS','MODEL_OBSERVATION_WLS');append=j.append
 def swap(event):
  event=dict(event);event['call_id']=z['call_id'] if event['call_id']==a['call_id'] else a['call_id'];return append(event)
 j.append=swap
 for h in [a,z]:n.event(h,'STARTED',{},{});n.event(h,'RETURNED',{}, {})
 rows=j.records();need(len(rows)==len(n._credentials)==4 and all(row['sequence']==cred['sequence'] and row['digest']==cred['digest'] for row,cred in zip(rows,n._credentials)),'S2_VALID_CHAIN')
 error_swap=rejection(n.audit,'ALLOCATED_IDENTITY_MISMATCH');j.close()
 results['S2']=dict(status='PASS',entry_rejection=error,direct_rejection=direct,swap_rejection=error_swap,digest_valid=True);save(ROOT/'S2.json',results['S2'])
 phases=[]
 for phase in ['PRE_SEAL','POST_SEAL']:
  d,c=context('S3_'+phase)
  with c as b:
   audit=b.nested.audit;reconcile=b.r.reconcile
   def probe():
    need(b.state==b.nested.state=='FINALIZING' and b.local.writes_frozen,'S3_STATE');before=b.local.path.read_bytes();events=b.local.sequence;creds=len(b.nested._credentials);count=dict(b.ledger.counts)
    errors=[rejection(lambda:b.local.append({'x':1}),'JOURNAL_FINALIZING' if phase=='PRE_SEAL' else 'JOURNAL_SEALED'),rejection(lambda:b.nested.event({},'STARTED',{},{})),rejection(lambda:b.model.event({},'STARTED',{},{})),rejection(lambda:b.ledger.invoke('ACTUAL_OBSERVATION_WLS',lambda:None)),rejection(lambda:b.r.invoke(lambda:None)),rejection(lambda:b.assignment.invoke(lambda:None))]
    b.local.records();audit()
    need(before==b.local.path.read_bytes() and events==b.local.sequence and creds==len(b.nested._credentials) and count==b.ledger.counts and not b.local.invalid,'S3_NO_WRITES')
    phases.append(dict(phase=phase,errors=errors,invalid=b.local.invalid,sealed=b.local.sealed))
   if phase=='PRE_SEAL':
    def observed_reconcile():probe();return reconcile()
    b.r.reconcile=observed_reconcile
   else:
    def observed_audit():probe();return audit()
    b.nested.audit=observed_audit
  need(b.state=='FINALIZED_PASS','S3_FINAL')
 results['S3']=dict(status='PASS',observations=phases);save(ROOT/'S3.json',results['S3'])
 save(ROOT/'PRECHECK_RESULT.json',dict(status='PASS',checks=results,real_science_calls=0,stub_process=True))
except BaseException as e:
 save(ROOT/'PRECHECK_RESULT.json',dict(status='FAIL',checks=results,error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()),real_science_calls=0))
 raise
