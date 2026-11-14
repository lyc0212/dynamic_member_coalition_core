"""Thin adapter. Job lifecycle/termination/accounting remain in the certified core."""
import json
from pathlib import Path
import sys
import time
from .windows_job_monitor.supervisor import GateSupervisor,Budget,save_new


class JobPilotSupervisor:
    def __init__(self,out,total_limit=600.,cpu_limit=15.,wall_limit=60.,max_calls=260):
        self.out=Path(out);self.out.mkdir(parents=True,exist_ok=False)
        self.budget=Budget(total_limit);self.cpu_limit=cpu_limit;self.wall_limit=wall_limit
        self.max_calls=max_calls;self.records=[]
        self.journal=(self.out/'pilot_ledger.jsonl').open('x',encoding='utf-8')

    @property
    def total(self):return self.budget.used

    def run(self,source,index,method,budget,phase,repeat,*,synthetic=None,synthetic_cpu=.2,
            cpu_limit=None,wall_limit=None,allow_expected=False):
        if self.budget.exhausted():raise RuntimeError('Shared cumulative CPU budget exhausted before Job creation')
        if len(self.records)>=self.max_calls:raise RuntimeError('Frozen Pilot call cap reached')
        folder=self.out/f'call_{len(self.records):03d}'
        req=dict(kind='synthetic' if synthetic else 'solver',source=str(Path(source).resolve()),
                 index=index,method=method,budget=budget)
        if synthetic:req.update(synthetic=synthetic,synthetic_cpu=synthetic_cpu)
        # One core instance per invocation. Its 25s facility budget is redundant
        # to the stricter 15s Pilot limit; g9 is the SAME shared 600s live ledger.
        core=GateSupervisor(folder)
        try:
            raw=core.run(phase+'_'+str(index)+'_'+method,sys.executable,
                Path(__file__).with_name('resume_worker.py'),mode=json.dumps(req,sort_keys=True),cpu=0.,
                cpu_limit=self.cpu_limit if cpu_limit is None else cpu_limit,
                wall_limit=self.wall_limit if wall_limit is None else wall_limit,g9=self.budget)
        finally:core.close()
        record=dict(index=index,method=method,budget=budget,phase=phase,repeat=repeat,
            completed=raw.get('reason')=='completed',job_uuid=raw.get('uuid'),job_result=raw,
            worker_lifetime_cpu=raw.get('final_accounting',{}).get('cpu'),
            worker_wall=raw.get('wall'),total_worker_cpu=self.total,
            stop_reason='aggregate_cpu_limit' if raw.get('reason')=='g9_cpu_limit' else raw.get('reason'))
        result_file=Path(raw['folder'])/'solver_result.json'
        if record['completed']:
            result=json.loads(result_file.read_text(encoding='utf-8'))
            memberships=[json.loads(p.read_text(encoding='utf-8')) for p in Path(raw['folder']).glob('membership_*.json')]
            assert memberships and all(m['member'] for m in memberships)
            assert any(m['pid']==result['worker_pid'] for m in memberships)
            assert raw['final_accounting']['ActiveProcesses']==0 and raw['handles_closed'] and raw['cleanup_passed']
            assert result['solve_cpu_ns']/1e9<=record['worker_lifetime_cpu']+.05
            assert all(v['currsize']==0 for v in result['cold_caches'].values())
            record.update(result=result,membership=memberships,cpu_monitor_valid=True)
        self.records.append(record)
        self.journal.write(json.dumps(record,ensure_ascii=False)+'\n');self.journal.flush()
        if not record['completed'] and not allow_expected:raise RuntimeError('Pilot Job failed: '+str(record))
        return record

    def close(self):self.journal.close()


def integration_gate(out,source):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    definition=dict(max_jobs=8,job_total_cpu=20.,wall_limit=120.,supervisor_cpu=10.,poll=.05,
        cases=['parallel','timing','crash','cpu_limit','wall_limit','cumulative_up_to_3','reject_before_create'],
        single_cpu=4.,single_wall=15.,cpu_trigger=1.5,wall_trigger=1.,cumulative_limit=2.2,
        cpu_overshoot_max=.25,wall_overshoot_max=.2)
    save_new(out/'frozen_inputs.json',definition)
    sup=JobPilotSupervisor(out/'workers',total_limit=20.,cpu_limit=4.,wall_limit=15.,max_calls=8)
    wall=time.perf_counter();cpu=time.process_time();tests=[];audit_cpu=0.
    try:
        def run(name,**kw):
            if time.perf_counter()-wall>120 or time.process_time()-cpu>10:raise RuntimeError('R2 supervisory quota')
            return sup.run(source,0,'R2_SYNTHETIC',None,'R2_'+name,0,**kw)
        a=run('A',synthetic='parallel');assert len(a['membership'])==3;tests.append('A')
        b=run('B',synthetic='busy');assert b['worker_lifetime_cpu']>b['result']['solve_cpu_ns']/1e9
        before=time.process_time()
        while time.process_time()-before<.10:pass
        audit_cpu=time.process_time()-before;tests.append('B')
        c=run('C',synthetic='crash',allow_expected=True);assert c['stop_reason']=='abnormal_parent_exit';tests.append('C')
        d=run('D_cpu',synthetic='busy',synthetic_cpu=10.,cpu_limit=1.5,allow_expected=True)
        assert d['stop_reason']=='cpu_limit' and d['job_result']['cpu_overshoot']<=.25
        d=run('D_wall',synthetic='sleep',wall_limit=1.,allow_expected=True)
        assert d['stop_reason']=='wall_limit' and d['job_result']['wall_overshoot']<=.2;tests.append('D')
        # Use a fresh shared synthetic budget for E, never the Pilot 600s ledger.
        cumulative=JobPilotSupervisor(out/'cumulative',total_limit=2.2,cpu_limit=4.,wall_limit=15.,max_calls=3)
        try:
            for _ in range(3):
                row=cumulative.run(source,0,'R2_SYNTHETIC',None,'R2_E',0,synthetic='busy',synthetic_cpu=.8,allow_expected=True)
                if cumulative.budget.exhausted():break
            assert cumulative.budget.exhausted() and row['stop_reason']=='aggregate_cpu_limit'
            n=len(cumulative.records)
            try:cumulative.run(source,0,'R2_SYNTHETIC',None,'R2_E_refusal',0,synthetic='busy')
            except RuntimeError:pass
            else:raise AssertionError('R2 exhausted budget accepted')
            assert len(cumulative.records)==n
            tests.append('E')
        finally:cumulative.close()
        allrows=sup.records+cumulative.records
        for r in allrows:assert r['job_result']['cleanup_passed'] and r['job_result']['final_accounting']['ActiveProcesses']==0
        assert len(allrows)<=8 and sup.total+cumulative.total<=20.
        result=dict(passed=True,tests=tests,jobs=len(allrows),job_cpu=sup.total+cumulative.total,
            supervisor_cpu=time.process_time()-cpu,wall=time.perf_counter()-wall,external_audit_cpu=audit_cpu,
            pilot_quota_consumed=0,cumulative_rows=cumulative.budget.rows)
        assert result['supervisor_cpu']<=10 and result['wall']<=120
        save_new(out/'result.json',result);return result
    finally:sup.close()
