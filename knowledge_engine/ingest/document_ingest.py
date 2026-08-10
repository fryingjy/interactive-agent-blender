"""Deterministic local documentation ingestion rooted in approved directories."""

from __future__ import annotations

import hashlib
import html
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

from knowledge_engine.schemas import AccessRecord, IngestedDocument, SourceRecord


class _Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self.headings: list[dict] = []
        self.links: list[str] = []
        self._heading_level: int | None = None
        self._heading_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if re.fullmatch(r"h[1-6]", tag):
            self._heading_level = int(tag[1])
            self._heading_parts = []
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag):
        if self._heading_level and tag == f"h{self._heading_level}":
            heading = " ".join(self._heading_parts).strip()
            if heading:
                self.headings.append({"level": self._heading_level, "text": heading})
            self._heading_level = None

    def handle_data(self, data):
        cleaned = " ".join(data.split())
        if cleaned:
            self.text_parts.append(cleaned)
            if self._heading_level:
                self._heading_parts.append(cleaned)


def _inside(path: Path, roots: list[Path]) -> bool:
    return any(path == root or root in path.parents for root in roots)


def ingest_document(
    path: str | Path,
    *,
    approved_roots: list[str | Path],
    source_id: str,
    title: str,
    creator: str,
    trust_tier: str,
    version: str,
    topics: list[str],
    canonical_url: str | None = None,
) -> IngestedDocument:
    source_path = Path(path).resolve()
    roots = [Path(item).resolve() for item in approved_roots]
    if not _inside(source_path, roots):
        raise PermissionError(f"document is outside approved roots: {source_path}")
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    raw = source_path.read_text(encoding="utf-8-sig")
    if source_path.suffix.lower() in {".html", ".htm"}:
        parser = _Extractor()
        parser.feed(raw)
        text = "\n".join(parser.text_parts)
        headings = parser.headings
        links = [urljoin(canonical_url or source_path.as_uri(), href) for href in parser.links]
    else:
        text = raw
        headings = [
            {"level": len(match.group(1)), "text": match.group(2).strip()}
            for match in re.finditer(r"(?m)^(#{1,6})\s+(.+)$", raw)
        ]
        links = re.findall(r"https?://[^\s)>]+", raw)

    parameter_lines = [
        line.strip(" -*`")
        for line in text.splitlines()
        if re.search(r"\b(parameter|option|setting|property|argument)\b", line, re.I)
    ]
    warnings = [
        line.strip(" -*`")
        for line in text.splitlines()
        if re.search(r"\b(warning|caution|important|note:)\b", line, re.I)
    ]
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    source = SourceRecord(
        id=source_id,
        url=canonical_url,
        local_path=str(source_path),
        title=title,
        creator=creator,
        source_type="document",
        trust_tier=trust_tier,
        version=version,
        topics=topics,
        access=AccessRecord(text=True),
        status="STUDIED",
        modalities_inspected=["text"],
    )
    return IngestedDocument(
        source=source,
        canonical_id=canonical_url or source_path.as_uri(),
        headings=headings,
        operator_parameters=parameter_lines,
        warnings=warnings,
        related_links=sorted(set(html.unescape(link) for link in links)),
        text=text,
        content_sha256=digest,
    )


def crawl_local_documents(
    start_paths: list[str | Path],
    *,
    approved_roots: list[str | Path],
    creator: str,
    trust_tier: str,
    version: str,
    topics: list[str],
    max_pages: int = 100,
    allowed_suffixes: tuple[str, ...] = (".html", ".htm", ".md", ".txt"),
) -> dict:
    """Follow approved-root local document links with completion and duplicate tracking."""
    if max_pages < 1:
        raise ValueError("max_pages must be positive")
    roots = [Path(item).resolve() for item in approved_roots]
    queue = [Path(item).resolve() for item in start_paths]
    visited_paths: set[Path] = set()
    canonical_seen: set[str] = set()
    hash_owner: dict[str, str] = {}
    documents = []
    skipped = []

    while queue and len(documents) < max_pages:
        path = queue.pop(0)
        if path in visited_paths:
            continue
        visited_paths.add(path)
        if not _inside(path, roots):
            skipped.append({"path": str(path), "reason": "OUTSIDE_APPROVED_ROOT"})
            continue
        if not path.is_file():
            skipped.append({"path": str(path), "reason": "MISSING"})
            continue
        if path.suffix.lower() not in allowed_suffixes:
            skipped.append({"path": str(path), "reason": "UNSUPPORTED_SUFFIX"})
            continue
        canonical = path.as_uri()
        if canonical in canonical_seen:
            skipped.append({"path": str(path), "reason": "DUPLICATE_CANONICAL"})
            continue
        canonical_seen.add(canonical)
        document = ingest_document(
            path,
            approved_roots=roots,
            source_id="local-doc-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12],
            title=path.stem,
            creator=creator,
            trust_tier=trust_tier,
            version=version,
            topics=topics,
            canonical_url=canonical,
        )
        prior = hash_owner.get(document.content_sha256)
        if prior:
            skipped.append({"path": str(path), "reason": "DUPLICATE_CONTENT", "same_as": prior})
        else:
            hash_owner[document.content_sha256] = canonical
            documents.append(document.to_dict())

        for link in document.related_links:
            parsed = urlparse(link)
            if parsed.scheme != "file":
                continue
            linked_path = Path(unquote(parsed.path.lstrip("/"))) if re.match(r"^/[A-Za-z]:", parsed.path) else Path(unquote(parsed.path))
            linked_path = linked_path.resolve()
            if linked_path not in visited_paths and linked_path not in queue:
                queue.append(linked_path)

    completion = {
        "max_pages": max_pages,
        "unique_documents": len(documents),
        "visited_paths": len(visited_paths),
        "remaining_queue": [str(path) for path in queue],
        "complete": not queue,
        "stopped_reason": "QUEUE_EXHAUSTED" if not queue else "MAX_PAGES_REACHED",
    }
    return {"documents": documents, "skipped": skipped, "completion": completion}
