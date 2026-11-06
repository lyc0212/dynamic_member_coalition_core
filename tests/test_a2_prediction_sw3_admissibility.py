from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch

from research.non_oracle import sw3_physical_admissibility_v1 as admission
from research.non_oracle.sw3_c1_private_worlds import private_world
from scripts.run_a2_prediction_sw3_dev import FAMILIES, read


class AdmissibilityTests(TestCase):
    def setUp(self):
        self.template = read("configs/a2_value2_two_target_v1.json")

    def test_first_rejection_and_next_hash(self):
        old = private_world(self.template, "dev", 11, 0, [])
        with self.assertRaisesRegex(ValueError, "eastward envelope"):
            admission.construct(old["world"])
        new = admission.sample(self.template, "dev", 11, 0, [])
        first = new["attempts"][0]
        self.assertEqual(first["draws"], old["attempts"][0]["draws"])
        self.assertEqual(first["rejection"], "HEADING_OUT_OF_PHYSICAL_ENVELOPE")
        self.assertEqual([r["a"] for r in new["attempts"]], list(range(new["accepted_a"] + 1)))
        self.assertEqual(new["attempts"][1]["draws"][0],
                         admission.draw_component("dev", 11, 0, 1, 0))
        self.assertNotEqual(first["draws"], new["attempts"][1]["draws"])

    def test_twelve_constructible_distinct_worlds(self):
        for family in FAMILIES:
            previous = []
            for w in range(4):
                result = admission.sample(self.template, "dev", family, w, previous)
                self.assertEqual(result["status"], "ACCEPTED")
                self.assertLessEqual(len(result["attempts"]), 32)
                world = result["world"]
                self.assertNotIn(world, previous)
                admission.construct(world)
                previous.append(world)

    def test_exhaustion_and_duplicate(self):
        with patch.object(admission, "reject_motion", return_value="DUPLICATE"):
            result = admission.sample(self.template, "dev", 11, 0, [])
        self.assertEqual(result["status"], "EXHAUSTED")
        self.assertEqual([r["a"] for r in result["attempts"]], list(range(32)))
        first = admission.sample(self.template, "dev", 11, 0, [])
        draws = first["attempts"][-1]["draws"]
        with patch.object(admission, "draw_component", side_effect=lambda s, n, w, a, j, **kw: draws[j]):
            result = admission.sample(self.template, "dev", 11, 1, [first["world"]])
        self.assertTrue(all(r["rejection"] == "DUPLICATE" for r in result["attempts"]))

    def test_fixed_and_unknown_errors_propagate(self):
        bad = deepcopy(self.template)
        bad["positions_initial"] = []
        with self.assertRaisesRegex(ValueError, "independent positions"):
            admission.sample(bad, "dev", 11, 0, [])
        with patch.object(admission, "construct", side_effect=[None, RuntimeError("unknown")]):
            with self.assertRaisesRegex(RuntimeError, "unknown"):
                admission.sample(self.template, "dev", 11, 0, [])
