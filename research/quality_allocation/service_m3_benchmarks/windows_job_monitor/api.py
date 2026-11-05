"""Explicit x64 Win32 ABI; no Job is created on import."""
import ctypes as C
from ctypes import wintypes as W
import os
import subprocess

SIZE=C.c_size_t
HANDLE=W.HANDLE
DWORD=W.DWORD
LARGE=C.c_int64


class Accounting(C.Structure):
    _fields_=[('TotalUserTime',LARGE),('TotalKernelTime',LARGE),
              ('ThisPeriodTotalUserTime',LARGE),('ThisPeriodTotalKernelTime',LARGE),
              ('TotalPageFaultCount',DWORD),('TotalProcesses',DWORD),
              ('ActiveProcesses',DWORD),('TotalTerminatedProcesses',DWORD)]


class BasicLimit(C.Structure):
    _fields_=[('PerProcessUserTimeLimit',LARGE),('PerJobUserTimeLimit',LARGE),
              ('LimitFlags',DWORD),('MinimumWorkingSetSize',SIZE),('MaximumWorkingSetSize',SIZE),
              ('ActiveProcessLimit',DWORD),('Affinity',SIZE),('PriorityClass',DWORD),('SchedulingClass',DWORD)]


class IO(C.Structure):
    _fields_=[(n,C.c_uint64) for n in ('ReadOperationCount','WriteOperationCount','OtherOperationCount',
                                    'ReadTransferCount','WriteTransferCount','OtherTransferCount')]


class ExtendedLimit(C.Structure):
    _fields_=[('BasicLimitInformation',BasicLimit),('IoInfo',IO),('ProcessMemoryLimit',SIZE),
              ('JobMemoryLimit',SIZE),('PeakProcessMemoryUsed',SIZE),('PeakJobMemoryUsed',SIZE)]


class Startup(C.Structure):
    _fields_=[('cb',DWORD),('lpReserved',W.LPWSTR),('lpDesktop',W.LPWSTR),('lpTitle',W.LPWSTR)]+[
        (n,DWORD) for n in ('dwX','dwY','dwXSize','dwYSize','dwXCountChars','dwYCountChars','dwFillAttribute','dwFlags')]+[
        ('wShowWindow',W.WORD),('cbReserved2',W.WORD),('lpReserved2',C.c_void_p),
        ('hStdInput',HANDLE),('hStdOutput',HANDLE),('hStdError',HANDLE)]


class StartupEx(C.Structure):
    _fields_=[('StartupInfo',Startup),('lpAttributeList',C.c_void_p)]


class ProcessInfo(C.Structure):
    _fields_=[('hProcess',HANDLE),('hThread',HANDLE),('dwProcessId',DWORD),('dwThreadId',DWORD)]


class Security(C.Structure):
    _fields_=[('nLength',DWORD),('lpSecurityDescriptor',C.c_void_p),('bInheritHandle',W.BOOL)]


def layout():
    values={x.__name__:C.sizeof(x) for x in (Accounting,BasicLimit,ExtendedLimit,Startup,StartupEx,ProcessInfo,Security)}
    if C.sizeof(C.c_void_p)!=8 or values!=dict(Accounting=48,BasicLimit=64,ExtendedLimit=144,
            Startup=104,StartupEx=112,ProcessInfo=24,Security=24):
        raise RuntimeError('Unsupported Win32 ABI layout: '+str(values))
    if Accounting.ActiveProcesses.offset!=40 or ExtendedLimit.IoInfo.offset!=64:
        raise RuntimeError('Invalid Win32 field offsets')
    return values


class API:
    def __init__(self):
        if os.name!='nt': raise RuntimeError('Windows only')
        layout(); self.k=C.WinDLL('kernel32',use_last_error=True);self.closed=[]
        signatures={
          'CreateJobObjectW':([C.c_void_p,W.LPCWSTR],HANDLE),
          'OpenJobObjectW':([DWORD,W.BOOL,W.LPCWSTR],HANDLE),
          'SetInformationJobObject':([HANDLE,C.c_int,C.c_void_p,DWORD],W.BOOL),
          'QueryInformationJobObject':([HANDLE,C.c_int,C.c_void_p,DWORD,C.c_void_p],W.BOOL),
          'IsProcessInJob':([HANDLE,HANDLE,C.POINTER(W.BOOL)],W.BOOL),
          'GetCurrentProcess':([],HANDLE),
          'InitializeProcThreadAttributeList':([C.c_void_p,DWORD,DWORD,C.POINTER(SIZE)],W.BOOL),
          'UpdateProcThreadAttribute':([C.c_void_p,DWORD,SIZE,C.c_void_p,SIZE,C.c_void_p,C.c_void_p],W.BOOL),
          'DeleteProcThreadAttributeList':([C.c_void_p],None),
          'CreateProcessW':([W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,DWORD,C.c_void_p,W.LPCWSTR,C.c_void_p,C.POINTER(ProcessInfo)],W.BOOL),
          'ResumeThread':([HANDLE],DWORD),
          'TerminateJobObject':([HANDLE,W.UINT],W.BOOL),
          'TerminateProcess':([HANDLE,W.UINT],W.BOOL),
          'GetExitCodeProcess':([HANDLE,C.POINTER(DWORD)],W.BOOL),
          'WaitForSingleObject':([HANDLE,DWORD],DWORD),
          'OpenProcess':([DWORD,W.BOOL,DWORD],HANDLE),
          'CloseHandle':([HANDLE],W.BOOL),
          'CreateFileW':([W.LPCWSTR,DWORD,DWORD,C.c_void_p,DWORD,DWORD,HANDLE],HANDLE)}
        for n,(args,result) in signatures.items():
            fn=getattr(self.k,n);fn.argtypes=args;fn.restype=result

    def check(self,result,name):
        if not result:
            code=C.get_last_error();raise OSError(code,name+': '+C.FormatError(code))
        return result

    def close(self,handle):
        if handle:
            self.check(self.k.CloseHandle(handle),'CloseHandle');self.closed.append(int(handle))

    def job(self,name):
        h=self.check(self.k.CreateJobObjectW(None,name),'CreateJobObjectW')
        try:
            info=ExtendedLimit();info.BasicLimitInformation.LimitFlags=0x2000 # KILL_ON_JOB_CLOSE only; no breakaway
            self.check(self.k.SetInformationJobObject(h,9,C.byref(info),C.sizeof(info)),'SetInformationJobObject')
            return h
        except BaseException:self.close(h);raise

    def member(self,process,job):
        b=W.BOOL();self.check(self.k.IsProcessInJob(process,job,C.byref(b)),'IsProcessInJob');return bool(b.value)

    def accounting(self,job):
        a=Accounting();self.check(self.k.QueryInformationJobObject(job,1,C.byref(a),C.sizeof(a),None),'QueryInformationJobObject')
        result={name:int(getattr(a,name)) for name,_ in a._fields_}
        result['cpu']=(a.TotalUserTime+a.TotalKernelTime)/1e7
        return result

    def pids(self,job):
        class PIDList(C.Structure):
            _fields_=[('assigned',DWORD),('count',DWORD),('ids',SIZE*128)]
        a=PIDList();self.check(self.k.QueryInformationJobObject(job,3,C.byref(a),C.sizeof(a),None),'QueryInformationJobObject/PIDs')
        if a.count>128:raise RuntimeError('Job PID list overflow')
        return [int(i) for i in a.ids[:a.count]]

    def exit_code(self,process):
        code=DWORD();self.check(self.k.GetExitCodeProcess(process,C.byref(code)),'GetExitCodeProcess');return int(code.value)

    def create(self,job,argv,cwd,env,log):
        """Atomic job-list association, suspended start, restricted inherited std handles."""
        handles=[]; attrs=None; initialized=False
        try:
            security=Security(C.sizeof(Security),None,True)
            for filename,access,disposition in [(str(log),0x40000000,1),('NUL',0x80000000,3)]:
                h=self.k.CreateFileW(filename,access,3,C.byref(security),disposition,0,None)
                if h==C.c_void_p(-1).value:self.check(False,'CreateFileW')
                handles.append(h)
            size=SIZE();self.k.InitializeProcThreadAttributeList(None,2,0,C.byref(size))
            if C.get_last_error()!=122:raise RuntimeError('Unexpected attribute-list sizing result')
            attrs=C.create_string_buffer(size.value)
            self.check(self.k.InitializeProcThreadAttributeList(attrs,2,0,C.byref(size)),'InitializeProcThreadAttributeList');initialized=True
            jobs=(HANDLE*1)(job); std=(HANDLE*2)(*handles)
            for key,value in [(0x2000D,jobs),(0x20002,std)]:
                self.check(self.k.UpdateProcThreadAttribute(attrs,0,key,value,C.sizeof(value),None,None),'UpdateProcThreadAttribute')
            startup=StartupEx();startup.StartupInfo.cb=C.sizeof(startup)
            startup.lpAttributeList=C.cast(attrs,C.c_void_p);startup.StartupInfo.dwFlags=0x100
            startup.StartupInfo.hStdOutput=handles[0];startup.StartupInfo.hStdError=handles[0];startup.StartupInfo.hStdInput=handles[1]
            pi=ProcessInfo();command=C.create_unicode_buffer(subprocess.list2cmdline(list(map(str,argv))))
            block=C.create_unicode_buffer('\0'.join(k+'='+v for k,v in sorted(env.items(),key=lambda x:x[0].upper()))+'\0\0')
            flags=0x80000|0x400|0x4|0x8000000 # EXTENDED_STARTUPINFO, unicode env, suspended, no window
            self.check(self.k.CreateProcessW(str(argv[0]),command,None,None,True,flags,block,str(cwd),C.byref(startup),C.byref(pi)),'CreateProcessW')
            return pi
        finally:
            if initialized:self.k.DeleteProcThreadAttributeList(attrs)
            for h in reversed(handles):self.close(h)

    def resume(self,thread):
        previous=self.k.ResumeThread(thread)
        if previous==0xffffffff:self.check(False,'ResumeThread')
        if previous!=1:raise RuntimeError('Unexpected initial suspend count: '+str(previous))

    def terminate(self,job):self.check(self.k.TerminateJobObject(job,99),'TerminateJobObject')
