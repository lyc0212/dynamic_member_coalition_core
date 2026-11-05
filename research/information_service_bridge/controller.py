"""Fixed scripted coordinator; never creates or reaps any subprocess."""
import os
from pathlib import Path
import sys
import time

from .common import ContractError, save_json
from .wire import WireClient


def _no_children(event, args):
    if event in ('subprocess.Popen', 'os.fork', 'os.forkpty', 'os.posix_spawn', 'os.posix_spawnp', 'os.system'):
        raise ContractError('Coordinator cannot create subprocesses')


def require_conditions(result, conditions):
    """Check the predeclared paths against the preceding STEP_RESULT.result."""
    for condition in conditions:
        if not isinstance(condition, dict) or set(condition) != {'path', 'equals'}:
            raise ContractError('Exact precondition path/equals fields required')
        value = result
        for part in condition['path']:
            try:
                value = value[part]
            except (TypeError, KeyError, IndexError) as error:
                raise ContractError('Missing controlled-action precondition path') from error
        if value != condition['equals']:
            raise ContractError('Controlled-action precondition failed: ' + repr(condition['path']))


def worker(args):
    """Root entry dispatches role=controller here with the common CLI args."""
    sys.addaudithook(_no_children)
    client = WireClient(args.fd)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    records = []
    seen_success_ids = set()
    last_result = None
    next_heartbeat = time.monotonic()

    def receive():
        nonlocal next_heartbeat
        while True:
            now = time.monotonic()
            if now >= next_heartbeat:
                client.send(dict(type='HEARTBEAT', role='controller'), timeout=0.5)
                next_heartbeat = now + 0.25
            try:
                return client.recv(timeout=max(0.001, min(0.25, next_heartbeat - time.monotonic())))
            except TimeoutError as error:
                if 'partial-frame' in str(error):
                    raise
                continue

    client.send(dict(type='READY', role='controller', pid=os.getpid()))
    try:
        message = receive()
        if message.get('type') != 'START':
            raise ContractError('Coordinator expected START')
        payload = message.get('payload', {})
        steps = payload.get('steps', [])
        if not isinstance(steps, list):
            raise ContractError('Fixed steps must be a list')
        for step in steps:
            required = {'actions', 'expected_start_tick', 'request_id'}
            if not required <= set(step) or set(step) - required - {'preconditions'}:
                raise ContractError('Unknown fixed-step fields')
            conditions = step.get('preconditions', [])
            if conditions and step['request_id'] not in seen_success_ids:
                require_conditions(last_result, conditions)
            client.send(dict(type='STEP', **step))
            while True:
                reply = receive()
                if reply.get('type') == 'STOP':
                    raise ContractError('STOP before the scripted step result')
                if reply.get('type') != 'STEP_RESULT' or reply.get('request_id') != step['request_id']:
                    raise ContractError('Wrong scripted step response identity')
                returned = reply.get('result')
                if step['request_id'] not in seen_success_ids:
                    last_result = returned
                seen_success_ids.add(step['request_id'])
                records.append(dict(request=step, result=returned))
                break
        client.send(dict(type='CONTROLLER_DONE', step_count=len(records)))
        # Empty-step unittest/old-G/audit jobs also wait for environment ENV_DONE.
        while True:
            reply = receive()
            if reply.get('type') != 'STOP':
                raise ContractError('Unexpected message after fixed script')
            if getattr(args, 'synthetic', None) == 'controller_shutdown_exit':
                os._exit(7)  # Atomic injected exit before STOP_ACK; no close/kill race.
            save_json(out / 'controller_result.json', dict(passed=True, steps=records,
                                                           pid=os.getpid(), no_children=True))
            client.send(dict(type='STOP_ACK', role='controller'))
            return 0
    except BaseException as error:
        save_json(out / 'controller_failure.json', dict(type=type(error).__name__,
                                                        message=str(error), steps=records))
        try:
            client.send(dict(type='CONTROL_ERROR', error_type=type(error).__name__,
                             message=str(error)), timeout=0.25)
        except BaseException:
            pass
        return 1
    finally:
        client.close()
