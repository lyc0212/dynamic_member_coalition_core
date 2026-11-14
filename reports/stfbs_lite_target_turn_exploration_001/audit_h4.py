"""Read recorded MODEL transitions; independent physical and economic checks."""
import math
from fractions import Fraction
from copy import deepcopy
import numpy as np
from .belief import trajectory
from pursuit_v2.config import Config
from pursuit_v2.observation_geometry import offset, radius

def service_audit(result, view):
    clocks = {}
    left = {}
    teams = {}
    targets = {t['id']: t for t in view['targets']}
    cfg = Config(**view['config'])
    for h in view['histories']:
        j = h['target_id']
        s = next((s for s in h['segments'] if s['segment_id'] == h['active_segment_id']), None)
        clocks[j] = deepcopy(s['latest_clock']) if s else dict(base=0.0, intervals=0, team=[])
        teams[j] = deepcopy(s['team']) if s else []
        left[j] = deepcopy(s['latest_endpoint']) if s else None
    feedback = {(f['frame']['target_id'], f['frame']['tick']): f for f in result['feedback']}
    boundaries = {b['tick']: b for b in result['boundaries']}
    checked = 0
    for frame in result['frames']:
        n = frame['tick']
        boundary = boundaries.get(n - 1)
        if boundary:
            for j in targets:
                team = [dict(robot_id=i, role=a['role']) for i, a in enumerate(boundary['after']) if a['target'] == j]
                if team != teams[j]:
                    clocks[j] = dict(base=0.0, intervals=0, team=deepcopy(team))
                    teams[j] = team
                    left[j] = feedback[j, n - 1]['endpoint'] if team else None
        for j, t in targets.items():
            terminal = next((e for e in result['events'] if e['target'] == j and e['kind'] in ('completed', 'escaped', 'unfinished')), None)
            if not teams[j] or (terminal and terminal['time'] < (n - 1) * 0.05 - 1e-10):
                continue
            if terminal and terminal['kind'] == 'escaped' and (terminal['time'] <= n * 0.05 + 1e-10):
                teams[j] = []
                continue
            row = feedback.get((j, n))
            if row is None:
                raise ValueError('Missing MODEL endpoint evidence')
            right = row['endpoint']
            motion = result['world']['motion'][j]
            p = _h4_point(result['world'], j, n)
            positions = {int(r['sensor_id'][1:]): r['position'] for r in row['frame']['records']}
            actual_G = all((np.linalg.norm(np.asarray(frame['positions'][m['robot_id']]) - p - offset(m['role'], cfg)) <= radius(cfg) for m in teams[j]))
            if actual_G != right['G']:
                raise ValueError('MODEL endpoint geometry mismatch')
            valid = left[j]['G'] and right['G'] and (left[j]['quality']['status'] == right['quality']['status'] == 'PASS')
            if valid:
                clocks[j]['intervals'] += 1
            else:
                clocks[j].update(base=0.0, intervals=0)
            progress = math.fsum((clocks[j]['base'], clocks[j]['intervals'] * 0.05))
            done = progress >= t['service_duration'] - 1e-10
            if done:
                if not terminal or terminal['kind'] != 'completed' or terminal['tick'] != n:
                    raise ValueError('Service completion mismatch')
                teams[j] = []
            elif frame['clocks'][j] is not None and frame['clocks'][j] != clocks[j]:
                raise ValueError('Service clock mismatch')
            left[j] = right
            checked += 1
    return dict(status='PASS', checked_intervals=checked)

def audit(result, view):
    cfg = view['config']
    wr = 4 * cfg['task_count']
    effortref = cfg['robots'] * cfg['stage_dt'] * cfg['control_reference'] ** 2
    total = {k: 0.0 for k in ('completion', 'flow', 'late', 'effort', 'terminal')}
    fees = 0.0
    exact = {k: Fraction(0) for k in total}
    last = view['positions']
    physical = 0
    for b in result['boundaries']:
        count = sum((x != y for x, y in zip(b['before'], b['after'])))
        cost = cfg['change_cost'] * count
        if b['changes'] != count or b['cost'] != cost:
            raise ValueError('Assignment fee mismatch')
        fees += cost
    targets = {t['id']: t for t in view['targets']}
    terminal_times = {e['target']: e['time'] for e in result['events'] if e['kind'] in ('completed', 'escaped', 'unfinished')}
    if set(terminal_times) != set(targets):
        raise ValueError('Missing task terminal event')
    for frame in result['frames']:
        tick = frame['tick']
        lo = (tick - 1) * 0.05
        hi = tick * 0.05
        if frame['before'] != last:
            raise ValueError('Position discontinuity')
        pos = np.asarray(frame['before'])
        u = np.asarray(frame['control'])
        dt = np.asarray(frame['elapsed'])
        if np.any(np.linalg.norm(u, axis=1) > cfg['max_speed'] + 1e-12) or not np.array_equal(pos + u * dt[:, None], np.asarray(frame['positions'])):
            raise ValueError('Physical displacement mismatch')
        energy = sum((float(u[i] @ u[i]) * float(dt[i]) for i in range(len(u))))
        bound = 16 * math.ulp(max(1.0, abs(energy)))
        if abs(energy - frame['energy']) > bound:
            raise ValueError('Control integral mismatch')
        increment = -cfg['control_weight'] * frame['energy'] / effortref
        total['effort'] += increment
        exact['effort'] += Fraction(increment)
        for j, t in targets.items():
            if terminal_times[j] < lo - 1e-10:
                continue
            stop = min(hi, terminal_times[j])
            flow = t['weight'] * max(0.0, stop - max(lo, t['birth']))
            late = t['weight'] * max(0.0, stop - max(lo, t['birth'], t['deadline']))
            for key, weight, val in (('flow', cfg['flow_weight'], flow), ('late', cfg['late_weight'], late)):
                increment = -weight * val / (wr * cfg['stage_dt'])
                total[key] += increment
                exact[key] += Fraction(increment)
        last = frame['positions']
        physical += 1
    for event in result['events']:
        if event['kind'] == 'completed':
            increment = targets[event['target']]['weight'] / wr
            total['completion'] += increment
            exact['completion'] += Fraction(increment)
    total['terminal'] = -cfg['unfinished_weight'] * math.fsum((t['weight'] for j, t in targets.items() if result['status'][j] != 'completed')) / wr
    exact['terminal'] = Fraction(total['terminal'])
    if result['frames'][-1]['tick'] != 120:
        raise ValueError('Incomplete horizon')
    for k in total:
        if total[k] != result['components'][k]:
            raise ValueError(f'Accounting mismatch: {k}')
    if fees != result['change_cost']:
        raise ValueError('Change cost mismatch')
    net = sum(total.values()) - fees
    if net != result['net']:
        raise ValueError('Net mismatch')
    rational = sum(exact.values()) - sum((Fraction(b['cost']) for b in result['boundaries']))
    return dict(status='PASS', physical_steps=physical, components=total, change_cost=fees, net=net, exact_sum_of_binary64_increments=str(rational), rounding_residual=str(Fraction(net) - rational), physics_scope='Displacement, speed and control integral from records; service/feedback separately tested')
