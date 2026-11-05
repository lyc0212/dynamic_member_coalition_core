"""Isolated OLD/NEW exact-type binding and symmetric post-peak sidecars.

The frozen scientific method bodies and old module dictionaries are unchanged.
Importing this module does not construct a cache, evaluate a candidate or scan a
measured graph. Only the supervised caller may perform those actions.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import types
import weakref

from .meter import FourRootMeter, MeterError, metadata_body_size
from research.information_service_shared.motion_cache import MotionComponentCache as FrozenCache
from research.information_service_shared import evaluator as frozen_evaluator


CONTRACT_ID = 'STAGE2A5B-GQ-MEMORY-ACCOUNTING-v0.1-DRAFT'
_ORIGINAL_INIT = FrozenCache.__init__
_ORIGINAL_RECORD = FrozenCache._record
_ORIGINAL_ALLOCATED = FrozenCache._allocated_bytes
_ORIGINAL_EVALUATE = frozen_evaluator.evaluate_candidate
_OBSERVERS = weakref.WeakKeyDictionary()


def process_identity():
    pid = os.getpid()
    if os.name == 'nt':
        import ctypes as C
        from ctypes import wintypes as W
        k=C.WinDLL('kernel32',use_last_error=True)
        k.GetCurrentProcess.restype=W.HANDLE
        k.GetProcessTimes.argtypes=[W.HANDLE]+[C.POINTER(W.FILETIME)]*4
        k.GetProcessTimes.restype=W.BOOL
        times=[W.FILETIME() for _ in range(4)]
        if not k.GetProcessTimes(k.GetCurrentProcess(),*[C.byref(t) for t in times]):
            raise C.WinError(C.get_last_error())
        creation=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime
        return {'platform':'windows','version':1,'pid':pid,'creation_filetime_100ns':creation}
    fields = Path('/proc/self/stat').read_text(encoding='utf-8').rsplit(')', 1)[1].split()
    return {'pid': pid, 'pgid': os.getpgrp(), 'start_ticks': int(fields[19])}


def validate_measurement_value(value):
    if type(value) is not int or value < 0:
        raise MeterError('MEM_INVALID_MEASUREMENT', 'Size measurement must return an exact nonnegative int')
    return value


def unit_measurement_boundary(function):
    """Pure UNIT_ONLY failure boundary; does not publish a successful sample."""
    try:
        value = function()
    except BaseException as error:
        raise MeterError('MEM_INVALID_MEASUREMENT',
                         'Declared measurement callable raised',
                         details={'exception_type': type(error).__name__}) from error
    return validate_measurement_value(value)


class FatalObserverError(MeterError):
    skip_cache_logging_close = True


class MotionComponentCache(FrozenCache):
    """Exact NEW class; all scientific inherited methods retain their old code."""
    def _allocated_bytes(self):
        return observer_for(self).meter.measure(self)


def _clone_evaluator():
    namespace = dict(_ORIGINAL_EVALUATE.__globals__)
    namespace['MotionComponentCache'] = MotionComponentCache
    clone = types.FunctionType(_ORIGINAL_EVALUATE.__code__, namespace,
                               _ORIGINAL_EVALUATE.__name__,
                               _ORIGINAL_EVALUATE.__defaults__,
                               _ORIGINAL_EVALUATE.__closure__)
    clone.__kwdefaults__ = _ORIGINAL_EVALUATE.__kwdefaults__
    clone.__annotations__ = dict(_ORIGINAL_EVALUATE.__annotations__)
    clone.__doc__ = _ORIGINAL_EVALUATE.__doc__
    clone.__module__ = __name__
    clone.__qualname__ = 'evaluate_candidate_new_exact'
    return clone


_NEW_EVALUATE = _clone_evaluator()


def evaluate_candidate_for(variant):
    if variant == 'OLD' and type(variant) is str:
        return _ORIGINAL_EVALUATE
    if variant == 'NEW' and type(variant) is str:
        return _NEW_EVALUATE
    raise MeterError('MEM_UNKNOWN_VARIANT')


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':'), sort_keys=True).encode('utf-8')


def _binding(raw, scope, variant):
    value = {} if raw is None else dict(raw)
    identity = process_identity()
    if os.name == 'nt':
        forbidden={'producer_pgid','producer_start_ticks','pgid','start_ticks','producer_pid'}
        if (forbidden.intersection(value) or type(value.get('producer_identity')) is not dict
                or set(value['producer_identity']) != set(identity)
                or any(type(value['producer_identity'][k]) is not type(v) or value['producer_identity'][k] != v for k,v in identity.items())):
            raise MeterError('MEM_PRODUCER_IDENTITY_MISMATCH', 'Explicit Windows identity required')
    for name in (() if os.name == 'nt' else ('pid', 'pgid', 'start_ticks')):
        supplied = value.get('producer_' + name, value.get(name, identity[name]))
        if type(supplied) is not int or supplied != identity[name]:
            raise MeterError('MEM_PRODUCER_IDENTITY_MISMATCH', name)
        value['producer_' + name] = supplied
        value.pop(name, None)
    value.setdefault('attempt_id', scope.get('attempt_id'))
    value.setdefault('pair_id', scope.get('batch_id'))
    value.setdefault('run_id', scope.get('batch_id'))
    value.setdefault('condition', variant)
    value.setdefault('cache_scope_id', scope.get('full_scope_id'))
    required = ('attempt_id', 'pair_id', 'run_id', 'condition', 'cache_scope_id',
                'execution_source_seal_sha256')
    if any(type(value.get(name)) is not str or not value[name] for name in required):
        raise MeterError('MEM_OBSERVER_BINDING_INCOMPLETE')
    if value['condition'] != variant or value['cache_scope_id'] != scope.get('full_scope_id'):
        raise MeterError('MEM_OBSERVER_BINDING_MISMATCH')
    return _encoded(value)


class MemoryObserver:
    def __init__(self, owner_ref, variant, scope, binding_bytes, *, gate_mode=False,
                 measurement_callback=None, buffered_callback=None):
        self.owner_ref = owner_ref
        self.variant = variant
        self.binding_bytes = bytes(bytearray(binding_bytes))
        self.meter = FourRootMeter(scope_id=scope['full_scope_id']) if variant == 'NEW' else None
        self.buffer = []
        self.handoff = {'serial': 0, 'value': None, 'consumed': 0}
        self.successful_measurement_count = 0
        self.buffered_record_count = 0
        self.durably_persisted_count = None
        self.current_bytes = None
        self.peak_bytes = 0
        self.event_frontier = 0
        self.old_reference_calls = 0
        self.measurement_failures = 0
        self.gate_mode = gate_mode
        self.measurement_callback = measurement_callback
        self.buffered_callback = buffered_callback
        self.space_checkpoints = []
        self._active = False
        self._failed = False
        self._finalized = False
        self._detached = False
        self._fault_stage = None
        self._fault_exception = None
        self._receipt = None
        self._file_state = {'pending_path': None, 'final_path': None,
                            'bytes_accepted_by_file_write': None,
                            'established_file_bytes': None}

    def _fatal(self, error, stage):
        self._failed = True
        # Keep scalar facts available even when constructor has not returned.
        details = self.snapshot()
        details.update(failure_stage=stage, actual_peak_preserved=True,
                       original_exception_type=type(error).__name__,
                       skip_cache_logging_close=True)
        return FatalObserverError('MEASUREMENT_SIDECAR_WRITE_FAILED_AFTER_PEAK',
                                  str(error), details=details)

    def _check_fault(self, stage):
        if self._fault_stage == stage:
            error = self._fault_exception or RuntimeError('Injected ' + stage)
            self._fault_stage = None
            self._fault_exception = None
            raise error

    def inject_failure(self, stage, exception=None):
        if not self.gate_mode or stage not in ('buffer_append', 'batch_flush'):
            raise MeterError('MEM_UNAUTHORIZED_FAULT_INJECTION')
        if self._fault_stage is not None or self._failed:
            raise MeterError('MEM_FAULT_INJECTION_ALREADY_ARMED')
        self._fault_stage = stage
        self._fault_exception = exception

    def measured(self, owner, value):
        try:
            validate_measurement_value(value)
            self.handoff['serial'] += 1
            self.handoff['value'] = value
        finally:
            owner = None
        return value

    def after_peak(self, owner, peak_before):
        """Called only after the unchanged old _record returned normally."""
        serial = self.handoff['serial']
        if serial <= self.handoff['consumed']:
            raise MeterError('MEM_MEASUREMENT_HANDOFF_MISSING')
        current = validate_measurement_value(self.handoff['value'])
        peak_after = owner._peak_cache_bytes
        if type(peak_after) is not int or peak_after != max(peak_before, current):
            raise MeterError('MEM_PEAK_COMMIT_MISMATCH')
        self.handoff['consumed'] = serial
        self.handoff['value'] = None
        trace = owner._trace
        observed = len(trace)
        previous = self.event_frontier
        if observed <= previous:
            raise MeterError('MEM_EVENT_FRONTIER_MISMATCH')
        event = trace[-1]
        self.current_bytes = current
        self.peak_bytes = peak_after
        self.successful_measurement_count += 1
        self.event_frontier = observed
        binding = row = None
        try:
            try:
                binding = json.loads(self.binding_bytes)
                row = {'message_kind': 'memory_measurement_record', 'record_version': '0.1',
                       'contract_id': CONTRACT_ID,
                       **{key: binding[key] for key in ('attempt_id', 'pair_id', 'run_id', 'condition',
                          'cache_scope_id')},
                       **({'producer_identity': binding['producer_identity']} if 'producer_identity' in binding else
                          {k: binding[k] for k in ('producer_pid','producer_pgid','producer_start_ticks')}),
                       'event_index': event['event_index'], 'event_kind': event['event'],
                       'event_digest': event['event_digest'],
                       'measurement_index': self.successful_measurement_count - 1,
                       'current_bytes': current, 'peak_before_bytes': peak_before,
                       'peak_after_bytes': peak_after,
                       'previous_measured_event_frontier': previous,
                       'observed_event_frontier': observed,
                       'absorbed_event_indices': list(range(previous, observed)),
                       'tracking_mode': 'OLD_FULL_SCAN' if self.variant == 'OLD' else 'NEW_INCREMENTAL'}
                # Both callback arguments and the eventual buffer row are truly
                # detached from ordinary source str/float/container identities.
                encoded_row = _encoded(row) + b'\n'
                gate_info = json.loads(encoded_row) if self.measurement_callback is not None else None
            except BaseException as error:
                raise self._fatal(error, 'buffer_encode') from error
            if self.measurement_callback is not None:
                # G0 oracle/conformance failures retain their actual exception;
                # they are not falsely described as persistence failures.
                self.measurement_callback(owner, gate_info)
            try:
                self._check_fault('buffer_append')
                self.buffer.append(encoded_row)
                self.buffered_record_count += 1
            except BaseException as error:
                raise self._fatal(error, 'buffer_append') from error
            if self.buffered_callback is not None:
                self.buffered_callback(owner, json.loads(encoded_row))
        finally:
            trace = event = row = binding = owner = None

    def snapshot(self):
        meter = None if self.meter is None else self.meter.snapshot()
        return {'binding': json.loads(self.binding_bytes), 'condition': self.variant,
                'current_bytes': self.current_bytes, 'peak_bytes': self.peak_bytes,
                'successful_measurement_count': self.successful_measurement_count,
                'buffered_record_count': self.buffered_record_count,
                'durably_persisted_count': self.durably_persisted_count,
                'event_frontier': self.event_frontier,
                'measurement_frontier': self.successful_measurement_count,
                'pending_event_count': self._pending_event_count(),
                'old_reference_calls': self.old_reference_calls,
                'full_walk_oracle_calls': self.old_reference_calls,
                'external_gate_reference_calls': 'RECORDED_BY_G0_NOT_PRODUCER',
                'failed_measurements': self.measurement_failures,
                'failed': self._failed, 'finalized': self._finalized,
                'detached': self._detached, 'meter': meter,
                'sidecar_file_state': dict(self._file_state),
                'space_checkpoints': [dict(item) for item in self.space_checkpoints],
                'metadata_continuous_true_peak_bytes': None}

    def _pending_event_count(self):
        owner = self.owner_ref()
        try:
            return None if owner is None or not hasattr(owner, '_trace') else len(owner._trace) - self.event_frontier
        finally:
            owner = None

    def persistent_payload(self):
        owner = self.owner_ref()
        try:
            wrappers = [] if owner is None else [owner.__dict__.get('_record'), owner.__dict__.get('_allocated_bytes')]
            return {'meter': None if self.meter is None else self.meter.persistent_payload(),
                    'buffer': self.buffer, 'binding_bytes': self.binding_bytes,
                    'handoff': self.handoff, 'owner_ref': self.owner_ref,
                    'actual_wrappers': wrappers,
                    'actual_gate_callbacks': [self.measurement_callback, self.buffered_callback],
                    'fault': [self._fault_stage, self._fault_exception]}
        finally:
            owner = None

    def space_checkpoint(self, label):
        # Exactly two metadata-body traversals per explicit named checkpoint.
        # The temporary root vector is not charged as persistent ledger memory.
        # Actual object/__dict__ bodies and actual scalar/table/closure objects
        # are sampled. Callback-owned state and function globals are excluded.
        owner = self.owner_ref()
        roots = [self]
        fixed_bodies = sys.getsizeof(self.__dict__)
        excluded = {'buffer', 'meter', 'measurement_callback', 'buffered_callback'}
        roots.extend(value for name, value in self.__dict__.items() if name not in excluded)
        if self.meter is not None:
            roots.append(self.meter)
            roots.extend(self.meter.__dict__.values())
            fixed_bodies += sys.getsizeof(self.meter.__dict__)
        try:
            if owner is not None:
                for name in ('_record', '_allocated_bytes'):
                    wrapper = owner.__dict__.get(name)
                    if wrapper is not None:
                        roots.append(wrapper)
                        if wrapper.__closure__ is not None:
                            roots.append(wrapper.__closure__)
            metadata = fixed_bodies + metadata_body_size(roots, roots=True)
            buffered = metadata_body_size(self.buffer)
        finally:
            roots = owner = wrapper = None
        meter = {} if self.meter is None else self.meter.snapshot()
        receipt = {'label': str(label).encode('utf-8').decode('utf-8'), 'metric_scope': 'NAMED_CHECKPOINT_ONLY',
                   'metadata_body_bytes': metadata, 'buffer_body_bytes': buffered,
                   'ledger_metadata_checkpoint_bytes': metadata,
                   'measurement_buffer_checkpoint_bytes': buffered,
                   'ledger_node_count': meter.get('node_count', 0),
                   'ledger_edge_count': meter.get('edge_count', 0),
                   'pending_update_count': meter.get('pending_update_count', 0),
                   'buffered_record_count': self.buffered_record_count,
                   'successful_measurement_count': self.successful_measurement_count,
                   'event_frontier': self.event_frontier,
                   'measurement_frontier': self.successful_measurement_count,
                   'continuous_true_peak_available': False,
                   'metadata_sample_scope': 'actual_observer_meter_dict_bodies_scalar_tables_wrapper_closure_bodies_excluding_callback_state_function_globals_and_target_graph',
                   'buffer_sample_scope': 'actual_buffer_list_and_owned_encoded_bytes_separate_from_ledger'}
        self.space_checkpoints.append(receipt)
        return dict(receipt)

    def finalize(self, out):
        if self._finalized or self._failed or self._detached:
            raise MeterError('MEM_SIDECAR_FINALIZATION_NOT_ALLOWED')
        owner = self.owner_ref()
        try:
            if owner is None:
                raise MeterError('IDENTITY_LIFETIME_ASSURANCE_FAILED')
            if owner._status != 'CLOSED' and not (self.gate_mode and self._fault_stage == 'batch_flush'):
                raise MeterError('MEM_SIDECAR_FINALIZE_REQUIRES_NORMAL_CLOSE')
            self._check_fault('batch_flush')
            directory = Path(out)
            directory.mkdir(parents=True, exist_ok=True)
            final = directory / 'memory_measurements.jsonl'
            partial = directory / 'memory_measurements.jsonl.pending'
            self._file_state['pending_path'] = str(partial.resolve())
            self._file_state['final_path'] = str(final.resolve())
            if final.exists() or partial.exists():
                raise FileExistsError('Sidecar output already exists')
            with partial.open('xb') as handle:
                accepted = 0
                self._file_state['bytes_accepted_by_file_write'] = 0
                for record in self.buffer:
                    actual = handle.write(record)
                    if actual != len(record):
                        raise OSError('Short sidecar write')
                    accepted += actual
                    self._file_state['bytes_accepted_by_file_write'] = accepted
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(partial, final)
            directory_fd = None if os.name == 'nt' else os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            try:
                if directory_fd is not None: os.fsync(directory_fd)
            finally:
                if directory_fd is not None: os.close(directory_fd)
            # Establish actual on-disk bytes, not the presumed buffer length.
            data = final.read_bytes()
            if data != b''.join(self.buffer):
                raise OSError('Sidecar content differs after atomic commit')
            pin = {'path': str(final.resolve()), 'sha256': hashlib.sha256(data).hexdigest(),
                   'size_bytes': len(data)}
            self._file_state['established_file_bytes'] = len(data)
            self.durably_persisted_count = self.buffered_record_count
            self._finalized = True
            self._receipt = {'completed': True, 'sidecar_pin': pin,
                             'successful_measurement_count': self.successful_measurement_count,
                             'buffered_record_count': self.buffered_record_count,
                             'durably_persisted_count': self.durably_persisted_count,
                             'binding': json.loads(self.binding_bytes)}
            return dict(self._receipt)
        except MeterError as error:
            if error.code in ('MEM_SIDECAR_FINALIZE_REQUIRES_NORMAL_CLOSE',
                              'IDENTITY_LIFETIME_ASSURANCE_FAILED'):
                raise
            raise self._fatal(error, 'batch_flush') from error
        except BaseException as error:
            raise self._fatal(error, 'batch_flush') from error
        finally:
            owner = None


def observer_for(cache):
    try:
        return _OBSERVERS[cache]
    except (KeyError, TypeError) as error:
        raise MeterError('MEM_CACHE_OBSERVER_UNAVAILABLE') from error


def make_cache(variant, scope, request, **kwargs):
    if type(variant) is not str or variant not in ('OLD', 'NEW'):
        raise MeterError('MEM_UNKNOWN_VARIANT')
    raw_binding = kwargs.pop('observer_binding', None)
    gate_mode = kwargs.pop('gate_mode', False)
    measurement_callback = kwargs.pop('gate_measurement_callback', None)
    buffered_callback = kwargs.pop('gate_buffered_callback', None)
    measurement_override = kwargs.pop('gate_measurement_override', None)
    if type(gate_mode) is not bool:
        raise MeterError('MEM_UNAUTHORIZED_GATE_HOOK')
    if gate_mode:
        if scope.get('scope_kind') != 'UNIT_ONLY' or kwargs.get('unit_fixture') is None:
            raise MeterError('MEM_UNAUTHORIZED_GATE_HOOK')
    elif measurement_callback is not None or buffered_callback is not None or measurement_override is not None:
        raise MeterError('MEM_UNAUTHORIZED_GATE_HOOK')
    if measurement_override is not None and not callable(measurement_override):
        raise MeterError('MEM_UNAUTHORIZED_GATE_HOOK')
    cache_class = FrozenCache if variant == 'OLD' else MotionComponentCache
    cache = cache_class.__new__(cache_class)
    try:
        owner_ref = weakref.ref(cache)
    except TypeError as error:
        raise MeterError('IDENTITY_LIFETIME_ASSURANCE_FAILED', 'Cache must support weak references') from error
    observer = MemoryObserver(owner_ref, variant, scope, _binding(raw_binding, scope, variant),
                              gate_mode=gate_mode, measurement_callback=measurement_callback,
                              buffered_callback=buffered_callback)
    _OBSERVERS[cache] = observer

    def allocated_wrapper():
        owner = owner_ref()
        try:
            if owner is None or observer._failed or observer._detached:
                raise MeterError('MEM_CACHE_OBSERVER_UNAVAILABLE')
            if measurement_override is not None:
                # G13 enters the very same original _record -> measurement
                # boundary. An override can only demonstrate pre-peak refusal;
                # no successful fake numerical measurement is permitted.
                unit_measurement_boundary(measurement_override)
                raise MeterError('MEM_UNAUTHORIZED_VALID_MEASUREMENT_OVERRIDE')
            if variant == 'OLD':
                observer.old_reference_calls += 1
                value = _ORIGINAL_ALLOCATED(owner)
            else:
                value = observer.meter.measure(owner)
            return observer.measured(owner, value)
        except BaseException as error:
            # Original callbacks which fail before this call do not come here.
            observer.measurement_failures += 1
            if isinstance(error, MeterError):
                error.details.update(observer.snapshot())
                error.details.update(actual_peak_bytes=None if owner is None else owner._peak_cache_bytes,
                                     original_trace_event_count=None if owner is None else len(owner._trace))
            raise
        finally:
            owner = None

    def record_wrapper(*args, **record_kwargs):
        owner = owner_ref()
        entered = False
        try:
            if owner is None or observer._failed or observer._detached:
                raise MeterError('MEM_CACHE_OBSERVER_UNAVAILABLE')
            if observer._active:
                raise MeterError('UNCONTROLLED_GRAPH_WRITER', 'Reentrant record callback')
            observer._active = True
            entered = True
            before = owner._peak_cache_bytes
            # Original callback/trace/peak order is the unmodified old code.
            _ORIGINAL_RECORD(owner, *args, **record_kwargs)
            observer.after_peak(owner, before)
        finally:
            if entered:
                observer._active = False
            owner = None

    cache._allocated_bytes = allocated_wrapper
    cache._record = record_wrapper
    try:
        _ORIGINAL_INIT(cache, scope, request, **kwargs)
    except BaseException:
        # No close, retry, scanner, or invented sample on constructor failure.
        # Weak registry/closures do not extend the failed owner's lifetime.
        raise
    return cache


def detach(cache):
    observer = observer_for(cache)
    for name in ('_record', '_allocated_bytes'):
        cache.__dict__.pop(name, None)
    _OBSERVERS.pop(cache, None)
    observer._detached = True
    observer.measurement_callback = observer.buffered_callback = None
    observer.handoff.clear()
    observer._fault_exception = None
    observer._fault_stage = None
    if observer.meter is not None:
        observer.meter.dispose()
