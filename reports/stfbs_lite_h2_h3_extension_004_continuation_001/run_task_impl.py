"""Single formal EXT004 controller; preparation and archival are separate."""
import time
START=globals().get('FORMAL_START',time.monotonic())
import pathlib,sys,json,hashlib,subprocess,ctypes,os,threading,ast,traceback,importlib.metadata
ROOT=pathlib.Path(__file__).resolve().parent;REPO=pathlib.Path(r'D:\1st\dynamic_member_coalition_core');sys.path.insert(0,str(ROOT));sys.path.insert(0,str(REPO))
from research.non_oracle.stfbs_lite_real_d60_supervisor_win import WindowsSupervisor,_process_cpu_ticks
from aggregate import aggregate
TASK='STFBS_LITE_LOCAL_DEV_H2_H3_EXTENSION_004'
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def save(n,x):
 with (ROOT/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
summary_start=None;summary_cpu=None;math_complete=False;aux=0;rows=[];protected={};error=None;admitted=False;active=None;stop=threading.Event();faults=[];precheck_receipt=None
def git(*args):
 global aux
 p=subprocess.Popen(['git','-c','safe.directory='+REPO.as_posix(),*args],cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.PIPE);o,e=p.communicate()
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.c_void_p]*4;k.GetProcessTimes.restype=ctypes.c_int;v=[ctypes.c_uint64() for _ in range(4)]
 need(k.GetProcessTimes(int(p._handle),*[ctypes.byref(a) for a in v]),'AUXILIARY_ACCOUNTING');aux+=v[2].value+v[3].value;need(p.returncode==0,'GIT_READ_FAILED/'+e.decode(errors='replace'));return o.decode().strip()
def bytes_used():return sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
def guard():
 while not stop.wait(.2):
  try:
   reason='TOTAL_WALL_LIMIT' if time.monotonic()-START>9720 else 'TOTAL_STORAGE_LIMIT' if bytes_used()>1879048192 else None
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
 save('RESOURCE_ACCOUNTING_START.json',dict(task_id=TASK,parent_cpu_ticks=_process_cpu_ticks(),wall_start=START,precheck_cpu_seconds=120,precheck_wall_seconds=180,total_wall_seconds=9720))
 need(git('rev-parse','HEAD')=='9b476fde2735a4c134b3e3cbe891c387fa71f2a9' and git('branch','--show-current')=='main','HEAD_OR_BRANCH')
 expected={'research/non_oracle/local_dev/journal.py':'fa544175e72520b8d3a2843637cd30e77eb5f09b7d079270a3eaa00ff4c83041','research/non_oracle/local_dev/resources.py':'594a0db780a9e3ed296fc8cb755c5957eff926cad6991cb7adfff5105a85a9eb'}
 for p,h in expected.items():need(sha(REPO/p)==h,'E0_IDENTITY/'+p)
 tracked=git('diff','--name-only').splitlines();need(set(tracked)<=set(expected),'UNEXPECTED_TRACKED_CHANGES')
 core_delta=git('diff','--name-only','6586ebff0dd6ee09ce969b4611b175d08c0dd97a','HEAD','--','research','pursuit_v2','scripts','configs').splitlines();need(set(core_delta)<=set(expected),'UNEXPECTED_CORE_BASELINE_DELTA')
 versions={n:next(d.version for d in importlib.metadata.distributions(path=[str(pathlib.Path(sys.prefix)/'Lib/site-packages')]) if d.metadata['Name'].lower()==n) for n in ['numpy','scipy','psutil']}
 need(sys.version_info[:3]==(3,13,5) and versions==dict(numpy='2.1.3',scipy='1.15.3',psutil='7.2.2'),'RUNTIME_VERSION')
 baseline=read(REPO/'docs/resource_interface_restoration/call_id_repair/BASELINE.json')['sha256'];protected={p:h for p,h in baseline.items() if pathlib.Path(p) not in {REPO/x for x in expected}}
 hist380=read(REPO/'docs/resource_interface_restoration/validation_b/run_04a541f43b3941a1a3d59c2057c1c428/PREFLIGHT.json')['protected_sha256'];protected.update(hist380);history()
 names={'PUBLIC_INPUT_FREEZE.json':'d207e40bc0474fdf4c37b50b4335a09b3d61ba33d19ebaec1c61b11bffadeb01','CANDIDATE_FREEZE.json':'90204472809f81f8e53255458999afc067743734edec88883655bbf56ab58de0','WORLD_LIBRARY.json':'3ae9ac133c37062c20f6d34bb9284a196c3856272b08e0aa9889148df747ded9','PROXY_VALUE_TABLE.json':'96391d141e81268f883f1d391b6139481af8ca0e1050e0186af97c7701dbdb3a','WORLD_SELECTION.json':'8e2da1a1808916e04bb8b630ff03879cd8b51d78bba30b9331e972479d794398','MODEL_WORLD_MAPPING.json':'0918d3c7657127a552b263cbd3babca168a8c3cb789272cb1bbad878a2ecf5fa'}
 for p,h in names.items():need(sha(ROOT/p)==h,'SCIENCE_INPUT_IDENTITY/'+p)
 run=next(ROOT.parent.glob('stfbs_local_dev_actual_d60_002*'));c=read(run/'D60_MODEL_CANDIDATE.json')['candidate']
 need(digest(c['consumer_seed'])=='cf5ddd31c60ccfb87bbcd7fef2cb89ef24d5cd803983910fc585681bfde6f6f5','SEED_DIGEST')
 need(digest(c['a2_policy_view'])=='a37cde42a2c4c147f4abc9289e5de693790218d17bcafcbe7fe3cfb49a9d6602','PUBLIC_DIGEST')
 for rec in read(run/'evidence_manifest.json')['files']:need(sha(run/rec['path'])==rec['sha256'],'RUN002_MANIFEST')
 c5=next(ROOT.parent.glob('stfbs_member_change_001*'))
 for rec in read(c5/'evidence_manifest_final.json')['files']:need(sha(c5/rec['path'])==rec['sha256'],'H1_C5_MANIFEST')
 need(sha(c5/'THREE_ACTION_COMPARISON.json')=='59d5402db2a429c78e05bbc1e6a9039520c21589be4de2ee147cde373b5e4a42','H1_RESULTS')
 old=ROOT.parent/'stfbs_lite_h2_h3_extension_003_a801a60d3e2142ca94567c0f75929a49';need(sha(old/'EXECUTION_FREEZE.json')=='554061b40e9132f5823e7411812eb719e6e0de8281b14f314ca0a635882e3de0','EXT003_FREEZE')
 index=read(ROOT/'BRANCH_EXECUTION_INDEX.json')
 need(not (ROOT.parent/(TASK+'.consumed.json')).exists(),'TASK004_PREEXISTING')
 prior_attempts=[]
 for root in ROOT.parent.glob('stfbs*'):
  if root==ROOT:continue
  for marker in root.rglob('*.consumed*'):
   text=marker.read_text(encoding='utf-8-sig',errors='replace')
   if any(b['attempt_id'] in text for b in index):prior_attempts.append(str(marker))
 need(not prior_attempts,'NEW_ATTEMPT_ALREADY_USED')
 for p in ROOT.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
 runtime=read(ROOT/'RUNTIME_REFERENCE.json')['file_sha256']
 for p,h in runtime.items():need(sha(p)==h,'RUNTIME_FROZEN_FILE')
 source={p.relative_to(REPO).as_posix():sha(p) for root in ['research','pursuit_v2','scripts'] for p in (REPO/root).rglob('*.py')}
 for b in index:
  d=pathlib.Path(b['directory']);a=read(d/'authorization.json');a.update(source_sha256=source,runtime_sha256=runtime,git_head='9b476fde2735a4c134b3e3cbe891c387fa71f2a9',runtime=dict(python=sys.executable,version=sys.version))
  (d/'authorization.json').write_text(json.dumps(a,indent=2,sort_keys=True),encoding='utf-8')
  f=read(d/'execution_freeze.json');f['files']['authorization.json']=sha(d/'authorization.json');(d/'execution_freeze.json').write_text(json.dumps(f,indent=2),encoding='utf-8')
 save('S4_STATIC.json',dict(status='PASS',source_sha256=source,public_digest=digest(c['a2_policy_view']),seed_digest=digest(c['consumer_seed']),versions=versions,prior_attempts_found=prior_attempts,frozen_scientific_inputs=names,branch_count=6,thin_driver='True Branch in initialized_budget + solver_guard; no scientific trial run',history=history()))
 # Synthetic S1-S3 use one independent process, never imported into science workers.
 remaining_cpu=120-(_process_cpu_ticks()+aux)/1e7;remaining_wall=180-(time.monotonic()-START);need(remaining_cpu>0 and remaining_wall>0,'PRECHECK_PREPARATION_BUDGET')
 supervisor=WindowsSupervisor(total_cpu_seconds=remaining_cpu,wall_seconds=remaining_wall,attempt_identity='EXT004_SYNTHETIC_PRECHECK')
 precheck_receipt=supervisor.run_monitored([sys.executable,'-I','-S','-B',str(ROOT/'precheck.py')],cwd=REPO,log=ROOT/'precheck.log');save('PRECHECK_SUPERVISOR_RECEIPT.json',precheck_receipt)
 need(precheck_receipt['worker_exit_code']==0 and precheck_receipt['accounting_status']=='FINAL_VALID' and precheck_receipt['process_tree_status']=='PROCESS_TREE_EXIT_CONFIRMED' and not precheck_receipt['errors'],'S1_S3_WORKER_FAILED')
 need(read(ROOT/'PRECHECK_RESULT.json')['status']=='PASS','S1_S3_NOT_PASS')
 need((_process_cpu_ticks()+aux+precheck_receipt['final_cpu_ticks'])/1e7<=120 and time.monotonic()-START<=180,'PRECHECK_BUDGET')
 admitted=True;save('RESEARCH_ADMISSION_S1_S4.json',dict(status='PASS',S1_S3=read(ROOT/'PRECHECK_RESULT.json'),S4='S4_STATIC.json',precheck_cpu_ticks=_process_cpu_ticks()+aux+precheck_receipt['final_cpu_ticks'],wall_seconds=time.monotonic()-START,scientific_attempts_consumed=0))
 programs={p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*') if p.is_file() and (p.suffix=='.py' or p.name in set(names)|{'AUTHORIZATION.txt','BRANCH_EXECUTION_INDEX.json','authorization.json','execution_freeze.json','RUNTIME_REFERENCE.json','S4_STATIC.json','RESEARCH_ADMISSION_S1_S4.json'})}
 save('EXECUTION_FREEZE.json',dict(task_id=TASK,programs=programs,source_sha256=source,runtime_sha256=runtime,branches=index,budgets=dict(policy_wls=744,observation_wls=63,solver_starts=7263,R=2,Assignment=2,physical_steps=60,cpu=1200,inner_wall=1500,outer_wall=1560,storage=268435456,attempts=1),stop_on_failure=True,retry=False))
 frozen()
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
  if ok:frozen()
  report=dict(name=b['name'],run_id=b['run_id'],attempt_id=b['attempt_id'],branch_id=b['branch_id'],valid_cell_candidate=bool(ok),status='VALID_CELL_CANDIDATE' if ok else 'FAILED_OR_INCOMPLETE',returncode=exitcode,stdout=stdout,stderr=stderr,outer=out,inner=inn,counts=read(d/'RESOURCE_COUNTS.json') if (d/'RESOURCE_COUNTS.json').exists() else None,raw_net=read(d/'BRANCH_RAW.json')['net'] if (d/'BRANCH_RAW.json').exists() else None)
  with (d/'FINAL_BRANCH_REPORT.json').open('x') as f:json.dump(report,f,indent=2)
  entries=[dict(path=p.relative_to(d).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in d.rglob('*') if p.is_file()]
  with (d/'evidence_manifest.json').open('x') as f:json.dump(dict(files=entries),f,indent=2)
  for entry in read(d/'evidence_manifest.json')['files']:need(sha(d/entry['path'])==entry['sha256'],'OUTPUT_MANIFEST')
  rows.append(report);print('SCIENCE_FINISH',b['name'],report['status'],flush=True);need(ok,'BRANCH_FAILED/'+b['name'])
 summary_start=time.monotonic();summary_cpu=_process_cpu_ticks()+aux
 result=aggregate(ROOT,index);save('NINE_CELL_VALUE_MATRIX.json',dict(matrix=result['matrix'],evidence=result['cell_evidence'],H1=result['h1_evidence']));save('REGRET_MATRIX.json',dict(regret=result['regret'],worst_regret=result['worst_regret']));save('MINIMAX_REGRET_RESULT.json',result);math_complete=True
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
  return u['cpu_seconds']<=120 and u['wall_seconds']<=180 and u['total_wall_seconds']<=9720 and u['storage_bytes']<=1879048192
 if not resource_ok():final_faults.append('FINAL_RESOURCE_BUDGET')
 accepted=admitted and valid==6 and error is None and math_complete and not faults and not final_faults and all_exited and resource_ok()
 final=dict(task_id=TASK,continuation='EXTENSION_004_CONTINUATION_001',status='LOCAL_DEV_D60_H2_H3_VALUE_MATRIX_INCOMPLETE',S1_S4='PASS' if admitted else 'NOT_PASSED',valid_new_cells=valid,scientific_attempts_consumed=consumed,branches_not_started=6-consumed,branches=rows,error=error,precheck_receipt=precheck_receipt,parent_cpu_ticks=_process_cpu_ticks(),aux_cpu_ticks=aux,wall_seconds=time.monotonic()-START,faults=faults,final_faults=final_faults,retry=False,h1_reused_cells=3,actual_run=False,h1_rerun=False,minimax_regret='COMPUTED_NOT_FULLY_ACCEPTED' if math_complete else 'NOT_COMPLETED',production_admission='BLOCKED',science_scope='Exploratory finite three-world three-action single-D60 offline MODEL; no statistical or full uncertainty-set guarantee',final_summary_resource_usage=summary_usage(),all_started_processes_exit_confirmed=all_exited)
 save('HISTORICAL_PROTECTION_AUDIT.json',protection);save('AGGREGATE_RESOURCE_LEDGER.json',dict(branches=rows,precheck=precheck_receipt,outer_and_inner_not_additive=True,parent_cpu_ticks=_process_cpu_ticks(),aux_cpu_ticks=aux));save('FINAL_REPORT.json',final)
 (ROOT/'FINAL_REPORT.md').write_text('# EXTENSION_004_CONTINUATION_001\n\n'+json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8')
 def manifest():
  entries=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in ROOT.rglob('*') if p.is_file() and p.name!='evidence_manifest_final.json']
  (ROOT/'evidence_manifest_final.json').write_text(json.dumps(dict(files=entries,self_excluded=True),indent=2),encoding='utf-8')
  for e in entries:
   if sha(ROOT/e['path'])!=e['sha256']:raise RuntimeError('FINAL_EVIDENCE_MISMATCH/'+e['path'])
 manifest()
 if accepted and resource_ok() and not faults:
  final['status']='LOCAL_DEV_D60_H2_H3_VALUE_MATRIX_PASS_CANDIDATE';final['minimax_regret']='COMPUTED'
 final['final_summary_resource_usage']=summary_usage()
 (ROOT/'FINAL_REPORT.json').write_text(json.dumps(final,sort_keys=True,indent=2),encoding='utf-8')
 (ROOT/'FINAL_REPORT.md').write_text('# EXTENSION_004_CONTINUATION_001\n\n'+json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8')
 manifest()
 if not resource_ok() or faults:
  final['status']='LOCAL_DEV_D60_H2_H3_VALUE_MATRIX_INCOMPLETE';final['faults']=faults;final['final_faults'].append('POST_SEAL_RESOURCE_CHECK');final['final_summary_resource_usage']=summary_usage()
  (ROOT/'FINAL_REPORT.json').write_text(json.dumps(final,sort_keys=True,indent=2),encoding='utf-8')
  (ROOT/'FINAL_REPORT.md').write_text('# EXTENSION_004_CONTINUATION_001\n\n'+json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8');manifest()
 stop.set();watcher.join()
 print(str(ROOT),final['status'],repr(error),flush=True)
