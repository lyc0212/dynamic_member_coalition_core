"""Public-file-only WLS replay. No physical state, generator, or service imports."""
import json
from pathlib import Path
import sys

from .common import save_json
from .public_quality import FrameProcessor


def run_public_file(path, out, *, repeats=1):
    raw = json.loads(Path(path).read_text())
    results = []
    for repeat in range(repeats):
        processor = FrameProcessor(raw["allowed_sensor_ids"])
        for frame in raw["frames"]:
            value = processor.process(frame)
            row = dict(tick=frame["tick"], frame_id=frame["frame_id"],
                       repeat=repeat, result=value)
            results.append(row)
            save_json(Path(out) / f"frame_{repeat}_{frame['tick']:04d}.json", row)
    forbidden = [name for name in sys.modules if name.startswith("pursuit_v2")
                 or name in ("research.cooperative_sensing.fixtures",
                             "research.information_service.fixtures")]
    if forbidden:
        raise RuntimeError(f"Private/physical module entered sensing worker: {forbidden}")
    result = dict(passed=True, case_id=raw["case_id"], rows=results,
                  forbidden_modules=forbidden, scope="public input only")
    save_json(Path(out) / "sensing.json", result)
    return result
