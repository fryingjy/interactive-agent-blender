"""Small validated records shared by the knowledge-ingestion modules."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


VALID_TRUST_TIERS = {"A", "B", "C", "D"}
VALID_SOURCE_STATUSES = {
    "QUEUED",
    "STUDYING",
    "STUDIED",
    "EXPERIMENTALLY_TESTED",
    "RUNTIME_VALIDATED",
    "REJECTED",
}


@dataclass
class AccessRecord:
    text: bool = False
    video: bool = False
    audio: bool = False
    captions: bool = False


@dataclass
class SourceRecord:
    id: str
    title: str
    creator: str
    source_type: str
    trust_tier: str
    version: str
    topics: list[str]
    access: AccessRecord
    status: str
    url: str | None = None
    local_path: str | None = None
    rejected_reason: str | None = None
    modalities_inspected: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.id.strip() or not self.title.strip():
            raise ValueError("source id and title are required")
        if self.trust_tier not in VALID_TRUST_TIERS:
            raise ValueError(f"invalid trust tier: {self.trust_tier}")
        if self.status not in VALID_SOURCE_STATUSES:
            raise ValueError(f"invalid source status: {self.status}")
        if self.status == "REJECTED" and not self.rejected_reason:
            raise ValueError("rejected sources require rejected_reason")
        if not self.url and not self.local_path:
            raise ValueError("a canonical URL or local path is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass
class IngestedDocument:
    source: SourceRecord
    canonical_id: str
    headings: list[dict[str, Any]]
    operator_parameters: list[str]
    warnings: list[str]
    related_links: list[str]
    text: str
    content_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source.to_dict(),
            "canonical_id": self.canonical_id,
            "headings": self.headings,
            "operator_parameters": self.operator_parameters,
            "warnings": self.warnings,
            "related_links": self.related_links,
            "text": self.text,
            "content_sha256": self.content_sha256,
        }
