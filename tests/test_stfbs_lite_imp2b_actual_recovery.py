"""Real archived A2_R reconstruction; no new sensing, WLS or physical steps."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from research.non_oracle import stfbs_lite_archive_root as ar
from research.non_oracle import stfbs_lite_actual_recovery as recovery
from research.non_oracle import stfbs_lite_cut_state as imp2a
from research.non_oracle.stfbs_d1a_replay import digest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def forbid_new_science(monkeypatch):
    from research.cooperative_sensing import estimator
    from research.non_oracle import policy, environment, stfbs_d1a_model, stfbs_d1b_qm_model
    from research.information_service_online.execution import OnlineEnvironment, ActualMeasurementCache
    from research.information_service_bridge.public_stream import BridgeFrameProcessor
    import scipy.optimize

    def forbidden(*args, **kwargs):
        raise AssertionError('New science forbidden in archived-state reconstruction')

    for owner, names in (
        (estimator, ('estimate', 'least_squares')), (scipy.optimize, ('least_squares',)),
        (policy, ('decide', 'evaluate', 'endpoint', 'estimate')),
        (OnlineEnvironment, ('step', '_advance_tick', '_sample', '_fuse')),
        (ActualMeasurementCache, ('query', 'record_outcome')),
        (environment.NonOracleEnvironment, ('prepare_decision', '_fuse')),
        (BridgeFrameProcessor, ('process',)),
        (stfbs_d1a_model.Branch, ('run', 'advance', 'assign', 'fuse')),
        (stfbs_d1b_qm_model.QMBranch, ('run', 'advance', 'assign', 'fuse')),
    ):
        for name in names:
            monkeypatch.setattr(owner, name, forbidden)
    # Beliefs.freeze/enqueue/activate_visible remain enabled intentionally.


@pytest.fixture(scope='module')
def bound():
    return ar.bind_actual_archive(ROOT)


@pytest.mark.parametrize('tick,consumed,raw_count,fee', [(60,61,122,.02), (80,82,164,.04), (100,102,204,.04)])
def test_real_archive_cut_reconstruction(bound, tick, consumed, raw_count, fee):
    before = bound._documents_json
    result = recovery.recover_actual_cut(bound, tick)
    assert result['status'] == 'ARCHIVED_ACTUAL_CUT_RECONSTRUCTION_PASS', result
    cut = result['cut'].to_dict()
    docs = bound.documents()
    view = docs[f'R_D{tick}.json']['policy_input']
    prev = docs[f'R_D{tick-20}.json']['step']
    assert cut['cut_tick'] == prev['end_tick'] == view['tick'] == tick
    assert cut['cut_phase'] == 'POST_FREEZE_PRE_ASSIGNMENT'
    assert cut['checkpoint_id'] == prev['checkpoint_after']['checkpoint_id']
    assert cut['checkpoint_id'] == docs[f'R_D{tick}.json']['step']['action_commit']['checkpoint_id']
    assert cut['public_policy_view'] == view
    assert cut['frozen_public_beliefs'] == view['beliefs']
    assert cut['physical_cut_state']['positions'] == view['positions']
    assert cut['current_assignment'] == view['assignment']
    assert list(cut['task_histories'].values()) == view['histories']
    assert len(cut['consumed_records']) == consumed
    assert cut['pending_observations'] == []
    assert len(cut['raw_cache_history']) == raw_count
    assert cut['settled_economic_components'] == prev['frames'][-1]['metrics']['reward_components']
    assert cut['change_cost_so_far'] == fee
    assert cut['future_value_origin'] == 'EXCLUDE_SETTLED_PREFIX'
    assert cut['imp2a_field_mapping']['trusted_prefix_digest'].startswith('NOT_ISSUED')
    assert cut['archive_binding']['status'] == result['archive_bytes'] == 'ARCHIVE_BYTES_BOUND'
    assert result['real_source_authentication'] == result['full_trusted_cut'] == 'NOT_VERIFIED'
    assert bound._documents_json == before


def test_d60_reference_seed_is_comparison_not_replay_input(bound):
    cut = recovery.recover_actual_cut(bound, 60)['cut'].to_dict()
    seed = bound.d60_reference_seed()
    assert cut['consumer_states'] == seed['internal_states_at_D60']
    assert cut['accepted_position_history'] == seed['accepted_position_history']
    assert cut['accepted_receipts'] == seed['accepted_receipts']
    assert cut['consumed_records'] == seed['consumed_records']


def test_same_tick_consumer_and_raw_transaction_boundary(bound):
    c60 = recovery.recover_actual_cut(bound, 60)['cut'].to_dict()
    c80 = recovery.recover_actual_cut(bound, 80)['cut'].to_dict()
    assert any(r['target_id'] == 0 and r['measurement_tick'] == r['consumed_tick'] == 60 for r in c60['consumed_records'])
    assert not any(r['target_id'] == 1 for r in c60['consumed_records'])
    assert any(r['target_id'] == 1 and r['measurement_tick'] == 60 and r['consumed_tick'] == 80 for r in c80['consumed_records'])
    keys60 = {tuple(r['raw_key']) for r in c60['raw_cache_history']}
    keys80 = {tuple(r['raw_key']) for r in c80['raw_cache_history']}
    assert ('A2_R', 0, 0, 60) in keys60
    assert ('A2_R', 1, 0, 60) not in keys60
    assert ('A2_R', 1, 0, 60) in keys80
    prepared = bound.documents()['R_D60.json']['step']['action_commit']['prepared_actual_slots']
    assert all(('A2_R', s['slot_key']['target_id'], s['slot_key']['robot_id'], s['slot_key']['tick']) not in keys60 for s in prepared)


@pytest.mark.parametrize('tick', [80, 100])
def test_accepted_history_receipts_are_derived_from_saved_estimates(bound, tick):
    cut = recovery.recover_actual_cut(bound, tick)['cut'].to_dict()
    for j, positions in cut['accepted_position_history'].items():
        assert [x[0] for x in positions] == sorted(set(x[0] for x in positions))
        if positions:
            receipt = cut['accepted_receipts'][j]
            assert receipt in cut['consumed_records']
            assert receipt['measurement_tick'] == positions[-1][0]
            state = cut['consumer_states'][j]
            assert state['position_estimate'] == positions[-1][1]
            assert state['estimate_tick'] == positions[-1][0]
    assert cut['freeze_boundary_identity']['ordinal_kind'].startswith('DERIVED_')
    assert all('#/step/fusion_records/' in x['source_ref'] for x in cut['observation_arrivals'])


def test_original_context_and_packet_identity_unchanged(bound):
    cut = recovery.recover_actual_cut(bound, 100)['cut'].to_dict()
    entries = {tuple(x['raw_key']): x for x in bound.documents()['R.json']['final']['sampler']['entries']}
    for row in cut['raw_cache_history']:
        assert set(row['original_context']) == {'position', 'sigma', 'health'}
        assert digest(row['original_context']) == row['context_digest']
        assert row['raw_key'][0] == row['episode_binding']['physical_environment_id'] == 'A2_R'
        assert {k: row[k] for k in ('raw_key', 'context_digest', 'slot')} == entries[tuple(row['raw_key'])]


def test_archive_read_or_expected_manifest_tamper_rejected(monkeypatch):
    original = Path.read_bytes
    for target in ('R_D80.json', 'BASELINE.json'):
        def altered(path, chosen=target):
            raw = original(path)
            return raw+b' ' if path.name == chosen else raw
        with monkeypatch.context() as patch:
            patch.setattr(Path, 'read_bytes', altered)
            with pytest.raises(ar.ArchiveBindingError): ar.bind_actual_archive(ROOT)


def test_bound_archive_cannot_be_replaced_by_self_issued_expectations(bound):
    assert recovery.recover_actual_cut(None, 60)['status'].endswith('FAIL')
    fake = replace(bound, _seal=None)
    assert recovery.recover_actual_cut(fake, 60)['reason'] == 'BOUND_ACTUAL_ARCHIVE_REQUIRED'
    docs = bound.documents()
    docs['R_D60.json']['policy_input']['positions'][0][0] += 1
    fake = replace(bound, _documents_json=json.dumps(docs))
    assert recovery.recover_actual_cut(fake, 60)['reason'] == 'BOUND_DOCUMENT_IDENTITY_MISMATCH'


def resync_embedded(docs):
    docs['R.json']['records'] = [deepcopy(docs[f'R_D{k}.json']) for k in (0,20,40,60,80,100)]


def resync_final(docs):
    f = docs['R.json']['final']
    f['snapshot_digest'] = digest({k: v for k, v in f.items() if k != 'snapshot_digest'})


@pytest.mark.parametrize('bad', ['environment', 'episode', 'checkpoint', 'position', 'missing_fusion',
                                'fusion_order', 'consumed', 'early_t1', 'raw_context', 'raw_environment',
                                'economic', 'service_clock', 'sampler_environment', 'missing_prepared', 'receipt_evidence'])
def test_semantic_tampering_rejected_in_memory_audit(bound, bad):
    docs = bound.documents()
    if bad == 'environment': docs['R.json']['final']['physical_environment_id'] = 'A2_S_NEW'
    if bad == 'episode': docs['R.json']['final']['source_identity'] = 'foreign'
    if bad == 'checkpoint': docs['R_D60.json']['step']['action_commit']['checkpoint_id'] = 'foreign'
    if bad == 'position': docs['R_D80.json']['policy_input']['positions'][0][0] += 1
    if bad == 'missing_fusion': docs['R_D40.json']['step']['fusion_records'].pop()
    if bad == 'fusion_order': docs['R_D40.json']['step']['fusion_records'].reverse()
    if bad == 'consumed': docs['R.json']['observations_consumed'].pop(0)
    if bad == 'early_t1':
        docs['R_D40.json']['step']['fusion_records'].append(deepcopy(docs['R_D60.json']['step']['fusion_records'][0]))
    if bad == 'raw_context':
        row = docs['R.json']['final']['sampler']['entries'][0]
        context = dict(position=row['slot']['packet']['position'], sigma=.02, health='available', episode_id='A2_R')
        row['context_digest'] = digest(context)
        docs['R.json']['final']['sampler']['attempts'][0]['context_digest'] = row['context_digest']
        resync_final(docs)
    if bad == 'raw_environment':
        docs['R.json']['final']['sampler']['entries'][0]['raw_key'][0] = 'MODEL'
        resync_final(docs)
    if bad == 'economic': docs['R_D60.json']['step']['metrics']['change_cost'] += .02
    if bad == 'service_clock': docs['R_D80.json']['policy_input']['histories'][0]['cutoff_tick'] = 100
    if bad == 'receipt_evidence': docs['R_D80.json']['evidence']['targets'][0]['corresponding_consumed_tick'] = 80
    if bad == 'sampler_environment':
        docs['R.json']['final']['sampler']['physical_environment_id'] = 'MODEL'
        resync_final(docs)
    if bad == 'missing_prepared':
        docs['R_D60.json']['step']['action_commit']['prepared_actual_slots'].pop()
        commit = docs['R_D60.json']['step']['action_commit']
        commit['action_commit_id'] = digest({k: v for k, v in commit.items() if k != 'action_commit_id'})
        docs['R_D60.json']['step']['action_commit_id'] = commit['action_commit_id']
    resync_embedded(docs)
    # The private helper can audit corrupted copies, but does not issue a bound
    # reconstruction PASS. Public admission independently checks sealed bytes.
    with pytest.raises((recovery.ReconstructionError, KeyError, ValueError)):
        recovery._recover_documents(docs, 80)


def test_actual_archive_cannot_claim_imp2a_synthetic_pass(bound):
    cut = recovery.recover_actual_cut(bound, 60)['cut'].to_dict()
    root = imp2a.ExternalTrustRoot('A2_R', cut['source_identity'], 60, cut['cut_phase'],
                                 '', '', '', 'ARCHIVE_BYTES_BOUND')
    assert imp2a.verify_trusted_cut(cut, trusted_root=root)['status'] == 'REAL_TRUST_PROVIDER_NOT_CONFIGURED'
    fake_synthetic = replace(root, evidence_kind=imp2a.SYNTHETIC_ROOT)
    assert imp2a.verify_trusted_cut(cut, trusted_root=fake_synthetic)['status'] != 'SYNTHETIC_CUT_INTERFACE_VERIFIED'


def test_isolation_repeatability_and_original_files_unchanged(bound):
    before = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ar.ARCHIVES}
    first = recovery.recover_actual_cut(bound, 80)
    second = recovery.recover_actual_cut(bound, 80)
    assert first == second
    result = first['cut'].to_dict()
    result['accepted_position_history'].clear()
    result['raw_cache_history'][0]['original_context']['position'][0] = -999
    assert first['cut'].to_dict() == second['cut'].to_dict()
    assert before == {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ar.ARCHIVES}


@pytest.mark.parametrize('tick', [0, 59, 120, True])
def test_unsupported_cut_refused(bound, tick):
    assert recovery.recover_actual_cut(bound, tick)['reason'] == 'UNSUPPORTED_CUT'
