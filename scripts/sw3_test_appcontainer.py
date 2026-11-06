"""Native Windows AppContainer launcher for SW3 TEST-0."""
from contextlib import ExitStack, contextmanager
import ctypes as c
from ctypes import wintypes as w
import subprocess
import msvcrt
import os
from uuid import uuid4

P = c.c_void_p


class Startup(c.Structure):
    _fields_ = [("cb", w.DWORD), ("reserved", w.LPWSTR), ("desktop", w.LPWSTR),
                ("title", w.LPWSTR), ("values", w.DWORD * 8), ("show", w.WORD),
                ("reserved_count", w.WORD), ("reserved_bytes", P), ("handles", w.HANDLE * 3)]


class Extended(c.Structure):
    _fields_ = [("startup", Startup), ("attributes", P)]


class Process(c.Structure):
    _fields_ = [("process", w.HANDLE), ("thread", w.HANDLE), ("pid", w.DWORD), ("tid", w.DWORD)]


class Capabilities(c.Structure):
    _fields_ = [("sid", P), ("capabilities", P), ("count", w.DWORD), ("reserved", w.DWORD)]


def bind(dll, name, args, result=w.BOOL):
    method = getattr(c.WinDLL(dll, use_last_error=True), name)
    method.argtypes, method.restype = args, result
    return method


def kernel(name, args, result=w.BOOL):
    return bind("kernel32", name, args, result)


def check(value):
    if not value:
        raise c.WinError(c.get_last_error())


@contextmanager
def profile():
    name = "Codex.SW3.Test." + uuid4().hex
    sid = P()
    create = bind("userenv", "CreateAppContainerProfile",
                  [w.LPCWSTR, w.LPCWSTR, w.LPCWSTR, P, w.DWORD, c.POINTER(P)], c.c_long)
    delete = bind("userenv", "DeleteAppContainerProfile", [w.LPCWSTR], c.c_long)
    hr = create(name, name, "SW3 limited prediction worker", None, 0, c.byref(sid))
    if hr != 0:
        raise OSError(f"CreateAppContainerProfile HRESULT {hr:#x}")
    sid_text = w.LPWSTR()
    try:
        check(bind("advapi32", "ConvertSidToStringSidW", [P, c.POINTER(w.LPWSTR)])(
            sid, c.byref(sid_text)))
        yield sid, sid_text.value
    finally:
        if sid_text:
            kernel("LocalFree", [P], P)(c.cast(sid_text, P))
        bind("advapi32", "FreeSid", [P], P)(sid)
        delete(name)


@contextmanager
def diagnostic_handles(stdout, stderr, empty_stdin):
    with ExitStack() as stack:
        handles = []
        for path, mode in ((empty_stdin, "rb"), (stdout, "xb"), (stderr, "xb")):
            stream = stack.enter_context(path.open(mode, buffering=0))
            handle = msvcrt.get_osfhandle(stream.fileno())
            os.set_handle_inheritable(handle, True)
            handles.append(handle)
        yield (w.HANDLE * 3)(*handles)


def run(sid, executable, args, cwd, environment, *, stdout, stderr, empty_stdin,
        timeout_ms=180000):
    init = kernel("InitializeProcThreadAttributeList", [P, w.DWORD, w.DWORD, c.POINTER(c.c_size_t)])
    size = c.c_size_t()
    init(None, 2, 0, c.byref(size))
    buffer = c.create_string_buffer(size.value)
    check(init(buffer, 2, 0, c.byref(size)))
    close = kernel("CloseHandle", [w.HANDLE])
    try:
        cap = Capabilities(sid, None, 0, 0)
        update = kernel("UpdateProcThreadAttribute", [P, w.DWORD, c.c_size_t, P, c.c_size_t, P, P])
        check(update(buffer, 0, 0x20009, c.byref(cap), c.sizeof(cap), None, None))
        startup = Extended()
        startup.startup.cb = c.sizeof(startup)
        startup.attributes = c.cast(buffer, P)
        proc = Process()
        command = c.create_unicode_buffer(subprocess.list2cmdline([str(executable), *args]))
        env = c.create_unicode_buffer("\0".join(
            f"{k}={environment[k]}" for k in sorted(environment, key=str.casefold)) + "\0\0")
        create = kernel("CreateProcessW", [w.LPCWSTR, w.LPWSTR, P, P, w.BOOL, w.DWORD,
                                           P, w.LPCWSTR, c.POINTER(Extended), c.POINTER(Process)])
        with diagnostic_handles(stdout, stderr, empty_stdin) as handles:
            check(update(buffer, 0, 0x20002, handles, c.sizeof(handles), None, None))
            startup.startup.values[7] = 0x100  # STARTF_USESTDHANDLES
            startup.startup.handles = handles
            check(create(str(executable), command, None, None, True, 0x08080400, env,
                         str(cwd), c.byref(startup), c.byref(proc)))
        wait = kernel("WaitForSingleObject", [w.HANDLE, w.DWORD], w.DWORD)
        try:
            waited = wait(proc.process, timeout_ms)
            if waited == 258:
                check(kernel("TerminateProcess", [w.HANDLE, w.UINT])(proc.process, 124))
                if wait(proc.process, 5000) != 0:
                    raise TimeoutError(f"AppContainer worker {proc.pid} did not exit after termination")
            elif waited != 0:
                raise c.WinError(c.get_last_error())
            status = w.DWORD()
            check(kernel("GetExitCodeProcess", [w.HANDLE, c.POINTER(w.DWORD)])(proc.process, c.byref(status)))
            return dict(pid=proc.pid, exit_code=status.value, timed_out=waited == 258)
        finally:
            close(proc.thread)
            close(proc.process)
    finally:
        kernel("DeleteProcThreadAttributeList", [P], None)(buffer)
