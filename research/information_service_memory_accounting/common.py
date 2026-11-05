"""Small strict metadata utilities; scientific work is never run at import."""
import hashlib
import json
import math
from pathlib import Path
import sys

from research.information_service_shared.common import ContractError

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'evidence/stage2a5b_gq_memory_accounting'
PROTOCOL = BASE / 'protocol_preparation_20261027_v01'
PROTOCOL_SHA = '6881e6d43bf980f85bf8b4f17aec066934528aa220548d4bfdcf7fea74c4b047'
CONTRACT = 'STAGE2A5B-GQ-MEMORY-ACCOUNTING-v0.1-DRAFT'
ENTRY = ROOT / 'examples/validate_stage2a5b_gq_memory_accounting.py'
ORDER = ['G0', 'G1', 'OLD_a', 'OLD_a_AUDIT', 'NEW_a', 'NEW_a_AUDIT',
         'NEW_b', 'NEW_b_AUDIT', 'OLD_b', 'OLD_b_AUDIT', 'Z']
PREDICTIONS = ['OLD_a', 'NEW_a', 'NEW_b', 'OLD_b']


class MemoryAccountingError(ContractError):
    def __init__(self, code, message='', **details):
        self.code = code
        self.details = details
        super().__init__(code + (': ' + message if message else ''))


def require(condition, code, message='', **details):
    if not condition:
        raise MemoryAccountingError(code, message, **details)


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'DUPLICATE_JSON_KEY', key)
        result[key] = value
    return result


def read_json(path):
    def reject(value):
        raise MemoryAccountingError('NONFINITE_JSON_NUMBER', value)
    def number(value):
        value = float(value)
        require(math.isfinite(value), 'NONFINITE_JSON_NUMBER')
        return value
    return json.loads(Path(path).read_bytes(), object_pairs_hook=_pairs,
                      parse_constant=reject, parse_float=number)


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.pending')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temp.replace(path)


def file_pin(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path and path.is_file() and not path.is_symlink(),
            'CANONICAL_FILE_REQUIRED', str(path))
    return dict(path=str(path), sha256=sha_file(path), size_bytes=path.stat().st_size)


def check_pin(pin):
    observed = file_pin(pin['path'])
    require(observed['sha256'] == pin['sha256'], 'PIN_SHA_MISMATCH', pin['path'])
    size = pin.get('size_bytes', pin.get('size'))
    require(size is None or observed['size_bytes'] == size, 'PIN_SIZE_MISMATCH', pin['path'])
    return Path(pin['path'])


def ordered_total(values):
    total = 0.0
    for value in values:
        require(type(value) in (int, float) and math.isfinite(value) and value >= 0, 'INVALID_CPU')
        total += value
    require(math.isfinite(total), 'INVALID_CPU_TOTAL')
    return total


class NoWLS:
    """Call-entry barrier, allowing G0 motion but no estimator/solver body."""
    def __init__(self):
        self.blocked_calls = []
        self.previous = None
        self.installed = False
        self.restored = False

    def _profile(self, frame, event, arg):
        if event != 'call' or frame.f_code.co_name == '<module>':
            return
        module, name = frame.f_globals.get('__name__', ''), frame.f_code.co_name
        blocked = module == 'research.cooperative_sensing.estimator' or module.startswith('research.cooperative_sensing.estimator.')
        blocked |= module.startswith('scipy.optimize') and name in ('least_squares', 'least_squares_inner', 'leastsq')
        if blocked:
            self.blocked_calls.append(dict(module=module, function=name, body_entered=False))
            raise MemoryAccountingError('WLS_ENTRY_FORBIDDEN', module + '.' + name)

    def __enter__(self):
        self.previous = sys.getprofile()
        require(self.previous is None, 'FOREIGN_PROFILE_HOOK')
        sys.setprofile(self._profile)
        self.installed = True
        return self

    def __exit__(self, *args):
        sys.setprofile(self.previous)
        self.restored = True

    def snapshot(self):
        return dict(installed=self.installed, restored=self.restored,
                    blocked_calls=list(self.blocked_calls), estimator_bodies_entered=0,
                    native_WLS_bodies_entered=0, scope='pre-body entry barrier; any blocked attempt fails')
