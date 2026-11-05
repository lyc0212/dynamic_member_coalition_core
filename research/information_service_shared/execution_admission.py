"""Actual-step source admission and frozen whole-step strict comparison.

This module reads registered evidence only. It does not construct an execution
environment, acquire measurements, call WLS, or advance a control interval.
"""
from copy import deepcopy
from pathlib import Path

from .common import digest
from .artifact_admission import (pinned_read, require, same, fields, binary,
                                 _full_vectors, _assignment, validate_guardian)
from .comparator import ComparisonAdmission, compare_files, validate_value


SIDE_FIELDS = (
    'step_result_file', 'producer_job_file', 'guardian_result_file',
    'response_registry_file', 'env_result_file', 'action_file',
    'previous_public_checkpoint_file', 'previous_public_binding_file',
    'previous_private_snapshot_file', 'current_private_snapshot_file',
    'current_public_checkpoint_file', 'current_public_binding_file', 'private_input_file')
STEP_FIELDS = ('status', 'replayed', 'action_commit', 'action_commit_id', 'start_tick', 'end_tick',
               'checkpoint_after', 'public_binding', 'frames', 'events', 'fusion_records',
               'metrics', 'ended_ids', 'new_ids')
FRAME_FIELDS = ('tick', 'time', 'phase', 'positions_start', 'positions', 'control',
                'control_elapsed_by_robot', 'assignment', 'statuses', 'progress',
                'active_segment_ids', 'actual_endpoints', 'events', 'metrics')
METRIC_FIELDS = ('reward_components', 'return_without_changes', 'return_with_changes',
                 'change_cost', 'assignment_changes', 'control_integral', 'effort_by_robot',
                 'occupied_robot_seconds', 'idle_robot_seconds', 'flow', 'late', 'peak_speed',
                 'completed_count', 'escaped_count', 'actual_sampling_attempts',
                 'actual_cache_requests', 'actual_cache_reuses', 'actual_fusions',
                 'reported_estimator_calls')


def _resolved(path):
    return str(Path(path).resolve())


def _same_path(left, right, reason):
    same(_resolved(left), _resolved(right), reason)


def _pin_matches(actual, registered, reason):
    _same_path(actual['path'], registered['path'], reason + ' path')
    same(actual['sha256'], registered['sha256'], reason + ' SHA')
    size = registered.get('size_bytes', registered.get('size'))
    if size is not None:
        same(actual['size_bytes'], size, reason + ' size')


def _validate_metrics(value, robots, at):
    fields(value, METRIC_FIELDS, at)
    fields(value['reward_components'], ('completion', 'flow', 'late', 'effort', 'terminal'), at + '/reward_components')
    for name, number in value['reward_components'].items():
        binary(number, at + '/reward_components/' + name)
    integer_names = {'assignment_changes', 'completed_count', 'escaped_count', 'actual_sampling_attempts',
                     'actual_cache_requests', 'actual_cache_reuses', 'actual_fusions', 'reported_estimator_calls'}
    for name in METRIC_FIELDS:
        if name in integer_names:
            require(type(value[name]) is int and value[name] >= 0, 'Actual metric requires nonnegative integer: ' + name)
        elif name == 'effort_by_robot':
            require(type(value[name]) is list and len(value[name]) == robots, 'Actual effort ledger lost full X')
            for i, number in enumerate(value[name]):
                binary(number, at + f'/effort_by_robot/{i}')
        elif name != 'reward_components':
            binary(value[name], at + '/' + name)


class ExecutionAdmission:
    """One real old/new producer, linked to its complete saved actual step."""
    def __init__(self, job, descriptor, *, historical=None):
        from research.information_service_online import public

        fields(descriptor, SIDE_FIELDS, '/execution_side')
        self.job = job
        self.descriptor = deepcopy(descriptor)
        self.data, self.pins = {}, {}
        for name in SIDE_FIELDS:
            self.data[name], self.pins[name] = pinned_read(job, descriptor[name])
        self.step = self.data['step_result_file']
        self.previous = self.data['previous_public_checkpoint_file']
        self.current = self.data['current_public_checkpoint_file']
        self.before = self.data['previous_private_snapshot_file']
        self.after = self.data['current_private_snapshot_file']
        self.wrapped = self.data['producer_job_file']
        self.producer_job = self.wrapped['job']
        self.payload = self.producer_job['env_start']
        self.env = self.data['env_result_file']
        self.registry = self.data['response_registry_file']
        self.physical_id = self.payload['physical_environment_id']
        require(self.payload['kind'] == 'execute', 'Actual step must come from execute producer, never initialize/predict')
        self.process_proof = validate_guardian(self.data['guardian_result_file'], self.producer_job)
        require(self.env.get('passed') is True and self.registry.get('failed') is False, 'Actual producer or response registry failed')
        _same_path(self.env['step_result_file'], descriptor['step_result_file'], 'Step not published by this producer')
        require(Path(descriptor['step_result_file']).resolve().parent == Path(descriptor['env_result_file']).resolve().parent,
                'Actual step escaped its producer output directory')
        for name, payload_name in (('action_file', 'action_file'), ('private_input_file', 'private_input_file'),
                                    ('previous_private_snapshot_file', 'private_snapshot_file')):
            _same_path(descriptor[name], self.payload[payload_name], 'Dispatched actual input changed')
        same(self.payload['private_snapshot_sha256'], self.pins['previous_private_snapshot_file']['sha256'],
             'Actual restore did not bind its exact previous snapshot')
        for artifact, name in (('private_snapshot', 'current_private_snapshot_file'),
                               ('public_checkpoint', 'current_public_checkpoint_file'),
                               ('public_binding', 'current_public_binding_file')):
            _same_path(self.env['artifacts'][artifact], descriptor[name], 'Current artifact not from actual producer')
        for state, checkpoint, label in ((self.before, self.previous, 'before'), (self.after, self.current, 'after')):
            same(state['physical_environment_id'], self.physical_id, 'Actual private source belongs to another environment')
            same(state['source_identity'], digest(self.data['private_input_file']), 'Actual private initial/future source changed')
            same(state['snapshot_digest'], digest({k: v for k, v in state.items() if k != 'snapshot_digest'}),
                 'Actual ' + label + ' snapshot checksum differs')
            same(state['checkpoint'], checkpoint, 'Private actual state and published checkpoint differ')
            require(state['failed'] is False and state['inflight'] is None, 'Actual source is failed or in flight')
        self.previous_authority = public.HistoryAuthority.from_public_binding(self.data['previous_public_binding_file'])
        self.current_authority = public.HistoryAuthority.from_public_binding(self.data['current_public_binding_file'])
        public.validate_checkpoint(self.previous, self.previous_authority)
        public.validate_checkpoint(self.current, self.current_authority)
        same(self.data['previous_public_binding_file']['public_checkpoint'], self.previous, 'Previous binding/checkpoint mismatch')
        same(self.data['current_public_binding_file']['public_checkpoint'], self.current, 'Current binding/checkpoint mismatch')
        same(self.current['previous_checkpoint_id'], self.previous['checkpoint_id'], 'Actual checkpoint predecessor changed')
        same(self.current['tick'], self.previous['tick'] + 20, 'Actual step must span exactly the declared second')
        envelope = self.data['action_file']
        public.validate_action_request(envelope, self.previous)
        same(envelope['operation']['physical_environment_id'], self.physical_id, 'Action belongs to another environment')
        request_id = envelope['operation']['request_id']
        require(request_id not in self.before['successful_requests'], 'This declared actual interval was already committed before execution')
        require(request_id in self.after['successful_requests'], 'Actual successful-request journal omits this interval')
        cached = self.after['successful_requests'][request_id]
        same(cached['fingerprint'], digest(dict(physical_environment_id=self.physical_id,
            checkpoint_id=self.previous['checkpoint_id'], expected_start_tick=self.previous['tick'],
            assignment=envelope['payload']['assignment'])), 'Actual request fingerprint differs')
        same(cached['result'], self.step, 'Whole step differs from saved immutable successful-request result')
        for key, old in self.before['successful_requests'].items():
            require(key in self.after['successful_requests'], 'An earlier successful request was discarded')
            same(self.after['successful_requests'][key], old, 'An earlier successful replay result was changed')
        same(sorted(self.after['successful_requests']), sorted([*self.before['successful_requests'], request_id]),
             'Unexpected successful action committed within one declared interval')
        for name, step_name in (('frames', 'frames'), ('fusions', 'fusion_records')):
            old, new = self.before[name], self.after[name]
            same(new[:len(old)], old, 'Previously committed ' + name + ' history was rewritten')
            same(new[len(old):], self.step[step_name], 'Step omitted or added actual ' + name + ' history')
        before_events = self.before['state']['events']
        after_events = self.after['state']['events']
        same(after_events[:len(before_events)], before_events, 'Previously committed event history was rewritten')
        same(after_events[len(before_events):], self.step['events'], 'Step event list differs from complete actual interval')
        commits = self.before['action_commits']
        same(self.after['action_commits'][:len(commits)], commits, 'Previous action commits changed')
        same(self.after['action_commits'][len(commits):], [self.step['action_commit']], 'Actual interval does not have one unique action commit')
        plan = public.plan_action_metadata(self.previous, envelope['payload']['assignment'], self.payload['work_identity'],
                                           physical_environment_id=self.physical_id)
        expected_regs = [row['registration'] for row in plan['flows']]
        same(self.payload['streams'], expected_regs, 'Dispatched actual flow does not follow current actual segment/KEEP history')
        same(self.producer_job['sense_start']['streams'], expected_regs, 'Sense START registered another actual flow')
        self.registrations = {r['stream_id']: r for r in expected_regs}
        require(len(self.registrations) == len(expected_regs), 'Duplicate actual stream registration')
        same(self.registry['streams'], self.registrations, 'Actual response registry differs from registered flows')
        self.flow_by_stream = {row['registration']['stream_id']: row for row in plan['flows']}
        self._transport_and_actual_slots()
        if historical is not None:
            self._historical_origin(historical)

    def _historical_origin(self, comparison):
        registry, registry_pin = pinned_read(self.job, comparison['old_registry_file'])
        same(registry_pin['sha256'], comparison['old_registry_sha'], 'Historical registry differs from frozen external identity')
        index, index_pin = pinned_read(self.job, comparison['old_episode_index_file'])
        same(index_pin['sha256'], comparison['old_episode_index_sha'], 'Historical episode index differs from frozen external identity')
        episode = index['episode_id']
        same(episode, self.job['episode_id'], 'Historical comparison uses another episode')
        decisions = [d for d in index['decisions'] if d['tick'] == self.previous['tick']]
        require(len(decisions) == 1, 'Historical actual step not uniquely in frozen episode index')
        decision = decisions[0]
        for field, index_name in (('step_result_file', 'step_result_file'), ('env_result_file', 'execution_result_file'),
                                  ('action_file', 'action_file')):
            _same_path(self.descriptor[field], decision[index_name], 'Historical step/action/producer is not the indexed one')
        _same_path(self.descriptor['private_input_file'], index['private_input_file'], 'Historical private initial source is not indexed')
        for prefix, artifacts in (('previous', decision['artifacts']), ('current', decision['artifacts_after'])):
            checkpoint = self.previous if prefix == 'previous' else self.current
            rows = [r for r in registry if r['episode_id'] == episode and r['tick'] == checkpoint['tick']]
            require(len(rows) == 1, 'Historical before/after checkpoint not uniquely registered')
            registration = rows[0]
            same(registration['checkpoint_id'], checkpoint['checkpoint_id'], 'Historical registered checkpoint identity differs')
            same(registration['physical_environment_id'], self.physical_id, 'Historical actual environment differs from frozen registry')
            for kind, suffix in (('private_snapshot', 'private_snapshot_file'), ('public_checkpoint', 'public_checkpoint_file'),
                                  ('public_binding', 'public_binding_file')):
                name = prefix + '_' + suffix
                _same_path(self.descriptor[name], artifacts[kind], 'Historical indexed artifact differs')
                _pin_matches(self.pins[name], registration['artifacts'][kind], 'Historical actual-source artifact')
            if prefix == 'current':
                _same_path(registration['registered_execution_result'], self.descriptor['env_result_file'],
                           'Historical after-cut belongs to another actual producer')
        same(self.producer_job['pair_id'], f"{episode}_k{self.previous['tick']:03d}_ACTUAL", 'Historical dispatched producer pair changed')
        # Producer, guardian and response evidence are additional runtime-sealed
        # inputs. Their pins must equal the presealed old comparison catalog.
        if 'old_source_pins' in comparison:
            frozen = comparison['old_source_pins']
            for name, actual in self.pins.items():
                matches = [pin for key, pin in frozen.items() if _resolved(key) == _resolved(actual['path'])]
                require(len(matches) == 1, 'Historical comparison catalog did not freeze required input: ' + name)
                _pin_matches(actual, matches[0], 'Historical comparison catalog input')

    def _transport_and_actual_slots(self):
        from research.information_service_online import public

        registry = self.registry
        fields(registry, ('failed', 'streams', 'requests', 'committed'), '/actual_registry')
        same(sorted(registry['requests']), sorted(registry['committed']), 'Actual registry has uncommitted response')
        same(len(registry['requests']), self.process_proof['completed_sense_requests'], 'Actual guardian/registry fusion count differs')
        cache = {}
        for entry in self.after['sampler']['entries']:
            raw_key = entry['raw_key']
            require(type(raw_key) is list and len(raw_key) == 4, 'Malformed actual raw-measurement cache key')
            same(raw_key[0], self.physical_id, 'Actual raw cache crosses environment')
            key = tuple(raw_key[1:])
            require(key not in cache, 'Duplicate actual cached raw outcome')
            slot = entry['slot']
            public.validate_schema(slot, 'MeasurementSlot')
            same(slot['slot_key'], dict(target_id=key[0], robot_id=key[1], tick=key[2]), 'Cached raw slot identity differs')
            require(slot['state'] in ('VALID', 'MISSING'), 'Raw cache contains unqueried or invalid pseudo-measurement')
            same(slot['slot_digest'], digest({k: v for k, v in slot.items() if k != 'slot_digest'}), 'Cached actual slot digest differs')
            cache[key] = entry
        for old in self.before['sampler']['entries']:
            key = tuple(old['raw_key'][1:])
            require(key in cache, 'Previously acquired actual raw outcome disappeared')
            same(cache[key], old, 'Previously acquired VALID/MISSING outcome was altered or resampled')
        self.actual_cache = cache
        matched = set()
        actual_frames = {frame['tick']: frame for frame in self.step['frames']}
        require(len(actual_frames) == len(self.step['frames']), 'Actual step contains duplicate physical frame ticks')
        for i, row in enumerate(self.step['fusion_records']):
            at = f'/fusion_records/{i}'
            fields(row, ('frame', 'allowed_sensor_ids', 'start_tick', 'context', 'result', 'actual_endpoint'), at)
            frame = row['frame']; stream = frame['stream_id']; tick = frame['tick']; target = frame['target_id']
            require(stream in self.registrations, 'Unregistered actual execution stream')
            reg = self.registrations[stream]; flow = self.flow_by_stream[stream]
            same(row['context'], reg['context'], 'Actual row context differs from registered segment')
            same(reg['context']['purpose'], 'ACTUAL_EXECUTION', 'Predicted response cannot become actual')
            same(reg['context']['request_identity'], self.previous['checkpoint_id'], 'Actual context addresses another checkpoint')
            same(reg['context']['world_identity'], None, 'Actual context has a prediction world')
            same(reg['context']['action_identity'], reg['context']['segment_id'], 'Actual action/segment identity differs')
            matches = [(rid, r) for rid, r in registry['requests'].items()
                       if r['identity']['stream_id'] == stream and r['identity']['global_tick'] == tick]
            require(len(matches) == 1, 'Actual fusion lacks one unique transport request')
            rid, request = matches[0]; identity = request['identity']
            require(rid not in matched, 'Actual transport response used for multiple fusions')
            matched.add(rid)
            same(request['context'], reg['context'], 'Actual transport purpose/segment differs')
            same(identity['attempt_id'], self.producer_job['attempt_id'], 'Actual transport attempt differs')
            same(identity['pair_id'], self.producer_job['pair_id'], 'Actual transport pair differs')
            same(identity['sense_request_id'], rid, 'Actual transport request key differs')
            same(identity['target_id'], target, 'Actual transport target differs')
            same(identity['payload_sha256'], digest({k: row[k] for k in ('frame', 'allowed_sensor_ids', 'start_tick')}),
                 'Actual transport measurement-wrapper digest differs')
            committed = registry['committed'][rid]
            same(committed['identity'], identity, 'Actual committed response identity differs')
            response_sha = digest(row['result'])
            same(committed['result_sha256'], response_sha, 'Saved actual result differs from committed response')
            same(committed['commit_id'], digest(dict(identity=identity, context=request['context'], result_sha256=response_sha)),
                 'Actual response commitment digest differs')
            endpoint = row['actual_endpoint']
            public.validate_schema(endpoint, 'ActualEndpoint')
            same(endpoint['endpoint_digest'], digest({k: v for k, v in endpoint.items() if k != 'endpoint_digest'}),
                 'Actual endpoint digest differs')
            same(endpoint['team'], flow['team'], 'Actual occupied team changed from committed action')
            same(endpoint['target_id'], target, 'Actual endpoint target differs')
            same(endpoint['tick'], tick, 'Actual endpoint tick differs')
            same(endpoint['source_kind'], 'ACTUAL', 'Predicted endpoint was relabeled actual')
            records, slots = [], []
            for member in endpoint['team']:
                robot = member['robot_id']; key = (target, robot, tick)
                require(key in cache, 'Actual fusion has no acquired cached raw outcome')
                slot = cache[key]['slot']
                slots.append(dict(slot_key=slot['slot_key'], slot_digest=slot['slot_digest'], state=slot['state']))
                if slot['state'] == 'VALID':
                    records.append(dict(slot['packet'], packet_id=frame['frame_id'] + ':U' + str(robot)))
            same(endpoint['slots'], slots, 'Actual endpoint slot contribution ledger differs')
            same(frame['records'], records, 'Actual frame differs from acquired VALID/MISSING raw outcomes')
            quality = row['result']['quality']
            same(endpoint['quality']['status'], quality['status'], 'Saved actual quality did not enter endpoint')
            same(endpoint['quality']['payload_digest'], row['result']['payload_sha256'], 'Actual endpoint payload identity differs')
            same(endpoint['quality']['radius_proxy'], quality['radius_proxy'], 'Actual endpoint radius differs')
            require(tick in actual_frames and str(target) in actual_frames[tick]['actual_endpoints'],
                    'Actual fusion endpoint was not published in its physical/decision frame')
            same(actual_frames[tick]['actual_endpoints'][str(target)], endpoint,
                 'Actual fusion G/Q/history endpoint differs from the saved physical frame')
        same(sorted(matched), sorted(registry['requests']), 'Whole actual step omitted/added a committed fusion')

    def _shape(self, value, evidence):
        from research.information_service_online import public

        validate_value(value)
        fields(value, STEP_FIELDS, '')
        same(value['status'], 'COMMITTED', 'Actual step status changed')
        same(value['replayed'], False, 'Main fresh actual interval cannot be a replay')
        same(value['start_tick'], self.previous['tick'], 'Actual start tick changed')
        same(value['end_tick'], self.current['tick'], 'Actual end tick changed')
        same(value['checkpoint_after'], self.current, 'Actual step endpoint checkpoint changed')
        same(value['public_binding'], self.data['current_public_binding_file'], 'Actual step public history binding changed')
        public.validate_schema(value['action_commit'], 'CommittedAction')
        commit = value['action_commit']
        same(value['action_commit_id'], commit['action_commit_id'], 'Actual action commit identity changed')
        same(commit['action_commit_id'], digest({k: v for k, v in commit.items() if k != 'action_commit_id'}),
             'Actual action commit digest differs')
        same(commit['checkpoint_id'], self.previous['checkpoint_id'], 'Action commit addresses wrong checkpoint')
        same(commit['assignment'], self.data['action_file']['payload']['assignment'], 'Actual committed assignment differs')
        for slot in commit['prepared_actual_slots']:
            key = slot['slot_key']; cache_key = (key['target_id'], key['robot_id'], key['tick'])
            require(cache_key in self.actual_cache, 'Prepared action slot was not actually acquired')
            same(self.actual_cache[cache_key]['slot'], slot, 'Prepared action slot differs from immutable actual raw outcome')
        robots = self.previous['config']['robots']; targets = self.previous['config']['task_count']
        require(type(value['frames']) is list and len(value['frames']) == 21, 'Actual step must retain decision frame plus20 physical frames')
        for i, frame in enumerate(value['frames']):
            at = f'/frames/{i}'; fields(frame, FRAME_FIELDS, at)
            same(frame['tick'], value['start_tick'] + i, 'Actual frame cadence/order differs')
            binary(frame['time'], at + '/time')
            same(frame['time'], frame['tick'] * .05, 'Actual frame time differs')
            require(type(frame['phase']) is str, 'Actual frame phase must be a string')
            for name in ('positions_start', 'positions', 'control'):
                _full_vectors(frame[name], robots, at + '/' + name)
            _assignment(frame['assignment'], robots, at + '/assignment')
            require(type(frame['control_elapsed_by_robot']) is list and len(frame['control_elapsed_by_robot']) == robots,
                    'Actual interval duration ledger lost full X')
            for k, elapsed in enumerate(frame['control_elapsed_by_robot']):
                binary(elapsed, at + f'/control_elapsed_by_robot/{k}')
            require(type(frame['statuses']) is list and len(frame['statuses']) == targets and
                    all(type(s) is str for s in frame['statuses']), 'Actual lifecycle status ledger lost full Y')
            for name in ('progress', 'active_segment_ids', 'actual_endpoints'):
                require(type(frame[name]) is dict, 'Actual frame history maps must be explicit')
            for progress in frame['progress'].values():
                binary(progress, at + '/progress')
            for endpoint in frame['actual_endpoints'].values():
                if endpoint is not None:
                    public.validate_schema(endpoint, 'ActualEndpoint')
            for event in frame['events']:
                public.validate_schema(event, 'PublicEvent')
            _validate_metrics(frame['metrics'], robots, at + '/metrics')
        for event in value['events']:
            public.validate_schema(event, 'PublicEvent')
        for name in ('ended_ids', 'new_ids'):
            require(type(value[name]) is list and all(type(i) is int for i in value[name]), 'Actual task-event IDs malformed')
        _validate_metrics(value['metrics'], robots, '/metrics')
        same(value['frames'][-1]['metrics'], value['metrics'], 'Actual whole-step metrics differ from final physical frame')
        return dict(passed=True, shape='complete_actual_step_with21frames', terminal_cut=self.current['phase'] == 'TERMINAL')

    def admission(self):
        def source(value, evidence):
            same(value, self.step, 'Actual step bytes changed after source/commit admission')
            return dict(passed=True, real_actual_producer=self.process_proof,
                        complete_successful_request_result_verified=True,
                        complete_private_history_suffix_verified=True,
                        external_step_pin=self.pins['step_result_file'])
        def slots(value, evidence):
            from research.information_service_online.quality_audit import audit_fusion
            counts = {}
            for row in value['fusion_records']:
                observed = audit_fusion(row)['counts']
                for key, count in observed.items():
                    counts[key] = counts.get(key, 0) + count
            return dict(passed=True, actual_raw_cache_and_committed_response_count=len(value['fusion_records']),
                        independent_saved_information_audit=counts,
                        no_actual_sampler_or_WLS_invoked=True)
        return ComparisonAdmission(source_sha256=self.pins['step_result_file']['sha256'],
            registrations=self.registrations,
            expected_scientific_identity=dict(checkpoint_id=self.previous['checkpoint_id'],
                evaluation_request_id=None, world_id=None, candidate_id=None),
            source_validator=source, schema_validator=self._shape, source_slots_validator=slots)


def compare_actual_steps(job, comparison, out):
    """Called inside the existing noninitial D cut-source job, including T."""
    # Link the purported new side to the exact new source receipt being admitted
    # by this job. Two valid historical producers must never be substituted for
    # the intended old-versus-new comparison.
    receipt, _ = pinned_read(job, job['receipt_file'])
    previous, _ = pinned_read(job, job['previous_receipt_file'])
    producer, _ = pinned_read(job, receipt['producer_result_pin']['path'])
    dispatched, _ = pinned_read(job, receipt['producer_job_pin']['path'])
    payload = dispatched['job']['env_start']
    expected_new = dict(step_result_file=producer['step_result_file'],
        producer_job_file=receipt['producer_job_pin']['path'],
        guardian_result_file=receipt['producer_guardian_pin']['path'],
        response_registry_file=str(Path(receipt['producer_result_pin']['path']).parent / 'response_registry.json'),
        env_result_file=receipt['producer_result_pin']['path'], action_file=payload['action_file'],
        previous_public_checkpoint_file=previous['artifacts']['public_checkpoint']['path'],
        previous_public_binding_file=previous['artifacts']['public_binding']['path'],
        previous_private_snapshot_file=previous['artifacts']['private_snapshot']['path'],
        current_private_snapshot_file=receipt['artifacts']['private_snapshot']['path'],
        current_public_checkpoint_file=receipt['artifacts']['public_checkpoint']['path'],
        current_public_binding_file=receipt['artifacts']['public_binding']['path'],
        private_input_file=job['private_input_pin']['path'])
    fields(comparison['new'], SIDE_FIELDS, '/execution_comparison/new')
    for name, path in expected_new.items():
        _same_path(comparison['new'][name], path, 'New-side comparison descriptor does not address this actual source: ' + name)
    _same_path(comparison['old']['current_public_checkpoint_file'], job['old_checkpoint_pin']['path'],
               'Old-side comparison is not the exact frozen counterpart of this cut')
    old = ExecutionAdmission(job, comparison['old'], historical=comparison)
    new = ExecutionAdmission(job, comparison['new'])
    same(old.previous, new.previous, 'Actual intervals did not start from identical admitted public states')
    same(old.step['start_tick'], new.step['start_tick'], 'Actual interval starts differ')
    same(old.step['end_tick'], new.step['end_tick'], 'Actual interval ends differ')
    left, right = comparison['old']['step_result_file'], comparison['new']['step_result_file']
    result = compare_files(left, right, out=out,
        metadata=dict(artifact_scope='execution_step', left_artifact_id=str(left), right_artifact_id=str(right),
                      scientific_request_id=old.previous['checkpoint_id'], candidate_id_or_null=None,
                      comparison_route='RS_EXACT'),
        left_admission=old.admission(), right_admission=new.admission())
    require(result['status'] == 'EQUAL', 'Whole actual execution step differs; strict report retained, no next prediction allowed')
    return result
