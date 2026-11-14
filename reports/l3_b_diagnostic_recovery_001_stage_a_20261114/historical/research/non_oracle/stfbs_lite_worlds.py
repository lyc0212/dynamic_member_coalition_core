"""Public conditional worlds and ordinal-based H2/H3 screening, never MODEL."""
from itertools import product
from fractions import Fraction
import math

from .belief import trajectory
from .stfbs_lite_candidates import digest, assignment_key, team

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
            if t.get('motion_model') != 'constant_velocity':
                return dict(status='UNSUPPORTED_PUBLIC_MOTION_MODEL', worlds=[])
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
                             and 0 <= pos[0] < side and 0 <= pos[1] <= side
                             and vel[0] >= 0 and math.hypot(*vel) <= limit)
                    if legal:
                        escape_after = (side-pos[0])/vel[0] if vel[0] > 0 else math.inf
                        until = min((H-tick)*DT, escape_after)
                        end_y = pos[1]+vel[1]*until
                        legal = math.isfinite(end_y) and 0 <= end_y <= side
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


def screen_worlds(candidates, worlds, results, *, view):
    """Validate the entire canonical library against a trusted public view.

    results is either a keyed mapping or a sequence of (cell_key, output) pairs;
    the latter permits duplicate detection before constructing a mapping. No
    proxy, estimator or MODEL is executed here. Failure rejects the whole table.
    """
    canonical = generate_worlds(view)
    if canonical['status'] not in ('WORLDS_GENERATED', 'WORLD_SET_INSUFFICIENT'):
        return dict(status=canonical['status'])
    try:
        expected = canonical['worlds']
        if len(worlds) != len(expected):
            raise ValueError('Incomplete world library')
        for supplied, actual in zip(worlds, expected):
            if (set(supplied) != set(actual)
                    or type(supplied['world_ordinal']) is not int
                    or type(supplied['is_h1']) is not bool
                    or supplied != actual
                    or supplied['world_digest'] != world_digest(supplied)):
                raise ValueError('Noncanonical world identity/order')
        if canonical['status'] == 'WORLD_SET_INSUFFICIENT':
            return dict(status='WORLD_SET_INSUFFICIENT')
        keys = [assignment_key(a['actions']) for a in candidates]
        kinds = [a['kind'] for a in candidates]
        if (not keys or len(keys) > 3 or len(set(keys)) != len(keys)
                or len(set(kinds)) != len(kinds) or kinds.count('KEEP') != 1
                or any(k not in ('KEEP', 'SWITCH', 'MEMBER_CHANGE') for k in kinds)
                or any(a['assignment_key'] != k for a, k in zip(candidates, keys))):
            raise ValueError('Invalid action identities')
        from .stfbs_lite_candidates import classify
        if any(classify(view['assignment'], a['actions']) != a['kind'] for a in candidates):
            raise ValueError('Action classification conflict')
        required = {(k, h['world_digest']) for k in keys for h in worlds}
        entries = list(results.items()) if isinstance(results, dict) else list(results)
        table = {}
        for cell, out in entries:
            if cell not in required or cell in table:
                raise ValueError('Duplicate or foreign proxy cell')
            table[cell] = out
        if set(table) != required:
            raise ValueError('Missing proxy cell')
        targets = {t['id']: t for t in view['targets']}
        ledger_keys = {'completion', 'flow', 'late', 'effort', 'terminal', 'change'}

        def finite_float(x):
            return type(x) is float and math.isfinite(x)

        for a in candidates:
            assigned, _ = team(a['actions'])
            for h in worlds:
                out = table[a['assignment_key'], h['world_digest']]
                if (out['proxy_role'] != 'OPTIMISTIC_Q_PROXY'
                        or out['world_digest'] != h['world_digest']
                        or out['assignment_key'] != a['assignment_key']
                        or not finite_float(out['value']) or set(out['tasks']) != set(targets)):
                    raise ValueError('Invalid proxy identity/value/tasks')
                columns = out['ledger']
                if set(columns) != ledger_keys or not all(finite_float(v) for v in columns.values()):
                    raise ValueError('Invalid economic ledger')
                reconstructed = columns['completion']-sum(columns[k] for k in
                                                          ('flow', 'late', 'effort', 'terminal', 'change'))
                if not math.isfinite(reconstructed) or reconstructed != out['value']:
                    raise ValueError('Economic value/ledger mismatch')
                for j, record in out['tasks'].items():
                    if (any(not finite_float(record[k]) for k in ('P0', 'Pmax', 'duration'))
                            or record['P0'] < 0 or record['Pmax'] < record['P0']
                            or record['duration'] <= 0 or record['duration'] != targets[j]['service_duration']
                            or record['Pmax'] > record['duration']
                            or type(record['NG']) is not int or not 0 <= record['NG'] <= H-view['tick']
                            or type(record['complete_team']) is not bool
                            or record['complete_team'] != (j == assigned)):
                        raise ValueError('Invalid H2 task metrics')
                    ct = record['completion_tick']
                    if ct is not None and (type(ct) is not int or not view['tick'] < ct <= H
                                           or not record['complete_team']):
                        raise ValueError('Invalid completion tick')
        h1 = next(h for h in worlds if h['is_h1'])
        keep = next(a for a in candidates if a['kind'] == 'KEEP')
        scores = []
        for h in worlds:
            margins = []
            for a in candidates:
                for record in table[a['assignment_key'], h['world_digest']]['tasks'].values():
                    if record['complete_team'] and (record['P0'] > 0 or record['NG'] > 0):
                        # Retain the frozen binary64 service/TOL arithmetic, then
                        # compare the recorded finite margin exactly.
                        ct = record['completion_tick']
                        margin = ((H-ct)*DT if ct is not None else
                                  record['Pmax']-(record['duration']-TOL))
                        if not math.isfinite(margin):
                            raise ValueError('Nonfinite boundary margin')
                        margins.append(abs(Fraction.from_float(margin)))
            if margins and not h['is_h1']:
                scores.append((min(margins), h['world_ordinal'], h))
        if not scores:
            return dict(status='H2_NONTRIVIAL_BOUNDARY_UNAVAILABLE')
        best_h2 = min(scores, key=lambda item: item[:2])
        h2 = best_h2[2]
        alternatives = [a for a in candidates if a['kind'] != 'KEEP']
        if not alternatives:
            return dict(status='H3_NO_ALTERNATIVE_ACTION')

        def value(a, h):
            return Fraction.from_float(table[a['assignment_key'], h['world_digest']]['value'])

        def sensitivity(h):
            return max(abs((value(a, h)-value(keep, h))-(value(a, h1)-value(keep, h1)))
                       for a in alternatives)

        remaining = [h for h in worlds if h not in (h1, h2)]
        h3 = min(remaining, key=lambda h: (-sensitivity(h), h['world_ordinal']))
        return dict(status='WORLD_SET_FROZEN', H1=h1, H2=h2, H3=h3,
                    h2_score=best_h2[0], h3_score=sensitivity(h3))
    except (KeyError, TypeError, ValueError, OverflowError, StopIteration):
        return dict(status='SCREENING_VALIDATION_FAILED')
