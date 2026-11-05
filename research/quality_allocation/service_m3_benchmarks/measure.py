"""Single worker timing; parent retains Windows process handle through termination."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from .fixtures import restore, save
from .variants import solve
from pursuit_v2.types import Target


def clear_caches():
    result={}
    for name in ('_arc_segments','escape_time'):
        fn=getattr(Target,name); fn.cache_clear(); result[name]=fn.cache_info()._asdict()
        assert result[name]['currsize']==0
    return result


def worker(source, index, method, budget, output):
    raw=json.loads(Path(source).read_text(encoding='utf-8'))[index]['observation']
    # Rehydration before timer is only transport; public validation/Case/worlds remain inside.
    obs=restore(raw)
    cache=clear_caches()
    start_cpu=time.process_time_ns(); start_wall=time.perf_counter_ns()
    result=solve(obs,method,budget)
    cpu=time.process_time_ns()-start_cpu; wall=time.perf_counter_ns()-start_wall
    # Detailed table/history not serialized in the measured solver interval.
    slim={k:v for k,v in result.items() if k not in ('bounds','bound_details','history','known')}
    for k in ('L','U'): slim[k]=str(slim[k])
    slim.update(solve_cpu_ns=cpu,solve_wall_ns=wall,cold_caches=cache,worker_pid=os.getpid(),
                certified_gap=str(result['U']-result['L']))
    save(output,slim)


def process_cpu(handle):
    if os.name!='nt': raise RuntimeError('Pilot watchdog requires verified Windows CPU monitoring')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    fn=kernel.GetProcessTimes
    fn.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4
    fn.restype=wintypes.BOOL
    creation,exit_,system,user=[wintypes.FILETIME() for _ in range(4)]
    if not fn(int(handle),ctypes.byref(creation),ctypes.byref(exit_),ctypes.byref(system),ctypes.byref(user)):
        raise ctypes.WinError(ctypes.get_last_error())
    ticks=lambda x:(x.dwHighDateTime<<32)+x.dwLowDateTime
    return (ticks(system)+ticks(user))/1e7


class Supervisor:
    def __init__(self,out,total_limit=600.,cpu_limit=15.,wall_limit=60.):
        self.out=Path(out); self.out.mkdir(parents=True,exist_ok=True)
        self.total=0.; self.total_limit=total_limit; self.cpu_limit=cpu_limit; self.wall_limit=wall_limit
        self.records=[]

    def run(self,source,index,method,budget,phase,repeat):
        if self.total>=self.total_limit: raise RuntimeError('Aggregate worker CPU exhausted')
        ident=uuid.uuid4().hex; output=self.out/(ident+'.json')
        cmd=[sys.executable,'-B','-m',__name__,'--worker',str(source),str(index),method,
             'None' if budget is None else str(budget),str(output)]
        env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
                 NUMEXPR_NUM_THREADS='1',PYTHONHASHSEED='0',PYTHONIOENCODING='utf-8',
                 M3_SERVICE_AUDIT_ROOT=str(self.out/'audit_root'))
        # This worker does not spawn children. /T also kills descendants if that contract regresses.
        start=time.perf_counter(); cpu=0.; reason=None
        with (self.out/(ident+'.log')).open('w',encoding='utf-8') as log:
            child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
            try:
                while True:
                    cpu=process_cpu(child._handle)
                    elapsed=time.perf_counter()-start
                    if cpu>=self.cpu_limit: reason='cpu_limit'
                    elif self.total+cpu>=self.total_limit: reason='aggregate_cpu_limit'
                    elif elapsed>=self.wall_limit: reason='wall_limit'
                    if reason:
                        subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True)
                        child.wait(timeout=10); break
                    if child.poll() is not None: break
                    time.sleep(.01)
            except BaseException:
                subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True)
                child.wait(timeout=10)
                raise
            finally:
                cpu=process_cpu(child._handle); self.total+=cpu
        record=dict(id=ident,argv=cmd,index=index,method=method,budget=budget,phase=phase,repeat=repeat,
            launched_pid=child.pid,
            exit_code=child.returncode,worker_lifetime_cpu=cpu,worker_wall=time.perf_counter()-start,
            total_worker_cpu=self.total,stop_reason=reason,cpu_overshoot=max(0.,cpu-self.cpu_limit),
            aggregate_overshoot=max(0.,self.total-self.total_limit),completed=reason is None and child.returncode==0)
        if record['completed']:
            record['result']=json.loads(output.read_text(encoding='utf-8'))
            reported=record['result']
            # A Windows venv redirector can launch a second interpreter. Root CPU
            # then excludes the actual solver. Never extrapolate or start a pilot
            # on that measurement. Process-tree supervision requires a new gate.
            if reported['worker_pid']!=child.pid:
                record.update(completed=False,stop_reason='cpu_monitor_process_mismatch',
                              cpu_monitor_valid=False,observed_launcher_cpu=cpu,
                              worker_lifetime_cpu=None,total_worker_cpu=None)
            elif reported['solve_cpu_ns']/1e9>cpu+.02:
                record.update(completed=False,stop_reason='cpu_monitor_underreported',
                              cpu_monitor_valid=False,observed_launcher_cpu=cpu,
                              worker_lifetime_cpu=None,total_worker_cpu=None)
            else: record['cpu_monitor_valid']=True
        self.records.append(record); save(self.out/'ledger.json',self.records)
        if not record['completed']: raise RuntimeError('Worker did not complete: '+json.dumps(record))
        return record


if __name__=='__main__':
    if sys.argv[1]!='--worker': raise SystemExit('Worker entry only')
    worker(sys.argv[2],int(sys.argv[3]),sys.argv[4],None if sys.argv[5]=='None' else int(sys.argv[5]),sys.argv[6])
