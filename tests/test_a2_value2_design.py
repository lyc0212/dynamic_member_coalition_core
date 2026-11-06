"""Static design checks for the preregistered VALUE-2 scene."""
from fractions import Fraction
from pathlib import Path
import ast
import unittest

from pursuit_v2.config import Config
from pursuit_v2.types import Target
from research.non_oracle.environment import StaggeredEnvironment
from scripts.a2_value2_design_check import analyse, first_service, next_cut, read, sha


class Value2DesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not Path("reports/a2_value2_preflight_001/HISTORICAL_PINS.json").is_file():
            raise unittest.SkipTest("Frozen local design evidence is required")
        cls.result = analyse()

    def test_schema_and_announcement_boundary(self):
        world = read("configs/a2_value2_two_target_v1.json")
        ann = read("configs/a2_value2_public_announcements_v1.json")["announcements"]
        Config(**world["config"])
        for data in world["targets"]:
            Target(**data)
        env = object.__new__(StaggeredEnvironment)
        env._validate_announcements(world, ann)
        with self.assertRaises(ValueError):
            env._validate_announcements(world,[ann[0],dict(ann[1],announcement_tick=40)])
        self.assertEqual(ann[1]["announcement_tick"],60)

    def test_frozen_positive_progress_and_real_nonzero_error(self):
        self.assertEqual(self.result["locked_t0_progress"],.6)
        self.assertEqual(self.result["locked_t0_remaining"],1.65)
        self.assertGreater(self.result["position_error"],0)
        self.assertEqual(self.result["velocity_error"],.02)

    def test_both_endpoints_and_reset(self):
        self.assertIsNone(first_service([True,False,True],1))
        self.assertIsNone(first_service([True]*21,21))
        self.assertEqual(first_service([True]*22,21),(0,21))
        self.assertEqual(first_service([True,True,False]+[True]*22,21),(3,24))

    def test_integer_windows(self):
        self.assertEqual(self.result["service_intervals"],21)
        self.assertEqual(self.result["zero_slack_tick"],99)
        self.assertEqual(self.result["minimum_slack_ticks"],4)
        self.assertEqual(self.result["first_sustainable_tick"],74)
        self.assertEqual(self.result["conditional_complete_tick"],95)
        self.assertEqual(self.result["slack_ticks"],25)
        self.assertEqual(self.result["assumed_observation_consumption_tick"],80)
        self.assertEqual(self.result["locked_release_tick"],93)
        self.assertEqual(next_cut(93,20),100)
        self.assertEqual(next_cut(80,20),80)
        self.assertEqual(self.result["locked_t1_slack_best_case"],-.05)

    def test_conditional_accounting(self):
        d = self.result["ledger"]["delta"]
        self.assertEqual(Fraction(d["completion"])+Fraction(d["terminal"]),Fraction(3,16))
        self.assertAlmostEqual(d["flow"],.0021875)
        self.assertAlmostEqual(d["late"],.001875)
        self.assertAlmostEqual(d["change"],-.02)
        self.assertAlmostEqual(sum(v for k,v in d.items() if k!="net"),d["net"])

    def test_frozen_history_and_static_entrypoint(self):
        self.assertTrue(self.result["history_unchanged"])
        self.assertEqual(self.result["episode_calls"],0)
        path = Path("scripts/a2_value2_design_check.py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)}
        self.assertEqual(imports,{"fractions","pathlib"})
        self.assertEqual(sha("configs/a2_value2_public_announcements_v1.json"),
                         sha("configs/a2_switch_public_announcements_v1.json"))


if __name__=="__main__":
    unittest.main()
