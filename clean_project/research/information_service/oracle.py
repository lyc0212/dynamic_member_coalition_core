"""Independent scalar references for the frozen 2A-5b-A acceptance.

Only the Python standard library is imported.  No production estimator,
geometry, service clock, quality function, or scientific rollout is called.
The information matrix is local to the supplied evaluation point; its radius
is a mathematical proxy, never a certified error bound.
"""
from fractions import Fraction
import math


def _point(value, name):
    if len(value) != 2 or not all(math.isfinite(float(x)) for x in value):
        raise ValueError(name + ' must be a finite planar point')
    return float(value[0]), float(value[1])


def _measurements(payload):
    positions = payload['positions']
    sigmas = payload['sigmas']
    bearings = payload['bearings']
    identities = payload['sensor_ids']
    if not len(positions) == len(sigmas) == len(bearings) == len(identities):
        raise ValueError('Mismatched measurement lengths')
    if len(set(identities)) != len(identities):
        raise ValueError('Repeated sensor identity')
    rows = []
    for identity, position, bearing, sigma in zip(identities, positions, bearings, sigmas):
        position = _point(position, 'sensor position')
        bearing, sigma = float(bearing), float(sigma)
        if not math.isfinite(bearing) or not math.isfinite(sigma) or sigma <= 0:
            raise ValueError('Finite bearing and positive finite sigma required')
        rows.append((identity, position, bearing, sigma))
    return rows


def ray_intersection(payload, parallel_tolerance=1e-12):
    """Intersect two directed bearing rays without calling WLS.

    ``intersection`` is the line intersection even if it is behind a sensor
    or outside the public domain.  ``usable_ray_intersection`` distinguishes
    those cases.  Parallel/collinear rays have no unique returned point.
    """
    rows = _measurements(payload)
    if len(rows) != 2:
        return dict(intersection=None, estimate=None, usable_ray_intersection=False,
                    reason='requires_exactly_two_measurements', determinant=None,
                    ray_parameters=None, inside_domain=None)
    p, q = rows[0][1], rows[1][1]
    u = (math.cos(rows[0][2]), math.sin(rows[0][2]))
    v = (math.cos(rows[1][2]), math.sin(rows[1][2]))
    cross = lambda a, b: a[0] * b[1] - a[1] * b[0]
    determinant = cross(u, v)
    if abs(determinant) <= parallel_tolerance:
        return dict(intersection=None, estimate=None, usable_ray_intersection=False,
                    reason='parallel_or_collinear', determinant=determinant,
                    ray_parameters=None, inside_domain=None)
    delta = (q[0] - p[0], q[1] - p[1])
    first, second = cross(delta, v) / determinant, cross(delta, u) / determinant
    x = [p[0] + first * u[0], p[1] + first * u[1]]
    _point(x, 'intersection')
    forward = first >= -parallel_tolerance and second >= -parallel_tolerance
    domain = payload.get('domain')
    inside = None if domain is None else all(domain[0][i] <= x[i] <= domain[1][i]
                                              for i in range(2))
    usable = forward and inside is not False
    return dict(intersection=x, estimate=x, usable_ray_intersection=usable,
                reason='unique_forward_intersection' if usable else
                       'behind_sensor' if not forward else 'outside_public_domain',
                determinant=determinant, ray_parameters=[first, second],
                inside_domain=inside)


def quality_at(payload, x, *, p_ref=0.95, delta=0.06):
    """Scalar J/I/eigenvalue reference at an explicitly supplied point.

    det(J.T J) is evaluated by the two-column Cauchy--Binet identity.  The
    smaller eigenvalue is det/lambda_max, avoiding subtraction of two nearly
    equal eigenvalues.  A degenerate local matrix has radius_proxy=None.
    This function does not reproduce the estimator's acceptance diagnostics.
    """
    point = _point(x, 'evaluation point')
    if not 0 < p_ref < 1 or not math.isfinite(delta) or delta <= 0:
        raise ValueError('Invalid proxy parameters')
    jacobian = []
    for _, position, _, sigma in _measurements(payload):
        dx, dy = point[0] - position[0], point[1] - position[1]
        distance_squared = dx * dx + dy * dy
        if distance_squared <= 1e-18:
            raise ValueError('Evaluation point coincides with a sensor')
        jacobian.append([dy / (sigma * distance_squared),
                         -dx / (sigma * distance_squared)])
    a = math.fsum(row[0] * row[0] for row in jacobian)
    b = math.fsum(row[0] * row[1] for row in jacobian)
    c = math.fsum(row[1] * row[1] for row in jacobian)
    determinant = math.fsum((left[0] * right[1] - left[1] * right[0]) ** 2
                            for i, left in enumerate(jacobian)
                            for right in jacobian[i + 1:])
    largest = (a + c + math.hypot(a - c, 2 * b)) / 2
    smallest = determinant / largest if largest > 0 else 0.0
    if not all(math.isfinite(v) for v in (a, b, c, determinant, largest, smallest)):
        raise ValueError('Nonfinite reference arithmetic')
    s_max, s_min = math.sqrt(largest), math.sqrt(max(0.0, smallest))
    ratio = s_min / s_max if s_max > 0 else 0.0
    radius = math.sqrt(-2 * math.log1p(-p_ref)) / s_min if s_min > 0 else None
    return dict(evaluation_point=list(point), jacobian=jacobian,
                information=[[a, b], [b, c]], determinant=determinant,
                eigenvalues=[smallest, largest], singular_values=[s_max, s_min],
                s_min=s_min, s_max=s_max, condition_ratio=ratio,
                structural_degenerate=smallest <= 0,
                numerical_ill_conditioned=s_max == 0 or ratio < 1e-4,
                radius_proxy=radius, r_proxy=radius, p_ref=p_ref, delta=delta,
                analytic_radius_pass=radius is not None and radius <= delta,
                scope='independent local matrix at supplied point; not an error guarantee')


def truth_error(estimate, truth):
    """Euclidean error for offline evaluation; missing estimates remain None."""
    if estimate is None:
        return None
    x, y = _point(estimate, 'estimate'), _point(truth, 'truth')
    return math.hypot(x[0] - y[0], x[1] - y[1])


def _fraction(value):
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise ValueError('Boolean is not a time or cost')
    return Fraction(str(value))


def _canonical_team(team):
    normalized = sorted((int(row[0]), str(row[1])) for row in team)
    if len({i for i, _ in normalized}) != len(normalized) or any(i < 0 for i, _ in normalized):
        raise ValueError('Invalid independent team identities')
    return normalized


def clock_reference(ticks, G, Q=None, *, duration=1.0, dt=0.05, team=None,
                    powers=None, end_time=3.0, escape_time=None,
                    initial_progress=0.0, initial_team=None):
    """Fraction reference for a fixed-team endpoint stream.

    Q may contain booleans or PASS/FAIL/UNKNOWN strings; None means the G-only
    ledger.  powers[k][i] is robot i's squared control on the interval starting
    at ticks[k].  A partial stream remains ACTIVE until its actual hard end.
    No completed ledger can alter the other ledger or the common input trace.
    """
    ticks, G = list(ticks), list(G)
    if not ticks or len(G) != len(ticks):
        raise ValueError('Nonempty matched endpoint sequences required')
    if any(isinstance(n, bool) or not isinstance(n, int) or n < 0 for n in ticks):
        raise ValueError('Ticks must be nonnegative integers')
    if any(right != left + 1 for left, right in zip(ticks, ticks[1:])):
        raise ValueError('Missing or repeated tick in independent clock input')
    if not all(isinstance(value, bool) for value in G):
        raise ValueError('G must be Boolean')
    if Q is None:
        Q = [True] * len(ticks)
    else:
        Q = list(Q)
        if len(Q) != len(ticks):
            raise ValueError('Q length mismatch')
        if any(not isinstance(value, bool) and value not in ('PASS', 'FAIL', 'UNKNOWN')
               for value in Q):
            raise ValueError('Invalid Q state')
        Q = [value is True or value == 'PASS' for value in Q]
    interval, required, end = _fraction(dt), _fraction(duration), _fraction(end_time)
    progress = _fraction(initial_progress)
    escape = None if escape_time is None else _fraction(escape_time)
    if interval <= 0 or required <= 0 or not 0 <= progress < required:
        raise ValueError('Invalid interval, duration or active initial progress')
    if ticks[-1] * interval > end or end / interval != int(end / interval):
        raise ValueError('Hard end must be on-grid and cover the supplied stream')
    team = _canonical_team(team if team is not None else [(0, 'reference')])
    old_team = team if initial_team is None else _canonical_team(initial_team)
    if powers is None:
        robot_count = max((i for i, _ in team), default=-1) + 1
        powers = [[0.0] * robot_count for _ in ticks]
    else:
        powers = [list(row) for row in powers]
        if len(powers) not in (len(ticks), len(ticks) - 1):
            raise ValueError('Need one power vector per interval or endpoint')
        robot_count = len(powers[0]) if powers else max((i for i, _ in team), default=-1) + 1
        if any(len(row) != robot_count for row in powers):
            raise ValueError('Power vector size changed')
    if any(i >= robot_count for i, _ in team):
        raise ValueError('Occupied robot absent from the power vector')
    rational_powers = [[_fraction(v) for v in row] for row in powers]
    if any(v < 0 for row in rational_powers for v in row):
        raise ValueError('Negative control-square input')
    effort = [Fraction() for _ in range(robot_count)]
    full_effort = [Fraction() for _ in range(robot_count)]
    occupied_seconds = Fraction()
    valid_time = Fraction()
    restart_loss = Fraction()
    events, frames = [], []
    status = 'ACTIVE'
    completion_tick = completion_time = release_time = None
    window_start = None
    history_unknown = progress > 0
    completion_window = None

    def reset(at, reason):
        nonlocal progress, restart_loss, window_start, history_unknown
        if progress > 0:
            events.append(dict(time=float(at), reason=reason, progress_before=float(progress),
                               progress_before_fraction=str(progress)))
            restart_loss += progress
        progress, window_start, history_unknown = Fraction(), None, False

    start = ticks[0] * interval
    if team != old_team:
        reset(start, 'team_changed')
    if escape is not None and escape <= start:
        status, release_time = 'ESCAPED', escape
    elif start >= end:
        status, release_time = 'UNFINISHED', end
    elif not (G[0] and Q[0]):
        reset(start, 'observation_invalid')

    def record(k):
        frames.append(dict(tick=ticks[k], time=float(ticks[k] * interval),
                           valid=G[k] and Q[k], status=status,
                           progress=float(progress), progress_fraction=str(progress),
                           occupied_robot_seconds=float(occupied_seconds),
                           prefix_effort_by_robot=[float(v) for v in effort],
                           effort=float(sum(effort)),
                           occupied_robots=[i for i, _ in team] if status == 'ACTIVE' else []))

    record(0)
    for k in range(len(ticks) - 1):
        lo, hi = ticks[k] * interval, ticks[k + 1] * interval
        for i, value in enumerate(rational_powers[k]):
            full_effort[i] += value * (hi - lo)
        if status != 'ACTIVE':
            record(k + 1)
            continue
        stop = min(hi, escape) if escape is not None else hi
        elapsed = max(Fraction(), stop - lo)
        occupied_seconds += len(team) * elapsed
        for i, _ in team:
            effort[i] += rational_powers[k][i] * elapsed
        if escape is not None and escape <= hi:
            status, release_time = 'ESCAPED', escape
        else:
            valid = G[k] and Q[k] and G[k + 1] and Q[k + 1]
            if valid:
                if progress == 0:
                    window_start = ticks[k]
                valid_time += interval
                progress += interval
                if progress >= required:
                    progress = required
                    status, completion_tick, completion_time = 'COMPLETED', ticks[k + 1], hi
                    release_time = hi
                    if not history_unknown and window_start is not None:
                        completion_window = list(range(window_start, completion_tick + 1))
            else:
                reset(hi, 'observation_invalid')
            if status == 'ACTIVE' and hi >= end:
                status, release_time = 'UNFINISHED', end
        record(k + 1)
    return dict(reference='stdlib_fraction_fixed_team_v1', frames=frames, events=events,
                final_status=status, final_progress=float(progress), final_progress_fraction=str(progress),
                completion_tick=completion_tick,
                completion_time=None if completion_time is None else float(completion_time),
                completion_window_ticks=completion_window,
                completion_window_has_unprovided_history=completion_time is not None and history_unknown,
                release_time=None if release_time is None else float(release_time),
                release_count=int(release_time is not None),
                occupied_robot_seconds=float(occupied_seconds),
                occupied_robot_seconds_fraction=str(occupied_seconds),
                prefix_effort_by_robot=[float(v) for v in effort],
                prefix_effort_fraction_by_robot=[str(v) for v in effort],
                effort=float(sum(effort)),
                full_input_effort_by_robot=[float(v) for v in full_effort],
                full_input_effort=float(sum(full_effort)),
                total_valid_time=float(valid_time), restart_loss=float(restart_loss),
                interrupt_count=len(events),
                scope='independent exact rational clock/accounting, not a physical rollout')
