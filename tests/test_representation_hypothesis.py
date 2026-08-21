import unittest
from dataclasses import dataclass

from knowledge_engine.representation_hypothesis import (
    UNDECIDABLE_PERSPECTIVE_REASON,
    evaluate_predicted_consequence,
)


@dataclass
class FakeReferenceItem:
    projection: str


class RepresentationHypothesisTests(unittest.TestCase):
    def test_perspective_reference_is_undecidable_not_measured(self):
        consequence = {
            "view": "side_profile",
            "property": "roofline",
            "prediction_type": "boundary_linearity",
            "prediction": "linear",
        }
        result = evaluate_predicted_consequence(
            consequence,
            FakeReferenceItem(projection="PERSPECTIVE"),
            landmarks=[(0.0, 0.0), (0.5, 5.0), (1.0, 0.0)],  # a strongly curved shape
        )
        self.assertEqual(result["status"], "UNDECIDABLE")
        self.assertEqual(result["reason"], UNDECIDABLE_PERSPECTIVE_REASON)

    def test_unknown_projection_is_undecidable(self):
        consequence = {
            "view": "side_profile", "property": "roofline",
            "prediction_type": "boundary_linearity", "prediction": "linear",
        }
        result = evaluate_predicted_consequence(
            consequence, FakeReferenceItem(projection="UNKNOWN"),
            landmarks=[(0.0, 0.0), (0.5, 0.0), (1.0, 0.0)],
        )
        self.assertEqual(result["status"], "UNDECIDABLE")

    def test_orthographic_linear_prediction_confirmed_on_straight_data(self):
        consequence = {
            "view": "side_profile", "property": "roofline",
            "prediction_type": "boundary_linearity", "prediction": "linear",
        }
        # perfectly straight line from (0,0) to (1,10), with an interior point on it
        result = evaluate_predicted_consequence(
            consequence, FakeReferenceItem(projection="ORTHOGRAPHIC"),
            landmarks=[(0.0, 0.0), (0.5, 5.0), (1.0, 10.0)],
        )
        self.assertEqual(result["status"], "CONFIRMED")

    def test_orthographic_linear_prediction_contradicted_on_curved_data(self):
        consequence = {
            "view": "side_profile", "property": "roofline",
            "prediction_type": "boundary_linearity", "prediction": "linear",
        }
        # strongly bowed: interior point far from the straight-line prediction
        result = evaluate_predicted_consequence(
            consequence, FakeReferenceItem(projection="ORTHOGRAPHIC"),
            landmarks=[(0.0, 0.0), (0.5, 20.0), (1.0, 0.0)],
        )
        self.assertEqual(result["status"], "CONTRADICTED")

    def test_orthographic_curved_prediction_confirmed_on_curved_data(self):
        consequence = {
            "view": "side_profile", "property": "roofline",
            "prediction_type": "boundary_linearity", "prediction": "curved",
        }
        result = evaluate_predicted_consequence(
            consequence, FakeReferenceItem(projection="ORTHOGRAPHIC"),
            landmarks=[(0.0, 0.0), (0.5, 20.0), (1.0, 0.0)],
        )
        self.assertEqual(result["status"], "CONFIRMED")

    def test_too_few_landmarks_is_undecidable(self):
        consequence = {
            "view": "side_profile", "property": "roofline",
            "prediction_type": "boundary_linearity", "prediction": "linear",
        }
        result = evaluate_predicted_consequence(
            consequence, FakeReferenceItem(projection="ORTHOGRAPHIC"),
            landmarks=[(0.0, 0.0), (1.0, 10.0)],
        )
        self.assertEqual(result["status"], "UNDECIDABLE")

    def test_unimplemented_prediction_type_is_undecidable(self):
        consequence = {
            "view": "front", "property": "curvature",
            "prediction_type": "surface_curvature", "prediction": "convex",
        }
        result = evaluate_predicted_consequence(consequence, FakeReferenceItem(projection="ORTHOGRAPHIC"))
        self.assertEqual(result["status"], "UNDECIDABLE")

    def test_dict_reference_item_also_works(self):
        consequence = {
            "view": "side_profile", "property": "roofline",
            "prediction_type": "boundary_linearity", "prediction": "linear",
        }
        result = evaluate_predicted_consequence(
            consequence, {"projection": "PERSPECTIVE"},
            landmarks=[(0.0, 0.0), (0.5, 5.0), (1.0, 0.0)],
        )
        self.assertEqual(result["status"], "UNDECIDABLE")


if __name__ == "__main__":
    unittest.main()
