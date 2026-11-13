"""Preparation only: copies static drivers and identities; never imports science."""
import pathlib,json,hashlib,sys,uuid
R=pathlib.Path(__file__).resolve().parent;OLD=R.parent/'stfbs_lite_h2_h3_extension_003_a801a60d3e2142ca94567c0f75929a49';OLD2=R.parent/'stfbs_lite_h2_h3_extension_002_451cdb6e266e426692865771edc6a02f'
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def put(n,text):
 with (R/n).open('x',encoding='utf-8') as f:f.write(text)
put('common.py',r'''import sys,os,json,hashlib,subprocess,time,copy,math
from pathlib import Path
from copy import deepcopy
ROOT=Path(sys.argv[0]).resolve().parent
TASKROOT=ROOT.parent
REPO=Path(r'D:\1st\dynamic_member_coalition_core')
sys.path.insert(0,str(REPO));sys.path.insert(0,str(TASKROOT))
LIMIT=268435456
def require(b,m):
 if not b:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def save(n,x):
 encoded=(json.dumps(x,sort_keys=True,allow_nan=False,indent=2)+'\n').encode()
 require(sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())+len(encoded)<=LIMIT,'BRANCH_STORAGE_LIMIT')
 with (ROOT/n).open('xb') as f:f.write(encoded);f.flush();os.fsync(f.fileno())
def git(*a):return subprocess.check_output(['git','-c','safe.directory='+REPO.as_posix(),*a],cwd=REPO,text=True).strip()
a=read(ROOT/'authorization.json');ATTEMPT=a['attempt_id'];RUN=a['run_id']
def load_state():
 c=read(a['candidate_path'])['candidate'];v=c['a2_policy_view'];s=c['consumer_seed'];v['beliefs']={int(k):b for k,b in v['beliefs'].items()}
 for k in ('internal_states_at_D60','accepted_position_history','accepted_receipts'):s[k]={int(j):b for j,b in s[k].items()}
 return v,s
''')
for name in ['observed_branch.py','branch_audit.py','endpoint_graph.py']:
 put(name,(OLD/name).read_text(encoding='utf-8-sig'))
put('model_driver.py',r'''from common import *
import traceback
from research.non_oracle.stfbs_lite_local_dev import process_identity,verify_local_job_handoff
from research.non_oracle.stfbs_lite_real_d60_supervisor_win import WindowsSupervisor
def verify_frozen():
 f=read(TASKROOT/'EXECUTION_FREEZE.json')
 for p,h in f['programs'].items():require(sha(TASKROOT/p)==h,'PROGRAM_DRIFT/'+p)
 for p,h in f['source_sha256'].items():require(sha(REPO/p)==h,'SOURCE_DRIFT/'+p)
 for p,h in f['runtime_sha256'].items():require(sha(p)==h,'RUNTIME_DRIFT/'+p)
 require(git('rev-parse','HEAD')=='6586ebff0dd6ee09ce969b4611b175d08c0dd97a','HEAD_DRIFT')
 require(Path(sys.executable).resolve()==Path(a['runtime']['python']).resolve(),'INTERPRETER_IDENTITY')
 return a
def provenance(b,tick):
 return dict(tick=tick,branch=b.name,events=getattr(b,'_queue_audit',[]),states=deepcopy(b.consumer.states),accepted_history=deepcopy(b.consumer.history),accepted_receipts=deepcopy(b.consumer.accepted_receipts),pending=deepcopy(b.consumer.pending),historical_source_boundary='SOURCE_UNRESOLVED where original seed cannot identify unique event')
def worker():
 record=verify_frozen();verify_local_job_handoff(dict(attempt_id=ATTEMPT,mode=record['mode']),read(ROOT/'handoff.json'),sha(ROOT/'authorization.json'))
 from research.non_oracle.local_dev.resources import initialized_budget
 from research.non_oracle.stfbs_d1a_model import Branch
 from research.non_oracle.stfbs_d1a_history_audit import register_context,audit_branch_independent
 from research.non_oracle.stfbs_d1a_audit_input import audit_input
 from research.non_oracle.stfbs_d1a_verify import verify
 from research.non_oracle.stfbs_d1a_audit import audit
 from observed_branch import make_branch
 from branch_audit import service_audit
 view,seed=load_state();world=deepcopy(record['world']);world['motion']={int(k):m for k,m in world['motion'].items()};context=register_context(record['branch_id'],{h['target_id']:deepcopy(h) for h in view['histories']})
 branch=None;budget=None
 try:
  with initialized_budget(ROOT/'worker.jsonl',record['task_id'],ATTEMPT,provenance) as budget:
   with budget.solver_guard():
    branch=make_branch(Branch)(view,seed,world,record['branch_id'],budget);budget.branch=branch
    save('BELIEF_PROVENANCE_D60.json',provenance(branch,60))
    result=branch.run(record['initial_actions']);counts=budget.counts
    save('BRANCH_RAW.json',result);save('D120_PENDING_OBSERVATIONS.json',branch.consumer.pending)
    save('TERMINAL_BRANCH_HISTORY.json',dict(branch=branch.name,histories=branch.histories,actions=branch.actions,status=branch.status,consumer_states=branch.consumer.states,accepted_position_history=branch.consumer.history,accepted_receipts=branch.consumer.accepted_receipts,pending=branch.consumer.pending,consumed=branch.consumer.consumed,raw_cache=list(branch.cache.rows.values()),external_context=dict(expected_branch_id=context.expected_branch_id,prefix_json=context.prefix_json)))
    save('TERMINAL_HISTORY_CONTENT_DIGEST.json',dict(file_sha256=sha(ROOT/'TERMINAL_BRANCH_HISTORY.json'),canonical_current_digest=digest(branch.histories),rule='sorted compact JSON binary64',internal_digest_scope='Last policy freeze, retained unmodified'))
    normalized=audit_input(result,view)
    audits=dict(history=audit_branch_independent(branch,context=context),verify=verify(normalized,view,seed,audit_context=context),service=service_audit(normalized,view,branch=branch),physical_economic=audit(normalized,view))
    save('AUDITS.json',audits);save('ENDPOINT_CONNECTION_AUDIT.json',audits['service']);save('RESOURCE_COUNTS.json',counts)
    require(all(x['status']=='PASS' for x in audits.values()),'SCIENTIFIC_AUDIT_FAILED')
    require(branch.tick==120 and len(result['frames'])==60 and counts['R_CALLS']==2 and counts['ASSIGNMENT_EXACT_SOLVER']==2,'INCOMPLETE_BRANCH')
  require(budget.state==budget.nested.state==budget.finalization_report['state']=='FINALIZED_PASS','BUDGET_FINALIZATION_FAILED')
  save('CALL_CLOSURE_AUDIT.json',budget.nested.audit());save('BUDGET_FINALIZATION.json',budget.finalization_report)
  verify_frozen()
  save('worker_success.json',dict(status='VALID_CELL_CANDIDATE',task_id=record['task_id'],run_id=RUN,attempt_id=ATTEMPT,branch_id=branch.name,net=result['net'],counts=counts,real_model=True,raw_sha256=sha(ROOT/'BRANCH_RAW.json')))
 except BaseException as e:
  if branch is not None:save('BRANCH_PARTIAL.json',dict(tick=branch.tick,frames=branch.frames,events=branch.events,feedback=branch.feedback,histories=branch.histories,boundaries=branch.boundaries,decisions=branch.decisions))
  save('worker_failure.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc(),attempt_id=ATTEMPT,resource_counts=dict(budget.ledger.counts) if budget else None,budget_finalization=budget.finalization_report if budget else None,retry=False))
  raise
def parent():
 record=verify_frozen()
 with (ROOT/'attempt.consumed').open('x') as f:json.dump(dict(task_id=record['task_id'],attempt_id=ATTEMPT,refund=False),f);f.flush();os.fsync(f.fileno())
 supervisor=WindowsSupervisor(wall_seconds=1500,total_cpu_seconds=1200,attempt_identity=ATTEMPT);create=supervisor.api.create
 def monitored_create(job,argv,cwd,env,log):
  pi=create(job,argv,cwd,env,log);require(supervisor.api.member(pi.hProcess,job),'WORKER_JOB_MEMBERSHIP')
  save('handoff.json',dict(mode=record['mode'],attempt_id=ATTEMPT,approval_digest=sha(ROOT/'authorization.json'),parent=process_identity(supervisor.api,supervisor.api.k.GetCurrentProcess()),worker=process_identity(supervisor.api,pi.hProcess),parent_verified_target_job=True))
  return pi
 supervisor.api.create=monitored_create
 result=supervisor.run_monitored([sys.executable,'-B',str(ROOT/'model_driver.py'),'--worker'],cwd=REPO,log=ROOT/'worker.log')
 save('inner_receipt.json',result)
 require(result['worker_exit_code']==0 and result['job_cleanup_status']=='PASS' and result['process_tree_status']=='PROCESS_TREE_EXIT_CONFIRMED' and result['accounting_status']=='FINAL_VALID' and not result['errors'],'INNER_WORKER_FAILED')
 require(result['final_cpu_ticks']<=12000000000 and result['wall_elapsed']<=1500 and (ROOT/'worker_success.json').exists(),'BRANCH_RESOURCE_OR_SUCCESS')
 save('parent_success.json',dict(status='PASS_CANDIDATE',attempt_id=ATTEMPT,run_id=RUN))
if __name__=='__main__':
 if sys.argv[1:]==['--worker']:worker()
 elif sys.argv[1:]==['--parent']:parent()
 else:raise RuntimeError('EXPLICIT_SCIENTIFIC_ENTRY_REQUIRED')
''')
# Reuse original creation-time Job outer controller, without changing supervision.
put('outer_controller.py',(OLD/'outer_controller.py').read_text(encoding='utf-8-sig'))
for name in ['PUBLIC_INPUT_FREEZE.json','CANDIDATE_FREEZE.json','WORLD_LIBRARY.json','PROXY_VALUE_TABLE.json','WORLD_SELECTION.json','MODEL_WORLD_MAPPING.json']:
 (R/name).write_bytes((OLD2/name).read_bytes())
runtime=read(OLD/'RUNTIME_FREEZE.json')
(R/'RUNTIME_REFERENCE.json').write_text(json.dumps(runtime,indent=2),encoding='utf-8')
index=[];oldindex=read(OLD/'BRANCH_EXECUTION_INDEX.json')
for old in oldindex:
 name=old['name'];d=R/name;d.mkdir();a=read(pathlib.Path(old['directory'])/'authorization.json');a.update(task_id='STFBS_LITE_LOCAL_DEV_H2_H3_EXTENSION_004',attempt_id='EXT004_'+name+'_001',run_id='EXT004_'+name+'_RUN_001',branch_id='EXT004_'+name+'_BRANCH_001',mode='LOCAL_DEV_MODEL_EXT004',initial_actions=old['initial_actions'])
 (d/'authorization.json').write_text(json.dumps(a,indent=2,sort_keys=True),encoding='utf-8')
 for namefile in ['common.py','model_driver.py','observed_branch.py','branch_audit.py','endpoint_graph.py','outer_controller.py']:(d/namefile).write_bytes((R/namefile).read_bytes())
 (d/'execution_freeze.json').write_text(json.dumps(dict(controller_sha256=sha(d/'outer_controller.py'),files={p.name:sha(p) for p in d.iterdir() if p.is_file()}),indent=2),encoding='utf-8')
 index.append(dict(name=name,attempt_id=a['attempt_id'],run_id=a['run_id'],branch_id=a['branch_id'],directory=str(d),world=a['world'],initial_actions=a['initial_actions'],command=[sys.executable,'-B',str(d/'outer_controller.py')]))
(R/'BRANCH_EXECUTION_INDEX.json').write_text(json.dumps(index,indent=2),encoding='utf-8')
print('SCIENCE_DRIVER_PREPARED',R)
