from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from .pipeline import run_search


app = typer.Typer(help="AutoResearch command line interface.", no_args_is_help=True)
console = Console()


@app.callback()
def main() -> None:
    """Evidence-grounded research workflow tools."""


@app.command()
def search(
    topic: str = typer.Argument(..., help="Research topic or direction."),
    limit: int = typer.Option(30, help="Number of deduplicated ranked papers to keep."),
    output_root: Path = typer.Option(Path("outputs"), help="Directory for artifacts."),
    per_query_limit: int = typer.Option(8, help="Results per source/query pair."),
) -> None:
    """Run Auto Search for a research topic."""
    artifacts, output_dir = run_search(
        topic,
        limit=limit,
        output_root=output_root,
        per_query_limit=per_query_limit,
        console=console,
    )
    console.print()
    console.print(f"[bold green]Done[/bold green] wrote artifacts to {output_dir}")
    console.print(f"Papers: {len(artifacts.ranked_papers)}")
    console.print(f"Gaps: {len(artifacts.gaps)}")
    console.print(f"Report: {output_dir / 'report.md'}")


if __name__ == "__main__":
    app()
