"""Pinned saved-result audits; frozen strict comparison and cache oracle reused.

The subset adapter overrides only current producer metadata admission. Old
modules/classes/globals remain untouched; no motion, controller or WLS runs.
"""
from collections import Counter
import hashlib
import math
from pathlib import Path

from research.information_service_shared.common import save_json, safe_label
from research.information_service_shared.artifact_admission import ArtifactAdmissions, pinned_read
from research.information_service_shared.comparator import strict_loads
from research.information_service_future_profile import auditor as legacy
from .common import CONTRACT, require


INDICES = [8, 9, 10, 11]
RUNS = ['OLD_a', 'NEW_a', 'NEW_b', 'OLD_b']
RECORD_FIELDS = frozenset((
    'message_kind', 'record_version', 'contract_id', 'attempt_id', 'pair_id',
    'run_id', 'condition', 'producer_pid', 'producer_pgid', 'producer_start_ticks',
    'cache_scope_id', 'event_index', 'event_kind', 'event_digest', 'measurement_index',
    'current_bytes', 'peak_before_bytes', 'peak_after_bytes',
    'previous_measured_event_frontier', 'observed_event_frontier',
    'absorbed_event_indices', 'tracking_mode'))
DECLARATION_FIELDS = frozenset((
    'run_id', 'condition', 'repeat', 'method', 'attempt_id', 'pair_id',
    'physical_environment_id', 'runtime_binding_id', 'expected_source_seal_sha256',
    'expected_indices'))


def _same(left, right, code):
    require(legacy.first_difference(left, right) is None, code)


def _read(job, path):
    return pinned_read(job, path)


def _integer(value, code):
    require(type(value) is int and value >= 0, code)


def validate_current_metadata(producer, declaration, declaration_file):
    job, payload = producer['job'], producer['job']['env_start']
    require(DECLARATION_FIELDS <= set(declaration), 'CURRENT_DECLARATION_FIELDS')
    require(declaration['run_id'] in RUNS and declaration['condition'] in ('OLD', 'NEW') and
            declaration['repeat'] in ('a', 'b') and
            declaration['run_id'] == declaration['condition'] + '_' + declaration['repeat'],
            'CURRENT_RUN_IDENTITY')
    for key in ('attempt_id', 'pair_id'):
        _same(job[key], declaration[key], 'CURRENT_PRODUCER_IDENTITY')
    _same(payload['kind'], 'predict_shared', 'CURRENT_SHARED_KIND')
    _same(payload['method'], 'S', 'CURRENT_METHOD')
    _same(declaration['method'], 'S', 'CURRENT_METHOD')
    for key in ('physical_environment_id', 'runtime_binding_id'):
        _same(payload[key], declaration[key], 'CURRENT_RUNTIME_BINDING')
    _same(declaration['expected_indices'], INDICES, 'CURRENT_SUBSET')
    _same([w['candidate']['index'] for w in payload['work_items']], INDICES, 'CURRENT_SUBSET')
    meta = payload['memory_accounting']
    for key in ('run_id', 'condition', 'repeat'):
        _same(meta[key], declaration[key], 'CURRENT_MEMORY_META')
    _same(meta['variant'], declaration['condition'], 'CURRENT_VARIANT')
    _same(meta['runtime_binding_id'], declaration['runtime_binding_id'], 'CURRENT_MEMORY_RUNTIME')
    _same(meta['execution_source_seal_sha256'], declaration['expected_source_seal_sha256'],
          'CURRENT_SOURCE_SEAL')
    _same(meta['run_declaration_file'], declaration_file, 'CURRENT_DECLARATION_SOURCE')
    require('cost_profile' not in payload, 'PROFILE_METADATA_FORBIDDEN_IN_UNPROFILED_MEMORY_RUN')


class SubsetAdmissions(legacy.SubsetAdmissions):
    """Retain frozen four-candidate scientific/schema/flow admission bodies."""
    def _load_producer(self, descriptor):
        if self.source_role == 'historical_reference':
            return super()._load_producer(descriptor)
        producer = ArtifactAdmissions._load_producer(self, descriptor)
        validate_current_metadata(producer, self.declaration, self.job['run_declaration_file'])
        guardian = producer['guardian']
        for key, value in (('total_cpu', 240.0), ('pair_cpu', 60.0), ('pair_wall', 120.0)):
            _same(guardian['limits'][key], value, 'CURRENT_RESOURCE_LIMIT')
        receipt, _ = _read(self.job, descriptor['supervision_receipt_file'])
        for key, value in (('adapter_id', 'gq_memory_accounting_supervision_v1'),
                           ('attempt_id', self.declaration['attempt_id']),
                           ('pair_id', self.declaration['pair_id']),
                           ('status', 'RETURNED_VALIDATED'), ('defaults_restored', True),
                           ('default_object_identity_preserved', True), ('guardian_returned', True)):
            _same(receipt.get(key), value, 'CURRENT_SUPERVISION_RECEIPT')
        _same(receipt['validation_errors'], [], 'CURRENT_SUPERVISION_FAILED')
        _same(receipt['effective_limits'], guardian['limits'], 'CURRENT_RESOURCE_LIMIT')
        _same(receipt['defaults_before'], receipt['defaults_after'], 'CURRENT_DEFAULT_RESTORE')
        for key in ('cumulative_before', 'cumulative_after'):
            _same(receipt[key], guardian[key], 'CURRENT_RESOURCE_CHAIN')
        _, guardian_pin = _read(self.job, descriptor['guardian_result_file'])
        _same(receipt['guardian_result_sha256'], guardian_pin['sha256'], 'CURRENT_GUARDIAN_PIN')
        _same(receipt['absolute_deadline'], receipt['original_global_deadline'], 'CURRENT_DEADLINE')
        final = receipt['final_records_audit']
        require(final['complete'] is True and final['errors'] == [], 'CURRENT_FINAL_ACCOUNTING')
        self.loaded_producers.append(producer)
        return producer


def validate_sidecar_rows(rows, trace, binding, variant):
    """Pure fixed-normal-path shape/identity/peak check; no live graph claim."""
    require(variant in ('OLD', 'NEW'), 'SIDECAR_VARIANT')
    require(type(rows) is list and type(trace) is list and len(rows) == len(trace) == 482,
            'SIDECAR_COVERAGE')
    require(dict(Counter(event.get('event') for event in trace)) ==
            dict(CREATED=1, INTERVAL_BUILT=360, INTERVAL_HIT=120, CLOSED=1) and
            trace[0].get('event') == 'CREATED' and trace[-1].get('event') == 'CLOSED',
            'SIDECAR_NORMAL_EVENT_COVERAGE')
    peak = 0
    mode = 'OLD_FULL_SCAN' if variant == 'OLD' else 'NEW_INCREMENTAL'
    identity_keys = ('attempt_id', 'pair_id', 'run_id', 'condition', 'producer_pid',
                     'producer_pgid', 'producer_start_ticks', 'cache_scope_id')
    for i, (row, event) in enumerate(zip(rows, trace)):
        require(type(row) is dict and set(row) == RECORD_FIELDS, 'SIDECAR_RECORD_FIELDS')
        for key, value in (('message_kind', 'memory_measurement_record'), ('record_version', '0.1'),
                           ('contract_id', CONTRACT), ('tracking_mode', mode)):
            _same(row[key], value, 'SIDECAR_RECORD_CONSTANT')
        for key in identity_keys:
            _same(row[key], binding[key], 'SIDECAR_PRODUCER_BINDING')
        for key in ('measurement_index', 'event_index', 'current_bytes', 'peak_before_bytes',
                    'peak_after_bytes', 'previous_measured_event_frontier', 'observed_event_frontier'):
            _integer(row[key], 'SIDECAR_INTEGER')
        _same(row['measurement_index'], i, 'SIDECAR_MEASUREMENT_ORDER')
        _same(row['event_index'], i, 'SIDECAR_EVENT_ORDER')
        _same(row['event_index'], event['event_index'], 'SIDECAR_TRACE_ORDER')
        _same(row['event_kind'], event['event'], 'SIDECAR_EVENT_KIND')
        _same(row['event_digest'], event['event_digest'], 'SIDECAR_EVENT_DIGEST')
        _same(row['previous_measured_event_frontier'], i, 'SIDECAR_PREVIOUS_FRONTIER')
        _same(row['observed_event_frontier'], i + 1, 'SIDECAR_OBSERVED_FRONTIER')
        _same(row['absorbed_event_indices'], [i], 'SIDECAR_NORMAL_ABSORPTION')
        _same(row['peak_before_bytes'], peak, 'SIDECAR_PEAK_BEFORE')
        peak = max(peak, row['current_bytes'])
        _same(row['peak_after_bytes'], peak, 'SIDECAR_PEAK_RECURRENCE')
    return dict(passed=True, count=len(rows), final_peak_bytes=peak,
                same_point_recurrence_checked=True, live_graph_remeasured=False)


def compare_memory_series(left, right):
    require(type(left) is list and type(right) is list and len(left) == len(right) == 482,
            'CROSS_MEMORY_COVERAGE')
    for a, b in zip(left, right):
        for key in ('event_index', 'event_kind', 'measurement_index', 'current_bytes',
                    'peak_before_bytes', 'peak_after_bytes', 'previous_measured_event_frontier',
                    'observed_event_frontier', 'absorbed_event_indices'):
            _same(a[key], b[key], 'RECORD_CONSISTENCY_FAILED')
    return dict(passed=True, count=482, current_and_peak_series_equal=True,
                proof_scope='Saved-series equality; independent same-live-graph proof is G0 only')


def _raw_rows(job, path):
    key = str(Path(path).resolve())
    pin = job['source_pins'].get(key)
    require(type(pin) is dict and pin['path'] == key, 'SIDECAR_EXTERNAL_PIN_REQUIRED')
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == pin['sha256'] and len(raw) == pin['size_bytes'],
            'SIDECAR_EXTERNAL_PIN_MISMATCH')
    require(raw.endswith(b'\n') and all(raw.splitlines()), 'SIDECAR_JSONL_FRAMING')
    return [strict_loads(line) for line in raw.splitlines()], pin


def _sidecar(job, admission):
    descriptor = admission.table['producer_records'][0]
    producer = admission.loaded_producers[0]
    declaration = admission.declaration
    rows, pin = _raw_rows(job, descriptor['memory_sidecar_file'])
    receipt, _ = _read(job, descriptor['memory_receipt_file'])
    snapshot, _ = _read(job, descriptor['memory_snapshot_file'])
    runtime, _ = _read(job, descriptor['memory_runtime_file'])
    env = next(p for p in producer['guardian']['processes'] if p['role'] == 'env')
    payload = producer['job']['env_start']
    binding = dict(attempt_id=declaration['attempt_id'], pair_id=declaration['pair_id'],
                   run_id=declaration['run_id'], condition=declaration['condition'],
                   producer_pid=env['pid'], producer_pgid=env['pgid'],
                   producer_start_ticks=env['start_ticks'],
                   cache_scope_id=payload['cache_scope']['full_scope_id'])
    for obj in (runtime['binding'], receipt['binding'], snapshot['binding']):
        for key, value in binding.items():
            _same(obj[key], value, 'OBSERVER_BINDING_MISMATCH')
    _same(runtime['memory_accounting'], payload['memory_accounting'], 'RUNTIME_MEMORY_METADATA')
    _same(runtime['unprofiled'], True, 'FUNCTION_PROFILER_NOT_ALLOWED')
    _same(receipt['sidecar_pin'], pin, 'SIDECAR_RECEIPT_PIN')
    _same(receipt['completed'], True, 'SIDECAR_NOT_COMPLETED')
    for key in ('successful_measurement_count', 'buffered_record_count', 'durably_persisted_count'):
        _same(receipt[key], 482, 'SIDECAR_ACTUAL_COUNT')
        _same(snapshot[key], 482, 'SIDECAR_SNAPSHOT_COUNT')
    expected_oracles = 482 if declaration['condition'] == 'OLD' else 0
    for key in ('old_reference_calls', 'full_walk_oracle_calls'):
        _same(snapshot[key], expected_oracles, 'TIMED_REFERENCE_ORACLE_CONTAMINATION')
    checkpoints = snapshot['space_checkpoints']
    require(type(checkpoints) is list and len(checkpoints) == 2 and
            [cp['label'] for cp in checkpoints] == ['CP_INITIALIZED', 'CP_NORMAL_TERMINAL'],
            'SPACE_CHECKPOINT_COVERAGE')
    for cp, expected in zip(checkpoints, (1, 482)):
        _same(cp['metric_scope'], 'NAMED_CHECKPOINT_ONLY', 'SPACE_METRIC_SCOPE')
        for key in ('metadata_body_bytes', 'buffer_body_bytes', 'buffered_record_count',
                    'successful_measurement_count', 'event_frontier', 'measurement_frontier'):
            _integer(cp[key], 'SPACE_CHECKPOINT_VALUE')
        for key in ('buffered_record_count', 'successful_measurement_count',
                    'event_frontier', 'measurement_frontier'):
            _same(cp[key], expected, 'SPACE_CHECKPOINT_BINDING')
    trace, _ = _read(job, admission.table['cache_batches'][0]['cache_trace_file'])
    checked = validate_sidecar_rows(rows, trace, binding, declaration['condition'])
    for key, value in (('failed', False), ('finalized', True), ('failed_measurements', 0),
                       ('pending_event_count', 0), ('event_frontier', 482), ('measurement_frontier', 482),
                       ('current_bytes', rows[-1]['current_bytes']),
                       ('peak_bytes', checked['final_peak_bytes'])):
        _same(snapshot[key], value, 'OBSERVER_NORMAL_TERMINAL_STATE')
    if declaration['condition'] == 'NEW':
        meter = snapshot['meter']
        require(type(meter) is dict, 'NEW_METER_SNAPSHOT_REQUIRED')
        for key, value in (('initialization_walks', 1), ('measurement_count', 482),
                           ('trace_frontier', 482), ('pending_update_count', 0), ('disposed', False),
                           ('current_bytes', rows[-1]['current_bytes']),
                           ('peak_bytes', checked['final_peak_bytes'])):
            _same(meter[key], value, 'NEW_METER_TERMINAL_STATE')
    else:
        _same(snapshot['meter'], None, 'OLD_HAS_NEW_TRACKER')
    instrumentation, _ = _read(job, admission.table['cache_batches'][0]['cache_instrumentation_file'])
    _same(instrumentation['peak_cache_bytes'], checked['final_peak_bytes'], 'ORIGINAL_PEAK_BINDING')
    result = dict(checked, sidecar_pin=pin, binding=binding,
                  old_reference_calls=snapshot['old_reference_calls'],
                  full_walk_oracle_calls=snapshot['full_walk_oracle_calls'],
                  space_checkpoints=checkpoints,
                  proof_scope='saved points, not live alias remeasurement')
    cross = None
    paired = {'NEW_a': 'OLD_a', 'OLD_b': 'NEW_b'}.get(declaration['run_id'])
    if paired is not None:
        _same(job.get('paired_run_id'), paired, 'CROSS_MEMORY_PAIR_REQUIRED')
        prior, _ = _read(job, job['paired_audit_file'])
        require(prior.get('passed') is True and prior['run_id'] == paired, 'CROSS_MEMORY_PRIOR_AUDIT')
        other, other_pin = _raw_rows(job, job['paired_sidecar_file'])
        _same(prior['sidecar_audit']['sidecar_pin'], other_pin, 'CROSS_MEMORY_PRIOR_PIN')
        cross = compare_memory_series(other, rows)
        cross.update(left_run_id=paired, right_run_id=declaration['run_id'],
                     left_pin=other_pin, right_pin=pin)
    else:
        require(not any(job.get(k) for k in ('paired_run_id', 'paired_audit_file', 'paired_sidecar_file')),
                'UNDECLARED_EARLY_OR_FUTURE_MEMORY_READ')
    return result, cross


def historical_positive(job, out):
    inventory = legacy._inventory(job)
    table = legacy.historical_table(job, 'S', inventory)
    admitted = SubsetAdmissions(job, table, source_role='historical_reference', inventory=inventory)
    reports = legacy._compare_subsets(job, admitted, admitted, Path(out) / 'historical_science')
    cache = legacy._cache_checks(job, admitted, Path(out) / 'historical_cache')
    return dict(passed=True, comparisons=reports, cache=cache, real_WLS=0,
                scope='historical consumer wiring positive only; not current OLD/NEW evidence')


def validate_saved_comparison_report(report):
    """Check a saved verdict envelope; never rerun scientific comparison."""
    fields = {'message_kind', 'contract_id', 'comparator_id', 'status', 'left_artifact',
              'right_artifact', 'left_context_admission', 'right_context_admission',
              'omitted_operation_fields', 'first_difference', 'rejection'}
    require(type(report) is dict and set(report) == fields, 'SAVED_COMPARISON_REPORT_FIELDS')
    for key, value in (('message_kind', 'shared_full_comparison_report'),
                       ('contract_id', 'STAGE2A5B-GQ-SHARED-FULL-v1.0'),
                       ('comparator_id', 'gq_shared_full_typed_binary64_v1'),
                       ('status', 'EQUAL'), ('first_difference', None), ('rejection', None)):
        _same(report[key], value, 'SAVED_COMPARISON_REPORT_VERDICT')
    return dict(passed=True, new_scientific_comparisons=0)


def _saved_report_evidence(job, summary, left_pin, right_path, index, candidate_id):
    report, report_pin = _read(job, summary['report']['path'])
    _same(report_pin, summary['report'], 'SAVED_COMPARISON_REPORT_PIN')
    validate_saved_comparison_report(report)
    _same(report['left_artifact'], left_pin, 'SAVED_HISTORICAL_ARTIFACT_PIN')
    _same(report['right_artifact']['path'], right_path, 'SAVED_CURRENT_ARTIFACT_PATH')
    for side in ('left', 'right'):
        artifact_pin = report[side + '_artifact']
        artifact, observed_pin = _read(job, artifact_pin['path'])
        _same(observed_pin, artifact_pin, 'SAVED_COMPARISON_ARTIFACT_PIN')
        _same(artifact['candidate']['index'], index, 'SAVED_COMPARISON_CANDIDATE_INDEX')
        _same(artifact['candidate_identity'], candidate_id, 'SAVED_COMPARISON_CANDIDATE_ID')
        context_pin = report[side + '_context_admission']
        context, observed_context_pin = _read(job, context_pin['path'])
        _same(observed_context_pin, context_pin, 'SAVED_COMPARISON_CONTEXT_PIN')
        require(context.get('passed') is True and context.get('scope') == 'candidate_evaluation'
                and context.get('unit_only') is False, 'SAVED_COMPARISON_CONTEXT_VERDICT')
        _same(context['source_sha256'], artifact_pin['sha256'], 'SAVED_CONTEXT_SOURCE_BINDING')
        _same([row['kind'] for row in context['callbacks']], ['source', 'schema', 'source_slots'],
              'SAVED_CONTEXT_CALLBACK_COVERAGE')
        require(all(row['receipt'].get('passed') is True for row in context['callbacks']),
                'SAVED_CONTEXT_CALLBACK_VERDICT')
        _same(context['callbacks'][0]['receipt']['file_pin'], artifact_pin, 'SAVED_CONTEXT_ARTIFACT_PIN')
        _same(context['callbacks'][1]['receipt']['candidate_id'], candidate_id,
              'SAVED_CONTEXT_CANDIDATE_BINDING')
    omissions, omission_pin = _read(job, report['omitted_operation_fields']['path'])
    _same(omission_pin, report['omitted_operation_fields'], 'SAVED_OMISSION_PIN')
    require(type(omissions) is list and len(omissions) == 2 and
            [row['side'] for row in omissions] == ['left', 'right'] and
            all(type(row.get('fields')) is list and len(row['fields']) == 2074 for row in omissions),
            'SAVED_OMISSION_COVERAGE')
    detail_path = str(Path(report_pin['path']).parent / 'comparison_detail.json')
    detail, detail_pin = _read(job, detail_path)
    require(detail.get('status') == 'EQUAL' and detail.get('first_difference') is None
            and detail.get('rejection') is None, 'SAVED_COMPARISON_DETAIL_VERDICT')
    return dict(report_pin=report_pin, detail_pin=detail_pin,
                context_and_omission_pins_verified=True, new_scientific_comparisons=0)


def audit_run(job, out):
    out = Path(out)
    try:
        require(job['kind'] == 'memory_audit', 'MEMORY_AUDIT_KIND')
        inventory = legacy._inventory(job)
        declaration, _ = _read(job, job['run_declaration_file'])
        _same(declaration, job['expected_current'], 'EXTERNAL_DECLARATION_BINDING')
        _, seal = _read(job, job['execution_seal_file'])
        _same(seal['sha256'], declaration['expected_source_seal_sha256'], 'EXECUTION_SEAL_BINDING')
        historical = SubsetAdmissions(job, job['historical'], source_role='historical_reference', inventory=inventory)
        current = SubsetAdmissions(job, job['current'], source_role='current_designated_run',
                                   declaration=declaration, inventory=inventory)
        comparisons = legacy._compare_subsets(job, historical, current, out / 'science')
        cache = legacy._cache_checks(job, current, out / 'cache')
        sidecar, cross = _sidecar(job, current)
        result = dict(passed=True, run_id=declaration['run_id'], condition=declaration['condition'],
            repeat=declaration['repeat'], method='S', source_role='current_designated_run',
            candidate_indices=INDICES, candidate_count=4, science_comparisons=comparisons,
            cache_audit=cache, numerical_counts=current.numerical_counts,
            sidecar_audit=sidecar, paired_memory=cross, function_level_profiler_enabled=False,
            WLS_calls=0, candidate_evaluations=0, control_rollouts=0,
            scope='Pinned four-candidate science/cache and saved measurement audit only')
        save_json(out / 'audit_result.json', result)
        return result
    except BaseException as error:
        save_json(out / 'audit_failure.json', dict(passed=False, error_type=type(error).__name__,
            error=str(error), code=getattr(error, 'code', None), WLS_calls=0,
            scientific_rerun_performed=False))
        raise


def final_audit(job, out):
    """Summarize the accepted ten-job prefix; C09 remains launcher-only."""
    from .claims import cpu_claims, evaluate_cpu, decide
    from .common import ORDER, ordered_total
    from research.information_service_shared.artifact_admission import validate_guardian
    out = Path(out)
    claims = []
    try:
        require(job['kind'] == 'memory_final', 'MEMORY_FINAL_KIND')
        matrix, _ = _read(job, job['acceptance_matrix_file'])
        ledger, _ = _read(job, job['ledger_file'])
        rows = ledger['jobs']
        _same([row['pair_id'] for row in rows], ORDER[:-1], 'FINAL_PREFIX_ORDER')
        require(all(row['accepted'] is True for row in rows), 'FINAL_PREFIX_NOT_ACCEPTED')
        prefix_cpu = ordered_total([row['worker_cpu'] for row in rows])
        _same(prefix_cpu, ledger['worker_cpu'], 'FINAL_PREFIX_CPU_FOLD')
        require(0 <= prefix_cpu < 240, 'FINAL_PREFIX_CPU_LIMIT')
        _same(ledger['totals']['WLS_calls'], 976, 'FINAL_WLS_COVERAGE')
        _same(ledger['totals']['start_attempts'], 8784, 'FINAL_START_COVERAGE')
        gate0, _ = _read(job, job['gate_result_files']['G0'])
        gate1, _ = _read(job, job['gate_result_files']['G1'])
        require(gate0.get('passed') is True and gate1.get('passed') is True, 'FINAL_GATE_NOT_PASSED')
        gate0_claims = gate0.get('preliminary_claims', gate0.get('claims'))
        gate1_claims = gate1.get('preliminary_claims', gate1.get('claims'))
        require(type(gate0_claims) is list and type(gate1_claims) is list, 'FINAL_GATE_CLAIM_COLLECTION')
        gate_claims = gate0_claims + gate1_claims
        require(
                {row['id'] for row in gate_claims} == {f'C{i:02d}' for i in range(1, 8)} and
                len(gate_claims) == 7, 'FINAL_GATE_CLAIM_COVERAGE')
        require(all(row['status'] == 'VERIFIED' for row in gate_claims), 'FINAL_GATE_CLAIMS_INCOMPLETE')
        claims.extend(gate_claims)
        memory_inputs, _ = _read(job, job['memory_inputs_file'])
        historical_candidates = memory_inputs['registered_reference']['saved_reference']['candidates']
        require(len(historical_candidates) == 4, 'FINAL_HISTORICAL_CANDIDATE_COVERAGE')
        costs, reports, audits, identities, scopes = {}, [], {}, set(), set()
        retained_report_receipts = []
        for run in RUNS:
            audit, _ = _read(job, job['audit_result_files'][run])
            require(audit.get('passed') is True and audit['run_id'] == run and
                    audit['candidate_indices'] == INDICES and audit['candidate_count'] == 4,
                    'FINAL_AUDIT_COVERAGE')
            current_reports = audit['science_comparisons']
            require(len(current_reports) == 4 and all(row['status'] == 'EQUAL' for row in current_reports),
                    'FINAL_SCIENTIFIC_COMPARISON_COVERAGE')
            reports.extend(current_reports)
            cache = audit['cache_audit']
            _same(cache['counters'], legacy.WORKLOAD, 'FINAL_CACHE_WORKLOAD')
            _same(cache['component_instances'], 6, 'FINAL_CACHE_COMPONENTS')
            _same(cache['observed_trace_records'], 482, 'FINAL_CACHE_TRACE')
            _same(audit['numerical_counts'], dict(measurements=244, starts=2196, guardian_completed=244),
                  'FINAL_NUMERICAL_COVERAGE')
            require(audit['sidecar_audit']['count'] == 482 and
                    audit['function_level_profiler_enabled'] is False, 'FINAL_MEASUREMENT_COVERAGE')
            expected_oracles = 482 if run.startswith('OLD') else 0
            for key in ('old_reference_calls', 'full_walk_oracle_calls'):
                _same(audit['sidecar_audit'][key], expected_oracles, 'FINAL_TIMED_ORACLE_CONTAMINATION')
            guardian, _ = _read(job, job['prediction_guardian_files'][run])
            wrapped, _ = _read(job, job['prediction_job_files'][run])
            prediction = wrapped['job']
            validate_guardian(guardian, prediction)
            for index, summary, left_pin, work_item in zip(
                    INDICES, current_reports, historical_candidates, prediction['env_start']['work_items']):
                current_path = str(Path(job['prediction_guardian_files'][run]).parent / 'env' / 'work' /
                                   safe_label(work_item['work_id']) / 'result.json')
                retained_report_receipts.append(_saved_report_evidence(job, summary, left_pin, current_path,
                    index, work_item['candidate']['candidate_id']))
            cache_file = str(Path(job['audit_result_files'][run]).parent / 'cache' / 'cache_trace_audit.json')
            saved_cache, _ = _read(job, cache_file)
            _same(saved_cache, cache, 'FINAL_SAVED_CACHE_RECEIPT_BINDING')
            declaration, _ = _read(job, job['run_declaration_files'][run])
            validate_current_metadata(dict(job=prediction), declaration, job['run_declaration_files'][run])
            for key, value in (('total_cpu', 240.0), ('pair_cpu', 60.0), ('pair_wall', 120.0)):
                _same(guardian['limits'][key], value, 'FINAL_PRODUCER_LIMIT')
            env = next(row for row in guardian['processes'] if row['role'] == 'env')
            sense = next(row for row in guardian['processes'] if row['role'] == 'sense')
            ident = (env['pid'], env['start_ticks'])
            scope = prediction['env_start']['cache_scope']['full_scope_id']
            require(ident not in identities and scope not in scopes, 'FINAL_PRODUCER_REUSED')
            identities.add(ident); scopes.add(scope)
            runtime, _ = _read(job, job['memory_runtime_files'][run])
            require(runtime['unprofiled'] is True, 'FINAL_PROFILE_CONTAMINATION')
            _same(runtime['memory_accounting'], prediction['env_start']['memory_accounting'],
                  'FINAL_RUNTIME_META')
            _same(runtime['binding']['producer_pid'], env['pid'], 'FINAL_RUNTIME_PROCESS')
            _same(runtime['binding']['producer_start_ticks'], env['start_ticks'], 'FINAL_RUNTIME_PROCESS')
            saved_rows, pin = _raw_rows(job, job['memory_sidecar_files'][run])
            _same(pin, audit['sidecar_audit']['sidecar_pin'], 'FINAL_SIDECAR_PIN')
            require(len(saved_rows) == 482, 'FINAL_SIDECAR_COUNT')
            env_cpu = env['wait4_user_cpu'] + env['wait4_system_cpu']
            sense_cpu = sense['wait4_user_cpu'] + sense['wait4_system_cpu']
            worker_cpu = math.fsum((env_cpu, sense_cpu))
            _same(worker_cpu, guardian['worker_cpu'], 'FINAL_ROLE_CPU')
            costs[run] = dict(env_CPU=env_cpu, sense_CPU=sense_cpu, worker_CPU=worker_cpu)
            audits[run] = audit
        pairs = [('NEW_a', 'OLD_a', 'NEW_a'), ('OLD_b', 'NEW_b', 'OLD_b')]
        pair_results = []
        for audit_run_id, left, right in pairs:
            pair_result = audits[audit_run_id]['paired_memory']
            require(type(pair_result) is dict and pair_result.get('passed') is True and
                    pair_result['current_and_peak_series_equal'] is True and pair_result['count'] == 482,
                    'FINAL_RECORD_CONSISTENCY_FAILED')
            _same(pair_result['left_run_id'], left, 'FINAL_MEMORY_PAIR_IDENTITY')
            _same(pair_result['right_run_id'], right, 'FINAL_MEMORY_PAIR_IDENTITY')
            _same(pair_result['left_pin'], audits[left]['sidecar_audit']['sidecar_pin'],
                  'FINAL_MEMORY_PAIR_SOURCE_PIN')
            _same(pair_result['right_pin'], audits[right]['sidecar_audit']['sidecar_pin'],
                  'FINAL_MEMORY_PAIR_SOURCE_PIN')
            pair_results.append(pair_result)
        work = dict(predictions=4, candidate_comparisons=16, cache_audits=4,
                    measurements=976, starts=8784, sidecar_records=1928)
        refs = list(job['audit_result_files'].values())
        def claim(identifier, checks, **extra):
            return dict(id=identifier, status='VERIFIED', owner='saved_result_auditor',
                evidence_refs=refs, checks_completed=checks, actual_work_counters=work,
                unknown_or_missing_evidence=[], **extra)
        claims.append(claim('C08', ['FOUR_CURRENT_PRODUCERS', 'SIXTEEN_STRICT_EQUAL_REPORTS',
                                   'FOUR_INDEPENDENT_CACHE_ORACLES_AND_OWNERSHIP']))
        claims.append(claim('C10', ['TWO_SOURCE_ADMITTED_482_POINT_CURRENT_AND_PEAK_PAIRS']))
        evaluated = evaluate_cpu(costs)
        claims.append(claim('P01', ['FRESH_FOUR_RUN_ROLE_CPU', 'FROZEN_PAIRS',
                                   'UNPROFILED_SYMMETRIC_LOGGING_PATH'], cpu_inputs=costs))
        claims.extend(cpu_claims(costs, list(job['prediction_guardian_files'].values()),
                                 actual_work_counters=work))
        require(len(claims) == 13 and all(row['id'] != 'C09' for row in claims), 'FINAL_CLAIM_SCOPE')
        result = dict(passed=True, preliminary_claims=claims,
            preliminary_decision=decide(claims, matrix, executed=True, final=False),
            cpu_costs=costs, rawmetrics=evaluated, science_comparisons=reports,
            retained_report_receipts=retained_report_receipts,
            paired_memory=pair_results, prefix_scientific_CPU=prefix_cpu,
            Z_final_CPU_owner='launcher after Z reaped', WLS_calls=0,
            new_scientific_comparisons=0, scope='saved accepted prefix summary; no final C09 claim')
        save_json(out / 'final_memory_summary.json', result)
        return result
    except BaseException as error:
        save_json(out / 'final_audit_failure.json', dict(passed=False, preliminary_claims=claims,
            error_type=type(error).__name__, error=str(error), code=getattr(error, 'code', None),
            WLS_calls=0, new_scientific_comparisons=0))
        raise
