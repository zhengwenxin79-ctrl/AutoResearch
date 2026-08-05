from __future__ import annotations

from .schema import EvidenceSnippet, FieldMap, GapEvidence, PaperCard


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


def find_gaps(cards: list[PaperCard], field_map: FieldMap) -> list[GapEvidence]:
    gaps: list[GapEvidence] = []
    temporal_cards = _evidence(
        cards,
        lambda c: "temporal" in c.task or "longitudinal" in c.claimed_contribution.lower(),
        "paper explicitly touches temporal/longitudinal analysis",
    )
    static_or_general = _evidence(
        cards,
        lambda c: "temporal" not in c.task and "change" not in c.claimed_contribution.lower(),
        "candidate work appears focused on non-temporal or general medical VLM tasks",
    )
    if static_or_general:
        gaps.append(
            GapEvidence(
                gap="Lesion-level temporal reasoning is weakly covered by the retrieved medical VLM literature.",
                evidence=static_or_general[:4],
                counter_evidence=temporal_cards[:2],
                confidence=0.72 if len(static_or_general) >= 3 else 0.55,
                why_it_matters=(
                    "Temporal lesion change is central to follow-up diagnosis and treatment response, "
                    "but many candidate papers surface as single-image diagnosis, report generation, or broad VLM work."
                ),
                research_opportunity=(
                    "Build a lesion-localized temporal comparison task with paired studies and explicit change labels."
                ),
            )
        )

    no_dataset = _evidence(
        cards,
        lambda c: c.dataset == "not explicit",
        "dataset not explicit in metadata/abstract",
    )
    if no_dataset:
        gaps.append(
            GapEvidence(
                gap="Evaluation datasets and benchmark protocols are often not visible from abstracts.",
                evidence=no_dataset[:4],
                confidence=0.68 if len(no_dataset) >= 3 else 0.5,
                why_it_matters=(
                    "If dataset and metric details are not prominent, it is hard to verify whether a claimed capability "
                    "is actually evaluated under a comparable benchmark."
                ),
                research_opportunity=(
                    "Create a benchmark table that normalizes dataset, task, metric, baseline, and temporal pairing details."
                ),
            )
        )

    no_metric = _evidence(
        cards,
        lambda c: c.metrics == "not explicit",
        "metric not explicit in metadata/abstract",
    )
    if no_metric:
        gaps.append(
            GapEvidence(
                gap="Metric coverage appears under-specified for fine-grained clinical change analysis.",
                evidence=no_metric[:4],
                confidence=0.64 if len(no_metric) >= 3 else 0.48,
                why_it_matters=(
                    "Temporal lesion analysis needs more than generic text similarity or diagnosis accuracy; it needs "
                    "finding, location, direction-of-change, and consistency metrics."
                ),
                research_opportunity=(
                    "Evaluate change-label accuracy, finding/location consistency, report similarity, and mask-guided ablations."
                ),
            )
        )

    return gaps[:3]
