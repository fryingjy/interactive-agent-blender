"""Local, permitted video ingestion with honest modality accounting.

This module accepts files already supplied by the user/project. It contains no URL
downloader and no platform-restriction bypass. PyAV is optional at import time but
required to inspect video/audio streams and sample frames.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .transcript_ingest import find_sidecar, parse_transcript


def _require_av():
    try:
        import av
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("PyAV is required for local video ingestion") from exc
    return av


def _inside(path: Path, roots: list[Path]) -> bool:
    return any(path == root or root in path.parents for root in roots)


def ingest_video(
    path: str | Path,
    *,
    approved_roots: list[str | Path],
    output_dir: str | Path,
    source_id: str,
    coarse_interval: float = 30.0,
    fine_timestamps: list[float] | None = None,
) -> dict:
    video_path = Path(path).resolve()
    roots = [Path(item).resolve() for item in approved_roots]
    if not _inside(video_path, roots):
        raise PermissionError(f"video is outside approved roots: {video_path}")
    if not video_path.is_file():
        raise FileNotFoundError(video_path)
    if coarse_interval <= 0:
        raise ValueError("coarse_interval must be positive")

    av = _require_av()
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    with av.open(str(video_path)) as container:
        video_streams = list(container.streams.video)
        audio_streams = list(container.streams.audio)
        if not video_streams:
            raise ValueError("file has no video stream")
        stream = video_streams[0]
        fps = float(stream.average_rate) if stream.average_rate else 0.0
        duration = (
            float(container.duration / av.time_base)
            if container.duration is not None
            else float(stream.duration * stream.time_base) if stream.duration else 0.0
        )

    sidecar = find_sidecar(video_path)
    transcript_segments = parse_transcript(sidecar) if sidecar and sidecar.suffix.lower() != ".txt" else []
    targets = []
    cursor = 0.0
    while cursor <= duration + 1e-6:
        targets.append(round(cursor, 3))
        cursor += coarse_interval
    targets.extend(fine_timestamps or [])
    targets = sorted({max(0.0, min(float(value), duration)) for value in targets})

    frames = []
    with av.open(str(video_path)) as container:
        stream = container.streams.video[0]
        pending = iter(targets)
        target = next(pending, None)
        for frame in container.decode(stream):
            if target is None:
                break
            timestamp = float(frame.time or 0.0)
            while target is not None and timestamp + (0.5 / fps if fps else 0.0) >= target:
                destination = output / f"frame_{len(frames):04d}_{target:010.3f}s.png"
                frame.to_image().save(destination)
                frames.append({"timestamp": target, "decoded_at": timestamp, "path": str(destination)})
                target = next(pending, None)

    chapters = []
    if transcript_segments:
        chapters = [
            {"start": segment["start"], "title": segment["text"][:80]}
            for segment in transcript_segments
            if segment["text"].lower().startswith(("chapter", "section", "step"))
        ]
    result = {
        "source_id": source_id,
        "local_path": str(video_path),
        "sha256": hashlib.sha256(video_path.read_bytes()).hexdigest(),
        "duration": duration,
        "fps": fps,
        "video": True,
        "audio": bool(audio_streams),
        "captions": bool(sidecar),
        "transcript": bool(transcript_segments),
        "caption_path": str(sidecar) if sidecar else None,
        "chapters": chapters,
        "coarse_segments": frames,
        "fine_segments": [frame for frame in frames if frame["timestamp"] in set(fine_timestamps or [])],
        "transcript_segments": transcript_segments,
        "limitations": [
            "Frame extraction proves visual access, not comprehension.",
            "Audio presence is stream-level metadata; no speech-to-text is claimed unless a transcript is present.",
        ],
    }
    (output / "video_ingest_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
