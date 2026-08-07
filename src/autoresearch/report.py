from __future__ import annotations

from pathlib import Path

from .schema import ComparisonMatrix, GapEvidence, ResearchOpportunity, SearchArtifacts, TopicMOC


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

    lines.extend(["## Problem Spaces", ""])
    for group in moc.problem_spaces:
        lines.extend(
            [
                f"### {group.name}",
                f"- Problem Space: {group.problem_space}",
                f"- Representative Papers: {_join(group.representative_papers[:6])}",
                f"- Shared Assumptions: {_join(group.shared_assumptions)}",
                f"- Method Families: {_join(group.method_families)}",
                f"- Datasets / Benchmarks: {_join(group.datasets_or_benchmarks)}",
                f"- Metrics: {_join(group.metrics)}",
                f"- Covered Capabilities: {_join(group.covered_capabilities)}",
                f"- Missing Capabilities: {_join(group.missing_capabilities)}",
                "",
                "Open Questions:",
            ]
        )
        for question in group.open_questions:
            lines.append(f"- {question}")
        lines.extend(["", "Possible Experiments:"])
        for experiment in group.possible_experiments:
            lines.append(f"- {experiment}")
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


def _write_source_coverage(artifacts: SearchArtifacts, output_dir: Path) -> Path:
    by_source: dict[str, dict[str, int]] = {}
    for status in artifacts.source_statuses:
        bucket = by_source.setdefault(
            status.source,
            {"queries": 0, "ok": 0, "failed": 0, "skipped": 0, "raw": 0},
        )
        bucket["queries"] += 1
        bucket["raw"] += status.raw_count
        if status.status == "ok":
            bucket["ok"] += 1
        elif status.status == "skipped":
            bucket["skipped"] += 1
        else:
            bucket["failed"] += 1

    ranked_contrib: dict[str, int] = {}
    for ranked in artifacts.ranked_papers:
        for source in ranked.paper.source_records:
            ranked_contrib[source] = ranked_contrib.get(source, 0) + 1

    oa_statuses: dict[str, int] = {}
    for record in artifacts.open_access_records:
        oa_statuses[record.status] = oa_statuses.get(record.status, 0) + 1

    full_text_statuses: dict[str, int] = {}
    for record in artifacts.full_texts:
        full_text_statuses[record.status] = full_text_statuses.get(record.status, 0) + 1

    lines = [
        f"# Source Coverage: {artifacts.topic}",
        "",
        "This report checks whether the search space is broad enough before interpreting weakness/gap outputs.",
        "",
        "## Source Execution",
        "",
        "| Source | Queries | OK | Failed | Skipped | Raw Results | Ranked Contributions |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for source, stats in sorted(by_source.items()):
        lines.append(
            f"| {source} | {stats['queries']} | {stats['ok']} | {stats['failed']} | "
            f"{stats['skipped']} | {stats['raw']} | {ranked_contrib.get(source, 0)} |"
        )

    lines.extend(["", "## Full-Text / OA Coverage", ""])
    lines.append(f"- Full-text statuses: {full_text_statuses or 'not attempted'}")
    lines.append(f"- Unpaywall statuses: {oa_statuses or 'not attempted'}")
    lines.append("")

    lines.extend(["## Source Readiness Gate", ""])
    if artifacts.source_readiness:
        readiness = artifacts.source_readiness
        lines.append(f"- Status: {readiness.status}")
        lines.append(f"- Ranked papers: {readiness.ranked_papers}")
        lines.append(f"- Contributing sources: {readiness.contributing_sources}")
        lines.append(f"- MOC groups: {readiness.moc_groups}")
        for reason in readiness.reasons:
            lines.append(f"- {reason}")
    else:
        lines.append("- Source readiness was not evaluated.")
    lines.append("")

    lines.extend(["## MOC Coverage", ""])
    if artifacts.topic_moc:
        lines.append(f"- Paper groups: {len(artifacts.topic_moc.paper_groups)}")
        for group, titles in artifacts.topic_moc.paper_groups.items():
            lines.append(f"  - {group}: {len(titles)} papers")
    else:
        lines.append("- Topic MOC was not generated.")

    lines.extend(["", "## Warnings", ""])
    if artifacts.warnings:
        for warning in artifacts.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- No major source execution warnings.")
    lines.append("")

    path = output_dir / "source_coverage.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_comparison_matrix(comparison: ComparisonMatrix | None, output_dir: Path) -> Path | None:
    if not comparison:
        return None
    lines = [
        "# Cross-Paper Comparison Matrix",
        "",
        "| Group | Problem | Methods | Temporal Input | Lesion Localization | Evaluates Change | Location Consistency | Benchmark / Metrics | Gap Hints |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in comparison.rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_cell(row.group),
                    _escape_cell(row.problem),
                    _escape_cell(_join(row.method_families)),
                    _escape_cell(row.uses_temporal_input),
                    _escape_cell(row.uses_lesion_localization),
                    _escape_cell(row.evaluates_change),
                    _escape_cell(row.evaluates_location_consistency),
                    _escape_cell(_join(row.benchmark_or_metrics)),
                    _escape_cell(_join(row.gap_hints)),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Group Details", ""])
    for row in comparison.rows:
        lines.extend(
            [
                f"### {row.group}",
                f"- Representative Papers: {_join(row.representative_papers[:5])}",
                f"- Solves: {_join(row.solves)}",
                f"- Missing: {_join(row.missing)}",
                f"- Assumptions: {_join(row.assumptions)}",
                "",
            ]
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
        "Status: preliminary. Read this after validating `source_coverage.md`, `topic_moc.md`, and `comparison_matrix.md`.",
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


def _write_gap_evidence_chains(artifacts: SearchArtifacts, output_dir: Path) -> Path:
    lines = [
        f"# Gap Evidence Chains: {artifacts.topic}",
        "",
        "Each claim below is a preliminary research hypothesis. It should be read as an evidence chain, not as a final survey conclusion.",
        "",
    ]
    for idx, gap in enumerate(artifacts.gaps, start=1):
        lines.extend(
            [
                f"## Gap {idx}: {gap.gap}",
                "",
                f"- Confidence: {gap.confidence}",
                (
                    f"- Coverage: support={gap.support_count}/{gap.total_papers}, "
                    f"counter={gap.counter_count}/{gap.total_papers}, unclear={gap.unclear_count}"
                ),
                f"- Why it matters: {gap.why_it_matters}",
                "",
                "### Evidence Chain",
                "",
            ]
        )
        if gap.evidence_chain:
            for step_no, step in enumerate(gap.evidence_chain, start=1):
                missing = (
                    f" Missing dimensions: {', '.join(step.missing_dimensions)}."
                    if step.missing_dimensions
                    else ""
                )
                lines.append(
                    f"{step_no}. **{step.paper_title}** ({step.role}): {step.claim}.{missing}"
                )
                if step.evidence:
                    section = f" [{step.evidence.section}]" if step.evidence.section else ""
                    lines.append(f"   - Evidence{section}: {step.evidence.snippet}")
                    if step.source_url:
                        lines.append(f"   - Source: {step.source_url}")
        else:
            lines.append("- No paper-level evidence chain was generated.")

        lines.extend(["", "### Counter-Evidence To Resolve", ""])
        if gap.counter_evidence:
            for evidence in gap.counter_evidence:
                lines.append(f"- **{evidence.paper_title}**: {evidence.claim}")
        else:
            lines.append("- No counter-evidence surfaced in this run.")

        lines.extend(["", "### How To Validate", ""])
        for item in _verification_plan(gap):
            lines.append(f"- {item}")
        lines.append("")

    path = output_dir / "gap_evidence_chains.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _write_research_opportunities(
    opportunities: list[ResearchOpportunity],
    output_dir: Path,
    topic: str,
) -> Path:
    lines = [
        f"# Research Opportunities: {topic}",
        "",
        "These opportunities are generated only when a gap has at least two supporting evidence-chain steps.",
        "",
    ]
    if not opportunities:
        lines.append("- No evidence-backed research opportunities were generated in this run.")
    for idx, opportunity in enumerate(opportunities, start=1):
        lines.extend(
            [
                f"## Opportunity {idx}",
                "",
                f"- Bound Gap: {opportunity.gap}",
                f"- Research Question: {opportunity.research_question}",
                f"- Hypothesis: {opportunity.hypothesis}",
                f"- Proposed Method: {opportunity.proposed_method}",
                f"- Required Data: {opportunity.required_data}",
                f"- Evidence Refs: {_join(opportunity.evidence_refs)}",
                "",
                "### Innovations Bound To Gap",
                "",
            ]
        )
        for innovation in opportunity.innovations_bound_to_gap:
            lines.append(f"- {innovation}")

        lines.extend(["", "### Evaluation Protocol", ""])
        for item in opportunity.evaluation_protocol:
            lines.append(f"- {item}")

        lines.extend(["", "### Baselines", ""])
        for baseline in opportunity.baselines:
            lines.append(f"- {baseline}")

        lines.extend(["", "### Ablations", ""])
        for ablation in opportunity.ablations:
            lines.append(f"- {ablation}")

        lines.extend(["", "### Risks", ""])
        for risk in opportunity.risks:
            lines.append(f"- {risk}")
        lines.append("")

    path = output_dir / "research_opportunities.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_report(artifacts: SearchArtifacts, output_dir: Path) -> Path:
    source_coverage_path = _write_source_coverage(artifacts, output_dir)
    topic_moc_path = _write_topic_moc(artifacts, output_dir)
    comparison_path = _write_comparison_matrix(artifacts.comparison_matrix, output_dir)
    weakness_path = _write_weakness_report(artifacts, output_dir)
    gap_chain_path = _write_gap_evidence_chains(artifacts, output_dir)
    opportunity_path = _write_research_opportunities(
        artifacts.research_opportunities,
        output_dir,
        artifacts.topic,
    )

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
    lines.append(f"- Source coverage: `{source_coverage_path.name}`")
    if topic_moc_path:
        lines.append(f"- Topic MOC: `{topic_moc_path.name}`")
    if comparison_path:
        lines.append(f"- Cross-paper comparison matrix: `{comparison_path.name}`")
    lines.append(f"- Gap evidence chains: `{gap_chain_path.name}`")
    lines.append(f"- Research opportunities: `{opportunity_path.name}`")
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

    lines.extend(["", "## 5b. Open Access Enrichment", ""])
    if artifacts.open_access_records:
        for record in artifacts.open_access_records[:15]:
            if record.status == "ok":
                lines.append(
                    f"- **{record.title}**: open_access={record.is_open_access}, "
                    f"pdf={'yes' if record.pdf_url else 'no'}, landing={'yes' if record.landing_page_url else 'no'}"
                )
            else:
                lines.append(f"- **{record.title}**: {record.status}, error={record.error or 'n/a'}")
    else:
        lines.append("- Open access enrichment was not attempted.")

    lines.extend(["", "## 6. Paper Cards", ""])
    for card in artifacts.paper_cards[:15]:
        lines.extend(
            [
                f"### {card.title}",
                f"- Problem: {card.problem}",
                f"- Task: {card.task}",
                f"- Method: {card.method}",
                f"- Method Family: {card.method_family}",
                f"- Core Assumption: {card.core_assumption}",
                f"- Evidence Type: {card.evidence_type}",
                f"- Dataset: {card.dataset}",
                f"- Metrics: {card.metrics}",
                f"- Limitation: {card.limitation or 'not explicit'}",
                f"- Missing Capability: {card.missing_capability or 'not explicit'}",
                f"- Relation To Topic: {card.relation_to_topic or 'not explicit'}",
                f"- Gap Hint: {card.gap_hint or 'not explicit'}",
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

    lines.extend(["## 8b. Evidence-Backed Research Opportunities", ""])
    if artifacts.research_opportunities:
        for idx, opportunity in enumerate(artifacts.research_opportunities, start=1):
            lines.extend(
                [
                    f"### Opportunity {idx}",
                    f"- Bound gap: {opportunity.gap}",
                    f"- Research question: {opportunity.research_question}",
                    f"- Hypothesis: {opportunity.hypothesis}",
                    f"- Evidence refs: {_join(opportunity.evidence_refs)}",
                    f"- Required data: {opportunity.required_data}",
                    "",
                ]
            )
    else:
        lines.append("- No evidence-backed opportunities were generated.")
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
