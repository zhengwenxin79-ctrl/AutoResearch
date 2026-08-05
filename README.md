# AutoResearch

AutoResearch is an evidence-grounded research workflow engine. The first MVP focuses only on
Auto Search:

```text
research topic -> papers -> paper cards -> field map -> gap evidence report
```

It is intentionally not a paper-writing machine. The goal is to produce a research map that can
support group discussion and later method/benchmark design.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

autoresearch search "medical VLM temporal lesion change analysis" --limit 20 --full-text-limit 6
```

Outputs are written to:

```text
outputs/<topic-slug>/
  raw/
  search_result.json
  paper_cards.json
  field_map.json
  gaps.json
  report.md
```

## Current MVP

- Query planning from a high-level research direction.
- Multi-source paper collection from arXiv, OpenAlex, PubMed, and CrossRef.
- Failure-tolerant source execution with warnings.
- DOI / PMID / arXiv / OpenAlex / fuzzy-title deduplication.
- Explainable ranking using lexical relevance, recency, citation count, source reliability, and
  research-signal keywords.
- Optional PDF/HTML full-text fetching for top-ranked papers.
- Section splitting for abstract, methods, experiments, results, limitations, and related sections.
- Paper card extraction from title, abstract, metadata, and section-aware full text when available.
- Lightweight field mapping by task, method, dataset, metric, and model type.
- Evidence-grounded gap finding with source URLs, snippets, and section labels.
- Markdown and JSON artifact export.

## Design Principle

Every gap should be traceable to evidence. If evidence is weak, AutoResearch should say so.
