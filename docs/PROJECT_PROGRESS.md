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

## Next

- Add Semantic Scholar enrichment with optional API key.
- Add LitSearch-style evaluation for search/ranking quality.
- Add LLM-backed PaperCard extraction with strict evidence references.
