"""Fourteen production-connected unit contracts; explicit synthetic Q, zero WLS.

Only the audit driver reads expected values. Exercise functions receive detached
input/events and call the real cache, workspace, step, clock and comparator seams.
"""
from contextlib import ExitStack
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import json
import math
import os
from pathlib import Path
import struct
from unittest.mock import patch

from .common import ContractError, digest, read_json, save_json
from .trace_audit import audit_trace, typed, typed_digest


def require(ok,message):
    if not ok:raise ContractError('Shared short check: '+message)


def exact(a,b,message):require(typed(a)==typed(b),message)


def _native_snapshot(value, active=None, path=''):
    """Test-only immutable snapshot; native tuple is distinct from list.

    This does not widen the JSON contract. Exact built-in types only; the
    active recursion path detects cycles while allowing shared DAG leaves.
    """
    kind=type(value)
    if value is None:return ('none',)
    if kind is bool:return ('bool',value)
    if kind is int:return ('int',str(value))
    if kind is float:
        require(math.isfinite(value),'nonfinite native float at '+path)
        return ('float64',struct.pack('>d',value).hex())
    if kind is str:return ('str',value)
    require(kind in (list,tuple,dict),'unsupported native type '+kind.__name__+' at '+path)
    active=set() if active is None else active
    identity=id(value)
    require(identity not in active,'native container cycle at '+path)
    active.add(identity)
    try:
        if kind is dict:
            require(all(type(k) is str for k in value),'non-string native dictionary key at '+path)
            return ('dict',tuple((k,_native_snapshot(value[k],active,path+'/'+k)) for k in sorted(value)))
        return ('tuple' if kind is tuple else 'list',
                tuple(_native_snapshot(item,active,path+'/'+str(i)) for i,item in enumerate(value)))
    finally:
        active.remove(identity)


def match(actual,expected,path='',atol=1e-12):
    if type(expected) is dict:
        require(type(actual) is dict,'expected mapping '+path)
        for name,value in expected.items():
            require(name in actual,'missing observed '+path+'/'+name)
            match(actual[name],value,path+'/'+name,atol)
    elif type(expected) is list:
        require(type(actual) is list and len(actual)==len(expected),'array mismatch '+path)
        for i,(a,b) in enumerate(zip(actual,expected)):match(a,b,path+'/'+str(i),atol)
    elif type(expected) is float:
        require(type(actual) is float and math.isfinite(actual) and abs(actual-expected)<=atol,'float mismatch '+path)
    else:exact(actual,expected,'typed value mismatch '+path)


def rejected(function):
    try:function()
    except ContractError as error:return dict(error_type=type(error).__name__,message=str(error))
    raise ContractError('Declared invalid call was accepted')


class SyntheticQuality:
    """Declared test callback. It prepares payloads but never solves an estimate."""
    def __init__(self,status='PASS',failure=None):self.status=status;self.failure=failure;self.calls=[]
    def __call__(self,frame,allowed,start):
        from research.information_service.public_quality import prepare_frame
        self.calls.append(dict(frame=deepcopy(frame),allowed_sensor_ids=list(allowed),start_tick=start))
        if self.failure is not None and frame['tick']==self.failure['tick']:
            raise ContractError(self.failure['message'])
        prepared=prepare_frame(frame,allowed)
        return dict(frame_id=frame['frame_id'],stream_id=frame['stream_id'],target_id=frame['target_id'],tick=frame['tick'],
            payload=prepared['payload'],payload_sha256=prepared['payload_sha256'],estimator_called=False,
            quality=dict(status=self.status,payload_sha256=prepared['payload_sha256']),
            synthetic_unit_quality=True)


class CaseContext:
    def __init__(self,job,check_id,out):
        self.job=job;self.check_id=check_id;self.out=Path(out);self.caches=[];self.comparison_inputs=None
        self.out.mkdir(parents=True,exist_ok=True)
    def capability(self,fixture,label=None):
        from .contracts import make_unit_fixture
        return make_unit_fixture(label or self.check_id,deepcopy(fixture))
    def cache(self,cap,label):
        from .contracts import make_scope
        from .motion_cache import MotionComponentCache
        scope=make_scope(cap.request,attempt_id=self.job['attempt_id'],decision_id=self.check_id,
            batch_id=label,cache_instance_id=f'{self.check_id}:cache:{len(self.caches)}',
            runtime_binding_id=self.job['runtime_binding_id'],unit_fixture=cap)
        stem=self.out/f'cache_{len(self.caches):02d}';tracefile=Path(str(stem)+'.trace.jsonl')
        def save_event(row):
            with tracefile.open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())
        cache=MotionComponentCache(scope,cap.request,unit_fixture=cap,on_trace=save_event)
        self.caches.append((cache,cap,stem))
        return cache
    def capture(self):
        records=[]
        for cache,cap,stem in self.caches:
            diagnostics=cache.snapshot_diagnostics();trace=cache.trace_records()
            save_json(Path(str(stem)+'.diagnostics.json'),diagnostics)
            report=audit_trace(trace,diagnostics)
            instrumentation=cache.instrumentation()
            require(instrumentation['compute_entries']==instrumentation['compute_returns']==diagnostics['counters']['new_computed_intervals'],
                    'actual kernel entry/return counts differ from constructed intervals')
            records.append(dict(trace_file=str(stem)+'.trace.jsonl',diagnostics_file=str(stem)+'.diagnostics.json',
                                audit=report,instrumentation=instrumentation))
        return records


def get(cache,component,k):
    return cache.get_interval(component['target_id'],component['robot_id'],component['role'],k,cache.full_scope_id)


def descriptor(cap,target,robots,roles):
    matches=[s for s in cap.manifest['candidates'] if s['key']==dict(target=target,robots=robots,roles=roles)]
    require(len(matches)==1,'fixture team is not a unique canonical candidate')
    return matches[0]


def init(cap,spec,callback,work='unit'):
    from .evaluator import initialize_candidate_state
    return initialize_candidate_state(cap.request,spec,callback,unit_fixture=cap,work_identity=work,
                                      physical_environment_id='EXPLICIT_UNIT_ENVIRONMENT')


def evaluate(cap,spec,cache,callback,work='unit'):
    from .evaluator import evaluate_candidate
    return evaluate_candidate(cap.request,spec,callback,cache=cache,unit_fixture=cap,work_identity=work,
                              physical_environment_id='EXPLICIT_UNIT_ENVIRONMENT')


def prefix_rows(cache):
    return [{k:v for k,v in e['interval'].items() if k not in ('full_scope_id','component')}
            for c in cache.snapshot_diagnostics()['components'] for e in c['intervals']]


def storage_alias(a,b):
    import numpy as np
    def objects(value):
        mutable=set();arrays=[];seen=set()
        def visit(x):
            if id(x) in seen:return
            seen.add(id(x))
            if isinstance(x,np.ndarray):mutable.add(id(x));arrays.append(x)
            elif isinstance(x,dict):
                mutable.add(id(x))
                for v in x.values():visit(v)
            elif isinstance(x,list):
                mutable.add(id(x))
                for v in x:visit(v)
            elif isinstance(x,tuple):
                for v in x:visit(v)
        visit(value);return mutable,arrays
    ma,aa=objects(a);mb,ab=objects(b)
    return bool(ma&mb) or any(np.shares_memory(x,y) for x in aa for y in ab)


def _field_names(value):
    names=set()
    if isinstance(value,dict):
        names.update(value)
        for child in value.values():names.update(_field_names(child))
    elif isinstance(value,(list,tuple)):
        for child in value:names.update(_field_names(child))
    return names


def _exercise(number,I,events,ctx):
    from . import evaluator as production
    from . import contracts
    if number==1:
        cap=ctx.capability(I['fixture']);cache=ctx.cache(cap,I['scope_label']);c=I['component']
        initial=cache.get_initial_position(c['target_id'],c['robot_id'],c['role'],cache.full_scope_id)
        initially=cache.snapshot_diagnostics();returns=[get(cache,c,k) for k in (0,0,1,0)]
        exact(returns[0],returns[1],'same-key repeated interval changed');exact(returns[0],returns[-1],'non-tail read changed')
        storage=cache.unit_storage_references(cap);diag=cache.snapshot_diagnostics()
        return dict(counters=diag['counters'],component_instances=diag['component_instances'],rows=prefix_rows(cache),
            initial_position=initial,complete_candidate_position_shape=list(storage['initial_positions'].shape),
            unchanged_config_robots=cache.scope['robots'],stable_robot_ids=list(range(storage['initial_positions'].shape[0])),
            initial_read_constructed_intervals=initially['counters']['new_computed_intervals'],
            constructed_intervals=[r['interval_start_tick'] for r in diag['constructed_interval_identities']],
            accepted_requested_union=sorted({r['interval_start_tick'] for r in diag['accepted_interval_request_identities']}))
    if number==2:
        from .comparator import strict_read,compare_raw
        from .comparison_checks import test_metadata
        cap=ctx.capability(I['public_request']);cache=ctx.cache(cap,I['scope_label']);callback=SyntheticQuality()
        first=evaluate(cap,I['candidates'][0],cache,callback,'C02:c0');saved_first=deepcopy(first)
        native_before=_native_snapshot(first)
        save_json(ctx.out/'candidate0_native_before.json',dict(
            scope='test-only native type/value snapshot; not a scientific JSON result',snapshot=native_before))
        before=deepcopy(cache.snapshot_diagnostics()['components'][0]['intervals']);before_hash=typed_digest(before)
        second=evaluate(cap,I['candidates'][1],cache,callback,'C02:c2')
        after=cache.snapshot_diagnostics();common=next(c for c in after['components'] if c['component']==dict(target_id=0,robot_id=0,role='dual_neg45'))
        exact(before,common['intervals'][:len(before)],'earlier candidate completion froze/changed common prefix')
        native_after=_native_snapshot(first)
        save_json(ctx.out/'candidate0_native_after.json',dict(
            scope='test-only native type/value snapshot; not a scientific JSON result',snapshot=native_after))
        native_unchanged=native_after==native_before
        require(native_unchanged,'later candidate changed native type/value of returned first candidate')
        require(_native_snapshot(saved_first)==native_before,'independent saved native copy changed')
        _native_snapshot(second)  # Reject unknown types before JSON normalization.
        # Only after native invariance succeeds, cross the unchanged production
        # save_json boundary; never feed native containers to the JSON checker.
        before_file=ctx.out/'candidate0_before.json';after_file=ctx.out/'candidate0_after.json'
        second_file=ctx.out/'candidate2.json'
        save_json(before_file,saved_first);save_json(after_file,first);save_json(second_file,second)
        json_comparison=compare_raw(before_file.read_bytes(),after_file.read_bytes(),
            test_metadata('C02:unchanged_saved_json'))
        save_json(ctx.out/'candidate0_json_comparison.json',json_comparison)
        require(json_comparison['status']=='EQUAL','saved JSON candidate changed after later candidate')
        first_json=strict_read(after_file);second_json=strict_read(second_file)
        audit_trace(cache.trace_records(),after,candidate_results=[first_json,second_json])
        return dict(counters=after['counters'],component_instances=after['component_instances'],results=[first_json,second_json],
            old_prefix_binary64_unchanged=typed(before)==typed(common['intervals'][:len(before)]),
            old_prefix_digest_unchanged=before_hash==typed_digest(common['intervals'][:len(before)]),
            candidate0_returned_frames_unchanged_after_candidate2=native_unchanged,
            native_type_and_value_unchanged=native_unchanged,saved_json_comparison=json_comparison,
            comparison_order='native invariance; save_json; strict JSON comparison and saved-view audits',
            candidate0_completion_tick=first_json['per_target']['0']['completion_tick'],candidate2_completion_tick=second_json['per_target']['0']['completion_tick'])
    if number==3:
        cap=ctx.capability(I['fixture']);cache=ctx.cache(cap,'C03');returned=[get(cache,c,0) for c in I['components']]
        again=get(cache,I['components'][-1],0);exact(again,returned[-1],'cross-target repeated lookup differs')
        stored=cache.unit_storage_references(cap)['components'];keys=list(stored)
        require(len(keys)==len(set(keys)),'component keys collided')
        distinct=all(not storage_alias(stored[a],stored[b]) for n,a in enumerate(keys) for b in keys[n+1:])
        diag=cache.snapshot_diagnostics()
        return dict(counters=diag['counters'],component_instances=diag['component_instances'],
            distinct_component_keys=[c['component'] for c in diag['components']],
            each_constructed_intervals=sorted({r['interval']['interval_start_tick'] for c in diag['components'] for r in c['intervals']}),
            cross_target_same_robot_same_role_not_aliased=not storage_alias(stored[(0,0,'dual_neg45')],stored[(1,0,'dual_neg45')]),
            cross_role_same_robot_not_aliased=not storage_alias(stored[(0,0,'dual_neg45')],stored[(0,0,'dual_pos45')]),
            distinct_robot_storage_not_aliased=distinct,returned_intervals=returned)
    if number==4:
        cap=ctx.capability(I['fixture']);cache=ctx.cache(cap,I['scope_label']);get(cache,dict(target_id=0,robot_id=0,role='dual_neg45'),0)
        old=deepcopy(cache.snapshot_diagnostics()['components']);denied=[]
        for mutation in I['mutations']:
            other={k:deepcopy(v) for k,v in cache.scope.items() if k!='full_scope_id'}
            if mutation['field']=='config.travel_gain':
                config=deepcopy(cap.request['config']);config['travel_gain']=mutation['value'];other['config_digest']=digest(config)
            else:other[mutation['field']]=deepcopy(mutation['value'])
            expected_scope=typed_digest(other)
            require(expected_scope!=cache.full_scope_id,'declared scope mutation did not change the typed scope identity')
            denied.append(dict(id=mutation['id'],**rejected(lambda:cache.get_interval(0,0,'dual_neg45',0,expected_scope))))
        fresh=[]
        for recipe in I['legal_new_scope_recipes']:
            f=deepcopy(I['fixture']);newcap=cap
            if recipe['field']=='config.travel_gain':f['config']['travel_gain']=recipe['value'];newcap=ctx.capability(f,'C04:config')
            elif recipe['field']=='prediction_end_tick':f['prediction_end_tick']=recipe['value'];newcap=ctx.capability(f,'C04:horizon')
            new=ctx.cache(newcap,recipe['id']);before=new.snapshot_diagnostics();get(new,dict(target_id=0,robot_id=0,role='dual_neg45'),0)
            fresh.append(dict(before=before['counters'],after=new.snapshot_diagnostics()['counters']))
        exact(old,cache.snapshot_diagnostics()['components'],'rejected old scope changed prefix')
        return dict(old_scope_counters=cache.snapshot_diagnostics()['counters'],rejected_mutations=[r['id'] for r in denied],
            old_prefix_digest_unchanged=typed(old)==typed(cache.snapshot_diagnostics()['components']),
            new_scope_instances=len(fresh),new_scope_interval0_misses=sum(x['after']['new_computed_intervals'] for x in fresh),
            new_scope_foreign_progress_records=sum(x['before']['new_computed_intervals'] for x in fresh),rejections=denied,fresh_scopes=fresh)
    if number==5:
        cap=ctx.capability(I['fixture']);cache=ctx.cache(cap,'C05');c=I['component']
        initial=cache.get_initial_position(c['target_id'],c['robot_id'],c['role'],cache.full_scope_id)
        row=get(cache,c,0);before=deepcopy(row);before_bits=typed(before);before_hash=typed_digest(before)
        storage=cache.unit_storage_references(cap)
        aliases=storage_alias(initial,storage) or storage_alias(row,storage)
        require(not aliases,'getter returned mutable alias or readonly backing view of storage')
        spec=descriptor(cap,0,[0,1],['dual_neg45','dual_pos45'])
        w1=init(cap,spec,SyntheticQuality(),'C05:A');w2=init(cap,spec,SyntheticQuality(),'C05:B')
        b_positions=w2.positions.tolist();b_clock=deepcopy(w2.clock.raw())
        position_alias=storage_alias(w1.positions,w2.positions);clock_alias=w1.clock is w2.clock or w1.clock.state is w2.clock.state
        require(not position_alias and not clock_alias,'production workspaces alias')
        mutations=[]
        for mutation in I['mutations']:
            obj=mutation['object'];path=mutation['path'];value=mutation['value']
            try:
                if obj=='returned_initial_position':initial[path[0]]=value
                elif obj=='returned_interval':row[path[0]][path[1]]=value
                elif obj=='candidate_A_positions':w1.positions[tuple(path)]=value
                elif obj=='candidate_A_clock':w1.clock.state=replace(w1.clock.state,base=value)
                else:raise ContractError('Unknown frozen C05 mutation')
                mutations.append(dict(object=obj,outcome='DETACHED_WRITE'))
            except (TypeError,ValueError,AttributeError) as error:
                mutations.append(dict(object=obj,outcome='IMMUTABLE_DETACHED_REJECTION',error_type=type(error).__name__))
        again=get(cache,c,0);get(cache,c,1);final=get(cache,c,0)
        exact(before,again,'returned write contaminated cache');exact(before,final,'append altered an old prefix')
        exact(w2.positions.tolist(),b_positions,'candidate A altered B positions');exact(w2.clock.raw(),b_clock,'candidate A altered B clock')
        return dict(counters=cache.snapshot_diagnostics()['counters'],rows=prefix_rows(cache),
            old_prefix_0_binary64_and_hash_unchanged=typed(final)==before_bits and typed_digest(final)==before_hash,
            append_added_exactly_one_interval=cache.snapshot_diagnostics()['counters']['new_computed_intervals']==2,
            candidate_B_positions_equal_initial=typed(w2.positions.tolist())==typed(b_positions),candidate_B_clock_base=w2.clock.raw()['base'],
            candidate_position_shape=list(w2.positions.shape),production_workspace_initializer_reached=type(w1) is production.CandidateWorkspace and type(w2) is production.CandidateWorkspace,
            both_production_workspaces_alive_during_alias_check=w1 is not w2,
            returned_objects_share_mutable_container_or_ndarray_storage_with_cache=aliases,
            candidate_workspaces_share_positions_storage=position_alias,candidate_workspaces_share_clock=clock_alias,
            auditor_retained_original_prefix_bytes_and_independent_hash=before_bits==typed(before) and before_hash==typed_digest(before),
            observed_prefix_bytes=before_bits,observed_prefix_hash=before_hash,mutation_results=mutations,
            motion_cache_storage_field_names=sorted(k for k in _field_names(storage['components']) if type(k) is str),
            ownership_records=[w1.ownership_record(cache.full_scope_id,[w2]),w2.ownership_record(cache.full_scope_id,[w1])])
    if number==6:
        cap=ctx.capability(I['fixture']);cache=ctx.cache(cap,'C06');observed={};workspaces=[]
        for variant in I['variants']:
            callback=SyntheticQuality(I['synthetic_new_Q']);spec=descriptor(cap,0,variant['robots'],variant['roles'])
            w=init(cap,spec,callback,'C06:'+variant['id']);workspaces.append(w)
            observed[variant['id']]=dict(progress=w.clock.state.progress,reused=w.retained is not None,
                first=w.first,start=w.start,calls=len(callback.calls),shape=list(w.positions.shape))
        before=[deepcopy(w.clock.raw()) for w in workspaces]
        workspaces[0].clock.state=replace(workspaces[0].clock.state,base=.123)
        for w,c in zip(workspaces[1:],before[1:]):exact(w.clock.raw(),c,'C06 clock contamination')
        return dict(initial_progress_by_variant={k:v['progress'] for k,v in observed.items()},
            reused_actual_endpoint_by_variant={k:v['reused'] for k,v in observed.items()},
            first_new_fusion_tick={k:v['first'] for k,v in observed.items()},service_start_tick=workspaces[0].start,
            prepared_synthetic_quality_calls={k:v['calls'] for k,v in observed.items()},
            motion_intervals_constructed=cache.snapshot_diagnostics()['counters']['new_computed_intervals'],
            positions_per_candidate_shape=list(workspaces[0].positions.shape),motion_cache_clock_records=len(
                [k for v in cache.unit_storage_references(cap)['components'].values() for k in v if 'clock' in k]),
            workspace_observations=observed)
    if number==7:
        from dataclasses import asdict
        from pursuit_v2.config import Config
        from research.information_service_online import public
        from research.information_service.public_quality import prepare_frame,assess_quality
        source=deepcopy(I['assembler_inputs']);before=typed_digest(source);calls=[]
        require(I['stop_before_estimator'] is True,'C07 must stop before any estimator')
        x=len(source['positions']);j=source['target_id'];tick=source['tick']
        # Only structural wrapper fields are added. All current numerical input
        # positions/profiles/slots/target position come unchanged from C07 input.
        # This is explicitly synthetic unit authority, never a real checkpoint.
        cfg=Config(robots=x,task_count=j+1,capture_mode='stepwise_service',
                   geometry_mode='angular_standoff_v1',prediction_stages=1,max_stages=2)
        birth=dict(event_index=0,kind='BIRTH',target_id=j,
            at=dict(time_seconds=0.,event_tick=0),segment_id=None,
            progress_before=0.,progress_after=0.,reasons=['BIRTH'])
        history=public.seal_history(dict(target_id=j,birth_tick=0,cutoff_tick=tick,
            active_segment_id=None,segments=[],unassigned_intervals=[dict(start_tick=0,end_at=None,
                opened_by='BIRTH',opening_event_index=0,closing_event_index=None)],events=[birth]))
        checkpoint=public.seal_checkpoint(dict(
            previous_checkpoint_id=digest(dict(explicit_synthetic_C07_prior_cut=tick-20)),
            phase='DECISION_READY',tick=tick,episode_end_tick=round(cfg.end_time/.05),config=asdict(cfg),
            positions=deepcopy(source['positions']),assignment=[dict(target=None,role='none') for _ in range(x)],
            targets=[dict(id=j,birth=0.,position_now=deepcopy(source['target_position']),
                velocity_now=[float(cfg.target_speed_min),0.],required_robots=2,weight=1.,
                deadline=float(cfg.end_time),service_duration=1.)],
            sensor_profiles=deepcopy(source['sensor_profiles']),task_histories=[history],
            current_slots=[public.seal_slot(row) for row in source['current_slots']],events_since_previous_checkpoint=[]))
        request=public.request_from_checkpoint(checkpoint,unit_only=True)
        cap=ctx.capability(request,'C07:explicit_public_request')
        require(cap.manifest.get('unit_public_request') is not None,
                'C07 must preserve its public request; logical-unit all-MODEL fallback is forbidden')
        request_before=typed_digest(request);checkpoint_before=typed_digest(checkpoint)
        cap_before=typed_digest(cap.manifest['unit_public_request'])
        save_json(ctx.out/'C07_unit_public_request.json',request)
        route=[];current_variant={'id':None}
        original_initialize=production.initialize_candidate_state
        original_sense=production._sense
        original_prepare=production.prepare_candidate_endpoint
        original_current=production.measurements.assemble_current
        current_outputs={};callback_outputs={}

        class StopBeforeWLS(Exception):
            """Declared two-measurement stop after actual production assembly."""

        def record(name,phase,**data):
            route.append(dict(variant=current_variant['id'],function=name,phase=phase,**deepcopy(data)))
            save_json(ctx.out/'C07_production_route.json',route)

        def observe_initialize(*args,**kwargs):
            record('initialize_candidate_state','ENTER',request=deepcopy(args[0]),candidate=deepcopy(args[1]),
                unit_fixture_id=kwargs['unit_fixture'].fixture_id,work_identity=kwargs['work_identity'])
            try:workspace=original_initialize(*args,**kwargs)
            except StopBeforeWLS:
                record('initialize_candidate_state','STOP_BEFORE_WLS');raise
            record('initialize_candidate_state','RETURN',frame=workspace.frames[0],
                status=workspace.status,positions=workspace.positions.tolist(),clock=workspace.clock.raw())
            return workspace

        def observe_sense(workspace,at):
            record('_sense','ENTER',tick=at,target_id=workspace.j,candidate=workspace.descriptor,
                has_public_request=workspace.online_request is not None)
            try:answer=original_sense(workspace,at)
            except StopBeforeWLS:
                record('_sense','STOP_BEFORE_WLS');raise
            record('_sense','RETURN',result=answer)
            return answer

        def observe_prepare(workspace,at):
            record('prepare_candidate_endpoint','ENTER',tick=at,service_start_tick=workspace.start,
                public_request=workspace.online_request,candidate=workspace.descriptor)
            answer=original_prepare(workspace,at)
            record('prepare_candidate_endpoint','RETURN',result=answer)
            return answer

        def observe_current(*args,**kwargs):
            record('measurements.assemble_current','ENTER',public_request=args[0],candidate=args[1],
                work_identity=args[2],unit_only=kwargs.get('unit_only',False),
                authority_present=kwargs.get('authority') is not None,
                physical_environment_id=kwargs.get('physical_environment_id'))
            answer=original_current(*args,**kwargs)
            current_outputs[current_variant['id']]=deepcopy(answer)
            record('measurements.assemble_current','RETURN',result=answer)
            return answer

        def stop_or_assess_missing(frame,allowed,start):
            # The S _sense path has already assembled and prepared this frame.
            # Rechecking it here supplies the genuine m<2 UNKNOWN result; the
            # m=2 branch deliberately supplies no quality result at all.
            prepared=prepare_frame(frame,allowed)
            callback_outputs[current_variant['id']]=dict(frame=deepcopy(frame),
                allowed_sensor_ids=list(allowed),start_tick=start,prepared=deepcopy(prepared),quality=None)
            record('unit_sensing_boundary','ENTER',frame=frame,allowed_sensor_ids=list(allowed),
                start_tick=start,prepared=prepared)
            if prepared['valid_sensor_count']>=2:
                record('unit_sensing_boundary','STOP_BEFORE_WLS',quality_computed=False)
                raise StopBeforeWLS('C07 declared stop after production current-frame assembly')
            quality=assess_quality(prepared['payload'],None)
            callback_outputs[current_variant['id']]['quality']=deepcopy(quality)
            record('unit_sensing_boundary','RETURN',quality=quality)
            return dict(frame_id=frame['frame_id'],stream_id=frame['stream_id'],target_id=frame['target_id'],
                tick=frame['tick'],payload=prepared['payload'],payload_sha256=prepared['payload_sha256'],
                estimator_called=False,quality=quality,explicit_unit_missing_assessment=True)

        with ExitStack() as stack:
            for owner,name,wrapper in [(production,'initialize_candidate_state',observe_initialize),
                    (production,'_sense',observe_sense),(production,'prepare_candidate_endpoint',observe_prepare),
                    (production.measurements,'assemble_current',observe_current)]:
                stack.enter_context(patch.object(owner,name,wrapper))
            for variant in source['teams']:
                current_variant['id']=variant['id']
                robots=[m[0] for m in variant['team']];roles=[m[1] for m in variant['team']]
                spec=descriptor(cap,j,robots,roles);stopped=False;workspace=None
                try:workspace=init(cap,spec,stop_or_assess_missing,'C07:'+variant['id'])
                except StopBeforeWLS:stopped=True
                require(variant['id'] in current_outputs and variant['id'] in callback_outputs,
                        'C07 did not reach both real assemble_current and the sensing boundary')
                callback=callback_outputs[variant['id']];result=current_outputs[variant['id']]
                exact(result['frame'],callback['frame'],'S did not send the actual current-assembly result')
                exact(result['allowed_sensor_ids'],callback['allowed_sensor_ids'],'S changed the actual assembly team')
                require(stopped==(callback['prepared']['valid_sensor_count']>=2),
                        'C07 stop/UNKNOWN branch does not match actual measurement count')
                if workspace is not None:
                    require(len(workspace.frames)==1 and workspace.frames[0]['tick']==tick,
                            'C07 unexpectedly advanced the candidate')
                    exact(workspace.positions.tolist(),source['positions'],'C07 initialization moved robots')
                calls.append(dict(id=variant['id'],assembly=result,prepared=callback['prepared'],
                    quality=callback['quality'],stopped_before_WLS=stopped,
                    initialized_frame=None if workspace is None else deepcopy(workspace.frames[0])))
        expected_route=['initialize_candidate_state','_sense','prepare_candidate_endpoint',
                        'measurements.assemble_current','unit_sensing_boundary']
        for variant in source['teams']:
            entries=[r['function'] for r in route if r['variant']==variant['id'] and r['phase']=='ENTER']
            require(entries==expected_route,'C07 bypassed/repeated a required production current-endpoint call')
        require(typed_digest(source)==before,'C07 assembler mutated current data')
        require(typed_digest(request)==request_before and typed_digest(checkpoint)==checkpoint_before
                and typed_digest(cap.manifest['unit_public_request'])==cap_before,
                'C07 changed its synthetic public request/slots')
        by={r['id']:r for r in calls};u0=by['known_missing']['assembly']['source_slots'][0]['packet']
        u2=by['known_unqueried']['assembly']['source_slots'][1]['packet']
        return dict(source_outcomes={k:[[s['source'],s['outcome']] for s in r['assembly']['source_slots']] for k,r in by.items()},
            measurement_sensor_ids={k:r['prepared']['payload']['sensor_ids'] for k,r in by.items()},observed_U0_packet=u0,
            model_U2_bearing=u2['bearing'],retained_actual_slot_states=[s['state'] for s in source['current_slots']],
            real_sampling_calls=sum(r['assembly']['real_sampling_calls'] for r in calls),
            actual_cache_writes=int(typed_digest(source)!=before),missing_frame_quality=by['known_missing']['quality']['status'],
            missing_frame_estimator_calls=ctx.wls_counts['estimator_calls'],assemblies=calls,
            production_route=dict(entries={name:sum(r['function']==name and r['phase']=='ENTER' for r in route) for name in expected_route},
                calls=route,source_input_digest_before=before,source_input_digest_after=typed_digest(source),
                public_request_digest_before=request_before,public_request_digest_after=typed_digest(request),
                synthetic_wrapper=dict(scope='EXPLICIT_UNIT_ONLY; not actual history; no control/clock interval advanced',
                    config_source='Frozen Config defaults with X from C07, Y=target_id+1, service/angular, prediction_stages1,max_stages2',
                    structural_target_fields=dict(birth=0.,velocity_now=[float(cfg.target_speed_min),0.],weight=1.,
                        deadline=float(cfg.end_time),service_duration=1.),
                    original_current_input_fields_preserved=['tick','target_id','target_position','positions','sensor_profiles','current_slots']),
                two_measurement_quality_computed=by['known_unqueried']['quality'] is not None,
                production_callable_sources={name:dict(module=f.__module__,qualified_name=f.__qualname__,
                    source_file=f.__code__.co_filename,source_first_line=f.__code__.co_firstlineno) for name,f in
                    [('initialize_candidate_state',original_initialize),('_sense',original_sense),
                     ('prepare_candidate_endpoint',original_prepare),('measurements.assemble_current',original_current)]}))
    if number==8:
        from research.information_service_online.execution import ActualMeasurementCache,OnlineEnvironment
        from pursuit_v2.types import Target
        cap=ctx.capability(I['fixture']);cache=ctx.cache(cap,'C08');request=cap.request;before=typed_digest(request)
        counters={name:0 for name in I['forbidden_capabilities']}
        def poison(name):
            def forbidden(*args,**kwargs):
                counters[name]+=1;raise ContractError('C08 forbidden capability reached: '+name)
            return forbidden
        patches=[(ActualMeasurementCache,'query','actual_sampler.query'),
                 (ActualMeasurementCache,'record_outcome','actual_sampler.record_outcome'),
                 (OnlineEnvironment,'step','actual_environment.step'),
                 (Target,'position','private_future_reader'),(Target,'velocity_at','private_future_reader'),
                 (OnlineEnvironment,'_restore','private_resume_reader'),
                 (OnlineEnvironment,'_checkpoint','actual_checkpoint_writer')]
        callback=SyntheticQuality(failure=I['forced_endpoint_exception']);observed_error=None;last=None
        with ExitStack() as stack:
            for owner,name,label in patches:stack.enter_context(patch.object(owner,name,poison(label)))
            try:evaluate(cap,I['candidate'],cache,callback,'C08')
            except ContractError as error:
                observed_error=dict(type=type(error).__name__,message=str(error))
                last=deepcopy(getattr(error,'gq_last_committed',None))
        require(observed_error is not None,'declared numerical failure was swallowed')
        require(observed_error['message']==I['forced_endpoint_exception']['message'],'unexpected failure replaced injected contract error')
        return dict(forbidden_capability_calls=counters,exception_type=observed_error['type'],exception_message=observed_error['message'],
            error_not_converted_to_UNKNOWN=observed_error is not None,source_digest_unchanged=typed_digest(request)==before,
            last_committed_frame_tick=last['tick'],real_wls_calls=ctx.wls_counts['estimator_calls'],
            automatic_retry=len([r for r in callback.calls if r['frame']['tick']==I['forced_endpoint_exception']['tick']])>1,
            last_committed_frame=last,observed_quality_provider_calls=callback.calls)
    if number==9:
        from pursuit_v2.config import Config
        cfg=Config(robots=3,capture_mode='stepwise_service',geometry_mode='angular_standoff_v1')
        clocks={};progress={};completed={};sequences=I['endpoint_sequences'];states={}
        for name,sequence in sequences.items():
            first=sequence[0];clocks[name]=production.ClockStepper(cfg,I['H_seconds'],
                dict(base=I['initial_progress'],intervals=0,team=deepcopy(I['team'])),I['team'],first['tick'],first['G'],first['Q'])
            progress[name]=[clocks[name].state.progress];states[name]=[clocks[name].raw()]
        for n in range(1,max(len(s) for s in sequences.values())):
            for name,sequence in sequences.items():
                if n>=len(sequence) or clocks[name].done:continue
                endpoint=sequence[n]
                _,value,done,_=clocks[name].consume(endpoint['tick'],lambda endpoint=endpoint:dict(G=endpoint['G'],Q=endpoint['Q']))
                progress[name].append(value);states[name].append(clocks[name].raw())
                if done:completed[name]=endpoint['tick']
        denied=rejected(lambda:clocks['short_PASS'].advance(clocks['short_PASS'].tick+1,True,'PASS'))
        interruptions=clocks['interruptions'].events
        reset=next(e for e in interruptions if e.get('progress_before',0)>0)
        return dict(progress_by_sequence=progress,completion_tick=completed,completed_clock_advance='REJECT' if denied else None,
            uncredited_interval_end_ticks=[s['tick'] for s,p in zip(sequences['interruptions'][1:],progress['interruptions'][1:]) if p==0.],
            positive_progress_reset_tick=round(reset['time']/.05),independent_clock_objects=clocks['short_PASS'] is not clocks['interruptions'],
            actual_clock_states=states,actual_interruptions=interruptions,
            configuration_scope='Frozen default Config with robots3/service/angular; clock-only probe, no physical rollout')
    if number==10:
        rows={};diagnostics=[];refusals=[];unmutated=[];lasts=[]
        for variant in I['variants']:
            cap=ctx.capability(variant['fixture'],'C10:'+variant['id']);cache=ctx.cache(cap,variant['id']);c=variant['component']
            before=cache.snapshot_diagnostics()['components'];first=rejected(lambda:get(cache,c,2));after=cache.snapshot_diagnostics()['components']
            unmutated.append(typed(before)==typed(after));get(cache,c,0);get(cache,c,1);last=get(cache,c,0)
            before=cache.snapshot_diagnostics()['components'];second=rejected(lambda:get(cache,c,3));after=cache.snapshot_diagnostics()['components']
            unmutated.append(typed(before)==typed(after));require(all('GAP_REQUEST' in v['message'] for v in (first,second)),'C10 requires the frozen gap-first refusal')
            refusals.append(dict(variant=variant['id'],first=first,second=second));lasts.append(last['interval_start_tick'])
            rows[variant['id']]=prefix_rows(cache);diagnostics.append(cache.snapshot_diagnostics())
        for diag in diagnostics[1:]:exact(diag['counters'],diagnostics[0]['counters'],'C10 variant count mismatch')
        require(len(set(lasts))==1,'C10 non-tail reads differ')
        return dict(per_variant_counters=diagnostics[0]['counters'],constructed_intervals=[x['interval_start_tick'] for x in diagnostics[0]['constructed_interval_identities']],
            accepted_requested_union=sorted({x['interval_start_tick'] for x in diagnostics[0]['accepted_interval_request_identities']}),
            final_non_tail_read_returns_interval=lasts[0],rejected_gap_does_not_build=all(unmutated),rows_by_variant=rows,rejections=refusals)
    if number==11:
        from pursuit_v2.config import Config
        cfg=Config(**I['config']);variants={};results=[];counts=[]
        for variant in I['variants']:
            p=variant['target_position_now'];positions=[]
            for role in ('dual_neg45','dual_pos45'):
                offset=production.geometry.offset(role,cfg);positions.append([float(p[i]+offset[i]) for i in (0,1)])
            positions.append([2.,2.]);team=[[0,'dual_neg45'],[1,'dual_pos45']]
            fixture=dict(config=deepcopy(I['config']),start_tick=I['start_tick'],prediction_end_tick=I['after_stop_read_tick'],
                positions=positions,targets=[dict(id=0,birth=0.,position_now=deepcopy(p),velocity_now=deepcopy(I['constant_velocity']),
                    required_robots=I['q'],weight=1.,deadline=variant['deadline'],service_duration=I['H_seconds'])],
                assignment=[dict(target=0,role=r) for _,r in team]+[dict(target=None,role='none')],
                sensor_profiles=[dict(sensor_id=f'U{i}',sigma=.02,health='available',observed_tick=I['start_tick']) for i in range(3)],
                synthetic_clock=dict(base=I['initial_progress'],intervals=0,team=team),
                synthetic_retained_endpoint=dict(tick=I['start_tick'],**I['synthetic_left_endpoint']))
            # analytic_escape_time is never copied into this production fixture.
            cap=ctx.capability(fixture,'C11:'+variant['id']);cache=ctx.cache(cap,variant['id']);callback=SyntheticQuality()
            spec=descriptor(cap,0,[0,1],['dual_neg45','dual_pos45']);result=evaluate(cap,spec,cache,callback,'C11:'+variant['id'])
            first=result['frames'][1];last=result['frames'][-1];row=result['per_target']['0'];escape=row['escape_time']
            elapsed=first['control_stop_time']-first['lo_time'];types=Counter(e['type'] for e in result['events'])
            variants[variant['id']]=dict(elapsed=elapsed,energy=row['control_integral'],occupied_robot_seconds=row['occupied_robot_seconds'],
                x_increment=first['positions'][0][0]-positions[0][0],progress=row['final_progress'],
                completion_events=types['completion'],escape_events=types['escape'],release_events=types['release'],
                endpoint21_quality_calls=sum(x['frame']['tick']==21 for x in callback.calls),
                control=[first['control'][i] for i in (0,1)],raw_flow=escape-I['start_tick']*.05,
                raw_late=max(0.,escape-max(I['start_tick']*.05,variant['deadline'])),derived_escape_time=escape,
                derived_escape_f64_be=struct.pack('>d',escape).hex(),derived_elapsed=elapsed,elapsed_f64_be=struct.pack('>d',elapsed).hex(),
                requested_hi_f64_be=struct.pack('>d',first['time']).hex(),
                derived_escape_is_bitwise_endpoint=struct.pack('>d',escape)==struct.pack('>d',first['time']))
            results.append(result);counts.append(cache.snapshot_diagnostics()['counters'])
            audit_trace(cache.trace_records(),cache.snapshot_diagnostics(),candidate_results=[result])
        exact(counts[0],counts[1],'C11 interval read counts differ')
        return dict(variants=variants,next_frame_control=last['control'],next_frame_elapsed=last['control_stop_time']-last['lo_time'],
            each_variant_cache_counters=counts[0],constructed_per_member_intervals=sorted({x['interval_start_tick'] for x in cache.snapshot_diagnostics()['constructed_interval_identities']}),
            results=results)
    if number==12:
        from .common import absolute_O
        variants={}
        for v in I['variants']:
            components=production.components(I['config'],I['task'],v['start'],v['cost_stop'],False,I['energy'],v['until'])
            reason=production.termination_reason(False,v['escaped'],v['until'],I['config']['stage_dt']*I['config']['max_stages'])
            variants[v['id']]=dict(flow=components['flow'],late=components['late'],terminal=components['terminal'],
                absolute_O=absolute_O(components),termination_reason=reason,terminal_release=reason=='episode_end')
        return dict(variants=variants,real_wls_calls=ctx.wls_counts['estimator_calls'],
            component_intervals_built=sum(c.snapshot_diagnostics()['counters']['new_computed_intervals'] for c,_,_ in ctx.caches),
            original_task_count=I['config']['task_count'],weight_reference=float(4*I['config']['task_count']))
    if number==13:
        from .comparator import compare_raw
        from .comparison_checks import energy_order_witness,test_metadata
        values=ctx.comparison_inputs;raw_results={}
        for name,row in values['raw'].items():raw_results[name]=compare_raw(row['left_json'],row['right_json'],test_metadata(name))
        witness=values['arithmetic'];energy=energy_order_witness(witness['force_by_tick_robot_xy'],witness['elapsed_by_tick'])
        return dict(raw_results=raw_results,energy=energy)
    if number==14:
        from .table import restore_candidate_subset
        from .comparator import compare_raw
        from .comparison_checks import test_metadata
        cap=ctx.capability(I['fixture']);by_index={s['index']:s for s in I['candidates']};arrangements={};all_results={};comparisons=[]
        for arrangement in I['arrangements']:
            merged=[];aggregate={k:0 for k in ('accepted_interval_requests','new_computed_intervals','cache_hit_requests','rejected_requests','initial_position_reads')};created=[]
            for group_index,group in enumerate(arrangement['groups']):
                cache=ctx.cache(cap,f"C14:{arrangement['id']}:{group_index}");created.append(cache.snapshot_diagnostics())
                batch=[evaluate(cap,by_index[i],cache,SyntheticQuality(),f'C14:C{i:04d}') for i in group]
                restored=restore_candidate_subset(cap.request,batch,group,unit_fixture=cap)
                merged.extend(restored);audit_trace(cache.trace_records(),cache.snapshot_diagnostics(),candidate_results=batch)
                cache.close();refused=rejected(lambda:get(cache,dict(target_id=0,robot_id=0,role='dual_neg45'),0))
                require('CLOSED_CACHE' in refused['message'],'C14 closed handle returned or failed for wrong reason')
                for k,v in cache.snapshot_diagnostics()['counters'].items():aggregate[k]+=v
            canonical=restore_candidate_subset(cap.request,merged,list(by_index),unit_fixture=cap)
            all_results[arrangement['id']]=canonical
            arrangements[arrangement['id']]=dict(batches=len(created),counters=aggregate,
                initial_interval_counts=[r['counters']['new_computed_intervals'] for r in created])
        first=all_results['forward']
        for name in ('reverse','split'):
            result=compare_raw(json.dumps(first,allow_nan=False),json.dumps(all_results[name],allow_nan=False),test_metadata('C14:'+name))
            require(result['status']=='EQUAL','C14 scientific candidate output changed by grouping/order');comparisons.append(result)
        completion={str(r['candidate']['index']):r['per_target']['0']['completion_tick'] for r in first}
        progresses=[r['per_target']['0']['final_progress'] for r in first]
        require(len(set(progresses))==1,'C14 candidate progress differs unexpectedly')
        return dict(candidate_completion_ticks=completion,candidate_progress_at_completion=progresses[0],
            candidate_final_positions_shape=[len(first[0]['final_positions']),len(first[0]['final_positions'][0])],
            postcompletion_tick3_control_zero=all(all(v==0. for u in r['frames'][-1]['control'] for v in u) for r in first),
            arrangements=arrangements,canonical_candidate_outputs_equal=all(r['status']=='EQUAL' for r in comparisons),
            foreign_progress_or_cache_instances=sum(sum(v['initial_interval_counts']) for v in arrangements.values()),
            closed_handle_reads_rejected=sum(v['counters']['rejected_requests'] for v in arrangements.values())==sum(v['batches'] for v in arrangements.values()),
            each_new_batch_starts_with_zero_intervals=all(not any(v['initial_interval_counts']) for v in arrangements.values()),
            canonical_results=all_results,production_comparator_results=comparisons)
    raise ContractError('Unknown frozen shared short check')


def _numeric_rows(actual,expected):
    require(len(actual)==len(expected),'numeric prefix row count differs')
    for row,wanted in zip(actual,expected):
        match(row,{k:v for k,v in wanted.items() if k!='exact_algebra'})


def _verify(row,observed,comparison=None):
    """Expected values stay in this audit-only phase after observations are saved."""
    n=int(row['check_id'][1:]);E=row['expected']
    if n in (1,5):
        _numeric_rows(observed['rows'],E['rows'])
        documentary={'rows','permitted_mutation_outcomes','cache_record_forbidden_fields'}
        match(observed,{k:v for k,v in E.items() if k not in documentary})
        if n==5:
            require(not set(E['cache_record_forbidden_fields'])&set(observed['motion_cache_storage_field_names']),
                    'candidate-local state was stored in the motion cache')
    elif n==2:
        match(observed,{k:E[k] for k in ('counters','component_instances','candidate0_completion_tick','candidate2_completion_tick',
            'old_prefix_binary64_unchanged','old_prefix_digest_unchanged','candidate0_returned_frames_unchanged_after_candidate2')})
        for result,historical in zip(observed['results'],E['historical_motion_oracle']):
            saved=[{k:frame[k] for k in expected} for frame,expected in zip(result['frames'],historical['frames'])]
            exact(saved,historical['frames'],'C02 historical motion/energy bytes differ')
            require(len(result['frames'])==len(historical['frames']),'C02 dropped frames')
        first=observed['results'][0];terminal=first['per_target']['0']['completion_tick']
        frame=next(f for f in first['frames'] if f['tick']==terminal)
        require(any(v!=0. for u in frame['control'] for v in u),'C02 completion interval command was zeroed')
        require(frame['control_integral']>first['frames'][terminal-1]['control_integral'],'C02 completion interval energy was discarded')
        require(all(all(v==0. for u in f['control'] for v in u) for f in first['frames'] if f['tick']>terminal),'C02 later command not zero')
    elif n==7:
        match(observed,E)
        exact(observed['observed_U0_packet'],E['observed_U0_packet'],'C07 changed observed nonzero packet bytes')
        exact(observed['model_U2_bearing'],E['model_U2_bearing'],'C07 MODEL bearing differs')
        route=observed['production_route'];source=row['input']['assembler_inputs']
        require(set(route['entries'])=={'initialize_candidate_state','_sense','prepare_candidate_endpoint',
                'measurements.assemble_current','unit_sensing_boundary'} and all(v==2 for v in route['entries'].values()),
                'C07 actual production route is incomplete')
        require(route['two_measurement_quality_computed'] is False,'C07 invented two-measurement quality without WLS')
        for call in route['calls']:
            if call['function']!='measurements.assemble_current' or call['phase']!='ENTER':continue
            cp=call['public_request']['checkpoint']
            exact(cp['positions'],source['positions'],'C07 current positions changed before production assembly')
            exact(cp['sensor_profiles'],source['sensor_profiles'],'C07 current profiles changed before production assembly')
            exact([{k:s[k] for k in ('slot_key','state','packet')} for s in cp['current_slots']],source['current_slots'],
                  'C07 current actual-slot inputs changed before production assembly')
            require(call['unit_only'] is True and call['authority_present'] is False,'C07 fabricated main history authority')
            exact(next(t for t in cp['targets'] if t['id']==source['target_id'])['position_now'],source['target_position'],
                  'C07 target current position changed')
    elif n==10:
        for name,wanted in E['rows_by_variant'].items():_numeric_rows(observed['rows_by_variant'][name],wanted)
        match(observed,{k:v for k,v in E.items() if k!='rows_by_variant'})
    elif n==11:
        match(observed,{k:v for k,v in E.items() if k not in ('partial_exact','full_exact','same_endpoint_would_complete_if_incorrectly_credited')})
    elif n==13:
        require(comparison is not None,'C13 lacks the auditor-owned frozen comparison declaration')
        for name,result in observed['raw_results'].items():match(result,comparison['comparator_self_tests'][name]['expected'],atol=0.)
        energy=observed['energy']
        require(energy['original']['binary64_be_hex']==E['original_bits'] and energy['forbidden']['binary64_be_hex']==E['forbidden_regrouped_bits'],
                'C13 production energy reduction differs from frozen bit oracle')
        require(energy['comparison']['status']=='DIFFERENT','C13 production comparator missed reassociation')
    elif n==14:match(observed,{k:v for k,v in E.items() if k!='normal_component_rows'})
    else:match(observed,E)


def run_checks(job,out):
    from research.information_service_online.admission import forbid_solver_calls
    document=read_json(Path(job['short_file']));catalog={r['check_id']:r for r in document['checks']}
    ids=job['check_ids'];require(type(ids) is list and ids and len(ids)==len(set(ids)) and all(i in catalog for i in ids),'invalid cache check batch')
    require(type(job.get('runtime_binding_id')) is str and len(job['runtime_binding_id'])==64,'externally sealed runtime binding required')
    out=Path(out);out.mkdir(parents=True,exist_ok=True);results=[]
    for check_id in ids:
        row=catalog[check_id];I,events=deepcopy(row['input']),deepcopy(row['events'])
        require(digest(dict(input=I,events=events))==row['input_events_sha256'],'frozen short input/event bytes differ')
        before=typed_digest(dict(input=I,events=events));ctx=CaseContext(job,check_id,out/check_id);comparison=None
        if check_id=='C13':
            comparison=read_json(Path(job.get('comparison_file',I['comparison_file'])))
            witness=comparison['arithmetic_order_witnesses'][I['arithmetic_witness']]
            ctx.comparison_inputs=dict(raw={name:{k:comparison['comparator_self_tests'][name][k] for k in ('left_json','right_json')}
                for name in I['self_test_ids']},arithmetic={k:deepcopy(witness[k]) for k in ('force_by_tick_robot_xy','elapsed_by_tick')})
        try:
            with forbid_solver_calls() as counts:
                ctx.wls_counts=counts
                observed=_exercise(int(check_id[1:]),I,events,ctx)
                require(not any(counts.values()),'zero-WLS check reached estimator or native optimizer')
            save_json(ctx.out/'observed_before_comparison.json',observed)
            traces=ctx.capture();save_json(ctx.out/'cache_trace_audits.json',traces)
            require(typed_digest(dict(input=I,events=events))==before,'short exercise mutated its frozen inputs')
            _verify(row,observed,comparison)
            result=dict(check_id=check_id,passed=True,real_wls_calls=counts['estimator_calls'],
                native_optimizer_calls=counts['optimizer_start_calls'],trace_audits=traces,
                synthetic_not_actual_history=True,production_route=row['required_production_seams'])
            save_json(ctx.out/'result.json',result);results.append(result)
        except BaseException as error:
            try:save_json(ctx.out/'retained_cache_evidence.json',ctx.capture())
            except BaseException as audit_error:save_json(ctx.out/'cache_audit_failure.json',dict(type=type(audit_error).__name__,message=str(audit_error)))
            save_json(ctx.out/'failure.json',dict(error_type=type(error).__name__,error=str(error)))
            raise
    result=dict(passed=True,checks=results,real_wls_calls=sum(r['real_wls_calls'] for r in results),
        native_optimizer_calls=sum(r['native_optimizer_calls'] for r in results),scope='Production-connected explicit unit fixtures; no actual closed-loop or real localization-quality claim')
    save_json(out/'result.json',result);return result
