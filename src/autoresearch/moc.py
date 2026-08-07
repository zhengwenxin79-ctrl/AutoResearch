from __future__ import annotations

from collections import defaultdict

from .schema import (
    ComparisonMatrix,
    ComparisonRow,
    EvidenceSnippet,
    GapEvidence,
    MOCGroup,
    PaperCard,
    PaperInsightCard,
    TopicMOC,
)
from .utils import clean_text, tokens

GROUP_TEMPORAL_LESION = "Lesion-level temporal reasoning candidates"
GROUP_LONGITUDINAL = "Longitudinal medical imaging"
GROUP_REPORT = "Medical report generation"
GROUP_LOCALIZATION = "Lesion localization / grounding"
GROUP_BENCHMARK = "Benchmark / evaluation"
GROUP_DIAGNOSIS = "Single-image medical VLM diagnosis / VQA"
GROUP_GENERAL = "General medical VLM / foundation work"


GROUP_SOLVES = {
    GROUP_TEMPORAL_LESION: [
        "Connects temporal/change signals with lesion or localization signals.",
        "Provides the closest evidence for whether the target weakness is already addressed.",
    ],
    GROUP_LONGITUDINAL: [
        "Models temporal, longitudinal, follow-up, or change-oriented medical imaging signals.",
    ],
    GROUP_REPORT: [
        "Targets radiology or medical report generation and clinical text quality.",
    ],
    GROUP_LOCALIZATION: [
        "Grounds medical findings through lesions, masks, segmentation, localization, or regions.",
    ],
    GROUP_BENCHMARK: [
        "Makes datasets, metrics, or evaluation protocols explicit.",
    ],
    GROUP_DIAGNOSIS: [
        "Solves image-level diagnosis, classification, or VQA-style medical VLM tasks.",
    ],
    GROUP_GENERAL: [
        "Provides broad foundation-model or multimodal medical AI context.",
    ],
}

GROUP_MISSING = {
    GROUP_TEMPORAL_LESION: [
        "May still lack paired-study benchmarks, change-direction metrics, or explicit lesion tracking.",
    ],
    GROUP_LONGITUDINAL: [
        "Often lacks instruction-following VLM framing or lesion-grounded interaction.",
    ],
    GROUP_REPORT: [
        "Report-level metrics may not prove lesion-location or change-direction correctness.",
    ],
    GROUP_LOCALIZATION: [
        "Static localization does not necessarily evaluate temporal lesion change.",
    ],
    GROUP_BENCHMARK: [
        "Benchmark visibility does not guarantee the benchmark covers real clinical workflows.",
    ],
    GROUP_DIAGNOSIS: [
        "Image-level diagnosis/VQA may not test temporal comparison or lesion-level grounding.",
    ],
    GROUP_GENERAL: [
        "Broad capability claims may not isolate the target clinical reasoning ability.",
    ],
}

GROUP_ASSUMPTIONS = {
    GROUP_TEMPORAL_LESION: [
        "Temporal and lesion signals in the paper correspond to a real paired-study reasoning task.",
    ],
    GROUP_LONGITUDINAL: [
        "Task-specific longitudinal modelling transfers to VLM-style research questions.",
    ],
    GROUP_REPORT: [
        "Report text is a sufficient proxy for clinically meaningful visual change.",
    ],
    GROUP_LOCALIZATION: [
        "Static region grounding is enough to support downstream temporal reasoning.",
    ],
    GROUP_BENCHMARK: [
        "A named dataset or metric is a reliable proxy for the capability being claimed.",
    ],
    GROUP_DIAGNOSIS: [
        "Single-image medical VLM competence transfers to follow-up comparison settings.",
    ],
    GROUP_GENERAL: [
        "General multimodal medical capability transfers to specific lesion-level workflows.",
    ],
}

GROUP_PROBLEM_SPACE = {
    GROUP_TEMPORAL_LESION: "lesion-level temporal change reasoning",
    GROUP_LONGITUDINAL: "longitudinal medical imaging and follow-up comparison",
    GROUP_REPORT: "clinical report generation and textual finding description",
    GROUP_LOCALIZATION: "lesion localization, grounding, masking, and region-level evidence",
    GROUP_BENCHMARK: "benchmark and evaluation design for medical multimodal systems",
    GROUP_DIAGNOSIS: "single-study medical VLM diagnosis, classification, and VQA",
    GROUP_GENERAL: "general medical multimodal foundation-model capability",
}

GROUP_COVERED = {
    GROUP_TEMPORAL_LESION: [
        "temporal or change-oriented signals",
        "lesion, finding, mask, or localization signals",
    ],
    GROUP_LONGITUDINAL: [
        "longitudinal or follow-up medical image understanding",
    ],
    GROUP_REPORT: [
        "report-level clinical finding description",
    ],
    GROUP_LOCALIZATION: [
        "lesion or finding-level grounding",
    ],
    GROUP_BENCHMARK: [
        "explicit dataset, metric, or evaluation framing",
    ],
    GROUP_DIAGNOSIS: [
        "single-study image understanding or medical VQA",
    ],
    GROUP_GENERAL: [
        "broad medical multimodal capability context",
    ],
}


def _has_tag(card: PaperCard, tag: str) -> bool:
    return tag in card.coverage_tags


def group_for_card(card: PaperCard) -> str:
    task = card.task.lower()
    method = card.method.lower()
    if _has_tag(card, "temporal_or_change") and _has_tag(card, "lesion_or_localization"):
        return GROUP_TEMPORAL_LESION
    if "temporal" in task or _has_tag(card, "temporal_or_change"):
        return GROUP_LONGITUDINAL
    if "report generation" in task:
        return GROUP_REPORT
    if "localization" in task or "segmentation" in task or "mask-guided" in method:
        return GROUP_LOCALIZATION
    if _has_tag(card, "benchmark_or_evaluation") and (
        _has_tag(card, "dataset_explicit") or _has_tag(card, "metric_explicit")
    ):
        return GROUP_BENCHMARK
    if "visual question answering" in task or "diagnosis" in task or "classification" in task:
        return GROUP_DIAGNOSIS
    return GROUP_GENERAL


def _primary_evidence(card: PaperCard) -> EvidenceSnippet | None:
    return card.evidence_snippets[0] if card.evidence_snippets else None


def _evidence_summary(card: PaperCard) -> str:
    parts = []
    if card.dataset != "not explicit":
        parts.append(f"dataset={card.dataset}")
    if card.metrics != "not explicit":
        parts.append(f"metrics={card.metrics}")
    if card.evidence_snippets:
        section = card.evidence_snippets[0].section or "metadata"
        parts.append(f"evidence_section={section}")
    return "; ".join(parts) if parts else "Evidence is weak or not explicit in extracted metadata."


def _limitation_for(card: PaperCard, group: str) -> str:
    if card.missing_capability and card.missing_capability != "not obvious from extracted metadata":
        return card.missing_capability
    if card.limitation:
        return card.limitation
    missing = []
    if not _has_tag(card, "temporal_or_change"):
        missing.append("temporal/change setting is not explicit")
    if not _has_tag(card, "lesion_or_localization"):
        missing.append("lesion/localization grounding is not explicit")
    if _has_tag(card, "dataset_missing"):
        missing.append("dataset is not explicit")
    if _has_tag(card, "metric_missing"):
        missing.append("metric is not explicit")
    if missing:
        return "; ".join(missing)
    return GROUP_MISSING[group][0]


def _relation_to_others(group: str) -> list[str]:
    if group == GROUP_DIAGNOSIS:
        return [
            f"Contrasts with {GROUP_LONGITUDINAL}: diagnosis/VQA papers often test static inputs.",
            f"Needs {GROUP_LOCALIZATION} to become lesion-grounded.",
        ]
    if group == GROUP_REPORT:
        return [
            f"Complements {GROUP_LOCALIZATION}: reports describe findings but may not ground them spatially.",
            f"Contrasts with {GROUP_BENCHMARK}: text metrics may not measure clinical change correctness.",
        ]
    if group == GROUP_LOCALIZATION:
        return [
            f"Complements {GROUP_LONGITUDINAL}: localization can provide the unit of temporal comparison.",
        ]
    if group == GROUP_LONGITUDINAL:
        return [
            f"Complements {GROUP_LOCALIZATION}: temporal models need lesion-level anchors.",
            f"Contrasts with {GROUP_DIAGNOSIS}: follow-up comparison is not the same as single-image diagnosis.",
        ]
    if group == GROUP_BENCHMARK:
        return [
            "Links method papers to measurable capabilities and exposes metric mismatch.",
        ]
    if group == GROUP_TEMPORAL_LESION:
        return [
            "Acts as the closest counter-evidence class for lesion-level temporal reasoning gaps.",
        ]
    return [
        "Provides background context but needs comparison against task-specific groups.",
    ]


def _inspiration_for(group: str) -> str:
    if group == GROUP_TEMPORAL_LESION:
        return "Inspect whether temporal and lesion signals are truly coupled in the task, method, and evaluation."
    if group == GROUP_LONGITUDINAL:
        return "Convert longitudinal modelling into an instruction-following paired-study VLM setting."
    if group == GROUP_REPORT:
        return "Add lesion/location consistency checks to report-level change descriptions."
    if group == GROUP_LOCALIZATION:
        return "Use masks or regions as anchors for T1-to-T2 visual comparison."
    if group == GROUP_BENCHMARK:
        return "Normalize datasets, metrics, and baselines into a capability-oriented benchmark table."
    if group == GROUP_DIAGNOSIS:
        return "Test whether static VLM diagnosis capability survives paired temporal comparison."
    return "Use broad foundation-model claims as context, then isolate a measurable clinical capability."


def _experimentable_gap_for(group: str, card: PaperCard) -> str:
    if group in {GROUP_DIAGNOSIS, GROUP_REPORT, GROUP_LOCALIZATION, GROUP_LONGITUDINAL}:
        return (
            "Evaluate lesion-grounded temporal change with no-mask vs T1-mask vs T2-mask-upper-bound "
            "ablations and finding/location/change-direction metrics."
        )
    if group == GROUP_BENCHMARK:
        return (
            "Build a comparison table showing which benchmarks cover image-level, report-level, "
            "lesion-level, and temporal-change dimensions."
        )
    if _has_tag(card, "metric_missing"):
        return "Design metrics that separate generic performance from the target clinical reasoning ability."
    return "Audit whether the claimed capability is evaluated under the target workflow."


def build_paper_insights(cards: list[PaperCard]) -> list[PaperInsightCard]:
    insights: list[PaperInsightCard] = []
    for card in cards:
        group = group_for_card(card)
        insight = PaperInsightCard(
            title=card.title,
            url=card.url,
            group=group,
            problem=card.problem or f"{card.task} in the {group.lower()} problem space.",
            method_core=card.method_family or card.method,
            evidence=_evidence_summary(card),
            assumption=card.core_assumption or GROUP_ASSUMPTIONS[group][0],
            limitation=_limitation_for(card, group),
            relation_to_others=_relation_to_others(group),
            inspiration=card.gap_hint or _inspiration_for(group),
            experimentable_gap=_experimentable_gap_for(group, card),
            evidence_snippet=_primary_evidence(card),
        )
        insights.append(insight)
    return insights


def _concepts_from_topic(topic: str, insights: list[PaperInsightCard]) -> list[str]:
    concepts = []
    for term in tokens(topic):
        if len(term) > 2 and term not in concepts:
            concepts.append(term)
    for insight in insights:
        for value in [insight.group, insight.method_core]:
            for term in tokens(value):
                if len(term) > 3 and term not in concepts:
                    concepts.append(term)
    return concepts[:16]


def _paper_groups(insights: list[PaperInsightCard]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for insight in insights:
        groups[insight.group].append(insight.title)
    return dict(groups)


def _common_method_patterns(cards: list[PaperCard]) -> list[str]:
    counts: dict[str, int] = defaultdict(int)
    for card in cards:
        counts[card.method] += 1
    patterns = [
        f"{method}: {count} papers"
        for method, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)
    ]
    return patterns[:8]


def _shared_assumptions(insights: list[PaperInsightCard]) -> list[str]:
    assumptions = []
    for insight in insights:
        if insight.assumption not in assumptions:
            assumptions.append(insight.assumption)
    return assumptions[:8]


def _open_questions(gaps: list[GapEvidence]) -> list[str]:
    questions = [f"Is this weakness real after counter-evidence resolution: {gap.gap}" for gap in gaps]
    questions.extend(
        [
            "Which paper group provides the strongest counter-evidence, and does it fully address the target workflow?",
            "Which missing dimension can be turned into a clean benchmark or ablation?",
            "Are existing metrics measuring the target ability or only a nearby proxy?",
        ]
    )
    return questions[:8]


def _related_themes(cards: list[PaperCard]) -> list[str]:
    themes = []
    for card in cards:
        for value in [card.task, card.method, card.dataset, card.metrics]:
            if value and value != "not explicit" and value not in themes:
                themes.append(value)
    return themes[:12]


def _dedupe(values: list[str], limit: int = 8) -> list[str]:
    deduped = []
    for value in values:
        if value and value != "not explicit" and value not in deduped:
            deduped.append(value)
    return deduped[:limit]


def _split_capabilities(values: list[str]) -> list[str]:
    capabilities = []
    for value in values:
        for part in value.split(";"):
            cleaned = part.strip()
            if cleaned and cleaned != "not obvious from extracted metadata":
                capabilities.append(cleaned)
    return capabilities


def _capability_state(cards: list[PaperCard], tag: str) -> str:
    if not cards:
        return "not explicit"
    count = sum(1 for card in cards if _has_tag(card, tag))
    if count == len(cards):
        return "yes"
    if count > 0:
        return f"partial ({count}/{len(cards)})"
    return "no"


def _evaluates_location_consistency(cards: list[PaperCard]) -> str:
    if not cards:
        return "not explicit"
    count = 0
    for card in cards:
        text = f"{card.metrics} {card.claimed_contribution} {card.limitation}".lower()
        if "location consistency" in text or ("location" in text and "consistency" in text):
            count += 1
    if count == len(cards):
        return "yes"
    if count > 0:
        return f"partial ({count}/{len(cards)})"
    return "no"


def _problem_space_groups(cards: list[PaperCard], insights: list[PaperInsightCard]) -> list[MOCGroup]:
    cards_by_title = {card.title: card for card in cards}
    grouped: dict[str, list[PaperInsightCard]] = defaultdict(list)
    for insight in insights:
        grouped[insight.group].append(insight)

    groups: list[MOCGroup] = []
    for group, group_insights in grouped.items():
        group_cards = [cards_by_title[insight.title] for insight in group_insights if insight.title in cards_by_title]
        missing = _dedupe(_split_capabilities([card.missing_capability for card in group_cards]), limit=6)
        gap_hints = _dedupe([card.gap_hint for card in group_cards], limit=4)
        open_questions = [
            f"Does {GROUP_PROBLEM_SPACE[group]} cover the target workflow, or only an adjacent proxy?",
            "Which extracted assumptions would fail under paired-study lesion change evaluation?",
        ]
        if gap_hints:
            open_questions.extend(f"Can we validate this hint: {hint}" for hint in gap_hints[:2])
        experiments = _dedupe(
            [_experimentable_gap_for(group, card) for card in group_cards],
            limit=4,
        )
        groups.append(
            MOCGroup(
                name=group,
                problem_space=GROUP_PROBLEM_SPACE[group],
                representative_papers=[insight.title for insight in group_insights[:8]],
                shared_assumptions=_dedupe([insight.assumption for insight in group_insights], limit=5)
                or GROUP_ASSUMPTIONS[group],
                method_families=_dedupe([card.method_family for card in group_cards], limit=5)
                or _dedupe([card.method for card in group_cards], limit=5)
                or ["method family not explicit"],
                datasets_or_benchmarks=_dedupe(
                    [card.dataset for card in group_cards if card.dataset != "not explicit"],
                    limit=6,
                )
                or ["not explicit in extracted cards"],
                metrics=_dedupe(
                    [card.metrics for card in group_cards if card.metrics != "not explicit"],
                    limit=6,
                )
                or ["not explicit in extracted cards"],
                covered_capabilities=GROUP_COVERED[group],
                missing_capabilities=missing or GROUP_MISSING[group],
                open_questions=open_questions[:6],
                possible_experiments=experiments or [_experimentable_gap_for(group, group_cards[0])]
                if group_cards
                else GROUP_MISSING[group],
                evidence=[
                    insight.evidence_snippet
                    for insight in group_insights[:3]
                    if insight.evidence_snippet is not None
                ],
            )
        )
    return groups


def build_topic_moc(topic: str, cards: list[PaperCard], insights: list[PaperInsightCard], gaps: list[GapEvidence]) -> TopicMOC:
    return TopicMOC(
        topic=topic,
        core_concepts=_concepts_from_topic(topic, insights),
        paper_groups=_paper_groups(insights),
        problem_spaces=_problem_space_groups(cards, insights),
        common_method_patterns=_common_method_patterns(cards),
        shared_assumptions=_shared_assumptions(insights),
        open_questions=_open_questions(gaps),
        related_themes=_related_themes(cards),
    )


def _group_benchmark_or_metrics(cards: list[PaperCard]) -> list[str]:
    values = []
    for card in cards:
        if card.dataset != "not explicit":
            values.append(f"dataset: {card.dataset}")
        if card.metrics != "not explicit":
            values.append(f"metrics: {card.metrics}")
    deduped = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return deduped[:8] or ["not explicit in extracted cards"]


def build_comparison_matrix(cards: list[PaperCard], insights: list[PaperInsightCard]) -> ComparisonMatrix:
    cards_by_title = {card.title: card for card in cards}
    grouped: dict[str, list[PaperInsightCard]] = defaultdict(list)
    for insight in insights:
        grouped[insight.group].append(insight)

    rows = []
    for group, group_insights in grouped.items():
        group_cards = [cards_by_title[insight.title] for insight in group_insights if insight.title in cards_by_title]
        evidence = [
            insight.evidence_snippet
            for insight in group_insights[:3]
            if insight.evidence_snippet is not None
        ]
        rows.append(
            ComparisonRow(
                group=group,
                problem=GROUP_PROBLEM_SPACE[group],
                representative_papers=[insight.title for insight in group_insights[:5]],
                method_families=_dedupe([card.method_family for card in group_cards], limit=5),
                uses_temporal_input=_capability_state(group_cards, "temporal_or_change"),
                uses_lesion_localization=_capability_state(group_cards, "lesion_or_localization"),
                evaluates_change=_capability_state(group_cards, "temporal_or_change"),
                evaluates_location_consistency=_evaluates_location_consistency(group_cards),
                solves=GROUP_SOLVES[group],
                missing=GROUP_MISSING[group],
                assumptions=GROUP_ASSUMPTIONS[group],
                benchmark_or_metrics=_group_benchmark_or_metrics(group_cards),
                gap_hints=_dedupe([card.gap_hint for card in group_cards], limit=5),
                evidence=evidence,
            )
        )
    return ComparisonMatrix(rows=rows)


def build_research_space(
    topic: str,
    cards: list[PaperCard],
    gaps: list[GapEvidence],
) -> tuple[list[PaperInsightCard], TopicMOC, ComparisonMatrix]:
    insights = build_paper_insights(cards)
    topic_moc = build_topic_moc(topic, cards, insights, gaps)
    comparison = build_comparison_matrix(cards, insights)
    return insights, topic_moc, comparison


def titles_for_group(topic_moc: TopicMOC, group: str, limit: int = 3) -> str:
    titles = topic_moc.paper_groups.get(group, [])[:limit]
    return "; ".join(titles) if titles else "none"


def clean_for_markdown(value: str, limit: int = 320) -> str:
    return clean_text(value, limit).replace("\n", " ")
