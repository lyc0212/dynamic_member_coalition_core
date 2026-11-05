"""GQ episode execution extracted from validated W4-R1; launch via public CLI."""
from pathlib import Path
import sys,json,copy,os,hashlib,traceback,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from research.information_service_online import public
from research.information_service.public_quality import prepare_frame,assess_quality
from research.cooperative_sensing.estimator import estimate
from research.information_service_online.evaluator import evaluate_candidate
from research.information_service_shared.contracts import make_scope
from research.information_service_memory_accounting.wiring import make_cache,process_identity,evaluate_candidate_for,observer_for
from research.information_service_online.common import digest
from research.information_service_shared.comparator import first_difference
from research.information_service_shared.table import restore_candidate_subset
from research.information_service_online.selection import restore_canonical_table,select
out=Path(sys.argv[1]);options=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'));MODES=['R','S_NEW'] if options['evaluator']=='both' else [options['evaluator']];RUN=options['run_id']
def save(name,obj):
 p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
counts={};current='none';stage='admission'
FIELDS=('kind','execution_contract_id','mode','request_identity','world_identity','candidate_identity','candidate','start_tick','end_tick','frames','events','per_target','sensing_results','metrics','final_positions','final_assignment','input_unchanged')
def prediction_sense(spec,label):
 from research.information_service_bridge.public_stream import BridgeFrameProcessor
 metadata=public.prediction_metadata(request,spec,RUN,authority=auth,physical_environment_id=RUN+'_PREDICT')
 reg=metadata['registration'];save(label+'/PREDICTION_REGISTRATION.json',metadata)
 processor=BridgeFrameProcessor(**{k:reg[k] for k in ['allowed_sensor_ids','start_tick','stream_id','target_id']})
 def callback(frame,allowed,first):
  assert frame['stream_id']==reg['stream_id'] and frame['target_id']==reg['target_id']
  assert set(allowed)==set(reg['allowed_sensor_ids']) and first==reg['start_tick']
  assert reg['context']['purpose']=='CANDIDATE_PREDICTION'
  before=digest(frame);result=processor.process(frame);assert digest(frame)==before
  result['flow_context']=copy.deepcopy(reg['context']);result['flow_registration']=copy.deepcopy(reg)
  counts[label]=counts.get(label,0)+int(result['estimator_called'])
  return result
 return callback

def candidate_gate(result,spec,label):
 from research.information_service_online.acceptance import audit_prediction
 from research.information_service_online.quality_audit import audit_fusion
 fusion_checks=[audit_fusion(row) for row in result['sensing_results']]
 checked=audit_prediction(request,result,spec)
 save(label+'/PREDICTION_AUDIT.json',dict(status='PASS',fusion_checks=fusion_checks,prediction=checked))

def compare(a,b):
 a=json.loads(Path(a).read_text(encoding='utf-8'));b=json.loads(Path(b).read_text(encoding='utf-8'))
 for k in FIELDS:
  delta=first_difference(a[k],b[k])
  if delta is not None:raise RuntimeError('Scientific difference '+k+': '+str(delta))
 return dict(status='PASS',fields=list(FIELDS),rule='existing typed binary64 first_difference; no numeric tolerance widened')
def r_eval(spec,label):
 global current
 current=label;result=evaluate_candidate(request,spec,prediction_sense(spec,label),history_authority=auth,work_identity=RUN,physical_environment_id=RUN+'_PREDICT')
 save(label+'.json',result);candidate_gate(result,spec,label);assert digest(request)==original
 return result
def s_batch(specs,label):
 global current
 folder=out/label;folder.mkdir(parents=True,exist_ok=False)
 scope=make_scope(request,attempt_id=RUN,decision_id='D0',batch_id=label,cache_instance_id=label,runtime_binding_id=digest(RUN),history_authority=auth)
 def event(row):
  with (folder/'cache_trace.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
 cache=make_cache('NEW',scope,request,history_authority=auth,on_trace=event,observer_binding=dict(producer_identity=process_identity(),execution_source_seal_sha256=SOURCE_ID))
 observer=observer_for(cache);observer.space_checkpoint('CP_INITIALIZED');rows=[]
 for spec in specs:
  current=label+'/C'+str(spec['index'])
  row=evaluate_candidate_for('NEW')(request,spec,prediction_sense(spec,current),cache=cache,history_authority=auth,work_identity=RUN,physical_environment_id=RUN+'_PREDICT')
  save(current+'.json',row);candidate_gate(row,spec,current);rows.append(row);assert digest(request)==original
 restored=restore_candidate_subset(request,rows,[s['index'] for s in specs],history_authority=auth);save(label+'/RESTORED.json',restored)
 observer.space_checkpoint('CP_NORMAL_TERMINAL');cache.close()
 receipt=observer.finalize(folder);save(label+'/SIDECAR.json',receipt);save(label+'/MEMORY.json',observer.snapshot());save(label+'/CACHE.json',cache.snapshot_diagnostics())
 return rows
from research.information_service_online.execution import OnlineEnvironment
UNIT_SOURCE=json.loads(Path(options['scene']).read_text(encoding='utf-8'))
SOURCE_ID=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

from research.information_service_bridge.public_stream import BridgeFrameProcessor
class ActualSense:
 def __init__(self,physical_id):
  self.physical_id=physical_id;self.streams={};self.registrations=[];self.calls=[];self.wls=0
 def register(self,metadata,checkpoint,work):
  for row in metadata['flows']:
   flow=row['flow_registration'];reg=public.sensing_registration(flow);context=public.flow_context(flow)
   assert context['purpose']=='ACTUAL_EXECUTION'
   assert context['physical_environment_id']==self.physical_id
   assert context['checkpoint_id']==checkpoint['checkpoint_id'] and context['work_instance_id']==work
   assert reg==row['registration'] and context==row['context']
   key=reg['stream_id']
   if key in self.streams:
    assert self.streams[key][0]==reg,'Conflicting registered stream'
   else:
    processor=BridgeFrameProcessor(**{k:reg[k] for k in ['allowed_sensor_ids','start_tick','stream_id','target_id']})
    self.streams[key]=(copy.deepcopy(reg),processor)
   self.registrations.append(copy.deepcopy(reg))
 def __call__(self,frame,allowed,start_tick,context):
  reg,processor=self.streams[frame['stream_id']]
  assert context==reg['context'],'Unregistered or wrong actual context'
  assert context['purpose']=='ACTUAL_EXECUTION' and context['physical_environment_id']==self.physical_id
  assert start_tick==reg['start_tick'] and frame['target_id']==reg['target_id']
  assert set(allowed)==set(reg['allowed_sensor_ids'])
  before=digest(frame);prepared=prepare_frame(frame,allowed)
  result=processor.process(frame)
  assert digest(frame)==before and result['payload_sha256']==prepared['payload_sha256']
  assert result['quality']['payload_sha256']==prepared['payload_sha256']
  result['flow_context']=copy.deepcopy(reg['context']);result['flow_registration']=copy.deepcopy(reg)
  self.wls+=int(result['estimator_called'])
  self.calls.append(dict(stream=frame['stream_id'],tick=frame['tick'],target=frame['target_id'],start_tick=start_tick,context=copy.deepcopy(reg['context']),quality=result['quality']['status'],estimator_called=result['estimator_called'],duplicate=result['duplicate']))
  return result

from research.information_service_online.acceptance import audit_decision
from research.information_service_online.episode_audit import audit_episode
summary=[]
try:
 save('SOURCE_INPUT.json',UNIT_SOURCE)
 save('DESIGN.json',dict(episodes=[dict(episode_id=RUN+'_'+m,private_execution_input=UNIT_SOURCE,expected_only={}) for m in MODES]))
 for mode in MODES:
  actual_id=RUN+'_'+mode
  current=mode+'/ACTUAL'
  actual_sense=ActualSense(actual_id)
  env=OnlineEnvironment(copy.deepcopy(UNIT_SOURCE),actual_sense,actual_id,work_identity=actual_id)
  cp=env.initialize();records=[];index_rows=[]
  save(mode+'/INITIAL_CHECKPOINT.json',cp);save(mode+'/INITIAL_BINDING.json',env.public_binding())
  for step in range(env.end_tick//20):
   if options['max_decisions'] is not None and step>=options['max_decisions']:raise RuntimeError('DECISION_LIMIT_BEFORE_TERMINAL')
   stage=mode+'/D'+str(step);label=stage
   cp=env.observe_public()
   if cp['phase']=='TERMINAL':break
   binding=env.public_binding();save(label+'/BINDING.json',binding)
   raw=(out/(label+'/BINDING.json')).read_bytes();save(label+'/BINDING_PIN.json',dict(sha256=hashlib.sha256(raw).hexdigest(),size=len(raw)))
   auth=public.HistoryAuthority.from_public_binding(json.loads(raw))
   request=public.request_from_checkpoint(cp,auth);manifest=public.build_manifest(request,auth)
   save(label+'/REQUEST.json',request);save(label+'/MANIFEST.json',manifest)
   assert manifest['candidate_count']<=options['max_candidates'],'Candidate cap exceeded'
   original=digest(request);specs=manifest['candidates']
   if mode=='R':rows=[r_eval(s,label+'/PREDICT/C'+str(s['index'])) for s in specs]
   else:
    rows=[]
    for i in range(0,len(specs),4):rows.extend(s_batch(specs[i:i+4],label+'/PREDICT/B'+str(i//4)))
   table=restore_canonical_table(manifest,rows);save(label+'/TABLE.json',table)
   choice=select(request,rows,authority=auth,work_identity=actual_id,physical_environment_id=actual_id);save(label+'/SELECTION.json',choice)
   candidate_paths=([out/(label+'/PREDICT/C'+str(spec['index'])+'.json') for spec in specs] if mode=='R' else [out/(label+'/PREDICT/B'+str(i//4)+'/C'+str(spec['index'])+'.json') for i,spec in enumerate(specs)])
   audit_out=out/label/'SELECTION_AUDIT';audit_out.mkdir()
   audit_decision(dict(binding_file=str((out/(label+'/BINDING.json')).resolve()),binding_sha256=hashlib.sha256(raw).hexdigest(),request_file=str((out/(label+'/REQUEST.json')).resolve()),candidate_result_files=[str(x.resolve()) for x in candidate_paths],reference_result_files=[],reference_required=False,selection_file=str((out/(label+'/SELECTION.json')).resolve())),audit_out)
   index_rows.append(dict(tick=cp['tick'],selection_file=str((out/(label+'/SELECTION.json')).resolve()),selection_audit_file=str((audit_out/'decision_audit.json').resolve()),step_result_file=str((out/(label+'/STEP.json')).resolve())))
   request_id=actual_id+'_D'+str(step)
   envelope=dict(message_kind='action_request',contract_id='gq_online_action_request_v1',operation=dict(physical_environment_id=actual_id,request_id=request_id,action_request_id=None),payload=dict(contract_id='gq_online_action_transaction_v1',checkpoint_id=cp['checkpoint_id'],expected_start_tick=cp['tick'],assignment=choice['actions']))
   # plan_action_metadata and step perform original public action validation and identity checks.
   metadata=public.plan_action_metadata(cp,choice['actions'],actual_id,physical_environment_id=actual_id)
   assert metadata==choice['action_metadata']
   actual_sense.register(metadata,cp,actual_id)
   save(label+'/ACTUAL_REGISTRATION.json',actual_sense.registrations)
   current=mode+'/ACTUAL';before_frames=len(env.frames);before_fusions=len(env.fusions)
   result=env.step(choice['actions'],cp['checkpoint_id'],cp['tick'],request_id,work_identity=actual_id)
   save(label+'/STEP.json',result)
   assert result['status']=='COMMITTED'
   after=env.observe_public();assert after['tick']==min(cp['tick']+20,env.end_tick)
   save(label+'/ACTUAL_FRAMES.json',env.frames[before_frames:]);save(label+'/ACTUAL_FUSIONS.json',env.fusions[before_fusions:]);save(label+'/AFTER.json',after);save(label+'/ACTUAL_SENSE.json',actual_sense.calls)
   assert after['previous_checkpoint_id']==cp['checkpoint_id']
   records.append(dict(cycle=step,start_tick=cp['tick'],end_tick=after['tick'],candidate_count=len(specs),selected=choice['selected_indices'],actions=choice['actions'],checkpoint=cp['checkpoint_id'],next_checkpoint=after['checkpoint_id']))
   print(mode,step,cp['tick'],after['tick'],len(specs),flush=True)
  save(mode+'/PRIVATE_SNAPSHOT.json',env.private_snapshot())
  assert env.observe_public()['phase']=='TERMINAL' and env.tick==env.end_tick
  index=dict(episode_id=RUN+'_'+mode,design_file=str((out/'DESIGN.json').resolve()),private_input_file=str((out/'SOURCE_INPUT.json').resolve()),initial_artifacts=dict(public_checkpoint=str((out/mode/'INITIAL_CHECKPOINT.json').resolve())),decisions=index_rows,final_artifacts=dict(private_snapshot=str((out/mode/'PRIVATE_SNAPSHOT.json').resolve())))
  save(mode+'/EPISODE_INDEX.json',index)
  audit_dir=out/mode/'EPISODE_AUDIT';audit_dir.mkdir()
  audit_episode(dict(episode_index_file=str((out/mode/'EPISODE_INDEX.json').resolve())),audit_dir)
  save(mode+'/ACTUAL_SENSE_SUMMARY.json',dict(wls=actual_sense.wls,calls=actual_sense.calls,registrations=actual_sense.registrations));save(mode+'/FINAL_METRICS.json',env.metrics());save(mode+'/FINAL_CHECKPOINT.json',env.observe_public());save(mode+'/EVENTS.json',env.private_snapshot()['state']['events'])
  summary.append(dict(method=mode,cycles=records,terminal=env.observe_public()['phase']=='TERMINAL',final_tick=env.observe_public()['tick']))
 save('RESULT.json',dict(status='PASS_FULL_EPISODE_AND_INDEPENDENT_AUDIT',runs=summary,counts=counts))
except BaseException as e:
 save('FAILURE.json',dict(stage=stage,error=repr(e),traceback=traceback.format_exc(),counts=counts));raise
finally:save('COUNTS.json',counts)
