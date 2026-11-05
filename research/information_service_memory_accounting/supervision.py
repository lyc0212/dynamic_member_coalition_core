"""One fixed eleven-job 240/480 account; frozen guardian owns all children."""
from copy import deepcopy
import os
from pathlib import Path
import time

from research.information_service_bridge import guardian
from research.information_service_online.supervision import _SUPERVISION_LOCK
from research.information_service_future_profile.supervision import _validate_starts, _validate_return
from .common import (ENTRY, ORDER, MemoryAccountingError, require, read_json,
                     save_json, sha_file)

ADAPTER_ID = 'gq_memory_accounting_supervision_v1'
RECEIPT_NAME = 'memory_supervision_receipt.json'
_RUNS = {}


class SupervisionError(MemoryAccountingError):
    def __init__(self, code, guardian_result=None, **details):
        self.guardian_result = guardian_result
        super().__init__(code, **details)


def register_run(attempt_id, started, deadline):
    require(attempt_id not in _RUNS and deadline == started + 480., 'RUN_CHAIN_REUSE_OR_DEADLINE')
    _RUNS[attempt_id] = dict(owner=os.getpid(), started=started, deadline=deadline,
                            pairs=[], cumulative=0.0, stopped=False, previous=None)


def run_pair(job, out, deadline, cumulative):
    starts = _validate_starts(job)
    state = _RUNS[job['attempt_id']]
    require(state['owner'] == os.getpid() and not state['stopped'], 'STOPPED_OR_FOREIGN_RUN')
    require(state['deadline'] == deadline and state['cumulative'] == cumulative, 'RESOURCE_CHAIN_RESET')
    require(len(state['pairs']) < 11 and job['pair_id'] == ORDER[len(state['pairs'])], 'JOB_ORDER')
    require(cumulative < 240. and time.monotonic() < deadline - 5., 'NO_RESOURCE_BUDGET')
    out = Path(out).resolve()
    require(not out.exists() or not any(out.iterdir()), 'NO_PAIR_RETRY')
    out.mkdir(parents=True, exist_ok=True)
    receipt_file = out / RECEIPT_NAME
    result, error = None, None
    with _SUPERVISION_LOCK:
        old = guardian.DEFAULT_LIMITS
        before = deepcopy(old)
        require(before['cleanup_reserve'] == 5., 'CLEANUP_RESERVE_CHANGED')
        effective = dict(old, total_cpu=240., pair_cpu=60., pair_wall=120.)
        receipt = dict(adapter_id=ADAPTER_ID, attempt_id=job['attempt_id'], pair_id=job['pair_id'],
            status='DELEGATING', absolute_deadline=deadline, original_global_deadline=deadline,
            original_started_monotonic=state['started'], cumulative_before=cumulative,
            cumulative_after=None, job_ordinal=len(state['pairs'])+1,
            previous_receipt=deepcopy(state['previous']), effective_limits=None,
            requested_effective_limits=effective, defaults_before=before,
            defaults_restored=False, default_object_identity_preserved=False,
            guardian_returned=False, START_prechecks=starts, validation_errors=[],
            process_owner='frozen guardian creates/signals/wait4 only', guardian_CPU_subset_of_launcher=True)
        save_json(receipt_file, receipt)
        state['pairs'].append(job['pair_id'])
        guardian.DEFAULT_LIMITS = effective
        try:
            result = guardian.run_pair(job, out, ENTRY, deadline, cumulative)
        except BaseException as caught:
            error = caught
            receipt['delegate_exception'] = dict(type=type(caught).__name__, error=str(caught))
        finally:
            guardian.DEFAULT_LIMITS = old
            restored = guardian.DEFAULT_LIMITS is old and guardian.DEFAULT_LIMITS == before
            receipt.update(defaults_restored=restored, default_object_identity_preserved=restored,
                           defaults_after=deepcopy(guardian.DEFAULT_LIMITS), guardian_returned=result is not None)
        if result is None and (out/'guardian_result.json').is_file():
            try:
                result = read_json(out/'guardian_result.json')
            except BaseException as read_error:
                receipt['guardian_read_error'] = str(read_error)
        errors, audit = ['FINAL_ACCOUNTING_UNKNOWN'], None
        if isinstance(result, dict):
            try:
                errors, audit = _validate_return(result, job, cumulative, effective, restored)
                records = result.get('processes', [])
                physical = [(r.get('pid'), r.get('start_ticks')) for r in records]
                if len(records) != 3 or len(set(physical)) != 3:
                    errors.append('PHYSICAL_PROCESS_COVERAGE')
                if sorted(r.get('role','') for r in records) != ['controller','env','sense']:
                    errors.append('ROLE_COVERAGE')
                if (out/'guardian_result.json').is_file():
                    if read_json(out/'guardian_result.json') != result:
                        errors.append('SAVED_GUARDIAN_DIFFERS')
                    receipt['guardian_result_sha256'] = sha_file(out/'guardian_result.json')
                else:
                    errors.append('SAVED_GUARDIAN_MISSING')
                if time.monotonic() > deadline and result.get('passed'):
                    errors.append('DEADLINE_AFTER_RETURN')
            except BaseException as validation:
                errors.append('FINAL_VALIDATION_EXCEPTION:' + str(validation))
            receipt.update(cumulative_after=result.get('cumulative_after'), effective_limits=result.get('limits'),
                           raw_guardian_passed=result.get('passed'))
        receipt.update(final_records_audit=audit, validation_errors=errors,
                       status='RETURNED_VALIDATED' if not errors and error is None else 'RETURNED_REJECTED')
        state['stopped'] = bool(errors or error is not None or not result or not result.get('passed'))
        if not errors and result is not None:
            state['cumulative'] = result['cumulative_after']
        try:
            save_json(receipt_file, receipt)
            state['previous'] = dict(path=str(receipt_file), sha256=sha_file(receipt_file),
                                     cumulative_after=receipt.get('cumulative_after'), pair_id=job['pair_id'])
        except BaseException as persist_error:
            state['stopped'] = True
            raise SupervisionError('SUPERVISION_PERSISTENCE_FAILED', result, error=str(persist_error)) from persist_error
        if errors or error is not None:
            raise SupervisionError('SUPERVISION_FAILED', result, errors=errors,
                                   delegate_error=None if error is None else str(error))
        return result
