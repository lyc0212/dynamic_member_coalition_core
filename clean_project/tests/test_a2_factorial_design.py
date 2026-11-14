import copy
import json
from pathlib import Path
import unittest

from pursuit_v2.config import Config
from pursuit_v2.types import Target
from research.non_oracle.environment import StaggeredEnvironment
from scripts.gq_windows.a0_identity import exact_tree
from scripts.run_a2_value2_locked import compare_before_action, load_open


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


class FactorialDesignTests(unittest.TestCase):
    def test_crossed_worlds_have_only_the_registered_differences(self):
        a = read("configs/a2_switch_two_target_v1.json")
        b = read("configs/a2_value2_two_target_v1.json")
        for case, position, velocity in (("x1", a, b), ("x2", b, a)):
            expected = copy.deepcopy(a)
            expected["targets"][1]["position_at_birth"] = position["targets"][1]["position_at_birth"]
            expected["targets"][1]["velocity"] = velocity["targets"][1]["velocity"]
            exact_tree(read(f"configs/a2_factorial_{case}_v1.json"), expected, f"/{case}")

    def test_schema_and_no_early_announcement(self):
        ann = read("configs/a2_value2_public_announcements_v1.json")["announcements"]
        old = read("configs/a2_switch_public_announcements_v1.json")["announcements"]
        exact_tree(old, ann, "/announcements")
        env = object.__new__(StaggeredEnvironment)
        for case in ("x1", "x2"):
            world = read(f"configs/a2_factorial_{case}_v1.json")
            Config(**world["config"])
            for t in world["targets"]:
                Target(**t)
            env._validate_announcements(world, ann)
            with self.assertRaises(ValueError):
                env._validate_announcements(world, [ann[0], dict(ann[1], announcement_tick=40)])

    def test_historical_open_cannot_be_used_for_crossed_world(self):
        old = Path("runs/a2_value2_open_001")
        if not old.is_dir():
            self.skipTest("Local historical evidence is unavailable")
        ann = read("configs/a2_value2_public_announcements_v1.json")
        for case in ("x1", "x2"):
            with self.assertRaisesRegex(Exception, "/world"):
                load_open(old, read(f"configs/a2_factorial_{case}_v1.json"), ann)

    def test_reused_comparison_accepts_no_fork_and_late_fork(self):
        opened = dict(policy_input={"tick": 100}, choice={"actions": [0], "exact_value": "0"}, evidence={})
        locked = dict(opened, locked={"selected": {"actions": [0], "exact_value": "0"}, "protection": None})
        self.assertIsNone(compare_before_action(opened, locked, [], [], "R", 100))
        locked["locked"]["selected"]["actions"] = [1]
        self.assertEqual(compare_before_action(opened, locked, [], [], "R", 100)["FIRST_FORK_TICK"], 100)
