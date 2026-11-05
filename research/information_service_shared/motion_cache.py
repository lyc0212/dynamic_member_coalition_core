"""Batch-local append-only single-robot motion prefixes; no coalition state."""
from copy import deepcopy
import math
import sys

import numpy as np

from pursuit_v2.config import Config
from pursuit_v2 import observation_geometry as geometry
from .common import STAGE_CONTRACT, ContractError, typed_digest
from . import contracts

DT = .05
_COUNT_NAMES = ('accepted_interval_requests', 'new_computed_intervals', 'cache_hit_requests',
                'rejected_requests', 'initial_position_reads')


def _component(target_id, robot_id, role):
    return {'target_id':target_id, 'robot_id':robot_id, 'role':role}


class MotionComponentCache:
    def __init__(self, scope, request, *, history_authority=None, unit_fixture=None, on_trace=None):
        clean, flat, manifest = contracts.admit_scope(scope, request,
            history_authority=history_authority, unit_fixture=unit_fixture)
        self._scope = clean
        self._request_fingerprint = typed_digest(request)
        self._unit_fixture_id = None if unit_fixture is None else unit_fixture.fixture_id
        self._cfg = Config(**flat['config'])
        self._initial_positions = np.array(flat['positions'], dtype=float, copy=True)
        self._targets = {}
        t0 = flat['start_tick']*DT
        for target in flat['targets']:
            p0 = np.array(target['position_now'], dtype=float)
            velocity = np.array(target['velocity_now'], dtype=float)
            x = target['position_now'][0];vx = target['velocity_now'][0]
            escape = t0 if x >= self._cfg.side else t0+(self._cfg.side-x)/vx if vx > 0 else math.inf
            self._targets[target['id']] = {'p0':p0, 'velocity':velocity, 'escape':escape,
                'roles':geometry.required_roles(target['required_robots'], self._cfg)}
        self._components = {}
        self._counts = {name:0 for name in _COUNT_NAMES}
        self._constructed = [];self._accepted = [];self._trace = []
        self._status = 'OPEN';self._on_trace = on_trace
        self._kernel_entries = 0;self._kernel_returns = 0;self._vector_calls = 0
        self._peak_cache_bytes = 0
        self._record('CREATED', None, 'ABSENT', dict(self._counts), None)

    @property
    def scope(self): return deepcopy(self._scope)

    @property
    def full_scope_id(self): return self._scope['full_scope_id']

    def assert_request(self, request, *, unit_fixture=None):
        if self._status != 'OPEN': raise ContractError('Cannot evaluate with a closed cache')
        if typed_digest(request) != self._request_fingerprint: raise ContractError('Cache request differs')
        if self._unit_fixture_id is None:
            if unit_fixture is not None: raise ContractError('Unit capability cannot enter main cache')
        elif type(unit_fixture) is not contracts.UnitFixtureCapability or unit_fixture.fixture_id != self._unit_fixture_id:
            raise ContractError('Explicit matching unit capability required')

    def _ordered_keys(self):
        return sorted(self._components, key=lambda key:(key[0],key[1],contracts.ROLES.index(key[2])))

    def _prefix_digest(self, key):
        return typed_digest({'full_scope_id':self.full_scope_id,
            'component':_component(*key), 'intervals':self._components[key]['intervals']})

    def _prefixes_digest(self):
        return typed_digest([{'component':_component(*key), 'prefix_digest':self._components[key]['prefix_digest']}
                             for key in self._ordered_keys()])

    def _prefix_state(self, key):
        if key not in self._components: return None
        part = self._components[key]
        return {'component':_component(*key), 'frontier_next':self._scope['start_tick']+len(part['intervals']),
                'constructed_intervals':len(part['intervals']), 'prefix_digest':part['prefix_digest']}

    @staticmethod
    def _evidence(interval):
        return {'interval':deepcopy(interval), 'binary64':{
            'x_start':[contracts.f64hex(v) for v in interval['x_start']],
            'u':[contracts.f64hex(v) for v in interval['u']],
            'elapsed':contracts.f64hex(interval['elapsed']),
            'x_end':[contracts.f64hex(v) for v in interval['x_end']]},
            'interval_digest':typed_digest(interval)}

    def _record(self, event, request, status_before, counts_before, prefixes_before,
                *, prefix_before=None, prefix_after=None, interval=None, initial=None, rejection=None):
        row = {'message_kind':'motion_cache_trace_record','contract_id':STAGE_CONTRACT,
            'full_scope_id':self.full_scope_id,'event_index':len(self._trace),
            'previous_event_digest':self._trace[-1]['event_digest'] if self._trace else None,
            'event':event,'request':deepcopy(request),'cache_status_before':status_before,
            'cache_status_after':self._status,'counters_before':deepcopy(counts_before),
            'counters_after':dict(self._counts),'prefixes_digest_before':prefixes_before,
            'prefixes_digest_after':self._prefixes_digest(),
            'component_prefix_before':deepcopy(prefix_before),'component_prefix_after':deepcopy(prefix_after),
            'interval_evidence':None if interval is None else self._evidence(interval),
            'returned_initial_position':deepcopy(initial),
            'returned_initial_position_binary64':None if initial is None else [contracts.f64hex(v) for v in initial],
            'rejection':deepcopy(rejection)}
        row['event_digest'] = typed_digest(row)
        self._trace.append(row)
        if self._on_trace is not None: self._on_trace(deepcopy(row))
        self._peak_cache_bytes = max(self._peak_cache_bytes, self._allocated_bytes())

    def _allocated_bytes(self):
        # Count owned Python motion/trace containers and ndarray payloads once.
        seen = set()
        def visit(value):
            if id(value) in seen: return 0
            seen.add(id(value));size = sys.getsizeof(value)
            if type(value) is dict: return size+sum(visit(k)+visit(v) for k,v in value.items())
            if type(value) in (list,tuple): return size+sum(visit(v) for v in value)
            return size
        return visit(self._components)+visit(self._trace)+visit(self._initial_positions)+visit(self._targets)

    def _trace_request(self, method, arguments):
        name = 'GetIntervalRequest' if method == 'get_interval' else 'GetInitialPositionRequest'
        try:
            contracts.validate_definition(arguments, name)
            return {'method':method, 'arguments':deepcopy(arguments)}
        except ContractError:
            fields = {'target_id':'Count','robot_id':'Count','role':'Role',
                      'interval_start_tick':'Tick','expected_scope_id':'Sha256'}
            bad = next((k for k,v in arguments.items() if k in fields and not self._valid(v, fields[k])), 'call_signature')
            value = arguments.get(bad, arguments)
            kinds = {type(None):'null',bool:'bool',int:'int',float:'float',str:'string',list:'array',dict:'object'}
            return {'method':'invalid_request','arguments':{'method':method,'parameter':bad,
                'observed':{'type':kinds.get(type(value),'unsupported'),'value_json_or_repr':repr(value),
                            'binary64_be_hex':contracts.f64hex(value) if type(value) is float and math.isfinite(value) else None,
                            'raw_lexeme':None}}}

    @staticmethod
    def _valid(value, name):
        try: contracts.validate_definition(value, name);return True
        except ContractError: return False

    def _reject(self, code, method, arguments, parameter=None, frontier=None):
        before = dict(self._counts);prefixes = self._prefixes_digest();status = self._status
        self._counts['rejected_requests'] += 1
        tick = arguments.get('interval_start_tick')
        rejection = {'code':code,'exception_type':'ContractError','parameter':parameter,
            'requested_interval_start_tick':tick if type(tick) is int else None,
            'frontier_next':frontier,'message':code+': rejected without changing motion prefix'}
        self._record('REQUEST_REJECTED', self._trace_request(method,arguments), status, before, prefixes,
                     rejection=rejection)
        raise ContractError(rejection['message'])

    def _validate_get(self, method, arguments):
        if self._status != 'OPEN': self._reject('CLOSED_CACHE',method,arguments)
        if arguments['expected_scope_id'] != self.full_scope_id:
            self._reject('WRONG_SCOPE',method,arguments,'expected_scope_id')
        for name in ('target_id','robot_id'):
            if type(arguments[name]) is not int:
                self._reject('INVALID_ARGUMENT',method,arguments,name)
        j,i,role = arguments['target_id'],arguments['robot_id'],arguments['role']
        if j not in self._targets: self._reject('UNKNOWN_TARGET',method,arguments,'target_id')
        if not 0 <= i < self._cfg.robots: self._reject('INVALID_ROBOT',method,arguments,'robot_id')
        if type(role) is not str or role not in self._targets[j]['roles']:
            self._reject('INVALID_ROLE',method,arguments,'role')
        return j,i,role

    def get_initial_position(self, target_id, robot_id, role, expected_scope_id):
        args = dict(target_id=target_id,robot_id=robot_id,role=role,expected_scope_id=expected_scope_id)
        key = self._validate_get('get_initial_position',args)
        before = dict(self._counts);prefixes = self._prefixes_digest();prefix = self._prefix_state(key)
        result = self._initial_positions[robot_id].copy().tolist()
        self._counts['initial_position_reads'] += 1
        self._record('INITIAL_POSITION_READ',{'method':'get_initial_position','arguments':args},
                     'OPEN',before,prefixes,prefix_before=prefix,prefix_after=prefix,initial=result)
        return deepcopy(result)

    def _compute_interval(self, key, tick):
        """One actual numerical kernel entry; never loops across missing ticks."""
        self._kernel_entries += 1
        j,i,role = key;target = self._targets[j]
        old = self._components.get(key)
        previous = self._initial_positions[i] if old is None else old['intervals'][-1]['x_end']
        pos = np.array([previous],dtype=float,copy=True)
        offsets = np.array([geometry.offset(role,self._cfg)])
        p0=target['p0'];velocity=target['velocity'];t0=self._scope['start_tick']*DT
        n=tick+1;lo=(n-1)*DT;hi=n*DT
        stop=max(lo,min(hi,target['escape']));elapsed=max(0.,stop-lo)
        def target_at(t): return p0+velocity*(t*DT-t0)
        force=velocity+self._cfg.travel_gain*(target_at(n-1)+offsets-pos)
        self._vector_calls += 1
        speeds=np.linalg.norm(force,axis=1)
        force*=np.minimum(1.,self._cfg.max_speed/np.maximum(speeds,1e-15))[:,None]
        end=pos+force*elapsed
        if not all(np.isfinite(a).all() for a in (pos,force,end)) or not math.isfinite(elapsed):
            raise ContractError('Nonfinite component motion; abort without acceptance')
        result = {'full_scope_id':self.full_scope_id,'component':_component(*key),
            'interval_start_tick':tick,'interval_end_tick':n,'x_start':pos[0].tolist(),
            'u':force[0].tolist(),'elapsed':float(elapsed),'x_end':end[0].tolist()}
        self._kernel_returns += 1
        return result

    def get_interval(self, target_id, robot_id, role, interval_start_tick, expected_scope_id):
        args = dict(target_id=target_id,robot_id=robot_id,role=role,
                    interval_start_tick=interval_start_tick,expected_scope_id=expected_scope_id)
        key = self._validate_get('get_interval',args);tick = interval_start_tick
        if type(tick) is not int: self._reject('INVALID_ARGUMENT','get_interval',args,'interval_start_tick')
        if tick < self._scope['start_tick']: self._reject('BEFORE_START','get_interval',args,'interval_start_tick')
        part = self._components.get(key)
        frontier = self._scope['start_tick']+(0 if part is None else len(part['intervals']))
        # The frozen C10 vector deliberately asks k=end while frontier<end.
        # A skipped prefix is diagnosed as GAP first, with no allocation/build;
        # frontier==end then diagnoses the ordinary horizon refusal.
        if tick > frontier: self._reject('GAP_REQUEST','get_interval',args,'interval_start_tick',frontier)
        if tick >= self._scope['prediction_end_tick']: self._reject('AT_OR_AFTER_HORIZON','get_interval',args,'interval_start_tick')
        before = dict(self._counts);prefixes = self._prefixes_digest();prefix = self._prefix_state(key)
        identity = {'full_scope_id':self.full_scope_id,'component':_component(*key),'interval_start_tick':tick}
        if tick == frontier:
            result = self._compute_interval(key,tick)
            if part is None:
                part = {'initial_position':self._initial_positions[robot_id].copy().tolist(),'intervals':[]}
                self._components[key] = part
            part['intervals'].append(deepcopy(result));part['prefix_digest']=self._prefix_digest(key)
            self._constructed.append(deepcopy(identity));self._counts['new_computed_intervals']+=1
            event='INTERVAL_BUILT'
        else:
            result=deepcopy(part['intervals'][tick-self._scope['start_tick']])
            self._counts['cache_hit_requests']+=1;event='INTERVAL_HIT'
        self._accepted.append(deepcopy(identity));self._counts['accepted_interval_requests']+=1
        self._record(event,{'method':'get_interval','arguments':args},'OPEN',before,prefixes,
                     prefix_before=prefix,prefix_after=self._prefix_state(key),interval=result)
        return deepcopy(result)

    def snapshot_diagnostics(self):
        c=self._counts
        if c['accepted_interval_requests'] != c['new_computed_intervals']+c['cache_hit_requests']:
            raise ContractError('Cache accounting invariant failed')
        built=[typed_digest(i) for i in self._constructed];accepted={typed_digest(i) for i in self._accepted}
        if len(built)!=len(set(built)) or set(built)!=accepted or len(built)!=c['new_computed_intervals']:
            raise ContractError('Cache build/request set invariant failed')
        components=[]
        for key in self._ordered_keys():
            part=self._components[key]
            if [r['interval_start_tick'] for r in part['intervals']] != list(range(self._scope['start_tick'],self._scope['start_tick']+len(part['intervals']))):
                raise ContractError('Cache prefix is not contiguous')
            if part['prefix_digest']!=self._prefix_digest(key): raise ContractError('Stored prefix mutated')
            components.append({'component':_component(*key),'initial_position':deepcopy(part['initial_position']),
                'initial_position_binary64':[contracts.f64hex(v) for v in part['initial_position']],
                'frontier_next':self._scope['start_tick']+len(part['intervals']),
                'intervals':[self._evidence(r) for r in part['intervals']], 'prefix_digest':part['prefix_digest']})
        result={'message_kind':'motion_cache_diagnostics','contract_id':STAGE_CONTRACT,'scope':self.scope,
            'cache_status':self._status,'counters':dict(c),'component_instances':len(components),'components':components,
            'trace_record_count':len(self._trace),'trace_head_digest':self._trace[-1]['event_digest'],
            'constructed_interval_identities':deepcopy(self._constructed),
            'accepted_interval_request_identities':deepcopy(self._accepted)}
        result['diagnostics_digest']=typed_digest(result)
        return contracts.validate_definition(result,'CacheDiagnostics')

    def trace_records(self): return deepcopy(self._trace)

    def instrumentation(self):
        return {'compute_entries':self._kernel_entries,'compute_returns':self._kernel_returns,
                'numpy_vector_update_calls':self._vector_calls,'peak_cache_bytes':self._peak_cache_bytes}

    def unit_storage_references(self, capability):
        """Explicit unit-only alias probe; returns actual storage, not invented copies."""
        if self._unit_fixture_id is None or type(capability) is not contracts.UnitFixtureCapability or capability.fixture_id!=self._unit_fixture_id:
            raise ContractError('Storage probe requires this explicit unit fixture')
        return {'initial_positions':self._initial_positions,'components':self._components}

    def close(self):
        if self._status=='CLOSED': return
        before=dict(self._counts);prefixes=self._prefixes_digest();self._status='CLOSED'
        self._record('CLOSED',{'method':'close','arguments':{}},'OPEN',before,prefixes)
