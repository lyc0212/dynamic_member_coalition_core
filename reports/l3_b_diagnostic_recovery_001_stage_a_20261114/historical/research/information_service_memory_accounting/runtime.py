"""Exact memory-accounting role closure; no directory/data permission fallback."""
import os
from pathlib import Path

from research.information_service_shared import runtime as old

PREFIX = 'research.information_service_memory_accounting'
NEUTRAL = {PREFIX, PREFIX + '.runtime', PREFIX + '.common'}
PRODUCER = NEUTRAL | {PREFIX + '.worker', PREFIX + '.meter', PREFIX + '.wiring'}
SAVED = NEUTRAL | {PREFIX + '.worker', PREFIX + '.auditor', PREFIX + '.claims',
    'research.information_service_future_profile',
    'research.information_service_future_profile.auditor',
    'research.information_service_future_profile.profiler'}
EXTRA_MODULES = {
    'sense': frozenset({PREFIX, PREFIX + '.runtime'}),
    'S': frozenset(PRODUCER),
    'audit': frozenset(SAVED),
    'admission': frozenset(PRODUCER | SAVED | {PREFIX + '.gates'}),
}
REMOVED_MODULES = {'S': frozenset({'research.cooperative_sensing.estimator'})}
validate_worker_startup = old.validate_worker_startup
ResponseContextRegistry = old.ResponseContextRegistry
transport_digest = old.transport_digest


def role_modules(role):
    if role not in EXTRA_MODULES:
        raise old.AccessDenied('Undeclared memory-accounting role')
    return frozenset((set(old.ROLE_MODULES[role]) | set(EXTRA_MODULES[role])) -
                     set(REMOVED_MODULES.get(role, ())))


def install_role_guard(role, out, fd=None, *, read_files=()):
    if role not in EXTRA_MODULES:
        raise old.AccessDenied('Undeclared memory-accounting role')
    root = Path(__file__).resolve().parents[2]
    guard = old.RoleAccessGuard(role, root, out, fd, read_files=read_files)
    guard.allowed_modules.update(EXTRA_MODULES[role])
    for name in REMOVED_MODULES.get(role, ()):
        guard.allowed_modules.discard(name)
        base = root.joinpath(*name.split('.'))
        guard.public_files.difference_update((base.with_suffix('.py'), base / '__init__.py'))
    for name in EXTRA_MODULES[role]:
        base = root.joinpath(*name.split('.'))
        guard.public_files.update((base.with_suffix('.py'), base / '__init__.py'))
    guard.public_files.add(root / 'examples/validate_stage2a5b_gq_memory_accounting.py')
    guard.runtime_files.add(Path('/proc') / str(os.getpid()) / 'stat')
    for path in guard.public_files:
        guard.public_dirs.update(parent for parent in path.parents
                                 if parent == root or root in parent.parents)
    guard.install()
    guard.check_loaded_modules()
    return guard
