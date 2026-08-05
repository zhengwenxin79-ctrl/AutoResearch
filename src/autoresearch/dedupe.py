from __future__ import annotations

from rapidfuzz import fuzz

from .schema import PaperRecord
from .utils import normalize_title


def _strong_key(paper: PaperRecord) -> tuple[str, str] | None:
    for field in ["doi", "pmid", "pmcid", "arxiv_id", "openalex_id"]:
        value = getattr(paper, field)
        if value:
            return field, value.lower().replace("https://doi.org/", "")
    return None


def _merge(existing: PaperRecord, candidate: PaperRecord) -> PaperRecord:
    data = existing.model_dump()
    candidate_data = candidate.model_dump()
    for key, value in candidate_data.items():
        if key == "source_records":
            data[key] = sorted(set(data[key]) | set(value))
        elif key == "citation_count":
            data[key] = max(data[key] or 0, value or 0)
        elif key == "abstract":
            if len(value or "") > len(data[key] or ""):
                data[key] = value
        elif not data.get(key) and value:
            data[key] = value
    data["source"] = "+".join(sorted(set(data.get("source_records") or [])))
    return PaperRecord(**data)


def dedupe_papers(papers: list[PaperRecord], fuzzy_threshold: int = 94) -> list[PaperRecord]:
    merged: list[PaperRecord] = []
    strong_index: dict[tuple[str, str], int] = {}
    for paper in papers:
        key = _strong_key(paper)
        if key and key in strong_index:
            idx = strong_index[key]
            merged[idx] = _merge(merged[idx], paper)
            continue
        normalized = normalize_title(paper.title)
        fuzzy_idx = None
        for idx, existing in enumerate(merged):
            if fuzz.ratio(normalized, normalize_title(existing.title)) >= fuzzy_threshold:
                fuzzy_idx = idx
                break
        if fuzzy_idx is not None:
            merged[fuzzy_idx] = _merge(merged[fuzzy_idx], paper)
            if key:
                strong_index[key] = fuzzy_idx
            continue
        merged.append(paper)
        if key:
            strong_index[key] = len(merged) - 1
    return merged

