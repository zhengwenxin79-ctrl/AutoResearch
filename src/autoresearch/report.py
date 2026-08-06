from __future__ import annotations

from pathlib import Path

from .schema import SearchArtifacts


def write_report(artifacts: SearchArtifacts, output_dir: Path) -> Path:
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
