"""Regression coverage for source-registry evidence classification."""

import unittest

from tools.audit_source_registry import classify_reference


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


if __name__ == "__main__":
    unittest.main()
