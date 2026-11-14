"""Role access guards and public stream identity checks, with no model imports.

The guard is pre-access isolation for these controlled Python processes, not an
OS sandbox against arbitrary native code. Exact readable inputs come from the
trusted launcher after seal verification; callers cannot widen their own role.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from research.information_service_bridge.sensing_worker import (
    PublicAccessGuard, PUBLIC_MODULES as OLD_PUBLIC_MODULES,
    validate_startup as _old_validate_startup, _inside)
from research.information_service_bridge.common import digest as transport_digest
from .common import CONTRACT_ID, AccessDenied, ContractError, digest


PREFIX = 'research.information_service_online'
BASE_MODULES = frozenset(set(OLD_PUBLIC_MODULES) | {
    PREFIX, PREFIX + '.common', PREFIX + '.runtime'})
SENSE_MODULES = BASE_MODULES | {PREFIX + '.sensing'}
PRODUCTION_MODULES = frozenset({
    'pursuit_v2', 'pursuit_v2.config', 'pursuit_v2.types',
    'pursuit_v2.service', 'pursuit_v2.physics', 'pursuit_v2.observation_geometry',
    # The frozen package __init__ eagerly loads these when Config is imported.
    'pursuit_v2.scenario', 'pursuit_v2.motion', 'pursuit_v2.environment',
    'research.quality_allocation', 'research.quality_allocation.candidates',
    'research.quality_allocation.certified_solver'})
MODEL_BASE_MODULES = BASE_MODULES | PRODUCTION_MODULES | {
    PREFIX + '.model_worker', PREFIX + '.public', PREFIX + '.measurements', PREFIX + '.admission', PREFIX + '.adapter'}
REGRESSION_TESTS = (
    'test_information_service_public', 'test_information_service_clock',
    'test_cooperative_sensing', 'test_service_physics', 'test_service_reference',
    'test_observation_geometry', 'test_service_three_robot',
    'test_gq_bridge_public', 'test_gq_bridge_isolation', 'test_gq_bridge_environment')
NEW_UNIT_TESTS = ('test_gq_evaluation_public', 'test_gq_evaluation_reference')
# Exact transitive project imports of the frozen 114-test regression selection.
REGRESSION_MODULES = frozenset({
    'examples', 'examples.stage2a2_cases', 'examples.stage2a2_checks',
    'pursuit_v2.allocation', 'pursuit_v2.io', 'pursuit_v2.policies',
    'pursuit_v2.replay', 'pursuit_v2.risk', 'pursuit_v2.runner',
    'pursuit_v2.service_environment', 'pursuit_v2.timing',
    'research.cooperative_sensing.fixtures',
    'research.information_service.shadow_service', 'research.information_service.worker',
    'research.information_service_bridge.environment',
    'research.quality_allocation.bounds', 'research.quality_allocation.components',
    'research.quality_allocation.lazy_allocation', 'research.quality_allocation.policy',
    'research.quality_allocation.worlds', 'research.quality_allocation.service_migration',
    'research.quality_allocation.service_migration.additive',
    'research.quality_allocation.service_migration.bounds',
    'research.quality_allocation.service_migration.domain',
    'research.quality_allocation.service_migration.fixtures',
    'research.quality_allocation.service_migration.lazy_gate',
    'research.quality_allocation.service_migration.reference',
    'research.quality_allocation.service_migration.shared'})
ROLE_MODULES = {
    'sense': SENSE_MODULES,
    'execution': MODEL_BASE_MODULES | {PREFIX + '.execution', 'pursuit_v2.service_environment'},
    'predictor': MODEL_BASE_MODULES | {PREFIX + '.evaluator'},
    'reference': MODEL_BASE_MODULES | {PREFIX + '.reference'},
    'selector': MODEL_BASE_MODULES | {PREFIX + '.selection'},
    'audit': MODEL_BASE_MODULES | {PREFIX + '.acceptance', PREFIX + '.reference',
        PREFIX + '.short_checks', PREFIX + '.interface_checks', PREFIX + '.execution', PREFIX + '.evaluator', PREFIX + '.selection',
        PREFIX + '.quality_audit', PREFIX + '.episode_audit', PREFIX + '.supervision',
        'research.information_service_bridge.guardian', 'pursuit_v2.service_environment'},
    'regression': MODEL_BASE_MODULES | REGRESSION_MODULES | {
        PREFIX + '.regression_runner', PREFIX + '.reference',
        'research.information_service_evaluation',
        'research.information_service_evaluation.common',
        'research.information_service_evaluation.public',
        'research.information_service_evaluation.reference',
        'research.information_service_evaluation.regression_runner',
        'tests', 'service_oracle', 'tests.service_oracle', *REGRESSION_TESTS, *NEW_UNIT_TESTS,
        *('tests.' + name for name in (*REGRESSION_TESTS, *NEW_UNIT_TESTS))},
}
SENSOR_PRIVATE_LEAVES = frozenset(('public', 'evaluator', 'reference', 'acceptance',
                                  'prefix_export', 'runner', 'model_worker', 'fixtures',
                                  'private_probe', 'admission'))


def validate_worker_startup(args, *, transport_role=None, environ=None):
    """Reuse the frozen environment/argv validation without changing it."""
    values = vars(args).copy() if isinstance(args, argparse.Namespace) else dict(args)
    role = values.get('role')
    if role not in ('env', 'sense') or (transport_role is not None and role != transport_role):
        raise AccessDenied('Unexpected transport role for protected worker')
    values['role'] = 'sense'
    checked = _old_validate_startup(values, environ=environ)
    checked.role = role
    return checked


class RoleAccessGuard(PublicAccessGuard):
    """Explicit project-module and exact sealed-file permissions by role."""
    def __init__(self, role, project_root, output, ipc_fd=None, *, read_files=(),
                 extra_modules=()):
        if role not in ROLE_MODULES:
            raise AccessDenied('Unknown protected role')
        self.role = role
        self.allowed_modules = set(ROLE_MODULES[role])
        for name in extra_modules:
            if name not in self.allowed_modules:
                raise AccessDenied('Runtime arguments cannot extend the frozen role module list')
        super().__init__(project_root, output, ipc_fd)
        self.public_files = set()
        for name in self.allowed_modules:
            base = self.root.joinpath(*name.split('.'))
            self.public_files.add(base.with_suffix('.py'))
            self.public_files.add(base / '__init__.py')
        self.public_files.add(self.root / 'examples/validate_stage2a5b_gq_online.py')
        if role == 'regression':
            self.public_files.update(self.root / 'tests' / (name + '.py')
                                     for name in (*REGRESSION_TESTS, *NEW_UNIT_TESTS, 'service_oracle'))
        # The actual interpreter fingerprint is a declared runtime artifact.
        self.runtime_files.add(Path(sys.executable).resolve())
        self.read_files = {Path(path).resolve() for path in read_files}
        if len(self.read_files) > 256:
            raise AccessDenied('More than 256 exact input files in one job')
        if role == 'sense' and self.read_files:
            raise AccessDenied('Sensor receives current IPC only, not model input files')
        for path in self.read_files:
            self._forbid_private_data(path)
        self.public_files.update(self.read_files)
        self.public_dirs = {self.root}
        for path in self.public_files:
            self.public_dirs.update(parent for parent in path.parents if _inside(parent, self.root))

    def _deny(self, operation, target):
        self.events.append(dict(role=self.role, operation=operation, target=str(target), allowed=False))
        raise AccessDenied(f'{self.role} access denied before {operation}: {target}')

    def _forbid_private_data(self, path):
        if self.role not in ('sense', 'predictor', 'reference', 'selector'):
            return
        text = str(path).lower()
        private_name = path.name.lower()
        if (private_name in {'stage2a5b_gq_full_evaluation_design.json',
                             'stage2a5b_gq_online_design.json', 'design.json',
                             'expected.json', 'physical.json', 'short_checks.json',
                             'admission.json', 'batches.json'} or
                any(token in text for token in ('/private_admission/', '/expected/', '/private_prefix/',
                                               '/audit_sidecar/', '/raw_prefix/', '/private/')) or
                any(token in private_name for token in ('sidecar', 'private_snapshot', 'raw_snapshot',
                                                        'private_resume', 'future_turn', 'raw_prefix',
                                                        'seal_ii', 'expected_witness'))):
            self._deny('read', path)
        if self.role in ('sense', 'predictor', 'reference', 'selector') and path.suffix in ('.py', '.pyc'):
            stem = path.name.split('.')[0]
            if _inside(path, self.root / 'research/information_service_evaluation') and stem in {
                    'execution', 'acceptance', 'fixtures', 'private_probe', 'runner', 'short_checks'}:
                self._deny('read', path)
            if self.role in ('sense', 'predictor') and stem == 'reference' and _inside(path, self.root / 'research/information_service_online'):
                self._deny('read', path)
        if self.role == 'reference' and (path.name.startswith('candidate_table') or '/candidate_tables/' in text):
            self._deny('read', path)

    def check_import(self, name):
        if (name == 'research' or name.startswith('research.') or
                name == 'pursuit_v2' or name.startswith('pursuit_v2.') or
                name == 'examples' or name.startswith('examples.') or
                name == 'tests' or name.startswith('tests.') or
                name.startswith('test_') or name == 'service_oracle') and name not in self.allowed_modules:
            self._deny('import', name)

    def check_path(self, raw, *, write=False, directory=False):
        if self.role == 'regression' and isinstance(raw, int) and raw not in self.allowed_fds:
            # shutil uses descriptors for safe cleanup of its own TMPDIR.
            resolved = Path('/proc/self/fd/' + str(raw)).resolve()
            if _inside(resolved, self.output):
                return resolved
        if not isinstance(raw, int) and raw is not None and not write and not directory:
            self._forbid_private_data(Path(os.fsdecode(raw)).resolve())
        return super().check_path(raw, write=write, directory=directory)

    def _regression_relative(self, path, directory_fd):
        path = Path(os.fsdecode(path))
        if directory_fd is not None and directory_fd != -1 and not path.is_absolute():
            parent = Path('/proc/self/fd/' + str(directory_fd)).resolve()
            if not _inside(parent, self.output):
                self._deny('dir_fd', directory_fd)
            path = parent / path
        return path.resolve()

    def audit(self, event, args):
        # Frozen isolation unit tests create their own symlink canary inside
        # output/tmp before enabling an inner guard. No other role can do so.
        if (self.role == 'regression' and self.enabled and not self._checking and
                event == 'os.symlink'):
            source, destination = (Path(os.fsdecode(value)).resolve() for value in args[:2])
            if _inside(source, self.output) and _inside(destination, self.output):
                return
            self._deny(event, args[:2])
        if self.role == 'regression' and self.enabled and not self._checking:
            fd_position = {'os.remove': 1, 'os.rmdir': 1, 'os.mkdir': 2,
                           'os.chmod': 2, 'os.utime': 3}.get(event)
            if fd_position is not None and len(args) > fd_position and args[fd_position] != -1:
                path = self._regression_relative(args[0], args[fd_position])
                self.check_path(path, write=True)
                return
        return super().audit(event, args)

    def install(self):
        if self.role == 'regression':
            # The open audit event omits dir_fd. Resolve it explicitly before
            # calling the native open so nested temporary cleanup stays scoped.
            self._original_os_open = os.open
            original_open = self._original_os_open
            def guarded_open(path, flags, mode=0o777, *, dir_fd=None):
                if not self.enabled or dir_fd is None:
                    return original_open(path, flags, mode, dir_fd=dir_fd)
                resolved = self._regression_relative(path, dir_fd)
                write = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
                self.check_path(resolved, write=write)
                checking = self._checking
                self._checking = True
                try:
                    return original_open(path, flags, mode, dir_fd=dir_fd)
                finally:
                    self._checking = checking
            self._regression_open = guarded_open
            os.open = guarded_open
        return super().install()

    def disable(self):
        super().disable()
        if self.role == 'regression' and getattr(self, '_regression_open', None) is os.open:
            os.open = self._original_os_open

    def admit_manifest(self, reference):
        """Expand one already readable, externally hash-pinned exact manifest.

        The manifest grants no directory permission and is never followed
        recursively. All inputs together, including the manifest, stay <=256.
        """
        entries = read_compact_manifest(reference)
        paths = {Path(item['path']).resolve() for item in entries}
        if len(paths | self.read_files) > 256:
            self._deny('manifest', 'More than 256 exact input files including manifest')
        for path in paths:
            self._forbid_private_data(path)
        old_files,old_reads,old_dirs=set(self.public_files),set(self.read_files),set(self.public_dirs)
        try:
            self.public_files.update(paths)
            self.read_files.update(paths)
            for path in paths:
                self.public_dirs.update(parent for parent in path.parents if _inside(parent,self.root))
            for item in entries:
                if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() != item['sha256']:
                    raise ContractError('Manifest input bytes differ from their sealed hash')
        except BaseException:
            self.public_files,self.read_files,self.public_dirs=old_files,old_reads,old_dirs
            raise
        return copy.deepcopy(entries)


def install_role_guard(role, out, fd=None, *, public_files=(), read_files=None,
                       extra_public_modules=(), extra_modules=None, project_root=None):
    """Install before importing the role's implementation.

    read_files/public_files are aliases for exact trusted-launcher-approved
    inputs. No directory allowlist or arbitrary path fallback is provided.
    """
    if read_files is not None and public_files:
        raise AccessDenied('Use one exact readable-file argument')
    if extra_modules is not None and extra_public_modules:
        raise AccessDenied('Use one exact module-extension argument')
    root = Path(__file__).resolve().parents[2] if project_root is None else Path(project_root)
    guard = RoleAccessGuard(role, root, out, fd,
                           read_files=public_files if read_files is None else read_files,
                           extra_modules=extra_public_modules if extra_modules is None else extra_modules)
    guard.install()
    guard.check_loaded_modules()
    return guard


MAX_FRAME_BYTES = 2 * 1024 * 1024
MAX_INPUT_FILES = 256
CONTEXT_FIELDS = frozenset(('work_instance_id','request_identity','world_identity','action_identity',
    'checkpoint_id','physical_environment_id','purpose','segment_id','service_start_tick','first_new_fusion_tick'))
REGISTRATION_FIELDS = frozenset(('stream_id','target_id','start_tick','allowed_sensor_ids','context'))


def _hex(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None


def validate_context(value):
    if not isinstance(value,dict) or set(value) != CONTEXT_FIELDS:
        raise ContractError('Exact online scientific/segment context required')
    c=copy.deepcopy(value)
    for key in ('work_instance_id','physical_environment_id'):
        if not isinstance(c[key],str) or not 0<len(c[key])<=200:
            raise ContractError('Invalid public operational identity '+key)
    if not _hex(c['checkpoint_id']) or not _hex(c['request_identity']):
        raise ContractError('Checkpoint/request must be canonical SHA256 identities')
    for key in ('service_start_tick','first_new_fusion_tick'):
        if type(c[key]) is not int or c[key]<0:
            raise ContractError('Invalid registered clock origin')
    offset=c['first_new_fusion_tick']-c['service_start_tick']
    if offset not in (0,1):
        raise ContractError('Fresh fusion begins at k, or k+1 after reused actual endpoint')
    if c['purpose']=='ACTUAL_EXECUTION':
        if (not _hex(c['segment_id']) or c['world_identity'] is not None or
                c['request_identity']!=c['checkpoint_id'] or c['action_identity']!=c['segment_id']):
            raise ContractError('Actual stream must bind its prepared/committed segment, not a forecast')
    elif c['purpose'] in ('CANDIDATE_PREDICTION','INDEPENDENT_REFERENCE'):
        if not _hex(c['world_identity']) or not _hex(c['action_identity']):
            raise ContractError('Predicted/reference streams require candidate and world identities')
        if (offset==1 and not _hex(c['segment_id'])) or (offset==0 and c['segment_id'] is not None):
            raise ContractError('KEEP prediction must bind retained actual segment; nonKEEP has null segment')
    else:
        raise ContractError('Unregistered online stream purpose')
    return c


def context_from_flow(flow):
    """Map an admitted schema FlowRegistration without disclosing target points."""
    fields={'message_kind','contract_id','operation','purpose','checkpoint_id','evaluation_request_id',
            'world_id','candidate_id','target_id','team','service_start_tick','first_new_fusion_tick',
            'actual_endpoint_reused_at_start','source_contract_id','allowed_sensor_ids','segment_id'}
    if not isinstance(flow,dict) or set(flow)!=fields or flow['message_kind']!='flow_registration' or flow['contract_id']!='gq_online_flow_registration_v1':
        raise ContractError('Exact schema FlowRegistration required')
    operation=flow['operation']
    if not isinstance(operation,dict) or set(operation)!={'physical_environment_id','work_instance_id','stream_id'}:
        raise ContractError('Exact flow operational identities required')
    actual=flow['purpose']=='ACTUAL_EXECUTION'
    if type(flow['actual_endpoint_reused_at_start']) is not bool:
        raise ContractError('Endpoint reuse marker must be boolean')
    if flow['first_new_fusion_tick'] != flow['service_start_tick']+int(flow['actual_endpoint_reused_at_start']):
        raise ContractError('Flow first tick differs from explicit endpoint reuse')
    if flow['source_contract_id']!=('gq_online_actual_sampling_v1' if actual else 'gq_mixed_observed_model_left_v1'):
        raise ContractError('Actual/prediction source purpose mismatch')
    if actual and any(flow[name] is not None for name in ('evaluation_request_id','world_id','candidate_id')):
        raise ContractError('Actual flow cannot carry a prediction identity')
    return validate_context(dict(work_instance_id=operation['work_instance_id'],
        physical_environment_id=operation['physical_environment_id'],purpose=flow['purpose'],
        checkpoint_id=flow['checkpoint_id'],request_identity=flow['checkpoint_id'] if actual else flow['evaluation_request_id'],
        world_identity=flow['world_id'],action_identity=flow['segment_id'] if actual else flow['candidate_id'],
        segment_id=flow['segment_id'],service_start_tick=flow['service_start_tick'],
        first_new_fusion_tick=flow['first_new_fusion_tick']))


def sensing_registration(flow):
    context=context_from_flow(flow)
    team=flow['team']
    if not isinstance(team,list) or len(team) not in (2,3):
        raise ContractError('Online fusion requires complete q2/q3 team')
    if any(not isinstance(row,dict) or set(row)!={'robot_id','role'} or type(row['robot_id']) is not int
           or row['robot_id']<0 for row in team):
        raise ContractError('Malformed registered team')
    ids=['U'+str(row['robot_id']) for row in team]
    roles=[row['role'] for row in team]
    catalog={2:{'dual_neg45','dual_pos45'},3:{'tri_0','tri_120','tri_240'}}
    if len(set(ids))!=len(ids) or set(roles)!=catalog[len(team)] or ids!=flow['allowed_sensor_ids']:
        raise ContractError('Registered team/roles/allowed Uk differ')
    result=dict(stream_id=flow['operation']['stream_id'],target_id=flow['target_id'],
                start_tick=flow['first_new_fusion_tick'],allowed_sensor_ids=ids,context=context)
    validate_registration(result)
    return result


def validate_registration(reg):
    if not isinstance(reg,dict) or set(reg)!=REGISTRATION_FIELDS:
        raise ContractError('Exact sensing registration fields required')
    context=validate_context(reg['context'])
    if not isinstance(reg['stream_id'],str) or not 0<len(reg['stream_id'])<=300:
        raise ContractError('Invalid stream ID')
    if type(reg['target_id']) is not int or reg['target_id']<0 or type(reg['start_tick']) is not int:
        raise ContractError('Invalid target/start tick')
    ids=reg['allowed_sensor_ids']
    if (not isinstance(ids,list) or len(ids) not in (2,3) or
        any(not isinstance(v,str) or re.fullmatch(r'U(?:0|[1-9][0-9]*)',v) is None for v in ids) or
        len(ids)!=len(set(ids)) or ids!=sorted(ids,key=lambda v:int(v[1:]))):
        raise ContractError('Allowed Uk must be unique canonical stable order')
    if reg['start_tick']!=context['first_new_fusion_tick']:
        raise ContractError('Transport processor origin differs from registered fresh-fusion tick')
    return copy.deepcopy(reg)


def serialized_message_size(message):
    size=len(json.dumps(message,separators=(',',':'),ensure_ascii=False,sort_keys=True,allow_nan=False).encode('utf-8'))
    if size>MAX_FRAME_BYTES:
        raise ContractError('IPC payload exceeds frozen 2 MiB before enqueue')
    return size


def read_compact_manifest(reference):
    """Read one exact externally pinned manifest; never recurse or glob."""
    if not isinstance(reference,dict) or set(reference)!={'path','sha256','input_root'} or not _hex(reference['sha256']):
        raise ContractError('Exact pinned compact manifest reference required')
    manifest_path=Path(reference['path'])
    root=Path(reference['input_root']).resolve()
    if not manifest_path.is_absolute() or manifest_path.is_symlink():
        raise ContractError('Manifest must be an exact absolute nonsymlink file')
    raw=manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=reference['sha256']:
        raise ContractError('Compact manifest bytes differ from external pin')
    value=json.loads(raw)
    if not isinstance(value,dict) or set(value)!={'contract_id','entries'} or value['contract_id']!='gq_online_exact_input_manifest_v1':
        raise ContractError('Exact manifest schema required')
    entries=value['entries']
    if not isinstance(entries,list) or len(entries)>MAX_INPUT_FILES:
        raise ContractError('More than 256 exact manifest input entries')
    rows=[];seen_ids=set();seen_paths=set()
    for row in entries:
        if not isinstance(row,dict) or set(row)!={'file_id','relative_path','sha256'}:
            raise ContractError('Manifest grants only explicit file identity/path/hash')
        rel=Path(row['relative_path'])
        if (not isinstance(row['file_id'],str) or not row['file_id'] or row['file_id'] in seen_ids
                or not _hex(row['sha256']) or rel.is_absolute() or '..' in rel.parts):
            raise ContractError('Invalid, duplicate or escaping compact input entry')
        nominal=root/rel;resolved=nominal.resolve()
        if resolved!=nominal or not _inside(resolved,root) or not resolved.is_file():
            raise ContractError('Input entry is symlinked, absent or outside its registered root')
        if str(resolved) in seen_paths:
            raise ContractError('Same input path appears under multiple aliases')
        seen_ids.add(row['file_id']);seen_paths.add(str(resolved))
        rows.append(dict(file_id=row['file_id'],path=str(resolved),sha256=row['sha256']))
    return rows


class ResponseContextRegistry:
    """Binds transport replies to an immutable purpose/segment/work context."""
    IDENTITY_FIELDS=frozenset(('attempt_id','pair_id','sense_request_id','target_id','stream_id','global_tick','payload_sha256'))
    def __init__(self,attempt_id,pair_id):
        self.attempt_id,self.pair_id=str(attempt_id),str(pair_id)
        self.streams,self.requests,self.committed={},{},{}
        self.failed=False
    def _error(self,message):
        self.failed=True
        raise ContractError(message)
    def register_stream(self,registration,scientific_context=None):
        if self.failed:self._error('Failed registry cannot register new work')
        reg=copy.deepcopy(registration)
        if scientific_context is not None:
            if 'context' in reg and reg['context']!=scientific_context:self._error('Conflicting registered context')
            reg['context']=copy.deepcopy(scientific_context)
        try:validate_registration(reg)
        except ContractError as e:self._error(str(e))
        stream=reg['stream_id']
        if stream in self.streams and self.streams[stream]!=reg:self._error('Stream reused across purpose/segment/work contexts')
        self.streams[stream]=reg
        return copy.deepcopy(reg)
    def bind_request(self,identity,scientific_context):
        if self.failed:self._error('Failed registry cannot send new requests')
        if not isinstance(identity,dict) or set(identity)!=self.IDENTITY_FIELDS:self._error('Exact transport identity required')
        reg=self.streams.get(identity['stream_id'])
        if reg is None or reg['context']!=scientific_context:self._error('Unregistered scientific purpose/segment context')
        if identity['attempt_id']!=self.attempt_id or identity['pair_id']!=self.pair_id:self._error('Foreign transport instance')
        if (type(identity['global_tick']) is not int or identity['global_tick']<reg['start_tick'] or
            identity['target_id']!=reg['target_id'] or type(identity['target_id']) is not int):self._error('Wrong target/fresh-fusion tick')
        if not isinstance(identity['sense_request_id'],str) or not identity['sense_request_id'] or not _hex(identity['payload_sha256']):self._error('Invalid request/hash')
        key=identity['sense_request_id'];row=dict(identity=copy.deepcopy(identity),context=copy.deepcopy(scientific_context))
        if key in self.requests and self.requests[key]!=row:self._error('Conflicting request binding')
        self.requests[key]=row
        return copy.deepcopy(row)
    def accept_response(self,identity,result,scientific_context):
        if self.failed:self._error('Failed registry cannot accept a response')
        key=identity.get('sense_request_id') if isinstance(identity,dict) else None
        expected=self.requests.get(key)
        if expected is None or expected['identity']!=identity or expected['context']!=scientific_context:self._error('Response belongs to another target/checkpoint/segment/purpose')
        if not isinstance(result,dict) or result.get('flow_context')!=scientific_context:self._error('Sensor response did not echo its registered flow context')
        if result.get('flow_registration')!=self.streams[identity['stream_id']]:self._error('Sensor response target/allowed Uk/first tick registration differs')
        answer_hash=digest(result)
        if key in self.committed:
            if self.committed[key]['result_sha256']!=answer_hash:self._error('Conflicting duplicate response')
            return dict(committed=False,duplicate=True,commit_id=self.committed[key]['commit_id'])
        commit_id=digest(dict(identity=identity,context=scientific_context,result_sha256=answer_hash))
        self.committed[key]=dict(identity=copy.deepcopy(identity),result_sha256=answer_hash,commit_id=commit_id)
        return dict(committed=True,duplicate=False,commit_id=commit_id)
    def snapshot(self):
        return copy.deepcopy(dict(failed=self.failed,streams=self.streams,requests=self.requests,committed=self.committed))


StreamContextRegistry=ResponseContextRegistry


