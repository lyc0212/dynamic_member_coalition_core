"""SYNTHETIC_PURE_FIXTURE_NOT_SCIENTIFIC_EVIDENCE. No scientific rollouts."""
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
import math
from unittest.mock import patch

import numpy as np
import pytest

from pursuit_v2.config import Config
from pursuit_v2.observation_geometry import offset
from pursuit_v2.service import ServiceState
from research.non_oracle import policy
from research.non_oracle import stfbs_lite_candidates as c
from research.non_oracle import stfbs_lite_worlds as w
from research.non_oracle import stfbs_lite_proxy as p
from research.non_oracle import stfbs_lite_selector as s


@pytest.fixture
def view():
    cfg = Config(robots=3, task_count=2, capture_mode='stepwise_service',
                 geometry_mode='angular_standoff_v1', max_stages=2,
                 target_speed_min=0., target_speed_max=1.)
    actions = [dict(target=0, role='dual_neg45'), dict(target=0, role='dual_pos45'), dict(target=None, role='none')]
    beliefs = {j: dict(estimate_tick=60, available_tick=60, last_observation_tick=None,
                      position_estimate=[5.+j*3, 5.], velocity_estimate=[0., 0.]) for j in (0, 1)}
    positions = [(np.array([5., 5.])+offset(r, cfg)).tolist() for r in ('dual_neg45', 'dual_pos45')]+[[6., 6.]]
    return dict(config=cfg.to_dict(), tick=60, attempted_ticks=[], positions=positions,
                targets=[dict(id=j, required_robots=2, design_error_bound=.4, speed_limit=1.,
                              service_duration=2., weight=2., birth=0., deadline=4.) for j in (0, 1)],
                beliefs=beliefs, assignment=actions, active_ids=[0, 1], visible_ids=[0, 1],
                service_states={0: ServiceState(.5, 0, ((0, 'dual_neg45'), (1, 'dual_pos45'))), 1: ServiceState()},
                public_profiles={i: {'source': 'PUBLIC'} for i in range(3)},
                current_q={0: 'PASS', 1: 'UNKNOWN'}, public_provenance='LEGAL_PUBLIC_SNAPSHOT')


def candidates(view):
    keys = c.catalogue(view)
    rows = [dict(absolute_O=1., baseline=0., v=1.) for _ in keys]
    return c.select_candidates(view, keys, rows, source=c.FIXTURE)


def selector_input(view, matrix):
    actions = candidates(view)['candidates']
    worlds = w.generate_worlds(view)['worlds'][:3]
    ctx = s.table_context(actions, worlds, economy_digest='synthetic-economy')
    rows = [dict(assignment_key=a['assignment_key'], world_digest=h['world_digest'],
                 context_digest=ctx, source=c.FIXTURE, value=float(matrix[i][j]))
            for i, a in enumerate(actions) for j, h in enumerate(worlds)]
    return actions, worlds, rows, dict(economy_digest='synthetic-economy', context_digest=ctx)


def test_candidate_counts_keys_and_idle_member_switch(view):
    out = candidates(view)
    assert len(out['audit']) == 13
    assert {kind: sum(a['kind'] == kind for a in out['audit']) for kind in
            ('KEEP', 'SWITCH', 'MEMBER_CHANGE', 'EXCLUDED')} == dict(KEEP=1, SWITCH=6, MEMBER_CHANGE=4, EXCLUDED=2)
    for a in out['candidates']:
        group = [b for b in out['audit'] if b['kind'] == a['kind']]
        optimum = max(Fraction(b['exact_value']) for b in group)
        assert a['assignment_key'] == min(b['assignment_key'] for b in group if Fraction(b['exact_value']) == optimum)
    # Explicitly give an original-idle-member SWITCH the largest score.
    keys = c.catalogue(view)
    rows = [dict(absolute_O=0., baseline=0., v=0.) for _ in keys]
    index = next(i for i, k in enumerate(keys) if k['target'] == 1 and k['robots'] == [0, 2])
    rows[index] = dict(absolute_O=100., baseline=0., v=100.)
    out = c.select_candidates(view, keys, rows, source=c.FIXTURE)
    switch = next(a for a in out['candidates'] if a['kind'] == 'SWITCH')
    assert switch['actions'][2]['target'] == 1


@pytest.mark.parametrize('mutation', ['tick', 'repeat', 'visible', 'team', 'source', 'position'])
def test_applicability_rejection(view, mutation):
    if mutation == 'tick': view['tick'] = 61
    if mutation == 'repeat': view['attempted_ticks'] = [60]
    if mutation == 'visible': view['visible_ids'] = [0]
    if mutation == 'team': view['assignment'][1]['target'] = None
    if mutation == 'source': view['public_provenance'] = 'PRIVATE'
    if mutation == 'position': view['positions'][0][0] = math.nan
    assert c.applicability(view) != 'APPLICABLE'


@pytest.mark.parametrize('bad', ['missing', 'order', 'nan', 'arithmetic', 'baseline', 'source'])
def test_score_contract(view, bad):
    keys = c.catalogue(view)
    rows = [dict(absolute_O=1., baseline=0., v=1.) for _ in keys]
    source = c.FIXTURE
    if bad == 'missing': rows.pop()
    if bad == 'order': keys.reverse()
    if bad == 'nan': rows[0]['v'] = math.nan
    if bad == 'arithmetic': rows[0]['v'] = 2.
    if bad == 'baseline': rows[0] = dict(absolute_O=2., baseline=1., v=1.)
    if bad == 'source': source = 'REAL_A2'
    with pytest.raises(ValueError): c.select_candidates(view, keys, rows, source=source)


def test_world_generation_filter_dedup_and_nominal(view):
    out = w.generate_worlds(view)
    assert out['status'] == 'WORLDS_GENERATED'
    assert len(out['worlds']) == 100
    assert out['worlds'][0]['is_h1']
    assert [x['world_ordinal'] for x in out['worlds']] == list(range(100))
    view['targets'][0]['design_error_bound'] = 0.
    assert len(w.generate_worlds(view)['worlds']) == 20
    view['beliefs'][0]['velocity_estimate'] = [-.1, 0.]
    assert w.generate_worlds(view)['status'] == 'H1_INVALID'


def test_world_missing_bound_and_insufficient(view):
    del view['targets'][0]['speed_limit']
    assert w.generate_worlds(view)['status'] == 'INVALID_PUBLIC_WORLD_INPUT'


def test_zero_perturbations_signed_zero_and_escape(view):
    for t in view['targets']:
        t.update(design_error_bound=0., speed_limit=0.)
    view['beliefs'][0]['velocity_estimate'] = [-0., 0.]
    assert len(w.generate_worlds(view)['worlds']) == 1
    assert w.generate_worlds(view)['status'] == 'WORLD_SET_INSUFFICIENT'
    view['beliefs'][0]['position_estimate'] = [19.9, 5.]
    view['beliefs'][0]['velocity_estimate'] = [1., 0.]
    view['targets'][0]['speed_limit'] = 1.
    assert w.generate_worlds(view)['worlds'][0]['is_h1']


def test_proxy_inheritance_reset_completion_and_q(view):
    world = w.generate_worlds(view)['worlds'][0]
    out = p.run_proxy(view, view['assignment'], world)
    assert out['tasks'][0]['P0'] == .5
    assert out['tasks'][0]['completion_tick'] == 90
    assert out['tasks'][0]['Pmax'] == 2.
    assert out['proxy_role'] == 'OPTIMISTIC_Q_PROXY'
    swapped = deepcopy(view['assignment'])
    swapped[0]['role'], swapped[1]['role'] = swapped[1]['role'], swapped[0]['role']
    assert p.run_proxy(view, swapped, world)['tasks'][0]['P0'] == 0.
    view['current_q'][0] = 'FAIL'
    failed = p.run_proxy(view, view['assignment'], world)
    assert failed['tasks'][0]['completion_tick'] > 90


def test_proxy_escape_precedes_service_and_partial_effort(view):
    view['beliefs'][0]['position_estimate'] = [19.975, 5.]
    view['beliefs'][0]['velocity_estimate'] = [1., 0.]
    world = w.generate_worlds(view)['worlds'][0]
    cfg = Config(**view['config'])
    view['positions'][:2] = [(np.array([19.975, 5.])+offset(r, cfg)).tolist() for r in ('dual_neg45', 'dual_pos45')]
    out = p.run_proxy(view, view['assignment'], world)
    assert out['tasks'][0]['completion_tick'] is None
    assert out['tasks'][0]['NG'] == 0
    assert out['tasks'][0]['stop_time'] == pytest.approx(3.025)
    assert out['effort_integral'] == pytest.approx(.05)
    assert out['ledger']['terminal'] == .5


def test_six_accounting_columns(view):
    cfg = Config(**view['config'])
    outcomes = {0: dict(stop_time=4., completion_tick=80), 1: dict(stop_time=5., completion_tick=None)}
    columns, value = p.ledger(cfg, view['targets'], 60, outcomes, 12., 2)
    expected = dict(completion=2/8, flow=cfg.flow_weight*6/24,
                    late=cfg.late_weight*2/24, effort=cfg.control_weight*12/cfg.effort_reference,
                    terminal=cfg.unfinished_weight*2/8, change=cfg.change_cost*2)
    assert columns == expected
    assert value == expected['completion']-sum(expected[k] for k in ('flow', 'late', 'effort', 'terminal', 'change'))


def proxy_table(view):
    actions = candidates(view)['candidates']
    worlds = w.generate_worlds(view)['worlds'][:4]
    results = {(a['assignment_key'], h['world_digest']): p.run_proxy(view, a['actions'], h)
               for a in actions for h in worlds}
    return actions, worlds, results


def test_screen_ordinal_not_digest_and_h3_difference(view):
    actions, worlds, results = proxy_table(view)
    # Deliberately reverse digest lexical ordering while preserving ordinals.
    for i, h in enumerate(worlds):
        old = h['world_digest']
        h['world_digest'] = str(9-i)
        for a in actions:
            r = results.pop((a['assignment_key'], old))
            r['world_digest'] = h['world_digest']
            for task in r['tasks'].values():
                task.update(P0=1., Pmax=1., NG=1, completion_tick=None)
            r['value'] = 0. if a['kind'] == 'KEEP' or i == 0 else 1.
            results[a['assignment_key'], h['world_digest']] = r
    out = w.screen_worlds(actions, worlds, results)
    assert out['H2']['world_ordinal'] == 1
    assert out['H3']['world_ordinal'] == 2
    assert out['h3_score'] == 1.
    for r in results.values():
        for task in r['tasks'].values(): task.update(P0=0., NG=0)
    assert w.screen_worlds(actions, worlds, results)['status'] == 'H2_NONTRIVIAL_BOUNDARY_UNAVAILABLE'


def test_h2_completed_boundary_and_no_alternative(view):
    actions, worlds, results = proxy_table(view)
    for h in worlds:
        for a in actions:
            for task in results[a['assignment_key'], h['world_digest']]['tasks'].values():
                task.update(P0=1., NG=1, completion_tick=119 if h['world_ordinal'] == 2 else 100)
    assert w.screen_worlds(actions, worlds, results)['H2']['world_ordinal'] == 2
    assert w.screen_worlds(actions[:1], worlds, results)['status'] == 'H3_NO_ALTERNATIVE_ACTION'


def test_certificate_upper_bound_and_diagnostic_only(view):
    state = ServiceState(.5, 0, ((0, 'dual_neg45'), (1, 'dual_pos45')))
    args = dict(complete_team=True, premises_verified=True)
    assert p.certificate(state, 4., 60, **args)['status'].startswith('CERTIFIED')
    assert p.certificate(state, 3.5, 60, **args)['status'] == 'NOT_CERTIFIED'
    assert p.certificate(state, 3.5+5e-11, 60, **args)['status'] == 'NOT_CERTIFIED'
    assert p.certificate(state, 4., 60, complete_team=True)['status'] == 'NOT_CERTIFIED'
    assert p.certificate(state, 2., 60, proven_escape_time=3.05, **args)['N_plus'] == 0
    assert p.CERTIFICATE_ROLE == 'DIAGNOSTIC_ONLY'
    a, worlds, rows, kw = selector_input(view, [[1, 1, 1], [0, 0, 0], [0, 0, 0]])
    before = s.select(a, worlds, rows, **kw)
    for candidate in a: candidate['certificates'] = {'status': 'CERTIFIED_INFEASIBLE_UNDER_FIXED_PLAN_BY_H'}
    assert s.select(a, worlds, rows, **kw) == before


@pytest.mark.parametrize('winner', range(3))
def test_all_three_actions_can_win(view, winner):
    matrix = [[0., 0., 0.] for _ in range(3)]
    matrix[winner] = [1., 1., 1.]
    actions, worlds, rows, kw = selector_input(view, matrix)
    assert s.select(actions, worlds, rows, **kw)['kind'] == actions[winner]['kind']


def test_keep_tie_and_alternative_key_tie(view):
    a, worlds, rows, kw = selector_input(view, [[0]*3]*3)
    assert s.select(a, worlds, rows, **kw)['kind'] == 'KEEP'
    a, worlds, rows, kw = selector_input(view, [[0]*3, [1]*3, [1]*3])
    assert s.select(a, worlds, rows, **kw)['assignment_key'] == min(x['assignment_key'] for x in a[1:])


def test_exact_rational_subnormal_improvement(view):
    a, worlds, rows, kw = selector_input(view, [[0]*3, [math.ulp(0.)]*3, [0]*3])
    assert s.select(a, worlds, rows, **kw)['kind'] == 'SWITCH'


@pytest.mark.parametrize('bad', ['missing', 'nan', 'inf', 'duplicate', 'source', 'identity', 'context', 'world', 'budget'])
def test_bad_value_table_fallback(view, bad):
    a, worlds, rows, kw = selector_input(view, [[1]*3]*3)
    if bad == 'missing': rows.pop()
    if bad == 'nan': rows[0]['value'] = math.nan
    if bad == 'inf': rows[0]['value'] = math.inf
    if bad == 'duplicate': rows.append(deepcopy(rows[0]))
    if bad == 'source': rows[0]['source'] = 'MODEL'
    if bad == 'identity': rows[0]['assignment_key'] = ((99, 1),)*3
    if bad == 'context': rows[0]['context_digest'] = 'other-economy'
    if bad == 'world': worlds[1]['world_digest'] = worlds[0]['world_digest']
    if bad == 'budget': kw['budget_available'] = False
    assert s.select(a, worlds, rows, **kw)['status'] == 'KEEP_FALLBACK'
    assert s.select(a, worlds, rows, keep_legal=False, a2_available=True, **kw)['status'] == ('BLOCKED_NO_LEGAL_ACTION' if bad == 'budget' else 'A2_FALLBACK_REQUIRED')
    assert s.select(a, worlds, rows, keep_legal=False, **kw)['status'] == 'BLOCKED_NO_LEGAL_ACTION'


def test_repeatability_private_input_isolation_and_no_solver_calls(view):
    original = deepcopy(view)
    forbidden = AssertionError('Forbidden real scoring/estimation path')
    with patch.object(policy, 'decide', side_effect=forbidden), patch.object(policy, 'evaluate', side_effect=forbidden), patch.object(policy, 'endpoint', side_effect=forbidden), patch.object(policy, 'estimate', side_effect=forbidden):
        first = proxy_table(view)
        second = proxy_table(view)
        assert first == second
        assert view == original
        view['future_private_trajectory'] = object()
        view['private_sensor_schedule'] = object()
        assert proxy_table(view) == first
