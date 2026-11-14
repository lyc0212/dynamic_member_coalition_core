"""Final saved-evidence census; does not execute a controller or estimator."""
from pathlib import Path
from .common import ContractError,read_json,save_json


def final_payload(attempt,jobs,B_results,episode_indices,totals):
    from .runner import readpaths
    paths=[attempt/'resource_ledger.json',attempt/'pre_main_jobs.json',attempt/'inputs/BATCHES.json',attempt/'actual_checkpoint_registry.json',
           attempt/'B_index.json',*episode_indices]
    audits=[];source_audits=[]
    batches=read_json(attempt/'inputs/BATCHES.json')
    D_sources={c['source_audit']['work_id'] for e in batches['D_episodes'] for c in e['cuts']}
    for row in jobs:
        if row['phase']=='audit':
            p=attempt/'pairs'/row['pair_id']/'env/result.json'
            audits.append(str(p));paths.append(p)
        if row['pair_id'] in D_sources:
            p=attempt/'pairs'/row['pair_id']/'env/result.json'
            source_audits.append(dict(pair_id=row['pair_id'],result_file=str(p)));paths.append(p)
    # Under 256 exact data inputs: resource lifecycle was already individually
    # validated by the launcher; final worker reads their pinned complete ledger.
    return readpaths(dict(kind='shared_final',ledger_file=str(attempt/'resource_ledger.json'),
        pre_main_file=str(attempt/'pre_main_jobs.json'),batches_file=str(attempt/'inputs/BATCHES.json'),registry_file=str(attempt/'actual_checkpoint_registry.json'),
        B_index_file=str(attempt/'B_index.json'),episode_index_files=episode_indices,audit_result_files=audits,
        D_source_audit_files=source_audits,
        expected_totals=dict(totals)),paths)


def audit(job,out):
    ledger=read_json(job['ledger_file']);rows=ledger['jobs'];batches=read_json(job['batches_file'])
    registry=read_json(job['registry_file']);index=read_json(job['B_index_file'])
    if len({r['pair_id'] for r in rows})!=len(rows) or not all(r.get('accepted') is True for r in rows):
        raise ContractError('A declared job failed or was dispatched more than once')
    required={row['job']['pair_id'] for row in read_json(job['pre_main_file'])}
    def walk(value):
        if isinstance(value,dict):
            if 'work_id' in value:required.add(value['work_id'])
            if 'batch_id' in value and value.get('operation') in (
                    'evaluate_all_declared_candidates_in_list_order',
                    'full_shared_evaluation_of_new_admitted_public_catalog_subset'):
                required.add(value['batch_id'])
            for item in value.values():walk(item)
        elif isinstance(value,list):
            for item in value:walk(item)
    # Exact main work IDs are enumerated in the frozen B/C/D manifest. A jobs
    # have their own concrete IDs and are checked by the sealed pre-main list.
    for key in ('B_snapshots','C_transformations','D_episodes','D_n4_pair_audit'):
        walk(batches[key])
    observed={r['pair_id'] for r in rows}
    missing=required-observed
    if missing:raise ContractError('Missing main jobs: '+repr(sorted(missing)))
    extra=observed-required
    if extra:raise ContractError('Undeclared dispatched jobs: '+repr(sorted(extra)))
    if len(registry)!=35 or len(index)!=30 or len(job['episode_index_files'])!=5:
        raise ContractError('Incomplete source/decision/episode coverage')
    if sum(len(read_json(p)['decisions']) for p in job['episode_index_files'])!=30:
        raise ContractError('D did not actually make30 decisions')
    totals={k:sum(r.get(k,0) for r in rows) for k in ('real_wls','starts')}
    if totals!=job['expected_totals'] or totals!=ledger['totals']:
        raise ContractError('Final numerical ledger differs')
    if totals['real_wls']>25270 or totals['starts']>227430:
        raise ContractError('Frozen numerical budget exceeded')
    if sum(r['worker_cpu'] for r in rows)!=ledger['worker_cpu']:
        raise ContractError('Science CPU ledger does not sum')
    for path in job['audit_result_files']:
        value=read_json(path)
        if value.get('passed') is not True or value.get('all_episode_objectives_passed') is False:
            raise ContractError('A saved independent comparison/audit did not pass')
    expected_sources={c['source_audit']['work_id']:(e['episode_id'],c['tick'])
                      for e in batches['D_episodes'] for c in e['cuts']}
    source_files=job['D_source_audit_files']
    if len(source_files)!=35 or {r['pair_id'] for r in source_files}!=set(expected_sources):
        raise ContractError('Missing or duplicated D source/step comparison receipts')
    compared_steps=[]
    for source in source_files:
        value=read_json(source['result_file']);eid,tick=expected_sources[source['pair_id']]
        if (value.get('passed') is not True or (value.get('episode_id'),value.get('tick'))!=(eid,tick)
                or value.get('source_kind')!='NEW_COMMITTED_EXECUTION'):
            raise ContractError('D source audit identity or outcome differs')
        comparison=value.get('execution_step_comparison')
        if tick==0:
            if value.get('execution_step_compared') is not False or comparison is not None:
                raise ContractError('Initial cut cannot claim an actual execution-step comparison')
        else:
            if value.get('execution_step_compared') is not True or not isinstance(comparison,dict) or comparison.get('status')!='EQUAL':
                raise ContractError('A complete D execution step lacks strict comparison evidence')
            compared_steps.append(dict(episode_id=eid,start_tick=tick-20,end_tick=tick))
    if len(compared_steps)!=30:raise ContractError('All30 actual D segments, including final segments, are required')
    result=dict(passed=True,completed_jobs_before_final=len(rows),actual_cuts=35,
        D_decisions=30,B_snapshots=30,totals=totals,no_stable_speedup_claim=True,
        D_strict_execution_steps=compared_steps,
        evidence_scope='Saved declared deterministic work; no reliability or global optimum claim')
    save_json(Path(out)/'final_census.json',result);return result
