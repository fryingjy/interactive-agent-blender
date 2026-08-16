import json
import tempfile
import unittest
from pathlib import Path

from tools.run_retrieval_benchmark import DEFAULT_CASES, load_cases, run_benchmark


ROOT = Path(__file__).resolve().parents[1]


class RetrievalBenchmarkTests(unittest.TestCase):
    def test_repository_cases_pass_positive_and_abstention_gates(self):
        cases = load_cases(DEFAULT_CASES)
        report = run_benchmark(cases, ROOT / "knowledge" / "skills", min_score=4.0)
        self.assertTrue(report["pass"])
        self.assertEqual(report["case_count"], 23)
        self.assertEqual(report["positive_accuracy"], 1.0)
        self.assertEqual(report["abstention_accuracy"], 1.0)

    def test_case_schema_rejects_duplicate_ids(self):
        payload = {
            "cases": [
                {"case_id": "duplicate", "kind": "abstention", "context": {}, "expected_top_skill": None},
                {"case_id": "duplicate", "kind": "abstention", "context": {}, "expected_top_skill": None},
            ]
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cases.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique case_id"):
                load_cases(path)


if __name__ == "__main__":
    unittest.main()
