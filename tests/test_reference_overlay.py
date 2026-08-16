import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from knowledge_engine.reference_overlay import (
    align_candidate,
    compare_reference_render,
    contour_error_pixels,
    foreground_mask,
    overlay_pixels,
)


class ReferenceOverlayTests(unittest.TestCase):
    def test_strict_alignment_preserves_placement_error(self):
        reference = np.zeros((32, 32), dtype=bool)
        candidate = np.zeros((32, 32), dtype=bool)
        reference[8:24, 8:20] = True
        candidate[8:24, 12:24] = True
        aligned, record = align_candidate(reference, candidate, "strict")
        self.assertTrue(np.array_equal(aligned, candidate))
        self.assertEqual(record["normalization"], "none")

    def test_bbox_alignment_is_explicit_and_matches_scaled_rectangle(self):
        reference = np.zeros((40, 50), dtype=bool)
        candidate = np.zeros((20, 25), dtype=bool)
        reference[10:30, 15:35] = True
        candidate[3:13, 4:14] = True
        aligned, record = align_candidate(reference, candidate, "bbox")
        self.assertTrue(np.array_equal(aligned, reference))
        self.assertEqual(record["mode"], "bbox")
        self.assertIn("Translation", record["claim_boundary"])

    def test_uniform_bbox_preserves_aspect_ratio(self):
        reference = np.zeros((60, 80), dtype=bool)
        candidate = np.zeros((30, 30), dtype=bool)
        reference[10:50, 10:70] = True
        candidate[5:25, 10:20] = True
        aligned, record = align_candidate(reference, candidate, "uniform-bbox")
        ys, xs = np.nonzero(aligned)
        width = int(xs.max() - xs.min() + 1)
        height = int(ys.max() - ys.min() + 1)
        self.assertEqual(width / height, 0.5)
        self.assertEqual(record["mode"], "uniform-bbox")
        self.assertIn("aspect ratio", record["claim_boundary"])

    def test_mask_modes_and_saved_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference = np.full((32, 32, 3), 255, dtype=np.uint8)
            reference[8:24, 10:22] = 30
            candidate = np.zeros((32, 32, 4), dtype=np.uint8)
            candidate[8:24, 12:24, :3] = 255
            candidate[8:24, 12:24, 3] = 255
            ref_path = root / "reference.png"
            cand_path = root / "candidate.png"
            Image.fromarray(reference, "RGB").save(ref_path)
            Image.fromarray(candidate, "RGBA").save(cand_path)
            self.assertEqual(int(foreground_mask(ref_path, mode="light-background").sum()), 192)
            report, images = compare_reference_render(
                ref_path,
                cand_path,
                alignment="strict",
                reference_mask_mode="light-background",
                candidate_mask_mode="alpha",
                view="front",
            )
            self.assertLess(report["metrics"]["silhouette_iou"], 1.0)
            self.assertEqual(report["view"], "front")
            self.assertTrue(report["tickets"])
            self.assertEqual(images["overlay"].shape, (32, 32, 3))
            self.assertEqual(images["contour_error_heatmap"].shape, (32, 32, 3))

    def test_overlay_and_heatmap_reject_shape_mismatch(self):
        reference = np.zeros((16, 16), dtype=bool)
        candidate = np.zeros((16, 16), dtype=bool)
        reference[3:10, 3:10] = True
        candidate[5:12, 5:12] = True
        self.assertGreater(int(overlay_pixels(reference, candidate).sum()), 0)
        self.assertGreater(int(contour_error_pixels(reference, candidate).sum()), 0)

    def test_luminance_range_and_roi_isolate_component(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "component.png"
            pixels = np.full((20, 20, 3), 255, dtype=np.uint8)
            pixels[4:16, 4:16] = 40
            pixels[7:13, 7:13] = 180
            Image.fromarray(pixels, "RGB").save(path)
            mask = foreground_mask(path, mode="luminance-range", luminance_min=120, luminance_max=230)
            self.assertEqual(int(mask.sum()), 36)


if __name__ == "__main__":
    unittest.main()
