"""Saved-data-only cache trace audit, independent of the shared motion code.

No controller, estimator, production cache, or production comparator is imported.
Historical motion oracles enter only this audit side of the process boundary.
"""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import struct

from .common import ContractError, read_json, save_json


COUNTERS=('accepted_interval_requests','new_computed_intervals','cache_hit_requests',
          'rejected_requests','initial_position_reads')
ROLES=('dual_neg45','dual_pos45')


def _require(condition,message):
    if not condition:raise ContractError('Cache trace audit: '+message)


def typed(value):
    if value is None:return ['null']
    if type(value) is bool:return ['bool',value]
    if type(value) is int:return ['int',str(value)]
    if type(value) is float:
        _require(math.isfinite(value),'nonfinite saved float')
        return ['float',struct.pack('>d',value).hex()]
    if type(value) is str:return ['string',value]
    if type(value) is list:return ['array',[typed(v) for v in value]]
    if type(value) is dict:
        _require(all(type(k) is str for k in value),'non-string object key')
        return ['object',[[k,typed(value[k])] for k in sorted(value)]]
    raise ContractError('Cache audit received a non-JSON value: '+type(value).__name__)


def typed_digest(value):
    raw=json.dumps(typed(value),ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _same(a,b,message):
    _require(typed(a)==typed(b),message)


def _hex(value):
    _require(type(value) is float and math.isfinite(value),'interval numerical field is not finite binary64')
    return struct.pack('>d',value).hex()


def _key(component):
    _require(type(component) is dict and set(component)=={'target_id','robot_id','role'},'malformed component key')
    _require(all(type(component[k]) is int and component[k]>=0 for k in ('target_id','robot_id')),'invalid stable indices')
    _require(component['role'] in ROLES,'invalid frozen role')
    return component['target_id'],component['robot_id'],component['role']


def _component(key):return dict(target_id=key[0],robot_id=key[1],role=key[2])
def _order(key):return key[0],key[1],ROLES.index(key[2])


def _prefix(scope,key,intervals):
    return typed_digest(dict(full_scope_id=scope,component=_component(key),intervals=intervals))


def _all_prefixes(scope,prefixes,prefix_digest=_prefix):
    return typed_digest([dict(component=_component(k),prefix_digest=prefix_digest(scope,k,prefixes[k]))
                         for k in sorted(prefixes,key=_order)])


def _evidence(value):
    _require(set(value)=={'interval','binary64','interval_digest'},'interval evidence fields differ')
    row=value['interval']
    _require(set(row)=={'full_scope_id','component','interval_start_tick','interval_end_tick',
                        'x_start','u','elapsed','x_end'},'motion interval fields differ')
    _key(row['component'])
    _require(type(row['interval_start_tick']) is int and row['interval_end_tick']==row['interval_start_tick']+1,
             'interval endpoint mismatch')
    expected={name:[_hex(v) for v in row[name]] for name in ('x_start','u','x_end')}
    _require(all(len(row[name])==2 for name in ('x_start','u','x_end')),'motion vectors are not xy pairs')
    expected['elapsed']=_hex(row['elapsed'])
    _require(row['elapsed']>=0.,'negative elapsed')
    _same(value['binary64'],expected,'saved interval hex does not represent its actual numerical values')
    _require(value['interval_digest']==typed_digest(row),'interval digest differs')
    return row


def _identity(scope,key,k):
    return dict(full_scope_id=scope,component=_component(key),interval_start_tick=k)


def _prefix_state(value,scope,key,prefixes,start,prefix_digest=_prefix):
    if value is None:
        _require(key is None or key not in prefixes,'existing component prefix omitted')
        return
    actual_key=_key(value['component']);rows=prefixes.get(actual_key,[])
    if key is not None:_require(actual_key==key,'prefix belongs to another component')
    _same(value,dict(component=_component(actual_key),frontier_next=start+len(rows),
        constructed_intervals=len(rows),prefix_digest=prefix_digest(scope,actual_key,rows)),
        'component prefix state differs from independently retained rows')


def _oracle_reference(oracle,scope):
    """Read the frozen saved-R format, never the cache diagnostics format.

    Used by the real audit and the saved-data integration check. Identity and
    byte comparison remain mandatory; no component/component_key aliasing.
    """
    fields={'visibility','request_identity','world_identity','components',
            'observed_request_order','expected_component_accounting','candidate_indices','candidate_ownership'}
    _require(type(oracle) is dict and fields<=set(oracle),'oracle required fields missing')
    _require(oracle['visibility']=='AUDIT_ONLY_NOT_PREDICTOR_INPUT','oracle is not audit-only')
    _require(oracle['request_identity']==scope['evaluation_request_id']
             and oracle['world_identity']==scope['world_id'],'oracle request/world differs')
    _require(type(oracle['components']) is list,'oracle components must be a list')
    expected={};keys=set();start=scope['start_tick'];end=scope['prediction_end_tick']
    component_fields={'component_key','intervals','prefix_reference_sha256','prefix_hash_role'}
    interval_fields={'interval_start_tick','interval_end_tick','x_start_f64_be',
                     'control_f64_be','elapsed_f64_be','x_end_f64_be'}
    for component in oracle['components']:
        _require(type(component) is dict and set(component)==component_fields,
                 'oracle component fields require component_key and intervals')
        key=_key(component['component_key'])
        _require(key not in keys,'duplicate oracle component key');keys.add(key)
        rows=component['intervals']
        _require(type(rows) is list and rows,'empty/non-list oracle component prefix')
        for offset,row in enumerate(rows):
            _require(type(row) is dict and set(row)==interval_fields,'oracle interval fields differ')
            k=row['interval_start_tick'];hi=row['interval_end_tick']
            _require(type(k) is int and type(hi) is int and k==start+offset and hi==k+1 and k<end,
                     'oracle interval prefix/ticks differ')
            values=[]
            for name in ('x_start_f64_be','control_f64_be','x_end_f64_be'):
                _require(type(row[name]) is list and len(row[name])==2,'oracle binary64 vector shape differs')
                values.extend(row[name])
            values.append(row['elapsed_f64_be'])
            for value in values:
                _require(type(value) is str and len(value)==16 and all(c in '0123456789abcdef' for c in value),
                         'oracle binary64 encoding differs')
                _require(math.isfinite(struct.unpack('>d',bytes.fromhex(value))[0]),'oracle nonfinite binary64')
            _require(struct.unpack('>d',bytes.fromhex(row['elapsed_f64_be']))[0]>=0.,'oracle negative elapsed')
            expected[key+(k,)]=row
    indices=oracle['candidate_indices'];owners=oracle['candidate_ownership']
    _require(type(indices) is list and all(type(i) is int and i>=0 for i in indices)
             and len(set(indices))==len(indices),'oracle candidate indices differ')
    _require(type(owners) is list and len(owners)==len(indices),'oracle candidate ownership coverage differs')
    for index,owner in zip(indices,owners):
        _require(type(owner) is dict and {'candidate_index','candidate_id','robots','roles'}<=set(owner),
                 'oracle candidate ownership fields missing')
        _require(type(owner['candidate_index']) is int and owner['candidate_index']==index
                 and type(owner['candidate_id']) is str,'oracle candidate ownership identity differs')
    order=oracle['observed_request_order'];wanted=[];requested=set()
    _require(type(order) is list,'oracle request order must be a list')
    for row in order:
        _require(type(row) is dict and set(row)=={'candidate_index','component_key','interval_start_tick'},
                 'oracle request fields differ')
        key=_key(row['component_key']);k=row['interval_start_tick']
        _require(type(row['candidate_index']) is int and row['candidate_index'] in indices and type(k) is int
                 and key+(k,) in expected,'oracle request references an absent interval')
        requested.add(key+(k,))
        wanted.append(dict(component=row['component_key'],interval_start_tick=k))
    _require(requested==set(expected),'oracle requests do not cover component interval union')
    counts=oracle['expected_component_accounting']
    _require(type(counts) is dict and (set(COUNTERS)|{'component_instances'})<=set(counts),
             'oracle accounting fields missing')
    _require(all(type(counts[n]) is int and counts[n]>=0 for n in (*COUNTERS,'component_instances')),
             'oracle counters must be nonnegative integers')
    _require(counts['accepted_interval_requests']==len(order) and counts['new_computed_intervals']==len(expected)
             and counts['cache_hit_requests']==len(order)-len(expected) and counts['component_instances']==len(keys),
             'oracle reference accounting differs')
    return expected,wanted,counts


def audit_trace(trace_records,diagnostics,oracle=None,candidate_results=None):
    """Rebuild every prefix/count from saved events; compare optional audit oracle."""
    _require(type(trace_records) is list and trace_records,'empty/non-list cache trace')
    scope=diagnostics['scope'];sid=scope['full_scope_id'];start=scope['start_tick'];end=scope['prediction_end_tick']
    _require(sid==typed_digest({k:v for k,v in scope.items() if k!='full_scope_id'}),'scope digest differs')
    reference=_oracle_reference(oracle,scope) if oracle is not None else None
    # Only auditor-owned, deep-copied append-only prefixes enter this closure.
    # An event's claimed digest never populates it. A changed frontier gets a
    # fresh full hash; unchanged frontiers reuse the exact old digest. Lifetime
    # is one audit_trace call, including when a negative fixture raises.
    retained_digests={}
    def retained_prefix(scope_id,key,rows):
        identity=(scope_id,key,len(rows))
        if identity not in retained_digests:
            retained_digests[identity]=_prefix(scope_id,key,rows)
        return retained_digests[identity]
    prefixes={};counts={k:0 for k in COUNTERS};built=[];accepted=[];status='ABSENT';head=None
    initial_by_robot={};events=Counter()
    for index,event in enumerate(trace_records):
        _require(event['event_index']==index and event['previous_event_digest']==head,'event chain/index differs')
        _require(event['full_scope_id']==sid,'trace crossed cache scope')
        _require(event['event_digest']==typed_digest({k:v for k,v in event.items() if k!='event_digest'}),'trace event digest differs')
        _same(event['counters_before'],counts,'counters before event differ')
        _require(event['cache_status_before']==status,'cache lifecycle before event differs')
        if index==0:_require(event['prefixes_digest_before'] is None,'creation had prior prefix digest')
        else:_require(event['prefixes_digest_before']==_all_prefixes(sid,prefixes,retained_prefix),'prior prefix digest changed')
        kind=event['event'];events[kind]+=1;request=event['request'];key=None
        if request and request['method'] in ('get_interval','get_initial_position'):
            arguments=request['arguments']
            try:key=_key({k:arguments[k] for k in ('target_id','robot_id','role')})
            except (KeyError,ContractError):
                _require(kind=='REQUEST_REJECTED','invalid getter key was accepted')
        if kind!='REQUEST_REJECTED' or event['component_prefix_before'] is not None:
            _prefix_state(event['component_prefix_before'],sid,key,prefixes,start,retained_prefix)
        if kind=='CREATED':
            _require(index==0 and request is None and status=='ABSENT','invalid CREATED event')
            status='OPEN'
        elif kind=='INITIAL_POSITION_READ':
            _require(status=='OPEN' and key is not None and request['method']=='get_initial_position','invalid initial read')
            _require(request['arguments']['expected_scope_id']==sid,'foreign initial read accepted')
            position=event['returned_initial_position'];_require(len(position)==2,'initial position shape differs')
            _same(event['returned_initial_position_binary64'],[_hex(v) for v in position],'initial position hex differs')
            if key[1] in initial_by_robot:_same(position,initial_by_robot[key[1]],'robot initial position depends on key/role')
            initial_by_robot[key[1]]=deepcopy(position);counts['initial_position_reads']+=1
        elif kind in ('INTERVAL_BUILT','INTERVAL_HIT'):
            _require(status=='OPEN' and key is not None and request['method']=='get_interval','invalid interval read')
            args=request['arguments'];k=args['interval_start_tick']
            _require(args['expected_scope_id']==sid and type(k) is int and start<=k<end,'foreign/out-of-range interval accepted')
            interval=_evidence(event['interval_evidence'])
            _require(interval['full_scope_id']==sid and _key(interval['component'])==key
                     and interval['interval_start_tick']==k,'getter returned another interval')
            rows=prefixes.get(key,[])
            if kind=='INTERVAL_BUILT':
                _require(k==start+len(rows),'non-frontier interval built or duplicate build')
                if rows:_same(interval['x_start'],rows[-1]['x_end'],'component prefix position discontinuity')
                elif key[1] in initial_by_robot:_same(interval['x_start'],initial_by_robot[key[1]],'wrong component starting position')
                prefixes.setdefault(key,[]).append(deepcopy(interval));built.append(_identity(sid,key,k))
                counts['new_computed_intervals']+=1
            else:
                _require(key in prefixes and 0<=k-start<len(rows),'hit without existing interval')
                _same(interval,rows[k-start],'a hit changed existing interval bytes')
                counts['cache_hit_requests']+=1
            accepted.append(_identity(sid,key,k));counts['accepted_interval_requests']+=1
        elif kind=='REQUEST_REJECTED':
            _require(index>0 and event['rejection'] is not None,'rejection lacks cause')
            _require(event['rejection']['exception_type']=='ContractError','wrong refusal exception class')
            counts['rejected_requests']+=1
        elif kind=='CLOSED':
            _require(status=='OPEN' and request['method']=='close','close repeated or invalid')
            status='CLOSED'
        else:raise ContractError('Unknown cache trace event '+str(kind))
        if kind not in ('INTERVAL_BUILT','INTERVAL_HIT'):_require(event['interval_evidence'] is None,'non-interval event returned interval data')
        if kind!='INITIAL_POSITION_READ':
            _require(event['returned_initial_position'] is None and event['returned_initial_position_binary64'] is None,
                     'non-initial event returned position')
        if kind!='REQUEST_REJECTED':_require(event['rejection'] is None,'accepted event has rejection payload')
        _same(event['counters_after'],counts,'counters after event differ')
        _require(event['cache_status_after']==status,'cache lifecycle after event differs')
        _require(event['prefixes_digest_after']==_all_prefixes(sid,prefixes,retained_prefix),'new prefix digest differs')
        if kind!='REQUEST_REJECTED' or event['component_prefix_after'] is not None:
            _prefix_state(event['component_prefix_after'],sid,key,prefixes,start,retained_prefix)
        head=event['event_digest']
    _same(diagnostics['counters'],counts,'final diagnostic counters differ')
    _require(diagnostics['cache_status']==status and diagnostics['trace_record_count']==len(trace_records)
             and diagnostics['trace_head_digest']==head,'final lifecycle/trace head differs')
    _require(diagnostics['diagnostics_digest']==typed_digest({k:v for k,v in diagnostics.items() if k!='diagnostics_digest'}),
             'diagnostic digest differs')
    _same(diagnostics['constructed_interval_identities'],built,'diagnostics hide/change actual builds')
    _same(diagnostics['accepted_interval_request_identities'],accepted,'diagnostics hide/change accepted requests')
    _require(len({typed_digest(v) for v in built})==len(built),'duplicate construction identity')
    _require({typed_digest(v) for v in built}=={typed_digest(v) for v in accepted},'build set differs from accepted request union')
    _require(counts['accepted_interval_requests']==counts['new_computed_intervals']+counts['cache_hit_requests'],'request accounting identity failed')
    _require(diagnostics['component_instances']==len(prefixes)==len(diagnostics['components']),'component census differs')
    _require([_key(c['component']) for c in diagnostics['components']]==sorted(prefixes,key=_order),'diagnostic component order differs')
    for component in diagnostics['components']:
        key=_key(component['component']);rows=prefixes[key]
        _same([_evidence(r) for r in component['intervals']],rows,'diagnostic prefix differs from observed event history')
        _require(component['frontier_next']==start+len(rows) and component['prefix_digest']==retained_prefix(sid,key,rows),'final prefix state differs')
        _same(component['initial_position'],rows[0]['x_start'],'diagnostic initial position differs')
        _same(component['initial_position_binary64'],[_hex(v) for v in rows[0]['x_start']],'diagnostic initial bytes differ')
    candidate_summary=_audit_candidate_reads(candidate_results,prefixes,accepted,start) if candidate_results is not None else None
    if oracle is not None:
        expected,wanted,reference_counts=reference
        if candidate_results is not None:
            actual_owners=[dict(candidate_index=r['candidate']['index'],candidate_id=r['candidate_identity'],
                robots=r['candidate']['robots'],roles=r['candidate']['roles']) for r in candidate_results]
            wanted_owners=[{k:o[k] for k in ('candidate_index','candidate_id','robots','roles')}
                           for o in oracle['candidate_ownership']]
            _same(actual_owners,wanted_owners,'oracle candidate ownership differs from actual batch')
            request_candidates=[r['candidate']['index'] for r in candidate_results
                for frame in r['frames'][1:] if frame['control_stop_time']>frame['lo_time']
                for _ in r['candidate']['robots']]
            _same(request_candidates,[r['candidate_index'] for r in oracle['observed_request_order']],
                  'oracle request candidate identity/order differs')
        observed={}
        for key,rows in prefixes.items():
            for row in rows:
                observed[key+(row['interval_start_tick'],)]=dict(interval_start_tick=row['interval_start_tick'],
                    interval_end_tick=row['interval_end_tick'],x_start_f64_be=[_hex(v) for v in row['x_start']],
                    control_f64_be=[_hex(v) for v in row['u']],elapsed_f64_be=_hex(row['elapsed']),x_end_f64_be=[_hex(v) for v in row['x_end']])
        _require(observed==expected,'cache bytes differ from independent saved-R oracle')
        actual=[{k:r[k] for k in ('component','interval_start_tick')} for r in accepted]
        _same(actual,wanted,'cache request order differs from full-candidate oracle')
        for name in COUNTERS:_require(counts[name]==reference_counts[name],'oracle counter mismatch: '+name)
    return dict(passed=True,counters=counts,component_instances=len(prefixes),events=dict(events),
        observed_trace_records=len(trace_records),constructed_set_equals_accepted_request_union=True,
        old_prefix_bytes_reconstructed_independently=True,oracle_compared=oracle is not None,
        candidate_prefix_audit=candidate_summary,real_wls_calls=0,
        scope='Saved cache events, interval bytes and candidate frames only; no production cache/controller/estimator rerun')


def _audit_candidate_reads(results,prefixes,accepted,start):
    wanted=[];candidate_ids=[]
    for result in results:
        spec=result['candidate'];candidate_ids.append(result['candidate_identity']);frames=result['frames']
        robots,roles=spec['robots'],spec['roles'];x=len(frames[0]['positions']);ended=False
        for before,after in zip(frames,frames[1:]):
            _require(len(after['positions'])==len(after['control'])==x,'candidate shrank complete Uk arrays')
            elapsed=max(0.,after['control_stop_time']-after['lo_time'])
            if elapsed>0.:
                _require(not ended,'candidate consumed cache after terminal service')
                for robot,role in zip(robots,roles):
                    key=(spec['target'],robot,role);k=before['tick'];row=prefixes[key][k-start]
                    _same(before['positions'][robot],row['x_start'],'candidate/cache start position differs')
                    _same(after['positions'][robot],row['x_end'],'candidate/cache end position differs')
                    _same(after['control'][robot],row['u'],'completion/active interval command was cleared or changed')
                    _same(elapsed,row['elapsed'],'candidate/cache elapsed differs')
                    wanted.append(dict(component=_component(key),interval_start_tick=k))
            elif ended:
                _same(after['positions'],before['positions'],'postterminal positions moved')
                _require(all(_hex(v)=='0000000000000000' for row in after['control'] for v in row),'postterminal command not positive zero')
                _same(after['control_integral'],before['control_integral'],'postterminal energy changed')
            status=after['status'][str(spec['target'])]
            ended=ended or status in ('completed','escaped','unfinished')
    actual=[{k:r[k] for k in ('component','interval_start_tick')} for r in accepted]
    _same(actual,wanted,'cache requests differ from complete candidate active-interval reads')
    return dict(candidates=len(results),candidate_ids=candidate_ids,interval_component_reads=len(wanted),
                completion_interval_retained=True,postterminal_motion_and_energy_frozen=True)


def audit_batch(job,out):
    path=Path(job['cache_trace_file']);raw=path.read_text()
    trace=json.loads(raw) if raw.lstrip().startswith('[') else [json.loads(line) for line in raw.splitlines() if line.strip()]
    diagnostics=read_json(Path(job['cache_diagnostics_file']))
    oracle=read_json(Path(job['oracle_file'])) if job.get('oracle_file') else None
    results=[read_json(Path(p)) for p in job['candidate_result_files']] if 'candidate_result_files' in job else None
    result=audit_trace(trace,diagnostics,oracle,results)
    save_json(Path(out)/'cache_trace_audit.json',result)
    return result


def audit_ownership(records,request,candidates,scope_id):
    """Check saved production ownership records; tokens alone prove no aliasing.

    Candidates are the exact descriptor/legacy-spec subset evaluated by this
    batch. Simultaneously live mutable/storage independence is tested by C05.
    """
    cp=request.get('checkpoint',request);expected={}
    for candidate in candidates:
        if 'candidate_id' in candidate:
            identifier=candidate['candidate_id'];key=candidate['key']
        else:
            identifier=candidate['candidate_identity'];key=candidate['structural_key']
        _require(identifier not in expected,'duplicate ownership candidate declaration')
        expected[identifier]=key
    _require(type(records) is list and len(records)==len(expected),'ownership coverage differs from batch candidates')
    tokens=set();observed=set();instance_ids=set();alias_checks=0
    for record in records:
        cid=record['candidate_id'];_require(cid in expected and cid not in observed,'duplicate/foreign ownership record')
        observed.add(cid);_same(record['candidate_key'],expected[cid],'ownership key differs')
        _require(record['full_scope_id']==scope_id,'ownership record belongs to another scope')
        _same(record['positions_shape'],[len(cp['positions']),2],'ownership shrank complete X-by-2 positions')
        _require(record['initial_positions_typed_digest']==typed_digest(cp['positions']),'ownership started from another position state')
        iid=record['candidate_instance_id'];_require(type(iid) is str and iid and iid not in instance_ids,'duplicate/missing candidate instance identity')
        instance_ids.add(iid)
        for name in ('positions_storage_token','clock_instance_token','events_storage_token','metrics_storage_token'):
            token=record[name];_require(type(token) is str and token and token not in tokens,'duplicate/missing ownership storage token')
            tokens.add(token)
    for record in records:
        for check in record['observed_alias_checks']:
            _require(check['left_storage_token'] in tokens and check['right_storage_token'] in tokens,'alias check names unrecorded live objects')
            _require(check['shares_storage'] is False,'production ownership record reports storage aliasing')
            alias_checks+=1
    return dict(passed=True,candidate_records=len(records),full_robot_rows=len(cp['positions']),
        observed_alias_checks=alias_checks,token_uniqueness_is_not_alias_proof=True,
        simultaneous_storage_independence_scope='Only actual simultaneously live production-workspace checks in C05 establish that separate unit witness')
