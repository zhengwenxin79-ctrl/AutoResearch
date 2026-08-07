from __future__ import annotations

from collections import Counter
from pathlib import Path

from .schema import GapEvidence, SearchArtifacts, SynthesisGapSummary, SynthesisReport
from .utils import clean_text


def _join(values: list[str], fallback: str = "未明确") -> str:
    return "；".join(value for value in values if value) or fallback


def _source_assessment(artifacts: SearchArtifacts) -> str:
    statuses = artifacts.source_statuses
    if not statuses:
        return "本次没有记录信息源执行状态，因此不能判断检索覆盖是否充分。"
    by_status = Counter(status.status for status in statuses)
    by_source: dict[str, Counter[str]] = {}
    for status in statuses:
        by_source.setdefault(status.source, Counter())[status.status] += 1
    source_bits = [
        f"{source}: 成功 {counts.get('ok', 0)}，失败 {counts.get('failed', 0)}，跳过 {counts.get('skipped', 0)}"
        for source, counts in sorted(by_source.items())
    ]
    readiness = artifacts.source_readiness.status if artifacts.source_readiness else "not_evaluated"
    return (
        f"本次共执行 {len(statuses)} 个 source/query 组合，成功 {by_status.get('ok', 0)}，"
        f"失败 {by_status.get('failed', 0)}，跳过 {by_status.get('skipped', 0)}。"
        f"证据就绪状态为 `{readiness}`。分来源情况：{_join(source_bits)}。"
    )


def _domain_interpretation(artifacts: SearchArtifacts) -> str:
    profile = artifacts.domain_profile
    if not profile:
        return "本次没有显式 Domain Profile，只能把用户输入当作通用研究主题处理。"
    capabilities = [dimension.name for dimension in profile.capability_dimensions]
    return (
        f"我把这个研究方向理解为 `{profile.domain_name}` 领域。系统关注的核心概念是："
        f"{_join(profile.core_concepts[:8])}。后续 Gap 判断主要围绕这些能力维度展开："
        f"{_join(capabilities[:6])}。"
    )


def _moc_takeaways(artifacts: SearchArtifacts) -> list[str]:
    moc = artifacts.topic_moc
    if not moc or not moc.problem_spaces:
        return ["本次尚未形成稳定的 MOC 问题空间，需要扩大论文数量或补充全文证据。"]
    takeaways = []
    for group in moc.problem_spaces[:5]:
        missing = _join(group.missing_capabilities[:3])
        papers = len(group.representative_papers)
        takeaways.append(
            f"`{group.name}` 聚合了 {papers} 篇代表论文；它覆盖 `{_join(group.covered_capabilities[:3])}`，"
            f"但暴露的缺口是 `{missing}`。"
        )
    return takeaways


def _gap_judgment(gap: GapEvidence) -> str:
    if gap.confidence >= 0.65:
        strength = "较强"
    elif gap.confidence >= 0.45:
        strength = "中等"
    else:
        strength = "偏弱"
    return (
        f"这个 Gap 的证据强度为{strength}：{gap.support_count}/{gap.total_papers} 篇论文支持或暴露该弱点，"
        f"{gap.counter_count}/{gap.total_papers} 篇论文形成反证，置信度 {gap.confidence}。"
    )


def _gap_summary(gap: GapEvidence) -> SynthesisGapSummary:
    support_refs = [step.paper_title for step in gap.evidence_chain if step.role == "support"][:5]
    counter_refs = [step.paper_title for step in gap.evidence_chain if step.role == "counter"][:3]
    counter_text = (
        f"主要反证来自：{_join(counter_refs)}。"
        if counter_refs
        else "目前没有形成强反证，但这也可能是检索范围不足造成的。"
    )
    return SynthesisGapSummary(
        gap=gap.gap,
        judgment=_gap_judgment(gap),
        support=f"支持证据主要来自：{_join(support_refs)}。",
        counter_evidence=counter_text,
        evidence_refs=[*support_refs, *counter_refs],
        confidence=gap.confidence,
    )


def _recommended_opportunities(artifacts: SearchArtifacts) -> list[str]:
    if not artifacts.research_opportunities:
        return ["暂时不建议直接进入方法设计；应该先扩大检索或补充全文证据。"]
    recommendations = []
    for item in artifacts.research_opportunities[:3]:
        recommendations.append(
            f"围绕 `{item.gap}`，可以提出研究问题：{item.research_question} "
            f"建议方法方向：{item.proposed_method}"
        )
    return recommendations


def _evidence_quality(artifacts: SearchArtifacts) -> str:
    full_text_count = sum(1 for record in artifacts.full_texts if record.status == "ok")
    snippet_count = sum(len(card.evidence_snippets) for card in artifacts.paper_cards)
    if full_text_count:
        return (
            f"本次有 {full_text_count} 篇论文成功读取全文，纸面证据不只停留在摘要层面；"
            f"共记录 {snippet_count} 个主要证据片段。"
        )
    return (
        f"本次主要依赖摘要/元数据层面的证据，共记录 {snippet_count} 个主要证据片段。"
        "因此 Gap 可以作为初步研究判断，但还不适合作为最终论文动机。"
    )


def _limitations(artifacts: SearchArtifacts) -> list[str]:
    limitations = []
    if not artifacts.full_texts:
        limitations.append("本次未开启全文读取，method、experiment、limitation 字段主要来自摘要和元数据。")
    if artifacts.warnings:
        limitations.append(f"检索过程中有 {len(artifacts.warnings)} 条 source warning，需要后续重试或换源确认。")
    if artifacts.source_readiness and artifacts.source_readiness.status != "ready_for_preliminary_gap_analysis":
        limitations.append("source readiness 尚未达到初步 Gap 分析标准，当前结论应视为探索性结果。")
    profile = artifacts.domain_profile
    if profile and profile.domain_id != "medical-vlm":
        limitations.append("当前 ranker 和 source selection 仍未完全 profile-aware，非医学领域可能混入相邻或噪声论文。")
    return limitations or ["当前主要限制是证据仍需更多全文和 benchmark/dataset 级信息来加固。"]


def _next_steps(artifacts: SearchArtifacts) -> list[str]:
    profile = artifacts.domain_profile
    domain = profile.domain_name if profile else "当前领域"
    return [
        f"扩大 {domain} 的专用信息源，尤其是 benchmark、dataset registry、代码仓库和 leaderboard。",
        "对前 10-20 篇代表论文开启全文读取，重新抽取 method / experiment / limitation。",
        "让 LLM 或人工审查每个 Gap 的 support / counter evidence，剔除噪声论文。",
        "把最高优先级 Gap 转成一个可执行 benchmark 或 ablation 设计。",
    ]


def build_synthesis(artifacts: SearchArtifacts) -> SynthesisReport:
    profile = artifacts.domain_profile
    domain = profile.domain_name if profile else artifacts.topic
    strongest_gap = artifacts.gaps[0].gap if artifacts.gaps else "尚未形成稳定 Gap"
    summary = (
        f"本轮 AutoResearch 把 `{artifacts.topic}` 作为 `{domain}` 方向来分析，"
        f"共保留 {len(artifacts.ranked_papers)} 篇代表论文，形成 "
        f"{len(artifacts.topic_moc.problem_spaces) if artifacts.topic_moc else 0} 个 MOC 问题空间，"
        f"识别出 {len(artifacts.gaps)} 个候选 Gap。当前最值得优先检查的是：{strongest_gap}。"
    )
    return SynthesisReport(
        status="ready" if artifacts.gaps else "needs_more_evidence",
        executive_summary=summary,
        domain_interpretation=_domain_interpretation(artifacts),
        search_assessment=_source_assessment(artifacts),
        moc_takeaways=_moc_takeaways(artifacts),
        gap_summaries=[_gap_summary(gap) for gap in artifacts.gaps[:5]],
        recommended_opportunities=_recommended_opportunities(artifacts),
        evidence_quality=_evidence_quality(artifacts),
        limitations=_limitations(artifacts),
        next_steps=_next_steps(artifacts),
    )


def write_analysis_report(artifacts: SearchArtifacts, output_dir: Path) -> Path:
    synthesis = artifacts.synthesis or build_synthesis(artifacts)
    lines = [
        f"# AutoResearch 综合分析: {artifacts.topic}",
        "",
        "> 说明：本报告是 Codex 代替外部 LLM，根据 Domain Profile、论文卡片、MOC、Gap evidence chain 和研究机会生成的结构化分析。",
        "",
        "## 1. 总体判断",
        "",
        synthesis.executive_summary,
        "",
        "## 2. 领域理解",
        "",
        synthesis.domain_interpretation,
        "",
        "## 3. 信息源与证据质量",
        "",
        synthesis.search_assessment,
        "",
        synthesis.evidence_quality,
        "",
        "## 4. MOC 问题空间结论",
        "",
    ]
    for item in synthesis.moc_takeaways:
        lines.append(f"- {item}")
    lines.extend(["", "## 5. Gap / Weakness 判断", ""])
    for idx, gap in enumerate(synthesis.gap_summaries, start=1):
        lines.extend(
            [
                f"### Gap {idx}: {gap.gap}",
                "",
                f"- 判断：{gap.judgment}",
                f"- 支持：{gap.support}",
                f"- 反证：{gap.counter_evidence}",
                f"- 证据引用：{_join(gap.evidence_refs)}",
                "",
            ]
        )
    lines.extend(["## 6. 可转化的研究机会", ""])
    for item in synthesis.recommended_opportunities:
        lines.append(f"- {clean_text(item, 700)}")
    lines.extend(["", "## 7. 当前限制", ""])
    for item in synthesis.limitations:
        lines.append(f"- {item}")
    lines.extend(["", "## 8. 下一步建议", ""])
    for item in synthesis.next_steps:
        lines.append(f"- {item}")
    lines.append("")
    path = output_dir / "analysis_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
