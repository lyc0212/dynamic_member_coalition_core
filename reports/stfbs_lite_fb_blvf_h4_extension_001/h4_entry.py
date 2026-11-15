"""Authorized four-cell H4 BLVF V0.1 extension; task-local adapters only."""
import ast,copy,ctypes,hashlib,importlib.util,itertools,json,math,os,subprocess,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
H3=REPO/'reports/stfbs_lite_fb_blvf_initial_validation_001'
OLD=REPO/'reports/stfbs_lite_target_turn_exploration_001'
TURN=OLD/'ATTEMPT_003'
STAGE=REPO/'reports/l3_b_stage_a_minimal_remediation_execution_001_20261114121457'
HIST=REPO/'reports/l3_b_diagnostic_recovery_001_stage_a_20261114'
S=REPO/'reports/stfbs_lite_h2_h3_extension_005'
TASK='STFBS_LITE_FB_BLVF_H4_EXTENSION_001'
HEAD='a8524133c849e9e071693c6a9045af6479df64dc'
MATRIX=(('OFF','KEEP'),('ON','KEEP'),('ON','SWITCH'),('ON','MEMBER_CHANGE'))
sys.path[:0]=[str(HERE),str(STAGE)]
from recovery import Writer,Clock,require,plain,typed,digest,HistoricalImports

def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load_h3():
    path=H3/'fb_entry_attempt_002.py'
    require(sha(path)=='75226d448a454d8b6f711b52f7395ce844d03258dcdf4747e1d935c20b599117','H3_ENTRY_IDENTITY')
    spec=importlib.util.spec_from_file_location('h3_blvf_reused',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.HERE=HERE;module.TASK=TASK;module.HEAD=HEAD;sys.path.insert(0,str(HERE))
    # Only a reused task-local diagnostic module is adapted. Production modules remain unchanged.
    module.control_audit=control_audit
    return module

def load_motion():
    path=TURN/'turn_entry.py';source=path.read_text(encoding='utf-8');tree=ast.parse(source)
    wanted={'motion_spec','point','velocity_at','escape_time','world_digest'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
    require({n.name for n in nodes}==wanted,'MOTION_SOURCE_FUNCTIONS')
    ns=dict(__name__='task_h4_motion',__file__=str(path),math=math,digest=digest,require=require)
    # Exact existing function bodies, no source replacement or new motion formula.
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
    return ns

class LimitedCalls:
    def __init__(self,base,w,clock):self.inner=base.AnalyticCalls(w,clock)
    def __getattr__(self,k):return getattr(self.inner,k)
    def call(self,payload,scope,cell=None):
        require(scope=='SCIENCE','DIRECT_ANALYTIC_CALL_PROHIBITED')
        require(self.inner.total<252 and self.inner.science<252,'H4_ANALYTIC_TOTAL_LIMIT')
        require(self.inner.per_cell.get(cell,0)<63,'H4_ANALYTIC_CELL_LIMIT')
        return self.inner.call(payload,scope,cell)

def bootstrap(w,clock,base):
    require(Path(sys.executable).resolve()==Path(r'D:\miniconda3\envs\dynamic_member_coalition_core\python.exe').resolve(),'PYTHON_IDENTITY')
    sys.path.insert(0,r'D:\miniconda3\envs\dynamic_member_coalition_core\Lib\site-packages')
    pins=read(HIST/'HISTORICAL_IDENTITY.json');guard=HistoricalImports(HIST/'historical',pins);guard.install()
    import numpy as np,scipy
    from research.non_oracle import policy
    from research.cooperative_sensing import estimator
    from research.non_oracle.belief import DT
    require(DT==.05 and np.__version__=='2.1.3' and scipy.__version__=='1.15.3','ENVIRONMENT_DT')
    require(sha(HERE/'blvf.py')==sha(H3/'blvf.py')=='204fc231bf78004c33daf151983d751685666da75ed9e9b911abb83854c7365e','BLVF_IDENTITY')
    motion=load_motion();world_archive=read(TURN/'WORLD_H4.json');world=copy.deepcopy(world_archive['MODEL_world']);world['motion']={int(k):v for k,v in world['motion'].items()}
    require(motion['world_digest'](world)==world['world_digest']=='6e5d3f2944a8090f5da218420787ebfccbfedd5190d6511e57f299a00ebd8d76','H4_WORLD_IDENTITY')
    physical=world_archive['physical_definition'];require(physical['physics_digest']==motion['motion_spec'](world)['physics_digest']=='f1760d5f8830d757036eb19dbe0b9e34f82a767fded4a338703d6ea60ab93e05','H4_PHYSICS_IDENTITY')
    require(digest({k:v for k,v in physical.items() if k!='physics_digest'})==physical['physics_digest'],'PHYSICAL_DEFINITION_HASH')
    cp=Path(read(S/'H3_KEEP/authorization.json')['candidate_path']);candidate=read(cp)['candidate'];view=copy.deepcopy(candidate['a2_policy_view']);seed=copy.deepcopy(candidate['consumer_seed'])
    require(digest(seed)==read(S/'S4_STATIC.json')['seed_digest'],'SEED_IDENTITY')
    view['beliefs']={int(k):v for k,v in view['beliefs'].items()}
    for k in ('internal_states_at_D60','accepted_position_history','accepted_receipts'):seed[k]={int(j):v for j,v in seed[k].items()}
    require(digest(view)==world['public_digest']=='a37cde42a2c4c147f4abc9289e5de693790218d17bcafcbe7fe3cfb49a9d6602' and not seed['pending_observations'],'D60_PUBLIC_SEED')
    def isolated(path,extra):
        ns=dict(__name__='research.non_oracle.task_local_'+path.stem,__package__='research.non_oracle',__file__=str(path));ns.update(extra)
        exec(compile(path.read_bytes(),str(path),'exec'),ns);return ns
    model=isolated(TURN/'model_h4.py',dict(_h4_point=motion['point'],_velocity_at=motion['velocity_at'],_escape_time=motion['escape_time']))
    audit=isolated(TURN/'audit_h4.py',dict(_h4_point=motion['point']))
    candidates=read(S/'CANDIDATE_FREEZE.json');table=read(TURN/'VALUE_MATRIX.json');acceptance=read(TURN/'H4_HF_KEEP_OFFLINE_ACCEPTANCE.json')
    require(acceptance['status']=='ACCEPTED_WITH_LIMITATIONS' and acceptance['SCIENTIFIC_REEXECUTION']=='NO','HF_KEEP_OFFLINE_ACCEPTANCE')
    protected={str(p):sha(p) for p in [cp,H3/'blvf.py',H3/'fb_entry_attempt_002.py',H3/'MINIMAL_VALIDATION.json',TURN/'WORLD_H4.json',TURN/'VALUE_MATRIX.json',TURN/'turn_entry.py',TURN/'model_h4.py',TURN/'audit_h4.py',TURN/'H4_HF_KEEP_OFFLINE_ACCEPTANCE.json']}
    reference={};historical={};checks={}
    for action in base.ACTIONS:
        p=(OLD/'ATTEMPT_002' if action=='KEEP' else TURN)/'RAW'/('H4_HF_'+action+'.json');raw=read(p)
        require(raw['world']['world_digest']==world['world_digest'] and raw['net']==table[action]['H4_HF'],'HF_WORLD_VALUE')
        actions=next(c['actions'] for c in candidates if c['kind']==action)
        require(raw['boundaries'][0]['after']==actions,'HF_CANDIDATE')
        require(all(b['before']==b['after'] and b['changes']==0 and b['cost']==0 for b in raw['boundaries'] if b['tick'] in (80,100)),'HF_FIXED_HOLDS')
        if action=='KEEP':require(sha(p)==acceptance['source_files'][str(p)],'HF_KEEP_OFFLINE_RAW_HASH')
        protected[str(p)]=sha(p);reference[action]=dict(CAP=table[action]['H4_CAP'],HF=table[action]['H4_HF']);historical[action]=raw
        checks[action]=dict(source=str(p),sha256=sha(p),world_digest=world['world_digest'],fixed_holds=True,limitation='KEEP accepted offline from ATTEMPT_002; terminal memory and some historical objects unavailable' if action=='KEEP' else 'fixed-action MODEL HF reference; no new execution')
    point=motion['point'];vel=motion['velocity_at'];esc=motion['escape_time']
    p75=point(world,0,75);expected=np.asarray(world['motion'][0]['position'])+np.asarray(world['motion'][0]['velocity'])*.75
    require(np.array_equal(p75,expected) and vel(world,0,75)==physical['velocity_after'],'TURN_BOUNDARY')
    require(np.allclose(point(world,0,76),p75+np.asarray(physical['velocity_after'])*.05,rtol=0,atol=1e-14),'POST_TURN_POSITION')
    require(all(np.array_equal(point(world,1,k),np.asarray(world['motion'][1]['position'])+np.asarray(world['motion'][1]['velocity'])*((k-60)*.05)) for k in (60,75,76,120)),'T1_MOTION_CHANGED')
    require(all(math.isfinite(esc(world,j,t,view['config']['side'])) or esc(world,j,t,view['config']['side'])==math.inf for j in (0,1) for t in (3.,3.75,4.)),'ESCAPE_FUNCTION')
    ctx=dict(w=w,clock=clock,guard=guard,pins=pins,view=view,seed=seed,world=world,Branch=base.make_fb_branch(model['Branch']),point=point,velocity_at=vel,escape_time=esc,policy=policy,estimator=estimator,audit=audit['audit'],service_audit=audit['service_audit'],candidates=candidates,reference=reference,historical=historical,hf_comparability=checks,protected=protected,calls=LimitedCalls(base,w,clock),started=0,OFF={},ON={},traces={},timings={},failures=[],forbidden_counts=dict(WLS=0,SOLVER=0,R=0,ASSIGNMENT_OPTIMIZER=0))
    ctx['forbidden_codes']={estimator.estimate.__code__:'WLS',estimator.least_squares.__code__:'SOLVER',policy.decide.__code__:'R',policy.solve.__code__:'ASSIGNMENT_OPTIMIZER'}
    w.json('MINIMAL_VALIDATION.json',dict(status='PASS',checks=['frozen files and world identities','public view and full consumer seed','empty D60 pending','DT and numerical environment','exact existing motion function bodies','D75 position and right-continuous velocity','D76 post-turn displacement','unchanged T1','piecewise escape','fixed historical actions and holds'],analytic_calls=0,reused_H3_compatibility=dict(path=str(H3/'MINIMAL_VALIDATION.json'),sha256=sha(H3/'MINIMAL_VALIDATION.json')),moment_samples={str(k):dict(position=point(world,0,k).tolist(),instantaneous_velocity=vel(world,0,k)) for k in (60,74,75,76,80,100,120)}))
    w.json('EXPERIMENT_CONFIG.json',dict(task=TASK,git_head=HEAD,algorithm_version='V0.1',entry_sha256=sha(__file__),blvf_sha256=sha(HERE/'blvf.py'),world=plain(world),physical_definition=physical,D60_view_digest=digest(view),seed_digest=digest(seed),matrix=MATRIX,reference=reference,historical_comparability=checks,code_sources={str(p):sha(p) for p in (H3/'fb_entry_attempt_002.py',TURN/'turn_entry.py',TURN/'model_h4.py',TURN/'audit_h4.py')},source_binding='H4 base Branch only, H3 feedback subclass only; no old fixed Branch or RecordedConsumer; no production monkey patch',environment=dict(python=sys.executable,version=sys.version,numpy=np.__version__,numpy_path=np.__file__,scipy=scipy.__version__,scipy_path=scipy.__file__),limits=dict(cells=4,analytic_per_cell=63,analytic_science=252,analytic_direct=0,cpu=300,wall=1800,writes=134217728,WLS=0,solver=0,R=0,assignment_optimizer=0,ACTUAL=0),epsilon=1e-8))
    return ctx

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
            u=np.zeros(2);dt=0.;used=None
            if a['target'] is not None:
                j=a['target'];event=terminal[j]
                if event['time']>=lo and not(event['time']==lo and event['tick']<n):
                    b=frozen[j];p,v=trajectory(b,n-1);force=np.asarray(v)+cfg.travel_gain*(np.asarray(p)+offset(a['role'],cfg)-np.asarray(frame['before'][i]));u=force*min(1.,cfg.max_speed/max(float(np.linalg.norm(force)),1e-15));truth=ctx['point'](ctx['world'],j,n-1);escape=ctx['escape_time'](ctx['world'],j,lo,cfg.side);dt=max(0.,min(n*.05,escape)-lo);used=(j,b,p,v,truth)
            bound=16*math.ulp(max(1.,float(np.max(np.abs(u)))));require(float(np.max(np.abs(u-np.asarray(frame['control'][i]))))<=bound and dt==frame['elapsed'][i],'H4_ACTUAL_CONTROL_AUDIT');checked+=1
            if used is not None and dt>0:
                j,b,p,v,truth=used;et=b['estimate_tick'];tv=ctx['velocity_at'](ctx['world'],j,n-1);ep=ctx['point'](ctx['world'],j,et) if 60<=et<=120 else None;ev=ctx['velocity_at'](ctx['world'],j,et) if ep is not None else None
                records.append(dict(target=j,tick=n-1,robot_id=i,actual_control_belief=copy.deepcopy(b),prediction_position=list(p),prediction_velocity=list(v),propagation_age=(n-1-et)*.05,observation_age=None if b['last_observation_tick'] is None else (n-1-b['last_observation_tick'])*.05,cap_applied=b['last_observation_tick'] is not None and (n-1-et)*.05>1.,true_position=truth.tolist(),true_velocity=tv,position_error=math.dist(p,truth),velocity_error=math.dist(v,tv),estimation_position_error=None if ep is None else math.dist(b['position_estimate'],ep),estimation_velocity_error=None if ev is None else math.dist(b['velocity_estimate'],ev),estimate_truth_status='NOT_IDENTIFIABLE' if ep is None else 'IDENTIFIABLE',actual_control=frame['control'][i],robot_before=frame['before'][i],robot_after=frame['positions'][i]))
    require(checked==180 and [d['view']['tick'] for d in result['decisions']]==[80,100],'H4_CONTROL_HORIZON')
    return dict(status='PASS',checked_robot_intervals=checked,basis='actual control snapshots; piecewise position, instantaneous velocity at respective control/estimate ticks and piecewise escape'),records

def augment_trace(ctx,mode,action):
    trace=ctx['traces'][mode+'/'+action];raw=trace['result'];rows=read(HERE/('TRACE/BLVF_'+mode+'_'+action+'.json'));summary=trace['service'];j=1 if action=='SWITCH' else 0
    pairs=[];left=rows['initial_service'][str(j)]['endpoint'];endpoints={f['frame']['tick']:f['endpoint'] for f in raw['feedback'] if f['frame']['target_id']==j}
    for frame in raw['frames']:
        t=frame['tick'];right=endpoints.get(t)
        if right is None:continue
        if left is not None:pairs.append(dict(left_tick=t-1,right_tick=t,G=bool(left['G'] and right['G']),GQ=bool(left['G'] and right['G'] and left['quality']['status']==right['quality']['status']=='PASS')))
        left=right
    summary['G_intervals']=[r for r in pairs if r['G']];summary['GQ_intervals']=[r for r in pairs if r['GQ']]
    summary['terminal_statuses']=raw['status'];summary['terminal_positions']=raw['frames'][-1]['positions']
    summary['natural_release_boundaries']=[b for b in raw['boundaries'] if b['tick'] not in (60,80,100)]
    rows['service_summary']=summary
    details=[]
    for row in rows['actual_consumer_records']:
        row=copy.deepcopy(row);target=row['target'];k=row['measurement_tick'];s=row['reference_tick'];history=rows['accepted_history'][str(target)];ref=next((p for t,p in history if t==s),None)
        frame=next(f for f in raw['feedback'] if f['frame']['target_id']==target and f['frame']['tick']==k);p=frame['result']['estimate_result']
        row.update(reference_position=ref,accepted_position=None if not row['accepted'] else p['estimate'],reference_class='NOT_APPLICABLE' if s is None or target!=0 else 'PRE_TURN' if k<=75 else 'CROSSES_TURN' if s<75 else 'POST_TURN',unclipped_difference_velocity=None if ref is None or not row['accepted'] else [(x-y)/((k-s)*.05) for x,y in zip(p['estimate'],ref)])
        details.append(row)
    rows['actual_consumer_records']=details;rows['reference_scope']='own generated MODEL observations only; no HF feedback replay';trace['feedback_details']=details
    ctx['w'].write('TRACE/BLVF_'+mode+'_'+action+'.json',json.dumps(rows,ensure_ascii=False,indent=2,allow_nan=False),replace=True)

def analyze(ctx,base):
    a=base.analyze(ctx)
    for action,row in a['matrix'].items():
        if action!='KEEP':row['FB_OFF']='NOT_RUN'
    a['history_reference']='accepted H4 fixed-action HF and CAP; KEEP HF from ATTEMPT_002 offline acceptance'
    a['limits']='one frozen H4 instantaneous-turn world; four proxy cells; only KEEP has an ON/OFF pair; no statistical generalization'
    if 'KEEP' in a['mechanisms']:
        m=a['mechanisms']['KEEP'];off=ctx['traces']['OFF/KEEP'];on=ctx['traces']['ON/KEEP']
        def early(raw):return [plain(dict(frame=f['frame'],quality=f['result']['quality'],payload=f['result']['payload'])) for f in raw['feedback'] if f['frame']['tick']<=80]
        require(early(off['result'])==early(on['result']) and off['service']['P0']==on['service']['P0'],'KEEP_PRE_FEEDBACK_OBSERVATION_SERVICE_DIFFERENCE')
        m['pre_D80_observation_Q_and_initial_service']='VERIFIED'
        m.pop('service',None)
        for label,fields in [('G_service',['G_intervals']),('GQ_service',['GQ_intervals']),('continuous_progress',['Pmax']),('completion',['completion_tick']),('quality_classification',['quality_counts']),('economic_ledger',['positive_cost_ledger'])]:m[label]='CHANGED' if any(off['service'][f]!=on['service'][f] for f in fields) else 'UNCHANGED'
        m['OFF_service']=off['service'];m['ON_service']=on['service']
    a['feedback_details']={key:trace.get('feedback_details',[]) for key,trace in ctx['traces'].items()}
    a['freeze_views']={key:trace['freeze'] for key,trace in ctx['traces'].items()}
    a['H4_FEEDBACK_ADAPTATION_FINDINGS']='NOT_IDENTIFIABLE'
    if 'ON/KEEP' in ctx['traces']:
        freeze=next(f for f in ctx['traces']['ON/KEEP']['freeze'] if f['tick']==80);belief=freeze['actual_control_beliefs']['0'];et=belief['estimate_tick'];truth=ctx['velocity_at'](ctx['world'],0,80)
        ve=math.dist(belief['velocity_estimate'],truth);pe=math.dist(belief['position_estimate'],ctx['point'](ctx['world'],0,et)) if et>=60 else None
        a['D80_KEEP_ADAPTATION']=dict(actual_control_belief=belief,instantaneous_velocity_D80=truth,velocity_error_to_D80=ve,position_error_at_estimate_tick=pe,consumed_records=[r for r in ctx['traces']['ON/KEEP']['feedback_details'] if r['freeze_tick']==80],interpretation='actual reference interval retained; accepted position alone does not prove instantaneous velocity adaptation')
        a['H4_FEEDBACK_ADAPTATION_FINDINGS']='SUPPORTED_AT_D80_IN_TESTED_CASE' if ve<=1e-8 and pe is not None and pe<=1e-8 else 'PARTIAL_OR_NOT_SUPPORTED_AT_D80'
    onm=a['methods']['ON'];a['H4_CONDITIONAL_VALUE_PREDICTION_FINDINGS']='NOT_IDENTIFIABLE'
    if len(ctx['ON'])==3:a['H4_CONDITIONAL_VALUE_PREDICTION_FINDINGS']=dict(MAE=onm['complete_three_cell_MAE'],ranking=onm['ranking'],relative_errors=onm['relative_value_difference_errors'],interpretation='measured conditional value prediction, no forced zero error or success')
    a['H4_COMPUTATIONAL_SIMPLIFICATION_FINDINGS']=dict(analytic_counts=ctx['calls'].summary(),forbidden_entry_counts=ctx['forbidden_counts'],END_TO_END_SPEEDUP='NOT_ESTABLISHED',attribution='BLVF replaces observation estimation; fixed-action evaluation avoids policy optimization; do not conflate')
    # Replace only new task files written by base.analyze; every overwrite is charged.
    ctx['w'].write('VALUE_MATRIX.json',json.dumps(a['matrix'],ensure_ascii=False,indent=2,allow_nan=False),replace=True)
    ctx['w'].write('SCIENTIFIC_ANALYSIS.json',json.dumps(a,ensure_ascii=False,indent=2,allow_nan=False),replace=True)
    return a

def worker():
    prep=read(HERE/'PREPARATION_ACCOUNTING.json');origin=float(sys.argv[-1]);clock=Clock(origin,cpu_limit=300,wall_limit=1800);w=Writer(HERE,initial_written=prep['cumulative_logical_write_bytes'],clock=clock);ctx=None;a=None;fatal=None;old=sys.getprofile();base=load_h3()
    try:
        clock.check();ctx=bootstrap(w,clock,base)
        def profile(frame,event,arg):
            if event=='call' and frame.f_code in ctx['forbidden_codes']:
                kind=ctx['forbidden_codes'][frame.f_code];ctx['forbidden_counts'][kind]+=1;raise RuntimeError('FORBIDDEN_SCIENTIFIC_ENTRY/'+kind)
        sys.setprofile(profile)
        for mode,action in MATRIX:
            require(ctx['started']<4,'FOUR_CELL_START_LIMIT');base.run_cell(ctx,mode,action);augment_trace(ctx,mode,action)
    except BaseException as exc:
        fatal=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());w.json('FAILURE.json',fatal)
    finally:sys.setprofile(old)
    audit=None;protection=None
    if ctx is not None:
        try:
            a=analyze(ctx,base);audit=base.resource_audit(ctx);protection={p:sha(p)==h for p,h in ctx['protected'].items()};w.json('PROTECTION_CHECK.json',dict(files=protection,unchanged=all(protection.values())));require(all(protection.values()),'HISTORICAL_FILE_CHANGED');w.json('RUNTIME_PROJECT_IMPORTS.json',dict(modules=ctx['guard'].audit(),namespace_paths=ctx['guard'].namespace_paths,lazy_imports='NOT_VERIFIED',task_local_H4_sources='explicit source bindings in EXPERIMENT_CONFIG'))
        except BaseException as exc:
            extra=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());fatal=fatal or extra;w.json('FINALIZATION_FAILURE.json',extra)
    valid=0 if ctx is None else len(ctx['OFF'])+len(ctx['ON']);counts=None if ctx is None else ctx['calls'].summary();status='VALID_FOUR_CELL_RESULT_PENDING_INDEPENDENT_REVIEW' if valid==4 and fatal is None else 'PARTIAL_RESULTS' if valid else 'BLOCKED_NO_ACCEPTED_CELLS'
    report=dict(task=TASK,git_head=HEAD,entry_sha256=sha(__file__),blvf_sha256=sha(HERE/'blvf.py'),status=status,started=0 if ctx is None else ctx['started'],valid=valid,analytic_counts=counts,forbidden_entry_counts=None if ctx is None else ctx['forbidden_counts'],failure=fatal,resource_call_audit=audit,matrix=None if a is None else a['matrix'],H4_FEEDBACK_ADAPTATION_FINDINGS='NOT_IDENTIFIABLE' if a is None else a['H4_FEEDBACK_ADAPTATION_FINDINGS'],H4_CONDITIONAL_VALUE_PREDICTION_FINDINGS='NOT_IDENTIFIABLE' if a is None else a['H4_CONDITIONAL_VALUE_PREDICTION_FINDINGS'],H4_COMPUTATIONAL_SIMPLIFICATION_FINDINGS='NOT_IDENTIFIABLE' if a is None else a['H4_COMPUTATIONAL_SIMPLIFICATION_FINDINGS'],completion=None if ctx is None else {k:t['service']['completion_tick'] for k,t in ctx['traces'].items()},RESOURCE_ACCOUNTING='INCOMPLETE',RESOURCE_COMPLIANCE='NOT_ESTABLISHED',END_TO_END_SPEEDUP='NOT_ESTABLISHED',INDEPENDENT_SCIENTIFIC_ACCEPTANCE='PENDING',H3_BLVF_INITIAL_VALIDATION='CLOSED',H4_TARGET_TURN_EXPLORATION='CLOSED',BLVF_ALGORITHM_VERSION='V0.1',H5_ARC_EXECUTION_AUTHORIZATION='NOT_GRANTED',L3_C_EXECUTION_AUTHORIZATION='NOT_GRANTED',PRODUCTION_ADMISSION='BLOCKED',PAPER_NOVELTY='NOT_ESTABLISHED')
    w.json('FINAL_REPORT.json',report)
    lines=['# BLVF V0.1 H4瞬时转向四格最小验证','',status,'','本报告为本次实际计算结果，独立科学验收待完成。','', '| 动作 | 历史CAP | FB-OFF | FB-ON | 历史HF |','|---|---|---|---|---|']
    if a is not None:
        for action,row in a['matrix'].items():lines.append('| '+' | '.join([action]+[str(row[k]) for k in ('CAP','FB_OFF','FB_ON','HF')])+' |')
        lines+=['','## 价值误差、排序及条件regret','',json.dumps(a['methods'],ensure_ascii=False,indent=2),'','## KEEP反馈总效应及机制分层','',json.dumps(a['value_effects']['KEEP'],ensure_ascii=False,indent=2),'',json.dumps(a['mechanisms'].get('KEEP','NOT_IDENTIFIABLE'),ensure_ascii=False,indent=2),'','## D80转向适应','',json.dumps(a.get('D80_KEEP_ADAPTATION','NOT_IDENTIFIABLE'),ensure_ascii=False,indent=2),'','## 各有效单元服务、终端及经济账本','',json.dumps({k:t['service'] for k,t in ctx['traces'].items()},ensure_ascii=False,indent=2)]
    lines+=['','## 结论边界','', '本次仅H4固定候选动作条件世界。KEEP有真实ON/OFF配对；SWITCH和MEMBER_CHANGE仅有ON，不声称独立反馈增量效应。模型转向只进入模拟物理、观测和离线真值审计，BLVF仍只有五字段输入，控制器仅使用合法belief。保持原一秒传播截断。','', '服务变化分别按G/GQ区间、连续进度、完成及价值判断，不把Q分类或成本字典变化解释为服务能力改善。共同预测误差按目标—tick去重，完成后不补造预测记录。','', 'HF KEEP来源为ATTEMPT_002已保存RAW及ATTEMPT_003离线验收，保留终端内存及部分历史对象缺失限制。没有重跑HF、H3、NoCap或新世界。端到端加速未建立；未知宿主CPU、写入及计量入口尾部未记零。','',json.dumps(report,ensure_ascii=False,indent=2)]
    w.write('REPORT.md','\n'.join(lines));clock.check()
    w.json('FILE_SHA256.json',{p.relative_to(HERE).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in HERE.rglob('*') if p.is_file()})
    w.accounting_receipt('WORKER_ACCOUNTING.json',dict(cpu_snapshot=time.process_time(),wall_snapshot=time.monotonic()-origin,analytic_counts=counts,operations=w.operations,resource_accounting='INCOMPLETE'))
    print(json.dumps(dict(status=status,started=report['started'],valid=valid,counts=counts,matrix=report['matrix'],completion=report['completion'],failure=None if fatal is None else fatal['message']),ensure_ascii=False),flush=True)
    return 0 if valid==4 and fatal is None else 1

def process_times(handle):
    from ctypes import wintypes
    class FT(ctypes.Structure):_fields_=[('low',wintypes.DWORD),('high',wintypes.DWORD)]
    a,b,c,d=FT(),FT(),FT(),FT();fn=ctypes.windll.kernel32.GetProcessTimes;fn.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(FT)]*4;fn.restype=wintypes.BOOL;require(fn(int(handle),ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)),'GET_PROCESS_TIMES');v=lambda x:(x.high<<32)|x.low
    return dict(creation_filetime=v(a),exit_filetime=v(b),kernel_seconds=v(c)/1e7,user_seconds=v(d)/1e7)

def meter():
    prep=read(HERE/'PREPARATION_ACCOUNTING.json');origin=prep['monotonic_start'];elapsed=prep['elapsed_at_launch'];known_prep=prep['known_preparation_cpu_seconds'];writes=prep['cumulative_logical_write_bytes']
    require(all(type(x) in (int,float) and math.isfinite(x) for x in (origin,elapsed,known_prep,writes)) and elapsed>=0 and known_prep>=0,'INVALID_PREPARATION_NUMBERS');deadline=origin+1800
    require(math.isfinite(deadline) and 0<=time.monotonic()-origin<1800 and time.process_time()+known_prep<300 and 0<writes<134217728,'PRESTART_BUDGET')
    p=subprocess.Popen([sys.executable,'-I','-S','-B',str(Path(__file__).resolve()),'--worker',str(origin)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);limit=None
    while p.poll() is None:
        t=process_times(p._handle)
        if time.monotonic()>=deadline or known_prep+time.process_time()+t['kernel_seconds']+t['user_seconds']>=300:limit='RESOURCE_LIMIT';p.kill();break
        time.sleep(.05)
    out,err=p.communicate();end=time.monotonic();cpu=process_times(p._handle);entry_cpu=time.process_time();wf=HERE/'WORKER_ACCOUNTING.json';written=read(wf)['cumulative_logical_write_bytes'] if wf.exists() else writes
    w=Writer(HERE,initial_written=written)
    record=w.accounting_receipt('RESOURCE_RECEIPT.json',dict(task=TASK,worker_pid=p.pid,worker_exit_status=p.returncode,worker_cpu=cpu,entry_cpu_at_worker_exit=entry_cpu,known_preparation_cpu=known_prep,known_cpu_subtotal=known_prep+entry_cpu+cpu['kernel_seconds']+cpu['user_seconds'],wall_seconds_at_worker_exit=end-origin,wall_start_utc=prep['wall_start_utc'],limits=dict(cpu=300,wall=1800,writes=134217728),deadline_trigger=limit,path_b='APPROVED; worker exit cutoff; necessary receipt and handle close follow',RESOURCE_ACCOUNTING='INCOMPLETE',RESOURCE_COMPLIANCE='NOT_ESTABLISHED',cpu_unknown='host and readonly tools; entry final tail INCOMPLETE',write_limitation='all controlled logical writes counted including overwritten new-task trace/analysis; host writes INCOMPLETE; if worker accounting absent this is only known preparation lower bound',wall_limitation='initial preparation UTC-to-Python-monotonic bridge; same-machine Python monotonic thereafter',stdout=out.decode(errors='replace'),stderr=err.decode(errors='replace')))
    p._handle.Close();print(json.dumps(record,ensure_ascii=False),flush=True);return p.returncode

if __name__=='__main__':sys.exit(worker() if '--worker' in sys.argv else meter())
