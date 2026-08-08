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

AutoResearch can run with an explicit domain profile:

```bash
autoresearch search "medical VLM temporal lesion change analysis" --profile medical-vlm
autoresearch search "GUI agent benchmark real-world workflow" --profile gui-agent
```

To generate a profile from a topic before running search:

```bash
autoresearch profile "GUI agent benchmark real-world workflow"
```

To regenerate the UI from an existing run:

```bash
autoresearch dashboard outputs/medical-vlm-temporal-lesion-change-analysis
```

To regenerate the Chinese synthesis and UI from an existing run:

```bash
autoresearch synthesize outputs/gui-agent-benchmark-real-world-workflow
```

To serve generated dashboards through a small read-only web server:

```bash
AUTORESEARCH_PORT=8766 autoresearch-server
```

Open `http://127.0.0.1:8766/`. Deployment notes for ECS / Nginx are in
`docs/DEPLOY.md`.

To let Codex act as the manual LLM reviewer for MOC, Gap, and opportunities:

```bash
autoresearch codex-packet outputs/gui-agent-benchmark-real-world-workflow
# Ask Codex to read codex_review_packet.json and write codex_review_result.json.
autoresearch codex-apply \
  outputs/gui-agent-benchmark-real-world-workflow \
  outputs/gui-agent-benchmark-real-world-workflow/codex_review_result.json
```

The detailed workflow is documented in `docs/CODEX_REVIEW_WORKFLOW.md`. Codex Review is the current
main research-judgment path: automated code collects evidence, and Codex reviews/refines MOC, Gap,
and research opportunities.

The next search-quality plan is documented in `docs/PROFILE_AWARE_SOURCE_RANKER_PLAN.md`. It keeps
steps small: first label core/adjacent/noise evidence, then connect the labels to ranking and UI.

Optional Semantic Scholar API key:

```bash
export SEMANTIC_SCHOLAR_API_KEY="..."
```

Optional Unpaywall email for open-access PDF enrichment:

```bash
export UNPAYWALL_EMAIL="you@example.com"
```

Experimental API-based paper-card extraction:

```bash
export AUTORESEARCH_LLM_API_KEY="..."
export AUTORESEARCH_LLM_MODEL="..."
export AUTORESEARCH_LLM_BASE_URL="https://api.openai.com/v1"

autoresearch search "medical VLM temporal lesion change analysis" --llm-card-limit 5
```

This is not the current main path. The main path is Codex Review through `codex-packet` and
`codex-apply`.

Outputs are written to:

```text
outputs/<topic-slug>/
  dashboard.html
  domain_profile.json
  raw/
  source_coverage.md
  search_result.json
  synthesis.json
  analysis_report.md
  codex_review_packet.md
  codex_review_packet.json
  codex_review_result.template.json
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
- Domain Profile v1: `auto`, `medical-vlm`, `gui-agent`, `llm-agent`, or a custom JSON profile can
  define core concepts, query terms, capability dimensions, benchmark keywords, metric keywords, and
  gap lenses before search starts.
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
- Profile-grounded paper card coverage tags, including capability-specific tags such as
  `capability:real-world-long-horizon-workflow` or
  `capability:lesion-level-temporal-change-reasoning`.
- Paper Card v2 fields with problem, method family, core assumption, evidence type, missing
  capability, relation-to-topic, gap hint, per-field evidence snippets, extraction status, and
  coverage tags.
- Profile-aware non-medical paper-card heuristics so GUI/LLM agent runs do not reuse medical-only
  task, gap-hint, method-family, dataset, metric, or localization templates.
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
- Profile-grounded Gap Finder that can generate coverage, benchmark, and metric gaps for the
  selected domain instead of only using the medical VLM demo rules.
- Gap Evidence Chain v2 paper-level judgments: each paper is marked as support, counter, or unclear
  for each gap, with missing evidence and influence signals.
- Gap evidence chain Markdown export plus evidence-backed research opportunity generation.
- Chinese synthesis layer that lets Codex stand in for the later LLM step by summarizing Domain
  Profile, source quality, MOC takeaways, Gap evidence chains, limitations, and next actions into
  `analysis_report.md` and `synthesis.json`.
- Codex-in-the-loop review mode: `codex-packet` exports evidence for manual Codex review, and
  `codex-apply` imports Codex's structured JSON judgment back into MOC, Gap evidence chains,
  research opportunities, synthesis, reports, and the dashboard.
- Dashboard clearly marks whether current research judgments are `Rule-generated` or
  `Codex-reviewed`.
- Weakness report optimized for research discussion: how each weakness emerges, evidence chain,
  counter evidence, why still open, experimentable idea, and verification plan.
- Static local dashboard UI for source health, paper cards, MOC problem spaces, gap evidence chains,
  research opportunities, and synthesis.
- Dashboard UI labels and rule-generated research signals are localized in Chinese while preserving
  original paper titles and evidence snippets.
- Dashboard top actions switch between Chinese in-page tabs instead of jumping to Markdown exports.
- Dashboard shows the active Domain Profile, core concepts, capability dimensions, benchmark/metric
  keywords, and gap lenses.
- Paper cards, MOC problem spaces, Gap evidence chains, and research opportunities are expandable
  detail panels, with an LLM extraction summary shown at the top of the page.
- Source coverage report and readiness gate for validating search breadth before interpreting
  preliminary weaknesses.
- Markdown and JSON artifact export.

## Design Principle

Every gap should be traceable to evidence. If evidence is weak, AutoResearch should say so.
