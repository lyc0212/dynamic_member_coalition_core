"""Single-writer durable events and a shared semantic call stack."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import threading

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


class LocalJournal:
    def __init__(self, path, task_id, attempt_id, max_bytes):
        self.path = Path(path)
        self.task_id, self.attempt_id = task_id, attempt_id
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.max_bytes, self.invalid = max_bytes, False
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
        self.file.close()


class NestedJournal:
    def __init__(self, local):
        self.local, self.ordinal = local, 0
        self.stack, self.states = [], {}

    def allocate(self, call_type, actual_category=None, model_category=None):
        self.local.check()
        parent = self.stack[-1] if self.stack else None
        parent_type = parent['call_type'] if parent else None
        require(call_type in CALL_GRAPH_ALLOWLIST.get(parent_type, set()),
                'CALL_GRAPH_VIOLATION')
        self.ordinal += 1
        return dict(call_id=f'{self.local.attempt_id}:{self.ordinal}',
                    parent_call_id=parent['call_id'] if parent else None,
                    call_type=call_type, actual_category=actual_category,
                    model_category=model_category)

    def event(self, call, status, before, after, **extra):
        self.local.check()
        cid = call['call_id']
        require(status in {'STARTED', 'RETURNED', 'FAILED', 'REJECTED'}, 'UNKNOWN_STATUS')
        current_parent = self.stack[-1]['call_id'] if self.stack else None
        if status in {'STARTED', 'REJECTED'}:
            require(cid not in self.states and call['parent_call_id'] == current_parent,
                    'DUPLICATE_CALL_OR_PARENT')
        else:
            require(self.states.get(cid) == 'STARTED' and self.stack and
                    self.stack[-1] == call, 'CALL_NOT_LIFO_OR_TERMINATED')
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
        active, seen, states = [], {}, {}
        for row in self.local.records():
            e = row['event']
            require(e['event_kind'] == 'RESOURCE_CALL', 'UNKNOWN_EVENT_KIND')
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
        return dict(status='PASS', calls=len(seen))


class ModelJournal:
    def __init__(self, nested):
        self.nested = nested

    def event(self, call, status, before, after, **extra):
        require(call['actual_category'] in MODEL_MAP and
                call['model_category'] == MODEL_MAP[call['actual_category']], 'MODEL_MAPPING')
        mapped_before = {MODEL_MAP[k]: v for k, v in before.items()}
        mapped_after = {MODEL_MAP[k]: v for k, v in after.items()}
        return self.nested.event(call, status, mapped_before, mapped_after,
                                 actual_budget_before=deepcopy(before),
                                 actual_budget_after=deepcopy(after), **extra)
