"""Synchronous post-freeze structural capture. No real-source authentication.

Caller must own exclusive single-threaded access during capture. Repeated reads
detect changes; they do not implement a lock or prove absence of ABA mutation.
"""
from copy import deepcopy
import math

from .stfbs_d1a_replay import digest
from research.information_service_online.public import validate_schema

PUBLIC_FIELDS = {'kind', 'tick', 'end_tick', 'config', 'positions', 'assignment',
                 'sensor_profiles', 'targets', 'beliefs', 'histories', 'current_slots',
                 'first_policy_visible_ticks'}
ANN_FIELDS = {'id', 'announcement_tick', 'birth', 'weight', 'deadline', 'service_duration',
              'required_robots', 'coarse_position', 'velocity_prior', 'design_error_bound',
              'motion_model', 'speed_limit'}
BELIEF_FIELDS = {'target_id', 'estimate_tick', 'available_tick', 'position_estimate',
                 'velocity_estimate', 'velocity_source', 'last_observation_tick', 'source', 'status', 'diagnostics'}
DIAGNOSTIC_KEYS = {'starts', 'has_accepted_estimate', 'estimate', 'optimizer_converged',
    'numerical_ill_conditioned', 'ambiguity_detected', 'boundary_active', 'branch_guard_triggered',
    'numeric_contract_violation', 'selected_start', 'Q', 'singular_values', 'start_id', 'start',
    'accepted', 'guard', 'status', 'success', 'optimality', 'nfev', 'njev', 'active_mask', 'cost',
    'x', 'evaluation_calls', 'fun', 'jac', 'phase', 'sensor_id', 'residual', 'jacobian', 'reason', 'estimate_available'}


class LiveCutRejected(ValueError):
    """Fixed codes only; never expose private payloads in exceptions."""


def _require(condition, code):
    if not condition:
        raise LiveCutRejected(code)


def _plain(value, *, diagnostic=False):
    if type(value) is dict:
        if diagnostic:
            _require(set(value) <= DIAGNOSTIC_KEYS, 'UNRECOGNIZED_PUBLIC_DIAGNOSTICS')
        for child in value.values():
            _plain(child, diagnostic=diagnostic)
    elif type(value) in (list, tuple):
        for child in value:
            _plain(child, diagnostic=diagnostic)
    else:
        _require(value is None or type(value) in (str, bool, int, float), 'NON_DATA_OBJECT_REJECTED')
        _require(type(value) is not float or math.isfinite(value), 'NONFINITE_STATE')


def _read(env):
    snapshot = deepcopy(env.private_snapshot())
    consumer = {field: deepcopy(getattr(env.beliefs, attr)) for field, attr in (
        ('consumer_states', 'states'), ('accepted_position_history', 'history'),
        ('pending_observations', 'pending'), ('consumed_records', 'consumed'),
        ('accepted_receipts', 'accepted_receipts'), ('announcements', 'announcements'))}
    control = dict(tick=env.tick, decision_tick=env.decision_tick, frozen=deepcopy(env.frozen),
                   boundary_committed_tick=env._boundary_committed_tick,
                   inflight=deepcopy(env.journal.inflight), failed=env.failed, done=env.done,
                   physical_environment_id=env.physical_environment_id, source_identity=env.source_identity,
                   first_policy_visible_ticks=deepcopy(env.first_visible_ticks))
    _plain((snapshot, consumer, control))
    return dict(snapshot=snapshot, consumer=consumer, control=control)


def _validate(read, view):
    snap, consumer, control = read['snapshot'], read['consumer'], read['control']
    tick = control['tick']
    _require(type(tick) is int and tick in (60, 80, 100), 'ILLEGAL_CUT_TICK')
    _require(control['decision_tick'] == tick and control['frozen'] is not None, 'CUT_NOT_FROZEN')
    _require(control['boundary_committed_tick'] != tick and snap['boundary_committed_tick'] != tick,
             'ASSIGNMENT_ALREADY_COMMITTED')
    _require(control['inflight'] is None and snap['inflight'] is None, 'TRANSACTION_IN_PROGRESS')
    _require(control['failed'] is False and snap['failed'] is False and control['done'] is False,
             'EXECUTOR_NOT_LIVE')
    _require(snap['snapshot_digest'] == digest({k: v for k, v in snap.items() if k != 'snapshot_digest'}),
             'PRIVATE_SNAPSHOT_DIGEST_CONFLICT')
    cp, state = snap['checkpoint'], snap['state']
    _require(cp['phase'] == 'DECISION_READY' and cp['tick'] == state['tick'] == tick, 'CHECKPOINT_PHASE_CONFLICT')
    _require(cp['checkpoint_id'] == digest({k: v for k, v in cp.items() if k != 'checkpoint_id'}),
             'CHECKPOINT_IDENTITY_CONFLICT')
    _require(snap['physical_environment_id'] == control['physical_environment_id']
             and snap['source_identity'] == control['source_identity'] == digest(snap['case']), 'SOURCE_IDENTITY_CONFLICT')
    _require(set(view) == PUBLIC_FIELDS and view['kind'] == 'A2_POLICY_INPUT' and view['tick'] == tick,
             'PUBLIC_VIEW_SCHEMA_CONFLICT')
    _require(view['end_tick'] == cp['episode_end_tick'], 'PUBLIC_END_TICK_CONFLICT')
    for a, b in (('positions', 'positions'), ('assignment', 'assignment'), ('config', 'config'),
                 ('histories', 'task_histories'), ('current_slots', 'current_slots'), ('sensor_profiles', 'sensor_profiles')):
        _require(view[a] == cp[b], 'PUBLIC_CHECKPOINT_CONFLICT')
    _require(state['positions'] == cp['positions'] and state['assignment'] == cp['assignment'], 'PHYSICAL_STATE_CONFLICT')
    for history in view['histories']:
        validate_schema(history, 'TaskHistory')
    for slot in view['current_slots']:
        validate_schema(slot, 'MeasurementSlot')
    for action in view['assignment']:
        validate_schema(action, 'Assignment')
    active = [j for j, status in enumerate(state['statuses']) if status == 'active']
    _require([a['id'] for a in view['targets']] == active == [a['id'] for a in cp['targets']], 'VISIBLE_TARGET_CONFLICT')
    _require([state['histories'][str(j)] for j in active] == view['histories'], 'SERVICE_HISTORY_CONFLICT')
    announced = {a['id']: a for a in consumer['announcements'] if a['announcement_tick'] <= tick}
    for target in view['targets']:
        _require(set(target) == ANN_FIELDS and target['id'] in announced
                 and all(target[k] == announced[target['id']][k] for k in ANN_FIELDS), 'PUBLIC_ANNOUNCEMENT_CONFLICT')
    _require(view['beliefs'] == control['frozen'], 'PUBLIC_FROZEN_BELIEF_CONFLICT')
    for belief in view['beliefs'].values():
        _require(set(belief) == BELIEF_FIELDS, 'PUBLIC_BELIEF_SCHEMA_CONFLICT')
        _plain(belief['diagnostics'], diagnostic=True)
    _require(view['first_policy_visible_ticks'] == control['first_policy_visible_ticks'], 'VISIBILITY_HISTORY_CONFLICT')
    for i, profile in enumerate(view['sensor_profiles']):
        _require(set(profile) == {'sensor_id', 'sigma', 'health', 'observed_tick'}
                 and profile['sensor_id'] == f'U{i}' and profile['observed_tick'] <= tick
                 and profile['health'] in ('available', 'missing'), 'PUBLIC_PROFILE_CONFLICT')
    # Frozen output differs from internal states only by the production's
    # age-based public status projection. No freeze or consumption is repeated.
    frozen = deepcopy(consumer['consumer_states'])
    for b in frozen.values():
        if b['last_observation_tick'] is not None and tick-b['last_observation_tick'] > 20:
            b['status'] = 'DEGRADED'
    _require(frozen == control['frozen'], 'INTERNAL_FROZEN_STATE_CONFLICT')
    consumed = consumer['consumed_records']
    keys = [(r['target_id'], r['measurement_tick'], r['available_tick']) for r in consumed]
    _require(len(keys) == len(set(keys)) and all(r['consumed_tick'] <= tick for r in consumed), 'CONSUMED_RECORD_CONFLICT')
    _require([r['consumed_tick'] for r in consumed] == sorted(r['consumed_tick'] for r in consumed), 'CONSUMPTION_ORDER_CONFLICT')
    pending_keys = [(r['target_id'], r['measurement_tick'], r['available_tick']) for r in consumer['pending_observations']]
    _require(len(pending_keys) == len(set(pending_keys)) and not set(keys).intersection(pending_keys), 'PENDING_RECORD_CONFLICT')
    for j, receipt in consumer['accepted_receipts'].items():
        history = consumer['accepted_position_history'][j]
        _require(receipt in consumed and history and receipt['measurement_tick'] == history[-1][0]
                 and receipt['target_id'] == int(j), 'ACCEPTED_RECEIPT_CONFLICT')
    _require(snap['sampler']['physical_environment_id'] == control['physical_environment_id'], 'SAMPLER_IDENTITY_CONFLICT')
    for row in snap['sampler']['entries']:
        key = row['raw_key']
        _require(len(key) == 4 and key[0] == control['physical_environment_id'] and key[3] <= tick,
                 'RAW_KEY_CONFLICT')
    _require(all(commit['start_tick'] < tick for commit in snap['action_commits']), 'ASSIGNMENT_ALREADY_COMMITTED')
    return cp


def capture_live_cut(env, view):
    """Capture under caller-owned single-thread synchronous access, or reject.

    Two complete detached reads cover mutable data, counters and identities.
    No claim is made about a native episode-wide arrival/freeze journal.
    """
    try:
        first = _read(env)
        public = deepcopy({k: view[k] for k in PUBLIC_FIELDS})
        _require(set(view) == PUBLIC_FIELDS, 'PUBLIC_VIEW_SCHEMA_CONFLICT')
        _plain(public)
        cp = _validate(first, public)
        second = _read(env)
        _require(first == second, 'EXECUTOR_CHANGED_DURING_CAPTURE')
        _require(view == public, 'PUBLIC_VIEW_CHANGED_DURING_CAPTURE')
        private = deepcopy(first)
        private.update(cut_phase='POST_FREEZE_PRE_ASSIGNMENT',
                       causal_evidence=dict(order_kind='DERIVED', native_arrival_journal='NOT_VERIFIED',
                           complete_causal_order='NOT_VERIFIED', ordinals_issued=False,
                           relations=[dict(relation='CURRENT_BELIEF_FROZEN_BEFORE_NEW_ASSIGNMENT',
                               sources=['control.decision_tick', 'control.frozen', 'snapshot.boundary_committed_tick',
                                        'snapshot.action_commits', 'snapshot.checkpoint'],
                               rule='matched decision tick, no current commit, DECISION_READY checkpoint')]),
                       public_profile_watermark='NOT_VERIFIED_OBSERVED_TICK_IS_NOT_PUBLICATION_AUTHORITY')
        return dict(status='LIVE_CUT_STRUCTURAL_CAPTURE_PASS', private_live_cut=private,
                    public_policy_view=deepcopy(public), private_digest=digest(private), public_digest=digest(public),
                    checkpoint_id=cp['checkpoint_id'], execution_assumption='EXCLUSIVE_SINGLE_THREAD_SYNCHRONOUS',
                    real_actual_live_cut='NOT_RUN', real_source_authentication='NOT_VERIFIED',
                    full_trusted_cut='NOT_VERIFIED', real_model_initialization='NOT_VERIFIED')
    except LiveCutRejected as exc:
        return dict(status='LIVE_CUT_STRUCTURAL_CAPTURE_FAIL', reason=str(exc))
    except (KeyError, TypeError, ValueError, AttributeError, IndexError):
        return dict(status='LIVE_CUT_STRUCTURAL_CAPTURE_FAIL', reason='INCOMPLETE_OR_INVALID_EXECUTOR_STATE')
