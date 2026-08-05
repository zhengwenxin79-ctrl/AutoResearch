from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .pipeline import run_search

app = typer.Typer(help="AutoResearch command line interface.", no_args_is_help=True)
console = Console()
DEFAULT_OUTPUT_ROOT = Path("outputs")


@app.callback()
def main() -> None:
    """Evidence-grounded research workflow tools."""


@app.command()
def search(
    topic: str = typer.Argument(..., help="Research topic or direction."),
    limit: int = typer.Option(30, help="Number of deduplicated ranked papers to keep."),
    output_root: Path = typer.Option(  # noqa: B008
        DEFAULT_OUTPUT_ROOT,
        help="Directory for artifacts.",
    ),
    per_query_limit: int = typer.Option(8, help="Results per source/query pair."),
    full_text_limit: int = typer.Option(8, help="Number of top-ranked papers to fetch/read."),
) -> None:
    """Run Auto Search for a research topic."""
    artifacts, output_dir = run_search(
        topic,
        limit=limit,
        output_root=output_root,
        per_query_limit=per_query_limit,
        full_text_limit=full_text_limit,
        console=console,
    )
    console.print()
    console.print(f"[bold green]Done[/bold green] wrote artifacts to {output_dir}")
    console.print(f"Papers: {len(artifacts.ranked_papers)}")
    console.print(f"Gaps: {len(artifacts.gaps)}")
    console.print(f"Report: {output_dir / 'report.md'}")


if __name__ == "__main__":
    app()
