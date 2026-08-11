"""Optional local speech-to-text for permitted lesson files.

The backend is imported only when requested so ordinary ingestion remains dependency-light.
Generated transcripts are evidence with model provenance, not authoritative quotations.
"""

from __future__ import annotations

import json
from pathlib import Path


def _timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def write_webvtt(segments: list[dict], destination: str | Path) -> Path:
    path = Path(destination).resolve()
    lines = ["WEBVTT", ""]
    for index, segment in enumerate(segments, 1):
        lines.extend([
            str(index),
            f"{_timestamp(float(segment['start']))} --> {_timestamp(float(segment['end']))}",
            str(segment["text"]).strip(),
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def transcribe_video(
    path: str | Path,
    *,
    output_dir: str | Path,
    model_name: str = "tiny.en",
    language: str | None = "en",
) -> dict:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("faster-whisper is required when transcription is requested") from exc

    source = Path(path).resolve()
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    generated, info = model.transcribe(
        str(source),
        language=language,
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=True,
    )
    segments = [
        {"start": round(item.start, 3), "end": round(item.end, 3), "text": item.text.strip()}
        for item in generated
        if item.text.strip()
    ]
    vtt_path = write_webvtt(segments, output / "generated_transcript.vtt")
    report = {
        "backend": "faster-whisper",
        "model": model_name,
        "device": "cpu",
        "compute_type": "int8",
        "requested_language": language,
        "detected_language": info.language,
        "language_probability": info.language_probability,
        "source_path": str(source),
        "transcript_path": str(vtt_path),
        "segments": segments,
        "limitations": [
            "Machine transcription may contain errors; verify important claims against frames and official documentation.",
            "Generated text is evidence of local speech processing, not creator-supplied captions.",
        ],
    }
    (output / "speech_transcription_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
