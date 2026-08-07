from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from rich.console import Console

from .collectors import (
    search_arxiv,
    search_crossref,
    search_europepmc,
    search_openalex,
    search_openreview,
    search_pubmed,
)
from .dashboard import write_dashboard
from .dedupe import dedupe_papers
from .domain_profile import load_domain_profile
from .enrichment import enrich_ranked_papers
from .field_mapper import build_field_map
from .fulltext import fetch_full_texts
from .gap_finder import build_research_opportunities, find_gaps
from .llm_extractor import enhance_paper_cards_with_llm
from .moc import build_research_space
from .open_access import enrich_open_access
from .query_planner import plan_queries
from .ranker import rank_papers
from .reader import build_paper_cards
from .report import write_report
from .schema import PaperRecord, SearchArtifacts, SourceStatus
from .source_health import evaluate_source_readiness
from .synthesizer import build_synthesis, write_analysis_report
from .utils import slugify

Collector = Callable[[str, int], list[PaperRecord]]


COLLECTORS: dict[str, Collector] = {
    "arxiv": search_arxiv,
    "openalex": search_openalex,
    "pubmed": search_pubmed,
    "europepmc": search_europepmc,
    "crossref": search_crossref,
    "openreview": search_openreview,
}


def run_search(
    topic: str,
    *,
    limit: int = 30,
    output_root: Path = Path("outputs"),
    per_query_limit: int = 8,
    full_text_limit: int = 8,
    enrichment_limit: int = 20,
    open_access_limit: int = 20,
    source_failure_skip_threshold: int = 3,
    llm_card_limit: int = 0,
    llm_model: str = "",
    llm_timeout: float = 45.0,
    profile: str = "auto",
    console: Console | None = None,
) -> tuple[SearchArtifacts, Path]:
    console = console or Console()
    domain_profile = load_domain_profile(profile, topic)
    console.print(
        f"[cyan]profile[/cyan] {domain_profile.domain_id}: "
        f"{domain_profile.domain_name} ({len(domain_profile.capability_dimensions)} capabilities)"
    )
    plan = plan_queries(topic, domain_profile)
    statuses: list[SourceStatus] = []
    warnings: list[str] = []
    papers: list[PaperRecord] = []
    consecutive_failures: dict[str, int] = {}

    for query in plan.queries:
        for source_name, collector in COLLECTORS.items():
            if (
                source_failure_skip_threshold > 0
                and consecutive_failures.get(source_name, 0) >= source_failure_skip_threshold
            ):
                error = f"skipped after {source_failure_skip_threshold} consecutive failures"
                statuses.append(SourceStatus(source=source_name, query=query, status="skipped", error=error))
                console.print(f"[yellow]skip[/yellow] {source_name}: {error}")
                continue
            try:
                rows = collector(query, per_query_limit)
                papers.extend(rows)
                statuses.append(
                    SourceStatus(source=source_name, query=query, status="ok", raw_count=len(rows))
                )
                consecutive_failures[source_name] = 0
                console.print(f"[green]ok[/green] {source_name}: {len(rows)} results for {query!r}")
            except Exception as exc:  # noqa: BLE001 - keep one bad source/query from stopping the run.
                message = f"{source_name} failed for {query!r}: {exc}"
                warnings.append(message)
                consecutive_failures[source_name] = consecutive_failures.get(source_name, 0) + 1
                statuses.append(
                    SourceStatus(source=source_name, query=query, status="failed", error=str(exc))
                )
                console.print(f"[yellow]warn[/yellow] {message}")

    deduped = dedupe_papers([paper for paper in papers if paper.title])
    ranked = rank_papers(deduped, plan, limit=limit)
    output_dir = output_root / slugify(topic)
    influences = enrich_ranked_papers(ranked, limit=enrichment_limit)
    for title, influence in influences.items():
        if influence.status == "ok":
            console.print(
                f"[green]enrich[/green] {title[:80]} -> "
                f"citations={influence.citation_count}, refs={influence.reference_count}"
            )
        else:
            console.print(f"[yellow]enrich[/yellow] {title[:80]} -> {influence.status}: {influence.error[:120]}")
    open_access_records = enrich_open_access(ranked, limit=open_access_limit)
    for title, record in open_access_records.items():
        if record.status == "ok":
            console.print(
                f"[green]oa[/green] {title[:80]} -> "
                f"open={int(record.is_open_access)}, pdf={int(bool(record.pdf_url))}"
            )
        else:
            console.print(f"[yellow]oa[/yellow] {title[:80]} -> {record.status}: {record.error[:120]}")
    full_texts = fetch_full_texts(ranked, raw_dir=output_dir / "raw", limit=full_text_limit)
    for record in full_texts.values():
        if record.status == "ok":
            console.print(f"[green]fulltext[/green] {record.title[:80]} -> {len(record.sections)} sections")
        else:
            console.print(f"[yellow]fulltext[/yellow] {record.title[:80]} -> {record.status}: {record.error[:120]}")
    cards = build_paper_cards(
        ranked,
        full_texts=full_texts,
        influences=influences,
        profile=domain_profile,
    )
    llm_extractions = enhance_paper_cards_with_llm(
        cards,
        limit=llm_card_limit,
        model=llm_model,
        timeout=llm_timeout,
    )
    for record in llm_extractions:
        if record.status == "ok":
            console.print(
                f"[green]llm[/green] {record.title[:80]} -> "
                f"updated={','.join(record.fields_updated)}"
            )
        else:
            console.print(f"[yellow]llm[/yellow] {record.title[:80]} -> {record.status}: {record.error[:120]}")
    field_map = build_field_map(cards)
    gaps = find_gaps(cards, field_map, profile=domain_profile)
    paper_insights, topic_moc, comparison_matrix = build_research_space(
        topic,
        cards,
        gaps,
        profile=domain_profile,
    )
    source_readiness = evaluate_source_readiness(statuses, ranked, topic_moc)
    research_opportunities = build_research_opportunities(gaps, profile=domain_profile)

    artifacts = SearchArtifacts(
        topic=topic,
        domain_profile=domain_profile,
        query_plan=plan,
        source_statuses=statuses,
        ranked_papers=ranked,
        full_texts=list(full_texts.values()),
        influences=list(influences.values()),
        open_access_records=list(open_access_records.values()),
        llm_extractions=llm_extractions,
        source_readiness=source_readiness,
        paper_cards=cards,
        paper_insights=paper_insights,
        field_map=field_map,
        topic_moc=topic_moc,
        comparison_matrix=comparison_matrix,
        gaps=gaps,
        research_opportunities=research_opportunities,
        warnings=warnings,
    )
    artifacts.synthesis = build_synthesis(artifacts)
    artifacts.write_json(output_dir)
    write_analysis_report(artifacts, output_dir)
    write_report(artifacts, output_dir)
    write_dashboard(artifacts, output_dir)
    return artifacts, output_dir
