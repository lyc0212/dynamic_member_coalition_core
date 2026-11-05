"""Budgeted live conformance gates, entered only by a formally dispatched G0/G1.

Importing this module does not construct a cache or invoke a scientific kernel.
The old walker is called only in G0, at the declared live measurement points.
"""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
import weakref

from .common import (CONTRACT, ROOT, MemoryAccountingError, check_pin, file_pin,
                     read_json, require, save_json, sha_file)


G0_IDS = tuple(f'G{i:02d}' for i in range(1, 15))
CAPS = dict(motion_kernel_entries=363, motion_kernel_returns=363,
            numpy_vector_update_calls=363, frozen_OLD_oracle_walks=576,
            live_membership_traversals=4, ledger_closure_inspections=8,
            metadata_size_traversals=8, WLS_calls=0, start_attempts=0)


def _code(error):
    return getattr(error, 'code', None) or str(error).split(':', 1)[0]


def _typed_equal(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is list:
        return len(left)==len(right) and all(_typed_equal(a,b) for a,b in zip(left,right))
    if type(left) is dict:
        return set(left)==set(right) and all(_typed_equal(left[k],right[k]) for k in left)
    return left==right


def _read(job, field):
    return _read_path(job,job[field])


def _read_path(job, value):
    path = str(Path(value).resolve())
    pin = job.get('source_pins', {}).get(path)
    require(type(pin) is dict, 'GATE_EXTERNAL_PIN_REQUIRED', path)
    check_pin(pin)
    return read_json(path)


def _identity(job):
    from .wiring import process_identity
    identity = process_identity()
    return dict(attempt_id=job['gate_identity']['attempt_id'], pair_id='G0', run_id='G0',
                condition='NEW', execution_source_seal_sha256=job['expected_source_seal_sha256'], **identity)


def _roots(owner):
    return (owner._components, owner._trace, owner._initial_positions, owner._targets)


def _members(roots):
    """One explicitly budgeted membership traversal, never a byte oracle."""
    seen = set()
    pending = list(roots)
    while pending:
        node = pending.pop()
        marker = id(node)
        if marker in seen:
            continue
        seen.add(marker)
        if type(node) is dict:
            for key, value in node.items():
                pending.extend((key, value))
        elif type(node) in (tuple, list):
            pending.extend(node)
    return seen


class _Session:
    def __init__(self, job, out):
        self.job, self.out = job, Path(out)
        self.out.mkdir(parents=True, exist_ok=True)
        self.counts = {key: 0 for key in CAPS}
        self.cases = []
        self.pairs = {}
        self.checkpoints = []
        self.macro_trace = None
        self.macro_records = None
        self.macro_binding = None
        self._old_peak = {}

    def count(self, key, amount=1):
        self.counts[key] += amount
        require(self.counts[key] <= CAPS[key], 'GATE_WORK_CAP_EXCEEDED', key,
                observed=self.counts[key], maximum=CAPS[key])

    def persist(self, *, failure=False):
        value=dict(cases=self.cases, paired_observations=self.pairs,
                   space_checkpoints=self.checkpoints)
        if failure:
            value.update(actual_work_counters=None,work_counter_settlement_complete=False,
                known_collected_work_lower_bound=dict(self.counts),
                counter_evidence_limit='Cache motion counters are normally collected at case completion. '
                    'An interrupted case may have incurred uncollected motion work; collected zero is not exact zero.',
                unknown_or_missing_evidence=['complete failed-case work-counter settlement'])
        else:
            value['actual_work_counters']=self.counts
        save_json(self.out / 'gate_actuals.json',value)

    def case(self, identifier, actual, expected, passed):
        row = dict(id=identifier, actual=actual, expected=expected, passed=bool(passed))
        self.cases.append(row)
        self.persist()
        require(passed, 'GATE_CONFORMANCE_FAILED', identifier, actual=actual, expected=expected)
        return row

    def pair(self, case, owner, info):
        from research.information_service_shared.motion_cache import MotionComponentCache
        self.count('frozen_OLD_oracle_walks')
        old = MotionComponentCache._allocated_bytes(owner)
        previous = self._old_peak.get(case, 0)
        peak = max(previous, old)
        self._old_peak[case] = peak
        row = deepcopy(info)
        row.update(old_current_bytes=old, old_peak_bytes=peak,
                   actual_root_ids=[id(value) for value in _roots(owner)],
                   same_live_owner_id=id(owner))
        self.pairs.setdefault(case, []).append(row)
        # Persist actual values before making an equality assertion.
        with (self.out / 'paired_observations.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(case=case, **row), allow_nan=False) + '\n')
        require(type(info['current_bytes']) is int and info['current_bytes'] == old,
                'MEM_LIVE_VALUE_MISMATCH', case)
        require(owner._peak_cache_bytes == peak and info['peak_after_bytes'] == peak,
                'MEM_LIVE_PEAK_MISMATCH', case)

    def motion(self, cache):
        observed = cache.instrumentation()
        for target, source in (('motion_kernel_entries','compute_entries'),
                               ('motion_kernel_returns','compute_returns'),
                               ('numpy_vector_update_calls','numpy_vector_update_calls')):
            self.count(target, observed[source])
        return observed


def _unit_factory(job):
    from research.information_service_shared import contracts
    public_request = _read(job, 'request_file')
    capability = contracts.make_unit_fixture('MEMORY_G0_PUBLIC_BOUND_UNIT', public_request)
    flat = capability.request
    require(flat['start_tick'] == 20 and flat['prediction_end_tick'] == 80 and
            flat['config']['robots'] == 4 and flat['config']['task_count'] == 3,
            'GATE_PUBLIC_PHYSICAL_INPUT')

    def scope(case):
        identity = dict(job['gate_identity'])
        identity.update(batch_id='G0:' + case, cache_instance_id='G0:' + case + ':cache')
        return contracts.make_scope(flat, unit_fixture=capability, **identity)
    return capability, flat, scope


def _wiring_metadata():
    """Actual runtime binding facts; no initializer/evaluator/cache scan runs."""
    from research.information_service_shared import evaluator as frozen
    from research.information_service_shared.motion_cache import MotionComponentCache as Old
    from . import wiring
    original=wiring.evaluate_candidate_for('OLD')
    clone=wiring.evaluate_candidate_for('NEW')
    probe=Old.__new__(Old)
    reference=weakref.ref(probe)
    weak_supported=reference() is probe and type(probe) is Old
    probe_id=id(probe)
    del probe
    weak_released=reference() is None
    differences=[key for key in set(original.__globals__)|set(clone.__globals__)
                 if key not in original.__globals__ or key not in clone.__globals__ or
                 original.__globals__[key] is not clone.__globals__[key]]
    actual=dict(old_exact_class_weakref_supported=weak_supported,
        uninitialized_weakref_probe_id=probe_id,weak_owner_released=weak_released,
        cache_initializers_called=0,extra_cache_measurements=0,
        OLD_function_is_original=original is frozen.evaluate_candidate,
        original_global_class_is_OLD=original.__globals__['MotionComponentCache'] is Old,
        new_global_class_is_exact_NEW=clone.__globals__['MotionComponentCache'] is wiring.MotionComponentCache,
        clone_code_is_original=clone.__code__ is original.__code__,
        clone_private_globals=clone.__globals__ is not original.__globals__,
        functional_global_binding_differences=sorted(differences),
        defaults_identity_preserved=clone.__defaults__ is original.__defaults__,
        kwdefaults_identity_preserved=clone.__kwdefaults__ is original.__kwdefaults__,
        closure_identity_preserved=clone.__closure__ is original.__closure__,
        old_record_descriptor_preserved=Old._record is wiring._ORIGINAL_RECORD,
        old_allocated_descriptor_preserved=Old._allocated_bytes is wiring._ORIGINAL_ALLOCATED,
        metadata_names=dict(original_module=original.__module__,clone_module=clone.__module__,
                            original_qualname=original.__qualname__,clone_qualname=clone.__qualname__))
    passed=all(actual[key] is True for key in (
        'old_exact_class_weakref_supported','weak_owner_released','OLD_function_is_original',
        'original_global_class_is_OLD','new_global_class_is_exact_NEW','clone_code_is_original',
        'clone_private_globals','defaults_identity_preserved','kwdefaults_identity_preserved',
        'closure_identity_preserved','old_record_descriptor_preserved','old_allocated_descriptor_preserved'))
    return actual,passed and differences==['MotionComponentCache']


def _exact_type_refusals(session, cache, capability, request):
    """Call the actual frozen/clone entries and stop at their first statement."""
    from research.information_service_shared.common import ContractError
    from research.information_service_shared.motion_cache import MotionComponentCache as Old
    from . import wiring
    original=wiring.evaluate_candidate_for('OLD');clone=wiring.evaluate_candidate_for('NEW')
    class NewSubclass(wiring.MotionComponentCache):
        pass
    class OldSubclass(Old):
        pass
    inputs=[('OLD_rejects_NEW',original,cache),
            ('NEW_rejects_OLD',clone,Old.__new__(Old)),
            ('NEW_rejects_NEW_subclass',clone,NewSubclass.__new__(NewSubclass)),
            ('NEW_rejects_unrelated',clone,object()),
            ('OLD_rejects_OLD_subclass',original,OldSubclass.__new__(OldSubclass))]
    canaries=dict(sense_calls=0,on_commit_calls=0,on_ownership_calls=0)
    def forbidden_sense(*args,**kwargs):
        canaries['sense_calls']+=1
        raise MemoryAccountingError('EXACT_TYPE_REACHED_SENSING')
    def forbidden_commit(*args,**kwargs):
        canaries['on_commit_calls']+=1
        raise MemoryAccountingError('EXACT_TYPE_REACHED_COMMIT')
    def forbidden_ownership(*args,**kwargs):
        canaries['on_ownership_calls']+=1
        raise MemoryAccountingError('EXACT_TYPE_REACHED_OWNERSHIP')
    # The admitted capability supplies a real original descriptor; rejection
    # must precede request/scope/history admission and candidate initialization.
    spec=capability.manifest['candidates'][8]
    observed=[]
    for name,function,wrong_cache in inputs:
        exception_type=None;message=None;terminal=None;exception_class_ok=False
        try:
            function(request,spec,forbidden_sense,cache=wrong_cache,unit_fixture=capability,
                     on_commit=forbidden_commit,on_ownership=forbidden_ownership)
        except BaseException as error:
            exception_type=type(error).__name__;message=str(error)
            exception_class_ok=type(error) is ContractError
            trace=error.__traceback__
            while trace.tb_next is not None:
                trace=trace.tb_next
            terminal=dict(filename=trace.tb_frame.f_code.co_filename,line=trace.tb_lineno,
                          function=trace.tb_frame.f_code.co_name,
                          same_original_code=trace.tb_frame.f_code is original.__code__)
        row=dict(name=name,cache_exact_type=type(wrong_cache).__qualname__,
                 actual_exception_type=exception_type,actual_message=message,
                 terminal_frame=terminal,callback_canaries=dict(canaries),
                 expected_exception_type='ContractError',expected_message='Production motion cache required')
        observed.append(row)
        save_json(session.out/'G0_exact_type_refusals.json',observed)
        require(exception_class_ok and message=='Production motion cache required' and
                terminal is not None and terminal['same_original_code'] is True and
                terminal['line']==original.__code__.co_firstlineno+3 and not any(canaries.values()),
                'G0_EXACT_TYPE_GATE_FAILED',actual=row)
    return dict(passed=True,cases=observed,initializer_admission_reached=False,
                stop_proof='Actual ContractError terminal frame is the unchanged first exact-type statement',
                actual_constructor_count=0,extra_motion=0,extra_old_oracle=0)


def _make(session, case, capability, request, scope_factory, *, on_trace=None,
          buffered=None, measurement=None, measurement_override=None):
    from . import wiring
    scope = scope_factory(case)
    def paired(owner, info):
        session.pair(case, owner, info)
        if measurement is not None:
            measurement(owner, info)
    options=dict(on_trace=on_trace, observer_binding=_identity(session.job), gate_mode=True,
        gate_measurement_callback=paired, gate_buffered_callback=buffered)
    if measurement_override is not None:
        options['gate_measurement_override']=measurement_override
    return wiring.make_cache('NEW', scope, request, unit_fixture=capability,**options)


def _pure_pair(session, case, meter, roots, changes=()):
    from research.information_service_shared.motion_cache import MotionComponentCache
    current = meter.measure_unit_graph(roots, changes=changes)
    session.count('frozen_OLD_oracle_walks')
    owner = SimpleNamespace(_components=roots[0], _trace=roots[1],
                            _initial_positions=roots[2], _targets=roots[3])
    old = MotionComponentCache._allocated_bytes(owner)
    previous = session._old_peak.get(case, 0)
    peak = max(previous, old)
    session._old_peak[case] = peak
    snapshot = meter.snapshot()
    row = dict(current_bytes=current, old_current_bytes=old,
               old_peak_bytes=peak, meter_snapshot=snapshot,
               actual_root_ids=[id(item) for item in roots])
    session.pairs.setdefault(case, []).append(row)
    session.persist()
    require(type(current) is int and current == old, 'MEM_LIVE_VALUE_MISMATCH', case)
    require(snapshot.get('peak_bytes') == peak, 'MEM_LIVE_PEAK_MISMATCH', case)
    return row


def _metadata_gates(session, owner, info, label):
    from .meter import audit_detached_metadata
    from .wiring import observer_for
    observer = observer_for(owner)
    session.count('live_membership_traversals')
    source_ids = _members(_roots(owner))
    source_ids.add(id(owner))
    session.count('ledger_closure_inspections')
    detached = audit_detached_metadata(observer.persistent_payload(), source_ids)
    checkpoint = observer.space_checkpoint(label)
    session.count('metadata_size_traversals', 2)
    checkpoint.update(detachment=detached, source_node_count=len(source_ids),
        measurement_index=info['measurement_index'],event_index=info['event_index'],
        scope_and_producer_binding=observer.snapshot()['binding'])
    session.checkpoints.append(checkpoint)
    session.persist()
    for field in ('ledger_metadata_checkpoint_bytes','measurement_buffer_checkpoint_bytes',
                  'ledger_node_count','ledger_edge_count','pending_update_count'):
        require(type(checkpoint.get(field)) is int and checkpoint[field] >= 0,
                'GATE_SPACE_EVIDENCE_MISSING', field)
    require(detached.get('passed') is True, 'IDENTITY_LIFETIME_ASSURANCE_FAILED')
    # Four actual forbidden payloads, one per checkpoint, inspected against these
    # same actual live-node ids; no additional source graph walk is made.
    index = len(session.checkpoints) - 1
    if index == 0:
        forbidden = owner._components
    elif index == 1:
        forbidden = next(iter(owner._components))
    elif index == 2:
        forbidden = next(iter(owner._components.values()))['prefix_digest']
    else:
        forbidden = lambda: owner._components
    session.count('ledger_closure_inspections')
    error = None
    try:
        audit_detached_metadata({'forbidden': forbidden}, source_ids)
    except BaseException as observed:
        error = _code(observed)
    checkpoint['forbidden_payload_actual'] = dict(code=error, fixture_index=index)
    session.persist()
    require(error == 'IDENTITY_LIFETIME_ASSURANCE_FAILED',
            'GATE_FORBIDDEN_PAYLOAD_ACCEPTED', observed=error)


def _run_macro(session, job, capability, request, scope_factory):
    from .wiring import observer_for, detach
    sequence = _read(job, 'gate_sequence_file')
    observed_labels = set()
    def checkpoint(owner, info):
        kind = info['event_kind']
        label = {'CREATED':'CREATED','INTERVAL_BUILT':'FIRST_BUILD',
                 'INTERVAL_HIT':'FIRST_HIT','CLOSED':'CLOSED'}.get(kind)
        token=None if label is None else label.encode('utf-8')
        if token is not None and token not in observed_labels:
            observed_labels.add(token)
            _metadata_gates(session, owner, info, label)
    cache = _make(session, 'G02', capability, request, scope_factory, buffered=checkpoint)
    try:
        exact_types=_exact_type_refusals(session,cache,capability,request)
        for operation in sequence['operations'][1:]:
            if operation['operation'] == 'get_interval':
                cache.get_interval(**operation['arguments'], expected_scope_id=cache.full_scope_id)
            elif operation['operation'] == 'close':
                cache.close()
            else:
                raise MemoryAccountingError('UNDECLARED_G0_OPERATION')
        trace = cache.trace_records()
        instrumentation = session.motion(cache)
        diagnostic = cache.snapshot_diagnostics()
        observer = observer_for(cache)
        receipt = observer.finalize(session.out / 'G02')
        snapshot = observer.snapshot()
        session.macro_trace = json.loads(json.dumps(trace,allow_nan=False))
        session.macro_records = deepcopy(session.pairs['G02'])
        session.macro_binding = deepcopy(snapshot['binding'])
        actual = dict(trace_events=len(trace), event_histogram=dict(Counter(r['event'] for r in trace)),
            measurements=len(session.pairs['G02']), counters=diagnostic['counters'],
            component_instances=diagnostic['component_instances'], instrumentation=instrumentation,
            sidecar_receipt=receipt, meter_snapshot=snapshot,exact_type_entry_refusals=exact_types)
        expected = dict(trace_events=482, measurements=482, component_instances=6,
            event_histogram=dict(CREATED=1,INTERVAL_BUILT=360,INTERVAL_HIT=120,CLOSED=1))
        passed = (len(trace)==482 and len(session.pairs['G02'])==482 and
            actual['event_histogram']==expected['event_histogram'] and
            diagnostic['component_instances']==6 and diagnostic['counters']['accepted_interval_requests']==480 and
            diagnostic['counters']['new_computed_intervals']==360 and diagnostic['counters']['cache_hit_requests']==120 and
            all(instrumentation[key]==360 for key in ('compute_entries','compute_returns','numpy_vector_update_calls')) and
            len(session.checkpoints)==4 and receipt['completed'] is True)
        session.case('G02',actual,expected,passed)
        session.case('G07',dict(checkpoints=session.checkpoints,
                     final_file_bytes=receipt['sidecar_pin']['size_bytes'],
                     maximum_label='checkpoint_max_only_not_continuous_peak'),
                     dict(checkpoints=4,inspections=8,metadata_size_walks=8),len(session.checkpoints)==4)
    finally:
        detach(cache)


def _run_pure_graphs(session):
    import numpy as np
    from .meter import FourRootMeter
    shared=[1.25,2.5];distinct=[1.25,2.5]
    roots=({'shared':shared},[shared],[],{'distinct':distinct})
    meter=FourRootMeter(scope_id='G0:G03')
    _pure_pair(session,'G03',meter,roots)
    session.case('G03',dict(shared_identity=id(roots[0]['shared'])==id(roots[1][0]),
                 distinct_identity=id(shared)!=id(distinct)),dict(alias=True,distinct=True),
                 roots[0]['shared'] is roots[1][0] and shared is not distinct)
    seq=[];mapping={};roots=(mapping,seq,[],{})
    meter=FourRootMeter(scope_id='G0:G04')
    _pure_pair(session,'G04',meter,roots)
    for i in range(33):
        meter.controlled_transition(roots,'append',seq,value=float(i)+.125)
        _pure_pair(session,'G04',meter,roots,changes=(seq,))
    for i in range(22):
        meter.controlled_transition(roots,'dict_add',mapping,key='item_'+str(i),value=i+.25)
        _pure_pair(session,'G04',meter,roots,changes=(mapping,))
    session.case('G04',dict(points=len(session.pairs['G04']),list_length=len(seq),dict_length=len(mapping)),
                 dict(points=56,list_length=33,dict_length=22),len(session.pairs['G04'])==56)
    # A permitted edge name with no immutable trace retention must fail before
    # replacement; all other destructive operations are outside the channel.
    part={'prefix_digest':''.join(('unique','_old_digest')),'intervals':[]}
    component={'part':part};trace=[];array=np.zeros((4,2),dtype=np.float64)
    roots=(component,trace,array,{})
    meter=FourRootMeter(scope_id='G0:G06');_pure_pair(session,'G06',meter,roots)
    attempts=[('prefix_digest_replace',part,'prefix_digest','new_digest'),
              ('clear',component,None,None),('clear',trace,None,None),
              ('delete',component,'part',None),('overwrite',part,'intervals',[]),
              ('array_replace',array,None,np.ones((4,2),dtype=np.float64))]
    actual=[]
    for index,(operation,container,key,value) in enumerate(attempts):
        before=meter.snapshot();code=None
        try:meter.controlled_transition(roots,operation,container,key=key,value=value)
        except BaseException as error:code=_code(error)
        after=meter.snapshot()
        actual.append(dict(operation=operation,code=code,before=before,after=after))
        save_json(session.out/'G06_refusal_actuals.json',actual)
        _pure_pair(session,'G06',meter,roots)
        require(code==('LAST_ROOT_REFERENCE_REMOVAL_UNSUPPORTED' if index==0 else
                       'UNSUPPORTED_OWNED_GRAPH_MUTATION'), 'GATE_WRONG_MUTATION_REFUSAL',actual=actual[-1])
        require(before==after,'GATE_REFUSED_MUTATION_CHANGED_LEDGER')
    session.case('G06',actual,dict(refusals=6,paired_points=7),len(actual)==6)
    ids=[];snapshots=[];disposals=[]
    for i in range(16):
        mutable=[];roots=({},mutable,[],{})
        meter=FourRootMeter(scope_id='G0:G08:'+str(i))
        _pure_pair(session,'G08_scope_'+str(i),meter,roots)
        ids.append(id(mutable));snapshots.append(meter.snapshot())
        meter.dispose();disposals.append(meter.snapshot())
        require(disposals[-1]['disposed'] is True and disposals[-1]['node_count']==0,
                'G08_SCOPE_STATE_NOT_DESTROYED')
        del meter,roots,mutable
    session.case('G08',dict(actual_mutable_ids=ids,
        actual_reuse_observation='OBSERVED' if len(set(ids))<16 else 'NOT_OBSERVED',
        synthetic_keys=[['UNIT_SCOPE_A',1,1001],['UNIT_SCOPE_B',1,1001]],
        snapshots=snapshots,disposals=disposals,allocation_retries=0),
        dict(fresh_scopes=16,cross_scope_memo=False),
        len(snapshots)==16 and all(row['initialization_walks']==1 for row in snapshots) and
        len({row['scope_generation'] for row in snapshots})==16 and
        ['UNIT_SCOPE_A',1,1001]!=['UNIT_SCOPE_B',1,1001])
    own=np.arange(8,dtype=np.float64).reshape((4,2)).copy();target=np.array([1.,2.])
    roots=({},[],own,{'target':target,'alias':target,'view':own[:,0]})
    meter=FourRootMeter(scope_id='G0:G09');first=_pure_pair(session,'G09',meter,roots)
    external=[]
    for i in range(8):external.append(dict(detached_record=i,current_bytes=first['current_bytes']))
    second=_pure_pair(session,'G09',meter,roots)
    session.case('G09',dict(first=first['current_bytes'],second=second['current_bytes'],external_records=len(external)),
                 dict(external_records=8,statistic_unchanged=True),first['current_bytes']==second['current_bytes'])


def _run_cache_micros(session, capability, request, scope_factory):
    from .wiring import observer_for, detach
    cache=_make(session,'G05',capability,request,scope_factory)
    try:
        cache.get_interval(0,1,'dual_neg45',20,cache.full_scope_id)
        old=cache._components[(0,1,'dual_neg45')]['prefix_digest']
        old_id=id(old)
        cache.get_interval(0,1,'dual_neg45',21,cache.full_scope_id)
        retained=any(row['component_prefix_after'] is not None and
            row['component_prefix_after']['prefix_digest'] is old for row in cache._trace)
        # Prefix-state deepcopy may preserve the immutable exact string identity;
        # this is observed directly, not inferred from equal digest contents.
        cache.close();motion=session.motion(cache)
        actual=dict(old_digest_id=old_id,retained_by_actual_trace=retained,points=len(session.pairs['G05']),motion=motion)
        session.case('G05',actual,dict(retained=True,points=4,motion=2),retained and len(session.pairs['G05'])==4)
    finally:detach(cache)
    injected=RuntimeError('G10_DECLARED_CALLBACK_FAILURE')
    def fail_build(row):
        if row['event']=='INTERVAL_BUILT':raise injected
    cache=_make(session,'G10',capability,request,scope_factory,on_trace=fail_build)
    try:
        observed=None
        try:cache.get_interval(0,1,'dual_neg45',20,cache.full_scope_id)
        except BaseException as error:observed=error
        after_failure=observer_for(cache).snapshot();trace_after=cache.trace_records()
        cache.close();after_close=observer_for(cache).snapshot();motion=session.motion(cache)
        rows=session.pairs['G10']
        actual=dict(exception_type=type(observed).__name__,same_exception=observed is injected,
            after_failure=after_failure,after_cleanup_close=after_close,failed_event_index=1,
            trace_after_failure=trace_after,trace=cache.trace_records(),paired=rows,motion=motion)
        session.case('G10',actual,dict(trace_events=3,measurements=2,failed_measurements=0,motion=1),
            observed is injected and len(trace_after)==2 and len(cache._trace)==3 and len(rows)==2 and
            [row['event_index'] for row in rows]==[0,2] and
            rows[-1]['absorbed_event_indices']==[1,2])
    finally:detach(cache)
    injected=RuntimeError('G11_DECLARED_CLOSE_CALLBACK_FAILURE')
    def fail_close(row):
        if row['event']=='CLOSED':raise injected
    cache=_make(session,'G11',capability,request,scope_factory,on_trace=fail_close)
    try:
        observed=None
        try:cache.close()
        except BaseException as error:observed=error
        before=observer_for(cache).snapshot();count=len(cache._trace);cache.close()
        after=observer_for(cache).snapshot();motion=session.motion(cache)
        session.case('G11',dict(same_exception=observed is injected,before=before,after=after,
            trace_events=len(cache._trace),missing_first_close_sample=True,motion=motion),
            dict(trace_events=2,measurements=1,second_close_changes=False),
            observed is injected and count==len(cache._trace)==2 and before==after and len(session.pairs['G11'])==1)
    finally:detach(cache)
    # Buffer failure is installed post-peak at CREATED, before its real append.
    faults=[]
    for stage in ('buffer_append','batch_flush'):
        case='G12_'+stage;injected=RuntimeError('G12_'+stage);captured={}
        def arm(owner, info):
            captured.update(owner_ref=weakref.ref(owner),actual_peak=owner._peak_cache_bytes,
                            observed_measurement=deepcopy(info))
            if stage=='buffer_append':observer_for(owner).inject_failure(stage,injected)
        cache=None;observed=None
        try:
            cache=_make(session,case,capability,request,scope_factory,measurement=arm)
            observer_for(cache).inject_failure(stage,injected)
            observer_for(cache).finalize(session.out/case)
        except BaseException as error:
            observed=error
        finally:
            owner=captured.pop('owner_ref',lambda:None)()
            if owner is not None:
                captured.update(snapshot=observer_for(owner).snapshot(),actual_peak_after=owner._peak_cache_bytes)
                session.motion(owner);detach(owner)
            # No compensating close: the after-peak failure is terminal.
            del owner,cache
        actual=dict(stage=stage,code=None if observed is None else _code(observed),
                    exception_details=getattr(observed,'details',{}),captured=captured,
                    compensating_closes=0)
        faults.append(actual);session.persist()
        save_json(session.out/'G12_failure_actuals.json',faults)
        require(actual['code']=='MEASUREMENT_SIDECAR_WRITE_FAILED_AFTER_PEAK',
                'GATE_SIDECAR_FAILURE_NOT_RETAINED',actual=actual)
        failure=actual['exception_details']
        require(failure.get('actual_peak_preserved') is True and failure.get('failed') is True and
                failure.get('successful_measurement_count')==1 and
                failure.get('buffered_record_count')==(0 if stage=='buffer_append' else 1) and
                failure.get('durably_persisted_count') is None and
                failure.get('peak_bytes')==captured['observed_measurement']['peak_after_bytes'] and
                failure.get('current_bytes')==captured['observed_measurement']['current_bytes'] and
                failure.get('skip_cache_logging_close') is True,
                'GATE_SIDECAR_FAILURE_FACTS',actual=actual)
    session.case('G12',faults,dict(failures=2,peak_rollback=False,compensating_closes=0),len(faults)==2)
    invalid=[]
    for index,value in enumerate((True,None,-1,RuntimeError('G13_DECLARED_MEASUREMENT_FAILURE'))):
        code=None;failure_details={};unexpected_cache=None;exception_identity=None
        def measured_value():
            if isinstance(value,BaseException):
                raise value
            return value
        try:
            unexpected_cache=_make(session,'G13_'+str(index),capability,request,scope_factory,
                                   measurement_override=measured_value)
        except BaseException as error:
            code=_code(error);failure_details=getattr(error,'details',{})
            if isinstance(value,BaseException):
                exception_identity=error.__cause__ is value
        finally:
            if unexpected_cache is not None:
                detach(unexpected_cache)
        supplied=dict(type=type(value).__name__,value=value) if not isinstance(value,BaseException) else \
                 dict(type='predeclared_exception',exception_type=type(value).__name__,message=str(value))
        actual=dict(input=supplied,input_type=type(value).__name__,actual_code=code,
                    exception_identity_preserved=exception_identity,
                    constructor_actuals=failure_details,compensating_closes=0)
        invalid.append(actual);save_json(session.out/'G13_boundary_actuals.json',invalid)
        require(code=='MEM_INVALID_MEASUREMENT','GATE_INVALID_MEASUREMENT_ACCEPTED',actual=actual)
        require(not isinstance(value,BaseException) or exception_identity is True,
                'GATE_MEASUREMENT_EXCEPTION_REPLACED',actual=actual)
        require(failure_details.get('actual_peak_bytes')==0 and
                failure_details.get('successful_measurement_count')==0 and
                failure_details.get('original_trace_event_count')==1 and
                failure_details.get('failed_measurements')==1,
                'GATE_INVALID_MEASUREMENT_PATH_UNPROVEN',actual=actual)
    session.case('G13',invalid,dict(refusals=4,successful_measurements=0),len(invalid)==4)
    cache=_make(session,'G14',capability,request,scope_factory)
    try:
        cache.close();before=observer_for(cache).snapshot();cache.close();after=observer_for(cache).snapshot()
        error=None
        try:cache.get_interval(0,1,'dual_neg45',20,cache.full_scope_id)
        except BaseException as observed:error=_code(observed)
        motion=session.motion(cache)
        session.case('G14',dict(idempotent_before=before,idempotent_after=after,refusal=error,
            points=len(session.pairs['G14']),trace_events=len(cache._trace),motion=motion),
            dict(points=3,trace_events=3,refusal='CLOSED_CACHE'),
            before==after and error=='CLOSED_CACHE' and len(session.pairs['G14'])==3 and len(cache._trace)==3)
    finally:detach(cache)


def run_g0(job, out, exchange=None):
    """Only formal G0 may call this function; no pre-run conformance shortcut."""
    session=_Session(job,out)
    try:
        require(job.get('gate')=='G0' and job.get('kind')=='memory_gate','G0_JOB_IDENTITY')
        checklist=_read(job,'gate_checklist_file')
        _read(job,'object_contract_file');_read(job,'measurement_contract_file')
        require(checklist['planned_gate_count']==17,'GATE_PLAN_IDENTITY')
        frozen=checklist['G0_work_totals']
        require(frozen['total_motion_entries_returns_vector_calls_each']==363 and
                frozen['normal_macro_OLD_oracle_walks']+frozen['auxiliary_OLD_oracle_walks']==576 and
                frozen['additional_complete_live_node_membership_traversals']==4 and
                frozen['tracker_payload_or_closure_inspections']==8 and
                frozen['additional_detached_metadata_size_traversals']==8 and
                frozen['WLS_calls']==frozen['starts']==0,'GATE_FROZEN_WORK_CAP_IDENTITY')
        capability,request,scope_factory=_unit_factory(job)
        binding_actual,binding_passed=_wiring_metadata()
        session.case('G01',dict(pinned_controls_checked=True,gate_scope_kind='UNIT_ONLY',
            original_physical_request=True,WLS_calls=0,start_attempts=0,wiring_binding=binding_actual),
            dict(WLS_calls=0,start_attempts=0,main_runtime_authority=False,
                 old_exact_weakref=True,clone_only_functional_substitution='MotionComponentCache'),binding_passed)
        _run_macro(session,job,capability,request,scope_factory)
        _run_pure_graphs(session)
        _run_cache_micros(session,capability,request,scope_factory)
        require(set(row['id'] for row in session.cases)==set(G0_IDS),'G0_CASE_COVERAGE')
        session.persist()
        require(session.counts==CAPS,'G0_ACTUAL_WORK_MISMATCH',observed=session.counts,expected=CAPS)
        require(callable(exchange),'G0_EMPTY_FRAME_EXCHANGE_REQUIRED')
        endpoint=exchange(dict(frame=job['frame'],allowed_sensor_ids=job['allowed_sensor_ids'],
                               start_tick=20),'SENSE',job['streams'][0]['context'])
        save_json(session.out/'zero_WLS_exchange.json',dict(actual=endpoint,
            expected=dict(skipped=True,quality_status='UNKNOWN',estimator_called=False),
            sense_requests=1))
        require(endpoint.get('skipped') is True and endpoint.get('estimator_called') is False and
                endpoint.get('quality',{}).get('status')=='UNKNOWN','G0_EMPTY_FRAME_NOT_ZERO_WLS')
        macro=dict(trace=session.macro_trace,paired_observations=session.macro_records,
                   binding=session.macro_binding)
        save_json(session.out/'macro_live_evidence.json',macro)
        refs=[file_pin((session.out/'gate_actuals.json').resolve()),
              file_pin((session.out/'macro_live_evidence.json').resolve())]
        refs.append(file_pin((session.out/'zero_WLS_exchange.json').resolve()))
        # C07 remains G1-owned until the explicit forged-evidence refusals pass.
        claims=[dict(id=key,status='VERIFIED',owner='gate_auditor',evidence_refs=deepcopy(refs),
            checks_completed=[row['id'] for row in session.cases],
            actual_work_counters=dict(session.counts),unknown_or_missing_evidence=[])
            for key in ('C01','C02','C03','C04','C05','C06')]
        result=dict(passed=True,gate='G0',gates=session.cases,claims=claims,
            actual_work_counters=session.counts,macro_evidence_pin=refs[1],
            actuals_pin=refs[0],main_runtime_authority=False,scope='Live UNIT_ONLY conformance, not CPU sample')
        save_json(session.out/'gate_result.json',result)
        return result
    except BaseException as error:
        session.persist(failure=True)
        save_json(session.out/'gate_failure.json',dict(passed=False,gate='G0',code=_code(error),
            error_type=type(error).__name__,details=getattr(error,'details',{}),
            actual_work_counters=None,work_counter_settlement_complete=False,
            known_collected_work_lower_bound=dict(session.counts),
            counter_evidence_limit='Interrupted cache cases can incur motion before their completion-time '
                'counter collection. These collected values are lower bounds, not exact failed-run totals.',
            unknown_or_missing_evidence=['complete failed-case work-counter settlement'],
            completed_gates=session.cases))
        raise


def validate_live_evidence(rows, witness, *, failed_event_indices=()):
    """Pure complete-order comparison against independently observed G0 points."""
    require(type(rows) is list and type(witness) is list,'MEM_RECORD_COVERAGE_MISMATCH')
    if any(row.get('event_index') in failed_event_indices for row in rows):
        raise MemoryAccountingError('MEM_FAILURE_SAMPLE_FABRICATED')
    require(len(rows)==len(witness),'MEM_RECORD_COVERAGE_MISMATCH')
    peak=0
    for index,(row,actual) in enumerate(zip(rows,witness)):
        for key in ('event_index','event_kind','event_digest','observed_event_frontier',
                    'previous_measured_event_frontier','absorbed_event_indices'):
            require(_typed_equal(row.get(key),actual.get(key)),
                    'MEM_EVENT_BINDING_MISMATCH',field=key,index=index)
        require(type(row.get('measurement_index')) is int and row['measurement_index']==index,
                'MEM_EVENT_BINDING_MISMATCH')
        require(type(row.get('current_bytes')) is int and
                row['current_bytes']==actual['old_current_bytes'],
                'MEM_LIVE_VALUE_MISMATCH',index=index)
        require(type(row.get('peak_before_bytes')) is int and row['peak_before_bytes']==peak,
                'MEM_LIVE_VALUE_MISMATCH',index=index)
        peak=max(peak,row['current_bytes'])
        require(type(row.get('peak_after_bytes')) is int and
                row['peak_after_bytes']==peak==actual['old_peak_bytes'],
                'MEM_LIVE_VALUE_MISMATCH',index=index)
    return dict(passed=True,checked_points=len(rows),final_peak_bytes=peak)


def _forge(rows):
    """Recompute editable claimed indices/peak; actual-event authority stays fixed."""
    peak=0
    for index,row in enumerate(rows):
        row['measurement_index']=index
        row['peak_before_bytes']=peak
        peak=max(peak,row['current_bytes']);row['peak_after_bytes']=peak
    return rows


def _claimed_chain(rows):
    """Recomputed forgeries still have no authority over the actual trace."""
    previous=None;links=[]
    for row in rows:
        raw=json.dumps(dict(previous_claimed_digest=previous,record=row),
                       sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
        previous=hashlib.sha256(raw).hexdigest();links.append(previous)
    return dict(claimed_record_count=len(rows),claimed_digest_chain=links,
                claimed_final_peak=None if not rows else rows[-1]['peak_after_bytes'],
                claimed_current_sum=sum(row['current_bytes'] for row in rows),
                authority='FORGED_SELF_DIGESTS_NOT_ACTUAL_EVENT_AUTHORITY')


def _g1_provenance(job, macro):
    """Read actual earlier guardian/runtime facts, not a producer's pass flag."""
    seal=_read(job,'execution_seal_file')
    require(sha_file(job['execution_seal_file'])==job['expected_source_seal_sha256'],
            'G1_EXECUTION_SOURCE_SEAL')
    manifest=_read_path(job,seal['source_manifest']['path'])
    require(job['source_pins'][seal['source_manifest']['path']]['sha256']==
            seal['source_manifest']['sha256'],'G1_SOURCE_MANIFEST_BINDING')
    inspected=[]
    for relative in ('research/information_service_shared/motion_cache.py',
                     'research/information_service_shared/evaluator.py',
                     'research/information_service_shared/comparator.py',
                     'research/information_service_memory_accounting/meter.py',
                     'research/information_service_memory_accounting/wiring.py'):
        observed=sha_file(ROOT/relative)
        require(manifest['files'].get(relative)==observed,'G1_CURRENT_CODE_BINDING',relative)
        inspected.append(dict(path=str(ROOT/relative),sha256=observed))
    guardian=_read(job,'G0_guardian_file')
    receipt=_read(job,'G0_supervision_file')
    require(guardian.get('passed') is True and guardian.get('accounting_complete') is True and
            guardian.get('all_reaped') is True and guardian.get('pair_id')=='G0' and
            guardian.get('attempt_id')==job['gate_identity']['attempt_id'],
            'G1_G0_GUARDIAN_AUTHORITY')
    require(receipt.get('adapter_id')=='gq_memory_accounting_supervision_v1' and
            receipt.get('attempt_id')==guardian['attempt_id'] and receipt.get('pair_id')=='G0' and
            receipt.get('job_ordinal')==1 and receipt.get('previous_receipt') is None and
            receipt.get('status')=='RETURNED_VALIDATED' and receipt.get('validation_errors')==[] and
            receipt.get('guardian_result_sha256')==job['source_pins'][job['G0_guardian_file']]['sha256'] and
            receipt.get('defaults_restored') is True and
            receipt.get('default_object_identity_preserved') is True and
            receipt.get('defaults_before')==receipt.get('defaults_after'),
            'G1_G0_SUPERVISION_AUTHORITY')
    final=receipt.get('final_records_audit',{})
    require(final.get('complete') is True and final.get('errors')==[] and
            final.get('unique_entries')==3 and final.get('worker_cpu')==guardian['worker_cpu'] and
            guardian['cumulative_before']==receipt['cumulative_before']==0.0 and
            guardian['cumulative_after']==receipt['cumulative_after']==guardian['worker_cpu'],
            'G1_G0_FINAL_ACCOUNTING_RECEIPT')
    require(receipt['absolute_deadline']==receipt['original_global_deadline']==
            receipt['original_started_monotonic']+480.,'G1_G0_DEADLINE')
    for key,value in (('total_cpu',240.),('pair_cpu',60.),('pair_wall',120.)):
        require(guardian['limits'].get(key)==value and receipt['effective_limits'].get(key)==value,
                'G1_G0_RESOURCE_CONTRACT',key)
    processes=guardian['processes']
    require(len(processes)==3 and {r['role'] for r in processes}=={'env','sense','controller'} and
            len({(r['pid'],r['start_ticks']) for r in processes})==3,'G1_G0_PROCESS_COVERAGE')
    worker=[]
    base=Path(job['G0_guardian_file']).parent
    runtime_facts=[]
    for row in processes:
        require(row.get('created') is True and row.get('reaped') is True and
                row.get('live_after_reap') is False and row.get('returncode')==0,
                'G1_G0_FINAL_WAIT4')
        for key in ('wait4_user_cpu','wait4_system_cpu'):
            value=row.get(key)
            require(type(value) in (int,float) and math.isfinite(value) and value>=0,
                    'G1_G0_CPU_UNAVAILABLE')
        if row['role'] in ('env','sense'):
            worker.append(row['wait4_user_cpu']+row['wait4_system_cpu'])
        runtime=_read_path(job,str(base/row['role']/'entry_runtime.json'))
        require(runtime['pid']==row['pid'] and runtime['pgid']==row['pgid'] and
                runtime['attempt_id']==guardian['attempt_id'] and runtime['pair_id']=='G0' and
                str(Path(runtime['executable']).resolve()) in seal['runtime'] and
                runtime['rlimit_cpu']==[60,61] and runtime['rlimit_as']==[4*1024**3]*2 and
                len(runtime['thread_env'])==4 and set(runtime['thread_env'].values())=={'1'},
                'G1_G0_RUNTIME_AUTHORITY')
        runtime_facts.append(runtime)
        if row['role']=='env':
            for key in ('pid','pgid','start_ticks'):
                require(macro['binding']['producer_'+key]==row[key],'G1_G0_LIVE_PRODUCER_IDENTITY')
    require(guardian['worker_cpu']==math.fsum(worker) and
            guardian.get('completed_sense_requests')==1 and
            guardian.get('message_counts',{}).get('SENSE',0)==1,
            'G1_G0_ZERO_SENSE_OR_CPU')
    sense=_read_path(job,str(base/'sense/counters.json'))
    for key in ('estimator_calls','start_attempts','completed_estimates'):
        require(type(sense.get(key)) is int and sense[key]==0,'G1_G0_ZERO_WLS_COUNTER',key)
    no_wls=_read_path(job,str(base/'env/no_wls_entry_guard.json'))
    require(no_wls.get('installed') is True and no_wls.get('restored') is True and
            no_wls.get('blocked_calls')==[] and no_wls.get('estimator_bodies_entered')==0 and
            no_wls.get('native_WLS_bodies_entered')==0,'G1_G0_PREBODY_GUARD')
    return dict(passed=True,source_files=inspected,guardian_pin=job['source_pins'][job['G0_guardian_file']],
                runtime_roles=runtime_facts,zero_WLS_counters=sense,
                no_WLS_entry_guard=no_wls,full_run_science_or_CPU_admission=False)


def run_g1(job,out):
    """Saved G0 evidence and pure refusals only: no second cache or walker."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    result=_read(job,'G0_result_file')
    require(result.get('passed') is True and result.get('gate')=='G0','G1_REAL_G0_REQUIRED')
    for key in ('macro_evidence_pin','actuals_pin'):
        embedded=result[key]
        require(job.get('source_pins',{}).get(embedded['path'])==embedded,
                'G1_G0_OUTPUT_EXTERNAL_PIN_BINDING',key)
    macro=_read_path(job,result['macro_evidence_pin']['path'])
    actuals=_read_path(job,result['actuals_pin']['path'])
    provenance=_g1_provenance(job,macro)
    save_json(out/'G1_source_runtime_admission.json',provenance)
    witness=macro['paired_observations']
    g02=next(row for row in result['gates'] if row['id']=='G02')
    sidecar_pin=g02['actual']['sidecar_receipt']['sidecar_pin']
    require(job.get('source_pins',{}).get(sidecar_pin['path'])==sidecar_pin,
            'G1_G0_SIDECAR_EXTERNAL_PIN_BINDING')
    check_pin(sidecar_pin)
    raw=Path(sidecar_pin['path']).read_bytes()
    require(raw.endswith(b'\n') and all(raw.splitlines()),'G1_G0_SIDECAR_FRAMING')
    rows=[json.loads(line) for line in raw.splitlines()]
    from .auditor import validate_sidecar_rows
    normal=validate_sidecar_rows(rows,macro['trace'],macro['binding'],'NEW')
    validate_live_evidence(rows,witness)
    save_json(out/'G0_saved_series_recheck.json',normal)
    cases=[]
    changed=deepcopy(rows);del changed[100]
    cases.append(('drop100',_forge(changed),witness,(), 'MEM_RECORD_COVERAGE_MISMATCH'))
    changed=deepcopy(rows);changed[101]=deepcopy(changed[100])
    cases.append(('duplicate100_remove101',_forge(changed),witness,(),'MEM_EVENT_BINDING_MISMATCH'))
    changed=deepcopy(rows);changed[100],changed[101]=changed[101],changed[100]
    cases.append(('swap100_101',_forge(changed),witness,(),'MEM_EVENT_BINDING_MISMATCH'))
    changed=deepcopy(rows);changed[100]['current_bytes']+=1;changed[101]['current_bytes']-=1
    cases.append(('compensated_bytes',_forge(changed),witness,(),'MEM_LIVE_VALUE_MISMATCH'))
    abnormal=actuals['paired_observations']['G10'];changed=deepcopy(abnormal)
    fake=deepcopy(changed[0]);fake.update(event_index=1,event_kind='INTERVAL_BUILT')
    changed.insert(1,fake)
    cases.append(('failed_callback_sample',_forge(changed),abnormal,(1,),'MEM_FAILURE_SAMPLE_FABRICATED'))
    observed=[]
    for name,rows,expected_rows,failed,expected_code in cases:
        recomputed=_claimed_chain(rows)
        code=None
        try:validate_live_evidence(rows,expected_rows,failed_event_indices=failed)
        except BaseException as error:code=_code(error)
        observed.append(dict(name=name,input=rows,expected_code=expected_code,
                             recomputed_claimed_summary=recomputed,
                             actual=dict(code=code),passed=code==expected_code))
        save_json(out/'G15_negative_actuals.json',observed)
        require(code==expected_code,'G15_NEGATIVE_ACCEPTED_OR_WRONG_CODE',name)
    _read(job,'gate_checklist_file');_read(job,'measurement_contract_file')
    refs=[file_pin((out/'G15_negative_actuals.json').resolve()),result['macro_evidence_pin'],
          file_pin((out/'G1_source_runtime_admission.json').resolve()),
          file_pin((out/'G0_saved_series_recheck.json').resolve()),sidecar_pin]
    claim=dict(id='C07',status='VERIFIED',owner='gate_auditor',evidence_refs=refs,
        checks_completed=['G15_COMPLETE_MEMORY_EVENT_EVIDENCE'],
        actual_work_counters=dict(negative_evidence_copies=5,new_live_measurements=0,
                                  frozen_OLD_oracle_walks=0,WLS_calls=0,start_attempts=0),
        unknown_or_missing_evidence=[])
    answer=dict(passed=True,gate='G1',source_runtime_admission=provenance,
        gates=[dict(id='G15',actual=observed,passed=True),
        dict(id='G16',status='ADMITTED_FOR_FUTURE_RUNS_ONLY',actual=None),
        dict(id='G17',status='ADMITTED_FOR_FUTURE_AUDITS_ONLY',actual=None)],claims=[claim],
        actual_work_counters=claim['actual_work_counters'],
        full_run_claims_granted=False)
    save_json(out/'gate_result.json',answer)
    return answer


def run_gate(job,out,exchange=None):
    require(job.get('gate') in ('G0','G1'),'UNKNOWN_MEMORY_GATE')
    return run_g0(job,out,exchange=exchange) if job['gate']=='G0' else run_g1(job,out)
