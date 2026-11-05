from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean_json(value.tolist())
    if isinstance(value, np.generic):
        return clean_json(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def dump_json(path, value):
    Path(path).write_text(json.dumps(clean_json(value), ensure_ascii=False, indent=2,
                                    allow_nan=False), encoding="utf-8")


def write_csv(path, rows):
    if not rows:
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(clean_json(v), ensure_ascii=False)
                             if isinstance(v, (list, tuple, dict)) else v for k, v in row.items()})

