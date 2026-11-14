"""Typed JSON comparison and independently admitted, exact-path projection.

No estimator, cache, controller or old tolerance comparer is imported here.
Production authority comes from trusted caller callbacks, never document flags.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import struct

from .common import STAGE_CONTRACT, ContractError, digest, save_json, sha_file

COMPARATOR_ID = 'gq_shared_full_typed_binary64_v1'
MISSING = object()
_NUMBER = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?')
_HEX = re.compile(r'[0-9a-f]{64}\Z')
_TYPES = {type(None): 'null', bool: 'bool', int: 'int', float: 'float',
          str: 'string', list: 'array', dict: 'object'}
_META = ('artifact_scope', 'left_artifact_id', 'right_artifact_id',
         'scientific_request_id', 'candidate_id_or_null', 'comparison_route')
_ROUTES = ('RS_EXACT', 'RS_DIAGNOSTIC', 'INDEPENDENT_PHYSICAL_AUDIT', 'COMPARATOR_SELF_TEST')


def pointer(parent, key):
    return parent + '/' + str(key).replace('~', '~0').replace('/', '~1')


class ComparisonError(ContractError):
    def __init__(self, code, json_pointer='', raw_lexeme=None, byte_offset=None,
                 status='REJECTED_INPUT'):
        self.code = code
        self.json_pointer = json_pointer
        self.raw_lexeme = raw_lexeme
        self.byte_offset = byte_offset
        self.status = status
        super().__init__(f'{code} at {json_pointer or "/"}')

    def record(self, side):
        return dict(side=side, json_pointer=self.json_pointer, code=self.code,
                    raw_lexeme=self.raw_lexeme, byte_offset=self.byte_offset)


class ContextError(ComparisonError):
    def __init__(self, code, json_pointer=''):
        super().__init__(code, json_pointer, status='CONTEXT_REJECTED')


class _RawReader:
    def __init__(self, raw):
        if type(raw) is bytes:
            try:
                self.text = raw.decode('utf-8', errors='strict')
            except UnicodeDecodeError as e:
                raise ComparisonError('INVALID_UTF8', byte_offset=e.start) from e
        elif type(raw) is str:
            try:
                raw.encode('utf-8', errors='strict')
            except UnicodeEncodeError as e:
                raise ComparisonError('INVALID_UTF8', byte_offset=e.start) from e
            self.text = raw
        else:
            raise ComparisonError('RAW_UTF8_JSON_REQUIRED')
        self.at = 0
        self.lexemes = {}

    def whitespace(self):
        n = len(self.text)
        while self.at < n and self.text[self.at] in ' \t\n\r':
            self.at += 1

    def syntax(self):
        offset = len(self.text[:self.at].encode('utf-8'))
        raise ComparisonError('INVALID_JSON_SYNTAX', byte_offset=offset)

    def string(self):
        try:
            value, end = json.JSONDecoder().raw_decode(self.text, self.at)
        except (ValueError, RecursionError) as e:
            if isinstance(e, json.JSONDecodeError):
                self.at = e.pos
            self.syntax()
        if type(value) is not str:
            self.syntax()
        self.at = end
        return value

    def value(self, path='', depth=0):
        if depth > 256:
            raise ComparisonError('JSON_NESTING_LIMIT', path)
        self.whitespace()
        if self.at >= len(self.text):
            self.syntax()
        ch = self.text[self.at]
        if ch == '"':
            return self.string()
        if ch == '{':
            self.at += 1
            self.whitespace()
            out = {}
            if self.at < len(self.text) and self.text[self.at] == '}':
                self.at += 1
                return out
            while True:
                self.whitespace()
                if self.at >= len(self.text) or self.text[self.at] != '"':
                    self.syntax()
                key = self.string()
                key_path = pointer(path, key)
                if key in out:
                    raise ComparisonError('DUPLICATE_OBJECT_KEY', key_path, key)
                self.whitespace()
                if self.at >= len(self.text) or self.text[self.at] != ':':
                    self.syntax()
                self.at += 1
                out[key] = self.value(key_path, depth + 1)
                self.whitespace()
                if self.at >= len(self.text):
                    self.syntax()
                separator = self.text[self.at]
                self.at += 1
                if separator == '}':
                    return out
                if separator != ',':
                    self.syntax()
        if ch == '[':
            self.at += 1
            self.whitespace()
            out = []
            if self.at < len(self.text) and self.text[self.at] == ']':
                self.at += 1
                return out
            while True:
                out.append(self.value(pointer(path, len(out)), depth + 1))
                self.whitespace()
                if self.at >= len(self.text):
                    self.syntax()
                separator = self.text[self.at]
                self.at += 1
                if separator == ']':
                    return out
                if separator != ',':
                    self.syntax()
        for token in ('-Infinity', 'Infinity', 'NaN'):
            if self.text.startswith(token, self.at):
                raise ComparisonError('NONFINITE_NUMBER', path, token)
        for token, value in (('null', None), ('true', True), ('false', False)):
            if self.text.startswith(token, self.at):
                self.at += len(token)
                return value
        match = _NUMBER.match(self.text, self.at)
        if match is None:
            self.syntax()
        token = match.group()
        self.at = match.end()
        self.lexemes[path] = token
        if not any(c in token for c in '.eE'):
            if token == '-0':
                raise ComparisonError('FORBIDDEN_INTEGER_NEGATIVE_ZERO', path, token)
            try:
                return int(token)
            except ValueError as e:
                raise ComparisonError('INVALID_INTEGER', path, token) from e
        value = float(token)
        if not math.isfinite(value):
            raise ComparisonError('NONFINITE_BINARY64_CONVERSION', path, token)
        return value

    def decode(self):
        value = self.value()
        self.whitespace()
        if self.at != len(self.text):
            self.syntax()
        return value


def strict_loads(raw):
    """Decode raw UTF-8 JSON without int/bool/float or signed-zero coercion."""
    return _RawReader(raw).decode()


def strict_read(path):
    return strict_loads(Path(path).read_bytes())


def validate_value(value, path='', ancestors=None):
    """Reject unsupported/nonfinite in-memory values before any comparison."""
    kind = type(value)
    if kind not in _TYPES:
        raise ComparisonError('UNSUPPORTED_IN_MEMORY_TYPE', path)
    if kind is float and not math.isfinite(value):
        raise ComparisonError('NONFINITE_NUMBER', path, repr(value))
    if kind not in (dict, list):
        return
    ancestors = set() if ancestors is None else ancestors
    if id(value) in ancestors:
        raise ComparisonError('CYCLIC_VALUE', path)
    ancestors.add(id(value))
    try:
        if kind is dict:
            if any(type(k) is not str for k in value):
                raise ComparisonError('NON_STRING_OBJECT_KEY', path)
            for key in value:
                validate_value(value[key], pointer(path, key), ancestors)
        else:
            for i, child in enumerate(value):
                validate_value(child, pointer(path, i), ancestors)
    finally:
        ancestors.remove(id(value))


def describe(value):
    if value is MISSING:
        return dict(type='MISSING', value=None, binary64_be_hex=None, raw_lexeme=None)
    return dict(type=_TYPES[type(value)], value=deepcopy(value),
                binary64_be_hex=struct.pack('>d', value).hex() if type(value) is float else None,
                raw_lexeme=None)


def _metadata(metadata):
    if type(metadata) is not dict or set(metadata) != set(_META):
        raise ContractError('Exact comparator invocation metadata required')
    for key in ('artifact_scope', 'left_artifact_id', 'right_artifact_id'):
        if type(metadata[key]) is not str or not metadata[key]:
            raise ContractError('Invalid comparison artifact identity: ' + key)
    for key in ('scientific_request_id', 'candidate_id_or_null'):
        v = metadata[key]
        if v is not None and (type(v) is not str or _HEX.fullmatch(v) is None):
            raise ContractError('Invalid scientific comparison identity')
    if metadata['comparison_route'] not in _ROUTES:
        raise ContractError('Unknown comparison route')
    return deepcopy(metadata)


def _walk(left, right, path='', skip_float_paths=frozenset()):
    def different(reason, a=left, b=right, at=path):
        return dict(json_pointer=at, reason=reason, left=describe(a), right=describe(b))
    if type(left) is not type(right):
        return different('TYPE_MISMATCH')
    kind = type(left)
    if kind is dict:
        unequal_keys = set(left) ^ set(right)
        if unequal_keys:
            key = min(unequal_keys)
            return different('MISSING_FIELD', left.get(key, MISSING), right.get(key, MISSING), pointer(path, key))
        for key in sorted(left):
            result = _walk(left[key], right[key], pointer(path, key), skip_float_paths)
            if result is not None:
                return result
    elif kind is list:
        if len(left) != len(right):
            return different('ARRAY_LENGTH_MISMATCH')
        for i in range(len(left)):
            result = _walk(left[i], right[i], pointer(path, i), skip_float_paths)
            if result is not None:
                return result
    elif kind is float:
        if path not in skip_float_paths and struct.pack('>d', left) != struct.pack('>d', right):
            return different('BINARY64_MISMATCH')
    elif left != right:
        return different('VALUE_MISMATCH')
    return None


def first_difference(left, right, metadata=None):
    validate_value(left)
    validate_value(right)
    diff = _walk(left, right)
    return ({**_metadata(metadata), **diff} if metadata is not None and diff is not None else diff)


def _rejected(error, side):
    return dict(status=error.status, first_difference=None, rejection=error.record(side))


def compare_raw(left_raw, right_raw, metadata):
    meta = _metadata(metadata)
    values = []
    for side, raw in (('left', left_raw), ('right', right_raw)):
        try:
            values.append(strict_loads(raw))
        except ComparisonError as e:
            return _rejected(e, side)
    diff = first_difference(values[0], values[1], meta)
    return dict(status='EQUAL' if diff is None else 'DIFFERENT', first_difference=diff, rejection=None)


_FUSION_LEAVES = (
    '/frame/stream_id', '/frame/frame_id', '/frame/records/{record_index}/packet_id',
    '/result/stream_id', '/result/frame_id', '/result/frame_sha256',
    '/result/normalized_frame/stream_id', '/result/normalized_frame/frame_id',
    '/result/normalized_frame/records/{record_index}/packet_id', '/result/quality/frame_id',
    '/result/flow_context/work_instance_id', '/result/flow_context/physical_environment_id',
    '/result/flow_registration/stream_id', '/result/flow_registration/context/work_instance_id',
    '/result/flow_registration/context/physical_environment_id')
_SELECTION_LEAVES = (
    '/stream_id', '/flow_registration/operation/physical_environment_id',
    '/flow_registration/operation/work_instance_id', '/flow_registration/operation/stream_id',
    '/context/work_instance_id', '/context/physical_environment_id', '/registration/stream_id',
    '/registration/context/work_instance_id', '/registration/context/physical_environment_id')
ROW_PREFIXES = {
    'candidate_evaluation': ('/sensing_results/{sense_index}', '/frames/{frame_index}/sensing_results/{sense_index}'),
    'fusion_row_unit_context_test': ('',),
    'execution_step': ('/fusion_records/{sense_index}',),
}
PROJECTION_TEMPLATES = {
    scope: tuple(prefix + leaf for prefix in prefixes for leaf in _FUSION_LEAVES)
    for scope, prefixes in ROW_PREFIXES.items()
}
PROJECTION_TEMPLATES['execution_step'] += (
    '/fusion_records/{sense_index}/context/work_instance_id',
    '/fusion_records/{sense_index}/context/physical_environment_id')
PROJECTION_TEMPLATES['selection'] = tuple('/action_metadata/' + branch + leaf
    for branch in ('transitions/{transition_index}', 'flows/{flow_index}') for leaf in _SELECTION_LEAVES)
PROJECTION_TEMPLATES['public_checkpoint_or_request'] = ()
_DIAGNOSTIC_LEAVES = (
    '/result/estimate_result/estimate/{coordinate}', '/result/estimate_result/Q',
    '/result/estimate_result/singular_values/{index}', '/result/estimate_result/starts/{start_index}/optimality',
    '/result/estimate_result/starts/{start_index}/cost', '/result/estimate_result/starts/{start_index}/Q',
    '/result/estimate_result/starts/{start_index}/x/{coordinate}', '/result/estimate_result/starts/{start_index}/guard/x/{coordinate}',
    '/result/quality/representative_guard/x/{coordinate}', '/result/quality/estimate/{coordinate}',
    '/result/quality/J/{row}/{column}', '/result/quality/I/{row}/{column}',
    '/result/quality/information_at_estimate/{row}/{column}', '/result/quality/singular_values/{index}',
    '/result/quality/radius_proxy')


def _segments(template):
    return [s.replace('~1', '/').replace('~0', '~') for s in template.split('/')[1:]]


def _expand(value, template, required=False):
    """Concrete pointer matches; wildcard tokens match array indices only."""
    parts = _segments(template)
    found = []
    def visit(current, remaining, at):
        if not remaining:
            found.append((at, current))
            return
        part, tail = remaining[0], remaining[1:]
        if part.startswith('{') and part.endswith('}'):
            if type(current) is not list:
                if current is None and not required:
                    return
                raise ComparisonError('EXPECTED_ARRAY_AT_TEMPLATE', at)
            for i, child in enumerate(current):
                visit(child, tail, pointer(at, i))
        elif type(current) is dict and part in current:
            visit(current[part], tail, pointer(at, part))
        elif required:
            # A no-flow transition legitimately lacks the optional flow bundle.
            if (at.startswith('/action_metadata/transitions/') and type(current) is dict
                    and 'flow_registration' not in current and part in ('stream_id', 'flow_registration', 'context', 'registration')):
                return
            raise ComparisonError('MISSING_REQUIRED_PROJECTION_FIELD', pointer(at, part))
    visit(value, parts, '')
    return found


def _get(value, path):
    for part in _segments(path):
        value = value[int(part)] if type(value) is list else value[part]
    return value


def _equal(actual, expected, path, code='CONTEXT_MISMATCH'):
    diff = _walk(actual, expected)
    if diff is not None:
        raise ContextError(code, path + diff['json_pointer'])


def _exact_fields(value, fields, path):
    if type(value) is not dict:
        raise ComparisonError('EXPECTED_OBJECT', path)
    extra = set(value) - set(fields)
    if extra:
        raise ComparisonError('UNEXPECTED_FIELD', pointer(path, min(extra)))
    absent = set(fields) - set(value)
    if absent:
        raise ComparisonError('MISSING_FIELD', pointer(path, min(absent)))


_CONTEXT_FIELDS = ('work_instance_id', 'physical_environment_id', 'purpose', 'checkpoint_id',
                   'request_identity', 'world_identity', 'action_identity', 'segment_id',
                   'service_start_tick', 'first_new_fusion_tick')
_REG_FIELDS = ('stream_id', 'target_id', 'start_tick', 'allowed_sensor_ids', 'context')
_FRAME_FIELDS = ('contract_id', 'stream_id', 'frame_id', 'tick', 'target_id', 'measurement_time', 'available_time', 'records')
_RECORD_FIELDS = ('sensor_id', 'position', 'bearing', 'sigma', 'packet_id', 'measurement_tick', 'available_tick', 'status')
_RESULT_FIELDS = ('payload', 'payload_sha256', 'frame_sha256', 'normalized_frame', 'valid_sensor_count',
                  'excluded_records', 'duplicate_record_count', 'missing_sensor_ids', 'execution_contract_id',
                  'frame_id', 'stream_id', 'target_id', 'tick', 'start_tick', 'estimate_result', 'quality',
                  'skipped', 'estimator_called', 'duplicate', 'online_contract_id', 'flow_context', 'flow_registration')


def _validate_registration(reg, path=''):
    _exact_fields(reg, _REG_FIELDS, path)
    _exact_fields(reg['context'], _CONTEXT_FIELDS, path + '/context')
    ctx = reg['context']
    if ctx['purpose'] not in ('CANDIDATE_PREDICTION', 'INDEPENDENT_REFERENCE', 'ACTUAL_EXECUTION'):
        raise ContextError('UNKNOWN_PURPOSE', path + '/context/purpose')
    for key in ('target_id', 'start_tick'):
        if type(reg[key]) is not int or reg[key] < 0:
            raise ContextError('INVALID_REGISTRATION_INTEGER', pointer(path, key))
    for key in ('service_start_tick', 'first_new_fusion_tick'):
        if type(ctx[key]) is not int or ctx[key] < 0:
            raise ContextError('INVALID_CONTEXT_INTEGER', path + '/context/' + key)
    _equal(reg['start_tick'], ctx['first_new_fusion_tick'], path + '/start_tick')
    if ctx['first_new_fusion_tick'] not in (ctx['service_start_tick'], ctx['service_start_tick'] + 1):
        raise ContextError('INVALID_FIRST_FUSION_TICK', path + '/context/first_new_fusion_tick')
    if type(reg['allowed_sensor_ids']) is not list or len(reg['allowed_sensor_ids']) not in (2, 3):
        raise ContextError('INVALID_OCCUPIED_TEAM', path + '/allowed_sensor_ids')
    ids = reg['allowed_sensor_ids']
    if any(type(s) is not str or re.fullmatch(r'U(?:0|[1-9][0-9]*)', s) is None for s in ids):
        raise ContextError('INVALID_SENSOR_ID', path + '/allowed_sensor_ids')
    if ids != sorted(set(ids), key=lambda s: int(s[1:])):
        raise ContextError('UNSTABLE_SENSOR_ORDER', path + '/allowed_sensor_ids')
    if any(type(ctx[k]) is not str or not ctx[k] for k in ('work_instance_id', 'physical_environment_id')):
        raise ContextError('INVALID_OPERATION_IDENTITY', path + '/context')
    expected_stream = f"{ctx['work_instance_id']}:T{reg['target_id']}:first{reg['start_tick']}"
    _equal(reg['stream_id'], expected_stream, path + '/stream_id')


def _validate_fusion(row, reg, path, unit_only=False):
    required = {'frame', 'allowed_sensor_ids', 'start_tick', 'result'}
    permitted = required | ({'source_slots'} if unit_only else {'source_slots', 'context', 'actual_endpoint'})
    if type(row) is not dict or not required <= set(row):
        raise ComparisonError('INVALID_FUSION_ROW', path)
    extra = set(row) - permitted
    if extra:
        raise ComparisonError('UNEXPECTED_FIELD', pointer(path, min(extra)))
    _validate_registration(reg)
    result, frame = row['result'], row['frame']
    _exact_fields(result, _RESULT_FIELDS, path + '/result')
    _exact_fields(frame, _FRAME_FIELDS, path + '/frame')
    _equal(result['flow_context'], reg['context'], path + '/result/flow_context')
    _equal(result['flow_registration'], reg, path + '/result/flow_registration')
    if 'context' in row:
        _equal(row['context'], reg['context'], path + '/context')
    _equal(row['allowed_sensor_ids'], reg['allowed_sensor_ids'], path + '/allowed_sensor_ids')
    _equal(row['start_tick'], reg['start_tick'], path + '/start_tick')
    tick = frame['tick']
    if type(tick) is not int or tick < reg['start_tick']:
        raise ContextError('WRONG_FUSION_TICK', path + '/frame/tick')
    expected_id = f"{reg['stream_id']}:tick{tick}"
    _equal(frame['contract_id'], 'STAGE2A5B-A-MINIMAL-v0.2', path + '/frame/contract_id')
    _equal(frame['stream_id'], reg['stream_id'], path + '/frame/stream_id')
    _equal(frame['frame_id'], expected_id, path + '/frame/frame_id')
    _equal(frame['target_id'], reg['target_id'], path + '/frame/target_id')
    for key in ('measurement_time', 'available_time'):
        _equal(frame[key], tick * .05, path + '/frame/' + key)
    _equal(result['normalized_frame'], frame, path + '/result/normalized_frame', 'NONCANONICAL_OR_CHANGED_FRAME')
    _equal(result['frame_sha256'], digest(result['normalized_frame']), path + '/result/frame_sha256', 'FRAME_HASH_MISMATCH')
    for key, expected in (('stream_id', reg['stream_id']), ('frame_id', expected_id), ('target_id', reg['target_id']),
                          ('tick', tick), ('start_tick', reg['start_tick'])):
        _equal(result[key], expected, path + '/result/' + key)
    if type(frame['records']) is not list:
        raise ComparisonError('EXPECTED_ARRAY', path + '/frame/records')
    seen = []
    for i, record in enumerate(frame['records']):
        at = path + f'/frame/records/{i}'
        _exact_fields(record, _RECORD_FIELDS, at)
        sensor = record['sensor_id']
        if sensor not in reg['allowed_sensor_ids'] or sensor in seen:
            raise ContextError('INVALID_FRAME_SENSOR', at + '/sensor_id')
        seen.append(sensor)
        _equal(record['packet_id'], expected_id + ':' + sensor, at + '/packet_id')
        _equal(record['measurement_tick'], tick, at + '/measurement_tick')
        _equal(record['available_tick'], tick, at + '/available_tick')
        _equal(record['status'], 'ok', at + '/status')
    if seen != sorted(seen, key=lambda s: int(s[1:])):
        raise ContextError('UNSTABLE_FRAME_SENSOR_ORDER', path + '/frame/records')
    payload = result['payload']
    _exact_fields(payload, ('sensor_ids', 'positions', 'bearings', 'sigmas', 'domain'), path + '/result/payload')
    expected_payload = dict(sensor_ids=seen, positions=[r['position'] for r in frame['records']],
                            bearings=[r['bearing'] for r in frame['records']],
                            sigmas=[r['sigma'] for r in frame['records']], domain=payload['domain'])
    _equal(payload, expected_payload, path + '/result/payload', 'PAYLOAD_FRAME_MISMATCH')
    _equal(result['payload_sha256'], digest(payload), path + '/result/payload_sha256', 'PAYLOAD_HASH_MISMATCH')
    _equal(result['valid_sensor_count'], len(seen), path + '/result/valid_sensor_count')
    _equal(result['missing_sensor_ids'], [s for s in reg['allowed_sensor_ids'] if s not in seen], path + '/result/missing_sensor_ids')
    _equal(result['duplicate_record_count'], 0, path + '/result/duplicate_record_count')
    _equal(result['excluded_records'], [], path + '/result/excluded_records')
    quality = result['quality']
    if type(quality) is not dict:
        raise ComparisonError('EXPECTED_OBJECT', path + '/result/quality')
    for key, expected in (('frame_id', expected_id), ('payload_sha256', digest(payload)), ('contributing_sensor_ids', seen)):
        _equal(quality.get(key, MISSING), expected, path + '/result/quality/' + key)
    if unit_only:
        _equal(result['estimate_result'], None, path + '/result/estimate_result')
        _equal(result['estimator_called'], False, path + '/result/estimator_called')
        _equal(quality['status'], 'UNKNOWN', path + '/result/quality/status')
        slots = row.get('source_slots')
        if type(slots) is not list or len(slots) != len(reg['allowed_sensor_ids']):
            raise ContextError('INVALID_SOURCE_SLOTS', path + '/source_slots')
        for i, (slot, sensor) in enumerate(zip(slots, reg['allowed_sensor_ids'])):
            _equal(slot, dict(slot_key=dict(target_id=reg['target_id'], robot_id=int(sensor[1:]), tick=tick),
                              source='MODEL', outcome='MISSING', packet=None, observed_slot_digest=None), path + f'/source_slots/{i}')


class ComparisonAdmission:
    """Trusted in-process binding. A JSON dictionary can never instantiate it."""
    def __init__(self, *, source_sha256, registrations, expected_scientific_identity,
                 source_validator, schema_validator, source_slots_validator):
        if type(source_sha256) is not str or _HEX.fullmatch(source_sha256) is None:
            raise ContractError('Externally pinned source SHA256 required')
        callbacks = (source_validator, schema_validator, source_slots_validator)
        if not all(callable(f) for f in callbacks):
            raise ContractError('Three real trusted admission callbacks required')
        self.source_sha256 = source_sha256
        self.registrations = deepcopy(registrations)
        self.expected_scientific_identity = deepcopy(expected_scientific_identity)
        self.callbacks = callbacks
        self.unit_only = False

    @classmethod
    def unit_fixture(cls, *, source_sha256, registration):
        """Only the explicit fusion-row self-test route accepts this binding."""
        instance = object.__new__(cls)
        instance.source_sha256 = source_sha256
        instance.registrations = {registration['stream_id']: deepcopy(registration)}
        instance.expected_scientific_identity = deepcopy(registration['context'])
        instance.callbacks = ()
        instance.unit_only = True
        return instance

    def admit(self, value, raw_sha256, metadata):
        _equal(raw_sha256, self.source_sha256, '', 'EXTERNAL_SOURCE_PIN_MISMATCH')
        scope = metadata['artifact_scope']
        evidence = dict(artifact_scope=scope, source_sha256=raw_sha256, metadata=deepcopy(metadata),
                        expected_scientific_identity=deepcopy(self.expected_scientific_identity),
                        registrations=deepcopy(self.registrations))
        receipts = []
        if self.unit_only:
            if scope != 'fusion_row_unit_context_test' or metadata['comparison_route'] != 'COMPARATOR_SELF_TEST':
                raise ContextError('UNIT_BINDING_CANNOT_GRANT_PRODUCTION_AUTHORITY')
        else:
            if scope == 'fusion_row_unit_context_test':
                raise ContextError('UNIT_SCOPE_REQUIRES_EXPLICIT_UNIT_BINDING')
            for label, callback in zip(('source', 'schema', 'source_slots'), self.callbacks):
                try:
                    receipt = callback(deepcopy(value), deepcopy(evidence))
                except ComparisonError:
                    raise
                except ContractError as e:
                    raise ContextError(label.upper() + '_ADMISSION_FAILED') from e
                if type(receipt) is not dict or receipt.get('passed') is not True:
                    raise ContextError(label.upper() + '_ADMISSION_DID_NOT_PASS')
                validate_value(receipt)
                receipts.append(dict(kind=label, receipt=deepcopy(receipt)))
        if type(self.registrations) is not dict:
            raise ContextError('EXACT_REGISTRATION_MAP_REQUIRED')
        for stream, registration in self.registrations.items():
            _validate_registration(registration)
            _equal(stream, registration['stream_id'], '', 'REGISTRATION_MAP_KEY_MISMATCH')
        if scope in ROW_PREFIXES:
            for template in ROW_PREFIXES[scope]:
                for at, row in _expand(value, template, required=True):
                    try:
                        stream = row['frame']['stream_id']
                    except (KeyError, TypeError) as e:
                        raise ComparisonError('MISSING_FRAME_STREAM', at) from e
                    if stream not in self.registrations:
                        raise ContextError('UNREGISTERED_STREAM', at + '/frame/stream_id')
                    _validate_fusion(row, self.registrations[stream], at, self.unit_only)
            if scope == 'candidate_evaluation':
                rows = [row for frame in value['frames'] for row in frame['sensing_results']]
                _equal(rows, value['sensing_results'], '/sensing_results', 'DUPLICATE_FUSION_VIEWS_DIFFER')
        elif scope == 'selection':
            self._selection(value)
        elif scope != 'public_checkpoint_or_request':
            raise ContextError('UNDECLARED_ARTIFACT_SCOPE')
        return dict(passed=True, scope=scope, source_sha256=raw_sha256,
                    unit_only=self.unit_only, callbacks=receipts,
                    registrations=deepcopy(self.registrations))

    def _selection(self, value):
        meta = value['action_metadata']
        flows = meta['flows']
        for group in ('transitions', 'flows'):
            for i, row in enumerate(meta[group]):
                at = f'/action_metadata/{group}/{i}'
                if 'flow_registration' not in row:
                    if group == 'flows' or any(k in row for k in ('stream_id', 'context', 'registration')):
                        raise ContextError('INCOMPLETE_SELECTION_FLOW', at)
                    continue
                stream = row['stream_id']
                reg = self.registrations.get(stream)
                if reg is None:
                    raise ContextError('UNREGISTERED_SELECTION_STREAM', at + '/stream_id')
                _equal(row['registration'], reg, at + '/registration')
                _equal(row['context'], reg['context'], at + '/context')
                flow = row['flow_registration']
                ctx = reg['context']
                _equal(flow['operation'], dict(physical_environment_id=ctx['physical_environment_id'],
                                               work_instance_id=ctx['work_instance_id'], stream_id=stream), at + '/flow_registration/operation')
                for key, expected in (('purpose', ctx['purpose']), ('checkpoint_id', ctx['checkpoint_id']),
                                      ('segment_id', ctx['segment_id']), ('target_id', reg['target_id']),
                                      ('allowed_sensor_ids', reg['allowed_sensor_ids']),
                                      ('service_start_tick', ctx['service_start_tick']),
                                      ('first_new_fusion_tick', ctx['first_new_fusion_tick'])):
                    _equal(flow[key], expected, at + '/flow_registration/' + key)
                if group == 'transitions' and not any(_walk(row, f) is None for f in flows):
                    raise ContextError('SELECTION_DUPLICATE_FLOW_VIEWS_DIFFER', at)


def _project_admitted(value, scope):
    """Private helper: callers must obtain admission before invoking this."""
    if scope not in PROJECTION_TEMPLATES:
        raise ContractError('No projection contract for artifact scope')
    projected = deepcopy(value)
    omitted = []
    for template in PROJECTION_TEMPLATES[scope]:
        for at, original in _expand(value, template, required=True):
            if type(original) is not str:
                raise ComparisonError('PROJECTION_LEAF_TYPE_MISMATCH', at)
            parts = _segments(at)
            parent = projected
            for part in parts[:-1]:
                parent = parent[int(part)] if type(parent) is list else parent[part]
            del parent[parts[-1]]
            omitted.append(dict(json_pointer=at, value=original, template=template))
    return projected, omitted


def _diagnostic_paths(value, scope):
    paths = set()
    for prefix in ROW_PREFIXES.get(scope, ()):
        for leaf in _DIAGNOSTIC_LEAVES:
            for at, x in _expand(value, prefix + leaf):
                if type(x) is float:
                    paths.add(at)
    return paths


def compare_artifacts(left_raw, right_raw, *, metadata, left_admission, right_admission):
    meta = _metadata(metadata)
    if type(left_admission) is not ComparisonAdmission or type(right_admission) is not ComparisonAdmission:
        raise ContractError('Trusted ComparisonAdmission objects required on both sides')
    values = []
    for side, raw in (('left', left_raw), ('right', right_raw)):
        try:
            values.append(strict_loads(raw))
        except ComparisonError as e:
            return {**_rejected(e, side), 'context_admissions': [], 'omitted_operation_fields': []}
    admissions, projections, omitted = [], [], []
    # Both complete original contexts must pass before any field is projected.
    for side, raw, value, gate in (('left', left_raw, values[0], left_admission),
                                    ('right', right_raw, values[1], right_admission)):
        try:
            raw_bytes = raw.encode('utf-8') if type(raw) is str else raw
            admissions.append(gate.admit(value, hashlib.sha256(raw_bytes).hexdigest(), meta))
        except ComparisonError as e:
            return {**_rejected(e, side), 'context_admissions': admissions, 'omitted_operation_fields': []}
    for side, value in zip(('left', 'right'), values):
        try:
            projection, omissions = _project_admitted(value, meta['artifact_scope'])
        except ComparisonError as e:
            return {**_rejected(e, side), 'context_admissions': admissions, 'omitted_operation_fields': []}
        projections.append(projection)
        omitted.append(dict(side=side, fields=omissions))
    # Float diagnostic values have their own fixed tolerance gate; everything
    # else (including diagnostic shape/type/discrete flags) stays exact.
    left_diag = _diagnostic_paths(projections[0], meta['artifact_scope'])
    right_diag = _diagnostic_paths(projections[1], meta['artifact_scope'])
    diag_paths = left_diag & right_diag
    diff = _walk(projections[0], projections[1], skip_float_paths=diag_paths)
    if diff is not None:
        diff = {**meta, **diff}
    diagnostic_diff = None
    for at in sorted(diag_paths):
        a, b = _get(projections[0], at), _get(projections[1], at)
        if abs(a - b) > 1e-12:
            diagnostic_diff = {**meta, 'comparison_route': 'RS_DIAGNOSTIC',
                               'json_pointer': at, 'reason': 'DIAGNOSTIC_TOLERANCE_MISMATCH',
                               'left': describe(a), 'right': describe(b)}
            break
    failure = diff if diff is not None else diagnostic_diff
    return dict(status='EQUAL' if failure is None else 'DIFFERENT', first_difference=failure, rejection=None,
                context_admissions=admissions, omitted_operation_fields=omitted,
                exact_status='EQUAL' if diff is None else 'DIFFERENT',
                diagnostic_status='EQUAL' if diagnostic_diff is None else 'DIFFERENT',
                diagnostic_float_paths_checked=len(diag_paths), diagnostic_first_difference=diagnostic_diff)


def _file_ref(path):
    p = Path(path).resolve()
    return dict(path=str(p), sha256=sha_file(p), size_bytes=p.stat().st_size)


def compare_files(left_path, right_path, *, out, metadata, left_admission, right_admission):
    """Save strict Schema report and compact reference; never discard evidence."""
    out = Path(out)
    result = compare_artifacts(Path(left_path).read_bytes(), Path(right_path).read_bytes(),
                               metadata=metadata, left_admission=left_admission, right_admission=right_admission)
    contexts = result.get('context_admissions', [])
    context_paths = []
    for i, side in enumerate(('left', 'right')):
        path = out / (side + '_context_admission.json')
        save_json(path, contexts[i] if len(contexts) > i else dict(passed=False, not_completed=True, rejection=result.get('rejection')))
        context_paths.append(path)
    omitted_path = out / 'omitted_operation_fields.json'
    save_json(omitted_path, result.get('omitted_operation_fields', []))
    save_json(out / 'comparison_detail.json', result)
    report = dict(message_kind='shared_full_comparison_report', contract_id=STAGE_CONTRACT,
                  comparator_id=COMPARATOR_ID, status=result['status'],
                  left_artifact=_file_ref(left_path), right_artifact=_file_ref(right_path),
                  left_context_admission=_file_ref(context_paths[0]), right_context_admission=_file_ref(context_paths[1]),
                  omitted_operation_fields=_file_ref(omitted_path), first_difference=result['first_difference'],
                  rejection=result.get('rejection'))
    report_path = out / 'comparison_report.json'
    save_json(report_path, report)
    diff, rejection = result['first_difference'], result.get('rejection')
    return dict(message_kind='shared_full_comparison_report_reference', contract_id=STAGE_CONTRACT,
                report=_file_ref(report_path), status=result['status'],
                first_json_pointer=diff['json_pointer'] if diff else rejection['json_pointer'] if rejection else None,
                reason=diff['reason'] if diff else rejection['code'] if rejection else None,
                left_type=diff['left']['type'] if diff else None, right_type=diff['right']['type'] if diff else None,
                left_binary64_be_hex=diff['left']['binary64_be_hex'] if diff else None,
                right_binary64_be_hex=diff['right']['binary64_be_hex'] if diff else None)
