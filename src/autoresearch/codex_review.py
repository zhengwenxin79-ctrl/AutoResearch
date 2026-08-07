from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .dashboard import write_dashboard
from .report import write_report
from .schema import (
    ComparisonMatrix,
    ComparisonRow,
    EvidenceSnippet,
    GapEvidence,
    GapEvidenceStep,
    MOCGroup,
    ResearchOpportunity,
    SearchArtifacts,
    SynthesisGapSummary,
    SynthesisReport,
    TopicMOC,
)
from .synthesizer import write_analysis_report
from .utils import clean_text


class CodexMOCGroupResult(BaseModel):
    name: str
    problem_space: str = ""
    representative_papers: list[str] = Field(default_factory=list)
    shared_assumptions: list[str] = Field(default_factory=list)
    method_families: list[str] = Field(default_factory=list)
    datasets_or_benchmarks: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    covered_capabilities: list[str] = Field(default_factory=list)
    missing_capabilities: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    possible_experiments: list[str] = Field(default_factory=list)


class CodexGapResult(BaseModel):
    gap: str
    judgment: str = ""
    support: str = ""
    counter_evidence: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    support_papers: list[str] = Field(default_factory=list)
    counter_papers: list[str] = Field(default_factory=list)
    unclear_papers: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    why_it_matters: str = ""
    research_opportunity: str = ""
    score_reasons: list[str] = Field(default_factory=list)
    validation_plan: list[str] = Field(default_factory=list)


class CodexOpportunityResult(BaseModel):
    gap: str
    research_question: str = ""
    hypothesis: str = ""
    proposed_method: str = ""
    innovations_bound_to_gap: list[str] = Field(default_factory=list)
    required_data: str = ""
    evaluation_protocol: list[str] = Field(default_factory=list)
    baselines: list[str] = Field(default_factory=list)
    ablations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class CodexReviewResult(BaseModel):
    mode: str = "codex_manual_llm_pass"
    status: str = "draft"
    executive_summary: str = ""
    domain_interpretation: str = ""
    search_assessment: str = ""
    evidence_quality: str = ""
    moc_takeaways: list[str] = Field(default_factory=list)
    moc_groups: list[CodexMOCGroupResult] = Field(default_factory=list)
    gaps: list[CodexGapResult] = Field(default_factory=list)
    opportunities: list[CodexOpportunityResult] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


def _paper_lookup(artifacts: SearchArtifacts) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    ranked_by_title = {row.paper.title: row.paper for row in artifacts.ranked_papers}
    for card in artifacts.paper_cards:
        snippet = card.evidence_snippets[0].snippet if card.evidence_snippets else ""
        source_url = card.evidence_snippets[0].source_url if card.evidence_snippets else card.url
        lookup[card.title] = {
            "title": card.title,
            "url": source_url or card.url,
            "snippet": snippet or card.claimed_contribution,
        }
    for title, paper in ranked_by_title.items():
        lookup.setdefault(
            title,
            {
                "title": title,
                "url": paper.url,
                "snippet": paper.abstract,
            },
        )
    return lookup


def _evidence_for_title(
    artifacts: SearchArtifacts,
    title: str,
    claim: str,
    *,
    section: str = "abstract",
) -> EvidenceSnippet:
    lookup = _paper_lookup(artifacts)
    record = lookup.get(title, {"title": title, "url": "", "snippet": ""})
    return EvidenceSnippet(
        paper_title=title,
        source_url=record.get("url", ""),
        claim=claim,
        snippet=clean_text(record.get("snippet", "") or claim, 420),
        section=section,
    )


def _packet_payload(artifacts: SearchArtifacts) -> dict[str, Any]:
    return {
        "topic": artifacts.topic,
        "domain_profile": artifacts.domain_profile.model_dump(mode="json")
        if artifacts.domain_profile
        else None,
        "source_readiness": artifacts.source_readiness.model_dump(mode="json")
        if artifacts.source_readiness
        else None,
        "source_statuses": [status.model_dump(mode="json") for status in artifacts.source_statuses],
        "query_plan": artifacts.query_plan.model_dump(mode="json"),
        "papers": [
            {
                "title": card.title,
                "year": card.year,
                "venue": card.venue,
                "url": card.url,
                "problem": card.problem,
                "task": card.task,
                "method": card.method,
                "method_family": card.method_family,
                "dataset": card.dataset,
                "metrics": card.metrics,
                "missing_capability": card.missing_capability,
                "relation_to_topic": card.relation_to_topic,
                "gap_hint": card.gap_hint,
                "coverage_tags": card.coverage_tags,
                "evidence_snippets": [
                    snippet.model_dump(mode="json") for snippet in card.evidence_snippets[:2]
                ],
            }
            for card in artifacts.paper_cards
        ],
        "current_moc": artifacts.topic_moc.model_dump(mode="json") if artifacts.topic_moc else None,
        "current_gaps": [
            {
                "gap": gap.gap,
                "confidence": gap.confidence,
                "support_count": gap.support_count,
                "counter_count": gap.counter_count,
                "unclear_count": gap.unclear_count,
                "total_papers": gap.total_papers,
                "why_it_matters": gap.why_it_matters,
                "research_opportunity": gap.research_opportunity,
                "score_reasons": gap.score_reasons,
                "evidence_chain": [step.model_dump(mode="json") for step in gap.evidence_chain],
            }
            for gap in artifacts.gaps
        ],
        "current_opportunities": [
            opportunity.model_dump(mode="json") for opportunity in artifacts.research_opportunities
        ],
    }


def _result_template() -> CodexReviewResult:
    return CodexReviewResult(
        executive_summary="",
        domain_interpretation="",
        search_assessment="",
        evidence_quality="",
        moc_takeaways=[],
        moc_groups=[
            CodexMOCGroupResult(
                name="",
                problem_space="",
                representative_papers=[],
                shared_assumptions=[],
                method_families=[],
                datasets_or_benchmarks=[],
                metrics=[],
                covered_capabilities=[],
                missing_capabilities=[],
                open_questions=[],
                possible_experiments=[],
            )
        ],
        gaps=[
            CodexGapResult(
                gap="",
                judgment="",
                support="",
                counter_evidence="",
                evidence_refs=[],
                support_papers=[],
                counter_papers=[],
                unclear_papers=[],
                confidence=0.0,
                why_it_matters="",
                research_opportunity="",
                score_reasons=[],
                validation_plan=[],
            )
        ],
        opportunities=[
            CodexOpportunityResult(
                gap="",
                research_question="",
                hypothesis="",
                proposed_method="",
                innovations_bound_to_gap=[],
                required_data="",
                evaluation_protocol=[],
                baselines=[],
                ablations=[],
                risks=[],
                evidence_refs=[],
            )
        ],
        limitations=[],
        next_steps=[],
    )


def write_codex_review_packet(artifacts: SearchArtifacts, output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = _packet_payload(artifacts)
    packet_json = output_dir / "codex_review_packet.json"
    packet_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    template_path = output_dir / "codex_review_result.template.json"
    template_path.write_text(
        _result_template().model_dump_json(indent=2),
        encoding="utf-8",
    )

    packet_md = output_dir / "codex_review_packet.md"
    packet_md.write_text(
        "\n".join(
            [
                f"# Codex Manual LLM Review Packet: {artifacts.topic}",
                "",
                "这个文件用于让 Codex 代替正式 LLM 做研究判断。",
                "",
                "## 使用方式",
                "",
                "1. 让 Codex 读取 `codex_review_packet.json`。",
                "2. Codex 必须只基于 packet 里的论文、证据片段、MOC、Gap chain 和研究机会判断。",
                "3. Codex 输出符合 `codex_review_result.template.json` 结构的 JSON。",
                "4. 运行 `autoresearch codex-apply <output-dir> <result-json>` 写回 UI。",
                "",
                "## Codex 需要完成的判断",
                "",
                "- 重拆或修正 MOC 问题空间。",
                "- 判断原始 Gap 是否成立、是否需要改写、反证是什么。",
                "- 把真正稳定的 Gap 转成 research opportunity。",
                "- 明确哪些论文是 core evidence、adjacent evidence 或 noise。",
                "- 给出下一步全文读取、检索扩展、benchmark 设计建议。",
                "",
                "## 审查问题清单",
                "",
                "### 1. 论文证据分层",
                "",
                "- 哪些论文是目标领域的 core evidence？",
                "- 哪些论文只是 adjacent evidence，可以提供旁证但不能支撑核心结论？",
                "- 哪些论文应被视为 possible noise，并在 Gap 判断中降权？",
                "- 是否有高相关论文缺失，导致当前证据链不完整？",
                "",
                "### 2. MOC 问题空间",
                "",
                "- 当前 MOC 分组是否太粗，是否需要重拆？",
                "- 每个 MOC group 是否有清楚的问题空间、方法路线和 benchmark/metric 信号？",
                "- 是否存在所有论文都被塞进一个 group 的情况？",
                "- 哪些 shared assumptions 是跨论文共同成立或共同脆弱的？",
                "",
                "### 3. Gap / Weakness 审查",
                "",
                "- 原始 Gap 是否太宽、太空或已经被某些论文直接解决？",
                "- 哪些论文构成 support evidence？哪些论文构成 counter evidence？",
                "- 如果有强反证，Gap 应该被删除、降级，还是改写成更精确的 Gap？",
                "- 这个 Gap 的成立依赖摘要证据还是全文实验/限制证据？",
                "",
                "### 4. 研究机会",
                "",
                "- 哪个 refined Gap 最适合转成 research question？",
                "- proposed method 是否和 Gap 一一对应，而不是泛泛说“提出新框架”？",
                "- 需要什么数据集、benchmark、baseline、ablation 才能证明它？",
                "- 当前证据是否足够进入 Auto Benchmark，还是应该先继续检索/读全文？",
                "",
                "### 5. 下一步控制",
                "",
                "- 下一步最小可执行动作是什么？",
                "- 这个动作的验收标准是什么？",
                "- 哪些结论必须标记为 preliminary，避免过早写进论文动机？",
                "",
                "## 输出约束",
                "",
                "- 不要编造 packet 之外的论文。",
                "- 每个 Gap 必须给 `support_papers`、`counter_papers` 或 `unclear_papers`。",
                "- 如果证据不足，必须在 `limitations` 和 `next_steps` 里写清楚。",
                "- 最终 JSON 保存为 `codex_review_result.json`。",
                "",
                "## Packet 摘要",
                "",
                f"- Topic: `{artifacts.topic}`",
                f"- Papers: `{len(artifacts.paper_cards)}`",
                f"- Current gaps: `{len(artifacts.gaps)}`",
                f"- Current opportunities: `{len(artifacts.research_opportunities)}`",
                f"- Packet JSON: `{packet_json.name}`",
                f"- Result template: `{template_path.name}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return packet_md, packet_json, template_path


def load_codex_review_result(path: Path) -> CodexReviewResult:
    return CodexReviewResult.model_validate_json(path.read_text(encoding="utf-8"))


def _paper_groups(groups: list[CodexMOCGroupResult]) -> dict[str, list[str]]:
    return {group.name: group.representative_papers for group in groups}


def _comparison_from_groups(groups: list[CodexMOCGroupResult]) -> ComparisonMatrix:
    rows = []
    for group in groups:
        rows.append(
            ComparisonRow(
                group=group.name,
                problem=group.problem_space,
                representative_papers=group.representative_papers,
                method_families=group.method_families,
                uses_temporal_input="see problem-space notes",
                uses_lesion_localization="not applicable unless domain-specific",
                evaluates_change="see metrics and missing capabilities",
                evaluates_location_consistency="not explicit",
                solves=group.covered_capabilities,
                missing=group.missing_capabilities,
                assumptions=group.shared_assumptions,
                benchmark_or_metrics=[*group.datasets_or_benchmarks, *group.metrics],
                gap_hints=group.open_questions,
            )
        )
    return ComparisonMatrix(rows=rows)


def _moc_from_result(artifacts: SearchArtifacts, result: CodexReviewResult) -> TopicMOC | None:
    if not result.moc_groups:
        return artifacts.topic_moc
    core_concepts = artifacts.domain_profile.core_concepts if artifacts.domain_profile else []
    problem_spaces = [
        MOCGroup(
            name=group.name,
            problem_space=group.problem_space,
            representative_papers=group.representative_papers,
            shared_assumptions=group.shared_assumptions,
            method_families=group.method_families,
            datasets_or_benchmarks=group.datasets_or_benchmarks,
            metrics=group.metrics,
            covered_capabilities=group.covered_capabilities,
            missing_capabilities=group.missing_capabilities,
            open_questions=group.open_questions,
            possible_experiments=group.possible_experiments,
            evidence=[
                _evidence_for_title(artifacts, title, f"Representative evidence for {group.name}")
                for title in group.representative_papers[:3]
            ],
        )
        for group in result.moc_groups
        if group.name
    ]
    return TopicMOC(
        topic=artifacts.topic,
        core_concepts=core_concepts,
        paper_groups=_paper_groups(result.moc_groups),
        problem_spaces=problem_spaces,
        common_method_patterns=sorted(
            {method for group in result.moc_groups for method in group.method_families}
        ),
        shared_assumptions=list(
            dict.fromkeys(
                assumption for group in result.moc_groups for assumption in group.shared_assumptions
            )
        ),
        open_questions=list(
            dict.fromkeys(question for group in result.moc_groups for question in group.open_questions)
        ),
        related_themes=sorted(
            {item for group in result.moc_groups for item in group.datasets_or_benchmarks}
        ),
    )


def _gap_from_result(artifacts: SearchArtifacts, gap: CodexGapResult) -> GapEvidence:
    support_papers = gap.support_papers or gap.evidence_refs
    counter_papers = gap.counter_papers
    unclear_papers = gap.unclear_papers
    evidence = [
        _evidence_for_title(artifacts, title, gap.support or "support evidence")
        for title in support_papers
    ]
    counter_evidence = [
        _evidence_for_title(artifacts, title, gap.counter_evidence or "counter evidence")
        for title in counter_papers
    ]
    evidence_chain = [
        GapEvidenceStep(
            paper_title=title,
            source_url=_evidence_for_title(artifacts, title, gap.support or "support evidence").source_url,
            role="support",
            claim=gap.support or "support evidence",
            evidence=_evidence_for_title(artifacts, title, gap.support or "support evidence"),
        )
        for title in support_papers
    ]
    evidence_chain.extend(
        GapEvidenceStep(
            paper_title=title,
            source_url=_evidence_for_title(
                artifacts, title, gap.counter_evidence or "counter evidence"
            ).source_url,
            role="counter",
            claim=gap.counter_evidence or "counter evidence",
            evidence=_evidence_for_title(artifacts, title, gap.counter_evidence or "counter evidence"),
        )
        for title in counter_papers
    )
    total = len(artifacts.paper_cards)
    support_count = len(support_papers)
    counter_count = len(counter_papers)
    unclear_count = len(unclear_papers) if unclear_papers else max(total - support_count - counter_count, 0)
    return GapEvidence(
        gap=gap.gap,
        evidence=evidence,
        counter_evidence=counter_evidence,
        evidence_chain=evidence_chain,
        confidence=gap.confidence,
        support_count=support_count,
        counter_count=counter_count,
        unclear_count=unclear_count,
        total_papers=total,
        support_ratio=support_count / total if total else 0.0,
        counter_ratio=counter_count / total if total else 0.0,
        score_reasons=gap.score_reasons,
        why_it_matters=gap.why_it_matters,
        research_opportunity=gap.research_opportunity,
    )


def _opportunity_from_result(opportunity: CodexOpportunityResult) -> ResearchOpportunity:
    return ResearchOpportunity(
        gap=opportunity.gap,
        research_question=opportunity.research_question,
        hypothesis=opportunity.hypothesis,
        proposed_method=opportunity.proposed_method,
        innovations_bound_to_gap=opportunity.innovations_bound_to_gap,
        required_data=opportunity.required_data,
        evaluation_protocol=opportunity.evaluation_protocol,
        baselines=opportunity.baselines,
        ablations=opportunity.ablations,
        risks=opportunity.risks,
        evidence_refs=opportunity.evidence_refs,
    )


def apply_codex_review(artifacts: SearchArtifacts, result: CodexReviewResult) -> SearchArtifacts:
    artifacts.synthesis = SynthesisReport(
        mode=result.mode,
        status=result.status,
        executive_summary=result.executive_summary,
        domain_interpretation=result.domain_interpretation,
        search_assessment=result.search_assessment,
        moc_takeaways=result.moc_takeaways,
        gap_summaries=[
            SynthesisGapSummary(
                gap=gap.gap,
                judgment=gap.judgment,
                support=gap.support,
                counter_evidence=gap.counter_evidence,
                evidence_refs=gap.evidence_refs,
                confidence=gap.confidence,
            )
            for gap in result.gaps
        ],
        recommended_opportunities=[
            (
                f"{opportunity.research_question} 建议方法方向：{opportunity.proposed_method}"
                if opportunity.proposed_method
                else opportunity.research_question
            )
            for opportunity in result.opportunities
        ],
        evidence_quality=result.evidence_quality,
        limitations=result.limitations,
        next_steps=result.next_steps,
    )
    if result.moc_groups:
        artifacts.topic_moc = _moc_from_result(artifacts, result)
        artifacts.comparison_matrix = _comparison_from_groups(result.moc_groups)
        if artifacts.source_readiness:
            artifacts.source_readiness.moc_groups = len(result.moc_groups)
            artifacts.source_readiness.reasons = [
                f"codex_manual_llm_pass_moc_groups={len(result.moc_groups)}",
                "manual review may override rule-based MOC grouping",
            ]
    if result.gaps:
        artifacts.gaps = [_gap_from_result(artifacts, gap) for gap in result.gaps if gap.gap]
    if result.opportunities:
        artifacts.research_opportunities = [
            _opportunity_from_result(opportunity)
            for opportunity in result.opportunities
            if opportunity.research_question
        ]
    return artifacts


def apply_codex_review_to_output(
    artifact_path: Path,
    result_path: Path,
    *,
    output_dir: Path | None = None,
) -> tuple[SearchArtifacts, Path]:
    from .dashboard import load_artifacts

    artifacts = load_artifacts(artifact_path)
    result = load_codex_review_result(result_path)
    target_dir = output_dir or (artifact_path if artifact_path.is_dir() else artifact_path.parent)
    artifacts = apply_codex_review(artifacts, result)
    artifacts.write_json(target_dir)
    write_analysis_report(artifacts, target_dir)
    write_report(artifacts, target_dir)
    dashboard_path = write_dashboard(artifacts, target_dir)
    return artifacts, dashboard_path
