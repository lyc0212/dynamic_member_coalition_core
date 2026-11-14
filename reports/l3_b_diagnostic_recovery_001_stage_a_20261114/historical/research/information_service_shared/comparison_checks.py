"""SG05's 30 frozen checks, calling the production comparator directly.

Expected values remain here in the driver and are never arguments to the
production comparator or energy reducer.  Importing this module runs nothing.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .common import ContractError, save_json, sha_file
from .comparator import (COMPARATOR_ID, ComparisonAdmission, compare_artifacts,
                         compare_raw, describe, first_difference, strict_loads)


def test_metadata(check_id, scope='raw_json_unit_test'):
    return dict(artifact_scope=scope, left_artifact_id='SG05:' + check_id + ':left',
                right_artifact_id='SG05:' + check_id + ':right', scientific_request_id=None,
                candidate_id_or_null=None, comparison_route='COMPARATOR_SELF_TEST')


def _raw(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')


def _expect(actual, expected, path=''):
    """Driver-only exact assertion, allowing extra diagnostic report metadata."""
    if type(expected) is dict:
        if type(actual) is not dict:
            raise ContractError('SG05 expectation type mismatch at ' + path)
        for key, value in expected.items():
            if key not in actual:
                raise ContractError('SG05 missing observed field ' + path + '/' + key)
            _expect(actual[key], value, path + '/' + key)
    else:
        diff = first_difference(actual, expected)
        if diff is not None:
            raise ContractError('SG05 observed mismatch at ' + path + ': ' + str(diff))


def _mutate(wrapper, mutation):
    parts = mutation['json_pointer'].split('/')[1:]
    parts = [p.replace('~1', '/').replace('~0', '~') for p in parts]
    parent = wrapper
    for part in parts[:-1]:
        parent = parent[int(part)] if type(parent) is list else parent[part]
    key = int(parts[-1]) if type(parent) is list else parts[-1]
    if mutation['op'] == 'replace':
        if type(parent) is dict and key not in parent:
            raise ContractError('Frozen replacement target is absent')
    elif mutation['op'] == 'add':
        if type(parent) is dict and key in parent:
            raise ContractError('Frozen add target already exists')
    else:
        raise ContractError('Undeclared SG05 mutation operation')
    parent[key] = deepcopy(mutation['value'])


def energy_order_witness(force_by_tick_robot_xy, elapsed_by_tick):
    """Exercise the S evaluator's production increment; no control or WLS."""
    import numpy as np
    from .evaluator import energy_increment

    if len(force_by_tick_robot_xy) != len(elapsed_by_tick) or not force_by_tick_robot_xy:
        raise ContractError('Energy witness requires aligned nonempty intervals')
    forces = [np.ascontiguousarray(force, dtype=float) for force in force_by_tick_robot_xy]
    if any(force.ndim != 2 or force.shape[1] != 2 or force.shape != forces[0].shape for force in forces):
        raise ContractError('Energy witness requires stable q-by-2 force rows')
    if any(type(dt) is not float or not (dt > 0) for dt in elapsed_by_tick):
        raise ContractError('Energy witness requires positive binary64 intervals')
    total = 0.0
    increments = []
    for force, elapsed in zip(forces, elapsed_by_tick):
        increment = energy_increment(force, elapsed)
        if type(increment) is not float:
            raise ContractError('Production energy increment changed type')
        increments.append(increment)
        total += increment
    # The forbidden reassociation is deliberately a synthetic counterexample,
    # never an alternative energy implementation used by an evaluated branch.
    robot_totals = []
    for robot in range(forces[0].shape[0]):
        partial = 0.0
        for force, elapsed in zip(forces, elapsed_by_tick):
            partial += float(np.sum(force[robot] ** 2)) * elapsed
        robot_totals.append(partial)
    reassociated = 0.0
    for partial in robot_totals:
        reassociated += partial
    report = compare_raw(_raw({'energy': total}), _raw({'energy': reassociated}),
                         test_metadata('E01_time_before_robot_reduction'))
    return dict(production_reducer='research.information_service_shared.evaluator.energy_increment',
                production_increment_calls=len(increments), first_tick=describe(increments[0]),
                original=describe(total), forbidden=describe(reassociated), comparison=report,
                must_detect_reassociation=report['status'] == 'DIFFERENT', real_WLS=0)


def _assert_contract(document):
    if document.get('comparator_id') != COMPARATOR_ID:
        raise ContractError('Wrong frozen comparison contract')
    if document.get('protocol_id') != 'STAGE2A5B-GQ-SHARED-FULL-v1.0':
        raise ContractError('Wrong SG05 protocol identity')
    groups = ('comparator_self_tests', 'context_projection_self_tests', 'arithmetic_order_witnesses')
    if [len(document.get(k, {})) for k in groups] != [24, 5, 1]:
        raise ContractError('SG05 requires the exact frozen 24+5+1 vectors')
    if document['self_test_accounting']['total_checks'] != 30:
        raise ContractError('SG05 count changed')


def run_checks(comparison_file, out, *, expected_sha256):
    """Run all SG05 declarations after runtime seal; any mismatch raises."""
    if sha_file(comparison_file) != expected_sha256:
        raise ContractError('SG05 comparison file differs from external protocol pin')
    document = strict_loads(Path(comparison_file).read_bytes())
    _assert_contract(document)
    out = Path(out)
    records = []
    active_id = None
    observed = None
    try:
        for check_id, case in document['comparator_self_tests'].items():
            active_id = check_id
            if case['kind'] != 'raw_json_pair' or case['real_WLS'] != 0:
                raise ContractError('Undeclared SG05 raw probe kind/budget')
            observed = compare_raw(case['left_json'], case['right_json'], test_metadata(check_id))
            save_json(out / (check_id + '.observed.json'), observed)
            _expect(observed, case['expected'])
            records.append(dict(check_id=check_id, passed=True, production_entry='comparator.compare_raw',
                                observed_file=str((out / (check_id + '.observed.json')).resolve())))
        for check_id, case in document['context_projection_self_tests'].items():
            active_id = check_id
            if case['fixture_ref'] != '#/context_projection_fixture' or case['real_WLS'] != 0:
                raise ContractError('Unknown SG05 context fixture')
            sides = {side: deepcopy(document['context_projection_fixture'][side]) for side in ('left', 'right')}
            for side in sides:
                if sides[side]['fixture_scope'] != 'unit_only_no_actual_history_claim':
                    raise ContractError('SG05 context fixture must stay unit-only')
                _expect(sides[side]['external_expected_registration']['context'], sides[side]['external_expected_context'])
            for mutation in case['mutations']:
                _mutate(sides[mutation['side']], mutation)
            raw = {side: _raw(sides[side]['row']) for side in sides}
            gates = {side: ComparisonAdmission.unit_fixture(
                source_sha256=hashlib.sha256(raw[side]).hexdigest(),
                registration=sides[side]['external_expected_registration']) for side in sides}
            observed = compare_artifacts(raw['left'], raw['right'],
                metadata=test_metadata(check_id, 'fusion_row_unit_context_test'),
                left_admission=gates['left'], right_admission=gates['right'])
            save_json(out / (check_id + '.observed.json'), observed)
            expected = case['expected']
            _expect(observed['status'], expected['status'])
            if expected['status'] == 'EQUAL':
                _expect(len(observed['context_admissions']), 2)
                _expect(all(x['passed'] is True and x['unit_only'] is True for x in observed['context_admissions']), True)
                _expect(observed['first_difference'], None)
            else:
                _expect(observed['rejection'], {k: v for k, v in expected.items() if k in ('side', 'json_pointer', 'code')})
                _expect(observed['omitted_operation_fields'], [])
            records.append(dict(check_id=check_id, passed=True, production_entry='comparator.compare_artifacts',
                                synthetic_unit_only=True, observed_file=str((out / (check_id + '.observed.json')).resolve())))
        for check_id, case in document['arithmetic_order_witnesses'].items():
            active_id = check_id
            observed = energy_order_witness(case['force_by_tick_robot_xy'], case['elapsed_by_tick'])
            save_json(out / (check_id + '.observed.json'), observed)
            _expect(observed['first_tick'], case['first_tick_rounded_binary64'])
            _expect(observed['original'], case['original_tick_then_time_result'])
            _expect(observed['forbidden'], case['forbidden_robot_then_time_then_robot_result'])
            _expect(observed['must_detect_reassociation'], case['expected']['must_detect_reassociation'])
            records.append(dict(check_id=check_id, passed=True, production_entry=observed['production_reducer'],
                                synthetic_unit_only=True, observed_file=str((out / (check_id + '.observed.json')).resolve())))
        if len(records) != 30 or len({x['check_id'] for x in records}) != 30:
            raise ContractError('SG05 did not execute exactly all30 cases')
    except Exception as error:
        save_json(out / 'failure.json', dict(check_id=active_id, error_type=type(error).__name__, error=str(error),
                                            observed=observed, completed=records))
        save_json(out / 'result.json', dict(passed=False, completed_check_count=len(records), checks=records,
                                           real_WLS=0, local_starts=0, failure_check_id=active_id))
        raise
    result = dict(passed=True, check_count=30, checks=records, comparison_sha256=expected_sha256,
                  real_WLS=0, local_starts=0, scope='SG05 production comparator and energy-order unit checks; no model rollout or actual-history authority')
    save_json(out / 'result.json', result)
    return result
