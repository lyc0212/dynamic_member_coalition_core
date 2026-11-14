"""Public-only full-evaluation sensor worker; frozen WLS/Q are unchanged.

Only current public frames enter this process.  Logging retains every actual
least-squares start.  No evaluator, oracle, prefix exporter, or design is read.
"""
from __future__ import annotations
import copy
import hashlib
import importlib
import os
from pathlib import Path
import resource
import sys
import time
import traceback

from research.information_service_bridge.common import digest as transport_digest
from research.information_service_bridge.sensing_worker import THREAD_KEYS, IDENTITY_FIELDS, STREAM_FIELDS
from .common import CONTRACT_ID, AccessDenied, ContractError, digest, save_json
from .runtime import (install_role_guard, validate_worker_startup, SENSE_MODULES,
                      validate_registration, REGISTRATION_FIELDS)

PUBLIC_MODULES = SENSE_MODULES


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ContractError(label + " has unexpected or missing fields")


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
    if identity["payload_sha256"] != transport_digest(body):
        raise ContractError("IPC body digest differs from request identity")
    return identity


def main(args):
    """Entry called by the public root CLI; exceptions remain nonzero failures."""
    args = validate_worker_startup(args, transport_role="sense")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "tmp").mkdir(exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    guard = install_role_guard("sense", out, args.fd)
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
        from research.information_service_bridge.wire import WireClient
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
        fields = {"contract_id", "mode", "streams"}
        if isinstance(config, dict) and config.get("mode") == "interface_probe":
            fields.add("interface_fault")
        _exact(config, fields, "Public sensing config")
        if config["contract_id"] != CONTRACT_ID or config["mode"] not in {"science", "isolation_probe", "interface_probe"}:
            raise ContractError("Invalid sensing execution contract or mode")
        if config["mode"] == "interface_probe":
            _exact(config["interface_fault"], {"type"}, "Fixed interface fault")
            if config["interface_fault"]["type"] not in {"no_response", "worker_exit", "numeric_contract_violation"}:
                raise ContractError("Unknown interface fault vector")
        if not isinstance(config["streams"], list):
            raise ContractError("Public streams must be a list")
        # These permitted scientific dependencies are loaded under the guard,
        # even for the zero-WLS positive isolation check.
        import numpy as np
        import scipy
        import research.cooperative_sensing.estimator as estimator_module
        from research.cooperative_sensing.estimator import estimate
        from research.information_service_bridge.public_stream import BridgeFrameProcessor
        guard.check_loaded_modules()
        def fingerprint(path):
            resolved = Path(path).resolve()
            hasher = hashlib.sha256()
            with resolved.open('rb') as source:
                for block in iter(lambda: source.read(1 << 20), b''):
                    hasher.update(block)
            return dict(path=str(resolved), sha256=hasher.hexdigest())
        save_json(out / "runtime.json", dict(contract_id=CONTRACT_ID, mode=config["mode"],
            numpy_version=np.__version__, numpy_file=np.__file__, scipy_version=scipy.__version__,
            scipy_file=scipy.__file__, python=sys.version, executable=sys.executable,
            pid=os.getpid(), pgid=os.getpgrp(), ppid=os.getppid(),
            rlimit_cpu=list(resource.getrlimit(resource.RLIMIT_CPU)),
            rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),
            thread_env={key: os.environ.get(key) for key in THREAD_KEYS},
            public_modules=sorted(PUBLIC_MODULES),
            runtime_fingerprints={
                'executable': fingerprint(sys.executable), 'numpy': fingerprint(np.__file__),
                'scipy': fingerprint(scipy.__file__), 'estimator': fingerprint(estimator_module.__file__),
                'public_quality': fingerprint(sys.modules['research.information_service.public_quality'].__file__),
                'public_stream': fingerprint(sys.modules['research.information_service_bridge.public_stream'].__file__)}))
        save_json(out / "public_config.json", config)

        def logged_estimate(payload):
            counters["estimator_calls"] += 1
            index = counters["estimator_calls"]
            record = dict(index=index, identity=copy.deepcopy(active_identity),
                          flow_context=copy.deepcopy(stream_contexts[active_identity['stream_id']]),
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
        stream_contexts = {}
        stream_registrations = {}
        for row in config["streams"]:
            _exact(row, REGISTRATION_FIELDS, "Public stream registration")
            validate_registration(row)
            processor = BridgeFrameProcessor(**{key:row[key] for key in STREAM_FIELDS}, estimator_fn=logged_estimate)
            if row["stream_id"] in streams:
                raise ContractError("Duplicate public stream registration")
            streams[row["stream_id"]] = processor
            stream_contexts[row['stream_id']] = copy.deepcopy(row['context'])
            stream_registrations[row['stream_id']] = copy.deepcopy(row)
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
                if config["mode"] == "interface_probe":
                    fault = config["interface_fault"]["type"]
                    flush()
                    save_json(out / "injected_fault.json", dict(type=fault, identity=identity,
                              estimator_calls=0, start_attempts=0, declared_admission_only=True))
                    if fault == "worker_exit":
                        os._exit(7)
                    if fault == "no_response":
                        while True:
                            time.sleep(0.05)
                    from research.cooperative_sensing.estimator import NumericContractViolation
                    raise NumericContractViolation("INJECTED_ONLINE_NUMERIC_CONTRACT_ERROR")
                result = processor.process(frame)
                # The frozen BridgeFrameProcessor still advertises its original
                # adapter contract; the enclosing evaluation contract is distinct.
                result["online_contract_id"] = CONTRACT_ID
                result['flow_context'] = copy.deepcopy(stream_contexts[identity['stream_id']])
                result['flow_registration'] = copy.deepcopy(stream_registrations[identity['stream_id']])
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
