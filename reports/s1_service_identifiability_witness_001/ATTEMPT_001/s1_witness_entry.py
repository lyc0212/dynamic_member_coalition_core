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
 from research.non_oracle.stfbs_d1a_replay import digest as mdigest
 from research.information_service_bridge import public_stream
 from research.cooperative_sensing import estimator
 from scripts.gq_windows.a0_plans import plans
 from pursuit_v2.observation_geometry import offset,radius
 from pursuit_v2.config import Config
 original_est=estimator.estimate;original_solver=estimator.least_squares;original_solve=policy.solve
 def wls(payload):
  check();counts['RCV_WLS_CALLS' if phase=='RCV' else 'POLICY_EVALUATION_WLS_CALLS' if phase=='R' else 'ACTUAL_WLS_CALLS']+=1;return original_est(payload)
 def solver(*a,**k):check();counts['NONLINEAR_SOLVER_STARTS']+=1;return original_solver(*a,**k)
 def solve(*a,**k):counts['ASSIGNMENT_OPTIMIZATION_CALLS']+=1;return original_solve(*a,**k)
 def decide(view):
  counts['R_CALLS']+=1;before=mdigest(view);d=policy.decide(view,'R');require(before==mdigest(view),'PUBLIC_INPUT_MUTATED');return d
 history=REPO/'reports/n1_independent_decision_validation_001/ATTEMPT_001'
 config=load(history/'EXPERIMENT_CONFIG.json');cases={'I':cp(config['cases']['I'])};cases['I']['physical']['targets'][1]['position_at_birth']=[9.45,10.];cases['I']['physical']['targets'][1]['velocity']=[.4,0.]
 save('EXPERIMENT_CONFIG.json',cases['I']);save('WORLD_COMPARISON.json',dict(changed_fields={'targets/1/position_at_birth':[[9.,10.],[9.45,10.]],'targets/1/velocity':[[.6,0.],[.4,0.]]}))
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
 with patch.object(policy,'estimate',wls),patch.object(public_stream,'_estimate',wls),patch.object(estimator,'least_squares',solver),patch.object(policy,'solve',solve):
  label='I';physical=cp(cases[label]['physical'])
  counts['ACTUAL_RUNS_STARTED']+=1;counts['PREFIX_RUNS_STARTED']+=1
  env,view,records=prefix(label,physical,'S1_WORLD_B')
  frozen=load(history/'I/PUBLIC_D60.json');freeze=load(history/'I/DECISION_FREEZE.json')
  require(mdigest(view)==mdigest(frozen)==freeze['public_digest']=='4ca524be946aafaeece4058597433de613cdb29452d18efa63f45d1c2b8441fe','PUBLIC_STATE_NOT_IDENTICAL')
  require(env.metrics()==load(history/'I/PREFIX_RECEIPT.json')['metrics'],'PREFIX_ECONOMIC_MISMATCH')
  require(not env.beliefs.history[1] and view['beliefs'][1]['status']=='PRIOR_ONLY','T1_OBSERVATION_LEAK')
  require(all(s['state']=='UNQUERIED' and s['packet'] is None for s in view['current_slots'] if s['slot_key']['target_id']==1),'T1_SLOT_LEAK')
  save('PUBLIC_D60.json',view);pre=cp(env.metrics());save('COMMON_PREFIX_RECEIPT.json',dict(public_digest=mdigest(view),metrics=pre,records=records))
  actions=freeze['candidates']['S'];require(actions==[dict(target=1,role='dual_neg45'),dict(target=1,role='dual_pos45'),dict(target=None,role='none')],'S_IDENTITY')
  counts['ACTUAL_FUTURE_RUNS_STARTED']=1;phase='ACTUAL_HOLD';prefix_wls=counts['ACTUAL_WLS_CALLS']
  for tick in (60,80,100):
   if tick!=60:view=env.prepare_decision()
   records.append(dict(view=view,step=step(env,actions if tick==60 else view['assignment'],'S1_B_D'+str(tick))))
  final=env.private_snapshot();metrics=env.metrics();counts['ACTUAL_RUNS_VALID']=1
  save('ACTUAL_S_RAW.json',dict(records=records,final=final,metrics=metrics,observations_consumed=env.beliefs.consumed))
  components={k:metrics['reward_components'][k]-pre['reward_components'][k] for k in metrics['reward_components']};X=metrics['return_with_changes']-pre['return_with_changes'];require(abs(sum(components.values())-X)<1e-8,'ECONOMIC_RECONCILIATION')
  old=load(history/'I/ACTUAL_VALUES.json');V=load(history/'I/MODEL_VALUES.json')['S']['W1']
  results.update(X=X,components=components,change_cost=metrics['change_cost']-pre['change_cost'],completion_times=final['state']['completion_times'],D_A=old['S']['net']-old['K']['net'],D_B=X-old['K']['net'],MODEL_RESIDUAL_B=X-V,ACTUAL_PREFIX_WLS_CALLS=prefix_wls,ACTUAL_FUTURE_WLS_CALLS=counts['ACTUAL_WLS_CALLS']-prefix_wls)
  save('ACTUAL_VALUES.json',results)
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
   save('SCHEMA_ADAPTATION.json',dict(identity='S1_WITNESS_ATTEMPT_001_ECON_NOC_RESEARCH_ONLY',original_digest=digest(original_schema),local_digest=digest(local_schema),diff={'/$defs/Config/properties/change_cost/const':[.01,0.]},rejected_costs=rejected,other_constraint_rejected=True,scope='public.SCHEMA patched for complete run; all validators retain original functions'))
   run()
  require(schema_public.SCHEMA is original_schema,'SCHEMA_NOT_RESTORED')
 except BaseException as exc:status='BLOCKED';error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());save('FAILURE.json',error)
 finally:
  save('EXECUTION_STATUS.json',dict(status=status,phase=phase,counts=counts,error=error,results=results))
  save('RESOURCE_RECEIPT.json',dict(CPU_SECONDS=time.process_time()-CPU,WALL_SECONDS=time.monotonic()-START,CONTROLLED_LOGICAL_WRITE_BYTES=WRITES,counts=counts,RESOURCE_ACCOUNTING='PROCESS_CPU_AND_TASK_WRITER_ONLY',RESOURCE_COMPLIANCE='NOT_ESTABLISHED_FOR_PREPARATION_AND_NATIVE_CHILD_THREADS',retry=False))
 print(status,error,counts,flush=True)
