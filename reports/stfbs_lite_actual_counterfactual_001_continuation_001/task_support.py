import pathlib,json,hashlib,math
REPO=pathlib.Path(r'D:\1st\dynamic_member_coalition_core')
ROOT=pathlib.Path(__file__).resolve().parent
TASK='STFBS_LITE_ACTUAL_COUNTERFACTUAL_001'
EPS=1e-8
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def save(name,x):
 with (ROOT/name).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,sort_keys=True,allow_nan=False)
def same(a,b):return json.loads(json.dumps(a))==json.loads(json.dumps(b))
G0_PHASE = "FAILED_BEFORE_RECOVERY"
def prepare():
 global G0_PHASE
 from research.non_oracle.stfbs_lite_archive_root import bind_actual_archive
 from research.non_oracle.stfbs_lite_actual_recovery import recover_actual_cut
 G0_PHASE='RECOVERY_FAILED'
 bound=bind_actual_archive(REPO);recovered=recover_actual_cut(bound,60)
 need(recovered['status']=='ARCHIVED_ACTUAL_CUT_RECONSTRUCTION_PASS','D60_RECOVERY_FAILED/'+str(recovered.get('reason')))
 G0_PHASE='STATE_EQUIVALENCE_FAILED'
 cut=recovered['cut'].to_dict()
 a=read(ROOT/'A_SWITCH_REPLAY/authorization.json');candidate=read(a['candidate_path'])['candidate'];view=candidate['a2_policy_view'];seed=candidate['consumer_seed']
 checks=dict(phase=cut['cut_phase']=='POST_FREEZE_PRE_ASSIGNMENT',public_view=same(cut['public_policy_view'],view),positions=same(cut['physical_cut_state']['positions'],view['positions']),assignment=same(cut['current_assignment'],view['assignment']),histories=same(list(cut['task_histories'].values()),view['histories']),current_slots=same(cut['current_slots'],view['current_slots']))
 pairs=[('consumer_states','internal_states_at_D60'),('accepted_position_history','accepted_position_history'),('pending_observations','pending_observations'),('consumed_records','consumed_records'),('accepted_receipts','accepted_receipts')]
 for x,y in pairs:checks[y]=same(cut[x],seed[y])
 need(digest(view)=='a37cde42a2c4c147f4abc9289e5de693790218d17bcafcbe7fe3cfb49a9d6602' and digest(seed)=='cf5ddd31c60ccfb87bbcd7fef2cb89ef24d5cd803983910fc585681bfde6f6f5','D60_SEMANTIC_DIGEST')
 clock=cut['service_clocks']['0'];progress=math.fsum([clock['base'],clock['intervals']*.05])
 checks['progress']=abs(progress-.6000000000000001)<=EPS
 save('D60_STATE_EQUIVALENCE.json',dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,progress_seconds=progress,semantic_mapping='Exact JSON-normalized public view and consumer state equality; integer/string object keys normalized only. No scientific fields removed.',archive_binding=cut['archive_binding'],historical_source_authentication='NOT_VERIFIED_ARCHIVAL_STUDY_ONLY'))
 need(all(checks.values()),'D60_STATE_NOT_EQUIVALENT')
 h=read(REPO/'runs/a2_switch_episode_001/R.json');prefix=read(REPO/'runs/a2_switch_episode_001/R_D40.json')['step']['metrics'];final=h['metrics']
 components={k:final['reward_components'][k]-prefix['reward_components'][k] for k in prefix['reward_components']}
 cost=final['change_cost']-prefix['change_cost'];net=final['return_with_changes']-prefix['return_with_changes']
 need(abs(net-(sum(components.values())-cost))<=EPS,'HISTORICAL_LEDGER_ARITHMETIC')
 guard=read(REPO/'reports/a2_switch_episode_001_guard/PHYSICAL_RECHECK.json')['R']
 need(all(abs(sum(x[k] for x in guard['ledger'])-final['reward_components'][k])<=EPS for k in components),'HISTORICAL_PHYSICAL_LEDGER')
 boundaries=[]
 for t in [60,80,100]:
  cp=read(REPO/('runs/a2_switch_episode_001/R_D%d.json'%t));before=cp['policy_input']['assignment'];after=cp['step']['action_commit']['assignment'];count=sum(x!=y for x,y in zip(before,after))
  need(count==cp['step']['action_commit']['assignment_change_count'],'HISTORICAL_CHARGE_COUNT')
  boundaries.append(dict(tick=t,before=before,after=after,changes=count,cost=cp['step']['action_commit']['change_cost']))
 n=final['assignment_changes']-prefix['assignment_changes']
 need(sum(b['changes'] for b in boundaries)==n and abs(sum(b['cost'] for b in boundaries)-cost)<=EPS,'HISTORICAL_BOUNDARY_TOTAL')
 save('HISTORICAL_ACTUAL_VALUE_LEDGER.json',dict(task_id=TASK,version='V1.2',horizon=[60,120],prefix=prefix,final=final,components=components,change_cost=cost,net=net,N_change=n,boundaries=boundaries,source_sha256={str(REPO/p):sha(REPO/p) for p in ['runs/a2_switch_episode_001/R.json','runs/a2_switch_episode_001/R_D40.json','reports/a2_switch_episode_001_guard/PHYSICAL_RECHECK.json']},calculation='final minus D60 pre-assignment settled prefix'))
 actual=read(REPO/'runs/a2_switch_episode_001/WORLD_INPUT.json')
 need(actual['config']['step_dt']==.05 and actual['config']['change_cost']==.01 and same(actual['config'],view['config']),'HISTORICAL_CONFIG')
 need(actual['measurement_model']['kind']=='planar_bearing' and actual['measurement_model']['angle_perturbation']==0 and all(p['sigma']==.02 and p['health']=='available' for row in actual['sensor_declaration_schedule'] for p in row['profiles']),'SENSOR_RULE')
 motion={}
 for target in actual['targets']:
  need(not target['turns'] and target['turn_increment']==0 and all(row[1]==0 for row in target['arc_rates']),'NONCONSTANT_ACTUAL_MOTION')
  j=str(target['id']);motion[j]=dict(position=[p+v*(3-target['birth']) for p,v in zip(target['position_at_birth'],target['velocity'])],velocity=target['velocity'])
 candidates=read(REPO/'reports/stfbs_lite_h2_h3_extension_005/CANDIDATE_FREEZE.json')
 for row in read(ROOT/'BRANCH_EXECUTION_INDEX.json'):
  frozen=next(c for c in candidates if c['kind']==row['action'])
  need(row['initial_actions']==frozen['actions'],'FROZEN_CANDIDATE_ACTION')
  roles={'none':0,'dual_neg45':1,'dual_pos45':2}
  need([[(-1 if a['target'] is None else a['target']),roles[a['role']]] for a in row['initial_actions']]==frozen['assignment_key'],'FROZEN_ASSIGNMENT_KEY')
 world=read(ROOT/'A_SWITCH_REPLAY/authorization.json')['world']
 need(same(motion,world['motion']) and world['world_digest']==digest({k:v for k,v in world.items() if k!='world_digest'}),'HISTORICAL_WORLD_BINDING')
 save('HISTORICAL_WORLD_BINDING.json',dict(task_id=TASK,version='V1.2',status='PASS',purpose='OFFLINE_HISTORICAL_COUNTERFACTUAL',world=world,source=str(REPO/'runs/a2_switch_episode_001/WORLD_INPUT.json'),sha256=sha(REPO/'runs/a2_switch_episode_001/WORLD_INPUT.json'),target_motion_rule='birth position + velocity * (time-birth); no turns or arc rates',sensor_rules=actual['measurement_model'],execution_change_cost=.01))
 save('SWITCH_REFERENCE_ADMISSION.json',dict(reference_mode='MODEL_SWITCH_REPLAY_REQUIRED',reason='No direct complete historical/current executor dynamic-equivalence evidence; use single authorized calibration',frozen_before_any_branch=True,attempt_id='ACF001_SWITCH_001'))
 G0_PHASE='PASS'
 return dict(status='PASS',reference_mode='MODEL_SWITCH_REPLAY_REQUIRED',cut_phase=cut['cut_phase'],historical_progress=progress,checks=checks)

IDENTITY_FIELDS={'branch','branch_id','model_branch_id','stream_id','frame_id','packet_id','segment_id','active_segment_id','previous_segment_id','source_kind','provenance','observation_origin','payload_digest','payload_sha256','frame_sha256','endpoint_digest','history_digest','slot_digest','flow_context','flow_registration'}
def scientific(x):
 if isinstance(x,dict):
  if {'tick','target_id','team','G','quality'}<=set(x):
   return dict(tick=x['tick'],target_id=x['target_id'],team=scientific(x['team']),G=x['G'],quality={k:x['quality'][k] for k in ['contract_id','status','radius_proxy']})
  return {str(k):scientific(v) for k,v in x.items() if k not in IDENTITY_FIELDS and not k.endswith('_digest')}
 if isinstance(x,list):return [scientific(v) for v in x]
 return x
def replay_compare(directory):
 directory=pathlib.Path(directory);raw=read(directory/'BRANCH_RAW.json');terminal=read(directory/'TERMINAL_BRANCH_HISTORY.json')
 reports=[];mismatches=[];maximum=0.
 def compare(name,a,b):
  local=[];mx=0.
  def walk(x,y,p):
   nonlocal mx,maximum
   if isinstance(x,(int,float)) and not isinstance(x,bool) and isinstance(y,(int,float)) and not isinstance(y,bool):
    delta=abs(x-y);mx=max(mx,delta);maximum=max(maximum,delta)
    if not math.isfinite(delta) or delta>EPS:local.append(dict(path=p,left=x,right=y,absolute_difference=delta))
   elif isinstance(x,dict) and isinstance(y,dict):
    if set(x)!=set(y):local.append(dict(path=p,key_difference=[sorted(set(x)-set(y)),sorted(set(y)-set(x))]))
    for k in x.keys()&y.keys():walk(x[k],y[k],p+'/'+str(k))
   elif isinstance(x,list) and isinstance(y,list):
    if len(x)!=len(y):local.append(dict(path=p,lengths=[len(x),len(y)]))
    for i,(xx,yy) in enumerate(zip(x,y)):walk(xx,yy,p+'/'+str(i))
   elif x!=y:local.append(dict(path=p,left=x,right=y))
  walk(a,b,'');reports.append(dict(item=name,status='PASS' if not local else 'FAIL',maximum_absolute_difference=mx,mismatch_count=len(local)))
  mismatches.extend(dict(item=name,**e) for e in local[:20])
 records=[read(REPO/('runs/a2_switch_episode_001/R_D%d.json'%t)) for t in [60,80,100]]
 frames=[f for rec in records for f in rec['step']['frames'] if f['phase']=='physical']
 compare('frame_ticks',[f['tick'] for f in frames],[f['tick'] for f in raw['frames']])
 for a,b in zip(frames,raw['frames']):
  t=a['tick']
  for hk,mk in [('positions_start','before'),('positions','positions'),('control','control'),('control_elapsed_by_robot','elapsed'),('assignment','assignment')]:compare('physics/%d/%s'%(t,hk),a[hk],b[mk])
  compare('statuses/%d'%t,{str(i):s for i,s in enumerate(a['statuses'])},b['status'])
  if t<120:
   progress={j:0. if c is None else math.fsum([c['base'],c['intervals']*.05]) for j,c in b['clocks'].items()}
   compare('service_clock/%d'%t,a['progress'],progress)
 for rec,b in zip(records,raw['boundaries']):
  c=rec['step']['action_commit'];compare('assignment_boundary/%d'%b['tick'],dict(tick=c['start_tick'],before=rec['policy_input']['assignment'],after=c['assignment'],changes=c['assignment_change_count'],cost=c['change_cost']),b)
 history_fusions=[f for rec in records for f in rec['step']['fusion_records']]
 compare('fusion_order',[(f['frame']['tick'],f['frame']['target_id']) for f in history_fusions],[(f['frame']['tick'],f['frame']['target_id']) for f in raw['feedback']])
 for i,(a,b) in enumerate(zip(history_fusions,raw['feedback'])):
  compare('observation/%d/frame'%i,scientific(a['frame']),scientific(b['frame']))
  for k in ['estimate_result','quality','valid_sensor_count','excluded_records','duplicate_record_count','missing_sensor_ids','skipped','estimator_called','duplicate']:
   compare('observation/%d/%s'%(i,k),scientific(a['result'][k]),scientific(b['result'][k]))
  compare('service_endpoint/%d'%i,scientific(a['actual_endpoint']),scientific(b['endpoint']))
 for rec,dec in zip(records[1:],raw['decisions']):
  compare('decision/%d/actions'%rec['policy_input']['tick'],rec['choice']['actions'],dec['choice']['actions'])
  compare('decision/%d/beliefs'%rec['policy_input']['tick'],scientific(rec['policy_input']['beliefs']),scientific(dec['view']['beliefs']))
  compare('decision/%d/sensor_profiles'%rec['policy_input']['tick'],rec['policy_input']['sensor_profiles'],dec['view']['sensor_profiles'])
 # Terminal histories compare all scientific event/clock/segment/endpoint fields; identities documented above.
 historical=read(REPO/'runs/a2_switch_episode_001/R.json')['final']['state']['histories']

 def history_semantics(histories):
  def event(e):
   return dict(kind='EPISODE_END' if e['kind']=='EPISODE_ENDED' else e['kind'],target=e['target_id'],at=e['at'],progress_before=e['progress_before'],progress_after=e['progress_after'])
  def segment(z):
   close=z['closure']
   return dict(target=z['target_id'],segment_index=z['segment_index'],start_tick=z['start_tick'],team=z['team'],opened_by='INITIAL_ASSIGNMENT' if z['opened_by']=='FIRST_ASSIGNMENT' else z['opened_by'],initial_clock=z['initial_clock'],latest_clock=z['latest_clock'],latest_endpoint=scientific(z['latest_endpoint']),closure=None if close is None else dict(reason='EPISODE_END' if close['reason']=='EPISODE_ENDED' else close['reason'],at=close['at']),events=[event(e) for e in z['events'] if e['kind']!='INTERRUPTED'])
  return {j:dict(target_id=h['target_id'],birth_tick=h['birth_tick'],cutoff_tick=h['cutoff_tick'],segments=[segment(z) for z in h['segments']],unassigned_intervals=[{k:v for k,v in z.items() if k not in ['opening_event_index','closing_event_index']} for z in h['unassigned_intervals']],events=[event(e) for e in h['events'] if e['kind']!='INTERRUPTED']) for j,h in histories.items()}
 compare('terminal_histories',history_semantics(historical),history_semantics(terminal['histories']))
 oldresets=[dict(target=int(j),tick=e['at']['event_tick'],time=e['at']['time_seconds'],progress_before=e['progress_before'],progress_after=e['progress_after'],reasons=e['reasons']) for j,hist in historical.items() for e in hist['events'] if e['kind']=='INTERRUPTED' and e['at']['event_tick']>60]
 newresets=[]
 for e in raw['events']:
  if e['kind']!='reset':continue
  candidates=[f['endpoint'] for f in raw['feedback'] if f['endpoint']['target_id']==e['target'] and f['endpoint']['tick'] in [e['tick']-1,e['tick']]]
  reasons=[]
  if any(not f['G'] for f in candidates):reasons.append('GEOMETRY_INVALID')
  if any(f['quality']['status']!='PASS' for f in candidates):reasons.append('QUALITY_INVALID')
  newresets.append(dict(target=e['target'],tick=e['tick'],time=e['time'],progress_before=e['progress_before'],progress_after=0.,reasons=reasons))
 compare('service_reset_events',oldresets,newresets)
 trace=read(REPO/'reports/a2_switch_episode_001_guard/PHYSICAL_RECHECK.json')['R']['trace']
 for step in trace:
  if step['phase']!='physical' or not 60<step['tick']<=120:continue
  for j,ep in step['endpoints'].items():
   motion=raw['world']['motion'][str(j)]
   position=[p+v*((step['tick']-60)*.05) for p,v in zip(motion['position'],motion['velocity'])]
   compare('target_position/%d/%s'%(step['tick'],j),ep['target_position'],position)

 h=read(ROOT/'HISTORICAL_ACTUAL_VALUE_LEDGER.json')
 compare('economic_components',h['components'],raw['components']);compare('change_cost',h['change_cost'],raw['change_cost']);compare('net',h['net'],raw['net'])
 final=read(REPO/'runs/a2_switch_episode_001/R.json')
 compare('consumed_timing',[(x['target_id'],x['measurement_tick'],x['available_tick'],x['consumed_tick']) for x in final['observations_consumed'] if x['consumed_tick']>60],[(x['target_id'],x['measurement_tick'],x['available_tick'],x['consumed_tick']) for x in terminal['consumed'] if x['consumed_tick']>60])
 result=dict(status='SWITCH_REPLAY_EQUIVALENCE_PASS_CANDIDATE' if not mismatches else 'FAIL',absolute_tolerance=EPS,relative_tolerance=0,comparisons=reports,mismatch_count=sum(x['mismatch_count'] for x in reports),mismatches=mismatches,maximum_absolute_difference=maximum,historical_value=h['net'],model_value=raw['net'],model_minus_historical=raw['net']-h['net'],identity_alignment=dict(removed_identity_only_fields=sorted(IDENTITY_FIELDS),endpoint_alignment='tick,target,team,G,quality contract/status/radius; actual slots separately matched through frame packets',internal_integrity='historical bound archive + recovery; MODEL full scientific and credential audits'),scientific_fields_not_silently_discarded=True,history_schema_mapping='Operational segment/event identities and redundant contract labels mapped; FIRST_ASSIGNMENT=INITIAL_ASSIGNMENT, EPISODE_ENDED=EPISODE_END; reset events join MODEL raw.events with endpoint-derived G/Q reasons against historical INTERRUPTED events; indices are archive ordinals, not scientific state; all times/progress/teams/closures compared')
 save('SWITCH_REPLAY_EQUIVALENCE.json',result)
 need(not mismatches,'SWITCH_DYNAMIC_EQUIVALENCE_FAILED')
 return result
