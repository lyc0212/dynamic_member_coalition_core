"""Candidate schema tests, not real execution/source authentication evidence."""
from copy import deepcopy
import json

import pytest

from tests.test_stfbs_lite_imp2b_live_cut import port, block_science
from research.non_oracle import stfbs_lite_live_cut as live
from research.non_oracle import stfbs_lite_real_cut_to_model as mapping
from research.non_oracle.stfbs_d1a_replay import digest


@pytest.fixture(autouse=True)
def forbid_branch_and_budget(monkeypatch, block_science):
    from research.non_oracle import stfbs_d1a_model, stfbs_d1b_qm_execution
    from research.non_oracle.stfbs_d1a_state import ModelBeliefConsumer

    def forbidden(*args, **kwargs):
        raise AssertionError('Executable MODEL/budget/observation operation forbidden')

    monkeypatch.setattr(stfbs_d1a_model.Branch, '__init__', forbidden)
    monkeypatch.setattr(stfbs_d1a_model.Budget, '__init__', forbidden)
    monkeypatch.setattr(stfbs_d1b_qm_execution, 'bind_shared_budget', forbidden)
    monkeypatch.setattr(ModelBeliefConsumer, 'enqueue', forbidden)


@pytest.fixture(scope='module')
def original():
    # Reuse the existing artificial D60 port builder only; no old test executes.
    env, view = port.__wrapped__()
    out = live.capture_live_cut(env, view)
    assert out['status'] == 'LIVE_CUT_STRUCTURAL_CAPTURE_PASS', out
    return out


@pytest.fixture
def captured(original):
    return deepcopy(original)


def reseal(cut):
    snap = cut['private_live_cut']['snapshot']
    snap['snapshot_digest'] = digest({k: v for k, v in snap.items() if k != 'snapshot_digest'})
    cut['private_digest'] = digest(cut['private_live_cut'])
    cut['public_digest'] = digest(cut['public_policy_view'])


def test_candidate_mapping_seed_isolation_and_denied_admission(captured):
    before = deepcopy(captured)
    out = mapping.prepare_real_cut_model_input(captured)
    assert out['status'] == 'REAL_CUT_TO_MODEL_SCHEMA_MAPPING_PASS', out
    assert out['candidate_status'] == 'MODEL_INITIALIZATION_CANDIDATE_READY'
    assert out['execution_admission'] == 'MODEL_EXECUTION_ADMISSION_DENIED'
    candidate = out['candidate']
    seed = candidate['consumer_seed']
    consumer = captured['private_live_cut']['consumer']
    assert seed['internal_states_at_D60'] == consumer['consumer_states']
    assert seed['accepted_position_history'] == consumer['accepted_position_history']
    assert seed['pending_observations'] == consumer['pending_observations']
    assert seed['consumed_records'] == consumer['consumed_records']
    assert seed['accepted_receipts'] == consumer['accepted_receipts']
    assert candidate['a2_policy_view'] == captured['public_policy_view']
    assert candidate['model_future_increment'] is None
    assert candidate['future_value_origin'] == 'EXCLUDE_SETTLED_PREFIX'
    assert candidate['actual_settled_prefix']['components'] == captured['private_live_cut']['snapshot']['state']['components']
    assert candidate['actual_settled_prefix']['change_cost'] == .02
    assert len(candidate['historical_raw_reference']['sampler']['entries']) == 122
    assert candidate['historical_raw_reference']['sampler'] == captured['private_live_cut']['snapshot']['sampler']
    assert not {'world', 'name', 'budget'} & set(candidate)
    seed['internal_states_at_D60'].clear()
    candidate['a2_policy_view']['positions'][0][0] = -99
    assert captured == before
    assert consumer['consumer_states']


def test_json_string_keys_preserve_target_identity_and_order(captured):
    serialized = json.loads(json.dumps(captured))
    out = mapping.prepare_real_cut_model_input(serialized)
    assert out['status'].endswith('PASS'), out
    assert set(out['candidate']['consumer_seed']['internal_states_at_D60']) == {0, 1}
    assert out['candidate']['consumer_seed']['consumed_records'] == captured['private_live_cut']['consumer']['consumed_records']


@pytest.mark.parametrize('bad', ['status', 'private_digest', 'public_digest', 'checkpoint', 'phase', 'consumer',
    'pending', 'raw_context', 'raw_key', 'economics', 'private_target', 'future_frame', 'target_alias'])
def test_invalid_or_resealed_conflicts_are_rejected(captured, bad):
    private = captured['private_live_cut']
    if bad == 'status': captured['status'] = 'PASS'
    if bad == 'private_digest': captured['private_digest'] = 'wrong'
    if bad == 'public_digest': captured['public_digest'] = 'wrong'
    if bad == 'checkpoint': captured['checkpoint_id'] = 'wrong'
    if bad == 'phase': private['cut_phase'] = 'PRE_FREEZE'
    if bad == 'consumer': private['consumer']['consumer_states'][0]['position_estimate'][0] += 1
    if bad == 'pending':
        private['consumer']['pending_observations'].append(dict(source='ACTUAL', target_id=0,
            measurement_tick=60, available_tick=60, estimate=None))
    if bad == 'raw_context':
        snap = private['snapshot']
        row = snap['sampler']['entries'][0]
        wrong = dict(position=row['slot']['packet']['position'], sigma=.02, health='available', episode_id='A2_R')
        row['context_digest'] = digest(wrong)
        snap['sampler']['attempts'][0]['context_digest'] = row['context_digest']
    if bad == 'raw_key': private['snapshot']['sampler']['entries'][0]['raw_key'][0] = 'MODEL'
    if bad == 'economics': private['snapshot']['state']['components']['completion'] += 1.
    if bad == 'private_target': captured['public_policy_view']['targets'][0]['position_now'] = [99., 99.]
    if bad == 'future_frame': private['snapshot']['frames'].append(deepcopy(private['snapshot']['frames'][-1]))
    if bad == 'target_alias':
        states = {str(k): v for k, v in private['consumer']['consumer_states'].items()}
        states['00'] = deepcopy(states['0'])
        private['consumer']['consumer_states'] = states
    if bad not in ('private_digest', 'public_digest'): reseal(captured)
    out = mapping.prepare_real_cut_model_input(captured)
    assert out['candidate_status'] == 'NOT_READY', out
    assert out['execution_admission'] == 'MODEL_EXECUTION_ADMISSION_DENIED'


@pytest.mark.parametrize('tick', [80, 100])
def test_non_d60_tick_is_not_relabelled(captured, tick):
    captured['private_live_cut']['control']['tick'] = tick
    captured['public_policy_view']['tick'] = tick
    reseal(captured)
    out = mapping.prepare_real_cut_model_input(captured)
    assert out['status'] == 'MODEL_INITIALIZATION_TICK_NOT_SUPPORTED'
    assert out['candidate_status'] == 'NOT_READY'


@pytest.mark.parametrize('authority', ['SYNTHETIC_TRUST_ROOT_NOT_REAL_EXECUTION_EVIDENCE',
    {'evidence_kind': 'TEST_DOUBLE'}, {'authenticated': True}, object()])
def test_no_self_declared_authority_can_enable_real_execution(captured, authority):
    out = mapping.prepare_real_cut_model_input(captured, source_authority=authority)
    assert out['candidate_status'] == 'NOT_READY'
    assert out['reason'] == 'SOURCE_AUTHORITY_NOT_SUPPORTED'
    assert out['real_source_authentication'] == 'NOT_VERIFIED'
    assert out['execution_admission'] == 'MODEL_EXECUTION_ADMISSION_DENIED'


def test_pending_is_preserved_without_refreezing(captured):
    pending = dict(source='ACTUAL', target_id=1, measurement_tick=60, available_tick=60, estimate=None)
    captured['private_live_cut']['consumer']['pending_observations'] = [pending]
    reseal(captured)
    out = mapping.prepare_real_cut_model_input(captured)
    assert out['candidate_status'] == 'MODEL_INITIALIZATION_CANDIDATE_READY', out
    assert out['candidate']['consumer_seed']['pending_observations'] == [pending]
    assert not any(r['target_id'] == 1 for r in out['candidate']['consumer_seed']['consumed_records'])


def test_public_private_namespaces_and_certification_remain_separate(captured):
    out = mapping.prepare_real_cut_model_input(captured)
    assert out['candidate_status'].endswith('READY'), out
    c = out['candidate']
    public_text = json.dumps(c['a2_policy_view'])
    for forbidden in ('position_now', 'velocity_now', 'sensor_declaration_schedule', 'sampler'):
        assert forbidden not in public_text
    assert c['historical_raw_reference']['model_future_raw'].startswith('NOT_CREATED')
    assert c['unresolved_model_dependencies']['world'].startswith('D1A_WORLD_AND_STFBS')
    for field in ('real_source_authentication', 'full_trusted_cut', 'public_projection_authority', 'real_model_initialization'):
        assert out[field] == 'NOT_VERIFIED'
    assert out['trust_provider'] == 'REAL_TRUST_PROVIDER_NOT_CONFIGURED'


def test_missing_input_is_fixed_code_no_private_leak():
    for value in (None, {}, {'status': 'LIVE_CUT_STRUCTURAL_CAPTURE_PASS', 'private_secret': 'HIDDEN'}):
        out = mapping.prepare_real_cut_model_input(value)
        assert out['candidate_status'] == 'NOT_READY'
        assert 'HIDDEN' not in json.dumps(out)


@pytest.mark.parametrize('health,ready', [('missing', True), ('unavailable', False)])
def test_production_profile_semantics_are_not_silently_translated(captured, health, ready):
    private = captured['private_live_cut']
    snapshot = private['snapshot']
    captured['public_policy_view']['sensor_profiles'][2]['health'] = health
    cp = snapshot['checkpoint']
    cp['sensor_profiles'][2]['health'] = health
    cp['checkpoint_id'] = digest({k: v for k, v in cp.items() if k != 'checkpoint_id'})
    captured['checkpoint_id'] = cp['checkpoint_id']
    last = max(snapshot['successful_requests'].values(), key=lambda r: r['result']['end_tick'])
    last['result']['checkpoint_after'] = deepcopy(cp)
    reseal(captured)
    out = mapping.prepare_real_cut_model_input(captured)
    if ready:
        assert out['candidate_status'] == 'MODEL_INITIALIZATION_CANDIDATE_READY', out
        assert out['candidate']['a2_policy_view']['sensor_profiles'][2]['health'] == 'missing'
        assert out['public_projection_authority'] == 'NOT_VERIFIED'
    else:
        assert out['candidate_status'] == 'NOT_READY'
