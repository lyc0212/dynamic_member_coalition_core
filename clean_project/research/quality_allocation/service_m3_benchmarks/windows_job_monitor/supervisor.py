"""Job lifecycle, live dual ledgers and append-only accounting. No M3 imports."""
import json
import os
from pathlib import Path
import time
import uuid
from .api import API


def save_new(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False)


class Budget:
    def __init__(self,limit):self.limit=limit;self.rows=()
    @property
    def used(self):return sum(r[1] for r in self.rows)
    def exhausted(self,current=0.):return self.used+current>=self.limit
    def charge(self,ident,cpu):
        if cpu<0 or any(r[0]==ident for r in self.rows):raise ValueError('Invalid or duplicate final charge')
        self.rows+=((ident,cpu),)


class GateSupervisor:
    def __init__(self,out,api=None):
        self.out=Path(out);self.out.mkdir(parents=True,exist_ok=False)
        self.api=api or API();self.budget=Budget(25.);self.attempts=0;self.results=[]
        self.wall_start=time.perf_counter();self.cpu_start=time.process_time()
        self.journal=(self.out/'job_creation_ledger.jsonl').open('x',encoding='utf-8')

    def event(self,value):self.journal.write(json.dumps(value,ensure_ascii=False)+'\n');self.journal.flush()

    def guard(self,current=0.):
        if time.perf_counter()-self.wall_start>=180:return 'gate_wall_limit'
        if time.process_time()-self.cpu_start>=10:return 'supervisor_cpu_limit'
        if self.budget.exhausted(current):return 'gate_cpu_limit'
        return None

    def run(self,label,exe,load,*,mode='busy',cpu=.45,cpu_limit=4.,wall_limit=15.,g9=None,fault=None):
        refusal=self.guard() or ('g9_cpu_limit' if g9 and g9.exhausted() else None)
        if refusal:
            self.event(dict(event='request_rejected_before_create',label=label,reason=refusal,attempts=self.attempts))
            return dict(label=label,reason=refusal,rejected_before_create=True,created=False)
        if self.attempts>=13:raise RuntimeError('13 Job creation attempts exhausted')
        self.attempts+=1; ident=uuid.uuid4().hex; folder=self.out/ident;folder.mkdir()
        name='Local\\M3CpuGate_'+ident
        row=dict(label=label,uuid=ident,job_name=name,supervisor_pid=os.getpid(),folder=str(folder),
            mode=mode,requested_cpu=cpu,cpu_limit=cpu_limit,wall_limit=wall_limit,
            created=False,samples=[],reason=None,api_error=None,handles_closed=False,cleanup_passed=False)
        self.event(dict(event='job_create_attempt',label=label,uuid=ident,attempt=self.attempts))
        start=time.perf_counter();job=None;pi=None;final=None;seen=set();closed_start=len(self.api.closed)
        try:
            job=self.api.job(name);row['created']=True
            if self.api.member(self.api.k.GetCurrentProcess(),job):raise RuntimeError('Supervisor inside tested Job')
            row['supervisor_outside_job']=True
            argv=[str(exe),'-B',str(load),'--out',str(folder),'--job',name,'--mode',mode,'--cpu',str(cpu)]
            if fault=='create':argv[0]=str(folder/'nonexistent_interpreter.exe')
            row['argv']=argv
            env=dict(os.environ)
            # Base interpreter does not use the venv-specific startup audit shim.
            if Path(exe).parent.name.lower()!='scripts':env['PYTHONPATH']=str(Path.cwd())
            pi=self.api.create(job,argv,Path.cwd(),env,folder/'stdout_stderr.log')
            row['launcher_pid']=int(pi.dwProcessId);seen.add(int(pi.dwProcessId))
            row['launcher_member']=self.api.member(pi.hProcess,job)
            if not row['launcher_member']:raise RuntimeError('Launcher not associated at creation')
            if fault=='associated':row['reason']='injected_after_association';raise InterruptedError('Injected before ResumeThread')
            self.api.resume(pi.hThread);self.api.close(pi.hThread);pi.hThread=None
            previous=0.
            while True:
                a=self.api.accounting(job);pids=self.api.pids(job);seen.update(pids)
                elapsed=time.perf_counter()-start
                if a['cpu']<previous:raise RuntimeError('Nonmonotonic Job CPU')
                previous=a['cpu']
                row['samples'].append(dict(wall=elapsed,accounting=a,pids=pids,
                    gate_cpu=self.budget.used+a['cpu'],g9_cpu=g9.used+a['cpu'] if g9 else None))
                code=self.api.exit_code(pi.hProcess)
                reason=self.guard(a['cpu'])
                if not reason and g9 and g9.exhausted(a['cpu']):reason='g9_cpu_limit'
                if not reason and a['cpu']>=cpu_limit:reason='cpu_limit'
                if not reason and elapsed>=wall_limit:reason='wall_limit'
                if not reason and code not in (0,259):reason='abnormal_parent_exit'
                if reason:
                    row.update(reason=reason,trigger_cpu=a['cpu'],trigger_wall=elapsed,trigger_exit_code=code)
                    break
                if a['ActiveProcesses']==0:
                    row['reason']='completed';break
                time.sleep(.05)
        except Exception as e:
            row['api_error']=dict(type=type(e).__name__,message=str(e),win32_code=getattr(e,'errno',None))
            if row['reason'] is None:row['reason']='injected_create_failure' if fault=='create' and isinstance(e,OSError) and e.errno in (2,3) else 'api_failure'
        finally:
            try:
                if job:
                    terminate_start=time.perf_counter()
                    current=self.api.accounting(job)
                    if current['ActiveProcesses']:
                        row['termination_requested']=True;self.api.terminate(job)
                    else:row['termination_requested']=False
                    deadline=time.perf_counter()+5.
                    while True:
                        final=self.api.accounting(job)
                        if final['ActiveProcesses']==0:break
                        if time.perf_counter()>=deadline:raise RuntimeError('Job members did not exit within cleanup deadline')
                        time.sleep(.01)
                    row['termination_seconds']=time.perf_counter()-terminate_start
                    row['final_accounting']=final
                    if row['samples'] and final['cpu']<row['samples'][-1]['accounting']['cpu']:
                        raise RuntimeError('Final Job CPU decreased')
                    if pi:row['launcher_exit_code']=self.api.exit_code(pi.hProcess)
                    row['seen_pids']=sorted(seen)
                    # ActiveProcesses=0 is the authoritative group-wide check;
                    # also verify retained identities observed during this call.
                    residual=[]
                    for pid in sorted(seen):
                        handle=self.api.k.OpenProcess(0x100000,False,pid)
                        if not handle:
                            import ctypes
                            error=ctypes.get_last_error()
                            if error!=87:raise OSError(error,'OpenProcess cleanup check')
                        else:
                            try:
                                # Job active count may reach zero slightly before
                                # the kernel process object becomes signaled.
                                remaining=max(0,int((deadline-time.perf_counter())*1000))
                                if self.api.k.WaitForSingleObject(handle,remaining)!=0:residual.append(pid)
                            finally:self.api.close(handle)
                    row['residual_pids']=residual
                    if residual:raise RuntimeError('Residual test PIDs')
                    row['termination_seconds']=time.perf_counter()-terminate_start
                    self.budget.charge(ident,final['cpu'])
                    if g9:g9.charge(ident,final['cpu'])
                    self.event(dict(event='final_cpu_charge',uuid=ident,cpu=final['cpu'],gate_used=self.budget.used,
                                    g9_used=g9.used if g9 else None,active=final['ActiveProcesses']))
                    row['final_charge_before_job_close']=True
                    row['cleanup_passed']=True
            except Exception as e:
                row['cleanup_error']=repr(e);row['cleanup_passed']=False
            finally:
                for handle in ([pi.hThread,pi.hProcess] if pi else []):
                    if handle:self.api.close(handle)
                if job:self.api.close(job)
                row['handles_closed']=True;row['closed_handle_values']=self.api.closed[closed_start:]
                row['wall']=time.perf_counter()-start
                if final:
                    row['cpu_overshoot']=max(0.,final['cpu']-cpu_limit)
                    row['wall_overshoot']=max(0.,row['wall']-wall_limit) if row['reason']=='wall_limit' else 0.
                    row['cpu_after_trigger']=final['cpu']-row.get('trigger_cpu',final['cpu'])
                self.results.append(row);save_new(folder/'result.json',row)
        if not row['cleanup_passed']:raise RuntimeError('Job cleanup failed: '+str(row))
        return row

    def close(self):self.journal.close()
