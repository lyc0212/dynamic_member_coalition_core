"""Public-only sensing process with access checks before Python file/import use.

The guard is for this controlled Python worker, not an OS sandbox against hostile
native extensions. The separately supervised process receives only public IPC.
Neither the physical environment nor its input files are imported here.
"""
from __future__ import annotations

import argparse
import copy
import importlib
import importlib.abc
import os
from pathlib import Path
import resource
import sys
import sysconfig
import traceback

from .common import CONTRACT_ID, AccessDenied, ContractError, digest, save_json


ENV_KEYS = frozenset(("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TZ",
                      "PYTHONUTF8", "PYTHONIOENCODING", "PYTHONDONTWRITEBYTECODE",
                      "PYTHONHASHSEED", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                      "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "TMPDIR", "TEMP", "TMP"))
THREAD_KEYS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")
PUBLIC_MODULES = frozenset((
    "research", "research.information_service_bridge",
    "research.information_service_bridge.common", "research.information_service_bridge.wire",
    "research.information_service_bridge.public_stream", "research.information_service_bridge.sensing_worker",
    "research.information_service", "research.information_service.common",
    "research.information_service.public_quality", "research.cooperative_sensing",
    "research.cooperative_sensing.estimator"))
IDENTITY_FIELDS = frozenset(("attempt_id", "pair_id", "sense_request_id", "target_id",
                            "stream_id", "global_tick", "payload_sha256"))
STREAM_FIELDS = frozenset(("stream_id", "target_id", "start_tick", "allowed_sensor_ids"))


def _inside(path, root):
    return path == root or root in path.parents


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ContractError(label + " has unexpected or missing fields")


def validate_startup(args, environ=None):
    """Pure startup validation, usable without creating a process or installing hooks."""
    if isinstance(args, (list, tuple)):
        class StrictParser(argparse.ArgumentParser):
            def error(self, message):
                raise AccessDenied("Startup argv rejected: " + message)
        parser = StrictParser(add_help=False, allow_abbrev=False)
        for option in ("role", "fd", "out", "attempt-id", "pair-id"):
            parser.add_argument("--" + option, required=True)
        values = vars(parser.parse_args(list(args)))
        try:
            values["fd"] = int(values["fd"])
        except (ValueError, TypeError) as error:
            raise AccessDenied("Invalid IPC descriptor") from error
    elif isinstance(args, argparse.Namespace):
        values = vars(args).copy()
    elif isinstance(args, dict):
        values = args.copy()
    else:
        raise AccessDenied("Invalid worker startup arguments")
    permitted = {"role", "fd", "out", "attempt_id", "pair_id", "command", "synthetic"}
    if set(values) - permitted:
        raise AccessDenied("Unknown worker argv fields: " + repr(sorted(set(values) - permitted)))
    if values.get("command", "worker") != "worker" or values.get("synthetic") is not None:
        raise AccessDenied("Sensing worker cannot use a private or synthetic dispatch")
    if values.get("role") != "sense":
        raise AccessDenied("Wrong worker role")
    fd = values.get("fd")
    if isinstance(fd, bool) or not isinstance(fd, int) or fd < 0:
        raise AccessDenied("Invalid IPC descriptor")
    for field in ("out", "attempt_id", "pair_id"):
        if not isinstance(values.get(field), str) or not values[field]:
            raise AccessDenied("Missing public startup identity: " + field)
    out = Path(values["out"])
    if not out.is_absolute():
        raise AccessDenied("Worker output path must be absolute")
    out = out.resolve()
    env = dict(os.environ if environ is None else environ)
    if set(env) - ENV_KEYS:
        raise AccessDenied("Unknown environment keys: " + repr(sorted(set(env) - ENV_KEYS)))
    required = {"TMPDIR", "TEMP", "TMP", "PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED",
                "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"}
    if required - set(env):
        raise AccessDenied("Missing frozen environment keys: " + repr(sorted(required - set(env))))
    if env["PYTHONDONTWRITEBYTECODE"] != "1" or env["PYTHONHASHSEED"] != "0":
        raise AccessDenied("Python bytecode/hash environment differs from the contract")
    if any(env.get(key, "1") != "1" for key in THREAD_KEYS):
        raise AccessDenied("Scientific thread counts must equal one")
    for key in ("TMPDIR", "TEMP", "TMP"):
        if Path(env[key]).resolve() != out / "tmp":
            raise AccessDenied(key + " must be the private worker output/tmp directory")
    values["out"] = str(out)
    return argparse.Namespace(**values)


class _PublicImports(importlib.abc.MetaPathFinder):
    def __init__(self, guard):
        self.guard = guard

    def find_spec(self, fullname, path=None, target=None):
        if self.guard.enabled:
            self.guard.check_import(fullname)
        return None


class PublicAccessGuard:
    """Explicit realpath whitelist with pre-open and pre-import enforcement.

    Directory metadata needed by Python's importer can be listed; file contents
    remain separately restricted. Symlink aliases are resolved before admission.
    Hooks can be disabled for pure unit tests; production keeps them active.
    """

    def __init__(self, project_root, output, ipc_fd=None):
        self.root = Path(project_root).resolve()
        self.output = Path(output).resolve()
        self.enabled = False
        self._checking = False
        self.events = []
        self.allowed_fds = {0, 1, 2} | ({ipc_fd} if ipc_fd is not None else set())
        self.public_files = set()
        for module in PUBLIC_MODULES:
            base = self.root.joinpath(*module.split("."))
            self.public_files.add(base.with_suffix(".py"))
            self.public_files.add(base / "__init__.py")
        self.public_files.add(self.root / "examples/validate_stage2a5b_gq_bridge.py")
        self.public_dirs = {self.root}
        for path in self.public_files:
            self.public_dirs.update(parent for parent in path.parents if _inside(parent, self.root))
        paths = sysconfig.get_paths()
        self.stdlib_roots = {Path(paths[key]).resolve() for key in ("stdlib", "platstdlib")}
        self.site_roots = {Path(paths[key]).resolve() for key in ("purelib", "platlib")}
        # No project directory or arbitrary site-package is an allowed code root.
        self.runtime_roots = set()
        package_names = ("numpy", "scipy", "numpy.libs", "scipy.libs", "mkl", "charset_normalizer", "packaging",
                         "Cython", "cython.py", "typing_extensions.py", "threadpoolctl.py")
        for site in self.site_roots:
            self.runtime_roots.update(site / name for name in package_names)
        self.runtime_files = {Path("/dev/null"), Path("/dev/urandom"),
                              Path("/proc/cpuinfo"), Path("/proc/meminfo")}
        self.finder = _PublicImports(self)

    def _deny(self, operation, target):
        self.events.append(dict(operation=operation, target=str(target), allowed=False))
        raise AccessDenied(f"Sensing access denied before {operation}: {target}")

    def check_import(self, name):
        if name == "pursuit_v2" or name.startswith("pursuit_v2."):
            self._deny("import", name)
        if (name == "research" or name.startswith("research.")) and name not in PUBLIC_MODULES:
            self._deny("import", name)

    def _public_bytecode(self, path):
        if path.suffix != ".pyc" or path.parent.name != "__pycache__":
            return False
        stem = path.name.split(".")[0]
        return path.parent.parent / (stem + ".py") in self.public_files

    def _runtime(self, path):
        if any(_inside(path, site) for site in self.site_roots):
            if any(_inside(path, root) for root in self.runtime_roots):
                return True
            # Numeric package metadata is public runtime information, not input.
            for site in self.site_roots:
                if _inside(path, site):
                    parts = path.relative_to(site).parts
                    return bool(parts and parts[0].endswith(".dist-info") and
                                parts[0].startswith(("numpy-", "scipy-")))
            return False
        return any(_inside(path, root) for root in self.stdlib_roots)

    def check_path(self, raw, *, write=False, directory=False):
        if isinstance(raw, int):
            if raw not in self.allowed_fds:
                self._deny("fd", raw)
            return None
        if raw is None:
            raw = os.getcwd()
        path = Path(os.fsdecode(raw)).resolve()
        if any(part.lower() in {"archive", "archieve"} for part in path.parts):
            self._deny("path", path)
        own = _inside(path, self.output)
        if write:
            okay = own
        elif _inside(path, self.root):
            okay = own or path in self.public_files or self._public_bytecode(path)
            if directory:
                okay = okay or path in self.public_dirs
        else:
            okay = own or path in self.runtime_files or self._runtime(path)
            if directory:
                okay = okay or path in self.site_roots
        if not okay:
            self._deny("write" if write else "read", path)
        if not write and not directory:
            self.events.append(dict(operation="read", target=str(path), allowed=True))
        return path

    def check_loaded_modules(self):
        for name, module in list(sys.modules.items()):
            self.check_import(name)
            path = getattr(module, "__file__", None)
            if path and _inside(Path(path).resolve(), self.root):
                self.check_path(path)

    def audit(self, event, args):
        if not self.enabled or self._checking:
            return
        self._checking = True
        try:
            if event == "open":
                path, mode, flags = args
                write = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
                self.check_path(path, write=write)
            elif event == "import":
                self.check_import(args[0])
                if len(args) > 1 and args[1]:
                    self.check_path(args[1])
            elif event in {"os.listdir", "os.scandir"}:
                self.check_path(args[0], directory=True)
            elif event in {"os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.utime"}:
                self.check_path(args[0], write=True)
            elif event in {"os.rename", "os.replace"}:
                self.check_path(args[0], write=True)
                self.check_path(args[1], write=True)
            elif event in {"os.symlink", "os.link"}:
                self._deny(event, args[:2])
            elif event in {"subprocess.Popen", "os.system", "os.fork", "os.forkpty",
                           "os.posix_spawn", "os.exec", "socket.connect", "socket.bind"}:
                self._deny(event, "process/network access")
            elif event == "ctypes.dlopen" and args[0]:
                # Shared numeric libraries are runtime dependencies; project
                # paths still receive the same pre-access rejection.
                path = Path(os.fsdecode(args[0]))
                if path.is_absolute():
                    resolved = path.resolve()
                    if not (self._runtime(resolved) or
                            _inside(resolved, Path(sys.base_prefix).resolve() / "lib")):
                        self._deny(event, resolved)
        finally:
            self._checking = False

    def install(self):
        sys.addaudithook(self.audit)
        sys.meta_path.insert(0, self.finder)
        self.enabled = True
        return self

    def disable(self):
        self.enabled = False
        if self.finder in sys.meta_path:
            sys.meta_path.remove(self.finder)

    def __enter__(self):
        return self.install()

    def __exit__(self, *unused):
        self.disable()


def _identity(message, args, body):
    identity = message.get("identity")
    _exact(identity, IDENTITY_FIELDS, "Request identity")
    for name in ("attempt_id", "pair_id", "sense_request_id", "stream_id", "payload_sha256"):
        if not isinstance(identity[name], str) or not identity[name]:
            raise ContractError("Invalid identity field: " + name)
    for name in ("target_id", "global_tick"):
        if isinstance(identity[name], bool) or not isinstance(identity[name], int) or identity[name] < 0:
            raise ContractError("Invalid identity field: " + name)
    if identity["attempt_id"] != args.attempt_id or identity["pair_id"] != args.pair_id:
        raise ContractError("Request belongs to a different attempt or pair")
    if identity["payload_sha256"] != digest(body):
        raise ContractError("IPC body digest differs from request identity")
    return identity


def main(args):
    """Entry called by the public root CLI; exceptions remain nonzero failures."""
    args = validate_startup(args)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "tmp").mkdir(exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    guard = PublicAccessGuard(root, out, args.fd).install()
    counters = dict(estimator_calls=0, completed_estimates=0, start_attempts=0,
                    sense_requests=0, duplicate_requests=0, skipped_frames=0,
                    isolation_probes=0)
    isolation = []
    active_identity = None
    wire = None

    def flush():
        save_json(out / "counters.json", counters)
        save_json(out / "isolation.json", isolation)
        save_json(out / "access_audit.json", dict(scope="controlled_python_preaccess_guard",
                                                  events=guard.events))

    try:
        guard.check_loaded_modules()
        from .wire import WireClient
        wire = WireClient(args.fd)

        def receive():
            # Guardian owns the preregistered pair/request deadlines. A legal
            # idle sensor must not invent a shorter scientific-job deadline.
            while True:
                try:
                    return wire.recv(timeout=0.25)
                except TimeoutError:
                    wire.peer.check_partial_deadline()

        wire.send(dict(type="READY", role="sense", contract_id=CONTRACT_ID))
        start = receive()
        _exact(start, {"type", "payload"}, "START message")
        if start["type"] != "START":
            raise ContractError("START required after READY")
        config = start["payload"]
        _exact(config, {"contract_id", "mode", "streams"}, "Public sensing config")
        if config["contract_id"] != CONTRACT_ID or config["mode"] not in {"science", "isolation_probe"}:
            raise ContractError("Invalid sensing execution contract or mode")
        if not isinstance(config["streams"], list):
            raise ContractError("Public streams must be a list")
        # These permitted scientific dependencies are loaded under the guard,
        # even for the zero-WLS positive isolation check.
        import numpy as np
        import scipy
        import research.cooperative_sensing.estimator as estimator_module
        from research.cooperative_sensing.estimator import estimate
        from .public_stream import BridgeFrameProcessor
        guard.check_loaded_modules()
        save_json(out / "runtime.json", dict(contract_id=CONTRACT_ID, mode=config["mode"],
            numpy_version=np.__version__, numpy_file=np.__file__, scipy_version=scipy.__version__,
            scipy_file=scipy.__file__, python=sys.version, executable=sys.executable,
            pid=os.getpid(), pgid=os.getpgrp(), ppid=os.getppid(),
            rlimit_cpu=list(resource.getrlimit(resource.RLIMIT_CPU)),
            rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),
            thread_env={key: os.environ.get(key) for key in THREAD_KEYS},
            public_modules=sorted(PUBLIC_MODULES)))
        save_json(out / "public_config.json", config)

        def logged_estimate(payload):
            counters["estimator_calls"] += 1
            index = counters["estimator_calls"]
            record = dict(index=index, identity=copy.deepcopy(active_identity),
                          payload=copy.deepcopy(payload), payload_sha256=digest(payload),
                          status="started", native_starts=[])
            path = out / "estimates" / f"{index:06d}.json"
            save_json(path, record)
            save_json(out / "counters.json", counters)
            original_least_squares = estimator_module.least_squares
            starts_before = counters["start_attempts"]

            def tracked_least_squares(*positional, **keywords):
                counters["start_attempts"] += 1
                point = positional[1] if len(positional) > 1 else keywords["x0"]
                native = dict(start_id=len(record["native_starts"]),
                              start=[float(value) for value in point], status="entered")
                record["native_starts"].append(native)
                save_json(path, record)
                save_json(out / "counters.json", counters)
                try:
                    answer = original_least_squares(*positional, **keywords)
                    native["status"] = "returned"
                    return answer
                except BaseException as error:
                    native.update(status="raised", error_type=type(error).__name__, error=str(error))
                    raise

            try:
                estimator_module.least_squares = tracked_least_squares
                result = estimate(payload)
                record.update(status="returned", result=result)
                save_json(path, record)
                if (not isinstance(result.get("starts"), list) or len(result["starts"]) != 9 or
                        counters["start_attempts"] - starts_before != 9):
                    raise ContractError("Frozen WLS must return all nine start records")
                counters["completed_estimates"] += 1
                save_json(out / "counters.json", counters)
                return result
            except BaseException as error:
                record.update(status="error", error_type=type(error).__name__,
                              error=str(error), traceback=traceback.format_exc())
                save_json(path, record)
                save_json(out / "counters.json", counters)
                raise
            finally:
                estimator_module.least_squares = original_least_squares

        streams = {}
        for row in config["streams"]:
            _exact(row, STREAM_FIELDS, "Public stream registration")
            processor = BridgeFrameProcessor(**row, estimator_fn=logged_estimate)
            if row["stream_id"] in streams:
                raise ContractError("Duplicate public stream registration")
            streams[row["stream_id"]] = processor
        responses = {}
        while True:
            message = receive()
            kind = message.get("type")
            if kind == "STOP":
                _exact(message, {"type", "attempt_id", "pair_id"}, "STOP")
                if message["attempt_id"] != args.attempt_id or message["pair_id"] != args.pair_id:
                    raise ContractError("STOP belongs to another attempt or pair")
                flush()
                wire.send(dict(type="STOP_ACK", role="sense", counters=counters))
                return 0
            if kind == "ISOLATION_PROBE":
                _exact(message, {"type", "identity", "action", "target"}, "Isolation probe")
                if config["mode"] != "isolation_probe":
                    raise AccessDenied("Isolation probes are disabled for science streams")
                body = {name: message[name] for name in ("action", "target")}
                identity = _identity(message, args, body)
            elif kind == "SENSE":
                _exact(message, {"type", "identity", "frame", "allowed_sensor_ids", "start_tick"}, "SENSE")
                body = {name: message[name] for name in ("frame", "allowed_sensor_ids", "start_tick")}
                identity = _identity(message, args, body)
            else:
                raise ContractError("Unknown sensing IPC type: " + repr(kind))
            request = identity["sense_request_id"]
            message_digest = digest(message)
            if request in responses:
                previous_digest, response = responses[request]
                if message_digest != previous_digest:
                    raise ContractError("Conflicting request identity replay")
                counters["duplicate_requests"] += 1
                wire.send(copy.deepcopy(response))
                continue
            active_identity = identity
            if kind == "ISOLATION_PROBE":
                if body["action"] not in {"read", "import"} or not isinstance(body["target"], str):
                    raise ContractError("Invalid predeclared isolation probe")
                try:
                    if body["action"] == "read":
                        with open(body["target"], "rb") as source:
                            source.read(1)
                    else:
                        importlib.import_module(body["target"])
                except AccessDenied as error:
                    result = dict(passed=True, error_type="AccessDenied", error=str(error),
                                  action=body["action"], target=body["target"],
                                  estimator_calls=counters["estimator_calls"])
                else:
                    raise ContractError("A forbidden isolation probe unexpectedly succeeded")
                counters["isolation_probes"] += 1
                response = dict(type="ISOLATION_RESULT", identity=identity, result=result)
                isolation.append(copy.deepcopy(response))
                flush()
            else:
                frame = body["frame"]
                if not isinstance(frame, dict):
                    raise ContractError("Public frame must be a mapping")
                if (identity["stream_id"] != frame.get("stream_id") or
                        identity["target_id"] != frame.get("target_id") or
                        identity["global_tick"] != frame.get("tick")):
                    raise ContractError("Frame does not match its IPC identity")
                if identity["stream_id"] not in streams:
                    raise ContractError("Unregistered public stream")
                processor = streams[identity["stream_id"]]
                if (body["start_tick"] != processor.start_tick or
                        not isinstance(body["allowed_sensor_ids"], list) or
                        len(set(body["allowed_sensor_ids"])) != len(body["allowed_sensor_ids"]) or
                        set(body["allowed_sensor_ids"]) != processor.allowed_sensor_ids):
                    raise ContractError("Public stream registration changed")
                if config["mode"] == "isolation_probe" and len(frame.get("records", [])) >= 2:
                    raise ContractError("Isolation positive probe must skip WLS with m < 2")
                counters["sense_requests"] += 1
                ordinal = counters["sense_requests"]
                record = dict(request=message, status="started")
                path = out / "frames" / f"{ordinal:06d}.json"
                save_json(path, record)
                result = processor.process(frame)
                counters["skipped_frames"] += int(result["skipped"])
                response = dict(type="SENSE_RESULT", identity=identity, result=result)
                record.update(status="completed", response=response)
                save_json(path, record)
                save_json(out / "counters.json", counters)
            responses[request] = message_digest, copy.deepcopy(response)
            wire.send(response)
            active_identity = None
    except BaseException as error:
        save_json(out / "error.json", dict(error_type=type(error).__name__, error=str(error),
            identity=active_identity, traceback=traceback.format_exc(), counters=counters))
        flush()
        raise
    finally:
        if wire is not None:
            wire.close()
