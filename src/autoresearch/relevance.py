from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from .schema import DomainProfile, PaperRecord

EvidenceTier = Literal["core", "adjacent", "noise", "unknown"]

NORMALIZE_RE = re.compile(r"[^a-z0-9\u4e00-\u9fff]+")


@dataclass(frozen=True)
class EvidenceTierScore:
    tier: EvidenceTier
    score_delta: float = 0.0
    reasons: list[str] = field(default_factory=list)


def _paper_text(paper: PaperRecord) -> str:
    return " ".join(
        [
            paper.title,
            paper.abstract,
            paper.venue,
            paper.url,
            " ".join(paper.authors),
        ]
    )


def _normalize_words(value: str) -> list[str]:
    normalized = NORMALIZE_RE.sub(" ", value.lower()).strip()
    return [word for word in normalized.split() if word]


def _word_matches(word: str, keyword_word: str) -> bool:
    if word == keyword_word:
        return True
    return word.rstrip("s") == keyword_word.rstrip("s")


def _contains_keyword(text_words: list[str], keyword: str) -> bool:
    keyword_words = _normalize_words(keyword)
    if not keyword_words:
        return False
    if len(keyword_words) == 1:
        return any(_word_matches(word, keyword_words[0]) for word in text_words)
    window_size = len(keyword_words)
    for index in range(len(text_words) - window_size + 1):
        window = text_words[index : index + window_size]
        if all(_word_matches(word, keyword_word) for word, keyword_word in zip(window, keyword_words, strict=False)):
            return True
    return False


def _keyword_hits(text_words: list[str], keywords: list[str]) -> list[str]:
    hits: list[str] = []
    seen: set[str] = set()
    for keyword in keywords:
        normalized = " ".join(_normalize_words(keyword))
        if not normalized or normalized in seen:
            continue
        if _contains_keyword(text_words, keyword):
            hits.append(keyword)
            seen.add(normalized)
    return hits


def _paper_sources(paper: PaperRecord) -> set[str]:
    return {
        source.lower()
        for source in [paper.source, *paper.source_records]
        if source and source.strip()
    }


def _source_delta(paper: PaperRecord, profile: DomainProfile) -> tuple[float, list[str]]:
    policy = profile.source_policy
    sources = _paper_sources(paper)
    preferred = {source.lower() for source in policy.preferred_sources}
    neutral = {source.lower() for source in policy.neutral_sources}
    downrank = {source.lower() for source in policy.downrank_sources}
    disabled = {source.lower() for source in policy.disabled_sources}
    overrides = {source.lower(): weight for source, weight in policy.source_weight_overrides.items()}

    score_delta = 0.0
    reasons: list[str] = []
    for source in sorted(sources):
        if source in disabled:
            score_delta += overrides.get(source, -0.18)
            reasons.append(f"source_policy=disabled:{source}")
        elif source in downrank:
            score_delta += overrides.get(source, -0.06)
            reasons.append(f"source_policy=downrank:{source}")
        elif source in preferred:
            score_delta += overrides.get(source, 0.06)
            reasons.append(f"source_policy=preferred:{source}")
        elif source in neutral:
            score_delta += overrides.get(source, 0.0)
            reasons.append(f"source_policy=neutral:{source}")
    return score_delta, reasons


def _evidence_tier(
    core_hits: list[str],
    adjacent_hits: list[str],
    negative_hits: list[str],
) -> EvidenceTier:
    if core_hits:
        if negative_hits and len(core_hits) < 2:
            return "adjacent"
        return "core"
    if adjacent_hits:
        if negative_hits and len(negative_hits) >= len(adjacent_hits):
            return "noise"
        return "adjacent"
    if negative_hits:
        return "noise"
    return "unknown"


def _evidence_delta(tier: EvidenceTier, core_hits: list[str], adjacent_hits: list[str], negative_hits: list[str]) -> float:
    if tier == "core":
        return min(0.1 + len(core_hits) * 0.03 + len(adjacent_hits) * 0.01, 0.2)
    if tier == "adjacent":
        return min(0.03 + len(adjacent_hits) * 0.02 + len(core_hits) * 0.02, 0.1)
    if tier == "noise":
        return -min(0.1 + len(negative_hits) * 0.03, 0.22)
    return 0.0


def score_evidence_tier(paper: PaperRecord, profile: DomainProfile) -> EvidenceTierScore:
    """Label whether a paper is core, adjacent, or noisy evidence for a profile.

    The score is intentionally independent from the main ranker for now. It gives
    us a testable judgment layer before we let it influence retrieval order.
    """
    text_words = _normalize_words(_paper_text(paper))
    policy = profile.evidence_policy
    core_hits = _keyword_hits(text_words, policy.core_keywords)
    adjacent_hits = _keyword_hits(text_words, policy.adjacent_keywords)
    negative_hits = _keyword_hits(text_words, policy.negative_keywords)
    tier = _evidence_tier(core_hits, adjacent_hits, negative_hits)

    reasons: list[str] = []
    reasons.extend(f"matched core keyword: {keyword}" for keyword in core_hits)
    reasons.extend(f"matched adjacent keyword: {keyword}" for keyword in adjacent_hits)
    reasons.extend(f"matched negative keyword: {keyword}" for keyword in negative_hits)

    source_delta, source_reasons = _source_delta(paper, profile)
    reasons.extend(source_reasons)
    if not reasons:
        reasons.append("no profile evidence keyword or source policy matched")

    score_delta = _evidence_delta(tier, core_hits, adjacent_hits, negative_hits) + source_delta
    return EvidenceTierScore(tier=tier, score_delta=round(score_delta, 4), reasons=reasons)
