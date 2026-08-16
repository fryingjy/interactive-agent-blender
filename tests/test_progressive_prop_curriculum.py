import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_progressive_prop_curriculum import validate


class ProgressivePropCurriculumTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / "knowledge" / "foundation" / "progressive_prop_benchmark_curriculum.json"
        self.data = json.loads(path.read_text(encoding="utf-8"))

    def test_canonical_curriculum_passes(self):
        self.assertEqual(validate(self.data), [])

    def test_human_gate_cannot_be_silently_removed(self):
        self.data["promotion_policy"]["human_review_required"] = False
        self.assertIn("promotion must require human review", validate(self.data))

    def test_sequence_cannot_skip_a_prop(self):
        self.data["tiers"][0]["props"].pop(1)
        self.assertTrue(any("1..30" in error for error in validate(self.data)))


if __name__ == "__main__":
    unittest.main()
