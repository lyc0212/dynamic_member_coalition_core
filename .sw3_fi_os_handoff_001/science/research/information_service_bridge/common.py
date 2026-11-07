"""Public constants and serialization; no physical, generator or oracle imports."""
import hashlib
import json
import math
import os
from pathlib import Path

CONTRACT_ID = "STAGE2A5B-GQ-EXECUTION-BRIDGE-v1.1"
DT = 0.05
MAX_FRAME = 2 * 1024**2
IO_CHUNK = 64 * 1024
POLL = 0.05


class ContractError(ValueError):
    pass


class AccessDenied(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                    separators=(",", ":")).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".pending")
    with tmp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)


def canonical_actions(actions, robots):
    if not isinstance(actions, (tuple, list)) or len(actions) != robots:
        raise ContractError("One action per stable robot index required")
    result = []
    for a in actions:
        if hasattr(a, "to_dict"):
            a = a.to_dict()
        if not isinstance(a, dict) or set(a) != {"target", "role"}:
            raise ContractError("Exact Assignment fields required")
        t, role = a["target"], a["role"]
        if t is not None and (isinstance(t, bool) or not isinstance(t, int) or t < 0):
            raise ContractError("Target must be a nonnegative integer or null")
        if not isinstance(role, str) or (t is None and role != "none"):
            raise ContractError("Invalid role or IDLE")
        result.append({"target": t, "role": role})
    return result
