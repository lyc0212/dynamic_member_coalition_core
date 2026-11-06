"""AppContainer-side public prediction and artificial access probes."""
from dataclasses import asdict, is_dataclass
import json
import os
import ctypes
from ctypes import wintypes
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
    if mode == "FILE_WRITE_DATA":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                           ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        handle = create(path, 2, 7, None, 3, 0, None)
        evidence = dict(access_mask=2, share_mode=7, disposition=3)
        if handle == ctypes.c_void_p(-1).value:
            return dict(allowed=False, winerror=ctypes.get_last_error(), **evidence)
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        return dict(allowed=True, handle_closed=bool(kernel.CloseHandle(handle)), **evidence)
    try:
        with open(path, mode):
            pass
    except OSError as error:
        return dict(allowed=False, exception=type(error).__name__, errno=error.errno, winerror=error.winerror
                    if hasattr(error, "winerror") else None)
    return dict(allowed=True)


def main():
    root = Path.cwd()
    output = root / "output"
    try:
        job = json.loads((root / "input" / "job.json").read_bytes())
        phase = job.get("phase", "prediction")
        if phase == "startup":
            (output / "receipt.json").write_text(json.dumps(dict(phase=phase,
                python_initialized=True, worker_executed=True, pid=os.getpid())), encoding="utf-8")
            return
        with os.add_dll_directory(str(root / "native")):
            sys.path.insert(0, str(root / "science"))
            from research.non_oracle.sw3_f1_prediction import predict_method

            if phase == "dependencies":
                import numpy
                import scipy
                (output / "receipt.json").write_text(json.dumps(dict(phase=phase,
                    numpy=numpy.__version__, scipy=scipy.__version__, worker_executed=True)),
                    encoding="utf-8")
                return
            for key, view in job["inputs"].items():
                if not key.isascii() or not key.isalnum():
                    raise ValueError("Invalid public job key")
                for method in ("M0", "M1", "M2"):
                    product = predict_method(view, method)
                    (output / f"{key}_{method}.json").write_text(
                        json.dumps(product, default=encode, allow_nan=False), encoding="utf-8")
            probes = {key: dict(path=spec[0], mode=spec[1], **access(*spec))
                      for key, spec in job["probes"].items()}
            (output / "receipt.json").write_text(json.dumps(dict(probes=probes,
                sys_path=sys.path, environment=sorted(os.environ), executable=sys.executable)),
                encoding="utf-8")
    except Exception:
        (output / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
