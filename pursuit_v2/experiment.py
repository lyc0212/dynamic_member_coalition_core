"""Immutable input and implementation fingerprints for resumable experiments."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform

import numpy as np


MANIFEST_SCHEMA = 2


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def method_sha256(root: str | Path, runner: str | Path) -> str:
    """Hash the experiment entry point and every implementation module."""
    root = Path(root).resolve()
    paths = [*sorted((root / "pursuit_v2").glob("*.py")), Path(runner)]
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        name = path.relative_to(root).as_posix()
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def experiment_manifest(root: str | Path, runner: str | Path,
                        source_paths: dict[str, Path], **design) -> dict:
    root = Path(root).resolve()
    return {
        "schema_version": MANIFEST_SCHEMA,
        "method_sha256": method_sha256(root, runner),
        "source_sha256": {key: file_sha256(path)
                          for key, path in sorted(source_paths.items())},
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        **design,
    }


def ensure_manifest(output: str | Path, expected: dict) -> None:
    """Reject stale or unverifiable cached runs without changing their files."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "manifest.json"
    if path.exists():
        current = json.loads(path.read_text(encoding="utf-8"))
        if current != expected:
            changed = sorted(key for key in set(current) | set(expected)
                             if current.get(key) != expected.get(key))
            raise ValueError("Experiment manifest differs in " + ", ".join(changed) +
                             "; use a new output directory. Existing results were not changed.")
        return
    if any(output.iterdir()):
        raise ValueError("Output has data but no versioned manifest; use a new directory")
    path.write_text(json.dumps(expected, ensure_ascii=False, indent=2),
                    encoding="utf-8")
