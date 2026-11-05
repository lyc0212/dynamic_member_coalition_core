"""Independent scalar references. No execution, service or estimator imports."""
from fractions import Fraction as F
import math


def main_reference(case):
    """Reconstruct the frozen straight-line witnesses from scalar input only."""
    cid = case['case_id']
    q = case['targets'][0]['required_robots']
    r, dt = F(19, 20), F(1, 20)
    n_done = 46 if cid in ('E2', 'E3', 'E5') else 27
    energy_a = q * dt * (F(4, 25)*n_done + F(4, 25)*(1-r**n_done)/(1-r)
                          + F(1, 25)*(1-r**(2*n_done))/(1-r*r))
    has_b = cid == 'E5'
    energy = energy_a + (F(8, 125) if has_b else 0)
    wr = F(8 if has_b else 4)
    complete = F(2 if has_b else 1)/wr
    flow = -F(1, 10)*(n_done*dt+(F(1, 5) if has_b else 0))/(wr*3)
    late = -F(3, 10)*max(F(0), n_done*dt-2)/(wr*3)
    effort = -F(1, 50)*energy/900
    changes = q + (2 if has_b else 0)
    change_cost = F(changes, 100)
    offsets = ([(.6/math.sqrt(2), -.6/math.sqrt(2)),
                (.6/math.sqrt(2), .6/math.sqrt(2))] if q == 2 else
               [(.6*math.cos(a), .6*math.sin(a)) for a in (0, 2*math.pi/3, 4*math.pi/3)])
    records = []
    a_progress = F(0)
    for n in range(121):
        a_n = min(n, n_done)
        center = [float(8+F(1, 50)*a_n-F(1, 5)*r**a_n), 10.]
        if has_b and n > 60:
            center[0] = case['targets'][1]['position_at_birth'][0]+.02*min(n-60, 4)
        positions = [[center[0]+dx, center[1]+dy] for dx, dy in offsets]
        if q == 2:
            positions.append(list(case['positions_initial'][2]))
        bad = cid in ('E2', 'E3', 'E5') and 15 <= n < 25
        g = n >= 6
        if n <= n_done:
            if not g or bad:
                a_progress = F(0)
            elif n > 6 and not (cid in ('E2', 'E3', 'E5') and n == 25):
                a_progress += dt
        records.append(dict(tick=n, time=float(n*dt), positions=positions,
                            a_progress=float(min(a_progress, F(21, 20))),
                            a_G=g,
                            a_Q=('UNKNOWN' if cid == 'E3' else 'FAIL') if bad else 'PASS',
                            a_active=n < n_done, a_endpoint=n <= n_done))
    components = dict(completion=float(complete), flow=float(flow), late=float(late),
                      effort=float(effort), terminal=0.)
    return dict(case_id=cid, first_G_tick=6, A_completion_tick=n_done,
                A_completion_time=float(n_done*dt), B_completion_tick=64 if has_b else None,
                B_completion_time=3.2 if has_b else None, control_integral=float(energy),
                occupied_robot_seconds=float(q*n_done*dt+(F(2, 5) if has_b else 0)),
                assignment_changes=changes, change_cost=float(change_cost),
                return_without_changes=float(complete+flow+late+effort),
                return_with_changes=float(complete+flow+late+effort-change_cost),
                components=components, records=records)


def independent_information(positions, sigmas, estimate):
    """Two-dimensional bearing Jacobian/information and eigenvalues, scalar math."""
    jac = []
    aa = bb = cc = 0.
    for pos, sigma in zip(positions, sigmas):
        dx, dy = estimate[0]-pos[0], estimate[1]-pos[1]
        distance2 = dx*dx+dy*dy
        # Residual is (measured-bearing - predicted-bearing) / sigma.
        x, y = dy/(sigma*distance2), -dx/(sigma*distance2)
        jac.append([x, y])
        aa += x*x
        bb += x*y
        cc += y*y
    small = (aa+cc-math.hypot(aa-cc, 2*bb))/2
    return dict(J=jac, I=[[aa, bb], [bb, cc]],
                radius_proxy=math.sqrt(-2*math.log(.05)/small) if small > 0 else None)
