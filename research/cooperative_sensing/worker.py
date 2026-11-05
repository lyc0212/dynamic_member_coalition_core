"""Named-Job entry point; estimator receives serialized public measurements only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API
from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.supervisor import save_new

def main():
    parser=argparse.ArgumentParser()
    for name in ('out','job','mode','cpu'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args();out=Path(args.out);req=json.loads(args.mode);api=API()
    handle=api.check(api.k.OpenJobObjectW(4,False,args.job),'OpenJobObjectW')
    try:member=api.member(api.k.GetCurrentProcess(),handle)
    finally:api.close(handle)
    if not member:raise RuntimeError('Research interpreter outside named Job')
    save_new(out/'membership.json',dict(pid=os.getpid(),ppid=os.getppid(),member=member))
    if req.get('synthetic'):
        save_new(out/'synthetic_checkpoint.json',dict(completed=True))
        if req['synthetic']=='crash':os._exit(7)
        if req['synthetic']=='sleep':time.sleep(30.)
        start=time.process_time()
        while time.process_time()-start<req.get('cpu',.1):pass
        save_new(out/'synthetic_end.json',dict(internal_cpu=time.process_time()-start));return
    from research.cooperative_sensing.estimator import estimate,NumericContractViolation
    for task in req['tasks']:
        public=json.loads(json.dumps(task['input']))
        canonical=json.dumps(public,sort_keys=True,allow_nan=False,separators=(',',':')).encode()
        if hashlib.sha256(canonical).hexdigest()!=task['input_sha256']:
            raise NumericContractViolation('Public input digest changed')
        start=time.process_time()
        try:result=estimate(public)
        except NumericContractViolation as e:
            save_new(out/'numeric_contract_violation.json',dict(error=str(e),task=task));raise
        cpu=time.process_time()-start
        forbidden=[name for name in sys.modules if name.startswith('pursuit_v2') or name=='research.cooperative_sensing.fixtures']
        if forbidden:raise NumericContractViolation('Truth-side module imported: '+repr(forbidden))
        record=dict(case=task['case'],trial=task['trial'],input_sha256=task['input_sha256'],
            result=result,internal_cpu=cpu,completed=True,truth_side_imports=forbidden)
        blob=json.dumps(record,sort_keys=True,allow_nan=False).encode()
        stem=f"A{task['case']:02d}_{task['trial']:02d}"
        temp=out/(stem+'.tmp');target=out/(stem+'.json')
        if target.exists():raise FileExistsError(target)
        with temp.open('xb') as file:file.write(blob);file.flush();os.fsync(file.fileno())
        temp.rename(target)
        save_new(out/(stem+'.sha256.json'),dict(sha256=hashlib.sha256(blob).hexdigest()))

if __name__=='__main__':main()
