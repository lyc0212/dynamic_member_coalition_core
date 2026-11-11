"""Instance-only real-token process adapter. No accounts/credentials are created.

Only an independently approved, already running provider process may supply a
primary token. Obtaining it is privileged and can fail closed. Nothing executes
on import. This adapter is not a Python/DLL isolation or IPC authorization proof.
"""
import ctypes as C
from ctypes import wintypes as W
import os
from pathlib import Path

from research.non_oracle.stfbs_lite_real_d60_source import _require


class SidAndAttributes(C.Structure):
    _fields_ = [('Sid', C.c_void_p), ('Attributes', W.DWORD)]


def inspect_token(token, *, consumer_sid, worker_sid, restricted=True):
    import win32security as s
    sid = s.ConvertSidToStringSid(s.GetTokenInformation(token, s.TokenUser)[0])
    groups = [(s.ConvertSidToStringSid(v), int(flags)) for v, flags in
              s.GetTokenInformation(token, s.TokenGroups)]
    restrictions = [(s.ConvertSidToStringSid(v), int(flags)) for v, flags in
                    s.GetTokenInformation(token, s.TokenRestrictedSids)]
    privileges = [(s.LookupPrivilegeName(None, luid), int(flags)) for luid, flags in
                  s.GetTokenInformation(token, s.TokenPrivileges)]
    elevated = bool(s.GetTokenInformation(token, s.TokenElevation))
    _require(sid == worker_sid and sid != consumer_sid and not elevated, 'INDEPENDENT_WORKER_TOKEN_REQUIRED')
    _require(not any(v in {consumer_sid, 'S-1-5-18', 'S-1-5-32-544'} for v, _ in groups),
             'WORKER_PRIVILEGED_GROUP_REJECTED')
    _require(s.GetTokenInformation(token, s.TokenType) == 1, 'PRIMARY_WORKER_TOKEN_REQUIRED')
    if restricted:
        _require(bool(restrictions), 'RESTRICTED_SIDS_REQUIRED')
        _require(all(not flags & 2 or name == 'SeChangeNotifyPrivilege' for name, flags in privileges),
                 'WORKER_ENABLED_PRIVILEGE_REJECTED')
    return dict(user_sid=sid, groups=groups, restricted_sids=restrictions,
                privileges=privileges, elevated=elevated, restricted_required=restricted)


def process_identity(api, handle):
    api.k.GetProcessTimes.argtypes = [W.HANDLE] + [C.POINTER(W.FILETIME)] * 4
    api.k.GetProcessTimes.restype = W.BOOL
    api.k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]
    api.k.QueryFullProcessImageNameW.restype = W.BOOL
    times = [W.FILETIME() for _ in range(4)]
    api.check(api.k.GetProcessTimes(handle, *(C.byref(t) for t in times)), 'GetProcessTimes')
    image, length = C.create_unicode_buffer(32768), W.DWORD(32768)
    api.check(api.k.QueryFullProcessImageNameW(handle, 0, image, C.byref(length)), 'QueryFullProcessImageNameW')
    return dict(creation_ticks=(times[0].dwHighDateTime << 32) | times[0].dwLowDateTime,
                image=str(Path(image.value).resolve()))


def acquire_worker_token(context):
    """No LogonUser, password, service creation or consumer-token fallback."""
    _require(os.name == 'nt', 'WINDOWS_REQUIRED')
    provider = context.get('token_source')
    _require(type(provider) is dict and set(provider) == {'pid', 'creation_ticks', 'image'},
             'INDEPENDENT_TOKEN_PROVIDER_NOT_PROVISIONED')
    _require(type(provider['pid']) is int and provider['pid'] > 0, 'TOKEN_PROVIDER_PID_INVALID')
    import win32security as s
    from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API
    api = API()
    process = api.k.OpenProcess(0x1000 | 0x100000, False, provider['pid'])
    api.check(process, 'OpenProcess/APPROVED_TOKEN_PROVIDER')
    original, consumer, token = None, None, W.HANDLE()
    sid_pointer = C.c_void_p()
    adv = C.WinDLL('advapi32', use_last_error=True)
    adv.ConvertStringSidToSidW.argtypes = [W.LPCWSTR, C.POINTER(C.c_void_p)]
    adv.ConvertStringSidToSidW.restype = W.BOOL
    adv.CreateRestrictedToken.argtypes = [W.HANDLE, W.DWORD, W.DWORD, C.c_void_p,
        W.DWORD, C.c_void_p, W.DWORD, C.POINTER(SidAndAttributes), C.POINTER(W.HANDLE)]
    adv.CreateRestrictedToken.restype = W.BOOL
    api.k.LocalFree.argtypes = [C.c_void_p]
    api.k.LocalFree.restype = C.c_void_p
    try:
        consumer = s.OpenProcessToken(api.k.GetCurrentProcess(), 0x8)
        _require(s.ConvertSidToStringSid(s.GetTokenInformation(consumer, s.TokenUser)[0])
                 == context['consumer_sid'], 'TRUSTED_CONSUMER_IDENTITY_REQUIRED')
        held = {s.LookupPrivilegeName(None, luid) for luid, _ in
                s.GetTokenInformation(consumer, s.TokenPrivileges)}
        _require({'SeAssignPrimaryTokenPrivilege', 'SeIncreaseQuotaPrivilege'} <= held,
                 'INDEPENDENT_CREATE_PROCESS_PRIVILEGES_NOT_PROVISIONED')
        identity = process_identity(api, process)
        _require(identity == {'creation_ticks':provider['creation_ticks'],
                             'image':str(Path(provider['image']).resolve())}
                 and api.k.WaitForSingleObject(process, 0) == 258, 'TOKEN_PROVIDER_IDENTITY_CONFLICT')
        original = s.OpenProcessToken(process, 0x1 | 0x2 | 0x8)
        _require(s.GetTokenInformation(original, s.TokenSessionId)
                 == s.GetTokenInformation(consumer, s.TokenSessionId), 'WORKER_JOB_SESSION_CONFLICT')
        inspect_token(original, consumer_sid=context['consumer_sid'], worker_sid=context['worker_sid'], restricted=False)
        api.check(adv.ConvertStringSidToSidW(context['worker_sid'], C.byref(sid_pointer)), 'ConvertStringSidToSidW')
        restricting = SidAndAttributes(sid_pointer, 0)
        api.check(adv.CreateRestrictedToken(int(original), 1, 0, None, 0, None, 1,
                                          C.byref(restricting), C.byref(token)), 'CreateRestrictedToken')
        evidence = inspect_token(token.value, consumer_sid=context['consumer_sid'], worker_sid=context['worker_sid'])
        evidence['provider'] = dict(identity, pid=provider['pid'])
        owned = token.value
        token.value = None
        return owned, evidence
    finally:
        if token.value:
            api.close(token.value)
        if original is not None:
            original.Close()
        if consumer is not None:
            consumer.Close()
        if sid_pointer.value:
            api.k.LocalFree(sid_pointer)
        api.close(process)


def restricted_create_adapter(token, context, *, executable, environment):
    """Reuse audited ABI/job-list/std-handle logic, change only this API instance.

    The instance dispatch slot calls CreateProcessAsUserW, NEVER CreateProcessW.
    Job-list association is at suspended creation, before any worker instruction.
    Parent supervisor owns Job/process/thread handles. Caller owns token.
    """
    from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API, ProcessInfo
    api = API()
    native = api.k
    adv = C.WinDLL('advapi32', use_last_error=True)
    adv.CreateProcessAsUserW.argtypes = [W.HANDLE, W.LPCWSTR, W.LPWSTR, C.c_void_p,
        C.c_void_p, W.BOOL, W.DWORD, C.c_void_p, W.LPCWSTR, C.c_void_p, C.POINTER(ProcessInfo)]
    adv.CreateProcessAsUserW.restype = W.BOOL
    expected_executable = Path(executable).resolve()
    allowed_environment = dict(environment)
    evidence, failures, created = [], [], []

    def cleanup_failed_create(job, pi):
        record = dict(pid=int(pi.dwProcessId), errors=[], exit_confirmed=False)
        try:
            if api.k.WaitForSingleObject(pi.hProcess, 0) != 0:
                api.check(api.k.TerminateProcess(pi.hProcess, 97), 'TerminateProcess/FAILED_RESTRICTED_CREATE')
            record['exit_confirmed'] = api.k.WaitForSingleObject(pi.hProcess, 2000) == 0
        except BaseException as exc:
            record['errors'].append(str(exc))
        for handle in (pi.hThread, pi.hProcess):
            try:
                api.close(handle)
            except BaseException as exc:
                record['errors'].append(str(exc))
        failures.append(record)  # Parent still owns Job and its final cleanup.

    class InstanceKernel:
        def __getattr__(self, name):
            return getattr(native, name)

        def CreateProcessW(self, *args):
            # Existing API.create dispatch ABI only; actual native call differs.
            result = adv.CreateProcessAsUserW(token, *args)
            if result:
                saved = ProcessInfo()
                C.memmove(C.byref(saved), args[-1], C.sizeof(saved))
                created.append(saved)
            return result

    api.k = InstanceKernel()
    base_create = api.create

    def create(job, argv, cwd, env, log):
        _require(Path(argv[0]).resolve() == expected_executable, 'UNAPPROVED_WORKER_EXECUTABLE')
        _require(list(argv[1:4]) == ['-I', '-S', '-B'], 'CONTROLLED_PYTHON_START_FLAGS_REQUIRED')
        inspect_token(token, consumer_sid=context['consumer_sid'], worker_sid=context['worker_sid'])
        try:
            pi = base_create(job, argv, cwd, allowed_environment, log)
        except BaseException:
            if created:
                cleanup_failed_create(job, created.pop())
            raise
        created.clear()
        process_token = None
        try:
            import win32security as s
            _require(api.member(pi.hProcess, job), 'RESTRICTED_WORKER_NOT_IN_TARGET_JOB')
            _require(api.k.WaitForSingleObject(pi.hProcess, 0) == 258, 'WORKER_NOT_LIVE_SUSPENDED')
            process_token = s.OpenProcessToken(pi.hProcess, 0x8)
            token_identity = inspect_token(process_token, consumer_sid=context['consumer_sid'],
                                           worker_sid=context['worker_sid'])
            actual = process_identity(api, pi.hProcess)
            _require(Path(actual['image']).resolve() == expected_executable, 'ACTUAL_WORKER_IMAGE_CONFLICT')
            evidence.append(dict(pid=int(pi.dwProcessId), **actual, token=token_identity,
                                 target_job_handle=int(job), state='CONTAINED_BEFORE_RESUME'))
            return pi
        except BaseException:
            cleanup_failed_create(job, pi)
            raise
        finally:
            if process_token is not None:
                process_token.Close()
    api.create = create
    api.restricted_creation_evidence = evidence
    api.restricted_creation_failures = failures
    return api
