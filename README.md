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

To regenerate the UI from an existing run:

```bash
autoresearch dashboard outputs/medical-vlm-temporal-lesion-change-analysis
```

Optional Semantic Scholar API key:

```bash
export SEMANTIC_SCHOLAR_API_KEY="..."
```

Optional Unpaywall email for open-access PDF enrichment:

```bash
export UNPAYWALL_EMAIL="you@example.com"
```

Optional evidence-grounded LLM extraction:

```bash
export AUTORESEARCH_LLM_API_KEY="..."
export AUTORESEARCH_LLM_MODEL="..."
# Optional for local or non-default OpenAI-compatible endpoints:
export AUTORESEARCH_LLM_BASE_URL="https://api.openai.com/v1"

autoresearch search "medical VLM temporal lesion change analysis" --llm-card-limit 5
```

Outputs are written to:

```text
outputs/<topic-slug>/
  dashboard.html
  raw/
  source_coverage.md
  search_result.json
  paper_cards.json
  paper_insights.json
  influences.json
  open_access.json
  llm_extractions.json
  field_map.json
  topic_moc.json
  topic_moc.md
  comparison_matrix.json
  comparison_matrix.md
  gaps.json
  gap_evidence_chains.md
  research_opportunities.json
  research_opportunities.md
  report.md
  weakness_report.md
```

## Current MVP

- Query planning from a high-level research direction.
- Multi-source paper collection from arXiv, OpenAlex, PubMed, Europe PMC, CrossRef, and OpenReview.
- Failure-tolerant source execution with warnings.
- DOI / PMID / arXiv / OpenAlex / fuzzy-title deduplication.
- Explainable ranking using lexical relevance, recency, citation count, source reliability, and
  research-signal keywords.
- Optional PDF/HTML full-text fetching for top-ranked papers.
- Section splitting for abstract, methods, experiments, results, limitations, and related sections.
- Source stability guard: local arXiv cache, shorter arXiv timeout, and per-run source skipping after
  repeated consecutive failures.
- Semantic Scholar enrichment for citation counts, influential citation counts, references, fields
  of study, venue, and open-access PDF links.
- Unpaywall enrichment for DOI-based open-access landing pages and PDF links.
- Paper card extraction from title, abstract, metadata, and section-aware full text when available.
- Paper Card v2 fields with problem, method family, core assumption, evidence type, missing
  capability, relation-to-topic, gap hint, per-field evidence snippets, extraction status, and
  coverage tags.
- Optional LLM-backed Paper Card refinement through an OpenAI-compatible chat-completions endpoint.
  It is disabled by default and only updates fields that cite existing evidence snippet IDs.
- Paper Insight Cards that capture problem, method core, evidence, assumption, limitation,
  cross-paper relation, inspiration, and experimentable gap.
- Topic MOC v2 generation for core concepts, paper groups, problem spaces, shared assumptions,
  method families, datasets/benchmarks, covered capabilities, missing capabilities, open questions,
  and possible experiments.
- Cross-paper comparison matrix across paper groups: problem space, method family, temporal input,
  lesion localization, change evaluation, location consistency, benchmark/metric coverage, and gap
  hints.
- Lightweight field mapping by task, method, dataset, metric, and model type.
- Evidence-grounded gap finding with source URLs, snippets, section labels, support/counter counts,
  and confidence score reasons.
- Gap Evidence Chain v2 paper-level judgments: each paper is marked as support, counter, or unclear
  for each gap, with missing evidence and influence signals.
- Gap evidence chain Markdown export plus evidence-backed research opportunity generation.
- Weakness report optimized for research discussion: how each weakness emerges, evidence chain,
  counter evidence, why still open, experimentable idea, and verification plan.
- Static local dashboard UI for source health, paper cards, MOC problem spaces, gap evidence chains,
  and research opportunities.
- Source coverage report and readiness gate for validating search breadth before interpreting
  preliminary weaknesses.
- Markdown and JSON artifact export.

## Design Principle

Every gap should be traceable to evidence. If evidence is weak, AutoResearch should say so.
