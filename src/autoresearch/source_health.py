from __future__ import annotations

from .schema import RankedPaper, SourceReadiness, SourceStatus, TopicMOC


def evaluate_source_readiness(
    statuses: list[SourceStatus],
    ranked_papers: list[RankedPaper],
    topic_moc: TopicMOC | None,
) -> SourceReadiness:
    contributing_sources = {
        source
        for ranked in ranked_papers
        for source in ranked.paper.source_records
        if source
    }
    failed_sources = sorted(
        {
            status.source
            for status in statuses
            if status.status != "ok"
            and not any(
                other.source == status.source and other.status == "ok" and other.raw_count > 0
                for other in statuses
            )
        }
    )
    moc_groups = len(topic_moc.paper_groups) if topic_moc else 0
    reasons = []
    if len(ranked_papers) >= 8:
        reasons.append(f"ranked_papers={len(ranked_papers)} meets minimum 8")
    else:
        reasons.append(f"ranked_papers={len(ranked_papers)} below minimum 8")
    if len(contributing_sources) >= 3:
        reasons.append(f"contributing_sources={len(contributing_sources)} meets minimum 3")
    else:
        reasons.append(f"contributing_sources={len(contributing_sources)} below minimum 3")
    if moc_groups >= 3:
        reasons.append(f"moc_groups={moc_groups} meets minimum 3")
    else:
        reasons.append(f"moc_groups={moc_groups} below minimum 3")
    if failed_sources:
        reasons.append(f"failed_or_empty_sources={', '.join(failed_sources)}")

    ready = len(ranked_papers) >= 8 and len(contributing_sources) >= 3 and moc_groups >= 3
    return SourceReadiness(
        status="ready_for_preliminary_gap_analysis" if ready else "needs_more_evidence",
        ranked_papers=len(ranked_papers),
        contributing_sources=len(contributing_sources),
        moc_groups=moc_groups,
        reasons=reasons,
        failed_sources=failed_sources,
    )
