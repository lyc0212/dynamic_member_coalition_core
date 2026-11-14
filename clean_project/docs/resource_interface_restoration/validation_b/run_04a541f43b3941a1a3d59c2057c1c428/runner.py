"""Authorized isolated B tests. Stub functions only; stop on first failure."""
import pathlib,json,hashlib,sys,traceback,inspect
OUT=pathlib.Path(__file__).resolve().parent
REPO=OUT.parents[3]
sys.path.insert(0,str(REPO))
from research.non_oracle.local_dev.journal import LocalJournal,NestedJournal,ModelJournal,MODEL_MAP
from research.non_oracle.local_dev.resources import AuditedDurableResourceLedger,RRecorder,AssignmentRecorder,LIMITS
from research.non_oracle.local_dev.diagnostics import persist
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
def require(b,message):
 if not b:raise RuntimeError(message)
def fixture(name):
 d=OUT/name;d.mkdir();j=LocalJournal(d/'journal.jsonl','B_VALIDATION','B_SYNTHETIC_'+name,1048576);n=NestedJournal(j);m=ModelJournal(n);l=AuditedDurableResourceLedger(m,j.records);r=RRecorder(n,j.records);a=AssignmentRecorder(n,j.records)
 return d,j,n,m,l,r,a
graph=[
 dict(parent=None,child='OBSERVATION_WLS',file='research/non_oracle/stfbs_d1a_model.py',line=79,function='Branch.fuse',evidence="budget.estimator('MODEL_OBSERVATION_WLS')",actual_category='ACTUAL_OBSERVATION_WLS',model_category='MODEL_OBSERVATION_WLS'),
 dict(parent=None,child='R',file='research/non_oracle/stfbs_d1a_model.py',line=209,function='Branch.run',evidence='budget.choose(view)',actual_category=None,model_category=None),
 dict(parent='R',child='POLICY_WLS',file='research/non_oracle/policy.py',line=38,function='policy estimator call',evidence='estimate(payload)',actual_category='ACTUAL_POLICY_WLS',model_category='MODEL_POLICY_EVALUATION_WLS'),
 dict(parent='R',child='ASSIGNMENT',file='research/non_oracle/policy.py',line=98,function='decide',evidence='solve(obs,specs,...)',actual_category=None,model_category=None),
 dict(parent='POLICY_WLS or OBSERVATION_WLS',child='SOLVER',file='research/cooperative_sensing/estimator.py',line=71,function='estimate',evidence='least_squares(...)',actual_category='ACTUAL_SOLVER_START',model_category='MODEL_SOLVER_START')]
for row in graph:row['source_line_actual']=(REPO/row['file']).read_text().splitlines()[row['line']-1]
save('CALL_GRAPH_SOURCE_AUDIT.json',dict(status='PASS',basis='Read current source plus wrapper bindings; no science invoked',edges=graph))
results=[]
try:
 # T001: actual ledger/mapping layers, no scientific estimator.
 d,j,n,m,l,r,a=fixture('T001_MAPPING');counter={'observation':0,'solver':0}
 def solver():counter['solver']+=1;return 7
 def observation():counter['observation']+=1;return l.invoke('ACTUAL_SOLVER_START',solver)
 require(l.invoke('ACTUAL_OBSERVATION_WLS',observation)==7,'STUB_RESULT')
 rows=j.records()
 require(counter=={'observation':1,'solver':1},'STUB_COUNT')
 for row in rows:
  e=row['event'];require(e['scientific_execution']=='LOCAL_DEV_MODEL','MODEL_IDENTITY')
  require(set(e['budget_before'])==set(MODEL_MAP.values()) and set(e['budget_after'])==set(MODEL_MAP.values()),'SNAPSHOT_MAPPING')
 require(l.counts==dict(ACTUAL_POLICY_WLS=0,ACTUAL_OBSERVATION_WLS=1,ACTUAL_SOLVER_START=1),'NO_DOUBLE_CHARGE')
 require(n.audit()['status']=='PASS','NORMAL_CLOSURE')
 require(n.local is j and m.nested is n and l.model is m and r.nested is n and a.nested is n,'SINGLE_JOURNAL')
 results.append(dict(test_id='T001_MAPPING',status='PASS',stub_counts=counter,counts=l.counts))
 save('RESOURCE_MAPPING_AUDIT.json',dict(status='PASS',tests=results.copy(),raw='T001_MAPPING/journal.jsonl',test_quota_is_not_scientific_budget=True));j.close()
 # T002 normal complete R -> policy WLS -> solver; R -> independent assignment.
 d,j,n,m,l,r,a=fixture('T002_NESTING');counter={'R':0,'policy':0,'solver':0,'assignment':0};provenance=d/'provenance.json'
 def prep():
  persist(provenance,dict(test_only=True,tick=80));return dict(provenance_id=str(provenance),provenance_sha256=hashlib.sha256(provenance.read_bytes()).hexdigest(),provenance_tick=80)
 def sol():counter['solver']+=1;return 1
 def pol():counter['policy']+=1;return l.invoke('ACTUAL_SOLVER_START',sol)
 def ass():counter['assignment']+=1;return 2
 def real_r():
  counter['R']+=1;l.invoke('ACTUAL_POLICY_WLS',pol);return a.invoke(ass)
 require(r.invoke(real_r,prepare=prep)==2,'R_STUB_RESULT')
 require(n.audit()['status']=='PASS','GLOBAL_NESTING')
 require(r.usage()==r.runtime_counter==1 and a.usage()==a.runtime_counter==1,'INDEPENDENT_AUTHORITATIVE_COUNT')
 results.append(dict(test_id='T002_NESTING',status='PASS',stub_counts=counter,R=r.reconcile(),assignment=a.reconcile(),raw='T002_NESTING/journal.jsonl'))
 save('RUNTIME_COUNTER_RECONCILIATION.json',dict(status='PASS_FOR_EXECUTED_NORMAL_CASE_ONLY',journal_committed_usage=dict(R=1,ASSIGNMENT=1),runtime_counter=dict(R=1,ASSIGNMENT=1),fault_cases='NOT_RUN'));j.close()
 # T003: malformed call_id must be rejected by the actual event/audit path.
 # This is an isolated schema adversarial input, not a scientific attempt.
 d,j,n,m,l,r,a=fixture('T003_CALL_ID_SCHEMA');call=n.allocate('OBSERVATION_WLS','ACTUAL_OBSERVATION_WLS','MODEL_OBSERVATION_WLS');allocated=call['call_id'];call['call_id']=j.attempt_id+':NOT_AN_ORDINAL';accepted=False;error=None
 try:
  m.event(call,'STARTED',dict(l.counts),dict(l.counts));m.event(call,'RETURNED',dict(l.counts),dict(l.counts));actual=n.audit();accepted=actual.get('status')=='PASS'
 except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc))
 rows=j.records();j.close()
 result=dict(test_id='T003_CALL_ID_SCHEMA',status='FAIL' if accepted else 'PASS',input=dict(allocated_id=allocated,injected_id=call['call_id']),expected='REJECT_MALFORMED_CALL_ID',actual='AUDIT_PASS' if accepted else 'REJECTED',production_error=error,raw='T003_CALL_ID_SCHEMA/journal.jsonl',science_stubs_invoked=0)
 results.append(result);save('T003_CALL_ID_SCHEMA/result.json',result)
 require(not accepted,'BLOCKER: audit accepted non-ordinal call_id contrary to ATTEMPT_ID:CALL_ORDINAL contract')
 save('TEST_RESULTS.json',results)
except BaseException as exc:
 save('TEST_RESULTS.json',results);save('STOP.json',dict(status='FAILED',reason=str(exc),type=type(exc).__name__,traceback=traceback.format_exc(),automatic_retry=False,remaining_tests='NOT_RUN',production_code_modified=False));print(str(exc));raise
