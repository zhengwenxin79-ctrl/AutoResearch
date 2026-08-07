from __future__ import annotations

import json
from pathlib import Path

from .schema import SearchArtifacts


def _safe_json(artifacts: SearchArtifacts) -> str:
    return json.dumps(artifacts.model_dump(mode="json"), ensure_ascii=False).replace("</", "<\\/")


def load_artifacts(path: Path) -> SearchArtifacts:
    artifact_path = path
    if path.is_dir():
        artifact_path = path / "search_result.json"
    return SearchArtifacts.model_validate_json(artifact_path.read_text(encoding="utf-8"))


def write_dashboard(artifacts: SearchArtifacts, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    html = HTML_TEMPLATE.replace("__AUTORESEARCH_DATA__", _safe_json(artifacts))
    path = output_dir / "dashboard.html"
    path.write_text(html, encoding="utf-8")
    return path


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AutoResearch Dashboard</title>
  <style>
    :root {
      --bg: #f7f7f4;
      --panel: #ffffff;
      --panel-soft: #f0f4f3;
      --text: #202522;
      --muted: #68716d;
      --line: #d9dfdc;
      --teal: #176b5b;
      --blue: #345f8c;
      --amber: #91651a;
      --red: #9c3d35;
      --shadow: 0 1px 2px rgba(24, 32, 29, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--text);
      background: var(--bg);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }
    a { color: var(--blue); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .shell { max-width: 1440px; margin: 0 auto; padding: 24px; }
    .topbar {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 20px;
      align-items: end;
      padding: 8px 0 20px;
      border-bottom: 1px solid var(--line);
    }
    h1 { margin: 0; font-size: clamp(28px, 4vw, 46px); line-height: 1.04; letter-spacing: 0; }
    h2 { margin: 0 0 14px; font-size: 20px; letter-spacing: 0; }
    h3 { margin: 0; font-size: 16px; letter-spacing: 0; }
    .subtle { color: var(--muted); font-size: 14px; }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
    .link-button, .tab-button {
      min-height: 36px;
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--text);
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 14px;
      cursor: pointer;
      box-shadow: var(--shadow);
    }
    .link-button:hover, .tab-button:hover { border-color: #aeb8b4; text-decoration: none; }
    .tab-button.active { background: #20332e; color: #fff; border-color: #20332e; }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(140px, 1fr));
      gap: 12px;
      margin: 18px 0;
    }
    .metric {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-height: 96px;
      box-shadow: var(--shadow);
    }
    .metric-label { color: var(--muted); font-size: 12px; text-transform: uppercase; }
    .metric-value { margin-top: 8px; font-size: 28px; font-weight: 750; letter-spacing: 0; }
    .metric-note { margin-top: 2px; color: var(--muted); font-size: 13px; }
    .tabs { display: flex; gap: 8px; flex-wrap: wrap; margin: 18px 0; }
    .toolbar {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 16px;
    }
    .search {
      min-width: min(420px, 100%);
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 14px;
    }
    .section { display: none; }
    .section.active { display: block; }
    .grid-2 { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 14px; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      box-shadow: var(--shadow);
    }
    .card + .card { margin-top: 12px; }
    .card-header {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: start;
      margin-bottom: 10px;
    }
    .badge-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 3px 9px;
      border: 1px solid var(--line);
      background: var(--panel-soft);
      color: #33413c;
      font-size: 12px;
      white-space: nowrap;
    }
    .badge.teal { background: #e5f2ee; border-color: #b8d9cf; color: var(--teal); }
    .badge.amber { background: #fbf1dc; border-color: #e6c783; color: var(--amber); }
    .badge.red { background: #fae8e4; border-color: #e5b2aa; color: var(--red); }
    .kv {
      display: grid;
      grid-template-columns: minmax(120px, 190px) minmax(0, 1fr);
      gap: 8px 12px;
      margin-top: 12px;
      font-size: 14px;
    }
    .kv dt { color: var(--muted); }
    .kv dd { margin: 0; min-width: 0; overflow-wrap: anywhere; }
    table {
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      box-shadow: var(--shadow);
    }
    th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--line); }
    th { background: #ecf0ee; color: #48524e; font-size: 12px; text-transform: uppercase; }
    tr:last-child td { border-bottom: 0; }
    .status-ok { color: var(--teal); font-weight: 700; }
    .status-warn { color: var(--amber); font-weight: 700; }
    .status-bad { color: var(--red); font-weight: 700; }
    .confidence {
      height: 8px;
      background: #e2e7e4;
      border-radius: 999px;
      overflow: hidden;
      margin-top: 8px;
    }
    .confidence > span { display: block; height: 100%; background: var(--teal); }
    details {
      border-top: 1px solid var(--line);
      margin-top: 12px;
      padding-top: 10px;
    }
    summary { cursor: pointer; color: var(--blue); font-weight: 650; }
    .evidence-list { margin: 10px 0 0; padding-left: 18px; }
    .evidence-list li { margin-bottom: 10px; }
    .empty {
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 24px;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.55);
    }
    @media (max-width: 920px) {
      .topbar { grid-template-columns: 1fr; }
      .actions { justify-content: flex-start; }
      .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .grid-2, .grid-3 { grid-template-columns: 1fr; }
      .toolbar { align-items: stretch; flex-direction: column; }
      .kv { grid-template-columns: 1fr; }
    }
    @media (max-width: 560px) {
      .shell { padding: 16px; }
      .summary-grid { grid-template-columns: 1fr; }
      th, td { padding: 8px; font-size: 13px; }
      .card-header { flex-direction: column; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div>
        <p class="subtle">AutoResearch Dashboard</p>
        <h1 id="topic">Research Topic</h1>
        <p class="subtle" id="generatedAt"></p>
      </div>
      <div class="actions">
        <a class="link-button" href="report.md">Open report</a>
        <a class="link-button" href="source_coverage.md">Source coverage</a>
        <a class="link-button" href="gap_evidence_chains.md">Gap chains</a>
        <a class="link-button" href="research_opportunities.md">Opportunities</a>
      </div>
    </header>

    <section class="summary-grid" id="summaryGrid"></section>

    <nav class="tabs" aria-label="Dashboard tabs">
      <button class="tab-button active" data-tab="overview">Overview</button>
      <button class="tab-button" data-tab="papers">Papers</button>
      <button class="tab-button" data-tab="moc">MOC</button>
      <button class="tab-button" data-tab="gaps">Gaps</button>
      <button class="tab-button" data-tab="opportunities">Opportunities</button>
    </nav>

    <section id="overview" class="section active"></section>
    <section id="papers" class="section"></section>
    <section id="moc" class="section"></section>
    <section id="gaps" class="section"></section>
    <section id="opportunities" class="section"></section>
  </main>

  <script>
    const data = __AUTORESEARCH_DATA__;
    const state = { paperFilter: "" };

    const esc = (value) => String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

    const join = (values, fallback = "not explicit") => {
      if (!Array.isArray(values) || values.length === 0) return fallback;
      return values.filter(Boolean).map(esc).join("; ");
    };

    const sourceStats = () => {
      const stats = {};
      for (const row of data.source_statuses || []) {
        stats[row.source] ||= { queries: 0, ok: 0, failed: 0, skipped: 0, raw: 0 };
        stats[row.source].queries += 1;
        stats[row.source].raw += row.raw_count || 0;
        if (row.status === "ok") stats[row.source].ok += 1;
        else if (row.status === "skipped") stats[row.source].skipped += 1;
        else stats[row.source].failed += 1;
      }
      const ranked = {};
      for (const row of data.ranked_papers || []) {
        for (const source of row.paper?.source_records || []) {
          ranked[source] = (ranked[source] || 0) + 1;
        }
      }
      return Object.entries(stats).sort().map(([source, row]) => ({ source, ...row, ranked: ranked[source] || 0 }));
    };

    const badgeClass = (value) => {
      const text = String(value || "").toLowerCase();
      if (text.includes("ready") || text === "ok" || text === "yes") return "teal";
      if (text.includes("fail") || text.includes("no")) return "red";
      return "amber";
    };

    const metric = (label, value, note = "") => `
      <article class="metric">
        <div class="metric-label">${esc(label)}</div>
        <div class="metric-value">${esc(value)}</div>
        <div class="metric-note">${esc(note)}</div>
      </article>
    `;

    const renderSummary = () => {
      const readiness = data.source_readiness || {};
      const mocCount = data.topic_moc?.problem_spaces?.length || 0;
      document.getElementById("topic").textContent = data.topic || "Research Topic";
      document.getElementById("generatedAt").textContent = `Generated at ${data.generated_at || "unknown"}`;
      document.getElementById("summaryGrid").innerHTML = [
        metric("Readiness", readiness.status || "not evaluated", `${readiness.ranked_papers || 0} ranked papers`),
        metric("Papers", data.paper_cards?.length || 0, "structured paper cards"),
        metric("MOC Spaces", mocCount, "problem-space groups"),
        metric("Gaps", data.gaps?.length || 0, "evidence-backed claims"),
        metric("Opportunities", data.research_opportunities?.length || 0, "candidate projects"),
      ].join("");
    };

    const renderOverview = () => {
      const readiness = data.source_readiness || {};
      const sourceRows = sourceStats().map(row => `
        <tr>
          <td>${esc(row.source)}</td>
          <td>${row.queries}</td>
          <td class="status-ok">${row.ok}</td>
          <td class="status-bad">${row.failed}</td>
          <td class="status-warn">${row.skipped}</td>
          <td>${row.raw}</td>
          <td>${row.ranked}</td>
        </tr>
      `).join("");
      const llmRows = (data.llm_extractions || []).map(row => `
        <tr>
          <td>${esc(row.title)}</td>
          <td><span class="badge ${badgeClass(row.status)}">${esc(row.status)}</span></td>
          <td>${esc(row.model || "n/a")}</td>
          <td>${join(row.fields_updated, "none")}</td>
        </tr>
      `).join("");
      document.getElementById("overview").innerHTML = `
        <div class="grid-2">
          <section>
            <h2>Source Health</h2>
            <table>
              <thead>
                <tr>
                  <th>Source</th><th>Queries</th><th>OK</th><th>Failed</th>
                  <th>Skipped</th><th>Raw</th><th>Ranked</th>
                </tr>
              </thead>
              <tbody>${sourceRows}</tbody>
            </table>
          </section>
          <section>
            <h2>Readiness Gate</h2>
            <article class="card">
              <div class="card-header">
                <h3>${esc(readiness.status || "not evaluated")}</h3>
                <span class="badge ${badgeClass(readiness.status)}">${esc(readiness.status || "n/a")}</span>
              </div>
              <dl class="kv">
                <dt>Ranked papers</dt><dd>${esc(readiness.ranked_papers || 0)}</dd>
                <dt>Contributing sources</dt><dd>${esc(readiness.contributing_sources || 0)}</dd>
                <dt>MOC groups</dt><dd>${esc(readiness.moc_groups || 0)}</dd>
                <dt>Reasons</dt><dd>${join(readiness.reasons || [])}</dd>
              </dl>
            </article>
            <h2 style="margin-top:16px;">LLM Extraction</h2>
            ${llmRows ? `<table><thead><tr><th>Paper</th><th>Status</th><th>Model</th><th>Updated</th></tr></thead><tbody>${llmRows}</tbody></table>` : `<div class="empty">LLM extraction was not attempted.</div>`}
          </section>
        </div>
      `;
    };

    const paperMatches = (paper) => {
      const haystack = [
        paper.title, paper.problem, paper.task, paper.method_family,
        paper.missing_capability, paper.gap_hint
      ].join(" ").toLowerCase();
      return haystack.includes(state.paperFilter.toLowerCase());
    };

    const renderPapers = () => {
      const papers = (data.paper_cards || []).filter(paperMatches);
      const cards = papers.map((paper, idx) => `
        <article class="card">
          <div class="card-header">
            <div>
              <h3>${idx + 1}. ${esc(paper.title)}</h3>
              <p class="subtle">${esc(paper.year || "n.d.")} ${paper.venue ? `| ${esc(paper.venue)}` : ""}</p>
            </div>
            ${paper.url ? `<a class="link-button" href="${esc(paper.url)}">Open</a>` : ""}
          </div>
          <div class="badge-row">${(paper.coverage_tags || []).slice(0, 8).map(tag => `<span class="badge">${esc(tag)}</span>`).join("")}</div>
          <dl class="kv">
            <dt>Problem</dt><dd>${esc(paper.problem)}</dd>
            <dt>Task</dt><dd>${esc(paper.task)}</dd>
            <dt>Method family</dt><dd>${esc(paper.method_family)}</dd>
            <dt>Core assumption</dt><dd>${esc(paper.core_assumption)}</dd>
            <dt>Missing capability</dt><dd>${esc(paper.missing_capability)}</dd>
            <dt>Gap hint</dt><dd>${esc(paper.gap_hint)}</dd>
            <dt>Dataset</dt><dd>${esc(paper.dataset)}</dd>
            <dt>Metrics</dt><dd>${esc(paper.metrics)}</dd>
          </dl>
          <details>
            <summary>Evidence snippets</summary>
            <ol class="evidence-list">
              ${(paper.evidence_snippets || []).map(snippet => `<li><strong>${esc(snippet.claim)}</strong><br>${esc(snippet.snippet)}</li>`).join("") || "<li>No evidence snippet.</li>"}
            </ol>
          </details>
        </article>
      `).join("");
      document.getElementById("papers").innerHTML = `
        <div class="toolbar">
          <div>
            <h2>Paper Cards</h2>
            <p class="subtle">${papers.length} visible of ${(data.paper_cards || []).length}</p>
          </div>
          <input class="search" id="paperSearch" placeholder="Filter by problem, method, gap hint, title" value="${esc(state.paperFilter)}">
        </div>
        ${cards || `<div class="empty">No paper cards match the current filter.</div>`}
      `;
      document.getElementById("paperSearch").addEventListener("input", (event) => {
        state.paperFilter = event.target.value;
        renderPapers();
      });
    };

    const renderMoc = () => {
      const groups = data.topic_moc?.problem_spaces || [];
      document.getElementById("moc").innerHTML = `
        <div class="toolbar">
          <div>
            <h2>Problem-Space MOC</h2>
            <p class="subtle">${groups.length} groups built from cross-paper relations</p>
          </div>
          <a class="link-button" href="topic_moc.md">Open Markdown</a>
        </div>
        <div class="grid-2">
          ${groups.map(group => `
            <article class="card">
              <div class="card-header">
                <h3>${esc(group.name)}</h3>
                <span class="badge teal">${esc(group.problem_space)}</span>
              </div>
              <dl class="kv">
                <dt>Representative papers</dt><dd>${join(group.representative_papers)}</dd>
                <dt>Shared assumptions</dt><dd>${join(group.shared_assumptions)}</dd>
                <dt>Method families</dt><dd>${join(group.method_families)}</dd>
                <dt>Missing capabilities</dt><dd>${join(group.missing_capabilities)}</dd>
                <dt>Open questions</dt><dd>${join(group.open_questions)}</dd>
                <dt>Possible experiments</dt><dd>${join(group.possible_experiments)}</dd>
              </dl>
            </article>
          `).join("") || `<div class="empty">No MOC problem spaces were generated.</div>`}
        </div>
      `;
    };

    const renderGaps = () => {
      const gaps = data.gaps || [];
      document.getElementById("gaps").innerHTML = `
        <div class="toolbar">
          <div>
            <h2>Gap Evidence Chains</h2>
            <p class="subtle">Support, counter-evidence, and validation plans are shown together.</p>
          </div>
          <a class="link-button" href="gap_evidence_chains.md">Open Markdown</a>
        </div>
        ${gaps.map((gap, idx) => `
          <article class="card">
            <div class="card-header">
              <div>
                <h3>Gap ${idx + 1}: ${esc(gap.gap)}</h3>
                <p class="subtle">${esc(gap.why_it_matters)}</p>
              </div>
              <span class="badge ${badgeClass(gap.confidence >= 0.6 ? "ready" : "warn")}">confidence ${esc(gap.confidence)}</span>
            </div>
            <div class="confidence"><span style="width:${Math.round((gap.confidence || 0) * 100)}%"></span></div>
            <dl class="kv">
              <dt>Coverage</dt><dd>support ${gap.support_count}/${gap.total_papers}; counter ${gap.counter_count}/${gap.total_papers}; unclear ${gap.unclear_count}</dd>
              <dt>Research opportunity</dt><dd>${esc(gap.research_opportunity)}</dd>
              <dt>Score reasons</dt><dd>${join(gap.score_reasons)}</dd>
            </dl>
            <details open>
              <summary>Evidence chain</summary>
              <ol class="evidence-list">
                ${(gap.evidence_chain || []).map(step => `
                  <li>
                    <strong>${esc(step.paper_title)}</strong>
                    <span class="badge ${badgeClass(step.role === "counter" ? "no" : "yes")}">${esc(step.role)}</span>
                    <br>${esc(step.claim)}
                    ${step.missing_dimensions?.length ? `<br><span class="subtle">Missing: ${join(step.missing_dimensions)}</span>` : ""}
                  </li>
                `).join("") || "<li>No evidence chain.</li>"}
              </ol>
            </details>
          </article>
        `).join("") || `<div class="empty">No gaps were generated.</div>`}
      `;
    };

    const renderOpportunities = () => {
      const opportunities = data.research_opportunities || [];
      document.getElementById("opportunities").innerHTML = `
        <div class="toolbar">
          <div>
            <h2>Research Opportunities</h2>
            <p class="subtle">Each idea is bound to a previous gap evidence chain.</p>
          </div>
          <a class="link-button" href="research_opportunities.md">Open Markdown</a>
        </div>
        <div class="grid-2">
          ${opportunities.map((item, idx) => `
            <article class="card">
              <div class="card-header">
                <h3>Opportunity ${idx + 1}</h3>
                <span class="badge teal">evidence-backed</span>
              </div>
              <dl class="kv">
                <dt>Bound gap</dt><dd>${esc(item.gap)}</dd>
                <dt>Research question</dt><dd>${esc(item.research_question)}</dd>
                <dt>Hypothesis</dt><dd>${esc(item.hypothesis)}</dd>
                <dt>Proposed method</dt><dd>${esc(item.proposed_method)}</dd>
                <dt>Required data</dt><dd>${esc(item.required_data)}</dd>
                <dt>Evaluation</dt><dd>${join(item.evaluation_protocol)}</dd>
                <dt>Baselines</dt><dd>${join(item.baselines)}</dd>
                <dt>Ablations</dt><dd>${join(item.ablations)}</dd>
                <dt>Risks</dt><dd>${join(item.risks)}</dd>
                <dt>Evidence refs</dt><dd>${join(item.evidence_refs)}</dd>
              </dl>
            </article>
          `).join("") || `<div class="empty">No evidence-backed opportunities were generated.</div>`}
        </div>
      `;
    };

    const renderAll = () => {
      renderSummary();
      renderOverview();
      renderPapers();
      renderMoc();
      renderGaps();
      renderOpportunities();
    };

    document.querySelectorAll(".tab-button").forEach(button => {
      button.addEventListener("click", () => {
        document.querySelectorAll(".tab-button").forEach(item => item.classList.remove("active"));
        document.querySelectorAll(".section").forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        document.getElementById(button.dataset.tab).classList.add("active");
      });
    });

    renderAll();
  </script>
</body>
</html>
"""
