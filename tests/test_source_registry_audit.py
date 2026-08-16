"""Regression coverage for source-registry evidence classification."""

import json
import tempfile
import unittest
from pathlib import Path

from tools.audit_source_registry import classify_reference, load_retention_ledger, retention_key


class SourceRegistryAuditTests(unittest.TestCase):
    def test_path_like_experiment_is_an_artifact_claim(self):
        self.assertEqual(
            classify_reference("metadata.experiments", "runs/2026-08-16_example/report.json"),
            "artifact",
        )

    def test_skill_identifier_is_not_a_filesystem_claim(self):
        self.assertEqual(
            classify_reference("metadata.skills", "topology.loop_cuts.reserve_functional_regions"),
            "non_path_reference",
        )

    def test_removed_media_is_explicitly_non_retained(self):
        self.assertEqual(
            classify_reference("local_path", "REMOVED (temporary source media)"),
            "explicitly_non_retained",
        )

    def test_prose_experiment_note_is_not_a_filesystem_claim(self):
        self.assertEqual(
            classify_reference("metadata.experiments", "see operator card for controlled notes"),
            "non_path_reference",
        )

    def test_retention_ledger_is_keyed_and_rejects_duplicate_records(self):
        record = {
            "source_id": "source", "field": "metadata.experiments", "path": "runs/missing",
            "classification": "HISTORICAL_ARTIFACT_REMOVED_FROM_GIT_HISTORY",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.json"
            path.write_text(json.dumps({"records": [record]}), encoding="utf-8")
            ledger = load_retention_ledger(path)
            self.assertIn(retention_key("source", "metadata.experiments", "runs/missing"), ledger)
            path.write_text(json.dumps({"records": [record, record]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_retention_ledger(path)


if __name__ == "__main__":
    unittest.main()
