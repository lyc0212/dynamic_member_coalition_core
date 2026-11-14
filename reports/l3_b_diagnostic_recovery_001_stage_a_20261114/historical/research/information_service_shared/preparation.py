"""Append-only implementation sealing. Preparation performs metadata work only."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import time
from .common import STAGE_CONTRACT, ContractError, digest, typed_digest, read_json, save_json, sha_file
from .source_admission import ROOT, LOCK, LOCK_SHA, source_census, check_pin

STEM = 'STAGE2A5B_GQ_SHARED_FULL_'
ENTRY = ROOT / 'examples/validate_stage2a5b_gq_shared.py'
PREVIOUS_PREPARATION = ROOT/'evidence/stage2a5b_gq_shared_full/attempt_preparation_20261024_diagnostic_contract_r6'
PREVIOUS_SEAL_SHA = 'cf4ab616bdce019417f5c92aee66cd105118a9bd639406ab87ccd58177285a24'
REPAIR_CHECK_SOURCE = ROOT/'docs/stage2a5b_gq_shared_full_repairs/c02_r4/verify_native_adapter.py'
REPAIR_CHECK_RESULT = ROOT/'evidence/stage2a5b_gq_shared_full/audit_cost_r7_type_checks/result.json'
ORACLE_CHECK_SOURCE = ROOT/'docs/stage2a5b_gq_shared_full_repairs/oracle_r5/verify_oracle_interface.py'
ORACLE_CHECK_RESULT = ROOT/'evidence/stage2a5b_gq_shared_full/audit_cost_r7_oracle_checks/result.json'
DIAGNOSTIC_CHECK_SOURCE = ROOT/'docs/stage2a5b_gq_shared_full_repairs/diagnostics_r6/verify_diagnostics.py'
DIAGNOSTIC_CHECK_RESULT = ROOT/'evidence/stage2a5b_gq_shared_full/diagnostics_r6_checks/result.json'
AUDIT_CHECK_SOURCE = ROOT/'docs/stage2a5b_gq_shared_full_repairs/audit_cost/verify_audit_cost.py'
AUDIT_PROFILE_SOURCE = ROOT/'docs/stage2a5b_gq_shared_full_repairs/audit_cost/profile_saved_audit.py'
AUDIT_CHECK_DIR = ROOT/'evidence/stage2a5b_gq_shared_full/audit_cost_verified_r7_checks'
AUDIT_FAILURE_PROBE = ROOT/'evidence/stage2a5b_gq_shared_full/audit_cost_r7_failure_probe'
AUDIT_REGRESSION_SOURCE = ROOT/'docs/stage2a5b_gq_shared_full_repairs/audit_cost/verify_saved_regressions.py'
AUDIT_REGRESSION_DIR = ROOT/'evidence/stage2a5b_gq_shared_full/audit_cost_r7_saved_regressions'


def pin(path, relative_to=None):
    path = Path(path).resolve()
    return dict(path=str(path.relative_to(relative_to)) if relative_to else str(path),
                sha256=sha_file(path), size_bytes=path.stat().st_size)


def verify_previous_preparation():
    """Verify preserved copies, not mutable live implementation files."""
    path=PREVIOUS_PREPARATION
    if sha_file(path/'SEAL_I.json')!=PREVIOUS_SEAL_SHA:
        raise ContractError('Previous runtime seal changed')
    seal=read_json(path/'SEAL_I.json')
    for name,row in seal['files'].items():check_pin(dict(path=str(path/name),**row))
    manifest=read_json(path/'input_source_manifest.json')['files']
    for name,sha in manifest.items():
        check_pin(dict(path=str(path/'frozen_sources'/name),sha256=sha))
    if not (path/'execution_started.json').exists():
        raise ContractError('Expected preserved failed predecessor, not a replacement for it')
    previous_result=read_json(path/'result.json')
    if previous_result.get('passed') is not False or previous_result.get('status')!='STOPPED_WITH_RETAINED_EVIDENCE':
        raise ContractError('Unexpected predecessor execution status')
    if read_json(path/'finalization_receipt.json')['result_sha256']!=sha_file(path/'result.json'):
        raise ContractError('Previous result persistence receipt changed')
    return dict(seal=pin(path/'SEAL_I.json'),frozen_source_count=len(manifest),
                sealed_asset_count=len(seal['files']),execution_started=True,
                previous_guardian_job_count=previous_result['job_count'],
                previous_result=pin(path/'result.json'),previous_ledger=pin(path/'resource_ledger.json'),
                previous_finalization=pin(path/'finalization_receipt.json'),
                previous_status=previous_result['status'],previous_scientific_cpu=previous_result['scientific_cpu'],
                previous_numerical_totals=previous_result['totals'],new_attempt_is_not_resume=True)


def build_execution_step_sources(attempt):
    """Freeze exact saved actual evidence; no comparator or model is invoked."""
    batches=read_json(attempt/'inputs/BATCHES.json')
    registry_ref=batches['source_pins']['actual_checkpoint_registry']
    registry_path=check_pin(registry_ref);registry=read_json(registry_path)
    by_cut={(r['episode_id'],r['tick']):r for r in registry}
    entries=[]
    for index_ref in batches['source_pins']['episode_indices']:
        index_path=check_pin(index_ref);index=read_json(index_path);eid=index['episode_id']
        for decision in index['decisions']:
            start=decision['tick'];end=start+20;before=by_cut[(eid,start)];after=by_cut[(eid,end)]
            result=Path(decision['execution_result_file']).resolve();producer=result.parent
            if result!=Path(after['registered_execution_result']).resolve():
                raise ContractError('Historical step has another registered actual producer')
            for label,cut,artifacts in (('before',before,decision['artifacts']),('after',after,decision['artifacts_after'])):
                for name in ('private_snapshot','public_checkpoint','public_binding'):
                    registered=check_pin(cut['artifacts'][name])
                    if registered!=Path(artifacts[name]).resolve():
                        raise ContractError('Historical '+label+' step source differs from registered cut')
            side=dict(step_result_file=str(Path(decision['step_result_file']).resolve()),
                producer_job_file=str(registry_path.parent/'dispatched_jobs'/f'{producer.parent.name}.json'),
                guardian_result_file=str(producer.parent/'guardian_result.json'),
                response_registry_file=str(producer/'response_registry.json'),env_result_file=str(result),
                action_file=str(Path(decision['action_file']).resolve()),
                previous_public_checkpoint_file=str(check_pin(before['artifacts']['public_checkpoint'])),
                previous_public_binding_file=str(check_pin(before['artifacts']['public_binding'])),
                previous_private_snapshot_file=str(check_pin(before['artifacts']['private_snapshot'])),
                current_private_snapshot_file=str(check_pin(after['artifacts']['private_snapshot'])),
                current_public_checkpoint_file=str(check_pin(after['artifacts']['public_checkpoint'])),
                current_public_binding_file=str(check_pin(after['artifacts']['public_binding'])),
                private_input_file=str(Path(index['private_input_file']).resolve()))
            # This links the standalone step file to the old registry's already
            # pinned private successful-request cache; a new self hash is not
            # used as evidence of authentic historical execution.
            action=read_json(side['action_file']);request_id=action['operation']['request_id']
            private=read_json(side['current_private_snapshot_file']);step=read_json(side['step_result_file'])
            if typed_digest(step)!=typed_digest(private['successful_requests'][request_id]['result']):
                raise ContractError('Historical standalone step differs from its registered successful result')
            if (step['start_tick'],step['end_tick'])!=(start,end):
                raise ContractError('Historical step timing does not match its declared cut')
            fixed={name:pin(name) for name in sorted(set(side.values()))}
            entries.append(dict(episode_id=eid,start_tick=start,end_tick=end,old=side,
                old_source_pins=fixed,old_registry_file=str(registry_path),old_registry_sha=registry_ref['sha256'],
                old_episode_index_file=str(index_path),old_episode_index_sha=index_ref['sha256']))
    if len(entries)!=30 or len({(e['episode_id'],e['start_tick']) for e in entries})!=30:
        raise ContractError('Exactly30 historical actual steps must be frozen')
    catalog=dict(contract_id=STAGE_CONTRACT,visibility='AUDIT_ONLY_NEVER_PREDICTOR_OR_SELECTOR',
        scope='Existing D source audits compare full saved execution_step after provenance admission',
        scientific_calls=0,new_jobs=0,entries=entries)
    save_json(attempt/'inputs/execution_step_sources.json',catalog)
    return catalog


def prepare(attempt):
    """Seal existing code, exact role closures and data; no runtime pass implied."""
    attempt = Path(attempt).resolve()
    if attempt.exists() and any(attempt.iterdir()):
        raise FileExistsError('A new empty implementation preparation directory is required')
    start, cpu = time.monotonic(), time.process_time()
    census = source_census()
    predecessor=verify_previous_preparation()
    attempt.mkdir(parents=True, exist_ok=True)
    for name in ('DESIGN','SCHEMA','SHORT_CHECKS','COMPARISON','ADMISSION','BATCHES'):
        dst = attempt/'inputs'/f'{name}.json'
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/'docs'/f'{STEM}{name}.json', dst)
    build_execution_step_sources(attempt)
    save_json(attempt/'previous_preparation.json',predecessor)
    repair=read_json(REPAIR_CHECK_RESULT)
    if (repair.get('passed') is not True or repair.get('group_count')!=9 or repair.get('C02_executed') is not False
            or repair.get('candidate_evaluations')!=0 or repair.get('WLS_calls')!=0 or repair.get('control_rollouts')!=0
            or repair.get('science_modules_loaded')!=[]):
        raise ContractError('Expected pure type-adapter repair evidence, never C02 acceptance')
    for name,sha in repair['source_sha256'].items():check_pin(dict(path=name,sha256=sha))
    shutil.copyfile(REPAIR_CHECK_RESULT,attempt/'inputs/c02_adapter_type_checks.json')
    oracle_repair=read_json(ORACLE_CHECK_RESULT)
    if (oracle_repair.get('passed') is not True or oracle_repair.get('check_count')!=20
            or oracle_repair.get('actual_saved_batch_count')!=2 or oracle_repair.get('oracle_count')!=49
            or oracle_repair.get('oracle_variants')!={'STANDARD':33,'REVERSE':8,'REBATCH':8}
            or oracle_repair.get('negative_count')!=17 or oracle_repair.get('protected_inputs_unchanged') is not True
            or oracle_repair.get('scientific_imports')!=[] or oracle_repair.get('scientific_imports_denied')!=[]
            or any(oracle_repair.get(k)!=0 for k in ('WLS_calls','control_rollouts','candidate_evaluations','created_children'))
            or oracle_repair.get('formal_run_started') is not False or oracle_repair.get('old_failed_job_reclassified') is not False
            or not 0<=oracle_repair.get('process_CPU_seconds',-1)<60
            or not 0<=oracle_repair.get('wall_seconds',-1)<120):
        raise ContractError('Expected bounded saved-data oracle integration evidence, not formal acceptance')
    for name,sha in oracle_repair['source_sha256'].items():check_pin(dict(path=name,sha256=sha))
    oracle_plan=read_json(check_pin(oracle_repair['plan']))
    for source_pin in oracle_plan['input_pins']:check_pin(source_pin)
    if oracle_plan['source_sha256']!=oracle_repair['source_sha256']:
        raise ContractError('Oracle verification plan/source mismatch')
    for name in ('result.json','verification_plan.json','oracle_parser_coverage.json','completed_checks.json'):
        shutil.copyfile(ORACLE_CHECK_RESULT.parent/name,attempt/'inputs'/('oracle_repair_'+name))
    diagnostic=read_json(DIAGNOSTIC_CHECK_RESULT)
    if (diagnostic.get('passed') is not True or diagnostic.get('real_pairs')!=24
            or diagnostic.get('coverage')!={'candidates':114,'estimates':6236,'starts':56124,'guarded':12}
            or diagnostic.get('negative_cases')!=8 or diagnostic.get('discrete_differences')!=2
            or diagnostic.get('inputs_unchanged') is not True or diagnostic.get('forbidden_modules_loaded')!=[]
            or any(diagnostic.get(k)!=0 for k in ('WLS_calls','control_rollouts','candidate_evaluations','created_children'))
            or diagnostic.get('formal_run_started') is not False or diagnostic.get('old_failure_reclassified') is not False
            or not 0<=diagnostic.get('process_CPU_seconds',-1)<60 or not 0<=diagnostic.get('wall_seconds',-1)<120):
        raise ContractError('Expected bounded saved diagnostic branch/comparison evidence')
    for name,sha in diagnostic['source_sha256'].items():check_pin(dict(path=name,sha256=sha))
    diagnostic_plan=read_json(DIAGNOSTIC_CHECK_RESULT.parent/'plan.json')
    if diagnostic_plan['source_sha256']!=diagnostic['source_sha256']:
        raise ContractError('Diagnostic plan/source mismatch')
    for name,sha in diagnostic_plan['input_pins'].items():check_pin(dict(path=name,sha256=sha))
    for row in read_json(DIAGNOSTIC_CHECK_RESULT.parent/'completed.json'):
        if row['id'].startswith('real_pair_'):check_pin(row['result']['report'])
    for name in ('result.json','plan.json','completed.json'):
        shutil.copyfile(DIAGNOSTIC_CHECK_RESULT.parent/name,attempt/'inputs'/('diagnostic_repair_'+name))
    audit_repair=read_json(AUDIT_CHECK_DIR/'result.json')
    expected_counts=dict(positive_candidates=24,positive_selections=1,positive_cache_batches=6,
        byte_equal_details=25,byte_equal_cache_reports=6,negative_cases=3,completed_check_count=39)
    if (audit_repair.get('passed') is not True or any(audit_repair.get(k)!=v for k,v in expected_counts.items())
            or any(audit_repair.get(k)!=0 for k in ('WLS_calls','control_rollouts','candidate_evaluations','created_children'))
            or any(audit_repair.get(k) is not True for k in ('inputs_unchanged','postfailure_isolation','short_negatives_before_full'))
            or audit_repair.get('formal_started') is not False
            or not 0<=audit_repair.get('process_CPU_seconds',-1)<60
            or not 0<=audit_repair.get('wall_seconds',-1)<120):
        raise ContractError('Expected complete bounded audit-reuse repair evidence')
    for name,sha in audit_repair['source_sha256'].items():check_pin(dict(path=name,sha256=sha))
    audit_plan=read_json(AUDIT_CHECK_DIR/'plan.json')
    if audit_plan['sources']!=audit_repair['source_sha256']:
        raise ContractError('Audit repair source/plan mismatch')
    for source_pin in audit_plan['input_pins'].values():check_pin(source_pin)
    observed=read_json(AUDIT_CHECK_DIR/'changed_file_after_admission_observed.json')
    if (observed['status']!='CONTEXT_REJECTED' or
            {k:observed['rejection'][k] for k in ('code','side','json_pointer')}!=dict(
                code='EXTERNAL_SOURCE_PIN_MISMATCH',side='left',json_pointer='')):
        raise ContractError('Source pin negative was not actually observed')
    done=read_json(AUDIT_CHECK_DIR/'completed_checks.json')
    if (len(done)!=39 or not all(r['passed'] for r in done) or
            [r['check'] for r in done[:6]]!=['input_pins','changed_hit','changed_prefix',
                'postfailure_isolation','changed_file_after_admission','full_saved_audit']):
        raise ContractError('Audit repair lost immediate coverage or negative-first order')
    probe=read_json(AUDIT_FAILURE_PROBE/'failure.json')
    if (probe['error_type']!='RuntimeError' or probe['current_check']!='predeclared_failure_record_probe'
            or len(probe['completed'])!=1 or not probe['location']['line']
            or probe['CPU_seconds']<0 or probe['wall_seconds']<0):
        raise ContractError('Failure resource/location record probe did not complete as declared')
    if read_json(AUDIT_FAILURE_PROBE/'plan.json')['sources']!=audit_repair['source_sha256']:
        raise ContractError('Failure probe used another checker source')
    prior_local=AUDIT_CHECK_DIR.parent/'audit_cost_optimized_checks'
    prior_plan=read_json(prior_local/'plan.json')
    for name,sha in prior_plan['sources'].items():
        check_pin(dict(path=str(prior_local/'source_snapshot_before_checker_fix'/name),sha256=sha))
    save_json(attempt/'inputs/audit_previous_local_failure.json',dict(
        failure=pin(prior_local/'failure.json'),plan=pin(prior_local/'plan.json'),
        completed_core=pin(prior_local/'complete_equivalence.json'),
        original_source_copies=[pin(prior_local/'source_snapshot_before_checker_fix'/n) for n in prior_plan['sources']],
        failure_reclassified=False))
    for name in ('result.json','plan.json','completed_checks.json','negative_results.json',
                 'changed_file_after_admission_observed.json','complete_equivalence.json'):
        shutil.copyfile(AUDIT_CHECK_DIR/name,attempt/'inputs'/('audit_repair_'+name))
    shutil.copyfile(AUDIT_FAILURE_PROBE/'failure.json',attempt/'inputs/audit_failure_record_probe.json')
    save_json(attempt/'inputs/audit_repair_output_pins.json',
        [pin(p) for p in sorted(AUDIT_CHECK_DIR.rglob('*.json'))])
    audit_regression=read_json(AUDIT_REGRESSION_DIR/'result.json')
    if (audit_regression.get('passed') is not True or
            any(audit_regression.get(k)!=v for k,v in dict(saved_trace_count=9,empty_tables=1,pinned_equal_reports=31,checks=41).items())
            or audit_regression.get('input_pins_unchanged') is not True or audit_regression.get('formal_started') is not False
            or any(audit_regression.get(k)!=0 for k in ('WLS_calls','control_rollouts','candidate_evaluations','created_children'))
            or not 0<=audit_regression.get('process_CPU_seconds',-1)<60
            or not 0<=audit_regression.get('wall_seconds',-1)<120):
        raise ContractError('Saved audit regressions or post-verification baseline pins incomplete')
    for name,sha in audit_regression['source_sha256'].items():check_pin(dict(path=name,sha256=sha))
    regression_plan=read_json(AUDIT_REGRESSION_DIR/'plan.json')
    if regression_plan['source_sha256']!=audit_regression['source_sha256']:
        raise ContractError('Audit regression source/plan mismatch')
    for source_pin in regression_plan['input_pins']:check_pin(source_pin)
    for folder in ('audit_cost_table_baseline','audit_cost_caches_baseline'):
        if read_json(AUDIT_REGRESSION_DIR.parent/folder/'plan.json')['script_sha256']!=sha_file(AUDIT_PROFILE_SOURCE):
            raise ContractError('Profiling script differs from its original diagnosis')
    for name in ('result.json','plan.json','completed.json'):
        shutil.copyfile(AUDIT_REGRESSION_DIR/name,attempt/'inputs'/('audit_regression_'+name))
    lock = read_json(LOCK)
    names = set(lock['files']) | {str(LOCK.relative_to(ROOT)), str(ENTRY.relative_to(ROOT))}
    names.add(str(REPAIR_CHECK_SOURCE.relative_to(ROOT)))
    names.add(str(ORACLE_CHECK_SOURCE.relative_to(ROOT)))
    names.add(str(DIAGNOSTIC_CHECK_SOURCE.relative_to(ROOT)))
    names.update(str(p.relative_to(ROOT)) for p in (AUDIT_CHECK_SOURCE,AUDIT_PROFILE_SOURCE,AUDIT_REGRESSION_SOURCE))
    for item in lock['source_protection']:
        manifest = check_pin(item['manifest'])
        names.update(read_json(manifest)['files'])
        names.add(str(manifest.relative_to(ROOT)))
    new_files = sorted((ROOT/'research/information_service_shared').glob('*.py'))
    names.update(str(p.relative_to(ROOT)) for p in new_files)
    # Importing runtime installs no guard and imports no numerical/model module.
    from .runtime import ROLE_MODULES
    modules = {};namespaces={}
    for role, closure in ROLE_MODULES.items():
        files = []
        for module in sorted(closure):
            stem = ROOT.joinpath(*module.split('.'))
            choices = [stem.with_suffix('.py'), stem/'__init__.py']
            if module.startswith('test_') or module == 'service_oracle':
                choices += [ROOT/'tests'/(module+'.py')]
            found = [p for p in choices if p.is_file()]
            if not found:
                if not stem.is_dir():
                    raise ContractError('Declared source module does not exist: '+module)
                # An intentional Python namespace has no executable file to
                # hash. Freeze this absence rather than inventing an __init__.
                absent=[str(stem.with_suffix('.py').relative_to(ROOT)),
                        str((stem/'__init__.py').relative_to(ROOT))]
                entry=dict(module=module,namespace_directory=str(stem.relative_to(ROOT)),
                           absent_executable_files=absent)
                namespaces[module]=entry;files.append(entry)
                continue
            for path in found:
                names.add(str(path.relative_to(ROOT)))
                files.append(dict(module=module, **pin(path, ROOT)))
        modules[role] = files
    syntax=[]
    for name in sorted(names):
        path=ROOT/name
        if name.endswith('.py'):
            ast.parse(path.read_text(encoding='utf-8'), filename=name)
            syntax.append(name)
    manifest={name:sha_file(ROOT/name) for name in sorted(names)}
    for name in manifest:
        dst=attempt/'frozen_sources'/name
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,dst)
    save_json(attempt/'input_source_manifest.json',dict(count=len(manifest),files=manifest))
    runtime=read_json(check_pin(lock['source_seal']))['runtime']
    if str(Path(sys.executable).resolve()) not in runtime:
        raise ContractError('Preparation interpreter differs from the declared r2 runtime')
    for path,sha in runtime.items():check_pin(dict(path=path,sha256=sha))
    save_json(attempt/'runtime_fingerprint.json',dict(python=sys.version,executable=sys.executable,files=runtime))
    save_json(attempt/'role_closures.json',modules)
    save_json(attempt/'namespace_requirements.json',namespaces)
    source_seal=dict(contract_id=STAGE_CONTRACT, source_manifest=pin(attempt/'input_source_manifest.json'),
                     role_closures=pin(attempt/'role_closures.json'), source_file_count=len(manifest))
    save_json(attempt/'SOURCE_SEAL.json',source_seal)
    binding=dict(message_kind='runtime_cache_binding',contract_id=STAGE_CONTRACT,
        cache_impl_version='gq_shared_motion_source_v1',motion_geometry_contract_version='gq_shared_motion_prefix_v1',
        source_seal_sha256=sha_file(attempt/'SOURCE_SEAL.json'),
        source_files=[pin(p) for p in new_files],runtime_fingerprint_artifact=pin(attempt/'runtime_fingerprint.json'),
        comparison_contract_sha256=sha_file(attempt/'inputs/COMPARISON.json'))
    binding['runtime_binding_id']=typed_digest(binding)
    save_json(attempt/'runtime_cache_binding.json',binding)
    save_json(attempt/'protection_before.json',census)
    save_json(attempt/'authorization.json',dict(scope='Repair audit-reuse verifier and immediate failure accounting; zero-WLS regressions and reseal; no formal run',
        formal_run_authorized_in_this_preparation=False,scientific_calls=0))
    from .admission import prepare_jobs
    jobs=prepare_jobs(attempt,binding)
    save_json(attempt/'pre_main_jobs.json',jobs)
    from .runner import materialize_offline_jobs
    offline=materialize_offline_jobs(attempt,binding)
    save_json(attempt/'offline_jobs.json',offline)
    save_json(attempt/'runtime_job_rules.json',dict(contract_id=STAGE_CONTRACT,
        declared_batches=pin(attempt/'inputs/BATCHES.json'), static_offline_jobs=len(offline),
        D_source='Only new guardian-owned committed execution may register a new source; each cut audited before prediction.',
        D_execution_step='All30 noninitial cuts compare the entire old/new actual step after separate provenance/context admission, including final cuts; no added jobs or numerical work.',
        D_execution_sources=pin(attempt/'inputs/execution_step_sources.json'),
        D_action='Fresh exact selector, never historical action; actual executes next20 ticks only.',
        execution_environment_requirement='An approved local execution context that permits inherited AF_UNIX socket.send; default constrained context returned EPERM in independently recorded diagnostics. No internal elevation, fallback transport or automatic retry.',
        final_failure_accounting='Capture total wall and launcher CPU after post-census; guardian is a launcher subset; result persistence separately bracketed.',
        C02_comparison_order='Test-only immutable native type/value snapshot first; unchanged save_json output boundary next; strict JSON comparison and saved-view trace/historical audits last.',
        pure_adapter_checks=pin(attempt/'inputs/c02_adapter_type_checks.json'),
        pure_adapter_checks_are_not_C02_acceptance=True,
        oracle_reader='Use frozen component_key fields without aliases; verify actual byte/request/candidate correspondence.',
        oracle_repair_checks=pin(attempt/'inputs/oracle_repair_result.json'),
        oracle_repair_scope='Two actual saved r4 S batches plus49 saved-R oracle readers and17 synthetic negatives; no new S reverse/rebatch execution, IPC or formal pass transfer.',
        diagnostic_repair=pin(attempt/'inputs/diagnostic_repair_result.json'),
        diagnostic_scope='Existing estimator ordinary/guard/no-accepted branches; phase/reason remain strict discrete fields, never ignored or tolerance compared.',
        audit_reuse_repair=pin(attempt/'inputs/audit_repair_result.json'),
        audit_reuse_scope='Admitted identity index and auditor-owned append-only prefix hashes only; no job split or budget reset. Saved-data timing is not motion-sharing speedup.',
        exact_data_input_max=256,frame_max_bytes=2097152,all_zero_WLS_jobs_charged=True,
        old_pass_transferred=False))
    frozen={}
    for p in sorted(attempt.rglob('*')):
        if p.is_file() and not p.is_symlink() and 'frozen_sources' not in p.relative_to(attempt).parts:
            frozen[str(p.relative_to(attempt))]=dict(size=p.stat().st_size,sha256=sha_file(p))
    seal=dict(contract_id=STAGE_CONTRACT,status='SEALED_IMPLEMENTATION_PENDING_ADMISSION',
        files=frozen, source_manifest_sha256=sha_file(attempt/'input_source_manifest.json'),
        source_seal_sha256=sha_file(attempt/'SOURCE_SEAL.json'),runtime_cache_binding_id=binding['runtime_binding_id'],
        protocol_lock_sha256=LOCK_SHA,runtime=runtime,AST_checked=syntax,
        implementation_revision='bounded-audit-reuse-verified-r7',previous_preparation=predecessor,
        actual_new_source_count=len(new_files),new_implementation_unittest_modules=[],
        new_contract_check_ids=[f'C{i:02d}' for i in range(1,15)],comparator_vectors=30,
        inherited_regression_test_count=132,admission_physical_jobs=48,
        repair_verification=dict(groups=repair['group_count'],assertions=repair['assertions'],
            result=pin(attempt/'inputs/c02_adapter_type_checks.json'),script=pin(REPAIR_CHECK_SOURCE),
            C02_executed=False,formal_pass_transferred=False,new_formal_jobs=0),
        oracle_repair_verification=dict(checks=oracle_repair['check_count'],actual_saved_batches=2,oracles=49,
            negatives=17,result=pin(attempt/'inputs/oracle_repair_result.json'),script=pin(ORACLE_CHECK_SOURCE),
            formal_pass_transferred=False,new_scientific_calls=0),
        diagnostic_repair_verification=dict(result=pin(attempt/'inputs/diagnostic_repair_result.json'),
            script=pin(DIAGNOSTIC_CHECK_SOURCE),real_saved_pairs=24,formal_pass_transferred=False,new_scientific_calls=0),
        audit_repair_verification=dict(result=pin(attempt/'inputs/audit_repair_result.json'),
            script=pin(AUDIT_CHECK_SOURCE),checks=39,saved_regression=pin(attempt/'inputs/audit_regression_result.json'),
            formal_pass_transferred=False,new_scientific_calls=0),
        budget=deepcopy(lock['scientific_budget']),resources=deepcopy(lock['resources']),
        preparation_cost=dict(cpu=time.process_time()-cpu,wall=time.monotonic()-start),
        scientific_execution_started=False,admission_passed=False,cache_or_comparator_executed=False)
    save_json(attempt/'SEAL_I.json',seal)
    return dict(status=seal['status'],seal_I=pin(attempt/'SEAL_I.json'),new_source_files=len(new_files),
                source_manifest_files=len(manifest),pre_main_jobs=len(jobs),offline_jobs=len(offline),scientific_calls=0)


def verify_seal(attempt):
    attempt=Path(attempt)
    seal=read_json(attempt/'SEAL_I.json')
    if seal['protocol_lock_sha256']!=LOCK_SHA:
        raise ContractError('Wrong preparation revision at execution')
    for name, row in seal['files'].items():
        check_pin(dict(path=str(attempt/name),**row))
    for name, sha in read_json(attempt/'input_source_manifest.json')['files'].items():
        check_pin(dict(path=name,sha256=sha),historical_census_link=True)
    for entry in read_json(attempt/'namespace_requirements.json').values():
        if not (ROOT/entry['namespace_directory']).is_dir() or any((ROOT/n).exists() for n in entry['absent_executable_files']):
            raise ContractError('A frozen namespace acquired an unsealed executable initializer')
    for name, sha in seal['runtime'].items():check_pin(dict(path=name,sha256=sha))
    return seal
