"""Structural test doubles from saved D60 records; no live ACTUAL experiment."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from research.non_oracle.stfbs_d1a_replay import digest
from research.non_oracle import stfbs_lite_live_cut as live

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def block_science(monkeypatch):
    from research.non_oracle import belief, environment, policy, stfbs_d1a_model, stfbs_d1b_qm_model
    from research.cooperative_sensing import estimator
    from research.information_service_online.execution import OnlineEnvironment, ActualMeasurementCache
    from research.information_service_bridge.public_stream import BridgeFrameProcessor
    import scipy.optimize

    def forbidden(*args, **kwargs):
        raise AssertionError('Forbidden transition during structural capture')

    for owner, names in ((belief.Beliefs, ('freeze', 'enqueue')),
        (environment.NonOracleEnvironment, ('prepare_decision',)),
        (OnlineEnvironment, ('step', '_advance_tick', '_sample', '_fuse')),
        (ActualMeasurementCache, ('query',)), (BridgeFrameProcessor, ('process',)),
        (policy, ('decide', 'evaluate', 'endpoint', 'estimate')),
        (estimator, ('estimate', 'least_squares')), (scipy.optimize, ('least_squares',)),
        (stfbs_d1a_model.Branch, ('run', 'advance', 'assign', 'fuse')),
        (stfbs_d1b_qm_model.QMBranch, ('run', 'advance'))):
        for name in names:
            monkeypatch.setattr(owner, name, forbidden)


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))


def reseal(env):
    snapshot = env.snapshot
    snapshot['checkpoint']['checkpoint_id'] = digest({k: v for k, v in snapshot['checkpoint'].items() if k != 'checkpoint_id'})
    snapshot['snapshot_digest'] = digest({k: v for k, v in snapshot.items() if k != 'snapshot_digest'})


@pytest.fixture
def port():
    record = read('runs/a2_switch_episode_001/R_D60.json')
    previous = read('runs/a2_switch_episode_001/R_D40.json')['step']
    seed = read('reports/stfbs_lite_d1a_001/BELIEF_REPLAY_SEED.json')
    final = read('runs/a2_switch_episode_001/R.json')['final']
    view = record['policy_input']
    # Artificial frozen executor port assembled from saved records. It does not
    # instantiate or restore a real execution environment.
    snap = deepcopy(final)
    snap['checkpoint'] = deepcopy(previous['checkpoint_after'])
    snap['boundary_committed_tick'] = 40
    snap['inflight'] = None
    snap['failed'] = False
    snap['state'].update(tick=60, positions=deepcopy(view['positions']), assignment=deepcopy(view['assignment']),
                         statuses=['active', 'active'], histories={str(h['target_id']): deepcopy(h) for h in view['histories']},
                         components=deepcopy(previous['metrics']['reward_components']), change_cost=previous['metrics']['change_cost'])
    snap['action_commits'] = [a for a in snap['action_commits'] if a['start_tick'] < 60]
    snap['fusions'] = [f for f in snap['fusions'] if f['frame']['tick'] < 60 or f['frame']['tick'] == 60 and f['frame']['target_id'] == 0]
    snap['sampler']['entries'] = [r for r in snap['sampler']['entries'] if r['raw_key'][3] < 60 or r['raw_key'][3] == 60 and r['raw_key'][1] == 0]
    snap['sampler']['attempts'] = snap['sampler']['attempts'][:122]
    snap['sampler']['requests'] = 122
    snap['sampler']['reuses'] = 0
    consumer = SimpleNamespace(states={int(k): v for k, v in seed['internal_states_at_D60'].items()},
        history={int(k): v for k, v in seed['accepted_position_history'].items()},
        pending=deepcopy(seed['pending_observations']), consumed=deepcopy(seed['consumed_records']),
        accepted_receipts={int(k): v for k, v in seed['accepted_receipts'].items()}, announcements=deepcopy(seed['announcements']))
    view['beliefs'] = {int(k): v for k, v in view['beliefs'].items()}
    view['first_policy_visible_ticks'] = {int(k): v for k, v in view['first_policy_visible_ticks'].items()}
    env = SimpleNamespace(snapshot=snap, beliefs=consumer, tick=60, decision_tick=60, frozen=deepcopy(view['beliefs']),
        _boundary_committed_tick=40, journal=SimpleNamespace(inflight=None), failed=False, done=False,
        physical_environment_id='A2_R', source_identity=final['source_identity'],
        first_visible_ticks=deepcopy(view['first_policy_visible_ticks']))
    env.private_snapshot = lambda: deepcopy(env.snapshot)
    reseal(env)
    return env, view


def test_capture_detached_and_repeatable(port):
    env, view = port
    before = deepcopy((env.snapshot, vars(env.beliefs), view))
    out = live.capture_live_cut(env, view)
    assert out['status'] == 'LIVE_CUT_STRUCTURAL_CAPTURE_PASS', out
    assert out == live.capture_live_cut(env, view)
    assert (env.snapshot, vars(env.beliefs), view) == before
    private, public = out['private_live_cut'], out['public_policy_view']
    assert public == view and set(public) == live.PUBLIC_FIELDS
    assert private['snapshot'] == env.snapshot
    for field, attr in [('consumer_states', 'states'), ('accepted_position_history', 'history'),
                        ('pending_observations', 'pending'), ('consumed_records', 'consumed'), ('accepted_receipts', 'accepted_receipts')]:
        assert private['consumer'][field] == getattr(env.beliefs, attr)
    public['positions'][0][0] = -1
    assert private['snapshot']['state']['positions'][0][0] != -1
    private['snapshot']['state']['positions'][0][0] = -2
    assert env.snapshot == before[0]
    assert public['positions'][0][0] == -1


@pytest.mark.parametrize('bad', ['pre_freeze', 'committed', 'phase', 'tick', 'position', 'assignment',
                                'inflight', 'failed', 'done', 'belief', 'consumer', 'receipt'])
def test_phase_and_state_conflicts_reject(port, bad):
    env, view = port
    if bad == 'pre_freeze': env.decision_tick = 40
    if bad == 'committed': env._boundary_committed_tick = 60
    if bad == 'phase': env.snapshot['checkpoint']['phase'] = 'TERMINAL'
    if bad == 'tick': view['tick'] = 80
    if bad == 'position': view['positions'][0][0] += 1
    if bad == 'assignment': view['assignment'][0]['target'] = None
    if bad == 'inflight': env.journal.inflight = {'pending': True}
    if bad == 'failed': env.failed = True
    if bad == 'done': env.done = True
    if bad == 'belief': view['beliefs'][0]['position_estimate'][0] += 1
    if bad == 'consumer': env.beliefs.states[0]['position_estimate'][0] += 1
    if bad == 'receipt': env.beliefs.accepted_receipts[0]['consumed_tick'] = 999
    reseal(env)
    assert live.capture_live_cut(env, view)['status'] == 'LIVE_CUT_STRUCTURAL_CAPTURE_FAIL'


def test_change_during_capture_rejected(port):
    env, view = port
    original = env.private_snapshot
    calls = []
    def changing():
        calls.append(1)
        if len(calls) == 2:
            env.snapshot['sampler']['requests'] += 1
            reseal(env)
        return original()
    env.private_snapshot = changing
    assert live.capture_live_cut(env, view)['reason'] == 'EXECUTOR_CHANGED_DURING_CAPTURE'


def test_private_checkpoint_truth_and_schedule_not_exposed(port):
    env, view = port
    assert 'position_now' in env.snapshot['checkpoint']['targets'][0]
    out = live.capture_live_cut(env, view)
    assert out['status'] == 'LIVE_CUT_STRUCTURAL_CAPTURE_PASS', out
    public = out['public_policy_view']
    text = json.dumps(public)
    for forbidden in ('position_now', 'velocity_now', 'sensor_declaration_schedule', 'sampler', 'private_snapshot'):
        assert forbidden not in text
    assert set(public['targets'][0]) == live.ANN_FIELDS
    view['targets'][0]['position_now'] = [99., 99.]
    assert live.capture_live_cut(env, view)['status'].endswith('FAIL')


def test_profile_missing_preserved_without_watermark_claim(port):
    env, view = port
    for profiles in (view['sensor_profiles'], env.snapshot['checkpoint']['sensor_profiles']):
        profiles[2]['health'] = 'missing'
    reseal(env)
    out = live.capture_live_cut(env, view)
    assert out['status'].endswith('PASS'), out
    assert out['public_policy_view']['sensor_profiles'][2]['health'] == 'missing'
    assert out['private_live_cut']['public_profile_watermark'].startswith('NOT_VERIFIED')


def test_raw_and_economics_unchanged_and_no_certification_upgrade(port):
    env, view = port
    out = live.capture_live_cut(env, view)
    assert out['status'].endswith('PASS'), out
    snap = out['private_live_cut']['snapshot']
    assert snap['sampler'] == env.snapshot['sampler']
    assert all(row['raw_key'][0] == 'A2_R' for row in snap['sampler']['entries'])
    assert snap['state']['components'] == env.snapshot['state']['components']
    assert snap['state']['change_cost'] == .02
    evidence = out['private_live_cut']['causal_evidence']
    assert evidence['order_kind'] == 'DERIVED' and evidence['ordinals_issued'] is False
    assert evidence['complete_causal_order'] == 'NOT_VERIFIED'
    assert out['real_actual_live_cut'] == 'NOT_RUN'
    for key in ('real_source_authentication', 'full_trusted_cut', 'real_model_initialization'):
        assert out[key] == 'NOT_VERIFIED'


def test_same_tick_after_freeze_pending_is_not_consumed(port):
    env, view = port
    # Explicit synthetic arrival after the frozen boundary; capture must not
    # infer eligibility from available_tick or silently consume this record.
    pending = dict(source='ACTUAL', target_id=1, measurement_tick=60, available_tick=60, estimate=None)
    env.beliefs.pending.append(pending)
    out = live.capture_live_cut(env, view)
    assert out['status'].endswith('PASS'), out
    assert out['private_live_cut']['consumer']['pending_observations'] == [pending]
    assert env.beliefs.pending == [pending]
    assert not any(r['target_id'] == 1 for r in env.beliefs.consumed)


@pytest.mark.parametrize('where', ['top', 'history', 'diagnostics', 'duplicate_pending'])
def test_private_extensions_and_queue_conflict_rejected(port, where):
    env, view = port
    if where == 'top': view['private_sampler'] = {'secret': True}
    if where == 'history':
        for history in (view['histories'][0], env.snapshot['checkpoint']['task_histories'][0],
                        env.snapshot['state']['histories']['0']):
            history['private_future_schedule'] = ['secret']
        reseal(env)
    if where == 'diagnostics':
        for b in (view['beliefs'][0], env.frozen[0], env.beliefs.states[0]):
            b['diagnostics']['private_future_schedule'] = ['secret']
    if where == 'duplicate_pending':
        row = dict(source='ACTUAL', target_id=0, measurement_tick=60, available_tick=60, estimate=None)
        env.beliefs.pending = [row]
    out = live.capture_live_cut(env, view)
    assert out['status'] == 'LIVE_CUT_STRUCTURAL_CAPTURE_FAIL'
    assert 'secret' not in json.dumps(out)
