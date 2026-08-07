# Project Progress

## 2026-08-05

- Initialized AutoResearch as an independent project.
- Implemented Auto Search MVP:
  - query planning
  - arXiv / OpenAlex / PubMed / CrossRef collectors
  - deduplication
  - explainable ranking
  - paper cards
  - field map
  - evidence-grounded gap report
- Smoke test passed with:
  - topic: `medical VLM temporal lesion change analysis`
  - query count: 10
  - source/query executions: 40
  - raw candidates: 185
  - source failures: 0
  - ranked papers: 20
  - paper cards: 20
  - generated gaps: 3
  - report: `outputs/medical-vlm-temporal-lesion-change-analysis/report.md`
- Added full-text reading pipeline:
  - fetches PDF/HTML for top-ranked papers
  - extracts plain text from PDFs with PyMuPDF
  - splits papers into sections such as abstract, methods, experiments, and limitations
  - feeds section-aware text into paper cards, dataset/metric extraction, and gap evidence
  - writes full-text records into `search_result.json` and a `Full-Text Reading` section in the report
- Full-text smoke test passed with:
  - full-text limit: 6
  - successful full-text reads: 5
  - recorded fetch failures: 1
  - ranked papers: 20
  - paper cards: 20
  - generated gaps: 3
- Added Paper Card v2 and Gap Evidence Scoring:
  - paper cards now include field-level evidence, extraction status, and coverage tags
  - gap finder now scores support/counter/unclear coverage across retrieved papers
  - confidence now includes score reasons and a full-text evidence count
  - report now shows coverage tags and gap coverage statistics
- Gap scoring smoke test passed on `medical VLM temporal lesion change analysis`:
  - lesion-level temporal gap: support `15/20`, counter `5/20`, confidence `0.73`
  - dataset/benchmark gap: support `16/20`, counter `4/20`, confidence `0.74`
  - metric gap: support `8/20`, counter `12/20`, confidence `0.38`
- Added Gap Evidence Chain v2:
  - Semantic Scholar enrichment adds citations, influential citations, references, venue, fields of study, and open-access PDF links
  - paper cards now include optional influence metadata
  - each gap now includes paper-level judgments with `support` / `counter` / `unclear` roles
  - judgments explain missing evidence and include influence score reasons
  - confidence is adjusted when counter-evidence papers have notable influence signals

## 2026-08-07

- Reframed the next core direction from rule-based gap detection to MOC-style gap discovery.
- Key insight:
  - AutoResearch should not find gaps only from single-paper limitations or keyword absence.
  - Strong gaps should emerge from a problem-space map: single-paper notes, topic MOC aggregation, cross-paper comparison, method-family abstraction, shared assumptions, shared bottlenecks, open questions, and experimentable ideas.
- Target thinking pipeline:
  - single-paper insight card
  - topic MOC aggregation
  - cross-paper comparison matrix
  - method pattern and assumption mapping
  - weakness/gap discovery
  - counter-evidence resolution
  - experimentable research opportunity
- Proposed new artifacts:
  - `topic_moc.md`
  - `comparison_matrix.md`
  - `weakness_report.md`
- Proposed Paper Insight Card fields:
  - problem
  - method core
  - evidence
  - assumption
  - limitation
  - relation to other papers
  - inspiration
  - experimentable gap
- Gap types to support:
  - coverage gap
  - assumption gap
  - benchmark gap
  - contradiction gap
  - experimentability gap
- Updated product direction:
  - AutoResearch should become a research-judgment tool that explains how research questions grow from paper relationships, not just a paper search and summary pipeline.
- Implemented MOC-style Gap Discovery v1:
  - added Paper Insight Cards with problem, method core, evidence, assumption, limitation, relation to other papers, inspiration, and experimentable gap
  - added Topic MOC generation for core concepts, paper groups, method patterns, shared assumptions, open questions, and related themes
  - added Cross-paper Comparison Matrix across paper groups, including solves, missing dimensions, assumptions, and benchmark/metric coverage
  - added Weakness Report focused on how each weakness emerges, evidence chain, counter evidence, why still open, experimentable idea, and verification plan
  - added JSON and Markdown artifacts: `paper_insights.json`, `topic_moc.json`, `topic_moc.md`, `comparison_matrix.json`, `comparison_matrix.md`, `weakness_report.md`
- MOC smoke test passed on `medical VLM temporal lesion change analysis`:
  - ranked papers: `12`
  - paper insights: `12`
  - topic MOC groups: `6`
  - comparison rows: `6`
  - generated weaknesses: `3`
  - note: arXiv returned multiple `429`/timeout errors during this run, but OpenAlex/PubMed/CrossRef kept the pipeline running
- Reordered the next roadmap:
  - expand information sources first
  - build and validate the minimum MOC demo
  - only then interpret weakness/gap outputs
- Implemented Source Expansion v1:
  - added Europe PMC as a medical/life-sciences search collector
  - added OpenReview lightweight search as an AI/ML venue collector
  - added Unpaywall DOI-based open-access enrichment for landing page and PDF links
  - added `source_coverage.md` to summarize source execution, ranked contribution, full-text/OA coverage, MOC group coverage, and warnings
  - marked `weakness_report.md` as preliminary and dependent on source/MOC validation
- Source Expansion smoke test passed on `medical VLM temporal lesion change analysis` with `--per-query-limit 1` and enrichment/full-text disabled:
  - source/query executions: `60`
  - sources represented: `arxiv`, `openalex`, `pubmed`, `europepmc`, `crossref`, `openreview`
  - raw results: `openalex=10`, `pubmed=8`, `europepmc=10`, `crossref=9`, `openreview=10`, `arxiv=0`
  - ranked papers: `8`
  - topic MOC groups: `5`
  - comparison rows: `5`
  - note: arXiv still returned `429`/timeout errors and should be handled by source cache/backoff next
- Implemented MOC v2 + Gap Evidence v1 execution plan:
  - expanded Paper Card v2 with `problem`, `method_family`, `core_assumption`, `evidence_type`,
    `missing_capability`, `relation_to_topic`, and `gap_hint`
  - upgraded Topic MOC from simple paper grouping to problem-space MOC nodes with representative
    papers, shared assumptions, method families, datasets/benchmarks, metrics, covered capabilities,
    missing capabilities, open questions, and possible experiments
  - upgraded Comparison Matrix with temporal-input, lesion-localization, change-evaluation, and
    location-consistency columns
  - added explicit `gap_evidence_chains.md`
  - added evidence-backed `research_opportunities.json` and `research_opportunities.md`
  - added source readiness gate: `ready_for_preliminary_gap_analysis` vs `needs_more_evidence`
  - added arXiv local cache, shorter arXiv timeout, and per-run source skipping after repeated
    consecutive failures
- MOC v2 smoke test passed on `medical VLM temporal lesion change analysis` with `--limit 8`,
  `--per-query-limit 1`, and enrichment/full-text disabled:
  - ranked papers: `8`
  - generated gaps: `3`
  - research opportunities: `3`
  - source readiness: `ready_for_preliminary_gap_analysis`
  - MOC groups: `5`
  - source/query rows: `60`
  - arXiv: `0 ok`, `3 failed`, `7 skipped`
  - raw results: `openalex=10`, `pubmed=8`, `europepmc=10`, `crossref=9`, `openreview=10`, `arxiv=0`
  - key artifacts: `source_coverage.md`, `topic_moc.md`, `comparison_matrix.md`,
    `gap_evidence_chains.md`, `research_opportunities.md`, `weakness_report.md`
- Implemented optional LLM-backed Paper Card extraction:
  - added OpenAI-compatible chat-completions integration controlled by `AUTORESEARCH_LLM_API_KEY`,
    `AUTORESEARCH_LLM_MODEL`, and optional `AUTORESEARCH_LLM_BASE_URL`
  - added CLI flags: `--llm-card-limit`, `--llm-model`, and `--llm-timeout`
  - LLM extraction is disabled by default and safe to skip when no key/model is configured
  - each LLM-updated field must cite existing evidence snippet IDs; unsupported fields are ignored
  - added `llm_extractions.json` and an LLM extraction section in `report.md`
  - added tests for fenced JSON parsing, evidence-id validation, and no-key skip behavior
- LLM extraction smoke test passed with API keys intentionally unset:
  - command used `--llm-card-limit 2 --llm-model test-model`
  - `llm_extractions.json` recorded `2` skipped records with a clear missing-key message
  - no external LLM request was made
  - source readiness correctly reported `needs_more_evidence` when the demo was limited to `5`
    ranked papers, validating the readiness gate behavior
- Implemented static Dashboard UI:
  - search runs now automatically write `dashboard.html`
  - added `autoresearch dashboard <output-dir-or-search_result.json>` for regenerating the UI from
    existing artifacts
  - Dashboard tabs: Overview, Papers, MOC, Gaps, Opportunities
  - Overview shows source health, readiness gate, and LLM extraction status
  - Papers view supports filtering and expands evidence snippets
  - MOC view shows problem spaces, shared assumptions, missing capabilities, open questions, and
    possible experiments
  - Gaps view shows confidence, support/counter coverage, and evidence chains
  - Opportunities view shows evidence-bound research question, method, evaluation, baselines,
    ablations, and risks
- Dashboard demo regenerated for `medical VLM temporal lesion change analysis`:
  - ranked papers: `8`
  - generated gaps: `3`
  - source readiness: `ready_for_preliminary_gap_analysis`
  - arXiv: `1 failed`, `9 skipped`
  - dashboard path: `outputs/medical-vlm-temporal-lesion-change-analysis/dashboard.html`
- Localized Dashboard UI to Chinese:
  - translated navigation, metric cards, source table, readiness gate, paper-card field labels,
    MOC labels, Gap labels, and Research Opportunity labels
  - added Chinese mappings for common rule-generated signals such as problem spaces, method
    families, missing capabilities, gap claims, evidence roles, readiness reasons, evaluation
    items, baselines, ablations, and risks
  - preserved original paper titles and evidence snippets to avoid distorting source content
  - regenerated `outputs/medical-vlm-temporal-lesion-change-analysis/dashboard.html`
- Improved Dashboard interaction for the research-review demo:
  - top actions now navigate within the Chinese dashboard instead of opening Markdown exports
  - Paper Cards, MOC problem spaces, Gap evidence chains, and Research Opportunities are expandable
    panels
  - added a top LLM extraction strip and a detailed LLM extraction table in Overview
  - added Chinese error hints for skipped or failed LLM extraction states
  - changed dashboard HTML language metadata to `zh-CN`
  - ignored repo-local `.cache/` search cache files
- Reran `medical VLM temporal lesion change analysis` with LLM extraction enabled for the top `3`
  paper cards:
  - ranked papers: `8`
  - generated gaps: `3`
  - research opportunities: `3`
  - source readiness: `ready_for_preliminary_gap_analysis`
  - source coverage: arXiv `1 ok / 1 failed / 8 skipped`, CrossRef `0 ok / 1 failed / 9 skipped`,
    OpenAlex `10 ok`, PubMed `10 ok`, Europe PMC `10 ok`, OpenReview `10 ok`
  - LLM extraction model: `gpt-4o-mini`
  - LLM extraction result: `3 failed`, `0 updated`
  - failure reason: OpenAI-compatible endpoint returned `429 Too Many Requests`
  - regenerated `outputs/medical-vlm-temporal-lesion-change-analysis/dashboard.html`

## Next

- Add LLM-backed PaperInsight and MOC group refinement with strict evidence references.
- Add prompt/evaluation fixtures to compare rule-based vs LLM-backed card extraction quality.
- Add query/source balancing so weak sources do not dominate runtime and source diversity is explicit.
- Add Papers With Code / benchmark archive support as a dataset and benchmark source, not as a primary paper search source.
- Add LitSearch-style evaluation for search/ranking quality.
