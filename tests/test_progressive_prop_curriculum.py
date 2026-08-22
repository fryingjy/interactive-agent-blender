import copy
import json
import unittest
from pathlib import Path

from tools.validate_progressive_prop_curriculum import validate


ROOT = Path(__file__).resolve().parents[1]


class ProgressivePropCurriculumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(
            (ROOT / "knowledge" / "foundation" / "progressive_prop_benchmark_curriculum.json").read_text(encoding="utf-8")
        )

    def test_current_curriculum_passes(self):
        self.assertEqual(validate(copy.deepcopy(self.fixture)), [])

    def test_human_gate_cannot_be_silently_removed(self):
        corrupted = copy.deepcopy(self.fixture)
        corrupted["promotion_policy"]["human_review_required"] = False
        self.assertIn("promotion must require human review", validate(corrupted))

    def test_sequence_cannot_skip_a_prop(self):
        corrupted = copy.deepcopy(self.fixture)
        corrupted["tiers"][0]["props"].pop(1)
        self.assertTrue(any("1..30" in error for error in validate(corrupted)))

    def test_serialized_powershell_prop_is_rejected_without_crashing(self):
        corrupted = copy.deepcopy(self.fixture)
        corrupted["tiers"][0]["props"][0] = "@{id=1; title=Swingline 747 Stapler}"
        errors = validate(corrupted)
        self.assertTrue(any("every prop must be an object" in error for error in errors))

    def test_missing_difficulty_reason_is_rejected(self):
        corrupted = copy.deepcopy(self.fixture)
        corrupted["tiers"][0]["props"][0].pop("difficulty_reason")
        errors = validate(corrupted)
        self.assertIn("every prop requires a non-empty difficulty_reason", errors)


if __name__ == "__main__":
    unittest.main()
