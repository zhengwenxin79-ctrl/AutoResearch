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
- Implemented Domain Profile v1:
  - added `DomainProfile` and `CapabilityDimension` schema objects
  - added profile generation / loading utilities with `auto`, `medical-vlm`, `gui-agent`,
    `llm-agent`, and generic fallback profiles
  - added repository profile seeds: `profiles/medical-vlm.json` and `profiles/gui-agent.json`
  - added CLI command `autoresearch profile <topic>` to generate an inspectable profile JSON
  - added `--profile` to `autoresearch search`, accepting profile ids or custom JSON paths
  - query planning now expands from profile query terms, capability dimensions, benchmark keywords,
    and metric keywords
  - paper cards now receive profile-grounded capability tags such as
    `capability:lesion-level-temporal-change-reasoning` and
    `capability:real-world-long-horizon-workflow`
  - Gap Finder now creates profile-grounded coverage gaps plus generic benchmark and metric gaps
  - non-medical MOC grouping now uses profile capability dimensions instead of medical-only groups
  - dashboard and Markdown report now show the active Domain Profile
  - search runs now write `domain_profile.json`
- Domain Profile smoke tests:
  - `medical VLM temporal lesion change analysis --profile medical-vlm`: `8` papers, `4` gaps,
    dashboard regenerated at `outputs/medical-vlm-temporal-lesion-change-analysis/dashboard.html`
  - Medical VLM gaps now include `lesion-level temporal change reasoning`,
    `paired-study benchmark coverage`, benchmark protocol, and target-capability metric coverage
  - `GUI agent benchmark real-world workflow --profile gui-agent`: `8` papers, `4` gaps,
    dashboard generated at `outputs/gui-agent-benchmark-real-world-workflow/dashboard.html`
  - GUI Agent gaps include `failure recovery and self-correction`, `environment reproducibility`,
    benchmark protocol, and target-capability metric coverage
  - limitation found: GUI Agent run still admits some adjacent medical/clinical agent papers because
    ranker and source selection are not fully profile-aware yet
- Implemented Codex-substituted synthesis layer for the later LLM analysis step:
  - added `SynthesisReport` and `SynthesisGapSummary` schema objects
  - added `src/autoresearch/synthesizer.py` to summarize Domain Profile, source quality, MOC
    takeaways, Gap evidence chains, research opportunities, limitations, and next steps in Chinese
  - search runs now write `synthesis.json` and `analysis_report.md`
  - added `autoresearch synthesize <output-dir-or-search_result.json>` to regenerate synthesis from
    existing artifacts
  - Dashboard now includes a Chinese `分析 / 综合分析` tab and a link to `analysis_report.md`
- Rebuilt synthesis demos:
  - Medical VLM analysis report:
    `outputs/medical-vlm-temporal-lesion-change-analysis/analysis_report.md`
  - GUI Agent analysis report:
    `outputs/gui-agent-benchmark-real-world-workflow/analysis_report.md`
- Fixed non-medical profile leakage in rule-based paper-card extraction:
  - GUI/LLM agent profiles no longer reuse medical-only task labels, method-family labels, gap
    hints, dataset fallbacks, metric fallbacks, or lesion localization coverage tags
  - regression test added to ensure a medical-looking paper mixed into a GUI Agent run is treated as
    adjacent evidence instead of forcing medical templates
  - remaining limitation: ranker and source selection can still retrieve adjacent clinical-agent
    papers; this is a source/ranking problem, not a paper-card template problem
- Reframed the near-term LLM strategy as Codex-in-the-loop as the main review path:
  - the program collects papers, extracts cards, builds rule-based MOC/Gaps, and packages evidence
  - Codex manually plays the expensive reasoning role: MOC refinement, Gap rewriting, counter-evidence
    resolution, research opportunity design, and next-step planning
  - local model backends are not part of the current plan; the project should stay controllable
    through explicit Codex Review packets and user-approved review results
- Implemented Codex Manual LLM Review v1:
  - added `autoresearch codex-packet <output-dir-or-search_result.json>` to export
    `codex_review_packet.md`, `codex_review_packet.json`, and `codex_review_result.template.json`
  - added `autoresearch codex-apply <output-dir-or-search_result.json> <codex_review_result.json>`
    to import Codex's structured judgment back into `synthesis`, `topic_moc`, `comparison_matrix`,
    `gaps`, `research_opportunities`, reports, and `dashboard.html`
  - added validation schemas for Codex MOC groups, refined gaps, opportunities, and synthesis fields
  - added tests for packet export and applying Codex review results
- Locked the current project direction:
  - AutoResearch should focus on automated evidence collection plus Codex-reviewed research judgment
  - the next small-step workflow is documented in `docs/CODEX_REVIEW_WORKFLOW.md`
  - Dashboard now makes the judgment source visible: `Rule-generated` vs `Codex-reviewed`
- Planned Profile-Aware Source / Ranker v1 without changing ranking behavior yet:
  - documented the current drift cause: every profile uses the same sources and ranker still has
    hard-coded medical/VLM/temporal assumptions
  - defined source policy, evidence policy, and paper-level evidence tiers:
    `core`, `adjacent`, `noise`, and `unknown`
  - proposed an intentionally small implementation order: relevance fixtures, profile policy schema,
    standalone evidence-tier scoring, then ranker/pipeline/dashboard integration
  - plan is documented in `docs/PROFILE_AWARE_SOURCE_RANKER_PLAN.md`
- Implemented the first three Profile-Aware Source / Ranker steps without changing ranking behavior:
  - added `SourcePolicy` and `EvidencePolicy` to `DomainProfile` with backward-compatible defaults
  - seeded GUI Agent, Medical VLM, LLM Agent, and generic profiles with source/evidence policies
  - added relevance fixtures for GUI Agent and Medical VLM core/adjacent/noise judgments
  - added `score_evidence_tier(paper, profile)` in `src/autoresearch/relevance.py`
  - added tests for profile policy loading, legacy profile compatibility, and fixture tier judgments
  - validation passed: `.venv/bin/pytest` -> 28 passed; `.venv/bin/ruff check .` -> all checks passed

## 2026-08-08

- Integrated Profile-Aware Evidence Tier scoring into the real search path:
  - extended `RankedPaper` and `PaperCard` with `evidence_tier`,
    `evidence_tier_score_delta`, and `evidence_tier_reasons`
  - updated `rank_papers(..., profile=None)` so legacy calls keep old behavior while profile-aware
    calls add `score_evidence_tier` deltas and reasons
  - updated `pipeline.py` to pass the active `domain_profile` into the ranker
  - propagated evidence tiers from ranked papers into paper cards and Codex Review packets
  - added ranker tests for legacy compatibility, GUI Agent medical-noise downranking, Medical VLM
    GUI-noise downranking, and Paper Card tier propagation
  - validation passed: `.venv/bin/pytest` -> 32 passed; `.venv/bin/ruff check .` -> all checks passed
- Ran a small GUI Agent demo with profile-aware ranking:
  - command used `--profile gui-agent --limit 12 --per-query-limit 3 --full-text-limit 0`
  - output: `.cache/profile-ranker-demo/gui-agent-benchmark-real-world-workflow`
  - top ranked papers were all labeled `core`
  - `MobileUse`, `GUI-ReWalk`, and `LongHorizonUI` appeared in the ranked set with positive
    evidence-tier deltas
  - OpenAlex returned `429 Too Many Requests` and was skipped after the existing failure threshold
  - Codex Review Packet generation succeeded and includes paper-level evidence tiers
- Added Dashboard evidence-tier display:
  - summary metrics now include core/adjacent/noise evidence counts
  - overview page shows a Chinese evidence-tier distribution table with tier meanings
  - paper cards show `核心证据` / `相邻证据` / `噪声/需降权` / `未判定`
  - expanded paper cards show ranking delta and translated tier reasons such as matched core
    keywords and source-policy decisions
  - regenerated and visually checked the GUI Agent dashboard through a local preview server
  - validation passed: `.venv/bin/pytest` -> 32 passed; `.venv/bin/ruff check .` -> all checks passed
- Added a clearer Dashboard mainline page after reviewing the desired MOC-style gap workflow and
  public research-assistant UI patterns:
  - new default `主线` tab presents `核心结论 -> 论文到 Gap 的链条 -> Gap 优先级 -> 推荐切入点`
  - evidence is grouped into core / adjacent / noise columns before the user opens detailed paper cards
  - Gap priority table puts support and counter-evidence next to each candidate weakness
  - the page separates `Rule-generated` from `Codex-reviewed` so users can see whether a claim has
    passed manual Codex review
  - applied the existing Codex Review result to the GUI Agent demo so the visible mainline now
    emphasizes `failure-conditioned GUI workflow benchmark / evaluation`
  - validation passed: `.venv/bin/pytest` -> 32 passed; `.venv/bin/ruff check .` -> all checks passed

## Next

- Add source-quality reporting: source -> core / adjacent / noise contribution counts.
- Add Codex-reviewed PaperInsight and MOC refinement with strict evidence references.
- Add review/evaluation fixtures to compare rule-generated vs Codex-reviewed extraction quality.
- Add query/source balancing so weak sources do not dominate runtime and source diversity is explicit.
- Add Papers With Code / benchmark archive support as a dataset and benchmark source, not as a primary paper search source.
- Add LitSearch-style evaluation for search/ranking quality.
