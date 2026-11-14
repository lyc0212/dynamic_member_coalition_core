"""STFBS-Lite-FB / BLVF V0.1: six H3 endogenous-feedback proxy cells."""
import sys,os,time,json,hashlib,copy,math,traceback,subprocess,ctypes,itertools,html
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];S=REPO/'reports/stfbs_lite_h2_h3_extension_005';P=REPO/'reports/stfbs_lite_l3_b_p1_reproduction_001';H=REPO/'reports/l3_b_diagnostic_recovery_001_stage_a_20261114';STAGE=REPO/'reports/l3_b_stage_a_minimal_remediation_execution_001_20261114121457'
sys.path[:0]=[str(HERE),str(STAGE)]
from recovery import Writer,Clock,require,plain,typed,digest,HistoricalImports
TASK='STFBS_LITE_FB_BLVF_INITIAL_VALIDATION_001';HEAD='496abe824544e3602cda6136bdfc630bacdea629';ACTIONS=('KEEP','SWITCH','MEMBER_CHANGE')
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def signature(v):return digest(plain(v))
def reject_reasons(row,history):
    e=row['estimate']
    if e is None:return ['ESTIMATE_MISSING']
    flags=[]
    if not e.get('has_accepted_estimate'):flags.append('NO_ACCEPTED_ESTIMATE')
    if not e.get('optimizer_converged'):flags.append('OPTIMIZER_NOT_CONVERGED_COMPATIBILITY')
    flags += [k.upper() for k in ('numerical_ill_conditioned','ambiguity_detected','boundary_active','numeric_contract_violation') if e.get(k,True)]
    if flags:return flags
    if len(e['estimate'])!=2 or not all(math.isfinite(x) for x in e['estimate']):return ['INVALID_POSITION']
    if history and row['measurement_tick']<=history[-1][0]:return ['NONINCREASING_MEASUREMENT_TICK']
    return []

class AnalyticCalls:
    def __init__(self,w,clock):self.w=w;self.clock=clock;self.total=0;self.science=0;self.direct=0;self.historical=0;self.synthetic=0;self.success=0;self.rejected=0;self.per_cell={};self.records=[]
    def call(self,payload,scope,cell=None):
        self.clock.check();require(self.total<390,'ANALYTIC_TOTAL_LIMIT')
        if scope=='SCIENCE':require(self.science<378 and self.per_cell.get(cell,0)<63,'ANALYTIC_SCIENCE_LIMIT');self.science+=1;self.per_cell[cell]=self.per_cell.get(cell,0)+1
        else:
            require(self.direct<12,'ANALYTIC_DIRECT_LIMIT');self.direct+=1
            if scope=='HISTORICAL':require(self.historical<8,'HISTORICAL_FRAME_LIMIT');self.historical+=1
            else:require(scope=='SYNTHETIC' and self.synthetic<4,'SYNTHETIC_LIMIT');self.synthetic+=1
        self.total+=1;ordinal=self.total;self.w.write('ANALYTIC_CALLS.jsonl',json.dumps(dict(call_id=ordinal,scope=scope,cell=cell,status='STARTED',payload_sha256=digest(payload)),separators=(',',':'))+'\n',append=True)
        from blvf import estimate
        try:result=estimate(payload)
        except BaseException as exc:self.w.write('ANALYTIC_CALLS.jsonl',json.dumps(dict(call_id=ordinal,status='FAILED',exception_type=type(exc).__name__,message=str(exc)),separators=(',',':'))+'\n',append=True);raise
        self.success+=int(result['analytic_solution_success']);self.rejected+=int(not result['analytic_solution_success']);self.records.append(dict(call_id=ordinal,scope=scope,cell=cell,success=result['analytic_solution_success'],reason=result['rejection_reason']));self.w.write('ANALYTIC_CALLS.jsonl',json.dumps(dict(call_id=ordinal,status='RETURNED',analytic_success=result['analytic_solution_success'],reason=result['rejection_reason']),separators=(',',':'))+'\n',append=True);return result
    def summary(self):return dict(total=self.total,science=self.science,direct=self.direct,historical=self.historical,synthetic=self.synthetic,success=self.success,rejected=self.rejected,per_cell=self.per_cell)
class CellBudget:
    def __init__(self,counter,name):self.counter=counter;self.name=name
    def check(self):self.counter.clock.check()
    def estimator(self,kind):require(kind=='MODEL_OBSERVATION_WLS','POLICY_WLS_PROHIBITED');return lambda payload:self.counter.call(payload,'SCIENCE',self.name)
    def choose(self,*a,**kw):raise RuntimeError('R_ASSIGNMENT_OPTIMIZATION_PROHIBITED')

def physical_snapshot(b):return dict(positions=b.positions.copy(),actions=copy.deepcopy(b.actions),status=copy.deepcopy(b.status),components=copy.deepcopy(b.components),change_cost=b.change_cost,events=copy.deepcopy(b.events),clocks={j:None if b.segment(j) is None else copy.deepcopy(b.segment(j)['latest_clock']) for j in b.targets},endpoints={j:None if b.segment(j) is None else copy.deepcopy(b.segment(j)['latest_endpoint']) for j in b.targets})
def history_without_stream_restart(b):
    h=copy.deepcopy(b.histories)
    for row in h.values():
        for s in row['segments']:s.pop('first_fusion_tick',None)
    return h

def make_fb_branch(Base):
    class FeedbackBranch(Base):
        def __init__(self,view,seed,world,name,budget,enabled):
            super().__init__(view,seed,world,name,budget);self.feedback_enabled=enabled;self.d60_control_beliefs=copy.deepcopy(view['beliefs']);self.freeze_records=[];self.consumer_records=[];self.hold_checks=[]
        def run(self,*a,**k):raise RuntimeError('DEFAULT_R_RUN_PROHIBITED')
        def policy_view(self):
            before_physical=physical_snapshot(self);before_history=copy.deepcopy(self.consumer.history);before_states=copy.deepcopy(self.consumer.states);before_pending=copy.deepcopy(self.consumer.pending);n=len(self.consumer.consumed);shadow_view=super().policy_view();shadow=copy.deepcopy(self.frozen)
            require(typed(before_physical)==typed(physical_snapshot(self)),'FREEZE_CHANGED_PHYSICAL_SERVICE')
            eligible=[r for r in before_pending if r['available_tick']<=self.tick];require(self.consumer.consumed[n:]==[dict(target_id=r['target_id'],measurement_tick=r['measurement_tick'],available_tick=r['available_tick'],consumed_tick=self.tick) for r in eligible],'CONSUMPTION_ORDER_TIME')
            rolling=copy.deepcopy(before_history);appended={j:list(self.consumer.history[j][len(before_history[j]):]) for j in before_history};indices={j:0 for j in before_history};feedback_by_key={}
            for f in self.feedback:feedback_by_key.setdefault((f['frame']['target_id'],f['frame']['tick'],digest(f['result']['estimate_result'])),[]).append(f)
            for ordinal,r in enumerate(eligible):
                j=r['target_id'];t=r['measurement_tick'];reason=reject_reasons(r,rolling[j]);expected=not reason;idx=indices[j];entries=appended[j];observed=idx<len(entries) and entries[idx][0]==t and entries[idx][1]==r['estimate'].get('estimate') if r['estimate'] is not None else False;require(expected==observed,'ACTUAL_HISTORY_ACCEPTANCE_DISAGREEMENT')
                ref=next(((s,p) for s,p in reversed(rolling[j]) if t-s>=5),None);matches=feedback_by_key.get((j,t,digest(r['estimate'])),[]);require(len(matches)==1,'GENERATED_FEEDBACK_IDENTITY');f=matches[0]
                self.consumer_records.append(dict(freeze_tick=self.tick,freeze_ordinal=ordinal,target=j,frame_id=f['frame']['frame_id'],measurement_tick=t,available_tick=r['available_tick'],consumed_tick=self.tick,accepted=observed,rejection_reasons=reason,Q=f['result']['quality']['status'],reference_tick=None if ref is None or not observed else ref[0],reference_interval=None if ref is None or not observed else t-ref[0],estimator_method=None if r['estimate'] is None else r['estimate'].get('estimator_method'),observation_origin=r.get('observation_origin'),provenance=r.get('provenance'),accepted_evidence='actual appended consumer position history; original rule checked without extra freeze'))
                if observed:rolling[j].append(entries[idx]);indices[j]+=1
            require(all(indices[j]==len(appended[j]) for j in appended),'UNBOUND_ACCEPTED_HISTORY')
            # super.policy_view has changed self.frozen. Restore it before OFF can advance.
            if not self.feedback_enabled:self.frozen=copy.deepcopy(self.d60_control_beliefs)
            actual_view=copy.deepcopy(shadow_view);actual_view['beliefs']=copy.deepcopy(self.frozen)
            if not self.feedback_enabled:require(typed(self.frozen)==typed(self.d60_control_beliefs),'OFF_CONTROL_BELIEF_CHANGED')
            self.freeze_records.append(dict(tick=self.tick,feedback_enabled=self.feedback_enabled,actual_control_beliefs=copy.deepcopy(self.frozen),shadow_beliefs=shadow,consumer_internal_states=copy.deepcopy(self.consumer.states),consumer_before=before_states,pending_after=copy.deepcopy(self.consumer.pending),accepted_receipts=copy.deepcopy(self.consumer.accepted_receipts),actual_control='UPDATED_LEGAL_FEEDBACK' if self.feedback_enabled else 'D60_FROZEN',shadow='DIAGNOSTIC_ONLY_NOT_CONTROL' if not self.feedback_enabled else 'CONTROL_ENABLED'))
            return actual_view
        def fixed_run(self,initial):
            self.assign(copy.deepcopy(initial));self.initial_service={j:dict(progress=0. if self.segment(j) is None else math.fsum((self.segment(j)['latest_clock']['base'],self.segment(j)['latest_clock']['intervals']*.05)),endpoint=None if self.segment(j) is None else copy.deepcopy(self.segment(j)['latest_endpoint'])) for j in self.targets}
            while self.tick<120:
                if not self.feedback_enabled:require(typed(self.frozen)==typed(self.d60_control_beliefs),'OFF_ADVANCE_ENTRY_NOT_D60')
                self.advance()
                if self.tick in (80,100):
                    v=self.policy_view();self.decisions.append(dict(mode='FIXED_ACTION_HOLD',feedback_enabled=self.feedback_enabled,view=copy.deepcopy(v)));before=physical_snapshot(self);hist=history_without_stream_restart(self);self.assign(copy.deepcopy(self.actions));require(typed(before)==typed(physical_snapshot(self)) and typed(hist)==typed(history_without_stream_restart(self)),'HOLD_CHANGED_PHYSICAL_SERVICE');require(self.boundaries[-1]['changes']==0 and self.boundaries[-1]['cost']==0,'HOLD_RECHARGE');self.hold_checks.append(dict(tick=self.tick,status='PASS',actual_control_belief_sha256=signature(self.frozen),shadow_belief_sha256=signature(self.freeze_records[-1]['shadow_beliefs'])))
            return dict(branch=self.name,world=copy.deepcopy(self.world),provenance='SIMULATED',observation_origin='MODEL',method='STFBS_LITE_FB_BLVF_V0.1',feedback_enabled=self.feedback_enabled,components=copy.deepcopy(self.components),change_cost=self.change_cost,net=sum(self.components.values())-self.change_cost,frames=copy.deepcopy(self.frames),events=copy.deepcopy(self.events),boundaries=copy.deepcopy(self.boundaries),decisions=copy.deepcopy(self.decisions),feedback=copy.deepcopy(self.feedback),status=copy.deepcopy(self.status),raw_counts=copy.deepcopy(self.cache.counts),endpoint_fusions=self.fusions)
    return FeedbackBranch

def bootstrap(w,clock):
    require(Path(sys.executable).resolve()==Path(r'D:\miniconda3\envs\dynamic_member_coalition_core\python.exe').resolve(),'PYTHON_IDENTITY');sys.path.insert(0,r'D:\miniconda3\envs\dynamic_member_coalition_core\Lib\site-packages');pins=read(H/'HISTORICAL_IDENTITY.json');guard=HistoricalImports(H/'historical',pins);guard.install()
    import numpy,scipy
    from research.non_oracle.stfbs_d1a_model import Branch,point
    from research.non_oracle import policy
    from research.cooperative_sensing import estimator
    from research.non_oracle.stfbs_d1a_audit import audit,service_audit
    require(numpy.__version__=='2.1.3' and scipy.__version__=='1.15.3','NUMERICAL_ENVIRONMENT')
    mapping=read(S/'MODEL_WORLD_MAPPING.json');world=copy.deepcopy(mapping['H3']);world['motion']={int(k):v for k,v in world['motion'].items()};require(mapping['STFBS']['H3']['world_digest']==world['perturbation']['stfbs_world_digest'],'MODEL_STFBS_MAPPING')
    cp=Path(read(S/'H3_KEEP/authorization.json')['candidate_path']);c=read(cp)['candidate'];view=copy.deepcopy(c['a2_policy_view']);seed=copy.deepcopy(c['consumer_seed']);require(digest(seed)==read(S/'S4_STATIC.json')['seed_digest'],'SEED_IDENTITY');view['beliefs']={int(k):v for k,v in view['beliefs'].items()}
    for k in ('internal_states_at_D60','accepted_position_history','accepted_receipts'):seed[k]={int(j):v for j,v in seed[k].items()}
    require(digest(view)==world['public_digest'] and not seed['pending_observations'],'D60_VIEW_OR_PENDING');world_identity=copy.deepcopy(world);saved=world_identity.pop('world_digest');require(saved==digest(world_identity),'H3_MODEL_DIGEST')
    p1=read(P/'P1_METRICS.json');reference={};historical={};checks={};protected={str(cp):sha(cp),str(P/'P1_RESULTS.json'):sha(P/'P1_RESULTS.json'),str(S/'MODEL_WORLD_MAPPING.json'):sha(S/'MODEL_WORLD_MAPPING.json')}
    for action in ACTIONS:
        name='H3_'+action;row=next(r for r in p1['cells'] if r['world']=='H3' and r['action']==action);raw=read(S/name/'BRANCH_RAW.json');require(sha(S/name/'BRANCH_RAW.json')==row['HF_raw_sha256'],'HF_REFERENCE_SHA');require(raw['world']['world_digest']==world['world_digest'] and raw['net']==row['HF'],'HF_REFERENCE_WORLD_VALUE');candidate=next(x for x in read(S/'CANDIDATE_FREEZE.json') if x['kind']==action);require(raw['boundaries'][0]['after']==candidate['actions'],'HF_INITIAL_ACTION');require(all(b['changes']==0 and b['cost']==0 and b['before']==b['after'] for b in raw['boundaries'] if b['tick'] in (80,100)),'HF_FUTURE_ACTION_CHANGE');reference[action]=dict(CAP=row['P1'],HF=row['HF']);historical[action]=raw;checks[action]=dict(status='CONDITIONALLY_COMPARABLE_WITH_LIMITATIONS',world_digest=world['world_digest'],stfbs_digest=world['perturbation']['stfbs_world_digest'],D60_candidate_sha256=sha(cp),same_initial_actions=True,later_effective_actions_unchanged=True,limitation='historical HF ran R/Assignment optimization; this prototype uses fixed holds; strict whole-program equivalence not established');protected[str(S/name/'BRANCH_RAW.json')]=sha(S/name/'BRANCH_RAW.json')
    ctx=dict(w=w,clock=clock,guard=guard,pins=pins,view=view,seed=seed,world=world,Branch=make_fb_branch(Branch),point=point,policy=policy,estimator=estimator,audit=audit,service_audit=service_audit,candidates=read(S/'CANDIDATE_FREEZE.json'),reference=reference,historical=historical,hf_comparability=checks,protected=protected,calls=AnalyticCalls(w,clock),started=0,OFF={},ON={},traces={},timings={},failures=[],forbidden_counts=dict(WLS=0,SOLVER=0,R=0,ASSIGNMENT_OPTIMIZER=0))
    ctx['forbidden_codes']={estimator.estimate.__code__:'WLS',estimator.least_squares.__code__:'SOLVER',policy.decide.__code__:'R',policy.solve.__code__:'ASSIGNMENT_OPTIMIZER'}
    w.json('EXPERIMENT_CONFIG.json',dict(task=TASK,algorithm='STFBS_LITE_FB',core_mechanism='BLVF',version='V0.1',git_head=HEAD,historical_commit='98ed1160d9aba266d36cc263d95cfbeecef865e9',entry_sha256=sha(__file__),analytic_source_sha256=sha(HERE/'blvf.py'),world=plain(world),STFBS_world_digest=world['perturbation']['stfbs_world_digest'],D60_view_digest=digest(view),D60_candidate_path=str(cp),D60_candidate_sha256=sha(cp),seed_digest=digest(seed),candidates=ctx['candidates'],limits=dict(proxy_cells=6,analytic_per_cell=63,analytic_science=378,analytic_direct=12,analytic_total=390,historical_checks=8,synthetic_checks=4,cpu=300,wall=1800,logical_writes=134217728,WLS=0,solver=0,R=0,assignment_optimizer=0,ACTUAL=0),numeric_parameters=dict(DT=.05,P_REF=.95,DELTA=.06,DOMAIN=[[0.,0.],[20.,20.]],condition_ratio=1e-4,determinant_tolerance=64*sys.float_info.epsilon,boundary_tolerance=64*sys.float_info.epsilon*20.,epsilon_best=1e-8),environment=dict(python=sys.executable,version=sys.version,numpy=numpy.__version__,scipy=scipy.__version__,numpy_path=numpy.__file__,scipy_path=scipy.__file__),treatment='ON uses super.policy_view frozen; OFF restores D60 self.frozen BEFORE every advance and audits against actual control snapshots',historical_comparability=checks,guard='Python entry profile stops known WLS/Solver/R/Assignment solver before execution; overhead included; no new supervisor'))
    return ctx


def direct_checks(ctx):
    calls=ctx['calls'];w=ctx['w'];history=[];limitations=[]
    paths=[('H3_KEEP_NORMAL',S/'H3_KEEP/BRANCH_RAW.json',61),('H3_SWITCH_POSITION_PRIOR',S/'H3_SWITCH/BRANCH_RAW.json',60),('H3_MEMBER_Q_FAIL',S/'H3_MEMBER_CHANGE/BRANCH_RAW.json',60),('H4_MEMBER_D68_ILL',REPO/'reports/stfbs_lite_target_turn_exploration_001/ATTEMPT_003/RAW/H4_HF_MEMBER_CHANGE.json',68),('H4_MEMBER_D60_NONINCREASING',REPO/'reports/stfbs_lite_target_turn_exploration_001/ATTEMPT_003/RAW/H4_HF_MEMBER_CHANGE.json',60)]
    from research.information_service.public_quality import assess_quality
    from research.non_oracle.stfbs_d1a_state import ModelBeliefConsumer
    cache={}
    for label,path,tick in paths:
        if not path.exists():limitations.append(dict(sample=label,status='NOT_IDENTIFIABLE',missing=str(path)));continue
        if str(path) not in cache:cache[str(path)]=read(path)
        f=next((x for x in cache[str(path)]['feedback'] if x['frame']['tick']==tick),None)
        if f is None:limitations.append(dict(sample=label,status='NOT_IDENTIFIABLE',missing_tick=tick));continue
        payload=copy.deepcopy(f['result']['payload']);r=calls.call(payload,'HISTORICAL');q=assess_quality(payload,r);old=f['result']['estimate_result'];row=dict(sample=label,path=str(path),source_sha256=sha(path),frame_id=f['frame']['frame_id'],payload=payload,analytic=r,analytic_quality=q,historical_estimate=old,historical_quality=f['result']['quality'],position_difference=None if not r['has_accepted_estimate'] or old is None or not old['has_accepted_estimate'] else math.dist(r['estimate'],old['estimate']),quality_same=q['status']==f['result']['quality']['status'])
        if label.endswith('NONINCREASING'):
            c=ModelBeliefConsumer(copy.deepcopy(ctx['seed']));j=f['frame']['target_id'];n=len(c.history[j]);c.enqueue(dict(source='MODEL',provenance='SIMULATED',observation_origin='MODEL',target_id=j,measurement_tick=tick,available_tick=tick,estimate=copy.deepcopy(r)));c.freeze(80);require(len(c.history[j])==n,'NONINCREASING_ACCEPTED');row['original_consumer_nonincreasing_rejection']='VERIFIED_NO_HISTORY_APPEND'
        history.append(row);w.json('DIRECT/'+label+'.json',row)
    def payload(positions,bearings,sigmas):return dict(sensor_ids=['U0','U1'],positions=positions,bearings=bearings,sigmas=sigmas,domain=[[0.,0.],[20.,20.]])
    normal=payload([[0.,0.],[0.,2.]],[math.pi/4,-math.pi/4],[.01,.01]);a=calls.call(normal,'SYNTHETIC');aq=assess_quality(normal,a);require(a['analytic_solution_success'] and math.dist(a['estimate'],[1.,1.])<1e-12 and aq['status']=='PASS','SYNTHETIC_NORMAL')
    parallel=payload([[0.,0.],[0.,1.]],[0.,0.],[.01,.01]);b=calls.call(parallel,'SYNTHETIC');require(not b['analytic_solution_success'],'PARALLEL_ACCEPTED')
    backwards=payload([[1.,1.],[2.,2.]],[0.,math.pi/2],[.01,.01]);c=calls.call(backwards,'SYNTHETIC');require(not c['analytic_solution_success'],'NONFORWARD_ACCEPTED')
    weak=payload([[0.,0.],[0.,2.]],[math.pi/4,-math.pi/4],[.1,.1]);d=calls.call(weak,'SYNTHETIC');dq=assess_quality(weak,d);require(d['analytic_solution_success'] and dq['status']=='FAIL' and not d['numerical_ill_conditioned'],'Q_FAIL_BELIEF_SEPARATION_SETUP')
    w.json('DIRECT/SYNTHETIC_INTERSECTIONS.json',dict(normal=a,parallel=b,backwards=c,weak_quality=d))
    from research.information_service_bridge.public_stream import BridgeFrameProcessor
    from research.information_service.common import CONTRACT_ID
    stream='BLVF_SYNTHETIC_INTERFACE';records=[dict(sensor_id='U'+str(i),position=weak['positions'][i],bearing=weak['bearings'][i],sigma=weak['sigmas'][i],packet_id=stream+':tick5:U'+str(i),measurement_tick=5,available_tick=5,status='ok') for i in (0,1)];frame=dict(contract_id=CONTRACT_ID,stream_id=stream,frame_id=stream+':tick5',target_id=0,tick=5,measurement_time=.25,available_time=.25,records=records)
    def reuse(p):require(digest(p)==digest(weak),'REUSED_ANALYTIC_PAYLOAD_CHANGED');return copy.deepcopy(d)
    processor=BridgeFrameProcessor(['U0','U1'],5,stream,0,estimator_fn=reuse);processed=processor.process(frame);require(processed['quality']['status']=='FAIL' and processed['estimate_result']['analytic_solution_success'],'REAL_QUALITY_INTERFACE_PATH')
    receipt=dict(target_id=0,measurement_tick=0,available_tick=0,consumed_tick=0);state=dict(target_id=0,estimate_tick=0,available_tick=0,position_estimate=[.9,1.],velocity_estimate=[.2,0.],velocity_source='PUBLIC_PRIOR',last_observation_tick=0,source='ACTUAL_WLS',status='OBSERVED',diagnostics=None);seed=dict(announcements=[dict(id=0,speed_limit=1.)],internal_states_at_D60={0:state},accepted_position_history={0:[[0,[.9,1.]]]},accepted_receipts={0:receipt},pending_observations=[],consumed_records=[receipt]);consumer=ModelBeliefConsumer(seed)
    row=dict(source='MODEL',provenance='SIMULATED',observation_origin='MODEL',target_id=0,measurement_tick=5,available_tick=5,estimate=copy.deepcopy(processed['estimate_result']));consumer.enqueue(row);frozen=consumer.freeze(5);expected=[(x-y)/(.05*5) for x,y in zip(d['estimate'],[.9,1.])];require(frozen[0]['velocity_estimate']==expected and frozen[0]['velocity_source']=='ACTUAL_POSITION_DIFFERENCE' and len(consumer.history[0])==2,'REAL_FREEZE_SPEED_DIFFERENCE');require(processed['quality']['status']=='FAIL' and frozen[0]['last_observation_tick']==5,'Q_FAIL_MUST_NOT_FORCE_BELIEF_REJECTION')
    consumer.enqueue(dict(row,available_tick=6));consumer.freeze(6);require(len(consumer.history[0])==2,'SYNTHETIC_NONINCREASING')
    w.json('BLVF_COMPATIBILITY_CHECK.json',dict(status='COMPLETED',historical_samples=history,limitations=limitations,interpretation='finite representative samples; analytic/WLS differences preserved, not universal equivalence',analytic_calls=ctx['calls'].summary()))
    w.json('MINIMAL_VALIDATION.json',dict(status='PASS',normal_intersection=a,parallel_rejection=b,backward_rejection=c,Q_FAIL_accepted_analytic=d,real_bridge_quality=processed['quality'],real_consumer_updated_belief=frozen[0],expected_velocity=expected,strict_nondecreasing_rejection=True,DT=.05,reused_result_without_extra_analytic_call=True,synthetic_intersection_calls=4,new_WLS=0,new_HF=0,information_isolation='analytic function accepts exact five public fields; no world/truth input'))

def control_audit(ctx,result):
    import numpy as np
    from pursuit_v2.config import Config
    from pursuit_v2.observation_geometry import offset
    from research.non_oracle.belief import trajectory
    cfg=Config(**ctx['view']['config']);frozen=ctx['view']['beliefs'];decisions={d['view']['tick']:d['view'] for d in result['decisions']};boundaries={b['tick']:b for b in result['boundaries']};actions=copy.deepcopy(ctx['view']['assignment']);terminal={e['target']:e for e in result['events'] if e['kind'] in ('completed','escaped','unfinished')};checked=0;records=[]
    for frame in result['frames']:
        n=frame['tick'];lo=(n-1)*.05
        if n-1 in decisions:frozen=decisions[n-1]['beliefs']
        if n-1 in boundaries:actions=boundaries[n-1]['after']
        for i,a in enumerate(actions):
            u=np.zeros(2);dt=0.;prediction_used=None
            if a['target'] is not None:
                j=a['target'];event=terminal[j]
                if event['time']>=lo and not (event['time']==lo and event['tick']<n):
                    b=frozen[j];p,v=trajectory(b,n-1);force=np.asarray(v)+cfg.travel_gain*(np.asarray(p)+offset(a['role'],cfg)-np.asarray(frame['before'][i]));u=force*min(1.,cfg.max_speed/max(float(np.linalg.norm(force)),1e-15));truth=ctx['point'](ctx['world'],j,n-1);vx=ctx['world']['motion'][j]['velocity'][0];escape=lo if truth[0]>=cfg.side else lo+(cfg.side-truth[0])/vx if vx>0 else math.inf;dt=max(0.,min(n*.05,escape)-lo);prediction_used=(j,b,p,v,truth)
            bound=16*math.ulp(max(1.,float(np.max(np.abs(u)))));require(float(np.max(np.abs(u-np.asarray(frame['control'][i]))))<=bound and dt==frame['elapsed'][i],'ACTUAL_CONTROL_SNAPSHOT_AUDIT');checked+=1
            if prediction_used is not None and dt>0:
                j,b,p,v,truth=prediction_used;et=b['estimate_tick'];true_v=ctx['world']['motion'][j]['velocity'];est_truth=ctx['point'](ctx['world'],j,et) if et>=60 else None
                records.append(dict(target=j,tick=n-1,robot_id=i,actual_control_belief=copy.deepcopy(b),prediction_position=list(p),prediction_velocity=list(v),propagation_age=(n-1-et)*.05,observation_age=None if b['last_observation_tick'] is None else (n-1-b['last_observation_tick'])*.05,cap_applied=b['last_observation_tick'] is not None and (n-1-et)*.05>1.,true_position=truth.tolist(),true_velocity=list(true_v),position_error=math.dist(p,truth),velocity_error=math.dist(v,true_v),estimation_position_error=None if est_truth is None else math.dist(b['position_estimate'],est_truth),estimation_velocity_error=None if est_truth is None else math.dist(b['velocity_estimate'],true_v),actual_control=frame['control'][i],robot_before=frame['before'][i],robot_after=frame['positions'][i]))
    require(checked==180 and [d['view']['tick'] for d in result['decisions']]==[80,100],'CONTROL_AUDIT_HORIZON')
    return dict(status='PASS',checked_robot_intervals=checked,basis='actual ON/OFF control snapshots, not OFF shadow beliefs',rounding_bound='16 ulp of max(1,control magnitude)'),records

def service_summary(ctx,branch,result,action):
    j=1 if action=='SWITCH' else 0;t=branch.targets[j];clocks=[f['clocks'][j] for f in result['frames'] if f['clocks'][j] is not None];peaks=[math.fsum((s['base'],s['intervals']*.05)) for s in clocks];term=next(e for e in result['events'] if e['target']==j and e['kind'] in ('completed','escaped','unfinished'));p0=branch.initial_service[j]['progress'];peaks.append(p0)
    if term['kind']=='completed':peaks.append(t['service_duration'])
    left=branch.initial_service[j]['endpoint'];ng=0;valid=0;qcounts={}
    for f in result['feedback']:
        if f['frame']['target_id']!=j:continue
        right=f['endpoint'];q=right['quality']['status'];qcounts[q]=qcounts.get(q,0)+1
        if f['frame']['tick']==60:left=right;continue
        if left is not None:ng+=int(left['G'] and right['G']);valid+=int(left['G'] and right['G'] and left['quality']['status']==right['quality']['status']=='PASS')
        left=right
    return dict(P0=p0,Pmax=max(peaks),required_duration=t['service_duration'],M_service=max(peaks)-t['service_duration'],margin_note='zero means reached clipped completion threshold, not positive extra safety margin',NG=ng,GQ_valid_intervals=valid,quality_counts=qcounts,terminal=term,completion_tick=term['tick'] if term['kind']=='completed' else None,resets=[e for e in result['events'] if e['kind']=='reset' and e['target']==j],natural_release='original terminal transaction; no optimizer',positive_cost_ledger=dict(completion=result['components']['completion'],flow=-result['components']['flow'],late=-result['components']['late'],effort=-result['components']['effort'],terminal=-result['components']['terminal'],change=result['change_cost']))

def run_cell(ctx,mode,action):
    w,clock=ctx['w'],ctx['clock'];clock.check();require(ctx['started']<6,'PROXY_CELL_START_LIMIT');ctx['started']+=1;name='BLVF_'+mode+'_'+action;actions=copy.deepcopy(next(x['actions'] for x in ctx['candidates'] if x['kind']==action));view=copy.deepcopy(ctx['view']);seed=copy.deepcopy(ctx['seed']);world=copy.deepcopy(ctx['world']);w.json('CALLS/'+name+'_STARTED.json',dict(task=TASK,cell=name,status='STARTED',ordinal=ctx['started'],input_sha256=signature([view,seed,world,actions]),feedback_enabled=mode=='ON'))
    from research.non_oracle.stfbs_d1a_history_audit import register_context,audit_branch_independent
    context=register_context(name,{h['target_id']:copy.deepcopy(h) for h in view['histories']});budget=CellBudget(ctx['calls'],name);branch=None;full_start=time.monotonic();cpu_start=time.process_time();core_start=full_start
    try:
        branch=ctx['Branch'](view,seed,world,name,budget,mode=='ON');result=branch.fixed_run(actions);core_wall=time.monotonic()-core_start;core_cpu=time.process_time()-cpu_start;w.json('RAW/'+name+'.json',plain(result))
        audits=dict(history=audit_branch_independent(branch,context=context),service=ctx['service_audit'](result,view),physical_economic=ctx['audit'](result,view));ctrl,records=control_audit(ctx,result);audits['actual_control']=ctrl;require(all(x['status']=='PASS' for x in audits.values()),'CELL_SCIENTIFIC_AUDIT');require(len(result['frames'])==60 and result['frames'][-1]['tick']==120,'INCOMPLETE_HORIZON');actual_calls=ctx['calls'].per_cell.get(name,0);expected_calls=sum(f['result']['estimator_called'] for f in result['feedback']);require(actual_calls==expected_calls and result['endpoint_fusions']==len(result['feedback']),'ANALYTIC_ROUTE_ACCOUNTING');skipped=sum(f['result']['skipped'] for f in result['feedback']);summary=service_summary(ctx,branch,result,action)
        if mode=='OFF':require(all(typed(f['actual_control_beliefs'])==typed(view['beliefs']) for f in branch.freeze_records),'OFF_SHADOW_LEAKED_TO_CONTROL')
        w.json('TRACE/'+name+'.json',plain(dict(control_records=records,freeze_records=branch.freeze_records,actual_consumer_records=branch.consumer_records,accepted_history=branch.consumer.history,accepted_receipts=branch.consumer.accepted_receipts,pending_D120=branch.consumer.pending,consumer_terminal_states=branch.consumer.states,hold_checks=branch.hold_checks,physical_histories=branch.histories,initial_service=branch.initial_service,service_summary=summary,audits=audits,analytic_calls=actual_calls,insufficient_sensor_frames=skipped,estimator_route='MODEL_OBSERVATION_WLS compatibility name, actual ANALYTIC_BEARING_INTERSECTION')))
        timing=dict(core_wall=core_wall,core_cpu=core_cpu,complete_cell_wall=time.monotonic()-full_start,complete_cell_cpu=time.process_time()-cpu_start,core_includes=['Branch initialization','history transactions','analytic estimates','per-call accounting writes','physics and belief feedback','entry profile guard overhead'],complete_includes=['core','raw writes','history/service/economic/control audits','trace writes'],excludes=['initial environment and direct checks','final timing record self-write','task-wide analysis and report'],analytic_calls=actual_calls,END_TO_END_SPEEDUP='NOT_ESTABLISHED')
        w.json('TIMING/'+name+'.json',timing);ctx[mode][action]=result;ctx['traces'][mode+'/'+action]=dict(records=records,result=result,service=summary,freeze=plain(branch.freeze_records));ctx['timings'][mode+'/'+action]=timing;return result
    except BaseException as exc:
        w.json('RAW/'+name+'_FAILURE.json',dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),analytic_calls=ctx['calls'].per_cell.get(name,0),tick=None if branch is None else branch.tick))
        if branch is not None:w.json('RAW/'+name+'_PARTIAL.json',plain(dict(frames=branch.frames,feedback=branch.feedback,events=branch.events,decisions=branch.decisions,freeze_records=branch.freeze_records,consumer_records=branch.consumer_records)))
        raise


def pred_index(rows):
    out={}
    for r in rows:
        key=(r['target'],r['tick'])
        if key in out:require(out[key]['prediction_position']==r['prediction_position'] and out[key]['prediction_velocity']==r['prediction_velocity'],'DUPLICATE_ROBOT_PREDICTION_WEIGHTING')
        else:out[key]=r
    return out

def rank(values,hf):
    if not all(a in values for a in ACTIONS):return dict(status='NOT_IDENTIFIABLE',available_actions=list(values))
    top=max(values.values());best=[a for a in ACTIONS if top-values[a]<=1e-8];return dict(status='VALID',values=values,strict_order=sorted(ACTIONS,key=lambda a:-values[a]),exact_tie_groups=[[a for a in ACTIONS if values[a]==x] for x in sorted(set(values.values()),reverse=True)],epsilon_best=best,actual_selected_action=None,HF_regret_by_epsilon_best={a:max(hf.values())-hf[a] for a in best},actual_selection='NOT_SPECIFIED; all epsilon-best regrets reported separately')
def analyze(ctx):
    ref=ctx['reference'];values={'CAP':{a:r['CAP'] for a,r in ref.items()},'OFF':{a:r['net'] for a,r in ctx['OFF'].items()},'ON':{a:r['net'] for a,r in ctx['ON'].items()}};hf={a:r['HF'] for a,r in ref.items()};matrix={a:dict(CAP=ref[a]['CAP'],FB_OFF=values['OFF'].get(a),FB_ON=values['ON'].get(a),HF=hf[a]) for a in ACTIONS};method={};effects={};pairs={};process={}
    for label,d in values.items():
        errors={a:dict(signed_error=v-hf[a],AE=abs(v-hf[a])) for a,v in d.items()};subset=list(d);method[label]=dict(valid_actions=subset,denominator=len(d),complete_three_cell_MAE=None if len(d)!=3 else sum(e['AE'] for e in errors.values())/3,subset_mean_AE=None if not d else sum(e['AE'] for e in errors.values())/len(d),errors=errors,ranking=rank(d,hf),relative_value_difference_errors={a+'-'+b:None if a not in d or b not in d else (d[a]-d[b])-(hf[a]-hf[b]) for a,b in itertools.combinations(ACTIONS,2)})
    for p,b in [('ON','OFF'),('ON','CAP'),('OFF','CAP')]:
        common=[a for a in ACTIONS if a in values[p] and a in values[b]];baseline=[abs(values[b][a]-hf[a]) for a in common];target=[abs(values[p][a]-hf[a]) for a in common];pairs[p+'/'+b]=dict(status='NOT_IDENTIFIABLE' if not common else 'VALID_COMMON_ACTIONS',common_actions=common,denominator=len(common),baseline_subset_MAE=None if not common else sum(baseline)/len(common),treatment_subset_MAE=None if not common else sum(target)/len(common),paired_Delta_MAE=None if not common else sum(x-y for x,y in zip(target,baseline))/len(common))
    for a in ACTIONS:
        off=values['OFF'].get(a);on=values['ON'].get(a);effects[a]=dict(structure_value_effect=None if off is None else off-values['CAP'][a],feedback_value_effect=None if off is None or on is None else on-off,feedback_accuracy_improvement=None if off is None or on is None else abs(off-hf[a])-abs(on-hf[a]),interpretation='structure is total new predictor effect, not isolated Q causality; feedback is endogenous closed-loop total effect')
        if a not in ctx['OFF'] or a not in ctx['ON']:continue
        offtrace=ctx['traces']['OFF/'+a];ontrace=ctx['traces']['ON/'+a];io=pred_index(offtrace['records']);ion=pred_index(ontrace['records']);common=sorted(io.keys()&ion.keys());raw_off=offtrace['result'];raw_on=ontrace['result']
        before_off=[(f['positions'],f['control'],f['elapsed']) for f in raw_off['frames'] if f['tick']<=80];before_on=[(f['positions'],f['control'],f['elapsed']) for f in raw_on['frames'] if f['tick']<=80];require(before_off==before_on,'ON_OFF_PRE_FEEDBACK_DIFFERENCE')
        control_changed=any(f['control']!=g['control'] for f,g in zip(raw_off['frames'],raw_on['frames']));trajectory_changed=any(f['positions']!=g['positions'] for f,g in zip(raw_off['frames'],raw_on['frames']));obs_off=[dict(t=f['frame']['tick'],target=f['frame']['target_id'],payload=f['result']['payload'],Q=f['result']['quality']['status']) for f in raw_off['feedback']];obs_on=[dict(t=f['frame']['tick'],target=f['frame']['target_id'],payload=f['result']['payload'],Q=f['result']['quality']['status']) for f in raw_on['feedback']]
        def summary(idx):
            rows=list(idx.values());return dict(denominator_target_ticks=len(rows),valid_control_times=[dict(target=j,tick=t) for j,t in sorted(idx)],mean_position_error=None if not rows else sum(r['position_error'] for r in rows)/len(rows),mean_velocity_error=None if not rows else sum(r['velocity_error'] for r in rows)/len(rows))
        paired=dict(common_keys=[dict(target=j,tick=t) for j,t in common],denominator=len(common),OFF_position_error=None if not common else sum(io[k]['position_error'] for k in common)/len(common),ON_position_error=None if not common else sum(ion[k]['position_error'] for k in common)/len(common),OFF_velocity_error=None if not common else sum(io[k]['velocity_error'] for k in common)/len(common),ON_velocity_error=None if not common else sum(ion[k]['velocity_error'] for k in common)/len(common),status='VALID' if common else 'NOT_IDENTIFIABLE')
        belief_changed=any(plain(x['actual_control_beliefs'])!=plain(y['actual_control_beliefs']) for x,y in zip(offtrace['freeze'],ontrace['freeze']));process[a]=dict(pre_D80_physical_control_equivalence='VERIFIED',actual_control_belief='CHANGED' if belief_changed else 'UNCHANGED',actual_control='CHANGED' if control_changed else 'UNCHANGED',robot_trajectory='CHANGED' if trajectory_changed else 'UNCHANGED',endogenous_observation_or_Q='CHANGED' if obs_off!=obs_on else 'UNCHANGED',service='CHANGED' if offtrace['service']!=ontrace['service'] else 'UNCHANGED',value='CHANGED' if off!=on else 'UNCHANGED',OFF_service=offtrace['service'],ON_service=ontrace['service'],OFF_prediction=summary(io),ON_prediction=summary(ion),paired_prediction=paired,scope='same active feedback switch, natural downstream observation divergence; not individual-event direct causality')
    analysis=dict(matrix=matrix,methods=method,value_effects=effects,paired_MAE=pairs,mechanisms=process,timings=ctx['timings'],historical_HF_comparability=ctx['hf_comparability'],END_TO_END_SPEEDUP='NOT_ESTABLISHED',history_reference='H3 accepted values only; no new HF or WLS',limits='H3 deterministic conditional world, six cells not independent statistical samples; no new worlds, no robust guarantee or paper novelty')
    ctx['w'].json('VALUE_MATRIX.json',matrix);ctx['w'].json('SCIENTIFIC_ANALYSIS.json',analysis);return analysis

def resource_audit(ctx):
    rows=[json.loads(x) for x in (HERE/'ANALYTIC_CALLS.jsonl').read_text(encoding='utf-8').splitlines()] if (HERE/'ANALYTIC_CALLS.jsonl').exists() else [];starts={};ends={}
    for r in rows:
        if r['status']=='STARTED':require(r['call_id'] not in starts,'ANALYTIC_CALL_ID_DUPLICATE');starts[r['call_id']]=r
        else:require(r['call_id'] in starts and r['call_id'] not in ends,'ANALYTIC_CALL_CLOSURE');ends[r['call_id']]=r
    require(len(starts)==ctx['calls'].total and set(starts)==set(ends),'ANALYTIC_DISK_RUNTIME_AUDIT')
    return dict(status='PASS',starts=len(starts),closed=len(ends),counts=ctx['calls'].summary(),forbidden_entry_counts=ctx['forbidden_counts'])

def worker():
    prep=read(HERE/'ATTEMPT_002_PREPARATION_ACCOUNTING.json');origin=float(sys.argv[-1]);clock=Clock(origin,cpu_limit=300,wall_limit=1800);w=Writer(HERE,limit=134217728,initial_written=prep['cumulative_logical_write_bytes'],clock=clock);ctx=None;analysis=None;fatal=None;old_profile=sys.getprofile();profile_active=False;checks_finished=False
    try:
        ctx=bootstrap(w,clock)
        def profile(frame,event,arg):
            if event=='call':
                resource=ctx['forbidden_codes'].get(frame.f_code)
                if resource is not None:ctx['forbidden_counts'][resource]+=1;raise RuntimeError('FORBIDDEN_SCIENTIFIC_ENTRY/'+resource)
        sys.setprofile(profile);profile_active=True;direct_checks(ctx);checks_finished=True
        for action in ACTIONS:
            run_cell(ctx,'OFF',action);run_cell(ctx,'ON',action)
    except BaseException as exc:
        fatal=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());w.json('FAILURE.json',fatal)
    finally:
        if profile_active:sys.setprofile(old_profile)
    clock.check();resource=None
    if ctx is not None:
        try:analysis=analyze(ctx)
        except Exception as exc:fatal=fatal or dict(type=type(exc).__name__,message='ANALYSIS/'+str(exc));w.json('ANALYSIS_FAILURE.json',dict(message=str(exc),traceback=traceback.format_exc()))
        try:resource=resource_audit(ctx)
        except Exception as exc:fatal=fatal or dict(type=type(exc).__name__,message='RESOURCE/'+str(exc));w.json('RESOURCE_AUDIT_FAILURE.json',dict(message=str(exc)))
        protected={p:sha(p)==h for p,h in ctx['protected'].items()};w.json('PROTECTION_CHECK.json',dict(files=protected,unchanged=all(protected.values())));require(all(protected.values()),'FROZEN_REFERENCE_MODIFIED');w.json('RUNTIME_PROJECT_IMPORTS.json',dict(modules=ctx['guard'].audit(),namespace_paths=ctx['guard'].namespace_paths,untriggered_lazy_imports='NOT_VERIFIED'))
    off=0 if ctx is None else len(ctx['OFF']);on=0 if ctx is None else len(ctx['ON']);valid=off+on;status='VALID_SIX_CELL_INITIAL_PROTOTYPE_RESULT' if valid==6 and fatal is None else 'PARTIAL_VALID_SCIENTIFIC_RESULTS' if valid else 'BLOCKED_NO_VALID_CELLS';counts=None if ctx is None else ctx['calls'].summary();forbidden=None if ctx is None else ctx['forbidden_counts'];hyp_a='NOT_IDENTIFIABLE';hyp_b='NOT_IDENTIFIABLE';hyp_c='NOT_IDENTIFIABLE'
    if checks_finished:
        compatibility=read(HERE/'BLVF_COMPATIBILITY_CHECK.json');samples=compatibility['historical_samples'];same=sum(r['quality_same'] for r in samples);close=sum(r['position_difference'] is not None and r['position_difference']<=1e-8 for r in samples);hyp_a='SUPPORTED' if samples and same==close==len(samples) else 'PARTIALLY_SUPPORTED' if same or close else 'NOT_SUPPORTED'
    if analysis is not None and valid==6:
        improves=[r['feedback_accuracy_improvement'] for r in analysis['value_effects'].values()];completion_gain=any(r['ON_service']['completion_tick'] is not None and r['OFF_service']['completion_tick'] is None for r in analysis['mechanisms'].values());hyp_b='SUPPORTED' if completion_gain and any(x>0 for x in improves) else 'PARTIALLY_SUPPORTED' if any(x>0 for x in improves) else 'NOT_SUPPORTED';onm=analysis['methods']['ON'];capm=analysis['methods']['CAP'];better_mae=onm['complete_three_cell_MAE']<capm['complete_three_cell_MAE'];onreg=onm['ranking']['HF_regret_by_epsilon_best'];capreg=capm['ranking']['HF_regret_by_epsilon_best'];better_decision=max(onreg.values())<min(capreg.values());hyp_c='SUPPORTED' if better_mae and better_decision else 'PARTIALLY_SUPPORTED' if better_mae or better_decision else 'NOT_SUPPORTED'
    report=dict(TASK=TASK,git_head=HEAD,entry_sha256=sha(__file__),analytic_source_sha256=sha(HERE/'blvf.py'),EXECUTION_STATUS=status,BLVF_IMPLEMENTATION_STATUS='IMPLEMENTED_TASK_LOCAL',HISTORICAL_COMPATIBILITY_CHECK_STATUS='COMPLETED_WITH_FINITE_SAMPLE_LIMITS' if checks_finished else 'NOT_COMPLETED',NON_ORACLE_INFORMATION_ISOLATION='VERIFIED_PUBLIC_FIVE_FIELD_ESTIMATOR_AND_BELIEF_ONLY_CONTROL_PATH' if checks_finished and valid else 'NOT_FULLY_VERIFIED',ON_OFF_TREATMENT_VALIDITY='VERIFIED' if valid==6 and fatal is None else 'PARTIAL_OR_NOT_VERIFIED',HISTORICAL_HF_COMPARABILITY='CONDITIONALLY_COMPARABLE_WITH_LIMITATIONS',STARTED_PROXY_CELLS=0 if ctx is None else ctx['started'],VALID_PROXY_CELLS=valid,VALID_FB_OFF_CELLS=off,VALID_FB_ON_CELLS=on,ANALYTIC_ESTIMATE_CALLS=None if counts is None else counts['total'],SCIENCE_ANALYTIC_CALLS=None if counts is None else counts['science'],DIRECT_CHECK_ANALYTIC_CALLS=None if counts is None else counts['direct'],analytic_counts=counts,NONLINEAR_WLS_CALLS=None if forbidden is None else forbidden['WLS'],NONLINEAR_SOLVER_STARTS=None if forbidden is None else forbidden['SOLVER'],R_CALLS=None if forbidden is None else forbidden['R'],ASSIGNMENT_OPTIMIZATION_CALLS=None if forbidden is None else forbidden['ASSIGNMENT_OPTIMIZER'],ACTUAL_STEP_CALLS=0,ACTUAL_WLS_CALLS=0,H_A_FINDINGS=hyp_a,H_B_FINDINGS=hyp_b,H_C_FINDINGS=hyp_c,SWITCH_VALUE_PREDICTION_FINDINGS=None if analysis is None else analysis['value_effects']['SWITCH'],COMPLETION_PREDICTION_FINDINGS=None if analysis is None else {a:dict(OFF=r['OFF_service']['completion_tick'],ON=r['ON_service']['completion_tick']) for a,r in analysis['mechanisms'].items()},RELATIVE_ACTION_VALUE_FINDINGS=None if analysis is None else {m:r['relative_value_difference_errors'] for m,r in analysis['methods'].items()},resource_call_audit=resource,RESOURCE_ACCOUNTING='INCOMPLETE',RESOURCE_COMPLIANCE='NOT_ESTABLISHED',END_TO_END_SPEEDUP='NOT_ESTABLISHED',SCIENTIFIC_VALIDITY=status,INDEPENDENT_ACCEPTANCE='PENDING',PAPER_NOVELTY='NOT_ESTABLISHED',L3_B_EXPLORATORY_STAGE='CLOSED',L3_B_FORMAL_STATUS='L3_B_BLOCKED',H4_TARGET_TURN_EXPLORATION='CLOSED',L3_C_EXECUTION_AUTHORIZATION='NOT_GRANTED',PRODUCTION_ADMISSION='BLOCKED',failure=fatal,H_A_interpretation='classification only for checked samples; 1e-8 position comparison is reporting precision, not an estimator acceptance threshold; not universal WLS-equivalence')
    report['INSUFFICIENT_SENSOR_FRAMES_IN_VALID_CELLS']=None if ctx is None else sum(f['result']['skipped'] for mode in ('OFF','ON') for raw in ctx[mode].values() for f in raw['feedback'])
    w.json('FINAL_REPORT.json',report);lines=['# STFBS-Lite-FB / BLVF V0.1 首次验证','',status,'','| 动作 | 历史CAP | FB-OFF | FB-ON | 历史HF |','|---|---|---|---|---|']
    if analysis is not None:
        for a,r in analysis['matrix'].items():lines.append('| '+' | '.join([a]+[str(r[k]) for k in ('CAP','FB_OFF','FB_ON','HF')])+' |')
        lines+=['','| 方法 | 三格MAE | 最优集合 | HF regret（分别报告） |','|---|---|---|---|']
        for m,r in analysis['methods'].items():lines.append('| '+' | '.join([m,str(r['complete_three_cell_MAE']),str(r['ranking'].get('epsilon_best','NOT_IDENTIFIABLE')),str(r['ranking'].get('HF_regret_by_epsilon_best','NOT_IDENTIFIABLE'))])+' |')
        lines+=['','## 价值效应、相对价值与服务','',json.dumps(analysis['value_effects'],ensure_ascii=False,indent=2),'',json.dumps({m:r['relative_value_difference_errors'] for m,r in analysis['methods'].items()},ensure_ascii=False,indent=2)]
        for a,r in analysis['mechanisms'].items():lines+=['','### '+a,'OFF服务：'+json.dumps(r['OFF_service'],ensure_ascii=False),'ON服务：'+json.dumps(r['ON_service'],ensure_ascii=False),'共同有效控制误差：'+json.dumps(r['paired_prediction'],ensure_ascii=False),'机制分层：'+str({k:r[k] for k in ('actual_control_belief','actual_control','robot_trajectory','endogenous_observation_or_Q','service','value')})]
        lines+=['','## 科学问题结论','', '1. H-A解析替代性：'+hyp_a+'。历史样本逐项位置差、Q、病态及接受行为见BLVF_COMPATIBILITY_CHECK；合法差异保留，有限样本不能证明全部WLS行为等价。','2. H-B未来反馈：'+hyp_b+'。ON/OFF唯一主动因素为是否允许新增模拟反馈进入实际self.frozen；OFF在每次advance前强制检查D60控制belief，shadow只用于诊断。配对效应包含观测、质量及轨迹的自然下游变化，不是单次反馈净直接效应。','3. H-C完整预测器：'+hyp_c+'。按三动作价值误差、相对价值、排序与HF regret共同判断，不以KEEP完成或总体MAE单独判断。','4. SWITCH先验纠正：实际估计/控制belief及服务记录见TRACE，反馈价值及精度效应='+str(analysis['value_effects']['SWITCH'])+'。KEEP—SWITCH相对价值误差见上表，未省略SWITCH低估或失败。','5. MEMBER_CHANGE的继承损失、几何及可能病态：原initial assign与服务规则保持不变，初始P0、Q及拒绝、重置、完成/失败均保存，不为改善分数新增部分服务奖励。','6. 状态、服务、价值、决策不等价：逐动作同时报告共同目标tick误差、Pmax及阈值裕度、价值分项、排序与regret；零服务裕度仅说明达到被截停的完成阈值，不说明额外安全余量。','7. 计算成本：解析调用及其成功/拒绝、无足够传感器而跳过的帧独立计数。实际非线性入口计数见资源审计。单元核心计时包含初始化、事务、每次解析记录及监测开销，完整单元计时另含审计与RAW/TRACE写入；与历史HF窗口口径不同，END_TO_END_SPEEDUP=NOT_ESTABLISHED，不重跑HF追求加速比。','8. 后续H4：只根据本次有限H3证据判断是否值得另行验证。若H-B/H-C得到支持，可考虑在单独授权后检验运动模型失配；本次不启动H4、H2或L3-C。']
    lines+=['','## 接口、资源及限制','', '解析定位只接收sensor_ids、positions、bearings、sigmas、domain。机器精度级叉积阈值仅保障可计算性，原Jacobian病态比1e-4和Q半径0.06保持不变。非法交点不裁剪、不回退WLS。optimizer_converged仅为兼容成功标志，starts为空，没有伪造求解过程。','', '解析成功、belief接受、服务Q PASS是不同判断；直接检查已贯通同一解析结果、真实BridgeFrameProcessor、原质量接口和MODEL consumer，覆盖Q FAIL但belief合法接受与五tick速度差分。','', '历史HF含R和Assignment优化调用，本次固定候选动作保持实际有效团队；只核对历史同动作边界及原科学规则，不宣称完整程序严格等价。结构效应不单独归因于Q。','',json.dumps(report,ensure_ascii=False,indent=2),'', '资源会计INCOMPLETE；宿主准备及入口尾部未知不记零，不宣称整体资源合规。最终退出回执见RESOURCE_RECEIPT.json。结果仅属于一个指定H3条件世界，不证明真实噪声传感器性能、跨世界鲁棒优势或定位理论创新。完成后停止。']
    w.write('REPORT.md','\n'.join(lines));clock.check();files={p.relative_to(HERE).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in HERE.rglob('*') if p.is_file()};w.json('FILE_SHA256.json',dict(files=files,excludes=['self','WORKER_ACCOUNTING.json','RESOURCE_RECEIPT.json']))
    w.accounting_receipt('WORKER_ACCOUNTING.json',dict(worker_pid=os.getpid(),cpu_snapshot=time.process_time(),wall_snapshot=time.monotonic()-origin,analytic_counts=counts,operations=w.operations,resource_accounting='INCOMPLETE'))
    print(json.dumps(dict(status=status,started=report['STARTED_PROXY_CELLS'],valid=valid,analytic_counts=counts,forbidden=forbidden,failure=None if fatal is None else dict(type=fatal['type'],message=fatal['message']),matrix=None if analysis is None else analysis['matrix'],methods=None if analysis is None else {m:dict(MAE=r['complete_three_cell_MAE'],best=r['ranking'].get('epsilon_best'),HF_regret=r['ranking'].get('HF_regret_by_epsilon_best')) for m,r in analysis['methods'].items()}),ensure_ascii=False),flush=True);return 0 if valid==6 and fatal is None else 1

def process_times(handle):
    from ctypes import wintypes
    class FT(ctypes.Structure):_fields_=[('low',wintypes.DWORD),('high',wintypes.DWORD)]
    a,b,c,d=FT(),FT(),FT(),FT();f=ctypes.windll.kernel32.GetProcessTimes;f.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(FT)]*4;f.restype=wintypes.BOOL;require(f(int(handle),ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)),'GET_PROCESS_TIMES');v=lambda x:(x.high<<32)|x.low
    return dict(creation_filetime=v(a),exit_filetime=v(b),kernel_seconds=v(c)/1e7,user_seconds=v(d)/1e7)
def meter():
    prep=read(HERE/'ATTEMPT_002_PREPARATION_ACCOUNTING.json');origin=prep['monotonic_start'];require(type(origin) in (int,float) and math.isfinite(origin),'INVALID_MONOTONIC_START');require(type(prep['elapsed_at_launch']) in (int,float) and math.isfinite(prep['elapsed_at_launch']) and prep['elapsed_at_launch']>=0,'INVALID_PREPARATION_ELAPSED');deadline=origin+1800;require(math.isfinite(deadline) and 0<=time.monotonic()-origin<1800,'PRESTART_WALL_LIMIT');require(time.process_time()+prep['known_preparation_cpu_seconds']<300,'PRESTART_CPU_LIMIT');require(57481<=prep['cumulative_logical_write_bytes']<134217728,'PRESTART_WRITE_LIMIT');p=subprocess.Popen([sys.executable,'-I','-S','-B',str(Path(__file__).resolve()),'--worker',str(origin)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);limit=None
    while p.poll() is None:
        t=process_times(p._handle)
        if time.monotonic()>=deadline or t['kernel_seconds']+t['user_seconds']+time.process_time()>=300:limit='RESOURCE_LIMIT';p.kill();break
        time.sleep(.05)
    out,err=p.communicate();end=time.monotonic();final=process_times(p._handle);entry_cpu=time.process_time();wf=HERE/'WORKER_ACCOUNTING.json';prior=read(wf)['cumulative_logical_write_bytes'] if wf.exists() else prep['cumulative_logical_write_bytes'];writer=Writer(HERE,limit=134217728,initial_written=prior)
    receipt=writer.accounting_receipt('RESOURCE_RECEIPT.json',dict(worker_pid=p.pid,worker_exit_status=p.returncode,analytic_counts=read(HERE/'FINAL_REPORT.json').get('analytic_counts') if (HERE/'FINAL_REPORT.json').exists() else 'INCOMPLETE',worker_final_cpu=final,entry_pid=os.getpid(),entry_cpu_at_worker_exit=entry_cpu,known_cpu_subtotal=entry_cpu+final['kernel_seconds']+final['user_seconds'],limits=dict(cpu=300,wall=1800,cumulative_logical_write_bytes=134217728),wall_start_utc=prep['wall_start_utc'],wall_seconds_at_worker_exit=end-origin,deadline_trigger=limit,path_b='APPROVED: worker exit cutoff; final receipt and handle closure only',resource_accounting='INCOMPLETE',resource_compliance='NOT_ESTABLISHED',unknown_cpu='host preparation and readonly tools; final entry tail INCOMPLETE',wall_limitation='UTC bridge for first readonly preparation timestamp; Python Windows monotonic clock shared across entry and worker thereafter',write_limitation='controlled writes counted; host writes INCOMPLETE',entry_tail='INCOMPLETE; not zero',stdout=out.decode(errors='replace'),stderr=err.decode(errors='replace')));p._handle.Close();print(json.dumps(receipt,ensure_ascii=False),flush=True);return p.returncode
if __name__=='__main__':sys.exit(worker() if '--worker' in sys.argv else meter())
