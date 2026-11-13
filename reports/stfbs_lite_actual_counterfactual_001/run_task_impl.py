"""Single formal ACF001 controller; preparation and archival are separate."""
import time
START=globals().get('FORMAL_START',time.monotonic())
import pathlib,sys,json,hashlib,subprocess,ctypes,os,threading,ast,traceback,importlib.metadata
ROOT=pathlib.Path(__file__).resolve().parent;REPO=pathlib.Path(r'D:\1st\dynamic_member_coalition_core');sys.path.insert(0,str(ROOT));sys.path.insert(0,str(REPO))
from research.non_oracle.stfbs_lite_real_d60_supervisor_win import WindowsSupervisor,_process_cpu_ticks
from task_support import prepare,replay_compare
from analysis import analyze
TASK='STFBS_LITE_ACTUAL_COUNTERFACTUAL_001'
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def save(n,x):
 with (ROOT/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
summary_start=None;summary_cpu=None;math_complete=False;aux=0;rows=[];protected={};error=None;admitted=False;active=None;stop=threading.Event();faults=[];precheck_receipt=None;g1_pass=False;g0_cpu=0;g0_wall=0;analysis_result=None;g1_comparison_usage=None
def git(*args):
 global aux
 p=subprocess.Popen(['git','-c','safe.directory='+REPO.as_posix(),*args],cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.PIPE);o,e=p.communicate()
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.c_void_p]*4;k.GetProcessTimes.restype=ctypes.c_int;v=[ctypes.c_uint64() for _ in range(4)]
 need(k.GetProcessTimes(int(p._handle),*[ctypes.byref(a) for a in v]),'AUXILIARY_ACCOUNTING');aux+=v[2].value+v[3].value;need(p.returncode==0,'GIT_READ_FAILED/'+e.decode(errors='replace'));return o.decode().strip()
def bytes_used():return sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
def guard():
 while not stop.wait(.2):
  try:
   reason='TOTAL_WALL_LIMIT' if time.monotonic()-START>5040 else 'TOTAL_STORAGE_LIMIT' if bytes_used()>1073741824 else None
   if reason:
    faults.append(reason)
    if active is not None and active.poll() is None:active.terminate()
    stop.set()
  except BaseException as exc:faults.append('GUARD_ERROR/'+repr(exc));stop.set()
watcher=threading.Thread(target=guard,daemon=True);watcher.start()
def history():
 bad=[p for p,h in protected.items() if not pathlib.Path(p).is_file() or sha(p)!=h];need(not bad,'HISTORY_DRIFT/'+str(bad[:4]));return dict(count=len(protected),mismatches=[])
def frozen():
 f=read(ROOT/'EXECUTION_FREEZE.json')
 for p,h in f['programs'].items():need(sha(ROOT/p)==h,'PROGRAM_DRIFT/'+p)
 for p,h in f['source_sha256'].items():need(sha(REPO/p)==h,'SOURCE_DRIFT/'+p)
 for p,h in f['runtime_sha256'].items():need(sha(p)==h,'RUNTIME_DRIFT/'+p)
try:
 save('RESOURCE_ACCOUNTING_START.json',dict(task_id=TASK,parent_cpu_ticks=_process_cpu_ticks(),wall_start=START,precheck_cpu_seconds=120,precheck_wall_seconds=180,total_wall_seconds=5040))

 need(git('rev-parse','HEAD')=='1ab69f3508b9e79f8945a5c2feb83e57368a2fbc' and git('branch','--show-current')=='main','HEAD_OR_BRANCH')
 need(not git('diff','--name-only'),'TRACKED_WORKTREE_NOT_CLEAN')
 expected={'research/non_oracle/local_dev/journal.py':'585f921c6824ed937c33ff192da9eb5829bc040008baa32e7c988c4a822fdf3b','research/non_oracle/local_dev/resources.py':'e2cf203c1209942545aa9520d46cbd3c6d8c4763b8a9cd51ed42d06a1ebeceea'}
 for p,h in expected.items():need(sha(REPO/p)==h,'SCHEME_C_IDENTITY')
 need(not git('diff','--name-only','98ed1160d9aba266d36cc263d95cfbeecef865e9','HEAD','--','research','pursuit_v2','scripts','configs'),'SCIENTIFIC_CORE_DRIFT_FROM_005')
 need(pathlib.Path(sys.executable).resolve()==pathlib.Path(r'D:\miniconda3\envs\dynamic_member_coalition_core\python.exe').resolve() and os.name=='nt' and ctypes.sizeof(ctypes.c_void_p)==8,'INTERPRETER')
 versions={n:next(d.version for d in importlib.metadata.distributions(path=[str(pathlib.Path(sys.prefix)/'Lib/site-packages')]) if d.metadata['Name'].lower()==n) for n in ['numpy','scipy','psutil']}
 need(sys.version_info[:3]==(3,13,5) and versions==dict(numpy='2.1.3',scipy='1.15.3',psutil='7.2.2'),'RUNTIME_VERSION')
 baseline=read(REPO/'docs/resource_interface_restoration/call_id_repair/BASELINE.json')['sha256']
 protected={p:h for p,h in baseline.items() if pathlib.Path(p) not in {REPO/x for x in expected}}
 protected.update(read(REPO/'docs/resource_interface_restoration/validation_b/run_04a541f43b3941a1a3d59c2057c1c428/PREFLIGHT.json')['protected_sha256'])
 archive=REPO/'reports/stfbs_lite_h2_h3_extension_005'
 for e in read(archive/'archive_evidence_manifest.json')['files']:
  path=archive/e['path'];need(sha(path)==e['sha256'],'005_EVIDENCE_CHANGED');protected[str(path)]=e['sha256']
 for path in list((REPO/'runs/a2_switch_episode_001').glob('*.json'))+list((REPO/'reports/a2_switch_episode_001_guard').glob('*')):
  if path.is_file():protected[str(path)]=sha(path)
 for path in ROOT.parent.glob('stfbs*'):
  if path.is_dir() and path!=ROOT:
   for marker in path.rglob('*consumed*'):
    if marker.is_file():protected[str(marker)]=sha(marker)
 history()
 index=read(ROOT/'BRANCH_EXECUTION_INDEX.json')
 need([b['attempt_id'] for b in index]==['ACF001_SWITCH_001','ACF001_KEEP_001','ACF001_MEMBER_CHANGE_001'],'ATTEMPT_ORDER')
 need(not (ROOT.parent/(TASK+'.consumed.json')).exists(),'TASK_ALREADY_CONSUMED')
 for other in ROOT.parent.glob('stfbs_lite_actual_counterfactual_001_*'):
  if other==ROOT:continue
  need(not any(other.rglob('attempt.consumed')) and not any(other.rglob('parent_start_attempt.lock')),'PRIOR_TASK_STARTED')
 for p in ROOT.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
 runtime=read(ROOT/'RUNTIME_REFERENCE.json')['file_sha256']
 for p,h in runtime.items():need(sha(p)==h,'RUNTIME_DRIFT')
 source={p.relative_to(REPO).as_posix():sha(p) for name in ['research','pursuit_v2','scripts'] for p in (REPO/name).rglob('*.py')}
 for b in index:
  d=pathlib.Path(b['directory']);a=read(d/'authorization.json')
  need(d==ROOT/b['name'] and a['source_sha256']==source and a['runtime_sha256']==runtime,'SOURCE_OR_OUTPUT_BINDING')
  need(a['task_id']==TASK and a['mode']=='LOCAL_DEV_MODEL_ACTUAL_COUNTERFACTUAL_001' and a['attempt_id']==b['attempt_id'] and a['branch_id']==b['branch_id'] and a['run_id']==b['run_id'],'IDENTITY_BINDING')
  need(b['command']==[sys.executable,'-B',str(d/'outer_controller.py')],'COMMAND_BINDING')
  need(set(p.name for p in d.iterdir())=={'common.py','model_driver.py','observed_branch.py','branch_audit.py','endpoint_graph.py','outer_controller.py','authorization.json','execution_freeze.json'},'PRIOR_BRANCH_OUTPUT')
  f=read(d/'execution_freeze.json');need('execution_freeze.json' not in f['files'],'FREEZE_SELF_REFERENCE')
  for p,h in f['files'].items():need(sha(d/p)==h,'BRANCH_FROZEN_PROGRAM')
 g0=prepare()
 admitted=True
 precheck_receipt=dict(status='G0_PASS_NO_SYNTHETIC_RETEST',cpu_ticks=_process_cpu_ticks()+aux,wall_seconds=time.monotonic()-START)
 save('RESEARCH_EXECUTION_ADMISSION.json',dict(ADMISSION_STATUS='PASS',task_id=TASK,version='V1.2',REUSED_VALIDATION_EVIDENCE=str(archive),CURRENT_SOURCE_BASELINE=expected,FROZEN_SCIENTIFIC_INPUTS=g0,NEW_EXECUTION_IDENTITIES=index,DRIVER_AND_BUDGET_BINDING='real Branch / initialized_budget / solver_guard; change_cost=.01',USER_SCOPE_REMOVED=['S2','V3','Journal L2'],reference_mode='MODEL_SWITCH_REPLAY_REQUIRED',resources=precheck_receipt))
 programs={p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*') if p.is_file() and (p.suffix=='.py' or p.name in {'AUTHORIZATION.txt','BRANCH_EXECUTION_INDEX.json','authorization.json','execution_freeze.json','RUNTIME_REFERENCE.json','RESEARCH_EXECUTION_ADMISSION.json','D60_STATE_EQUIVALENCE.json','HISTORICAL_WORLD_BINDING.json','HISTORICAL_ACTUAL_VALUE_LEDGER.json','SWITCH_REFERENCE_ADMISSION.json','PRIOR_STATE_CHECK.json'})}
 save('EXECUTION_FREEZE.json',dict(task_id=TASK,version='V1.2',programs=programs,source_sha256=source,runtime_sha256=runtime,protected_sha256=protected,branches=index,reference_mode='MODEL_SWITCH_REPLAY_REQUIRED',execution_change_cost=.01,scientific_tolerance=1e-8,budgets=dict(policy_wls=744,observation_wls=63,solver_starts=7263,R=2,Assignment=2,physical_steps=60,cpu=1200,inner_wall=1500,outer_wall=1560,storage=268435456,attempts=1,G0_cpu=120,G0_wall=180,G4_cpu=120,G4_wall=180,total_wall=5040,total_storage=1073741824),G4_rules='V1.2 frozen-trajectory original/no-fee exact rankings and analytic sensitivity only; no solver calls',retry=False))
 frozen();g0_cpu=(_process_cpu_ticks()+aux)/1e7;g0_wall=time.monotonic()-START
 need(g0_cpu<=120 and g0_wall<=180,'G0_RESOURCE_LIMIT')
 with (ROOT.parent/(TASK+'.consumed.json')).open('x') as f:json.dump(dict(task_id=TASK,root=str(ROOT),freeze_sha256=sha(ROOT/'EXECUTION_FREEZE.json'),opportunities=6,refund=False),f);f.flush();os.fsync(f.fileno())
 for b in index:
  frozen();history();need(not faults,'GLOBAL_STOP')
  d=pathlib.Path(b['directory']);need(not (d/'attempt.consumed').exists(),'ATTEMPT_ALREADY_CONSUMED')
  print('SCIENCE_START',b['name'],flush=True)
  active=subprocess.Popen(b['command'],cwd=REPO,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
  stdout,stderr=active.communicate(timeout=1565);exitcode=active.returncode;active=None
  out=read(d/'outer_receipt.json') if (d/'outer_receipt.json').exists() else None;inn=read(d/'inner_receipt.json') if (d/'inner_receipt.json').exists() else None
  ok=exitcode==0 and out is not None and inn is not None and (d/'worker_success.json').exists()
  if ok:ok=out['process_tree_exit_confirmed'] and out['status']=='OUTER_CONTROL_COMPLETE' and inn['worker_exit_code']==0 and inn['accounting_status']=='FINAL_VALID' and inn['job_cleanup_status']=='PASS' and inn['process_tree_status']=='PROCESS_TREE_EXIT_CONFIRMED' and not inn['errors']
  if ok:
   raw=read(d/'BRANCH_RAW.json');ok=raw['branch']==b['branch_id'] and raw['world']==b['world'] and len(raw['frames'])==60 and raw['frames'][-1]['tick']==120 and read(d/'BUDGET_FINALIZATION.json')['state']=='FINALIZED_PASS' and all(x['status']=='PASS' for x in read(d/'AUDITS.json').values())
  if ok:
   finalization=read(d/'BUDGET_FINALIZATION.json');ra=finalization.get('resource_audit')
   ok=bool(ra) and ra['disk']==ra['committed']==ra['runtime'] and finalization['state']=='FINALIZED_PASS'
  if ok:frozen()
  report=dict(name=b['name'],run_id=b['run_id'],attempt_id=b['attempt_id'],branch_id=b['branch_id'],valid_cell_candidate=bool(ok),status='VALID_CELL_CANDIDATE' if ok else 'FAILED_OR_INCOMPLETE',returncode=exitcode,stdout=stdout,stderr=stderr,outer=out,inner=inn,counts=read(d/'RESOURCE_COUNTS.json') if (d/'RESOURCE_COUNTS.json').exists() else None,raw_net=read(d/'BRANCH_RAW.json')['net'] if (d/'BRANCH_RAW.json').exists() else None)
  with (d/'FINAL_BRANCH_REPORT.json').open('x') as f:json.dump(report,f,indent=2)
  entries=[dict(path=p.relative_to(d).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in d.rglob('*') if p.is_file()]
  with (d/'evidence_manifest.json').open('x') as f:json.dump(dict(files=entries),f,indent=2)
  for entry in read(d/'evidence_manifest.json')['files']:need(sha(d/entry['path'])==entry['sha256'],'OUTPUT_MANIFEST')
  rows.append(report);print('SCIENCE_FINISH',b['name'],report['status'],flush=True);need(ok,'BRANCH_FAILED/'+b['name'])
  if b['name']=='A_SWITCH_REPLAY':
   cmp_cpu=_process_cpu_ticks()+aux;cmp_wall=time.monotonic()
   replay_compare(d);g1_pass=True
   g1_comparison_usage=dict(cpu_seconds=((_process_cpu_ticks()+aux)-cmp_cpu)/1e7,wall_seconds=time.monotonic()-cmp_wall,charged_to='G0_PUBLIC_REMAINING_BUDGET')
   need(g0_cpu+g1_comparison_usage['cpu_seconds']<=120 and g0_wall+g1_comparison_usage['wall_seconds']<=180,'CALIBRATION_COMPARISON_RESOURCE')
  else:need(g1_pass,'G1_NOT_ACCEPTED')

 summary_start=time.monotonic();summary_cpu=_process_cpu_ticks()+aux
 analysis_result=analyze(ROOT,index);math_complete=analysis_result['complete']
except BaseException as exc:
 error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
 if active is not None and active.poll() is None:
  active.terminate()
  try:active.wait(5)
  except BaseException:pass
finally:
 if summary_start is None:summary_start=time.monotonic();summary_cpu=_process_cpu_ticks()+aux
 final_faults=[]
 try:protection=history()
 except BaseException as exc:protection=dict(status='FAIL',message=str(exc));final_faults.append('FINAL_HISTORY')
 if (ROOT/'EXECUTION_FREEZE.json').exists():
  try:frozen()
  except BaseException as exc:final_faults.append('FINAL_FREEZE/'+repr(exc))
 else:final_faults.append('EXECUTION_FREEZE_ABSENT')
 valid=sum(b['valid_cell_candidate'] for b in rows)
 branch_index=read(ROOT/'BRANCH_EXECUTION_INDEX.json');consumed=sum((pathlib.Path(b['directory'])/'attempt.consumed').exists() for b in branch_index)
 all_exited=all(b['outer'] and b['outer']['process_tree_exit_confirmed'] and b['inner'] and b['inner']['process_tree_status']=='PROCESS_TREE_EXIT_CONFIRMED' for b in rows)
 if active is not None and active.poll() is None:final_faults.append('ACTIVE_OUTER_PROCESS')
 for b in rows:
  if b['valid_cell_candidate']:
   d=ROOT/b['name']
   for e in read(d/'evidence_manifest.json')['files']:
    if sha(d/e['path'])!=e['sha256']:final_faults.append('FINAL_BRANCH_MANIFEST/'+b['name'])
 def summary_usage():
  return dict(cpu_ticks=(_process_cpu_ticks()+aux)-summary_cpu,cpu_seconds=((_process_cpu_ticks()+aux)-summary_cpu)/1e7,wall_seconds=time.monotonic()-summary_start,total_wall_seconds=time.monotonic()-START,storage_bytes=bytes_used())
 def resource_ok():
  u=summary_usage()
  return u['cpu_seconds']<=120 and u['wall_seconds']<=180 and u['total_wall_seconds']<=5040 and u['storage_bytes']<=1073741824
 if not resource_ok():final_faults.append('FINAL_RESOURCE_BUDGET')
 accepted=admitted and valid==3 and g1_pass and error is None and math_complete and not faults and not final_faults and all_exited and resource_ok()
 final=dict(task_id=TASK,continuation='ACTUAL_COUNTERFACTUAL_001_V1_2',status='LOCAL_DEV_ACTUAL_THREE_ACTION_COUNTERFACTUAL_INCOMPLETE',execution_admission='PASS' if admitted else 'NOT_PASSED',valid_new_cells=valid,scientific_attempts_consumed=consumed,branches_not_started=3-consumed,branches=rows,error=error,precheck_receipt=precheck_receipt,parent_cpu_ticks=_process_cpu_ticks(),aux_cpu_ticks=aux,wall_seconds=time.monotonic()-START,faults=faults,final_faults=final_faults,retry=False,h1_reused_cells=0,actual_run=False,h1_rerun=False,analysis=analysis_result,G0_STATUS='PASS' if admitted else 'FAIL',G1_STATUS='PASS_CANDIDATE' if g1_pass else 'NOT_PASSED',G2_STATUS='PASS_CANDIDATE' if any(b['name']=='A_KEEP' and b['valid_cell_candidate'] for b in rows) else 'NOT_COMPLETED',G3_STATUS='PASS_CANDIDATE' if any(b['name']=='A_MEMBER_CHANGE' and b['valid_cell_candidate'] for b in rows) else 'NOT_COMPLETED',G4_STATUS='PASS_CANDIDATE' if math_complete else 'NOT_COMPLETED',G4_CHANGE_COST_ANALYSIS='PASS_CANDIDATE' if math_complete else 'INCOMPLETE',V1_2_DELIVERABLE_COMPLETE=math_complete,SWITCH_REFERENCE_MODE='MODEL_SWITCH_REPLAY_REQUIRED',ORIGINAL_COUNTERFACTUAL_STATUS='PASS_CANDIDATE' if valid==3 and g1_pass else 'INCOMPLETE',VALID_ACTUAL_CELLS=valid if g1_pass else 0,STARTED_ATTEMPTS=consumed,CONSUMED_ATTEMPTS=consumed,calibration_comparison_resource_usage=g1_comparison_usage,production_admission='BLOCKED',science_scope='One historical actual world, fixed D60, three initial actions, same later A2-R; no zero-fee closed-loop',final_summary_resource_usage=summary_usage(),all_started_processes_exit_confirmed=all_exited)
 save('HISTORICAL_PROTECTION_AUDIT.json',protection);save('AGGREGATE_RESOURCE_LEDGER.json',dict(branches=rows,G0=precheck_receipt,G1_comparison=g1_comparison_usage,outer_and_inner_not_additive=True,parent_cpu_ticks=_process_cpu_ticks(),aux_cpu_ticks=aux));save('FINAL_REPORT.json',final)
 (ROOT/'FINAL_REPORT.md').write_text('# ACTUAL_COUNTERFACTUAL_001_V1_2\n\n'+json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8')
 def manifest():
  entries=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in ROOT.rglob('*') if p.is_file() and p.name!='evidence_manifest_final.json']
  (ROOT/'evidence_manifest_final.json').write_text(json.dumps(dict(files=entries,self_excluded=True),indent=2),encoding='utf-8')
  for e in entries:
   if sha(ROOT/e['path'])!=e['sha256']:raise RuntimeError('FINAL_EVIDENCE_MISMATCH/'+e['path'])
 manifest()
 if accepted and resource_ok() and not faults:
  final['status']='LOCAL_DEV_ACTUAL_THREE_ACTION_COUNTERFACTUAL_PASS_CANDIDATE';final['V1_2_DELIVERABLE_COMPLETE']=True
 final['final_summary_resource_usage']=summary_usage()
 (ROOT/'FINAL_REPORT.json').write_text(json.dumps(final,sort_keys=True,indent=2),encoding='utf-8')
 (ROOT/'FINAL_REPORT.md').write_text('# ACTUAL_COUNTERFACTUAL_001_V1_2\n\n'+json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8')
 manifest()
 if not resource_ok() or faults:
  final['status']='LOCAL_DEV_ACTUAL_THREE_ACTION_COUNTERFACTUAL_INCOMPLETE';final['faults']=faults;final['final_faults'].append('POST_SEAL_RESOURCE_CHECK');final['final_summary_resource_usage']=summary_usage()
  (ROOT/'FINAL_REPORT.json').write_text(json.dumps(final,sort_keys=True,indent=2),encoding='utf-8')
  (ROOT/'FINAL_REPORT.md').write_text('# ACTUAL_COUNTERFACTUAL_001_V1_2\n\n'+json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8');manifest()
 stop.set();watcher.join()
 print(str(ROOT),final['status'],repr(error),flush=True)
