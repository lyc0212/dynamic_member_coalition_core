"""Predeclared synthetic admission jobs: no NumPy, WLS, or model execution.

Root freezes gate_jobs and source before running them.  Negative process
outcomes remain failures in guardian evidence; validate_gate separately checks
whether the intended refusal/termination and complete accounting occurred.
"""
import argparse
import copy
import os
from pathlib import Path
import resource
import signal
import struct
import subprocess
import sys
import time

from .common import ContractError, digest, save_json
from .wire import WireClient


def _no_children(event, args):
    if event in ('subprocess.Popen', 'os.fork', 'os.forkpty', 'os.posix_spawn', 'os.posix_spawnp', 'os.system'):
        raise ContractError('Synthetic worker child creation denied')


def _busy(seconds):
    until = time.process_time() + seconds
    while time.process_time() < until:
        pass


def _idle():
    while True:
        time.sleep(0.05)


def _synthetic_frame(mode):
    frame = dict(contract_id='SYNTHETIC-NO-ESTIMATOR', stream_id='synthetic-stream',
                 frame_id='synthetic-0', tick=0, target_id=0,
                 measurement_time=0.0, available_time=0.0, records=[])
    if mode == 'backpressure':
        # Deliberately artificial transport data, not a scientific measurement.
        frame['synthetic_padding'] = 'x' * (1024 * 1024)
    return frame


def synthetic_worker(args):
    """Root dispatches only when the explicit --synthetic MODE is present."""
    mode = args.synthetic
    resource.setrlimit(resource.RLIMIT_CPU, (5, 6))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    sys.addaudithook(_no_children)
    if args.role == 'controller' and mode != 'controller_hang':
        from .controller import worker
        return worker(args)
    client = WireClient(args.fd)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        if mode == 'ready_failure' and args.role == 'sense':
            _idle()
        client.send(dict(type='READY', role=args.role, pid=os.getpid()))
        message = client.recv(timeout=10)
        if message.get('type') != 'START':
            raise ContractError('Synthetic worker expected START')
        if args.role == 'controller':
            os.kill(os.getpid(), signal.SIGSTOP)
            _idle()
        if mode == 'cpu_both':
            _busy(0.65)
        elif mode == 'cpu_env' and args.role == 'env':
            _busy(2.0)
        elif mode == 'pair_wall':
            _idle()
        if args.role == 'sense' and mode == 'backpressure':
            _idle()  # Do not read the large queued SENSE request.
        while True:
            message = client.recv(timeout=10)
            kind = message.get('type')
            if kind == 'STOP':
                if mode == 'stop_no_ack' and args.role == 'sense':
                    _idle()
                if mode == 'eof_after_stop' and args.role == 'sense':
                    os._exit(0)
                save_json(out / 'synthetic_result.json', dict(synthetic=True, mode=mode,
                                                              role=args.role, passed=True))
                client.send(dict(type='STOP_ACK', role=args.role))
                return 0
            if args.role == 'sense' and kind == 'SENSE':
                identity = message['identity']
                if mode == 'no_response':
                    _idle()
                if mode == 'half_response':
                    client.socket.send(struct.pack('!I', 100) + b'{"type":')
                    _idle()
                if mode in ('eof_zero', 'eof_before_stop'):
                    os._exit(0)
                if mode == 'eof_nonzero':
                    os._exit(7)
                if mode == 'child_guard':
                    try:
                        subprocess.Popen([sys.executable, '-c', 'pass'])
                    except ContractError:
                        client.send(dict(type='TEST_EVENT', detail=dict(child_denied=True)))
                    else:
                        raise ContractError('Synthetic child guard did not reject Popen')
                reply_identity = dict(identity)
                if mode == 'wrong_identity':
                    reply_identity['global_tick'] += 1
                elif mode == 'wrong_target':
                    reply_identity['target_id'] += 1
                elif mode == 'wrong_hash':
                    reply_identity['payload_sha256'] = '0' * 64
                reply = dict(type='SENSE_RESULT', identity=reply_identity,
                             result=dict(synthetic=True, estimator_calls=0, value='fixed'))
                client.send(reply)
                if mode in ('duplicate_same', 'duplicate_conflict'):
                    duplicate = copy.deepcopy(reply)
                    if mode == 'duplicate_conflict':
                        duplicate['result']['value'] = 'conflict'
                    client.send(duplicate)
            elif args.role == 'env' and kind == 'STEP':
                frame = _synthetic_frame(mode)
                body = dict(frame=frame, allowed_sensor_ids=[], start_tick=0)
                identity = dict(attempt_id=args.attempt_id, pair_id=args.pair_id,
                                sense_request_id='sense:synthetic:0:0', target_id=0,
                                stream_id=frame['stream_id'], global_tick=0,
                                payload_sha256=digest(body))
                client.send(dict(type='AUTHORIZE', identity=identity))
                authorized = client.recv(timeout=10)
                if authorized.get('type') != 'AUTHORIZED' or authorized.get('identity') != identity:
                    raise ContractError('Synthetic authorization mismatch')
                client.send(dict(type='SENSE', identity=identity, **body))
                response = client.recv(timeout=10)
                if response.get('type') != 'SENSE_RESULT' or response.get('identity') != identity:
                    raise ContractError('Synthetic response identity mismatch')
                client.send(dict(type='SENSE_ACK', identity=identity))
                result = dict(synthetic=True, state_after=dict(tick=20, status=['completed'],
                              last_assignment=[dict(target=None, role='none')] * 3))
                client.send(dict(type='STEP_RESULT', request_id=message['request_id'], result=result))
                client.send(dict(type='ENV_DONE', result=dict(passed=True, synthetic=True, mode=mode,
                                                              committed_ticks=[0], WLS_calls=0)))
            else:
                raise ContractError('Unexpected synthetic role/message combination')
    finally:
        client.close()


def gate_jobs(attempt_id):
    """All admission variants are fixed before the first run; no search/retry."""
    definitions = [
        ('R01_NORMAL', 'normal', True, {}, None),
        ('R02_BACKPRESSURE', 'backpressure', False, dict(request=0.60), 'backpressure'),
        ('R03_NO_RESPONSE', 'no_response', False, dict(request=0.40), None),
        ('R03_HALF_RESPONSE', 'half_response', False, dict(request=0.80, partial=0.25), 'partial'),
        ('R04_WRONG_IDENTITY', 'wrong_identity', False, {}, None),
        ('R04_WRONG_TARGET', 'wrong_target', False, {}, None),
        ('R04_WRONG_HASH', 'wrong_hash', False, {}, None),
        ('R04_IDENTICAL_DUPLICATE', 'duplicate_same', True, {}, 'duplicate_response'),
        ('R04_CONFLICTING_DUPLICATE', 'duplicate_conflict', False, {}, None),
        ('R05_EOF_ZERO', 'eof_zero', False, {}, 'zero_exit'),
        ('R05_EOF_NONZERO', 'eof_nonzero', False, {}, 'nonzero_exit'),
        ('R06_SUM_CPU', 'cpu_both', False, dict(pair_cpu=1.0), 'cpu_sum'),
        ('R07_ONE_CPU', 'cpu_env', False, dict(pair_cpu=0.50), None),
        ('R07_PAIR_WALL', 'pair_wall', False,
         dict(pair_wall=0.8, cleanup_reserve=0.30, term_grace=0.05), None),
        ('R08_SECOND_POPEN', 'second_spawn_failure', False, {}, 'partial_spawn'),
        ('R09_PUBLICATION_GAP', 'coordinator_publication_gap', False, {}, 'publication_gap'),
        ('R10_REGISTRY_FAILURE', 'registry_failure', False, {}, 'registry_failure'),
        ('R10_READY_FAILURE', 'ready_failure', False, dict(startup=0.50), None),
        ('R10_CONTROLLER_HANG', 'controller_hang', False, dict(heartbeat=0.50), None),
        ('R10_CONTROLLER_SHUTDOWN_EXIT', 'controller_shutdown_exit', False, {}, 'controller_shutdown_exit'),
        ('R11_STOP_NO_ACK', 'stop_no_ack', False, dict(stop_ack=0.30), None),
        ('R11_EOF_BEFORE_STOP', 'eof_before_stop', False, {}, 'zero_exit'),
        ('R11_EOF_AFTER_STOP', 'eof_after_stop', False, {}, 'eof_after_stop'),
        ('R12_CHILD_AND_ACCOUNTING', 'child_guard', True, {}, 'accounting'),
    ]
    jobs = []
    for name, mode, success, overrides, postcheck in definitions:
        limits = dict(pair_cpu=4.0, pair_wall=6.0, startup=2.0, request=1.0,
                      partial=1.0, heartbeat=1.0, stop_ack=0.60,
                      term_grace=0.10, cleanup_reserve=1.0)
        limits.update(overrides)
        jobs.append(dict(name=name, attempt_id=str(attempt_id), pair_id=name,
                         synthetic=dict(mode=mode), limits=limits,
                         env_start=dict(mode=mode), sense_start=dict(mode=mode),
                         controller_start=dict(steps=[dict(request_id='synthetic-step-0',
                             expected_start_tick=0,
                             actions=[dict(target=None, role='none') for _ in range(3)])]),
                         expected=dict(guardian_success=success, postcheck=postcheck,
                                       no_WLS=True, gate_id=name.split('_', 1)[0])))
    return jobs


def validate_gate(result, job):
    """Pure post-hoc admission decision; never modifies actual final CPU data."""
    from .guardian import audit_final_records
    mode = job['synthetic']['mode']
    failure = result.get('failure') or {}
    rows = [row for row in result['processes'] if row.get('created')]
    checks = dict(
        expected_success_state=bool(result['passed']) == bool(job['expected']['guardian_success']),
        accounting_complete=bool(result['accounting_complete']),
        all_created_reaped=bool(result['all_reaped']) and all(row.get('reaped') for row in rows),
        no_live_created_child=all(not row.get('live_after_reap') for row in rows),
        no_orphan_record=not result.get('orphan_records'),
    )
    expected_kinds = {
        'backpressure': {'REQUEST_TIMEOUT'}, 'no_response': {'REQUEST_TIMEOUT'},
        'half_response': {'PARTIAL_FRAME_TIMEOUT', 'REQUEST_TIMEOUT'},
        'wrong_identity': {'IPC_CONTRACT_FAILURE'},
        'wrong_target': {'IPC_CONTRACT_FAILURE'}, 'wrong_hash': {'IPC_CONTRACT_FAILURE'},
        'duplicate_conflict': {'IPC_CONTRACT_FAILURE'},
        'eof_zero': {'UNEXPECTED_EOF', 'UNEXPECTED_EXIT'},
        'eof_nonzero': {'UNEXPECTED_EOF', 'NONZERO_EXIT'},
        'cpu_both': {'PAIR_CPU_LIMIT'}, 'cpu_env': {'PAIR_CPU_LIMIT'},
        'pair_wall': {'WORK_WALL_LIMIT'},
        'second_spawn_failure': {'START_OR_GUARDIAN_FAILURE'},
        'coordinator_publication_gap': {'START_OR_GUARDIAN_FAILURE'},
        'registry_failure': {'START_OR_GUARDIAN_FAILURE'},
        'ready_failure': {'STARTUP_TIMEOUT'},
        'controller_hang': {'CONTROLLER_HEARTBEAT_TIMEOUT'},
        'controller_shutdown_exit': {'UNEXPECTED_EOF', 'NONZERO_EXIT'},
        'stop_no_ack': {'STOP_ACK_TIMEOUT'},
        'eof_before_stop': {'UNEXPECTED_EOF', 'UNEXPECTED_EXIT'},
        'eof_after_stop': {'UNEXPECTED_EOF', 'UNEXPECTED_EXIT'},
    }
    if mode in expected_kinds:
        checks['expected_failure_class'] = failure.get('kind') in expected_kinds[mode]
    post = job['expected'].get('postcheck')
    detail = {}
    by_role = {row['role']: row for row in result['processes']}
    if post == 'backpressure':
        checks['queued_large_payload'] = by_role.get('sense', {}).get('ipc', {}).get('max_queued_bytes', 0) > 65536
        checks['monitor_continued'] = len(result.get('samples', [])) >= 2
    elif post == 'partial':
        checks['partial_response_seen'] = by_role.get('sense', {}).get('ipc', {}).get('partial_at_finish', False)
    elif post == 'duplicate_response':
        checks['duplicate_was_ignored'] = any(e['type'] == 'DUPLICATE_RESPONSE_IGNORED' for e in result['messages'])
        checks['one_request_committed'] = result.get('completed_sense_requests') == 1
    elif post == 'zero_exit':
        checks['sense_exit_really_zero'] = by_role.get('sense', {}).get('returncode') == 0
    elif post == 'nonzero_exit':
        checks['sense_exit_really_nonzero'] = by_role.get('sense', {}).get('returncode') == 7
    elif post == 'controller_shutdown_exit':
        checks['coordinator_closed_without_ack'] = (by_role.get('controller', {}).get('stop_requested') and
            not by_role.get('controller', {}).get('stop_ack') and
            by_role.get('controller', {}).get('returncode') == 7)
    elif post == 'eof_after_stop':
        checks['sense_closed_after_stop_without_ack'] = (by_role.get('sense', {}).get('stop_requested') and
            not by_role.get('sense', {}).get('stop_ack') and by_role.get('sense', {}).get('returncode') == 0)
    elif post == 'cpu_sum':
        scientific = [row for row in rows if row['role'] in ('env', 'sense')]
        checks['both_consumed_cpu'] = len(scientific) == 2 and all(row['process_lifecycle_cpu'] > 0.10 for row in scientific)
        checks['each_below_one_second'] = all(row['process_lifecycle_cpu'] < 1.0 for row in scientific)
        checks['sum_triggered_one_second'] = result['worker_cpu'] >= 1.0
    elif post == 'partial_spawn':
        checks['first_scientific_child_owned'] = by_role.get('env', {}).get('created', False)
        checks['second_not_created'] = not by_role.get('sense', {}).get('created', False)
    elif post in ('publication_gap', 'registry_failure'):
        env = by_role.get('env', {})
        checks['unpublished_child_still_accounted'] = env.get('created', False) and env.get('reaped', False) and not any(
            h['state'] == 'REGISTERED' for h in env.get('history', []))
    elif post == 'accounting':
        checks['child_guard_rejected'] = any(e['type'] == 'SYNTHETIC_EVENT' and
                                             e.get('detail', {}).get('child_denied') for e in result['messages'])
        complete = copy.deepcopy(rows)
        baseline = audit_final_records(complete)
        duplicated = audit_final_records(complete + [copy.deepcopy(complete[0])])
        missing_rows = copy.deepcopy(complete)
        del missing_rows[0]['wait4_system_cpu']
        missing = audit_final_records(missing_rows)
        changed = copy.deepcopy(complete[0])
        changed['wait4_user_cpu'] += 0.125
        conflicting = audit_final_records(complete + [changed])
        checks['duplicate_final_not_double_counted'] = (duplicated['complete'] and
            duplicated['unique_entries'] == baseline['unique_entries'] and
            duplicated['worker_cpu'] == baseline['worker_cpu'] and duplicated['identical_duplicates'] == 1)
        checks['missing_final_classified_incomplete'] = not missing['complete']
        checks['conflicting_final_classified_incomplete'] = not conflicting['complete']
        detail['synthetic_accounting_only'] = dict(baseline=baseline, duplicate=duplicated,
                                                  missing=missing, conflict=conflicting)
    return dict(name=job['name'], passed=all(checks.values()), checks=checks, detail=detail,
                actual_guardian_passed=result['passed'], actual_failure=result.get('failure'),
                scientific_experiment=False, real_CPU_records_unchanged=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['worker'])
    parser.add_argument('--role', choices=['env', 'sense', 'controller'], required=True)
    parser.add_argument('--fd', type=int, required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--attempt-id', required=True)
    parser.add_argument('--pair-id', required=True)
    parser.add_argument('--synthetic', required=True)
    return synthetic_worker(parser.parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
