"""Regression coverage for the measurable retrieval-quiz constraints."""

import tempfile
import unittest
from pathlib import Path

from tools.validate_retrieval_quiz import parse_quiz, validate_quiz


class RetrievalQuizValidationTests(unittest.TestCase):
    def _quiz(self, directory: Path, name: str, quiz_date: str, answers: list[str]) -> dict[str, object]:
        path = directory / name
        body = [f"# Quiz\n\n**Date:** {quiz_date}\n"]
        for index, answer in enumerate(answers, 1):
            body.append(f"\n## {index}. Question {index}?\n\n{answer}\n")
        path.write_text("".join(body), encoding="utf-8")
        return parse_quiz(path)

    def test_novel_delayed_answers_pass(self):
        with tempfile.TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            prior = self._quiz(directory, "prior.md", "2026-08-01", ["alpha mechanism verifies topology state after each operation"])
            current = self._quiz(directory, "current.md", "2026-08-06", ["beta evidence checks a different reference boundary before authorizing geometry"])
            result = validate_quiz(current, [prior], expected_questions=1, minimum_words=5, minimum_days=5, similarity_limit=0.85)
            self.assertTrue(result["pass"])

    def test_copied_answer_and_short_interval_fail(self):
        with tempfile.TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            answer = "the same mechanism and consequence are copied exactly into this answer"
            prior = self._quiz(directory, "prior.md", "2026-08-01", [answer])
            current = self._quiz(directory, "current.md", "2026-08-02", [answer])
            result = validate_quiz(current, [prior], expected_questions=1, minimum_words=5, minimum_days=5, similarity_limit=0.85)
            self.assertFalse(result["pass"])
            self.assertFalse(result["checks"]["below_prior_answer_similarity_limit"])
            self.assertFalse(result["checks"]["minimum_calendar_interval_met"])


if __name__ == "__main__":
    unittest.main()
