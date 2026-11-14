"""Narrow startup-injection adapter around the byte-frozen guardian.

Normal jobs delegate directly. Only the declared predictor I03 startup probes
alter actual env-worker argv/environment. The frozen guardian still exclusively
owns every Popen handle, process identity, signal and final wait4 accounting.
"""
from __future__ import annotations
import copy
import math
from pathlib import Path
import threading
import time
from types import SimpleNamespace

from research.information_service_bridge import guardian as frozen_guardian
from .common import ContractError, save_json
from .runtime import serialized_message_size

_INJECTION_LOCK = threading.Lock()
_SUPERVISION_LOCK = threading.Lock()
TOTAL_CPU = 1200.0
TOTAL_WALL = 2400.0
PAIR_CPU = 60.0
PAIR_WALL = 120.0


def resource_contract():
    return dict(total_cpu=TOTAL_CPU,total_wall=TOTAL_WALL,pair_cpu=PAIR_CPU,pair_wall=PAIR_WALL,
                final_usage_owner='frozen guardian os.wait4',all_gates_count_global_budget=True)


def validate_resource_contract(value):
    if not isinstance(value,dict) or any(value.get(k)!=v for k,v in
        {'total_cpu':TOTAL_CPU,'total_wall':TOTAL_WALL,'pair_cpu':PAIR_CPU,'pair_wall':PAIR_WALL}.items()):
        raise ContractError('Stale or changed online resource declaration')
    return dict(value)


def validate_resource_arithmetic(cumulative,live):
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in (cumulative,live)):
        raise ContractError('Finite nonnegative cumulative/live science CPU required')
    return dict(total=float(cumulative+live),limit=TOTAL_CPU,tripped=cumulative+live>=TOTAL_CPU,
                scope='copied arithmetic only; never substitutes final process usage')


def run_pair(job,out,entry,deadline,cumulative=0.0):
    """Adapt only the frozen runtime defaults; never edit old source or reap."""
    if type(cumulative) not in (int,float) or not math.isfinite(cumulative) or not 0<=cumulative<TOTAL_CPU:
        raise ContractError('No legal global science CPU budget remains')
    if type(deadline) not in (int,float) or not math.isfinite(deadline):
        raise ContractError('Original absolute global wall deadline required')
    if deadline-time.monotonic()>TOTAL_WALL+.1:
        raise ContractError('Global deadline exceeds frozen 2400 seconds')
    if 'total_cpu' in job.get('limits',{}) and job['limits']['total_cpu']!=TOTAL_CPU:
        raise ContractError('Stale or changed total CPU contract, including legacy300')
    for role in ('env','sense','controller'):
        payload=job.get(role+'_start',{})
        serialized_message_size(dict(type='START',payload=payload))
        if len(payload.get('read_files',[]))>256:
            raise ContractError('START names more than256 exact input files')
    with _SUPERVISION_LOCK:
        old_defaults=frozen_guardian.DEFAULT_LIMITS
        frozen_guardian.DEFAULT_LIMITS=dict(old_defaults,total_cpu=TOTAL_CPU,
                                          pair_cpu=PAIR_CPU,pair_wall=PAIR_WALL)
        try:
            result=_injection_pair(job,out,entry,deadline,cumulative)
        finally:
            frozen_guardian.DEFAULT_LIMITS=old_defaults
        receipt=dict(contract=resource_contract(),effective_limits=result['limits'],
                     original_global_deadline=deadline,cumulative_before=cumulative,
                     cumulative_after=result['cumulative_after'],
                     guardian_ownership_unchanged=True)
        save_json(Path(out)/'online_supervision_receipt.json',receipt)
        if result['limits']['total_cpu']!=TOTAL_CPU:
            raise ContractError('Runtime did not use the frozen online total CPU budget')
        return result


def _injection_pair(job, out, entry, deadline, cumulative=0.0):
    """Same result/API as frozen run_pair, with a separate injection receipt."""
    argv_extra = job.get('env_argv_extra', [])
    env_extra = job.get('env_env_extra', {})
    if not argv_extra and not env_extra:
        return frozen_guardian.run_pair(job, out, entry, deadline, cumulative)
    if job.get('predeclared_isolation_probe') is not True:
        raise ContractError('Predictor startup injection requires a predeclared isolation probe')
    if job.get('synthetic') or job.get('env_start', {}).get('kind') != 'admission_startup_no_work':
        raise ContractError('Startup injection cannot target scientific or synthetic execution')
    if argv_extra not in ([], ['--private-scenario', 'FORBIDDEN']):
        raise ContractError('Undeclared predictor argv injection')
    if env_extra not in ({}, {'GQ_PRIVATE_SCENARIO': 'FORBIDDEN'}):
        raise ContractError('Undeclared predictor environment injection')
    if bool(argv_extra) == bool(env_extra):
        raise ContractError('Each declared startup probe injects exactly one channel')
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    receipt_path = out / 'startup_injection_receipt.json'
    if receipt_path.exists():
        raise FileExistsError('Refusing to overwrite a startup-injection receipt')
    receipt = dict(attempt_id=job['attempt_id'], pair_id=job['pair_id'],
                   protected_role='predictor', transport_role='env', applied=False,
                   argv_extra=copy.deepcopy(argv_extra), env_extra=copy.deepcopy(env_extra),
                   ownership='frozen guardian only; adapter never reaps or signals')
    save_json(receipt_path, receipt)

    def option(command, name):
        positions = [i for i, value in enumerate(command) if value == name]
        if len(positions) != 1 or positions[0] + 1 == len(command):
            raise ContractError('Unexpected frozen guardian command shape: ' + name)
        return command[positions[0] + 1]

    with _INJECTION_LOCK:
        original_subprocess = frozen_guardian.subprocess
        original_popen = original_subprocess.Popen

        def declared_popen(command, *args, **kwargs):
            # No post-Popen operations: once created, the handle must return
            # immediately to the guardian's ownership registration.
            if not isinstance(command, list):
                raise ContractError('Frozen guardian must supply its mutable argv list')
            if option(command, '--role') == 'env':
                if (option(command, '--attempt-id') != str(job['attempt_id']) or
                        option(command, '--pair-id') != str(job['pair_id'])):
                    raise ContractError('Injection target belongs to a different declared job')
                if receipt['applied']:
                    raise ContractError('Predictor startup injection applied more than once')
                environment = kwargs.get('env')
                if not isinstance(environment, dict):
                    raise ContractError('Frozen guardian must pass an explicit environment')
                command.extend(argv_extra)  # Same list is later recorded by the guardian.
                environment.update(env_extra)
                receipt.update(applied=True, actual_argv=copy.deepcopy(command),
                               actual_injected_environment=copy.deepcopy(env_extra),
                               actual_environment_keys=sorted(environment))
                save_json(receipt_path, receipt)  # Persist BEFORE creating any target process.
            return original_popen(command, *args, **kwargs)

        # Replace only this module's subprocess reference, not Python's shared
        # subprocess module. No guardian source or wait4 behavior is modified.
        frozen_guardian.subprocess = SimpleNamespace(Popen=declared_popen,
                                                     STDOUT=original_subprocess.STDOUT)
        try:
            result = frozen_guardian.run_pair(job, out, entry, deadline, cumulative)
        finally:
            frozen_guardian.subprocess = original_subprocess
        receipt['final_owned_processes'] = [
            {key: row.get(key) for key in ('role', 'pid', 'start_ticks', 'pgid', 'reaped', 'returncode')}
            for row in result['processes'] if row.get('created')]
        receipt['final_accounting_complete'] = result['accounting_complete']
        receipt['guardian_result_passed'] = result['passed']
        save_json(receipt_path, receipt)
        return result
