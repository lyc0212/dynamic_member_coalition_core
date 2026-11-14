"""Independent failure transport through the existing shared Windows log."""
import ctypes
import json
import os
from pathlib import Path
import sys
import threading
import time

PREFIX = '@@STFBS_RESOURCE_DIAG_V1@@'


def emit(task_id, attempt_id, phase, exc, **fields):
    record = dict(schema_version=1, diagnostic_type='RESOURCE_FAILURE',
                  task_id=task_id, attempt_id=attempt_id, phase=phase,
                  call_id=None, call_type=None, actual_category=None,
                  model_category=None, budget_before='UNKNOWN',
                  budget_after='UNKNOWN', resource_state='UNKNOWN',
                  exception_type=type(exc).__name__, exception_message=str(exc))
    record.update(fields)
    try:
        line = PREFIX + json.dumps(record, separators=(',', ':'), allow_nan=False) + '\n'
        if sys.stderr.write(line) != len(line):
            raise OSError('DIAGNOSTIC_SHORT_WRITE')
        sys.stderr.flush()
    except BaseException:
        # Failure of both channels cannot be reconciled by inventing an event.
        raise RuntimeError('RESOURCE_STATE=UNRECONCILED') from exc


def persist(path, value):
    """Exclusive receipt creation; never rewrite a historical receipt."""
    encoded = (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_BINARY, 0o600)
    try:
        offset = 0
        while offset < len(encoded):
            n = os.write(fd, encoded[offset:])
            if n <= 0:
                raise OSError('RECEIPT_SHORT_WRITE')
            offset += n
        os.fsync(fd)
        if os.fstat(fd).st_size != len(encoded):
            raise OSError('RECEIPT_SIZE_MISMATCH')
    finally:
        os.close(fd)


def shared_reader(path):
    """Reader shares READ|WRITE|DELETE; existing writer uses share READ|WRITE."""
    import msvcrt
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32,
                               ctypes.c_uint32, ctypes.c_void_p,
                               ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    api.CreateFileW.restype = ctypes.c_void_p
    handle = api.CreateFileW(str(path), 0x80000000, 7, None, 3, 0, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        api.CloseHandle.argtypes = [ctypes.c_void_p]
        api.CloseHandle(handle)
        raise
    return os.fdopen(fd, 'rb', buffering=0)


class DiagnosticReceiver:
    """Start before monitored launch; tail concurrently, then record real exit."""
    def __init__(self, log, receipt_directory, task_id, attempt_id):
        self.log = Path(log)
        self.directory = Path(receipt_directory)
        if self.log.exists() or not self.directory.is_dir():
            raise ValueError('FRESH_LOG_AND_EXISTING_RECEIPT_DIRECTORY_REQUIRED')
        self.task_id, self.attempt_id = task_id, attempt_id
        self.stop = threading.Event()
        self.records, self.errors = [], []
        self.resource_state = 'UNKNOWN'
        self.thread = threading.Thread(target=self._receive, daemon=True)

    def start(self):
        self.thread.start()

    def _receive(self):
        reader = None
        pending = b''
        offset = 0
        try:
            while True:
                if reader is None:
                    if self.log.exists():
                        reader = shared_reader(self.log)
                    elif self.stop.wait(.02):
                        break
                    else:
                        continue
                block = reader.read(65536)
                if block:
                    pending += block
                    while b'\n' in pending:
                        line, pending = pending.split(b'\n', 1)
                        start = offset
                        offset += len(line) + 1
                        marker = line.find(PREFIX.encode())
                        if marker < 0:
                            continue
                        value = json.loads(line[marker + len(PREFIX):])
                        if (value.get('task_id') != self.task_id or
                                value.get('attempt_id') != self.attempt_id or
                                value.get('schema_version') != 1):
                            raise ValueError('DIAGNOSTIC_IDENTITY_MISMATCH')
                        required = {'schema_version', 'diagnostic_type', 'task_id', 'attempt_id',
                                    'phase', 'call_id', 'call_type', 'actual_category',
                                    'model_category', 'budget_before', 'budget_after',
                                    'resource_state', 'exception_type', 'exception_message'}
                        if not required <= set(value) or value['resource_state'] not in {
                                'KNOWN', 'UNKNOWN', 'UNRECONCILED'}:
                            raise ValueError('DIAGNOSTIC_SCHEMA_INVALID')
                        receipt = dict(diagnostic=value, log=str(self.log),
                                       byte_offset=start + marker,
                                       worker_exit_status='UNKNOWN',
                                       receipt_persistence='COMMITTED_ON_SUCCESS')
                        persist(self.directory / ('diagnostic_%06d.json' %
                                                   len(self.records)), receipt)
                        self.records.append(receipt)
                        self.resource_state = value.get('resource_state', 'UNKNOWN')
                    continue
                if self.stop.wait(.02):
                    if PREFIX.encode() in pending:
                        raise ValueError('INCOMPLETE_LOG_LINE_AT_EXIT')
                    break
        except BaseException as exc:
            self.resource_state = 'UNRECONCILED'
            self.errors.append(dict(type=type(exc).__name__, message=str(exc)))
        finally:
            if reader is not None:
                reader.close()

    def finish(self, worker_exit_status):
        self.stop.set()
        self.thread.join()
        result = dict(task_id=self.task_id, attempt_id=self.attempt_id,
                      resource_state=self.resource_state, records=self.records,
                      errors=self.errors, worker_exit_status=worker_exit_status,
                      journal_audit_pass=False)
        try:
            persist(self.directory / 'diagnostic_final.json', result)
        except BaseException as exc:
            self.resource_state = 'UNRECONCILED'
            emit(self.task_id, self.attempt_id, 'CONTROLLER_RECEIPT', exc,
                 resource_state='UNRECONCILED')
            raise
        if self.errors:
            raise RuntimeError('RESOURCE_STATE=UNRECONCILED')
        return result


def monitor_supervised(supervisor, argv, *, cwd, log, receipts, task_id, attempt_id):
    """Future authorized controller integration; no launch occurs on import."""
    receiver = DiagnosticReceiver(log, receipts, task_id, attempt_id)
    receiver.start()
    result = None
    try:
        result = supervisor.run_monitored(argv, cwd=cwd, log=log)
        return result
    finally:
        receiver.finish(result.get('worker_exit_code', 'UNKNOWN')
                        if result is not None else 'UNKNOWN')
