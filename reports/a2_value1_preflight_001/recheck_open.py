"""Read-only OPEN verification and frozen-cut ranking for VALUE-1P."""
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

import numpy
import scipy

from research.non_oracle.a2_value_lock import locked_decision
from scripts.run_a2_value_locked import (
    ANN_SHA, MODES, OPEN, TICKS, WORLD_SHA, load_open, read,
)
from scripts.gq_windows.a0_compare import admitted_pair
from scripts.gq_windows.a0_identity import IdentityMap, exact_tree


def hashes(paths):
    return {str(p).replace("\\", "/"): hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in paths}


def main():
    guard = Path("reports/a2_switch_episode_001_guard")
    out = Path(__file__).parent
    previous = read(guard / "BEFORE.json")
    exact_tree(previous["pins"], read(guard / "AFTER.json")["pins"], "/OPEN/pins")
    exact_tree(previous["pins"], hashes(previous["pins"]), "/local/pins")
    world = Path("configs/a2_switch_two_target_v1.json")
    announcements = Path("configs/a2_switch_public_announcements_v1.json")
    assert hashlib.sha256(world.read_bytes()).hexdigest() == WORLD_SHA
    assert hashlib.sha256(announcements.read_bytes()).hexdigest() == ANN_SHA
    open_paths = sorted(OPEN.glob("*.json")) + sorted(guard.iterdir())
    open_before = hashes(p for p in open_paths if p.is_file())
    records = load_open(OPEN, read(world), read(announcements))
    legacy = runpy.run_path(str(guard / "recheck.py"))
    physics, rankings = {}, {}
    for mode in MODES:
        rows = records[mode]
        final = read(OPEN / f"{mode}.json")
        physics[mode] = legacy["verify_physics"](rows, final, read(world))
        legacy["verify_observation_feedback"](
            rows, final, physics[mode]["receipts"], read(announcements)["announcements"])
        for row in rows:
            legacy["table"](row)
        cut = rows[3]
        view, choice = cut["policy_input"], cut["choice"]
        accepted_receipts = {}
        for target in cut["evidence"]["targets"]:
            j, tick = target["target_id"], target["last_observation_tick"]
            if tick is not None:
                accepted_receipts[j] = next(r for r in final["observations_consumed"]
                    if r["target_id"] == j and r["measurement_tick"] == tick)
        # These two in-memory maps have integer keys before JSON serialization.
        live_view = dict(view, **{k: {int(j): v for j, v in view[k].items()}
                                  for k in ("beliefs", "first_policy_visible_ticks")})
        unrestricted, constrained = locked_decision(live_view, choice, accepted_receipts)
        exact_tree(unrestricted, cut["evidence"], "/D60/unrestricted")
        selected = constrained["selected"]
        rankings[mode] = dict(
            unrestricted_selected=choice["selected_indices"], unrestricted_exact_value=choice["exact_value"],
            constrained=constrained)
        assert choice["selected_indices"] == [6] and selected["selected_indices"] == [0]
        assert len(rankings[mode]["constrained"]["original_legal_plans"]) == 13
    exact_tree(rankings["R"], rankings["S_NEW"], "/D60")
    exact_tree(physics["R"], physics["S_NEW"], "/OPEN/physics")
    mapping = IdentityMap()
    for tick, a, b in zip(TICKS, records["R"], records["S_NEW"]):
        for key in ("policy_input", "choice", "evidence"):
            exact_tree(a[key], b[key], f"/OPEN/D{tick}/{key}")
        admitted_pair(a["step"], b["step"], "step", "A2", tick,
                      (a["policy_input"], b["policy_input"]), mapping)
    exact_tree(open_before, hashes(p for p in open_paths if p.is_file()), "/OPEN/unchanged")
    exact_tree(previous["pins"], hashes(previous["pins"]), "/local/unchanged")
    assert not Path("runs/a2_value1_locked_001").exists()
    assert not Path("reports/a2_value1_locked_001_guard").exists()
    added = hashes([
        "docs/A2_VALUE1_PROTOCOL_V1.md", "research/non_oracle/a2_value_lock.py",
        "scripts/run_a2_value_locked.py", "tests/test_a2_value_lock.py", __file__,
    ])
    result = dict(
        status="PASS", head=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
        git_status=subprocess.check_output(["git","status","--short"],text=True).splitlines(),
        python=sys.version, numpy=numpy.__version__, scipy=scipy.__version__,
        science_and_inputs=previous["pins"], added_sha256=added, open_sha256=open_before,
        open_pair_identity_count=len(mapping.records), open_net=-0.7775828814863254,
        full_locked_run=False, tick60=rankings)
    (out / "PREFLIGHT.json").write_text(json.dumps(result,indent=2),encoding="utf-8")


if __name__ == "__main__":
    main()
