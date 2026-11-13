import time
BOOT_WALL=time.monotonic()
BOOT_CPU=time.process_time()
import pathlib,sys,runpy,json,traceback,importlib
ROOT=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path(r'D:\1st\dynamic_member_coalition_core')
ENV=pathlib.Path(r'D:\miniconda3\envs\dynamic_member_coalition_core')
sys.path[:0]=[str(REPO),str(ROOT)]
try:
 if pathlib.Path(sys.executable).resolve()!=ENV/'python.exe':raise RuntimeError('FIXED_INTERPRETER_IDENTITY')
 if pathlib.Path(sys.prefix).resolve()!=ENV:raise RuntimeError('FIXED_ENVIRONMENT_PREFIX')
 site=ENV/'Lib/site-packages'
 if not site.is_dir():raise RuntimeError('SITE_PACKAGES_MISSING')
 sys.path.insert(2,str(site))
 versions={'numpy':'2.1.3','scipy':'1.15.3','psutil':'7.2.2'};modules={}
 for name,version in versions.items():
  module=importlib.import_module(name)
  if module.__version__!=version:raise RuntimeError('PACKAGE_VERSION/'+name)
  path=pathlib.Path(module.__file__).resolve()
  if not path.is_relative_to(site.resolve()):raise RuntimeError('PACKAGE_ORIGIN/'+name)
  modules[name]=dict(version=module.__version__,file=str(path))
 import research.non_oracle.stfbs_lite_actual_recovery
 import task_support,analysis
 record=dict(status='IMPORT_VERIFICATION_PASS_NOT_G0_PASS',executable=sys.executable,prefix=sys.prefix,site_packages=str(site),modules=modules,isolated_flags=['-I','-S','-B'],import_priority=sys.path[:3],cpu_seconds=time.process_time()-BOOT_CPU,wall_seconds=time.monotonic()-BOOT_WALL)
 with (ROOT/'ENTRY_IMPORT_VERIFICATION.json').open('x') as f:json.dump(record,f,indent=2)
 runpy.run_path(str(ROOT/'run_task_impl.py'),run_name='__main__',init_globals={'FORMAL_START':BOOT_WALL})
except BaseException as exc:
 record=dict(task_id='STFBS_LITE_ACTUAL_COUNTERFACTUAL_001',continuation_id='STFBS_LITE_ACTUAL_COUNTERFACTUAL_001_CONTINUATION_001',status='LOCAL_DEV_ACTUAL_THREE_ACTION_COUNTERFACTUAL_INCOMPLETE',G0_STATUS='FAILED_BEFORE_RECOVERY',phase='BOOTSTRAP_OR_UNHANDLED_CONTROLLER_FAILURE',type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),bootstrap_cpu_seconds=time.process_time()-BOOT_CPU,bootstrap_wall_seconds=time.monotonic()-BOOT_WALL,retry=False)
 with (ROOT/'BOOTSTRAP_FAILURE.json').open('x') as f:json.dump(record,f,indent=2)
 raise
