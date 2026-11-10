"""IMP-2A detached public projection; no sensing, scoring or physical evolution.

Only the cut validator grants the projection capability. This is an API access
boundary, not a cryptographic authentication scheme or a Python sandbox.
"""
from copy import deepcopy
from dataclasses import dataclass
import json
import math

from pursuit_v2.config import Config
from pursuit_v2.service import ServiceState
from .stfbs_lite_candidates import applicability
from .stfbs_d1a_replay import digest

PROJECTION_AUTHORITY = object()
REAL_A2_CANDIDATE_SCORE = 'REAL_A2_CANDIDATE_SCORE'
TRUSTED_MODEL_CONDITIONAL_VALUE = 'TRUSTED_MODEL_CONDITIONAL_VALUE'
ANN_FIELDS = ('id', 'announcement_tick', 'birth', 'weight', 'deadline', 'service_duration',
              'required_robots', 'coarse_position', 'velocity_prior', 'design_error_bound',
              'motion_model', 'speed_limit')
BELIEF_FIELDS = ('target_id', 'estimate_tick', 'available_tick', 'position_estimate',
                 'velocity_estimate', 'velocity_source', 'last_observation_tick', 'source', 'status')


class ProjectionError(ValueError):
    """Contains a fixed public status code only, never private payload values."""


def _require(condition, code='INVALID_PUBLIC_SOURCE'):
    if not condition:
        raise ProjectionError(code)


def _vector(value):
    _require(type(value) is list and len(value) == 2 and all(
        type(x) in (int, float) and math.isfinite(x) for x in value))
    return [float(x) for x in value]


def _scalar(value):
    _require(value is None or type(value) in (str, int, float, bool))
    _require(type(value) is not float or math.isfinite(value))
    return value


def _public_payload(cut):
    """Internal projection of a validated cut, also used to compute its binding.

    Source maps use the existing JSON target-ID representation (string keys).
    No consumer internals, pending results or sensor-authority fields are read.
    """
    tick = cut['cut_tick']
    source = cut['public_source']
    policy = source['policy_view']
    cfg = Config(**policy['config'])
    _require(policy['tick'] == tick)
    announcements = source['published_announcements']
    _require(all(set(ANN_FIELDS) <= set(a) for a in announcements),
             'PUBLIC_ANNOUNCEMENT_FIELDS_MISSING')
    announced = {}
    for a in announcements:
        _require(type(a['id']) is int and a['id'] >= 0 and a['id'] not in announced)
        _require(type(a['announcement_tick']) is int and a['announcement_tick'] <= tick)
        _require(a['motion_model'] == 'constant_velocity', 'UNSUPPORTED_PUBLIC_MOTION_MODEL')
        row = {k: _scalar(a[k]) for k in ANN_FIELDS if k not in ('coarse_position', 'velocity_prior')}
        row.update(coarse_position=_vector(a['coarse_position']), velocity_prior=_vector(a['velocity_prior']))
        _require(type(row['required_robots']) is int and row['required_robots'] > 0)
        _require(all(type(row[k]) in (int, float) and math.isfinite(row[k]) and row[k] > 0
                     for k in ('weight', 'service_duration')))
        _require(all(type(row[k]) in (int, float) and math.isfinite(row[k]) and row[k] >= 0
                     for k in ('speed_limit', 'design_error_bound')))
        _require(row['birth'] == row['announcement_tick']*.05 and row['deadline'] >= row['birth'])
        announced[a['id']] = row
    active = sorted(int(j) for j, status in cut['terminal_status'].items() if status == 'active')
    _require(set(source['visible_ids']) == set(active))
    _require({t['id'] for t in policy['targets']} == set(active))
    targets, beliefs, clocks, endpoints, quality = [], {}, {}, {}, {}
    for j in active:
        _require(j in announced, 'PUBLIC_ANNOUNCEMENT_FIELDS_MISSING')
        target = announced[j]
        supplied = next(t for t in policy['targets'] if t['id'] == j)
        _require(all(k in supplied and supplied[k] == target[k] for k in ANN_FIELDS))
        targets.append(target)
        b = cut['frozen_public_beliefs'][str(j)]
        _require(set(BELIEF_FIELDS) <= set(b))
        _require(b['target_id'] == j and b['estimate_tick'] <= tick and b['available_tick'] <= tick)
        _require(b['source'] in ('PUBLIC_PRIOR', 'ACTUAL_WLS')
                 and b['status'] in ('PRIOR_ONLY', 'OBSERVED', 'DEGRADED')
                 and b['velocity_source'] in ('PUBLIC_PRIOR', 'ACTUAL_POSITION_DIFFERENCE'))
        public_b = {k: _scalar(b[k]) for k in BELIEF_FIELDS if k not in ('position_estimate', 'velocity_estimate')}
        public_b.update(position_estimate=_vector(b['position_estimate']), velocity_estimate=_vector(b['velocity_estimate']))
        beliefs[str(j)] = public_b
        history = cut['task_histories'][str(j)]
        sid = history['active_segment_id']
        segment = next((s for s in history['segments'] if s['segment_id'] == sid), None)
        if segment is None:
            clocks[str(j)] = dict(base=0., intervals=0, team=[])
            endpoints[str(j)], quality[str(j)] = None, 'UNKNOWN'
        else:
            raw, ep = segment['latest_clock'], segment['latest_endpoint']
            members = [[m['robot_id'], m['role']] for m in segment['team']]
            clocks[str(j)] = dict(base=float(raw['base']), intervals=raw['intervals'], team=members)
            endpoints[str(j)] = dict(tick=ep['tick'], team=members, G=ep['G'],
                                      Q=ep['quality']['status'], source='RECORDED_PUBLIC_ENDPOINT')
            quality[str(j)] = ep['quality']['status']
    watermark = cut['public_profile_watermark']
    _require(type(watermark) is int and 0 <= watermark <= tick)
    profiles = source['published_profiles']
    _require(len(profiles) == cfg.robots)
    public_profiles = {}
    for i, profile in enumerate(profiles):
        _require(profile['sensor_id'] == f'U{i}' and type(profile['observed_tick']) is int
                 and profile['observed_tick'] <= watermark and profile['observed_tick'] >= 0)
        _require(type(profile['sigma']) in (float, int) and math.isfinite(profile['sigma']) and profile['sigma'] > 0)
        _require(profile['health'] in ('available', 'unavailable'))
        public_profiles[str(i)] = {k: _scalar(profile[k]) for k in ('sensor_id', 'observed_tick', 'sigma', 'health')}
    attempts = source['attempted_ticks']
    _require(all(type(k) is int and k in (60, 80, 100) and k < tick for k in attempts)
             and len(attempts) == len(set(attempts)))
    assignment = [{k: _scalar(a[k]) for k in ('target', 'role')} for a in cut['current_assignment']]
    _require(policy['assignment'] == cut['current_assignment'])
    return dict(tick=tick, config=cfg.to_dict(), positions=[_vector(x) for x in policy['positions']],
                assignment=assignment, targets=targets, beliefs=beliefs, service_states=clocks,
                current_endpoints=endpoints, current_q=quality, public_profiles=public_profiles,
                active_ids=active, visible_ids=active, attempted_ticks=list(attempts),
                public_provenance='LEGAL_PUBLIC_SNAPSHOT')


@dataclass(frozen=True, init=False)
class PublicDecisionSnapshot:
    _json: str
    evidence_kind: str

    def __init__(self, payload, evidence_kind, *, authority=None):
        if authority is not PROJECTION_AUTHORITY:
            raise ProjectionError('VERIFIED_PROJECTION_REQUIRED')
        object.__setattr__(self, '_json', json.dumps(payload, sort_keys=True, allow_nan=False))
        object.__setattr__(self, 'evidence_kind', evidence_kind)

    @property
    def snapshot_digest(self):
        return digest(json.loads(self._json))

    def to_view(self):
        view = json.loads(self._json)
        for field in ('beliefs', 'service_states', 'current_endpoints', 'current_q', 'public_profiles'):
            view[field] = {int(j): value for j, value in view[field].items()}
        view['service_states'] = {j: ServiceState(raw['base'], raw['intervals'], tuple(map(tuple, raw['team'])))
                                  for j, raw in view['service_states'].items()}
        for ep in view['current_endpoints'].values():
            if ep is not None:
                ep['team'] = tuple(map(tuple, ep['team']))
        return deepcopy(view)

    @property
    def applicability(self):
        return applicability(self.to_view())
