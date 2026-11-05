"""Fixed world-frame geometry only; no sensor accuracy or allocation model."""
import math
import numpy as np

LEGACY = ('center', 'upper', 'lower')
ANGULAR = {1: ('solo_0',), 2: ('dual_neg45', 'dual_pos45'),
           3: ('tri_0', 'tri_120', 'tri_240')}
ANGLES = dict(zip(sum(ANGULAR.values(), ()), (0., -45., 45., 0., 120., 240.)))
ALL_ROLES = LEGACY + tuple(ANGLES)
TOL = 1e-10


def required_roles(q, cfg):
    if cfg.geometry_mode == 'angular_standoff_v1':
        if cfg.capture_mode != 'stepwise_service' or q not in ANGULAR:
            raise ValueError('Angular geometry requires service with q=1/2/3')
        return ANGULAR[q]
    if q not in (1, 2):
        raise ValueError('Legacy geometry requires q=1/2')
    return ('center',) if q == 1 else ('upper', 'lower')


def identity(cfg):
    if cfg.geometry_mode == 'legacy_anchor':
        return None
    return ('angular_standoff_v1', 1, cfg.observation_radius, cfg.observation_tolerance,
            tuple(ANGLES.items()))


def offset(role, cfg):
    if cfg.geometry_mode == 'legacy_anchor':
        if role not in LEGACY:
            raise ValueError('Role incompatible with legacy geometry')
        return np.array([0., {'center': 0., 'upper': cfg.anchor_offset,
                              'lower': -cfg.anchor_offset}[role]])
    if role not in ANGLES:
        raise ValueError('Role incompatible with angular geometry')
    a = math.radians(ANGLES[role])
    return cfg.observation_radius * np.array([math.cos(a), math.sin(a)])


def validate_roles(q, roles, cfg):
    required = required_roles(q, cfg)
    if any(r not in required for r in roles):
        raise ValueError('Role incompatible with task geometry')
    if cfg.geometry_mode != 'legacy_anchor' and len(set(roles)) != len(roles):
        raise ValueError('Duplicate angular role')
    if len(roles) > q:
        raise ValueError('Too many service members')
    return len(roles) == q and set(roles) == set(required)


def radius(cfg):
    return (cfg.capture_radius if cfg.geometry_mode == 'legacy_anchor'
            else cfg.observation_tolerance) + TOL


def diagnostics(cfg, target_position, positions, roles):
    pos = np.asarray(positions, float).reshape((-1, 2))
    x = np.asarray(target_position)
    anchors = np.array([x + offset(r, cfg) for r in roles]).reshape((-1, 2))
    vectors = pos - x
    distances = np.linalg.norm(vectors, axis=1)
    bearings = [math.atan2(v[1], v[0]) if d > 0 else None
                for v, d in zip(vectors, distances)]
    pairs = []
    separations = []
    for i in range(len(pos)):
        for k in range(i+1, len(pos)):
            a, b = bearings[i], bearings[k]
            angle = None if a is None or b is None else abs(math.atan2(math.sin(a-b), math.cos(a-b)))
            pairs.append(dict(members=[i, k], angle_radians=angle))
            separations.append(float(np.linalg.norm(pos[i]-pos[k])))
    outside = lambda p: bool(p[0] < 0 or p[0] > cfg.side or p[1] < 0 or p[1] > cfg.side)
    return dict(anchors=anchors.tolist(), errors=np.linalg.norm(pos-anchors, axis=1).tolist(),
                distances=distances.tolist(), bearings_radians=bearings,
                undefined_bearing_members=[i for i, a in enumerate(bearings) if a is None],
                pair_angles=pairs, minimum_robot_distance=min(separations, default=None),
                anchors_outside_reference_region=[outside(a) for a in anchors],
                robots_outside_reference_region=[outside(p) for p in pos])
