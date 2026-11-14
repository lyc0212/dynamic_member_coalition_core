"""Freeze inputs and run the bounded bridge acceptance in predeclared order."""
import ast
import copy
import json
import os
from pathlib import Path
import shutil
import shlex
import time
import traceback

from .common import CONTRACT_ID, digest, file_sha, save_json

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT/'examples/validate_stage2a5b_gq_bridge.py'
DESIGN = ROOT/'docs/STAGE2A5B_GQ_BRIDGE_DESIGN.json'
LOCK = ROOT/'docs/STAGE2A5B_GQ_BRIDGE_PROTOCOL_LOCK.json'
OLD = ROOT/'evidence/stage2a5b_a/attempt_538182597f57435cb7d5cc9ab727c87b/input_source_manifest.json'


def read(path):
    return json.loads(Path(path).read_text())


def protected():
    for name, wanted in read(LOCK)['files'].items():
        assert file_sha(ROOT/name)==wanted['sha256']
        assert (ROOT/name).stat().st_size==wanted['size']
    assert file_sha(OLD)=='97e6194cb6d92fdd505ab32978865333279d0fabb1db8cc8c0401a945c71fb6f'
    mismatches = [name for name,sha in read(OLD)['files'].items() if file_sha(ROOT/name)!=sha]
    assert not mismatches, mismatches
    return dict(passed=True, old_file_count=len(read(OLD)['files']), mismatches=mismatches)


def private_case(case):
    # Expected results and scripted decisions are never sent to environment/sense.
    return {key:copy.deepcopy(case[key]) for key in ('case_id','config','positions_initial','targets','disturbance') if key in case}


def actions(target, q=2):
    roles = ['dual_neg45','dual_pos45'] if q==2 else ['tri_0','tri_120','tri_240']
    return ([dict(target=target,role=role) for role in roles] +
            [dict(target=None,role='none') for _ in range(3-q)])


def steps_for(case):
    cid, q = case['case_id'], case['targets'][0]['required_robots']
    result = []
    for sec in range(6):
        active = sec <= (1 if cid in ('E1','E4') else 2)
        acts = actions(0,q) if active and cid.startswith('E') else [dict(target=None,role='none') for _ in range(3)]
        row = dict(request_id=f'{cid}-step-{20*sec}',expected_start_tick=20*sec,actions=acts)
        if cid=='E5' and sec==3:
            row['actions']=actions(1)
            row['preconditions']=[dict(path=['state_after',*path],equals=value) for path,value in (
                (['tick'],60),(['status',0],'completed'),(['status',1],'active'),
                (['last_assignment',0,'target'],None),(['last_assignment',1,'target'],None))]
        result.append(row)
    return result


def stream_id(aid, pair, target, tick):
    return f'{aid}:{pair}:target{target}:start{tick}'


def pair_job(aid, pair, payload, steps=None, streams=None, mode='science'):
    return dict(attempt_id=aid,pair_id=pair,env_start=payload,
                sense_start=dict(contract_id=CONTRACT_ID,mode=mode,streams=streams or []),
                controller_start=dict(steps=steps or []))


def prepare(attempt):
    if (attempt/'input_source_manifest.json').exists():
        raise FileExistsError('Frozen attempt already exists; never overwrite')
    protected()
    attempt.mkdir(parents=True,exist_ok=True)
    aid = attempt.name
    design = read(DESIGN)
    from .oracle import main_reference
    references = {}
    for case in design['cases']:
        ref = main_reference(case)
        for key in ('A_completion_tick','A_completion_time','control_integral',
                    'occupied_robot_seconds','assignment_changes','change_cost',
                    'return_without_changes','return_with_changes'):
            assert abs(ref[key]-case['expected'][key])<=1e-12, (case['case_id'],key)
        for key,value in ref['components'].items():
            assert abs(value-case['expected'][key])<=1e-12, (case['case_id'],key)
        references[case['case_id']]=ref
    save_json(attempt/'inputs/independent_reference.json',references)
    save_json(attempt/'inputs/design.json',design)
    save_json(attempt/'private_probe/expected.json',dict(expected='PRIVATE_EXPECTED_SENTINEL'))
    save_json(attempt/'private_probe/physical.json',dict(truth='PRIVATE_PHYSICAL_SENTINEL'))
    link = attempt/'private_probe/alias.json'
    link.symlink_to(attempt/'private_probe/expected.json')
    from .gate_probes import gate_jobs
    gates = gate_jobs(aid)
    jobs = []
    def add(job, phase, expected_failure=False):
        row = dict(job=job,phase=phase,expected_failure=expected_failure)
        jobs.append(row)
        save_json(attempt/'jobs'/f"{job['pair_id']}.json",row)
    for job in gates:
        add(job,'supervision')
    add(pair_job(aid,'runtime',dict(kind='runtime')),'runtime')
    from research.information_service.common import CONTRACT_ID as PUBLIC_ID
    positive = dict(frame=dict(contract_id=PUBLIC_ID,stream_id='isolation-positive',frame_id='positive-0',
        tick=0,target_id=0,measurement_time=0.,available_time=0.,records=[]),allowed_sensor_ids=['U0','U1'],start_tick=0)
    probes = [dict(action='read',target=str(path)) for path in (
        DESIGN, attempt/'private_probe/expected.json',attempt/'private_probe/physical.json',
        attempt/'private_probe/alias.json')]
    probes.append(dict(action='read',target=os.path.relpath(attempt/'private_probe/expected.json',ROOT)))
    probes.append(dict(action='import',target='research.information_service_bridge.private_probe'))
    add(pair_job(aid,'isolation',dict(kind='isolation',probes=probes,positive=positive),
        streams=[dict(stream_id='isolation-positive',target_id=0,start_tick=0,allowed_sensor_ids=['U0','U1'])],
        mode='isolation_probe'),'isolation')
    for label,extra in (('argv',{'sense_argv_extra':['--private-scenario','forbidden']}),
                        ('env',{'sense_env_extra':{'GQ_PRIVATE_SCENARIO':'forbidden'}})):
        job=pair_job(aid,'isolation_'+label,dict(kind='runtime'))
        job.update(predeclared_isolation_probe=True,**extra)
        add(job,'isolation_startup',True)
    add(pair_job(aid,'bridge_unit',dict(kind='unittest',modules=[
        'test_gq_bridge_public','test_gq_bridge_isolation','test_gq_bridge_environment'])), 'unit')
    for case in design['non_success_accounting_checks']:
        add(pair_job(aid,case['case_id'],dict(kind='science',case=private_case(case)),steps_for(case)), 'accounting')
    add(pair_job(aid,'accounting_audit',dict(kind='pre_main_audit',attempt=str(attempt))), 'accounting')
    add(pair_job(aid,'regressions',dict(kind='unittest',modules=[
        'test_information_service_public','test_information_service_clock','test_cooperative_sensing',
        'test_service_physics','test_service_reference','test_observation_geometry','test_service_three_robot'])), 'regression')
    for case in design['cases']:
        cid=case['case_id']
        streams=[]
        for target in case['targets']:
            first=0 if target['id']==0 else 60
            streams.append(dict(stream_id=stream_id(aid,cid,target['id'],first),target_id=target['id'],
                                start_tick=first,allowed_sensor_ids=[f'U{k}' for k in range(target['required_robots'])]))
        add(pair_job(aid,cid,dict(kind='science',case=private_case(case)),steps_for(case),streams), 'main')
    for case in design['cases'][:4]:
        add(pair_job(aid,case['case_id']+'_old_G',dict(kind='old_g',case=private_case(case))), 'old_g')
    add(pair_job(aid,'audit',dict(kind='audit',attempt=str(attempt))), 'audit')
    add(pair_job(aid,'plot',dict(kind='plot',attempt=str(attempt))), 'plot')
    save_json(attempt/'execution_plan.json',dict(contract_id=CONTRACT_ID,jobs=jobs,
        limits=dict(pair_cpu=60,pair_wall=120,total_cpu=300,total_wall=600,cleanup_reserve=5),
        commands=[shlex.join(['python3','-B',str(ENTRY),'prepare','--attempt',str(attempt)]),
                  shlex.join(['python3','-B',str(ENTRY),'run','--attempt',str(attempt)])],
        main_real_estimates=192,main_start_attempts=1728))
    files={}
    for base in ('research/information_service_bridge','research/information_service','research/cooperative_sensing',
                 'pursuit_v2','tests'):
        for path in (ROOT/base).rglob('*.py'):
            ast.parse(path.read_text())
            files[str(path.relative_to(ROOT))]=file_sha(path)
    for path in [ENTRY,DESIGN,LOCK,ROOT/'docs/STAGE2A5B_GQ_EXECUTION_BRIDGE_SPEC.md']:
        ast.parse(path.read_text()) if path.suffix=='.py' else None
        files[str(path.relative_to(ROOT))]=file_sha(path)
    for base in ('inputs','jobs','private_probe'):
        for path in (attempt/base).rglob('*'):
            if path.is_file():
                files[str(path.relative_to(ROOT))]=file_sha(path)
    files[str((attempt/'execution_plan.json').relative_to(ROOT))]=file_sha(attempt/'execution_plan.json')
    save_json(attempt/'input_source_manifest.json',dict(count=len(files),files=files))
    for name in files:
        destination=attempt/'frozen_sources'/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,destination)
    save_json(attempt/'preparation.json',dict(passed=True,kind='static and scalar reference preparation; no WLS/tests',
        manifest_sha256=file_sha(attempt/'input_source_manifest.json'),protection=protected()))
    return dict(prepared=str(attempt),frozen_files=len(files),jobs=len(jobs))


def check_frozen(attempt):
    for name,sha in read(attempt/'input_source_manifest.json')['files'].items():
        if file_sha(ROOT/name)!=sha:
            raise RuntimeError('Frozen source/input changed: '+name)


def run(attempt):
    if (attempt/'run.json').exists():
        raise FileExistsError('Attempt already executed; preserve it')
    check_frozen(attempt)
    from .guardian import run_pair
    from .gate_probes import validate_gate
    started=time.monotonic()
    cpu=0.
    records=[]
    error=None
    save_json(attempt/'run.json',dict(status='RUNNING',start_monotonic=started))
    try:
        for item in read(attempt/'execution_plan.json')['jobs']:
            check_frozen(attempt)
            job=item['job']
            print(json.dumps(dict(start=job['pair_id'],phase=item['phase'])),flush=True)
            out=attempt/'logs'/job['pair_id']
            result=run_pair(job,out,str(ENTRY),started+600,cpu)
            cpu+=result['scientific_cpu']
            if item['phase']=='supervision':
                gate=validate_gate(result,job)
                save_json(out/'gate_acceptance.json',gate)
                accepted=gate['passed']
            elif item['expected_failure']:
                log=(out/'sense/stdout_stderr.log').read_text()
                marker='--private-scenario' if job['pair_id'].endswith('_argv') else 'GQ_PRIVATE_SCENARIO'
                accepted=(not result['passed'] and result['accounting_complete'] and
                          result['all_reaped'] and marker in log)
            else:
                accepted=result['passed']
            row=dict(pair_id=job['pair_id'],phase=item['phase'],accepted=bool(accepted),result=result)
            records.append(row)
            save_json(attempt/'progress.json',dict(jobs=records,scientific_cpu=cpu,wall=time.monotonic()-started))
            print(json.dumps(dict(finished=job['pair_id'],accepted=bool(accepted),worker_cpu=cpu)),flush=True)
            if not accepted:
                raise RuntimeError('Gate/job failed: '+job['pair_id'])
        check_frozen(attempt)
        protected()
    except BaseException as exc:
        error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    result=dict(passed=error is None,status='PASS' if error is None else 'STOPPED',jobs=records,
                scientific_cpu=cpu,wall=time.monotonic()-started,error=error,
                protection_after=protected())
    save_json(attempt/'run.json',result)
    print(json.dumps(dict(passed=result['passed'],scientific_cpu=cpu,wall=result['wall'],error=error)),flush=True)
    return result


def dispatch(args):
    attempt=Path(args.attempt).resolve()
    if args.command=='prepare':
        print(json.dumps(prepare(attempt)),flush=True)
        return 0
    if args.command=='run':
        return 0 if run(attempt)['passed'] else 1
    raise ValueError('Use the verified result to author the final report')
