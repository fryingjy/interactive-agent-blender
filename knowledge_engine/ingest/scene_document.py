"""Local, permitted reconstruction of CloudGlue's observed video-description schema.

CloudGlue (`mcp__Cloudglue__describe_video`) was observed to return a markdown "Video
Document" shaped like: `## File` (Filename / URI / Source URI / Source / Added /
Duration), `## Title`, `## Summary`, then `## Scenes` made of `### Scene [MM:SS -
MM:SS]` blocks carrying a `**Speech:**` bullet list of timestamped transcript lines,
chunked into roughly 20-second windows.

This module reproduces that STRUCTURE using this project's own legitimate local
`video_ingest.py` pipeline (frame sampling + transcript parsing/transcription), run
only against files already inside `approved_roots` -- the same safety boundary as
`video_ingest.py` itself: no URL downloader, no platform-restriction bypass.

It does NOT reproduce CloudGlue's automated visual captioning -- there is no local
vision-captioning backend in this project. Each scene's `visual_description` (and the
document's overall `summary`) is left as an explicit placeholder for a vision-capable
reviewer -- a human, or Claude itself reading the extracted frame PNGs directly via the
`frame_paths` listed on the scene -- to fill in with `fill_visual_descriptions`. An
unfilled scene document is frame/transcript access, not comprehension, matching this
project's own standing evidence discipline (see `video_ingest.py`'s own limitations).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .video_ingest import _inside, _require_av, ingest_video

UNFILLED = "[UNFILLED -- inspect frame_paths and replace this placeholder with a real description]"


def _format_timestamp(seconds: float) -> str:
    total = max(0, round(seconds))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _bucket_transcript(segments: list[dict], window: float, duration: float) -> list[dict]:
    # A tiny epsilon absorbs ordinary container/encoder timing rounding (a real
    # video's reported duration is essentially never an exact multiple of the
    # scene window) so a few stray milliseconds don't spawn a near-empty trailing
    # scene on their own.
    epsilon = 0.25
    remainder = duration % window
    n_windows = max(1, int(duration // window) + (1 if remainder > epsilon else 0))
    buckets = [
        {"start": i * window, "end": min((i + 1) * window, duration), "lines": []}
        for i in range(n_windows)
    ]
    for segment in segments:
        index = min(int(segment["start"] // window), n_windows - 1)
        buckets[index]["lines"].append(segment)
    return buckets


def _probe_duration(video_path: Path, roots: list[Path]) -> float:
    if not _inside(video_path, roots):
        raise PermissionError(f"video is outside approved roots: {video_path}")
    av = _require_av()
    with av.open(str(video_path)) as container:
        video_streams = list(container.streams.video)
        if not video_streams:
            raise ValueError("file has no video stream")
        stream = video_streams[0]
        if container.duration is not None:
            return float(container.duration / av.time_base)
        if stream.duration:
            return float(stream.duration * stream.time_base)
        return 0.0


def _frames_in_window(frames: list[dict], start: float, end: float) -> list[dict]:
    within = [frame for frame in frames if start - 1e-6 <= frame["timestamp"] < end + 1e-6]
    if within:
        return within
    midpoint = (start + end) / 2
    return sorted(frames, key=lambda frame: abs(frame["timestamp"] - midpoint))[:1]


def build_scene_document(
    path: str | Path,
    *,
    approved_roots: list[str | Path],
    output_dir: str | Path,
    source_id: str,
    title: str | None = None,
    scene_window: float = 20.0,
    frames_per_scene: int = 3,
    transcribe_model: str | None = None,
    transcript_language: str | None = "en",
) -> dict:
    video_path = Path(path).resolve()
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    # One coarse frame per scene_window is too sparse to actually see what changes
    # within a scene (a viewport orbit, a modifier being applied). Request extra
    # intra-scene sample points so a reviewer has real visual coverage, not just a
    # single frame at each boundary. A lightweight duration-only probe avoids paying
    # for a second full frame-decode pass just to compute those sample points.
    roots = [Path(item).resolve() for item in approved_roots]
    duration = _probe_duration(video_path, roots)
    fine_timestamps: list[float] = []
    if frames_per_scene > 1:
        n_windows = max(1, int(duration // scene_window) + (1 if duration % scene_window else 0))
        for i in range(n_windows):
            window_start = i * scene_window
            window_end = min((i + 1) * scene_window, duration)
            span = window_end - window_start
            for step in range(1, frames_per_scene):
                fine_timestamps.append(window_start + span * step / frames_per_scene)

    ingest = ingest_video(
        video_path,
        approved_roots=approved_roots,
        output_dir=output / "frames",
        source_id=source_id,
        coarse_interval=scene_window,
        fine_timestamps=fine_timestamps,
        transcribe_model=transcribe_model,
        transcript_language=transcript_language,
        include_transcript_text=True,
    )

    duration = ingest["duration"]
    buckets = _bucket_transcript(ingest["transcript_segments"], scene_window, duration)

    scenes = []
    for bucket in buckets:
        frames = _frames_in_window(ingest["coarse_segments"], bucket["start"], bucket["end"])
        scenes.append(
            {
                "start": bucket["start"],
                "end": bucket["end"],
                "start_label": _format_timestamp(bucket["start"]),
                "end_label": _format_timestamp(bucket["end"]),
                "speech": [
                    {
                        "start_label": _format_timestamp(line["start"]),
                        "end_label": _format_timestamp(line["end"]),
                        "text": line["text"],
                    }
                    for line in bucket["lines"]
                ],
                "frame_paths": [frame["path"] for frame in frames],
                "visual_description": UNFILLED,
            }
        )

    document = {
        "file": {
            "filename": video_path.name,
            "local_path": str(video_path),
            "sha256": ingest["sha256"],
            "source": "local-file",
            "added": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration,
        },
        "title": title or video_path.stem.replace("_", " ").title(),
        "summary": UNFILLED,
        "scenes": scenes,
        "modalities": {
            "video": ingest["video"],
            "audio": ingest["audio"],
            "captions": ingest["captions"],
            "transcript": ingest["transcript"],
        },
        "limitations": [
            "visual_description and summary fields are placeholders: no local vision-captioning "
            "backend exists in this project. They must be filled from the listed frame_paths by a "
            "vision-capable reviewer (e.g. Claude reading the frame PNGs directly) before this "
            "document is treated as comprehension evidence rather than access evidence.",
            "This mirrors CloudGlue's OBSERVED output schema shape (File/Title/Summary/Scenes with "
            "timestamped Speech), not its proprietary automated visual-understanding model.",
        ]
        + ingest["limitations"],
    }

    (output / "scene_document.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
    (output / "scene_document.md").write_text(render_markdown(document), encoding="utf-8")
    return document


def render_markdown(document: dict) -> str:
    file_info = document["file"]
    lines = [
        "## File",
        "",
        f"- Filename: {file_info['filename']}",
        f"- Local path: {file_info['local_path']}",
        f"- SHA256: {file_info['sha256']}",
        f"- Source: {file_info['source']}",
        f"- Added: {file_info['added']}",
        f"- Duration: {file_info['duration_seconds']:.2f}s",
        "",
        "## Title",
        "",
        document["title"],
        "",
        "## Summary",
        "",
        document["summary"],
        "",
        "## Scenes",
    ]
    for scene in document["scenes"]:
        lines.append("")
        lines.append(f"### Scene [{scene['start_label']} - {scene['end_label']}]")
        lines.append("")
        lines.append(f"**Visual:** {scene['visual_description']}")
        if scene["frame_paths"]:
            lines.append("")
            lines.append(f"**Frames:** {', '.join(scene['frame_paths'])}")
        if scene["speech"]:
            lines.append("")
            lines.append("**Speech:**")
            for line in scene["speech"]:
                lines.append(f"- [{line['start_label']} - {line['end_label']}] {line['text']}")
    return "\n".join(lines) + "\n"


def fill_visual_descriptions(
    document_path: str | Path,
    descriptions: dict[int, str],
    summary: str | None = None,
) -> dict:
    """Apply reviewer-supplied, frame-grounded descriptions to an existing scene document.

    `descriptions` maps scene index -> description text. Call this only after actually
    viewing that scene's frame_paths -- never fabricate a description from the title or
    speech text alone, per this project's standing evidence discipline.
    """
    path = Path(document_path).resolve()
    document = json.loads(path.read_text(encoding="utf-8"))
    for index, text in descriptions.items():
        document["scenes"][int(index)]["visual_description"] = text
    if summary is not None:
        document["summary"] = summary
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    path.with_suffix(".md").write_text(render_markdown(document), encoding="utf-8")
    return document
