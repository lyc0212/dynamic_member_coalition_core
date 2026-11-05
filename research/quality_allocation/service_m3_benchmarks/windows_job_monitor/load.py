"""Frozen synthetic workloads only: busy/sleep/children/abnormal exit."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API


def save(path,value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2)


def busy(cpu):
    start=time.process_time_ns();value=1
    while (time.process_time_ns()-start)/1e9<cpu:
        value=(value*1664525+1013904223)&0xffffffff
    return (time.process_time_ns()-start)/1e9


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--job',required=True)
    p.add_argument('--mode',required=True);p.add_argument('--cpu',type=float,required=True);args=p.parse_args()
    out=Path(args.out);api=API();job=api.check(api.k.OpenJobObjectW(4,False,args.job),'OpenJobObjectW')
    # Query-only handle held while verifying identity; close before doing work.
    member=api.member(api.k.GetCurrentProcess(),job);api.close(job)
    if not member:raise RuntimeError('Synthetic interpreter outside expected Job')
    try:
        import sitecustomize
        if hasattr(sitecustomize,'_root'):
            audit=out/('audit_'+str(os.getpid()));(audit/'evidence/runtime_access').mkdir(parents=True)
            sitecustomize._root=str(audit)
    except ImportError:pass
    pid=os.getpid();save(out/f'start_{pid}.json',dict(pid=pid,ppid=os.getppid(),member=member,mode=args.mode))
    start=time.process_time_ns();children=[];relations=[];solver=0.

    def child(cpu,wait=False):
        cmd=[sys.executable,'-B',__file__,'--out',str(out),'--job',args.job,'--mode','leaf','--cpu',str(cpu)]
        proc=subprocess.Popen(cmd)
        h=api.check(api.k.OpenJobObjectW(4,False,args.job),'OpenJobObjectW')
        try:included=api.member(proc._handle,h)
        finally:api.close(h)
        relations.append(dict(parent_pid=pid,launcher_pid=proc.pid,member=included))
        if not included:raise RuntimeError('Child launcher outside Job')
        children.append(proc)
        if wait:proc.wait()
        return proc

    if args.mode in ('busy','leaf'):solver=busy(args.cpu)
    elif args.mode=='sleep':time.sleep(2.)
    elif args.mode=='parallel':
        child(.35);child(.35);solver=busy(.10)
        for proc in children:
            if proc.wait()!=0:raise RuntimeError('Synthetic child failed')
    elif args.mode=='short':
        for _ in range(3):
            if child(.25,True).returncode!=0:raise RuntimeError('Short child failed')
        solver=busy(.05)
    elif args.mode=='audit':
        busy(.10);solver=busy(.30);busy(.05)
    elif args.mode=='crash':
        proc=child(10.)
        # Ensure actual child interpreter has started before parent exits.
        until=time.perf_counter()+3.
        while len(list(out.glob('start_*.json')))<2:
            if time.perf_counter()>until:raise RuntimeError('Child startup acknowledgement timeout')
            time.sleep(.01)
        save(out/f'crash_{pid}.json',dict(pid=pid,relations=relations,expected_exit=7))
        os._exit(7)
    else:raise ValueError(args.mode)
    elapsed=(time.process_time_ns()-start)/1e9
    save(out/f'end_{pid}.json',dict(pid=pid,ppid=os.getppid(),member=member,process_internal_cpu=elapsed,
                                  solver_cpu=solver,relations=relations,completed=True))


if __name__=='__main__':main()
