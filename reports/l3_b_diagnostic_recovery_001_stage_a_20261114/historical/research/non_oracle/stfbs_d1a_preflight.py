"""Fixed H1 source identity and independent worktree checks; never runs MODEL."""
import hashlib,subprocess
from pathlib import Path

REQUIRED_SOURCES = ('pursuit_v2/__init__.py', 'pursuit_v2/config.py', 'pursuit_v2/environment.py', 'pursuit_v2/motion.py', 'pursuit_v2/observation_geometry.py', 'pursuit_v2/physics.py', 'pursuit_v2/scenario.py', 'pursuit_v2/service.py', 'pursuit_v2/service_environment.py', 'pursuit_v2/types.py', 'research/__init__.py', 'research/cooperative_sensing/__init__.py', 'research/cooperative_sensing/estimator.py', 'research/information_service/__init__.py', 'research/information_service/common.py', 'research/information_service/public_quality.py', 'research/information_service_bridge/__init__.py', 'research/information_service_bridge/common.py', 'research/information_service_bridge/public_stream.py', 'research/information_service_online/__init__.py', 'research/information_service_online/adapter.py', 'research/information_service_online/common.py', 'research/information_service_online/evaluator.py', 'research/information_service_online/measurements.py', 'research/information_service_online/public.py', 'research/non_oracle/__init__.py', 'research/non_oracle/belief.py', 'research/non_oracle/policy.py', 'research/non_oracle/stfbs_d1a_audit.py', 'research/non_oracle/stfbs_d1a_audit_input.py', 'research/non_oracle/stfbs_d1a_audit_registration.py', 'research/non_oracle/stfbs_d1a_history.py', 'research/non_oracle/stfbs_d1a_history_audit.py', 'research/non_oracle/stfbs_d1a_model.py', 'research/non_oracle/stfbs_d1a_plan.py', 'research/non_oracle/stfbs_d1a_preflight.py', 'research/non_oracle/stfbs_d1a_replay.py', 'research/non_oracle/stfbs_d1a_state.py', 'research/non_oracle/stfbs_d1a_verify.py', 'research/non_oracle/stfbs_d1a_watchdog_support.py', 'research/quality_allocation/__init__.py', 'research/quality_allocation/certified_solver.py', 'scripts/gq_windows/a0_plans.py', 'scripts/stfbs_d1a_run.py', 'scripts/stfbs_d1a_watchdog.py')
SOURCE_ROOTS=('research','pursuit_v2','scripts')
EXECUTABLE_SUFFIXES={'.py','.pyw','.pyc','.pyd','.dll','.exe','.so','.pth','.zip'}

def git(root,*args):
    return subprocess.check_output(['git',*args],cwd=root)

def check_worktree(root):
    required=set(REQUIRED_SOURCES)
    for staged in (False,True):
        args=['diff','--name-only','-z']
        if staged:args.append('--cached')
        changed=git(root,*args).decode().split('\0')
        for name in changed:
            p=Path(name)
            if name in required or (p.parts and (p.parts[0] in SOURCE_ROOTS or len(p.parts)==1) and p.suffix.lower() in EXECUTABLE_SUFFIXES):
                raise ValueError('Uncommitted scientific source: '+name)
    # --others without exclude-standard also catches ignored importable source.
    for name in git(root,'ls-files','--others','-z').decode().split('\0'):
        if not name:continue
        p=Path(name)
        if (p.parts and p.parts[0] in SOURCE_ROOTS or len(p.parts)==1) and p.suffix.lower() in EXECUTABLE_SUFFIXES:
            raise ValueError('Untracked importable source: '+name)
    # Root-level import shadowing and startup hooks are not experiment output.
    tracked=set(git(root,'ls-files','-z').decode().split('\0'))
    for p in Path(root).iterdir():
        if p.is_file() and p.suffix.lower() in EXECUTABLE_SUFFIXES and p.name not in tracked:
            raise ValueError('Untracked import root source: '+p.name)

def check_source_lock(root,expected,*,worktree_check=check_worktree):
    root=Path(root).resolve()
    if not isinstance(expected,dict) or not set(REQUIRED_SOURCES)<=set(expected):
        raise ValueError('Missing required scientific dependency pins')
    worktree_check(root)
    for name,wanted in expected.items():
        p=(root/name).resolve()
        if not p.is_relative_to(root) or not p.is_file():raise ValueError('Required scientific source missing: '+name)
        if hashlib.sha256(p.read_bytes()).hexdigest()!=wanted:raise ValueError('Scientific SHA256 mismatch: '+name)
    return {'status':'PASS','checked':len(expected)}
