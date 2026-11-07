"""Identity and evidence helpers, with no estimator or truth dependency."""
import hashlib
import json
import os
from pathlib import Path

CONTRACT_ID = "STAGE2A5B-A-MINIMAL-v0.2"
QUALITY_ID = "local_wls_radius_proxy_v1"
DT = 0.05
DELTA = 0.06
P_REF = 0.95
DOMAIN = [[0.0, 0.0], [20.0, 20.0]]


class ContractError(ValueError):
    """Malformed or conflicting input, never an ordinary unavailable sensor."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                    separators=(",", ":")).encode()).hexdigest()


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".pending")
    with temp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)
