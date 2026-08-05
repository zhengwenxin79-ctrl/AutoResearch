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

## Next

- Add full-text PDF parsing and section-aware evidence extraction.
- Add Semantic Scholar enrichment with optional API key.
- Add LitSearch-style evaluation for search/ranking quality.
- Add LLM-backed PaperCard extraction with strict evidence references.
