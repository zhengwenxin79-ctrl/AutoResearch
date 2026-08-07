# Codex Review Workflow

This project uses Codex Review as the main research-judgment loop. The program collects and
structures evidence; Codex reviews the evidence and writes the research judgment back into the
artifacts and dashboard.

## Goal

```text
research topic
-> automated search and paper cards
-> rule-generated MOC / Gap / opportunities
-> Codex review packet
-> Codex-reviewed MOC / refined Gap / research opportunity
-> dashboard for inspection
```

Codex Review is the current main path. Local model backends are not part of the near-term plan.

## Step 1: Run Search

Use a domain profile when you know the area:

```bash
autoresearch search "GUI agent benchmark real-world workflow" --profile gui-agent
```

Expected output:

```text
outputs/<topic-slug>/
  search_result.json
  paper_cards.json
  topic_moc.md
  gap_evidence_chains.md
  research_opportunities.md
  dashboard.html
```

Checkpoint:

- The run keeps enough ranked papers.
- Source readiness is not ignored.
- The dashboard opens and shows rule-generated MOC, Gap, and opportunities.

## Step 2: Export Codex Packet

```bash
autoresearch codex-packet outputs/gui-agent-benchmark-real-world-workflow
```

This writes:

```text
codex_review_packet.md
codex_review_packet.json
codex_review_result.template.json
```

Checkpoint:

- `codex_review_packet.md` explains the review questions.
- `codex_review_packet.json` contains papers, evidence snippets, current MOC, current gaps, and current opportunities.
- `codex_review_result.template.json` defines the JSON structure Codex must fill.

## Step 3: Ask Codex To Review

Codex should read `codex_review_packet.json` and produce `codex_review_result.json`.

The review must answer:

- Which papers are core evidence?
- Which papers are adjacent evidence?
- Which papers are possible noise?
- Is the rule-generated MOC too coarse?
- Which original Gaps are valid, weak, or already solved?
- What counter-evidence changes the Gap?
- What is the refined Gap?
- What research opportunity follows from that refined Gap?
- What data, benchmark, metrics, baselines, and ablations are needed?

Checkpoint:

- Every refined Gap has support and/or counter papers.
- Evidence limitations are explicit.
- Research opportunities are bound to refined Gaps.
- The output is valid JSON matching the template.

## Step 4: Apply Codex Review

```bash
autoresearch codex-apply \
  outputs/gui-agent-benchmark-real-world-workflow \
  outputs/gui-agent-benchmark-real-world-workflow/codex_review_result.json
```

This writes the Codex-reviewed judgment back into:

```text
synthesis.json
analysis_report.md
topic_moc.md
comparison_matrix.md
gap_evidence_chains.md
research_opportunities.md
report.md
dashboard.html
```

Checkpoint:

- Dashboard shows `Codex-reviewed` as the judgment source.
- MOC groups reflect Codex's refined grouping.
- Gap evidence chains show refined Gaps and counter-evidence.
- Research opportunities are no longer generic templates.

## Step 5: Inspect And Decide

Open:

```text
outputs/<topic-slug>/dashboard.html
```

Review these tabs in order:

```text
Overview -> Papers -> MOC -> Gap -> Opportunities -> Analysis
```

Decision checklist:

- If source readiness is weak, improve search before trusting Gaps.
- If too many papers are adjacent/noise, fix source selection and ranker.
- If MOC has only one group, improve grouping before accepting the Gap.
- If counter-evidence is strong, rewrite the Gap instead of forcing it.
- If one refined Gap is stable, move to Auto Benchmark planning.

## Current Priority

The next engineering priority is not writing or local model integration. It is:

```text
profile-aware source selection
-> core / adjacent / noise evidence labels
-> better MOC grouping
-> repeatable Codex Review
```
