"""H5 seven-cell authorized run. No old task execution entry is invoked."""
import ast,copy,ctypes,hashlib,importlib.util,itertools,json,math,os,re,subprocess,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
H3=REPO/'reports/stfbs_lite_fb_blvf_initial_validation_001';H4=REPO/'reports/stfbs_lite_fb_blvf_h4_extension_001';OLD=REPO/'reports/stfbs_lite_target_turn_exploration_001/ATTEMPT_003';HIST=REPO/'reports/l3_b_diagnostic_recovery_001_stage_a_20261114';STAGE=REPO/'reports/l3_b_stage_a_minimal_remediation_execution_001_20261114121457';S=REPO/'reports/stfbs_lite_h2_h3_extension_005'
sys.path[:0]=[str(HERE),str(STAGE)]
from recovery import Writer,Clock,require,plain,typed,digest,HistoricalImports
import h5_motion as motion
TASK='STFBS_LITE_FB_BLVF_H5_ARC_EXTENSION_001';HEAD='5c7e8e5a0c44a5f7f161cc601797937229ce9053';ACTIONS=('KEEP','SWITCH','MEMBER_CHANGE')
MATRIX=(('HF','KEEP'),('HF','SWITCH'),('HF','MEMBER_CHANGE'),('OFF','KEEP'),('ON','KEEP'),('ON','SWITCH'),('ON','MEMBER_CHANGE'))
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def isolated(path,extra=None):
    ns=dict(__name__='research.non_oracle.h5_local_'+path.stem,__package__='research.non_oracle',__file__=str(path));ns.update(extra or {});exec(compile(path.read_bytes(),str(path),'exec'),ns);return ns

class Calls:
    def __init__(self,w,clock):self.w=w;self.clock=clock;self.sequence=0;self.total=dict(WLS=0,SOLVER=0,ANALYTIC=0);self.per={};self.records=[];self.active=None;self.inside=dict(WLS=0,SOLVER=0,ANALYTIC=0)
    def invoke(self,kind,method,cell,fn,/,*args,**kw):
        self.clock.check();require(self.active==method,'RESOURCE_METHOD_ROUTE');require((method=='HF')==(kind in ('WLS','SOLVER')),'ESTIMATOR_METHOD_CROSSOVER');limits={'WLS':(63,189),'SOLVER':(600,1800),'ANALYTIC':(63,252)};local,total=limits[kind];counts=self.per.setdefault(cell,dict(WLS=0,SOLVER=0,ANALYTIC=0));require(counts[kind]<local and self.total[kind]<total,'CALL_LIMIT/'+kind)
        self.sequence+=1;cid=self.sequence;counts[kind]+=1;self.total[kind]+=1
        row=dict(call_id=cid,cell=cell,method=method,resource=kind,actual_source='MODEL',provenance='SIMULATED',status='STARTED');self.w.write('RESOURCE_EVENTS.jsonl',json.dumps(row,separators=(',',':'))+'\n',append=True)
        if kind=='ANALYTIC':self.w.write('ANALYTIC_CALLS.jsonl',json.dumps(row,separators=(',',':'))+'\n',append=True)
        self.inside[kind]+=1
        try:out=fn(*args,**kw)
        except BaseException as exc:
            row=dict(call_id=cid,status='FAILED',exception_type=type(exc).__name__,message=str(exc));self.w.write('RESOURCE_EVENTS.jsonl',json.dumps(row,separators=(',',':'))+'\n',append=True)
            if kind=='ANALYTIC':self.w.write('ANALYTIC_CALLS.jsonl',json.dumps(row,separators=(',',':'))+'\n',append=True)
            raise
        else:
            row=dict(call_id=cid,status='RETURNED');self.w.write('RESOURCE_EVENTS.jsonl',json.dumps(row,separators=(',',':'))+'\n',append=True)
            if kind=='ANALYTIC':self.w.write('ANALYTIC_CALLS.jsonl',json.dumps(row,separators=(',',':'))+'\n',append=True)
            return out
        finally:self.inside[kind]-=1;self.clock.check()

class CellBudget:
    def __init__(self,ctx,method,name):
        self.ctx=ctx;self.method=method;self.name=name
        if method=='HF':
            ns=isolated(HIST/'historical/research/cooperative_sensing/estimator.py');self.original_solver=ns['least_squares'];ns['least_squares']=self.solver;self.estimate=ns['estimate'];ctx['hf_code_ids'].add(id(self.estimate.__code__))
        else:self.estimate=ctx['analytic_estimate']
    def check(self):self.ctx['clock'].check()
    def estimator(self,kind):
        require(kind=='MODEL_OBSERVATION_WLS','POLICY_WLS_PROHIBITED');resource='WLS' if self.method=='HF' else 'ANALYTIC'
        return lambda payload:self.ctx['calls'].invoke(resource,self.method,self.name,self.estimate,payload)
    def solver(self,*args,**kw):return self.ctx['calls'].invoke('SOLVER',self.method,self.name,self.original_solver,*args,**kw)
    def choose(self,*args,**kw):raise RuntimeError('R_ASSIGNMENT_OPTIMIZATION_PROHIBITED')

def bootstrap(w,clock):
    require(Path(sys.executable).resolve()==Path(r'D:\miniconda3\envs\dynamic_member_coalition_core\python.exe').resolve(),'PYTHON_IDENTITY');sys.path.insert(0,r'D:\miniconda3\envs\dynamic_member_coalition_core\Lib\site-packages')
    guard=HistoricalImports(HIST/'historical',read(HIST/'HISTORICAL_IDENTITY.json'));guard.install()
    import numpy as np,scipy
    from research.non_oracle import policy
    from research.non_oracle.belief import DT
    from research.cooperative_sensing import estimator
    import blvf
    require(DT==motion.DT==.05 and np.__version__=='2.1.3' and scipy.__version__=='1.15.3','ENVIRONMENT')
    pins={H3/'fb_entry_attempt_002.py':'75226d448a454d8b6f711b52f7395ce844d03258dcdf4747e1d935c20b599117',H4/'h4_entry.py':'354d416d3e24da6ee661f532db9c8a4aec5643e4c32705bf5c2ecf364c59fe61',HERE/'blvf.py':'204fc231bf78004c33daf151983d751685666da75ed9e9b911abb83854c7365e'}
    require(all(sha(p)==v for p,v in pins.items()),'FROZEN_SOURCE_IDENTITY');require('任务关闭状态：CLOSED' in (H4/'BLVF_H4_FINAL_INDEPENDENT_SCIENTIFIC_ACCEPTANCE.md').read_text(encoding='utf-8'),'H4_CLOSURE')
    base=load(H3/'fb_entry_attempt_002.py','h5_reuse_h3');h4=load(H4/'h4_entry.py','h5_reuse_h4');sys.path.insert(0,str(HERE))
    mapping=read(S/'MODEL_WORLD_MAPPING.json');baseworld=copy.deepcopy(mapping['H3']);baseworld['motion']={int(k):v for k,v in baseworld['motion'].items()};require(baseworld['world_digest']=='f2cc0471de904e5ec8af765f10ccc85b7488b06262a374dfbc614343adb6dedc' and digest({k:v for k,v in baseworld.items() if k!='world_digest'})==baseworld['world_digest'],'H3_WORLD')
    cp=Path(read(S/'H3_KEEP/authorization.json')['candidate_path']);c=read(cp)['candidate'];view=copy.deepcopy(c['a2_policy_view']);seed=copy.deepcopy(c['consumer_seed']);require(digest(seed)==read(S/'S4_STATIC.json')['seed_digest']=='cf5ddd31c60ccfb87bbcd7fef2cb89ef24d5cd803983910fc585681bfde6f6f5','SEED')
    view['beliefs']={int(k):v for k,v in view['beliefs'].items()}
    for key in ('internal_states_at_D60','accepted_position_history','accepted_receipts'):seed[key]={int(k):v for k,v in seed[key].items()}
    require(digest(view)==baseworld['public_digest']=='a37cde42a2c4c147f4abc9289e5de693790218d17bcafcbe7fe3cfb49a9d6602' and not seed['pending_observations'],'PUBLIC_D60')
    world,physical=motion.make_world(baseworld,digest);require(digest({k:v for k,v in world.items() if k!='world_digest'})==world['world_digest'],'H5_WORLD_IDENTITY');w.json('WORLD_H5_ARC.json',dict(MODEL_world=plain(world),physical_definition=physical,base_world_digest=baseworld['world_digest'],D60_view_digest=digest(view)))
    model=isolated(OLD/'model_h4.py',dict(_h4_point=motion.point,_velocity_at=motion.velocity_at,_escape_time=motion.escape_time));audit=isolated(OLD/'audit_h4.py',dict(_h4_point=motion.point))
    # Reuse only comparison functions/constant, not the old offline entry or its timers.
    tree=ast.parse((H4/'offline_finalize.py').read_text(encoding='utf-8'));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('diffs','identity_path','frame_binding') or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='IDENTITY_PATTERNS' for t in n.targets)];identity=dict(re=re,digest=digest);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(H4/'offline_finalize.py'),'exec'),identity)
    protected={str(p):sha(p) for p in (cp,S/'MODEL_WORLD_MAPPING.json',S/'CANDIDATE_FREEZE.json',S/'S4_STATIC.json',H3/'blvf.py',H3/'fb_entry_attempt_002.py',H4/'h4_entry.py',H4/'offline_finalize.py',H4/'BLVF_H4_FINAL_INDEPENDENT_SCIENTIFIC_ACCEPTANCE.md',OLD/'model_h4.py',OLD/'audit_h4.py',HIST/'historical/research/cooperative_sensing/estimator.py')}
    ctx=dict(w=w,clock=clock,guard=guard,view=view,seed=seed,world=world,physical=physical,Branch=base.make_fb_branch(model['Branch']),base=base,h4=h4,point=motion.point,velocity_at=motion.velocity_at,escape_time=motion.escape_time,audit=audit['audit'],service_audit=audit['service_audit'],candidates=read(S/'CANDIDATE_FREEZE.json'),calls=Calls(w,clock),analytic_estimate=blvf.estimate,hf_code_ids=set(),forbidden_ids={id(policy.decide.__code__):'R',id(policy.solve.__code__):'ASSIGNMENT_OPTIMIZER',id(estimator.estimate.__code__):'UNROUTED_WLS'},solver_code=id(estimator.least_squares.__code__),analytic_code=id(blvf.estimate.__code__),forbidden_counts=dict(R=0,ASSIGNMENT_OPTIMIZER=0,UNROUTED_ESTIMATE=0),started=0,starts_by_method=dict(HF=0,BLVF=0),results={},traces={},timings={},identity=identity,protected=protected)
    # No estimators or Branch instances are executed during these mathematical/interface checks.
    require(motion.velocity_at(world,0,75)==list(baseworld['motion'][0]['velocity']),'D75_VELOCITY')
    for tick in (75,85):
        p=motion.point(world,0,tick);v=motion.velocity_at(world,0,tick)
        for delta in (-1e-6,1e-6):require(math.dist(motion.point(world,0,tick+delta),p)<1e-6 and math.dist(motion.velocity_at(world,0,tick+delta),v)<1e-6,'ARC_CONTINUITY')
    for tick in (60,75,77.5,80,85,100,120):require(abs(math.hypot(*motion.velocity_at(world,0,tick))-physical['speed'])<1e-14 and list(motion.point(world,1,tick))==baseworld['motion'][1]['position'],'ARC_SPEED_OR_T1')
    require(abs(math.atan2(*reversed(motion.velocity_at(world,0,85)))-.5)<1e-14,'FINAL_ANGLE')
    xs=motion.point(world,0,75)[0];xe=motion.point(world,0,85)[0]
    escape_checks=[]
    for side in (xs-.01,(xs+xe)/2,xe+.01):
        t=motion.escape_time(world,0,3.,side);require(abs(motion.point(world,0,t/.05)[0]-side)<1e-12,'ANALYTIC_ESCAPE');escape_checks.append(dict(side=float(side),time=float(t)))
    require(motion.escape_time(world,0,4.,9.)==4. and motion.escape_time(world,1,3.,20.)==math.inf,'ESCAPE_QUERY_SEMANTICS')
    routes=[dict(method=m,action=a,feedback_enabled=m!='OFF',estimator='NINE_START_WLS' if m=='HF' else 'ANALYTIC_BEARING_INTERSECTION',cell='H5_'+m+'_'+a) for m,a in MATRIX]
    require(len(routes)==7 and sum(r['method']=='HF' for r in routes)==3,'METHOD_MATRIX')
    w.json('MINIMAL_VALIDATION.json',dict(status='PASS',estimator_calls=0,scientific_starts=0,checks=['frozen source and D60 identities','H5 world digest','DT and dependencies','D75 D85 position and velocity continuity','constant speed and final angle','unchanged T1','three analytic escape segments and query semantics','method routing','separate HF and BLVF budgets','common feedback wrapper and OFF guard','H5 standalone summary'],escape_checks=escape_checks,routes=routes))
    w.json('EXPERIMENT_CONFIG.json',dict(task=TASK,attempt_id='ATTEMPT_002',git_head=HEAD,entry_sha256=sha(__file__),motion_sha256=sha(HERE/'h5_motion.py'),blvf_sha256=sha(HERE/'blvf.py'),world=plain(world),physical_definition=physical,D60_digest=digest(view),seed_digest=digest(seed),candidate_source=str(cp),candidate_sha256=sha(cp),routes=routes,protected_source_hashes=protected,environment=dict(python=sys.executable,python_version=sys.version,numpy=np.__version__,numpy_path=np.__file__,scipy=scipy.__version__,scipy_path=scipy.__file__),limits=dict(cells=7,HF=3,BLVF=4,WLS_per_cell=63,WLS_total=189,solver_per_cell=600,solver_total=1800,analytic_per_cell=63,analytic_total=252,direct_estimates=0,cpu=300,wall=1800,writes=134217728),information_isolation='five-field estimator inputs; legal frozen beliefs only; motion parameters confined to simulator and offline truth audits',shared_wrapper='H3 make_fb_branch on H4 model base with H5 motion; no old run_cell/run_hf or execution entries',epsilon=1e-8))
    w.json('RUNTIME_BINDINGS_BEFORE_SCIENCE.json',dict(project_modules=guard.audit(),namespace_paths=guard.namespace_paths,task_source_hashes=protected,local_motion=str(HERE/'h5_motion.py'),local_BLVF=str(HERE/'blvf.py'),HF_estimator_source=str(HIST/'historical/research/cooperative_sensing/estimator.py'),HF_binding='each cell isolated original estimator globals; least_squares wrapper records actual calls; original function bodies unchanged',lazy_imports='NOT_VERIFIED_UNTIL_USED'))
    return ctx

def profile_guard(ctx):
    def profile(frame,event,arg):
        if event!='call':return
        cid=id(frame.f_code);calls=ctx['calls']
        if cid in ctx['forbidden_ids']:
            kind=ctx['forbidden_ids'][cid];ctx['forbidden_counts']['UNROUTED_ESTIMATE' if kind=='UNROUTED_WLS' else kind]+=1;raise RuntimeError('FORBIDDEN_ENTRY/'+kind)
        if cid in ctx['hf_code_ids']:require(calls.active=='HF' and calls.inside['WLS']>0,'UNROUTED_HF_ESTIMATOR')
        if cid==ctx['solver_code']:require(calls.active=='HF' and calls.inside['SOLVER']>0,'UNROUTED_OR_BLVF_SOLVER')
        if cid==ctx['analytic_code']:require(calls.active in ('ON','OFF') and calls.inside['ANALYTIC']>0,'HF_OR_UNROUTED_ANALYTIC')
    return profile

def service_trace(ctx,branch,r,action):
    summary=ctx['base'].service_summary(ctx,branch,r,action);j=1 if action=='SWITCH' else 0;left=branch.initial_service[j]['endpoint'];endpoints={f['frame']['tick']:f['endpoint'] for f in r['feedback'] if f['frame']['target_id']==j};intervals=[]
    for frame in r['frames']:
        right=endpoints.get(frame['tick'])
        if right is None:continue
        if left is not None:intervals.append(dict(left_tick=frame['tick']-1,right_tick=frame['tick'],G=bool(left['G'] and right['G']),GQ=bool(left['G'] and right['G'] and left['quality']['status']==right['quality']['status']=='PASS')))
        left=right
    summary.update(G_intervals=[x for x in intervals if x['G']],GQ_intervals=[x for x in intervals if x['GQ']],terminal_positions=r['frames'][-1]['positions'],terminal_status=r['status'],natural_release_events=[e for e in r['events'] if e['kind'] in ('completed','escaped')])
    details=[]
    for row in branch.consumer_records:
        e=copy.deepcopy(row);j=e['target'];k=e['measurement_tick'];s=e['reference_tick'];ref=next((p for t,p in branch.consumer.history[j] if t==s),None);f=next(f for f in r['feedback'] if f['frame']['target_id']==j and f['frame']['tick']==k);est=f['result']['estimate_result']
        e.update(reference_position=ref,accepted_position=est['estimate'] if e['accepted'] else None,unclipped_difference_velocity=None if not e['accepted'] or ref is None else [(x-y)/((k-s)*.05) for x,y in zip(est['estimate'],ref)],actual_estimator='NINE_START_WLS' if r['method']=='HF_NINE_START_WLS' else 'ANALYTIC_BEARING_INTERSECTION')
        details.append(e)
    return summary,details

def run_cell(ctx,method,action):
    w=ctx['w'];ctx['clock'].check();require(ctx['started']<7,'SEVEN_CELL_LIMIT');category='HF' if method=='HF' else 'BLVF';require(ctx['starts_by_method'][category]<(3 if category=='HF' else 4),'METHOD_START_LIMIT');ctx['started']+=1;ctx['starts_by_method'][category]+=1;name='H5_'+method+'_'+action;ctx['calls'].active=method;ctx['results'][name]=dict(status='STARTED_NO_VALID_RESULT',method=method,action=action)
    actions=copy.deepcopy(next(c['actions'] for c in ctx['candidates'] if c['kind']==action));view=copy.deepcopy(ctx['view']);seed=copy.deepcopy(ctx['seed']);world=copy.deepcopy(ctx['world'])
    w.json('CALLS/'+name+'_STARTED.json',dict(task=TASK,cell=name,ordinal=ctx['started'],method=method,feedback_enabled=method!='OFF',input_digest=digest(plain([view,seed,world,actions]))))
    from research.non_oracle.stfbs_d1a_history_audit import register_context,audit_branch_independent
    context=register_context(name,{h['target_id']:copy.deepcopy(h) for h in view['histories']});branch=None;start=time.monotonic();cpu=time.process_time();prepare_start=time.monotonic();prepare_cpu=time.process_time()
    try:
        budget=CellBudget(ctx,method,name);method_prepare=dict(wall=time.monotonic()-prepare_start,cpu=time.process_time()-prepare_cpu);core=time.monotonic();core_cpu=time.process_time()
        branch=ctx['Branch'](view,seed,world,name,budget,method!='OFF');r=branch.fixed_run(actions);core_t=dict(wall=time.monotonic()-core,cpu=time.process_time()-core_cpu)
        # Correct outer identity before first RAW persistence; preserve native estimator objects.
        r.update(method='HF_NINE_START_WLS' if method=='HF' else 'STFBS_LITE_FB_BLVF_V0.1',method_route=method,estimator_route='NINE_START_WLS' if method=='HF' else 'ANALYTIC_BEARING_INTERSECTION')
        w.json('RAW/'+name+'.json',plain(r))
        audits=dict(history=audit_branch_independent(branch,context=context),service=ctx['service_audit'](r,view),physical_economic=ctx['audit'](r,view));control,records=ctx['h4'].control_audit(ctx,r);audits['actual_control']=control
        require(all(v['status']=='PASS' for v in audits.values()) and len(r['frames'])==60 and r['frames'][-1]['tick']==120,'CELL_AUDIT_OR_HORIZON')
        counts=ctx['calls'].per.get(name,dict(WLS=0,SOLVER=0,ANALYTIC=0));expected=sum(f['result']['estimator_called'] for f in r['feedback']);require(counts['WLS' if method=='HF' else 'ANALYTIC']==expected and r['endpoint_fusions']==len(r['feedback']),'ACTUAL_ESTIMATOR_ROUTE_COUNT')
        if method=='OFF':require(all(typed(f['actual_control_beliefs'])==typed(view['beliefs']) for f in branch.freeze_records),'OFF_CONTROL_LEAK')
        summary,details=service_trace(ctx,branch,r,action)
        trace=plain(dict(method=method,feedback_enabled=method!='OFF',control_records=records,freeze_records=branch.freeze_records,actual_consumer_records=details,accepted_history=branch.consumer.history,accepted_receipts=branch.consumer.accepted_receipts,pending_D120=branch.consumer.pending,consumer_terminal_states=branch.consumer.states,physical_histories=branch.histories,initial_service=branch.initial_service,hold_checks=branch.hold_checks,service_summary=summary,audits=audits,counts=counts,insufficient_sensor_frames=sum(f['result']['skipped'] for f in r['feedback'])))
        w.json('TRACE/'+name+'.json',trace);timing=dict(method=method,action=action,method_preparation=method_prepare,core=core_t,complete_cell=dict(wall=time.monotonic()-start,cpu=time.process_time()-cpu),core_scope='Branch initialization, original transactions, model loop, estimator/solver wrappers, per-call persistence and profile guard; estimator namespace setup excluded and separately timed',complete_scope='method preparation, core, RAW write, saved-record history/service/physical/control audit and TRACE write; own timing-record write and task analysis excluded')
        w.json('TIMING/'+name+'.json',timing);ctx['results'][name]=dict(status='VALID_PENDING_INDEPENDENT_REVIEW',method=method,action=action,net=r['net']);ctx['traces'][name]=dict(raw=r,trace=trace);ctx['timings'][name]=timing
    except BaseException as exc:
        ctx['results'][name]['status']='STARTED_FAILED_OR_NOT_ACCEPTED';w.json('RAW/'+name+'_FAILURE.json',dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),tick=None if branch is None else branch.tick,resource_counts=ctx['calls'].per.get(name)))
        if branch is not None:w.json('RAW/'+name+'_PARTIAL.json',plain(dict(frames=branch.frames,feedback=branch.feedback,events=branch.events,decisions=branch.decisions,consumer_records=branch.consumer_records,freeze_records=branch.freeze_records)))
        raise

def rank(values):
    if len(values)!=3:return dict(status='NOT_IDENTIFIABLE',available=list(values))
    return dict(status='VALID',strict_order=sorted(ACTIONS,key=lambda a:-values[a]),exact_ties=[[a for a in ACTIONS if values[a]==v] for v in sorted(set(values.values()),reverse=True)],epsilon_best=[a for a in ACTIONS if max(values.values())-values[a]<=1e-8],actual_selection='NOT_SPECIFIED')

def adaptation(ctx,name):
    if name not in ctx['traces']:return dict(status='NOT_IDENTIFIABLE')
    tr=ctx['traces'][name]['trace'];raw=ctx['traces'][name]['raw'];f=next(f for f in tr['freeze_records'] if f['tick']==80);b=f['actual_control_beliefs']['0'];k=b['estimate_tick'];row=next((r for r in tr['actual_consumer_records'] if r['target']==0 and r['freeze_tick']==80 and r['measurement_tick']==k and r['accepted']),None)
    if row is None:return dict(status='NOT_IDENTIFIABLE',actual_belief=b)
    s=row['reference_tick'];p=row['accepted_position'];q=row['reference_position'];truek=motion.point(ctx['world'],0,k).tolist();vk=motion.velocity_at(ctx['world'],0,k);vc=motion.velocity_at(ctx['world'],0,80);v=b['velocity_estimate'];mean=None if s is None else [(x-y)/((k-s)*.05) for x,y in zip(truek,motion.point(ctx['world'],0,s))]
    def angle(x,y):return None if math.hypot(*x)==0 or math.hypot(*y)==0 else (math.atan2(x[1],x[0])-math.atan2(y[1],y[0])+math.pi)%(2*math.pi)-math.pi
    return dict(status='IDENTIFIABLE',freeze_tick=80,actual_control_belief=b,event=row,reference_true_position=None if s is None else motion.point(ctx['world'],0,s).tolist(),accepted_true_position=truek,true_interval_mean_velocity=mean,unclipped_velocity=row['unclipped_difference_velocity'],final_belief_velocity=v,instantaneous_velocity_at_estimate_tick=vk,instantaneous_velocity_at_control_tick=vc,velocity_vector_error_at_estimate_tick=math.dist(v,vk),velocity_vector_error_at_control_tick=math.dist(v,vc),speed_error_at_estimate_tick=math.hypot(*v)-math.hypot(*vk),direction_error_at_estimate_tick=angle(v,vk),estimate_minus_true_mean=None if mean is None else [x-y for x,y in zip(v,mean)],true_mean_minus_anchor_instantaneous=None if mean is None else [x-y for x,y in zip(mean,vk)],velocity_clipping_or_retention_difference=None if row['unclipped_difference_velocity'] is None else [x-y for x,y in zip(v,row['unclipped_difference_velocity'])],D100_control_activity='NOT_ACTIVE_AFTER_COMPLETION' if any(e['target']==0 and e['kind']=='completed' and e['tick']<=100 for e in raw['events']) else 'CHECK_SAVED_CONTROL_RECORDS')

def analyze(ctx):
    traces=ctx['traces'];valid={m:{a:traces['H5_'+m+'_'+a]['raw']['net'] for a in ACTIONS if 'H5_'+m+'_'+a in traces} for m in ('HF','ON','OFF')};matrix={a:{} for a in ACTIONS}
    for a in ACTIONS:
        for m in ('HF','ON','OFF'):
            name='H5_'+m+'_'+a;matrix[a][m]=dict(status='NOT_RUN' if (m,a) not in MATRIX else ctx['results'].get(name,{}).get('status','NOT_STARTED'),value=valid[m].get(a))
    common=[a for a in ACTIONS if a in valid['HF'] and a in valid['ON']];errors={a:dict(signed_error=valid['ON'][a]-valid['HF'][a],AE=abs(valid['ON'][a]-valid['HF'][a])) for a in common};ranks={m:rank(v) for m,v in valid.items()};regret=None
    if len(valid['HF'])==len(valid['ON'])==3:regret={a:max(valid['HF'].values())-valid['HF'][a] for a in ranks['ON']['epsilon_best']}
    analysis=dict(matrix=matrix,errors=errors,common_actions=common,complete_three_cell_MAE=None if len(common)!=3 else sum(e['AE'] for e in errors.values())/3,subset_mean_AE=None if not common else sum(e['AE'] for e in errors.values())/len(common),denominator=len(common),relative_errors={a+'-'+b:None if a not in common or b not in common else (valid['ON'][a]-valid['ON'][b])-(valid['HF'][a]-valid['HF'][b]) for a,b in itertools.combinations(ACTIONS,2)},rankings=ranks,HF_regret_by_ON_epsilon_best=regret,H5_A_MOTION_ESTIMATION_FINDINGS={m:adaptation(ctx,'H5_'+m+'_KEEP') for m in ('HF','ON')},H5_B_FEEDBACK_SERVICE_FINDINGS=dict(FEEDBACK_EFFECT_IDENTIFIED='NOT_IDENTIFIABLE'),H5_C_CONDITIONAL_VALUE_FINDINGS='IDENTIFIABLE_COMPLETE_MATRIX' if len(common)==3 else 'PARTIAL_OR_NOT_IDENTIFIABLE',H5_COMPUTATIONAL_SIMPLIFICATION_FINDINGS=ctx['calls'].total,timings=ctx['timings'],prediction_pairs={},propagation_decomposition={})
    def index(records):
        out={}
        for r in records:
            key=(r['target'],r['tick'])
            if key in out:require(out[key]['prediction_position']==r['prediction_position'] and out[key]['prediction_velocity']==r['prediction_velocity'],'TARGET_TICK_PREDICTION_DUPLICATE')
            else:out[key]=r
        return out
    for left,right in [('HF','ON'),('OFF','ON')]:
        for a in ACTIONS:
            ln='H5_'+left+'_'+a;rn='H5_'+right+'_'+a
            if ln not in traces or rn not in traces:continue
            il=index(traces[ln]['trace']['control_records']);ir=index(traces[rn]['trace']['control_records']);keys=sorted(il.keys()&ir.keys());p=dict(common_target_ticks=[list(k) for k in keys],denominator=len(keys),left_valid_count=len(il),right_valid_count=len(ir))
            for side,idx in [('left',il),('right',ir)]:
                for field in ('position_error','velocity_error'):p[side+'_'+field]=None if not keys else sum(idx[k][field] for k in keys)/len(keys)
            analysis['prediction_pairs'][left+'/'+right+'/'+a]=p
    if 'H5_OFF_KEEP' in traces and 'H5_ON_KEEP' in traces:
        off=traces['H5_OFF_KEEP'];on=traces['H5_ON_KEEP'];ident=ctx['identity'];fo=[f for f in off['raw']['feedback'] if f['frame']['tick']<=80];fn=[f for f in on['raw']['feedback'] if f['frame']['tick']<=80];require(len(fo)==len(fn),'KEEP_EARLY_FRAME_COUNT');diff=[]
        for x,y in zip(fo,fn):
            ident['frame_binding'](x,'H5_OFF_KEEP');ident['frame_binding'](y,'H5_ON_KEEP');rows=ident['diffs'](x,y);require(all(ident['identity_path'](r['path']) and not r.get('missing_key') for r in rows),'KEEP_SCIENTIFIC_OBSERVATION_DIFFERENCE');diff.extend(dict(tick=x['frame']['tick'],**r) for r in rows)
        require(not ident['diffs']([f for f in off['raw']['frames'] if f['tick']<=80],[f for f in on['raw']['frames'] if f['tick']<=80]),'KEEP_EARLY_PHYSICAL_DIFFERENCE');require(off['trace']['initial_service']==on['trace']['initial_service'],'KEEP_INITIAL_SERVICE_DIFFERENCE')
        ov=off['raw']['net'];nv=on['raw']['net'];feedback=analysis['H5_B_FEEDBACK_SERVICE_FINDINGS'];feedback.update(FEEDBACK_EFFECT_IDENTIFIED='YES',Delta_V_FB=nv-ov,I_FB=None if 'KEEP' not in valid['HF'] else abs(ov-valid['HF']['KEEP'])-abs(nv-valid['HF']['KEEP']),FEEDBACK_BENEFIT_SUPPORTED='POSITIVE_NET_VALUE_EFFECT' if nv>ov else 'ZERO_NET_VALUE_EFFECT' if nv==ov else 'NEGATIVE_NET_VALUE_EFFECT',pre_D80_scientific_equivalence='PASS',pre_D80_feedback_pairs=len(fo),identity_only_differences=diff,mechanism_layers={})
        layers=feedback['mechanism_layers']
        for label,field in [('G_intervals','G_intervals'),('GQ_intervals','GQ_intervals'),('continuous_progress','Pmax'),('completion','completion_tick')]:layers[label]='CHANGED' if off['trace']['service_summary'][field]!=on['trace']['service_summary'][field] else 'UNCHANGED'
        for label,field in [('actual_control','control'),('robot_trajectory','positions')]:layers[label]='CHANGED' if [f[field] for f in off['raw']['frames']]!=[f[field] for f in on['raw']['frames']] else 'UNCHANGED'
        layers['belief']='CHANGED' if [f['actual_control_beliefs'] for f in off['trace']['freeze_records']]!=[f['actual_control_beliefs'] for f in on['trace']['freeze_records']] else 'UNCHANGED'
        layers['subsequent_observations']='CHANGED' if [f['result']['payload'] for f in off['raw']['feedback']]!=[f['result']['payload'] for f in on['raw']['feedback']] else 'UNCHANGED';layers['Q_classification']='CHANGED' if [f['result']['quality']['status'] for f in off['raw']['feedback']]!=[f['result']['quality']['status'] for f in on['raw']['feedback']] else 'UNCHANGED';layers['economic_value']='CHANGED' if ov!=nv else 'UNCHANGED'
    for name,t in traces.items():
        rows=[]
        for r in index(t['trace']['control_records']).values():
            j=r['target'];tick=r['tick'];b=r['actual_control_belief'];k=b['estimate_tick'];dt=(tick-k)*.05
            if k<60:rows.append(dict(target=j,tick=tick,status='NOT_IDENTIFIABLE'));continue
            pk=motion.point(ctx['world'],j,k);vk=motion.velocity_at(ctx['world'],j,k);truth=motion.point(ctx['world'],j,tick)
            if r['cap_applied']:
                rows.append(dict(target=j,tick=tick,status='ORIGINAL_CAP_ACTIVE',actual_prediction_error=[x-y for x,y in zip(r['prediction_position'],truth)],note='uncapped decomposition not applied'))
            else:
                position=[x-y for x,y in zip(b['position_estimate'],pk)];velocity=[(x-y)*dt for x,y in zip(b['velocity_estimate'],vk)];mismatch=[x+y*dt-z for x,y,z in zip(pk,vk,truth)];total=[x-y for x,y in zip(r['prediction_position'],truth)];require(max(abs(sum(v)-e) for v,e in zip(zip(position,velocity,mismatch),total))<1e-12,'PROPAGATION_DECOMPOSITION')
                rows.append(dict(target=j,tick=tick,status='UNCAPPED_IDENTITY',position_estimation_error=position,velocity_estimation_times_age=velocity,instantaneous_CV_model_mismatch=mismatch,actual_prediction_error=total))
        analysis['propagation_decomposition'][name]=rows
    analysis['single_run_timing_comparisons']={}
    for a in ACTIONS:
        hf=ctx['timings'].get('H5_HF_'+a);on=ctx['timings'].get('H5_ON_'+a)
        if hf and on:analysis['single_run_timing_comparisons'][a]=dict(core_cpu_HF_over_ON=hf['core']['cpu']/on['core']['cpu'] if on['core']['cpu'] else None,core_wall_HF_over_ON=hf['core']['wall']/on['core']['wall'] if on['core']['wall'] else None,HF_method_setup=hf['method_preparation'],ON_method_setup=on['method_preparation'],scope='same core boundary; separate namespace setup recorded; one pair, not statistical speedup or end-to-end advantage')
    analysis['END_TO_END_SPEEDUP']='NOT_ESTABLISHED';analysis['service']={n:t['trace']['service_summary'] for n,t in traces.items()}
    ctx['w'].json('VALUE_MATRIX.json',matrix);ctx['w'].json('SCIENTIFIC_ANALYSIS.json',plain(analysis));return analysis

def resource_audit(ctx):
    rows=[json.loads(line) for line in (HERE/'RESOURCE_EVENTS.jsonl').read_text().splitlines()] if (HERE/'RESOURCE_EVENTS.jsonl').exists() else [];starts={};ends={};counts=dict(WLS=0,SOLVER=0,ANALYTIC=0)
    for row in rows:
        key=row['call_id']
        if row['status']=='STARTED':require(key not in starts,'DUPLICATE_RESOURCE_ID');starts[key]=row;counts[row['resource']]+=1
        else:require(key in starts and key not in ends and row['status'] in ('RETURNED','FAILED'),'RESOURCE_EVENT_CLOSURE');ends[key]=row
    require(starts.keys()==ends.keys() and counts==ctx['calls'].total,'DISK_RUNTIME_RESOURCE_RECONCILIATION')
    return dict(status='PASS',started=len(starts),closed=len(ends),counts=counts,failed_internal_calls=sum(r['status']=='FAILED' for r in ends.values()),per_cell=ctx['calls'].per,forbidden=ctx['forbidden_counts'],direct_estimator_calls=0)

def worker():
    prep=read(HERE/'PREPARATION_ACCOUNTING.json');origin=float(sys.argv[-1]);clock=Clock(origin,cpu_limit=300,wall_limit=1800);w=Writer(HERE,initial_written=prep['cumulative_logical_write_bytes'],clock=clock);ctx=None;analysis=None;fatal=None;old=sys.getprofile();audit=None
    try:
        ctx=bootstrap(w,clock);sys.setprofile(profile_guard(ctx))
        for method,action in MATRIX:run_cell(ctx,method,action)
    except BaseException as exc:fatal=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());w.json('FAILURE.json',fatal)
    finally:sys.setprofile(old)
    if ctx is not None:
        try:
            analysis=analyze(ctx);audit=resource_audit(ctx);checks={p:sha(p)==h for p,h in ctx['protected'].items()};require(all(checks.values()),'HISTORICAL_PROTECTION');w.json('PROTECTION_CHECK.json',checks);w.json('RUNTIME_BINDINGS_FINAL.json',dict(modules=ctx['guard'].audit(),namespace_paths=ctx['guard'].namespace_paths,actual_HF_estimator_code_ids=sorted(ctx['hf_code_ids']),HF_source=str(HIST/'historical/research/cooperative_sensing/estimator.py'),untriggered_lazy_imports='NOT_VERIFIED'))
        except BaseException as exc:
            extra=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());fatal=fatal or extra;w.json('FINALIZATION_FAILURE.json',extra)
    valid=0 if ctx is None else len(ctx['traces']);status='VALID_SEVEN_CELL_RESULT_PENDING_INDEPENDENT_ACCEPTANCE' if valid==7 and fatal is None else 'PARTIAL_RESULTS' if valid else 'BLOCKED_NO_ACCEPTED_CELLS'
    report=dict(task=TASK,attempt_id='ATTEMPT_002',git_head=HEAD,status=status,started=0 if ctx is None else ctx['started'],valid=valid,world_digest=None if ctx is None else ctx['world']['world_digest'],counts=None if ctx is None else ctx['calls'].total,starts_by_method=None if ctx is None else ctx['starts_by_method'],failure=fatal,resource_audit=audit,MAE=None if analysis is None else analysis['complete_three_cell_MAE'],rankings=None if analysis is None else analysis['rankings'],HF_regret=None if analysis is None else analysis['HF_regret_by_ON_epsilon_best'],H5_A_MOTION_ESTIMATION_FINDINGS='NOT_IDENTIFIABLE' if analysis is None else analysis['H5_A_MOTION_ESTIMATION_FINDINGS'],H5_B_FEEDBACK_SERVICE_FINDINGS='NOT_IDENTIFIABLE' if analysis is None else {k:v for k,v in analysis['H5_B_FEEDBACK_SERVICE_FINDINGS'].items() if k!='identity_only_differences'},H5_C_CONDITIONAL_VALUE_FINDINGS='NOT_IDENTIFIABLE' if analysis is None else analysis['H5_C_CONDITIONAL_VALUE_FINDINGS'],H5_COMPUTATIONAL_SIMPLIFICATION_FINDINGS='NOT_IDENTIFIABLE' if analysis is None else analysis['H5_COMPUTATIONAL_SIMPLIFICATION_FINDINGS'],entry_sha256=sha(__file__),motion_sha256=sha(HERE/'h5_motion.py'),blvf_sha256=sha(HERE/'blvf.py'),RESOURCE_ACCOUNTING='INCOMPLETE',RESOURCE_COMPLIANCE='NOT_ESTABLISHED',END_TO_END_SPEEDUP='NOT_ESTABLISHED',INDEPENDENT_SCIENTIFIC_ACCEPTANCE='PENDING',PAPER_NOVELTY='NOT_ESTABLISHED',PRODUCTION_ADMISSION='BLOCKED',L3_C_EXECUTION_AUTHORIZATION='NOT_GRANTED',H3_BLVF_INITIAL_VALIDATION='CLOSED',H4_BLVF_EXTENSION='CLOSED',BLVF_ALGORITHM_VERSION='V0.1')
    w.json('FINAL_REPORT.json',plain(report));lines=['# H5-ARC BLVF V0.1 七格科学结果','',status,'','本报告是执行及机制证据汇总，独立科学验收待完成。','', '| 动作 | HF | FB-ON | FB-OFF |','|---|---|---|---|']
    if analysis is not None:
        for a,row in analysis['matrix'].items():lines.append('| '+' | '.join([a]+[str(row[m]['value']) if row[m]['value'] is not None else row[m]['status'] for m in ('HF','ON','OFF')])+' |')
        lines+=['','## H5-A：实际区间平均速度与瞬时速度','',json.dumps(analysis['H5_A_MOTION_ESTIMATION_FINDINGS'],ensure_ascii=False,indent=2),'','## H5-B：KEEP反馈条件闭环总效应','',json.dumps(report['H5_B_FEEDBACK_SERVICE_FINDINGS'],ensure_ascii=False,indent=2),'','## H5-C：价值及排序','',json.dumps(dict(errors=analysis['errors'],MAE=analysis['complete_three_cell_MAE'],relative_errors=analysis['relative_errors'],rankings=analysis['rankings'],HF_regret=analysis['HF_regret_by_ON_epsilon_best']),ensure_ascii=False,indent=2),'','## 服务和经济账本','',json.dumps(analysis['service'],ensure_ascii=False,indent=2),'','## 计算计数及本次单对耗时','',json.dumps(dict(resource_audit=audit,timing=analysis['single_run_timing_comparisons']),ensure_ascii=False,indent=2)]
    lines+=['','## 解释及限制','', '本次H5轨迹是指定条件世界，不是公开信息驱动的未来情景生成。瞬时速度与真实历史平均速度分别记录；超过原一秒截断的记录不套用未截断分解。D100终端belief不等于仍在发挥控制作用。','', 'HF和ON使用相同原consumer及固定动作事务，估计方法不同，D80之前允许合法估计、Q及服务差异。仅KEEP ON/OFF受主动反馈等同性约束。反馈效应是位置、速度、时间锚点及后续观测服务共同改变的总效应，不只归因于一次速度更新。','', '若HF和BLVF共同未完成而价值一致，应区分原控制能力限制和价值预测成功。真实噪声、跨世界鲁棒决策、论文创新性及一般端到端效率未建立。单次配对计时只描述本次执行，方法专属准备单列，未重复性能实验。','', '资源会计INCOMPLETE；宿主准备及尾部未知不记零。原科学RAW、TRACE、方法对象、调用日志和保护记录均保存。完成后停止，不追加世界或自动改算法。','',json.dumps(plain(report),ensure_ascii=False,indent=2)]
    w.write('REPORT.md','\n'.join(lines));clock.check();w.json('FILE_SHA256.json',{p.relative_to(HERE).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in HERE.rglob('*') if p.is_file()});w.accounting_receipt('WORKER_ACCOUNTING.json',dict(cpu_snapshot=time.process_time(),wall_snapshot=time.monotonic()-origin,counts=None if ctx is None else ctx['calls'].total,operations=w.operations,RESOURCE_ACCOUNTING='INCOMPLETE'))
    print(json.dumps(dict(status=status,started=report['started'],valid=valid,counts=report['counts'],MAE=report['MAE'],regret=report['HF_regret'],failure=None if fatal is None else fatal['message']),ensure_ascii=False),flush=True);return 0 if valid==7 and fatal is None else 1

def process_times(handle):
    from ctypes import wintypes
    class FT(ctypes.Structure):_fields_=[('low',wintypes.DWORD),('high',wintypes.DWORD)]
    a,b,c,d=FT(),FT(),FT(),FT();fn=ctypes.windll.kernel32.GetProcessTimes;fn.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(FT)]*4;fn.restype=wintypes.BOOL;require(fn(int(handle),ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)),'GET_PROCESS_TIMES');v=lambda x:(x.high<<32)|x.low
    return dict(creation_filetime=v(a),exit_filetime=v(b),kernel_seconds=v(c)/1e7,user_seconds=v(d)/1e7)
def meter():
    prep=read(HERE/'PREPARATION_ACCOUNTING.json');origin=prep['monotonic_start'];elapsed=prep['elapsed_at_launch'];pcpu=prep['known_preparation_cpu_seconds'];written=prep['cumulative_logical_write_bytes'];require(all(type(v) in (int,float) and math.isfinite(v) for v in (origin,elapsed,pcpu,written)) and elapsed>=0 and pcpu>=0,'PREPARATION_TIMING');deadline=origin+1800;require(math.isfinite(deadline) and 0<=time.monotonic()-origin<1800 and time.process_time()+pcpu<300 and 0<written<134217728,'PRESTART_BUDGET')
    p=subprocess.Popen([sys.executable,'-I','-S','-B',str(Path(__file__).resolve()),'--worker',str(origin)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);limit=None
    while p.poll() is None:
        t=process_times(p._handle)
        if time.monotonic()>=deadline or pcpu+time.process_time()+t['user_seconds']+t['kernel_seconds']>=300:limit='RESOURCE_LIMIT';p.kill();break
        time.sleep(.05)
    out,err=p.communicate();end=time.monotonic();cpu=process_times(p._handle);entry=time.process_time();wf=HERE/'WORKER_ACCOUNTING.json';written=read(wf)['cumulative_logical_write_bytes'] if wf.exists() else written;w=Writer(HERE,initial_written=written)
    receipt=w.accounting_receipt('RESOURCE_RECEIPT.json',dict(task=TASK,attempt_id='ATTEMPT_002',historical_execution=dict(scientific_starts=1,valid=0,WLS=1,SOLVER=0,ANALYTIC=0,known_cpu_subtotal=1.046875,wall_recorded=397.43556092950166,writes=122024,RESOURCE_ACCOUNTING='INCOMPLETE'),current_scientific_counts=read(HERE/'FINAL_REPORT.json').get('counts') if (HERE/'FINAL_REPORT.json').exists() else 'INCOMPLETE',task_cumulative_scientific_starts=1+read(HERE/'FINAL_REPORT.json')['started'] if (HERE/'FINAL_REPORT.json').exists() else 'INCOMPLETE',task_cumulative_known_cpu_subtotal=1.046875+pcpu+entry+cpu['user_seconds']+cpu['kernel_seconds'],worker_pid=p.pid,worker_exit_status=p.returncode,worker_cpu=cpu,entry_cpu_at_worker_exit=entry,known_preparation_cpu=pcpu,known_cpu_subtotal=pcpu+entry+cpu['user_seconds']+cpu['kernel_seconds'],wall_seconds_at_worker_exit=end-origin,wall_start_utc=prep['wall_start_utc'],limits=dict(cpu=300,wall=1800,writes=134217728),deadline_trigger=limit,path_b='APPROVED: worker exit; final receipt and handle close follow',RESOURCE_ACCOUNTING='INCOMPLETE',RESOURCE_COMPLIANCE='NOT_ESTABLISHED',cpu_unknown='host/read-only preparation and entry exit tail INCOMPLETE',writes_scope='controlled writes cumulative; if worker receipt absent only known preparation lower bound; host I/O INCOMPLETE',wall_scope='initial UTC-to-monotonic bridge then one shared Python Windows monotonic deadline',stdout=out.decode(errors='replace'),stderr=err.decode(errors='replace')));p._handle.Close();print(json.dumps(receipt,ensure_ascii=False),flush=True);return p.returncode
if __name__=='__main__':sys.exit(worker() if '--worker' in sys.argv else meter())
