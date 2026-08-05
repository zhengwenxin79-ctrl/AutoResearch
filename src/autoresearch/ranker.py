from __future__ import annotations

import math
from collections import Counter

from .schema import PaperRecord, QueryPlan, RankedPaper
from .utils import current_year, tokens

SIGNAL_TERMS = {
    "dataset",
    "benchmark",
    "evaluation",
    "metric",
    "baseline",
    "limitation",
    "gap",
    "challenge",
    "temporal",
    "longitudinal",
    "change",
    "lesion",
    "vision-language",
    "multimodal",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "the",
    "of",
    "for",
    "with",
    "using",
    "via",
    "to",
    "in",
    "on",
    "core",
    "task",
    "problem",
    "formulation",
    "methods",
    "method",
    "model",
    "models",
    "analysis",
    "architectures",
    "datasets",
    "dataset",
    "benchmarks",
    "benchmark",
    "evaluation",
    "metrics",
    "baselines",
}

MEDICAL_TERMS = {
    "medical",
    "clinical",
    "radiology",
    "radiological",
    "lesion",
    "lesions",
    "ct",
    "mri",
    "x-ray",
    "ultrasound",
    "image",
    "imaging",
    "diagnosis",
    "patient",
    "disease",
}

VLM_TERMS = {
    "vlm",
    "vision-language",
    "vision",
    "language",
    "multimodal",
    "clip",
    "foundation",
}

TEMPORAL_TERMS = {
    "temporal",
    "longitudinal",
    "change",
    "follow-up",
    "progression",
    "prior",
    "current",
}

SOURCE_WEIGHT = {
    "pubmed": 0.12,
    "arxiv": 0.1,
    "openalex": 0.08,
    "crossref": 0.06,
}


def _paper_text(paper: PaperRecord) -> str:
    return f"{paper.title} {paper.abstract} {paper.venue} {paper.url}"


def rank_papers(papers: list[PaperRecord], plan: QueryPlan, limit: int) -> list[RankedPaper]:
    query_terms = set(tokens(" ".join([plan.topic, *plan.queries]))) - STOPWORDS
    topic_terms = set(tokens(plan.topic))
    wants_medical = bool(topic_terms & MEDICAL_TERMS)
    wants_vlm = "vlm" in topic_terms or "multimodal" in topic_terms or "vision" in topic_terms
    wants_temporal = bool(topic_terms & TEMPORAL_TERMS)
    ranked: list[RankedPaper] = []
    now_year = current_year()
    for paper in papers:
        text = _paper_text(paper)
        lowered = text.lower()
        text_terms = tokens(text)
        token_set = set(text_terms)
        counts = Counter(term for term in text_terms if term not in STOPWORDS)
        overlap = sorted(query_terms & token_set)
        lexical = sum(1 + math.log(counts[term]) for term in overlap)
        lexical_norm = min(lexical / 12.0, 1.0)
        signal_hits = sorted(SIGNAL_TERMS & set(lowered.replace("/", " ").split()))
        signal_score = min(len(signal_hits) * 0.04, 0.2)
        recency = 0.0
        if paper.year:
            recency = max(0.0, 1.0 - max(now_year - paper.year, 0) / 8.0) * 0.18
        citations = min(math.log1p(max(paper.citation_count, 0)) / 8.0, 1.0) * 0.12
        source = sum(SOURCE_WEIGHT.get(src, 0.03) for src in set(paper.source_records))
        abstract_bonus = 0.08 if len(paper.abstract) > 300 else 0.0
        domain_bonus = 0.0
        penalty = 0.0
        medical_hit = bool(token_set & MEDICAL_TERMS)
        vlm_hit = bool(token_set & VLM_TERMS) or "vision-language" in lowered
        temporal_hit = bool(token_set & TEMPORAL_TERMS)
        if wants_medical:
            domain_bonus += 0.14 if medical_hit else -0.35
        if wants_vlm:
            domain_bonus += 0.1 if vlm_hit else -0.12
        if wants_temporal:
            domain_bonus += 0.08 if temporal_hit else -0.08
        if any(
            term in lowered
            for term in [
                "seismic",
                "earth",
                "quantum",
                "nisq",
                "inner core",
                "satellite",
                "remote sensing",
                "land cover",
            ]
        ):
            penalty += 0.45
        score = max(
            0.0,
            min(1.0, lexical_norm * 0.46 + signal_score + recency + citations + source + abstract_bonus + domain_bonus - penalty),
        )
        reasons = []
        if overlap:
            reasons.append("query_overlap=" + ", ".join(overlap[:8]))
        if signal_hits:
            reasons.append("research_signals=" + ", ".join(signal_hits[:6]))
        reasons.append(
            f"domain=medical:{int(medical_hit)},vlm:{int(vlm_hit)},temporal:{int(temporal_hit)}"
        )
        if paper.citation_count:
            reasons.append(f"citations={paper.citation_count}")
        if paper.year:
            reasons.append(f"year={paper.year}")
        reasons.append("sources=" + ", ".join(paper.source_records))
        ranked.append(RankedPaper(paper=paper, relevance_score=round(score, 4), score_reasons=reasons))
    return sorted(ranked, key=lambda row: row.relevance_score, reverse=True)[:limit]
