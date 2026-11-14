from copy import deepcopy
from unittest import TestCase

from scripts.run_a2_prediction_sw3_test import difference, normalize


class IsolationCompareTests(TestCase):
    def test_only_registered_timings_are_ignored(self):
        timing = {"wall": 1.0, "cpu": 2.0}
        value = dict(end_to_end=dict(timing), selection=dict(validation_timing=dict(timing),
                     screening_timing=dict(timing)), prediction=dict(cost=dict(timing, wls=41),
                     results=[dict(cost=dict(timing), science={"wall": 3.0})]))
        actual = deepcopy(value)
        actual["prediction"]["results"][0]["cost"]["wall"] = 4.0
        self.assertIsNone(difference(normalize(value), normalize(actual)))
        actual["prediction"]["results"][0]["science"]["wall"] = 4.0
        self.assertEqual(difference(normalize(value), normalize(actual)), dict(
            path="/prediction/results/0/science/wall", reference=3.0, restricted=4.0))
        self.assertEqual(difference({"wls": 41}, {"wls": 41.0})["path"], "/wls")
