"""Task-local synthetic engineering verification only. No archived replay or science."""
import sys,os,time,json,hashlib,ast,copy,unittest,subprocess,ctypes,difflib,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'l3_b_diagnostic_recovery_001_stage_a_20261114'
sys.path.insert(0,str(HERE))
from recovery import *
WRITER=None
CLOCK=None
PROOF=None

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class SyntheticTests(unittest.TestCase):
    def seed(self):
        state=dict(target_id=0,estimate_tick=0,available_tick=0,position_estimate=[0.,0.],velocity_estimate=[0.,0.],velocity_source='PUBLIC_PRIOR',last_observation_tick=None,source='PUBLIC_PRIOR',status='PRIOR_ONLY',diagnostics=None)
        return dict(announcements=[dict(id=0,speed_limit=1.)],internal_states_at_D60={0:state},accepted_position_history={0:[]},accepted_receipts={},pending_observations=[],consumed_records=[])
    def event(self,i,t,available,accepted=True):
        e=dict(has_accepted_estimate=accepted,optimizer_converged=True,numerical_ill_conditioned=False,ambiguity_detected=False,boundary_active=False,numeric_contract_violation=False,estimate=[t*.01,0.])
        return dict(identity=str(i),target_id=0,measurement_tick=t,available_tick=available,estimate=e,source='MODEL',provenance='SIMULATED',observation_origin='MODEL')
    def physical(self):
        return dict(positions=[[0.,0.],[1.,0.],[0.,1.]],states={},lefts={0:True},geometry_before={0:True},statuses={0:'ACTIVE'},tasks={},effort=.2)
    def test_queue_pending_rejected_velocity(self):
        r=Replay(self.seed());r.enqueue(self.event(0,0,0));r.enqueue(self.event(1,5,10));r.enqueue(self.event(2,6,6,False));r.freeze(6)
        self.assertEqual((len(r.pending),len(r.history[0]),len(r.consumed)),(1,1,2));r.freeze(10)
        self.assertEqual(r.states[0]['velocity_estimate'],[.2,0.]);self.assertEqual(len(r.history[0]),2)
        before=typed(vars(r));r.terminal(120);self.assertEqual(before,typed(vars(r)))
        with self.assertRaises(RuntimeError):r.freeze(120)
    def test_historical_consumed_and_pending(self):
        s=self.seed();s['consumed_records']=[self.event('old',0,0)];r=Replay(s)
        with self.assertRaises(RuntimeError):r.enqueue(self.event('old',0,0))
        s=self.seed();s['pending_observations']=[self.event('pending',1,80)];r=Replay(s)
        with self.assertRaises(RuntimeError):r.enqueue(self.event('pending',1,80))
        del s['pending_observations'][0]['identity']
        with self.assertRaises(RuntimeError):Replay(s)
    def test_duplicate_source_and_latency(self):
        r=Replay(self.seed());e=self.event(0,0,0);r.enqueue(e)
        with self.assertRaises(RuntimeError):r.enqueue(e)
        with self.assertRaises(RuntimeError):r.enqueue(self.event(2,10,9))
        e=self.event(3,10,10);e['observation_origin']='ACTUAL'
        with self.assertRaises(RuntimeError):r.enqueue(e)
    def test_typed_snapshot(self):
        self.assertNotEqual(typed(0.),typed(-0.));self.assertNotEqual(typed([1]),typed((1,)));self.assertNotEqual(typed(1),typed(True));self.assertEqual(typed(float('nan')),typed(float('nan')))
        with self.assertRaises(RuntimeError):same({'states':1},{'states':2})
    def test_real_boundary_operation(self):
        p=self.physical();v=dict(beliefs=copy.deepcopy(self.seed()['internal_states_at_D60']),assignment=[0]);seen=[]
        boundary_check(80,v,p,operation=lambda:seen.append(80));self.assertEqual(seen,[80])
        def corrupt():p['positions'][0][0]=2.
        with self.assertRaisesRegex(RuntimeError,'BOUNDARY_STATE_CHANGED'):boundary_check(100,v,p,operation=corrupt)
    def test_feedback_whitelist_and_continuity(self):
        r=Replay(self.seed());r.enqueue(self.event('f',5,80));p=self.physical();v=dict(beliefs=copy.deepcopy(r.states),assignment=[0]);bid=id(v['beliefs']);target=id(v['beliefs'][0]);before=typed(p)
        boundary_check(80,v,p,consumer=r,operation=lambda:None,feedback_operation=lambda:r.freeze(80))
        self.assertEqual(typed(p),before);self.assertEqual((id(v['beliefs']),id(v['beliefs'][0])),(bid,target));self.assertEqual(v['beliefs'][0]['estimate_tick'],5)
        def illegal():r.announcements[0]['speed_limit']=100.;return r.freeze(100)
        with self.assertRaises(RuntimeError):boundary_check(100,v,p,consumer=r,operation=lambda:None,feedback_operation=illegal)
    def test_nonfinite(self):
        p=self.physical();p['positions'][0][0]=float('nan')
        with self.assertRaises(RuntimeError):validate_state(p,self.seed()['internal_states_at_D60'])
    def test_prediction_and_feedback_chain(self):
        b=self.seed()['internal_states_at_D60'][0];b['velocity_estimate']=[.4,0.]
        self.assertEqual(prediction(b,40),prediction(b,40,True));b['last_observation_tick']=0
        self.assertEqual(prediction(b,40)[0],[.4,0.]);self.assertEqual(prediction(b,40,True)[0],[.8,0.]);self.assertEqual(prediction(b,20)[1],[.4,0.]);self.assertEqual(prediction(b,21)[1],[0.,0.])
    def catalog_fixture(self):
        feedback=[];links=[]
        for i,(tick,available,phase) in enumerate([(60,90,'MODEL_ASSIGNMENT_LEFT'),(80,80,'MODEL_INTERVAL_RIGHT')]):
            f=dict(frame=dict(frame_id=str(i),target_id=0,tick=tick,measurement_time=tick*.05,available_time=available*.05,records=[]),endpoint=dict(target_id=0,tick=tick,provenance='SIMULATED',observation_origin='MODEL'),result=dict(estimate_result=self.event(i,tick,available)['estimate']))
            feedback.append(f);links.append(dict(feedback_event_ordinal=i,feedback_digest=digest(f),frame_id=str(i),target_id=0,tick=tick,transaction_identity='b'+(':ASSIGN:' if i==0 else ':ADVANCE:')+str(tick),endpoint_side=phase))
        raw=dict(branch='b',provenance='SIMULATED',observation_origin='MODEL',endpoint_fusions=2,feedback=feedback)
        tx={t:dict(transaction_identity='b:ASSIGN:'+str(t),committed_feedback_ordinals=[0] if t==60 else [],connections=links) for t in (60,80,100)}
        def consumed(i,t,ord):
            f=feedback[i];return dict(feedback_identity=str(i),feedback_digest=digest(f),target_id=0,measurement_tick=f['frame']['tick'],available_tick=90 if i==0 else 80,consumed_tick=t,queue_ordinal=ord)
        pending=self.event('0',60,90)
        snapshots={80:dict(events=[consumed(1,80,1)],pending=[pending]),100:dict(events=[consumed(0,100,0)],pending=[])}
        return raw,tx,snapshots,links
    def test_catalog_transactions_pending_same_tick(self):
        args=self.catalog_fixture();out=event_catalog(*args,order_evidence=PROOF,terminal_pending=[])
        self.assertEqual([e['available_tick'] for e in out['events']],[90,80]);self.assertEqual(out['events'][1]['phase'],'MODEL_INTERVAL_RIGHT')
        bad=copy.deepcopy(args);bad[1][60]['committed_feedback_ordinals']=[]
        with self.assertRaises(RuntimeError):event_catalog(*bad,order_evidence=PROOF)
        bad=copy.deepcopy(args);bad[2][80]['events'][0]['queue_ordinal']=0
        with self.assertRaises(RuntimeError):event_catalog(*bad,order_evidence=PROOF)
        with self.assertRaises(RuntimeError):event_catalog(*args,order_evidence={})
    def test_metrics_and_p1(self):
        cells=[dict(version=v,world=w,action=a,value=float(i)+j,hf=float(i)) for j,v in enumerate(['P1','P2','P3','P4']) for w in ['H2','H3'] for i,a in enumerate(['KEEP','SWITCH','MEMBER_CHANGE'])]
        m=value_metrics(cells);self.assertEqual(m['MAE']['P2'],1.);self.assertEqual(m['effects'][0]['Interaction'],0.)
        a={k:[] for k in P1_FIELDS};a['value']=1.;self.assertEqual(compare_p1(a,copy.deepcopy(a))['status'],'VERIFIED')
        b=copy.deepcopy(a);b['tasks']=[1]
        self.assertEqual(compare_p1(a,b)['status'],'FAILED')
        b=copy.deepcopy(a);b['value']+=1e-12
        self.assertEqual(compare_p1(a,b)['status'],'FAILED')
    def test_evidence_gate(self):
        with self.assertRaises(RuntimeError):final_status({k:True for k in REQUIRED_GATES},HERE,CODE_SHA)
        self.assertEqual(final_status({},HERE,CODE_SHA)['status'],'L3_B_BLOCKED')
    def test_writes_do_not_refund(self):
        w=Writer(HERE/'synthetic_io',limit=12);w.write('a',b'1234');w.write('a',b'12',replace=True);(w.root/'a').unlink();w.write('b',b'1234');self.assertEqual(w.written,10)
        with self.assertRaises(RuntimeError):w.write('c',b'123')
        WRITER.written+=w.written;WRITER.operations+=w.operations
    def test_ledger(self):
        c=dict(completion=1.,flow=.1,late=.2,effort=.05,terminal=.1,change=.02);v=c['completion']-sum(c[k] for k in ('flow','late','effort','terminal','change'));self.assertEqual(ledger_check(c,v),v)
    def test_velocity_retention_clipping_and_chain(self):
        s=self.seed();s['internal_states_at_D60'][0]['velocity_estimate']=[.3,0.];r=Replay(s);r.enqueue(self.event('one',1,1));r.freeze(1);self.assertEqual(r.states[0]['velocity_estimate'],[.3,0.])
        e=self.event('two',6,6);e['estimate']['estimate']=[100.,0.];r.enqueue(e);r.freeze(6);self.assertEqual(r.states[0]['velocity_estimate'],[1.,0.]);self.assertTrue(r.audit_rows[-1]['clipped'])
        self.assertEqual(feedback_chain(True,{'x':1},{'x':1})['belief_changed'],'UNCHANGED');self.assertEqual(feedback_chain(True,{},None)['belief_changed'],'NOT_VERIFIED')
    def test_boundary_all_physical_fields(self):
        for key in PHYSICAL:
            p=self.physical();v=dict(beliefs=copy.deepcopy(self.seed()['internal_states_at_D60']))
            def mutation():
                if key=='effort':p[key]+=1.
                elif key=='positions':p[key][0][0]+=1.
                else:p[key]['synthetic_corruption']=True
            with self.subTest(field=key):
                with self.assertRaisesRegex(RuntimeError,'BOUNDARY_STATE_CHANGED'):boundary_check(80,v,p,operation=mutation)
    def test_trajectory_diagnostics(self):
        r=dict(target=0,tick=40,estimate_tick=0,roles=['a'],position_prediction=[1.,0.],velocity_prediction=[.2,0.],estimate_position=[0.,0.],estimate_velocity=[.2,0.],control=[[1.,0.]])
        b=copy.deepcopy(r);b['control']=[[0.,0.]]
        m=trajectory_metrics([], [r],lambda j,t:([t*.01,0.],[.2,0.]),[b],comparison_pair='P2/P1')
        self.assertEqual(m['first_control_divergence'],40);self.assertAlmostEqual(m['state_errors'][0]['prediction_position_error'],.6);self.assertEqual(m['state_errors'][0]['estimation_position_error'],0.)
    def test_clock_stop(self):
        with self.assertRaises(RuntimeError):Clock(time.monotonic()-1801).check()
        with self.assertRaises(RuntimeError):Clock(time.monotonic(),cpu_limit=0).check()

class TimedResult(unittest.TestResult):
    def startTest(self,test):CLOCK.check();super().startTest(test)
    def stopTest(self,test):super().stopTest(test);CLOCK.check()

def worker():
    global WRITER,CLOCK,PROOF,CODE_SHA
    prep=json.loads((HERE/'PREPARATION_ACCOUNTING.json').read_bytes());CLOCK=Clock(float(sys.argv[-1]),cpu_limit=300,wall_limit=1800)
    WRITER=Writer(HERE,initial_written=prep['cumulative_logical_write_bytes'],clock=CLOCK)
    CODE_SHA=sha(HERE/'recovery.py');engine_sha=sha(__file__);pins=json.loads((BASE/'HISTORICAL_IDENTITY.json').read_bytes());before={str(p):sha(p) for p in [BASE/'recovery.py',BASE/'engineering_check.py',BASE/'HISTORICAL_IDENTITY.json',BASE/'ACTUAL_IMPORTS.json',BASE/'ENVIRONMENT.json']}
    report=dict(task='L3_B_STAGE_A_MINIMAL_REMEDIATION_EXECUTION_001',code_sha256=CODE_SHA,engineering_sha256=engine_sha,formal_replay=False,p1_p4=False,scientific_calls=0,historical_wall=334.8579769,historical_status='OVER_LIMIT')
    try:
        CLOCK.check()
        for f in [HERE/'recovery.py',Path(__file__)]:ast.parse(f.read_bytes())
        PROOF=source_order_evidence(BASE/'historical',pins)
        result=TimedResult();unittest.defaultTestLoader.loadTestsFromTestCase(SyntheticTests).run(result)
        WRITER.json('SYNTHETIC_TEST_RESULTS.json',dict(code_sha256=CODE_SHA,engineering_sha256=engine_sha,tests=result.testsRun,failures=[str(x) for x in result.failures],errors=[str(x) for x in result.errors],scientific_calls=0,scope='synthetic only; no archived consumer replay'))
        require(result.wasSuccessful(),'SYNTHETIC_TEST_FAILED')
        site=Path(r'D:\miniconda3\envs\dynamic_member_coalition_core\Lib\site-packages');require(site.is_dir(),'FIXED_SITE');sys.path.insert(0,str(site))
        guard=HistoricalImports(BASE/'historical',pins);guard.install();proxy=importlib.import_module('research.non_oracle.stfbs_lite_proxy')
        fn,ns=build_kernel((BASE/'historical/research/non_oracle/stfbs_lite_proxy.py').read_text(encoding='utf-8'));require(callable(fn),'KERNEL_CONSTRUCTION')
        actual=guard.audit();old=json.loads((BASE/'ACTUAL_IMPORTS.json').read_bytes())
        delta={k:v for k,v in actual.items() if k not in old};require(all(v['sha256']==pins[Path(v['path']).relative_to(BASE/'historical').as_posix()]['sha256'] for v in actual.values()),'PROJECT_IMPORT_IDENTITY')
        import numpy,scipy,psutil
        env={}
        for module,version in [(numpy,'2.1.3'),(scipy,'1.15.3'),(psutil,'7.2.2')]:
            require(module.__version__==version,'PACKAGE_VERSION');require(Path(module.__file__).resolve().is_relative_to(site.resolve()),'PACKAGE_ORIGIN')
            env[module.__name__]=dict(version=module.__version__,path=module.__file__)
        binaries={}
        for n,m in list(sys.modules.items()):
            p=getattr(m,'__file__',None)
            if p and str(p).lower().endswith('.pyd') and Path(p).resolve().is_relative_to(site.resolve()):CLOCK.check();binaries[str(p)]=sha(p)
        # Actual imported extensions above; DLL files below are package identities, not a claim of loaded DLL enumeration.
        dlls={}
        for d in (site/'numpy.libs',site/'scipy.libs'):
            for p in d.glob('*.dll'):CLOCK.check();dlls[str(p)]=sha(p)
        WRITER.json('IDENTITY_SUPPLEMENT.json',dict(baseline_commit='ff626f05173d6f11519e213a6230a9ead9441bfb',historical_manifest_reference=str(BASE/'HISTORICAL_IDENTITY.json'),existing_import_reference=str(BASE/'ACTUAL_IMPORTS.json'),historical_files=len(pins),observed_project_modules=len(actual),new_project_modules=delta,namespace_paths=guard.namespace_paths,python=dict(path=sys.executable,version=sys.version,sha256=sha(sys.executable)),packages=env,imported_extensions=binaries,package_dll_identities=dlls,untriggered_lazy_imports='NOT_VERIFIED',order_source_evidence=PROOF))
        report.update(implementation='TASK_LOCAL_PATCH_IMPLEMENTED',engineering_tests='PASSED',tests=result.testsRun,actual_project_modules=len(actual),stage_a_acceptance='PENDING_INDEPENDENT_REVIEW',l3_b='BLOCKED_PENDING_REVIEW')
    except BaseException as exc:
        report.update(implementation='INCOMPLETE',engineering_tests='FAILED_OR_NOT_COMPLETED',error=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),stage_a_acceptance='NOT_ACCEPTED',l3_b='BLOCKED')
    CLOCK.check()
    after={p:sha(p) for p in before};require(before==after,'HISTORICAL_PROTECTION')
    WRITER.json('HISTORICAL_PROTECTION.json',dict(before=before,after=after,equal=before==after,scope='existing stage A source and identity records; no historical extraction performed'))
    diff=''.join(''.join(difflib.unified_diff((BASE/n).read_text(encoding='utf-8').splitlines(True),(HERE/n).read_text(encoding='utf-8').splitlines(True),fromfile='frozen/'+n,tofile='task_local/'+n)) for n in ['recovery.py','engineering_check.py'])
    WRITER.write('FULL_UNIFIED_DIFF.patch',diff)
    report.update(resource_accounting='INCOMPLETE',resource_acceptance='NOT_ESTABLISHED',unverified=['archived event replay and six actual seed bindings','P1 ten-field historical reproduction','formal 24-cell metrics','untriggered lazy imports','host editing CPU, preliminary Git/read subprocess CPU and meter final exit tail'],path_b='APPROVED: worker exit cutoff',cpu_worker_snapshot=time.process_time(),wall_window_snapshot=time.monotonic()-CLOCK.wall_start)
    WRITER.json('ENGINEERING_RESULT.json',report)
    text='# Stage A 最小整改回执\n\n'+json.dumps(report,ensure_ascii=False,indent=2)+'\n\nR1：完整种子、历史已消费身份、事务及真实 available 时间保护。R2：真实边界回调前后比较，consumer 与控制快照分开核对，逐字段更新。R3：复用265项及32项原身份资料，只保存隔离导入补证。R4：年龄、估计/预测误差、控制、服务、经济、因子指标；本轮仅合成验证。R6：十字段比较及绑定代码和输入身份的证据门槛。\n\n原历史超时334.8579769秒及原CPU/写入未知保持不变。本轮没有执行P1—P4、历史反馈回放、WLS、R、Assignment或科学attempt。生产文件未修改。最终退出资源见RESOURCE_RECEIPT.json。\n'
    WRITER.write('REPORT.md',text)
    manifest={p.relative_to(HERE).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in HERE.rglob('*') if p.is_file()}
    WRITER.json('MANIFEST.json',dict(files=manifest,exclusions=['MANIFEST.json self','WORKER_ACCOUNTING.json','RESOURCE_RECEIPT.json'],note='final accounting and outer receipt contain their own cumulative counts; no self-hash claim'))
    record=WRITER.accounting_receipt('WORKER_ACCOUNTING.json',dict(report_status=report.get('engineering_tests'),worker_pid=os.getpid(),worker_cpu_snapshot=time.process_time(),window_wall_snapshot=time.monotonic()-CLOCK.wall_start,operations=WRITER.operations,logical_write_scope='all controlled task-file writes including preparation; unknown host writes INCOMPLETE',resource_accounting='INCOMPLETE'))
    print(json.dumps(dict(status=report.get('engineering_tests'),tests=report.get('tests'),error=report.get('message'),cumulative_write=record['cumulative_logical_write_bytes'])),flush=True)
    return 0 if report.get('engineering_tests')=='PASSED' else 1

def process_times(handle):
    from ctypes import wintypes
    class FT(ctypes.Structure):_fields_=[('low',wintypes.DWORD),('high',wintypes.DWORD)]
    a,b,c,d=FT(),FT(),FT(),FT();f=ctypes.windll.kernel32.GetProcessTimes;f.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(FT)]*4;f.restype=wintypes.BOOL
    require(f(int(handle),ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)),'GET_PROCESS_TIMES')
    val=lambda x:((x.high<<32)|x.low)
    return dict(creation_filetime=val(a),exit_filetime=val(b),kernel_seconds=val(c)/1e7,user_seconds=val(d)/1e7)

def meter():
    prep=json.loads((HERE/'PREPARATION_ACCOUNTING.json').read_bytes());origin=time.monotonic()-(prep['elapsed_at_launch']+max(0.,time.time()-prep['bridge_utc_epoch']));deadline=origin+1800
    p=subprocess.Popen([sys.executable,'-I','-S','-B',str(Path(__file__).resolve()),'--worker',str(origin)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    limit=None
    while p.poll() is None:
        current=process_times(p._handle)
        if time.monotonic()>=deadline or current['kernel_seconds']+current['user_seconds']+time.process_time()>=300:
            limit='RESOURCE_LIMIT';p.kill();break
        time.sleep(.05)
    out,err=p.communicate();exit_at=time.monotonic();final=process_times(p._handle);entry_cpu=time.process_time()
    wf=HERE/'WORKER_ACCOUNTING.json';prior=json.loads(wf.read_bytes())['cumulative_logical_write_bytes'] if wf.exists() else prep['cumulative_logical_write_bytes']
    w=Writer(HERE,initial_written=prior)
    receipt=w.accounting_receipt('RESOURCE_RECEIPT.json',dict(worker_pid=p.pid,worker_final_cpu=final,worker_exit_status=p.returncode,entry_pid=os.getpid(),entry_cpu_at_worker_exit=entry_cpu,known_cpu_subtotal=entry_cpu+final['kernel_seconds']+final['user_seconds'],cpu_unknown='host editing and preparatory tools INCOMPLETE; entry exit tail INCOMPLETE',wall_start_utc=prep['wall_start_utc'],wall_seconds_at_worker_exit=exit_at-origin,wall_cutoff='worker exit observed by external meter; polling resolution 0.05 sec',deadline_trigger=limit,path_b='APPROVED',accounting='INCOMPLETE',acceptance='NOT_ESTABLISHED',entry_administrative_tail='INCOMPLETE; resource receipt and handle closure only',worker_stdout=out.decode(errors='replace'),worker_stderr=err.decode(errors='replace'),historical_resources='UNCHANGED; historical wall334.8579769 OVER_LIMIT',write_accounting='controlled writes counted; unobserved host writes INCOMPLETE'))
    p._handle.Close();print(json.dumps(receipt,ensure_ascii=False),flush=True)
    return p.returncode

if __name__=='__main__':sys.exit(worker() if '--worker' in sys.argv else meter())
