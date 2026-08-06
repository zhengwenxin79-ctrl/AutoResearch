from __future__ import annotations

import os
import time
from urllib.parse import quote

import httpx

from .http import get_client
from .schema import PaperInfluence, RankedPaper
from .utils import clean_text

SEMANTIC_SCHOLAR_FIELDS = (
    "paperId,title,year,venue,citationCount,influentialCitationCount,referenceCount,"
    "isOpenAccess,openAccessPdf,fieldsOfStudy,s2FieldsOfStudy,tldr,url,externalIds"
)


def _headers() -> dict[str, str]:
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    return {"x-api-key": api_key} if api_key else {}


def _request_delay() -> float:
    return 0.15 if os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip() else 1.0


def _get_json(client: httpx.Client, url: str, params: dict[str, str]) -> dict | None:
    for attempt in range(3):
        response = client.get(url, params=params, headers=_headers())
        if response.status_code == 404:
            return None
        if response.status_code == 429 and attempt < 2:
            retry_after = response.headers.get("retry-after")
            delay = float(retry_after) if retry_after and retry_after.isdecimal() else 2.0 * (attempt + 1)
            time.sleep(delay)
            continue
        response.raise_for_status()
        return response.json()
    return None


def _paper_identifiers(row: RankedPaper) -> list[str]:
    paper = row.paper
    identifiers: list[str] = []
    if paper.doi:
        identifiers.append(f"DOI:{paper.doi}")
    if paper.arxiv_id:
        identifiers.append(f"ARXIV:{paper.arxiv_id}")
    if paper.pmid:
        identifiers.append(f"PMID:{paper.pmid}")
    return identifiers


def _fields_of_study(payload: dict) -> list[str]:
    fields = [field for field in payload.get("fieldsOfStudy") or [] if field]
    for item in payload.get("s2FieldsOfStudy") or []:
        category = item.get("category")
        if category and category not in fields:
            fields.append(category)
    return fields[:8]


def _influence_from_payload(payload: dict, *, source: str = "semantic_scholar") -> PaperInfluence:
    open_access_pdf = payload.get("openAccessPdf") or {}
    tldr = payload.get("tldr") or {}
    return PaperInfluence(
        source=source,
        paper_id=payload.get("paperId") or "",
        url=payload.get("url") or "",
        citation_count=int(payload.get("citationCount") or 0),
        influential_citation_count=int(payload.get("influentialCitationCount") or 0),
        reference_count=int(payload.get("referenceCount") or 0),
        venue=clean_text(payload.get("venue") or ""),
        is_open_access=bool(payload.get("isOpenAccess")),
        open_access_pdf=open_access_pdf.get("url") or "",
        fields_of_study=_fields_of_study(payload),
        tldr=clean_text(tldr.get("text") or "", 500),
        status="ok",
    )


def _get_paper_by_identifier(client: httpx.Client, identifier: str) -> dict | None:
    url = f"https://api.semanticscholar.org/graph/v1/paper/{quote(identifier, safe=':')}"
    return _get_json(client, url, {"fields": SEMANTIC_SCHOLAR_FIELDS})


def _match_paper_by_title(client: httpx.Client, title: str) -> dict | None:
    payload = _get_json(
        client,
        "https://api.semanticscholar.org/graph/v1/paper/search/match",
        params={"query": title, "fields": SEMANTIC_SCHOLAR_FIELDS},
    )
    if not payload:
        return None
    if payload.get("paperId"):
        return payload
    data = payload.get("data") or []
    return data[0] if data else None


def enrich_paper(row: RankedPaper) -> PaperInfluence:
    paper = row.paper
    if not paper.title:
        return PaperInfluence(source="semantic_scholar", status="skipped", error="missing title")
    try:
        with get_client(timeout=30.0) as client:
            payload = None
            for identifier in _paper_identifiers(row):
                payload = _get_paper_by_identifier(client, identifier)
                if payload:
                    break
            if payload is None:
                payload = _match_paper_by_title(client, paper.title)
            if payload is None:
                return PaperInfluence(
                    source="semantic_scholar",
                    status="not_found",
                    error="no Semantic Scholar match",
                )
            influence = _influence_from_payload(payload)
            paper.citation_count = max(paper.citation_count, influence.citation_count)
            if influence.venue and not paper.venue:
                paper.venue = influence.venue
            if influence.open_access_pdf and not paper.pdf_url:
                paper.pdf_url = influence.open_access_pdf
            paper.raw["semantic_scholar"] = payload
            return influence
    except Exception as exc:  # noqa: BLE001 - enrichment is optional and should not stop search.
        return PaperInfluence(source="semantic_scholar", status="failed", error=str(exc))


def enrich_ranked_papers(ranked: list[RankedPaper], limit: int = 20) -> dict[str, PaperInfluence]:
    influences: dict[str, PaperInfluence] = {}
    for row in ranked[:limit]:
        influences[row.paper.title] = enrich_paper(row)
        time.sleep(_request_delay())
    return influences
