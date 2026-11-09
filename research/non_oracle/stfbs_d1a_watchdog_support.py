"""Windows job accounting and minimal live watchdog launch binding."""
import ctypes,hashlib,json,os,time,sys,math
from ctypes import wintypes as W
from pathlib import Path
import psutil

class Accounting(ctypes.Structure):
    _fields_=[('TotalUserTime',ctypes.c_longlong),('TotalKernelTime',ctypes.c_longlong),('ThisPeriodTotalUserTime',ctypes.c_longlong),('ThisPeriodTotalKernelTime',ctypes.c_longlong),('TotalPageFaultCount',W.DWORD),('TotalProcesses',W.DWORD),('ActiveProcesses',W.DWORD),('TotalTerminatedProcesses',W.DWORD)]

class BasicLimits(ctypes.Structure):
    _fields_=[('process_time',ctypes.c_longlong),('job_time',ctypes.c_longlong),('flags',W.DWORD),('min_working',ctypes.c_size_t),('max_working',ctypes.c_size_t),('active_limit',W.DWORD),('affinity',ctypes.c_size_t),('priority',W.DWORD),('scheduling',W.DWORD)]

class ExtendedLimits(ctypes.Structure):
    _fields_=[('basic',BasicLimits),('io',ctypes.c_ulonglong*6),('process_memory',ctypes.c_size_t),('job_memory',ctypes.c_size_t),('peak_process_memory',ctypes.c_size_t),('peak_job_memory',ctypes.c_size_t)]

class WindowsJob:
    def __init__(self):
        if os.name!='nt':raise RuntimeError('Windows job accounting required')
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        signatures={'CreateJobObjectW':([ctypes.c_void_p,W.LPCWSTR],W.HANDLE),'AssignProcessToJobObject':([W.HANDLE,W.HANDLE],W.BOOL),'QueryInformationJobObject':([W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD,ctypes.c_void_p],W.BOOL),'TerminateJobObject':([W.HANDLE,W.UINT],W.BOOL),'CloseHandle':([W.HANDLE],W.BOOL),'GetProcessTimes':([W.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p],W.BOOL)}
        for name,(args,ret) in signatures.items():
            f=getattr(self.api,name);f.argtypes=args;f.restype=ret
        self.handle=self.api.CreateJobObjectW(None,None)
        if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
        setter=self.api.SetInformationJobObject;setter.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD];setter.restype=W.BOOL
        limits=ExtendedLimits();limits.basic.flags=0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not setter(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)):
            error=ctypes.get_last_error();self.close();raise ctypes.WinError(error)
    def assign(self,process):
        if not self.api.AssignProcessToJobObject(self.handle,int(process._handle)):raise ctypes.WinError(ctypes.get_last_error())
    def accounting(self):
        a=Accounting()
        if not self.api.QueryInformationJobObject(self.handle,1,ctypes.byref(a),ctypes.sizeof(a),None):raise ctypes.WinError(ctypes.get_last_error())
        return dict(tree_cpu_seconds=(a.TotalUserTime+a.TotalKernelTime)/1e7,total_processes=a.TotalProcesses,active_processes=a.ActiveProcesses,terminated_processes=a.TotalTerminatedProcesses)
    def process_cpu(self,process):
        fields=[ctypes.c_ulonglong() for _ in range(4)]
        if not self.api.GetProcessTimes(int(process._handle),*(ctypes.byref(f) for f in fields)):raise ctypes.WinError(ctypes.get_last_error())
        return (fields[2].value+fields[3].value)/1e7
    def terminate(self):
        if not self.api.TerminateJobObject(self.handle,124):raise ctypes.WinError(ctypes.get_last_error())
    def close(self):self.api.CloseHandle(self.handle)

def require_watchdog(ticket,approval_path):
    if not ticket:raise ValueError('External watchdog launch required')
    if not sys.flags.isolated:raise ValueError('Watchdog child must use isolated Python (-I)')
    record=json.loads(Path(ticket).read_bytes())
    parent=psutil.Process(os.getppid())
    expected=(Path(__file__).resolve().parents[2]/'scripts/stfbs_d1a_watchdog.py').resolve()
    if record.get('watchdog_pid')!=parent.pid or record.get('child_pid')!=os.getpid() or record.get('wall_limit')!=900 or record.get('assigned_before_resume') is not True:
        raise ValueError('Invalid watchdog launch binding')
    if str(expected).lower() not in [str(Path(a).resolve()).lower() for a in parent.cmdline() if a.endswith('.py')]:raise ValueError('Unexpected watchdog parent')
    if record.get('approval_sha256')!=hashlib.sha256(Path(approval_path).read_bytes()).hexdigest():raise ValueError('Watchdog approval mismatch')
    return record

def verify_watchdog_receipt(record):
    if record.get('wall_limit')!=900 or record.get('production_launch') is not True:
        raise ValueError('Not a formal 900-second watchdog receipt')
    if record.get('status')!='EXITED' or record.get('exit_code')!=0 or record.get('wall_seconds',901)>900:
        raise ValueError('Watchdog execution not successful')
    for field in ('tree_cpu_seconds','process_cpu_seconds'):
        value=record.get(field)
        if type(value) not in (int,float) or not math.isfinite(value) or value<0:raise ValueError('Missing/invalid CPU measurement: '+field)
    if not record.get('cpu_complete') or record['tree_cpu_seconds']>600 or record.get('active_processes')!=0:
        raise ValueError('Incomplete or excessive watchdog CPU accounting')
    if not record.get('assigned_before_resume') or not record.get('child_pid'):raise ValueError('Missing watchdog lifecycle proof')
    return {'status':'PASS','scope':'resource evidence only; not automatic G5/science acceptance'}
