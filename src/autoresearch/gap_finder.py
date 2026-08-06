from __future__ import annotations

import math
from collections.abc import Callable

from .schema import EvidenceSnippet, FieldMap, GapEvidence, GapPaperJudgment, PaperCard

FULL_TEXT_SECTIONS = {
    "methods",
    "method",
    "materials and methods",
    "experiments",
    "experimental setup",
    "evaluation",
    "results",
    "discussion",
    "limitations",
    "limitation",
    "body",
}


def _has_tag(card: PaperCard, tag: str) -> bool:
    return tag in card.coverage_tags


def _first_evidence(card: PaperCard, claim: str) -> EvidenceSnippet:
    if card.evidence_snippets:
        snippet = card.evidence_snippets[0]
        return EvidenceSnippet(
            paper_title=card.title,
            source_url=card.url,
            claim=claim,
            snippet=snippet.snippet,
            section=snippet.section,
        )
    return EvidenceSnippet(
        paper_title=card.title,
        source_url=card.url,
        claim=claim,
        snippet=card.claimed_contribution,
    )


def _full_text_count(snippets: list[EvidenceSnippet]) -> int:
    return sum(1 for snippet in snippets if snippet.section.lower() in FULL_TEXT_SECTIONS)


def _influence_score(card: PaperCard) -> tuple[float, list[str]]:
    influence = card.influence
    if not influence or influence.status != "ok":
        return 0.0, ["Semantic Scholar enrichment unavailable"]
    citation_score = min(math.log1p(influence.citation_count) / 8.0, 1.0) * 0.55
    influential_score = min(math.log1p(influence.influential_citation_count) / 5.0, 1.0) * 0.25
    reference_score = min(math.log1p(influence.reference_count) / 6.0, 1.0) * 0.1
    open_access_score = 0.1 if influence.open_access_pdf else 0.0
    reasons = [
        f"citations={influence.citation_count}",
        f"influential_citations={influence.influential_citation_count}",
        f"references={influence.reference_count}",
    ]
    if influence.open_access_pdf:
        reasons.append("open_access_pdf=available")
    if influence.venue:
        reasons.append(f"venue={influence.venue}")
    return round(citation_score + influential_score + reference_score + open_access_score, 3), reasons


def _missing_lesion_temporal(card: PaperCard) -> list[str]:
    missing = []
    if not _has_tag(card, "temporal_or_change"):
        missing.append("no explicit temporal/change signal")
    if not _has_tag(card, "lesion_or_localization"):
        missing.append("no explicit lesion/localization signal")
    return missing


def _missing_dataset_benchmark(card: PaperCard) -> list[str]:
    missing = []
    if not _has_tag(card, "dataset_explicit"):
        missing.append("dataset not explicit")
    if not _has_tag(card, "benchmark_or_evaluation"):
        missing.append("benchmark/evaluation protocol not explicit")
    return missing


def _missing_metric(card: PaperCard) -> list[str]:
    if not _has_tag(card, "metric_explicit"):
        return ["metric not explicit"]
    return []


def _judge_card(
    card: PaperCard,
    *,
    support_predicate: Callable[[PaperCard], bool],
    counter_predicate: Callable[[PaperCard], bool],
    support_claim: str,
    counter_claim: str,
    missing_builder: Callable[[PaperCard], list[str]],
) -> GapPaperJudgment:
    influence_score, influence_reasons = _influence_score(card)
    if counter_predicate(card):
        evidence = _first_evidence(card, counter_claim)
        return GapPaperJudgment(
            paper_title=card.title,
            source_url=card.url,
            decision="yes",
            role="counter",
            rationale="The extracted card contains the signals this gap expects to be missing.",
            evidence=evidence,
            influence_score=influence_score,
            influence_reasons=influence_reasons,
        )
    if support_predicate(card):
        evidence = _first_evidence(card, support_claim)
        missing = missing_builder(card)
        return GapPaperJudgment(
            paper_title=card.title,
            source_url=card.url,
            decision="no",
            role="support",
            rationale="The extracted card is missing one or more required signals for this capability.",
            evidence=evidence,
            missing_evidence=missing,
            influence_score=influence_score,
            influence_reasons=influence_reasons,
        )
    evidence = _first_evidence(card, "insufficient evidence to judge whether this paper addresses the gap")
    return GapPaperJudgment(
        paper_title=card.title,
        source_url=card.url,
        decision="unclear",
        role="unclear",
        rationale="The extracted signals are mixed or insufficient for a rule-based judgment.",
        evidence=evidence,
        missing_evidence=missing_builder(card),
        influence_score=influence_score,
        influence_reasons=influence_reasons,
    )


def _confidence(
    total: int,
    support_count: int,
    counter_count: int,
    full_text_count: int,
    influential_counter_count: int = 0,
    base: float = 0.42,
) -> tuple[float, list[str]]:
    if total == 0:
        return 0.0, ["no papers available"]
    support_ratio = support_count / total
    counter_ratio = counter_count / total
    full_text_bonus = min(full_text_count, 3) * 0.05
    influential_counter_penalty = min(influential_counter_count, 3) * 0.04
    confidence = (
        base
        + support_ratio * 0.42
        - counter_ratio * 0.25
        + full_text_bonus
        - influential_counter_penalty
    )
    confidence = max(0.15, min(0.92, confidence))
    reasons = [
        f"{support_count}/{total} papers support or expose this weakness",
        f"{counter_count}/{total} papers provide counter-evidence",
    ]
    if full_text_count:
        reasons.append(f"{full_text_count} evidence snippets come from full-text sections")
    else:
        reasons.append("evidence is mostly abstract/metadata-level")
    if influential_counter_count:
        reasons.append(f"{influential_counter_count} counter-evidence papers have notable influence signals")
    return round(confidence, 2), reasons


def _build_gap(
    *,
    gap: str,
    cards: list[PaperCard],
    support_predicate,
    counter_predicate,
    support_claim: str,
    counter_claim: str,
    missing_builder: Callable[[PaperCard], list[str]],
    why_it_matters: str,
    research_opportunity: str,
    base: float = 0.42,
) -> GapEvidence | None:
    judgments = [
        _judge_card(
            card,
            support_predicate=support_predicate,
            counter_predicate=counter_predicate,
            support_claim=support_claim,
            counter_claim=counter_claim,
            missing_builder=missing_builder,
        )
        for card in cards
    ]
    supporting = [judgment for judgment in judgments if judgment.role == "support"]
    counters = [judgment for judgment in judgments if judgment.role == "counter"]
    if not supporting:
        return None
    evidence = [judgment.evidence for judgment in supporting[:4] if judgment.evidence]
    counter_evidence = [judgment.evidence for judgment in counters[:3] if judgment.evidence]
    total = len(cards)
    support_count = len(supporting)
    counter_count = len(counters)
    full_text_count = _full_text_count(evidence)
    influential_counter_count = sum(1 for judgment in counters if judgment.influence_score >= 0.35)
    confidence, reasons = _confidence(
        total,
        support_count,
        counter_count,
        full_text_count,
        influential_counter_count=influential_counter_count,
        base=base,
    )
    support_ratio = round(support_count / total, 2) if total else 0.0
    counter_ratio = round(counter_count / total, 2) if total else 0.0
    unclear_count = max(0, total - support_count - counter_count)
    return GapEvidence(
        gap=gap,
        evidence=evidence,
        counter_evidence=counter_evidence,
        confidence=confidence,
        support_count=support_count,
        counter_count=counter_count,
        unclear_count=unclear_count,
        total_papers=total,
        support_ratio=support_ratio,
        counter_ratio=counter_ratio,
        full_text_evidence_count=full_text_count,
        score_reasons=reasons,
        paper_judgments=judgments,
        why_it_matters=why_it_matters,
        research_opportunity=research_opportunity,
    )


def find_gaps(cards: list[PaperCard], field_map: FieldMap) -> list[GapEvidence]:
    gaps: list[GapEvidence] = []

    lesion_temporal_gap = _build_gap(
        gap="Lesion-level temporal reasoning is weakly covered by the retrieved medical VLM literature.",
        cards=cards,
        support_predicate=lambda c: not (
            _has_tag(c, "temporal_or_change") and _has_tag(c, "lesion_or_localization")
        ),
        counter_predicate=lambda c: _has_tag(c, "temporal_or_change")
        and _has_tag(c, "lesion_or_localization"),
        support_claim="candidate work does not clearly combine temporal/change reasoning with lesion-level localization",
        counter_claim="paper contains both temporal/change and lesion/localization signals",
        missing_builder=_missing_lesion_temporal,
        why_it_matters=(
            "Temporal lesion change is central to follow-up diagnosis and treatment response, "
            "but many candidate papers surface as single-image diagnosis, report generation, or broad VLM work."
        ),
        research_opportunity="Build a lesion-localized temporal comparison task with paired studies and explicit change labels.",
        base=0.38,
    )
    if lesion_temporal_gap:
        gaps.append(lesion_temporal_gap)

    dataset_gap = _build_gap(
        gap="Evaluation datasets and benchmark protocols are often under-specified or not comparable.",
        cards=cards,
        support_predicate=lambda c: _has_tag(c, "dataset_missing") or not _has_tag(c, "benchmark_or_evaluation"),
        counter_predicate=lambda c: _has_tag(c, "dataset_explicit") and _has_tag(c, "benchmark_or_evaluation"),
        support_claim="dataset or benchmark protocol is not explicit in the extracted card",
        counter_claim="paper exposes dataset and benchmark/evaluation signals",
        missing_builder=_missing_dataset_benchmark,
        why_it_matters=(
            "If dataset and protocol details are not prominent, it is hard to verify whether a claimed capability "
            "is actually evaluated under a comparable benchmark."
        ),
        research_opportunity=(
            "Create a benchmark table that normalizes dataset, task, metric, baseline, and temporal pairing details."
        ),
        base=0.4,
    )
    if dataset_gap:
        gaps.append(dataset_gap)

    metric_gap = _build_gap(
        gap="Metric coverage appears under-specified for fine-grained clinical change analysis.",
        cards=cards,
        support_predicate=lambda c: _has_tag(c, "metric_missing"),
        counter_predicate=lambda c: _has_tag(c, "metric_explicit"),
        support_claim="metric not explicit in the extracted card",
        counter_claim="paper exposes at least one evaluation metric",
        missing_builder=_missing_metric,
        why_it_matters=(
            "Temporal lesion analysis needs more than generic text similarity or diagnosis accuracy; it needs "
            "finding, location, direction-of-change, and consistency metrics."
        ),
        research_opportunity=(
            "Evaluate change-label accuracy, finding/location consistency, report similarity, and mask-guided ablations."
        ),
        base=0.36,
    )
    if metric_gap:
        gaps.append(metric_gap)

    return gaps[:3]
