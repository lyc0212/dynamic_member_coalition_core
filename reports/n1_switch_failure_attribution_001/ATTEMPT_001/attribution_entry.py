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
 if time.process_time()-CPU>110 or time.monotonic()-START>850 or WRITES>125000000:raise RuntimeError('JOINT_RESOURCE_STOP')
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
 history=REPO/'reports/n1_independent_decision_validation_001/ATTEMPT_001'
 config=load(history/'EXPERIMENT_CONFIG.json');cases={'I':config['cases']['I']}
 save('INPUT_IDENTITY.json',dict(history=str(history),files={str(p.relative_to(history)):hashlib.sha256(p.read_bytes()).hexdigest() for p in history.rglob('*') if p.is_file()}))
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
  check();require(counts['MODEL_CELLS_STARTED']<1,'MODEL_LIMIT');counts['MODEL_CELLS_STARTED']+=1;phase='MODEL'
  w=dict(public_digest=mdigest(view),motion=cp(motion),start_tick=60,end_tick=120,motion_rule='CCVD_CV',provenance='SIMULATED',observation_origin='MODEL');w['world_digest']=mdigest(w)
  b=Branch(cp(view),cp(seed),w,label+'_'+key,Budget());b.assign(cp(action))
  while b.tick<120:
   b.advance()
   if b.tick in (80,100):
    v=b.policy_view();b.decisions.append(dict(mode='HOLD',view=cp(v)));b.assign(cp(b.actions));require(b.boundaries[-1]['changes']==0,'MODEL_HOLD_CHANGED')
  raw=dict(world=w,components=b.components,net=sum(b.components.values())-b.change_cost,change_cost=b.change_cost,frames=b.frames,events=b.events,feedback=b.feedback,decisions=b.decisions,boundaries=b.boundaries,status=b.status)
  save(label+'/'+key+'_RAW.json',raw);counts['MODEL_CELLS_VALID']+=1;return raw
 with patch.object(policy,'estimate',wls),patch.object(public_stream,'_estimate',wls),patch.object(estimator,'least_squares',solver),patch.object(policy,'solve',solve):
  label='I';physical=cp(cases[label]['physical'])
  # No separate complete D60 consumer seed is saved; do not fabricate one from PUBLIC_D60 or terminal state.
  counts['PREFIX_RUNS_STARTED']+=1;env,view,records=prefix(label,physical,'N1_ATTRIBUTION_PREFIX')
  frozen=load(history/'I/PUBLIC_D60.json');require(mdigest(view)==mdigest(frozen),'D60_PUBLIC_STATE_MISMATCH')
  oldprefix=load(history/'I/PREFIX_RECEIPT.json');require(env.metrics()==oldprefix['metrics'],'PREFIX_ECONOMIC_MISMATCH')
  cut=capture_live_cut(env,view);mapped=prepare_real_cut_model_input(cut);require(mapped['status']=='REAL_CUT_TO_MODEL_SCHEMA_MAPPING_PASS','MAPPING_FAILED')
  seed=mapped['candidate']['consumer_seed']
  require(view==mapped['candidate']['a2_policy_view'],'PUBLIC_MAPPING_MISMATCH')
  save('RECOVERED_CONSUMER_SEED.json',seed)
  save('STATE_RECOVERY_RECEIPT.json',dict(path='B',path_A='No standalone complete consumer seed; public state and receipt insufficient; terminal snapshots not used as D60 seeds',public_digest=mdigest(view),original_public_digest=mdigest(frozen),prefix_metrics=env.metrics(),mapping=mapped['status'],seed_digest=mdigest(seed),progress=.15,feedback_freeze='POST_FREEZE_PRE_ASSIGNMENT'))
  freeze=load(history/'I/DECISION_FREEZE.json');actions=freeze['candidates']['S'];require(actions==[dict(target=1,role='dual_neg45'),dict(target=1,role='dual_pos45'),dict(target=None,role='none')],'S_IDENTITY')
  motion={t['id']:dict(position=[t['position_at_birth'][i]+t['velocity'][i]*(3.-t['birth']) for i in range(2)],velocity=cp(t['velocity'])) for t in physical['targets']}
  save('MATCHED_WORLD.json',motion)
  raw=model('I','MATCHED_S',view,seed,motion,actions)
  actual=load(history/'I/ACTUAL_VALUES.json')['S'];old=load(history/'I/MODEL_VALUES.json');X=raw['net'];original=old['S']['W1'];J=actual['net'];total=J-original;world=X-original;residual=J-X
  require(abs(total-world-residual)<1e-10,'ATTRIBUTION_ARITHMETIC')
  results.update(X=X,V_original=original,J_actual=J,E_total=total,E_world=world,E_residual=residual,world_contribution_ratio=world/total,D_K=X-old['K']['W1'],D_M=X-old['M']['W1'],economics={k:dict(model=v,actual=actual['components'][k],residual=actual['components'][k]-v) for k,v in raw['components'].items()},change_cost=raw['change_cost'],events=raw['events'])
  save('ATTRIBUTION_ANALYSIS.json',results)
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
   save('SCHEMA_ADAPTATION.json',dict(identity='N1_ATTRIBUTION_ATTEMPT_001_ECON_NOC_RESEARCH_ONLY',original_digest=digest(original_schema),local_digest=digest(local_schema),diff={'/$defs/Config/properties/change_cost/const':[.01,0.]},rejected_costs=rejected,other_constraint_rejected=True,scope='public.SCHEMA patched for complete run; all validators retain original functions'))
   run()
  require(schema_public.SCHEMA is original_schema,'SCHEMA_NOT_RESTORED')
 except BaseException as exc:status='BLOCKED';error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());save('FAILURE.json',error)
 finally:
  save('EXECUTION_STATUS.json',dict(status=status,phase=phase,counts=counts,error=error,results=results))
  save('RESOURCE_RECEIPT.json',dict(CPU_SECONDS=time.process_time()-CPU,WALL_SECONDS=time.monotonic()-START,CONTROLLED_LOGICAL_WRITE_BYTES=WRITES,counts=counts,RESOURCE_ACCOUNTING='PROCESS_CPU_AND_TASK_WRITER_ONLY',RESOURCE_COMPLIANCE='NOT_ESTABLISHED_FOR_PREPARATION_AND_NATIVE_CHILD_THREADS',retry=False))
 print(status,error,counts,flush=True)
