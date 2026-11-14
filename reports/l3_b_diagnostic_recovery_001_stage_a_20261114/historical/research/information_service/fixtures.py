"""Freeze deterministic 2A-5b-A inputs and analytical expectations.

This module never imports or calls WLS, a production rollout, or a quality
implementation.  freeze_inputs constructs Config only to serialize its full
values.  All coordinates, perturbations and expected transitions are declared
before any estimate is evaluated.
"""
from dataclasses import asdict
import math
from pathlib import Path

from .common import CONTRACT_ID, DT, DELTA, DOMAIN, digest, save_json
from .oracle import clock_reference, quality_at, ray_intersection, truth_error


ROLES = {2: ('dual_neg45', 'dual_pos45'), 3: ('tri_0', 'tri_120', 'tri_240')}
ANGLES = {2: (-45.0, 45.0), 3: (0.0, 120.0, 240.0)}
CASE_ORDER = ('C1', 'C2', 'C3', 'C4', 'G_FALSE', 'P1', 'P2', 'D06', 'D08')


def _wrap(value):
    return (value + math.pi) % (2 * math.pi) - math.pi


def public_payload(frame):
    """Generator-side extraction only; not a replacement for public_adapter."""
    rows = sorted(frame['records'], key=lambda row: int(row['sensor_id'][1:]))
    return dict(sensor_ids=[row['sensor_id'] for row in rows],
                positions=[list(row['position']) for row in rows],
                bearings=[row['bearing'] for row in rows],
                sigmas=[row['sigma'] for row in rows],
                domain=[list(row) for row in DOMAIN])


def _frame(case_id, q, tick):
    at = tick * DT
    truth = [8.0 + 0.4 * at, 10.0]
    positions = []
    for i, angle in enumerate(ANGLES[q]):
        radius = 0.76 if case_id == 'G_FALSE' and i == 0 else 0.6
        radians = math.radians(angle)
        positions.append([truth[0] + radius * math.cos(radians),
                          truth[1] + radius * math.sin(radians)])
    if q == 2:
        positions.append([2.0, 2.0])
    if case_id == 'D08':
        positions = [[7.4, 10.0], [8.6, 10.0], [2.0, 2.0]]
    records = []
    for i in range(q):
        if 10 <= tick < 20 and ((case_id == 'C3' and i == 1) or
                              (case_id == 'C4' and i == 2)):
            continue
        position = positions[i]
        bearing = math.atan2(truth[1] - position[1], truth[0] - position[0])
        if case_id in ('P1', 'P2'):
            sign = 1 if case_id == 'P1' else -1
            bearing += sign * (0.01 if i == 0 else -0.01)
        sigma = 0.08 if case_id == 'C2' and 10 <= tick < 20 else 0.02
        records.append(dict(sensor_id='U' + str(i), position=list(position),
                            bearing=_wrap(bearing), sigma=sigma,
                            packet_id=f'{CONTRACT_ID}:{case_id}:{tick}:U{i}',
                            measurement_tick=tick, available_tick=tick, status='ok'))
    public = dict(contract_id=CONTRACT_ID, stream_id=f'{CONTRACT_ID}:{case_id}',
                  frame_id=f'{case_id}:{tick}', tick=tick, target_id=0,
                  measurement_time=at, available_time=at, records=records)
    expected_G = case_id not in ('G_FALSE', 'D08')
    return dict(public=public, truth=truth, positions=positions,
                powers=[0.16] * q + ([0.0] if q == 2 else []), expected_G=expected_G)


def _case(case_id, config):
    q = 3 if case_id == 'C4' else 2
    ticks = range(61) if case_id in ('C1', 'C2', 'C3', 'C4') else \
            range(2) if case_id == 'G_FALSE' else range(1)
    frames = [_frame(case_id, q, n) for n in ticks]
    expected_frames = []
    for frame in frames:
        payload = public_payload(frame['public'])
        ideal = list(frame['truth'])
        intersection = None
        if case_id in ('P1', 'P2'):
            intersection = ray_intersection(payload)
            ideal = intersection['intersection']
        if case_id == 'D08':
            intersection = ray_intersection(payload)
            ideal = None
        reference = quality_at(payload, frame['truth'] if ideal is None else ideal, delta=DELTA)
        if len(payload['sensor_ids']) < 2 or reference['numerical_ill_conditioned']:
            expected_Q = 'UNKNOWN'
        else:
            expected_Q = 'PASS' if reference['analytic_radius_pass'] else 'FAIL'
        expected_frames.append(dict(tick=frame['public']['tick'], expected_G=frame['expected_G'],
                                    expected_Q=expected_Q, ideal_estimate=ideal,
                                    ideal_truth_error=truth_error(ideal, frame['truth']),
                                    scalar_quality_reference=reference,
                                    ray_intersection=intersection))
    team = [[i, role] for i, role in enumerate(ROLES[q])]
    common_clock = dict(duration=1.0, dt=DT, team=team,
                        powers=[frame['powers'] for frame in frames], end_time=3.0)
    ticks = [frame['public']['tick'] for frame in frames]
    G = [frame['expected_G'] for frame in frames]
    Q = [row['expected_Q'] for row in expected_frames]
    expected = dict(provenance='pre-estimation analytical construction; not a WLS or simulation result',
                    endpoint_references=expected_frames,
                    G_ledger=clock_reference(ticks, G, **common_clock),
                    GQ_ledger=clock_reference(ticks, G, Q, **common_clock))
    if case_id in ('P1', 'P2'):
        expected['perturbation_radians'] = [0.01, -0.01] if case_id == 'P1' else [-0.01, 0.01]
        expected['purpose'] = 'Two-ray estimate must respond to public bearing changes, not truth metadata'
    elif case_id == 'D06':
        expected['purpose'] = 'Reuse identical public frame under changed private truth/labels; hold G fixed'
        expected['hidden_truth_variants'] = [[8.0, 10.0], [9.0, 9.0]]
    elif case_id == 'D08':
        expected['purpose'] = 'Standalone collinear sensing probe; not legal angular service geometry'
    elif case_id == 'G_FALSE':
        expected['purpose'] = 'Two-endpoint G=false/Q=PASS wiring probe, not a three-second rollout'
    return dict(case_id=case_id, contract_id=CONTRACT_ID, q=q, team=team,
                duration=1.0, end_time=3.0, birth=0.0, deadline=2.0,
                config=dict(config), frames=frames, expected=expected)


def _short_test_definitions():
    """Inventory of the exact checklist/tests, not a second experiment set.

    Nonfinite malformed inputs are described as mutations, never serialized as
    nonstandard JSON values.  Actual test code and its execution log determine
    coverage; recording a requirement here is not evidence it has run.
    """
    return dict(
        version=CONTRACT_ID,
        scope='pure rules and short probes; no additional complete WLS replay',
        checklist='docs/STAGE2A5B_A_EXECUTION_CHECKLIST.md',
        clock_test_module='tests/test_information_service_clock.py',
        public_test_module='tests/test_information_service_public.py',
        clock_defaults=dict(team=[[0, 'dual_neg45'], [1, 'dual_pos45']],
                            dt=0.05, initial_progress=0.0, G=True,
                            powers=[0.16, 0.16, 0.0], end_time=3.0),
        quality_boundaries=[dict(radius=math.nextafter(DELTA, -math.inf), expected='PASS'),
                            dict(radius=DELTA, expected='PASS'),
                            dict(radius=math.nextafter(DELTA, math.inf), expected='FAIL')],
        clock_sequences=[
            dict(case_id='S01', test='test_s01_initial_endpoint_has_no_interval',
                 ticks=[0, 1], Q=['PASS', 'PASS'], duration=0.05,
                 expected_progress=[0.0, 0.05], expected_completion_tick=1,
                 expected_initial_events=[], expected_release_count=1),
            dict(case_id='S02', test='test_s02_initial_bad_endpoint_no_backfill',
                 ticks=[0, 1, 2], Q=['FAIL', 'PASS', 'PASS'], duration=0.05,
                 expected_progress=[0.0, 0.0, 0.05], expected_completion_tick=2),
            dict(case_id='S03', test='test_s03_noninteger_h_and_frozen_terminal',
                 ticks=[0, 1, 2, 3, 4], Q=['PASS'] * 5, duration=0.12,
                 expected_progress=[0.0, 0.05, 0.10, 0.12, 0.12],
                 expected_completion_tick=3, expected_completion_window_ticks=[0, 1, 2, 3],
                 terminal_check='tick 4 adds no event/release/effort and has no occupied robot'),
            dict(case_id='S04', test='test_s04_failure_unknown_recovery_and_two_ledgers',
                 ticks=list(range(9)), Q=['PASS'] * 3 + ['FAIL'] * 2 + ['PASS'] * 4,
                 duration=0.15, expected_progress=[0.0, 0.05, 0.10, 0.0, 0.0, 0.0, 0.05, 0.10, 0.15],
                 expected_completion_tick=8, expected_completion_window_ticks=[5, 6, 7, 8],
                 expected_interruption_tick=3, expected_lost_progress=0.10,
                 expected_interruption_count=1, expected_reason='quality_threshold',
                 expected_G_ledger_completion_tick=3),
            dict(case_id='S04_U', checklist_id='S04',
                 test='test_s04_failure_unknown_recovery_and_two_ledgers',
                 ticks=list(range(9)), Q=['PASS'] * 3 + ['UNKNOWN'] * 2 + ['PASS'] * 4,
                 duration=0.15, expected_progress=[0.0, 0.05, 0.10, 0.0, 0.0, 0.0, 0.05, 0.10, 0.15],
                 expected_completion_tick=8, expected_completion_window_ticks=[5, 6, 7, 8],
                 expected_interruption_tick=3, expected_lost_progress=0.10,
                 expected_interruption_count=1, expected_reason='quality_unavailable',
                 expected_G_ledger_completion_tick=3),
            dict(case_id='S05', test='test_s05_bad_left_endpoint_clears_history_immediately',
                 ticks=[4, 5, 6, 7, 8], Q=['FAIL'] + ['PASS'] * 4,
                 duration=0.12, initial_progress=0.10,
                 expected_progress=[0.0, 0.0, 0.05, 0.10, 0.12],
                 expected_completion_tick=8, expected_interruption_tick=4,
                 expected_lost_progress=0.10, expected_initial_effort=0.0),
            dict(case_id='S06', test='test_s06_escape_wins_completion_tie',
                 ticks=[0, 1, 2, 3, 4], Q=['PASS'] * 5, duration=0.15, escape_time=0.15,
                 expected_status='ESCAPED', expected_completion_tick=None,
                 expected_final_progress=0.10, expected_prefix_effort=0.048,
                 expected_occupied_robot_seconds=0.30, expected_release_count=1),
            dict(case_id='S07', test='test_s07_offgrid_escape_truncates_cost_not_service',
                 ticks=[0, 1, 2, 3, 4], Q=['PASS'] * 5, duration=0.15, escape_time=0.073,
                 expected_status='ESCAPED', expected_final_progress=0.05,
                 expected_prefix_effort=0.02336, expected_occupied_robot_seconds=0.146,
                 expected_escape_tick=None, expected_release_count=1),
            dict(case_id='S08', test='test_s08_json_snapshot_split_and_shared_endpoint',
                 ticks=[0, 1, 2, 3, 4], Q=['PASS'] * 5, duration=0.12,
                 segments=[[0, 1, 2], [2, 3, 4]], snapshot_encoding='JSON round trip',
                 expected_completion_tick=3,
                 expected='shared tick 2 is cached; resumed frames and final snapshot equal whole stream'),
            dict(case_id='S09', test='test_s09_end_time_completion_then_unfinished',
                 ticks=[57, 58, 59, 60], Q=['PASS'] * 4, end_time=3.0,
                 initial_progress=0.0, scope='specified tail only, not whole-episode accounting',
                 variants=[dict(duration=0.15, expected_status='COMPLETED',
                                expected_completion_tick=60, expected_final_progress=0.15),
                           dict(duration=0.20, expected_status='UNFINISHED',
                                expected_completion_tick=None, expected_final_progress=0.15)],
                 terminal_check='identical tick 60 is cached; tick 61 rejected atomically; one release'),
        ],
        adapter_probes=[
            dict(case_id='D01', test='test_D01_stale_frame_is_unknown_without_estimation',
                 input_factory='tests/test_information_service_public.py:frame',
                 estimator='CountingEstimator, not WLS', submitted_ticks=[0, 1],
                 mutation='replace BOTH tick-1 records with unchanged tick-0 records',
                 expected_valid_sensor_count=0, expected_excluded_count=2,
                 expected_status='UNKNOWN', expected_reason='insufficient_measurements',
                 expected_tick1_estimator_calls=0, expected_total_estimator_calls=1,
                 expected_last_tick=1),
            dict(case_id='D02', test='test_D02_exact_replay_is_cached_and_returns_a_copy',
                 input_factory='tests/test_information_service_public.py:frame',
                 estimator='CountingEstimator, not WLS', submitted_ticks=[0, 1, 1, 2],
                 mutation='second tick-1 frame is an exact deep copy; then mutate returned estimate copy',
                 expected_estimator_call_counts=[1, 2, 2, 3],
                 expected='duplicate flags true; saved payload/hashes/result/Q unchanged; cache not externally mutable',
                 clock_checklist_requirement=dict(duration=0.10, expected_completion_tick=2,
                                                   note='clock coverage must be recorded separately from public-only test')),
            dict(case_id='D03', test='test_D03_conflicting_frame_and_packet_do_not_overwrite',
                 input_factory='tests/test_information_service_public.py:frame',
                 mutations=['after tick 0 reuse its frame identity and add .01 to U0 bearing',
                            'in tick-1 shell reuse tick-0 packets and add .01 to U0 bearing'],
                 expected='ContractError for conflicting frame/previously received packet; original state unchanged',
                 expected_last_tick=0, expected_estimator_calls=1),
            dict(case_id='D04', test='test_D04_missing_tick_is_not_skipped',
                 input_factory='tests/test_information_service_public.py:frame',
                 submitted_ticks=[0, 2], expected='ContractError; cannot skip missing tick 1',
                 expected_last_tick_after_error=0, expected_estimator_calls_after_error=1,
                 recovery='submit explicit empty-record tick 1, then tick 2; final last_tick is 2'),
            dict(case_id='D05', test='test_D05_illegal_time_identity_and_numeric_fields_are_fatal',
                 input_factory='tests/test_information_service_public.py:frame',
                 mutations=[
                     'tick-0 U0 measurement_tick=1', 'tick-0 U0 available_tick=1',
                     'tick-0 U0 measurement_tick=-1', 'tick-0 U0 available_tick=-1',
                     'U0 position=[1.]', "U0 position=[float('nan'),0.]",
                     "U0 bearing=float('inf')", 'U0 sigma=0.', 'U0 sigma=-1.',
                     "U0 sigma=float('nan')", 'U0 sigma=True', 'U0 sensor_id=U2',
                     'U0 status=private_fault', 'tick-1 U0 available_tick=0 (negative delay)',
                     'change U1 sensor_id to U0 (duplicate robot)', 'frame tick=True',
                     'frame measurement_time=-1.', 'tick-0 frame available_time=.05',
                     'frame contract_id=wrong', 'extra frame truth=[8.,10.]',
                     'extra U0 record case=favorable',
                 ], expected='ContractError for every variant; not ordinary missing data'),
            dict(case_id='D06', source='inputs/D06.public.json',
                 estimator='two real WLS calls in independent FrameProcessor instances',
                 mutation='identical public frame; evaluator changes private truth/case metadata only',
                 expected='same estimate/Q fields and normalized payload; fix G for any clock comparison',
                 whitelist_check='adding truth to the five-field payload is ContractError'),
            dict(case_id='D07', test='test_D07_member_order_preserves_canonical_payload_and_hashes',
                 input_factory='tests/test_information_service_public.py:frame',
                 mutation='reverse both record order and allowed_sensor_ids; preserve paired fields and Uk',
                 expected='same normalized payload/payload hash/frame hash; canonical ids U0,U1; input unchanged',
                 real_wls_calls=0, production_probe_reference='reuse D06 output, no additional solve'),
        ],
        integration_requirements=[
            'D06 public output invariant under private metadata changes; fix G for clock comparison',
            'D08 collinear geometry cannot be reported as reliable localization service',
            'canonical member order does not change a fixed-team clock',
            'terminal replay does not create a second completion or release',
            'split replay matches full replay with persisted identity and previous endpoint',
            'unavailable/diagnostic failures preserve records; NumericContractViolation stops batch',
        ])


def freeze_inputs(folder):
    """Create new input/expected assets without estimates or model execution."""
    from pursuit_v2.config import Config
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    reserved = ['config_expanded.json', 'inputs', 'expected', 'short_tests.json', 'input_manifest.json']
    for name in reserved:
        if (folder / name).exists():
            raise FileExistsError(folder / name)
    config = asdict(Config(robots=3, task_count=1, side=20.0, max_stages=1,
                           stage_dt=3.0, step_dt=DT, risk_prediction_dt=DT,
                           capture_mode='stepwise_service', geometry_mode='angular_standoff_v1',
                           observation_radius=0.6, observation_tolerance=0.15))
    save_json(folder / 'config_expanded.json', config)
    cases, public_files, identities = {}, {}, {}
    for case_id in CASE_ORDER:
        case = _case(case_id, config)
        input_path, expected_path = f'inputs/{case_id}.json', f'expected/{case_id}.json'
        save_json(folder / input_path, case)
        save_json(folder / expected_path, case['expected'])
        public_path = f'inputs/{case_id}.public.json'
        public_case = dict(case_id=case_id,
                           allowed_sensor_ids=['U' + str(i) for i, _ in case['team']],
                           frames=[frame['public'] for frame in case['frames']])
        save_json(folder / public_path, public_case)
        public_files[case_id] = public_path
        cases[case_id] = dict(input=input_path, expected=expected_path,
                              public_input=public_path,
                              endpoint_count=len(case['frames']), q=case['q'])
        identities[input_path] = digest(case)
        identities[expected_path] = digest(case['expected'])
        identities[public_path] = digest(public_case)
    short = _short_test_definitions()
    save_json(folder / 'short_tests.json', short)
    identities['config_expanded.json'] = digest(config)
    identities['short_tests.json'] = digest(short)
    # Byte hashes complement canonical JSON identities; both are immutable inputs.
    import hashlib
    byte_hashes = {name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
                   for name in identities}
    manifest = dict(contract_id=CONTRACT_ID, case_order=list(CASE_ORDER), cases=cases,
                    public_files=public_files,
                    canonical_sha256=identities, file_sha256=byte_hashes,
                    full_replay_cases=list(CASE_ORDER[:4]),
                    full_replay_endpoints=244, full_replay_wls_calls_upper=244,
                    nominal_full_replay_wls_calls_after_insufficient_data_gate=234,
                    full_replay_local_starts_upper=2196,
                    scope='deterministic A-only inputs and scalar/Fraction expectations; no B sampling')
    save_json(folder / 'input_manifest.json', manifest)
    return manifest
