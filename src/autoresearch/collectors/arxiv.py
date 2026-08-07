from __future__ import annotations

import hashlib
import os
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from xml.etree import ElementTree

import httpx

from autoresearch.http import get_client
from autoresearch.schema import PaperRecord
from autoresearch.utils import clean_text

NS = {"atom": "http://www.w3.org/2005/Atom"}
ARXIV_CACHE_DIR = Path(os.environ.get("AUTORESEARCH_CACHE_DIR", ".cache/autoresearch")) / "arxiv"
RETRY_STATUSES = {429, 500, 502, 503, 504}
DEFAULT_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60


def _extract_year(published: str) -> int | None:
    match = re.match(r"(\d{4})", published or "")
    return int(match.group(1)) if match else None


def _cache_path(query: str, limit: int) -> Path:
    key = hashlib.sha256(f"{query}|{limit}".encode()).hexdigest()[:24]
    return ARXIV_CACHE_DIR / f"{key}.xml"


def _read_cache(query: str, limit: int) -> str:
    path = _cache_path(query, limit)
    ttl = int(os.environ.get("AUTORESEARCH_ARXIV_CACHE_TTL_SECONDS", DEFAULT_CACHE_TTL_SECONDS))
    if path.exists() and time.time() - path.stat().st_mtime <= ttl:
        return path.read_text(encoding="utf-8")
    return ""


def _write_cache(query: str, limit: int, text: str) -> None:
    ARXIV_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(query, limit).write_text(text, encoding="utf-8")


def _fetch_arxiv(url: str, query: str, limit: int) -> str:
    cached = _read_cache(query, limit)
    if cached:
        return cached
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            timeout = float(os.environ.get("AUTORESEARCH_ARXIV_TIMEOUT_SECONDS", "4.0"))
            with get_client(timeout=timeout) as client:
                response = client.get(url)
            if response.status_code in RETRY_STATUSES and attempt == 0:
                retry_after = response.headers.get("Retry-After")
                delay = min(float(retry_after), 4.0) if retry_after else 1.0
                time.sleep(delay)
                continue
            response.raise_for_status()
            _write_cache(query, limit, response.text)
            return response.text
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            if attempt == 0 and not isinstance(exc, httpx.TimeoutException):
                time.sleep(1.0)
                continue
            break
    if cached:
        return cached
    if last_error:
        raise last_error
    return ""


def _parse_feed(text: str) -> list[PaperRecord]:
    if not text:
        return []
    root = ElementTree.fromstring(text)
    papers: list[PaperRecord] = []
    for entry in root.findall("atom:entry", NS):
        title = clean_text(entry.findtext("atom:title", default="", namespaces=NS))
        abstract = clean_text(entry.findtext("atom:summary", default="", namespaces=NS))
        published = entry.findtext("atom:published", default="", namespaces=NS)
        authors = [
            clean_text(author.findtext("atom:name", default="", namespaces=NS))
            for author in entry.findall("atom:author", NS)
        ]
        abs_url = ""
        pdf_url = ""
        for link in entry.findall("atom:link", NS):
            href = link.attrib.get("href", "")
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = href
            elif "/abs/" in href:
                abs_url = href
        arxiv_id = abs_url.rstrip("/").split("/")[-1] if abs_url else ""
        papers.append(
            PaperRecord(
                title=title,
                abstract=abstract,
                year=_extract_year(published),
                authors=[author for author in authors if author],
                url=abs_url,
                pdf_url=pdf_url,
                arxiv_id=arxiv_id,
                source="arxiv",
                source_records=["arxiv"],
            )
        )
    return papers


def search_arxiv(query: str, limit: int = 10) -> list[PaperRecord]:
    params = urlencode(
        {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": limit,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
    )
    url = f"https://export.arxiv.org/api/query?{params}"
    return _parse_feed(_fetch_arxiv(url, query, limit))
