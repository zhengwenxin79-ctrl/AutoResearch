from __future__ import annotations

from urllib.parse import urljoin

from autoresearch.http import get_client
from autoresearch.schema import PaperRecord
from autoresearch.utils import clean_text


def _value(content: dict, key: str) -> str:
    raw = content.get(key)
    if isinstance(raw, dict):
        raw = raw.get("value")
    if isinstance(raw, list):
        return clean_text(", ".join(str(item) for item in raw))
    return clean_text(str(raw or ""))


def _authors(content: dict) -> list[str]:
    raw = content.get("authors")
    if isinstance(raw, dict):
        raw = raw.get("value")
    if not isinstance(raw, list):
        return []
    return [clean_text(str(author)) for author in raw[:8] if clean_text(str(author))]


def _pdf_url(content: dict) -> str:
    pdf = _value(content, "pdf")
    if not pdf:
        return ""
    return urljoin("https://openreview.net", pdf)


def _paper_from_note(note: dict) -> PaperRecord | None:
    content = note.get("forumContent") or note.get("content") or {}
    title = _value(content, "title")
    abstract = _value(content, "abstract") or _value(content, "TLDR") or _value(content, "summary")
    if not title:
        return None
    forum = note.get("forum") or note.get("id") or ""
    url = f"https://openreview.net/forum?id={forum}" if forum else ""
    return PaperRecord(
        title=title,
        abstract=abstract,
        year=None,
        venue=_value(content, "venue"),
        authors=_authors(content),
        url=url,
        pdf_url=_pdf_url(content),
        source="openreview",
        source_records=["openreview"],
        raw={
            "openreview_id": note.get("id"),
            "forum": forum,
            "keywords": _value(content, "keywords"),
            "primary_area": _value(content, "primary_area") or _value(content, "primary_subject_area"),
        },
    )


def search_openreview(query: str, limit: int = 10) -> list[PaperRecord]:
    with get_client(timeout=30.0) as client:
        response = client.get(
            "https://api2.openreview.net/notes/search",
            params={"term": query, "limit": limit},
        )
        response.raise_for_status()
        payload = response.json()
    papers = []
    seen_forums = set()
    for note in payload.get("notes", []):
        paper = _paper_from_note(note)
        if not paper:
            continue
        forum = paper.raw.get("forum")
        if forum and forum in seen_forums:
            continue
        if forum:
            seen_forums.add(forum)
        papers.append(paper)
    return papers[:limit]
