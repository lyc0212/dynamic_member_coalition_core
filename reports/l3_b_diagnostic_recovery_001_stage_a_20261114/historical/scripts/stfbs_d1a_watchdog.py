"""Single-attempt external H1 watchdog; production wall limit is always 900s."""
import argparse,subprocess,sys,os,time,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.non_oracle.stfbs_d1a_watchdog_support import WindowsJob
import psutil

def supervise(command,evidence_dir,*,wall_limit=900,cpu_limit=600,cwd=None,approval_path=None):
    out=Path(evidence_dir);out.mkdir(exist_ok=False)
    start=time.monotonic();record=dict(status='STARTING',watchdog_pid=os.getpid(),start_utc=time.time(),command=command,wall_limit=wall_limit,cpu_limit=cpu_limit,attempts=1,production_launch=approval_path is not None,cpu_complete=False,process_cpu_seconds=None,tree_cpu_seconds=None,cpu_missing_reason='not yet measured')
    process=None;job=None
    try:
        job=WindowsJob()
        with (out/'stdout.bin').open('xb') as stdout,(out/'stderr.bin').open('xb') as stderr:
            process=subprocess.Popen(command,cwd=cwd,stdout=stdout,stderr=stderr,creationflags=0x00000004)  # CREATE_SUSPENDED, not exported by subprocess.
            record['child_pid']=process.pid
            job.assign(process);record['assigned_before_resume']=True
            ticket=dict(watchdog_pid=os.getpid(),child_pid=process.pid,wall_limit=wall_limit,assigned_before_resume=True,approval_sha256=hashlib.sha256(Path(approval_path).read_bytes()).hexdigest() if approval_path else None)
            (out/'LAUNCH.json').write_text(json.dumps(ticket,indent=2),encoding='utf-8')
            psutil.Process(process.pid).resume()
            while process.poll() is None:
                if time.monotonic()-start>=wall_limit:
                    record['status']='TIMED_OUT';job.terminate();break
                if job.accounting()['tree_cpu_seconds']>cpu_limit:
                    record['status']='CPU_LIMIT';job.terminate();break
                time.sleep(.01)
            process.wait(timeout=5)
            if record['status']=='STARTING':record['status']='EXITED' if process.returncode==0 else 'ABNORMAL_EXIT'
            # Drain/terminate any descendants left behind by the primary process.
            if job.accounting()['active_processes']:
                record['descendant_cleanup']=True;job.terminate()
            until=time.monotonic()+5
            while job.accounting()['active_processes'] and time.monotonic()<until:time.sleep(.01)
            record.update(job.accounting());record['process_cpu_seconds']=job.process_cpu(process)
            record['descendant_cpu_seconds']=record['tree_cpu_seconds']-record['process_cpu_seconds']
            record['cpu_scope']='Retained primary-process handle + Windows Job total for all assigned descendants; child created suspended and assigned before resume'
            record['cpu_complete']=record['active_processes']==0
            record['cpu_missing_reason']=None if record['cpu_complete'] else 'Job still has active processes'
            record['exit_code']=process.returncode
    except Exception as e:
        record.update(status='PROTECTION_ERROR',error=repr(e),cpu_complete=False,cpu_missing_reason='Protection/accounting exception: '+repr(e))
        if process and process.poll() is None:
            try:
                if job:job.terminate()
                process.kill();process.wait(timeout=5)
            except Exception as stop:record['cleanup_error']=repr(stop)
    finally:
        record.update(end_utc=time.time(),wall_seconds=time.monotonic()-start)
        if job:job.close()
        (out/'WATCHDOG_RECEIPT.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    return record

def main(argv=None):
    parser=argparse.ArgumentParser(description='Explicit approval required; one frozen H1, no retry')
    parser.add_argument('--execute-frozen-h1',action='store_true');parser.add_argument('--approval-manifest');parser.add_argument('--output-dir');parser.add_argument('--evidence-dir',required=True)
    args=parser.parse_args(argv)
    from scripts.stfbs_d1a_run import authorize,ROOT
    output,_=authorize(args)  # Source/worktree/approval preflight before any child/output.
    approval=json.loads(Path(args.approval_manifest).read_bytes())
    evidence=Path(args.evidence_dir).resolve()
    if evidence!=Path(approval.get('watchdog_evidence_dir','')).resolve() or evidence.exists() or evidence.parent!=output.parent or evidence.name!=output.name+'_watchdog':raise ValueError('Watchdog evidence path mismatch/conflict; use a new sibling <output>_watchdog')
    command=[sys.executable,'-I','-B',str(ROOT/'scripts/stfbs_d1a_run.py'),'--execute-frozen-h1','--approval-manifest',str(Path(args.approval_manifest).resolve()),'--output-dir',str(Path(args.output_dir).resolve()),'--watchdog-ticket',str(evidence/'LAUNCH.json')]
    receipt=supervise(command,evidence,wall_limit=900,cpu_limit=600,cwd=ROOT,approval_path=args.approval_manifest)
    return 0 if receipt['status']=='EXITED' and receipt.get('cpu_complete') else 1

if __name__=='__main__':raise SystemExit(main())
