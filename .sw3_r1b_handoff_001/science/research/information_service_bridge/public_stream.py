"""Global-clock public streams; the frozen A estimator and quality rule are reused.

This module receives measurements, never physical truth or scenario objects.
The execution bridge identity is separate from the unchanged A frame identity.
"""
from __future__ import annotations

import copy
import re

from research.information_service.common import ContractError as PublicContractError
from research.information_service.public_quality import prepare_frame, assess_quality

from .common import CONTRACT_ID, ContractError, digest


def _estimate(payload):
    from research.cooperative_sensing.estimator import estimate
    return estimate(payload)


class BridgeFrameProcessor:
    """One predefined target/stream, contiguous from its global birth tick.

    Failed operations do not advance the endpoint or packet caches. Invocation
    counters do include a solver call that raises, so failures cannot disappear.
    """

    def __init__(self, allowed_sensor_ids, start_tick, stream_id, target_id,
                 estimator_fn=None):
        if (not isinstance(allowed_sensor_ids, (list, tuple, set, frozenset)) or
                any(not isinstance(s, str) or re.fullmatch(r"U(?:0|[1-9][0-9]*)", s) is None
                    for s in allowed_sensor_ids) or
                len(set(allowed_sensor_ids)) != len(allowed_sensor_ids)):
            raise ContractError("Unique canonical allowed Uk identities required")
        for name, value in (("start_tick", start_tick), ("target_id", target_id)):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ContractError(name + " must be a nonnegative integer")
        if not isinstance(stream_id, str) or not stream_id:
            raise ContractError("stream_id must be nonempty")
        self.allowed_sensor_ids = frozenset(allowed_sensor_ids)
        self.start_tick, self.stream_id, self.target_id = start_tick, stream_id, target_id
        self.estimator_fn = _estimate if estimator_fn is None else estimator_fn
        if not callable(self.estimator_fn):
            raise ContractError("estimator_fn must be callable")
        self.last_tick = None
        self.estimator_calls = 0
        self.start_records = 0
        self._frames = {}
        self._packets = {}

    def process(self, frame):
        try:
            prepared = prepare_frame(frame, self.allowed_sensor_ids)
        except PublicContractError as error:
            raise ContractError(str(error)) from error
        clean = prepared["normalized_frame"]
        if clean["stream_id"] != self.stream_id or clean["target_id"] != self.target_id:
            raise ContractError("Stream and target differ from their public registration")
        frame_id = clean["frame_id"]
        if frame_id in self._frames:
            cached = self._frames[frame_id]
            if cached["frame_sha256"] != prepared["frame_sha256"]:
                raise ContractError("Conflicting duplicate frame")
            result = copy.deepcopy(cached)
            result.update(duplicate=True, estimator_called=False)
            return result
        expected = self.start_tick if self.last_tick is None else self.last_tick + 1
        if clean["tick"] != expected:
            raise ContractError(f"Missing or reordered endpoint: expected global tick {expected}")
        packet_hashes = {r["packet_id"]: digest(r) for r in clean["records"]}
        for packet, identity in packet_hashes.items():
            if packet in self._packets and self._packets[packet] != identity:
                raise ContractError("Conflicting previously received packet")
        skipped = prepared["valid_sensor_count"] < 2
        estimate_result = None
        if not skipped:
            work = copy.deepcopy(prepared["payload"])
            self.estimator_calls += 1
            estimate_result = self.estimator_fn(work)
            if isinstance(estimate_result, dict) and isinstance(estimate_result.get("starts"), list):
                self.start_records += len(estimate_result["starts"])
            if digest(work) != prepared["payload_sha256"]:
                raise ContractError("Estimator mutated the five-field public input")
        try:
            quality = assess_quality(prepared["payload"], estimate_result)
        except PublicContractError as error:
            raise ContractError(str(error)) from error
        quality["frame_id"] = frame_id
        result = dict(prepared, execution_contract_id=CONTRACT_ID, frame_id=frame_id,
                      stream_id=self.stream_id, target_id=self.target_id, tick=clean["tick"],
                      start_tick=self.start_tick, estimate_result=copy.deepcopy(estimate_result),
                      quality=quality, skipped=skipped, estimator_called=not skipped, duplicate=False)
        self._frames[frame_id] = copy.deepcopy(result)
        self._packets.update(packet_hashes)
        self.last_tick = clean["tick"]
        return result
