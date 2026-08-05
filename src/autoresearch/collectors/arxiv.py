from __future__ import annotations

import re
from urllib.parse import urlencode
from xml.etree import ElementTree

from autoresearch.http import get_client
from autoresearch.schema import PaperRecord
from autoresearch.utils import clean_text

NS = {"atom": "http://www.w3.org/2005/Atom"}


def _extract_year(published: str) -> int | None:
    match = re.match(r"(\d{4})", published or "")
    return int(match.group(1)) if match else None


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
    with get_client() as client:
        response = client.get(url)
        response.raise_for_status()
    root = ElementTree.fromstring(response.text)
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

