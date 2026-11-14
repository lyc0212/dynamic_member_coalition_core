"""A2-VALUE-1 locked episode. Run only after separate VALUE-1E authorization."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.non_oracle.a2_value_lock import locked_decision
from research.non_oracle.environment import StaggeredEnvironment
from research.non_oracle.policy import decide
from scripts.gq_windows.a0_compare import admitted_pair, get_pointer, strict_pair
from scripts.gq_windows.a0_identity import IdentityMap, digest, exact_tree
from scripts.run_a1 import Sensing

OPEN = Path("runs/a2_switch_episode_001")
WORLD_SHA = "b23661dcb927f814dadc033df37d2aa142a63960ddf4cb60083041c56f3a37b6"
ANN_SHA = "80853bbd59c1f06b1864819a98c9fae7090cbca99bbedfc9ab9198d07b5daed0"
MODES = ("R", "S_NEW")
TICKS = tuple(range(0, 120, 20))


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_open(root, world, announcements):
    exact_tree(read(root / "WORLD_INPUT.json"), world, "/world")
    exact_tree(read(root / "PUBLIC_INPUT.json"), announcements, "/announcements")
    if read(root / "PAIR_CHECK.json")["status"] != "PASS":
        raise ValueError("OPEN pair did not pass")
    records = {}
    for mode in MODES:
        saved = read(root / f"{mode}.json")
        rows = [read(root / f"{mode}_D{tick}.json") for tick in TICKS]
        exact_tree(rows, saved["records"], f"/{mode}/records")
        for tick, row in zip(TICKS, rows):
            step = row["step"]
            if (row["policy_input"]["tick"], step["start_tick"], step["end_tick"], step["status"]) != (tick, tick, tick+20, "COMMITTED"):
                raise ValueError("OPEN incomplete decision")
        final = saved["final"]["state"]
        if not (rows[-1]["step"]["checkpoint_after"]["phase"] == "TERMINAL"
                and final["tick"] == 120 and final["terminal_settled"]
                and saved["metrics"]["return_with_changes"] == -0.7775828814863254):
            raise ValueError("OPEN terminal settlement missing or changed")
        records[mode] = rows
    return records


def compare_cut(open_row, locked_row, mode, tick):
    for field in ("policy_input", "choice", "evidence"):
        exact_tree(open_row[field], locked_row[field], f"/{mode}/D{tick}/{field}")


def compare_prefork_step(open_step, locked_step, mode, tick):
    """Admit only the fixed STEP paths and the exact run-name substitution."""
    context = {"pending": []}
    strict_pair(open_step, locked_step, "step", context=context)
    old_id, new_id = "A2_" + mode, "A2_VALUE1_LOCKED_" + mode
    for kind, path, old, new in context["pending"]:
        if kind == "frame_digest":
            source = path.rsplit("/", 1)[0] + "/normalized_frame"
            valid = (old == digest(get_pointer(open_step, source))
                     and new == digest(get_pointer(locked_step, source)))
        elif kind in ("work", "environment"):
            valid = (old, new) == (old_id, new_id)
        else:
            valid = (kind in ("stream", "frame", "packet") and old.startswith(old_id + ":")
                     and new == new_id + old[len(old_id):])
        if not valid:
            raise ValueError(f"Unexpected pre-fork identity at /{mode}/D{tick}/step{path}")
    return len(context["pending"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("world", "announcements", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    for path, sha in ((args.world, WORLD_SHA), (args.announcements, ANN_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValueError(f"Frozen SHA256 mismatch: {path}")
    world, announcements = read(args.world), read(args.announcements)
    opened = load_open(OPEN, world, announcements)
    args.output.mkdir(parents=True, exist_ok=False)

    def save(name, value):
        path = args.output / (name + ".json")
        with path.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        return path

    save("WORLD_INPUT", world)
    save("PUBLIC_INPUT", announcements)
    runs = {}
    finals = {}
    prefork = {}
    for mode in MODES:
        open_consumed = read(OPEN / f"{mode}.json")["observations_consumed"]
        env = StaggeredEnvironment(world, Sensing(), "A2_VALUE1_LOCKED_" + mode,
                                   announcements["announcements"])
        records = []
        for index, tick in enumerate(TICKS):
            view = env.prepare_decision()
            if view["tick"] != tick:
                raise ValueError("Unexpected decision tick")
            choice = decide(view, mode)
            evidence, locked = locked_decision(view, choice, env.beliefs.accepted_receipts)
            row = dict(policy_input=view, choice=choice, evidence=evidence, locked=locked)
            decision_path = save(f"{mode}_D{tick}_DECISION", row)
            if tick <= 60:
                compare_cut(opened[mode][index], read(decision_path), mode, tick)
                exact_tree([r for r in open_consumed if r["consumed_tick"] <= tick],
                           env.beliefs.consumed, f"/{mode}/D{tick}/observations_consumed")
                expected = [0] if tick == 60 else choice["selected_indices"]
                if locked["selected"]["selected_indices"] != expected or (tick == 60 and choice["selected_indices"] != [6]):
                    raise ValueError("Unexpected pre-fork/fork selection")
            result = env.step(locked["selected"]["actions"], env.observe_public()["checkpoint_id"],
                              tick, f"{mode}_D{tick}")
            row["step"] = result
            row = read(save(f"{mode}_D{tick}", row))
            if result["status"] != "COMMITTED":
                raise ValueError(f"{mode} D{tick} not committed")
            if tick < 60:
                prefork[f"{mode}/D{tick}"] = compare_prefork_step(
                    opened[mode][index]["step"], row["step"], mode, tick)
            records.append(row)
        if not env.done or env.tick != 120 or records[-1]["step"]["checkpoint_after"]["phase"] != "TERMINAL":
            raise ValueError("LOCKED did not reach terminal tick")
        runs[mode] = records
        finals[mode] = dict(metrics=env.metrics(), observations_consumed=env.beliefs.consumed,
                            final=env.private_snapshot())
        save(mode, dict(records=records, **finals[mode]))
    mapping = IdentityMap()
    for tick, a, b in zip(TICKS, runs["R"], runs["S_NEW"]):
        for field in ("policy_input", "choice", "evidence", "locked"):
            exact_tree(a[field], b[field], f"/D{tick}/{field}")
        admitted_pair(a["step"], b["step"], "step", "A2_VALUE1_LOCKED", tick,
                      (a["policy_input"], b["policy_input"]), mapping)
    for field in ("metrics", "observations_consumed"):
        exact_tree(finals["R"][field], finals["S_NEW"][field], "/" + field)
    save("PRE_FORK_CHECK", dict(status="PASS", identity_path_counts=prefork))
    save("PAIR_CHECK", dict(status="PASS", mappings=mapping.records))
    save("SUMMARY", dict(status="EXECUTION_COMPLETE_NOT_SCIENTIFIC_ACCEPTANCE",
                         decision_count=len(TICKS)))


if __name__ == "__main__":
    main()
