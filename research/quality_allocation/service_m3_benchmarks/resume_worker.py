"""Pilot worker entry: unchanged measure.worker, plus isolated R2 synthetic injection."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API
from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.supervisor import save_new


def busy(seconds):
    start=time.process_time();value=1
    while time.process_time()-start<seconds:value=(value*1664525+1013904223)&0xffffffff
    return time.process_time()-start


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--job',required=True)
    p.add_argument('--mode',required=True);p.add_argument('--cpu');args=p.parse_args()
    out=Path(args.out);req=json.loads(args.mode);api=API()
    try:
        import sitecustomize
        if hasattr(sitecustomize,'_root'):
            audit=out/('audit_'+str(os.getpid()));(audit/'evidence/runtime_access').mkdir(parents=True)
            sitecustomize._root=str(audit)
    except ImportError:pass
    h=api.check(api.k.OpenJobObjectW(4,False,args.job),'OpenJobObjectW')
    try:member=api.member(api.k.GetCurrentProcess(),h)
    finally:api.close(h)
    if not member:raise RuntimeError('Pilot interpreter outside named Job')
    save_new(out/f'membership_{os.getpid()}.json',dict(pid=os.getpid(),ppid=os.getppid(),member=member,kind=req['kind']))
    if req['kind']=='leaf':
        cpu=busy(req['cpu']);save_new(out/f'leaf_end_{os.getpid()}.json',dict(pid=os.getpid(),cpu=cpu));return
    from research.quality_allocation.service_m3_benchmarks import measure
    children=[];relations=[]

    def child(cpu):
        payload=json.dumps(dict(kind='leaf',cpu=cpu))
        proc=subprocess.Popen([sys.executable,'-B',__file__,'--out',str(out),'--job',args.job,'--mode',payload])
        h=api.check(api.k.OpenJobObjectW(4,False,args.job),'OpenJobObjectW')
        try:included=api.member(proc._handle,h)
        finally:api.close(h)
        relations.append(dict(launcher_pid=proc.pid,parent_pid=os.getpid(),member=included));children.append(proc)
        if not included:raise RuntimeError('R2 child outside Job')
        return proc

    if req['kind']=='synthetic':
        busy(.05) # before measure.worker's unchanged solve clock
        def synthetic_solve(obs,method,budget):
            mode=req['synthetic'];start=time.process_time()
            if mode=='parallel':
                child(.10);child(.10);busy(.20)
                for c in children:
                    if c.wait()!=0:raise RuntimeError('R2 child failed')
            elif mode=='crash':
                child(10.)
                deadline=time.perf_counter()+4
                while len(list(out.glob('membership_*.json')))<2:
                    if time.perf_counter()>deadline:raise RuntimeError('R2 child not started')
                    time.sleep(.01)
                save_new(out/'abnormal_parent.json',dict(pid=os.getpid(),relations=relations));os._exit(7)
            elif mode=='sleep':time.sleep(3.)
            else:busy(req.get('synthetic_cpu',.20))
            return dict(L=Fraction(),U=Fraction(),known=[],method='R2_SYNTHETIC',exact=0,total=0,
                actions=[],accuracy_met=True,stop_reason='synthetic_completed',relations=relations,
                synthetic_segment_cpu=time.process_time()-start)
        measure.solve=synthetic_solve # isolated child-only injection; no algorithm scoring invoked
    elif req['kind']!='solver':raise ValueError('Invalid payload kind')
    measure.worker(req['source'],req['index'],req['method'],req['budget'],out/'solver_result.json')
    if req['kind']=='synthetic':busy(.05)
    save_new(out/'worker_completed.json',dict(pid=os.getpid(),member=member,relations=relations))


if __name__=='__main__':main()
