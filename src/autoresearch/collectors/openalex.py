from __future__ import annotations

from urllib.parse import urlencode

from autoresearch.http import get_client
from autoresearch.schema import PaperRecord
from autoresearch.utils import clean_text


def _abstract_from_inverted_index(index: dict | None) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        for pos in positions:
            words.append((int(pos), word))
    return clean_text(" ".join(word for _, word in sorted(words)))


def search_openalex(query: str, limit: int = 10) -> list[PaperRecord]:
    params = urlencode(
        {
            "search": query,
            "per-page": limit,
            "sort": "relevance_score:desc",
            "filter": "type:article",
            "select": "id,doi,title,display_name,publication_year,authorships,"
            "cited_by_count,abstract_inverted_index,open_access,primary_location",
        }
    )
    url = f"https://api.openalex.org/works?{params}"
    with get_client() as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    papers: list[PaperRecord] = []
    for item in payload.get("results", []):
        title = clean_text(item.get("title") or item.get("display_name") or "")
        doi = (item.get("doi") or "").replace("https://doi.org/", "")
        primary_location = item.get("primary_location") or {}
        source = primary_location.get("source") or {}
        venue = clean_text(source.get("display_name") or "")
        authors = [
            clean_text((authorship.get("author") or {}).get("display_name") or "")
            for authorship in item.get("authorships", [])[:8]
        ]
        oa = item.get("open_access") or {}
        pdf_url = oa.get("oa_url") or (primary_location.get("pdf_url") or "")
        landing_url = doi and f"https://doi.org/{doi}"
        papers.append(
            PaperRecord(
                title=title,
                abstract=_abstract_from_inverted_index(item.get("abstract_inverted_index")),
                year=item.get("publication_year"),
                venue=venue,
                authors=[author for author in authors if author],
                url=landing_url or item.get("id", ""),
                pdf_url=pdf_url or "",
                doi=doi,
                openalex_id=item.get("id", ""),
                citation_count=int(item.get("cited_by_count") or 0),
                source="openalex",
                source_records=["openalex"],
                raw={"open_access": oa},
            )
        )
    return papers
