"""Bounded saved-artifact audits; never runs motion, WLS or a new rollout."""
from copy import deepcopy
from pathlib import Path

from .common import ContractError, digest, save_json
from .artifact_admission import ArtifactAdmissions, pinned_read, require, same, validate_guardian
from .comparator import compare_files, compare_raw
from .source_admission import admit_original, validate_new_receipt


def _metadata(scope, left, right, request_id=None, candidate_id=None):
    return dict(artifact_scope=scope, left_artifact_id=str(left), right_artifact_id=str(right),
                scientific_request_id=request_id, candidate_id_or_null=candidate_id, comparison_route='RS_EXACT')


def _cache(job, batch, out):
    from .trace_audit import audit_trace, audit_ownership
    diagnostics, _ = pinned_read(job, batch['cache_diagnostics_file'])
    producer_record, _ = pinned_read(job, batch['producer_job_file'])
    producer_payload = producer_record['job']['env_start']
    require(producer_payload['kind'] == 'predict_shared' and producer_payload['method'] == 'S',
            'Cache audit source is not a registered shared producer')
    same(diagnostics['scope'], producer_payload['cache_scope'], 'Saved cache scope differs from exact dispatched producer scope')
    trace, _ = pinned_read(job, batch['cache_trace_file'])
    instrumentation, _ = pinned_read(job, batch['cache_instrumentation_file'])
    require(batch.get('oracle_file') is not None, 'Main cache audit requires its sealed saved-R oracle')
    oracle, _ = pinned_read(job, batch['oracle_file'])
    values = [pinned_read(job, p)[0] for p in batch['candidate_result_files']]
    ownership, _ = pinned_read(job, batch['candidate_ownership_file'])
    request, _ = pinned_read(job, job['request_file'])
    ownership_audit = audit_ownership(ownership, request, [value['candidate'] for value in values],
                                      diagnostics['scope']['full_scope_id'])
    require(diagnostics['cache_status'] == 'CLOSED', 'Main worker did not destroy its cache scope')
    result = audit_trace(trace, diagnostics, oracle, values)
    built = result['counters']['new_computed_intervals']
    same(instrumentation['compute_entries'], built, 'Compute entry count differs from unique actual builds')
    same(instrumentation['compute_returns'], built, 'Compute return count differs from unique actual builds')
    same(instrumentation['numpy_vector_update_calls'], built, 'Per-component vector kernel count differs')
    require(type(instrumentation['peak_cache_bytes']) is int and instrumentation['peak_cache_bytes'] >= 0,
            'Actual peak-cache measurement missing')
    result['instrumentation'] = instrumentation
    result['candidate_ownership'] = ownership_audit
    save_json(Path(out) / 'cache_trace_audit.json', result)
    return result


def _compare(job, out):
    comparison, _ = pinned_read(job, job['comparison_file'])
    require(comparison['comparator_id'] == 'gq_shared_full_typed_binary64_v1', 'Wrong frozen comparison contract')
    left = ArtifactAdmissions(job, job['left'])
    right = ArtifactAdmissions(job, job['right'])
    same(left.request, right.request, 'Comparison requires identical current scientific request')
    # Both complete producer maps have just passed source/context admission.
    # Reuse their identity index only. compare_files still rereads the files,
    # checks their pins and validates their content against admitted values.
    left_by_id = {r['candidate']['candidate_id']: p for p,r in left.producers.items()}
    right_by_id = {r['candidate']['candidate_id']: p for p,r in right.producers.items()}
    refs = []
    for candidate in left.manifest['candidates']:
        cid = candidate['candidate_id']; lp = left_by_id[cid]; rp = right_by_id[cid]
        result = compare_files(lp, rp, out=Path(out) / f"candidate_{candidate['index']:04d}",
            metadata=_metadata('candidate_evaluation', lp, rp, left.request['evaluation_request_id'], cid),
            left_admission=left.candidate_admission(lp), right_admission=right.candidate_admission(rp))
        refs.append(result)
        save_json(Path(out) / 'completed_candidate_comparisons.json', refs)
        require(result['status'] == 'EQUAL', 'Candidate strict/diagnostic equivalence failed; saved report retained')
    selection = compare_files(job['left']['selection_file'], job['right']['selection_file'],
        out=Path(out) / 'selection', metadata=_metadata('selection', job['left']['selection_file'],
            job['right']['selection_file'], left.request['evaluation_request_id']),
        left_admission=left.selection_admission(), right_admission=right.selection_admission())
    require(selection['status'] == 'EQUAL', 'Complete selection/fees/finite table mismatch; saved report retained')
    cache_results = []
    for side in ('left', 'right'):
        for i, batch in enumerate(job[side].get('cache_batches', [])):
            matched = [p for p in job[side]['producer_records']
                       if Path(p['job_file']).resolve() == Path(batch['producer_job_file']).resolve()]
            require(len(matched) == 1, 'Cache source not uniquely among this table side producers')
            source_result, _ = pinned_read(job, matched[0]['env_result_file'])
            same([str(Path(p).resolve()) for p in batch['candidate_result_files']],
                 [str(Path(row['result_file']).resolve()) for row in source_result['items']],
                 'Cache audit omitted/reordered/added producer candidate outputs')
            result = _cache(job, batch, Path(out) / f'{side}_cache_{i:02d}')
            cache_results.append(dict(side=side, batch_id=batch['batch_id'], result=result))
    decision_audit = None
    if job.get('decision_audit_job') is not None:
        from research.information_service_online.acceptance import audit_decision
        declared = job['decision_audit_job']
        # Every legacy audit input is independently pinned before the saved-data
        # routine is allowed to open it; no recursive directory permission.
        for name in ('request_file', 'binding_file', 'selection_file'):
            pinned_read(job, declared[name])
        for name in ('candidate_result_files', 'reference_result_files'):
            for p in declared.get(name, []):
                pinned_read(job, p)
        decision_audit = audit_decision(declared, Path(out) / 'independent_finite_table')
    return dict(passed=True, snapshot_id=job['snapshot_id'], candidate_count=len(refs),
                empty_complete_table_compared=not refs, candidate_comparisons=refs, selection_comparison=selection,
                cache_audits=cache_results, independent_decision_audit=decision_audit,
                real_wls_calls=0, scope='strict typed complete-table/selection and admitted saved-data audit; no scientific rerun')


def _original_source(job, out):
    registry, pin = pinned_read(job, job['registry_path'])
    same(pin['sha256'], job['registry_sha'], 'Original source registry pin differs')
    for p in job['snapshot']['public_inputs'].values():
        pinned_read(job, p['path'])
    pinned_read(job, job['snapshot']['source_registration']['registered_execution_result_auditor_only']['path'])
    return admit_original(job['snapshot'], registry, job['registry_sha'], registry_path=job['registry_path'])


def _fresh_source(job, out):
    from research.information_service_online import public
    receipt, _ = pinned_read(job, job['receipt_file'])
    same(receipt, job['receipt'], 'New source receipt differs from external file pin')
    previous = None
    if job.get('previous_receipt_file') is not None:
        previous, _ = pinned_read(job, job['previous_receipt_file'])
    same(previous, job.get('previous'), 'Previous actual source receipt changed')
    validate_new_receipt(receipt, attempt_id=job['attempt_id'], episode_id=job['episode_id'], previous=previous)
    producer, producer_pin = pinned_read(job, receipt['producer_result_pin']['path'])
    same(producer_pin['sha256'], receipt['producer_result_pin']['sha256'], 'New producer result pin differs')
    wrapped, job_pin = pinned_read(job, receipt['producer_job_pin']['path'])
    same(job_pin['sha256'], receipt['producer_job_pin']['sha256'], 'New producer dispatched-job pin differs')
    dispatched = wrapped['job']; payload = dispatched['env_start']
    guardian, guardian_pin = pinned_read(job, receipt['producer_guardian_pin']['path'])
    same(guardian_pin['sha256'], receipt['producer_guardian_pin']['sha256'], 'New producer guardian pin differs')
    process_proof = validate_guardian(guardian, dispatched)
    require(payload['kind'] == ('initialize' if receipt['tick'] == 0 else 'execute'), 'New actual cut came from wrong producer operation')
    same(payload['physical_environment_id'], receipt['physical_environment_id'], 'New physical producer identity mismatch')
    require(producer.get('passed') is True, 'New actual worker did not commit successfully')
    same(producer['checkpoint_id'], receipt['checkpoint_id'], 'New producer checkpoint differs from receipt')
    same(producer['tick'], receipt['tick'], 'New producer tick differs from receipt')
    values = {}
    for name, pin in receipt['artifacts'].items():
        value, external_pin = pinned_read(job, pin['path'])
        same(pin['sha256'], external_pin['sha256'], 'New artifact differs from outer pin')
        same(str(Path(pin['path']).resolve()), str(Path(producer['artifacts'][name]).resolve()), 'Artifact was not published by actual producer')
        require(Path(pin['path']).resolve().parent == Path(receipt['producer_result_pin']['path']).resolve().parent,
                'Actual artifact escaped producer output directory')
        values[name] = value
    same(sorted(values), sorted(producer['artifacts']), 'Incomplete actual artifact set')
    checkpoint, binding, private = values['public_checkpoint'], values['public_binding'], values['private_snapshot']
    same(private['physical_environment_id'], receipt['physical_environment_id'], 'Private restore belongs to another actual environment')
    require(private['failed'] is False and private['inflight'] is None, 'New cut is failed or still preparing')
    same(private['checkpoint'], checkpoint, 'Private commit and published checkpoint differ')
    same(private['snapshot_digest'], digest({k: v for k, v in private.items() if k != 'snapshot_digest'}),
         'Actual private snapshot checksum differs')
    same(binding['public_checkpoint'], checkpoint, 'Actual binding and checkpoint differ')
    initial, initial_pin = pinned_read(job, job['private_input_pin']['path'])
    same(initial_pin['sha256'], job['private_input_pin']['sha256'], 'Private initial input differs from external pin')
    same(private['source_identity'], digest(initial), 'New actual source initial/future identity changed')
    same(str(Path(payload['private_input_file']).resolve()), str(Path(job['private_input_pin']['path']).resolve()), 'Foreign private initial input')
    authority = public.HistoryAuthority.from_public_binding(binding)
    public.validate_checkpoint(checkpoint, authority)
    if previous is not None:
        old_state, _ = pinned_read(job, payload['private_snapshot_file'])
        same(payload['private_snapshot_sha256'], previous['artifacts']['private_snapshot']['sha256'], 'Producer restored an unregistered old cut')
        same(old_state['checkpoint']['checkpoint_id'], previous['checkpoint_id'], 'Producer restored wrong checkpoint')
        envelope, _ = pinned_read(job, payload['action_file'])
        request_id = envelope['operation']['request_id']
        require(request_id in private['successful_requests'], 'New action absent from successful replay journal')
        cached = private['successful_requests'][request_id]
        same(digest(cached), receipt['successful_action_cache_link'], 'Actual successful action cache link changed')
        same(cached['fingerprint'], digest(dict(physical_environment_id=receipt['physical_environment_id'],
             checkpoint_id=envelope['payload']['checkpoint_id'], expected_start_tick=envelope['payload']['expected_start_tick'],
             assignment=envelope['payload']['assignment'])), 'Actual successful request fingerprint changed')
        step, _ = pinned_read(job, producer['step_result_file'])
        same(cached['result'], step, 'Successful replay journal differs from original actual step result')
        for old_id, old_result in old_state['successful_requests'].items():
            require(old_id in private['successful_requests'], 'Previously successful request disappeared during resume')
            same(private['successful_requests'][old_id], old_result, 'Previously committed replay result changed')
        same(step['status'], 'COMMITTED', 'Actual step did not commit')
        same(step['checkpoint_after'], checkpoint, 'Step result and new cut differ')
        same(step['action_commit']['assignment'], envelope['payload']['assignment'], 'Actual committed another action')
        same(step['action_commit']['checkpoint_id'], previous['checkpoint_id'], 'Actual action addressed stale checkpoint')
        same(step['start_tick'], previous['tick'], 'Actual step start differs')
        same(step['end_tick'], receipt['tick'], 'Actual step end differs')
    if checkpoint['phase'] == 'DECISION_READY':
        request = public.validate_request(values['evaluation_request'], authority)
        same(request['checkpoint'], checkpoint, 'New evaluation request not derived from actual cut')
        manifest = public.build_manifest(request, authority)
        same([row['candidate'] for row in values['candidate_catalog']], manifest['candidates'], 'New actual candidate catalog changed')
    else:
        same(checkpoint['phase'], 'TERMINAL', 'Unexpected terminal source phase')
        require('evaluation_request' not in values and 'candidate_catalog' not in values, 'Terminal cut must not authorize another decision')
    old_path = job.get('expected_public_checkpoint_file', job['old_checkpoint_pin']['path'])
    _, old_pin = pinned_read(job, old_path)
    same(old_pin['sha256'], job['old_checkpoint_pin']['sha256'], 'Frozen old comparison checkpoint pin mismatch')
    current_path = receipt['artifacts']['public_checkpoint']['path']
    compared = compare_raw(Path(old_path).read_bytes(), Path(current_path).read_bytes(),
        _metadata('public_checkpoint_or_request', old_path, current_path))
    save_json(Path(out) / 'new_cut_vs_frozen_public_state.json', compared)
    require(compared['status'] == 'EQUAL', 'New actual state left frozen domain; stop before prediction, never force old action')
    execution_report = None
    if previous is None:
        require(job.get('execution_comparison') is None, 'Initial cut has no preceding actual interval to compare')
    else:
        require(type(job.get('execution_comparison')) is dict,
                'Every noninitial actual cut, including terminal cuts, requires whole-step comparison')
        from .execution_admission import compare_actual_steps
        execution_report = compare_actual_steps(job, job['execution_comparison'], Path(out) / 'execution_step_comparison')
    return dict(passed=True, source_kind='NEW_COMMITTED_EXECUTION', grants_main_authority=True,
                episode_id=job['episode_id'], tick=receipt['tick'], checkpoint_id=receipt['checkpoint_id'],
                producer=process_proof, new_source_receipt_id=digest(receipt),
                matched_old_public_checkpoint=True, synthetic_fixture_used=False,
                old_action_supplied_to_selector=False, real_wls_calls=0,
                execution_step_compared=execution_report is not None,
                execution_step_comparison=execution_report)


def run_audit(job, out):
    out = Path(out)
    try:
        if job['kind'] == 'shared_compare':
            result = _compare(job, out)
        elif job['kind'] == 'shared_source':
            if job['source_mode'] == 'original':
                result = _original_source(job, out)
            elif job['source_mode'] == 'fresh':
                result = _fresh_source(job, out)
            else:
                raise ContractError('Unknown declared source admission mode')
        elif job['kind'] == 'shared_trace':
            result = _cache(job, job, out)
        else:
            raise ContractError('Unknown shared saved-data audit operation')
        require(result.get('passed') is True, 'Saved-data audit did not pass')
        save_json(out / 'audit_result.json', result)
        return result
    except Exception as error:
        save_json(out / 'audit_failure.json', dict(passed=False, kind=job.get('kind'),
            error_type=type(error).__name__, error=str(error), original_evidence_preserved=True,
            no_retry=True, scientific_rerun_performed=False))
        raise
