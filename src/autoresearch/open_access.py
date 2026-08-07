from __future__ import annotations

import os
import time
from urllib.parse import quote

from .http import get_client
from .schema import OpenAccessRecord, RankedPaper
from .utils import clean_text


def _email() -> str:
    return os.getenv("UNPAYWALL_EMAIL", "").strip()


def _best_oa_location(payload: dict) -> dict:
    best = payload.get("best_oa_location") or {}
    if best:
        return best
    locations = payload.get("oa_locations") or []
    return locations[0] if locations else {}


def _record_from_payload(title: str, doi: str, payload: dict) -> OpenAccessRecord:
    location = _best_oa_location(payload)
    return OpenAccessRecord(
        title=title,
        doi=doi,
        status="ok",
        is_open_access=bool(payload.get("is_oa")),
        landing_page_url=location.get("url_for_landing_page") or "",
        pdf_url=location.get("url_for_pdf") or "",
        evidence=clean_text(location.get("evidence") or payload.get("oa_status") or ""),
    )


def enrich_open_access(ranked: list[RankedPaper], limit: int = 20) -> dict[str, OpenAccessRecord]:
    email = _email()
    records: dict[str, OpenAccessRecord] = {}
    if limit <= 0:
        return records

    for row in ranked[:limit]:
        paper = row.paper
        if not paper.doi:
            records[paper.title] = OpenAccessRecord(
                title=paper.title,
                status="skipped",
                error="missing DOI",
            )
            continue
        if not email:
            records[paper.title] = OpenAccessRecord(
                title=paper.title,
                doi=paper.doi,
                status="skipped",
                error="UNPAYWALL_EMAIL is not configured",
            )
            continue
        try:
            with get_client(timeout=30.0) as client:
                response = client.get(
                    f"https://api.unpaywall.org/v2/{quote(paper.doi, safe='')}",
                    params={"email": email},
                )
                if response.status_code == 404:
                    records[paper.title] = OpenAccessRecord(
                        title=paper.title,
                        doi=paper.doi,
                        status="not_found",
                        error="DOI not found in Unpaywall",
                    )
                    continue
                response.raise_for_status()
                record = _record_from_payload(paper.title, paper.doi, response.json())
                if record.pdf_url and not paper.pdf_url:
                    paper.pdf_url = record.pdf_url
                if record.landing_page_url and not paper.url:
                    paper.url = record.landing_page_url
                paper.raw["unpaywall"] = record.model_dump()
                records[paper.title] = record
        except Exception as exc:  # noqa: BLE001 - OA enrichment should not stop search.
            records[paper.title] = OpenAccessRecord(
                title=paper.title,
                doi=paper.doi,
                status="failed",
                error=str(exc),
            )
        time.sleep(0.2)
    return records
