"""Neutral identities and file utilities; no scientific imports or execution."""
import hashlib
import json
import math
import os
from pathlib import Path
import struct

from research.information_service_online.common import (
    AccessDenied, ContractError, DT, absolute_O, digest, json_safe, safe_label,
)

STAGE_CONTRACT = 'STAGE2A5B-GQ-SHARED-FULL-v1.0'
SCIENTIFIC_CONTRACT = 'STAGE2A5B-GQ-ONLINE-v1.0'
# Transport continues to carry the unchanged scientific frame contract.
CONTRACT_ID = SCIENTIFIC_CONTRACT


def typed_encode(value):
    """Frozen tagged JSON encoding; distinguish integers, bools and signed zero."""
    kind = type(value)
    if value is None:
        return ['null']
    if kind is bool:
        return ['bool', value]
    if kind is int:
        return ['int', str(value)]
    if kind is float:
        if not math.isfinite(value):
            raise ContractError('Nonfinite binary64 value')
        return ['float', struct.pack('>d', value).hex()]
    if kind is str:
        return ['string', value]
    if kind is list:
        return ['array', [typed_encode(v) for v in value]]
    if kind is dict and all(type(k) is str for k in value):
        return ['object', [[k, typed_encode(value[k])] for k in sorted(value)]]
    raise ContractError('Not a typed JSON value: ' + kind.__name__)


def typed_digest(value):
    raw = json.dumps(typed_encode(value), ensure_ascii=False,
                     separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    # Scientific comparison has a separate lexical decoder. This loader is
    # restricted to externally pinned preparation/runtime bookkeeping files.
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.pending')
    with temp.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
