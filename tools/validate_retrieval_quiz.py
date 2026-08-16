"""Validate retrieval-quiz structure, interval, and textual novelty.

This deliberately cannot validate factual correctness, independent authorship, or cognitive
retention. It only makes the measurable parts of a self-administered quiz reproducible.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEADING = re.compile(r"(?m)^(?:##\s+|\*\*)(\d+)\.\s+([^\n]+)")
DATE = re.compile(r"\*\*Date:\*\*\s+(\d{4}-\d{2}-\d{2})")
WORD = re.compile(r"\b[\w’-]+\b")


def parse_quiz(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    date_match = DATE.search(text)
    matches = list(HEADING.finditer(text))
    answers: list[str] = []
    questions: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        answer = text[match.end():end]
        answer = answer.split("\n## Self-evaluation", 1)[0].strip()
        questions.append(match.group(2).strip("* "))
        answers.append(answer)
    return {
        "path": path,
        "date": date.fromisoformat(date_match.group(1)) if date_match else None,
        "questions": questions,
        "answers": answers,
    }


def normalize(text: str) -> str:
    return " ".join(WORD.findall(text.lower()))


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def validate_quiz(current: dict[str, object], prior: list[dict[str, object]], *, expected_questions: int, minimum_words: int, minimum_days: int, similarity_limit: float) -> dict[str, object]:
    answers = current["answers"]
    word_counts = [len(WORD.findall(answer)) for answer in answers]
    previous_answers = [answer for quiz in prior for answer in quiz["answers"]]
    maximum_similarity = 0.0
    closest_pair: dict[str, int] | None = None
    for current_index, answer in enumerate(answers):
        for prior_index, old_answer in enumerate(previous_answers):
            similarity = SequenceMatcher(None, normalize(answer), normalize(old_answer)).ratio()
            if similarity > maximum_similarity:
                maximum_similarity = similarity
                closest_pair = {"current_answer": current_index + 1, "prior_answer_flat_index": prior_index + 1}
    dates = [quiz["date"] for quiz in prior if quiz["date"] is not None]
    interval_days = (current["date"] - max(dates)).days if current["date"] and dates else None
    checks = {
        "expected_numbered_answers_present": len(answers) == expected_questions,
        "every_answer_meets_minimum_words": bool(word_counts) and min(word_counts) >= minimum_words,
        "below_prior_answer_similarity_limit": maximum_similarity < similarity_limit,
        "minimum_calendar_interval_met": interval_days is not None and interval_days >= minimum_days,
    }
    return {
        "quiz": display_path(current["path"]),
        "question_count": len(answers),
        "minimum_answer_words": min(word_counts) if word_counts else 0,
        "median_answer_words": sorted(word_counts)[len(word_counts) // 2] if word_counts else 0,
        "maximum_answer_words": max(word_counts) if word_counts else 0,
        "days_since_latest_prior_quiz": interval_days,
        "maximum_sequence_similarity_to_any_prior_answer": maximum_similarity,
        "closest_pair": closest_pair,
        "checks": checks,
        "pass": all(checks.values()),
        "claim_boundary": "This validates answer count, length, calendar separation, and textual novelty only. It does not validate factual correctness, closed-book conditions, independent authorship, cognitive retention, or professional proficiency.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("quiz", type=Path)
    parser.add_argument("--prior", type=Path, nargs="+", required=True)
    parser.add_argument("--expected-questions", type=int, default=20)
    parser.add_argument("--minimum-words", type=int, default=30)
    parser.add_argument("--minimum-days", type=int, default=5)
    parser.add_argument("--similarity-limit", type=float, default=0.85)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate_quiz(
        parse_quiz(args.quiz),
        [parse_quiz(path) for path in args.prior],
        expected_questions=args.expected_questions,
        minimum_words=args.minimum_words,
        minimum_days=args.minimum_days,
        similarity_limit=args.similarity_limit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
