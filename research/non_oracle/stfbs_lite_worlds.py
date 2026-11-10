"""Public conditional worlds and ordinal-based H2/H3 screening, never MODEL."""
from itertools import product
import math

from .belief import trajectory
from .stfbs_lite_candidates import digest

DT = .05
H = 120
TOL = 1e-10
WORLD_RULE_VERSION = 'STFBS_LITE_R0.2.1_P1_PUBLIC_CV_V1'


def public_input_digest(view):
    """Closed projection of the public envelope, never hash arbitrary view keys.

    Numeric floats use exact binary64 hex, with signed zero normalized. Only
    declared public scalar/vector fields are read, not diagnostics, private
    schedules, future labels, or opaque nested provenance objects.
    """
    def project(row, names):
        return {name: row[name] for name in names if name in row}

    def normalize(value):
        if type(value) is float:
            if not math.isfinite(value):
                raise ValueError('Nonfinite public input')
            return (0. if value == 0 else value).hex()
        if isinstance(value, dict):
            return {str(k): normalize(v) for k, v in value.items()}
        if isinstance(value, (tuple, list)):
            return [normalize(v) for v in value]
        if value is None or type(value) in (str, bool, int):
            return value
        raise ValueError('Unsupported public input')

    # Config is a frozen public dataclass; reject unrecognized config fields.
    from pursuit_v2.config import Config
    cfg = Config(**view['config']).to_dict()
    target_fields = ('id', 'announcement_tick', 'birth', 'weight', 'deadline',
                     'service_duration', 'required_robots', 'coarse_position',
                     'velocity_prior', 'design_error_bound', 'motion_model', 'speed_limit')
    belief_fields = ('target_id', 'estimate_tick', 'available_tick', 'position_estimate',
                     'velocity_estimate', 'velocity_source', 'last_observation_tick', 'source', 'status')
    profile_fields = ('sensor_id', 'observed_tick', 'sigma', 'health', 'source')
    ids = sorted(t['id'] for t in view['targets'])
    endpoints = {}
    for j in ids:
        ep = view['current_endpoints'][j]
        endpoints[j] = None if ep is None else project(ep, ('tick', 'team', 'G', 'Q', 'source'))
    snapshot = dict(tick=view['tick'], config=cfg, positions=view['positions'],
                    assignment=[project(a, ('target', 'role')) for a in view['assignment']],
                    targets=[project(t, target_fields) for t in sorted(view['targets'], key=lambda t: t['id'])],
                    beliefs={j: project(view['beliefs'][j], belief_fields) for j in ids},
                    public_profiles={i: project(view['public_profiles'][i], profile_fields) for i in range(3)},
                    service_states={j: dict(base=view['service_states'][j].base,
                                            intervals=view['service_states'][j].intervals,
                                            team=view['service_states'][j].team) for j in ids},
                    current_endpoints=endpoints, active_ids=sorted(view['active_ids']),
                    visible_ids=sorted(view['visible_ids']), public_provenance=view['public_provenance'])
    return digest(normalize(snapshot))


def world_digest(world):
    return digest(dict(tick=world['tick'], horizon=world['horizon'], dt=DT,
                       public_input_digest=world['public_input_digest'],
                       generation_rule=world['generation_rule'], motion=motion_identity(world['motion'])))


def motion_identity(motion):
    return tuple((j, tuple((0. if x == 0 else float(x)).hex() for x in
                          (*m['position'], *m['velocity']))) for j, m in sorted(motion.items()))


def point(world, j, tick):
    m = world['motion'][j]
    return tuple(p + (tick-world['tick'])*DT*v for p, v in zip(m['position'], m['velocity']))


def generate_worlds(view):
    """No defaults for public uncertainty fields; no access to private target objects."""
    try:
        tick, side = view['tick'], view['config']['side']
        if tick not in (60, 80, 100) or not math.isfinite(side) or side <= 0:
            raise ValueError('Invalid domain')
        context = public_input_digest(view)
        libraries, ids, nominal = [], [], {}
        targets = sorted(view['targets'], key=lambda t: t['id'])
        if len(targets) != 2 or len({t['id'] for t in targets}) != 2:
            raise ValueError('Expected two distinct targets')
        for t in targets:
            j = t['id']
            if type(j) is not int or j < 0:
                raise ValueError('Invalid target ID')
            bound, limit = t['design_error_bound'], t['speed_limit']
            if not all(math.isfinite(x) and x >= 0 for x in (bound, limit)):
                raise ValueError('Invalid public bounds')
            b = view['beliefs'][j]
            if b['available_tick'] > tick or b['estimate_tick'] > tick:
                raise ValueError('Future belief')
            p, v = trajectory(b, tick)
            if len(p) != 2 or len(v) != 2:
                raise ValueError('Expected planar state')
            r, s = bound/2, limit/2
            hypotheses = []
            for dp in ((0., 0.), (r, 0.), (-r, 0.), (0., r), (0., -r)):
                for dv in ((0., 0.), (s, 0.)):
                    pos = tuple(float(x+y) for x, y in zip(p, dp))
                    vel = tuple(float(x+y) for x, y in zip(v, dv))
                    # Eastward motion leaves the physical region through x=side;
                    # that legal escape is handled by the proxy, not filtered.
                    legal = (all(math.isfinite(x) for x in (*pos, *vel))
                             and all(0 <= x <= side for x in pos)
                             and vel[0] >= 0 and math.hypot(*vel) <= limit)
                    if dp == (0., 0.) and dv == (0., 0.):
                        if not legal:
                            return dict(status='H1_INVALID', worlds=[])
                        nominal[j] = dict(position=pos, velocity=vel)
                    if legal:
                        hypotheses.append(dict(position=pos, velocity=vel))
            ids.append(j)
            libraries.append(hypotheses)
        worlds, seen = [], set()
        for combo in product(*libraries):
            motion = dict(zip(ids, combo))
            identity = motion_identity(motion)
            if identity in seen:
                continue
            seen.add(identity)
            world = dict(tick=tick, horizon=H, generation_rule=WORLD_RULE_VERSION,
                         public_input_digest=context, motion=motion, world_ordinal=len(worlds),
                         is_h1=identity == motion_identity(nominal))
            world['world_digest'] = world_digest(world)
            worlds.append(world)
        return dict(status='WORLDS_GENERATED' if len(worlds) >= 3 else 'WORLD_SET_INSUFFICIENT', worlds=worlds)
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
        return dict(status='INVALID_PUBLIC_WORLD_INPUT', worlds=[])


def screen_worlds(candidates, worlds, results):
    """results[(assignment_key, world_digest)] contains only fixed-plan proxy outputs."""
    if len(worlds) < 3:
        return dict(status='WORLD_SET_INSUFFICIENT')
    if len({w['world_digest'] for w in worlds}) != len(worlds) or len({w['world_ordinal'] for w in worlds}) != len(worlds):
        raise ValueError('Conflicting world identities')
    h1s = [w for w in worlds if w['is_h1']]
    keeps = [a for a in candidates if a['kind'] == 'KEEP']
    if len(h1s) != 1 or len(keeps) != 1:
        return dict(status='SCREENING_IDENTITY_FAILURE')
    h1, keep = h1s[0], keeps[0]
    def result(a, w):
        out = results[(a['assignment_key'], w['world_digest'])]
        if (out['proxy_role'] != 'OPTIMISTIC_Q_PROXY' or out['world_digest'] != w['world_digest']
                or out['assignment_key'] != a['assignment_key'] or not math.isfinite(out['value'])):
            raise ValueError('Invalid proxy identity/value')
        return out
    scores = []
    for w in worlds:
        margins = []
        for a in candidates:
            for task in result(a, w)['tasks'].values():
                if task['complete_team'] and (task['P0'] > 0 or task['NG'] > 0):
                    margin = ((H-task['completion_tick'])*DT if task['completion_tick'] is not None
                              else task['Pmax']-(task['duration']-TOL))
                    margins.append(abs(margin))
        if margins and w != h1:
            scores.append((min(margins), w['world_ordinal'], w))
    if not scores:
        return dict(status='H2_NONTRIVIAL_BOUNDARY_UNAVAILABLE')
    h2 = min(scores, key=lambda s: s[:2])[2]
    alternatives = [a for a in candidates if a['kind'] != 'KEEP']
    if not alternatives:
        return dict(status='H3_NO_ALTERNATIVE_ACTION')
    def sensitivity(w):
        return max(abs((result(a, w)['value']-result(keep, w)['value'])
                       -(result(a, h1)['value']-result(keep, h1)['value'])) for a in alternatives)
    remaining = [w for w in worlds if w not in (h1, h2)]
    h3 = min(remaining, key=lambda w: (-sensitivity(w), w['world_ordinal']))
    return dict(status='WORLD_SET_FROZEN', H1=h1, H2=h2, H3=h3,
                h2_score=min(scores, key=lambda s: s[:2])[0], h3_score=sensitivity(h3))
