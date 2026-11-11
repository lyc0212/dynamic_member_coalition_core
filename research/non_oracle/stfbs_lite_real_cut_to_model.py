"""D60 schema candidate only. No branch/world/budget or execution admission.

Detached capture digests are integrity checks, not issuer authentication. Shared
LIVE CUT validation and original transaction/raw records provide independent
cross-field checks, while every real-source claim remains NOT_VERIFIED.
"""
from copy import deepcopy

from research.information_service_online import public
from .stfbs_d1a_replay import digest
from .stfbs_d1a_state import ModelBeliefConsumer
from . import stfbs_lite_live_cut as live


class MappingRejected(ValueError):
    pass


def _require(condition, code):
    if not condition:
        raise MappingRejected(code)


def _id_map(mapping):
    result = {}
    for key, value in mapping.items():
        _require(type(key) is int or type(key) is str and key.isdecimal(), 'INVALID_TARGET_ID_MAP')
        integer = int(key)
        _require(integer >= 0 and integer not in result, 'DUPLICATE_TARGET_ID_ALIAS')
        result[integer] = deepcopy(value)
    return result


def _normalize(private, view):
    private, view = deepcopy(private), deepcopy(view)
    for field in ('consumer_states', 'accepted_position_history', 'accepted_receipts'):
        private['consumer'][field] = _id_map(private['consumer'][field])
    private['control']['frozen'] = _id_map(private['control']['frozen'])
    private['control']['first_policy_visible_ticks'] = _id_map(private['control']['first_policy_visible_ticks'])
    for field in ('beliefs', 'first_policy_visible_ticks'):
        view[field] = _id_map(view[field])
    return private, view


def _raw_reference(snapshot):
    """Check original three-field context against saved positions/declarations.

    No episode tag is inserted into context. No raw cache is instantiated.
    """
    sampler = snapshot['sampler']
    positions = {f['tick']: f['positions'] for f in snapshot['frames']}
    schedule = snapshot['case']['sensor_declaration_schedule']
    entries = {}
    for row in sampler['entries']:
        key = tuple(row['raw_key'])
        _require(key not in entries and key[0] == snapshot['physical_environment_id'], 'RAW_ENVIRONMENT_OR_DUPLICATE_KEY')
        slot = row['slot']
        _require(public.seal_slot(slot) == slot and slot['slot_key'] == dict(target_id=key[1], robot_id=key[2], tick=key[3]),
                 'RAW_SLOT_IDENTITY_CONFLICT')
        profile = next(r for r in reversed(schedule) if r['effective_tick'] <= key[3])['profiles'][key[2]]
        context = dict(position=positions[key[3]][key[2]], sigma=profile['sigma'], health=profile['health'])
        _require(digest(context) == row['context_digest'], 'RAW_ORIGINAL_CONTEXT_CONFLICT')
        if slot['state'] == 'VALID':
            packet = slot['packet']
            _require(packet['position'] == context['position'] and packet['sigma'] == context['sigma']
                     and packet['sensor_id'] == f'U{key[2]}' and context['health'] == 'available'
                     and packet['measurement_tick'] == packet['available_tick'] == key[3], 'RAW_PACKET_CONTEXT_CONFLICT')
        entries[key] = slot
    for slot in snapshot['checkpoint']['current_slots']:
        k = slot['slot_key']
        key = (snapshot['physical_environment_id'], k['target_id'], k['robot_id'], k['tick'])
        _require(entries.get(key) == slot if slot['state'] != 'UNQUERIED' else key not in entries,
                 'CURRENT_HISTORICAL_SLOT_CONFLICT')
    return dict(physical_environment_id=snapshot['physical_environment_id'],
                sampler=deepcopy(sampler), namespace_role='HISTORICAL_ACTUAL_ONLY',
                model_future_raw='NOT_CREATED_SEPARATE_BRANCH_NAMESPACE_REQUIRED')


def prepare_real_cut_model_input(live_cut_result, *, source_authority=None):
    """Prepare a detached data candidate; real execution is always denied."""
    base = dict(execution_admission='MODEL_EXECUTION_ADMISSION_DENIED',
                trust_provider='REAL_TRUST_PROVIDER_NOT_CONFIGURED',
                real_source_authentication='NOT_VERIFIED', public_projection_authority='NOT_VERIFIED',
                full_trusted_cut='NOT_VERIFIED', real_model_initialization='NOT_VERIFIED',
                real_actual_live_cut='NOT_RUN')
    try:
        _require(source_authority is None, 'SOURCE_AUTHORITY_NOT_SUPPORTED')
        _require(type(live_cut_result) is dict and live_cut_result['status'] == 'LIVE_CUT_STRUCTURAL_CAPTURE_PASS',
                 'VALID_LIVE_CUT_REQUIRED')
        data = deepcopy(live_cut_result)
        private, view = data['private_live_cut'], data['public_policy_view']
        _require(private['control']['tick'] == view['tick'], 'CUT_TICK_IDENTITY_CONFLICT')
        if type(view['tick']) is int and view['tick'] in (80, 100):
            return dict(base, status='MODEL_INITIALIZATION_TICK_NOT_SUPPORTED', candidate_status='NOT_READY')
        _require(type(view['tick']) is int and view['tick'] == 60, 'MODEL_INITIALIZATION_TICK_NOT_SUPPORTED')
        _require(data['private_digest'] == digest(private) and data['public_digest'] == digest(view), 'LIVE_CUT_INTEGRITY_CONFLICT')
        _require(private['cut_phase'] == 'POST_FREEZE_PRE_ASSIGNMENT'
                 and data['checkpoint_id'] == private['snapshot']['checkpoint']['checkpoint_id'], 'CUT_PHASE_OR_CHECKPOINT_CONFLICT')
        private, view = _normalize(private, view)
        # Reuse the existing validated stage, history prefix, public schema and
        # consumer checks. Do not trust the supplied PASS string or hashes alone.
        live._plain((private, view))
        live._validate(private, view)
        snapshot, consumer = private['snapshot'], private['consumer']
        raw = _raw_reference(snapshot)
        seed = dict(internal_states_at_D60=deepcopy(consumer['consumer_states']),
                    accepted_position_history=deepcopy(consumer['accepted_position_history']),
                    pending_observations=deepcopy(consumer['pending_observations']),
                    consumed_records=deepcopy(consumer['consumed_records']),
                    accepted_receipts=deepcopy(consumer['accepted_receipts']), announcements=deepcopy(consumer['announcements']))
        # Constructor and reads only: no freeze, enqueue, fusion, assign or run.
        probe = ModelBeliefConsumer(seed)
        for attribute, field in (('states', 'internal_states_at_D60'), ('history', 'accepted_position_history'),
                                 ('pending', 'pending_observations'), ('consumed', 'consumed_records'),
                                 ('accepted_receipts', 'accepted_receipts'), ('announcements', 'announcements')):
            _require(getattr(probe, attribute) == seed[field], 'MODEL_CONSUMER_SCHEMA_MISMATCH')
        candidate = dict(a2_policy_view=deepcopy(view), consumer_seed=seed,
            physical_cut_reference=dict(physical_environment_id=snapshot['physical_environment_id'],
                source_identity=snapshot['source_identity'], checkpoint_id=data['checkpoint_id'], cut_tick=60,
                positions=deepcopy(snapshot['state']['positions']), assignment=deepcopy(snapshot['state']['assignment']),
                task_histories=deepcopy(snapshot['state']['histories'])),
            historical_raw_reference=raw,
            actual_settled_prefix=dict(components=deepcopy(snapshot['state']['components']), change_cost=snapshot['state']['change_cost']),
            model_future_increment=None, future_value_origin='EXCLUDE_SETTLED_PREFIX',
            unresolved_model_dependencies=dict(
                view='A2_POLICY_INPUT_NOT_STFBS_PUBLIC_DECISION_SNAPSHOT',
                world='D1A_WORLD_AND_STFBS_H1_H2_H3_REQUIRE_EXPLICIT_FUTURE_ADAPTATION',
                name='LEGAL_INDEPENDENT_MODEL_BRANCH_ID_NOT_ISSUED', budget='REAL_BUDGET_NOT_BOUND',
                source='INDEPENDENT_EXECUTION_SOURCE_PROVIDER_NOT_CONFIGURED',
                profiles='PRODUCTION_AVAILABLE_MISSING_PRESERVED_PUBLICATION_WATERMARK_NOT_AUTHENTICATED'))
        return dict(base, status='REAL_CUT_TO_MODEL_SCHEMA_MAPPING_PASS',
                    candidate_status='MODEL_INITIALIZATION_CANDIDATE_READY', candidate=candidate)
    except (MappingRejected, live.LiveCutRejected) as exc:
        return dict(base, status='REAL_CUT_TO_MODEL_SCHEMA_MAPPING_FAIL', candidate_status='NOT_READY', reason=str(exc))
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, StopIteration):
        return dict(base, status='REAL_CUT_TO_MODEL_SCHEMA_MAPPING_FAIL', candidate_status='NOT_READY', reason='INVALID_OR_INCOMPLETE_LIVE_CUT')
