"""Use the existing WindowsSupervisor and persist cumulative phase accounting."""
import time
CPU0, WALL0 = time.process_time(), time.monotonic()
import sys, pathlib, json, hashlib
ROOT=pathlib.Path(__file__).resolve().parent
REPO=ROOT.parent.parent
sys.path.insert(0,str(REPO))
from research.non_oracle.stfbs_lite_real_d60_supervisor_win import WindowsSupervisor
phase=sys.argv[1]
p=ROOT/'CUMULATIVE_RESOURCE_ACCOUNTING.json'
prior=json.loads(p.read_bytes()) if p.exists() else dict(cpu_seconds=0,wall_seconds=0,phases=[])
cpu=180-prior['cpu_seconds']-(time.process_time()-CPU0)
wall=360-prior['wall_seconds']-(time.monotonic()-WALL0)
assert cpu>0 and wall>0
script='benchmark.py' if phase in ('baseline','optimized') else 'validate.py'
argv=[sys.executable,'-I','-S','-B',str(ROOT/script)]+([phase] if script=='benchmark.py' else [])
receipt=WindowsSupervisor(total_cpu_seconds=cpu,wall_seconds=wall,attempt_identity='SYNTHETIC_FAST_PATH_'+phase).run_monitored(argv,cwd=REPO,log=ROOT/(phase+'.log'))
(ROOT/(phase+'_supervisor_receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
prior['cpu_seconds']+=receipt['final_cpu_ticks']/1e7+time.process_time()-CPU0
prior['wall_seconds']+=time.monotonic()-WALL0
prior['phases'].append(dict(phase=phase,worker_cpu_seconds=receipt['final_cpu_ticks']/1e7,controller_cpu_seconds=time.process_time()-CPU0,worker_exit_code=receipt['worker_exit_code'],wall_seconds=time.monotonic()-WALL0))
prior['storage_bytes']=sum(f.stat().st_size for f in ROOT.rglob('*') if f.is_file())
p.write_text(json.dumps(prior,indent=2),encoding='utf-8')
print(json.dumps(prior))
assert receipt['worker_exit_code']==0 and receipt['accounting_status']=='FINAL_VALID' and receipt['process_tree_status']=='PROCESS_TREE_EXIT_CONFIRMED' and not receipt['errors']
assert prior['cpu_seconds']<=180 and prior['wall_seconds']<=360 and prior['storage_bytes']<=67108864
