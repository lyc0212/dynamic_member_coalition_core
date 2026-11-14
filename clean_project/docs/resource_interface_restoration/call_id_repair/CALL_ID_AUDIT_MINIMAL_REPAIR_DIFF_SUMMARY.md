# 最小修复差异

仅两个目标源码变更；无测试执行，无历史材料改动。

## 当前Git状态

 M research/non_oracle/local_dev/journal.py
 M research/non_oracle/local_dev/resources.py
?? docs/resource_interface_restoration/call_id_repair/

## 完整diff

diff --git a/research/non_oracle/local_dev/journal.py b/research/non_oracle/local_dev/journal.py
index 287092e..806c942 100644
--- a/research/non_oracle/local_dev/journal.py
+++ b/research/non_oracle/local_dev/journal.py
@@ -5,6 +5,7 @@ import json
 import os
 from pathlib import Path
 import threading
+from collections.abc import Mapping
 
 from .diagnostics import emit
 
@@ -30,12 +31,65 @@ def digest(value):
                                      allow_nan=False).encode()).hexdigest()
 
 
+class _Immutable(Mapping):
+    """Ordinary API mutation is intercepted; hostile reflection is out of scope."""
+    __slots__ = ('_items', '_mutation')
+
+    def __init__(self, items, mutation):
+        if hasattr(self, '_items'):
+            self._reject()
+        object.__setattr__(self, '_items', tuple(items))
+        object.__setattr__(self, '_mutation', mutation)
+
+    def __getitem__(self, key):
+        return next(value for name, value in self._items if name == key)
+
+    def __iter__(self):
+        return (name for name, _ in self._items)
+
+    def __len__(self):
+        return len(self._items)
+
+    def _reject(self, *args, **kwargs):
+        self._mutation()
+        raise RuntimeError('IMMUTABLE_CALL_IDENTITY')
+
+    __setattr__ = __delattr__ = __setitem__ = __delitem__ = _reject
+    update = clear = pop = popitem = setdefault = __ior__ = _reject
+
+
+class CallHandle(_Immutable):
+    __slots__ = ()
+
+
+class AllocationRecord(_Immutable):
+    __slots__ = ()
+
+
+class _VerifiedCall(_Immutable):
+    __slots__ = ()
+
+    def __init__(self, owner, token, items):
+        require(token is owner._factory_token, 'PRIVATE_VERIFIED_FACTORY')
+        super().__init__(items, owner._identity_mutation)
+
+
+class CommitCredential(_Immutable):
+    __slots__ = ()
+
+    def __init__(self, owner, token, items):
+        require(token is owner._factory_token, 'PRIVATE_CREDENTIAL_FACTORY')
+        super().__init__(items, owner._identity_mutation)
+
+
 class LocalJournal:
     def __init__(self, path, task_id, attempt_id, max_bytes):
+        require(isinstance(attempt_id, str) and bool(attempt_id), 'INVALID_ATTEMPT_ID')
         self.path = Path(path)
         self.task_id, self.attempt_id = task_id, attempt_id
         self.pid, self.thread = os.getpid(), threading.get_ident()
         self.max_bytes, self.invalid = max_bytes, False
+        self.sealed = False
         self.sequence, self.previous, self.size = 0, None, 0
         self.hash = hashlib.sha256()
         self.file = self.path.open('xb', buffering=0)
@@ -77,6 +131,8 @@ class LocalJournal:
         return rows
 
     def append(self, event):
+        require(not self.sealed, 'JOURNAL_SEALED')
+        require(not self.file.closed, 'JOURNAL_CLOSED')
         try:
             self.check()
             event = deepcopy(event)
@@ -106,28 +162,105 @@ class LocalJournal:
             raise
 
     def close(self):
-        self.file.close()
+        if not self.file.closed:
+            self.file.close()
+
+    def seal(self):
+        if not self.sealed:
+            try:
+                self.records()
+                if not self.file.closed:
+                    self.file.flush()
+                    os.fsync(self.file.fileno())
+                self.sealed = True
+            except BaseException:
+                self.invalid = True
+                raise
 
 
 class NestedJournal:
     def __init__(self, local):
         self.local, self.ordinal = local, 0
         self.stack, self.states = [], {}
+        self.state, self.poisoned = 'OPEN', False
+        self._allocations, self._credentials = [], []
+        self._factory_token = object()
 
-    def allocate(self, call_type, actual_category=None, model_category=None):
+    def _identity_mutation(self):
+        if self.state not in {'FINALIZED_PASS', 'FINALIZED_FAILED'}:
+            self.poisoned = True
+            self.state = 'POISONED'
+        emit(self.local.task_id, self.local.attempt_id, 'CALL_ID_MUTATION',
+             RuntimeError('IMMUTABLE_CALL_IDENTITY'), resource_state='UNKNOWN')
+        raise RuntimeError('IMMUTABLE_CALL_IDENTITY')
+
+    def require_open(self):
+        require(not self.poisoned, 'NESTED_JOURNAL_POISONED')
+        require(self.state == 'OPEN', 'NESTED_JOURNAL_FINALIZED_OR_FINALIZING')
         self.local.check()
+
+    def _bad_identity(self, message):
+        if self.state not in {'FINALIZED_PASS', 'FINALIZED_FAILED'}:
+            self.poisoned, self.state = True, 'POISONED'
+        emit(self.local.task_id, self.local.attempt_id, 'IDENTITY_VALIDATION',
+             RuntimeError(message), resource_state='UNKNOWN')
+        raise RuntimeError(message)
+
+    def _verify(self, handle):
+        self.require_open()
+        record = next((r for r in self._allocations if r['handle'] is handle), None)
+        if type(handle) is not CallHandle or record is None:
+            self._bad_identity('UNALLOCATED_CALL_HANDLE')
+        snapshot = record['snapshot']
+        if tuple(handle.items()) != snapshot:
+            self._bad_identity('ALLOCATED_IDENTITY_MISMATCH')
+        self._validate_id(handle['call_id'])
+        return _VerifiedCall(self, self._factory_token,
+                             (('record', record), ('snapshot', snapshot)))
+
+    def _validate_id(self, cid):
+        prefix, separator, suffix = cid.rpartition(':CALL_') if isinstance(cid, str) else ('', '', '')
+        valid = (separator and prefix == self.local.attempt_id and suffix.isascii()
+                 and suffix.isdecimal() and int(suffix) > 0
+                 and cid == f'{prefix}:CALL_{int(suffix):03d}')
+        require(valid, 'INVALID_CALL_ID_FORMAT')
+
+    def _check_extra(self, extra):
+        reserved = {'call_id', 'parent_call_id', 'call_type', 'actual_category',
+                    'model_category', 'event_kind', 'status', 'scientific_execution',
+                    'budget_before', 'budget_after', 'actual_budget_before',
+                    'actual_budget_after', 'sequence'} | set(MODEL_MAP) | set(MODEL_MAP.values())
+        if reserved.intersection(extra):
+            self._bad_identity('RESERVED_EVENT_FIELD_OVERRIDE')
+
+    def allocate(self, call_type, actual_category=None, model_category=None):
+        self.require_open()
+        require(all(x is None or isinstance(x, str) for x in
+                    (actual_category, model_category)), 'NONSCALAR_CALL_IDENTITY')
         parent = self.stack[-1] if self.stack else None
         parent_type = parent['call_type'] if parent else None
         require(call_type in CALL_GRAPH_ALLOWLIST.get(parent_type, set()),
                 'CALL_GRAPH_VIOLATION')
+        require(type(self.ordinal) is int and self.ordinal >= 0, 'INVALID_CALL_ORDINAL')
         self.ordinal += 1
-        return dict(call_id=f'{self.local.attempt_id}:{self.ordinal}',
+        handle = CallHandle(dict(call_id=f'{self.local.attempt_id}:CALL_{self.ordinal:03d}',
                     parent_call_id=parent['call_id'] if parent else None,
                     call_type=call_type, actual_category=actual_category,
-                    model_category=model_category)
+                    model_category=model_category).items(), self._identity_mutation)
+        self._allocations.append(AllocationRecord(
+            (('handle', handle), ('snapshot', tuple(handle.items()))), self._identity_mutation))
+        return handle
 
-    def event(self, call, status, before, after, **extra):
-        self.local.check()
+    def event(self, call, status, before, after, /, **extra):
+        verified = self._verify(call)
+        self._check_extra(extra)
+        return self._commit(verified, status, before, after, extra)
+
+    def _commit(self, verified, status, before, after, extra):
+        self.require_open()
+        require(type(verified) is _VerifiedCall and any(
+            verified['record'] is r for r in self._allocations), 'PRIVATE_VERIFIED_CALL')
+        call = verified['record']['handle']
         cid = call['call_id']
         require(status in {'STARTED', 'RETURNED', 'FAILED', 'REJECTED'}, 'UNKNOWN_STATUS')
         current_parent = self.stack[-1]['call_id'] if self.stack else None
@@ -136,7 +269,7 @@ class NestedJournal:
                     'DUPLICATE_CALL_OR_PARENT')
         else:
             require(self.states.get(cid) == 'STARTED' and self.stack and
-                    self.stack[-1] == call, 'CALL_NOT_LIFO_OR_TERMINATED')
+                    self.stack[-1] is call, 'CALL_NOT_LIFO_OR_TERMINATED')
         event = dict(call, event_kind='RESOURCE_CALL', status=status,
                      scientific_execution='LOCAL_DEV_MODEL',
                      budget_before=deepcopy(before), budget_after=deepcopy(after), **extra)
@@ -149,6 +282,14 @@ class NestedJournal:
                  **call, budget_before=before, budget_after=after,
                  resource_state='UNRECONCILED')
             raise
+        try:
+            self._credentials.append(CommitCredential(self, self._factory_token,
+                (('allocation', verified['record']), ('snapshot', verified['snapshot']),
+                 ('status', status), ('sequence', result['sequence']),
+                 ('digest', result['digest']))))
+        except BaseException:
+            self.poisoned, self.state = True, 'POISONED'
+            raise
         self.states[cid] = status
         if status == 'STARTED':
             self.stack.append(call)
@@ -162,10 +303,26 @@ class NestedJournal:
                    row['event']['status'] == 'STARTED' for row in self.local.records())
 
     def audit(self):
+        resource_rows = [row for row in self.local.records()
+                         if row['event'].get('event_kind') == 'RESOURCE_CALL']
+        require(len(resource_rows) == len(self._credentials), 'COMMIT_CREDENTIAL_COUNT')
+        for row, credential in zip(resource_rows, self._credentials):
+            require(row['sequence'] == credential['sequence'] and
+                    row['digest'] == credential['digest'], 'COMMIT_CREDENTIAL_ORDER')
+            record = credential['allocation']
+            require(any(record is original for original in self._allocations),
+                    'ORPHAN_COMMIT_CREDENTIAL')
+            self._validate_id(row['event'].get('call_id'))
+            require(all(row['event'].get(k) == v for k, v in credential['snapshot'])
+                    and record['snapshot'] == credential['snapshot'],
+                    'ALLOCATED_IDENTITY_MISMATCH')
+            require(row['event'].get('status') == credential['status'],
+                    'COMMITTED_STATUS_MISMATCH')
         active, seen, states = [], {}, {}
         for row in self.local.records():
             e = row['event']
-            require(e['event_kind'] == 'RESOURCE_CALL', 'UNKNOWN_EVENT_KIND')
+            if e.get('event_kind') != 'RESOURCE_CALL':
+                continue
             cid, status = e['call_id'], e['status']
             require(cid.startswith(self.local.attempt_id + ':'), 'FOREIGN_CALL_ID')
             actual = e['actual_category']
@@ -200,6 +357,7 @@ class NestedJournal:
             states[cid] = status
         require(not active, 'UNCLOSED_CALLS')
         require(all(v == 'RETURNED' for v in states.values()), 'FAILED_OR_REJECTED_CALLS')
+        require(not self.poisoned, 'NESTED_JOURNAL_POISONED')
         return dict(status='PASS', calls=len(seen))
 
 
@@ -207,11 +365,13 @@ class ModelJournal:
     def __init__(self, nested):
         self.nested = nested
 
-    def event(self, call, status, before, after, **extra):
+    def event(self, call, status, before, after, /, **extra):
+        verified = self.nested._verify(call)
+        self.nested._check_extra(extra)
         require(call['actual_category'] in MODEL_MAP and
                 call['model_category'] == MODEL_MAP[call['actual_category']], 'MODEL_MAPPING')
         mapped_before = {MODEL_MAP[k]: v for k, v in before.items()}
         mapped_after = {MODEL_MAP[k]: v for k, v in after.items()}
-        return self.nested.event(call, status, mapped_before, mapped_after,
-                                 actual_budget_before=deepcopy(before),
-                                 actual_budget_after=deepcopy(after), **extra)
+        metadata = dict(extra, actual_budget_before=deepcopy(before),
+                        actual_budget_after=deepcopy(after))
+        return self.nested._commit(verified, status, mapped_before, mapped_after, metadata)
diff --git a/research/non_oracle/local_dev/resources.py b/research/non_oracle/local_dev/resources.py
index c5654b4..9e46003 100644
--- a/research/non_oracle/local_dev/resources.py
+++ b/research/non_oracle/local_dev/resources.py
@@ -35,6 +35,7 @@ class AuditedDurableResourceLedger(ResourceLedger):
         self.integrity_check = checked
 
     def invoke(self, category, fn, *args, **kwargs):
+        self.model.nested.require_open()
         self.integrity_check()
         require(category in CALL_TYPES, 'UNKNOWN_RESOURCE_CATEGORY')
         call = self.model.nested.allocate(CALL_TYPES[category], category, MODEL_MAP[category])
@@ -82,6 +83,7 @@ class IndependentRecorder:
         return usage
 
     def invoke(self, fn, *args, logical_allowed=True, prepare=None, **kwargs):
+        self.nested.require_open()
         self.integrity_check()
         usage = self.reconcile()
         call = self.nested.allocate(self.call_type)
@@ -128,6 +130,8 @@ class Budget:
         self.ledger, self.r, self.assignment = ledger, r, assignment
         self.provenance, self.directory, self.branch = provenance, Path(directory), None
         self.halted = False
+        self.state = 'OPEN'
+        self.finalization_report = None
         from research.cooperative_sensing import estimator
         from research.non_oracle import policy, stfbs_d1a_model
         from scipy import optimize
@@ -137,6 +141,8 @@ class Budget:
         self.est, self.solver, self.exact = estimator.estimate, estimator.least_squares, policy.solve
 
     def check(self):
+        require(self.state == 'OPEN', 'BUDGET_FINALIZED_OR_FINALIZING')
+        self.nested.require_open()
         require(not self.halted, 'BUDGET_FAIL_STOP')
         self.local.records()
         for category, call_type in CALL_TYPES.items():
@@ -199,11 +205,50 @@ class Budget:
         with patch.object(estimator, 'least_squares', real):
             yield
 
+    def finalize(self, *, success=True):
+        """Irreversible, best-effort failure enclosure independent of file health."""
+        require(self.state not in {'FINALIZED_PASS', 'FINALIZED_FAILED', 'FINALIZING'},
+                'BUDGET_FINALIZATION_IRREVERSIBLE')
+        self.state = 'FINALIZING'
+        if self.nested.state not in {'FINALIZED_PASS', 'FINALIZED_FAILED'}:
+            self.nested.state = 'FINALIZING'
+        failures = []
+        if not success or self.halted or self.nested.poisoned:
+            failures.append(dict(check='EXECUTION_OUTCOME', error='FAILED_OR_POISONED'))
+        def perform(name, operation):
+            try:
+                return operation()
+            except BaseException as exc:
+                failures.append(dict(check=name, error=type(exc).__name__, message=str(exc)))
+                return None
+        def reconcile_wls():
+            for category, call_type in CALL_TYPES.items():
+                require(self.ledger.counts[category] == self.nested.committed_usage(call_type),
+                        'WLS_RUNTIME_COUNTER_RECONCILIATION')
+        perform('WLS_RECONCILIATION', reconcile_wls)
+        perform('R_RECONCILIATION', self.r.reconcile)
+        perform('ASSIGNMENT_RECONCILIATION', self.assignment.reconcile)
+        # Do not skip sealing a healthy Journal because resource checks failed.
+        perform('LOCAL_JOURNAL_SEAL', self.local.seal)
+        perform('NESTED_IDENTITY_AND_LIFECYCLE_AUDIT', self.nested.audit)
+        terminal = 'FINALIZED_FAILED' if failures else 'FINALIZED_PASS'
+        self.state = self.nested.state = terminal
+        self.halted = terminal == 'FINALIZED_FAILED'
+        self.finalization_report = dict(state=terminal, failures=failures,
+                                        local_invalid=self.local.invalid,
+                                        local_sealed=self.local.sealed)
+        perform('LOCAL_JOURNAL_CLOSE', self.local.close)
+        if failures:
+            self.state = self.nested.state = 'FINALIZED_FAILED'
+            raise RuntimeError('BUDGET_FINALIZED_FAILED: ' + repr(failures))
+        return self.finalization_report
+
 
 @contextmanager
 def initialized_budget(path, task_id, attempt_id, provenance):
     """Caller constructs Branch only inside this protected context; never an attempt factory."""
     local = None
+    budget = None
     try:
         local = LocalJournal(path, task_id, attempt_id, 268435456)
         nested = NestedJournal(local)
@@ -219,7 +264,20 @@ def initialized_budget(path, task_id, attempt_id, provenance):
         budget = Budget(local, nested, model, ledger, r, assignment, provenance, Path(path).parent)
         owner.append(budget)
         yield budget
+        budget.finalize()
     except BaseException as exc:
+        if budget is not None and budget.state not in {'FINALIZED_PASS', 'FINALIZED_FAILED'}:
+            try:
+                budget.finalize(success=False)
+            except BaseException as final_exc:
+                emit(task_id, attempt_id, 'FAILED_FINALIZATION', final_exc,
+                     resource_state='UNRECONCILED' if local and local.invalid else 'UNKNOWN')
+        elif local is not None and not local.invalid and not local.sealed:
+            try:
+                local.seal()
+            except BaseException as seal_exc:
+                emit(task_id, attempt_id, 'FAILED_INITIALIZATION_SEAL', seal_exc,
+                     resource_state='UNRECONCILED')
         emit(task_id, attempt_id, 'INITIALIZATION_OR_EXECUTION', exc,
              resource_state='UNRECONCILED' if local and local.invalid else 'UNKNOWN')
         raise
