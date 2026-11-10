"""G-only fixed-plan proxy; optimistic unknown Q is not a PASS observation."""
from dataclasses import replace
import math
import numpy as np

from pursuit_v2.config import Config
from pursuit_v2.observation_geometry import offset, radius, validate_roles
from pursuit_v2.service import ServiceState, advance_clock
from .policy import command
from .stfbs_lite_candidates import assignment_key, team
from .stfbs_lite_worlds import DT, H, TOL, point

CERTIFICATE_ROLE = 'DIAGNOSTIC_ONLY'


def certificate(state, duration, start_tick, *, complete_team, proven_escape_time=None,
                premises_verified=False):
    """Use every remaining complete interval, never predicted G failures.

    An escape bound must be proved by the caller for this fixed conditional
    trajectory. Without verified premises no infeasibility claim is emitted.
    """
    out = dict(status='NOT_CERTIFIED', certificate_role=CERTIFICATE_ROLE)
    if (not premises_verified or not isinstance(state, ServiceState)
            or type(start_tick) is not int or not 0 <= start_tick <= H
            or not math.isfinite(duration) or duration <= 0):
        return out
    if proven_escape_time is not None and (math.isnan(proven_escape_time) or proven_escape_time < start_tick*DT):
        return out
    n = H-start_tick if complete_team else 0
    if proven_escape_time is not None:
        n = sum(1 for k in range(start_tick+1, H+1) if proven_escape_time > k*DT+TOL) if complete_team else 0
    upper = math.fsum((state.base, (state.intervals+n)*DT))
    out.update(N_plus=n, U_plus=upper)
    if upper < duration-TOL:
        out['status'] = 'CERTIFIED_INFEASIBLE_UNDER_FIXED_PLAN_BY_H'
    return out


def ledger(cfg, targets, start_tick, outcomes, effort, changed):
    """Positive cost columns, with completion reward separated."""
    start = start_tick*DT
    reward = flow = late = terminal = 0.
    for t in targets:
        o = outcomes[t['id']]
        stop = o['stop_time']
        reward += t['weight'] if o['completion_tick'] is not None else 0.
        terminal += t['weight'] if o['completion_tick'] is None else 0.
        flow += t['weight']*max(0., stop-max(start, t['birth']))
        late += t['weight']*max(0., stop-max(start, t['birth'], t['deadline']))
    columns = dict(completion=reward/cfg.weight_reference,
                   flow=cfg.flow_weight*flow/(cfg.weight_reference*cfg.stage_dt),
                   late=cfg.late_weight*late/(cfg.weight_reference*cfg.stage_dt),
                   effort=cfg.control_weight*effort/cfg.effort_reference,
                   terminal=cfg.unfinished_weight*terminal/cfg.weight_reference,
                   change=cfg.change_cost*changed)
    value = columns['completion']-sum(columns[k] for k in ('flow', 'late', 'effort', 'terminal', 'change'))
    if not all(math.isfinite(x) for x in (*columns.values(), value)):
        raise ValueError('Invalid economic output')
    return columns, value


def run_proxy(view, actions, world):
    """Public envelope plus immutable service clocks and known current Q states.

    current_q is indexed by target. A changed team starts UNKNOWN; known
    non-PASS Q prevents inheritance at the initial endpoint only. All future
    endpoints are explicitly optimistic, with no synthesized observations.
    """
    cfg = Config(**view['config'])
    start = view['tick']
    if world['tick'] != start or start not in (60, 80, 100):
        raise ValueError('Cut mismatch')
    target_id, members = team(actions)
    ids = {t['id'] for t in view['targets']}
    if target_id not in ids or set(world['motion']) != ids:
        raise ValueError('Foreign task')
    if cfg.geometry_mode != 'angular_standoff_v1' or cfg.capture_mode != 'stepwise_service':
        raise ValueError('Expected frozen angular service geometry')
    positions = np.array(view['positions'], dtype=float, copy=True)
    if positions.shape != (3, 2) or not np.isfinite(positions).all():
        raise ValueError('Invalid robot positions')
    tasks, states, initial, lefts, statuses = {}, {}, {}, {}, {}
    def geometry(j, at):
        if j != target_id:
            return False
        roles = [r for _, r in members]
        return bool(validate_roles(2, roles, cfg) and all(
            np.linalg.norm(positions[i]-np.array(point(world, j, at))-offset(r, cfg)) <= radius(cfg)
            for i, r in members))
    for t in view['targets']:
        j = t['id']
        old = view['service_states'][j]
        if not isinstance(old, ServiceState) or old.progress >= t['service_duration']:
            raise ValueError('Invalid active clock')
        expected = tuple((i, a['role']) for i, a in enumerate(view['assignment']) if a['target'] == j)
        if old.team != expected:
            raise ValueError('Service history/assignment conflict')
        active_team = members if j == target_id else ()
        inherited = old.team == active_team
        state = old if inherited else replace(old, base=0., intervals=0, team=active_team)
        q = view['current_q'][j] if inherited else 'UNKNOWN'
        if q not in ('PASS', 'FAIL', 'UNKNOWN'):
            raise ValueError('Invalid public Q')
        # P0 is the transaction inheritance/reset state, before endpoint failure.
        initial[j] = state
        p0 = state.progress
        left = geometry(j, start) and q != 'FAIL'
        if not left:
            state = replace(state, base=0., intervals=0)
        states[j], lefts[j], statuses[j] = state, left, 'active'
        tasks[j] = dict(P0=p0, Pmax=p0, NG=0, duration=t['service_duration'],
                        complete_team=j == target_id, completion_tick=None, stop_time=H*DT)
    geometry_before = {j: geometry(j, start) for j in ids}
    effort = 0.
    for k in range(start+1, H+1):
        lo, hi = (k-1)*DT, k*DT
        for t in view['targets']:
            j = t['id']
            if statuses[j] != 'active':
                continue
            p = point(world, j, k-1)
            vx = world['motion'][j]['velocity'][0]
            escape = lo if p[0] >= cfg.side else lo+(cfg.side-p[0])/vx if vx > 0 else math.inf
            stop = min(hi, escape)
            elapsed = max(0., stop-lo)
            if j == target_id:
                for i, role in members:
                    u = command(view['beliefs'][j], k-1, [positions[i]], [role], cfg)[0]
                    positions[i] += u*elapsed
                    effort += float(np.sum(u*u))*elapsed
            if escape <= hi+TOL:
                statuses[j] = 'escaped'
                tasks[j]['stop_time'] = escape
                continue
            if j == target_id:
                right = geometry(j, k)
                # NG is geometry-only, independent of known initial Q failure.
                if geometry_before[j] and right:
                    tasks[j]['NG'] += 1
                states[j], done, _ = advance_clock(states[j], t['service_duration'], members,
                                                  lefts[j] and right, hi)
                tasks[j]['Pmax'] = max(tasks[j]['Pmax'], states[j].progress)
                lefts[j] = right
                geometry_before[j] = right
                if done:
                    statuses[j] = 'completed'
                    tasks[j].update(completion_tick=k, stop_time=hi)
    changed = sum(a != b for a, b in zip(actions, view['assignment']))
    columns, value = ledger(cfg, view['targets'], start, tasks, effort, changed)
    diagnostics = {}
    for t in view['targets']:
        j = t['id']
        p = point(world, j, start)
        vx = world['motion'][j]['velocity'][0]
        escape = start*DT if p[0] >= cfg.side else start*DT+(cfg.side-p[0])/vx if vx > 0 else math.inf
        diagnostics[j] = certificate(initial[j], t['service_duration'], start,
                                     complete_team=j == target_id, proven_escape_time=escape,
                                     premises_verified=True)
    return dict(proxy_role='OPTIMISTIC_Q_PROXY', assignment_key=assignment_key(actions),
                world_digest=world['world_digest'], tasks=tasks, ledger=columns, value=value,
                effort_integral=effort, certificates=diagnostics, positions=positions.tolist())
