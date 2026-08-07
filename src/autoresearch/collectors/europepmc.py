from __future__ import annotations

from urllib.parse import urlencode

from autoresearch.http import get_client
from autoresearch.schema import PaperRecord
from autoresearch.utils import clean_text


def _first_full_text_url(item: dict) -> str:
    entries = ((item.get("fullTextUrlList") or {}).get("fullTextUrl")) or []
    for entry in entries:
        url = entry.get("url") or ""
        if url:
            return url
    return ""


def _authors(item: dict) -> list[str]:
    author_string = item.get("authorString") or ""
    if not author_string:
        return []
    return [clean_text(part) for part in author_string.split(",")[:8] if clean_text(part)]


def _expanded_query(query: str) -> str:
    if "vlm" not in query.lower() and "vision-language" not in query.lower():
        return query
    return (
        '("vision language" OR "vision-language" OR multimodal) '
        "AND (medical OR radiology OR lesion) "
        "AND (temporal OR longitudinal OR change OR benchmark)"
    )


def _search_once(query: str, limit: int) -> list[PaperRecord]:
    params = urlencode(
        {
            "query": query,
            "format": "json",
            "pageSize": limit,
            "resultType": "core",
        }
    )
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{params}"
    with get_client() as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()

    papers: list[PaperRecord] = []
    for item in (payload.get("resultList") or {}).get("result", []):
        title = clean_text(item.get("title") or "")
        if not title:
            continue
        year_text = str(item.get("pubYear") or "")
        doi = clean_text(item.get("doi") or "")
        pmid = clean_text(item.get("pmid") or "")
        pmcid = clean_text(item.get("pmcid") or "")
        full_text_url = _first_full_text_url(item)
        papers.append(
            PaperRecord(
                title=title,
                abstract=clean_text(item.get("abstractText") or ""),
                year=int(year_text) if year_text.isdigit() else None,
                venue=clean_text(item.get("journalTitle") or ""),
                authors=_authors(item),
                url=full_text_url or (f"https://europepmc.org/article/MED/{pmid}" if pmid else ""),
                pdf_url=full_text_url if full_text_url.lower().endswith(".pdf") else "",
                doi=doi,
                pmid=pmid,
                pmcid=pmcid,
                citation_count=int(item.get("citedByCount") or 0),
                source="europepmc",
                source_records=["europepmc"],
                raw={
                    "source": item.get("source"),
                    "is_open_access": item.get("isOpenAccess"),
                    "full_text_url": full_text_url,
                },
            )
        )
    return papers


def search_europepmc(query: str, limit: int = 10) -> list[PaperRecord]:
    papers = _search_once(query, limit)
    if papers:
        return papers
    expanded = _expanded_query(query)
    if expanded == query:
        return []
    return _search_once(expanded, limit)
