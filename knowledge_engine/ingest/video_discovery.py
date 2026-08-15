"""Metadata-only YouTube lesson discovery for bounded modeling research.

Discovery is not video understanding. This module searches public metadata with
``yt-dlp`` and creates an auditable study queue; it never downloads media and it
never promotes a result into knowledge merely because its title looks relevant.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


DISCOVERY_STATUS = "DISCOVERED_METADATA_ONLY"
_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "and", "are", "blender", "for", "from", "how", "in", "of", "on", "the",
    "to", "tutorial", "using", "with",
}


def known_youtube_ids(paths: Iterable[str | Path]) -> set[str]:
    """Extract public YouTube IDs from explicit UTF-8 evidence/registry files."""
    ids = set()
    url_pattern = re.compile(r"https://(?:www\.|m\.)?(?:youtube\.com/watch\?[^\s\"'<>]+|youtu\.be/[^\s\"'<>]+)")
    for item in paths:
        path = Path(item)
        if not path.is_file():
            raise FileNotFoundError(path)
        for url in url_pattern.findall(path.read_text(encoding="utf-8-sig")):
            parsed = urlparse(url.rstrip(".,);]"))
            if parsed.hostname and parsed.hostname.endswith("youtu.be"):
                video_id = parsed.path.strip("/")
            else:
                video_id = (parse_qs(parsed.query).get("v") or [""])[0]
            if video_id:
                ids.add(video_id)
    return ids


def _tokens(text: str) -> set[str]:
    return {token for token in _TOKEN.findall(text.lower()) if token not in _STOPWORDS}


def _matched_terms(candidate_terms: set[str], blocked_terms: set[str]) -> list[str]:
    return sorted({
        blocked
        for blocked in blocked_terms
        if any(
            token == blocked
            or (len(blocked) >= 4 and token.startswith(blocked))
            or (len(token) >= 4 and blocked.startswith(token))
            for token in candidate_terms
        )
    })


def _default_runner(command: list[str], timeout: float) -> str:
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("yt-dlp is required for public-video discovery") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"video discovery exceeded {timeout:.0f}s") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "yt-dlp search failed").strip().splitlines()[-1]
        raise RuntimeError(f"video discovery failed: {detail}") from exc
    return completed.stdout


def _validate_query(query: str, limit: int) -> str:
    normalized = " ".join(query.split())
    if not normalized or len(normalized) > 240:
        raise ValueError("query must contain 1-240 non-whitespace characters")
    if normalized.lower().startswith(("http://", "https://", "ytsearch")):
        raise ValueError("query must describe a learning gap, not supply a URL or yt-dlp expression")
    if not 1 <= limit <= 25:
        raise ValueError("limit must be between 1 and 25")
    return normalized


def _candidate_score(entry: dict[str, Any], query: str) -> tuple[float, list[str], list[str]]:
    title = str(entry.get("title") or "")
    description = str(entry.get("description") or "")
    haystack = _tokens(f"{title} {description}")
    query_terms = _tokens(query)
    overlap = sorted(query_terms & haystack)
    coverage = len(overlap) / max(1, len(query_terms))
    score = 6.0 * coverage
    reasons = [f"metadata covers {len(overlap)}/{len(query_terms)} meaningful query terms"]
    risks = ["title/description relevance is not proof of instructional quality or video content"]

    duration = float(entry.get("duration") or 0)
    if 180 <= duration <= 3600:
        score += 1.25
        reasons.append("duration supports a substantive lesson")
    elif duration and duration < 90:
        score -= 1.5
        risks.append("short duration may omit reasoning, failure, and recovery")
    elif duration > 7200:
        score -= 0.5
        risks.append("very long source requires episode-level triage")

    views = int(entry.get("view_count") or 0)
    if views > 0:
        score += min(0.75, math.log10(views + 1) / 8)
        reasons.append("public view count provides a weak discoverability signal only")
    if entry.get("channel_is_verified") is True:
        score += 0.2
        reasons.append("channel identity is platform-verified, not technically validated")
    if description:
        score += 0.2
    return round(score, 4), reasons, risks


def _normalize_entry(entry: dict[str, Any], query: str) -> dict[str, Any] | None:
    video_id = str(entry.get("id") or "").strip()
    title = str(entry.get("title") or "").strip()
    if not video_id or not title:
        return None
    score, reasons, risks = _candidate_score(entry, query)
    return {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "title": title,
        "creator": str(entry.get("channel") or entry.get("uploader") or "").strip(),
        "duration_seconds": float(entry.get("duration") or 0),
        "view_count": int(entry.get("view_count") or 0),
        "description": str(entry.get("description") or "").strip(),
        "source_queries": [query],
        "metadata_relevance_score": score,
        "selection_reasons": reasons,
        "risks": risks,
        "status": DISCOVERY_STATUS,
        "video_archived": False,
        "knowledge_promoted": False,
    }


def discover_youtube_lessons(
    query: str,
    *,
    limit: int = 10,
    excluded_video_ids: Iterable[str] = (),
    heldout_target_terms: Iterable[str] = (),
    excluded_topic_terms: Iterable[str] = (),
    timeout: float = 45.0,
    runner: Callable[[list[str], float], str] = _default_runner,
) -> dict[str, Any]:
    """Return ranked public metadata without downloading or understanding video."""
    normalized_query = _validate_query(query, limit)
    excluded = {str(item).strip() for item in excluded_video_ids if str(item).strip()}
    target_terms = _tokens(" ".join(heldout_target_terms))
    excluded_topics = _tokens(" ".join(excluded_topic_terms))
    command = [
        "yt-dlp", "--dump-single-json", "--flat-playlist", "--no-warnings",
        f"ytsearch{limit}:{normalized_query}",
    ]
    payload = json.loads(runner(command, timeout))
    candidates = []
    rejected = []
    seen = set()
    for entry in payload.get("entries") or []:
        candidate = _normalize_entry(entry, normalized_query)
        if candidate is None:
            rejected.append({"reason": "missing stable video id or title"})
            continue
        video_id = candidate["video_id"]
        if video_id in seen or video_id in excluded:
            rejected.append({"video_id": video_id, "reason": "duplicate or previously studied"})
            continue
        seen.add(video_id)
        candidate_terms = _tokens(f"{candidate['title']} {candidate['description']}")
        contamination = _matched_terms(candidate_terms, target_terms)
        if contamination:
            rejected.append({
                "video_id": video_id,
                "reason": "held-out target contamination risk",
                "matched_terms": contamination,
            })
            continue
        off_priority = _matched_terms(candidate_terms, excluded_topics)
        if off_priority:
            rejected.append({
                "video_id": video_id,
                "reason": "current curriculum priority exclusion",
                "matched_terms": off_priority,
            })
            continue
        candidates.append(candidate)
    candidates.sort(key=lambda item: (-item["metadata_relevance_score"], item["video_id"]))
    return {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backend": "yt-dlp public metadata search",
        "query": normalized_query,
        "requested_limit": limit,
        "candidates": candidates,
        "rejected": rejected,
        "media_downloaded": False,
        "limitations": [
            "Discovery inspects public metadata only; it does not watch, hear, validate, or learn from a video.",
            "Ranking measures query fit and triage value, not creator authority or technical correctness.",
            "A selected source must pass multimodal extraction, independent timestamp review, reproduction, and transfer before promotion.",
        ],
    }


def build_study_queue(discoveries: Iterable[dict[str, Any]], *, maximum: int = 20) -> dict[str, Any]:
    if not 1 <= maximum <= 100:
        raise ValueError("maximum must be between 1 and 100")
    by_id: dict[str, dict[str, Any]] = {}
    queries = []
    summaries = []
    for discovery in discoveries:
        query = str(discovery.get("query") or "")
        if query:
            queries.append(query)
        summaries.append({
            "query": query,
            "requested_limit": discovery.get("requested_limit"),
            "candidate_video_ids": [item["video_id"] for item in discovery.get("candidates") or []],
            "rejected": discovery.get("rejected") or [],
        })
        for candidate in discovery.get("candidates") or []:
            video_id = candidate["video_id"]
            existing = by_id.get(video_id)
            if existing is None:
                by_id[video_id] = dict(candidate)
                continue
            existing["source_queries"] = sorted(set(existing["source_queries"] + candidate["source_queries"]))
            if candidate["metadata_relevance_score"] > existing["metadata_relevance_score"]:
                existing["metadata_relevance_score"] = candidate["metadata_relevance_score"]
                existing["selection_reasons"] = candidate["selection_reasons"]
    candidates = sorted(
        by_id.values(), key=lambda item: (-item["metadata_relevance_score"], item["video_id"])
    )[:maximum]
    for index, candidate in enumerate(candidates, 1):
        candidate["queue_rank"] = index
        candidate["next_gate"] = "MULTIMODAL_EXTRACTION"
    return {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "queries": sorted(set(queries)),
        "discovery_summaries": summaries,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "media_downloaded": False,
        "promotion_count": 0,
    }
