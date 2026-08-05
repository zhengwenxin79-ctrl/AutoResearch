from __future__ import annotations

from .schema import EvidenceSnippet, FieldMap, GapEvidence, PaperCard

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


def _evidence(cards: list[PaperCard], predicate, claim: str, limit: int = 4) -> list[EvidenceSnippet]:
    snippets: list[EvidenceSnippet] = []
    for card in cards:
        if not predicate(card):
            continue
        snippet = card.evidence_snippets[0].snippet if card.evidence_snippets else card.claimed_contribution
        snippets.append(
            EvidenceSnippet(
                paper_title=card.title,
                source_url=card.url,
                claim=claim,
                snippet=snippet,
                section=card.evidence_snippets[0].section if card.evidence_snippets else "",
            )
        )
        if len(snippets) >= limit:
            break
    return snippets


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


def _confidence(
    total: int,
    support_count: int,
    counter_count: int,
    full_text_count: int,
    base: float = 0.42,
) -> tuple[float, list[str]]:
    if total == 0:
        return 0.0, ["no papers available"]
    support_ratio = support_count / total
    counter_ratio = counter_count / total
    full_text_bonus = min(full_text_count, 3) * 0.05
    confidence = base + support_ratio * 0.42 - counter_ratio * 0.25 + full_text_bonus
    confidence = max(0.15, min(0.92, confidence))
    reasons = [
        f"{support_count}/{total} papers support or expose this weakness",
        f"{counter_count}/{total} papers provide counter-evidence",
    ]
    if full_text_count:
        reasons.append(f"{full_text_count} evidence snippets come from full-text sections")
    else:
        reasons.append("evidence is mostly abstract/metadata-level")
    return round(confidence, 2), reasons


def _build_gap(
    *,
    gap: str,
    cards: list[PaperCard],
    support_predicate,
    counter_predicate,
    support_claim: str,
    counter_claim: str,
    why_it_matters: str,
    research_opportunity: str,
    base: float = 0.42,
) -> GapEvidence | None:
    supporting = [card for card in cards if support_predicate(card)]
    counters = [card for card in cards if counter_predicate(card)]
    if not supporting:
        return None
    evidence = [_first_evidence(card, support_claim) for card in supporting[:4]]
    counter_evidence = [_first_evidence(card, counter_claim) for card in counters[:3]]
    total = len(cards)
    support_count = len(supporting)
    counter_count = len(counters)
    full_text_count = _full_text_count(evidence)
    confidence, reasons = _confidence(
        total,
        support_count,
        counter_count,
        full_text_count,
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
