"""Archived ACTUAL cuts, production belief state replay, zero physical advance.

This isolated object intentionally does not impersonate an IMP-2A synthetic cut.
Raw keys and contexts retain the production A2_R identity and exact schema.
"""
from copy import deepcopy
from dataclasses import dataclass
import json
import math

from pursuit_v2.service import ServiceState
from research.information_service_online import public
from .belief import Beliefs
from .stfbs_d1a_replay import digest
from .stfbs_d1a_history_audit import audit_histories
from .stfbs_lite_archive_root import (BoundActualArchive, ArchiveBindingError,
                                      checked_documents, DIRECTORY)

PHASE = 'POST_FREEZE_PRE_ASSIGNMENT'
EVIDENCE = 'ARCHIVED_A2_R_ACTUAL_RECONSTRUCTION_NOT_REAL_SOURCE_AUTHENTICATION'


class ReconstructionError(ValueError):
    pass


def _require(condition, reason):
    if not condition:
        raise ReconstructionError(reason)


@dataclass(frozen=True)
class ReconstructedActualCut:
    _json: str
    evidence_kind: str = EVIDENCE

    def to_dict(self):
        """Trusted archival data; never pass this entire object to IMP-1."""
        return json.loads(self._json)


def _checkpoint(record):
    cp = record['step']['checkpoint_after']
    _require(cp['checkpoint_id'] == digest({k: v for k, v in cp.items() if k != 'checkpoint_id'}),
             'CHECKPOINT_DIGEST_MISMATCH')
    return cp


def _recover_documents(docs, tick):
    """Internal audit/replay implementation. Public admission requires bound bytes."""
    _require(type(tick) is int and tick in (60, 80, 100), 'UNSUPPORTED_CUT')
    final_record = docs['R.json']
    final = final_record['final']
    _require(final['physical_environment_id'] == 'A2_R', 'PHYSICAL_ENVIRONMENT_MISMATCH')
    _require(final['sampler']['physical_environment_id'] == 'A2_R', 'RAW_SAMPLER_ENVIRONMENT_MISMATCH')
    _require(final['source_identity'] == digest(final['case']), 'EPISODE_SOURCE_IDENTITY_MISMATCH')
    world = docs['WORLD_INPUT.json']
    world = world.get('private_execution_input', world)
    _require(final['case'] == {k: world[k] for k in final['case']}, 'WORLD_SOURCE_MISMATCH')
    _require(final['snapshot_digest'] == digest({k: v for k, v in final.items() if k != 'snapshot_digest'}),
             'FINAL_SNAPSHOT_IDENTITY_MISMATCH')
    records = [docs[f'R_D{k}.json'] for k in (0, 20, 40, 60, 80, 100)]
    _require(records == final_record['records'], 'EMBEDDED_RECORDS_MISMATCH')
    announcements = docs['PUBLIC_INPUT.json']['announcements']
    consumer = Beliefs(announcements, deferred=True)
    trace, boundaries = [], []
    sequence = 0
    expected_raw_order = []
    raw_slots = {}
    positions_at = {}
    for index, record in enumerate(records):
        view, step = record['policy_input'], record['step']
        cut = index*20
        _require(view['tick'] == step['start_tick'] == cut and step['end_tick'] == cut+20
                 and step['status'] == 'COMMITTED' and not step['replayed'], 'STEP_PHASE_OR_ORDER_CONFLICT')
        _require(view['kind'] == 'A2_POLICY_INPUT', 'PUBLIC_SOURCE_KIND_MISMATCH')
        if index:
            previous = _checkpoint(records[index-1])
            _require(previous['tick'] == cut and previous['phase'] == 'DECISION_READY', 'PRE_CUT_CHECKPOINT_MISMATCH')
            for a, b in (('positions', 'positions'), ('assignment', 'assignment'),
                         ('task_histories', 'histories'), ('sensor_profiles', 'sensor_profiles'), ('current_slots', 'current_slots')):
                _require(previous[a] == view[b], 'CHECKPOINT_PUBLIC_CONTINUITY_CONFLICT')
            _require(step['action_commit']['checkpoint_id'] == previous['checkpoint_id'], 'CHECKPOINT_COMMIT_LINK_MISMATCH')
        _require(step['action_commit']['start_tick'] == cut and step['action_commit_id'] == step['action_commit']['action_commit_id'],
                 'ACTION_COMMIT_IDENTITY_CONFLICT')
        commit = step['action_commit']
        _require(commit['action_commit_id'] == digest({k: v for k, v in commit.items() if k != 'action_commit_id'}),
                 'ACTION_COMMIT_DIGEST_MISMATCH')
        consumer.activate_visible(cut, {t['id'] for t in view['targets']})
        frozen = consumer.freeze(cut)
        _require(frozen == {int(j): b for j, b in view['beliefs'].items()}, 'FROZEN_BELIEF_REPLAY_MISMATCH')
        for item in record['evidence']['targets']:
            j = item['target_id']
            belief = frozen[j]
            receipt = consumer.accepted_receipts.get(j) if belief['last_observation_tick'] is not None else None
            _require(item['last_observation_tick'] == belief['last_observation_tick']
                     and item['corresponding_consumed_tick'] == (None if receipt is None else receipt['consumed_tick'])
                     and item['last_available_tick'] == (None if receipt is None else receipt['available_tick'])
                     and item['diagnostics'] == belief['diagnostics'], 'ARCHIVED_ACCEPTED_RECEIPT_EVIDENCE_CONFLICT')
        sequence += 1
        boundaries.append(dict(cut_tick=cut, derived_ordinal=sequence,
                               source_ref=f'{DIRECTORY}R_D{cut}.json#/policy_input',
                               derivation='run_a2.main: previous STEP -> prepare_decision.freeze -> step assignment',
                               ordinal_kind='DERIVED_FROM_ARCHIVED_PHASE_ORDER_NOT_ORIGINAL_LOG_ORDINAL'))
        if cut == tick:
            break  # NEVER ingest this cut's new assignment or its fusion records.
        prepared = commit['prepared_actual_slots']
        prefix_fusions = step['fusion_records']
        _require(all(cut <= f['frame']['tick'] <= cut+20 for f in prefix_fusions), 'FUSION_OUTSIDE_STEP')
        _require([f['frame']['tick'] for f in prefix_fusions] == sorted(f['frame']['tick'] for f in prefix_fusions),
                 'FUSION_ORDER_CONFLICT')
        # Newly acquired boundary slots and right endpoints together determine
        # the raw prefix. The endpoint references alone do not contain packets.
        slot_map = {tuple(s['slot_key'][k] for k in ('target_id', 'robot_id', 'tick')): s for s in prepared}
        boundary_refs = {tuple(s['slot_key'][k] for k in ('target_id', 'robot_id', 'tick')): s
                         for f in prefix_fusions if f['frame']['tick'] == cut for s in f['actual_endpoint']['slots']}
        _require(len(slot_map) == len(prepared) and set(slot_map) == set(boundary_refs)
                 and all(slot_map[k]['slot_digest'] == boundary_refs[k]['slot_digest']
                         and slot_map[k]['state'] == boundary_refs[k]['state'] for k in slot_map),
                 'PREPARED_SLOT_FUSION_BOUNDARY_CONFLICT')
        for fusion_index, f in enumerate(prefix_fusions):
            frame, endpoint = f['frame'], f['actual_endpoint']
            _require(endpoint['source_kind'] == 'ACTUAL' and endpoint['target_id'] == frame['target_id']
                     and endpoint['tick'] == frame['tick'], 'FUSION_ENDPOINT_IDENTITY_MISMATCH')
            _require(f['result']['tick'] == frame['tick'] and f['result']['target_id'] == frame['target_id']
                     and f['result']['frame_id'] == frame['frame_id']
                     and f['result']['flow_context'] == f['context'], 'FUSION_RESULT_IDENTITY_MISMATCH')
            public._endpoint(endpoint, frame['target_id'], endpoint['team'])
            for ref in endpoint['slots']:
                key = ('A2_R', ref['slot_key']['target_id'], ref['slot_key']['robot_id'], ref['slot_key']['tick'])
                if key not in raw_slots:
                    expected_raw_order.append(key)
                    raw_slots[key] = deepcopy(ref)
            obs = dict(source='ACTUAL', target_id=frame['target_id'], measurement_tick=frame['tick'],
                       available_tick=frame['tick'], estimate=deepcopy(f['result']['estimate_result']))
            consumer.enqueue(obs)
            sequence += 1
            trace.append(dict(derived_arrival_ordinal=sequence, observation=obs,
                              source_ref=f'{DIRECTORY}R_D{cut}.json#/step/fusion_records/{fusion_index}',
                              ordinal_kind='DERIVED_FROM_ARCHIVED_PHASE_ORDER_NOT_ORIGINAL_LOG_ORDINAL'))
        for frame in step['frames']:
            # Frames preserve the positions actually used for sampled endpoints.
            positions_at[frame['tick']] = deepcopy(frame['positions'])
        for slot in prepared:
            i = slot['slot_key']['robot_id']
            _require(slot['packet'] is None or slot['packet']['position'] == view['positions'][i], 'PREPARED_SLOT_POSITION_CONFLICT')
    current = records[tick//20]['policy_input']
    prior_step = records[tick//20-1]['step']
    cp = _checkpoint(records[tick//20-1])
    last = prior_step['frames'][-1]
    _require(last['tick'] == tick and last['positions'] == current['positions']
             and last['assignment'] == current['assignment'], 'PHYSICAL_CUT_FRAME_MISMATCH')
    expected_consumed = [r for r in final_record['observations_consumed'] if r['consumed_tick'] <= tick]
    _require(consumer.consumed == expected_consumed, 'CONSUMED_PREFIX_MISMATCH')
    arrived = {(t['observation']['target_id'], t['observation']['measurement_tick']) for t in trace}
    consumed = {(r['target_id'], r['measurement_tick']) for r in consumer.consumed}
    _require(len(consumed) == len(consumer.consumed) and consumed <= arrived, 'DUPLICATE_OR_MISSING_OBSERVATION')
    # This archive's zero-latency synchronous pre-assignment cuts have no pending.
    _require(not consumer.pending and len(trace) == len(consumer.consumed), 'PENDING_PREFIX_AMBIGUITY')
    statuses = {j: status for j, status in enumerate(last['statuses'])}
    histories = {h['target_id']: deepcopy(h) for h in cp['task_histories']}
    _require(set(histories) == {j for j, status in statuses.items() if status == 'active'}, 'TERMINAL_TASK_REVIVAL')
    audit_histories(histories, current['assignment'], {j: statuses[j] for j in histories}, tick)
    clocks, endpoints, quality = {}, {}, {}
    for j, h in histories.items():
        segment = next((s for s in h['segments'] if s['segment_id'] == h['active_segment_id']), None)
        if segment is None:
            clocks[j], endpoints[j], quality[j] = dict(base=0., intervals=0, team=[]), None, 'UNKNOWN'
        else:
            clocks[j] = deepcopy(segment['latest_clock'])
            ep = segment['latest_endpoint']
            public._endpoint(ep, j, segment['team'])
            ServiceState(clocks[j]['base'], clocks[j]['intervals'], tuple((m['robot_id'], m['role']) for m in clocks[j]['team']))
            endpoints[j], quality[j] = deepcopy(ep), ep['quality']['status']
    all_entries = {tuple(row['raw_key']): row for row in final['sampler']['entries']}
    _require(len(all_entries) == len(final['sampler']['entries']), 'DUPLICATE_RAW_KEY')
    attempts = final['sampler']['attempts'][:len(expected_raw_order)]
    _require([tuple(a['raw_key']) for a in attempts] == expected_raw_order, 'RAW_ATTEMPT_PREFIX_ORDER_CONFLICT')
    raw_history = []
    schedule = final['case']['sensor_declaration_schedule']
    for key, attempt in zip(expected_raw_order, attempts):
        row = all_entries[key]
        slot = row['slot']
        _require(key[0] == 'A2_R' and slot['slot_key'] == dict(target_id=key[1], robot_id=key[2], tick=key[3]),
                 'RAW_ENVIRONMENT_OR_SLOT_IDENTITY_CONFLICT')
        _require(public.seal_slot(slot) == slot, 'RAW_SLOT_DIGEST_MISMATCH')
        _require(slot['slot_digest'] == raw_slots[key]['slot_digest'] and slot['state'] == raw_slots[key]['state'],
                 'RAW_ENDPOINT_REFERENCE_MISMATCH')
        profile = next(r for r in reversed(schedule) if r['effective_tick'] <= key[3])['profiles'][key[2]]
        position = positions_at[key[3]][key[2]]
        context = dict(position=position, sigma=profile['sigma'], health=profile['health'])
        _require(row['context_digest'] == digest(context) == attempt['context_digest'], 'ORIGINAL_RAW_CONTEXT_MISMATCH')
        _require(attempt['outcome'] == slot['state'] and attempt['slot_digest'] == slot['slot_digest'], 'RAW_ATTEMPT_OUTCOME_CONFLICT')
        if slot['state'] == 'VALID':
            packet = slot['packet']
            _require(packet['position'] == position and packet['sigma'] == profile['sigma']
                     and packet['sensor_id'] == f'U{key[2]}' and profile['health'] == 'available'
                     and packet['measurement_tick'] == packet['available_tick'] == key[3], 'RAW_PACKET_CONTEXT_CONFLICT')
        raw_history.append(dict(**deepcopy(row), original_context=context,
                                episode_binding=dict(physical_environment_id='A2_R', source_identity=final['source_identity'])))
    for slot in cp['current_slots']:
        key = ('A2_R', slot['slot_key']['target_id'], slot['slot_key']['robot_id'], tick)
        if slot['state'] == 'UNQUERIED':
            _require(key not in raw_slots, 'POST_ASSIGNMENT_RAW_LEAK')
        else:
            _require(key in raw_slots and all_entries[key]['slot'] == slot, 'CURRENT_RAW_SLOT_CONFLICT')
    metrics = last['metrics']
    _require(metrics == prior_step['metrics'], 'CUMULATIVE_ECONOMIC_PREFIX_CONFLICT')
    _require(metrics['actual_sampling_attempts'] == len(raw_history) == metrics['actual_cache_requests']
             and metrics['actual_cache_reuses'] == 0, 'RAW_PREFIX_COUNTER_CONFLICT')
    _require(set(metrics['reward_components']) == {'completion', 'flow', 'late', 'effort', 'terminal'}
             and all(math.isfinite(v) for v in metrics['reward_components'].values()), 'ECONOMIC_COMPONENT_CONFLICT')
    return dict(episode_id='A2_R', physical_environment_id='A2_R', source_identity=final['source_identity'],
                cut_tick=tick, cut_phase=PHASE, checkpoint_id=cp['checkpoint_id'],
                public_policy_view=deepcopy(current), physical_cut_state=dict(tick=tick, positions=deepcopy(cp['positions']),
                    assignment=deepcopy(cp['assignment']), statuses=statuses, private_execution_input=deepcopy(final['case'])),
                current_assignment=deepcopy(current['assignment']), terminal_status=statuses,
                consumer_states=deepcopy(consumer.states), accepted_position_history=deepcopy(consumer.history),
                pending_observations=deepcopy(consumer.pending), consumed_records=deepcopy(consumer.consumed),
                accepted_receipts=deepcopy(consumer.accepted_receipts), frozen_public_beliefs=deepcopy(frozen),
                task_histories=histories, service_segments=[s for h in histories.values() for s in h['segments']],
                service_clocks=clocks, current_endpoints=endpoints, current_q=quality,
                raw_cache_history=raw_history, current_slots=deepcopy(cp['current_slots']),
                freeze_boundary_identity=boundaries[-1], freeze_boundaries=boundaries, observation_arrivals=trace,
                public_profile_watermark=dict(cut_tick=tick, published_profiles=deepcopy(cp['sensor_profiles']),
                    evidence='DERIVED_CURRENT_DECLARATION_CUT_NOT_ORIGINAL_WATERMARK_FIELD'),
                trusted_sensor_authority_state=deepcopy(final['case']['sensor_declaration_schedule']),
                settled_economic_components=deepcopy(metrics['reward_components']), change_cost_so_far=metrics['change_cost'],
                cumulative_metrics=deepcopy(metrics), future_value_origin='EXCLUDE_SETTLED_PREFIX',
                imp2a_field_mapping=dict(
                    directly_corresponding=['episode_id', 'cut_tick', 'cut_phase', 'source_identity',
                        'physical_cut_state', 'current_assignment', 'terminal_status', 'task_histories',
                        'service_segments', 'consumer_states', 'accepted_position_history', 'pending_observations',
                        'consumed_records', 'accepted_receipts', 'frozen_public_beliefs', 'current_slots',
                        'settled_economic_components', 'change_cost_so_far'],
                    raw_cache_history='PRODUCTION_ENVIRONMENT_KEY_AND_THREE_FIELD_CONTEXT_PRESERVED_NOT_SYNTHETIC_SCHEMA',
                    public_snapshot_digest='NOT_ISSUED_IMP2A_PUBLIC_PROJECTION_NOT_CALLED',
                    trusted_prefix_digest='NOT_ISSUED_ARCHIVE_BINDING_IS_SEPARATE',
                    freeze_boundary_identity='DERIVED_SOURCE_REFERENCED_ORDER_REQUIRES_EXPLICIT_ADAPTER',
                    public_profile_watermark='SAVED_PROFILES_AND_DERIVED_CUT_NOT_NATIVE_WATERMARK',
                    trusted_sensor_authority_state='SAVED_ACTUAL_DECLARATION_SCHEDULE_NOT_QM_AUTHORITY',
                    original_policy_view_digest=digest(current),
                    certification='NOT_ADMITTED_BY_IMP2A_SYNTHETIC_ONLY_VALIDATOR'),
                source_refs=dict(physical=f'{DIRECTORY}R_D{tick-20}.json#/step/checkpoint_after',
                                 public=f'{DIRECTORY}R_D{tick}.json#/policy_input',
                                 economics=f'{DIRECTORY}R_D{tick-20}.json#/step/frames/-1/metrics'))


def recover_actual_cut(bound_archive, tick):
    """Return a reconstruction audit, not real-source or full-trusted admission."""
    try:
        docs = checked_documents(bound_archive)
        data = _recover_documents(docs, tick)
        if tick == 60:
            seed = bound_archive.d60_reference_seed()
            pairs = (('consumer_states', 'internal_states_at_D60'), ('accepted_position_history', 'accepted_position_history'),
                     ('pending_observations', 'pending_observations'), ('consumed_records', 'consumed_records'),
                     ('accepted_receipts', 'accepted_receipts'), ('frozen_public_beliefs', 'frozen_policy_beliefs_at_D60'))
            _require(all(json.loads(json.dumps(data[a])) == seed[b] for a, b in pairs), 'D60_INDEPENDENT_SEED_MISMATCH')
        data['archive_binding'] = bound_archive.references()
        return dict(status='ARCHIVED_ACTUAL_CUT_RECONSTRUCTION_PASS', cut_tick=tick,
                    archive_bytes='ARCHIVE_BYTES_BOUND', real_source_authentication='NOT_VERIFIED',
                    full_trusted_cut='NOT_VERIFIED',
                    imp2a_compatibility='NOT_ADMITTED_REAL_ARCHIVE_REQUIRES_SEPARATE_PROVIDER_AND_SCHEMA_ADAPTER',
                    cut=ReconstructedActualCut(json.dumps(data, sort_keys=True, allow_nan=False)))
    except (ArchiveBindingError, ReconstructionError) as exc:
        return dict(status='ARCHIVED_ACTUAL_CUT_RECONSTRUCTION_FAIL', reason=str(exc))
    except (KeyError, TypeError, ValueError, IndexError, StopIteration, OverflowError):
        return dict(status='ARCHIVED_ACTUAL_CUT_RECONSTRUCTION_FAIL', reason='ARCHIVE_STRUCTURE_OR_PREFIX_INCOMPLETE')
