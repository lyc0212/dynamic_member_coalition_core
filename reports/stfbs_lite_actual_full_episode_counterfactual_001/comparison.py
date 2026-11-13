import json,hashlib,math
EPS=1e-8
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def need(x,m):
 if not x:raise RuntimeError(m)
def validate_snapshot(x):
 need(digest({k:v for k,v in x.items() if k!='snapshot_digest'})==x['snapshot_digest'],'SNAPSHOT_DIGEST')
def scientific_compare(left,right,left_env,right_env):
 differences=[];identity_mappings=[];maximum=0.;leaves=0
 def walk(a,b,path='',key=''):
  nonlocal maximum,leaves
  if isinstance(a,dict) and isinstance(b,dict):
   if set(a)!=set(b):differences.append(dict(path=path,reason='KEYS',left=sorted(set(a)-set(b)),right=sorted(set(b)-set(a))))
   for k in a.keys()&b.keys():walk(a[k],b[k],path+'/'+str(k),str(k))
  elif isinstance(a,list) and isinstance(b,list):
   if len(a)!=len(b):differences.append(dict(path=path,reason='LENGTH',left=len(a),right=len(b)))
   for i,(x,y) in enumerate(zip(a,b)):walk(x,y,path+'/'+str(i),key)
  elif isinstance(a,str) and isinstance(b,str):
   def canon(v,env):return '<ENV>'+v[len(env):] if v==env or v.startswith(env+':') else v
   if a!=b:
    if canon(a,left_env)==canon(b,right_env):identity_mappings.append(dict(path=path,left=a,right=b,rule='independent actual environment/work/stream/frame/packet namespace'))
    elif key in {'frame_sha256','action_commit_id'}:
     identity_mappings.append(dict(path=path,left=a,right=b,rule='derived digest; each source validated separately by fusion/checkpoint/action-commit audits; entire underlying science tree compared'))
    else:differences.append(dict(path=path,left=a,right=b))
  elif isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
   leaves+=1;delta=abs(a-b);maximum=max(maximum,delta)
   if not math.isfinite(delta) or delta>EPS:differences.append(dict(path=path,left=a,right=b,absolute_difference=delta))
  elif a!=b or type(a)!=type(b):differences.append(dict(path=path,left=a,right=b))
 walk(json.loads(json.dumps(left)),json.loads(json.dumps(right)))
 return dict(status='PASS' if not differences else 'FAIL',absolute_tolerance=EPS,relative_tolerance=0,maximum_absolute_difference=maximum,numeric_leaves=leaves,mismatch_count=len(differences),mismatches=differences[:100],identity_mappings=identity_mappings,observed_tick_and_all_scientific_timestamps_compared=True)
def prefix(env,view,records,nominal):
 snap=env.private_snapshot();validate_snapshot(snap)
 return dict(cut_phase='POST_FREEZE_PRE_ASSIGNMENT',policy_input=view,public_checkpoint=env.observe_public(),metrics=env.metrics(),beliefs=dict(states=env.beliefs.states,history=env.beliefs.history,pending=env.beliefs.pending,consumed=env.beliefs.consumed,accepted_receipts=env.beliefs.accepted_receipts,announcements=env.beliefs.announcements),prefix_records=records,nominal_choice=nominal,private_scientific={k:snap[k] for k in ['case','state','sampler','frames','fusions']},private_snapshot_digest=snap['snapshot_digest'])
def comparable_prefix(document):
 x=dict(document['science']);x.pop('private_snapshot_digest')
 # Operational snapshot digest verified on capture; scientific snapshot fields retained.
 return x
def history_body(raw):
 return dict(records=[dict(policy_input=x['policy_input'],nominal_choice=x.get('nominal_choice',x.get('choice')),submitted_assignment=x.get('submitted_assignment',x.get('choice',{}).get('actions')),step=x['step']) for x in raw['records']],metrics=raw['metrics'],terminal_state=raw['final']['state'],observations_consumed=raw['observations_consumed'])
