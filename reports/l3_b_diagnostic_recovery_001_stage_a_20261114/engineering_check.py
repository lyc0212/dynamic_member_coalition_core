"""Engineering only: synthetic data and import identity. No archived replay."""
import sys,time,os,json,hashlib,subprocess,ast,unittest,copy
from pathlib import Path
START=time.monotonic(); CPU=time.process_time()
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
sys.path.insert(0,str(HERE))
from recovery import *
WRITER=Writer(HERE)

class SyntheticTests(unittest.TestCase):
    def seed(self):
        state=dict(target_id=0,estimate_tick=0,available_tick=0,position_estimate=[0.,0.],velocity_estimate=[0.,0.],velocity_source='PUBLIC_PRIOR',last_observation_tick=None,source='PUBLIC_PRIOR',status='PRIOR_ONLY',diagnostics=None)
        return dict(internal_states_at_D60={0:state},accepted_position_history={0:[]},accepted_receipts={},pending_observations=[],consumed_records=[])
    def event(self,i,t,available,accepted=True):
        e=dict(has_accepted_estimate=accepted,optimizer_converged=True,numerical_ill_conditioned=False,ambiguity_detected=False,boundary_active=False,numeric_contract_violation=False,estimate=[t*.01,0.])
        return dict(identity=str(i),target_id=0,measurement_tick=t,available_tick=available,estimate=e,provenance='SIMULATED',observation_origin='MODEL')
    def test_queue_pending_rejected_velocity(self):
        r=Replay(self.seed(),[dict(id=0,speed_limit=1.)]);r.enqueue(self.event(0,0,0));r.enqueue(self.event(1,5,10));r.enqueue(self.event(2,6,6,False));r.freeze(6)
        self.assertEqual(len(r.pending),1);self.assertEqual(len(r.history[0]),1);self.assertEqual(len(r.consumed),2)
        r.freeze(10);self.assertEqual(len(r.pending),0);self.assertEqual(len(r.history[0]),2);self.assertEqual(r.states[0]['velocity_estimate'],[.2,0.])
    def test_duplicate_source_and_latency(self):
        r=Replay(self.seed(),[dict(id=0,speed_limit=1.)]);e=self.event(0,0,0);r.enqueue(e)
        with self.assertRaises(RuntimeError):r.enqueue(e)
        e=self.event(2,10,9)
        with self.assertRaises(RuntimeError):r.enqueue(e)
        e=self.event(3,10,10);e['observation_origin']='ACTUAL'
        with self.assertRaises(RuntimeError):r.enqueue(e)
    def test_typed_snapshot(self):
        self.assertNotEqual(typed(0.),typed(-0.));self.assertNotEqual(typed([1]),typed((1,)));self.assertNotEqual(typed(1),typed(True));self.assertEqual(typed(float('nan')),typed(float('nan')))
        a={'states':{'x':1}};b=copy.deepcopy(a);b['states']['x']=2
        with self.assertRaises(RuntimeError):same(a,b)
    def test_boundary_fields(self):
        p={k:{} for k in PHYSICAL};p['positions']=[1.,2.];p['effort']=.2;v=dict(beliefs={0:1},assignment=[0]);before=typed(p)
        boundary_check(80,v,p,{0:2});self.assertEqual(typed(p),before);self.assertEqual(v['beliefs'],{0:2})
        del p['tasks']
        with self.assertRaises(RuntimeError):boundary_check(80,v,p)
    def test_prediction(self):
        b=self.seed()['internal_states_at_D60'][0];b['velocity_estimate']=[.4,0.]
        self.assertEqual(prediction(b,40),prediction(b,40,True));b['last_observation_tick']=0
        self.assertEqual(prediction(b,40)[0],[.4,0.]);self.assertEqual(prediction(b,40,True)[0],[.8,0.]);self.assertEqual(prediction(b,40)[1],[0.,0.])
    def test_metrics_and_final_gate(self):
        cells=[dict(version=v,world=w,action=a,value=float(i),hf=float(i)) for v in ['P1','P2','P3','P4'] for w in ['H2','H3'] for i,a in enumerate(['KEEP','SWITCH','MEMBER_CHANGE'])]
        m=value_metrics(cells);self.assertEqual(m['MAE']['P1'],0);self.assertTrue(all(e['Interaction']==0 for e in m['effects']))
        g={k:True for k in REQUIRED_GATES};self.assertEqual(final_status(g),'L3_B_DIAGNOSTIC_PASS_CANDIDATE');g['resource_accounting']=False;self.assertEqual(final_status(g),'L3_B_BLOCKED')
    def test_writes_do_not_refund(self):
        w=Writer(HERE/'synthetic_io',limit=12);w.write('a',b'1234');w.write('a',b'12',replace=True);(w.root/'a').unlink();w.write('b',b'1234');self.assertEqual(w.written,10)
        with self.assertRaises(RuntimeError):w.write('c',b'123')
        WRITER.written+=w.written;WRITER.operations+=w.operations
    def test_ledger(self):
        c=dict(completion=1.,flow=.1,late=.2,effort=.05,terminal=.1,change=.02);v=c['completion']-sum(c[k] for k in ('flow','late','effort','terminal','change'));self.assertEqual(ledger_check(c,v),v)

def prepare_history():
    auth=json.loads((REPO/'reports/stfbs_lite_h2_h3_extension_005/H2_SWITCH/authorization.json').read_bytes());pins=auth['source_sha256']
    git=['git','-c','safe.directory='+REPO.as_posix()]
    names=list(pins);queries=''.join(HISTORICAL_COMMIT+':'+n+'\n' for n in names)
    raw=subprocess.check_output(git+['cat-file','--batch'],input=queries.encode(),cwd=REPO)
    pos=0;identities={}
    for name in names:
        end=raw.index(b'\n',pos);header=raw[pos:end].decode().split();require(len(header)==3 and header[1]=='blob','HISTORICAL_BLOB');length=int(header[2]);data=raw[end+1:end+1+length];pos=end+length+2
        actual=hashlib.sha256(data).hexdigest();require(actual==pins[name],'HISTORICAL_SHA/'+name)
        WRITER.write('historical/'+name,data);identities[name]=dict(commit=HISTORICAL_COMMIT,blob=header[0],sha256=actual)
    require(pos==len(raw),'BATCH_PARSE_TAIL');WRITER.json('HISTORICAL_IDENTITY.json',identities)
    return identities

def main():
    require(time.time()<float(sys.argv[1]),'WALL_LIMIT')
    for f in [HERE/'recovery.py',Path(__file__)]:ast.parse(f.read_text(encoding='utf-8'))
    pins=prepare_history()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(SyntheticTests);result=unittest.TestResult();suite.run(result)
    WRITER.json('SYNTHETIC_TEST_RESULTS.json',dict(tests=result.testsRun,failures=[str(x) for x in result.failures],errors=[str(x) for x in result.errors],scientific_calls=0))
    require(result.wasSuccessful(),'SYNTHETIC_TEST_FAILED')
    # Import engineering validation only; do not invoke any scientific function.
    sys.path.insert(0,r'D:\miniconda3\envs\dynamic_member_coalition_core\Lib\site-packages')
    imports=HistoricalImports(HERE/'historical',pins);imports.install()
    proxy=importlib.import_module('research.non_oracle.stfbs_lite_proxy')
    fn,ns=build_kernel((HERE/'historical/research/non_oracle/stfbs_lite_proxy.py').read_text(encoding='utf-8'))
    require(callable(fn),'KERNEL_CONSTRUCTION');actual=imports.audit();WRITER.json('ACTUAL_IMPORTS.json',actual)
    from importlib import metadata
    WRITER.json('ENVIRONMENT.json',dict(python=sys.executable,version=sys.version,packages={n:metadata.version(n) for n in ['numpy','scipy','psutil']},imports={n:getattr(sys.modules.get(n),'__file__',None) for n in ['numpy','scipy','psutil']},scope='import identity only; no scientific evaluation'))
    require(time.time()<float(sys.argv[1]),'WALL_LIMIT');require(time.process_time()-CPU<120,'CPU_LIMIT')
    return dict(status='STAGE_A_IMPLEMENTED_ENGINEERING_CHECKS_PASSED',tests=result.testsRun,actual_project_modules=len(actual),formal_replay=False,p1_p4=False,scientific_calls=0,unverified=['archived queue replay','P1 equality','final full scientific acceptance','complete host/controller CPU tail'],cpu_process_seconds=time.process_time()-CPU,wall_process_seconds=time.monotonic()-START,cumulative_write_bytes_before_final=WRITER.written,accounting_status='INCOMPLETE: process CPU measured; Git child, host editing and final exit tail not fully measured')

if __name__=='__main__':
    try:report=main()
    except BaseException as exc:
        import traceback
        report=dict(status='STAGE_A_STOPPED',error=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),cpu_process_seconds=time.process_time()-CPU,wall_process_seconds=time.monotonic()-START,scientific_calls=0)
    WRITER.json('ENGINEERING_RESULT.json',report)
    print(json.dumps(report,ensure_ascii=False))
