"""Parse local WebVTT, SRT, or timestamped plain-text transcripts."""

from __future__ import annotations

import re
from pathlib import Path


_TIME_RE = re.compile(
    r"(?P<h>\d{1,2}):(?P<m>\d{2}):(?P<s>\d{2})[,.](?P<ms>\d{3})"
)


def _seconds(value: str) -> float:
    match = _TIME_RE.search(value.strip())
    if not match:
        raise ValueError(f"invalid timestamp: {value!r}")
    parts = {key: int(item) for key, item in match.groupdict().items()}
    return parts["h"] * 3600 + parts["m"] * 60 + parts["s"] + parts["ms"] / 1000


def parse_transcript(path: str | Path) -> list[dict]:
    source = Path(path).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    text = source.read_text(encoding="utf-8-sig")
    blocks = re.split(r"\r?\n\s*\r?\n", text.strip())
    segments = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or lines[0].upper() == "WEBVTT":
            continue
        timing_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        start_text, end_text = [part.strip().split()[0] for part in lines[timing_index].split("-->", 1)]
        body = " ".join(lines[timing_index + 1 :])
        if not body:
            continue
        segments.append(
            {
                "start": _seconds(start_text),
                "end": _seconds(end_text),
                "text": re.sub(r"<[^>]+>", "", body),
            }
        )
    return segments


def find_sidecar(video_path: str | Path) -> Path | None:
    video = Path(video_path)
    for suffix in (".vtt", ".srt", ".txt"):
        candidate = video.with_suffix(suffix)
        if candidate.is_file():
            return candidate.resolve()
    return None
