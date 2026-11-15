from pathlib import Path
import sys,time,json,hashlib,copy,math,traceback,importlib.util
from fractions import Fraction
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2];sys.path.insert(0,str(REPO))
START=time.monotonic();CPU=time.process_time();WRITES=0
counts=dict(PREFIX_RUNS_STARTED=0,MODEL_CELLS_STARTED=0,MODEL_CELLS_VALID=0,ACTUAL_RUNS_STARTED=0,ACTUAL_RUNS_VALID=0,ANALYTIC_ESTIMATE_CALLS=0,MODEL_OBSERVATION_WLS_CALLS=0,ACTUAL_WLS_CALLS=0,POLICY_EVALUATION_WLS_CALLS=0,NONLINEAR_SOLVER_STARTS=0,R_CALLS=0,ASSIGNMENT_OPTIMIZATION_CALLS=0)
counts.update(ACTUAL_PREFIX_RECONSTRUCTIONS_STARTED=0,RCV_SCORES_STARTED=0,RCV_SCORES_VALID=0,RCV_WLS_CALLS=0)
phase='IMPLEMENTATION';results={};matched={};stage_counts={}
def check():
 if time.process_time()-CPU>2350 or time.monotonic()-START>5300 or WRITES>2100000000:raise RuntimeError('JOINT_RESOURCE_STOP')
def save(name,data):
 global WRITES
 raw=(json.dumps(data,ensure_ascii=False,allow_nan=False,default=lambda x:x.item(),indent=2)+'\n').encode();check();p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);WRITES+=len(raw)
def cp(x):return copy.deepcopy(x)
def identity(a):return tuple((-1 if x['target'] is None else x['target'],x['role']) for x in a)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def require(v,msg):
 if not v:raise RuntimeError(msg)
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def run():
 global phase
 import numpy as np
 from scripts.run_a1 import Sensing
 from research.non_oracle.environment import StaggeredEnvironment
 from research.non_oracle import policy
 from research.non_oracle.stfbs_d1a_model import Branch
 from research.non_oracle.stfbs_d1a_replay import digest as mdigest
 from research.non_oracle.stfbs_lite_live_cut import capture_live_cut
 from research.non_oracle.stfbs_lite_real_cut_to_model import prepare_real_cut_model_input
 from research.information_service_bridge import public_stream
 from research.cooperative_sensing import estimator
 from scripts.gq_windows.a0_plans import plans
 from pursuit_v2.observation_geometry import offset,radius
 from pursuit_v2.config import Config
 # Use frozen analytic estimator directly; no historical executable imported.
 path=REPO/'reports/stfbs_lite_fb_blvf_initial_validation_001/blvf.py'
 require(hashlib.sha256(path.read_bytes()).hexdigest()=='204fc231bf78004c33daf151983d751685666da75ed9e9b911abb83854c7365e','BLVF_IDENTITY')
 spec=importlib.util.spec_from_file_location('ccvd_frozen_blvf',path);analytic=importlib.util.module_from_spec(spec);spec.loader.exec_module(analytic)
 original_est=estimator.estimate;original_solver=estimator.least_squares;original_solve=policy.solve
 def wls(payload):
  check();counts['RCV_WLS_CALLS' if phase=='RCV' else 'POLICY_EVALUATION_WLS_CALLS' if phase=='R' else 'ACTUAL_WLS_CALLS']+=1;return original_est(payload)
 def solver(*a,**k):check();counts['NONLINEAR_SOLVER_STARTS']+=1;return original_solver(*a,**k)
 def solve(*a,**k):counts['ASSIGNMENT_OPTIMIZATION_CALLS']+=1;return original_solve(*a,**k)
 def decide(view):
  counts['R_CALLS']+=1;before=mdigest(view);d=policy.decide(view,'R');require(before==mdigest(view),'PUBLIC_INPUT_MUTATED');return d
 class Budget:
  def check(self):check()
  def estimator(self,kind):
   def call(payload):check();counts['ANALYTIC_ESTIMATE_CALLS']+=1;return analytic.estimate(payload)
   return call
 world=load(REPO/'runs/a2_switch_episode_001/WORLD_INPUT.json');world['config']['change_cost']=0.;public=load(REPO/'runs/a2_switch_episode_001/PUBLIC_INPUT.json')
 cases={}
 for label in ('I','II'):
  physical=cp(world);ann=cp(public)
  physical['positions_initial']=([[8.874264,9.575736],[8.874264,10.424264],[9.6,9.6]] if label=='I' else [[6.874264,9.575736],[8.874264,10.424264],[9.6,9.6]])
  ann['announcements'][0]['coarse_position']=[8.45,10.]
  ann['announcements'][1]['coarse_position']=[9.45,10.] if label=='I' else [9.8,10.3]
  physical['targets'][1]['position_at_birth']=[9.,10.] if label=='I' else [9.8,10.1]
  physical['targets'][1]['velocity']=[.6,0.] if label=='I' else [.8*math.cos(.25),.8*math.sin(.25)]
  cases[label]=dict(physical=physical,public=ann)
 save('EXPERIMENT_CONFIG.json',dict(cases=cases,reference_speeds=[0.,.4],reference_heading=0.,limits=dict(prefix=2,model=12,rcv=6,actual=8)))
 def step(env,actions,tag):
  check();c=env.observe_public();r=env.step(cp(actions),c['checkpoint_id'],env.tick,tag);require(r['status']=='COMMITTED','STEP_NOT_COMMITTED');return r
 def prefix(label,physical,name):
  global phase
  env=StaggeredEnvironment(cp(physical),Sensing(),name,cp(cases[label]['public']['announcements']));records=[]
  for tick in (0,20,40):
   view=env.prepare_decision();require(view['tick']==tick,'PREFIX_TICK')
   d=None;a=[dict(target=None,role='none') for _ in range(3)] if tick==0 or not any(t['id']==0 for t in view['targets']) else [dict(target=0,role='dual_neg45'),dict(target=0,role='dual_pos45'),dict(target=None,role='none')]
   phase='PREFIX_ACTUAL';records.append(dict(view=view,decision=d,step=step(env,a,name+str(tick))))
  view=env.prepare_decision();return env,view,records
 def model(label,key,view,seed,motion,action):
  global phase
  check();require(counts['MODEL_CELLS_STARTED']<12,'MODEL_LIMIT');counts['MODEL_CELLS_STARTED']+=1;phase='MODEL'
  w=dict(public_digest=mdigest(view),motion=cp(motion),start_tick=60,end_tick=120,motion_rule='CCVD_CV',provenance='SIMULATED',observation_origin='MODEL');w['world_digest']=mdigest(w)
  b=Branch(cp(view),cp(seed),w,label+'_'+key,Budget());b.assign(cp(action))
  while b.tick<120:
   b.advance()
   if b.tick in (80,100):
    v=b.policy_view();b.decisions.append(dict(mode='HOLD',view=cp(v)));b.assign(cp(b.actions));require(b.boundaries[-1]['changes']==0,'MODEL_HOLD_CHANGED')
  raw=dict(world=w,components=b.components,net=sum(b.components.values())-b.change_cost,change_cost=b.change_cost,frames=b.frames,events=b.events,feedback=b.feedback,decisions=b.decisions,boundaries=b.boundaries,status=b.status)
  save(label+'/'+key+'_RAW.json',raw);counts['MODEL_CELLS_VALID']+=1;return raw
 with patch.object(policy,'estimate',wls),patch.object(public_stream,'_estimate',wls),patch.object(estimator,'least_squares',solver),patch.object(policy,'solve',solve):
  for label in ('I','II'):
   check();physical=cp(cases[label]['physical'])
   counts['PREFIX_RUNS_STARTED']+=1;env,view,records=prefix(label,physical,label+'_PREFIX');save(label+'/PUBLIC_D60.json',view);save(label+'/PREFIX_RECEIPT.json',dict(metrics=env.metrics(),records=records))
   # Structural capture and whitelist mapping do not admit arbitrary production execution.
   cut=capture_live_cut(env,view);mapped=prepare_real_cut_model_input(cut);save(label+'/MAPPING_RECEIPT.json',dict(status=mapped['status'],candidate_status=mapped['candidate_status']))
   require(mapped['status']=='REAL_CUT_TO_MODEL_SCHEMA_MAPPING_PASS','LOCAL_MAPPING_FAILED')
   seed=mapped['candidate']['consumer_seed'];require(view==mapped['candidate']['a2_policy_view'],'MAPPED_PUBLIC_DIFFERENCE')
   phase='R';r=decide(view);table=plans(view,[x['key'] for x in r['rows']],r['rows']);save(label+'/R_CATALOGUE.json',dict(result=r,plans=table))
   K=cp(view['assignment']);active=[t['id'] for t in view['targets']];teams={j:{i for i,a in enumerate(K) if a['target']==j} for j in active};current=next((j for j,s in teams.items() if len(s)==2),None)
   if current is None:results[label]=dict(status='NO_LEGAL_KEEP');continue
   team=teams[current];candidates={'K':K}
   for kind in ('S','M'):
    pool=[]
    for p in table:
     groups={j:{i for i,a in enumerate(p['actions']) if a['target']==j} for j in active}
     good=any(j!=current and ids==team for j,ids in groups.items()) if kind=='S' else len(groups[current])==2 and groups[current]!=team
     if good:pool.append(p)
    if pool:candidates[kind]=cp(sorted(pool,key=lambda p:(-Fraction(p['exact_value']),identity(p['actions'])))[0]['actions'])
   common=sorted((p for p in table if any(p['actions']==a for a in candidates.values())),key=lambda p:(-Fraction(p['exact_value']),identity(p['actions'])))[0]['actions']
   save(label+'/CANDIDATES.json',dict(candidates=candidates,R=r['actions'],R_common=common))
   # T0 witness from accepted public history, verified against every saved raw bearing and G endpoint.
   hist=seed['accepted_position_history'].get(0,[]);require(len(hist)>1,'T0_CV_WITNESS_MISSING');kb,pb=hist[-1];ka,pa=next((k,p) for k,p in reversed(hist[:-1]) if kb-k>=5);v0=(np.array(pb)-pa)/((kb-ka)*.05);p0=np.array(pb)+v0*((60-kb)*.05)
   ann=next(a for a in cases[label]['public']['announcements'] if a['id']==0);birthpos=p0-v0*3.;require(np.linalg.norm(birthpos-ann['coarse_position'])<=ann['design_error_bound']+1e-10 and np.linalg.norm(v0)<=ann['speed_limit']+1e-10,'WITNESS_PUBLIC_SUPPORT')
   cfg=Config(**view['config']);checked=0
   for f in [fusion for rec in records for fusion in rec['step']['fusion_records']]:
    if f['frame']['target_id']!=0:continue
    tick=f['frame']['tick'];point=p0+v0*((tick-60)*.05)
    for packet in f['frame']['records']:
     delta=point-np.array(packet['position']);err=(math.atan2(delta[1],delta[0])-packet['bearing']+math.pi)%(2*math.pi)-math.pi;require(abs(err)<=1e-10,'WITNESS_BEARING_INCOMPATIBLE');checked+=1
    ep=f['actual_endpoint'];g=all(np.linalg.norm(np.array(next(p['position'] for p in f['frame']['records'] if p['sensor_id']=='U'+str(m['robot_id'])))-point-offset(m['role'],cfg))<=radius(cfg) for m in ep['team']);require(g==ep['G'],'WITNESS_G_INCOMPATIBLE')
   save(label+'/WITNESS.json',dict(position=p0.tolist(),velocity=v0.tolist(),bearing_checks=checked,conditions='public birth support, speed, all sampled bearings and G endpoints; inherited service history remains unchanged',not_established='unqueried observations; general historical inverse solution'))
   worlds={w:{0:dict(position=p0.tolist(),velocity=v0.tolist()),1:dict(position=cp(next(t for t in view['targets'] if t['id']==1)['coarse_position']),velocity=[speed,0.])} for w,speed in [('W0',0.),('W1',.4)]};save(label+'/WORLDS.json',worlds)
   matrix={a:{} for a in candidates}
   for a,actions in candidates.items():
    for w,motion in worlds.items():matrix[a][w]=model(label,a+'_'+w,view,seed,motion,actions)['net']
   # R-CV only scores frozen representatives, using W1 public reference trajectory.
   rcv={};original_trajectory=policy.trajectory
   def reference_trajectory(belief,tick):
    m=worlds['W1'][belief['target_id']];return [p+(tick-60)*.05*v for p,v in zip(m['position'],m['velocity'])],list(m['velocity'])
   from research.information_service_online.evaluator import components
   baseline={t['id']:sum(components(view['config'],t,3.,6.,False,0.,6.).values()) for t in view['targets']}
   require(all(m['position'][0]+max(0.,m['velocity'][0])*3.<view['config']['side'] for m in worlds['W1'].values()),'RCV_BASELINE_ESCAPE_NOT_SUPPORTED')
   phase='RCV'
   with patch.object(policy,'trajectory',reference_trajectory):
    for a,actions in candidates.items():
     counts['RCV_SCORES_STARTED']+=1;require(counts['RCV_SCORES_STARTED']<=6,'RCV_LIMIT')
     j=next(x['target'] for x in actions if x['target'] is not None);key=dict(target=j,robots=[i for i,x in enumerate(actions) if x['target']==j],roles=[x['role'] for x in actions if x['target']==j])
     row=policy.evaluate(view,key);rcv[a]=dict(net=row['absolute_O']+sum(v for k,v in baseline.items() if k!=j),score=row);counts['RCV_SCORES_VALID']+=1
   require(policy.trajectory is original_trajectory,'TRAJECTORY_NOT_RESTORED')
   save(label+'/R_CV_VALUES.json',rcv)
   best=lambda w:sorted(candidates,key=lambda a:(-matrix[a][w],identity(candidates[a])))[0]
   choices=dict(N0=best('W0'),N1=best('W1'),RCV=sorted(candidates,key=lambda a:(-rcv[a]['net'],identity(candidates[a])))[0],K='K')
   save(label+'/MODEL_VALUES.json',matrix);save(label+'/DECISION_FREEZE.json',dict(public_digest=mdigest(view),candidates=candidates,worlds=worlds,values=matrix,rcv={a:r['net'] for a,r in rcv.items()},choices=choices,R=r['actions'],R_common=common))
   actual_actions=cp(candidates)
   if not any(a==r['actions'] for a in candidates.values()):actual_actions['R_EXTRA']=r['actions']
   actual={};prefix_digest=mdigest(view)
   for a,actions in actual_actions.items():
    check();counts['ACTUAL_PREFIX_RECONSTRUCTIONS_STARTED']+=1;counts['ACTUAL_RUNS_STARTED']+=1;require(counts['ACTUAL_RUNS_STARTED']<=8,'ACTUAL_LIMIT');e,v,recs=prefix(label,physical,label+'_'+a);require(mdigest(v)==prefix_digest,'COMMON_PUBLIC_PREFIX_DIFFERENCE');require(e.metrics()==env.metrics(),'COMMON_PREFIX_ECONOMICS_DIFFERENCE');prefix_metrics=cp(e.metrics());phase='ACTUAL_HOLD'
    for tick in (60,80,100):
     if tick!=60:v=e.prepare_decision()
     hold=actions if tick==60 else v['assignment'];recs.append(dict(view=v,step=step(e,hold,label+'_'+a+str(tick))))
    met=e.metrics();comps={k:met['reward_components'][k]-prefix_metrics['reward_components'][k] for k in met['reward_components']};value=met['return_with_changes']-prefix_metrics['return_with_changes'];require(abs(sum(comps.values())-value)<1e-8,'ECONOMIC_RECONCILIATION')
    actual[a]=dict(net=value,components=comps,completion_times=e.private_snapshot()['state']['completion_times']);save(label+'/ACTUAL_'+a+'_RAW.json',dict(records=recs,final=e.private_snapshot(),metrics=met,observations_consumed=e.beliefs.consumed));counts['ACTUAL_RUNS_VALID']+=1
   save(label+'/ACTUAL_VALUES.json',actual);results[label]=dict(status='COMPLETED',matrix=matrix,rcv={a:x['net'] for a,x in rcv.items()},choices=choices,actual=actual,candidates=candidates,R=r['actions'],R_common=common)
 save('SCIENTIFIC_ANALYSIS.json',results)

if __name__=='__main__':
 status='COMPLETED';error=None
 try:
  from research.information_service_online import public as schema_public
  original_schema=schema_public.SCHEMA
  local_schema=cp(original_schema)
  local_schema['$defs']['Config']['properties']['change_cost']={'const':0.0}
  require(original_schema['$defs']['Config']['properties']['change_cost']=={'const':0.01},'ORIGINAL_SCHEMA_CHANGED')
  verify=cp(local_schema);verify['$defs']['Config']['properties']['change_cost']={'const':0.01}
  require(verify==original_schema,'UNEXPECTED_SCHEMA_DIFF')
  with patch.object(schema_public,'SCHEMA',local_schema):
   config=load(REPO/'runs/a2_switch_episode_001/WORLD_INPUT.json')['config'];config['change_cost']=0.
   schema_public.validate_schema(config,'Config')
   rejected=[]
   for cost in (.01,-.01,.1):
    bad=cp(config);bad['change_cost']=cost
    try:schema_public.validate_schema(bad,'Config')
    except Exception:rejected.append(cost)
   require(len(rejected)==3,'LOCAL_SCHEMA_NOT_STRICT')
   bad=cp(config);bad['robots']=99
   try:schema_public.validate_schema(bad,'Config');raise RuntimeError('OTHER_CONSTRAINT_DISABLED')
   except schema_public.ContractError:pass
   save('SCHEMA_ADAPTATION.json',dict(identity='N1_ATTEMPT_001_ECON_NOC_RESEARCH_ONLY',original_digest=digest(original_schema),local_digest=digest(local_schema),diff={'/$defs/Config/properties/change_cost/const':[.01,0.]},rejected_costs=rejected,other_constraint_rejected=True,scope='public.SCHEMA patched for complete run; all validators retain original functions'))
   run()
  require(schema_public.SCHEMA is original_schema,'SCHEMA_NOT_RESTORED')
 except BaseException as exc:status='BLOCKED';error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());save('FAILURE.json',error)
 finally:
  save('EXECUTION_STATUS.json',dict(status=status,phase=phase,counts=counts,error=error,results=results))
  save('RESOURCE_RECEIPT.json',dict(CPU_SECONDS=time.process_time()-CPU,WALL_SECONDS=time.monotonic()-START,CONTROLLED_LOGICAL_WRITE_BYTES=WRITES,counts=counts,RESOURCE_ACCOUNTING='PROCESS_CPU_AND_TASK_WRITER_ONLY',RESOURCE_COMPLIANCE='NOT_ESTABLISHED_FOR_PREPARATION_AND_NATIVE_CHILD_THREADS',retry=False))
 print(status,error,counts,flush=True)
