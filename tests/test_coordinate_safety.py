import unittest

from blender_ops.coordinate_safety import detect_implausible_shift


def _state(min_pt, max_pt, centroid):
    return {"local_bounds": {"min": min_pt, "max": max_pt}, "local_centroid": centroid}


class DetectImplausibleShiftTests(unittest.TestCase):
    def test_small_local_edit_is_not_flagged(self):
        before = _state([0, 0, 0], [1, 1, 1], [0.5, 0.5, 0.5])
        after = _state([0, 0, 0], [1, 1, 1.2], [0.5, 0.5, 0.6])
        result = detect_implausible_shift(before, after)
        self.assertEqual(result["status"], "EVALUATED")
        self.assertFalse(result["flagged"])

    def test_world_space_target_applied_as_local_is_flagged(self):
        # Reproduces the Swingline/donut-mug shape: a small object (diagonal
        # ~1.7) whose edit result lands tens of units away, consistent with a
        # world-space coordinate applied without converting to local space.
        before = _state([0, 0, 0], [1, 1, 1], [0.5, 0.5, 0.5])
        after = _state([0, 0, 0], [1, 1, 1], [40.0, 12.0, 3.0])
        result = detect_implausible_shift(before, after)
        self.assertEqual(result["status"], "EVALUATED")
        self.assertTrue(result["flagged"])
        self.assertIn("coordinate-frame mixup", result["reason"])

    def test_custom_threshold_is_respected(self):
        before = _state([0, 0, 0], [1, 1, 1], [0.5, 0.5, 0.5])
        after = _state([0, 0, 0], [1, 1, 1], [5.5, 0.5, 0.5])  # shift ~= 2.9x diagonal
        self.assertFalse(detect_implausible_shift(before, after, max_relative_shift=3.0)["flagged"])
        self.assertTrue(detect_implausible_shift(before, after, max_relative_shift=2.0)["flagged"])

    def test_degenerate_before_shape_is_not_flagged(self):
        before = _state([1, 1, 1], [1, 1, 1], [1, 1, 1])
        after = _state([1, 1, 1], [1, 1, 1], [50, 50, 50])
        result = detect_implausible_shift(before, after)
        self.assertFalse(result["flagged"])
        self.assertIn("degenerate", result["reason"])

    def test_missing_bounds_reports_unavailable_not_a_silent_pass(self):
        before = {"vertices": 8}
        after = _state([0, 0, 0], [1, 1, 1], [0.5, 0.5, 0.5])
        result = detect_implausible_shift(before, after)
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertFalse(result["flagged"])


if __name__ == "__main__":
    unittest.main()
