"""Authorized paired P1 only; no feedback, WLS, R or Assignment."""
import sys,os,time,json,hashlib,copy,traceback,subprocess,ctypes,csv,io,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
STAGE=REPO/'reports/l3_b_stage_a_minimal_remediation_execution_001_20261114121457';HISTORY=REPO/'reports/l3_b_diagnostic_recovery_001_stage_a_20261114';S=REPO/'reports/stfbs_lite_h2_h3_extension_005'
sys.path.insert(0,str(STAGE))
from recovery import Writer,Clock,require,plain,typed,HistoricalImports,build_kernel,boundary_check,controller,compare_p1,TraceRecorder,ledger_check,P1_FIELDS
HEAD='4cf0a01775c479899be401f5b035026808177e52'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fp(x):return hashlib.sha256(json.dumps(plain(x),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def leaf_differences(a,b,path=''):
    a=plain(a);b=plain(b)
    if isinstance(a,dict) and isinstance(b,dict):
        return [d for k in sorted(set(a)|set(b)) for d in leaf_differences(a.get(k),b.get(k),path+'/'+str(k))]
    if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in leaf_differences(x,y,path+'/'+str(i))]
    if type(a)!=type(b) or a!=b:return [dict(path=path,reference=a,archive=b,reference_type=type(a).__name__,archive_type=type(b).__name__,numeric_equal=(a==b) if type(a) in (int,float) and type(b) in (int,float) else None)]
    return []

def worker():
    prep=read(HERE/'PREPARATION_ACCOUNTING.json');origin=float(sys.argv[-1]);clock=Clock(origin,cpu_limit=120,wall_limit=900);w=Writer(HERE,limit=134217728,initial_written=prep['cumulative_logical_write_bytes'],clock=clock)
    refs={};results={};comparisons={};bindings=[];metrics=[];calls={'reference':0,'p1':0};failure=None;phase='INPUT_CHECK';protected={};guard=None
    try:
        clock.check();require(Path(sys.executable).resolve()==Path(r'D:\miniconda3\envs\dynamic_member_coalition_core\python.exe').resolve(),'PYTHON_IDENTITY')
        manifest=read(STAGE/'MANIFEST.json');require(sha(STAGE/'recovery.py')==manifest['files']['recovery.py']['sha256'],'ACCEPTED_KERNEL_SHA')
        tests=read(STAGE/'SYNTHETIC_TEST_RESULTS.json');require(tests['code_sha256']==sha(STAGE/'recovery.py') and tests['tests']==17 and not tests['failures'] and not tests['errors'],'ACCEPTED_TEST_VERSION')
        pins=read(HISTORY/'HISTORICAL_IDENTITY.json');site=Path(r'D:\miniconda3\envs\dynamic_member_coalition_core\Lib\site-packages');sys.path.insert(0,str(site));guard=HistoricalImports(HISTORY/'historical',pins);guard.install()
        import importlib,numpy,scipy
        proxy=importlib.import_module('research.non_oracle.stfbs_lite_proxy');from pursuit_v2.service import ServiceState
        require(numpy.__version__=='2.1.3' and scipy.__version__=='1.15.3','NUMERICAL_ENVIRONMENT')
        for m in (numpy,scipy):require(Path(m.__file__).resolve().is_relative_to(site.resolve()),'NUMERICAL_ORIGIN')
        raw_view=read(S/'PUBLIC_INPUT_FREEZE.json');worlds=read(S/'WORLD_LIBRARY.json')['worlds'];mapping=read(S/'MODEL_WORLD_MAPPING.json');candidates=read(S/'CANDIDATE_FREEZE.json');table=read(S/'PROXY_VALUE_TABLE.json');freeze=read(S/'EXECUTION_FREEZE.json');archive=read(S/'archive_evidence_manifest.json')
        for name in ['PUBLIC_INPUT_FREEZE.json','WORLD_LIBRARY.json','MODEL_WORLD_MAPPING.json','CANDIDATE_FREEZE.json','PROXY_VALUE_TABLE.json']:
            record=next(x for x in archive['files'] if x['path']==name);require(sha(S/name)==record['sha256'],'INPUT_SHA/'+name);protected[str(S/name)]=sha(S/name)
        for p in (STAGE/'recovery.py',HISTORY/'HISTORICAL_IDENTITY.json',REPO/'pursuit_v2/policies.py'):protected[str(p)]=sha(p)
        def make_view():
            v=copy.deepcopy(raw_view)
            for key in ('beliefs','service_states','current_endpoints','current_q','public_profiles'):v[key]={int(k):x for k,x in v[key].items()}
            for ep in v['current_endpoints'].values():
                if ep is not None:ep['team']=tuple(tuple(x) for x in ep['team'])
            v['service_states']={j:ServiceState(base=x['base'],intervals=x['intervals'],team=tuple(tuple(y) for y in x['team'])) for j,x in v['service_states'].items()};return v
        public_digest=proxy.public_input_digest(make_view());source=HISTORY/'historical/research/non_oracle/stfbs_lite_proxy.py';require(sha(source)==freeze['source_sha256']['research/non_oracle/stfbs_lite_proxy.py'],'HISTORICAL_PROXY_SHA');kernel,ns=build_kernel(source.read_text(encoding='utf-8'));cells=[]
        for world_name in ('H2','H3'):
            mw=mapping[world_name];wd=mw['perturbation']['stfbs_world_digest'];matches=[x for x in worlds if x['world_digest']==wd];require(len(matches)==1,'ORIGINAL_WORLD_IDENTITY');world=copy.deepcopy(matches[0]);world['motion']={int(k):x for k,x in world['motion'].items()}
            require(proxy.world_digest(world)==wd and world['public_input_digest']==public_digest and mapping['STFBS'][world_name]['world_digest']==wd,'WORLD_CONTEXT')
            for action in ('KEEP','SWITCH','MEMBER_CHANGE'):
                c=next(x for x in candidates if x['kind']==action);found=[r[1] for r in table if r[0]==[c['assignment_key'],wd]];require(len(found)==1 and all(k in found[0] for k in P1_FIELDS),'P0_BINDING');name=world_name+'_'+action;b=next(x for x in freeze['branches'] if x['name']==name);require(b['world']==mw and b['initial_actions']==c['actions'],'MODEL_ACTION_BINDING')
                binding=dict(cell=name,original_world_digest=wd,model_world_digest=mw['world_digest'],original_world=plain(world),model_world=mw,actions=c['actions'],assignment_key=c['assignment_key'],public_input_digest=public_digest,public_input_sha256=sha(S/'PUBLIC_INPUT_FREEZE.json'),p0_record_sha256=fp(found[0]),p0_value=found[0]['value'],generation=dict(rule=world['generation_rule'],ordinal=world['world_ordinal'],random_seed='NOT_APPLICABLE: deterministic archived construction'),pre_d60='SOURCE_UNRESOLVED');bindings.append(binding);cells.append((binding,world,copy.deepcopy(c['actions']),copy.deepcopy(found[0])))
        w.json('INPUT_BINDINGS.json',bindings);w.json('EXECUTION_CONFIG.json',dict(task='STFBS_LITE_L3_B_P1_REPRODUCTION_001',git_head=HEAD,entry_sha256=sha(__file__),kernel_sha256=sha(STAGE/'recovery.py'),historical_proxy=pins['research/non_oracle/stfbs_lite_proxy.py'],environment=dict(python=sys.executable,version=sys.version,numpy=dict(version=numpy.__version__,path=numpy.__file__),scipy=dict(version=scipy.__version__,path=scipy.__file__)),limits=dict(cpu=120,wall=900,cumulative_logical_write_bytes=134217728),path_b='APPROVED',precision='exact archived numbers; no rounding; epsilon only for best sets',no_cap=False,feedback=False,historical_identity_reference=str(HISTORY/'HISTORICAL_IDENTITY.json'),existing_import_reference=str(HISTORY/'ACTUAL_IMPORTS.json')))
        for binding,world,actions,p0 in cells:
            clock.check();name=binding['cell'];phase=name+'/REF';rv,pv=make_view(),make_view();rw,pw=copy.deepcopy(world),copy.deepcopy(world);ra,pa=copy.deepcopy(actions),copy.deepcopy(actions)
            require(typed(rv)==typed(pv) and typed(rw)==typed(pw) and typed(ra)==typed(pa),'EQUAL_INPUT');require(rv is not pv and rv['beliefs'] is not pv['beliefs'],'INPUT_ALIAS')
            calls['reference']+=1;w.json('CALLS/'+name+'_REF_STARTED.json',dict(ordinal=calls['reference'],input_sha256=fp([rv,ra,rw]),state='STARTED'))
            ref=proxy.run_proxy(rv,ra,rw);refs[name]=plain(ref);w.json('RAW/'+name+'_REF.json',plain(ref));clock.check();rc=compare_p1(ref,p0);comparisons[name]=dict(REF_P0=rc,REF_P0_leaf_differences=leaf_differences(ref,p0));require(rc['status']=='VERIFIED','SHARED_REF_P0_DIFFERENCE/'+name)
            phase=name+'/P1';controls=[];trace=TraceRecorder();boundaries=[];belief_before=typed(pv['beliefs']);actions_before=typed(pa);cmd=controller(ns,False,controls,actions=pa)
            def command(*args):clock.check();return cmd(*args)
            def boundary(t,v,physical):
                clock.check();before=plain(dict(physical=physical,beliefs=v['beliefs'],actions=pa));invoked=[]
                def noop():invoked.append(t)
                check=boundary_check(t,v,physical,operation=noop);require(invoked==[t],'BOUNDARY_NOT_EXECUTED');check.update(before=before,after=plain(dict(physical=physical,beliefs=v['beliefs'],actions=pa)),operation='in-place no-op pause/resume; no reconstruction');boundaries.append(check)
            def record(state):clock.check();trace(state)
            calls['p1']+=1;w.json('CALLS/'+name+'_P1_STARTED.json',dict(ordinal=calls['p1'],input_sha256=fp([pv,pa,pw]),state='STARTED'))
            try:
                p1=kernel(pv,pa,pw,command,boundary,record);results[name]=plain(p1);w.json('RAW/'+name+'_P1.json',plain(p1))
            finally:w.json('TRACE/'+name+'.json',plain(dict(frames=trace.rows,controls=controls,boundaries=boundaries,Q_semantics='G-only optimistic Q; not observed PASS')))
            require([x['tick'] for x in boundaries]==[80,100] and len(trace.rows)==60 and trace.rows[-1]['tick']==120,'SHARED_BOUNDARY_HORIZON');require(typed(pv['beliefs'])==belief_before and typed(pa)==actions_before,'SHARED_FIXED_BELIEF_ACTION')
            pr,pp=compare_p1(p1,ref),compare_p1(p1,p0);comparisons[name].update(P1_REF=pr,P1_P0=pp,boundary_status='VERIFIED');require(pr['status']==pp['status']=='VERIFIED','SHARED_P1_TEN_FIELD_DIFFERENCE/'+name)
            for out in (ref,p1,p0):ledger_check(out['ledger'],out['value'])
            errors=[]
            for r in controls:
                j=r['target'];truth=proxy.point(world,j,r['tick']);velocity=world['motion'][j]['velocity'];est=proxy.point(world,j,r['estimate_tick']) if r['estimate_tick']>=60 else None
                errors.append(dict(tick=r['tick'],target=j,prediction_position_error=math.dist(r['position_prediction'],truth),prediction_velocity_error=math.dist(r['velocity_prediction'],velocity),estimate_tick=r['estimate_tick'],estimation_position_error=None if est is None else math.dist(r['estimate_position'],est),estimation_velocity_error=None if est is None else math.dist(r['estimate_velocity'],velocity),estimate_reference='NOT_IDENTIFIABLE_BEFORE_D60' if est is None else 'ARCHIVED_CONDITIONAL_WORLD_TRUTH'))
            w.json('TRACE/'+name+'_STATE_ERRORS.json',errors)
            row=dict(world=name[:2],action=name[3:],P0=p0['value'],REF=ref['value'],P1=p1['value'],REF_minus_P0=ref['value']-p0['value'],P1_minus_REF=p1['value']-ref['value'],P1_minus_P0=p1['value']-p0['value'],ten_fields='VERIFIED',ledger=p1['ledger'],tasks=p1['tasks'],boundary_ticks=[80,100],terminal=plain(trace.rows[-1]),HF_status='NOT_VERIFIED')
            try:
                raw_path=S/name/'BRANCH_RAW.json';entry=next(x for x in read(S/name/'evidence_manifest.json')['files'] if x['path']=='BRANCH_RAW.json');require(sha(raw_path)==entry['sha256'],'HF_RAW_SHA');hf=read(raw_path);require(hf['world']['world_digest']==binding['model_world_digest'] and hf['boundaries'][0]['after']==actions and hf['frames'][-1]['tick']==120,'HF_IDENTITY');require(read(S/name/'FINAL_BRANCH_REPORT.json')['valid_cell_candidate'] is True,'HF_UNACCEPTED');row.update(HF=hf['net'],signed_error=p1['value']-hf['net'],AE=abs(p1['value']-hf['net']),HF_status='VERIFIED_ARCHIVED_IDENTITY',HF_raw_sha256=entry['sha256'],HF_components=hf['components'],HF_change_cost=hf['change_cost'])
            except Exception as exc:row['HF_limitation']=str(exc)
            metrics.append(row);w.json('CELL/'+name+'.json',plain(row));clock.check();guard.audit()
    except BaseException as exc:
        failure=dict(phase=phase,type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),calls=copy.deepcopy(calls));w.json('FAILURE.json',failure)
    clock.check();actual={} if guard is None else guard.audit();w.json('RUNTIME_IMPORT_IDENTITY.json',dict(actual_modules=actual,namespaces={} if guard is None else guard.namespace_paths,untriggered_lazy_imports='NOT_VERIFIED'))
    w.json('REFERENCE_RESULTS.json',refs);w.json('P1_RESULTS.json',results);w.json('P1_COMPARISON.json',comparisons)
    summary=dict(valid_cells=len(metrics),calls=calls,MAE=None,signed_bias=None,per_world={})
    if len(metrics)==6:
        good=[r for r in metrics if 'HF' in r];summary['HF_valid_cells']=len(good)
        if len(good)==6:summary.update(MAE=sum(r['AE'] for r in good)/6,signed_bias=sum(r['signed_error'] for r in good)/6,action_bias={a:sum(r['signed_error'] for r in good if r['action']==a)/2 for a in ('KEEP','SWITCH','MEMBER_CHANGE')})
        for world_name in ('H2','H3'):
            group=[r for r in metrics if r['world']==world_name];best=max(r['P1'] for r in group);opt=[r for r in group if best-r['P1']<=1e-8];hf_ok=all('HF' in r for r in group);summary['per_world'][world_name]=dict(keep_minus_switch=next(r['P1'] for r in group if r['action']=='KEEP')-next(r['P1'] for r in group if r['action']=='SWITCH'),strict_order=sorted([r['action'] for r in group],key=lambda a:-next(x['P1'] for x in group if x['action']==a)),epsilon_best=[r['action'] for r in opt],HF_regret=None if not hf_ok else {r['action']:max(x['HF'] for x in group)-r['HF'] for r in opt})
    w.json('P1_METRICS.json',plain(dict(summary=summary,cells=metrics)));buffer=io.StringIO(newline='');cols=['world','action','P0','REF','P1','REF_minus_P0','P1_minus_REF','P1_minus_P0','ten_fields','HF_status','HF','signed_error','AE'];cw=csv.DictWriter(buffer,fieldnames=cols);cw.writeheader()
    for row in metrics:cw.writerow({k:row.get(k) for k in cols})
    w.write('P1_METRICS.csv',buffer.getvalue());protection={p:sha(p)==h for p,h in protected.items()};require(all(protection.values()),'FROZEN_FILE_CHANGED');w.json('PROTECTION_CHECK.json',dict(files=protection,production_code_modified=False,scientific_attempts=0))
    status='P1_PASS_CANDIDATE' if len(metrics)==6 and failure is None else 'P1_PARTIAL' if metrics else 'P1_BLOCKED'
    report=dict(P1_REPRODUCTION=status,P1_DIAGNOSTIC_CALLS=calls['p1'],ORIGINAL_REFERENCE_CALLS=calls['reference'],completed_valid_cells=len(metrics),reference_values={k:v['value'] for k,v in refs.items()},comparisons=comparisons,failure=failure,HF_AUXILIARY_ANALYSIS='AVAILABLE' if any('HF' in r for r in metrics) else 'NOT_VERIFIED',RESOURCE_ACCOUNTING='INCOMPLETE',RESOURCE_COMPLIANCE='NOT_ESTABLISHED',P1_INDEPENDENT_ACCEPTANCE='PENDING',P2_P3_P4='NOT_EXECUTED',PRODUCTION_ADMISSION='BLOCKED',limitations=['pre-D60 source unresolved; conditional on frozen seed','six cells are not independent random samples','reproduction does not prove proxy accuracy','host preparation CPU and meter tail incomplete'],summary=summary,entry_sha256=sha(__file__),kernel_sha256=sha(STAGE/'recovery.py'))
    w.json('FINAL_REPORT.json',report);lines=['# P1 历史代理复现结果','',status,'','| 世界 | 动作 | P0 | REF | P1 | REF−P0 | P1−REF | P1−P0 | 十字段 |','|---|---|---|---|---|---|---|---|---|']
    for r in metrics:lines.append('| '+' | '.join(str(r[k]) for k in ['world','action','P0','REF','P1','REF_minus_P0','P1_minus_REF','P1_minus_P0','ten_fields'])+' |')
    lines+=['',json.dumps(report,ensure_ascii=False,indent=2),'','CELL保存服务状态、Pmax、NG、完成/停止时刻、经济账本和D120状态。TRACE保存控制、几何端点、时钟、reset、边界快照。没有创造释放事务。历史超时334.8579769秒及历史CPU/写入未知保持不变。最终退出会计见RESOURCE_RECEIPT.json。'];w.write('REPORT.md','\n'.join(lines));clock.check()
    w.accounting_receipt('WORKER_ACCOUNTING.json',dict(status=status,worker_pid=os.getpid(),cpu_snapshot=time.process_time(),wall_snapshot=time.monotonic()-origin,operations=w.operations,accounting='INCOMPLETE: unobserved host resources'));print(json.dumps(dict(status=status,calls=calls,valid_cells=len(metrics),failure=None if failure is None else failure['message'],summary=summary),ensure_ascii=False),flush=True);return 0 if status=='P1_PASS_CANDIDATE' else 1

def process_times(handle):
    from ctypes import wintypes
    class FT(ctypes.Structure):_fields_=[('low',wintypes.DWORD),('high',wintypes.DWORD)]
    a,b,c,d=FT(),FT(),FT(),FT();f=ctypes.windll.kernel32.GetProcessTimes;f.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(FT)]*4;f.restype=wintypes.BOOL;require(f(int(handle),ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)),'GET_PROCESS_TIMES');v=lambda x:(x.high<<32)|x.low
    return dict(creation_filetime=v(a),exit_filetime=v(b),kernel_seconds=v(c)/1e7,user_seconds=v(d)/1e7)
def meter():
    prep=read(HERE/'PREPARATION_ACCOUNTING.json');origin=time.monotonic()-(prep['elapsed_at_launch']+max(0.,time.time()-prep['bridge_utc_epoch']));deadline=origin+900;p=subprocess.Popen([sys.executable,'-I','-S','-B',str(Path(__file__).resolve()),'--worker',str(origin)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);limit=None
    while p.poll() is None:
        t=process_times(p._handle)
        if time.monotonic()>=deadline or t['kernel_seconds']+t['user_seconds']+time.process_time()>=120:limit='RESOURCE_LIMIT';p.kill();break
        time.sleep(.05)
    out,err=p.communicate();end=time.monotonic();final=process_times(p._handle);entry_cpu=time.process_time();wf=HERE/'WORKER_ACCOUNTING.json';prior=read(wf)['cumulative_logical_write_bytes'] if wf.exists() else prep['cumulative_logical_write_bytes'];writer=Writer(HERE,limit=134217728,initial_written=prior)
    receipt=writer.accounting_receipt('RESOURCE_RECEIPT.json',dict(worker_pid=p.pid,worker_exit_status=p.returncode,worker_final_cpu=final,entry_pid=os.getpid(),entry_cpu_at_worker_exit=entry_cpu,known_cpu_subtotal=entry_cpu+final['kernel_seconds']+final['user_seconds'],limits=dict(cpu=120,wall=900,cumulative_logical_write_bytes=134217728),wall_start_utc=prep['wall_start_utc'],wall_seconds_at_worker_exit=end-origin,deadline_trigger=limit,path_b='APPROVED: worker exit cutoff; final receipt and handle closure only',resource_accounting='INCOMPLETE',resource_compliance='NOT_ESTABLISHED',unknown_cpu='host preparation and readonly tools; final entry tail INCOMPLETE',wall_limitation='initial readonly command before clock anchor not precisely captured; UTC bridge at startup then common monotonic deadline',write_limitation='controlled writes counted; host writes INCOMPLETE',entry_tail='INCOMPLETE; not zero',stdout=out.decode(errors='replace'),stderr=err.decode(errors='replace')));p._handle.Close();print(json.dumps(receipt,ensure_ascii=False),flush=True);return p.returncode
if __name__=='__main__':sys.exit(worker() if '--worker' in sys.argv else meter())
