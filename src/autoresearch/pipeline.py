from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from rich.console import Console

from .collectors import search_arxiv, search_crossref, search_openalex, search_pubmed
from .dedupe import dedupe_papers
from .field_mapper import build_field_map
from .gap_finder import find_gaps
from .query_planner import plan_queries
from .ranker import rank_papers
from .reader import build_paper_cards
from .report import write_report
from .schema import PaperRecord, SearchArtifacts, SourceStatus
from .utils import slugify


Collector = Callable[[str, int], list[PaperRecord]]


COLLECTORS: dict[str, Collector] = {
    "arxiv": search_arxiv,
    "openalex": search_openalex,
    "pubmed": search_pubmed,
    "crossref": search_crossref,
}


def run_search(
    topic: str,
    *,
    limit: int = 30,
    output_root: Path = Path("outputs"),
    per_query_limit: int = 8,
    console: Console | None = None,
) -> tuple[SearchArtifacts, Path]:
    console = console or Console()
    plan = plan_queries(topic)
    statuses: list[SourceStatus] = []
    warnings: list[str] = []
    papers: list[PaperRecord] = []

    for query in plan.queries:
        for source_name, collector in COLLECTORS.items():
            try:
                rows = collector(query, per_query_limit)
                papers.extend(rows)
                statuses.append(
                    SourceStatus(source=source_name, query=query, status="ok", raw_count=len(rows))
                )
                console.print(f"[green]ok[/green] {source_name}: {len(rows)} results for {query!r}")
            except Exception as exc:
                message = f"{source_name} failed for {query!r}: {exc}"
                warnings.append(message)
                statuses.append(
                    SourceStatus(source=source_name, query=query, status="failed", error=str(exc))
                )
                console.print(f"[yellow]warn[/yellow] {message}")

    deduped = dedupe_papers([paper for paper in papers if paper.title])
    ranked = rank_papers(deduped, plan, limit=limit)
    cards = build_paper_cards(ranked)
    field_map = build_field_map(cards)
    gaps = find_gaps(cards, field_map)

    artifacts = SearchArtifacts(
        topic=topic,
        query_plan=plan,
        source_statuses=statuses,
        ranked_papers=ranked,
        paper_cards=cards,
        field_map=field_map,
        gaps=gaps,
        warnings=warnings,
    )
    output_dir = output_root / slugify(topic)
    artifacts.write_json(output_dir)
    write_report(artifacts, output_dir)
    return artifacts, output_dir

