"""L3-B: one process, archived inputs, no estimator/solver/branch execution."""
import sys,time,json,hashlib,copy,traceback,os
from pathlib import Path
C=time.process_time(); W=time.monotonic()
R=Path(__file__).resolve().parents[2]; D=Path(__file__).resolve().parent
S=R/'reports/stfbs_lite_h2_h3_extension_005'
sys.path[:0]=[str(R),r'D:\miniconda3\envs\dynamic_member_coalition_core\Lib\site-packages']
PINS={}; RESULTS=[]; REFERENCES=0; PHASE='STAGE_0'
# Preparation commands are charged conservatively, without resetting on interruption.
PRIOR_CPU=15.; DEADLINE=__import__('datetime').datetime.fromisoformat('2026-11-14T15:55:59+08:00').timestamp()  # conservative cumulative wall deadline
def check():
    if time.process_time()-C+PRIOR_CPU>=115: raise RuntimeError('CPU_STOP_RESERVE')
    if time.time()>=DEADLINE: raise RuntimeError('WALL_STOP_RESERVE')
    if sum(p.stat().st_size for p in D.rglob('*') if p.is_file())>=63*1048576: raise RuntimeError('STORAGE_STOP_RESERVE')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
    p=Path(p); PINS[str(p)]=sha(p); return json.loads(p.read_bytes())
def save(n,x):
    b=json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False).encode()
    if sum(p.stat().st_size for p in D.rglob('*') if p.is_file())+len(b)>67108864: raise RuntimeError('STORAGE_LIMIT')
    with (D/n).open('xb') as f: f.write(b)
def norm(x): return json.loads(json.dumps(x))
def require(ok,code):
    if not ok: raise RuntimeError(code)
def integer_keys(d): return {int(k):v for k,v in d.items()}
def main():
    global PHASE,REFERENCES
    from pursuit_v2.service import ServiceState
    from pursuit_v2.config import Config
    from pursuit_v2.observation_geometry import offset
    import numpy as np
    from research.non_oracle import stfbs_lite_proxy as original
    from research.non_oracle.belief import trajectory
    view=read(S/'PUBLIC_INPUT_FREEZE.json')
    for k in ('beliefs','service_states','current_endpoints','current_q'): view[k]=integer_keys(view[k])
    for ep in view['current_endpoints'].values():
        if ep is not None: ep['team']=tuple(tuple(t) for t in ep['team'])
    for j,s in view['service_states'].items(): view['service_states'][j]=ServiceState(base=s['base'],intervals=s['intervals'],team=tuple(tuple(t) for t in s['team']))
    candidates=read(S/'CANDIDATE_FREEZE.json'); selection=read(S/'WORLD_SELECTION.json')
    table=read(S/'PROXY_VALUE_TABLE.json'); matrix=read(S/'NINE_CELL_VALUE_MATRIX.json')['matrix']
    read(S/'MODEL_WORLD_MAPPING.json'); read(S/'EXECUTION_FREEZE.json')
    lp=read(R/'reports/stfbs_lite_l3_a_proxy_screening_diagnosis_001/INPUT_SHA256.json')
    for p,h in lp.items(): require(sha(p)==h,'L3_A_INPUT_DRIFT/'+p)
    branches={}; audit=[]; streams={}
    source=(R/'research/non_oracle/stfbs_lite_proxy.py').read_text(encoding='utf-8')
    belief_source=(R/'research/non_oracle/belief.py').read_text(encoding='utf-8')
    # Independent namespace: no replacement of production module globals or functions.
    bn={}; exec(compile(belief_source,'frozen_belief_copy','exec'),bn)
    for world in ('H2','H3'):
      for candidate in candidates:
        check(); action=candidate['kind']; name=world+'_'+action; b=S/name
        auth=read(b/'authorization.json'); require(auth['git_head']=='98ed1160d9aba266d36cc263d95cfbeecef865e9','SOURCE_IDENTITY')
        for p,h in auth['source_sha256'].items():
            require(sha(R/p)==h,'SOURCE_DRIFT/'+p); PINS[str(R/p)]=h
        for row in read(b/'evidence_manifest.json')['files']:
            require(sha(b/row['path'])==row['sha256'],'EVIDENCE_DRIFT/'+name+'/'+row['path']);PINS[str(b/row['path'])]=row['sha256']
        freeze=read(b/'execution_freeze.json')
        for p,h in freeze['files'].items(): require(sha(b/p)==h,'FREEZE_DRIFT/'+name+'/'+p)
        raw=read(b/'BRANCH_RAW.json'); branches[name]=raw
        require(raw['net']==matrix[world][action],'HF_NET_MATRIX')
        require(abs(sum(raw['components'].values())-raw['change_cost']-raw['net'])<1e-12,'HF_LEDGER')
        seed=read(auth['candidate_path'])['candidate']['consumer_seed']
        consumer=bn['Beliefs'](copy.deepcopy(seed['announcements']))
        consumer.states=integer_keys(copy.deepcopy(seed['internal_states_at_D60']))
        consumer.history=integer_keys(copy.deepcopy(seed['accepted_position_history']))
        consumer.accepted_receipts=integer_keys(copy.deepcopy(seed['accepted_receipts']))
        consumer.consumed=copy.deepcopy(seed['consumed_records']); consumer.pending=[]
        require(not seed['pending_observations'],'SEED_PENDING_NEEDS_EXPLICIT_REPLAY')
        fb={f['frame']['frame_id']:f for f in raw['feedback']}; used=set(); updates={}; timeline=[]
        for tick in (80,100):
          snap=read(b/('BELIEF_PROVENANCE_D%d.json'%tick))
          for e in snap['events']:
            if e.get('consumed_tick')!=tick or e.get('status')=='PENDING': continue
            require(e['event_id'] not in used,'DUPLICATE_CONSUMPTION');used.add(e['event_id'])
            require(e['observation_origin']=='MODEL','OBSERVATION_ORIGIN')
            f=fb[e['feedback_identity']]; require(f['provenance']=='SIMULATED' if 'provenance' in f else f['endpoint']['provenance']=='SIMULATED','MODEL_PROVENANCE')
            j=int(e['target_id']); before=len(consumer.history[j]); require(e['available_tick']<=tick,'FUTURE_OBSERVATION')
            consumer.pending=[dict(target_id=j,measurement_tick=e['measurement_tick'],available_tick=e['available_tick'],estimate=f['result']['estimate_result'])]
            consumer.freeze(tick)
            require((len(consumer.history[j])>before)==e['accepted'],'ACCEPTANCE_REPLAY')
            timeline.append(e)
          require(norm(consumer.states)==snap['states'],'BELIEF_STATE_REPLAY/'+name+'/'+str(tick))
          require(norm(consumer.history)==snap['accepted_history'],'BELIEF_HISTORY_REPLAY')
          require(norm(consumer.accepted_receipts)==snap['accepted_receipts'],'BELIEF_RECEIPT_REPLAY')
          updates[tick]=copy.deepcopy(consumer.states)
        streams[name]=updates
        audit.append(dict(branch=name,feedback_events=timeline,updates=updates,hf_net=raw['net'],hf_components=raw['components'],change_cost=raw['change_cost'],boundaries=raw['boundaries'],events=raw['events']))
    save('BRANCH_TRACE_SUMMARY.json',audit)
    save('INPUT_SHA256.json',PINS)
    save('SOURCE_INVENTORY.json',dict(historical_head='98ed1160d9aba266d36cc263d95cfbeecef865e9',proxy_sha256=sha(R/'research/non_oracle/stfbs_lite_proxy.py'),production_files_verified=len([p for p in PINS if '/reports/' not in p.replace('\\','/')]),feedback_replay='PASS'))
    # Preserve arithmetic order; add boundary callbacks and observational trace only.
    modified=source.replace('def run_proxy(view, actions, world):','def run_proxy(view, actions, world, command_fn, boundary, trace):')
    modified=modified.replace("    cfg = Config(**view['config'])","    command = command_fn\n    cfg = Config(**view['config'])")
    modified=modified.replace('    for k in range(start+1, H+1):','    for k in range(start+1, H+1):\n        boundary(k-1, view, positions, states, lefts, geometry_before, statuses, tasks, effort)')
    modified=modified.replace('    changed = sum(',"        trace.append(dict(tick=k,positions=positions.tolist(),states={j:dict(base=s.base,intervals=s.intervals,team=s.team) for j,s in states.items()},tasks=deepcopy(tasks),statuses=deepcopy(statuses),effort=effort,lefts=deepcopy(lefts),geometry_before=deepcopy(geometry_before)))\n    changed = sum(")
    modified='from copy import deepcopy\n'+modified
    save('IMPLEMENTATION_TRANSFORM.json',dict(method='task-local isolated namespace; unchanged production modules',source_sha256=hashlib.sha256(source.encode()).hexdigest(),transformed_sha256=hashlib.sha256(modified.encode()).hexdigest(),new_tolerance=0.,historical_net='exact numeric equality'))
    with (D/'proxy_diagnostic.py').open('x',encoding='utf-8') as f:f.write(modified)
    ns={'__package__':'research.non_oracle'};exec(compile(modified,str(D/'proxy_diagnostic.py'),'exec'),ns)
    PHASE='P1'
    for version in (1,2,3,4):
      for world in ('H2','H3'):
       for candidate in candidates:
        check();action=candidate['kind'];name=world+'_'+action
        v=copy.deepcopy(view);h=copy.deepcopy(selection[world]);h['motion']=integer_keys(h['motion'])
        controls=[];trace=[];boundaries=[]
        def command(b,t,positions,roles,cfg):
            capped=trajectory(b,t)
            age=(t-b['estimate_tick'])*.05; prior=b['last_observation_tick'] is None
            p,vel=capped
            if version in (2,4) and not prior:
                p=[x+y*age for x,y in zip(b['position_estimate'],b['velocity_estimate'])];vel=list(b['velocity_estimate'])
            pos=np.asarray(positions,dtype=float);force=np.asarray(vel)+cfg.travel_gain*(np.asarray(p)+np.array([offset(r,cfg) for r in roles])-pos)
            speed=np.linalg.norm(force,axis=1);u=force*np.minimum(1.,cfg.max_speed/np.maximum(speed,1e-15))[:,None]
            controls.append(dict(tick=t,target=b['target_id'],positions=pos.tolist(),prediction_position=p,prediction_velocity=vel,cap_position=capped[0],cap_velocity=capped[1],propagation_age=age,cap_applicable=not prior and age>1.,control=u.tolist(),estimate_tick=b['estimate_tick'],last_observation_tick=b['last_observation_tick']))
            return u
        def boundary(t,v,*state):
            check()
            if t not in (80,100):return
            before=copy.deepcopy(state)
            if version in (3,4):v['beliefs']=copy.deepcopy(streams[name][t])
            require(all(norm(x)==norm(y) if not isinstance(x,np.ndarray) else np.array_equal(x,y) for x,y in zip(before,state) if not isinstance(x,dict)),'BOUNDARY_CONTINUITY')
            boundaries.append(dict(tick=t,belief=copy.deepcopy(v['beliefs']),state_unchanged=True))
        # Boundary performs no assignments to any physical/service state object.
        out=ns['run_proxy'](v,candidate['actions'],h,command,boundary,trace)
        legacy=next(o for key,o in table if key[1]==selection[world]['world_digest'] and key[0]==candidate['assignment_key'])
        if version==1:
            ref=original.run_proxy(copy.deepcopy(view),candidate['actions'],h); REFERENCES+=1
            require(norm(out)==norm(ref),'P1_REFERENCE_DIFFERENCE/'+name)
            require(out['value']==legacy['value'] and out['ledger']==legacy['ledger'],'P1_ARCHIVE_DIFFERENCE/'+name)
        RESULTS.append(dict(version='P'+str(version),world=world,action=action,output=out,hf=matrix[world][action],signed_error=out['value']-matrix[world][action],absolute_error=abs(out['value']-matrix[world][action])))
        save('P%d_%s_TRACE.json'%(version,name),dict(controls=controls,frames=trace,boundaries=boundaries))
        PHASE='P'+str(version)
    save('ABLATION_RESULTS.json',RESULTS)
    summary=[]
    for world in ('H2','H3'):
      for action in ('KEEP','SWITCH','MEMBER_CHANGE'):
        vals=[next(x['output']['value'] for x in RESULTS if x['world']==world and x['action']==action and x['version']=='P'+str(i)) for i in (1,2,3,4)]
        a,b,c,d=vals;summary.append(dict(world=world,action=action,values=vals,NoCap_F0=b-a,NoCap_F1=d-c,Feedback_Cap=c-a,Feedback_NoCap=d-b,Interaction=d-c-b+a,ME_NoCap=((b-a)+(d-c))/2,ME_Feedback=((c-a)+(d-b))/2))
    save('FACTOR_EFFECTS.json',summary)
    rankings=[]
    for world in ('H2','H3'):
      for version in ('P1','P2','P3','P4'):
        cells=sorted([x for x in RESULTS if x['world']==world and x['version']==version],key=lambda x:-x['output']['value'])
        rankings.append(dict(world=world,version=version,ranking=[x['action'] for x in cells],hf_regret=max(matrix[world].values())-matrix[world][cells[0]['action']],MAE=sum(x['absolute_error'] for x in cells)/3))
    save('RANKING_COMPARISON.json',rankings)
    for p,h in PINS.items():require(sha(p)==h,'FINAL_INPUT_DRIFT/'+p)
    return 'L3_B_DIAGNOSTIC_PASS_CANDIDATE',None
if __name__=='__main__':
    status='L3_B_BLOCKED';error=None
    try:check();status,error=main()
    except BaseException as e:error=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
    final=dict(status=status,phase=PHASE,error=error,completed_units=len(RESULTS),reference_calculations=REFERENCES,cpu_seconds_current=time.process_time()-C,prior_cpu_conservative_seconds=PRIOR_CPU,current_wall_seconds=time.monotonic()-W,deadline_epoch=DEADLINE,storage_bytes=sum(p.stat().st_size for p in D.rglob('*') if p.is_file()),new_WLS=0,new_Assignment=0,new_R=0,new_high_fidelity=0,new_attempts=0)
    save('FINAL_REPORT.json',final)
    text='# L3-B 诊断回执\n\n状态：'+status+'\n\n'+json.dumps(final,ensure_ascii=False,indent=2)+'\n\n历史反馈仅为固定信息干预，不证明自主观测能力。生产准入保持BLOCKED。\n'
    with (D/'REPORT.md').open('x',encoding='utf-8') as f:f.write(text)
    save('evidence_manifest.json',dict(files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in D.iterdir() if p.is_file()]))
    print(json.dumps(final,ensure_ascii=False))
