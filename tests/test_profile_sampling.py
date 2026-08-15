import unittest

import numpy as np

from knowledge_engine.profile_sampling import (
    adaptive_profile_positions,
    profile_width_at,
    smooth_profile_widths,
)


def rows(widths):
    return [
        {"y_norm_top_to_bottom": float(index / (len(widths) - 1)), "width_norm": float(width)}
        for index, width in enumerate(widths)
    ]


class ProfileSamplingTests(unittest.TestCase):
    def test_adaptive_positions_are_bounded_ordered_and_exact_count(self):
        profile = rows(0.4 + 0.2 * np.sin(np.linspace(0, 4 * np.pi, 301)))
        positions = adaptive_profile_positions(profile, 37)
        self.assertEqual(len(positions), 37)
        self.assertEqual(positions[0], 0.0)
        self.assertEqual(positions[-1], 1.0)
        self.assertTrue(all(left < right for left, right in zip(positions, positions[1:])))

    def test_curved_region_receives_more_samples_than_flat_region(self):
        x = np.linspace(0, 1, 501)
        widths = np.where(x < 0.55, 0.4, 0.4 + 0.18 * np.sin((x - 0.55) * 7 * np.pi))
        positions = adaptive_profile_positions(rows(widths), 45)
        curved = sum(position >= 0.55 for position in positions)
        self.assertGreater(curved, len(positions) * 0.55)

    def test_smoothing_reduces_single_row_segmentation_spike(self):
        widths = np.full(101, 0.5)
        widths[50] = 1.0
        _, smoothed = smooth_profile_widths(rows(widths), window=9)
        self.assertLess(smoothed[50], 0.6)

    def test_width_lookup_interpolates_denoised_measurement(self):
        profile = rows(np.linspace(0.2, 0.8, 101))
        self.assertAlmostEqual(profile_width_at(profile, 0.5), 0.5, places=3)

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            adaptive_profile_positions(rows([0.2, 0.3, 0.4]), 4)
        with self.assertRaises(ValueError):
            adaptive_profile_positions(rows(np.linspace(0.2, 0.8, 20)), 3)
        with self.assertRaises(ValueError):
            profile_width_at(rows(np.linspace(0.2, 0.8, 20)), 1.1)


if __name__ == "__main__":
    unittest.main()
