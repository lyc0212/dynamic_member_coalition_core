"""Task-local L3-B recovery. Importing this file never runs archived replay."""
from __future__ import annotations
import ast
import copy
import dataclasses
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import json
import math
from pathlib import Path
import struct
import sys
import time

HISTORICAL_COMMIT = '98ed1160d9aba266d36cc263d95cfbeecef865e9'
PROJECT_PACKAGES = {'research', 'pursuit_v2', 'scripts'}


def require(ok, code):
    if not ok:
        raise RuntimeError(code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def typed(value):
    """Exact snapshots; preserve type, signed zero and ndarray representation."""
    if dataclasses.is_dataclass(value):
        return (type(value).__module__, type(value).__qualname__, tuple((f.name, typed(getattr(value, f.name))) for f in dataclasses.fields(value)))
    if hasattr(value, 'dtype') and hasattr(value, 'shape') and hasattr(value, 'tobytes'):
        require(not value.dtype.hasobject, 'OBJECT_ARRAY_NOT_SUPPORTED')
        return ('array', type(value).__module__, str(value.dtype), tuple(value.shape), value.tobytes(order='C'))
    if type(value) is float:
        return ('float', struct.pack('!d', value))
    if isinstance(value, (set, frozenset)):
        return (type(value).__name__, tuple(sorted((typed(v) for v in value),key=repr)))
    if isinstance(value, dict):
        return ('dict', tuple((typed(k), typed(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return (type(value).__name__, tuple(typed(v) for v in value))
    if value is None or type(value) in (bool, int, str, bytes):
        return (type(value).__name__, value)
    raise TypeError('UNREGISTERED_SNAPSHOT_TYPE/' + type(value).__name__)


def plain(value):
    if dataclasses.is_dataclass(value):
        return {f.name: plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if hasattr(value, 'tolist'):
        return plain(value.tolist())
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if isinstance(value,(set,frozenset)):return [plain(v) for v in sorted(value,key=repr)]
    return value


def same(a, b, code='STATE_CONTINUITY'):
    require(typed(a) == typed(b), code)


class Writer:
    """Controlled logical writes; actual returned bytes accumulate without refunds."""
    def __init__(self,root,limit=134217728,initial_written=0,clock=None):
        self.root=Path(root).resolve();self.limit=limit;self.written=initial_written;self.complete=True;self.operations=[];self.clock=clock;self.peak_live_bytes=0
    def write(self,relative,payload,*,replace=False,append=False):
        if self.clock:self.clock.check()
        p=(self.root/relative).resolve();require(p.is_relative_to(self.root),'OUTPUT_OUTSIDE_ROOT');require(not(replace and append),'WRITE_MODE')
        data=payload if isinstance(payload,bytes) else payload.encode('utf-8')
        require(self.written+len(data)<=self.limit,'CUMULATIVE_WRITE_LIMIT');p.parent.mkdir(parents=True,exist_ok=True)
        offset=0
        try:
            with p.open('ab' if append else 'wb' if replace else 'xb',buffering=0) as stream:
                while offset<len(data):
                    n=stream.write(data[offset:]);require(type(n) is int and 0<n<=len(data)-offset,'SHORT_WRITE')
                    self.written+=n;offset+=n
                    if self.clock:self.clock.check()
        except BaseException:
            self.complete=False;raise
        self.operations.append(dict(path=relative,bytes=offset,mode='append' if append else 'replace' if replace else 'new'))
        self.peak_live_bytes=max(self.peak_live_bytes,sum(f.stat().st_size for f in self.root.rglob('*') if f.is_file()))
        return offset
    def json(self,relative,value):return self.write(relative,json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False))
    def accounting_receipt(self,relative,value):
        # Find the encoded length before writing; confirm actual full write afterwards.
        base=self.written;record=dict(value);total=base
        for _ in range(20):
            record['cumulative_logical_write_bytes']=total
            data=json.dumps(record,ensure_ascii=False,indent=2,allow_nan=False).encode();new=base+len(data)
            if new==total:break
            total=new
        else:raise RuntimeError('RECEIPT_SIZE_FIXED_POINT')
        self.write(relative,data);require(self.written==total,'FINAL_WRITE_ACCOUNTING');return record


class Clock:
    def __init__(self,wall_start,*,cpu_limit=300,wall_limit=1800):
        self.wall_start=wall_start;self.deadline=wall_start+wall_limit;self.cpu_limit=cpu_limit
    def check(self):
        require(time.monotonic()<self.deadline,'WALL_LIMIT')
        require(time.process_time()<self.cpu_limit,'CPU_LIMIT')




class HistoricalImports(importlib.abc.MetaPathFinder):
    """Only project imports are restricted; not a general security framework."""
    def __init__(self, historical_root, pins):
        self.root = Path(historical_root).resolve()
        self.pins = pins
        self.modules = {}
        self.namespace_paths = {}

    def validate(self, name, spec):
        if spec.origin and spec.origin not in ('built-in', 'frozen'):
            p = Path(spec.origin).resolve()
            require(p.is_relative_to(self.root), 'CURRENT_PROJECT_IMPORT/' + name)
            rel = p.relative_to(self.root).as_posix()
            require(rel in self.pins, 'UNREGISTERED_PROJECT_DEPENDENCY/' + rel)
            require(hashlib.sha256(p.read_bytes()).hexdigest() == self.pins[rel]['sha256'], 'IMPORT_HASH/' + rel)
            self.modules[name] = dict(path=str(p), **self.pins[rel])
        locations=list(spec.submodule_search_locations or ())
        for location in locations:
            require(Path(location).resolve().is_relative_to(self.root), 'NAMESPACE_FALLBACK/' + name)
        if not spec.origin and locations:self.namespace_paths[name]=[str(Path(p).resolve()) for p in locations]

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] not in PROJECT_PACKAGES:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        require(spec is not None, 'MISSING_HISTORICAL_DEPENDENCY/' + fullname)
        self.validate(fullname, spec)
        return spec

    def install(self):
        require(not any(n.split('.')[0] in PROJECT_PACKAGES for n in sys.modules), 'PROJECT_ALREADY_IMPORTED')
        sys.path.insert(0, str(self.root))
        sys.meta_path.insert(0, self)

    def audit(self):
        for name, module in list(sys.modules.items()):
            if name.split('.')[0] in PROJECT_PACKAGES and getattr(module, '__spec__', None):
                self.validate(name, module.__spec__)
        return self.modules


class Replay:
    """Independent conditional replay; historical identities are never fabricated."""
    def __init__(self, seed, announcements=None, identity_bindings=None):
        required=('announcements','internal_states_at_D60','accepted_position_history','accepted_receipts','pending_observations','consumed_records')
        require(all(k in seed for k in required),'CONSUMER_SEED_INCOMPLETE')
        if announcements is not None:
            require(plain(announcements)==plain(seed['announcements']),'ANNOUNCEMENT_SEED_MISMATCH')
        self.announcements=copy.deepcopy(seed['announcements'])
        self.states={int(k):copy.deepcopy(v) for k,v in seed['internal_states_at_D60'].items()}
        self.history={int(k):copy.deepcopy(v) for k,v in seed['accepted_position_history'].items()}
        self.accepted_receipts={int(k):copy.deepcopy(v) for k,v in seed['accepted_receipts'].items()}
        self.receipts=self.accepted_receipts
        self.pending=copy.deepcopy(seed['pending_observations'])
        self.consumed=copy.deepcopy(seed['consumed_records'])
        self.used=set();self.enqueued=set();self.audit_rows=[];self.model_measurements=[]
        self.unresolved_consumed=[];self.last_freeze=None
        self.seed_identifiability=dict(state='AVAILABLE',initial_pending='AVAILABLE',pre_d60='SOURCE_UNRESOLVED')
        bindings=identity_bindings or {}
        def identity(row):
            direct=row.get('identity') or row.get('feedback_identity')
            if direct and direct!='SOURCE_UNRESOLVED':return direct
            matches=bindings.get(digest(row),[])
            require(len(matches)<=1,'NOT_IDENTIFIABLE:AMBIGUOUS_SEED_IDENTITY')
            if not matches:return None
            m=matches[0]
            require(isinstance(m,dict) and m.get('record_locator') and len(m.get('source_sha256',''))==64,'IDENTITY_BINDING_EVIDENCE_MISSING')
            return m['identity']
        for row in self.consumed:
            i=identity(row)
            if i is None:self.unresolved_consumed.append(copy.deepcopy(row))
            else:
                require(i not in self.used,'DUPLICATE_SEED_CONSUMPTION');self.used.add(i)
        for row in self.pending:
            i=identity(row)
            require(i is not None,'NOT_IDENTIFIABLE:INITIAL_PENDING_IDENTITY')
            require(i not in self.used and i not in self.enqueued,'DUPLICATE_INITIAL_PENDING')
            row['identity']=i;self.enqueued.add(i)
        require(set(self.history)==set(self.states),'SEED_HISTORY_TARGETS')

    def enqueue(self,event):
        require(event.get('source','MODEL')=='MODEL' and event.get('observation_origin')=='MODEL' and event.get('provenance')=='SIMULATED','MODEL_SOURCE')
        require(type(event.get('measurement_tick')) is int and type(event.get('available_tick')) is int,'OBSERVATION_TIME_TYPE')
        require(event['available_tick']>=event['measurement_tick'],'NEGATIVE_LATENCY')
        require(int(event['target_id']) in self.states,'UNANNOUNCED_TARGET')
        i=event.get('identity');require(isinstance(i,str) and i,'EVENT_IDENTITY_MISSING')
        require(i not in self.used,'ALREADY_CONSUMED');require(i not in self.enqueued,'DUPLICATE_ENQUEUE')
        for old in self.unresolved_consumed:
            collision=all(old.get(k)==event.get(k) for k in ('target_id','measurement_tick','available_tick'))
            if collision:
                proof=event.get('post_seed_evidence',{})
                require(proof.get('branch') and proof.get('frame_id')==i and len(proof.get('source_sha256',''))==64,'NOT_IDENTIFIABLE:HISTORICAL_CONSUMPTION_COLLISION')
        self.enqueued.add(i);self.pending.append(copy.deepcopy(event));self.model_measurements.append(copy.deepcopy(event))

    def freeze(self,tick):
        require(type(tick) is int and tick>=0 and tick!=120,'INVALID_OR_TERMINAL_FREEZE')
        require(self.last_freeze is None or tick>self.last_freeze,'FREEZE_ORDER')
        remaining=[]
        for ordinal,row in enumerate(self.pending):
            if row['available_tick']>tick:
                remaining.append(row);continue
            i=row['identity'];require(i not in self.used,'DUPLICATE_CONSUMPTION')
            j=int(row['target_id']);require(j in self.states,'UNANNOUNCED_TARGET')
            e=row['estimate'];b=self.states[j];hist=self.history[j]
            before_history=copy.deepcopy(hist);before_state=copy.deepcopy(b);before_receipts=copy.deepcopy(self.accepted_receipts)
            reasons=[]
            if e is None:reasons=['ESTIMATE_MISSING']
            else:
                if not e.get('has_accepted_estimate'):reasons.append('NO_ACCEPTED_ESTIMATE')
                if not e.get('optimizer_converged'):reasons.append('OPTIMIZER_NOT_CONVERGED')
                reasons += [k.upper() for k in ('numerical_ill_conditioned','ambiguity_detected','boundary_active','numeric_contract_violation') if e.get(k,True)]
                if not reasons:
                    p=e['estimate'];t=row['measurement_tick']
                    if len(p)!=2:reasons=['INVALID_ESTIMATE_DIMENSION']
                    elif not all(type(x) in (int,float) and math.isfinite(x) for x in p):reasons=['NONFINITE_ESTIMATE']
                    elif hist and t<=hist[-1][0]:reasons=['NONINCREASING_MEASUREMENT_TICK']
            receipt=dict(target_id=j,measurement_tick=row['measurement_tick'],available_tick=row['available_tick'],consumed_tick=tick)
            self.used.add(i);self.consumed.append(receipt)
            reference=None;raw_velocity=None;clipped=False
            if not reasons:
                p=e['estimate'];t=row['measurement_tick'];reference=next(((s,q) for s,q in reversed(hist) if t-s>=5),None)
                velocity=list(b['velocity_estimate'])
                if reference:
                    s,q=reference;velocity=[(x-y)/((t-s)*.05) for x,y in zip(p,q)];raw_velocity=list(velocity)
                    limit=next(a['speed_limit'] for a in self.announcements if a['id']==j);speed=math.hypot(*velocity)
                    if speed>limit:velocity=[v*limit/speed for v in velocity];clipped=True
                hist.append((t,list(p)));self.accepted_receipts[j]=receipt.copy()
                b.update(estimate_tick=t,available_tick=row['available_tick'],position_estimate=list(p),velocity_estimate=velocity,velocity_source='ACTUAL_POSITION_DIFFERENCE' if reference else b['velocity_source'],last_observation_tick=t,source='ACTUAL_WLS',status='OBSERVED',diagnostics=copy.deepcopy(e))
            else:
                same(hist,before_history,'REJECTED_HISTORY_CHANGED');same(b,before_state,'REJECTED_STATE_CHANGED');same(self.accepted_receipts,before_receipts,'REJECTED_RECEIPT_CHANGED')
            self.audit_rows.append(dict(identity=i,freeze_id=tick,freeze_ordinal=ordinal,consumption_ordinal=len(self.consumed)-1,accepted=not reasons,reasons=reasons,receipt=receipt,observation_origin=row.get('observation_origin'),provenance=row.get('provenance'),generation_ordinal=row.get('generation_ordinal','NOT_IDENTIFIABLE'),enqueue_ordinal=row.get('enqueue_ordinal','NOT_IDENTIFIABLE'),before_state=before_state,after_state=copy.deepcopy(b),accepted_count=len(hist),first_accepted_tick=hist[0][0] if hist else None,last_accepted_tick=hist[-1][0] if hist else None,reference_tick=reference[0] if reference else None,reference_interval=row['measurement_tick']-reference[0] if reference else None,velocity_before=before_state['velocity_estimate'],velocity_after=b['velocity_estimate'],unclipped_velocity=raw_velocity,clipped=clipped,velocity_source=b['velocity_source']))
        self.pending=remaining;self.last_freeze=tick
        result=copy.deepcopy(self.states)
        for b in result.values():
            if b['last_observation_tick'] is not None and tick-b['last_observation_tick']>20:b['status']='DEGRADED'
        return result

    def terminal(self,tick=120):
        require(tick==120,'TERMINAL_TICK');return dict(states=copy.deepcopy(self.states),pending=copy.deepcopy(self.pending),consumed=copy.deepcopy(self.consumed),source_limit=self.seed_identifiability['pre_d60'])


def source_order_evidence(historical_root,pins):
    rel='research/non_oracle/stfbs_d1a_model.py';p=Path(historical_root)/rel;raw=p.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==pins[rel]['sha256'],'GENERATION_SOURCE_IDENTITY')
    tree=ast.parse(raw);branch=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Branch')
    fuse=next(n for n in branch.body if isinstance(n,ast.FunctionDef) and n.name=='fuse')
    calls=[]
    for index,stmt in enumerate(fuse.body):
        for n in ast.walk(stmt):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute):
                text=ast.unparse(n.func)
                if text in ('self.consumer.enqueue','self.feedback.append'):calls.append((text,index,n.lineno))
    require(len(calls)==2 and calls[0][0]=='self.consumer.enqueue' and calls[1][0]=='self.feedback.append' and calls[0][1]==calls[1][1]-1,'GENERATION_ENQUEUE_ORDER_NOT_PROVEN')
    mutations=[]
    for n in ast.walk(branch):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and ast.unparse(n.func.value)=='self.feedback':mutations.append(n.func.attr)
    require(mutations==['append'],'FEEDBACK_REORDER_PATH')
    return dict(kind='FROZEN_SYNCHRONOUS_ENQUEUE_THEN_APPEND',source_sha256=pins[rel]['sha256'],commit=pins[rel]['commit'],blob=pins[rel]['blob'],locations=calls,pre_d60='SOURCE_UNRESOLVED')


def event_catalog(raw,transactions,snapshots,committed_connections,*,order_evidence,initial_pending=(),terminal_pending=None):
    """Read-only catalog checks; callers need separate archived-replay authorization."""
    require(order_evidence.get('kind')=='FROZEN_SYNCHRONOUS_ENQUEUE_THEN_APPEND' and len(order_evidence.get('source_sha256',''))==64,'ORDER_EVIDENCE_NOT_VERIFIED')
    require(raw['provenance']=='SIMULATED' and raw['observation_origin']=='MODEL','RAW_SOURCE')
    require(set(transactions)>={60,80,100},'TRANSACTION_DIRECTORY_INCOMPLETE')
    require(raw['endpoint_fusions']==len(raw['feedback']),'FUSION_DIRECTORY_COUNT')
    grouped={}
    for c in committed_connections:grouped.setdefault(c['feedback_event_ordinal'],[]).append(c)
    require(set(grouped)==set(range(len(raw['feedback']))),'COMMITTED_DIRECTORY_COMPLETENESS')
    events=[];identities=set()
    def archive_tick(value):
        require(type(value) in (int,float) and math.isfinite(value),'FRAME_TIME')
        tick=round(value/.05);require(abs(tick*.05-value)<=1e-10,'FRAME_TIME_ALIGNMENT');return tick
    for generation,f in enumerate(raw['feedback']):
        fr=f['frame'];ep=f['endpoint'];identity=fr['frame_id'];links=grouped[generation]
        require(identity not in identities,'DUPLICATE_FRAME');identities.add(identity)
        require(ep['target_id']==fr['target_id'] and ep['tick']==fr['tick'],'FRAME_ENDPOINT_BINDING')
        require(ep['provenance']=='SIMULATED' and ep['observation_origin']=='MODEL','ENDPOINT_SOURCE')
        for c in links:
            require(c['feedback_digest']==digest(f) and c['frame_id']==identity and c['target_id']==fr['target_id'] and c['tick']==fr['tick'],'CONNECTION_BINDING')
        phases={(c['transaction_identity'],c['endpoint_side']) for c in links};require(len(phases)==1,'GENERATION_PHASE_AMBIGUOUS')
        transaction,phase=next(iter(phases));require(phase in ('MODEL_INTERVAL_RIGHT','MODEL_ASSIGNMENT_LEFT'),'GENERATION_PHASE')
        require(transaction==raw['branch']+(':ADVANCE:' if phase=='MODEL_INTERVAL_RIGHT' else ':ASSIGN:')+str(fr['tick']),'GENERATION_TRANSACTION')
        measurement=archive_tick(fr['measurement_time']);available=archive_tick(fr['available_time'])
        require(measurement==fr['tick'] and available>=measurement,'FRAME_TIME_BINDING')
        for packet in fr.get('records',[]):
            require(packet['measurement_tick']==measurement and packet['available_tick']<=available and packet['available_tick']>=measurement,'PACKET_TIME_BINDING')
        events.append(dict(identity=identity,generation_ordinal=generation,phase=phase,transaction_identity=transaction,frame_tick=fr['tick'],target_id=fr['target_id'],measurement_tick=measurement,available_tick=available,source='MODEL',observation_origin='MODEL',provenance='SIMULATED',estimate=copy.deepcopy(f['result']['estimate_result']),feedback_digest=digest(f),post_seed_evidence=dict(branch=raw['branch'],frame_id=identity,source_sha256=order_evidence['source_sha256'])))
    # Equal ordinal values are derived only after the frozen synchronous path is checked.
    enqueue_ids=[e['identity'] for e in events]
    enqueue_map={identity:ordinal for ordinal,identity in enumerate(enqueue_ids)}
    for e in events:e['enqueue_ordinal']=enqueue_map[e['identity']]
    for tick,tx in transactions.items():
        require(tx['transaction_identity']==raw['branch']+':ASSIGN:'+str(tick),'TRANSACTION_IDENTITY')
        expected=[e['generation_ordinal'] for e in events if e['phase']=='MODEL_ASSIGNMENT_LEFT' and e['frame_tick']==tick]
        require(tx['committed_feedback_ordinals']==expected,'TRANSACTION_COMMIT_COMPLETENESS')
        for c in tx['connections']:
            require(c in grouped.get(c['feedback_event_ordinal'],[]),'TRANSACTION_CONNECTION_MISSING')
        require(set(expected)<=set(c['feedback_event_ordinal'] for c in tx['connections']),'TRANSACTION_COMMIT_CONNECTIONS')
    known={e['identity']:e for e in events};previous=set();initial=[]
    for row in initial_pending:
        require(row.get('identity'),'NOT_IDENTIFIABLE:INITIAL_PENDING');require(row['identity'] not in known,'SEED_GENERATION_OVERLAP');initial.append(copy.deepcopy(row))
    def pending_key(row):return (int(row['target_id']),row['measurement_tick'],row['available_tick'],digest(row.get('estimate')))
    for tick,snapshot in sorted(snapshots.items()):
        eligible=initial+[e for e in events if e['frame_tick']<tick or (e['frame_tick']==tick and e['phase']=='MODEL_INTERVAL_RIGHT')]
        queue=[e for e in eligible if e['identity'] not in previous]
        consumed=[(ordinal,e) for ordinal,e in enumerate(queue) if e['available_tick']<=tick]
        pending=[e for e in queue if e['available_tick']>tick]
        archived=[e for e in snapshot['events'] if e.get('consumed_tick')==tick]
        require(len(archived)==len(consumed),'QUEUE_CONSUMPTION_COUNT')
        for n,(ordinal,e) in enumerate(consumed):
            a=archived[n]
            require(a.get('feedback_identity',a.get('identity'))==e['identity'],'QUEUE_CONSUMPTION_ORDER')
            require(e['feedback_digest']==a['feedback_digest'] and int(a['target_id'])==int(e['target_id']) and e['measurement_tick']==a['measurement_tick'] and e['available_tick']==a['available_tick'],'EVENT_BINDING')
            require(a['queue_ordinal']==ordinal and a['available_tick']<=tick,'FREEZE_ORDINAL_OR_TIME')
            require(e['identity'] not in previous,'DUPLICATE_CONSUMPTION');previous.add(e['identity'])
        require([pending_key(e) for e in pending]==[pending_key(e) for e in snapshot['pending']],'PENDING_QUEUE_MISMATCH')
    if terminal_pending is not None:
        rest=initial+[e for e in events if e['identity'] not in previous]
        rest=[e for e in rest if e['identity'] not in previous]
        require([pending_key(e) for e in rest]==[pending_key(e) for e in terminal_pending],'TERMINAL_QUEUE_MISMATCH')
    return dict(events=events,order_evidence=order_evidence,completeness='VERIFIED_WITHIN_FROZEN_COMMITTED_BRANCH',pre_d60='SOURCE_UNRESOLVED',terminal_consumption_added=False)


def verify_replay_snapshot(consumer,snapshot,control_snapshot=None,expected_control=None):
    for actual,key in ((consumer.states,'states'),(consumer.history,'accepted_history'),(consumer.accepted_receipts,'accepted_receipts')):
        require(plain(actual)==snapshot[key],'ARCHIVED_'+key.upper())
    # Identity metadata added by the adapter does not change original pending semantics.
    def row_core(r):return {k:plain(r[k]) for k in ('target_id','measurement_tick','available_tick','estimate')}
    require([row_core(r) for r in consumer.pending]==[row_core(r) for r in snapshot['pending']],'ARCHIVED_PENDING')
    expected=[e for e in snapshot['events'] if e.get('consumed_tick')==snapshot['tick']]
    observed=[e for e in consumer.audit_rows if e['freeze_id']==snapshot['tick']]
    require(len(expected)==len(observed),'ARCHIVED_CONSUMPTION_COUNT')
    for a,b in zip(observed,expected):
        require(a['identity']==b['feedback_identity'] and a['accepted']==b['accepted'] and a['reasons']==b['rejection_conditions'] and a['freeze_ordinal']==b['queue_ordinal'],'ARCHIVED_ACCEPTANCE')
    if expected_control is not None:require(plain(control_snapshot)==plain(expected_control),'ARCHIVED_CONTROL_SNAPSHOT')
    return dict(status='VERIFIED',tick=snapshot['tick'],events=len(observed))


PHYSICAL=('positions','states','lefts','geometry_before','statuses','tasks','effort')
BELIEF_FIELDS={'estimate_tick','available_tick','position_estimate','velocity_estimate','velocity_source','last_observation_tick','source','status','diagnostics'}


def validate_state(physical,beliefs):
    require(set(PHYSICAL)<=set(physical),'SNAPSHOT_FIELD_MISSING')
    positions=physical['positions']
    if hasattr(positions,'shape'):
        require(tuple(positions.shape)==(3,2) and positions.dtype.kind=='f','POSITION_ARRAY_CONTRACT')
        rows=positions.tolist()
    else:rows=positions
    require(len(rows)==3 and all(len(r)==2 for r in rows),'POSITION_SHAPE')
    require(all(type(v) in (int,float) and math.isfinite(v) for r in rows for v in r),'POSITION_FINITE')
    require(type(physical['effort']) in (int,float) and math.isfinite(physical['effort']) and physical['effort']>=0,'EFFORT_VALIDITY')
    for state in physical['states'].values():
        require(type(state.base) in (int,float) and math.isfinite(state.base) and state.base>=0,'CLOCK_BASE')
        require(type(state.intervals) is int and state.intervals>=0 and isinstance(state.team,tuple),'CLOCK_CONTRACT')
    for table in ('lefts','geometry_before'):require(all(type(x) is bool for x in physical[table].values()),'ENDPOINT_VALIDITY')
    for task in physical['tasks'].values():
        for key in ('P0','Pmax','duration','stop_time'):
            require(type(task[key]) in (int,float) and math.isfinite(task[key]),'TASK_NUMERIC/'+key)
        require(type(task['NG']) is int and task['NG']>=0,'NG_TYPE')
        require(task['completion_tick'] is None or type(task['completion_tick']) is int,'COMPLETION_TICK')
    for b in beliefs.values():
        require(type(b['estimate_tick']) is int and type(b['available_tick']) is int,'BELIEF_TIME_TYPE')
        require(b['last_observation_tick'] is None or type(b['last_observation_tick']) is int,'OBSERVATION_TIME_TYPE')
        for key in ('position_estimate','velocity_estimate'):
            require(len(b[key])==2 and all(type(v) in (int,float) and math.isfinite(v) for v in b[key]),'BELIEF_NUMERIC/'+key)


def _consumer_state(consumer):
    return None if consumer is None else copy.deepcopy(vars(consumer))


def _verify_consumer_mutations(before,consumer):
    after=vars(consumer)
    require(set(before)==set(after),'CONSUMER_FIELD_SET_CHANGED')
    allowed={'states','history','receipts','accepted_receipts','pending','consumed','used','enqueued','audit_rows','model_measurements','last_freeze'}
    for key in before:
        if key not in allowed:same(before[key],after[key],'CONSUMER_FORBIDDEN_FIELD/'+key)
    for key in ('consumed','audit_rows','model_measurements'):
        same(after[key][:len(before[key])],before[key],'CONSUMER_HISTORY_REWRITTEN/'+key)
    require(after['used']>=before['used'] and after['enqueued']>=before['enqueued'],'IDENTITY_HISTORY_REMOVED')
    require(set(before['states'])==set(after['states']),'TARGET_SET_CHANGED')
    for j,b in before['states'].items():
        a=after['states'][j];require(set(a)==set(b),'BELIEF_FIELD_SET_CHANGED')
        for k in b:
            if typed(b[k])!=typed(a[k]):require(k in BELIEF_FIELDS,'BELIEF_FIELD_FORBIDDEN/'+k)
        same(after['history'][j][:len(before['history'][j])],before['history'][j],'POSITION_HISTORY_REWRITTEN')
        accepted=[r for r in after['audit_rows'][len(before['audit_rows']):] if r['accepted'] and r['receipt']['target_id']==j]
        if not accepted:
            same(a,b,'UNACCEPTED_STATE_CHANGED')
            require(plain(after['history'][j])==plain(before['history'][j]),'UNACCEPTED_HISTORY_CHANGED')
            same(after['accepted_receipts'].get(j),before['accepted_receipts'].get(j),'UNACCEPTED_RECEIPT_CHANGED')
        else:
            last=accepted[-1];require(plain(a)==plain(last['after_state']),'BELIEF_UPDATE_PROVENANCE')
            require(plain(after['accepted_receipts'][j])==plain(last['receipt']),'RECEIPT_UPDATE_PROVENANCE')
    require(consumer.receipts is consumer.accepted_receipts,'RECEIPT_ALIAS_CHANGED')


def boundary_check(tick,view,physical,*,consumer=None,operation,feedback_operation=None):
    require(tick in (80,100),'BOUNDARY_TICK')
    require(callable(operation),'ACTUAL_BOUNDARY_OPERATION_REQUIRED')
    validate_state(physical,view['beliefs'])
    before=typed(dict(physical=physical,view=view,consumer=_consumer_state(consumer)))
    operation()
    require(typed(dict(physical=physical,view=view,consumer=_consumer_state(consumer)))==before,'BOUNDARY_STATE_CHANGED')
    physical_before=typed(physical);view_before=typed({k:v for k,v in view.items() if k!='beliefs'})
    beliefs_id=id(view['beliefs']);targets={j:id(b) for j,b in view['beliefs'].items()}
    if feedback_operation is not None:
        require(consumer is not None,'FEEDBACK_CONSUMER_REQUIRED')
        cbefore=_consumer_state(consumer);frozen=feedback_operation()
        _verify_consumer_mutations(cbefore,consumer)
        require(set(frozen)==set(view['beliefs']),'CONTROL_TARGET_SET_CHANGED')
        for j,new in frozen.items():
            old=view['beliefs'][j];require(set(new)==set(old),'CONTROL_BELIEF_FIELD_SET_CHANGED')
            for key,value in new.items():
                if typed(old[key])!=typed(value):
                    require(key in BELIEF_FIELDS,'CONTROL_BELIEF_FORBIDDEN/'+key)
                    old[key]=copy.deepcopy(value)
        require(view['beliefs'] is not frozen,'WHOLE_BELIEFS_REPLACED')
    require(id(view['beliefs'])==beliefs_id and all(id(view['beliefs'][j])==i for j,i in targets.items()),'WHOLE_BELIEFS_REPLACED')
    require(typed(physical)==physical_before and typed({k:v for k,v in view.items() if k!='beliefs'})==view_before,'FEEDBACK_PHYSICAL_STATE_CHANGED')
    validate_state(physical,view['beliefs'])
    return dict(tick=tick,actual_boundary_operation='VERIFIED',feedback='NOT_APPLICABLE' if feedback_operation is None else 'VERIFIED',consumer_and_control_checked_separately=True)




def build_kernel(source, package='research.non_oracle'):
    """Explicit AST edits, exact structural assertions; no string replacement."""
    tree=ast.parse(source);matches=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_proxy'];require(len(matches)==1,'RUN_PROXY_IDENTITY')
    fn=matches[0];require([a.arg for a in fn.args.args]==['view','actions','world'],'RUN_PROXY_SIGNATURE')
    fn.args.args += [ast.arg(arg=n) for n in ('_command','_boundary','_trace')]
    loops=[n for n in fn.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='k'];require(len(loops)==1,'PROXY_LOOP_IDENTITY')
    loop=loops[0]
    calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='command'];require(len(calls)==1,'COMMAND_SITE_IDENTITY');calls[0].func.id='_command'
    clocks=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='advance_clock'];require(len(clocks)==1,'CLOCK_SITE_IDENTITY');clocks[0].func.id='_clock_logged'
    helpers=ast.parse('_reset_events=[]\ndef _clock_logged(*args):\n    result=advance_clock(*args)\n    _reset_events.extend(result[2])\n    return result').body
    fn.body[1:1]=helpers
    member_loops=[n for n in ast.walk(loop) if isinstance(n,ast.For) and any(isinstance(s,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='u' for t in s.targets) for s in n.body)]
    require(len(member_loops)==1,'CONTROL_ASSIGNMENT_SITE')
    member_loop=member_loops[0];u_index=next(i for i,s in enumerate(member_loop.body) if isinstance(s,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='u' for t in s.targets))
    member_loop.body.insert(u_index+1,ast.parse('_controls[i]=u.copy()').body[0])
    loop.body.insert(0,ast.parse('_controls=np.zeros_like(positions)').body[0])
    loop.body.insert(0,ast.Pass())
    # Explicit expressions avoid comprehension-scope access to function locals.
    loop.body[0]=ast.parse("if k-1 in (80,100):\n    _boundary(k-1, view, dict(positions=positions,states=states,lefts=lefts,geometry_before=geometry_before,statuses=statuses,tasks=tasks,effort=effort))").body[0]
    loop.body.append(ast.parse("_trace(dict(tick=k,positions=positions,states=states,lefts=lefts,geometry_before=geometry_before,statuses=statuses,tasks=tasks,effort=effort,controls=_controls,resets=_reset_events))").body[0])
    ast.fix_missing_locations(tree)
    ns={'__package__':package};exec(compile(tree,'historical_proxy_diagnostic_ast','exec'),ns)
    return ns['run_proxy'],ns


def prediction(belief,tick,no_cap=False):
    age=(tick-belief['estimate_tick'])*.05;require(age>=0,'PREDICT_BEFORE_ESTIMATE')
    prior=belief['last_observation_tick'] is None
    span=age if prior or no_cap else min(age,1.)
    return ([p+v*span for p,v in zip(belief['position_estimate'],belief['velocity_estimate'])],list(belief['velocity_estimate']) if prior or no_cap or age<=1. else [0.,0.])


def controller(namespace,no_cap,log,*,actions=None,lineage=None):
    np=namespace['np'];offset=namespace['offset'];lineage=lineage or {}
    role_ids={} if actions is None else {(a['target'],a['role']):i for i,a in enumerate(actions) if a['target'] is not None}
    def command(b,t,positions,roles,cfg):
        p,v=prediction(b,t,no_cap);cap=prediction(b,t,False);pos=np.asarray(positions,dtype=float)
        force=np.asarray(v)+cfg.travel_gain*(np.asarray(p)+np.array([offset(r,cfg) for r in roles])-pos)
        speed=np.linalg.norm(force,axis=1);u=force*np.minimum(1.,cfg.max_speed/np.maximum(speed,1e-15))[:,None]
        origin=lineage.get((b['target_id'],b['estimate_tick']))
        log.append(dict(tick=t,target=b['target_id'],roles=list(roles),robot_ids=[role_ids.get((b['target_id'],r),'NOT_IDENTIFIABLE') for r in roles],positions=pos.tolist(),position_prediction=p,velocity_prediction=v,estimate_position=list(b['position_estimate']),estimate_velocity=list(b['velocity_estimate']),control=u.tolist(),propagation_age=(t-b['estimate_tick'])*.05,observation_age=None if b['last_observation_tick'] is None else (t-b['last_observation_tick'])*.05,cap_applicable=b['last_observation_tick'] is not None and t-b['estimate_tick']>20,prediction_changed=typed((p,v))!=typed(cap),source=b['source'],velocity_source=b['velocity_source'],estimate_tick=b['estimate_tick'],available_tick=b['available_tick'],last_observation_tick=b['last_observation_tick'],belief_status=b['status'],origin=copy.deepcopy(origin) if origin is not None else dict(status='NOT_VERIFIED',note='internal ACTUAL_WLS alone does not identify observation origin')))
        return u
    return command




def trajectory_metrics(trace,control_log,truth,baseline_controls,*,comparison_pair,control_atol=0.):
    require(comparison_pair in ('P2/P1','P3/P1','P4/P3','P4/P2'),'CONTROL_COMPARISON_PAIR')
    errors=[]
    for row in control_log:
        future=truth(row['target'],row['tick']);estimate=truth(row['target'],row['estimate_tick'])
        errors.append(dict(tick=row['tick'],target=row['target'],estimate_tick=row['estimate_tick'],prediction_position_error=None if future is None else math.dist(row['position_prediction'],future[0]),prediction_velocity_error=None if future is None else math.dist(row['velocity_prediction'],future[1]),estimation_position_error=None if estimate is None else math.dist(row['estimate_position'],estimate[0]),estimation_velocity_error=None if estimate is None else math.dist(row['estimate_velocity'],estimate[1]),estimation_status='NOT_IDENTIFIABLE' if estimate is None else 'VERIFIED_REFERENCE_AVAILABLE'))
    def index(rows):
        d={}
        for r in rows:
            key=(r['tick'],r['target'],tuple(r['roles']));require(key not in d,'DUPLICATE_CONTROL_RECORD');d[key]=r
        return d
    current=index(control_log);baseline=index(baseline_controls);changed=[]
    for key in current.keys()|baseline.keys():
        if key not in current or key not in baseline:changed.append(key[0]);continue
        a=current[key]['control'];b=baseline[key]['control']
        if len(a)!=len(b) or any(len(x)!=len(y) for x,y in zip(a,b)) or any(abs(x-y)>control_atol for ar,br in zip(a,b) for x,y in zip(ar,br)):changed.append(key[0])
    final=trace[-1] if trace else None;outcomes={};served={r['target'] for r in control_log}
    if final:
        for j,t in final['tasks'].items():
            status=final['statuses'][j];completed=t['completion_tick'] is not None
            outcomes[j]=dict(completion=completed,completion_tick=t['completion_tick'],completion_time=None if not completed else t['completion_tick']*.05,terminal_status=status,Pmax=t['Pmax'],NG=t['NG'],stop_time=t['stop_time'],control_stop_time=t['stop_time'] if j in served else None,control_stop_status='RECORDED_PROXY_TERMINAL_OR_HORIZON' if j in served else 'NOT_APPLICABLE',assignment_release='NOT_APPLICABLE: no original proxy release transaction')
    return dict(state_errors=errors,first_control_divergence=min(changed,default=None),comparison_pair=comparison_pair,control_atol=control_atol,frames=plain(trace),control_sequence=plain(control_log),outcomes=plain(outcomes),service_resets=plain(final['resets']) if final else [],Q_semantics='OPTIMISTIC_UNKNOWN_Q_PROXY_NOT_OBSERVED_PASS')


def feedback_chain(accepted,belief_before,belief_after,prediction_before=None,prediction_after=None,control_before=None,control_after=None,service_before=None,service_after=None):
    def change(a,b):return 'NOT_VERIFIED' if a is None or b is None else 'UNCHANGED' if typed(a)==typed(b) else 'CHANGED'
    require(accepted is None or type(accepted) is bool,'ACCEPTANCE_TYPE')
    return dict(feedback_accepted=accepted,feedback_status='NOT_VERIFIED' if accepted is None else 'CHANGED' if accepted else 'UNCHANGED',belief_changed=change(belief_before,belief_after),prediction_changed=change(prediction_before,prediction_after),control_changed=change(control_before,control_after),service_outcome_changed=change(service_before,service_after),interpretation='descriptive fixed historical information intervention; no strict causal or online capability claim')


def economic_reconciliation(proxy_columns,proxy_value,hf_raw):
    ledger_check(proxy_columns,proxy_value)
    components=hf_raw['components'];order=('completion','flow','late','effort','terminal')
    require(all(math.isfinite(components[k]) for k in order),'HF_COMPONENT_FINITE')
    reconstructed=sum(components[k] for k in order)-hf_raw['change_cost']
    require(reconstructed==hf_raw['net'],'HF_LEDGER_RECONSTRUCTION')
    normalized=dict(completion=components['completion'],flow=-components['flow'],late=-components['late'],effort=-components['effort'],terminal=-components['terminal'],change=hf_raw['change_cost'])
    return dict(proxy=proxy_columns,hf_positive_cost_columns=normalized,hf_reconstructed_value=reconstructed,difference={k:proxy_columns[k]-normalized[k] for k in normalized},scope='same frozen economic definitions; trajectory-dependent components need not be equal')




class TraceRecorder:
    def __init__(self):self.rows=[]
    def __call__(self,state):self.rows.append(copy.deepcopy(state))


def value_metrics(cells):
    require(len(cells)==24,'INCOMPLETE_DIAGNOSTIC_MATRIX')
    indexed={(x['version'],x['world'],x['action']):x for x in cells};require(len(indexed)==24,'DUPLICATE_CELL')
    actions=('KEEP','SWITCH','MEMBER_CHANGE');worlds=('H2','H3');versions=('P1','P2','P3','P4')
    rows=[];effects=[];rankings=[]
    for world in worlds:
        for action in actions:
            group=[indexed[v,world,action] for v in versions];require(len({x['hf'] for x in group})==1,'HF_LABEL_CHANGED_BETWEEN_VERSIONS');a,b,c,d=[x['value'] for x in group]
            for x in group:
                require(math.isfinite(x['value']) and math.isfinite(x['hf']),'NONFINITE_VALUE')
                err=x['value']-x['hf'];rows.append(dict(x,signed_error=err,AE=abs(err),Delta_AE=abs(err)-abs(a-group[0]['hf'])))
            effects.append(dict(world=world,action=action,NoCap_F0=b-a,NoCap_F1=d-c,Feedback_Cap=c-a,Feedback_NoCap=d-b,Interaction=d-c-b+a,ME_NoCap=((b-a)+(d-c))/2,ME_Feedback=((c-a)+(d-b))/2))
        for version in versions:
            group=[indexed[version,world,a] for a in actions];best=max(x['value'] for x in group);truth=max(x['hf'] for x in group)
            rankings.append(dict(world=world,version=version,strict_order=sorted(actions,key=lambda a:-indexed[version,world,a]['value']),exact_best=[x['action'] for x in group if x['value']==best],epsilon_best=[x['action'] for x in group if best-x['value']<=1e-8],regret_by_best={x['action']:truth-x['hf'] for x in group if best-x['value']<=1e-8},keep_minus_switch=indexed[version,world,'KEEP']['value']-indexed[version,world,'SWITCH']['value']))
    return dict(cells=rows,effects=effects,rankings=rankings,MAE={v:sum(x['AE'] for x in rows if x['version']==v)/6 for v in versions},signed_bias={v:{a:sum(x['signed_error'] for x in rows if x['version']==v and x['action']==a)/2 for a in actions} for v in versions})


def ledger_check(columns,value):
    require(set(columns)=={'completion','flow','late','effort','terminal','change'},'LEDGER_FIELDS')
    expected=columns['completion']-sum(columns[k] for k in ('flow','late','effort','terminal','change'))
    require(expected==value,'LEDGER_RECONSTRUCTION');return expected


P1_FIELDS=('assignment_key','certificates','effort_integral','ledger','left_endpoints','positions','proxy_role','tasks','value','world_digest')


def compare_p1(actual,archived):
    def equal(a,b):
        a=plain(a);b=plain(b)
        if type(a) is not type(b):return False
        if isinstance(a,dict):return set(a)==set(b) and all(equal(a[k],b[k]) for k in a)
        if isinstance(a,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
        if type(a) is float:return math.isfinite(a) and math.isfinite(b) and a==b
        return a==b
    require(all(k in actual and k in archived for k in P1_FIELDS),'P1_CORE_FIELD_MISSING')
    results={k:equal(actual[k],archived[k]) for k in P1_FIELDS}
    return dict(status='VERIFIED' if all(results.values()) else 'FAILED',fields=results,precision='archive numeric equality; no rounding; only ten core fields')


REQUIRED_GATES=('historical_identity','import_closure','p1_reproduction','boundary_continuity','feedback_integrity','treatment_definition','metrics_complete','history_protected','resource_accounting','evidence_sealed')

def final_status(records,evidence_root,expected_code_sha,*,feedback_identifiable=True):
    require(isinstance(records,dict) and all(isinstance(v,dict) for v in records.values()),'EVIDENCE_RECORDS_REQUIRED')
    root=Path(evidence_root).resolve();results={}
    for gate in REQUIRED_GATES:
        r=records.get(gate)
        if r is None:results[gate]='NOT_VERIFIED';continue
        p=(root/r['path']).resolve();require(p.is_relative_to(root),'EVIDENCE_SCOPE')
        raw=p.read_bytes();require(hashlib.sha256(raw).hexdigest()==r['sha256'],'EVIDENCE_HASH')
        doc=json.loads(raw);require(doc.get('code_sha256')==expected_code_sha,'EVIDENCE_CODE_VERSION')
        verification=doc['checks'].get(gate,{})
        require(verification.get('check_id') and verification.get('input_sha256'),'EVIDENCE_VERIFICATION_PROVENANCE')
        results[gate]=verification.get('status','NOT_VERIFIED')
    if any(results[k]!='VERIFIED' for k in REQUIRED_GATES if k!='feedback_integrity'):status='L3_B_BLOCKED'
    elif not feedback_identifiable:status='L3_B_NOT_IDENTIFIABLE'
    else:status='L3_B_DIAGNOSTIC_PASS_CANDIDATE' if results['feedback_integrity']=='VERIFIED' else 'L3_B_BLOCKED'
    return dict(status=status,gates=results,independent_review='PENDING',authorization='NOT_ESTABLISHED_BY_THIS_FUNCTION')
