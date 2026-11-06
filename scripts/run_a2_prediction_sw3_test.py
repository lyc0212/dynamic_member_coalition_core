"""Trusted coordinator. TEST-0 uses artificial fixtures only."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from research.non_oracle.sw3_f1_prediction import predict_method
from research.non_oracle.sw3_c1_sealing import public_handoff
from scripts import sw3_test_appcontainer as container
from scripts import run_a2_prediction_sw3_dev as dev

HEAD = "6afa12a3cd416438291a1f05631af9b39ca25ec7"
REPORT = REPO / "reports/a2_prediction_sw3_test_001"
WORKER = "scripts/sw3_test_worker.py"


def fixture():
    source = "reports/a2_prediction_sw3_dev_002/family_11/public/D60.json"
    view = deepcopy(dev.read(REPO / source)["D60"])
    # Use a fabricated public center outside the frozen family grid.
    view["targets"][1]["coarse_position"] = [9.21, 10.41]
    view["beliefs"]["1"]["position_estimate"] = [9.21, 10.41]
    return public_handoff(view)["D60"]


def acl(path, sid, rights):
    cmd = [str(Path(os.environ["SystemRoot"]) / "System32/icacls.exe"),
           str(path), "/grant", f"*{sid}:{rights}"]
    subprocess.run(cmd, check=True, capture_output=True)


def stage(root, modules):
    prefix = Path(sys.base_prefix)
    for name in ("python.exe", "python313.dll", "python3.dll", "vcruntime140.dll",
                 "vcruntime140_1.dll", "msvcp140.dll", "zlib.dll"):
        shutil.copyfile(prefix / name, root / name)
    ignore = shutil.ignore_patterns("__pycache__", "tests", "*.pdb", "*.pyc")
    shutil.copytree(prefix / "Lib", root / "Lib",
                    ignore=lambda p, names: set(ignore(p, names)) | {"site-packages", "test", "ensurepip", "tkinter"})
    shutil.copytree(prefix / "DLLs", root / "DLLs", ignore=ignore)
    for package in ("numpy", "scipy"):
        shutil.copytree(prefix / "Lib/site-packages" / package,
                        root / "Lib/site-packages" / package, ignore=ignore)
    native = root / "native"
    native.mkdir()
    for file in (prefix / "Library/bin").glob("*.dll"):
        if file.name.startswith(("mkl_", "libiomp", "libifcore", "libifport", "libmmd", "svml", "tbb")):
            shutil.copyfile(file, native / file.name)
    for source in modules:
        destination = root / "science" / source.relative_to(REPO)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    shutil.copyfile(REPO / WORKER, root / "worker.py")


def normalize(value):
    value = json.loads(json.dumps(value, default=dev.encode_special))
    def omit_timings(obj):
        if isinstance(obj, dict):
            return {k: omit_timings(v) for k, v in obj.items() if k not in {"wall", "cpu"}}
        if isinstance(obj, list):
            return [omit_timings(v) for v in obj]
        return obj
    return omit_timings(value)


def worker_run(sid, root):
    windows = os.environ["SystemRoot"]
    env = dict(SystemRoot=windows, WINDIR=windows, PATH=str(root / "native") + ";" + windows + r"\System32")
    return container.run(sid, root / "python.exe", ["-I", "-B", "-S", "-c",
        "import runpy,sys;sys.path.append('Lib/site-packages');runpy.run_path('worker.py',run_name='__main__')"],
        root, env)


def gate_zero(root, sid, sid_text, view, reference, modules):
    stage(root, modules)
    for name in ("input", "output", "private", "sealed"):
        (root / name).mkdir()
    for name in ("world", "execution_state", "trajectory", "future_wls", "label", "draw_manifest", "association"):
        (root / "private" / f"{name}.json").write_text('{"artificial":true}', encoding="utf-8")
    probes = {file.stem: [str(file), "rb"] for file in (root / "private").glob("*.json")}
    link = root / "input" / "private_link"
    # A directory junction exercises an NTFS reparse path without requiring symlink privilege.
    subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(root / "private")],
                   check=True, capture_output=True)
    probes.update(relative=["private/world.json", "rb"],
                  reparse=["input/private_link/world.json", "rb"],
                  sampler=[str(REPO / "research/non_oracle/sw3_c1_private_worlds.py"), "rb"],
                  admissibility=[str(REPO / "research/non_oracle/sw3_physical_admissibility_v1.py"), "rb"],
                  repository=[str(REPO / "docs/A2_PRED_SW3_EVALUATION_SPEC_V1.md"), "rb"])
    (root / "sealed" / "fixture.json").write_text('{"sealed_fixture":true}', encoding="utf-8")
    probes["sealed_write"] = [str(root / "sealed" / "fixture.json"), "r+b"]
    acl(root, sid_text, "(RX)")
    for child in root.iterdir():
        if child.name in {"private", "sealed"}:
            continue
        acl(child, sid_text, "(OI)(CI)(M)" if child.name == "output" else
            ("(OI)(CI)(RX)" if child.is_dir() else "(RX)"))
    (root / "input" / "job.json").write_text(json.dumps(dict(inputs={"fixture":view}, probes=probes)), encoding="utf-8")
    manifest = {x.relative_to(root).as_posix(): dev.sha(x) for x in root.rglob("*")
                if x.is_file() and x.relative_to(root).parts[0] not in {"input", "output", "sealed", "private"}}
    dev.save(REPORT / "PREDICTOR_DEPENDENCIES.json", manifest)
    dev.save(REPORT / "TEST_0_LAUNCH.json", dict(appcontainer_sid=sid_text, capabilities=[],
             python=sys.version, launcher_sha256=dev.sha(REPO / "scripts/sw3_test_appcontainer.py"),
             artificial_fixture_sha256=dev.sha(root / "input/job.json"),
             mount_policy="Root RX, staged runtime/science/input RX, output M, private and sealed no package grant"))
    result = worker_run(sid, root)
    dev.save(REPORT / "TEST_0_PROCESS.json", result)
    if (root / "output/error.txt").exists():
        shutil.copyfile(root / "output/error.txt", REPORT / "TEST_0_WORKER_ERROR.txt")
    if result["exit_code"] != 0:
        raise RuntimeError(f"AppContainer prediction worker exit {result['exit_code']:#x}")
    receipt = dev.read(root / "output/receipt.json")
    dev.save(REPORT / "TEST_0_ACCESS.json", receipt)
    if set(receipt["probes"]) != set(probes) or any(
            r["allowed"] or r["errno"] != 13 for r in receipt["probes"].values()):
        raise RuntimeError("A forbidden access was not denied by OS permission")
    for method, expected in reference.items():
        actual = dev.read(root / "output" / f"fixture_{method}.json")
        if normalize(actual) != normalize(expected):
            raise RuntimeError(f"Scientific fixture mismatch: {method}")


def main():
    if subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != HEAD:
        raise ValueError("Unexpected baseline HEAD")
    REPORT.mkdir(exist_ok=False)
    root = REPO / (".sw3_test_stage_" + uuid4().hex)
    root.mkdir()
    try:
        view = fixture()
        reference = {m: predict_method(view, m) for m in dev.METHODS}
        modules = sorted({Path(m.__file__).resolve() for k,m in sys.modules.copy().items()
                          if k.startswith(("research", "pursuit_v2")) and getattr(m,"__file__",None)
                          and Path(m.__file__).resolve().is_relative_to(REPO)
                          and not k.startswith(("research.non_oracle.sw3_c1_", "research.non_oracle.sw3_physical"))
                          and k != "research.non_oracle.environment"})
        with container.profile() as (sid, sid_text):
            gate_zero(root, sid, sid_text, view, reference, modules)
    except Exception as error:
        dev.save(REPORT / "TEST_0_FAILURE.json", dict(error=repr(error)))
        raise
    finally:
        if root.resolve().parent != REPO or not root.name.startswith(".sw3_test_stage_"):
            raise ValueError("Unsafe staging cleanup")
        link = root / "input/private_link"
        if link.exists():
            link.rmdir()
        shutil.rmtree(root)


if __name__ == "__main__":
    main()
