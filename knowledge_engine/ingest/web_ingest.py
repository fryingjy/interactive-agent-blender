"""Approved-root web fetcher; intentionally not a crawler or downloader bypass."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass
class WebPage:
    canonical_url: str
    content_type: str
    body: bytes


def fetch_approved_page(url: str, *, approved_hosts: set[str], timeout: float = 20.0) -> WebPage:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in approved_hosts:
        raise PermissionError(f"URL is outside approved hosts: {url}")
    request = Request(url, headers={"User-Agent": "interactive-agent-blender-research/1.0"})
    with urlopen(request, timeout=timeout) as response:
        final = urlparse(response.geturl())
        if final.hostname not in approved_hosts:
            raise PermissionError(f"redirect left approved hosts: {response.geturl()}")
        return WebPage(
            canonical_url=response.geturl(),
            content_type=response.headers.get_content_type(),
            body=response.read(),
        )
