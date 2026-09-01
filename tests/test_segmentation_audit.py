import unittest

import numpy as np

from knowledge_engine.segmentation_audit import audit_segmentation_mask


class SegmentationAuditTests(unittest.TestCase):
    def test_valid_ring_preserves_expected_negative_space(self):
        mask = np.zeros((64, 64), dtype=bool)
        mask[10:54, 10:54] = True
        mask[24:40, 24:40] = False
        result = audit_segmentation_mask(mask, expected_hole_range=(1, 1))
        self.assertTrue(result["pass"])
        self.assertEqual(result["enclosed_negative_space_count"], 1)

    def test_morphologically_closed_hole_fails_expectation(self):
        mask = np.zeros((64, 64), dtype=bool)
        mask[10:54, 10:54] = True
        result = audit_segmentation_mask(mask, expected_hole_range=(1, 1))
        self.assertFalse(result["pass"])
        self.assertIn("negative-space", result["issues"][0])

    def test_full_canvas_polarity_and_border_touch_fail(self):
        result = audit_segmentation_mask(np.ones((32, 32), dtype=bool))
        self.assertFalse(result["pass"])
        self.assertGreaterEqual(len(result["issues"]), 2)

    def test_disconnected_mask_requires_declared_component_range(self):
        mask = np.zeros((64, 64), dtype=bool)
        mask[10:20, 10:20] = True
        mask[40:50, 40:50] = True
        self.assertFalse(audit_segmentation_mask(mask)["pass"])
        self.assertTrue(audit_segmentation_mask(mask, expected_component_range=(2, 2))["pass"])


if __name__ == "__main__":
    unittest.main()
