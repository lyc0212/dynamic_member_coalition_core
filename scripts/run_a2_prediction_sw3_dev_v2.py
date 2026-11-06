"""Development-only recovery using the SW3 physical admission addendum."""
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.non_oracle.sw3_physical_admissibility_v1 import sample
from scripts import run_a2_prediction_sw3_dev as dev

ROOT = Path("reports/a2_prediction_sw3_dev_002")
HEAD = "a4f29dcdd24cef3bd7b968a8bedc8973ce7e34b1"
ADDENDUM = "docs/A2_PRED_SW3_C_PHYSICAL_ADMISSIBILITY_ADDENDUM_V1.md"
FILES = (ADDENDUM, "research/non_oracle/sw3_physical_admissibility_v1.py",
         "scripts/run_a2_prediction_sw3_dev.py", "scripts/run_a2_prediction_sw3_dev_v2.py",
         "tests/test_a2_prediction_sw3_admissibility.py")


def preflight(world):
    admitted = {}
    for n in dev.FAMILIES:
        previous = []
        for w in range(4):
            draw = sample(world, "dev", n, w, previous)
            dev.save(ROOT / "admission" / f"family_{n}_world_{w}.json", draw)
            if draw["status"] != "ACCEPTED":
                raise ValueError(f"Admission exhausted for {n}/{w}")
            admitted[n, w] = draw
            previous.append(draw["world"])
    return admitted


def main():
    if subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != HEAD:
        raise ValueError("Unexpected baseline HEAD")
    c1 = Path("reports/a2_prediction_sw3_c1_001")
    pins = dev.read(c1 / "SOURCE_PINS.json")["pins"] | dev.read(c1 / "SHA256.json")
    for folder in (c1, Path("reports/a2_prediction_sw3_dev_001")):
        tracked = set(subprocess.check_output(
            ["git", "ls-files", "--", folder.as_posix()], text=True).splitlines())
        for file in folder.rglob("*"):
            if file.is_file():
                key = file.as_posix()
                if key in tracked:
                    expected = subprocess.check_output(["git", "show", f"HEAD:{key}"])
                    if file.read_bytes() != expected:
                        raise ValueError(f"Historical evidence changed: {file}")
                    tracked.remove(key)
                pins.setdefault(key, dev.sha(file))
        if tracked:
            raise ValueError(f"Missing historical files: {sorted(tracked)}")
    if not all(dev.sha(p) == h for p, h in pins.items()):
        raise ValueError("Frozen input changed")
    pins.update({p: dev.sha(p) for p in FILES})
    if tuple(r["n"] for r in dev.manifest() if r["split"] == "dev") != dev.FAMILIES:
        raise ValueError("Frozen DEV split changed")
    ROOT.mkdir(exist_ok=False)
    dev.save(ROOT / "SOURCE_PINS.json", dict(head=HEAD, pins=pins))
    family = None
    stage = "ADMISSION"
    try:
        world = dev.read("configs/a2_value2_two_target_v1.json")
        ann = dev.read("configs/a2_value2_public_announcements_v1.json")
        admitted = preflight(world)
        dev.save(ROOT / "ADMISSION_PASS.json", {
            f"{n}/{w}": dev.sha(ROOT / "admission" / f"family_{n}_world_{w}.json")
            for n, w in admitted})

        def prepare(n, path, template, announcements):
            def frozen_sample(_template, split, family, w, previous):
                if split != "dev" or family != n or len(previous) != w:
                    raise ValueError("Unexpected DEV admission request")
                return admitted[family, w]
            return dev.prepare_family(n, path, template, announcements, sample=frozen_sample)

        stage = "DEV"
        results = {}
        for family in dev.FAMILIES:
            print(f"DEV family {family}", flush=True)
            results[str(family)] = dev.run_family(family, ROOT / f"family_{family}", world, ann, prepare=prepare)
        dev.save(ROOT / "DEV_METRICS.json", results)
        if not all(dev.sha(p) == h for p, h in pins.items()):
            raise ValueError("Frozen files changed during DEV")
    except Exception as error:
        dev.save(ROOT / "FAILURE.json", dict(status="SW3_DEV_BLOCKED", stage=stage,
                                            family=family, error=repr(error)))
        raise


if __name__ == "__main__":
    main()
