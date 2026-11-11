"""Local research execution, NOT production authentication or RUN admission.

No approval/budget is issued here. Engineering and actual modes require separate
explicit local approval records. Science is imported only by the Job worker.
Current-user governance is not a malicious-user/TOCTOU isolation boundary.
"""
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from research.non_oracle.stfbs_lite_real_d60_source import (
    AdmissionRejected, CATEGORIES, DurableJournal, DurableResourceLedger,
    _require, _dispatch_d60, guard_wls_bindings, inspect_attempt_journal,
    inspect_production_aliases, read_durable_journal, REQUIRED_SOURCE_PATHS,
)
from research.non_oracle.stfbs_lite_real_d60_supervisor_win import WindowsSupervisor, _seconds

ENGINEERING = 'LOCAL_DEV_ENGINEERING'
ACTUAL = 'LOCAL_DEV_ACTUAL_D60'
ARTIFICIAL = 'LOCAL_DEV_ENGINEERING_NOT_SCIENTIFIC_EVIDENCE'
STOP = 'POST_FREEZE_PRE_ASSIGNMENT_D60'
LOCAL_PATHS = frozenset(('research/non_oracle/stfbs_lite_local_dev.py',
    'scripts/run_stfbs_lite_local_dev.py', 'scripts/stfbs_lite_local_dev_worker.py'))


def digest_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_digest(value):
    _require(type(value) is str and len(value)==64 and all(c in '0123456789abcdefABCDEF' for c in value),
             'LOCAL_SHA256_INVALID')
    return value.lower()


def decode_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, 'DUPLICATE_JSON_KEY')
            result[key] = value
        return result
    def invalid(value):
        raise AdmissionRejected('NONFINITE_JSON')
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique, parse_constant=invalid)


def load_approval(path, expected_digest):
    raw = Path(path).read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == normalized_digest(expected_digest), 'LOCAL_APPROVAL_BYTES_CONFLICT')
    return decode_json(raw), raw


def validate_approval(record, repository, *, check_worktree=False):
    fields = {'schema', 'mode', 'execution_authorized', 'approval_reference', 'approved_by',
        'git_head', 'source_sha256', 'inputs', 'world_id', 'physical_environment_id',
        'run_id', 'attempt_id', 'runtime', 'budget', 'stop_rule', 'output_directory',
        'attempt_directory', 'overshoot_disposition'}
    _require(type(record) is dict and set(record) == fields, 'LOCAL_APPROVAL_FIELDS_INVALID')
    _require(record['schema'] == 'STFBS_LOCAL_DEV_APPROVAL_V1' and record['mode'] in (ENGINEERING, ACTUAL)
             and record['execution_authorized'] is True, 'EXPLICIT_LOCAL_EXECUTION_APPROVAL_REQUIRED')
    for name in ('approval_reference', 'approved_by', 'world_id', 'physical_environment_id', 'run_id', 'attempt_id'):
        _require(type(record[name]) is str and bool(record[name].strip()), 'LOCAL_IDENTITY_MISSING')
    _require(record['stop_rule'] == STOP and record['overshoot_disposition'] == 'FAIL_ATTEMPT',
             'LOCAL_STOP_OR_DISPOSITION_NOT_APPROVED')
    repository = Path(repository).resolve()
    head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=repository, text=True).strip()
    branch = subprocess.check_output(['git','branch','--show-current'], cwd=repository, text=True).strip()
    _require(head == record['git_head'] and branch == 'main', 'LOCAL_SOURCE_HEAD_CONFLICT')
    if check_worktree:
        dirty = subprocess.check_output(['git','status','--porcelain','--untracked-files=all'], cwd=repository, text=True)
        _require(not dirty.strip(), 'LOCAL_INITIAL_WORKTREE_DIRTY')
    required = REQUIRED_SOURCE_PATHS | LOCAL_PATHS
    _require(type(record['source_sha256']) is dict and required <= set(record['source_sha256']),
             'LOCAL_SOURCE_COVERAGE_INCOMPLETE')
    for relative, sha in record['source_sha256'].items():
        path = repository/relative
        _require(not Path(relative).is_absolute() and path.resolve().is_relative_to(repository), 'LOCAL_SOURCE_ESCAPE')
        _require(digest_file(path) == normalized_digest(sha), 'LOCAL_SOURCE_BYTES_CONFLICT')
    runtime = record['runtime']
    _require(set(runtime) == {'python', 'python_sha256', 'version', 'dependency_sha256'}
             and Path(runtime['python']).resolve() == Path(sys.executable).resolve()
             and runtime['version'] == sys.version and digest_file(runtime['python']) == normalized_digest(runtime['python_sha256']),
             'LOCAL_RUNTIME_CONFLICT')
    _require(type(runtime['dependency_sha256']) is dict and bool(runtime['dependency_sha256']),
             'LOCAL_DEPENDENCY_IDENTITY_REQUIRED')
    for path, sha in runtime['dependency_sha256'].items():
        _require(Path(path).is_absolute() and digest_file(path) == normalized_digest(sha), 'LOCAL_DEPENDENCY_BYTES_CONFLICT')
    budget = record['budget']
    _require(set(budget) == {'total_cpu_seconds', 'wall_seconds', 'wls', 'storage_bytes'}, 'LOCAL_BUDGET_MISSING')
    _seconds(budget['total_cpu_seconds'], cpu=True)
    _seconds(budget['wall_seconds'])
    _require(type(budget['storage_bytes']) is int and budget['storage_bytes'] > 0, 'LOCAL_STORAGE_BUDGET_INVALID')
    _require(set(budget['wls']) == set(CATEGORIES) and all(type(v) is int and v >= 0 for v in budget['wls'].values()),
             'LOCAL_WLS_BUDGET_INVALID')
    for name in ('output_directory','attempt_directory'):
        _require(Path(record[name]).is_absolute(), 'ABSOLUTE_LOCAL_DIRECTORY_REQUIRED')
    output = Path(record['output_directory']).resolve()
    attempts = Path(record['attempt_directory']).resolve()
    _require(output != attempts and not attempts.is_relative_to(output), 'LOCAL_DIRECTORY_CONFLICT')
    if record['mode'] == ACTUAL:
        _require(all(v > 0 for v in budget['wls'].values()) and set(record['inputs']) == {'world','public'},
                 'ACTUAL_INPUTS_AND_BUDGET_REQUIRED')
        for info in record['inputs'].values():
            _require(set(info) == {'path','sha256'} and Path(info['path']).is_absolute()
                     and digest_file(info['path']) == normalized_digest(info['sha256']), 'LOCAL_INPUT_BYTES_CONFLICT')
    else:
        _require(record['inputs'] == {} and all(v == 0 for v in budget['wls'].values()),
                 'ENGINEERING_MUST_HAVE_NO_SCIENCE_INPUT_OR_WLS')
    return record


def storage_usage(root):
    total = 0
    for path in Path(root).rglob('*'):
        _require(not path.is_symlink(), 'LOCAL_OUTPUT_LINK_REJECTED')
        if path.is_file():
            total += path.stat().st_size
    return total


def write_new(root, name, value, limit):
    payload = (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)+'\n').encode()
    write_bytes_new(root,name,payload,limit)


def write_bytes_new(root, name, payload, limit):
    _require(storage_usage(root)+len(payload) <= limit, 'LOCAL_STORAGE_EXHAUSTED')
    with (Path(root)/name).open('xb') as stream:
        _require(stream.write(payload) == len(payload), 'LOCAL_SHORT_WRITE')
        stream.flush()
        os.fsync(stream.fileno())


class LocalJournal(DurableJournal):
    def __init__(self, root, attempt_id, limit):
        self.root = Path(root)
        super().__init__(self.root/'worker.jsonl', attempt_id=attempt_id, max_bytes=limit)

    def append(self, event):
        from research.non_oracle.stfbs_lite_real_d60_source import content_digest
        row = dict(attempt_id=self.attempt_id, sequence=self.sequence+1, previous=self.previous, event=event)
        row['digest'] = content_digest(row)
        encoded = (json.dumps(row,sort_keys=True,separators=(',',':'))+'\n').encode()
        _require(storage_usage(self.root)+len(encoded) <= self.limit, 'LOCAL_STORAGE_EXHAUSTED')
        return super().append(event)


def process_identity(api, handle):
    api.k.GetProcessTimes.argtypes = [W.HANDLE]+[C.POINTER(W.FILETIME)]*4
    api.k.GetProcessTimes.restype = W.BOOL
    api.k.GetProcessId.argtypes = [W.HANDLE]
    api.k.GetProcessId.restype = W.DWORD
    times = [W.FILETIME() for _ in range(4)]
    api.check(api.k.GetProcessTimes(handle, *(C.byref(t) for t in times)), 'GetProcessTimes/LOCAL_DEV')
    return dict(pid=int(api.k.GetProcessId(handle)),
                creation_ticks=(times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)


def verify_local_job_handoff(record, handoff, approval_digest):
    """Local current-user governance, NOT independent IPC/authentication."""
    from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API
    api = API()
    _require(handoff['attempt_id'] == record['attempt_id'] and handoff['mode'] == record['mode']
             and handoff['approval_digest'] == approval_digest, 'LOCAL_HANDOFF_IDENTITY_CONFLICT')
    current = api.k.GetCurrentProcess()
    _require(process_identity(api,current) == handoff['worker'] and api.member(current,None),
             'LOCAL_WORKER_MUST_BE_IN_JOB')
    parent = api.k.OpenProcess(0x1000 | 0x100000,False,handoff['parent']['pid'])
    api.check(parent,'OpenProcess/LOCAL_PARENT')
    try:
        _require(process_identity(api,parent) == handoff['parent']
                 and api.k.WaitForSingleObject(parent,0) == 258, 'LOCAL_PARENT_NOT_LIVE')
    finally:
        api.close(parent)
    _require(handoff['parent_verified_target_job'] is True, 'LOCAL_PARENT_JOB_CHECK_MISSING')


class ArtificialEnvironment:
    """Full STEP signature, artificial state only; no scientific imports."""
    def __init__(self):
        self.tick = 0
    def prepare_decision(self):
        return {'tick':self.tick,'evidence_kind':ARTIFICIAL}
    def observe_public(self):
        return {'checkpoint_id':'ARTIFICIAL_D'+str(self.tick)}
    def step(self, actions, checkpoint_id, expected_start_tick, request_id, *, on_commit):
        _require(self.tick == expected_start_tick and checkpoint_id == self.observe_public()['checkpoint_id'],
                 'ARTIFICIAL_STEP_CONFLICT')
        start = self.tick
        on_commit({'tick':start,'evidence_kind':ARTIFICIAL})
        self.tick += 20
        return {'status':'COMMITTED','start_tick':start,'end_tick':self.tick,
                'checkpoint_after':{'tick':self.tick,'checkpoint_id':'ARTIFICIAL_D'+str(self.tick)},
                'evidence_kind':ARTIFICIAL}


def execute_worker_mode(record, journal, *, handoff=None, approval_digest=None):
    if record['mode'] == ENGINEERING:
        candidate = _dispatch_d60(ArtificialEnvironment(),
            decide=lambda view, method: {'actions':[{'target':None,'role':'none'}]*3},
            capture=lambda env,view: {'status':'LIVE_CUT_STRUCTURAL_CAPTURE_PASS','tick':view['tick'], 'evidence_kind':ARTIFICIAL},
            map_candidate=lambda cut: {'candidate_status':'MODEL_INITIALIZATION_CANDIDATE_READY',
                'execution_admission':'MODEL_EXECUTION_ADMISSION_DENIED','evidence_kind':ARTIFICIAL}, journal=journal)
        return candidate, {'scope':ARTIFICIAL,'counts':dict.fromkeys(CATEGORIES,0)}
    _require(record['mode'] == ACTUAL, 'LOCAL_MODE_INVALID')
    _require(handoff is not None and approval_digest is not None, 'LOCAL_ACTUAL_WORKER_CONTEXT_REQUIRED')
    verify_local_job_handoff(record,handoff,approval_digest)
    # These imports occur only after worker approval + Job checks.
    from research.non_oracle.environment import StaggeredEnvironment
    from scripts.run_a1 import Sensing
    from research.non_oracle import policy
    from research.information_service_bridge import public_stream
    from research.cooperative_sensing import estimator
    from research.non_oracle.stfbs_lite_live_cut import capture_live_cut
    from research.non_oracle.stfbs_lite_real_cut_to_model import prepare_real_cut_model_input
    import numpy
    import scipy
    runtime_pins = {str(Path(p).resolve()):normalized_digest(sha) for p,sha in record['runtime']['dependency_sha256'].items()}
    modules = {m.__name__:str(Path(m.__file__).resolve()) for m in (numpy,scipy)}
    _require(all(path in runtime_pins and digest_file(path)==runtime_pins[path] for path in modules.values()),
             'LOCAL_NUMERICAL_RUNTIME_NOT_PINNED')
    journal.append({'kind':'LOCAL_RUNTIME','numpy_version':numpy.__version__,
                    'scipy_version':scipy.__version__,'module_files':modules})
    inputs = {}
    for name, info in record['inputs'].items():
        raw = Path(info['path']).read_bytes()
        _require(hashlib.sha256(raw).hexdigest()==normalized_digest(info['sha256']), 'LOCAL_INPUT_CHANGED_BEFORE_READ')
        write_bytes_new(record['output_directory'], 'WORLD_INPUT.json' if name=='world' else 'PUBLIC_INPUT.json',
                        raw, record['budget']['storage_bytes'])
        inputs[name] = decode_json(raw)
    world, public = inputs['world'], inputs['public']
    _require(type(public) is dict and type(public.get('announcements')) is list, 'ANNOUNCEMENTS_LIST_REQUIRED')
    inspect_production_aliases()
    ledger = DurableResourceLedger(record['budget']['wls'], journal)
    class AuditedSensing(Sensing):
        def check_streams(self):
            verify_sensing_streams(self, public_stream)
        def __call__(self, *args, **kwargs):
            self.check_streams()
            result = super().__call__(*args, **kwargs)
            self.check_streams()
            return result
    with guard_wls_bindings(ledger,policy=policy,bridge=public_stream,estimator=estimator):
        sensing = AuditedSensing()
        env = StaggeredEnvironment(world,sensing,record['physical_environment_id'],public['announcements'])
        candidate = _dispatch_d60(env,decide=policy.decide,capture=capture_live_cut,
                                  map_candidate=prepare_real_cut_model_input,journal=journal)
        sensing.check_streams()
        _require(candidate.get('candidate_status') == 'MODEL_INITIALIZATION_CANDIDATE_READY', 'LOCAL_MAPPING_NOT_READY')
    return candidate, {'scope':'KNOWN_POLICY_OBSERVATION_SOLVER_BINDINGS_AND_DYNAMIC_SENSING_STREAMS',
                       'arbitrary_external_aliases':'NOT_PROVEN', 'counts':dict(ledger.counts)}


def verify_sensing_streams(sensing, public_stream):
    _require(all(p.estimator_fn is public_stream._estimate for p in sensing.streams.values()),
             'LOCAL_UNGUARDED_PROCESSOR_ALIAS')


def worker_main(approval_path, approval_digest, handoff_path, repository):
    record, _ = load_approval(approval_path,approval_digest)
    validate_approval(record,repository)
    handoff = decode_json(Path(handoff_path).read_bytes())
    verify_local_job_handoff(record,handoff,approval_digest)
    journal = LocalJournal(record['output_directory'],record['attempt_id'],record['budget']['storage_bytes'])
    try:
        journal.append({'kind':'LOCAL_WORKER_START','mode':record['mode'], 'approval_digest':approval_digest,
                        'attempt_id':record['attempt_id'], 'worker_pid':os.getpid(),
                        'evidence_kind':ARTIFICIAL if record['mode']==ENGINEERING else 'LOCAL_DEV_ACTUAL_NOT_SOURCE_AUTHENTICATED'})
        candidate, wls = execute_worker_mode(record,journal,handoff=handoff,approval_digest=approval_digest)
        journal.append({'kind':'LOCAL_WORKER_COMPLETE','mode':record['mode'],'tick':60,
                        'stop_rule':STOP,'candidate_status':candidate['candidate_status'], 'wls':wls,
                        'model_admission':'MODEL_EXECUTION_ADMISSION_DENIED'})
        return 0
    except BaseException as exc:
        try:
            journal.append({'kind':'LOCAL_WORKER_FAILED','type':type(exc).__name__,'message':str(exc)})
        except BaseException:
            pass  # Parent sees missing completion/truncated audit, never PASS.
        raise
    finally:
        journal.close()


def audit_local_result(record, result, rows, approval_digest, *, expected_worker_pid=None):
    _require(result.get('execution_entry') == 'RUN_MONITORED'
             and result.get('attempt_identity') == record['attempt_id']
             and result.get('job_cleanup_status') == 'PASS'
             and result.get('process_tree_status') == 'PROCESS_TREE_EXIT_CONFIRMED'
             and type(result.get('worker_exit_status')) is int and result['worker_exit_status'] == 0
             and result.get('cpu_semantics') == 'TOTAL_CPU_SECONDS' and result.get('cpu_scope') == 'WHOLE_JOB'
             and result.get('stop_reason') == 'NATURAL_EXIT'
             and result.get('accounting_status') == 'FINAL_VALID'
             and result.get('evidence_completeness_status') == 'COMPLETE_IN_MEMORY'
             and result.get('errors') == [], 'LOCAL_RESOURCE_OR_EXIT_INCOMPLETE')
    accounting = result.get('accounting')
    _require(type(accounting) is dict and all(type(accounting.get(k)) is int and accounting[k] >= 0
        for k in ('TotalUserTime','TotalKernelTime','ActiveProcesses')), 'LOCAL_FINAL_ACCOUNTING_MISSING')
    total = accounting['TotalUserTime']+accounting['TotalKernelTime']
    _require(type(result.get('final_cpu_ticks')) is int and type(result.get('total_cpu_ticks')) is int
             and accounting['ActiveProcesses'] == 0 and result.get('final_cpu_ticks') == total
             and result.get('total_cpu_ticks') == total, 'LOCAL_FINAL_ACCOUNTING_CONFLICT')
    _require(result.get('cpu_limit_ticks') == _seconds(record['budget']['total_cpu_seconds'],cpu=True)
             and result.get('wall_limit_seconds') == _seconds(record['budget']['wall_seconds'])
             and result.get('cpu_overshoot_ticks') == 0
             and total <= result['cpu_limit_ticks'], 'LOCAL_RESOURCE_LIMIT_OR_OVERSHOOT')
    elapsed = _seconds(result.get('wall_elapsed_at_tree_exit'))
    _require(elapsed <= record['budget']['wall_seconds'], 'LOCAL_WALL_OVERSHOOT')
    _require(type(result.get('supervisor_cpu_ticks')) is int and result['supervisor_cpu_ticks'] >= 0
             and 'EXCLUDED_FROM_JOB' in result.get('supervisor_cpu_scope',''), 'LOCAL_SUPERVISOR_CPU_AUDIT_MISSING')
    boundary = inspect_attempt_journal(rows)
    _require(boundary['last_complete_step'] == 60 and boundary['incomplete_transaction'] is None
             and not boundary['unfinished_calls'], 'LOCAL_D60_INCOMPLETE')
    starts = [r['event'] for r in rows if r['event']['kind']=='LOCAL_WORKER_START']
    finishes = [r['event'] for r in rows if r['event']['kind']=='LOCAL_WORKER_COMPLETE']
    _require(len(starts)==len(finishes)==1 and starts[0]['mode']==finishes[0]['mode']==record['mode']
             and starts[0]['approval_digest']==approval_digest and starts[0]['attempt_id']==record['attempt_id']
             and finishes[0]['stop_rule']==STOP, 'LOCAL_WORKER_IDENTITY_OR_COMPLETION_CONFLICT')
    _require(rows[0]['event']['kind']=='LOCAL_WORKER_START' and rows[-1]['event']['kind']=='LOCAL_WORKER_COMPLETE'
             and (expected_worker_pid is None or starts[0]['worker_pid']==expected_worker_pid),
             'LOCAL_WORKER_EVENT_ORDER_OR_PID_CONFLICT')
    steps = [(r['event']['start_tick'],r['event']['end_tick']) for r in rows if r['event']['kind']=='STEP_COMPLETE']
    _require(steps == [(0,20),(20,40),(40,60)], 'LOCAL_STEP_ORDER_CONFLICT')
    candidates = [r['event'] for r in rows if r['event']['kind']=='D60_CANDIDATE']
    _require(len(candidates)==1 and candidates[0]['candidate'].get('candidate_status')=='MODEL_INITIALIZATION_CANDIDATE_READY'
             and candidates[0]['candidate']['execution_admission']=='MODEL_EXECUTION_ADMISSION_DENIED',
             'LOCAL_MODEL_OR_CANDIDATE_CONFLICT')
    calls, completed, counts = {}, set(), dict.fromkeys(CATEGORIES,0)
    for row in rows:
        event=row['event']
        if event['kind']=='LOCAL_WORKER_FAILED':
            raise AdmissionRejected('LOCAL_WORKER_FAILED')
        if event['kind']!='WLS':
            continue
        call, category=event['call_id'], event['category']
        _require(category in counts, 'LOCAL_UNKNOWN_WLS_CATEGORY')
        if event['status']=='STARTED':
            _require(call not in calls, 'LOCAL_DUPLICATE_WLS_CALL')
            calls[call]=category
            counts[category]+=1
            _require(counts[category]<=record['budget']['wls'][category], 'LOCAL_WLS_EXCEEDED')
        else:
            _require(event['status']=='RETURNED' and calls.get(call)==category and call not in completed,
                     'LOCAL_WLS_FAILED_OR_CONFLICTING')
            completed.add(call)
    _require(set(calls)==completed and counts==finishes[0]['wls']['counts'], 'LOCAL_WLS_AUDIT_INCOMPLETE')
    if record['mode']==ENGINEERING:
        _require(not calls and starts[0]['evidence_kind']==ARTIFICIAL, 'LOCAL_ENGINEERING_SCIENCE_CONFLICT')
    return dict(boundary=boundary, wls_counts=counts, candidate=candidates[0]['candidate'])


def run_parent(approval_path, approval_digest, repository):
    """Only metadata and Win32 supervision here, never environment/decide/STEP."""
    record, raw=load_approval(approval_path,approval_digest)
    validate_approval(record,repository,check_worktree=True)
    output, store=Path(record['output_directory']), Path(record['attempt_directory'])
    _require(not output.exists(), 'LOCAL_OUTPUT_ALREADY_EXISTS')
    store.mkdir(parents=True,exist_ok=True)
    marker=store/(hashlib.sha256(record['attempt_id'].encode()).hexdigest()+'.consumed')
    payload=json.dumps({'attempt_id':record['attempt_id'],'run_id':record['run_id'],
        'approval_digest':approval_digest,'output':str(output),'status':'LOCAL_CONSUMED_NO_AUTOMATIC_RETRY'}).encode()
    # Local governance O_EXCL; no production ACL/durability claim.
    with marker.open('xb') as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    output.mkdir(parents=True,exist_ok=False)
    limit=record['budget']['storage_bytes']
    write_bytes_new(output,'approval.json',raw,limit)
    supervisor=None
    result=None
    try:
        supervisor=WindowsSupervisor(wall_seconds=record['budget']['wall_seconds'],
            total_cpu_seconds=record['budget']['total_cpu_seconds'],attempt_identity=record['attempt_id'])
        api=supervisor.api
        original_create=api.create
        def create(job,argv,cwd,env,log):
            pi=original_create(job,argv,cwd,env,log)
            try:
                _require(api.member(pi.hProcess,job),'LOCAL_TARGET_JOB_CONTAINMENT_FAILED')
                handoff=dict(attempt_id=record['attempt_id'],mode=record['mode'],approval_digest=approval_digest,
                    parent=process_identity(api,api.k.GetCurrentProcess()), worker=process_identity(api,pi.hProcess),
                    parent_verified_target_job=True, governance='CURRENT_USER_LOCAL_NOT_AUTHENTICATED_IPC')
                write_new(output,'handoff.json',handoff,limit)  # Before resume.
                return pi
            except BaseException:
                # The frozen start() exception path terminates its Job, including
                # this still-suspended member. Release handles not returned to it.
                for handle in (pi.hThread,pi.hProcess):
                    try: api.close(handle)
                    except BaseException: pass
                raise
        api.create=create  # Instance only; frozen supervisor/API files unchanged.
        worker=Path(repository)/'scripts/stfbs_lite_local_dev_worker.py'
        result=supervisor.run_monitored([record['runtime']['python'],'-B',str(worker),
            '--authorization',str(output/'approval.json'),'--approved-sha256',approval_digest,
            '--handoff',str(output/'handoff.json')],cwd=repository,log=output/'worker.log')
        # Handle closure errors must be reflected before success evaluation.
        supervisor.close()
        rows=read_durable_journal(output/'worker.jsonl',attempt_id=record['attempt_id'])
        handoff=decode_json((output/'handoff.json').read_bytes())
        audited=audit_local_result(record,result,rows,approval_digest,expected_worker_pid=handoff['worker']['pid'])
        outcome=dict(status='LOCAL_DEV_EXECUTION_COMPLETE',mode=record['mode'],run_id=record['run_id'],
            attempt_id=record['attempt_id'],job=result,audit=audited,
            evidence_kind=ARTIFICIAL if record['mode']==ENGINEERING else 'LOCAL_DEV_ACTUAL_R_POLICY_D60_PREFIX',
            source_authentication='NOT_VERIFIED',model_admission='MODEL_EXECUTION_ADMISSION_DENIED',
            scientific_gain='NOT_ESTABLISHED',production_run_admission='RUN_ADMISSION_BLOCKED',
            storage_scope='PREWRITE_JSON_AND_JOURNAL_PLUS_FINAL_TOTAL_CHECK_NOT_OS_DISK_QUOTA',retry_authorized=False)
        write_new(output,'success.json',outcome,limit)
        return outcome
    except BaseException as exc:
        if supervisor is not None:
            try: supervisor.close()
            except BaseException: pass
            result=supervisor.result
        failure=dict(status='LOCAL_DEV_FAILED_OR_INCOMPLETE',mode=record['mode'],attempt_id=record['attempt_id'],
            error={'type':type(exc).__name__,'message':str(exc)},job=result,
            retry_authorized=False,source_authentication='NOT_VERIFIED',model_admission='MODEL_EXECUTION_ADMISSION_DENIED')
        try:
            write_new(output,'failure.json',failure,limit)
        except BaseException as persist_error:
            failure['failure_evidence_persistence']='UNAVAILABLE: '+str(persist_error)
        return failure
    finally:
        if supervisor is not None:
            supervisor.close()
