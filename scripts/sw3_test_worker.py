"""AppContainer-side public prediction and artificial access probes."""
from dataclasses import asdict, is_dataclass
import json
import os
from pathlib import Path
import sys
import traceback


def encode(value):
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "tolist"):
        return value.tolist()
    raise TypeError(type(value))


def access(path, mode):
    try:
        with open(path, mode):
            pass
    except OSError as error:
        return dict(allowed=False, errno=error.errno, winerror=error.winerror
                    if hasattr(error, "winerror") else None)
    return dict(allowed=True)


def main():
    root = Path.cwd()
    output = root / "output"
    try:
        with os.add_dll_directory(str(root / "native")):
            sys.path.insert(0, str(root / "science"))
            from research.non_oracle.sw3_f1_prediction import predict_method

            job = json.loads((root / "input" / "job.json").read_bytes())
            for key, view in job["inputs"].items():
                if not key.isascii() or not key.isalnum():
                    raise ValueError("Invalid public job key")
                for method in ("M0", "M1", "M2"):
                    product = predict_method(view, method)
                    (output / f"{key}_{method}.json").write_text(
                        json.dumps(product, default=encode, allow_nan=False), encoding="utf-8")
            probes = {key: access(spec[0], spec[1]) for key, spec in job["probes"].items()}
            (output / "receipt.json").write_text(json.dumps(dict(probes=probes,
                sys_path=sys.path, environment=sorted(os.environ), executable=sys.executable)),
                encoding="utf-8")
    except Exception:
        (output / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
