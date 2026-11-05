"""Read-only source, shape and flow admission for strict result comparison."""
from copy import deepcopy
from pathlib import Path
import math

from .common import ContractError, digest
from .comparator import (ComparisonAdmission, ContextError, ComparisonError,
                         first_difference, strict_read, validate_value)
from .source_admission import check_pin


def require(condition, message):
    if not condition:
        raise ContractError(message)


def same(left, right, message):
    difference = first_difference(left, right)
    if difference is not None:
        raise ContractError(message + ': ' + str(difference))


def pinned_read(job, path):
    """Only launcher-supplied exact pins; never bless the bytes just read."""
    path = Path(path).resolve()
    pins = job.get('source_pins')
    require(type(pins) is dict, 'Missing external exact source pin map')
    candidates = [p for name, p in pins.items() if Path(name).resolve() == path]
    require(len(candidates) == 1, 'File is not uniquely externally pinned: ' + str(path))
    pin = deepcopy(candidates[0])
    if type(pin) is str:
        raise ContractError('Source pin must include exact path/SHA/size, not a bare digest')
    require(Path(pin['path']).resolve() == path, 'External pin path/key mismatch')
    require(check_pin(pin) == path, 'External source pin changed')
    return strict_read(path), pin


def fields(value, names, path):
    if type(value) is not dict:
        raise ComparisonError('EXPECTED_OBJECT', path)
    difference = set(value) ^ set(names)
    if difference:
        key = min(difference)
        raise ComparisonError('UNEXPECTED_FIELD' if key in value else 'MISSING_FIELD', path + '/' + key)


def binary(value, path):
    if type(value) is not float or not math.isfinite(value):
        raise ComparisonError('EXPECTED_FINITE_BINARY64', path)


def integer(value, path):
    if type(value) is not int:
        raise ComparisonError('EXPECTED_INTEGER', path)


def vector(value, length, path):
    if type(value) is not list or len(value) != length:
        raise ComparisonError('WRONG_ARRAY_LENGTH', path)
    for i, item in enumerate(value):
        binary(item, path + '/' + str(i))


_CANDIDATE = ('kind', 'execution_contract_id', 'mode', 'request_identity', 'world_identity', 'candidate_identity',
              'candidate', 'start_tick', 'end_tick', 'frames', 'events', 'per_target', 'sensing_results', 'metrics',
              'final_positions', 'final_assignment', 'input_unchanged')
_FRAME = ('tick', 'time', 'lo_time', 'control_stop_time', 'positions', 'control', 'assignment', 'progress', 'G', 'Q',
          'sensing_results', 'reused_actual_endpoint', 'clock_state', 'control_integral', 'energy',
          'occupied_robot_seconds', 'status')
_PER = ('target', 'status', 'termination_reason', 'completion_time', 'completion_tick', 'escape_time', 'clock_state',
        'kept_history', 'selected_team', 'final_progress', 'components', 'absolute_O', 'baseline', 'v',
        'control_integral', 'occupied_robot_seconds', 'measurement_requests', 'reported_estimator_calls')
_COMPONENTS = ('completion', 'flow', 'late', 'effort', 'terminal')
_METRICS = ('components', 'physical_O', 'B64', 'net_O', 'change_cost', 'assignment_changes', 'control_integral', 'occupied_robot_seconds')
_QUALITY = ('contract_id', 'service_contract_id', 'payload_sha256', 'contributing_sensor_ids', 'status', 'reasons',
            'has_estimate', 'estimate', 'J', 'I', 'information_at_estimate', 'singular_values', 'radius_proxy',
            'delta', 'p_ref', 'estimator_diagnostics', 'representative_guard', 'frame_id')
_ESTIMATE = ('starts', 'has_accepted_estimate', 'estimate', 'optimizer_converged', 'numerical_ill_conditioned',
             'ambiguity_detected', 'boundary_active', 'branch_guard_triggered', 'numeric_contract_violation',
             'selected_start', 'Q', 'singular_values')
_START = ('start_id', 'start', 'accepted', 'guard', 'status', 'success', 'optimality', 'nfev', 'njev',
          'active_mask', 'cost', 'Q', 'x', 'evaluation_calls')
_SELECTION = ('passed', 'optimality_checked', 'tie_rule_checked', 'tie_rule_scope', 'checkpoint_id', 'request_identity',
              'world_identity', 'candidate_count', 'table', 'B64', 'selected_indices', 'selected_candidate_ids', 'actions',
              'assignment_change_count', 'exact_table_value', 'table_value_float', 'legal_plan_count', 'tied_optima',
              'independent_plans', 'action_metadata', 'scope')


def validate_estimate_diagnostics(estimate, path):
    """Frozen estimator return branches; diagnostic strings remain exact data."""
    if estimate is None:return
    if type(estimate) is not dict or type(estimate.get('has_accepted_estimate')) is not bool:
        raise ComparisonError('ESTIMATE_BRANCH_REQUIRED',path)
    selected=estimate['has_accepted_estimate']
    names=_ESTIMATE if selected else tuple(k for k in _ESTIMATE if k not in ('selected_start','Q','singular_values'))
    fields(estimate,names,path)
    starts=estimate['starts']
    if type(starts) is not list or len(starts)!=9:
        raise ComparisonError('ALL_NINE_STARTS_REQUIRED',path+'/starts')
    for n,start in enumerate(starts):
        at=path+'/starts/'+str(n)
        guarded=type(start) is dict and start.get('guard') is not None
        fields(start,_START+('phase','reason') if guarded else _START,at)
        integer(start['start_id'],at+'/start_id')
        same(start['start_id'],n,'Optimizer start identity/order changed')
        for key in ('accepted','success'):
            if type(start[key]) is not bool:raise ComparisonError('EXPECTED_BOOL',at+'/'+key)
        fields(start['evaluation_calls'],('fun','jac'),at+'/evaluation_calls')
        for key,value in start['evaluation_calls'].items():
            integer(value,at+'/evaluation_calls/'+key)
            if value<0:raise ComparisonError('NEGATIVE_CALL_COUNT',at+'/evaluation_calls/'+key)
        if guarded:
            fields(start['guard'],('reason','sensor_id','x'),at+'/guard')
            phase=start['phase'];reason=start['guard']['reason']
            if phase not in ('fun','jac','recompute') or start['reason']!='undefined_or_branch_guard' or start['accepted']:
                raise ComparisonError('INVALID_GUARD_BRANCH',at)
            if reason not in ('sensor_distance','residual_branch','recompute_sensor_distance','recompute_branch'):
                raise ComparisonError('INVALID_GUARD_REASON',at+'/guard/reason')
            if reason.startswith('recompute_'):
                if phase!='recompute' or start['guard']['x'] is not None or start['guard']['sensor_id'] is not None:
                    raise ComparisonError('INVALID_RECOMPUTE_GUARD',at+'/guard')
            else:
                vector(start['guard']['x'],2,at+'/guard/x')
                if type(start['guard']['sensor_id']) is not str:
                    raise ComparisonError('INVALID_GUARD_SENSOR',at+'/guard/sensor_id')
            if phase in ('fun','jac'):
                if start['success'] or any(start[k] is not None for k in ('status','optimality','nfev','njev','active_mask','cost','Q','x')):
                    raise ComparisonError('PRE_SOLVER_GUARD_HAS_RESULT',at)
                if start['evaluation_calls'][phase]<1:
                    raise ComparisonError('GUARD_WITHOUT_EVALUATION',at+'/evaluation_calls')
            else:
                integer(start['status'],at+'/status')
                vector(start['x'],2,at+'/x')
                binary(start['cost'],at+'/cost')
    if selected!=any(row['accepted'] for row in starts):
        raise ComparisonError('ESTIMATE_ACCEPTANCE_MISMATCH',path)


def _assignment(value, robots, path):
    if type(value) is not list or len(value) != robots:
        raise ComparisonError('FULL_X_ASSIGNMENT_REQUIRED', path)
    for i, row in enumerate(value):
        fields(row, ('target', 'role'), path + '/' + str(i))
        if row['target'] is not None:
            integer(row['target'], path + '/' + str(i) + '/target')
        if type(row['role']) is not str:
            raise ComparisonError('ROLE_STRING_REQUIRED', path)


def _full_vectors(value, robots, path):
    if type(value) is not list or len(value) != robots:
        raise ComparisonError('FULL_X_VECTOR_REQUIRED', path)
    for i, row in enumerate(value):
        vector(row, 2, path + '/' + str(i))


def validate_candidate_shape(value, request, candidate):
    from research.information_service_online import public
    validate_value(value)
    fields(value, _CANDIDATE, '')
    same(value['kind'], 'candidate_evaluation', 'Wrong artifact kind')
    same(value['execution_contract_id'], 'STAGE2A5B-GQ-ONLINE-v1.0', 'Scientific contract changed')
    same(value['mode'], 'GQ', 'Wrong scientific mode')
    cp = request['checkpoint']; key = candidate['key']; x = cp['config']['robots']; j = str(key['target'])
    world = public.world_identity(request)
    expected_spec = dict(target=key['target'], robots=key['robots'], roles=key['roles'], index=candidate['index'],
                         mask=candidate['resource_mask'], structural_key=key, candidate_identity=candidate['candidate_id'],
                         request_identity=request['evaluation_request_id'], world_identity=world)
    same(value['candidate'], expected_spec, 'Full candidate descriptor mismatch')
    for field, expected in (('request_identity', request['evaluation_request_id']), ('world_identity', world),
                            ('candidate_identity', candidate['candidate_id']), ('start_tick', cp['tick']),
                            ('end_tick', request['prediction_end_tick']), ('input_unchanged', True)):
        same(value[field], expected, 'Candidate field mismatch ' + field)
    if type(value['frames']) is not list or len(value['frames']) != value['end_tick'] - value['start_tick'] + 1:
        raise ComparisonError('INCOMPLETE_FRAME_ARRAY', '/frames')
    for i, frame in enumerate(value['frames']):
        at = '/frames/' + str(i)
        fields(frame, _FRAME, at)
        same(frame['tick'], value['start_tick'] + i, 'Noncanonical frame tick')
        for name in ('time', 'lo_time', 'control_stop_time', 'control_integral', 'energy', 'occupied_robot_seconds'):
            binary(frame[name], at + '/' + name)
        _full_vectors(frame['positions'], x, at + '/positions'); _full_vectors(frame['control'], x, at + '/control')
        _assignment(frame['assignment'], x, at + '/assignment')
        for name in ('progress', 'G', 'Q', 'clock_state', 'status'):
            if type(frame[name]) is not dict:
                raise ComparisonError('EXPECTED_OBJECT', at + '/' + name)
        if type(frame['sensing_results']) is not list:
            raise ComparisonError('EXPECTED_ARRAY', at + '/sensing_results')
        for target, progress in frame['progress'].items():
            binary(progress, at + '/progress/' + target)
        for target, geometric in frame['G'].items():
            if type(geometric) is not bool:
                raise ComparisonError('EXPECTED_BOOL', at + '/G/' + target)
        if any(q not in ('PASS', 'FAIL', 'UNKNOWN') for q in frame['Q'].values()):
            raise ComparisonError('INVALID_QUALITY_STATUS', at + '/Q')
    fields(value['per_target'], (j,), '/per_target')
    per = value['per_target'][j]; fields(per, _PER, '/per_target/' + j)
    fields(per['components'], _COMPONENTS, '/per_target/' + j + '/components')
    for name in _COMPONENTS:
        binary(per['components'][name], '/per_target/' + j + '/components/' + name)
    for name in ('final_progress', 'absolute_O', 'baseline', 'v', 'control_integral', 'occupied_robot_seconds'):
        binary(per[name], '/per_target/' + j + '/' + name)
    for name in ('measurement_requests', 'reported_estimator_calls'):
        integer(per[name], '/per_target/' + j + '/' + name)
    fields(value['metrics'], _METRICS, '/metrics')
    fields(value['metrics']['components'], _COMPONENTS, '/metrics/components')
    for name in _METRICS:
        if name not in ('components', 'assignment_changes'):
            binary(value['metrics'][name], '/metrics/' + name)
    integer(value['metrics']['assignment_changes'], '/metrics/assignment_changes')
    _full_vectors(value['final_positions'], x, '/final_positions'); _assignment(value['final_assignment'], x, '/final_assignment')
    for i, row in enumerate(value['sensing_results']):
        at = '/sensing_results/' + str(i)
        fields(row, ('frame', 'allowed_sensor_ids', 'start_tick', 'result', 'source_slots'), at)
        for slot in row['source_slots']:
            public.validate_schema(slot, 'PredictedSourceSlot')
        result = row['result']; quality = result['quality']
        fields(quality, _QUALITY, at + '/result/quality')
        estimate = result['estimate_result']
        validate_estimate_diagnostics(estimate,at+'/result/estimate_result')
    return dict(passed=True, shape='frozen_r2_candidate_full_X', candidate_id=candidate['candidate_id'])


def validate_guardian(guardian, producer_job):
    require(guardian.get('passed') is True and guardian.get('failure') is None, 'Producer guardian failed')
    require(guardian.get('accounting_complete') is True and guardian.get('all_reaped') is True,
            'Producer accounting/reaping incomplete')
    require(not guardian.get('accounting_errors') and not guardian.get('finalization_errors') and not guardian.get('orphan_records'),
            'Producer accounting errors')
    same(guardian['attempt_id'], producer_job['attempt_id'], 'Producer attempt mismatch')
    same(guardian['pair_id'], producer_job['pair_id'], 'Producer pair mismatch')
    ledger = guardian['ledger']
    require(type(ledger) is list and {x['role'] for x in ledger} == {'env', 'sense', 'controller'} and len(ledger) == 3,
            'Expected exactly three guardian-owned worker records')
    identities = []
    for row in ledger:
        require(row.get('created') is True and row.get('reaped') is True and row.get('state') == 'FINAL_ACCOUNTED',
                'Producer child missing unique final wait4')
        require(row.get('returncode') == 0 and row.get('live_after_reap') is False, 'Producer child abnormal/live after return')
        identities.append((row['pid'], row['start_ticks'], row['pgid']))
        for name in ('wait4_user_cpu', 'wait4_system_cpu'):
            require(type(row[name]) in (float, int) and row[name] >= 0 and math.isfinite(row[name]), 'Missing final rusage')
    require(len(set(identities)) == 3, 'Duplicate process identity')
    return dict(passed=True, pair_id=guardian['pair_id'], accounted_processes=3,
                completed_sense_requests=guardian['completed_sense_requests'])


class ArtifactAdmissions:
    """One side of a complete table, bound to pinned producers and public input."""
    def __init__(self, job, table):
        from research.information_service_online import public
        self.job = job
        self.table = table
        self.request, self.request_pin = pinned_read(job, job['request_file'])
        binding, binding_pin = pinned_read(job, job['binding_file'])
        require(binding_pin['sha256'] == job['binding_sha256'], 'External public binding hash mismatch')
        self.authority = public.HistoryAuthority.from_public_binding(binding)
        public.validate_request(self.request, self.authority)
        self.manifest = public.build_manifest(self.request, self.authority)
        self.candidates = {c['candidate_id']: c for c in self.manifest['candidates']}
        self.values = {}; self.pins = {}; self.producers = {}
        for filename in table['candidate_result_files']:
            value, pin = pinned_read(job, filename)
            cid = value.get('candidate_identity')
            require(cid in self.candidates and cid not in self.values, 'Missing, duplicate or foreign candidate')
            self.values[cid] = value; self.pins[str(Path(filename).resolve())] = pin
        require(set(self.values) == set(self.candidates), 'Complete candidate table required including the empty table')
        for producer in table['producer_records']:
            self._producer(producer)
        require(set(self.producers) == set(self.pins), 'Each candidate file must have one exact successful producer')
        self.selection, self.selection_pin = pinned_read(job, table['selection_file'])
        self.selection_producer = self._load_producer(table['selection_producer'])
        require(self.selection_producer['job']['env_start']['kind'] == 'select', 'Selection did not come from selector')
        expected_selection_path = self.selection_producer['env']['scientific_file']
        same(str(Path(table['selection_file']).resolve()), str(Path(expected_selection_path).resolve()), 'Foreign selection scientific file')
        require(Path(expected_selection_path).resolve().parent == Path(table['selection_producer']['env_result_file']).resolve().parent,
                'Selection scientific file escaped registered producer output')
        self.selection_registrations = {r['stream_id']: r for r in table['selection_registrations']}
        require(len(self.selection_registrations) == len(table['selection_registrations']), 'Duplicate selection flow registrations')
        selected_job = self.selection_producer['job']['env_start']
        selected_request, _ = pinned_read(job, selected_job['request_file'])
        selected_binding, selected_binding_pin = pinned_read(job, selected_job['binding_file'])
        same(selected_request, self.request, 'Selector used another scientific request')
        same(selected_binding_pin['sha256'], selected_job['binding_sha256'], 'Selector external binding differs')
        same(selected_binding, binding, 'Selector used another public source binding')
        expected_plan = public.plan_action_metadata(self.request['checkpoint'], self.selection['actions'],
            selected_job['actual_work_identity'], physical_environment_id=selected_job['physical_environment_id'])
        same(self.selection['action_metadata'], expected_plan, 'Selection metadata differs from admitted current action')
        same(list(self.selection_registrations.values()), [r['registration'] for r in expected_plan['flows']],
             'Selector external flow list differs from its registered plan')

    def _load_producer(self, producer):
        wrapped, _ = pinned_read(self.job, producer['job_file'])
        job = wrapped['job']
        same(job['pair_id'], producer['pair_id'], 'Producer descriptor/pair mismatch')
        guardian, _ = pinned_read(self.job, producer['guardian_result_file'])
        proof = validate_guardian(guardian, job)
        registry, _ = pinned_read(self.job, producer['response_registry_file'])
        env, _ = pinned_read(self.job, producer['env_result_file'])
        require(env.get('passed') is True and registry.get('failed') is False, 'Producer env/response registry failed')
        same(sorted(registry['requests']), sorted(registry['committed']), 'Uncommitted response registry request')
        same(len(registry['requests']), guardian['completed_sense_requests'], 'Guardian/registry response count differs')
        registrations = job['sense_start']['streams']
        expected = {r['stream_id']: r for r in registrations}
        require(len(expected) == len(registrations), 'Producer registered duplicate stream')
        same(registry['streams'], expected, 'Producer response registry stream set differs from dispatched job')
        return dict(job=job, guardian=guardian, registry=registry, env=env, proof=proof)

    def _producer(self, descriptor):
        from research.information_service_online import public
        producer = self._load_producer(descriptor)
        payload = producer['job']['env_start']
        require(payload['kind'] in ('predict', 'predict_shared'), 'Nonprediction producer for candidate')
        same(payload['binding_sha256'], self.job['binding_sha256'], 'Prediction binding differs')
        # In D vs B, public binding paths differ but canonical public request is
        # identical. Their external pins are independently checked by the loader.
        original_request, _ = pinned_read(self.job, payload['request_file'])
        original_binding, original_binding_pin = pinned_read(self.job, payload['binding_file'])
        same(original_binding_pin['sha256'], payload['binding_sha256'], 'Prediction original binding pin differs')
        same(original_binding['public_checkpoint'], self.request['checkpoint'], 'Prediction original binding addresses another checkpoint')
        same(original_request, self.request, 'Prediction source left the admitted public state')
        declared = {w['candidate']['candidate_id']: w for w in payload['work_items']}
        require(len(declared) == len(payload['work_items']), 'Duplicate dispatched candidate')
        found_requests = set()
        for item in producer['env']['items']:
            path = str(Path(item['result_file']).resolve())
            require(path in self.pins and path not in self.producers, 'Unregistered or duplicate result producer')
            require(Path(path).parents[2] == Path(descriptor['env_result_file']).resolve().parent,
                    'Candidate result escaped its registered producer work directory')
            value = self.values[item['candidate_id']]
            candidate = self.candidates[item['candidate_id']]
            work = declared.pop(candidate['candidate_id'], None)
            require(work is not None, 'Producer returned an undeclared candidate')
            same(work['candidate'], candidate, 'Dispatched scientific candidate descriptor changed')
            same(item['work_id'], work['work_id'], 'Producer work identity changed')
            expected = public.prediction_metadata(self.request, candidate, work['work_id'], self.authority,
                physical_environment_id=payload['physical_environment_id'], purpose='CANDIDATE_PREDICTION')['registration']
            same(producer['registry']['streams'][expected['stream_id']], expected, 'Stream not registered from current public history')
            for row in value['sensing_results']:
                tick = row['frame']['tick']; stream = row['frame']['stream_id']
                matches = [(rid, rec) for rid, rec in producer['registry']['requests'].items()
                           if rec['identity']['stream_id'] == stream and rec['identity']['global_tick'] == tick]
                require(len(matches) == 1, 'Fusion lacks unique externally committed transport request')
                rid, request = matches[0]; identity = request['identity']
                require(rid not in found_requests, 'Transport request committed to multiple endpoint rows')
                found_requests.add(rid)
                same(request['context'], expected['context'], 'Transport context changed')
                same(identity['attempt_id'], producer['job']['attempt_id'], 'Transport attempt changed')
                same(identity['pair_id'], producer['job']['pair_id'], 'Transport pair changed')
                same(identity['target_id'], candidate['key']['target'], 'Transport target changed')
                same(identity['sense_request_id'], rid, 'Transport request ID/key changed')
                same(identity['payload_sha256'], digest({k: row[k] for k in ('frame', 'allowed_sensor_ids', 'start_tick')}),
                     'Transport measurement-wrapper digest mismatch')
                commit = producer['registry']['committed'][rid]
                same(commit['identity'], identity, 'Committed response identity changed')
                result_sha = digest(row['result'])
                same(commit['result_sha256'], result_sha, 'Response result differs from committed payload')
                same(commit['commit_id'], digest(dict(identity=identity, context=request['context'], result_sha256=result_sha)),
                     'Response commitment digest changed')
            self.producers[path] = dict(producer=producer, registration=expected, candidate=candidate)
        require(not declared, 'Dispatched candidate did not complete')
        same(sorted(found_requests), sorted(producer['registry']['requests']), 'Extra committed fusion not present in candidate artifacts')

    def candidate_admission(self, path):
        key = str(Path(path).resolve()); record = self.producers[key]; candidate = record['candidate']
        def source(value, evidence):
            same(value, self.values[candidate['candidate_id']], 'Candidate bytes changed after source admission')
            return dict(passed=True, producer=record['producer']['proof'], file_pin=self.pins[key])
        def schema(value, evidence):
            return validate_candidate_shape(value, self.request, candidate)
        def slots(value, evidence):
            from research.information_service_online.acceptance import audit_prediction
            result = audit_prediction(self.request, value, candidate)
            return dict(passed=True, source_slot_and_independent_fusion_audit=result)
        reg = record['registration']
        return ComparisonAdmission(source_sha256=self.pins[key]['sha256'], registrations={reg['stream_id']: reg},
            expected_scientific_identity=dict(checkpoint_id=self.request['checkpoint']['checkpoint_id'],
                evaluation_request_id=self.request['evaluation_request_id'], world_id=candidate['world_id'], candidate_id=candidate['candidate_id']),
            source_validator=source, schema_validator=schema, source_slots_validator=slots)

    def selection_admission(self):
        def source(value, evidence):
            same(value, self.selection, 'Selection bytes changed after source admission')
            return dict(passed=True, producer=self.selection_producer['proof'], file_pin=self.selection_pin)
        def schema(value, evidence):
            fields(value, _SELECTION, '')
            for name in ('passed', 'optimality_checked', 'tie_rule_checked'):
                same(value[name], True, 'Selector did not pass own exact gate')
            same(value['candidate_count'], len(self.candidates), 'Selection table coverage changed')
            same(value['request_identity'], self.request['evaluation_request_id'], 'Selection request changed')
            return dict(passed=True, shape='pure_frozen_r2_selection_without_file_wrapper')
        def slots(value, evidence):
            return dict(passed=True, source_slots_not_applicable=True,
                        current_public_action_plan_already_checked=True)
        return ComparisonAdmission(source_sha256=self.selection_pin['sha256'], registrations=self.selection_registrations,
            expected_scientific_identity=dict(checkpoint_id=self.request['checkpoint']['checkpoint_id'],
                evaluation_request_id=self.request['evaluation_request_id'], world_id=self.selection['world_identity'], candidate_id=None),
            source_validator=source, schema_validator=schema, source_slots_validator=slots)
