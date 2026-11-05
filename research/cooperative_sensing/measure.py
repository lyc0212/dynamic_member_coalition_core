"""Thin single-batch adapter; certified Win32 lifecycle implementation is unchanged."""
import hashlib
import json
from pathlib import Path
import sys
import time
from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.supervisor import GateSupervisor,Budget,save_new

class Measurement:
    def __init__(self,out,total=300.,wall=600.,reserve=5.5):
        self.out=Path(out);self.out.mkdir(parents=True,exist_ok=False)
        self.budget=Budget(total);self.deadline=time.perf_counter()+wall
        self.reserve=reserve;self.rows=[];self.cpu_start=time.process_time()

    def run(self,request,cpu=25.,wall=180.):
        remaining=self.deadline-time.perf_counter()-self.reserve
        if remaining<=0 or self.budget.exhausted():raise RuntimeError('resource_blocked_before_create')
        core=GateSupervisor(self.out/f'batch_{len(self.rows):03d}')
        try:
            raw=core.run('bearing_fusion',sys.executable,Path(__file__).with_name('worker.py'),
                mode=json.dumps(request),cpu=0.,cpu_limit=cpu,wall_limit=min(wall,remaining),g9=self.budget)
        finally:core.close()
        self.rows.append(raw)
        save_new(self.out/f'ledger_{len(self.rows):03d}.json',dict(rows=self.budget.rows,
            used=self.budget.used,supervisor_cpu=time.process_time()-self.cpu_start))
        if raw['reason']=='completed':
            folder=Path(raw['folder']);membership=json.loads((folder/'membership.json').read_text())
            assert membership['member'] and raw['cleanup_passed'] and raw['final_accounting']['ActiveProcesses']==0
        return raw

def integration(out):
    """Synthetic thresholds only; production 300/25/600/180 constants stay frozen."""
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    save_new(out/'definition.json',dict(max_jobs=10,job_cpu_cap=20.,wall_cap=120.,
        tests=['two_instances','cpu_coverage','crash','single_cpu','single_wall','shared_live_cpu','deadline','checkpoint']))
    start=time.perf_counter()
    m=Measurement(out/'normal',total=12.,wall=100.)
    a=m.run(dict(synthetic='busy',cpu=.15));assert a['reason']=='completed'
    b=m.run(dict(synthetic='busy',cpu=.15));assert b['reason']=='completed'
    assert len(m.budget.rows)==2 and a['job_name']!=b['job_name']
    assert (Path(a['folder'])/'synthetic_checkpoint.json').exists()
    for row in (a,b):
        internal=json.loads((Path(row['folder'])/'synthetic_end.json').read_text())['internal_cpu']
        assert internal<=row['final_accounting']['cpu']+.05
    c=m.run(dict(synthetic='crash'));assert c['reason']=='abnormal_parent_exit'
    d=m.run(dict(synthetic='busy',cpu=10.),cpu=.8);assert d['reason']=='cpu_limit'
    e=m.run(dict(synthetic='sleep'),wall=.7);assert e['reason']=='wall_limit'
    n=Measurement(out/'cumulative',total=1.4,wall=30.)
    for _ in range(3):
        row=n.run(dict(synthetic='busy',cpu=.65))
        if row['reason']=='g9_cpu_limit':break
    assert row['reason']=='g9_cpu_limit'
    count=len(n.rows)
    try:n.run(dict(synthetic='busy'))
    except RuntimeError:pass
    else:raise AssertionError('Exhausted budget accepted')
    assert len(n.rows)==count
    w=Measurement(out/'deadline',total=4.,wall=6.5)
    row=w.run(dict(synthetic='sleep'));assert row['reason']=='wall_limit'
    rows=m.rows+n.rows+w.rows
    for row in rows:assert row['cleanup_passed'] and row['final_accounting']['ActiveProcesses']==0
    result=dict(passed=True,jobs=len(rows),job_cpu=m.budget.used+n.budget.used+w.budget.used,
        wall=time.perf_counter()-start,production_budget_consumed=0)
    assert result['jobs']<=10 and result['job_cpu']<=20 and result['wall']<=120
    save_new(out/'result.json',result);return result

def core_run(attempt,deadline):
    attempt=Path(attempt);inputs=json.loads((attempt/'fixtures/inputs.json').read_text())
    prefix=[r for r in inputs if r['trial']==0];remaining=[r for r in inputs if r['trial']!=0]
    batches=[prefix]+[remaining[i:i+8] for i in range(0,len(remaining),8)]
    assert len(batches)==72 and len(inputs)==576
    m=Measurement(attempt/'core');m.deadline=deadline;records=[];start=time.perf_counter()
    try:
        for batch_id,batch in enumerate(batches):
            raw=m.run(dict(tasks=batch));folder=Path(raw['folder'])
            for task in batch:
                stem=f"A{task['case']:02d}_{task['trial']:02d}"
                path=folder/(stem+'.json');sha=folder/(stem+'.sha256.json')
                if not path.exists() or not sha.exists():continue
                blob=path.read_bytes()
                assert hashlib.sha256(blob).hexdigest()==json.loads(sha.read_text())['sha256']
                record=json.loads(blob);assert record['input_sha256']==task['input_sha256']
                records.append(record)
            if raw['reason']!='completed':raise RuntimeError('resource_or_worker_blocked:'+raw['reason'])
            assert all(any(r['case']==t['case'] and r['trial']==t['trial'] for r in records) for t in batch)
            if batch_id==0:
                c0=raw['final_accounting']['cpu'];ci=[r['internal_cpu'] for r in records];h=c0-sum(ci)
                forecast=c0+1.2*(63*sum(ci)+71*h)
                save_new(attempt/'prefix_admission.json',dict(C0=c0,ci=ci,H=h,delta_H=max(.05,.05*c0),C_admit=forecast,admitted=h>=0 and forecast<=300))
                if h<0 or forecast>300:raise RuntimeError('resource_prefix_blocked')
        assert len(records)==576 and len(m.rows)==72 and m.budget.used<300 and time.perf_counter()<deadline
        status=dict(passed=True,estimates=576,starts=5184,jobs=72,job_cpu=m.budget.used,wall=time.perf_counter()-start)
    except Exception as error:
        status=dict(passed=False,error=repr(error),completed=len(records),jobs=len(m.rows),job_cpu=m.budget.used,wall=time.perf_counter()-start)
    save_new(attempt/'core_result.json',status)
    if not status['passed']:raise RuntimeError(status)
