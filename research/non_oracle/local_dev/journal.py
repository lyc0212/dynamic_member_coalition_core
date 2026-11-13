"""Single-writer durable events and a shared semantic call stack."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import threading
from collections.abc import Mapping

from .diagnostics import emit

MODEL_MAP = {'ACTUAL_POLICY_WLS': 'MODEL_POLICY_EVALUATION_WLS',
             'ACTUAL_OBSERVATION_WLS': 'MODEL_OBSERVATION_WLS',
             'ACTUAL_SOLVER_START': 'MODEL_SOLVER_START'}
CALL_GRAPH_ALLOWLIST = {
    None: {'R', 'OBSERVATION_WLS'},
    'R': {'POLICY_WLS', 'ASSIGNMENT'},
    'POLICY_WLS': {'SOLVER'},
    'OBSERVATION_WLS': {'SOLVER'},
    'SOLVER': set(), 'ASSIGNMENT': set(),
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


class _Immutable(Mapping):
    """Ordinary API mutation is intercepted; hostile reflection is out of scope."""
    __slots__ = ('_items', '_mutation')

    def __init__(self, items, mutation):
        if hasattr(self, '_items'):
            self._reject()
        object.__setattr__(self, '_items', tuple(items))
        object.__setattr__(self, '_mutation', mutation)

    def __getitem__(self, key):
        return next(value for name, value in self._items if name == key)

    def __iter__(self):
        return (name for name, _ in self._items)

    def __len__(self):
        return len(self._items)

    def _reject(self, *args, **kwargs):
        self._mutation()
        raise RuntimeError('IMMUTABLE_CALL_IDENTITY')

    __setattr__ = __delattr__ = __setitem__ = __delitem__ = _reject
    update = clear = pop = popitem = setdefault = __ior__ = _reject


class CallHandle(_Immutable):
    __slots__ = ()


class AllocationRecord(_Immutable):
    __slots__ = ()


class _VerifiedCall(_Immutable):
    __slots__ = ()

    def __init__(self, owner, token, items):
        require(token is owner._factory_token, 'PRIVATE_VERIFIED_FACTORY')
        super().__init__(items, owner._identity_mutation)


class CommitCredential(_Immutable):
    __slots__ = ()

    def __init__(self, owner, token, items):
        require(token is owner._factory_token, 'PRIVATE_CREDENTIAL_FACTORY')
        super().__init__(items, owner._identity_mutation)


class LocalJournal:
    def __init__(self, path, task_id, attempt_id, max_bytes):
        require(isinstance(attempt_id, str) and bool(attempt_id), 'INVALID_ATTEMPT_ID')
        self.path = Path(path)
        self.task_id, self.attempt_id = task_id, attempt_id
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.max_bytes, self.invalid = max_bytes, False
        self.sealed = False
        self.sequence, self.previous, self.size = 0, None, 0
        self.hash = hashlib.sha256()
        self.file = self.path.open('xb', buffering=0)
        stat = os.fstat(self.file.fileno())
        self.identity = (stat.st_dev, stat.st_ino)

    def check(self):
        require(not self.invalid, 'JOURNAL_INVALID')
        require((self.pid, self.thread) == (os.getpid(), threading.get_ident()),
                'JOURNAL_WRITER_IDENTITY')
        stat = self.path.stat()
        require((stat.st_dev, stat.st_ino) == self.identity and stat.st_size == self.size,
                'JOURNAL_IDENTITY_OR_SIZE')

    def records(self):
        try:
            return self._records()
        except BaseException:
            self.invalid = True
            raise

    def _records(self):
        self.check()
        raw = self.path.read_bytes()
        require(hashlib.sha256(raw).digest() == self.hash.digest(), 'JOURNAL_HISTORY_CHANGED')
        rows = []
        previous = None
        for number, line in enumerate(raw.splitlines(), 1):
            row = json.loads(line)
            saved = row.pop('digest')
            require(row['sequence'] == number and row['event']['sequence'] == number
                    and row['previous'] == previous and
                    row['attempt_id'] == self.attempt_id and row['task_id'] == self.task_id
                    and saved == digest(row), 'JOURNAL_CHAIN_INVALID')
            previous = saved
            row['digest'] = saved
            rows.append(row)
        require(len(rows) == self.sequence, 'JOURNAL_SEQUENCE_INVALID')
        return rows

    def append(self, event):
        require(not self.sealed, 'JOURNAL_SEALED')
        require(not self.file.closed, 'JOURNAL_CLOSED')
        try:
            self.check()
            event = deepcopy(event)
            event['sequence'] = self.sequence + 1
            row = dict(task_id=self.task_id, attempt_id=self.attempt_id,
                       sequence=self.sequence + 1, previous=self.previous, event=event)
            row['digest'] = digest(row)
            data = (json.dumps(row, sort_keys=True, separators=(',', ':'),
                               allow_nan=False) + '\n').encode()
            require(self.size + len(data) <= self.max_bytes, 'JOURNAL_STORAGE_LIMIT')
            offset = 0
            while offset < len(data):
                count = self.file.write(data[offset:])
                require(count is not None and count > 0, 'JOURNAL_SHORT_WRITE')
                offset += count
            self.file.flush()
            os.fsync(self.file.fileno())
            require(os.fstat(self.file.fileno()).st_size == self.size + len(data),
                    'JOURNAL_WRITE_UNCERTAIN')
            self.hash.update(data)
            self.size += len(data)
            self.sequence += 1
            self.previous = row['digest']
            return row
        except BaseException:
            self.invalid = True
            raise

    def close(self):
        if not self.file.closed:
            self.file.close()

    def seal(self):
        if not self.sealed:
            try:
                self.records()
                if not self.file.closed:
                    self.file.flush()
                    os.fsync(self.file.fileno())
                self.sealed = True
            except BaseException:
                self.invalid = True
                raise


class NestedJournal:
    def __init__(self, local):
        self.local, self.ordinal = local, 0
        self.stack, self.states = [], {}
        self.state, self.poisoned = 'OPEN', False
        self._allocations, self._credentials = [], []
        self._factory_token = object()

    def _identity_mutation(self):
        if self.state not in {'FINALIZED_PASS', 'FINALIZED_FAILED'}:
            self.poisoned = True
            self.state = 'POISONED'
        emit(self.local.task_id, self.local.attempt_id, 'CALL_ID_MUTATION',
             RuntimeError('IMMUTABLE_CALL_IDENTITY'), resource_state='UNKNOWN')
        raise RuntimeError('IMMUTABLE_CALL_IDENTITY')

    def require_open(self):
        require(not self.poisoned, 'NESTED_JOURNAL_POISONED')
        require(self.state == 'OPEN', 'NESTED_JOURNAL_FINALIZED_OR_FINALIZING')
        self.local.check()

    def _bad_identity(self, message):
        if self.state not in {'FINALIZED_PASS', 'FINALIZED_FAILED'}:
            self.poisoned, self.state = True, 'POISONED'
        emit(self.local.task_id, self.local.attempt_id, 'IDENTITY_VALIDATION',
             RuntimeError(message), resource_state='UNKNOWN')
        raise RuntimeError(message)

    def _verify(self, handle):
        self.require_open()
        record = next((r for r in self._allocations if r['handle'] is handle), None)
        if type(handle) is not CallHandle or record is None:
            self._bad_identity('UNALLOCATED_CALL_HANDLE')
        snapshot = record['snapshot']
        if tuple(handle.items()) != snapshot:
            self._bad_identity('ALLOCATED_IDENTITY_MISMATCH')
        self._validate_id(handle['call_id'])
        return _VerifiedCall(self, self._factory_token,
                             (('record', record), ('snapshot', snapshot)))

    def _validate_id(self, cid):
        prefix, separator, suffix = cid.rpartition(':CALL_') if isinstance(cid, str) else ('', '', '')
        valid = (separator and prefix == self.local.attempt_id and suffix.isascii()
                 and suffix.isdecimal() and int(suffix) > 0
                 and cid == f'{prefix}:CALL_{int(suffix):03d}')
        require(valid, 'INVALID_CALL_ID_FORMAT')

    def _check_extra(self, extra):
        reserved = {'call_id', 'parent_call_id', 'call_type', 'actual_category',
                    'model_category', 'event_kind', 'status', 'scientific_execution',
                    'budget_before', 'budget_after', 'actual_budget_before',
                    'actual_budget_after', 'sequence'} | set(MODEL_MAP) | set(MODEL_MAP.values())
        if reserved.intersection(extra):
            self._bad_identity('RESERVED_EVENT_FIELD_OVERRIDE')

    def allocate(self, call_type, actual_category=None, model_category=None):
        self.require_open()
        require(all(x is None or isinstance(x, str) for x in
                    (actual_category, model_category)), 'NONSCALAR_CALL_IDENTITY')
        parent = self.stack[-1] if self.stack else None
        parent_type = parent['call_type'] if parent else None
        require(call_type in CALL_GRAPH_ALLOWLIST.get(parent_type, set()),
                'CALL_GRAPH_VIOLATION')
        require(type(self.ordinal) is int and self.ordinal >= 0, 'INVALID_CALL_ORDINAL')
        self.ordinal += 1
        handle = CallHandle(dict(call_id=f'{self.local.attempt_id}:CALL_{self.ordinal:03d}',
                    parent_call_id=parent['call_id'] if parent else None,
                    call_type=call_type, actual_category=actual_category,
                    model_category=model_category).items(), self._identity_mutation)
        self._allocations.append(AllocationRecord(
            (('handle', handle), ('snapshot', tuple(handle.items()))), self._identity_mutation))
        return handle

    def event(self, call, status, before, after, /, **extra):
        verified = self._verify(call)
        self._check_extra(extra)
        return self._commit(verified, status, before, after, extra)

    def _commit(self, verified, status, before, after, extra):
        self.require_open()
        require(type(verified) is _VerifiedCall and any(
            verified['record'] is r for r in self._allocations), 'PRIVATE_VERIFIED_CALL')
        call = verified['record']['handle']
        cid = call['call_id']
        require(status in {'STARTED', 'RETURNED', 'FAILED', 'REJECTED'}, 'UNKNOWN_STATUS')
        current_parent = self.stack[-1]['call_id'] if self.stack else None
        if status in {'STARTED', 'REJECTED'}:
            require(cid not in self.states and call['parent_call_id'] == current_parent,
                    'DUPLICATE_CALL_OR_PARENT')
        else:
            require(self.states.get(cid) == 'STARTED' and self.stack and
                    self.stack[-1] is call, 'CALL_NOT_LIFO_OR_TERMINATED')
        event = dict(call, event_kind='RESOURCE_CALL', status=status,
                     scientific_execution='LOCAL_DEV_MODEL',
                     budget_before=deepcopy(before), budget_after=deepcopy(after), **extra)
        try:
            result = self.local.append(event)
        except BaseException as exc:
            emit(self.local.task_id, self.local.attempt_id, status + '_PERSISTENCE', exc,
                 diagnostic_type=('STARTED_PERSISTENCE_FAILURE' if status == 'STARTED'
                                  else 'JOURNAL_PERSISTENCE_FAILURE'),
                 **call, budget_before=before, budget_after=after,
                 resource_state='UNRECONCILED')
            raise
        try:
            self._credentials.append(CommitCredential(self, self._factory_token,
                (('allocation', verified['record']), ('snapshot', verified['snapshot']),
                 ('status', status), ('sequence', result['sequence']),
                 ('digest', result['digest']))))
        except BaseException:
            self.poisoned, self.state = True, 'POISONED'
            raise
        self.states[cid] = status
        if status == 'STARTED':
            self.stack.append(call)
        elif status in {'RETURNED', 'FAILED'}:
            self.stack.pop()
        return result

    def committed_usage(self, call_type):
        return sum(row['event']['event_kind'] == 'RESOURCE_CALL' and
                   row['event']['call_type'] == call_type and
                   row['event']['status'] == 'STARTED' for row in self.local.records())

    def audit(self):
        resource_rows = [row for row in self.local.records()
                         if row['event'].get('event_kind') == 'RESOURCE_CALL']
        require(len(resource_rows) == len(self._credentials), 'COMMIT_CREDENTIAL_COUNT')
        for row, credential in zip(resource_rows, self._credentials):
            require(row['sequence'] == credential['sequence'] and
                    row['digest'] == credential['digest'], 'COMMIT_CREDENTIAL_ORDER')
            record = credential['allocation']
            require(any(record is original for original in self._allocations),
                    'ORPHAN_COMMIT_CREDENTIAL')
            self._validate_id(row['event'].get('call_id'))
            require(all(row['event'].get(k) == v for k, v in credential['snapshot'])
                    and record['snapshot'] == credential['snapshot'],
                    'ALLOCATED_IDENTITY_MISMATCH')
            require(row['event'].get('status') == credential['status'],
                    'COMMITTED_STATUS_MISMATCH')
        active, seen, states = [], {}, {}
        for row in self.local.records():
            e = row['event']
            if e.get('event_kind') != 'RESOURCE_CALL':
                continue
            cid, status = e['call_id'], e['status']
            require(cid.startswith(self.local.attempt_id + ':'), 'FOREIGN_CALL_ID')
            actual = e['actual_category']
            if e['call_type'] in {'R', 'ASSIGNMENT'}:
                require(actual is None and e['model_category'] is None, 'INDEPENDENT_CATEGORY')
            else:
                expected = {'POLICY_WLS': 'ACTUAL_POLICY_WLS',
                            'OBSERVATION_WLS': 'ACTUAL_OBSERVATION_WLS',
                            'SOLVER': 'ACTUAL_SOLVER_START'}
                require(e['call_type'] in expected and actual == expected[e['call_type']]
                        and e['model_category'] == MODEL_MAP[actual], 'RESOURCE_CATEGORY')
            if e['call_type'] == 'R' and status == 'STARTED':
                path = Path(e['provenance_id'])
                require(e['provenance_tick'] in (80, 100) and
                        hashlib.sha256(path.read_bytes()).hexdigest() == e['provenance_sha256'],
                        'R_PROVENANCE_BINDING')
            if status in {'STARTED', 'REJECTED'}:
                parent = active[-1] if active else None
                require(cid not in seen and e['parent_call_id'] == parent, 'CALL_ID_OR_PARENT')
                pt = seen[parent]['call_type'] if parent else None
                require(e['call_type'] in CALL_GRAPH_ALLOWLIST.get(pt, set()), 'CALL_GRAPH')
                seen[cid] = e
                if status == 'STARTED':
                    active.append(cid)
            else:
                require(status in {'RETURNED', 'FAILED'} and active and active[-1] == cid
                        and states.get(cid) == 'STARTED', 'UNCLOSED_OR_DUPLICATE_CALL')
                require(all(e[k] == seen[cid][k] for k in
                            ('parent_call_id', 'call_type', 'actual_category', 'model_category')),
                        'TERMINAL_IDENTITY')
                active.pop()
            states[cid] = status
        require(not active, 'UNCLOSED_CALLS')
        require(all(v == 'RETURNED' for v in states.values()), 'FAILED_OR_REJECTED_CALLS')
        require(not self.poisoned, 'NESTED_JOURNAL_POISONED')
        return dict(status='PASS', calls=len(seen))


class ModelJournal:
    def __init__(self, nested):
        self.nested = nested

    def event(self, call, status, before, after, /, **extra):
        verified = self.nested._verify(call)
        self.nested._check_extra(extra)
        require(call['actual_category'] in MODEL_MAP and
                call['model_category'] == MODEL_MAP[call['actual_category']], 'MODEL_MAPPING')
        mapped_before = {MODEL_MAP[k]: v for k, v in before.items()}
        mapped_after = {MODEL_MAP[k]: v for k, v in after.items()}
        metadata = dict(extra, actual_budget_before=deepcopy(before),
                        actual_budget_after=deepcopy(after))
        return self.nested._commit(verified, status, mapped_before, mapped_after, metadata)
