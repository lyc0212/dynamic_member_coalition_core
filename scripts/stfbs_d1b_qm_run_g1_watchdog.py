"""Future approved batch supervisor. No CLI toggle or in-policy SHA grants authority."""
import argparse,json,sys,time,hashlib
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--approval-file',required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
    from research.non_oracle.stfbs_d1b_qm_run_release import authorize_policy
    permit=authorize_policy(args.approval_file)  # Independent user root required before output/attempt creation.
    import psutil
    output=Path(permit.bindings['output_dir']);output.mkdir(exist_ok=False)
    approval_sha=hashlib.sha256(Path(args.approval_file).read_bytes()).hexdigest()
    with (output/'ATTEMPT.json').open('x',encoding='utf-8') as f:
        json.dump(dict(batch_id=permit.bindings['batch_id'],attempt_id=permit.bindings['attempt_id'],watchdog_pid=psutil.Process().pid,watchdog_create_time=psutil.Process().create_time(),approval_sha256=approval_sha,started_utc=time.time(),attempt=1,automatic_retry=False),f,indent=2)
    with (output/'APPROVAL_COPY.json').open('xb') as f:f.write(Path(args.approval_file).read_bytes())
    command=[str(Path(sys.executable).resolve()),'-I','-B',str(root/'scripts/stfbs_d1b_qm_run_g1.py'),'--approval-file',str(Path(args.approval_file).resolve()),'--launch-ticket',str(output/'WATCHDOG'/'LAUNCH.json')]
    from scripts.stfbs_d1a_watchdog import supervise
    receipt=supervise(command,output/'WATCHDOG',cpu_limit=permit.bindings['cpu_limit'],wall_limit=permit.bindings['wall_limit'],cwd=root,approval_path=Path(args.approval_file))
    from research.non_oracle.stfbs_d1b_qm_budget import inspect_journal
    ledger=inspect_journal(output/'RAW_CALLS.jsonl') if (output/'RAW_CALLS.jsonl').is_file() else dict(status='RESOURCE_LEDGER_INCOMPLETE')
    unchanged=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==wanted for name,wanted in permit.bindings['source_pins'].items())
    valid=receipt['status']=='EXITED' and receipt['exit_code']==0 and receipt['cpu_complete'] and receipt['active_processes']==0 and ledger['status']=='COMPLETE' and unchanged
    with (output/'FINAL_EXTERNAL_RESOURCE_AUDIT.json').open('x',encoding='utf-8') as f:json.dump(dict(status='PASS' if valid else 'BLOCKED',source_pins_unchanged=unchanged,receipt=receipt,journal_status=ledger['status'],no_retry=True),f,indent=2)
    return 0 if valid else 1

if __name__=='__main__':raise SystemExit(main())
