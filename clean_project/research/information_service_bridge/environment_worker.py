"""Private environment-side dispatcher. Never imported by the sensing worker."""
import copy
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import sys
import traceback
import unittest

from .common import CONTRACT_ID, ContractError, digest, file_sha, save_json
from .wire import WireClient

ROOT = Path(__file__).resolve().parents[2]


def check_preconditions(value, conditions):
    for item in conditions:
        current = value
        for key in item['path']:
            current = current[key]
        if current != item['equals']:
            raise ContractError('Predetermined action precondition failed: '+repr(item))


def guards():
    def hook(event, args):
        if event in ('subprocess.Popen', 'os.fork', 'os.forkpty', 'os.posix_spawn', 'os.posix_spawnp'):
            raise ContractError('Scientific worker child creation forbidden')
    sys.addaudithook(hook)


def run_admin(payload, out):
    kind = payload['kind']
    if kind == 'runtime':
        import numpy
        import scipy
        versions = dict(python=sys.version.split()[0], numpy=numpy.__version__, scipy=scipy.__version__)
        assert versions == dict(python='3.13.9', numpy='2.3.5', scipy='1.16.3'), versions
        return dict(passed=True, versions=versions, executable=sys.executable,
                    executable_sha256=file_sha(sys.executable),
                    dependencies={numpy.__file__:file_sha(numpy.__file__),scipy.__file__:file_sha(scipy.__file__)})
    if kind == 'unittest':
        from research.information_service.worker import instrument_estimator
        counts = instrument_estimator(out)
        sys.path.insert(0, str(ROOT/'tests'))
        suite = unittest.TestSuite()
        for name in payload['modules']:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
        tested = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
        result = dict(passed=tested.wasSuccessful(), tests=tested.testsRun,
                      failures=len(tested.failures), errors=len(tested.errors), skipped=len(tested.skipped),
                      estimate_counts=copy.deepcopy(counts))
        save_json(out/'result.json', result)
        if not tested.wasSuccessful():
            raise AssertionError('Required unit checks failed')
        return result
    if kind == 'old_g':
        from pursuit_v2.config import Config
        from pursuit_v2.types import Target, Scenario, Assignment, IDLE
        from pursuit_v2.environment import TimedEnvironment
        from research.information_service.worker import json_safe
        case = payload['case']
        env = TimedEnvironment(Config(**case['config']), Scenario(case['positions_initial'],
                      tuple(Target(**target) for target in case['targets'])))
        q = case['targets'][0]['required_robots']
        roles = ['dual_neg45','dual_pos45'] if q == 2 else ['tri_0','tri_120','tri_240']
        steps = []
        while not env.done:
            actions = [IDLE]*case['config']['robots']
            if env.status[0] == 'active':
                actions[:q] = [Assignment(0, role) for role in roles]
            steps.append(json_safe(env.step(tuple(actions), trace=True).info))
        return dict(passed=True, metrics=json_safe(env.metrics()), steps=steps)
    if kind == 'audit':
        from .acceptance import audit_attempt
        return audit_attempt(Path(payload['attempt']), out)
    if kind == 'pre_main_audit':
        from .acceptance import audit_accounting
        return audit_accounting(Path(payload['attempt']))
    if kind == 'plot':
        os.environ['MPLCONFIGDIR']=str(out/'tmp/matplotlib')
        from .plotting import plot_attempt
        return dict(passed=True,artifact=plot_attempt(Path(payload['attempt'])))
    raise ContractError('Unknown environment admin job '+repr(kind))


def main(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    guards()
    wire = WireClient(args.fd)
    save_json(out/'worker_environment.json', dict(role='env', pid=os.getpid(),
        python=sys.version, executable=sys.executable,
        limits=dict(cpu=resource.getrlimit(resource.RLIMIT_CPU), address_space=resource.getrlimit(resource.RLIMIT_AS)),
        threads={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')}))
    wire.send(dict(type='READY',role='env'))
    start = wire.recv(timeout=12.)
    if start['type'] != 'START':
        raise ContractError('START expected')
    payload = start['payload']
    env = None
    messages = []
    result = None
    sequence = 0
    try:
        if payload['kind'] == 'isolation':
            results = []
            for number, probe in enumerate(payload['probes']):
                ident = dict(attempt_id=args.attempt_id, pair_id=args.pair_id,
                    sense_request_id=f'probe-{number}', target_id=0,
                    stream_id='isolation', global_tick=number, payload_sha256=digest(probe))
                wire.send(dict(type='AUTHORIZE', identity=ident))
                permission = wire.recv(timeout=12.)
                assert permission['type']=='AUTHORIZED' and permission['identity']==ident
                wire.send(dict(type='ISOLATION_PROBE', identity=ident, **probe))
                response = wire.recv(timeout=12.)
                assert response['type']=='ISOLATION_RESULT' and response['identity']==ident, response
                assert response['result']['passed'] and response['result']['error_type']=='AccessDenied'
                assert response['result']['estimator_calls']==0
                wire.send(dict(type='SENSE_ACK', identity=ident))
                results.append(response)
            data = payload['positive']
            ident = dict(attempt_id=args.attempt_id, pair_id=args.pair_id,
                sense_request_id='positive', target_id=data['frame']['target_id'],
                stream_id=data['frame']['stream_id'], global_tick=data['frame']['tick'],
                payload_sha256=digest(data))
            wire.send(dict(type='AUTHORIZE', identity=ident))
            permission = wire.recv(timeout=12.)
            assert permission['type']=='AUTHORIZED' and permission['identity']==ident
            wire.send(dict(type='SENSE', identity=ident, **data))
            positive = wire.recv(timeout=12.)
            assert positive['type']=='SENSE_RESULT' and positive['identity']==ident
            assert positive['result']['quality']['status']=='UNKNOWN'
            assert positive['result']['skipped'] is True
            wire.send(dict(type='SENSE_ACK', identity=ident))
            result = dict(passed=True, probes=results, positive=positive)
            save_json(out/'result.json',result)
            wire.send(dict(type='ENV_DONE',result=dict(passed=True)))
        elif payload['kind'] == 'science':
            from .environment import GQExecutionEnvironment
            def sense(frame, allowed_sensor_ids, start_tick):
                nonlocal sequence
                sequence += 1
                data = dict(frame=frame, allowed_sensor_ids=list(allowed_sensor_ids), start_tick=start_tick)
                ident = dict(attempt_id=args.attempt_id, pair_id=args.pair_id,
                    sense_request_id=f'sense-{sequence}', target_id=frame['target_id'],
                    stream_id=frame['stream_id'], global_tick=frame['tick'], payload_sha256=digest(data))
                wire.send(dict(type='AUTHORIZE', identity=ident))
                authorized = wire.recv(timeout=12.)
                if authorized.get('type') != 'AUTHORIZED' or authorized.get('identity') != ident:
                    raise ContractError('Invalid sensing authorization')
                wire.send(dict(type='SENSE', identity=ident, **data))
                response = wire.recv(timeout=12.)
                if response.get('type') != 'SENSE_RESULT' or response.get('identity') != ident:
                    raise ContractError('Mismatched sensing response')
                from research.information_service.public_quality import prepare_frame
                prepared=prepare_frame(frame,allowed_sensor_ids)
                sensed=response['result']
                for field in ('frame_id','target_id','stream_id','tick'):
                    if sensed.get(field)!=frame[field]:
                        raise ContractError('Invalid response frame identity')
                if (sensed.get('payload_sha256')!=prepared['payload_sha256'] or
                    sensed.get('quality',{}).get('payload_sha256')!=prepared['payload_sha256'] or
                    sensed.get('quality',{}).get('status') not in ('PASS','FAIL','UNKNOWN')):
                    raise ContractError('Invalid public response contract')
                messages.append(dict(identity=ident, public_request=data, response=response['result']))
                save_json(out/'sensing_responses.json', messages)
                wire.send(dict(type='SENSE_ACK', identity=ident))
                return response['result']
            env = GQExecutionEnvironment(payload['case'], sense,
                      attempt_id=args.attempt_id, environment_id=args.pair_id)
            save_json(out/'initial_state.json', env.observe_execution())
        else:
            result = run_admin(payload, out)
            save_json(out/'result.json', result)
            wire.send(dict(type='ENV_DONE', result=dict(passed=result.get('passed',True))))
        while True:
            message = wire.recv(timeout=12.)
            if message['type'] == 'STOP':
                if env is not None:
                    result = dict(passed=env.observe_execution()['tick']==120,
                                  state=env.observe_execution(), snapshot=env.snapshot(),
                                  actual_requests=sequence)
                    save_json(out/'result.json', result)
                wire.send(dict(type='STOP_ACK',role='env'))
                return 0
            if message['type'] != 'STEP' or env is None:
                raise ContractError('Unexpected environment message')
            if message['request_id'] not in env.snapshot()['cache']:
                check_preconditions({'state_after':env.observe_execution()}, message.get('preconditions',[]))
            step = env.step_fixed_assignment(message['actions'],
                expected_start_tick=message['expected_start_tick'], request_id=message['request_id'])
            save_json(out/'last_committed_state.json', env.snapshot())
            wire.send(dict(type='STEP_RESULT', request_id=message['request_id'], result=step))
            if env.observe_execution()['tick'] >= 120:
                wire.send(dict(type='ENV_DONE', result=dict(passed=True)))
    except BaseException as exc:
        save_json(out/'failure.json', dict(type=type(exc).__name__,message=str(exc),
                   traceback=traceback.format_exc(),last_committed_state=env.snapshot() if env else None,
                   sensing_requests=sequence))
        raise
