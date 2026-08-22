import unittest

from knowledge_engine.representation_hypothesis import rank_competing_hypotheses


class CompetingRepresentationHypothesisTests(unittest.TestCase):
    def setUp(self):
        self.references = {
            "side": {"reference_id": "side", "projection": "ORTHOGRAPHIC"},
            "top": {"reference_id": "top", "projection": "ORTHOGRAPHIC"},
        }
        self.observations = {
            "height": {
                "reference_id": "side", "view": "side", "property": "total_height",
                "value": {"min": 49.2, "max": 50.5}, "unit": "mm",
            },
            "diameter": {
                "reference_id": "top", "view": "top", "property": "body_diameter",
                "value": {"min": 13.5, "max": 14.5}, "unit": "mm",
            },
        }

    def candidate(self, name, height_range, diameter_range=(13.5, 14.5)):
        return {
            "name": name,
            "representation": name,
            "predicted_consequences": [
                {
                    "reference_id": "side", "observation_id": "height", "view": "side",
                    "property": "total_height", "prediction_type": "numeric_range",
                    "prediction": {"min": height_range[0], "max": height_range[1]},
                },
                {
                    "reference_id": "top", "observation_id": "diameter", "view": "top",
                    "property": "body_diameter", "prediction_type": "numeric_range",
                    "prediction": {"min": diameter_range[0], "max": diameter_range[1]},
                },
            ],
        }

    def test_unique_cross_view_candidate_is_selected(self):
        result = rank_competing_hypotheses(
            [self.candidate("height_includes_terminal", (49.2, 50.5)),
             self.candidate("terminal_added_after_nominal_height", (51.5, 56.0))],
            self.references,
            self.observations,
        )
        self.assertEqual(result["disposition"], "SELECTED")
        self.assertEqual(result["selected_candidate"], "height_includes_terminal")
        self.assertTrue(result["candidates"][0]["viable"])
        self.assertFalse(result["candidates"][1]["viable"])

    def test_tie_remains_ambiguous(self):
        result = rank_competing_hypotheses(
            [self.candidate("a", (49.2, 50.5)), self.candidate("b", (49.2, 50.5))],
            self.references,
            self.observations,
        )
        self.assertEqual(result["disposition"], "AMBIGUOUS")
        self.assertIsNone(result["selected_candidate"])

    def test_one_view_is_not_cross_view_evidence(self):
        candidate_a = self.candidate("a", (49.2, 50.5))
        candidate_b = self.candidate("b", (51.5, 56.0))
        candidate_a["predicted_consequences"] = candidate_a["predicted_consequences"][:1]
        candidate_b["predicted_consequences"] = candidate_b["predicted_consequences"][:1]
        result = rank_competing_hypotheses(
            [candidate_a, candidate_b], self.references, self.observations
        )
        self.assertEqual(result["disposition"], "INSUFFICIENT_EVIDENCE")

    def test_candidate_cannot_inline_its_own_observation(self):
        candidate_a = self.candidate("a", (49.2, 50.5))
        candidate_b = self.candidate("b", (51.5, 56.0))
        candidate_a["predicted_consequences"][0]["observation_id"] = "missing"
        result = rank_competing_hypotheses(
            [candidate_a, candidate_b], self.references, self.observations
        )
        self.assertEqual(result["disposition"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(
            result["candidates"][0]["results"][0]["result"]["status"], "UNDECIDABLE"
        )


if __name__ == "__main__":
    unittest.main()
