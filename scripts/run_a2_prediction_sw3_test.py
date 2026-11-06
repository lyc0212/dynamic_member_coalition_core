"""Trusted coordinator. TEST-0 uses artificial fixtures only."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from uuid import uuid4

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from research.non_oracle.sw3_f1_prediction import predict_method
from research.non_oracle.sw3_c1_sealing import public_handoff
from scripts import sw3_test_appcontainer as container
from scripts import run_a2_prediction_sw3_dev as dev

HEAD = "73de7ddffd742183ba74e5be4c192b9b5a660b7c"
REPORT = REPO / "reports/a2_prediction_sw3_test_003"
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
    result = json.loads(json.dumps(value, default=dev.encode_special, allow_nan=False))
    costs = [result["end_to_end"], result["selection"]["validation_timing"],
             result["selection"]["screening_timing"], result["prediction"]["cost"]]
    costs.extend(row["cost"] for row in result["prediction"]["results"])
    for cost in costs:
        for key in ("cpu", "wall"):
            if type(cost[key]) is not float:
                raise ValueError("Invalid registered timing type")
            cost[key] = None
    return result


def difference(a, b, path=""):
    if type(a) is type(b):
        if isinstance(a, dict) and a.keys() == b.keys():
            for k in sorted(a):
                result = difference(a[k], b[k], f"{path}/{k}")
                if result:
                    return result
            return None
        if isinstance(a, list) and len(a) == len(b):
            for i, (left, right) in enumerate(zip(a, b)):
                result = difference(left, right, f"{path}/{i}")
                if result:
                    return result
            return None
        if type(a) is float and a.hex() == b.hex():
            return None
        if type(a) not in (dict, list, float) and a == b:
            return None
    return dict(path=path or "/", reference=a, restricted=b)


def minimal_environment(root):
    windows = os.environ["SystemRoot"]
    return dict(SystemRoot=windows, WINDIR=windows, PATH=str(root / "native") + ";" + windows + r"\System32")


def worker_run(sid, root, env):
    return container.run(sid, root / "python.exe", ["-I", "-B", "-S", "-c",
        "import runpy,sys;sys.path.append('Lib/site-packages');runpy.run_path('worker.py',run_name='__main__')"],
        root, env)


def launch_record(root, sid, sid_text, name, env):
    try:
        result = worker_run(sid, root, env)
    except OSError as error:
        dev.save(REPORT / f"{name}_PROCESS.json", dict(sid=sid_text, created=False,
                 environment_names=sorted(env), winerror=error.winerror, error=str(error)))
        return None
    dev.save(REPORT / f"{name}_PROCESS.json", dict(sid=sid_text, created=True,
             environment_names=sorted(env), **result))
    if (root / "output/error.txt").exists():
        shutil.copyfile(root / "output/error.txt", REPORT / f"{name}_ERROR.txt")
    return result


def startup(root, sid, sid_text):
    env = minimal_environment(root)
    local = Path(os.environ["LOCALAPPDATA"])
    if not local.is_absolute() or not local.is_dir():
        raise ValueError("LOCALAPPDATA is not a verified absolute directory")
    enhanced = dict(env, LOCALAPPDATA=str(local))
    dev.save(REPORT / "E0_ENVIRONMENT.json", dict(A=sorted(env), B=sorted(enhanced),
             LOCALAPPDATA="<verified local profile directory>", delta=["LOCALAPPDATA"],
             sid=sid_text, cwd=str(root), python=str(root / "python.exe")))
    for name, config, phase in (("E0_A", env, "startup"), ("E0_B", enhanced, "startup"),
                                ("E1_DEPENDENCIES", enhanced, "dependencies")):
        for file in ("receipt.json", "error.txt"):
            (root / "output" / file).unlink(missing_ok=True)
        (root / "input/job.json").write_text(json.dumps(dict(phase=phase)), encoding="utf-8")
        result = launch_record(root, sid, sid_text, name, config)
        receipt = root / "output/receipt.json"
        if receipt.is_file():
            dev.save(REPORT / f"{name}_RECEIPT.json", dev.read(receipt))
        if name != "E0_A" and (result is None or result["exit_code"] != 0 or not receipt.is_file()):
            raise RuntimeError(f"{name} did not complete")
    return enhanced


def probe_run(root, sid, sid_text, name, inputs, probes, env, *, allow=False):
    files = {key: root / path for key, (path, _) in probes.items()}
    before = {key: dev.sha(path) for key, path in files.items()}
    job = dict(inputs=inputs, probes=probes)
    dev.save(REPORT / f"{name}_REQUEST.json", dict(sid=sid_text, cwd=str(root),
        probes={key: dict(path=str(path), resolved=str(path.resolve()), mode=probes[key][1],
                         sha256=before[key]) for key,path in files.items()},
        public_inputs={key: public_handoff(view)["public_sha256"] for key,view in inputs.items()}))
    for file in ("receipt.json", "error.txt"):
        (root / "output" / file).unlink(missing_ok=True)
    (root / "input/job.json").write_text(json.dumps(job), encoding="utf-8")
    result = launch_record(root, sid, sid_text, name, env)
    if result is None or result["exit_code"] != 0:
        raise RuntimeError(f"{name} AppContainer worker failed")
    receipt = dev.read(root / "output/receipt.json")
    after = {key: dev.sha(path) for key, path in files.items()}
    dev.save(REPORT / f"{name}_ACCESS.json", dict(sid=sid_text, hashes_after=after, **receipt))
    if before != after or set(receipt["probes"]) != set(probes):
        raise RuntimeError(f"{name} probe evidence changed")
    for key, r in receipt["probes"].items():
        if r["mode"] == "FILE_WRITE_DATA":
            valid = (r["access_mask"], r["share_mode"], r["disposition"]) == (2, 7, 3)
            valid &= (r["allowed"] and r["handle_closed"]) if allow else (
                not r["allowed"] and r["winerror"] == 5)
        else:
            valid = not r["allowed"] and r["exception"] == "PermissionError" and r["errno"] == 13
        if not valid or [r["path"], r["mode"]] != probes[key]:
            raise RuntimeError(f"{name} access result failed the OS contract for {key}")
    return receipt


def junction(root):
    link = root / "input/private_link"
    target = root / "private"
    if os.path.lexists(link):
        raise ValueError("Unexpected existing junction path")
    command = ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)]
    run = subprocess.run(command, capture_output=True)
    dev.save(REPORT / "R1_B_JUNCTION.json", dict(command=command, exit_code=run.returncode,
        stdout=run.stdout.decode(errors="replace"), stderr=run.stderr.decode(errors="replace")))
    if run.returncode:
        return None
    if link.lstat().st_reparse_tag != stat.IO_REPARSE_TAG_MOUNT_POINT or link.resolve() != target.resolve():
        raise ValueError("Unexpected junction identity")
    if dev.sha(link / "world.json") != dev.sha(target / "world.json"):
        raise ValueError("Unexpected junction fixture content")
    return link


def gate_zero(root, sid, sid_text, view, reference, modules):
    stage(root, modules)
    for name in ("input", "output", "private", "sealed"):
        (root / name).mkdir()
    for name in ("world", "execution_state", "trajectory", "future_wls", "label", "draw_manifest", "association"):
        (root / "private" / f"{name}.json").write_text('{"artificial":true}', encoding="utf-8")
    probes = {file.stem: [str(file), "rb"] for file in (root / "private").glob("*.json")}
    probes.update(relative=["private/world.json", "rb"],
                  sampler=[str(REPO / "research/non_oracle/sw3_c1_private_worlds.py"), "rb"],
                  admissibility=[str(REPO / "research/non_oracle/sw3_physical_admissibility_v1.py"), "rb"],
                  repository=[str(REPO / "docs/A2_PRED_SW3_EVALUATION_SPEC_V1.md"), "rb"])
    acl(root, sid_text, "(RX)")
    for child in root.iterdir():
        if child.name in {"private", "sealed"}:
            continue
        acl(child, sid_text, "(OI)(CI)(M)" if child.name == "output" else
            ("(OI)(CI)(RX)" if child.is_dir() else "(RX)"))
    manifest = {x.relative_to(root).as_posix(): dev.sha(x) for x in root.rglob("*")
                if x.is_file() and x.relative_to(root).parts[0] not in {"input", "output", "sealed", "private"}}
    dev.save(REPORT / "PREDICTOR_DEPENDENCIES.json", manifest)
    dev.save(REPORT / "TEST_0_LAUNCH.json", dict(appcontainer_sid=sid_text, capabilities=[],
             python=sys.version, launcher_sha256=dev.sha(REPO / "scripts/sw3_test_appcontainer.py"),
             mount_policy="Root RX, staged runtime/science/input RX, output M, private and sealed no package grant"))
    link = junction(root)
    env = startup(root, sid, sid_text)
    receipt = probe_run(root, sid, sid_text, "R1_A", {"fixture":view}, probes, env)
    if (Path(receipt["executable"]).resolve() != root / "python.exe"
            or any(not (root / p).resolve().is_relative_to(root) for p in receipt["sys_path"])
            or any(k.startswith("PYTHON") for k in receipt["environment"])):
        raise ValueError("Unexpected worker dependency search path")
    seals = {}
    for method, expected in reference.items():
        source = root / "output" / f"fixture_{method}.json"
        actual = dev.read(source)
        mismatch = difference(normalize(expected), normalize(actual))
        if mismatch:
            dev.save(REPORT / "R1_A_SCIENCE_DIFFERENCE.json", dict(method=method, **mismatch))
            raise RuntimeError(f"Scientific fixture mismatch: {method}")
        seals[source.name] = dev.sha(source)
    dev.save(REPORT / "R1_A_SCIENCE_PASS.json", dict(sid=sid_text, hashes=seals))
    if link is not None:
        probe_run(root, sid, sid_text, "R1_B", {}, {"reparse":["input/private_link/world.json","rb"]}, env)
    probe_run(root, sid, sid_text, "R1_C_POSITIVE", {}, {
        name:[str(root / "output" / name), "FILE_WRITE_DATA"] for name in seals}, env, allow=True)
    identities = {}
    for name,digest in seals.items():
        source = root / "output" / name
        destination = root / "sealed" / name
        identity = source.stat()
        shutil.copyfile(source, destination)  # New object inherits the sealed directory ACL.
        if dev.sha(destination) != digest or dev.sha(source) != digest or not source.stat().st_ino == identity.st_ino:
            raise ValueError("Prediction content or source identity changed during sealing")
        identities[name] = dict(source=str(source), source_file_id=identity.st_ino,
            sealed=str(destination), sealed_file_id=destination.stat().st_ino, sha256=digest)
        source.unlink()
        shutil.copyfile(destination, REPORT / name)
    dev.save(REPORT / "R1_C_SEAL.json", dict(sid=sid_text, objects=identities))
    probe_run(root, sid, sid_text, "R1_C_NEGATIVE", {}, {
        name:[str(root / "sealed" / name), "FILE_WRITE_DATA"] for name in seals}, env)
    if any(dev.sha(root / "sealed" / name) != h for name,h in seals.items()):
        raise ValueError("Sealed products changed")
    if link is None:
        raise RuntimeError("R1-B junction setup blocked; base and seal evidence retained")


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
        if os.path.lexists(link):
            if (link.lstat().st_reparse_tag != stat.IO_REPARSE_TAG_MOUNT_POINT
                    or link.resolve() != (root / "private").resolve()):
                raise ValueError("Unsafe junction cleanup")
            link.rmdir()
        shutil.rmtree(root)


if __name__ == "__main__":
    main()
