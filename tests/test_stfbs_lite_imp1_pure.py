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


@pytest.fixture(autouse=True)
def forbid_real_scoring_and_wls(monkeypatch):
    """Fail before any forbidden production scorer/optimizer can execute."""
    import scipy.optimize
    from research.cooperative_sensing import estimator

    def forbidden(*args, **kwargs):
        raise AssertionError('Real A2/WLS is forbidden in IMP-1 fixtures')

    for name in ('decide', 'evaluate', 'endpoint', 'estimate'):
        monkeypatch.setattr(policy, name, forbidden)
    monkeypatch.setattr(estimator, 'estimate', forbidden)
    monkeypatch.setattr(scipy.optimize, 'least_squares', forbidden)
    if hasattr(estimator, 'least_squares'):
        monkeypatch.setattr(estimator, 'least_squares', forbidden)


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
                targets=[dict(id=j, motion_model='constant_velocity', required_robots=2, design_error_bound=.4, speed_limit=1.,
                              service_duration=2., weight=2., birth=0., deadline=4.) for j in (0, 1)],
                beliefs=beliefs, assignment=actions, active_ids=[0, 1], visible_ids=[0, 1],
                service_states={0: ServiceState(.5, 0, ((0, 'dual_neg45'), (1, 'dual_pos45'))), 1: ServiceState()},
                public_profiles={i: {'source': 'PUBLIC'} for i in range(3)},
                current_q={0: 'PASS', 1: 'UNKNOWN'},
                current_endpoints={0: dict(tick=60, team=((0, 'dual_neg45'), (1, 'dual_pos45')),
                                          G=True, Q='PASS', source='RECORDED_PUBLIC_ENDPOINT'), 1: None},
                public_provenance='LEGAL_PUBLIC_SNAPSHOT')


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
    view['current_endpoints'][0]['Q'] = 'FAIL'
    view['service_states'][0] = replace(view['service_states'][0], base=0.)
    world = w.generate_worlds(view)['worlds'][0]
    failed = p.run_proxy(view, view['assignment'], world)
    assert failed['tasks'][0]['completion_tick'] > 90


def test_proxy_escape_precedes_service_and_partial_effort(view):
    view['beliefs'][0]['position_estimate'] = [19.975, 5.]
    view['beliefs'][0]['velocity_estimate'] = [1., 0.]
    cfg = Config(**view['config'])
    view['positions'][:2] = [(np.array([19.975, 5.])+offset(r, cfg)).tolist() for r in ('dual_neg45', 'dual_pos45')]
    world = w.generate_worlds(view)['worlds'][0]
    out = p.run_proxy(view, view['assignment'], world)
    assert out['tasks'][0]['completion_tick'] is None
    assert out['tasks'][0]['NG'] == 0
    assert out['tasks'][0]['stop_time'] == pytest.approx(3.025)
    assert out['effort_integral'] == pytest.approx(.05)
    assert out['ledger']['terminal'] == cfg.unfinished_weight*4/cfg.weight_reference == 1.


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
    actions, worlds, results = screening_table(view)
    # Real generated digests do not sort in ordinal order. Never mutate them.
    assert sorted(worlds[1:], key=lambda h: h['world_digest'])[0]['world_ordinal'] != 1
    for i, h in enumerate(worlds):
        for a in actions:
            r = results[a['assignment_key'], h['world_digest']]
            set_proxy_value(r, 0. if a['kind'] == 'KEEP' or i == 0 else 1.)
    out = w.screen_worlds(actions, worlds, results, view=view)
    assert out['H2']['world_ordinal'] == 1
    assert out['H3']['world_ordinal'] == 2
    assert out['h3_score'] == 1.
    for r in results.values():
        for task in r['tasks'].values(): task.update(P0=0., NG=0)
    assert w.screen_worlds(actions, worlds, results, view=view)['status'] == 'H2_NONTRIVIAL_BOUNDARY_UNAVAILABLE'


def test_h2_completed_boundary_and_no_alternative(view):
    actions, worlds, results = screening_table(view)
    for h in worlds:
        for a in actions:
            for task in results[a['assignment_key'], h['world_digest']]['tasks'].values():
                if task['complete_team']:
                    task.update(Pmax=2., NG=1, completion_tick=119 if h['world_ordinal'] == 2 else 100)
    assert w.screen_worlds(actions, worlds, results, view=view)['H2']['world_ordinal'] == 2
    keep_results = {k: v for k, v in results.items() if k[0] == actions[0]['assignment_key']}
    assert w.screen_worlds(actions[:1], worlds, keep_results, view=view)['status'] == 'H3_NO_ALTERNATIVE_ACTION'


def set_proxy_value(result, value):
    result['value'] = float(value)
    result['ledger'] = dict(completion=max(0., float(value)), flow=max(0., -float(value)),
                            late=0., effort=0., terminal=0., change=0.)


def screening_table(view):
    """Complete, identity-bound artificial proxy metrics; not physical evidence."""
    actions = candidates(view)['candidates']
    worlds = w.generate_worlds(view)['worlds']
    results = {}
    for a in actions:
        assigned, _ = c.team(a['actions'])
        for h in worlds:
            r = dict(proxy_role='OPTIMISTIC_Q_PROXY', assignment_key=a['assignment_key'],
                     world_digest=h['world_digest'], tasks={
                         t['id']: dict(P0=0., Pmax=1. if t['id'] == assigned else 0.,
                                       NG=1 if t['id'] == assigned else 0, duration=t['service_duration'],
                                       complete_team=t['id'] == assigned, completion_tick=None)
                         for t in view['targets']})
            set_proxy_value(r, 0.)
            results[a['assignment_key'], h['world_digest']] = r
    return actions, worlds, results


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


@pytest.mark.parametrize('field', ['tick', 'horizon', 'generation_rule', 'motion', 'public_input_digest'])
def test_world_identity_rejects_tampering(view, field):
    world = w.generate_worlds(view)['worlds'][0]
    if field == 'tick': world[field] = 80
    if field == 'horizon': world[field] = 119
    if field == 'generation_rule': world[field] = 'OTHER_RULE'
    if field == 'motion': world['motion'][0]['position'] = (6., 5.)
    if field == 'public_input_digest': world[field] = 'OTHER_PUBLIC_SNAPSHOT'
    with pytest.raises(ValueError): p.run_proxy(view, view['assignment'], world)


def test_world_binds_public_context_and_excludes_private_data(view):
    original = w.generate_worlds(view)
    view['private_sensor_schedule'] = object()
    view['future_actual_labels'] = object()
    view['beliefs'][0]['private_future_motion'] = object()
    assert w.generate_worlds(view) == original
    view['public_profiles'][0]['sigma'] = .03
    changed = w.generate_worlds(view)
    assert changed['worlds'][0]['motion'] == original['worlds'][0]['motion']
    assert changed['worlds'][0]['world_digest'] != original['worlds'][0]['world_digest']
    with pytest.raises(ValueError): p.run_proxy(view, view['assignment'], original['worlds'][0])


@pytest.mark.parametrize('q', ['FAIL', 'UNKNOWN'])
def test_recorded_nonpass_never_counts_first_interval(view, q):
    view['current_q'][0] = q
    view['current_endpoints'][0]['Q'] = q
    view['service_states'][0] = replace(view['service_states'][0], base=0.)
    world = w.generate_worlds(view)['worlds'][0]
    before = deepcopy(view)
    out = p.run_proxy(view, view['assignment'], world)
    assert out['left_endpoints'][0] == dict(source='RECORDED_PUBLIC_ENDPOINT', tick=60,
                                          G=True, Q=q, service_valid=False)
    assert out['tasks'][0]['completion_tick'] == 101
    assert out['tasks'][0]['NG'] == 41  # G-only count is independent of Q
    assert view == before


def test_recorded_g_is_not_recomputed_from_world(view):
    # A slightly shifted conditional position is outside current tolerance but
    # reachable at the right endpoint. The recorded left G must remain true.
    view['targets'][0]['design_error_bound'] = .31
    world = next(h for h in w.generate_worlds(view)['worlds']
                 if h['motion'][0]['position'] == (5.155, 5.)
                 and h['motion'][0]['velocity'] == (0., 0.))
    # Steer right endpoint to the conditional anchors, without rewriting history.
    def controlled_command(belief, tick, positions, roles, cfg):
        return np.array([[3., 0.]]) if tick == 60 else policy.command(belief, tick, positions, roles, cfg)
    with patch.object(p, 'command', side_effect=controlled_command):
        out = p.run_proxy(view, view['assignment'], world)
    assert out['left_endpoints'][0]['G'] is True
    assert out['tasks'][0]['NG'] >= 1
    assert out['tasks'][0]['Pmax'] >= .55
    # Conversely a recorded G=false cannot become true at the current endpoint.
    view['current_endpoints'][0]['G'] = False
    view['service_states'][0] = replace(view['service_states'][0], base=0.)
    nominal = w.generate_worlds(view)['worlds'][0]
    out = p.run_proxy(view, view['assignment'], nominal)
    assert out['left_endpoints'][0]['G'] is False
    assert out['tasks'][0]['completion_tick'] == 101
    assert out['tasks'][0]['NG'] == 40


def test_new_team_has_proxy_endpoint_not_recorded_pass(view):
    changed = next(a for a in candidates(view)['candidates'] if a['kind'] == 'MEMBER_CHANGE')
    world = w.generate_worlds(view)['worlds'][0]
    out = p.run_proxy(view, changed['actions'], world)
    assert out['tasks'][0]['P0'] == 0.
    assert out['left_endpoints'][0]['source'] == 'OPTIMISTIC_Q_PROXY'
    assert out['left_endpoints'][0]['Q'] == 'UNKNOWN'


@pytest.mark.parametrize('bad', ['missing', 'tick', 'team', 'g', 'source', 'positive_unknown'])
def test_invalid_recorded_endpoint_rejected(view, bad):
    ep = view['current_endpoints'][0]
    if bad == 'missing': view['current_endpoints'][0] = None
    if bad == 'tick': ep['tick'] = 59
    if bad == 'team': ep['team'] = ()
    if bad == 'g': ep['G'] = 1
    if bad == 'source': ep['source'] = 'CONDITIONAL_WORLD'
    if bad == 'positive_unknown':
        ep['Q'] = view['current_q'][0] = 'UNKNOWN'
    world = w.generate_worlds(view)['worlds'][0]
    with pytest.raises(ValueError): p.run_proxy(view, view['assignment'], world)


@pytest.mark.parametrize('y,vy', [(19.9, .1), (.1, -.1)])
def test_future_vertical_exit_blocks_h1(view, y, vy):
    view['beliefs'][0]['position_estimate'] = [5., y]
    view['beliefs'][0]['velocity_estimate'] = [0., vy]
    assert w.generate_worlds(view)['status'] == 'H1_INVALID'


def test_east_escape_truncates_vertical_admission(view):
    view['beliefs'][0]['position_estimate'] = [19.95, 19.9]
    view['beliefs'][0]['velocity_estimate'] = [.5, .5]
    out = w.generate_worlds(view)
    assert out['status'] == 'WORLDS_GENERATED'
    h1 = next(h for h in out['worlds'] if h['is_h1'])
    assert w.point(h1, 0, 120)[1] > 20.  # after legal east escape: irrelevant
    view['beliefs'][0]['position_estimate'][0] = 19.
    assert w.generate_worlds(view)['status'] == 'H1_INVALID'


@pytest.mark.parametrize('model', [None, 'unregistered', 'continuous_turn'])
def test_public_motion_model_required(view, model):
    if model is None:
        del view['targets'][0]['motion_model']
    else:
        view['targets'][0]['motion_model'] = model
    assert w.generate_worlds(view)['status'] == 'UNSUPPORTED_PUBLIC_MOTION_MODEL'


def test_non_nominal_filter_leaves_insufficient_worlds(view):
    for t in view['targets']:
        t.update(design_error_bound=0., speed_limit=0.)
    # nominal at the east edge remains active; east perturbations are outside.
    view['targets'][0].update(design_error_bound=1., speed_limit=.1)
    view['beliefs'][0]['position_estimate'] = [19.5, 20.]
    view['beliefs'][0]['velocity_estimate'] = [.1, 0.]
    # Remove position perturbations: only the nominal velocity survives speed bound.
    view['targets'][0]['design_error_bound'] = 0.
    assert w.generate_worlds(view)['status'] == 'WORLD_SET_INSUFFICIENT'
    # A nonzero position library can also be filtered to fewer than three:
    # enormous r makes all nonzero perturbations leave the initial physical domain.
    view['targets'][0]['design_error_bound'] = 100.
    out = w.generate_worlds(view)
    assert out['status'] == 'WORLD_SET_INSUFFICIENT'
    assert len(out['worlds']) == 1 and out['worlds'][0]['is_h1']
    assert w.screen_worlds([], out['worlds'], {}, view=view)['status'] == 'WORLD_SET_INSUFFICIENT'


@pytest.mark.parametrize('bad', ['digest', 'motion', 'context', 'ordinal', 'order', 'subset',
                                'h1', 'horizon', 'rule', 'tick', 'rehashed_motion'])
def test_screen_rejects_noncanonical_worlds(view, bad):
    actions, worlds, results = screening_table(view)
    if bad == 'digest': worlds[1]['world_digest'] = 'replaced'
    if bad in ('motion', 'rehashed_motion'):
        worlds[1]['motion'][0]['position'] = (6., 6.)
        if bad == 'rehashed_motion': worlds[1]['world_digest'] = w.world_digest(worlds[1])
    if bad == 'context': view['public_profiles'][0]['sigma'] = .1
    if bad == 'ordinal': worlds[1]['world_ordinal'] = 0
    if bad == 'order': worlds[1], worlds[2] = worlds[2], worlds[1]
    if bad == 'subset': worlds = worlds[:3]
    if bad == 'h1': worlds[1]['is_h1'] = True
    if bad == 'horizon': worlds[1]['horizon'] = 119
    if bad == 'rule': worlds[1]['generation_rule'] = 'foreign'
    if bad == 'tick': worlds[1]['tick'] = 80
    assert w.screen_worlds(actions, worlds, results, view=view)['status'] == 'SCREENING_VALIDATION_FAILED'


@pytest.mark.parametrize('bad', ['identity', 'assignment', 'source', 'missing_cell', 'extra_cell', 'duplicate',
                                'missing_task', 'extra_task', 'p0_nan', 'pmax_inf', 'ng_bool', 'ng_float',
                                'duration_nan', 'ct_float', 'value_nan', 'value_inf', 'ledger_missing',
                                'ledger_inf', 'ledger_mismatch'])
def test_screen_rejects_invalid_proxy_table(view, bad):
    actions, worlds, results = screening_table(view)
    cell = next(iter(results))
    r = results[cell]
    task = r['tasks'][0]
    if bad == 'identity': r['world_digest'] = 'foreign'
    if bad == 'assignment': r['assignment_key'] = actions[1]['assignment_key']
    if bad == 'source': r['proxy_role'] = 'MODEL'
    if bad == 'missing_cell': del results[cell]
    if bad == 'extra_cell': results[(cell[0], 'foreign')] = deepcopy(r)
    if bad == 'duplicate': results = list(results.items())+[(cell, deepcopy(r))]
    if bad == 'missing_task': del r['tasks'][0]
    if bad == 'extra_task': r['tasks'][99] = deepcopy(task)
    if bad == 'p0_nan': task['P0'] = math.nan
    if bad == 'pmax_inf': task['Pmax'] = math.inf
    if bad == 'ng_bool': task['NG'] = True
    if bad == 'ng_float': task['NG'] = 1.
    if bad == 'duration_nan': task['duration'] = math.nan
    if bad == 'ct_float': task['completion_tick'] = 90.
    if bad == 'value_nan': r['value'] = math.nan
    if bad == 'value_inf': r['value'] = math.inf
    if bad == 'ledger_missing': del r['ledger']['flow']
    if bad == 'ledger_inf': r['ledger']['flow'] = math.inf
    if bad == 'ledger_mismatch': r['value'] = 1.
    assert w.screen_worlds(actions, worlds, results, view=view)['status'] == 'SCREENING_VALIDATION_FAILED'


def test_h3_exact_difference_avoids_binary64_overflow_tie(view):
    actions, worlds, results = screening_table(view)
    large = float.fromhex('0x1.fffffffffffffp+1023')
    lesser = math.nextafter(large, 0.)
    for a in actions:
        for h in worlds:
            value = 0.
            if h['world_ordinal'] in (2, 3):
                magnitude = lesser if h['world_ordinal'] == 2 else large
                value = -magnitude if a['kind'] == 'KEEP' else magnitude
            set_proxy_value(results[a['assignment_key'], h['world_digest']], value)
    out = w.screen_worlds(actions, worlds, results, view=view)
    assert out['H2']['world_ordinal'] == 1
    assert out['H3']['world_ordinal'] == 3  # rounded float differences both overflow
    assert out['h3_score'] == 2*Fraction.from_float(large)


def test_h2_exact_recorded_margin_and_reproducibility(view):
    actions, worlds, results = screening_table(view)
    for a in actions:
        for h in worlds:
            for task in results[a['assignment_key'], h['world_digest']]['tasks'].values():
                if task['complete_team']:
                    task['Pmax'] = math.nextafter(2.-w.TOL, 0.) if h['world_ordinal'] == 2 else 1.
    before = deepcopy((view, actions, worlds, results))
    out = w.screen_worlds(actions, worlds, results, view=view)
    assert out['H2']['world_ordinal'] == 2
    expected = abs(math.nextafter(2.-w.TOL, 0.)-(2.-w.TOL))
    assert out['h2_score'] == Fraction.from_float(expected)
    assert w.screen_worlds(actions, worlds, results, view=view) == out
    assert (view, actions, worlds, results) == before


def test_h3_exact_finite_difference_breaks_rounded_tie(view):
    actions, worlds, results = screening_table(view)
    base = float(2**53)
    for a in actions:
        for h in worlds:
            value = 0.
            if h['world_ordinal'] in (2, 3):
                value = (-.5 if h['world_ordinal'] == 2 else -1.) if a['kind'] == 'KEEP' else base
            set_proxy_value(results[a['assignment_key'], h['world_digest']], value)
    assert base-(-.5) == base-(-1.)  # binary64 subtraction erases this distinction
    out = w.screen_worlds(actions, worlds, results, view=view)
    assert out['H3']['world_ordinal'] == 3
    assert out['h3_score'] == Fraction(2**53+1)


def test_complete_real_g_only_proxy_table_satisfies_contract(view):
    # Four legal worlds, all evaluated; no arbitrary subset and no WLS/MODEL.
    for t in view['targets']:
        t['design_error_bound'] = 0.
    actions = candidates(view)['candidates']
    worlds = w.generate_worlds(view)['worlds']
    assert len(worlds) == 4
    results = {(a['assignment_key'], h['world_digest']): p.run_proxy(view, a['actions'], h)
               for a in actions for h in worlds}
    assert w.screen_worlds(actions, worlds, results, view=view)['status'] == 'WORLD_SET_FROZEN'
