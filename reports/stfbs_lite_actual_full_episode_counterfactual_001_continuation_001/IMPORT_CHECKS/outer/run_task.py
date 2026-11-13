import time
START=time.monotonic();CPU0=time.process_time()
import pathlib,sys,json,hashlib,os,subprocess,ctypes,threading,traceback,shutil,ast
ROOT=pathlib.Path(__file__).resolve().parent;REPO=pathlib.Path(r'D:\1st\dynamic_member_coalition_core')
ARCHIVE=REPO/'reports/stfbs_lite_actual_full_episode_counterfactual_001_continuation_001'
TASK='STFBS_LITE_ACTUAL_FULL_EPISODE_COUNTERFACTUAL_001_CONTINUATION_001';SCIENTIFIC_TASK='STFBS_LITE_ACTUAL_FULL_EPISODE_COUNTERFACTUAL_001';HEAD='65237ed82e30363c3013d70582ca591277e72cea'
PRIOR=json.loads((ROOT/'PRIOR_RESOURCE_DEDUCTION.json').read_bytes())['prior']
sys.path.insert(0,str(ROOT))
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def save(n,x,replace=False):
 with (ROOT/n).open('w' if replace else 'x',encoding='utf-8') as f:json.dump(x,f,indent=2,sort_keys=True,allow_nan=False)
aux=0.;stage='G0';g4_cpu=None;g4_wall=None;active=None;error=None;rows=[];admitted=False;analysis=None;protected={};stop=threading.Event();faults=[];g0=None
BRANCHES={'FULL_SWITCH','FULL_KEEP','FULL_MEMBER_CHANGE'}
def size(directory):return sum(p.stat().st_size for p in directory.rglob('*') if p.is_file()) if directory.exists() else 0
def public_size(directory):return sum(p.stat().st_size for p in directory.rglob('*') if p.is_file() and p.relative_to(directory).parts[0] not in BRANCHES) if directory.exists() else 0
def external_bytes():
 return sum(p.stat().st_size for p in [ROOT.parent/(TASK+'.controller.started'),ROOT.parent/(TASK+'.consumed.json')] if p.is_file())
def resources():
 return dict(controller_cpu=time.process_time()-CPU0,auxiliary_cpu=aux,wall=time.monotonic()-START+PRIOR['task_wall'],current_wall=time.monotonic()-START,work_storage=size(ROOT),archive_storage=size(ARCHIVE),total_storage=size(ROOT)+size(ARCHIVE)+PRIOR['total_storage']+external_bytes(),current_storage=size(ROOT)+size(ARCHIVE)+external_bytes(),public_storage=public_size(ROOT)+public_size(ARCHIVE)+PRIOR['public_storage']+external_bytes(),current_public_storage=public_size(ROOT)+public_size(ARCHIVE)+external_bytes(),prior=PRIOR,G4_cpu=0 if g4_cpu is None else time.process_time()+aux-g4_cpu,G4_wall=0 if g4_wall is None else time.monotonic()-g4_wall)
def limit():
 u=resources()
 if u['wall']>7860:return 'TASK_WALL'
 if u['total_storage']>1073741824:return 'TASK_STORAGE'
 if u['public_storage']>268435456:return 'PUBLIC_STORAGE'
 if stage=='G0' and (u['controller_cpu']+aux+PRIOR['G0_cpu']>180 or u['current_wall']+PRIOR['G0_wall']>240):return 'G0_BUDGET'
 if stage=='G4' and (u['G4_cpu']+PRIOR['G4_cpu']>180 or u['G4_wall']+PRIOR['G4_wall']>240):return 'G4_BUDGET'
 for n in BRANCHES:
  if size(ROOT/n)+size(ARCHIVE/n)+PRIOR['branch_storage'][n]>268435456:return 'BRANCH_STORAGE/'+n
 return None
def watch():
 while not stop.wait(.2):
  try:
   reason=limit()
   if reason:
    faults.append(reason)
    if active is not None and active.poll() is None:active.terminate()
    import _thread
    _thread.interrupt_main();return
  except BaseException as e:faults.append('MONITOR/'+repr(e));return
def git(*args):
 global aux
 p=subprocess.Popen(['git','-c','safe.directory='+REPO.as_posix(),*args],cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out,err=p.communicate()
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.c_void_p]*4;k.GetProcessTimes.restype=ctypes.c_int;t=[ctypes.c_uint64() for _ in range(4)]
 need(k.GetProcessTimes(int(p._handle),*[ctypes.byref(x) for x in t]),'AUX_CPU_ACCOUNTING');aux+=(t[2].value+t[3].value)/1e7;need(p.returncode==0,err.decode());return out.decode().strip()
def history():
 bad=[p for p,h in protected.items() if not pathlib.Path(p).is_file() or sha(p)!=h];need(not bad,'HISTORY_CHANGED/'+str(bad[:3]));return dict(status='PASS',count=len(protected),mismatches=[])
def frozen():
 f=read(ROOT/'EXECUTION_FREEZE.json')
 for p,h in f['files'].items():need(sha(ROOT/p)==h,'FROZEN_INPUT_OR_DRIVER/'+p)
 for p,h in f['source_sha256'].items():need(sha(REPO/p)==h,'SCIENCE_SOURCE_DRIFT/'+p)
 for p,h in f['runtime_sha256'].items():need(sha(p)==h,'RUNTIME_DRIFT/'+p)
monitor=threading.Thread(target=watch,daemon=True);monitor.start()
try:
 with (ROOT.parent/(TASK+'.controller.started')).open('x') as f:f.write(str(ROOT));f.flush();os.fsync(f.fileno())
 save('RESOURCE_ACCOUNTING_START.json',dict(task_id=TASK,wall_start=START,cpu_start=CPU0,formal_entry='run_task.py before any package/science import',limits=dict(G0_cpu=180,G0_wall=240,G4_cpu=180,G4_wall=240,total_wall=7860,total_storage=1073741824,public_storage=268435456)))
 from bootstrap import bind
 entry=bind(ROOT,'controller');save('ENTRY_IMPORT_VERIFICATION.json',entry)
 need(git('rev-parse','HEAD')==HEAD and git('branch','--show-current')=='main','HEAD_OR_BRANCH')
 need(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'TRACKED_OR_STAGING_CHANGES')
 need(not ARCHIVE.exists(),'ARCHIVE_ALREADY_EXISTS')
 need(not git('diff','--name-only','a17627c83444a4c0e2b05903b2272eac5d579191','HEAD','--','research','pursuit_v2','scripts','configs'),'ORIGINAL_SCIENTIFIC_SOURCE_CHANGED')
 original=read(REPO/'reports/stfbs_lite_actual_full_episode_counterfactual_001/EXECUTION_FREEZE.json')
 for p,h in original['source_sha256'].items():need(sha(REPO/p)==h,'ORIGINAL_SCIENCE_FINGERPRINT')
 need(read(ROOT/'CONTINUATION_AUTHORIZATION.json')['controller_task']==TASK,'CONTINUATION_AUTHORIZATION')

 import psutil
 previous=[]
 for p in psutil.process_iter(['pid','cmdline']):
  try:
   if p.pid==os.getpid():continue
   argv=p.info['cmdline'] or []
   if any('stfbs_lite_actual_full_episode_counterfactual_001_' in x and x.endswith('.py') for x in argv):previous.append(p.pid)
  except (psutil.NoSuchProcess,psutil.AccessDenied):pass
 need(not previous,'PRIOR_ACTIVE_TASK')
 for other in ROOT.parent.glob('stfbs_lite_actual_full_episode_counterfactual_001_*'):
  if other!=ROOT:need(not any(other.rglob('attempt.consumed')) and not any(other.rglob('parent_start_attempt.lock')),'PRIOR_IDENTITY_CONSUMED')
 need(not (ROOT.parent/(TASK+'.consumed.json')).exists(),'TASK_ALREADY_CONSUMED')
 for rel in ['runs/a2_switch_episode_001','reports/a2_switch_episode_001_guard','reports/stfbs_lite_h2_h3_extension_005','reports/stfbs_lite_actual_counterfactual_001','reports/stfbs_lite_actual_counterfactual_001_continuation_001','reports/stfbs_lite_actual_full_episode_counterfactual_001']:
  for p in (REPO/rel).rglob('*'):
   if p.is_file():protected[str(p)]=sha(p)
 for d in ROOT.parent.glob('stfbs*'):
  if d==ROOT or not d.is_dir():continue
  for p in d.rglob('*'):
   if p.is_file() and ('consumed' in p.name or d.name.startswith('stfbs_member_change_001') or d.name.startswith('stfbs_lite_actual_counterfactual_001') or d.name=='stfbs_lite_actual_full_episode_counterfactual_001_0a5e0ff09fee4d0396baf445aa47bc58'):protected[str(p)]=sha(p)
 save('HISTORICAL_PROTECTION_BEFORE.json',dict(sha256=protected))
 for p in ROOT.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
 source={p.relative_to(REPO).as_posix():sha(p) for name in ['research','pursuit_v2','scripts'] for p in (REPO/name).rglob('*.py')}
 runtime=read(ROOT/'RUNTIME_REFERENCE.json')['file_sha256']
 for p,h in runtime.items():need(sha(p)==h,'RUNTIME_REFERENCE')
 for name in ['WORLD_INPUT.json','PUBLIC_INPUT.json']:need(sha(ROOT/name)==sha(REPO/'runs/a2_switch_episode_001'/name),'FROZEN_SCENE_SOURCE')
 need(sha(ROOT/'ACTION_FREEZE.json')==sha(REPO/'reports/stfbs_lite_h2_h3_extension_005/CANDIDATE_FREEZE.json'),'CANDIDATE_SOURCE')
 world=read(ROOT/'WORLD_INPUT.json');need(world['config']['change_cost']==.01 and world['config']['step_dt']==.05,'SCIENTIFIC_CONFIG')
 from research.non_oracle.stfbs_lite_real_d60_source import inspect_production_aliases
 aliases=inspect_production_aliases()
 save('RESOURCE_BINDING.json',dict(status='STATIC_BINDING_PREPARED',aliases=aliases,actual_categories={'policy.estimate':'ACTUAL_POLICY_WLS','public_stream._estimate':'ACTUAL_OBSERVATION_WLS','estimator.least_squares':'ACTUAL_SOLVER_START'},limits={'ACTUAL_POLICY_WLS':2574,'ACTUAL_OBSERVATION_WLS':126,'ACTUAL_SOLVER_START':24300},mapping='Original ACTUAL events retained; RESOURCE_CALL and five call_type counters added',runtime_dynamic_processor_check='each actual STEP; all processors must reference metered public_stream._estimate',STEP_contract='21 frames = 1 decision +20 physical, each tick verified',production_dispatcher_called=False,tests_executed=False))
 index=read(ROOT/'BRANCH_EXECUTION_INDEX.json')
 need([x['name'] for x in index]==['FULL_SWITCH','FULL_KEEP','FULL_MEMBER_CHANGE'],'BRANCH_ORDER')
 actions=read(ROOT/'ACTION_FREEZE.json');role={'none':0,'dual_neg45':1,'dual_pos45':2}
 for b in index:
  a=read(pathlib.Path(b['directory'])/'authorization.json');candidate=next(x for x in actions if x['kind']==b['action'])
  need(a['initial_actions']==candidate['actions'] and [[-1 if x['target'] is None else x['target'],role[x['role']]] for x in a['initial_actions']]==candidate['assignment_key'],'ACTION_ASSIGNMENT_KEY')
  need(a['git_head']==HEAD and a['source_sha256']==source and a['runtime_sha256']==runtime,'BRANCH_BINDING')
  need(not (pathlib.Path(b['directory'])/'attempt.consumed').exists() and not (pathlib.Path(b['directory'])/'parent_start_attempt.lock').exists(),'PRIOR_BRANCH_START')

 def verify_entries():
  global aux
  results=[]
  first=pathlib.Path(read(ROOT/'BRANCH_EXECUTION_INDEX.json')[0]['directory'])
  for role in ['outer','parent','worker']:
   scratch=ROOT/'IMPORT_CHECKS'/role;scratch.mkdir(parents=True)
   for source in list(ROOT.glob('*.py'))+[first/'authorization.json']:
    shutil.copy2(source,scratch/source.name)
   # Match actual formal entry bytes and common/bootstrap exactly.
   for n in ['outer_controller.py','model_driver.py','common.py','bootstrap.py']:need(sha(scratch/n)==sha(first/n),'IMPORT_PROBE_BYTES')
   args=[sys.executable,'-I','-S','-B',str(scratch/'entry_import_probe.py'),role]
   process=subprocess.Popen(args,cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   try:stdout,stderr=process.communicate(timeout=max(.1,240-PRIOR['G0_wall']-(time.monotonic()-START)))
   except BaseException:process.terminate();process.wait();raise
   k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.c_void_p]*4;k.GetProcessTimes.restype=ctypes.c_int;times=[ctypes.c_uint64() for _ in range(4)]
   need(k.GetProcessTimes(int(process._handle),*[ctypes.byref(x) for x in times]),'IMPORT_PROBE_CPU_RECEIPT')
   cpu=(times[2].value+times[3].value)/1e7;aux+=cpu
   receipt=dict(role=role,command=args,returncode=process.returncode,cpu_seconds=cpu,stdout=stdout,stderr=stderr,scratch=str(scratch))
   save('IMPORT_CHECK_'+role+'.json',receipt);need(process.returncode==0,'ISOLATED_ENTRY_IMPORT_FAILED/'+role)
   results.append(read(scratch/'RESULT.json'));need(not limit(),'IMPORT_CHECK_RESOURCE_LIMIT')
  save('ISOLATED_ENTRY_IMPORT_VERIFICATION.json',dict(status='PASS',checks=results,science_calls=0,formal_output_directories_untouched=True))
 verify_entries()

 save('INPUT_FREEZE.json',dict(files={n:sha(ROOT/n) for n in ['WORLD_INPUT.json','PUBLIC_INPUT.json','ACTION_FREEZE.json']},execution_change_cost=.01,start_tick=0,end_tick=120))
 g0=resources();need(not limit() and not faults,'G0_RESOURCE_STOP')
 save('RESEARCH_EXECUTION_ADMISSION.json',dict(status='PASS',task_id=TASK,head=HEAD,environment=entry,scientific_source_count=len(source),new_identities=index,actual_executor='StaggeredEnvironment',old_ACTUAL_MODEL_route_resumed=False,G0_resources=g0,no_extra_scientific_trial=True))
 files={p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*') if p.is_file() and (p.suffix=='.py' or p.name in {'AUTHORIZATION.txt','WORLD_INPUT.json','PUBLIC_INPUT.json','ACTION_FREEZE.json','authorization.json','execution_freeze.json','RUNTIME_REFERENCE.json','BRANCH_EXECUTION_INDEX.json','INPUT_FREEZE.json','RESEARCH_EXECUTION_ADMISSION.json','RESOURCE_BINDING.json','PRIOR_RESOURCE_DEDUCTION.json','CONTINUATION_AUTHORIZATION.json','OPPORTUNITY_INHERITANCE.json','ISOLATED_ENTRY_IMPORT_VERIFICATION.json'})}
 save('EXECUTION_FREEZE.json',dict(task_id=TASK,scientific_task=SCIENTIFIC_TASK,prior_deduction=PRIOR,original_scientific_head='a17627c83444a4c0e2b05903b2272eac5d579191',head=HEAD,files=files,source_sha256=source,runtime_sha256=runtime,budgets=dict(policy_wls=2574,observation_wls=126,solver_starts=24300,R=6,Assignment=6,STEP=6,physical=120,cpu_trigger=1750,wall_trigger=2350,final_cpu=1800,final_wall=2400,outer_wall=2460,branch_storage=268435456,G0_cpu=180,G0_wall=240,G4_cpu=180,G4_wall=240,total_wall=7860,total_storage=1073741824,public_storage=268435456),scientific_tolerance=1e-8,common_prefix_rule='Full scientific prefix comparison including observed_tick; operation namespaces and validated derived digests aligned',audit_adapter='Original independent verify_physics uses submitted_assignment, nominal table audit remains separate; member and role transition names admitted',retry=False))
 frozen();history();need(not limit(),'G0_FINAL_RESOURCE')
 admitted=True;stage='SCIENCE'
 with (ROOT.parent/(TASK+'.consumed.json')).open('x') as f:json.dump(dict(task_id=TASK,scientific_task=SCIENTIFIC_TASK,root=str(ROOT),opportunities=3,one_to_one_inheritance=True,freeze_sha256=sha(ROOT/'EXECUTION_FREEZE.json'),refund=False),f);f.flush();os.fsync(f.fileno())
 for b in index:
  frozen();history();need(not faults and not limit(),'GLOBAL_STOP')
  d=pathlib.Path(b['directory']);print('SCIENCE_START',b['name'],flush=True)
  active=subprocess.Popen(b['command'],cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  stdout,stderr=active.communicate(timeout=2465);code=active.returncode;active=None
  inner=read(d/'SUPERVISOR_RECEIPT.json') if (d/'SUPERVISOR_RECEIPT.json').exists() else None
  outer=read(d/'outer_receipt.json') if (d/'outer_receipt.json').exists() else None
  ok=code==0 and inner and outer and (d/'worker_success.json').exists()
  if ok:ok=inner['worker_exit_code']==0 and inner['accounting_status']=='FINAL_VALID' and inner['process_tree_status']=='PROCESS_TREE_EXIT_CONFIRMED' and inner['final_cpu_ticks']/1e7<=1800 and inner['wall_elapsed']<=2400 and not inner['errors'] and outer['status']=='OUTER_CONTROL_COMPLETE' and outer['process_tree_exit_confirmed'] and outer['elapsed_seconds']<=2460 and not outer['errors']
  if ok:
   fin=read(d/'RESOURCE_FINALIZATION.json');ok=fin['state']=='FINALIZED_PASS' and fin['disk']==fin['committed']==fin['runtime'] and read(d/'ACTUAL_PHYSICAL_SERVICE_AUDIT.json')['status']=='PASS'
  report=dict(name=b['name'],action=b['action'],attempt_id=b['attempt_id'],valid=bool(ok),status='VALID_ACTUAL_CELL_CANDIDATE' if ok else 'FAILED_OR_INCOMPLETE',returncode=code,stdout=stdout,stderr=stderr,inner=inner,outer=outer,counts=read(d/'RESOURCE_COUNTS.json') if (d/'RESOURCE_COUNTS.json').exists() else None,economic=read(d/'ECONOMIC_LEDGER.json') if (d/'ECONOMIC_LEDGER.json').exists() else None)
  with (d/'FINAL_BRANCH_REPORT.json').open('x') as f:json.dump(report,f,indent=2)
  entries=[dict(path=p.relative_to(d).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in d.rglob('*') if p.is_file()]
  with (d/'evidence_manifest.json').open('x') as f:json.dump(dict(files=entries),f,indent=2)
  for e in entries:need(sha(d/e['path'])==e['sha256'],'BRANCH_EVIDENCE_DRIFT')
  rows.append(report);print('SCIENCE_FINISH',b['name'],report['status'],flush=True);need(ok,'BRANCH_FAILED/'+b['name'])
  if b['name']=='FULL_SWITCH':shutil.copy2(d/'HISTORICAL_CASE_REPRODUCTION.json',ROOT/'HISTORICAL_CASE_REPRODUCTION.json')
 stage='G4';g4_cpu=time.process_time()+aux;g4_wall=time.monotonic()
 prefix=[dict(branch=b['name'],result=read(ROOT/b['name']/'COMMON_D60_PREFIX_EQUIVALENCE.json')) for b in index]
 save('COMMON_D60_PREFIX_EQUIVALENCE.json',dict(status='PASS',comparisons=prefix))
 from analysis import analyze
 analysis=analyze(index)
except BaseException as exc:
 error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),stage=stage)
 if active is not None and active.poll() is None:
  active.terminate()
  try:active.wait(5)
  except BaseException:pass
finally:
 if g4_cpu is None:g4_cpu=time.process_time()+aux;g4_wall=time.monotonic()
 stage='G4'
 protection=None;final_faults=[]
 try:protection=history()
 except BaseException as exc:protection=dict(status='FAIL',message=str(exc));final_faults.append('HISTORY')
 if (ROOT/'EXECUTION_FREEZE.json').exists():
  try:frozen()
  except BaseException as exc:final_faults.append('FREEZE/'+repr(exc))
 else:final_faults.append('FREEZE_ABSENT')
 index=read(ROOT/'BRANCH_EXECUTION_INDEX.json')
 consumed=sum((pathlib.Path(b['directory'])/'attempt.consumed').exists() for b in index)
 started=sum((pathlib.Path(b['directory'])/'parent_start_attempt.lock').exists() for b in index)
 valid=sum(b['valid'] for b in rows)
 exited=all(b['inner'] and b['outer'] and b['inner']['process_tree_status']=='PROCESS_TREE_EXIT_CONFIRMED' and b['outer']['process_tree_exit_confirmed'] for b in rows)
 if active is not None and active.poll() is None:exited=False
 final=dict(task_id=TASK,scientific_task=SCIENTIFIC_TASK,CONTINUATION_OF=SCIENTIFIC_TASK,prior_deduction=PRIOR,FINAL_TASK_STATUS='LOCAL_DEV_ACTUAL_FULL_EPISODE_THREE_ACTION_INCOMPLETE',G0_STATUS='PASS' if admitted else 'FAIL',FULL_SWITCH_STATUS=next((b['status'] for b in rows if b['name']=='FULL_SWITCH'),'NOT_STARTED'),FULL_KEEP_STATUS=next((b['status'] for b in rows if b['name']=='FULL_KEEP'),'NOT_STARTED'),FULL_MEMBER_CHANGE_STATUS=next((b['status'] for b in rows if b['name']=='FULL_MEMBER_CHANGE'),'NOT_STARTED'),G4_STATUS='PASS_CANDIDATE' if analysis else 'NOT_EXECUTED',HISTORICAL_CASE_REPRODUCTION=read(ROOT/'HISTORICAL_CASE_REPRODUCTION.json')['status'] if (ROOT/'HISTORICAL_CASE_REPRODUCTION.json').exists() else 'NOT_EXECUTED',COMMON_D60_PREFIX_EQUIVALENCE='PASS' if analysis else 'NOT_COMPLETED',NEW_ACTUAL_MATRIX_INTERNAL_VALIDITY='PASS_CANDIDATE' if valid==3 and analysis else 'INCOMPLETE',ORIGINAL_COUNTERFACTUAL_STATUS='PASS_CANDIDATE' if analysis else 'INCOMPLETE',NO_CHANGE_COST_REVALUATION_STATUS='PASS_CANDIDATE' if analysis else 'INCOMPLETE',FOUR_WORLD_AUXILIARY_MATRIX_STATUS='PASS_CANDIDATE' if analysis and analysis['complete'] else 'INCOMPLETE',FEE_SENSITIVITY_STATUS='PASS_CANDIDATE' if analysis else 'INCOMPLETE',FULL_DELIVERABLE_COMPLETE=False,VALID_ACTUAL_CELLS=valid,STARTED_ATTEMPTS=started,CONSUMED_ATTEMPTS=consumed,UNSTARTED_BRANCHES=3-started,branches=rows,error=error,faults=faults,final_faults=final_faults,PROCESS_EXIT_STATUS='ALL_CONFIRMED' if exited else 'NOT_CONFIRMED',PRODUCTION_SOURCE_MODIFIED=False,OLD_ACTUAL_MODEL_CALIBRATION_RESUMED=False,OLD_CONSUMED_ATTEMPT_RETRIED=False,EXECUTION_CHANGE_COST=.01,ZERO_CHANGE_COST_CLOSED_LOOP_EXECUTED=False,H1_H2_H3_RERUN=False,ADDITIONAL_SCIENTIFIC_ATTEMPTS=0,AUTOMATIC_RETRY=False,PRODUCTION_ADMISSION='BLOCKED')
 save('HISTORICAL_PROTECTION_AUDIT.json',protection)
 def report():
  u=resources();final['RESOURCE_USAGE']=u;final['RESOURCE_ACCEPTANCE']='PASS' if not limit() else 'FAIL'
  save('FINAL_REPORT.json',final,True)
  save('AGGREGATE_RESOURCE_LEDGER.json',dict(task_id=TASK,prior=PRIOR,remaining=dict(G0_CPU=180-PRIOR['G0_cpu']-(g0['controller_cpu']+g0['auxiliary_cpu'] if g0 else u['controller_cpu']+aux),G0_wall=240-PRIOR['G0_wall']-(g0['current_wall'] if g0 else u['current_wall']),G4_CPU=180-PRIOR['G4_cpu']-u['G4_cpu'],G4_wall=240-PRIOR['G4_wall']-u['G4_wall'],task_wall=7860-u['wall'],public_storage=268435456-u['public_storage'],total_storage=1073741824-u['total_storage']),G0=g0,G4=dict(cpu=u['G4_cpu'],wall=u['G4_wall']),task=u,branches=rows,CPU_scope='Inner Job cumulative CPU; outer includes inner and is not added; controller and Git auxiliary reported separately',storage_scope='Work+archive counted; public excludes formal branch dirs; branch classifications not added twice'),True)
  if not (ROOT/'SCIENTIFIC_SUMMARY.md').exists():(ROOT/'SCIENTIFIC_SUMMARY.md').write_text('# 任务停止报告\n\n'+json.dumps(final,ensure_ascii=False,indent=2),encoding='utf-8')
 def manifest():
  entries=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in ROOT.rglob('*') if p.is_file() and p.name!='evidence_manifest_final.json']
  save('evidence_manifest_final.json',dict(files=entries,self_excluded=True),True)
  for e in entries:need(sha(ROOT/e['path'])==e['sha256'],'FINAL_MANIFEST')
 report();manifest()
 archive_ok=False
 try:
  need(not ARCHIVE.exists(),'ARCHIVE_CONFLICT');need(resources()['total_storage']+size(ROOT)<1073741824,'PROJECTED_ARCHIVE_TOTAL')
  need(2*public_size(ROOT)+PRIOR['public_storage']+external_bytes()<268435456,'PROJECTED_ARCHIVE_PUBLIC')
  for n in BRANCHES:need(2*size(ROOT/n)+PRIOR['branch_storage'][n]<268435456,'PROJECTED_BRANCH_COPY_STORAGE')
  ARCHIVE.mkdir()
  mapping=[]
  def copy_all():
   nonlocal_dummy=None
   for p in ROOT.rglob('*'):
    if not p.is_file():continue
    q=ARCHIVE/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);need(sha(p)==sha(q),'ARCHIVE_COPY_SHA')
  copy_all()
  archive_ok=True
  if admitted and valid==3 and analysis and not error and not faults and not final_faults and exited and not limit():final['FINAL_TASK_STATUS']='LOCAL_DEV_ACTUAL_FULL_EPISODE_THREE_ACTION_PASS_CANDIDATE';final['FULL_DELIVERABLE_COMPLETE']=analysis['complete']
  report();manifest();copy_all()
  for p in ROOT.rglob('*'):
   if p.is_file():mapping.append(dict(source=str(p),archive=str(ARCHIVE/p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)))
  with (ARCHIVE/'ARCHIVE_PATH_MAPPING.json').open('x') as f:json.dump(dict(files=mapping),f,indent=2)
  with (ARCHIVE/'ARCHIVE_VERIFICATION.json').open('x') as f:json.dump(dict(status='PASS',original_files=len(mapping),original_bytes=sum(e['bytes'] for e in mapping),source_and_archive_sha256_match=True,missing_files=0,sha256_mismatches=0,historical_protection=protection,started_attempts=started,consumed_attempts=consumed,valid_cells=valid,process_exit_confirmed=exited,resource_usage=resources()),f,indent=2)
  need(not limit() and not faults,'POST_ARCHIVE_RESOURCE')
 except BaseException as exc:
  final['FINAL_TASK_STATUS']='LOCAL_DEV_ACTUAL_FULL_EPISODE_THREE_ACTION_INCOMPLETE';final['FULL_DELIVERABLE_COMPLETE']=False;final['archive_error']=dict(type=type(exc).__name__,message=str(exc));report();manifest()
  if ARCHIVE.exists():
   for n in ['FINAL_REPORT.json','AGGREGATE_RESOURCE_LEDGER.json','evidence_manifest_final.json']:shutil.copy2(ROOT/n,ARCHIVE/n)
 stop.set();monitor.join()
 print(str(ROOT),final['FINAL_TASK_STATUS'],repr(error),flush=True)
