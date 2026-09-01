import unittest

from knowledge_engine.reference_registration import (
    evaluate_reference_registration,
    landmark_registration_error,
)


class ReferenceRegistrationTests(unittest.TestCase):
    def test_uncalibrated_perspective_cannot_authorize_geometry(self):
        gate = evaluate_reference_registration({
            "schema_version": 1,
            "target_id": "prop",
            "views": [{
                "view_id": "hero",
                "classification": "UNCALIBRATED_PERSPECTIVE_STYLE_ONLY",
                "alignment_mode": "LANDMARK_SIMILARITY",
                "requested_geometry_claims": ["body width"],
            }],
        })
        self.assertFalse(gate["pass"])
        self.assertIn("style-only", gate["issues"][0])

    def test_calibrated_perspective_requires_low_reprojection_error(self):
        base = {
            "schema_version": 1,
            "target_id": "prop",
            "views": [{
                "view_id": "hero",
                "classification": "CALIBRATED_PERSPECTIVE",
                "alignment_mode": "CAMERA_SOLUTION",
                "requested_geometry_claims": ["body width"],
                "camera_solution": {"control_point_count": 6, "reprojection_error_normalized": 0.03},
            }],
        }
        self.assertFalse(evaluate_reference_registration(base)["pass"])
        base["views"][0]["camera_solution"]["reprojection_error_normalized"] = 0.01
        self.assertTrue(evaluate_reference_registration(base)["pass"])

    def test_orthographic_view_requires_projection_evidence(self):
        record = {
            "schema_version": 1,
            "views": [{
                "view_id": "front",
                "classification": "ORTHOGRAPHIC_OR_NEAR_ORTHOGRAPHIC",
                "alignment_mode": "STRICT_FRAME",
                "requested_geometry_claims": ["front silhouette"],
            }],
        }
        self.assertFalse(evaluate_reference_registration(record)["pass"])
        record["views"][0]["projection_evidence"] = "manufacturer elevation drawing"
        self.assertTrue(evaluate_reference_registration(record)["pass"])

    def test_landmark_residuals_are_normalized(self):
        report = landmark_registration_error([
            {"reference": [10, 10], "candidate": [10, 10]},
            {"reference": [90, 90], "candidate": [80, 90]},
        ], (100, 100))
        self.assertAlmostEqual(report["mean_error_normalized"], 0.05)
        self.assertAlmostEqual(report["max_error_normalized"], 0.1)


if __name__ == "__main__":
    unittest.main()
