from common import *
import traceback
from research.non_oracle.stfbs_lite_real_d60_supervisor_win import WindowsSupervisor
from research.non_oracle.stfbs_lite_local_dev import process_identity,verify_local_job_handoff
def worker():
 verify_frozen();verify_local_job_handoff(dict(attempt_id=ATTEMPT,mode=a['mode']),read(ROOT/'handoff.json'),sha(ROOT/'authorization.json'))
 from scripts.run_a1 import Sensing
 from research.non_oracle.environment import StaggeredEnvironment
 from research.non_oracle import policy
 from research.non_oracle.a2_analysis import decision_evidence
 from research.information_service_bridge import public_stream
 from research.cooperative_sensing import estimator
 from research.non_oracle.stfbs_lite_real_d60_source import guard_wls_bindings,inspect_production_aliases
 from actual_resources import ActualJournal,ResourceStop
 from comparison import prefix,comparable_prefix,scientific_compare,validate_snapshot
 from scripts.gq_windows.a0_identity import checkpoint
 from unittest.mock import patch
 journal=ActualJournal(ROOT/'worker.jsonl',TASK,ATTEMPT,LIMIT);env=None;records=[]
 try:
  world=read(ROOT/'WORLD_INPUT.json');public=read(ROOT/'PUBLIC_INPUT.json')
  require(world['config']['change_cost']==.01 and world['config']['step_dt']==.05,'FIXED_SCIENTIFIC_CONFIG')
  aliases=inspect_production_aliases();save('RESOURCE_BINDING_BEFORE.json',aliases)
  exact=policy.solve
  def counted_solve(*args,**kwargs):return journal.independent('ASSIGNMENT',exact,*args,**kwargs)
  with guard_wls_bindings(journal.ledger,policy=policy,bridge=public_stream,estimator=estimator),patch.object(policy,'solve',counted_solve):
   intact=journal.ledger.integrity_check
   def checked():
    try:intact();journal.check()
    except BaseException as exc:journal.halted=True;raise ResourceStop(str(exc)) from exc
   journal.ledger.integrity_check=checked
   require(policy.estimate is not estimator.estimate and estimator.least_squares.__name__=='wrapped','HOOK_INSTALLATION')
   sensing=Sensing()
   env=StaggeredEnvironment(deepcopy(world),sensing,a['physical_environment_id'],deepcopy(public['announcements']))
   while not env.done:
    journal.check();view=env.prepare_decision();tick=view['tick'];require(tick in [0,20,40,60,80,100],'DECISION_TICK')
    before=digest(view)
    nominal=journal.independent('R',policy.decide,view,'R')
    require(digest(view)==before,'NOMINAL_MUTATED_PUBLIC_VIEW')
    evidence=decision_evidence(view,nominal,env.beliefs.accepted_receipts)
    cp=env.observe_public();checkpoint(json.loads(json.dumps(cp)))
    if tick==60:
     science=deepcopy(prefix(env,view,records,nominal))
     require(digest(science['metrics'])==digest(records[-1]['step']['metrics']),'PREFIX_METRICS_LINK')
     document=dict(task_id=TASK,attempt_id=ATTEMPT,environment=a['physical_environment_id'],science=science)
     save('D60_PRE_INTERVENTION.json',document)
     if a['action']=='SWITCH':save('COMMON_D60_PREFIX_EQUIVALENCE.json',dict(status='REFERENCE_ESTABLISHED',reference_sha256=sha(ROOT/'D60_PRE_INTERVENTION.json')))
     else:
      reference=TASKROOT/'FULL_SWITCH/D60_PRE_INTERVENTION.json'
      manifest=read(reference.parent/'evidence_manifest.json')
      entry=next(x for x in manifest['files'] if x['path']=='D60_PRE_INTERVENTION.json');require(sha(reference)==entry['sha256'],'REFERENCE_PREFIX_CHANGED')
      other=read(reference);comparison=scientific_compare(comparable_prefix(other),comparable_prefix(document),other['environment'],document['environment'])
      save('COMMON_D60_PREFIX_EQUIVALENCE.json',comparison);require(comparison['status']=='PASS','COMMON_D60_PREFIX_NOT_EQUIVALENT')
     submitted=deepcopy(a['initial_actions'])
    else:submitted=deepcopy(nominal['actions'])
    request=a['physical_environment_id']+':D'+str(tick);journal.start_step(tick,request,cp['checkpoint_id'])
    committed_frames=[]
    def on_commit(frame):
     require(size()<LIMIT,'BRANCH_STORAGE_LIMIT')
     journal.append(dict(kind='STEP_FRAME',request_id=request,frame=frame));committed_frames.append(frame['tick'])
    result=env.step(submitted,cp['checkpoint_id'],tick,request,work_identity=a['work_identity'],on_commit=on_commit)
    require(result['status']=='COMMITTED' and result['replayed'] is False and result['start_tick']==tick and result['end_tick']==tick+20,'STEP_TRANSACTION')
    frames=result['frames'];physical=[f for f in frames if f['phase']=='physical']
    require(len(frames)==21 and frames[0]['phase']=='decision' and frames[0]['tick']==tick and len(physical)==20 and [f['tick'] for f in physical]==list(range(tick+1,tick+21)),'STEP_FRAME_COVERAGE')
    require(committed_frames==[f['tick'] for f in frames] and result['action_commit']['assignment']==submitted and result['action_commit']['checkpoint_id']==cp['checkpoint_id'],'COMMIT_SUBMISSION_OR_DURABILITY')
    commit=result['action_commit'];require(digest({k:v for k,v in commit.items() if k!='action_commit_id'})==commit['action_commit_id'],'ACTION_COMMIT_DIGEST')
    checkpoint(json.loads(json.dumps(result['checkpoint_after'])))
    require(result['checkpoint_after']['tick']==tick+20 and result['checkpoint_after']['phase']==('TERMINAL' if tick==100 else 'DECISION_READY'),'CHECKPOINT_PHASE')
    journal.complete_step(result)
    record=dict(policy_input=view,nominal_choice=nominal,nominal_decision_evidence=evidence,intervention_action=deepcopy(a['initial_actions']) if tick==60 else None,submitted_assignment=submitted,request_id=request,step=result)
    records.append(record);save('D%d_TRANSACTION.json'%tick,record)
    require(all(p.estimator_fn is public_stream._estimate for p in sensing.streams.values()),'UNMETERED_DYNAMIC_PROCESSOR')
   final=env.private_snapshot();validate_snapshot(final)
   require(env.tick==120 and final['state']['terminal_settled'],'INCOMPLETE_ACTUAL_EPISODE')
   raw=dict(task_id=TASK,attempt_id=ATTEMPT,execution_origin='ACTUAL',execution_scope='OFFLINE_SIMULATION_RESEARCH',records=records,final=final,metrics=env.metrics(),observations_consumed=env.beliefs.consumed)
   save('FULL_EPISODE_RAW.json',raw);save('D120_TERMINAL_STATE.json',final)
   save('BELIEF_AND_OBSERVATION_HISTORY.json',dict(states=env.beliefs.states,history=env.beliefs.history,pending=env.beliefs.pending,consumed=env.beliefs.consumed,accepted_receipts=env.beliefs.accepted_receipts,fusions=env.fusions))
   from physical_audit import verify_physics,verify_observation_feedback,table
   data=read(ROOT/'FULL_EPISODE_RAW.json')
   for rec in data['records']:
    table(rec)
    expected=a['initial_actions'] if rec['policy_input']['tick']==60 else rec['nominal_choice']['actions']
    require(rec['submitted_assignment']==expected,'INTERVENTION_OR_POLICY_AUDIT')
    for target in rec['policy_input']['targets']:require(target==public['announcements'][target['id']],'PUBLIC_TASK_TRUTH_BOUNDARY')
   physics=verify_physics(data['records'],data,world)
   verify_observation_feedback(data['records'],data,physics['receipts'],public['announcements'])
   save('ACTUAL_PHYSICAL_SERVICE_AUDIT.json',dict(status='PASS',recomputed=physics,nominal_plan_audit='PASS',submitted_assignment_audit='PASS',observation_belief_audit='PASS'))
   prefix_metrics=read(ROOT/'D60_PRE_INTERVENTION.json')['science']['metrics'];metrics=data['metrics']
   economic=dict(full=metrics,prefix=prefix_metrics,future_components={k:metrics['reward_components'][k]-prefix_metrics['reward_components'][k] for k in metrics['reward_components']},full_net=metrics['return_with_changes'],prefix_net=prefix_metrics['return_with_changes'],future_net=metrics['return_with_changes']-prefix_metrics['return_with_changes'],future_change_cost=metrics['change_cost']-prefix_metrics['change_cost'],future_assignment_changes=metrics['assignment_changes']-prefix_metrics['assignment_changes'])
   require(abs(sum(economic['future_components'].values())-economic['future_change_cost']-economic['future_net'])<=1e-8,'ECONOMIC_FUTURE_RECONCILIATION')
   save('ECONOMIC_LEDGER.json',economic)
   if a['action']=='SWITCH':
    from comparison import history_body
    historical=read(REPO/'runs/a2_switch_episode_001/R.json');validate_snapshot(historical['final'])
    reproduction=scientific_compare(history_body(historical),history_body(data),'A2_R',a['physical_environment_id'])
    reproduction['status']='CONFIRMED' if reproduction['status']=='PASS' else 'NOT_CONFIRMED'
    reproduction['FULL_SWITCH_INTERNAL_VALIDITY']='PASS_CANDIDATE'
    reproduction['historical_source_sha256']=sha(REPO/'runs/a2_switch_episode_001/R.json')
    reproduction['historical_full_net']=historical['metrics']['return_with_changes']
    reproduction['new_full_net']=data['metrics']['return_with_changes']
    save('HISTORICAL_CASE_REPRODUCTION.json',reproduction)

   finalization=journal.finalize();save('RESOURCE_FINALIZATION.json',finalization);save('CALL_CLOSURE_AUDIT.json',dict(status='PASS',calls=finalization['calls'],unclosed=[]))
   save('RESOURCE_COUNTS.json',dict(**journal.ledger.counts,R_CALLS=journal.runtime['R'],ASSIGNMENT_EXACT_SOLVER=journal.runtime['ASSIGNMENT'],ACTUAL_STEP_TRANSACTIONS=journal.steps,DECISION_BOUNDARY_FRAMES=journal.boundaries,ACTUAL_PHYSICAL_STEPS=journal.physical,TOTAL_STEP_RETURNED_FRAMES=journal.returned_frames))
   save('RESOURCE_BINDING_AFTER.json',dict(status='PASS',processors=len(sensing.streams),all_dynamic_processors_metered=True,known_wrappers_intact=True))
  verify_frozen()
  save('worker_success.json',dict(status='VALID_ACTUAL_CELL_CANDIDATE',attempt_id=ATTEMPT,raw_sha256=sha(ROOT/'FULL_EPISODE_RAW.json'),future_net=economic['future_net']))
 except BaseException as exc:
  journal.halted=True
  save('worker_failure.json',dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),tick=None if env is None else env.tick,counts=journal.ledger.counts,independent=journal.runtime,retry=False))
  raise
 finally:journal.local.close()
def parent():
 verify_frozen()
 with (ROOT/'attempt.consumed').open('x') as f:json.dump(dict(task_id=TASK,attempt_id=ATTEMPT,refund=False),f);f.flush();os.fsync(f.fileno())
 supervisor=WindowsSupervisor(total_cpu_seconds=1750,wall_seconds=2350,attempt_identity=ATTEMPT);create=supervisor.api.create
 def monitored_create(job,argv,cwd,env,log):
  pi=create(job,argv,cwd,env,log);require(supervisor.api.member(pi.hProcess,job),'WORKER_JOB_MEMBERSHIP')
  save('handoff.json',dict(mode=a['mode'],attempt_id=ATTEMPT,approval_digest=sha(ROOT/'authorization.json'),parent=process_identity(supervisor.api,supervisor.api.k.GetCurrentProcess()),worker=process_identity(supervisor.api,pi.hProcess),parent_verified_target_job=True))
  return pi
 supervisor.api.create=monitored_create
 receipt=supervisor.run_monitored([sys.executable,'-I','-S','-B',str(ROOT/'model_driver.py'),'--worker'],cwd=REPO,log=ROOT/'worker.log')
 save('SUPERVISOR_RECEIPT.json',receipt)
 require(receipt['worker_exit_code']==0 and receipt['accounting_status']=='FINAL_VALID' and receipt['process_tree_status']=='PROCESS_TREE_EXIT_CONFIRMED' and receipt['job_cleanup_status']=='PASS' and not receipt['errors'],'WORKER_FAILED')
 require(receipt['final_cpu_ticks']/1e7<=1800 and receipt['wall_elapsed']<=2400 and (ROOT/'worker_success.json').exists(),'FINAL_RESOURCE_ACCEPTANCE')
 save('parent_success.json',dict(status='PASS_CANDIDATE',attempt_id=ATTEMPT))
if __name__=='__main__':
 if '--worker' in sys.argv:worker()
 elif '--parent' in sys.argv:parent()
 else:raise RuntimeError('EXPLICIT_ACTUAL_ENTRY_REQUIRED')
