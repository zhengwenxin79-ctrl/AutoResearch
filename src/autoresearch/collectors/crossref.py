from __future__ import annotations

from urllib.parse import urlencode

from bs4 import BeautifulSoup

from autoresearch.http import get_client
from autoresearch.schema import PaperRecord
from autoresearch.utils import clean_text


def _first(value: list | None) -> str:
    return clean_text(str(value[0])) if value else ""


def _year(item: dict) -> int | None:
    parts = (
        item.get("published-print")
        or item.get("published-online")
        or item.get("published")
        or {}
    ).get("date-parts") or []
    if parts and parts[0]:
        return int(parts[0][0])
    return None


def search_crossref(query: str, limit: int = 10) -> list[PaperRecord]:
    params = urlencode(
        {
            "query.bibliographic": query,
            "rows": limit,
            "select": "DOI,title,abstract,published-print,published-online,published,"
            "container-title,author,is-referenced-by-count,URL",
        }
    )
    url = f"https://api.crossref.org/works?{params}"
    with get_client() as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    papers: list[PaperRecord] = []
    for item in payload.get("message", {}).get("items", []):
        title = _first(item.get("title"))
        raw_abstract = item.get("abstract") or ""
        abstract = clean_text(BeautifulSoup(raw_abstract, "html.parser").get_text(" "))
        authors = []
        for author in item.get("author", [])[:8]:
            name = clean_text(" ".join(p for p in [author.get("given", ""), author.get("family", "")] if p))
            if name:
                authors.append(name)
        doi = clean_text(item.get("DOI", ""))
        papers.append(
            PaperRecord(
                title=title,
                abstract=abstract,
                year=_year(item),
                venue=_first(item.get("container-title")),
                authors=authors,
                url=item.get("URL") or (f"https://doi.org/{doi}" if doi else ""),
                doi=doi,
                citation_count=int(item.get("is-referenced-by-count") or 0),
                source="crossref",
                source_records=["crossref"],
                raw={"crossref_score": item.get("score")},
            )
        )
    return [paper for paper in papers if paper.title]

