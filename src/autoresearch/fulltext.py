from __future__ import annotations

import hashlib
import re
from pathlib import Path

import fitz
from bs4 import BeautifulSoup

from .http import get_client
from .schema import FullTextRecord, PaperRecord, RankedPaper, TextSection
from .utils import clean_text, normalize_title

SECTION_HEADINGS = {
    "abstract",
    "introduction",
    "background",
    "related work",
    "methods",
    "method",
    "materials and methods",
    "experiments",
    "experimental setup",
    "results",
    "evaluation",
    "discussion",
    "limitations",
    "limitation",
    "conclusion",
    "conclusions",
}


def _safe_stem(title: str, index: int) -> str:
    digest = hashlib.sha1(title.encode("utf-8", errors="ignore")).hexdigest()[:10]
    slug = re.sub(r"[^a-z0-9]+", "-", normalize_title(title)).strip("-")[:80]
    return f"{index:02d}-{slug or 'paper'}-{digest}"


def _candidate_urls(paper: PaperRecord) -> list[str]:
    urls: list[str] = []
    if paper.pdf_url:
        urls.append(paper.pdf_url)
    if paper.arxiv_id:
        urls.append(f"https://arxiv.org/pdf/{paper.arxiv_id}")
    if paper.pmcid:
        urls.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{paper.pmcid}/")
    if paper.url:
        urls.append(paper.url)
    seen = set()
    return [url for url in urls if url and not (url in seen or seen.add(url))]


def _extract_pdf_text(content: bytes) -> str:
    document = fitz.open(stream=content, filetype="pdf")
    return "\n".join(page.get_text("text") for page in document)


def _extract_html_text(content: bytes) -> tuple[str, list[TextSection]]:
    soup = BeautifulSoup(content, "html.parser")
    for node in soup(["script", "style", "noscript", "nav", "footer"]):
        node.decompose()
    sections: list[TextSection] = []
    current_heading = "body"
    current_parts: list[str] = []
    for node in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = clean_text(node.get_text(" "))
        if not text:
            continue
        if node.name in {"h1", "h2", "h3"}:
            if current_parts:
                sections.append(TextSection(heading=current_heading, text=clean_text(" ".join(current_parts))))
            current_heading = text[:100]
            current_parts = []
        else:
            current_parts.append(text)
    if current_parts:
        sections.append(TextSection(heading=current_heading, text=clean_text(" ".join(current_parts))))
    return clean_text(soup.get_text(" ")), sections


def _looks_like_heading(line: str) -> bool:
    normalized = re.sub(r"^\d+(?:\.\d+)*\s+", "", clean_text(line)).lower().strip(":")
    if normalized in SECTION_HEADINGS:
        return True
    return bool(
        re.match(
            r"^(?:\d+\.?\s+)?(abstract|introduction|methods?|experiments?|results|discussion|limitations?|conclusions?)$",
            normalized,
        )
    )


def split_sections(text: str, max_section_chars: int = 9000) -> list[TextSection]:
    sections: list[TextSection] = []
    heading = "body"
    parts: list[str] = []
    for raw_line in text.splitlines():
        line = clean_text(raw_line)
        if not line:
            continue
        if len(line) < 90 and _looks_like_heading(line):
            if parts:
                sections.append(TextSection(heading=heading, text=clean_text(" ".join(parts), max_section_chars)))
            heading = re.sub(r"^\d+(?:\.\d+)*\s+", "", line).strip()
            parts = []
        else:
            parts.append(line)
    if parts:
        sections.append(TextSection(heading=heading, text=clean_text(" ".join(parts), max_section_chars)))
    if not sections and text:
        sections.append(TextSection(heading="body", text=clean_text(text, max_section_chars)))
    return sections[:20]


def fetch_full_text(paper: PaperRecord, raw_dir: Path, index: int, max_chars: int = 180_000) -> FullTextRecord:
    raw_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_stem(paper.title, index)
    candidates = _candidate_urls(paper)
    if not candidates:
        return FullTextRecord(title=paper.title, source_url=paper.url, status="skipped", error="No full-text candidate URL.")

    last_error = ""
    with get_client(timeout=30.0) as client:
        for url in candidates:
            try:
                response = client.get(url)
                response.raise_for_status()
            except Exception as exc:  # noqa: BLE001 - individual fetch failures should not stop search.
                last_error = str(exc)
                continue
            content_type = response.headers.get("content-type", "")
            lower_url = str(response.url).lower()
            is_pdf = "pdf" in content_type.lower() or lower_url.endswith(".pdf")
            suffix = ".pdf" if is_pdf else ".html"
            raw_path = raw_dir / f"{stem}{suffix}"
            raw_path.write_bytes(response.content)
            try:
                if is_pdf:
                    text = _extract_pdf_text(response.content)
                    sections = split_sections(text)
                else:
                    text, html_sections = _extract_html_text(response.content)
                    sections = html_sections or split_sections(text)
            except Exception as exc:  # noqa: BLE001 - parsers can raise library-specific errors.
                return FullTextRecord(
                    title=paper.title,
                    source_url=paper.url,
                    fetched_url=str(response.url),
                    raw_path=str(raw_path),
                    status="failed",
                    content_type=content_type,
                    error=f"text extraction failed: {exc}",
                )
            text = text[:max_chars]
            text_path = raw_dir / f"{stem}.txt"
            text_path.write_text(text, encoding="utf-8", errors="ignore")
            return FullTextRecord(
                title=paper.title,
                source_url=paper.url,
                fetched_url=str(response.url),
                raw_path=str(raw_path),
                text_path=str(text_path),
                status="ok",
                content_type=content_type,
                sections=sections,
            )
    return FullTextRecord(title=paper.title, source_url=paper.url, status="failed", error=last_error)


def fetch_full_texts(ranked: list[RankedPaper], raw_dir: Path, limit: int = 8) -> dict[str, FullTextRecord]:
    records: dict[str, FullTextRecord] = {}
    for index, row in enumerate(ranked[:limit], start=1):
        records[row.paper.title] = fetch_full_text(row.paper, raw_dir=raw_dir, index=index)
    return records
