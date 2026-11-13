import time
BOOT_WALL=time.monotonic()
BOOT_CPU=time.process_time()
import pathlib,sys,runpy,json,traceback
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
try:
 runpy.run_path(str(ROOT/'run_task_impl.py'),run_name='__main__',init_globals={'FORMAL_START':BOOT_WALL})
except BaseException as exc:
 record=dict(task_id='STFBS_LITE_LOCAL_DEV_H2_H3_EXTENSION_004',continuation='EXTENSION_004_CONTINUATION_001',status='LOCAL_DEV_D60_H2_H3_VALUE_MATRIX_INCOMPLETE',phase='BOOTSTRAP_OR_UNHANDLED_CONTROLLER_FAILURE',type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),bootstrap_cpu_seconds=time.process_time()-BOOT_CPU,bootstrap_wall_seconds=time.monotonic()-BOOT_WALL,retry=False)
 with (ROOT/'BOOTSTRAP_FAILURE.json').open('x') as f:json.dump(record,f,indent=2)
 raise
