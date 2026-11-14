"""Unique child owner, nonblocking router, and wait4 lifecycle accountant.

This module contains no model or estimator imports.  The coordinator is a
separate directly owned child and cannot consume a scientific worker's wait4.
"""
from collections import Counter
import math
import os
from pathlib import Path
import selectors
import signal
import socket
import subprocess
import sys
import time

from .common import ContractError, POLL, digest, save_json
from .wire import Peer


DEFAULT_LIMITS = dict(pair_cpu=60.0, pair_wall=120.0, total_cpu=300.0,
                      startup=10.0, request=10.0, partial=10.0,
                      heartbeat=2.0, stop_ack=2.0, term_grace=0.5,
                      cleanup_reserve=5.0)
IDENTITY_FIELDS = frozenset(('attempt_id', 'pair_id', 'sense_request_id', 'target_id',
                            'stream_id', 'global_tick', 'payload_sha256'))
PUBLIC_FRAME_FIELDS = frozenset(('contract_id', 'stream_id', 'frame_id', 'tick', 'target_id',
                                'measurement_time', 'available_time', 'records'))
PUBLIC_RECORD_FIELDS = frozenset(('sensor_id', 'position', 'bearing', 'sigma', 'packet_id',
                                 'measurement_tick', 'available_tick', 'status'))
# In an unrecoverable kernel/accounting failure retain ownership objects rather
# than letting Popen.__del__ silently consume waitpid behind the guardian.
_UNREAPED_HANDLES = []


def proc_identity(pid):
    """Read Linux identity and own CPU without any child-reaping operation."""
    try:
        text = Path(f'/proc/{pid}/stat').read_text()
        fields = text.rsplit(')', 1)[1].split()
        return dict(start_ticks=int(fields[19]), pgid=int(fields[2]),
                    cpu=(int(fields[11]) + int(fields[12])) / os.sysconf('SC_CLK_TCK'),
                    state=fields[0])
    except (FileNotFoundError, ProcessLookupError):
        return None


def _identity_key(record):
    return tuple(record[k] for k in ('attempt_id', 'pair_id', 'role', 'pid', 'start_ticks', 'pgid'))


class FinalCPUBook:
    """Exactly-once final entries; missing/conflicting values are not zero."""
    def __init__(self):
        self.entries = {}
        self.errors = []
        self.identical_duplicates = 0

    def add(self, record):
        try:
            key = _identity_key(record)
            user, system = record['wait4_user_cpu'], record['wait4_system_cpu']
            if any(v is None or not isinstance(v, (int, float)) or
                   not math.isfinite(v) or v < 0 for v in (user, system)):
                raise ValueError('Missing/nonfinite final CPU')
            value = (float(user), float(system), record['returncode'])
        except (KeyError, ValueError, TypeError) as error:
            self.errors.append(dict(kind='ACCOUNTING_INCOMPLETE', message=str(error)))
            return False
        if key in self.entries:
            if self.entries[key] != value:
                self.errors.append(dict(kind='ACCOUNTING_INCOMPLETE', message='Conflicting duplicate final identity'))
                return False
            self.identical_duplicates += 1
            return False
        self.entries[key] = value
        return True

    def total(self, roles=('env', 'sense')):
        return math.fsum(value[0] + value[1] for key, value in self.entries.items() if key[2] in roles)


def audit_final_records(records):
    book = FinalCPUBook()
    for row in records:
        book.add(row)
    return dict(complete=not book.errors, errors=book.errors,
                unique_entries=len(book.entries), identical_duplicates=book.identical_duplicates,
                worker_cpu=book.total(), controller_cpu=book.total(('controller',)))


def _worker_env(out):
    temp = Path(out) / 'tmp'
    temp.mkdir(parents=True, exist_ok=True)
    return dict(PATH=os.environ.get('PATH', '/usr/bin:/bin'),
                LANG='C.UTF-8', LC_ALL='C.UTF-8', PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
                PYTHONDONTWRITEBYTECODE='1', PYTHONHASHSEED='0',
                OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
                NUMEXPR_NUM_THREADS='1',
                TMPDIR=str(temp), TEMP=str(temp), TMP=str(temp))


def run_pair(job, out, entry, deadline, cumulative=0.0):
    """Run one preregistered job; only this process Popen/wait4s its children.

    job: attempt_id, pair_id, env_start, sense_start, controller_start.
    entry: root script handling ``worker --role ... --fd ... --out ...``.
    deadline: absolute monotonic overall deadline, including cleanup.
    Synthetic jobs may supply ``synthetic={'mode':...}`` and smaller limits.
    Returned worker_cpu excludes coordinator and guardian CPU.
    """
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'guardian_result.json').exists() or (out / 'registry.json').exists():
        raise FileExistsError('Refusing an existing guardian job output')
    attempt, pair = str(job['attempt_id']), str(job['pair_id'])
    synthetic = job.get('synthetic')
    mode = synthetic.get('mode') if isinstance(synthetic, dict) else None
    if (job.get('sense_argv_extra') or job.get('sense_env_extra')) and not job.get('predeclared_isolation_probe'):
        raise ContractError('Private startup injection is restricted to declared isolation probes')
    limits = dict(DEFAULT_LIMITS)
    if job.get('limits'):
        if not synthetic:
            raise ContractError('Science resource limits may not be overridden')
        if set(job['limits']) - set(limits):
            raise ContractError('Unknown synthetic resource limit')
        limits.update(job['limits'])
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in limits.values()):
        raise ContractError('Positive finite guardian limits required')
    start, guardian_start_cpu = time.monotonic(), time.process_time()
    hard_deadline = min(start + limits['pair_wall'], float(deadline))
    work_deadline = hard_deadline - limits['cleanup_reserve']
    selector = selectors.DefaultSelector()
    children, records, events, samples = {}, [], [], []
    book = FinalCPUBook()
    failure = None
    pending = None
    completed_sense = {}
    pending_step = None
    started = False
    stopping = False
    stop_deadline = None
    cleanup_started = None
    kill_sent = False
    env_done = None
    last_heartbeat = None
    last_monitor = start
    max_monitor_interval = 0.0
    finalization_errors = []

    def event(kind, role=None, **details):
        row = dict(wall=time.monotonic() - start, type=kind, role=role)
        row.update(details)
        events.append(row)

    def persist_registry():
        save_json(out / 'registry.json', dict(attempt_id=attempt, pair_id=pair, processes=records))

    def fail(kind, message):
        nonlocal failure, cleanup_started
        if failure is None:
            failure = dict(kind=kind, message=str(message), wall=time.monotonic() - start)
            event('FAILURE', failure_kind=kind, message=str(message),
                  failure_wall=failure['wall'])
            cleanup_started = time.monotonic()

    def refresh(role):
        child = children[role]
        peer = child['peer']
        if peer.eof:
            try:
                selector.unregister(peer.socket)
            except KeyError:
                pass
            return
        mask = selectors.EVENT_READ | (selectors.EVENT_WRITE if peer.outgoing else 0)
        try:
            selector.modify(peer.socket, mask, role)
        except KeyError:
            selector.register(peer.socket, mask, role)

    def queue(role, message):
        if role not in children or children[role]['peer'].eof:
            raise EOFError('Destination unavailable: ' + role)
        children[role]['peer'].queue(message)
        refresh(role)

    def spawn(role):
        role_out = out / role
        role_out.mkdir(parents=True, exist_ok=False)
        record = dict(attempt_id=attempt, pair_id=pair, role=role, state='INTENT',
                      created=False, pid=None, start_ticks=None, pgid=None, ready=False,
                      stop_requested=False, stop_ack=False, reaped=False,
                      returncode=None, wait4_user_cpu=None, wait4_system_cpu=None,
                      history=[dict(state='INTENT', wall=time.monotonic() - start)])
        records.append(record)
        persist_registry()
        if mode == 'second_spawn_failure' and role == 'sense':
            record.update(state='NOT_CREATED', wait4_user_cpu=0.0, wait4_system_cpu=0.0)
            raise OSError('Fixed synthetic failure before second scientific Popen')
        parent_sock, child_sock = socket.socketpair()
        log = (role_out / 'stdout_stderr.log').open('x')
        command = [sys.executable, '-B', str(Path(entry).resolve()), 'worker', '--role', role,
                   '--fd', str(child_sock.fileno()), '--out', str(role_out),
                   '--attempt-id', attempt, '--pair-id', pair]
        if mode is not None:
            command += ['--synthetic', mode]
        environment = _worker_env(role_out)
        if role == 'sense' and job.get('predeclared_isolation_probe'):
            command += list(job.get('sense_argv_extra', []))
            environment.update(job.get('sense_env_extra', {}))
        try:
            proc = subprocess.Popen(command, pass_fds=(child_sock.fileno(),), close_fds=True,
                                    cwd=Path(__file__).resolve().parents[2],
                                    env=environment, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=True)
        except BaseException:
            parent_sock.close()
            child_sock.close()
            log.close()
            record.update(state='NOT_CREATED', wait4_user_cpu=0.0, wait4_system_cpu=0.0)
            raise
        # Ownership is retained BEFORE any publication or /proc operation.
        record.update(created=True, pid=proc.pid, state='SPAWNED', command=command)
        peer = Peer(parent_sock, partial_timeout=limits['partial'])
        children[role] = dict(proc=proc, peer=peer, log=log, record=record)
        child_sock.close()
        record['history'].append(dict(state='SPAWNED', wall=time.monotonic() - start))
        identity = proc_identity(proc.pid)
        if identity is None:
            raise RuntimeError('Cannot read newly owned process identity')
        record.update(start_ticks=identity['start_ticks'], pgid=identity['pgid'])
        if mode == 'coordinator_publication_gap' and role == 'env':
            os.kill(children['controller']['proc'].pid, signal.SIGKILL)
            raise RuntimeError('Synthetic coordinator death before env registry publication')
        if mode == 'registry_failure' and role == 'env':
            raise OSError('Fixed synthetic registry publication failure')
        record['state'] = 'REGISTERED'
        record['history'].append(dict(state='REGISTERED', wall=time.monotonic() - start))
        persist_registry()
        refresh(role)

    def validate_identity(identity):
        if not isinstance(identity, dict) or set(identity) != IDENTITY_FIELDS:
            raise ContractError('Exact sense response identity fields required')
        if identity['attempt_id'] != attempt or identity['pair_id'] != pair:
            raise ContractError('Sense request belongs to another attempt/pair')
        if any(isinstance(identity[k], bool) or not isinstance(identity[k], int) or identity[k] < 0
               for k in ('target_id', 'global_tick')):
            raise ContractError('Invalid public target/tick identity')
        if any(not isinstance(identity[k], str) or not identity[k]
               for k in ('sense_request_id', 'stream_id', 'payload_sha256')):
            raise ContractError('Invalid request/stream/hash identity')
        return digest(identity)

    def request_body(message):
        if message['type'] == 'SENSE':
            if set(message) != {'type', 'identity', 'frame', 'allowed_sensor_ids', 'start_tick'}:
                raise ContractError('Unexpected sense transport fields')
            body = {key: message[key] for key in ('frame', 'allowed_sensor_ids', 'start_tick')}
            frame = body['frame']
            if not synthetic:
                if not isinstance(frame, dict) or set(frame) != PUBLIC_FRAME_FIELDS:
                    raise ContractError('Private/unknown public frame fields')
                if not isinstance(frame['records'], list) or any(
                        not isinstance(row, dict) or set(row) != PUBLIC_RECORD_FIELDS
                        for row in frame['records']):
                    raise ContractError('Private/unknown measurement record fields')
            if any(frame.get(key) != message['identity'][identity_key] for key, identity_key in
                   (('tick', 'global_tick'), ('target_id', 'target_id'), ('stream_id', 'stream_id'))):
                raise ContractError('Public frame/transport identity mismatch')
            return body
        if message['type'] == 'ISOLATION_PROBE':
            if job.get('sense_start', {}).get('mode') != 'isolation_probe':
                raise ContractError('Isolation probe cannot run in a science sensor')
            if set(message) != {'type', 'identity', 'action', 'target'}:
                raise ContractError('Unexpected isolation probe fields')
            if message['action'] not in ('read', 'import'):
                raise ContractError('Unknown isolation probe action')
            return {key: message[key] for key in ('action', 'target')}
        raise ContractError('Unknown authorized request type')

    def on_message(role, message):
        nonlocal last_heartbeat, pending, pending_step, started, stopping, stop_deadline, env_done
        kind = message.get('type')
        row = children[role]['record']
        event('MESSAGE', role, message_type=kind,
              request_id=message.get('request_id', message.get('identity', {}).get('sense_request_id')))
        if kind == 'READY':
            if row['ready'] or message.get('role') != role:
                raise ContractError('Repeated or wrong READY role')
            row.update(ready=True, state='READY')
            row['history'].append(dict(state='READY', wall=time.monotonic() - start))
            if role == 'controller':
                last_heartbeat = time.monotonic()
            return
        if kind == 'HEARTBEAT' and role == 'controller':
            if not row['ready']:
                raise ContractError('Heartbeat before READY')
            last_heartbeat = time.monotonic()
            return
        if kind == 'STOP_ACK':
            if not stopping or not row['stop_requested'] or message.get('role') != role:
                raise ContractError('Unexpected STOP_ACK')
            row['stop_ack'] = True
            return
        if kind in ('CONTROL_ERROR', 'WORKER_ERROR', 'ERROR'):
            raise ContractError(f'{role} reported {kind}: {message.get("message", message.get("error"))}')
        if kind == 'TEST_EVENT' and synthetic:
            event('SYNTHETIC_EVENT', role, detail=message.get('detail'))
            return
        if kind == 'CONTROLLER_DONE' and role == 'controller' and started:
            # The final STEP_RESULT and STOP can reach the controller together.
            # Its script-complete notification is harmless during that close.
            row['script_done'] = True
            return
        if role == 'sense' and kind in ('SENSE_RESULT', 'ISOLATION_RESULT'):
            identity = message.get('identity')
            validate_identity(identity)
            old = completed_sense.get(identity['sense_request_id'])
            if old is not None:
                if old['identity'] != identity or old['response_digest'] != digest(message):
                    raise ContractError('Conflicting duplicate sense response')
                event('DUPLICATE_RESPONSE_IGNORED', role)
                return
        if not started or stopping:
            raise ContractError('Work message outside running phase')
        if role == 'controller' and kind == 'STEP':
            if pending_step is not None:
                raise ContractError('More than one outstanding step')
            if not isinstance(message.get('request_id'), str):
                raise ContractError('Missing step request identity')
            pending_step = message['request_id']
            queue('env', message)
            return
        if role == 'env' and kind == 'STEP_RESULT':
            if pending_step is None or message.get('request_id') != pending_step or pending is not None:
                raise ContractError('Step result identity/pending-sense mismatch')
            pending_step = None
            queue('controller', message)
            return
        if role == 'env' and kind == 'AUTHORIZE':
            identity = message.get('identity')
            fingerprint = validate_identity(identity)
            if pending is not None:
                if pending['identity'] != identity:
                    raise ContractError('Second outstanding sense request')
                queue('env', dict(type='AUTHORIZED', identity=identity, deadline=pending['deadline']))
                return
            if identity['sense_request_id'] in completed_sense:
                raise ContractError('Completed sense request identity cannot be reused')
            until = min(time.monotonic() + limits['request'], work_deadline)
            if until <= time.monotonic():
                raise TimeoutError('No request budget remains before cleanup')
            pending = dict(identity=dict(identity), fingerprint=fingerprint, deadline=until,
                           authorized=time.monotonic(), dispatched=False, result_sent=False)
            queue('env', dict(type='AUTHORIZED', identity=identity, deadline=until))
            return
        if role == 'env' and kind in ('SENSE', 'ISOLATION_PROBE'):
            validate_identity(message.get('identity'))
            if pending is None or pending['identity'] != message['identity']:
                raise ContractError('Sense payload was not authorized')
            body = request_body(message)
            if digest(body) != pending['identity']['payload_sha256']:
                raise ContractError('Authorized payload hash mismatch')
            if pending['dispatched']:
                event('DUPLICATE_REQUEST_IGNORED', role)
                return
            pending.update(dispatched=True, request_type=kind)
            queue('sense', message)
            return
        if role == 'sense' and kind in ('SENSE_RESULT', 'ISOLATION_RESULT'):
            identity = message.get('identity')
            validate_identity(identity)
            result_digest = digest(message)
            old = completed_sense.get(identity['sense_request_id'])
            if old is not None:
                if old['identity'] != identity or old['response_digest'] != result_digest:
                    raise ContractError('Conflicting duplicate sense response')
                event('DUPLICATE_RESPONSE_IGNORED', role)
                return
            if pending is None or pending['identity'] != identity or not pending['dispatched']:
                raise ContractError('Wrong target/tick/hash/request in sense response')
            expected_type = 'SENSE_RESULT' if pending['request_type'] == 'SENSE' else 'ISOLATION_RESULT'
            if kind != expected_type:
                raise ContractError('Wrong response type')
            if pending['result_sent']:
                if pending['response_digest'] != result_digest:
                    raise ContractError('Conflicting in-flight response')
                event('DUPLICATE_RESPONSE_IGNORED', role)
                return
            pending.update(result_sent=True, response_digest=result_digest)
            queue('env', message)
            return
        if role == 'env' and kind == 'SENSE_ACK':
            identity = message.get('identity')
            validate_identity(identity)
            if pending is None or pending['identity'] != identity or not pending['result_sent']:
                raise ContractError('Unexpected sense validation ACK')
            completed_sense[identity['sense_request_id']] = dict(
                identity=dict(identity), response_digest=pending['response_digest'])
            event('SENSE_ACKNOWLEDGED', role,
                  request_duration=time.monotonic() - pending['authorized'])
            pending = None
            return
        if role == 'env' and kind == 'ENV_DONE':
            if pending is not None or pending_step is not None or env_done is not None:
                raise ContractError('ENV_DONE with outstanding/duplicate work')
            env_done = message.get('result', {})
            stopping = True
            stop_deadline = min(time.monotonic() + limits['stop_ack'], hard_deadline)
            for dest, child in children.items():
                child['record'].update(stop_requested=True, state='STOP_REQUESTED')
                queue(dest, dict(type='STOP', attempt_id=attempt, pair_id=pair))
            return
        raise ContractError(f'Unexpected {kind!r} from {role}')

    def signal_owned(child, sig):
        row = child['record']
        if row['reaped']:
            return
        now_id = proc_identity(row['pid'])
        if now_id is None:
            return
        if row['start_ticks'] is not None and now_id['start_ticks'] != row['start_ticks']:
            fail('IDENTITY_CONFLICT', 'PID was reused before cleanup')
            return
        try:
            if now_id['pgid'] == row['pid']:
                os.killpg(now_id['pgid'], sig)
            else:
                os.kill(row['pid'], sig)
            event('SIGNAL', row['role'], signal=int(sig))
        except ProcessLookupError:
            pass

    def reap_ready():
        for child in children.values():
            row = child['record']
            if row['reaped']:
                continue
            try:
                got, status, usage = os.wait4(row['pid'], os.WNOHANG)
            except ChildProcessError:
                row.update(reaped=True, state='ACCOUNTING_INCOMPLETE', accounting_missing=True)
                child['proc'].returncode = -255
                book.errors.append(dict(kind='ACCOUNTING_INCOMPLETE', message='Unexpected ECHILD', role=row['role']))
                fail('ACCOUNTING_INCOMPLETE', 'Final wait4 unavailable for owned child')
                continue
            if not got:
                continue
            code = os.waitstatus_to_exitcode(status)
            child['proc'].returncode = code
            row.update(reaped=True, state='FINAL_ACCOUNTED', returncode=code,
                       wait4_user_cpu=usage.ru_utime, wait4_system_cpu=usage.ru_stime,
                       process_lifecycle_cpu=usage.ru_utime + usage.ru_stime,
                       reaped_wall=time.monotonic() - start)
            row['history'] += [dict(state='EXIT_OBSERVED', wall=time.monotonic() - start),
                               dict(state='REAPED', wall=time.monotonic() - start),
                               dict(state='FINAL_ACCOUNTED', wall=time.monotonic() - start)]
            book.add(row)
            if code != 0 and failure is None:
                fail('NONZERO_EXIT', f'{row["role"]} exited {code}')
            # Zero exit is judged after its buffered messages/EOF are drained.

    try:
        if work_deadline <= start:
            raise TimeoutError('Insufficient overall time for cleanup reserve')
        for role in ('controller', 'env', 'sense'):
            spawn(role)
        while True:
            now = time.monotonic()
            max_monitor_interval = max(max_monitor_interval, now - last_monitor)
            last_monitor = now
            live = {}
            for role, child in children.items():
                row = child['record']
                item = None if row['reaped'] else proc_identity(row['pid'])
                if item is not None:
                    if item['start_ticks'] != row['start_ticks']:
                        fail('IDENTITY_CONFLICT', 'Live PID identity changed')
                    live[role] = item['cpu']
            interim = book.total() + math.fsum(v for role, v in live.items() if role in ('env', 'sense'))
            samples.append(dict(wall=now - start, worker_cpu=interim, live_cpu=live,
                                final_worker_cpu=book.total(), cumulative_worker_cpu=cumulative + interim))
            if failure is None:
                if interim >= limits['pair_cpu']:
                    fail('PAIR_CPU_LIMIT', 'Sum of live plus exited worker CPU reached pair limit')
                elif cumulative + interim >= limits['total_cpu']:
                    fail('TOTAL_CPU_LIMIT', 'Cumulative worker CPU reached overall limit')
                elif now >= work_deadline and not stopping:
                    fail('WORK_WALL_LIMIT', 'Work deadline reached; cleanup reserve begins')
                elif not started and now >= min(start + limits['startup'], work_deadline):
                    fail('STARTUP_TIMEOUT', 'All children did not become READY')
                elif pending is not None and now >= pending['deadline']:
                    fail('REQUEST_TIMEOUT', 'Authorized request deadline includes the response ACK')
                elif last_heartbeat is not None and not stopping and now - last_heartbeat >= limits['heartbeat']:
                    fail('CONTROLLER_HEARTBEAT_TIMEOUT', 'Coordinator heartbeat missing')
                elif stopping and now >= stop_deadline and not all(c['record']['stop_ack'] for c in children.values()):
                    fail('STOP_ACK_TIMEOUT', 'Bounded STOP acknowledgment deadline')
                for child in children.values():
                    try:
                        child['peer'].check_partial_deadline(now)
                    except TimeoutError as error:
                        fail('PARTIAL_FRAME_TIMEOUT', error)
            if failure is not None and cleanup_started is not None:
                if not any(c['record'].get('term_sent') for c in children.values()):
                    for child in children.values():
                        child['peer'].outgoing.clear()
                        child['peer'].out_offset = child['peer'].queued_bytes = 0
                        refresh(child['record']['role'])
                        signal_owned(child, signal.SIGTERM)
                        child['record']['term_sent'] = True
                if not kill_sent and (now >= cleanup_started + limits['term_grace'] or now >= hard_deadline):
                    for child in children.values():
                        signal_owned(child, signal.SIGKILL)
                    kill_sent = True
            if failure is None and not started and all(c['record']['ready'] for c in children.values()):
                started = True
                for role in ('env', 'sense', 'controller'):
                    queue(role, dict(type='START', payload=job.get(role + '_start', {})))
                event('STARTED')
            # Always drain readable sockets before interpreting a zero exit.
            for key, mask in selector.select(POLL):
                role, child = key.data, children[key.data]
                peer = child['peer']
                try:
                    if mask & selectors.EVENT_READ:
                        messages = peer.read_ready()
                        for message in messages:
                            if failure is None:
                                on_message(role, message)
                        if peer.eof and failure is None and not child['record']['stop_ack']:
                            fail('UNEXPECTED_EOF', f'{role} EOF before authorized STOP_ACK')
                    if failure is None and mask & selectors.EVENT_WRITE and peer.outgoing:
                        peer.write_ready()
                    refresh(role)
                except BaseException as error:
                    fail('IPC_CONTRACT_FAILURE', f'{role}: {type(error).__name__}: {error}')
                    if peer.eof:
                        refresh(role)
            reap_ready()
            if all(c['record']['reaped'] for c in children.values()):
                if failure is not None:
                    break
                if all(c['peer'].eof for c in children.values()):
                    if not stopping or env_done is None or not all(c['record']['stop_ack'] for c in children.values()):
                        fail('UNEXPECTED_EXIT', 'Children exited without complete normal close')
                    break
            if time.monotonic() >= hard_deadline:
                fail('HARD_WALL_LIMIT', 'Original wall deadline reached during shutdown')
                for child in children.values():
                    signal_owned(child, signal.SIGKILL)
                reap_ready()
                break
    except BaseException as error:
        fail('START_OR_GUARDIAN_FAILURE', f'{type(error).__name__}: {error}')
    finally:
        # This also covers a child created before registry publication failed.
        unfinished = [c for c in children.values() if not c['record']['reaped']]
        if unfinished:
            for child in unfinished:
                signal_owned(child, signal.SIGTERM)
            cleanup_bound = min(hard_deadline, time.monotonic() + limits['cleanup_reserve'])
            grace_end = min(cleanup_bound, time.monotonic() + limits['term_grace'])
            while any(not c['record']['reaped'] for c in children.values()):
                if time.monotonic() >= grace_end:
                    for child in children.values():
                        signal_owned(child, signal.SIGKILL)
                reap_ready()
                if time.monotonic() >= cleanup_bound:
                    # One final nonblocking collection; unreaped is incomplete,
                    # never a fictitious zero-valued final CPU entry.
                    for child in children.values():
                        signal_owned(child, signal.SIGKILL)
                    reap_ready()
                    break
                if any(not c['record']['reaped'] for c in children.values()):
                    time.sleep(min(POLL, max(0.0, cleanup_bound - time.monotonic())))
        for child in children.values():
            row = child['record']
            item = proc_identity(row['pid'])
            row['live_after_reap'] = item is not None and item['start_ticks'] == row['start_ticks']
            if not row['reaped']:
                book.errors.append(dict(kind='ACCOUNTING_INCOMPLETE', role=row['role'], message='No final wait4 by deadline'))
                _UNREAPED_HANDLES.append(child['proc'])
            row['ipc'] = dict(bytes_received=child['peer'].bytes_received,
                              bytes_sent=child['peer'].bytes_sent,
                              max_queued_bytes=child['peer'].max_queued_bytes,
                              partial_at_finish=child['peer'].partial_started is not None)
            child['peer'].close()
            child['log'].close()
        selector.close()
        try:
            persist_registry()
        except BaseException as error:
            finalization_errors.append(str(error))
    if failure is None and (book.total() >= limits['pair_cpu'] or cumulative + book.total() >= limits['total_cpu']):
        failure = dict(kind='FINAL_CPU_LIMIT', message='Final wait4 confirms a resource-limit overrun')
    complete = not book.errors and not finalization_errors and all(
        row['reaped'] for row in records if row['created'])
    if not complete and failure is None:
        failure = dict(kind='ACCOUNTING_INCOMPLETE', message='Final accounting is not complete')
    result = dict(attempt_id=attempt, pair_id=pair, passed=failure is None and complete,
                  failure=failure, accounting_complete=complete, accounting_errors=book.errors,
                  finalization_errors=finalization_errors, worker_cpu=book.total(),
                  total_worker_cpu=book.total(), scientific_cpu=book.total(),
                  controller_cpu=book.total(('controller',)),
                  guardian_cpu=time.process_time() - guardian_start_cpu,
                  cumulative_before=cumulative, cumulative_after=cumulative + book.total(),
                  wall=time.monotonic() - start, limits=limits,
                  max_monitor_interval=max_monitor_interval, processes=records, ledger=records,
                  all_reaped=all(c['record']['reaped'] for c in children.values()),
                  orphan_records=[r for r in records if r['created'] and not r['reaped']],
                  env_done=env_done, messages=events, samples=samples,
                  message_counts=dict(Counter(e.get('message_type') for e in events if e['type'] == 'MESSAGE')),
                  completed_sense_requests=len(completed_sense),
                  scope='unique guardian wait4 ownership; worker CPU excludes controller and guardian')
    save_json(out / 'guardian_result.json', result)
    return result
