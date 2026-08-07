from __future__ import annotations

from pathlib import Path

from .schema import ComparisonMatrix, GapEvidence, SearchArtifacts, TopicMOC


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _join(values: list[str], fallback: str = "not explicit") -> str:
    return "; ".join(values) if values else fallback


def _write_topic_moc(artifacts: SearchArtifacts, output_dir: Path) -> Path | None:
    moc = artifacts.topic_moc
    if not moc:
        return None
    lines = [
        f"# Topic MOC: {moc.topic}",
        "",
        "## Core Concepts",
        "",
    ]
    for concept in moc.core_concepts:
        lines.append(f"- {concept}")

    lines.extend(["", "## Paper Groups", ""])
    for group, titles in moc.paper_groups.items():
        lines.append(f"### {group}")
        for title in titles[:10]:
            lines.append(f"- {title}")
        lines.append("")

    lines.extend(["## Common Method Patterns", ""])
    for pattern in moc.common_method_patterns:
        lines.append(f"- {pattern}")

    lines.extend(["", "## Shared Assumptions", ""])
    for assumption in moc.shared_assumptions:
        lines.append(f"- {assumption}")

    lines.extend(["", "## Open Questions", ""])
    for question in moc.open_questions:
        lines.append(f"- {question}")

    lines.extend(["", "## Related Themes", ""])
    for theme in moc.related_themes:
        lines.append(f"- {theme}")
    lines.append("")

    path = output_dir / "topic_moc.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_comparison_matrix(comparison: ComparisonMatrix | None, output_dir: Path) -> Path | None:
    if not comparison:
        return None
    lines = [
        "# Cross-Paper Comparison Matrix",
        "",
        "| Group | Representative Papers | Solves | Missing | Assumptions | Benchmark / Metrics |",
        "|---|---|---|---|---|---|",
    ]
    for row in comparison.rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_cell(row.group),
                    _escape_cell(_join(row.representative_papers[:4])),
                    _escape_cell(_join(row.solves)),
                    _escape_cell(_join(row.missing)),
                    _escape_cell(_join(row.assumptions)),
                    _escape_cell(_join(row.benchmark_or_metrics)),
                ]
            )
            + " |"
        )
    lines.append("")

    path = output_dir / "comparison_matrix.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _verification_plan(gap: GapEvidence) -> list[str]:
    lowered = gap.gap.lower()
    if "temporal" in lowered or "lesion" in lowered:
        return [
            "change label accuracy",
            "finding/location consistency",
            "no-mask vs T1-mask ablation",
            "T2-mask upper-bound comparison",
            "failure taxonomy for missed, hallucinated, and wrong-direction changes",
        ]
    if "dataset" in lowered or "benchmark" in lowered:
        return [
            "dataset coverage table",
            "benchmark dimension checklist",
            "baseline comparability audit",
            "paired-study availability check",
        ]
    if "metric" in lowered:
        return [
            "generic metric vs clinical-consistency metric comparison",
            "finding/location/change-direction metric split",
            "case-level failure analysis",
        ]
    return [
        "support/counter evidence audit",
        "representative paper group comparison",
        "targeted ablation plan",
    ]


def _emergence_lines(gap: GapEvidence, moc: TopicMOC | None, comparison: ComparisonMatrix | None) -> list[str]:
    lines = []
    if comparison:
        for row in comparison.rows[:6]:
            missing = _join(row.missing)
            solves = _join(row.solves)
            lines.append(f"- **{row.group}** solves: {solves} Missing: {missing}")
    if not lines and moc:
        for group, titles in moc.paper_groups.items():
            lines.append(f"- **{group}** contributes {len(titles)} papers to this problem space.")
    if not lines:
        lines.append("- The weakness emerges from support/counter evidence patterns in the retrieved papers.")
    lines.append(f"- Gap score reasons: {'; '.join(gap.score_reasons) if gap.score_reasons else 'not available'}")
    return lines


def _write_weakness_report(artifacts: SearchArtifacts, output_dir: Path) -> Path:
    lines = [
        f"# Weakness Report: {artifacts.topic}",
        "",
        "This report is optimized for research discussion. It focuses on how weaknesses emerge from paper groups, assumptions, counter-evidence, and experimentable next steps.",
        "",
        "## Paper Groups",
        "",
    ]
    if artifacts.topic_moc:
        for group, titles in artifacts.topic_moc.paper_groups.items():
            lines.append(f"- **{group}**: {len(titles)} papers")
    else:
        lines.append("- Topic MOC was not generated.")

    for idx, gap in enumerate(artifacts.gaps, start=1):
        lines.extend(
            [
                "",
                f"## Weakness {idx}: {gap.gap}",
                "",
                f"- Confidence: {gap.confidence}",
                (
                    f"- Coverage: support={gap.support_count}/{gap.total_papers}, "
                    f"counter={gap.counter_count}/{gap.total_papers}, unclear={gap.unclear_count}"
                ),
                f"- Why it matters: {gap.why_it_matters}",
                "",
                "### How This Weakness Emerges",
                "",
            ]
        )
        lines.extend(_emergence_lines(gap, artifacts.topic_moc, artifacts.comparison_matrix))

        lines.extend(["", "### Evidence Chain", ""])
        for evidence in gap.evidence:
            section = f" [{evidence.section}]" if evidence.section else ""
            lines.append(f"- **{evidence.paper_title}**{section}: {evidence.claim}")

        lines.extend(["", "### Counter Evidence", ""])
        if gap.counter_evidence:
            for evidence in gap.counter_evidence:
                lines.append(f"- **{evidence.paper_title}**: {evidence.claim}")
        else:
            lines.append("- No counter evidence surfaced in the current run.")

        lines.extend(["", "### Why Still Open", ""])
        for judgment in gap.paper_judgments[:8]:
            if judgment.role != "support":
                continue
            missing = ", ".join(judgment.missing_evidence) or "missing dimensions not explicit"
            lines.append(f"- **{judgment.paper_title}**: {missing}")
        if not any(judgment.role == "support" for judgment in gap.paper_judgments):
            lines.append("- Current evidence does not clearly support this weakness.")

        lines.extend(
            [
                "",
                "### Experimentable Idea",
                "",
                f"- {gap.research_opportunity}",
                "",
                "### Verification Plan",
                "",
            ]
        )
        for item in _verification_plan(gap):
            lines.append(f"- {item}")

    lines.append("")
    path = output_dir / "weakness_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_report(artifacts: SearchArtifacts, output_dir: Path) -> Path:
    topic_moc_path = _write_topic_moc(artifacts, output_dir)
    comparison_path = _write_comparison_matrix(artifacts.comparison_matrix, output_dir)
    weakness_path = _write_weakness_report(artifacts, output_dir)

    lines = [
        f"# Auto Search Report: {artifacts.topic}",
        "",
        f"Generated at: `{artifacts.generated_at}`",
        "",
        "## 1. Query Plan",
        "",
    ]
    for query in artifacts.query_plan.queries:
        lines.append(f"- `{query}`")

    lines.extend(["", "## MOC-Style Research Artifacts", ""])
    if topic_moc_path:
        lines.append(f"- Topic MOC: `{topic_moc_path.name}`")
    if comparison_path:
        lines.append(f"- Cross-paper comparison matrix: `{comparison_path.name}`")
    lines.append(f"- Weakness report: `{weakness_path.name}`")

    lines.extend(["", "## 2. Source Execution", ""])
    for status in artifacts.source_statuses:
        suffix = f" ({status.error})" if status.error else ""
        lines.append(f"- `{status.source}` / `{status.query}`: {status.status}, raw={status.raw_count}{suffix}")

    lines.extend(["", "## 3. Representative Papers", ""])
    for idx, ranked in enumerate(artifacts.ranked_papers[:15], start=1):
        paper = ranked.paper
        year = paper.year or "n.d."
        lines.append(
            f"{idx}. **{paper.title}** ({year}) score={ranked.relevance_score}  "
            f"[link]({paper.url})"
        )
        if ranked.score_reasons:
            lines.append(f"   - reasons: {'; '.join(ranked.score_reasons[:3])}")

    lines.extend(["", "## 4. Full-Text Reading", ""])
    if artifacts.full_texts:
        for record in artifacts.full_texts:
            section_count = len(record.sections)
            lines.append(
                f"- **{record.title}**: {record.status}, sections={section_count}, "
                f"fetched_url={record.fetched_url or 'n/a'}"
            )
            if record.error:
                lines.append(f"  - error: {record.error}")
    else:
        lines.append("- Full-text reading was not attempted.")

    lines.extend(["", "## 5. Semantic Scholar Enrichment", ""])
    if artifacts.influences:
        for card in artifacts.paper_cards[:15]:
            influence = card.influence
            if not influence:
                lines.append(f"- **{card.title}**: not attempted")
                continue
            if influence.status == "ok":
                lines.append(
                    f"- **{card.title}**: citations={influence.citation_count}, "
                    f"influential={influence.influential_citation_count}, refs={influence.reference_count}, "
                    f"open_pdf={'yes' if influence.open_access_pdf else 'no'}"
                )
            else:
                lines.append(f"- **{card.title}**: {influence.status}, error={influence.error or 'n/a'}")
    else:
        lines.append("- Semantic Scholar enrichment was not attempted.")

    lines.extend(["", "## 6. Paper Cards", ""])
    for card in artifacts.paper_cards[:15]:
        lines.extend(
            [
                f"### {card.title}",
                f"- Task: {card.task}",
                f"- Method: {card.method}",
                f"- Dataset: {card.dataset}",
                f"- Metrics: {card.metrics}",
                f"- Limitation: {card.limitation or 'not explicit'}",
                f"- Coverage tags: {', '.join(card.coverage_tags) if card.coverage_tags else 'none'}",
                f"- Influence score inputs: {', '.join(card.influence.fields_of_study) if card.influence and card.influence.fields_of_study else 'not available'}",
                "",
            ]
        )

    lines.extend(["", "## 7. Field Map", ""])
    lines.append("### Tasks")
    for key, titles in artifacts.field_map.task_clusters.items():
        lines.append(f"- {key}: {len(titles)} papers")
    lines.append("")
    lines.append("### Methods")
    for key, titles in artifacts.field_map.method_clusters.items():
        lines.append(f"- {key}: {len(titles)} papers")
    lines.append("")
    lines.append("### Datasets")
    for key, titles in artifacts.field_map.datasets.items():
        lines.append(f"- {key}: {len(titles)} papers")
    lines.append("")
    lines.append("### Metrics")
    for key, titles in artifacts.field_map.metrics.items():
        lines.append(f"- {key}: {len(titles)} papers")

    lines.extend(["", "## 8. Core Gaps With Evidence", ""])
    for idx, gap in enumerate(artifacts.gaps, start=1):
        lines.extend(
            [
                f"### Gap {idx}: {gap.gap}",
                f"- Confidence: {gap.confidence}",
                (
                    f"- Coverage: support={gap.support_count}/{gap.total_papers} "
                    f"({gap.support_ratio}), counter={gap.counter_count}/{gap.total_papers} "
                    f"({gap.counter_ratio}), unclear={gap.unclear_count}"
                ),
                f"- Full-text evidence snippets: {gap.full_text_evidence_count}",
                f"- Score reasons: {'; '.join(gap.score_reasons) if gap.score_reasons else 'not available'}",
                f"- Why it matters: {gap.why_it_matters}",
                f"- Research opportunity: {gap.research_opportunity}",
                "- Evidence:",
            ]
        )
        for evidence in gap.evidence:
            section = f" [{evidence.section}]" if evidence.section else ""
            lines.append(
                f"  - **{evidence.paper_title}**{section}: {evidence.claim}. "
                f"[source]({evidence.source_url})  \n"
                f"    Snippet: {evidence.snippet}"
            )
        if gap.counter_evidence:
            lines.append("- Counter evidence:")
            for evidence in gap.counter_evidence:
                lines.append(f"  - **{evidence.paper_title}**: {evidence.claim}. [source]({evidence.source_url})")
        if gap.paper_judgments:
            lines.append("- Paper-level judgments:")
            for judgment in gap.paper_judgments[:10]:
                missing = (
                    f"; missing: {', '.join(judgment.missing_evidence)}"
                    if judgment.missing_evidence
                    else ""
                )
                reasons = (
                    f"; influence: {', '.join(judgment.influence_reasons[:3])}"
                    if judgment.influence_reasons
                    else ""
                )
                lines.append(
                    f"  - **{judgment.paper_title}**: decision={judgment.decision}, "
                    f"role={judgment.role}, influence_score={judgment.influence_score}"
                    f"{missing}{reasons}"
                )
        lines.append("")

    lines.extend(["## 9. Search Limitations", ""])
    if artifacts.warnings:
        for warning in artifacts.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- No major source execution warnings.")
    lines.extend(
        [
            "- MVP extraction uses rule-based evidence signals; full-text parsing improves coverage but is not a substitute for expert review.",
            "- Gap evidence is a research triage signal, not a final systematic-review conclusion.",
            "",
        ]
    )

    path = output_dir / "report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
