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
    return value


def same(a, b, code='STATE_CONTINUITY'):
    require(typed(a) == typed(b), code)


class Writer:
    """Cumulative logical writes, including overwritten/deleted outputs."""
    def __init__(self, root, limit=67108864):
        self.root = Path(root).resolve()
        self.limit = limit
        self.written = 0
        self.complete = True
        self.operations = []

    def write(self, relative, payload, *, replace=False):
        p = (self.root / relative).resolve()
        require(p.is_relative_to(self.root), 'OUTPUT_OUTSIDE_ROOT')
        data = payload if isinstance(payload, bytes) else payload.encode('utf-8')
        require(self.written + len(data) <= self.limit, 'CUMULATIVE_WRITE_LIMIT')
        p.parent.mkdir(parents=True, exist_ok=True)
        before = self.written
        try:
            with p.open('wb' if replace else 'xb', buffering=0) as stream:
                offset = 0
                while offset < len(data):
                    n = stream.write(data[offset:])
                    require(type(n) is int and 0 < n <= len(data)-offset, 'SHORT_WRITE')
                    offset += n
                    self.written += n
        except BaseException:
            self.complete = False
            raise
        self.operations.append(dict(path=relative,bytes=self.written-before,mode='replace' if replace else 'new'))

    def json(self, relative, value):
        self.write(relative, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))


class Clock:
    def __init__(self, wall_start, *, cpu_limit=120, wall_limit=300):
        self.wall_start = wall_start
        self.cpu_start = time.process_time()
        self.cpu_limit = cpu_limit
        self.wall_limit = wall_limit

    def check(self):
        require(time.monotonic()-self.wall_start < self.wall_limit, 'WALL_LIMIT')
        require(time.process_time()-self.cpu_start < self.cpu_limit, 'CPU_LIMIT')


class HistoricalImports(importlib.abc.MetaPathFinder):
    """Only project imports are restricted; not a general security framework."""
    def __init__(self, historical_root, pins):
        self.root = Path(historical_root).resolve()
        self.pins = pins
        self.modules = {}

    def validate(self, name, spec):
        if spec.origin and spec.origin not in ('built-in', 'frozen'):
            p = Path(spec.origin).resolve()
            require(p.is_relative_to(self.root), 'CURRENT_PROJECT_IMPORT/' + name)
            rel = p.relative_to(self.root).as_posix()
            require(rel in self.pins, 'UNREGISTERED_PROJECT_DEPENDENCY/' + rel)
            require(hashlib.sha256(p.read_bytes()).hexdigest() == self.pins[rel]['sha256'], 'IMPORT_HASH/' + rel)
            self.modules[name] = dict(path=str(p), **self.pins[rel])
        for location in spec.submodule_search_locations or ():
            require(Path(location).resolve().is_relative_to(self.root), 'NAMESPACE_FALLBACK/' + name)

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
    """Data-only conditional MODEL replay; no enqueue into ACTUAL consumers."""
    def __init__(self, seed, announcements):
        self.states = {int(k):copy.deepcopy(v) for k,v in seed['internal_states_at_D60'].items()}
        self.history = {int(k):copy.deepcopy(v) for k,v in seed['accepted_position_history'].items()}
        self.receipts = {int(k):copy.deepcopy(v) for k,v in seed['accepted_receipts'].items()}
        self.pending = copy.deepcopy(seed['pending_observations'])
        self.consumed = copy.deepcopy(seed['consumed_records'])
        self.announcements = copy.deepcopy(announcements)
        self.used = set()
        self.enqueued = set()
        self.audit_rows = []

    def enqueue(self, event):
        require(event['observation_origin']=='MODEL' and event['provenance']=='SIMULATED', 'MODEL_SOURCE')
        require(event['available_tick']>=event['measurement_tick'], 'NEGATIVE_LATENCY')
        identity=event['identity'];require(identity not in self.enqueued, 'DUPLICATE_ENQUEUE')
        self.enqueued.add(identity);self.pending.append(copy.deepcopy(event))

    def freeze(self, tick):
        remaining=[]
        for ordinal,row in enumerate(self.pending):
            if row['available_tick']>tick:
                remaining.append(row);continue
            identity=row['identity'];require(identity not in self.used,'DUPLICATE_CONSUMPTION');self.used.add(identity)
            j=int(row['target_id']);e=row['estimate'];b=self.states[j];hist=self.history[j]
            receipt=dict(target_id=j,measurement_tick=row['measurement_tick'],available_tick=row['available_tick'],consumed_tick=tick)
            self.consumed.append(receipt)
            reason=[]
            if e is None:reason=['ESTIMATE_MISSING']
            else:
                if not e.get('has_accepted_estimate'):reason.append('NO_ACCEPTED_ESTIMATE')
                if not e.get('optimizer_converged'):reason.append('OPTIMIZER_NOT_CONVERGED')
                reason += [k.upper() for k in ('numerical_ill_conditioned','ambiguity_detected','boundary_active','numeric_contract_violation') if e.get(k,True)]
            if e is not None and not reason:
                p=e['estimate'];t=row['measurement_tick']
                if len(p)!=2:reason=['INVALID_ESTIMATE_DIMENSION']
                elif not all(math.isfinite(x) for x in p):reason=['NONFINITE_ESTIMATE']
                elif hist and t<=hist[-1][0]:reason=['NONINCREASING_MEASUREMENT_TICK']
            before=copy.deepcopy(hist)
            if not reason:
                p=e['estimate'];t=row['measurement_tick'];previous=next(((s,q) for s,q in reversed(hist) if t-s>=5),None)
                velocity=list(b['velocity_estimate'])
                if previous:
                    s,q=previous;velocity=[(x-y)/((t-s)*.05) for x,y in zip(p,q)]
                    limit=next(a['speed_limit'] for a in self.announcements if a['id']==j);speed=math.hypot(*velocity)
                    if speed>limit:velocity=[v*limit/speed for v in velocity]
                hist.append((t,list(p)));self.receipts[j]=receipt.copy()
                b.update(estimate_tick=t,available_tick=row['available_tick'],position_estimate=list(p),velocity_estimate=velocity,velocity_source='ACTUAL_POSITION_DIFFERENCE' if previous else b['velocity_source'],last_observation_tick=t,source='ACTUAL_WLS',status='OBSERVED',diagnostics=copy.deepcopy(e))
            else:same(hist,before,'REJECTED_HISTORY_CHANGED')
            self.audit_rows.append(dict(identity=identity,freeze_tick=tick,freeze_ordinal=ordinal,consumption_ordinal=len(self.audit_rows),accepted=not reason,reasons=reason,receipt=receipt))
        self.pending=remaining
        result=copy.deepcopy(self.states)
        for b in result.values():
            if b['last_observation_tick'] is not None and tick-b['last_observation_tick']>20:b['status']='DEGRADED'
        return result


def event_catalog(raw, transactions, snapshots, committed_connections):
    """Build/verify a catalog only when explicitly called by later authorization."""
    require(raw['provenance']=='SIMULATED' and raw['observation_origin']=='MODEL','RAW_SOURCE')
    require(raw['endpoint_fusions']==len(raw['feedback']),'FUSION_DIRECTORY_COUNT')
    require({c['feedback_event_ordinal'] for c in committed_connections}==set(range(len(raw['feedback']))),'COMMITTED_DIRECTORY_COMPLETENESS')
    events=[];identities=set()
    for i,f in enumerate(raw['feedback']):
        fr=f['frame'];ep=f['endpoint'];identity=fr['frame_id']
        require(identity not in identities,'DUPLICATE_FRAME');identities.add(identity)
        require(ep['target_id']==fr['target_id'] and ep['tick']==fr['tick'],'FRAME_ENDPOINT_BINDING')
        require(ep['provenance']=='SIMULATED' and ep['observation_origin']=='MODEL','ENDPOINT_SOURCE')
        links=[c for c in committed_connections if c['feedback_event_ordinal']==i]
        require(links,'MISSING_GENERATION_CONNECTION')
        for c in links:
            require(c['feedback_digest']==digest(f) and c['frame_id']==identity,'CONNECTION_BINDING')
        unique={(c['transaction_identity'],c['endpoint_side']) for c in links};require(len(unique)==1,'GENERATION_PHASE_AMBIGUOUS')
        phase=links[0]['endpoint_side']
        events.append(dict(identity=identity,generation_ordinal=i,enqueue_ordinal=i,phase=phase,frame_tick=fr['tick'],target_id=fr['target_id'],measurement_tick=fr['tick'],available_tick=fr['tick'],observation_origin='MODEL',provenance='SIMULATED',estimate=copy.deepcopy(f['result']['estimate_result']),feedback_digest=digest(f)))
    previous=[]
    for tick,snapshot in sorted(snapshots.items()):
        eligible=[e for e in events if e['frame_tick']<tick or (e['frame_tick']==tick and e['phase']=='MODEL_INTERVAL_RIGHT')]
        queue=[e for e in eligible if e['identity'] not in previous]
        archived=[e for e in snapshot['events'] if e.get('consumed_tick')==tick]
        require([e['identity'] for e in queue if e['available_tick']<=tick]==[e['feedback_identity'] for e in archived],'QUEUE_DIRECTORY_COMPLETENESS')
        for e,a in zip(queue,archived):
            require(e['feedback_digest']==a['feedback_digest'] and e['target_id']==a['target_id'] and e['measurement_tick']==a['measurement_tick'],'EVENT_BINDING')
            require(a['queue_ordinal']==queue.index(e),'FREEZE_ORDINAL')
        previous += [e['feedback_identity'] for e in archived]
    return events


PHYSICAL=('positions','states','lefts','geometry_before','statuses','tasks','effort')


def boundary_check(tick, view, physical, updates=None):
    before=typed(physical);require(set(PHYSICAL)<=set(physical),'SNAPSHOT_FIELD_MISSING')
    # Pause/resume is an in-place no-op: never reconstruct a simulator.
    require(typed(physical)==before,'BOUNDARY_STATE_CHANGED')
    old=typed({k:v for k,v in view.items() if k!='beliefs'})
    if updates is not None:view['beliefs']=copy.deepcopy(updates)
    require(typed(physical)==before and typed({k:v for k,v in view.items() if k!='beliefs'})==old,'FEEDBACK_PHYSICAL_STATE_CHANGED')


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
    loop.body.insert(0,ast.Pass())
    # Explicit expressions avoid comprehension-scope access to function locals.
    loop.body[0]=ast.parse("_boundary(k-1, view, dict(positions=positions,states=states,lefts=lefts,geometry_before=geometry_before,statuses=statuses,tasks=tasks,effort=effort))").body[0]
    loop.body.append(ast.parse("_trace(dict(tick=k,positions=positions,states=states,lefts=lefts,geometry_before=geometry_before,statuses=statuses,tasks=tasks,effort=effort,resets=_reset_events))").body[0])
    ast.fix_missing_locations(tree)
    ns={'__package__':package};exec(compile(tree,'historical_proxy_diagnostic_ast','exec'),ns)
    return ns['run_proxy'],ns


def prediction(belief,tick,no_cap=False):
    age=(tick-belief['estimate_tick'])*.05;require(age>=0,'PREDICT_BEFORE_ESTIMATE')
    prior=belief['last_observation_tick'] is None
    span=age if prior or no_cap else min(age,1.)
    return ([p+v*span for p,v in zip(belief['position_estimate'],belief['velocity_estimate'])],list(belief['velocity_estimate']) if prior or no_cap or age<=1. else [0.,0.])


def controller(namespace,no_cap,log):
    np=namespace['np'];offset=namespace['offset']
    def command(b,t,positions,roles,cfg):
        p,v=prediction(b,t,no_cap);cap=prediction(b,t,False);pos=np.asarray(positions,dtype=float)
        force=np.asarray(v)+cfg.travel_gain*(np.asarray(p)+np.array([offset(r,cfg) for r in roles])-pos)
        speed=np.linalg.norm(force,axis=1);u=force*np.minimum(1.,cfg.max_speed/np.maximum(speed,1e-15))[:,None]
        log.append(dict(tick=t,target=b['target_id'],roles=list(roles),position_prediction=p,velocity_prediction=v,control=u.tolist(),propagation_age=(t-b['estimate_tick'])*.05,observation_age=None if b['last_observation_tick'] is None else (t-b['last_observation_tick'])*.05,cap_applicable=b['last_observation_tick'] is not None and t-b['estimate_tick']>20,prediction_changed=typed((p,v))!=typed(cap),source=b['source'],estimate_tick=b['estimate_tick']))
        return u
    return command


def trajectory_metrics(trace,control_log,truth,baseline_controls):
    errors=[]
    for row in control_log:
        p,v=truth(row['target'],row['tick']);errors.append(dict(tick=row['tick'],target=row['target'],position_error=math.dist(row['position_prediction'],p),velocity_error=math.dist(row['velocity_prediction'],v)))
    def index(rows):return {(r['tick'],r['target'],tuple(r['roles'])):r for r in rows}
    current=index(control_log);baseline=index(baseline_controls)
    changed=[k[0] for k in current.keys()|baseline.keys() if k not in current or k not in baseline or typed(current[k]['control'])!=typed(baseline[k]['control'])]
    first=min(changed,default=None)
    # NG, Pmax, completion and stop_time are taken from recorded task states.
    return dict(state_errors=errors,first_control_divergence=first,frames=plain(trace),service_resets=plain(trace[-1]['resets']) if trace else [],resource_release_semantics='original proxy stops control after terminal status; no new Assignment')


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
            group=[indexed[v,world,action] for v in versions];a,b,c,d=[x['value'] for x in group]
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


REQUIRED_GATES=('historical_identity','import_closure','p1_reproduction','boundary_continuity','feedback_integrity','treatment_definition','metrics_complete','history_protected','resource_accounting','evidence_sealed')
def final_status(gates, *, feedback_identifiable=True):
    if any(gates.get(k) is not True for k in REQUIRED_GATES if k!='feedback_integrity'):
        return 'L3_B_BLOCKED'
    if not feedback_identifiable:return 'L3_B_NOT_IDENTIFIABLE'
    return 'L3_B_DIAGNOSTIC_PASS_CANDIDATE' if gates.get('feedback_integrity') is True else 'L3_B_BLOCKED'
