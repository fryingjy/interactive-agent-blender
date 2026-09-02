import unittest

import numpy as np

from modeling_core import build_section_loft, compile_blender_command, fit_hypothesis, render_silhouette


def hypothesis(scale_x=1.0, scale_y=1.0):
    return {
        "schema_version": 1,
        "shape": {
            "family": "section_loft",
            "segments": 12,
            "scale_x": scale_x,
            "scale_y": scale_y,
            "scale_z": 1.0,
            "stations": [
                {"z": -0.8, "half_width": 0.32, "half_depth": 0.22, "power": 4.0},
                {"z": 0.0, "half_width": 0.42, "half_depth": 0.28, "power": 4.0},
                {"z": 0.8, "half_width": 0.25, "half_depth": 0.18, "power": 4.0},
            ],
        },
        "views": [
            {"id": "front", "projection": "orthographic", "image_size": [72, 72], "yaw_degrees": 0, "pitch_degrees": 0, "roll_degrees": 0, "world_scale": 2.2, "offset_x": 0, "offset_y": 0},
            {"id": "side", "projection": "orthographic", "image_size": [72, 72], "yaw_degrees": 90, "pitch_degrees": 0, "roll_degrees": 0, "world_scale": 2.2, "offset_x": 0, "offset_y": 0},
        ],
        "variables": [
            {"pointer": "/shape/scale_x", "bounds": [0.65, 1.45]},
            {"pointer": "/shape/scale_y", "bounds": [0.55, 1.25]},
        ],
    }


class ModelingCoreTests(unittest.TestCase):
    def test_box_cross_section_preserves_true_sharp_corners(self):
        box = hypothesis()
        box["shape"]["cross_section"] = "box"
        vertices, _faces = build_section_loft(box["shape"])
        first_ring = vertices[:12, :2]
        expected_corners = {(0.32, 0.22), (-0.32, 0.22), (-0.32, -0.22), (0.32, -0.22)}
        observed = {tuple(np.round(point, 6)) for point in first_ring}
        self.assertTrue(expected_corners.issubset(observed))

    def test_compiler_emits_one_connected_all_quad_cage(self):
        command = compile_blender_command(hypothesis(), name="Recovered")
        self.assertEqual(command["command"], "create_authored_quad_mesh")
        self.assertEqual(len(command["params"]["vertices"]), 36)
        self.assertEqual(len(command["params"]["faces"]), 24)
        self.assertTrue(all(len(face) == 4 for face in command["params"]["faces"]))
        self.assertFalse(command["metadata"]["modifiers_applied"])

    def test_multiview_fit_recovers_independent_width_and_depth(self):
        truth = hypothesis(scale_x=1.28, scale_y=0.72)
        vertices, faces = build_section_loft(truth["shape"])
        masks = {view["id"]: render_silhouette(vertices, faces, view) for view in truth["views"]}
        result = fit_hypothesis(hypothesis(), masks, seed=4, maxiter=12, popsize=6)
        fitted = result["hypothesis"]["shape"]
        self.assertLess(abs(fitted["scale_x"] - 1.28), 0.08)
        self.assertLess(abs(fitted["scale_y"] - 0.72), 0.08)
        self.assertLess(result["mean_view_loss"], 0.08)
        self.assertTrue(result["fit"]["retain_candidate"])


if __name__ == "__main__":
    unittest.main()
