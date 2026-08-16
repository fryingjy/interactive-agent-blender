import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from knowledge_engine.component_mask_observations import extract_component_mask_observations


class ComponentMaskObservationTests(unittest.TestCase):
    def test_extracts_normalized_boxes_from_stable_palette(self):
        with tempfile.TemporaryDirectory() as directory:
            pixels = np.zeros((20, 30, 4), dtype=np.uint8)
            pixels[3:17, 4:26, 3] = 255  # combined foreground frame
            pixels[4:10, 5:15, :3] = (255, 26, 26)  # red / housing
            pixels[11:16, 16:24, :3] = (26, 255, 26)  # green / handle
            path = Path(directory) / "mask.png"
            Image.fromarray(pixels, "RGBA").save(path)
            report = extract_component_mask_observations(path, ["housing", "handle"])
        self.assertEqual(report["missing_component_ids"], [])
        self.assertEqual(report["normalization_frame_bbox_px"], {"left": 4, "top": 3, "right": 25, "bottom": 16})
        self.assertEqual(report["observations"]["housing"]["left"], round(1 / 21, 6))
        self.assertEqual(report["observations"]["handle"]["bottom"], round(12 / 13, 6))

    def test_missing_component_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            pixels = np.zeros((5, 5, 4), dtype=np.uint8)
            pixels[1:4, 1:4, :3] = (255, 26, 26)
            pixels[1:4, 1:4, 3] = 255
            path = Path(directory) / "mask.png"
            Image.fromarray(pixels, "RGBA").save(path)
            report = extract_component_mask_observations(path, ["housing", "handle"])
        self.assertEqual(report["missing_component_ids"], ["handle"])

    def test_rejects_ambiguous_repeating_palette_request(self):
        with self.assertRaisesRegex(ValueError, "one and four"):
            extract_component_mask_observations("unused.png", ["a", "b", "c", "d", "e"])


if __name__ == "__main__":
    unittest.main()
