import unittest

import cv2
import numpy as np

from modeling_core import build_profile_extrusion, build_section_loft, calibrate_perspective_view, camera_intrinsics, compile_blender_command, fit_hypothesis, mask_diagnostics, render_silhouette, select_shape_family


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
    def test_family_competition_selects_profile_for_blade_outline(self):
        profile = hypothesis()
        profile["candidate_id"] = "profile"
        profile["views"] = [profile["views"][0]]
        profile["shape"] = {
            "family": "profile_extrusion", "scale_x": 1.0, "scale_y": 1.0, "scale_z": 1.0,
            "profile": [[-0.18, -0.9], [0.18, -0.9], [0.38, 0.15], [0.12, 0.72], [0.0, 1.12], [-0.12, 0.72], [-0.38, 0.15]],
            "depth_stations": [{"y": -0.1}, {"y": 0.1}],
        }
        profile["variables"] = [{"pointer": "/shape/scale_x", "bounds": [0.92, 1.08]}]
        vertices, faces = build_profile_extrusion(profile["shape"])
        masks = {"front": render_silhouette(vertices, faces, profile["views"][0])}
        loft = hypothesis()
        loft["candidate_id"] = "loft"
        loft["views"] = [loft["views"][0]]
        loft["variables"] = [{"pointer": "/shape/scale_x", "bounds": [0.7, 1.3]}]
        result = select_shape_family([loft, profile], masks, seed=3, maxiter=5, popsize=4)
        self.assertTrue(result["pass"])
        self.assertEqual(result["selected_candidate_id"], "profile")
        self.assertEqual(result["selected_family"], "profile_extrusion")

    def test_pnp_camera_calibration_recovers_measured_projection(self):
        points = np.asarray([
            [-0.5, -0.4, -0.7], [0.5, -0.4, -0.7], [0.5, 0.4, -0.7], [-0.5, 0.4, -0.7],
            [-0.5, -0.4, 0.7], [0.5, -0.4, 0.7], [0.5, 0.4, 0.7], [-0.5, 0.4, 0.7],
        ], dtype=float)
        rotation = np.asarray([0.12, -0.18, 0.04], dtype=float)
        translation = np.asarray([0.08, -0.06, 5.2], dtype=float)
        intrinsics = camera_intrinsics((160, 120), 48.0)
        image_points, _ = cv2.projectPoints(points, rotation, translation, intrinsics, np.zeros(5))
        result = calibrate_perspective_view(
            points,
            image_points.reshape(-1, 2),
            image_size=(160, 120),
            vertical_fov_degrees=48.0,
        )
        self.assertLess(result["max_reprojection_error_normalized"], 1e-6)
        self.assertEqual(np.asarray(result["view"]["world_to_camera"]).shape, (3, 4))

    def test_arbitrary_profile_extrusion_compiles_as_one_quad_cage(self):
        raw = hypothesis()
        raw["shape"] = {
            "family": "profile_extrusion",
            "scale_x": 1.0,
            "scale_y": 1.0,
            "scale_z": 1.0,
            "profile": [[-0.22, -1.0], [0.22, -1.0], [0.34, 0.35], [0.16, 0.78], [0.0, 1.08], [-0.16, 0.78], [-0.34, 0.35]],
            "depth_stations": [
                {"y": -0.12, "scale_x": 0.92, "scale_z": 1.0},
                {"y": 0.0, "scale_x": 1.0, "scale_z": 1.0},
                {"y": 0.12, "scale_x": 0.92, "scale_z": 1.0}
            ]
        }
        vertices, faces = build_profile_extrusion(raw["shape"])
        self.assertEqual(vertices.shape, (21, 3))
        self.assertEqual(len(faces), 14)
        command = compile_blender_command(raw, name="BladeProxy")
        self.assertEqual(command["metadata"]["source"], "modeling_core.profile_extrusion")
        self.assertTrue(all(len(face) == 4 for face in command["params"]["faces"]))
        self.assertTrue(command["metadata"]["profile_winding_normalized"])

    def test_box_cross_section_preserves_true_sharp_corners(self):
        box = hypothesis()
        box["shape"]["cross_section"] = "box"
        vertices, _faces = build_section_loft(box["shape"])
        first_ring = vertices[:12, :2]
        expected_corners = {(0.32, 0.22), (-0.32, 0.22), (-0.32, -0.22), (0.32, -0.22)}
        observed = {tuple(np.round(point, 6)) for point in first_ring}
        self.assertTrue(expected_corners.issubset(observed))

    def test_shape_translation_places_component_without_moving_shared_camera(self):
        translated = hypothesis()
        translated["shape"].update({"translate_x": 1.25, "translate_y": -0.4, "translate_z": 0.75})
        original, _ = build_section_loft(hypothesis()["shape"])
        moved, _ = build_section_loft(translated["shape"])
        expected = np.tile(np.asarray([1.25, -0.4, 0.75]), (len(original), 1))
        np.testing.assert_allclose(moved - original, expected)

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
        self.assertTrue(result["family_compatible"])

    def test_perspective_fit_recovers_declared_camera_distance(self):
        truth = hypothesis()
        truth["views"] = [truth["views"][0]]
        truth["views"][0].update({"projection": "perspective", "camera_distance": 6.2, "vertical_fov_degrees": 42.0})
        truth["variables"] = [{"pointer": "/views/0/camera_distance", "bounds": [3.5, 8.0]}]
        vertices, faces = build_section_loft(truth["shape"])
        masks = {"front": render_silhouette(vertices, faces, truth["views"][0])}
        initial = hypothesis()
        initial["views"] = [initial["views"][0]]
        initial["views"][0].update({"projection": "perspective", "camera_distance": 4.0, "vertical_fov_degrees": 42.0})
        initial["variables"] = truth["variables"]
        result = fit_hypothesis(initial, masks, seed=7, maxiter=10, popsize=6)
        self.assertLess(abs(result["hypothesis"]["views"][0]["camera_distance"] - 6.2), 0.35)
        self.assertTrue(result["family_compatible"])

    def test_enclosed_negative_space_rejects_incompatible_solid_family(self):
        source = hypothesis()
        source["views"] = [source["views"][0]]
        source["variables"] = [{"pointer": "/shape/scale_x", "bounds": [0.9, 1.1]}]
        vertices, faces = build_section_loft(source["shape"])
        reference = render_silhouette(vertices, faces, source["views"][0])
        reference[33:39, 33:39] = False
        result = fit_hypothesis(source, {"front": reference}, seed=2, maxiter=4, popsize=4)
        self.assertFalse(result["family_compatible"])
        self.assertTrue(any("negative-space" in issue for issue in result["compatibility_issues"]))
        diagnostics = mask_diagnostics(reference, render_silhouette(vertices, faces, source["views"][0]))
        self.assertEqual(diagnostics["reference_hole_count"], 1)
        self.assertEqual(diagnostics["candidate_hole_count"], 0)


if __name__ == "__main__":
    unittest.main()
