"""Public measurement adaptation and a local WLS quality proxy.

No true target state, trajectory generator or physical simulator is imported.
Only the final representative estimate is assessed; a different local start's
branch guard remains a diagnostic and does not veto that representative.
"""
from __future__ import annotations

import copy
import math
import re

import numpy as np

from .common import CONTRACT_ID, QUALITY_ID, DT, DELTA, P_REF, DOMAIN, ContractError, digest


# Match the frozen service time-representation tolerance without importing the
# simulator into this isolated measurement/estimation module.
FRAME_TIME_TOL = 1e-10
FRAME_FIELDS = frozenset(("contract_id", "stream_id", "frame_id", "tick", "target_id",
                          "measurement_time", "available_time", "records"))
RECORD_FIELDS = frozenset(("sensor_id", "position", "bearing", "sigma", "packet_id",
                           "measurement_tick", "available_tick", "status"))
PAYLOAD_FIELDS = frozenset(("sensor_ids", "positions", "bearings", "sigmas", "domain"))
_ROBOT_ID = re.compile(r"U(?:0|[1-9][0-9]*)\Z")


def _fields(value, fields, label):
    if not isinstance(value, dict) or set(value) != fields:
        raise ContractError(f"{label} fields must be exactly {sorted(fields)}")


def _text(value, label):
    if not isinstance(value, str) or not value:
        raise ContractError(f"{label} must be a nonempty string")
    return value


def _integer(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContractError(f"{label} must be a nonnegative integer")
    return value


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{label} must be a finite number")
    return result


def _position(value, label):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ContractError(f"{label} must have two coordinates")
    return [_number(x, label) for x in value]


def _sensor_id(value):
    if not isinstance(value, str) or _ROBOT_ID.fullmatch(value) is None:
        raise ContractError("sensor_id must preserve a canonical Uk identity")
    return value


def _allowed(values):
    if not isinstance(values, (list, tuple, set, frozenset)):
        raise ContractError("allowed_sensor_ids must be a collection of Uk identities")
    result = tuple(_sensor_id(value) for value in values)
    if len(set(result)) != len(result):
        raise ContractError("Duplicate allowed sensor identity")
    return frozenset(result)


def _robot_order(value):
    return int(value[1:])


def _validated_payload(payload):
    _fields(payload, PAYLOAD_FIELDS, "Estimator payload")
    for name in ("sensor_ids", "positions", "bearings", "sigmas"):
        if not isinstance(payload[name], (list, tuple)):
            raise ContractError(f"Payload {name} must be a sequence")
    count = len(payload["sensor_ids"])
    if any(len(payload[name]) != count for name in ("positions", "bearings", "sigmas")):
        raise ContractError("Estimator payload lengths differ")
    ids = [_sensor_id(value) for value in payload["sensor_ids"]]
    if len(set(ids)) != count:
        raise ContractError("Repeated sensor identity in estimator payload")
    positions = [_position(value, "position") for value in payload["positions"]]
    bearings = [_number(value, "bearing") for value in payload["bearings"]]
    sigmas = [_number(value, "sigma") for value in payload["sigmas"]]
    if any(value <= 0 for value in sigmas):
        raise ContractError("sigma must be positive")
    domain = payload["domain"]
    if not isinstance(domain, (list, tuple)) or len(domain) != 2:
        raise ContractError("Public domain must be the frozen rectangle")
    domain = [_position(row, "domain") for row in domain]
    if domain != DOMAIN:
        raise ContractError("Public domain differs from the frozen rectangle")
    return dict(sensor_ids=ids, positions=positions, bearings=bearings,
                sigmas=sigmas, domain=copy.deepcopy(DOMAIN))


def prepare_frame(frame, allowed_sensor_ids):
    """Validate and canonicalize one public frame without keeping any state."""
    _fields(frame, FRAME_FIELDS, "Public frame")
    allowed = _allowed(allowed_sensor_ids)
    if frame["contract_id"] != CONTRACT_ID:
        raise ContractError("Public frame contract identity changed")
    stream_id = _text(frame["stream_id"], "stream_id")
    frame_id = _text(frame["frame_id"], "frame_id")
    tick = _integer(frame["tick"], "tick")
    target_id = _integer(frame["target_id"], "target_id")
    when = tick * DT
    for name in ("measurement_time", "available_time"):
        value = _number(frame[name], name)
        if value < 0 or abs(value - when) > FRAME_TIME_TOL:
            raise ContractError(f"Frame {name} does not match its tick")
    if not isinstance(frame["records"], (list, tuple)):
        raise ContractError("records must be a sequence; missing sensors use no record")
    packets, sensors = {}, {}
    duplicate_records = 0
    for record in frame["records"]:
        _fields(record, RECORD_FIELDS, "Measurement record")
        sensor = _sensor_id(record["sensor_id"])
        if sensor not in allowed:
            raise ContractError("Measurement sensor is outside the occupied team")
        packet = _text(record["packet_id"], "packet_id")
        measured = _integer(record["measurement_tick"], "measurement_tick")
        available = _integer(record["available_tick"], "available_tick")
        if measured > tick or available > tick:
            raise ContractError("Future measurements or packets cannot be used early")
        if available < measured:
            raise ContractError("Negative packet delay")
        if record["status"] != "ok":
            raise ContractError("Only received status=ok records are public; missing packets are absent")
        sigma = _number(record["sigma"], "sigma")
        if sigma <= 0:
            raise ContractError("sigma must be positive")
        clean = dict(sensor_id=sensor, position=_position(record["position"], "position"),
                     bearing=_number(record["bearing"], "bearing"), sigma=sigma,
                     packet_id=packet, measurement_tick=measured,
                     available_tick=available, status="ok")
        if packet in packets:
            if digest(clean) != digest(packets[packet]):
                raise ContractError("Conflicting duplicate packet")
            duplicate_records += 1
            continue
        if sensor in sensors:
            raise ContractError("Repeated Uk with different packets in the same frame")
        packets[packet] = clean
        sensors[sensor] = packet
    canonical_records = sorted(packets.values(), key=lambda row: _robot_order(row["sensor_id"]))
    current = [row for row in canonical_records if row["measurement_tick"] == tick]
    excluded = [dict(sensor_id=row["sensor_id"], packet_id=row["packet_id"], reason="stale")
                for row in canonical_records if row["measurement_tick"] != tick]
    payload = dict(sensor_ids=[row["sensor_id"] for row in current],
                   positions=[row["position"] for row in current],
                   bearings=[row["bearing"] for row in current],
                   sigmas=[row["sigma"] for row in current], domain=copy.deepcopy(DOMAIN))
    normalized = dict(contract_id=CONTRACT_ID, stream_id=stream_id, frame_id=frame_id,
                      tick=tick, target_id=target_id, measurement_time=when,
                      available_time=when, records=canonical_records)
    return dict(payload=payload, payload_sha256=digest(payload),
                frame_sha256=digest(normalized), normalized_frame=normalized,
                valid_sensor_count=len(current), excluded_records=excluded,
                duplicate_record_count=duplicate_records,
                missing_sensor_ids=sorted(allowed - {row["sensor_id"] for row in current},
                                          key=_robot_order))


def classify_radius(radius, delta=DELTA):
    """Strict binary64 threshold comparison, with no acceptance tolerance."""
    radius = _number(radius, "radius")
    delta = _number(delta, "delta")
    if radius < 0 or delta <= 0:
        raise ContractError("radius must be nonnegative and delta must be positive")
    return "PASS" if radius <= delta else "FAIL"


def _diagnostics(result):
    if result is None:
        return {}
    names = ("optimizer_converged", "numerical_ill_conditioned", "ambiguity_detected",
             "boundary_active", "branch_guard_triggered", "numeric_contract_violation")
    data = {name: copy.deepcopy(result.get(name)) for name in names}
    starts = result.get("starts", [])
    if not isinstance(starts, list):
        raise ContractError("Estimator starts must be a list")
    if any(not isinstance(row, dict) for row in starts):
        raise ContractError("Estimator start records must be mappings")
    data["start_guard_count"] = sum(row.get("guard") is not None for row in starts)
    return data


def assess_quality(payload, estimate_result):
    """Assess the public representative estimate; no true state is accepted."""
    public = _validated_payload(payload)
    if estimate_result is not None and not isinstance(estimate_result, dict):
        raise ContractError("Estimator result must be a mapping or null when skipped")
    diagnostics = _diagnostics(estimate_result)
    result = dict(contract_id=QUALITY_ID, service_contract_id=CONTRACT_ID,
                  payload_sha256=digest(public), contributing_sensor_ids=public["sensor_ids"],
                  status="UNKNOWN", reasons=[], has_estimate=False, estimate=None,
                  J=None, I=None, information_at_estimate=None, singular_values=None,
                  radius_proxy=None, delta=DELTA, p_ref=P_REF,
                  estimator_diagnostics=diagnostics, representative_guard=None)
    if len(public["sensor_ids"]) < 2:
        result["reasons"] = ["insufficient_measurements"]
        return result
    if estimate_result is None:
        raise ContractError("A non-skipped frame needs an estimator result")
    from research.cooperative_sensing.estimator import (
        values, condition, EvaluationGuard, NumericContractViolation)

    if estimate_result.get("numeric_contract_violation") is True:
        raise NumericContractViolation("Estimator reported a numerical contract violation")
    accepted = estimate_result.get("has_accepted_estimate")
    if not isinstance(accepted, bool):
        raise ContractError("has_accepted_estimate must be an explicit boolean")
    if not accepted:
        result["reasons"] = ["no_accepted_estimate"]
        return result
    point = _position(estimate_result.get("estimate"), "representative estimate")
    if not all(DOMAIN[0][axis]-1e-10 <= point[axis] <= DOMAIN[1][axis]+1e-10 for axis in (0, 1)):
        raise ContractError("Accepted representative is outside the public domain")
    result.update(has_estimate=True, estimate=point)
    for name in ("optimizer_converged", "numerical_ill_conditioned", "ambiguity_detected",
                 "boundary_active", "branch_guard_triggered", "numeric_contract_violation"):
        if not isinstance(estimate_result.get(name), bool):
            raise ContractError(f"Accepted representative needs boolean diagnostic {name}")
    if not estimate_result["optimizer_converged"]:
        raise ContractError("An accepted representative must have converged under the estimator contract")
    try:
        residual, jacobian = values(public, point)
    except EvaluationGuard as exc:
        result["reasons"] = ["representative_quality_unavailable"]
        result["representative_guard"] = copy.deepcopy(exc.detail)
        return result
    if not np.isfinite(residual).all() or not np.isfinite(jacobian).all():
        raise NumericContractViolation("Nonfinite representative residual or Jacobian")
    info = condition(jacobian)
    information = jacobian.T @ jacobian
    if not np.isfinite(information).all() or not all(math.isfinite(x) for x in info["singular_values"]):
        raise NumericContractViolation("Nonfinite local information or singular values")
    result.update(J=jacobian.tolist(), I=information.tolist(),
                  information_at_estimate=information.tolist(),
                  singular_values=info["singular_values"])
    diagnostics["recomputed_numerical_ill_conditioned"] = info["ill"]
    s_min = info["singular_values"][-1]
    if s_min > 0:
        radius = math.sqrt(-2. * math.log1p(-P_REF)) / s_min
        if not math.isfinite(radius):
            raise NumericContractViolation("Nonfinite local radius proxy")
        result["radius_proxy"] = radius
    reasons = []
    if info["ill"] or estimate_result["numerical_ill_conditioned"]:
        reasons.append("numerical_ill_conditioned")
    if estimate_result["ambiguity_detected"]:
        reasons.append("ambiguity_detected")
    if estimate_result["boundary_active"]:
        reasons.append("boundary_active")
    if reasons:
        result["reasons"] = reasons
        return result
    if result["radius_proxy"] is None:
        result["reasons"] = ["representative_quality_unavailable"]
        return result
    result["status"] = classify_radius(result["radius_proxy"])
    result["reasons"] = ["radius_within_threshold" if result["status"] == "PASS" else "radius_exceeds_threshold"]
    return result


def _estimate(payload):
    from research.cooperative_sensing.estimator import estimate
    return estimate(payload)


class FrameProcessor:
    """One stream/target's contiguous frames, with immutable replay results."""

    def __init__(self, allowed_sensor_ids, estimator_fn=None):
        self.allowed_sensor_ids = _allowed(allowed_sensor_ids)
        self.estimator_fn = _estimate if estimator_fn is None else estimator_fn
        if not callable(self.estimator_fn):
            raise ContractError("estimator_fn must be callable")
        self.last_tick = None
        self.estimator_calls = 0
        self._stream_id = None
        self._target_id = None
        self._frames = {}
        self._packets = {}

    def process(self, frame):
        prepared = prepare_frame(frame, self.allowed_sensor_ids)
        clean = prepared["normalized_frame"]
        if self._stream_id is not None and (clean["stream_id"] != self._stream_id or
                                            clean["target_id"] != self._target_id):
            raise ContractError("A processor cannot change stream or target identity")
        frame_id = clean["frame_id"]
        if frame_id in self._frames:
            cached = self._frames[frame_id]
            if prepared["frame_sha256"] != cached["frame_sha256"]:
                raise ContractError("Conflicting duplicate frame")
            repeated = copy.deepcopy(cached)
            repeated.update(duplicate=True, estimator_called=False)
            return repeated
        expected_tick = 0 if self.last_tick is None else self.last_tick + 1
        if clean["tick"] != expected_tick:
            raise ContractError(f"Missing or reordered endpoint: expected tick {expected_tick}")
        packet_hashes = {row["packet_id"]: digest(row) for row in clean["records"]}
        for packet, identity in packet_hashes.items():
            if packet in self._packets and self._packets[packet] != identity:
                raise ContractError("Conflicting previously received packet")
        skipped = prepared["valid_sensor_count"] < 2
        estimate_result = None
        if not skipped:
            work = copy.deepcopy(prepared["payload"])
            self.estimator_calls += 1
            estimate_result = self.estimator_fn(work)
            if digest(work) != prepared["payload_sha256"]:
                raise ContractError("Estimator mutated the public input")
        quality = assess_quality(prepared["payload"], estimate_result)
        quality["frame_id"] = frame_id
        output = dict(prepared, frame_id=frame_id, stream_id=clean["stream_id"],
                      target_id=clean["target_id"], tick=clean["tick"],
                      estimate_result=copy.deepcopy(estimate_result), quality=quality,
                      skipped=skipped, estimator_called=not skipped, duplicate=False)
        # Commit only after input, estimation and quality contracts all succeed.
        self._frames[frame_id] = copy.deepcopy(output)
        self._packets.update(packet_hashes)
        self._stream_id, self._target_id = clean["stream_id"], clean["target_id"]
        self.last_tick = clean["tick"]
        return output
