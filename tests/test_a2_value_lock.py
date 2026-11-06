import copy
import json
from types import SimpleNamespace
import unittest

from pursuit_v2.types import Assignment
from research.non_oracle.a2_value_lock import audit_selection, protected_team, select
from research.quality_allocation.certified_solver import solve
from scripts.run_a2_value_locked import OPEN, compare_cut, compare_prefork_step, load_open


def read(name):
    return json.loads((OPEN / (name + ".json")).read_bytes())


class ValueLockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (OPEN / "R_D60.json").is_file():
            raise unittest.SkipTest("Local frozen A2-S2 OPEN evidence is required")
        cls.r = read("R_D60")
        cls.s = read("S_NEW_D60")

    def setUp(self):
        self.view = copy.deepcopy(self.r["policy_input"])
        self.choice = copy.deepcopy(self.r["choice"])
        self.clock = self.view["histories"][0]["segments"][0]["latest_clock"]

    def test_exact_frozen_plan_and_all_exclusions(self):
        lock = protected_team(self.view)
        self.assertAlmostEqual(lock["progress"], .6)
        chosen = select(self.view, self.choice, lock)
        self.assertEqual(chosen["selected_indices"], [0])
        self.assertEqual(chosen["exact_value"], "-354669055230257/1125899906842624")
        self.assertEqual(self.choice, self.r["choice"])
        self.assertEqual(self.choice, self.s["choice"])
        self.assertEqual(self.choice["selected_indices"], [6])
        self.assertEqual(self.choice["exact_value"], "-41523928784916923/288230376151711744")
        evidence = audit_selection(self.view, self.choice, lock, chosen)
        self.assertEqual(len(evidence["original_legal_plans"]), 13)
        self.assertEqual(evidence["feasible_ranking"], [[0]])
        self.assertEqual(chosen["actions"][2], {"target": None, "role": "none"})
        for plan in evidence["original_legal_plans"]:
            with self.subTest(plan=plan["selected"]):
                self.assertEqual(plan["lock_feasible"], plan["selected"] == [0])

    def test_zero_then_recovered(self):
        self.clock["intervals"] = 0
        self.assertIsNone(protected_team(self.view))
        self.clock["intervals"] = 1
        self.assertAlmostEqual(protected_team(self.view)["progress"], .05)

    def test_invalid_clock(self):
        for field, value in (("base", -1), ("base", float("nan")), ("base", float("inf")),
                             ("intervals", -1), ("intervals", 1.5), ("intervals", True), ("intervals", 61)):
            with self.subTest(field=field, value=value):
                self.clock.update(base=0., intervals=12)
                self.clock[field] = value
                with self.assertRaisesRegex(ValueError, "clock"):
                    protected_team(self.view)

    def test_mismatched_role_team_and_inactive_release(self):
        self.view["assignment"][0]["role"] = "dual_pos45"
        with self.assertRaisesRegex(ValueError, "teams differ"):
            protected_team(self.view)
        self.view["targets"].pop(0)
        self.view["assignment"] = [{"target": None, "role": "none"} for _ in range(3)]
        self.assertIsNone(protected_team(self.view))

    def test_missing_active_segment_with_assignment(self):
        self.view["histories"][0]["active_segment_id"] = None
        with self.assertRaisesRegex(ValueError, "without active"):
            protected_team(self.view)

    def test_nonpositive_keep_retained(self):
        keep = self.choice["rows"][0]
        keep["absolute_O"] = keep["baseline"] - 10.
        keep["v"] = float(keep["absolute_O"] - keep["baseline"])
        lock = protected_team(self.view)
        selected = select(self.view, self.choice, lock)
        self.assertEqual(audit_selection(self.view, self.choice, lock, selected)["feasible_ranking"], [[0]])

    def test_no_lock_native_tie(self):
        self.clock["intervals"] = 0
        self.view["assignment"] = [{"target": None, "role": "none"} for _ in range(3)]
        self.view["histories"][0]["active_segment_id"] = None
        rows = self.choice["rows"]
        for row in rows:
            row.update(absolute_O=1., baseline=0., v=1.)
        specs = [SimpleNamespace(**row["key"], index=i, mask=sum(1 << r for r in row["key"]["robots"]))
                 for i, row in enumerate(rows)]
        obs = SimpleNamespace(assignment=tuple(Assignment(**a) for a in self.view["assignment"]),
                              config=SimpleNamespace(change_cost=self.view["config"]["change_cost"]))
        chosen, _ = solve(obs, specs, [1.] * len(rows))
        self.assertEqual(chosen, (0,))
        self.choice.update(selected_indices=[0], actions=self.r["policy_input"]["assignment"],
                           exact_value="282465768628677509/288230376151711744")
        selected = select(self.view, self.choice, protected_team(self.view))
        self.assertEqual(selected["selected_indices"], [0])
        audit_selection(self.view, self.choice, None, selected)
        with self.assertRaises(ValueError):
            audit_selection(self.view, self.choice, None, dict(selected, selected_indices=[1]))

    def test_lock_uses_no_world_or_prediction_fields(self):
        expected = protected_team(self.view)
        self.view.pop("beliefs")
        self.view.pop("current_slots")
        self.assertEqual(protected_team(self.view), expected)

    def test_open_inventory_and_scientific_rejections(self):
        runs = load_open(OPEN, read("WORLD_INPUT"), read("PUBLIC_INPUT"))
        self.assertEqual(len(runs["S_NEW"]), 6)
        compare_cut(self.r, self.s, "R", 60)
        for field in ("beliefs", "assignment"):
            modified = copy.deepcopy(self.r)
            modified["policy_input"].pop(field)
            with self.assertRaisesRegex(Exception, field):
                compare_cut(self.r, modified, "R", 60)
        modified = copy.deepcopy(self.r)
        modified["choice"]["rows"][0]["v"] += .125
        with self.assertRaisesRegex(Exception, "/choice/rows/0/v"):
            compare_cut(self.r, modified, "R", 60)
        for field in ("control", "progress"):
            step = copy.deepcopy(self.r["step"])
            step["frames"][0][field] = []
            with self.assertRaisesRegex(Exception, field):
                compare_prefork_step(self.r["step"], step, "R", 60)

    def test_narrow_identity_admission(self):
        before = {"fusion_records": [{"context": {"work_instance_id": "A2_R"}}]}
        after = {"fusion_records": [{"context": {"work_instance_id": "A2_VALUE1_LOCKED_R"}}]}
        self.assertEqual(compare_prefork_step(before, after, "R", 0), 1)
        after["fusion_records"][0]["context"]["work_instance_id"] = "foreign"
        with self.assertRaisesRegex(ValueError, "/fusion_records/0/context/work_instance_id"):
            compare_prefork_step(before, after, "R", 0)
