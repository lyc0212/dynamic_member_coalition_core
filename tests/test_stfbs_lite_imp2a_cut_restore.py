"""Artificial interface evidence only, never actual or MODEL evolution."""
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
import json

import pytest

from pursuit_v2.config import Config
from research.information_service_online.public import segment_identity
from research.non_oracle.belief import Beliefs
from research.non_oracle.stfbs_d1a_replay import digest
from research.non_oracle import stfbs_lite_cut_state as cs
from research.non_oracle import stfbs_lite_public_adapter as pa
from research.non_oracle.stfbs_lite_worlds import generate_worlds


@pytest.fixture(autouse=True)
def forbid_computation(monkeypatch):
    from research.non_oracle import policy, environment, stfbs_d1a_model, stfbs_d1b_qm_model
    from research.cooperative_sensing import estimator
    import scipy.optimize

    def forbidden(*args, **kwargs):
        raise AssertionError('Forbidden A2/WLS/freeze/physical execution')

    for name in ('decide', 'evaluate', 'endpoint', 'estimate'):
        monkeypatch.setattr(policy, name, forbidden)
    monkeypatch.setattr(estimator, 'estimate', forbidden)
    monkeypatch.setattr(estimator, 'least_squares', forbidden)
    monkeypatch.setattr(scipy.optimize, 'least_squares', forbidden)
    monkeypatch.setattr(Beliefs, 'freeze', forbidden)
    monkeypatch.setattr(environment.NonOracleEnvironment, 'prepare_decision', forbidden)
    monkeypatch.setattr(stfbs_d1a_model.Branch, 'advance', forbidden)
    monkeypatch.setattr(stfbs_d1a_model.Branch, 'run', forbidden)
    monkeypatch.setattr(stfbs_d1b_qm_model.QMBranch, 'run', forbidden)


def event(j, index, kind, when, segment_id=None):
    return dict(event_index=index, target_id=j, kind=kind, segment_id=segment_id,
                at=dict(time_seconds=when*.05, event_tick=when), progress_before=0., progress_after=0.)


def slot(j, i, tick, state='UNQUERIED'):
    return dict(slot_key=dict(target_id=j, robot_id=i, tick=tick), state=state,
                packet=None, slot_digest=None)


def seal_external_fixture(cut):
    """Artificial issuer in test code, not a production trust-root factory."""
    cut['public_snapshot_digest'] = digest(pa._public_payload(cut))
    cut['trusted_prefix_digest'] = cs.cut_prefix_digest(cut)
    return cs.ExternalTrustRoot(cut['episode_id'], cut['source_identity'], cut['cut_tick'], cut['cut_phase'],
                               cut['trusted_prefix_digest'], cut['public_snapshot_digest'],
                               digest(cut['freeze_boundary_identity']), cs.SYNTHETIC_ROOT)


def consumer_boundary(cut):
    cut['freeze_boundary_identity']['consumer_digest'] = digest(dict(
        states=cut['consumer_states'], history=cut['accepted_position_history'],
        consumed=cut['consumed_records'], receipts=cut['accepted_receipts']))


def fixture(tick):
    cfg = Config(robots=3, task_count=2, capture_mode='stepwise_service', geometry_mode='angular_standoff_v1')
    actions = [dict(target=0, role='dual_neg45'), dict(target=0, role='dual_pos45'), dict(target=None, role='none')]
    members = [dict(robot_id=i, role=a['role']) for i, a in enumerate(actions[:2])]
    announcements = [dict(id=j, announcement_tick=0, birth=0., weight=2., deadline=6.,
                          service_duration=2., required_robots=2, coarse_position=[5.+j, 5.],
                          velocity_prior=[0., 0.], design_error_bound=.4, speed_limit=1.,
                          motion_model='constant_velocity') for j in (0, 1)]
    consumer = Beliefs(announcements)
    histories = {}
    zero = dict(base=0., intervals=0, team=deepcopy(members))
    endpoint = dict(tick=tick, target_id=0, team=deepcopy(members), G=True,
                    quality=dict(status='UNKNOWN', radius_proxy=None),
                    slots=[slot(0, i, tick, 'MISSING') for i in (0, 1)])
    seg = dict(contract_id='gq_online_service_segment_v1', target_id=0, segment_index=0,
               previous_segment_id=None, start_tick=0, team=deepcopy(members), opened_by='FIRST_ASSIGNMENT',
               initial_clock=deepcopy(zero), latest_clock=deepcopy(zero), latest_endpoint=endpoint,
               closure=None, events=[])
    seg['segment_id'] = segment_identity(seg)
    e = event(0, 0, 'ASSIGNED', 0, seg['segment_id'])
    seg['events'] = [deepcopy(e)]
    histories['0'] = dict(target_id=0, birth_tick=0, cutoff_tick=tick, active_segment_id=seg['segment_id'],
                          segments=[seg], unassigned_intervals=[], events=[e])
    e1 = event(1, 1, 'BORN', 0)
    histories['1'] = dict(target_id=1, birth_tick=0, cutoff_tick=tick, active_segment_id=None,
                          segments=[], unassigned_intervals=[dict(start_tick=0, end_at=None, opened_by='BIRTH',
                          opening_event_index=1, closing_event_index=None)], events=[e1])
    current = [slot(j, i, tick, 'MISSING' if j == 0 and i < 2 else 'UNQUERIED')
               for j in (0, 1) for i in range(3)]
    raw = []
    for s in current[:2]:
        context = dict(episode_id='synthetic-episode', acquisition='synthetic-slot')
        raw.append(dict(slot=deepcopy(s), slot_digest=digest(s), context=context, context_digest=digest(context)))
    states = {str(j): b for j, b in consumer.states.items()}
    policy = dict(tick=tick, config=cfg.to_dict(), positions=[[5., 4.5], [5., 5.5], [7., 7.]],
                  assignment=deepcopy(actions), targets=deepcopy(announcements), beliefs=deepcopy(states))
    economics = dict(completion=0., flow=-.1, late=-.02, effort=-.03, terminal=0.)
    cut = dict(episode_id='synthetic-episode', cut_tick=tick, cut_phase=cs.PHASE,
               source_identity='synthetic-independent-issuer', trusted_prefix_digest='', public_snapshot_digest='',
               freeze_boundary_identity=dict(cut_tick=tick, freeze_ordinal=10, consumer_digest=''),
               physical_cut_state=dict(tick=tick, positions=deepcopy(policy['positions']), assignment=deepcopy(actions),
                   terminal_status={'0': 'active', '1': 'active'}, settled_economic_components=deepcopy(economics),
                   change_cost_so_far=.02, private_future_motion={'secret': [99, 99]}),
               current_assignment=deepcopy(actions), terminal_status={'0': 'active', '1': 'active'},
               task_histories=histories, service_segments=[deepcopy(seg)], consumer_states=states,
               accepted_position_history={'0': [], '1': []}, pending_observations=[], consumed_records=[],
               accepted_receipts={}, frozen_public_beliefs=deepcopy(states), raw_cache_history=raw,
               current_slots=current, public_profile_watermark=tick,
               trusted_sensor_authority_state=dict(published_watermark=tick, private_future_schedule=[{'secret': 99}]),
               settled_economic_components=economics, change_cost_so_far=.02,
               public_source=dict(policy_view=policy, published_announcements=deepcopy(announcements),
                   published_profiles=[dict(sensor_id=f'U{i}', observed_tick=tick, sigma=.02, health='available') for i in range(3)],
                   visible_ids=[0, 1], attempted_ticks=[]),
               observation_arrivals=[], freeze_boundaries={str(tick): 10}, evidence_kind=cs.SYNTHETIC_CUT)
    consumer_boundary(cut)
    return cut, seal_external_fixture(cut)


@pytest.mark.parametrize('tick', [60, 80, 100])
def test_import_synthetic_cut_at_actual_tick(tick):
    cut, root = fixture(tick)
    before = deepcopy(cut)
    out = cs.import_verified_cut(cut, trusted_root=root)
    assert out['status'] == 'SYNTHETIC_CUT_INTERFACE_VERIFIED'
    assert out['real_causal_restore_verified'] is False
    assert out['applicability'] == 'APPLICABLE'
    view = out['public_snapshot'].to_view()
    assert view['tick'] == tick and generate_worlds(view)['status'] == 'WORLDS_GENERATED'
    restored = out['trusted_state'].to_restore_payload()
    assert restored == cut
    assert restored['settled_economic_components'] == before['settled_economic_components']
    assert out['future_economic_origin'] == 'EXCLUDE_SETTLED_PREFIX_FROM_FUTURE_VALUE'
    assert cut == before
    assert cs.import_verified_cut(cut, trusted_root=root)['public_snapshot'] == out['public_snapshot']
    view['positions'][0][0] = -99
    restored['trusted_sensor_authority_state']['private_future_schedule'].clear()
    assert out['public_snapshot'].to_view()['positions'] == before['physical_cut_state']['positions']
    assert out['trusted_state'].to_restore_payload() == cut


@pytest.mark.parametrize('field,value', [('expected_episode_id', 'foreign'), ('expected_cut_tick', 80),
    ('expected_cut_phase', 'PRE_FREEZE'), ('expected_source_identity', 'foreign'),
    ('expected_trusted_prefix_digest', 'bad'), ('expected_public_snapshot_digest', 'bad'),
    ('expected_freeze_boundary', 'bad')])
def test_external_root_mismatch(field, value):
    cut, root = fixture(60)
    assert cs.import_verified_cut(cut, trusted_root=replace(root, **{field: value}))['status'] == 'EXTERNAL_ROOT_IDENTITY_CONFLICT'


def test_no_self_authentication_or_synthetic_elevation():
    cut, root = fixture(60)
    assert cs.verify_trusted_cut(cut)['status'] == 'EXTERNAL_TRUST_ROOT_REQUIRED'
    assert cs.verify_trusted_cut(cut, trusted_root=cut)['status'] == 'EXTERNAL_TRUST_ROOT_REQUIRED'
    assert cs.verify_trusted_cut(cut, trusted_root=root, requested_certification='REAL_CAUSAL_RESTORE_VERIFIED')['status'] == 'REAL_CERTIFICATION_NOT_AVAILABLE'
    assert cs.verify_trusted_cut(cut, trusted_root=replace(root, evidence_kind='REAL_EXECUTOR'))['status'] == 'REAL_TRUST_PROVIDER_NOT_CONFIGURED'
    cut['physical_cut_state']['private_future_motion']['secret'][0] = 100
    assert cs.verify_trusted_cut(cut, trusted_root=root)['status'] == 'EXTERNAL_ROOT_IDENTITY_CONFLICT'
    cut['trusted_prefix_digest'] = cs.cut_prefix_digest(cut)
    assert cs.verify_trusted_cut(cut, trusted_root=root)['status'] == 'EXTERNAL_ROOT_IDENTITY_CONFLICT'


def test_public_projection_no_private_reference_or_bypass():
    cut, root = fixture(60)
    cut['public_source']['policy_view']['targets'][0]['private_schedule'] = 'SECRET'
    cut['public_source']['published_announcements'][0]['private_schedule'] = 'SECRET'
    cut['frozen_public_beliefs']['0']['diagnostics'] = {'private_future': 'SECRET'}
    cut['consumer_states']['0']['diagnostics'] = {'private_future': 'SECRET'}
    cut['public_source']['policy_view']['beliefs']['0']['diagnostics'] = {'private_future': 'SECRET'}
    consumer_boundary(cut)
    root = seal_external_fixture(cut)
    out = cs.import_verified_cut(cut, trusted_root=root)
    assert out['status'] == 'SYNTHETIC_CUT_INTERFACE_VERIFIED'
    assert 'SECRET' not in out['public_snapshot']._json
    assert 'private' not in out['public_snapshot']._json
    assert 'trusted_prefix' not in out['public_snapshot']._json
    with pytest.raises(pa.ProjectionError): pa.PublicDecisionSnapshot({}, cs.SYNTHETIC_CUT)
    with pytest.raises(FrozenInstanceError): out['public_snapshot'].evidence_kind = 'REAL'


@pytest.mark.parametrize('missing', ['design_error_bound', 'speed_limit', 'motion_model', 'coarse_position', 'velocity_prior'])
def test_missing_announcements_fail_closed(missing):
    cut, root = fixture(60)
    del cut['public_source']['published_announcements'][0][missing]
    # Independent root can bind even an invalid candidate. Structural validation
    # must still refuse it; never substitute private physical fields.
    cut['trusted_prefix_digest'] = cs.cut_prefix_digest(cut)
    root = replace(root, expected_trusted_prefix_digest=cut['trusted_prefix_digest'])
    assert cs.import_verified_cut(cut, trusted_root=root)['status'] == 'PUBLIC_ANNOUNCEMENT_FIELDS_MISSING'


@pytest.mark.parametrize('bad', ['future_announcement', 'model', 'profile_watermark', 'future_profile', 'phase',
                                'physical_position', 'service_clock', 'raw_conflict', 'economic', 'assignment',
                                'receipt', 'frozen_belief', 'boundary'])
def test_reject_semantic_conflicts_even_with_matching_external_binding(bad):
    cut, root = fixture(80)
    if bad == 'future_announcement': cut['public_source']['published_announcements'][0]['announcement_tick'] = 100
    if bad == 'model': cut['public_source']['published_announcements'][0]['motion_model'] = 'unknown'
    if bad == 'profile_watermark': cut['public_profile_watermark'] = 100
    if bad == 'future_profile': cut['public_source']['published_profiles'][0]['observed_tick'] = 100
    if bad == 'phase': cut['cut_phase'] = 'POST_ASSIGNMENT'
    if bad == 'physical_position': cut['physical_cut_state']['positions'][0][0] = 999
    if bad == 'service_clock': cut['task_histories']['0']['segments'][0]['latest_clock']['base'] = .5
    if bad == 'raw_conflict': cut['raw_cache_history'][0]['slot']['state'] = 'VALID'
    if bad == 'economic': cut['settled_economic_components']['flow'] = -.2
    if bad == 'assignment': cut['current_assignment'][0]['target'] = 1
    if bad == 'receipt': cut['accepted_receipts']['0'] = {}
    if bad == 'frozen_belief': cut['frozen_public_beliefs']['0']['position_estimate'][0] = 999
    if bad == 'boundary': cut['freeze_boundary_identity']['freeze_ordinal'] = 9
    # Preserve original expected public digest so invalid source paths can reject
    # before projection rather than trying to mint a successful snapshot.
    cut['trusted_prefix_digest'] = cs.cut_prefix_digest(cut)
    root = replace(root, expected_trusted_prefix_digest=cut['trusted_prefix_digest'],
                   expected_cut_phase=cut['cut_phase'], expected_freeze_boundary=digest(cut['freeze_boundary_identity']))
    assert cs.import_verified_cut(cut, trusted_root=root)['status'] != 'SYNTHETIC_CUT_INTERFACE_VERIFIED'


def add_queue(cut, *, after_freeze, future_delivery=False):
    tick = cut['cut_tick']
    obs = dict(source='ACTUAL', target_id=0, measurement_tick=tick,
               available_tick=tick+1 if future_delivery else tick, estimate=None)
    pending = after_freeze or future_delivery
    cut['observation_arrivals'] = [dict(arrival_ordinal=11 if after_freeze else 1,
                                      consumed_tick=None if pending else tick, observation=obs)]
    cut['pending_observations'] = [deepcopy(obs)] if pending else []
    cut['consumed_records'] = [] if pending else [dict(target_id=0, measurement_tick=tick, available_tick=tick, consumed_tick=tick)]
    consumer_boundary(cut)


@pytest.mark.parametrize('tick', [60, 80, 100])
@pytest.mark.parametrize('after,future', [(True, False), (False, False), (False, True)])
def test_queue_freeze_boundary_not_available_tick_alone(tick, after, future):
    cut, _ = fixture(tick)
    add_queue(cut, after_freeze=after, future_delivery=future)
    root = seal_external_fixture(cut)
    out = cs.import_verified_cut(cut, trusted_root=root)
    assert out['status'] == 'SYNTHETIC_CUT_INTERFACE_VERIFIED'
    assert out['trusted_state'].to_restore_payload()['pending_observations'] == cut['pending_observations']


@pytest.mark.parametrize('bad', ['lost_pending', 'early_consume', 'lost_consumed', 'duplicate_arrival'])
def test_queue_conflict_refused(bad):
    cut, _ = fixture(100)
    add_queue(cut, after_freeze=bad != 'lost_consumed')
    if bad == 'lost_pending': cut['pending_observations'] = []
    if bad == 'early_consume': cut['observation_arrivals'][0]['consumed_tick'] = 100
    if bad == 'lost_consumed': cut['consumed_records'] = []
    if bad == 'duplicate_arrival': cut['observation_arrivals'].append(deepcopy(cut['observation_arrivals'][0]))
    consumer_boundary(cut)
    root = seal_external_fixture(cut)
    assert cs.import_verified_cut(cut, trusted_root=root)['status'] != 'SYNTHETIC_CUT_INTERFACE_VERIFIED'


def test_full_history_unavailable_cannot_be_seed_import():
    cut, root = fixture(60)
    for prefix in (None, {}, {'complete': True, 'seed': cut}, cut):
        out = cs.recover_from_verified_history(prefix, trusted_root=root)
        assert out['status'] == 'FULL_CAUSAL_HISTORY_PREFIX_UNAVAILABLE'
        assert out['d60_belief_replay'] == 'NOT_VERIFIED'
        assert out['d60_full_causal_cut'] == 'NOT_VERIFIED'
    assert cs.recover_from_verified_history(cut)['status'] == 'EXTERNAL_TRUST_ROOT_REQUIRED'


def test_error_does_not_expose_private_payload():
    cut, root = fixture(60)
    cut['trusted_sensor_authority_state']['private_future_schedule'] = ['NEVER_PRINT_ME']
    out = cs.import_verified_cut(cut, trusted_root=root)
    assert 'NEVER_PRINT_ME' not in json.dumps(out)


def add_accepted_observation(cut):
    tick = cut['cut_tick']
    estimate = dict(has_accepted_estimate=True, optimizer_converged=True,
                    numerical_ill_conditioned=False, ambiguity_detected=False,
                    boundary_active=False, numeric_contract_violation=False, estimate=[5., 5.])
    obs = dict(source='ACTUAL', target_id=0, measurement_tick=tick, available_tick=tick, estimate=estimate)
    cut['observation_arrivals'] = [dict(arrival_ordinal=1, consumed_tick=tick, observation=obs)]
    receipt = dict(target_id=0, measurement_tick=tick, available_tick=tick, consumed_tick=tick)
    cut['consumed_records'] = [receipt]
    cut['accepted_receipts'] = {'0': deepcopy(receipt)}
    cut['accepted_position_history']['0'] = [[tick, [5., 5.]]]
    b = cut['consumer_states']['0']
    b.update(estimate_tick=tick, available_tick=tick, last_observation_tick=tick,
             position_estimate=[5., 5.], source='ACTUAL_WLS', status='OBSERVED', diagnostics=estimate)
    cut['frozen_public_beliefs'] = deepcopy(cut['consumer_states'])
    cut['public_source']['policy_view']['beliefs'] = deepcopy(cut['frozen_public_beliefs'])
    consumer_boundary(cut)


@pytest.mark.parametrize('tick', [60, 80, 100])
def test_accepted_receipt_and_pending_coexist_without_refreeze(tick):
    cut, _ = fixture(tick)
    add_accepted_observation(cut)
    pending = dict(source='ACTUAL', target_id=1, measurement_tick=tick, available_tick=tick, estimate=None)
    cut['observation_arrivals'].append(dict(arrival_ordinal=11, consumed_tick=None, observation=pending))
    cut['pending_observations'] = [deepcopy(pending)]
    root = seal_external_fixture(cut)
    out = cs.import_verified_cut(cut, trusted_root=root)
    assert out['status'] == 'SYNTHETIC_CUT_INTERFACE_VERIFIED'
    payload = out['trusted_state'].to_restore_payload()
    assert payload['accepted_receipts'] == cut['accepted_receipts']
    assert payload['pending_observations'] == [pending]
    assert out['public_snapshot'].to_view()['beliefs'][0]['last_observation_tick'] == tick


@pytest.mark.parametrize('bad', ['receipt', 'position', 'flags', 'consumed_duplicate', 'accepted_duplicate'])
def test_accepted_consumer_conflicts_rejected(bad):
    cut, _ = fixture(80)
    add_accepted_observation(cut)
    if bad == 'receipt': cut['accepted_receipts']['0']['measurement_tick'] = 79
    if bad == 'position': cut['accepted_position_history']['0'][0][1][0] = 99.
    if bad == 'flags': cut['observation_arrivals'][0]['observation']['estimate']['boundary_active'] = True
    if bad == 'consumed_duplicate': cut['consumed_records'].append(deepcopy(cut['consumed_records'][0]))
    if bad == 'accepted_duplicate': cut['accepted_position_history']['0'].append(deepcopy(cut['accepted_position_history']['0'][0]))
    consumer_boundary(cut)
    root = seal_external_fixture(cut)
    assert cs.import_verified_cut(cut, trusted_root=root)['status'] != 'SYNTHETIC_CUT_INTERFACE_VERIFIED'


def terminal_fixture():
    cut, _ = fixture(100)
    h = cut['task_histories']['1']
    end = event(1, 2, 'ESCAPED', 99)
    end['processed_tick'] = 99
    h['events'].append(end)
    h['cutoff_tick'] = 99
    h['unassigned_intervals'][0].update(end_at=deepcopy(end['at']), closing_event_index=2)
    cut['terminal_status']['1'] = 'escaped'
    cut['physical_cut_state']['terminal_status']['1'] = 'escaped'
    cut['public_source']['policy_view']['targets'] = cut['public_source']['policy_view']['targets'][:1]
    cut['public_source']['visible_ids'] = [0]
    cut['current_slots'] = cut['current_slots'][:3]
    return cut


def test_terminal_task_never_reactivated_and_not_applicable():
    cut = terminal_fixture()
    root = seal_external_fixture(cut)
    out = cs.import_verified_cut(cut, trusted_root=root)
    assert out['status'] == 'SYNTHETIC_CUT_INTERFACE_VERIFIED'
    assert out['applicability'] == 'NOT_APPLICABLE'
    assert out['public_snapshot'].to_view()['active_ids'] == [0]
    assert out['trusted_state'].to_restore_payload()['terminal_status']['1'] == 'escaped'
    cut['terminal_status']['1'] = cut['physical_cut_state']['terminal_status']['1'] = 'active'
    cut['trusted_prefix_digest'] = cs.cut_prefix_digest(cut)
    root = replace(root, expected_trusted_prefix_digest=cut['trusted_prefix_digest'])
    assert cs.import_verified_cut(cut, trusted_root=root)['status'] != 'SYNTHETIC_CUT_INTERFACE_VERIFIED'


def test_new_assignment_transaction_at_cut_is_rejected():
    cut, _ = fixture(60)
    ep = cut['task_histories']['0']['events'][0]
    ep['at'] = dict(time_seconds=3., event_tick=60)
    cut['trusted_prefix_digest'] = cs.cut_prefix_digest(cut)
    # A root over a structurally wrong state cannot authorize changing phases.
    root = seal_external_fixture(cut)
    assert cs.import_verified_cut(cut, trusted_root=root)['status'] == 'CURRENT_CUT_ASSIGNMENT_ALREADY_COMMITTED'


def test_delayed_receipt_freeze_status_projection_only():
    cut, _ = fixture(100)
    add_accepted_observation(cut)
    entry = cut['observation_arrivals'][0]
    entry['observation']['measurement_tick'] = 60
    entry['observation']['available_tick'] = 60
    entry['consumed_tick'] = 60
    cut['freeze_boundaries'] = {'60': 5, '100': 10}
    receipt = dict(target_id=0, measurement_tick=60, available_tick=60, consumed_tick=60)
    cut['consumed_records'] = [receipt]
    cut['accepted_receipts'] = {'0': deepcopy(receipt)}
    cut['accepted_position_history']['0'][0][0] = 60
    cut['consumer_states']['0'].update(estimate_tick=60, available_tick=60, last_observation_tick=60)
    cut['frozen_public_beliefs'] = deepcopy(cut['consumer_states'])
    cut['frozen_public_beliefs']['0']['status'] = 'DEGRADED'
    cut['public_source']['policy_view']['beliefs'] = deepcopy(cut['frozen_public_beliefs'])
    consumer_boundary(cut)
    root = seal_external_fixture(cut)
    out = cs.import_verified_cut(cut, trusted_root=root)
    assert out['status'] == 'SYNTHETIC_CUT_INTERFACE_VERIFIED'
    assert out['public_snapshot'].to_view()['beliefs'][0]['status'] == 'DEGRADED'
    assert cut['consumer_states']['0']['status'] == 'OBSERVED'
