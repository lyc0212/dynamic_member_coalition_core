"""IMP-2A post-freeze import/validation only; never runs a physical branch.

The supported trust provider is explicitly synthetic. A future production
provider must authenticate external roots outside the submitted state; declaring
a real-looking evidence string in a local object cannot activate that provider.
"""
from copy import deepcopy
from dataclasses import dataclass
import json
import math

from pursuit_v2.config import Config
from pursuit_v2.service import ServiceState
from .stfbs_d1a_replay import digest
from .stfbs_d1a_history_audit import audit_histories
from .stfbs_lite_candidates import assignment_key
from .stfbs_lite_public_adapter import (PublicDecisionSnapshot, ProjectionError,
                                       PROJECTION_AUTHORITY, _public_payload)

PHASE = 'POST_FREEZE_PRE_ASSIGNMENT'
SYNTHETIC_ROOT = 'SYNTHETIC_TRUST_ROOT_NOT_REAL_EXECUTION_EVIDENCE'
SYNTHETIC_CUT = 'SYNTHETIC_TRUSTED_CUT_FIXTURE_NOT_PHYSICAL_EVIDENCE'
REQUIRED = {
    'episode_id', 'cut_tick', 'cut_phase', 'source_identity', 'trusted_prefix_digest',
    'public_snapshot_digest', 'freeze_boundary_identity', 'physical_cut_state',
    'current_assignment', 'terminal_status', 'task_histories', 'service_segments',
    'consumer_states', 'accepted_position_history', 'pending_observations',
    'consumed_records', 'accepted_receipts', 'frozen_public_beliefs', 'raw_cache_history',
    'current_slots', 'public_profile_watermark', 'trusted_sensor_authority_state',
    'settled_economic_components', 'change_cost_so_far', 'public_source',
    'observation_arrivals', 'freeze_boundaries', 'evidence_kind',
}


class CutRejected(ValueError):
    """Fixed reason codes only: never put a private value into an exception."""


def _require(condition, code='CUT_STRUCTURE_CONFLICT'):
    if not condition:
        raise CutRejected(code)


def _plain(value):
    """Existing JSON representation only; no live executor/authority objects."""
    if type(value) is dict:
        _require(all(type(k) is str for k in value), 'PLAIN_JSON_REQUIRED')
        for child in value.values():
            _plain(child)
    elif type(value) is list:
        for child in value:
            _plain(child)
    else:
        _require(value is None or type(value) in (str, int, float, bool), 'PLAIN_JSON_REQUIRED')
        _require(type(value) is not float or math.isfinite(value), 'NONFINITE_CUT_STATE')


def cut_prefix_digest(state):
    """Binding recipe, not a source authenticator. Includes the public digest."""
    _plain(state)
    return digest({k: v for k, v in state.items() if k != 'trusted_prefix_digest'})


@dataclass(frozen=True)
class ExternalTrustRoot:
    expected_episode_id: str
    expected_source_identity: str
    expected_cut_tick: int
    expected_cut_phase: str
    expected_trusted_prefix_digest: str
    expected_public_snapshot_digest: str
    expected_freeze_boundary: str
    evidence_kind: str


@dataclass(frozen=True)
class TrustedModelCutState:
    """Detached, immutable serialized cut; no runnable branch or public export."""
    _json: str
    evidence_kind: str

    def to_restore_payload(self):
        """Trusted-only future initializer input, not an IMP-1 policy view."""
        return json.loads(self._json)


def _validate_consumer(cut):
    tick = cut['cut_tick']
    boundary = cut['freeze_boundary_identity']
    _require(boundary['cut_tick'] == tick and type(boundary['freeze_ordinal']) is int)
    freezes = cut['freeze_boundaries']
    _require(freezes[str(tick)] == boundary['freeze_ordinal'])
    freeze_ticks = sorted(int(k) for k in freezes)
    _require(all(0 <= k <= tick and type(freezes[str(k)]) is int for k in freeze_ticks))
    _require([freezes[str(k)] for k in freeze_ticks] == sorted(set(freezes.values())))
    journal = cut['observation_arrivals']
    ordinals = [r['arrival_ordinal'] for r in journal]
    _require(all(type(n) is int and n >= 0 for n in ordinals) and ordinals == sorted(set(ordinals)))
    pending, consumed = [], []
    for entry in journal:
        row = entry['observation']
        _require(row['source'] == 'ACTUAL' and str(row['target_id']) in cut['consumer_states'])
        _require(all(type(row[k]) is int for k in ('measurement_tick', 'available_tick')))
        _require(0 <= row['measurement_tick'] <= tick and row['measurement_tick'] <= row['available_tick'])
        # Future delivery is permitted for already occurred measurements.
        ct = entry['consumed_tick']
        eligible = [k for k in freeze_ticks if row['available_tick'] <= k
                    and entry['arrival_ordinal'] < freezes[str(k)]]
        expected = eligible[0] if eligible else None
        _require(ct == expected, 'OBSERVATION_FREEZE_BOUNDARY_CONFLICT')
        if ct is None:
            pending.append(deepcopy(row))
        else:
            _require(type(ct) is int)
            consumed.append(dict(target_id=row['target_id'], measurement_tick=row['measurement_tick'],
                                 available_tick=row['available_tick'], consumed_tick=ct))
    # Consumer processes queued rows in arrival order at each freeze.
    consumed.sort(key=lambda row: row['consumed_tick'])
    _require(cut['pending_observations'] == pending, 'PENDING_QUEUE_CONFLICT')
    _require(cut['consumed_records'] == consumed, 'CONSUMED_ORDER_CONFLICT')
    identities = [(r['target_id'], r['measurement_tick'], r['available_tick']) for r in consumed]
    _require(len(identities) == len(set(identities)), 'DUPLICATE_CONSUMPTION')
    states = cut['consumer_states']
    _require(set(states) == set(cut['accepted_position_history']) == set(cut['frozen_public_beliefs']))
    projected = deepcopy(states)
    for j, b in states.items():
        _require(b['target_id'] == int(j) and b['estimate_tick'] <= tick and b['available_tick'] <= tick)
        history = cut['accepted_position_history'][j]
        times = [r[0] for r in history]
        _require(times == sorted(set(times)) and all(type(k) is int and k <= tick for k in times))
        for when, position in history:
            matches = [e for e in journal if e['consumed_tick'] is not None
                       and e['observation']['target_id'] == int(j)
                       and e['observation']['measurement_tick'] == when]
            _require(len(matches) == 1 and matches[0]['observation']['estimate'] is not None)
            estimate = matches[0]['observation']['estimate']
            _require(estimate.get('has_accepted_estimate') is True
                     and estimate.get('optimizer_converged') is True
                     and all(estimate.get(k, True) is False for k in (
                         'numerical_ill_conditioned', 'ambiguity_detected', 'boundary_active', 'numeric_contract_violation'))
                     and estimate['estimate'] == position, 'ACCEPTED_HISTORY_CONFLICT')
        if history:
            _require(b['estimate_tick'] == history[-1][0] and b['position_estimate'] == history[-1][1])
            receipt = cut['accepted_receipts'][j]
            _require(receipt in consumed and receipt['target_id'] == int(j)
                     and receipt['measurement_tick'] == history[-1][0], 'ACCEPTED_RECEIPT_CONFLICT')
        else:
            _require(j not in cut['accepted_receipts'] and b['last_observation_tick'] is None)
        if b['last_observation_tick'] is not None and tick-b['last_observation_tick'] > 20:
            projected[j]['status'] = 'DEGRADED'
    _require(set(cut['accepted_receipts']) <= set(states))
    _require(projected == cut['frozen_public_beliefs'], 'FROZEN_BELIEF_CONFLICT')
    _require(boundary['consumer_digest'] == digest(dict(states=states,
             history=cut['accepted_position_history'], consumed=cut['consumed_records'],
             receipts=cut['accepted_receipts'])), 'FREEZE_CONSUMER_IDENTITY_CONFLICT')


def _validate_histories_and_raw(cut):
    tick = cut['cut_tick']
    histories = {int(j): h for j, h in cut['task_histories'].items()}
    statuses = {int(j): status for j, status in cut['terminal_status'].items()}
    _require(set(histories) == set(statuses))
    _require(all(s in ('active', 'completed', 'escaped', 'unfinished') for s in statuses.values()))
    terminal_times = {}
    for j, h in histories.items():
        _require(h['target_id'] == j)
        if statuses[j] != 'active':
            events = [e for e in h['events'] if e['kind'] in ('COMPLETED', 'ESCAPED', 'EPISODE_END')]
            _require(len(events) == 1)
            terminal_times[j] = events[0]['at']['time_seconds']
        # Current-cut assignment transactions would already violate PRE_ASSIGNMENT.
        _require(not any(e['kind'] in ('ASSIGNED', 'WITHDRAWN', 'TEAM_CHANGED', 'ROLE_CHANGED')
                         and e['at']['time_seconds'] == tick*.05 for e in h['events']),
                 'CURRENT_CUT_ASSIGNMENT_ALREADY_COMMITTED')
    audit_histories(histories, cut['current_assignment'], statuses, tick, terminal_times)
    segments = [s for j in sorted(histories) for s in histories[j]['segments']]
    _require(segments == cut['service_segments'], 'SERVICE_SEGMENT_CONFLICT')
    slots = {}
    for h in histories.values():
        for segment in h['segments']:
            clock = segment['latest_clock']
            ServiceState(clock['base'], clock['intervals'], tuple((m['robot_id'], m['role']) for m in clock['team']))
            ep = segment['latest_endpoint']
            _require(type(ep['G']) is bool and ep['quality']['status'] in ('PASS', 'FAIL', 'UNKNOWN'))
            _require(ep['target_id'] == h['target_id'] and ep['team'] == segment['team'])
            for slot in ep['slots']:
                key = tuple(slot['slot_key'][k] for k in ('target_id', 'robot_id', 'tick'))
                _require(key not in slots or slots[key] == slot, 'RAW_SLOT_CONFLICT')
                slots[key] = slot
    current = cut['current_slots']
    active = sorted(j for j, status in statuses.items() if status == 'active')
    expected = [(j, i, tick) for j in active for i in range(3)]
    _require([tuple(s['slot_key'][k] for k in ('target_id', 'robot_id', 'tick')) for s in current] == expected)
    for slot in current:
        key = tuple(slot['slot_key'][k] for k in ('target_id', 'robot_id', 'tick'))
        _require(key not in slots or slots[key] == slot, 'RAW_SLOT_CONFLICT')
        slots[key] = slot
    cache = {}
    for row in cut['raw_cache_history']:
        slot = row['slot']
        key = tuple(slot['slot_key'][k] for k in ('target_id', 'robot_id', 'tick'))
        _require(key not in cache and 0 <= key[2] <= tick and key[0] in histories
                 and type(key[1]) is int and 0 <= key[1] < 3, 'RAW_CACHE_IDENTITY_CONFLICT')
        _require(row['slot_digest'] == digest(slot) and row['context_digest'] == digest(row['context']))
        _require(row['context']['episode_id'] == cut['episode_id'])
        _require(slot['state'] in ('VALID', 'MISSING'), 'INVALID_RAW_STATE')
        cache[key] = slot
    for key, slot in slots.items():
        _require(slot['state'] in ('VALID', 'MISSING', 'UNQUERIED'))
        if slot['state'] != 'UNQUERIED':
            _require(cache.get(key) == slot, 'RAW_CACHE_SLOT_CONFLICT')
        else:
            _require(key not in cache, 'UNQUERIED_RAW_CACHE_CONFLICT')


def verify_trusted_cut(candidate_cut_state, *, trusted_root=None, requested_certification=None):
    """Structural interface verification, never authenticates a real execution."""
    if type(trusted_root) is not ExternalTrustRoot:
        return dict(status='EXTERNAL_TRUST_ROOT_REQUIRED')
    if trusted_root.evidence_kind != SYNTHETIC_ROOT:
        return dict(status='REAL_TRUST_PROVIDER_NOT_CONFIGURED')
    if requested_certification not in (None, SYNTHETIC_CUT):
        return dict(status='REAL_CERTIFICATION_NOT_AVAILABLE')
    try:
        cut = candidate_cut_state
        _plain(cut)
        _require(set(cut) == REQUIRED, 'CUT_FIELDS_MISSING_OR_UNRECOGNIZED')
        root = trusted_root
        expected = (root.expected_episode_id, root.expected_source_identity, root.expected_cut_tick,
                    root.expected_cut_phase, root.expected_trusted_prefix_digest,
                    root.expected_public_snapshot_digest, root.expected_freeze_boundary)
        actual = (cut['episode_id'], cut['source_identity'], cut['cut_tick'], cut['cut_phase'],
                  cut_prefix_digest(cut), cut['public_snapshot_digest'], digest(cut['freeze_boundary_identity']))
        _require(actual == expected and cut['trusted_prefix_digest'] == expected[4], 'EXTERNAL_ROOT_IDENTITY_CONFLICT')
        _require(type(cut['cut_tick']) is int and cut['cut_tick'] in (60, 80, 100)
                 and cut['cut_phase'] == PHASE and cut['evidence_kind'] == SYNTHETIC_CUT)
        physical = cut['physical_cut_state']
        public = cut['public_source']['policy_view']
        _require(physical['tick'] == cut['cut_tick'] and physical['positions'] == public['positions']
                 and physical['assignment'] == cut['current_assignment'] == public['assignment']
                 and physical['terminal_status'] == cut['terminal_status'])
        assignment_key(cut['current_assignment'])
        Config(**public['config'])
        _require(public['beliefs'] == cut['frozen_public_beliefs'], 'PUBLIC_FROZEN_BELIEF_CONFLICT')
        if (public['config']['robots'] != 3
                or any(t['required_robots'] != 2 for t in public['targets'])):
            return dict(status='NOT_APPLICABLE', real_causal_restore_verified=False)
        _validate_consumer(cut)
        _validate_histories_and_raw(cut)
        _require(physical['settled_economic_components'] == cut['settled_economic_components']
                 and physical['change_cost_so_far'] == cut['change_cost_so_far'])
        _require(set(cut['settled_economic_components']) == {'completion', 'flow', 'late', 'effort', 'terminal'})
        _require(all(type(v) in (int, float) and math.isfinite(v) for v in cut['settled_economic_components'].values()))
        _require(type(cut['change_cost_so_far']) in (int, float) and cut['change_cost_so_far'] >= 0)
        _require(cut['trusted_sensor_authority_state']['published_watermark'] == cut['public_profile_watermark'])
        payload = _public_payload(cut)
        _require(digest(payload) == root.expected_public_snapshot_digest, 'PUBLIC_SNAPSHOT_IDENTITY_CONFLICT')
        return dict(status='SYNTHETIC_CUT_INTERFACE_VERIFIED', evidence_kind=SYNTHETIC_CUT,
                    real_causal_restore_verified=False)
    except ProjectionError as exc:
        return dict(status=str(exc))
    except CutRejected as exc:
        return dict(status=str(exc))
    except (KeyError, TypeError, ValueError, IndexError, StopIteration, OverflowError):
        return dict(status='CUT_STRUCTURE_CONFLICT')


def import_verified_cut(trusted_cut_snapshot, *, trusted_root=None, requested_certification=None):
    result = verify_trusted_cut(trusted_cut_snapshot, trusted_root=trusted_root,
                                requested_certification=requested_certification)
    if result['status'] != 'SYNTHETIC_CUT_INTERFACE_VERIFIED':
        return result
    detached = deepcopy(trusted_cut_snapshot)
    public = PublicDecisionSnapshot(_public_payload(detached), SYNTHETIC_CUT, authority=PROJECTION_AUTHORITY)
    return dict(result, public_snapshot=public, applicability=public.applicability,
                trusted_state=TrustedModelCutState(json.dumps(detached, sort_keys=True, allow_nan=False), SYNTHETIC_CUT),
                future_economic_origin='EXCLUDE_SETTLED_PREFIX_FROM_FUTURE_VALUE')


def recover_from_verified_history(verified_history_prefix, *, trusted_root=None):
    """No generic full-causal replay provider exists in IMP-2A.

    The old D60 belief-only recover() is deliberately not repackaged as a full
    replay. No claimed completeness flag or a supplied seed can bypass this.
    """
    if type(trusted_root) is not ExternalTrustRoot:
        return dict(status='EXTERNAL_TRUST_ROOT_REQUIRED')
    return dict(status='FULL_CAUSAL_HISTORY_PREFIX_UNAVAILABLE',
                reason='VERIFIED_FULL_CAUSAL_REPLAY_PROVIDER_NOT_CONNECTED',
                d60_belief_replay='NOT_VERIFIED', d60_full_causal_cut='NOT_VERIFIED',
                real_d80_d100_causal_restore='NOT_YET_VERIFIED')
