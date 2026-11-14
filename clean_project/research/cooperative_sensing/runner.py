"""External wall watchdog and stage entry points. No experiment runs on import."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from .measure import core_run,integration,Measurement
from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.supervisor import save_new

def watch(attempt,action,seconds):
    attempt=Path(attempt);start=time.perf_counter();deadline=start+seconds
    argv=[sys.executable,'-B','-m','research.cooperative_sensing.runner','--action',action,'--out',str(attempt),'--deadline',str(deadline)]
    with (attempt/(action+'_controller.log')).open('xb') as log:
        process=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        triggered=False;handles=[];jobs=[];api=None;final_jobs=[]
        try:code=process.wait(timeout=max(0.,deadline-time.perf_counter()))
        except subprocess.TimeoutExpired:
            triggered=True
            from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API
            api=API()
            for file in attempt.rglob('membership.json'):
                pid=json.loads(file.read_text())['pid'];handle=api.k.OpenProcess(0x100000,False,pid)
                if handle:handles.append((pid,handle))
            # Retain query/terminate handles for final accounting after the
            # controller is stopped. Reuse the original API, not a second ABI.
            for journal in attempt.rglob('job_creation_ledger.jsonl'):
                for line in journal.read_text().splitlines():
                    event=json.loads(line)
                    if event.get('event')!='job_create_attempt':continue
                    name='Local\\M3CpuGate_'+event['uuid']
                    handle=api.k.OpenJobObjectW(4|8,False,name)
                    if handle:jobs.append((name,handle))
            process.terminate();code=process.wait(timeout=5.)
            for name,handle in jobs:
                try:
                    if api.accounting(handle)['ActiveProcesses']:api.terminate(handle)
                    cleanup_deadline=time.perf_counter()+5.
                    while api.accounting(handle)['ActiveProcesses'] and time.perf_counter()<cleanup_deadline:time.sleep(.01)
                    accounting=api.accounting(handle)
                    final_jobs.append(dict(job_name=name,accounting=accounting))
                    if accounting['ActiveProcesses']:raise RuntimeError('External watchdog cleanup failed')
                finally:api.close(handle)
        residual=[]
        if api:
            for pid,handle in handles:
                try:
                    if api.k.WaitForSingleObject(handle,5000)!=0:residual.append(pid)
                finally:api.close(handle)
        result=dict(action=action,controller_pid=process.pid,exit_code=code,
            triggered=triggered,wall=time.perf_counter()-start,deadline_seconds=seconds,
            observed_worker_handles=len(handles),residual_pids=residual,final_jobs=final_jobs)
        save_new(attempt/(action+'_watchdog.json'),result)
        return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--action',required=True)
    parser.add_argument('--out',required=True);parser.add_argument('--deadline',type=float)
    args=parser.parse_args();out=Path(args.out)
    if args.action=='integration':
        integration(out/'interface')
        probe=out/'watchdog_probe';probe.mkdir()
        result=watch(probe,'probe',3.)
        assert result['triggered'] and result['observed_worker_handles']>=1 and not result['residual_pids']
        assert result['final_jobs'] and all(j['accounting']['ActiveProcesses']==0 for j in result['final_jobs'])
        save_new(out/'K2_result.json',dict(passed=True,watchdog=result))
    elif args.action=='probe':
        m=Measurement(out/'probe_jobs',wall=60.)
        m.run(dict(synthetic='sleep'),wall=30.)
    elif args.action=='formal':
        # Absolute deadline includes controller import, every batch and bookkeeping.
        result=watch(out,'core',600.)
        if result['triggered'] or result['exit_code']!=0:raise RuntimeError('Core stopped: '+repr(result))
    elif args.action=='core':core_run(out,args.deadline)
    else:raise ValueError(args.action)

if __name__=='__main__':main()
