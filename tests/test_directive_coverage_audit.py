"""Regression checks for directive coverage auditing."""

import copy
import json
import unittest
from pathlib import Path

from tools.audit_directive_coverage import MATRIX, audit_matrix, directive_sections


class DirectiveCoverageAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.sections = directive_sections()

    def test_current_matrix_covers_every_directive_heading(self):
        result = audit_matrix(self.payload, self.sections)
        self.assertEqual(result["structural_status"], "PASS")
        self.assertEqual(result["directive_status"], "PARTIAL")
        self.assertEqual(result["master_sections"], 20)

    def test_missing_evidence_path_fails_closed(self):
        payload = copy.deepcopy(self.payload)
        payload["requirements"][0]["evidence"] = ["runs/not-retained/missing.json"]
        result = audit_matrix(payload, self.sections)
        self.assertEqual(result["structural_status"], "FAIL")
        self.assertTrue(any("must resolve" in error for error in result["errors"]))

    def test_duplicate_section_fails_closed(self):
        payload = copy.deepcopy(self.payload)
        payload["requirements"].append(copy.deepcopy(payload["requirements"][0]))
        result = audit_matrix(payload, self.sections)
        self.assertEqual(result["structural_status"], "FAIL")
        self.assertTrue(any("duplicate" in error for error in result["errors"]))

    def test_all_implemented_requires_matching_overall_status(self):
        payload = copy.deepcopy(self.payload)
        for requirement in payload["requirements"]:
            requirement["status"] = "IMPLEMENTED_VERIFIED"
        result = audit_matrix(payload, self.sections)
        self.assertEqual(result["structural_status"], "FAIL")
        self.assertTrue(any("overall_status" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
