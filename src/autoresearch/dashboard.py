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
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AutoResearch 调研看板</title>
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
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
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
    .profile-strip,
    .llm-strip {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 16px;
      box-shadow: var(--shadow);
      margin-bottom: 18px;
    }
    .profile-strip strong,
    .llm-strip strong { display: block; margin-bottom: 3px; }
    .llm-strip.ok { border-left: 4px solid var(--teal); }
    .llm-strip.warn { border-left: 4px solid var(--amber); }
    .llm-strip.bad { border-left: 4px solid var(--red); }
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
    details.card {
      display: block;
      padding: 0;
      overflow: hidden;
    }
    details.card + details.card { margin-top: 12px; }
    .fold-summary {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: start;
      padding: 16px;
      color: var(--text);
      list-style: none;
    }
    .fold-summary::-webkit-details-marker { display: none; }
    .fold-summary::after {
      content: "展开";
      color: var(--blue);
      font-size: 13px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 10px;
      white-space: nowrap;
    }
    details[open] > .fold-summary::after { content: "收起"; }
    .fold-content {
      border-top: 1px solid var(--line);
      padding: 14px 16px 16px;
    }
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
    .badge.gray { background: #eef1ef; border-color: #d5dbd8; color: #59635f; }
    .tier-note {
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
    }
    .mainline-layout {
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
      gap: 14px;
      align-items: start;
    }
    .verdict {
      border-left: 4px solid var(--teal);
      background: #fbfcfb;
    }
    .logic-chain {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 14px;
    }
    .chain-step {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-height: 128px;
      box-shadow: var(--shadow);
    }
    .step-index {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 26px;
      height: 26px;
      border-radius: 999px;
      background: #20332e;
      color: #fff;
      font-size: 12px;
      font-weight: 750;
      margin-bottom: 8px;
    }
    .evidence-columns {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 14px;
    }
    .evidence-column {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      box-shadow: var(--shadow);
    }
    .paper-list {
      margin: 10px 0 0;
      padding-left: 18px;
      font-size: 13px;
    }
    .paper-list li { margin-bottom: 8px; }
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
      .grid-2, .grid-3, .mainline-layout, .logic-chain, .evidence-columns { grid-template-columns: 1fr; }
      .toolbar { align-items: stretch; flex-direction: column; }
      .kv { grid-template-columns: 1fr; }
      .profile-strip, .llm-strip { grid-template-columns: 1fr; }
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
        <p class="subtle">AutoResearch 调研看板</p>
        <h1 id="topic">研究主题</h1>
        <p class="subtle" id="generatedAt"></p>
      </div>
      <div class="actions">
        <button class="link-button" data-tab-go="mainline" type="button">研究主线</button>
        <button class="link-button" data-tab-go="overview" type="button">信息源覆盖</button>
        <button class="link-button" data-tab-go="papers" type="button">论文卡片</button>
        <button class="link-button" data-tab-go="gaps" type="button">Gap 证据链</button>
        <button class="link-button" data-tab-go="opportunities" type="button">研究机会</button>
        <button class="link-button" data-tab-go="synthesis" type="button">综合分析</button>
      </div>
    </header>

    <section class="profile-strip" id="profileStrip"></section>
    <section class="summary-grid" id="summaryGrid"></section>
    <section class="llm-strip" id="llmStrip"></section>

    <nav class="tabs" aria-label="看板标签页">
      <button class="tab-button active" data-tab="mainline">主线</button>
      <button class="tab-button" data-tab="overview">总览</button>
      <button class="tab-button" data-tab="papers">论文</button>
      <button class="tab-button" data-tab="moc">MOC</button>
      <button class="tab-button" data-tab="gaps">Gap</button>
      <button class="tab-button" data-tab="opportunities">机会</button>
      <button class="tab-button" data-tab="synthesis">分析</button>
    </nav>

    <section id="mainline" class="section active"></section>
    <section id="overview" class="section"></section>
    <section id="papers" class="section"></section>
    <section id="moc" class="section"></section>
    <section id="gaps" class="section"></section>
    <section id="opportunities" class="section"></section>
    <section id="synthesis" class="section"></section>
  </main>

  <script>
    const data = __AUTORESEARCH_DATA__;
    const state = { paperFilter: "" };

    const esc = (value) => String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

    const translations = new Map([
      ["lesion-level temporal change reasoning", "病灶级时序变化推理"],
      ["longitudinal or temporal medical image understanding", "纵向或时序医学影像理解"],
      ["lesion or finding localization in medical multimodal tasks", "医学多模态任务中的病灶/发现定位"],
      ["clinical report generation and textual finding description", "临床报告生成与文本化发现描述"],
      ["single-study medical VLM diagnosis or question answering", "单次检查医学 VLM 诊断或问答"],
      ["medical AI evaluation and benchmark construction", "医学 AI 评估与 Benchmark 构建"],
      ["general medical multimodal foundation capability", "通用医学多模态基础能力"],
      ["temporal change analysis", "时序变化分析"],
      ["visual question answering", "视觉问答"],
      ["medical report generation", "医学报告生成"],
      ["lesion segmentation/localization", "病灶分割/定位"],
      ["diagnosis/classification", "诊断/分类"],
      ["general medical AI / multimodal research", "通用医学 AI / 多模态研究"],
      ["vision-language model", "视觉语言模型"],
      ["instruction tuning", "指令微调"],
      ["contrastive/alignment learning", "对比/对齐学习"],
      ["retrieval-augmented method", "检索增强方法"],
      ["mask-guided modeling", "Mask 引导建模"],
      ["lesion- or region-guided modeling", "病灶/区域引导建模"],
      ["instruction-tuned multimodal modeling", "指令微调多模态建模"],
      ["contrastive vision-language alignment", "对比式视觉语言对齐"],
      ["retrieval-augmented multimodal modeling", "检索增强多模态建模"],
      ["medical vision-language foundation model", "医学视觉语言基础模型"],
      ["method family not explicit", "方法族未明确"],
      ["not explicit", "未明确"],
      ["not explicit in abstract", "摘要中未明确"],
      ["not explicit in extracted cards", "抽取卡片中未明确"],
      ["abstract/metadata evidence", "摘要/元数据证据"],
      ["full-text section evidence", "全文章节证据"],
      ["dataset named", "命名了数据集"],
      ["metric named", "命名了指标"],
      ["evaluation signal present", "存在评估信号"],
      ["appears to emphasize single-timepoint/static analysis", "看起来强调单时间点/静态分析"],
      ["dataset/evaluation details are not explicit in metadata or abstract", "元数据或摘要中未明确数据集/评估细节"],
      ["localized findings can serve as anchors for comparing disease state across time.", "局部发现可以作为跨时间比较疾病状态的锚点。"],
      ["temporal clinical change can be captured without always requiring explicit lesion anchors.", "时序临床变化不一定总需要显式病灶锚点。"],
      ["static lesion or region grounding is a useful proxy for downstream clinical reasoning.", "静态病灶或区域 grounding 可作为下游临床推理的代理。"],
      ["report text quality is a sufficient proxy for clinically meaningful visual understanding.", "报告文本质量可作为临床视觉理解的代理。"],
      ["single-study recognition performance transfers to richer clinical reasoning workflows.", "单次检查识别能力可以迁移到更复杂的临床推理流程。"],
      ["broad medical multimodal performance transfers to the target research workflow.", "通用医学多模态能力可以迁移到目标科研工作流。"],
      ["explicit temporal/change reasoning", "显式时序/变化推理"],
      ["lesion-level localization or grounding", "病灶级定位或 grounding"],
      ["capability-specific metrics", "面向具体能力的评估指标"],
      ["explicit dataset or benchmark context", "明确的数据集或 Benchmark 上下文"],
      ["not obvious from extracted metadata", "从已抽取元数据中未发现明显缺失"],
      ["direct candidate for the target problem space", "目标问题空间的直接候选论文"],
      ["temporal candidate that needs lesion-level grounding comparison", "需要病灶级 grounding 对比的时序候选论文"],
      ["localization candidate that needs paired temporal comparison", "需要配对时序比较的定位候选论文"],
      ["evaluation context that may expose benchmark coverage gaps", "可能暴露 Benchmark 覆盖不足的评估上下文"],
      ["background or adjacent medical VLM evidence", "背景或相邻医学 VLM 证据"],
      ["The paper may support a gap around missing lesion-grounded temporal reasoning.", "该论文可能支持“缺少病灶 grounding 的时序推理”这一 Gap。"],
      ["The paper may support a gap between static localization and temporal lesion tracking.", "该论文可能支持“静态定位与时序病灶追踪之间存在断层”这一 Gap。"],
      ["The paper may support a gap between longitudinal modeling and localized lesion comparison.", "该论文可能支持“纵向建模与局部病灶比较之间存在断层”这一 Gap。"],
      ["The paper may support a gap around evaluation metrics that miss fine-grained clinical change.", "该论文可能支持“指标无法覆盖细粒度临床变化”这一 Gap。"],
      ["The paper may support a gap around benchmark comparability and dataset transparency.", "该论文可能支持“Benchmark 可比性和数据集透明度不足”这一 Gap。"],
      ["Use this paper as possible counter-evidence when testing whether the gap still holds.", "验证 Gap 是否成立时，可将该论文作为潜在反证。"],
      ["Use this paper to refine the problem-space map before claiming a gap.", "在提出 Gap 前，可用该论文修正问题空间图谱。"],
      ["temporal or change-oriented signals", "时序或变化信号"],
      ["lesion, finding, mask, or localization signals", "病灶、发现、Mask 或定位信号"],
      ["longitudinal or follow-up medical image understanding", "纵向或随访医学影像理解"],
      ["report-level clinical finding description", "报告级临床发现描述"],
      ["lesion or finding-level grounding", "病灶或发现级 grounding"],
      ["explicit dataset, metric, or evaluation framing", "明确的数据集、指标或评估框架"],
      ["single-study image understanding or medical VQA", "单次检查影像理解或医学 VQA"],
      ["broad medical multimodal capability context", "通用医学多模态能力背景"],
      ["Lesion-level temporal reasoning candidates", "病灶级时序推理候选"],
      ["Longitudinal medical imaging", "纵向医学影像"],
      ["Medical report generation", "医学报告生成"],
      ["Lesion localization / grounding", "病灶定位 / Grounding"],
      ["Benchmark / evaluation", "Benchmark / 评估"],
      ["Single-image medical VLM diagnosis / VQA", "单图医学 VLM 诊断 / VQA"],
      ["General medical VLM / foundation work", "通用医学 VLM / 基础工作"],
      ["Lesion-level temporal reasoning is weakly covered by the retrieved medical VLM literature.", "当前检索到的医学 VLM 文献对病灶级时序推理覆盖较弱。"],
      ["Evaluation datasets and benchmark protocols are often under-specified or not comparable.", "评估数据集和 Benchmark 协议经常描述不足或不可比较。"],
      ["Metric coverage appears under-specified for fine-grained clinical change analysis.", "针对细粒度临床变化分析的指标覆盖仍不充分。"],
      ["Temporal lesion change is central to follow-up diagnosis and treatment response, but many candidate papers surface as single-image diagnosis, report generation, or broad VLM work.", "病灶时序变化对随访诊断和治疗反应评估很关键，但许多候选论文仍主要落在单图诊断、报告生成或宽泛 VLM 工作上。"],
      ["If dataset and protocol details are not prominent, it is hard to verify whether a claimed capability is actually evaluated under a comparable benchmark.", "如果数据集和协议细节不突出，就很难判断论文声称的能力是否真的在可比较 Benchmark 下被验证。"],
      ["Temporal lesion analysis needs more than generic text similarity or diagnosis accuracy; it needs finding, location, direction-of-change, and consistency metrics.", "病灶时序分析不能只依赖通用文本相似度或诊断准确率，还需要发现、位置、变化方向和一致性指标。"],
      ["Build a lesion-localized temporal comparison task with paired studies and explicit change labels.", "构建一个病灶定位的配对时序比较任务，并提供明确变化标签。"],
      ["Create a benchmark table that normalizes dataset, task, metric, baseline, and temporal pairing details.", "构建统一表格，规范化数据集、任务、指标、Baseline 和时序配对细节。"],
      ["Evaluate change-label accuracy, finding/location consistency, report similarity, and mask-guided ablations.", "评估变化标签准确率、发现/位置一致性、报告相似度和 Mask 引导消融。"],
      ["candidate work does not clearly combine temporal/change reasoning with lesion-level localization", "候选工作没有清楚结合时序/变化推理与病灶级定位"],
      ["paper contains both temporal/change and lesion/localization signals", "论文同时包含时序/变化信号和病灶/定位信号"],
      ["dataset or benchmark protocol is not explicit in the extracted card", "抽取卡片中没有明确数据集或 Benchmark 协议"],
      ["paper exposes dataset and benchmark/evaluation signals", "论文暴露了数据集和 Benchmark/评估信号"],
      ["metric not explicit in the extracted card", "抽取卡片中没有明确指标"],
      ["paper exposes at least one evaluation metric", "论文至少暴露了一个评估指标"],
      ["Can lesion-localized visual anchors improve temporal change reasoning in medical VLMs?", "病灶定位视觉锚点能否提升医学 VLM 的时序变化推理？"],
      ["A model that explicitly compares T1/T2 lesion regions will make fewer finding, location, and change-direction errors than a report-only or image-level VLM baseline.", "相比只做报告或图像级判断的 VLM Baseline，显式比较 T1/T2 病灶区域的模型应当产生更少的发现、位置和变化方向错误。"],
      ["Use T1 lesion masks or predicted regions as anchors for paired-study visual comparison, then instruction-tune the model on localized temporal change prompts.", "使用 T1 病灶 Mask 或预测区域作为配对检查视觉比较的锚点，再用局部时序变化指令对模型进行微调。"],
      ["Paired T1/T2 medical images or studies with lesion/finding annotations and change labels.", "带有病灶/发现标注和变化标签的 T1/T2 配对医学图像或检查。"],
      ["Can a capability-oriented benchmark map make medical VLM claims comparable?", "面向能力的 Benchmark 图谱能否让医学 VLM 的能力声明变得可比较？"],
      ["Normalizing papers by task, data, temporal pairing, localization, metrics, and baselines will expose evaluation gaps that aggregate benchmark scores hide.", "按任务、数据、时序配对、定位、指标和 Baseline 规范化论文，可以暴露总分型 Benchmark 隐藏的评估缺口。"],
      ["Build a benchmark coverage matrix that maps each dataset and paper to explicit clinical capabilities rather than only leaderboard-style scores.", "构建 Benchmark 覆盖矩阵，把每个数据集和论文映射到明确临床能力，而不只是 leaderboard 分数。"],
      ["Metadata and full-text evidence for datasets, metrics, baselines, and task settings.", "关于数据集、指标、Baseline 和任务设置的元数据与全文证据。"],
      ["Which evaluation metrics actually measure fine-grained clinical change reasoning?", "哪些评估指标真正衡量了细粒度临床变化推理？"],
      ["Splitting evaluation into finding, location, and change-direction dimensions will reveal failures hidden by generic text similarity or aggregate accuracy.", "把评估拆成发现、位置和变化方向维度，可以暴露通用文本相似度或总体准确率隐藏的失败。"],
      ["Define a metric suite that separates semantic report quality from localized clinical change correctness.", "定义一组指标，将报告语义质量与局部临床变化正确性分开评估。"],
      ["Predictions, reference findings, locations, change labels, and optional report text.", "预测结果、参考发现、位置、变化标签，以及可选报告文本。"],
      ["public paired lesion-change data may be sparse", "公开配对病灶变化数据可能稀缺"],
      ["mask quality may dominate measured gains", "Mask 质量可能主导观测到的收益"],
      ["report-derived change labels may contain clinical noise", "从报告中抽取的变化标签可能包含临床噪声"],
      ["paper-level score table", "论文级分数表"],
      ["single benchmark leaderboard", "单一 Benchmark 排行榜"],
      ["manual systematic-review spreadsheet", "人工系统综述表格"],
      ["metadata-only extraction", "仅元数据抽取"],
      ["full-text extraction", "全文抽取"],
      ["without source coverage gate", "不使用信息源覆盖门控"],
      ["with source coverage gate", "使用信息源覆盖门控"],
      ["papers may omit benchmark details from accessible text", "论文可能在可访问文本中省略 Benchmark 细节"],
      ["dataset names may be ambiguous", "数据集名称可能有歧义"],
      ["benchmark dimensions require expert validation", "Benchmark 维度需要专家验证"],
      ["BLEU/ROUGE/BERTScore-only report evaluation", "仅 BLEU/ROUGE/BERTScore 的报告评估"],
      ["diagnosis accuracy-only evaluation", "仅诊断准确率评估"],
      ["human adjudication sample", "人工裁决样本"],
      ["without location metric", "不使用位置指标"],
      ["without change-direction metric", "不使用变化方向指标"],
      ["without finding consistency metric", "不使用发现一致性指标"],
      ["metric definitions may need clinician review", "指标定义可能需要临床医生审阅"],
      ["automated clinical consistency labels may be noisy", "自动临床一致性标签可能有噪声"],
      ["Which paper group provides the strongest counter-evidence, and does it fully address the target workflow?", "哪一组论文提供了最强反证？它是否完整覆盖目标工作流？"],
      ["Which missing dimension can be turned into a clean benchmark or ablation?", "哪个缺失维度可以转化为清晰的 Benchmark 或消融实验？"],
      ["Are existing metrics measuring the target ability or only a nearby proxy?", "现有指标是在衡量目标能力，还是只衡量了相邻代理任务？"],
      ["change label accuracy", "变化标签准确率"],
      ["finding consistency", "发现一致性"],
      ["location consistency", "位置一致性"],
      ["report similarity as an auxiliary metric", "报告相似度作为辅助指标"],
      ["failure taxonomy for missed, hallucinated, and wrong-direction changes", "漏检、幻觉和变化方向错误的失败类型分析"],
      ["dataset coverage table", "数据集覆盖表"],
      ["benchmark dimension checklist", "Benchmark 维度清单"],
      ["baseline comparability audit", "Baseline 可比性审计"],
      ["paired-study availability check", "配对检查数据可用性检查"],
      ["generic metric vs clinical-consistency metric comparison", "通用指标与临床一致性指标对比"],
      ["finding/location/change-direction metric split", "发现/位置/变化方向指标拆分"],
      ["case-level failure analysis", "病例级失败分析"],
      ["single-study medical VLM", "单次检查医学 VLM"],
      ["report-generation model without visual localization", "无视觉定位的报告生成模型"],
      ["paired-image VLM without mask guidance", "无 Mask 引导的配对图像 VLM"],
      ["text-only report comparison baseline", "纯文本报告比较 Baseline"],
      ["no mask", "无 Mask"],
      ["T1 mask guidance", "T1 Mask 引导"],
      ["predicted mask guidance", "预测 Mask 引导"],
      ["T2 mask upper bound", "T2 Mask 上界"],
      ["abstract_only", "仅摘要"],
      ["full_text_read", "已读全文"],
      ["temporal_or_change", "时序/变化"],
      ["lesion_or_localization", "病灶/定位"],
      ["benchmark_or_evaluation", "Benchmark/评估"],
      ["dataset_explicit", "数据集明确"],
      ["dataset_missing", "数据集缺失"],
      ["metric_explicit", "指标明确"],
      ["metric_missing", "指标缺失"],
      ["llm_extracted", "LLM 抽取"],
      ["coverage gap", "覆盖不足"],
      ["benchmark gap", "Benchmark 不足"],
      ["metric gap", "指标不足"],
      ["assumption gap", "假设不足"],
      ["contradiction gap", "结论冲突"],
      ["failure-analysis gap", "失败分析不足"],
      ["real-world-transfer gap", "真实场景迁移不足"],
    ]);

    const zh = (value) => {
      let text = String(value ?? "");
      if (!text) return "";
      if (translations.has(text)) return translations.get(text);
      let match = text.match(/^Audit whether (.*) is truly evaluated under the target clinical workflow\\.$/);
      if (match) return `审查“${zh(match[1])}”是否真的在目标临床工作流中被评估。`;
      match = text.match(/^Does (.*) cover the target workflow, or only an adjacent proxy\\?$/);
      if (match) return `“${zh(match[1])}”覆盖的是目标工作流，还是只是相邻代理任务？`;
      match = text.match(/^Can we validate this hint: (.*)$/);
      if (match) return `能否验证这个提示：${zh(match[1])}`;
      match = text.match(/^Is this weakness real after counter-evidence resolution: (.*)$/);
      if (match) return `在处理反证后，这个弱点是否仍然成立：${zh(match[1])}`;
      match = text.match(/^dataset: (.*)$/);
      if (match) return `数据集：${zh(match[1])}`;
      match = text.match(/^metrics: (.*)$/);
      if (match) return `指标：${zh(match[1])}`;
      text = text.replace(/ranked_papers=([0-9]+) meets minimum ([0-9]+)/g, "入选论文数=$1，达到最低要求 $2");
      text = text.replace(/ranked_papers=([0-9]+) below minimum ([0-9]+)/g, "入选论文数=$1，低于最低要求 $2");
      text = text.replace(/contributing_sources=([0-9]+) meets minimum ([0-9]+)/g, "贡献来源数=$1，达到最低要求 $2");
      text = text.replace(/contributing_sources=([0-9]+) below minimum ([0-9]+)/g, "贡献来源数=$1，低于最低要求 $2");
      text = text.replace(/moc_groups=([0-9]+) meets minimum ([0-9]+)/g, "MOC 分组数=$1，达到最低要求 $2");
      text = text.replace(/moc_groups=([0-9]+) below minimum ([0-9]+)/g, "MOC 分组数=$1，低于最低要求 $2");
      text = text.replace(/failed_or_empty_sources=/g, "失败或空结果来源=");
      text = text.replace(/([0-9]+)[/]([0-9]+) papers support or expose this weakness/g, "$1/$2 篇论文支持或暴露该弱点");
      text = text.replace(/([0-9]+)[/]([0-9]+) papers provide counter-evidence/g, "$1/$2 篇论文提供反证");
      text = text.replace("evidence is mostly abstract/metadata-level", "证据主要来自摘要/元数据层面");
      return text;
    };

    const join = (values, fallback = "未明确") => {
      if (!Array.isArray(values) || values.length === 0) return fallback;
      return values.filter(Boolean).map(value => esc(zh(value))).join("; ");
    };

    const statusLabel = (value) => {
      const text = String(value || "");
      const map = {
        ready_for_preliminary_gap_analysis: "可进入初步 Gap 分析",
        needs_more_evidence: "证据不足，需继续检索",
        not_evaluated: "未评估",
        ok: "成功",
        ready: "已生成",
        draft: "草稿",
        failed: "失败",
        skipped: "已跳过",
        no_update: "无更新",
        not_attempted: "未执行",
      };
      return map[text] || text || "未评估";
    };

    const judgmentSource = () => {
      const mode = String(data.synthesis?.mode || "");
      const reviewed = mode.includes("codex_manual") || mode.includes("codex_review");
      if (reviewed) {
        return {
          label: "Codex-reviewed",
          badge: "teal",
          mode,
          note: "已通过 Codex Review 写回 MOC、Gap 和研究机会",
        };
      }
      return {
        label: "Rule-generated",
        badge: "amber",
        mode: mode || "rule_generated",
        note: "当前为规则生成或自动综合，尚未执行 Codex Review",
      };
    };

    const roleLabel = (value) => {
      const map = { support: "支持", counter: "反证", unclear: "不明确" };
      return map[value] || value || "不明确";
    };

    const tierMeta = (value) => {
      const map = {
        core: {
          label: "核心证据",
          badge: "teal",
          note: "可进入目标领域 Gap 证据链的主要论文",
        },
        adjacent: {
          label: "相邻证据",
          badge: "amber",
          note: "与目标方向相关，但更适合作为背景或旁证",
        },
        noise: {
          label: "噪声/需降权",
          badge: "red",
          note: "表面相关但不应支撑核心 Gap 判断",
        },
        unknown: {
          label: "未判定",
          badge: "gray",
          note: "没有命中当前 profile 的证据层级规则",
        },
      };
      return map[String(value || "unknown")] || map.unknown;
    };

    const tierReason = (reason) => {
      let text = String(reason || "");
      text = text.replace(/^evidence_tier=core$/, "证据层级：核心证据");
      text = text.replace(/^evidence_tier=adjacent$/, "证据层级：相邻证据");
      text = text.replace(/^evidence_tier=noise$/, "证据层级：噪声/需降权");
      text = text.replace(/^evidence_tier=unknown$/, "证据层级：未判定");
      text = text.replace(/^matched core keyword: (.*)$/i, "命中核心关键词：$1");
      text = text.replace(/^matched adjacent keyword: (.*)$/i, "命中相邻关键词：$1");
      text = text.replace(/^matched negative keyword: (.*)$/i, "命中负面/噪声关键词：$1");
      text = text.replace(/^source_policy=preferred:(.*)$/i, "信息源策略：优先来源 $1");
      text = text.replace(/^source_policy=neutral:(.*)$/i, "信息源策略：中性来源 $1");
      text = text.replace(/^source_policy=downrank:(.*)$/i, "信息源策略：降权来源 $1");
      text = text.replace(/^source_policy=disabled:(.*)$/i, "信息源策略：禁用来源 $1");
      text = text.replace(
        "no profile evidence keyword or source policy matched",
        "未命中 profile 证据关键词或信息源策略"
      );
      return zh(text);
    };

    const joinReasons = (values, fallback = "未记录") => {
      if (!Array.isArray(values) || values.length === 0) return fallback;
      return values.filter(Boolean).map(value => esc(tierReason(value))).join("; ");
    };

    const evidenceTierStats = () => {
      const stats = { core: 0, adjacent: 0, noise: 0, unknown: 0 };
      for (const paper of data.paper_cards || []) {
        const tier = String(paper.evidence_tier || "unknown");
        stats[tier] = (stats[tier] || 0) + 1;
      }
      return stats;
    };

    const tierBadge = (tier) => {
      const meta = tierMeta(tier);
      return `<span class="badge ${meta.badge}">${esc(meta.label)}</span>`;
    };

    const formatDelta = (value) => {
      const number = Number(value || 0);
      const sign = number > 0 ? "+" : "";
      return `${sign}${number.toFixed(2)}`;
    };

    const cleanTitle = (value, limit = 96) => {
      const text = String(value || "");
      return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
    };

    const papersByTier = (tier, limit = 5) => (data.paper_cards || [])
      .filter(paper => String(paper.evidence_tier || "unknown") === tier)
      .slice(0, limit);

    const paperList = (papers, fallback) => {
      if (!papers.length) return `<p class="subtle">${esc(fallback)}</p>`;
      return `
        <ol class="paper-list">
          ${papers.map(paper => `
            <li>
              <strong>${esc(cleanTitle(paper.title, 80))}</strong><br>
              <span class="subtle">${tierBadge(paper.evidence_tier)} 排序影响 ${esc(formatDelta(paper.evidence_tier_score_delta))}</span>
            </li>
          `).join("")}
        </ol>
      `;
    };

    const synthesizedGaps = () => {
      const reviewed = data.synthesis?.gap_summaries || [];
      if (reviewed.length) {
        return reviewed.map(gap => ({
          gap: gap.gap,
          confidence: gap.confidence,
          judgment: gap.judgment,
          support: gap.support,
          counter: gap.counter_evidence,
          source: "synthesis",
        }));
      }
      return (data.gaps || []).map(gap => ({
        gap: gap.gap,
        confidence: gap.confidence,
        judgment: gap.why_it_matters,
        support: `${gap.support_count || 0}/${gap.total_papers || 0} 篇支持或暴露该弱点`,
        counter: `${gap.counter_count || 0}/${gap.total_papers || 0} 篇提供反证`,
        source: "rule",
      }));
    };

    const gapStrength = (gap) => {
      const confidence = Number(gap.confidence || 0);
      const counterText = String(gap.counter || "");
      if (counterText.includes("暂无明确反证") || confidence >= 0.6) {
        return { label: "优先验证", badge: "teal" };
      }
      if (confidence >= 0.4) return { label: "候选 Gap", badge: "amber" };
      return { label: "证据偏弱", badge: "red" };
    };

    const bestOpportunity = () => {
      const items = data.research_opportunities || [];
      return items.find(item => !String(item.gap || "").toLowerCase().includes("autoresearch")) || items[0] || {};
    };

    const mainClaim = () => {
      const summary = String(data.synthesis?.executive_summary || "");
      if (summary) return summary;
      const gaps = synthesizedGaps();
      if (gaps[0]) return `当前最值得检查的研究缺口是：${gaps[0].gap}`;
      return "当前还没有形成稳定主线，需要先补充核心论文和证据分层。";
    };

    const renderMainline = () => {
      const source = judgmentSource();
      const tiers = evidenceTierStats();
      const gaps = synthesizedGaps();
      const primaryGap = gaps.find(gap => !String(gap.gap || "").includes("System Gap")) || gaps[0] || {};
      const opportunity = bestOpportunity();
      const mocGroups = data.topic_moc?.problem_spaces || [];
      const firstMoc = mocGroups[0] || {};
      const corePapers = papersByTier("core", 5);
      const adjacentPapers = papersByTier("adjacent", 4);
      const noisePapers = papersByTier("noise", 4);
      const gapRows = gaps.slice(0, 5).map((gap, idx) => {
        const strength = gapStrength(gap);
        return `
          <tr>
            <td>${idx + 1}</td>
            <td>${esc(zh(gap.gap))}</td>
            <td><span class="badge ${strength.badge}">${esc(strength.label)}</span></td>
            <td>${esc(gap.confidence ?? "n/a")}</td>
            <td>${esc(gap.support || "未记录")}</td>
            <td>${esc(gap.counter || "未记录")}</td>
          </tr>
        `;
      }).join("");

      document.getElementById("mainline").innerHTML = `
        <div class="mainline-layout">
          <section>
            <article class="card verdict">
              <div class="card-header">
                <div>
                  <h2>核心结论</h2>
                  <p class="subtle">先看这个，再看论文卡片和 Gap 细节。</p>
                </div>
                <span class="badge ${source.badge}">${esc(source.label)}</span>
              </div>
              <p>${esc(mainClaim())}</p>
              <dl class="kv">
                <dt>当前领域</dt><dd>${esc(data.domain_profile?.domain_name || data.topic || "未配置")}</dd>
                <dt>证据分层</dt><dd>核心 ${tiers.core || 0}；相邻 ${tiers.adjacent || 0}；噪声 ${tiers.noise || 0}；未判定 ${tiers.unknown || 0}</dd>
                <dt>最该检查的 Gap</dt><dd>${esc(zh(primaryGap.gap || "未形成稳定 Gap"))}</dd>
                <dt>为什么不是最终结论</dt><dd>${esc(data.synthesis?.evidence_quality || "当前判断仍需要全文实验设置、指标定义和反证审查。")}</dd>
              </dl>
            </article>

            <h2 style="margin-top:16px;">从论文到 Gap 的链条</h2>
            <div class="logic-chain">
              <article class="chain-step">
                <span class="step-index">1</span>
                <h3>输入领域</h3>
                <p class="subtle">${esc(data.topic || "未记录")}</p>
              </article>
              <article class="chain-step">
                <span class="step-index">2</span>
                <h3>核心证据池</h3>
                <p class="subtle">先把真正属于目标领域的论文和旁证/噪声分开。</p>
                <div class="badge-row">${tierBadge("core")}<span class="badge">${tiers.core || 0} 篇</span></div>
              </article>
              <article class="chain-step">
                <span class="step-index">3</span>
                <h3>MOC 对比</h3>
                <p class="subtle">${esc(zh(firstMoc.name || "问题空间尚未拆细"))}</p>
              </article>
              <article class="chain-step">
                <span class="step-index">4</span>
                <h3>Weakness</h3>
                <p class="subtle">${esc(zh(primaryGap.gap || "暂无"))}</p>
              </article>
              <article class="chain-step">
                <span class="step-index">5</span>
                <h3>反证处理</h3>
                <p class="subtle">${esc(primaryGap.counter || "需要检查是否已有论文解决该问题。")}</p>
              </article>
              <article class="chain-step">
                <span class="step-index">6</span>
                <h3>可做项目</h3>
                <p class="subtle">${esc(opportunity.research_question || "等待 Gap 收敛后生成研究问题。")}</p>
              </article>
            </div>

            <h2 style="margin-top:16px;">Gap 优先级</h2>
            <table>
              <thead><tr><th>#</th><th>Gap / Weakness</th><th>状态</th><th>置信度</th><th>支持</th><th>反证</th></tr></thead>
              <tbody>${gapRows || `<tr><td colspan="6">暂无 Gap。</td></tr>`}</tbody>
            </table>
          </section>

          <aside>
            <article class="card">
              <h2>推荐切入点</h2>
              <dl class="kv">
                <dt>研究问题</dt><dd>${esc(opportunity.research_question || "暂无")}</dd>
                <dt>方法设想</dt><dd>${esc(opportunity.proposed_method || "暂无")}</dd>
                <dt>评估方案</dt><dd>${join(opportunity.evaluation_protocol || [])}</dd>
                <dt>消融/对比</dt><dd>${join([...(opportunity.baselines || []), ...(opportunity.ablations || [])], "暂无")}</dd>
              </dl>
            </article>
            <article class="card" style="margin-top:12px;">
              <h2>页面阅读顺序</h2>
              <ol class="evidence-list">
                <li>先看本页的核心结论和 Gap 优先级。</li>
                <li>再去“论文”页检查每篇论文的证据层级和原因。</li>
                <li>去“MOC”页看论文被放进哪个问题空间。</li>
                <li>最后看“Gap”和“机会”页，追踪证据链和项目设计。</li>
              </ol>
            </article>
          </aside>
        </div>

        <h2 style="margin-top:16px;">证据分层板</h2>
        <div class="evidence-columns">
          <section class="evidence-column">
            <h3>核心证据</h3>
            <p class="subtle">主要用于支撑目标领域 Gap。</p>
            ${paperList(corePapers, "暂无核心证据。")}
          </section>
          <section class="evidence-column">
            <h3>相邻证据</h3>
            <p class="subtle">可以提供背景，但不能直接当作核心支撑。</p>
            ${paperList(adjacentPapers, "暂无相邻证据。")}
          </section>
          <section class="evidence-column">
            <h3>噪声/需降权</h3>
            <p class="subtle">容易污染 Gap 判断，应谨慎使用。</p>
            ${paperList(noisePapers, "暂无明显噪声论文。")}
          </section>
        </div>
      `;
    };

    const translatedLlmError = (error) => {
      const text = String(error || "");
      if (!text) return "";
      if (text.includes("429")) return "接口返回 429 Too Many Requests：当前 Key 可能被限流或额度不足，稍后重试或更换可用模型/Key。";
      if (text.includes("AUTORESEARCH_LLM_MODEL")) return "未配置模型名，请设置 AUTORESEARCH_LLM_MODEL 或传入 --llm-model。";
      if (text.includes("AUTORESEARCH_LLM_API_KEY") || text.includes("OPENAI_API_KEY")) return "未配置 API Key，请设置 AUTORESEARCH_LLM_API_KEY 或 OPENAI_API_KEY。";
      return text.split("\\n")[0];
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
      const source = judgmentSource();
      const tiers = evidenceTierStats();
      document.getElementById("topic").textContent = data.topic || "研究主题";
      document.getElementById("generatedAt").textContent = `生成时间：${data.generated_at || "未知"}`;
      document.getElementById("summaryGrid").innerHTML = [
        metric("就绪状态", statusLabel(readiness.status), `${readiness.ranked_papers || 0} 篇入选论文`),
        metric("论文", data.paper_cards?.length || 0, "结构化论文卡片"),
        metric("核心证据", tiers.core || 0, `相邻 ${tiers.adjacent || 0}；噪声 ${tiers.noise || 0}`),
        metric("MOC 空间", mocCount, "问题空间分组"),
        metric("Gap", data.gaps?.length || 0, "带证据的判断"),
        metric("研究机会", data.research_opportunities?.length || 0, "候选项目方向"),
        metric("综合分析", statusLabel(data.synthesis?.status), "Codex 代替 LLM 生成"),
        metric("判断来源", source.label, source.note),
      ].join("");
    };

    const renderProfileStrip = () => {
      const profile = data.domain_profile || {};
      const capabilities = (profile.capability_dimensions || []).map(item => item.name);
      const concepts = profile.core_concepts || [];
      const lenses = profile.gap_lenses || [];
      const source = judgmentSource();
      document.getElementById("profileStrip").innerHTML = `
        <div>
          <strong>当前领域 Profile：${esc(profile.domain_name || "未配置")}</strong>
          <span class="badge ${source.badge}">当前判断来源：${esc(source.label)}</span>
          <span class="subtle">核心概念：${join(concepts.slice(0, 8), "未配置")}；能力维度：${join(capabilities.slice(0, 5), "未配置")}</span>
          <span class="subtle">Gap 视角：${join(lenses.slice(0, 6), "未配置")}</span>
        </div>
        <button class="link-button" data-tab-go="overview" type="button">查看领域配置</button>
      `;
    };

    const renderLlmStrip = () => {
      const records = data.llm_extractions || [];
      const counts = records.reduce((acc, row) => {
        acc[row.status || "unknown"] = (acc[row.status || "unknown"] || 0) + 1;
        return acc;
      }, {});
      const updatedFields = [...new Set(records.flatMap(row => row.fields_updated || []))];
      const models = [...new Set(records.map(row => row.model).filter(Boolean))];
      const stripState = !records.length ? "warn" : counts.failed ? "bad" : counts.skipped ? "warn" : "ok";
      const statusText = records.length
        ? `已尝试 ${records.length} 篇：成功 ${counts.ok || 0}，无更新 ${counts.no_update || 0}，跳过 ${counts.skipped || 0}，失败 ${counts.failed || 0}`
        : "本次未执行 LLM 抽取";
      const details = records.length
        ? `模型：${models.length ? models.join(", ") : "未记录"}；更新字段：${updatedFields.length ? updatedFields.join(", ") : "无"}`
        : "可以通过 --llm-card-limit 开启；缺少模型或 Key 时会在这里显示原因。";
      const firstError = translatedLlmError(records.find(row => row.error)?.error);
      const container = document.getElementById("llmStrip");
      container.className = `llm-strip ${stripState}`;
      container.innerHTML = `
        <div>
          <strong>LLM 抽取概况：${esc(statusText)}</strong>
          <span class="subtle">${esc(details)}${firstError ? `；失败原因：${esc(firstError)}` : ""}</span>
        </div>
        <button class="link-button" data-tab-go="overview" type="button">查看抽取明细</button>
      `;
    };

    const renderOverview = () => {
      const readiness = data.source_readiness || {};
      const tiers = evidenceTierStats();
      const tierRows = ["core", "adjacent", "noise", "unknown"].map(tier => {
        const meta = tierMeta(tier);
        return `
          <tr>
            <td><span class="badge ${meta.badge}">${esc(meta.label)}</span></td>
            <td>${tiers[tier] || 0}</td>
            <td>${esc(meta.note)}</td>
          </tr>
        `;
      }).join("");
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
          <td><span class="badge ${badgeClass(row.status)}">${esc(statusLabel(row.status))}</span></td>
          <td>${esc(row.model || "n/a")}</td>
          <td>${join(row.fields_updated, "无")}</td>
          <td>${esc(translatedLlmError(row.error) || "无")}</td>
        </tr>
      `).join("");
      document.getElementById("overview").innerHTML = `
        <div class="grid-2">
          <section>
            <h2>信息源健康度</h2>
            <table>
              <thead>
                <tr>
                  <th>来源</th><th>查询数</th><th>成功</th><th>失败</th>
                  <th>跳过</th><th>原始结果</th><th>入选贡献</th>
                </tr>
              </thead>
              <tbody>${sourceRows}</tbody>
            </table>
          </section>
          <section>
            <h2>证据就绪判断</h2>
            <article class="card">
              <div class="card-header">
                <h3>${esc(statusLabel(readiness.status))}</h3>
                <span class="badge ${badgeClass(readiness.status)}">${esc(statusLabel(readiness.status))}</span>
              </div>
              <dl class="kv">
                <dt>入选论文数</dt><dd>${esc(readiness.ranked_papers || 0)}</dd>
                <dt>贡献来源数</dt><dd>${esc(readiness.contributing_sources || 0)}</dd>
                <dt>MOC 分组数</dt><dd>${esc(readiness.moc_groups || 0)}</dd>
                <dt>判断依据</dt><dd>${join(readiness.reasons || [])}</dd>
              </dl>
            </article>
            <h2 style="margin-top:16px;">证据层级分布</h2>
            <table>
              <thead>
                <tr><th>层级</th><th>论文数</th><th>含义</th></tr>
              </thead>
              <tbody>${tierRows}</tbody>
            </table>
            <h2 style="margin-top:16px;">领域配置</h2>
            <article class="card">
              <dl class="kv">
                <dt>领域</dt><dd>${esc(data.domain_profile?.domain_name || "未配置")}</dd>
                <dt>Profile ID</dt><dd>${esc(data.domain_profile?.domain_id || "n/a")}</dd>
                <dt>核心概念</dt><dd>${join(data.domain_profile?.core_concepts || [])}</dd>
                <dt>能力维度</dt><dd>${join((data.domain_profile?.capability_dimensions || []).map(item => item.name))}</dd>
                <dt>Benchmark 关键词</dt><dd>${join(data.domain_profile?.benchmark_keywords || [])}</dd>
                <dt>Metric 关键词</dt><dd>${join(data.domain_profile?.metric_keywords || [])}</dd>
                <dt>Gap 视角</dt><dd>${join(data.domain_profile?.gap_lenses || [])}</dd>
              </dl>
            </article>
            <h2 style="margin-top:16px;">LLM 抽取状态</h2>
            ${llmRows ? `<table><thead><tr><th>论文</th><th>状态</th><th>模型</th><th>更新字段</th><th>错误/提示</th></tr></thead><tbody>${llmRows}</tbody></table>` : `<div class="empty">本次未执行 LLM 抽取。</div>`}
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
      const cards = papers.map((paper, idx) => {
        const meta = tierMeta(paper.evidence_tier);
        const tierReasons = paper.evidence_tier_reasons || [];
        const coverageBadges = (paper.coverage_tags || [])
          .slice(0, 6)
          .map(tag => `<span class="badge">${esc(zh(tag))}</span>`)
          .join("");
        return `
          <details class="card fold-card">
            <summary class="fold-summary">
              <div>
                <h3>${idx + 1}. ${esc(paper.title)}</h3>
                <p class="subtle">${esc(zh(paper.problem || paper.task || "未明确"))}</p>
                <div class="badge-row">
                  ${tierBadge(paper.evidence_tier)}
                  <span class="badge ${meta.badge}">排序影响 ${esc(formatDelta(paper.evidence_tier_score_delta))}</span>
                  ${coverageBadges}
                </div>
                <div class="tier-note">${esc(meta.note)}</div>
              </div>
            </summary>
            <div class="fold-content">
            <div class="card-header">
              <p class="subtle">${esc(paper.year || "n.d.")} ${paper.venue ? `| ${esc(paper.venue)}` : ""}</p>
              ${paper.url ? `<a class="link-button" href="${esc(paper.url)}">打开原文</a>` : ""}
            </div>
            <dl class="kv">
              <dt>证据层级</dt><dd>${tierBadge(paper.evidence_tier)} <span class="subtle">排序影响 ${esc(formatDelta(paper.evidence_tier_score_delta))}</span></dd>
              <dt>层级原因</dt><dd>${joinReasons(tierReasons)}</dd>
              <dt>问题空间</dt><dd>${esc(zh(paper.problem))}</dd>
              <dt>任务</dt><dd>${esc(zh(paper.task))}</dd>
              <dt>方法族</dt><dd>${esc(zh(paper.method_family))}</dd>
              <dt>核心假设</dt><dd>${esc(zh(paper.core_assumption))}</dd>
              <dt>缺失能力</dt><dd>${esc(zh(paper.missing_capability))}</dd>
              <dt>Gap 提示</dt><dd>${esc(zh(paper.gap_hint))}</dd>
              <dt>数据集</dt><dd>${esc(zh(paper.dataset))}</dd>
              <dt>指标</dt><dd>${esc(zh(paper.metrics))}</dd>
            </dl>
            <details>
              <summary>证据片段</summary>
              <ol class="evidence-list">
                ${(paper.evidence_snippets || []).map(snippet => `<li><strong>${esc(snippet.claim)}</strong><br>${esc(snippet.snippet)}</li>`).join("") || "<li>暂无证据片段。</li>"}
              </ol>
            </details>
            </div>
          </details>
        `;
      }).join("");
      document.getElementById("papers").innerHTML = `
        <div class="toolbar">
          <div>
            <h2>论文卡片</h2>
            <p class="subtle">当前显示 ${papers.length} / ${(data.paper_cards || []).length} 篇</p>
          </div>
          <input class="search" id="paperSearch" placeholder="按问题、方法、Gap 提示或标题筛选" value="${esc(state.paperFilter)}">
        </div>
        ${cards || `<div class="empty">没有匹配当前筛选条件的论文卡片。</div>`}
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
            <h2>问题空间 MOC</h2>
            <p class="subtle">基于论文关系构建的 ${groups.length} 个问题空间</p>
          </div>
        </div>
        <div class="grid-2">
          ${groups.map(group => `
            <details class="card fold-card">
              <summary class="fold-summary">
                <div>
                  <h3>${esc(zh(group.name))}</h3>
                  <p class="subtle">${esc(zh(group.problem_space))}</p>
                </div>
              </summary>
              <div class="fold-content">
              <div class="card-header">
                <h3>${esc(zh(group.name))}</h3>
                <span class="badge teal">${esc(zh(group.problem_space))}</span>
              </div>
              <dl class="kv">
                <dt>代表论文</dt><dd>${join(group.representative_papers)}</dd>
                <dt>共同假设</dt><dd>${join(group.shared_assumptions)}</dd>
                <dt>方法族</dt><dd>${join(group.method_families)}</dd>
                <dt>缺失能力</dt><dd>${join(group.missing_capabilities)}</dd>
                <dt>开放问题</dt><dd>${join(group.open_questions)}</dd>
                <dt>可做实验</dt><dd>${join(group.possible_experiments)}</dd>
              </dl>
              </div>
            </details>
          `).join("") || `<div class="empty">本次未生成 MOC 问题空间。</div>`}
        </div>
      `;
    };

    const renderGaps = () => {
      const gaps = data.gaps || [];
      document.getElementById("gaps").innerHTML = `
        <div class="toolbar">
          <div>
            <h2>Gap 证据链</h2>
            <p class="subtle">把支持证据、反证和验证计划放在一起看。</p>
          </div>
        </div>
        ${gaps.map((gap, idx) => `
          <details class="card fold-card" ${idx === 0 ? "open" : ""}>
            <summary class="fold-summary">
              <div>
                <h3>Gap ${idx + 1}: ${esc(zh(gap.gap))}</h3>
                <p class="subtle">支持 ${gap.support_count}/${gap.total_papers}；反证 ${gap.counter_count}/${gap.total_papers}；置信度 ${esc(gap.confidence)}</p>
              </div>
            </summary>
            <div class="fold-content">
            <div class="card-header">
              <div>
                <h3>Gap ${idx + 1}: ${esc(zh(gap.gap))}</h3>
                <p class="subtle">${esc(zh(gap.why_it_matters))}</p>
              </div>
              <span class="badge ${badgeClass(gap.confidence >= 0.6 ? "ready" : "warn")}">置信度 ${esc(gap.confidence)}</span>
            </div>
            <div class="confidence"><span style="width:${Math.round((gap.confidence || 0) * 100)}%"></span></div>
            <dl class="kv">
              <dt>证据覆盖</dt><dd>支持 ${gap.support_count}/${gap.total_papers}; 反证 ${gap.counter_count}/${gap.total_papers}; 不明确 ${gap.unclear_count}</dd>
              <dt>研究机会</dt><dd>${esc(zh(gap.research_opportunity))}</dd>
              <dt>评分依据</dt><dd>${join(gap.score_reasons)}</dd>
            </dl>
            <details open>
              <summary>证据链</summary>
              <ol class="evidence-list">
                ${(gap.evidence_chain || []).map(step => `
                  <li>
                    <strong>${esc(step.paper_title)}</strong>
                    <span class="badge ${badgeClass(step.role === "counter" ? "no" : "yes")}">${esc(roleLabel(step.role))}</span>
                    <br>${esc(zh(step.claim))}
                    ${step.missing_dimensions?.length ? `<br><span class="subtle">缺失维度：${join(step.missing_dimensions)}</span>` : ""}
                  </li>
                `).join("") || "<li>暂无证据链。</li>"}
              </ol>
            </details>
            </div>
          </details>
        `).join("") || `<div class="empty">本次未生成 Gap。</div>`}
      `;
    };

    const renderOpportunities = () => {
      const opportunities = data.research_opportunities || [];
      document.getElementById("opportunities").innerHTML = `
        <div class="toolbar">
          <div>
            <h2>研究机会</h2>
            <p class="subtle">每个想法都绑定到前面的 Gap 证据链。</p>
          </div>
        </div>
        <div class="grid-2">
          ${opportunities.map((item, idx) => `
            <details class="card fold-card" ${idx === 0 ? "open" : ""}>
              <summary class="fold-summary">
                <div>
                  <h3>机会 ${idx + 1}</h3>
                  <p class="subtle">${esc(zh(item.research_question || item.gap))}</p>
                </div>
              </summary>
              <div class="fold-content">
              <div class="card-header">
                <h3>机会 ${idx + 1}</h3>
                <span class="badge teal">证据支撑</span>
              </div>
              <dl class="kv">
                <dt>绑定 Gap</dt><dd>${esc(zh(item.gap))}</dd>
                <dt>研究问题</dt><dd>${esc(zh(item.research_question))}</dd>
                <dt>假设</dt><dd>${esc(zh(item.hypothesis))}</dd>
                <dt>方法设想</dt><dd>${esc(zh(item.proposed_method))}</dd>
                <dt>所需数据</dt><dd>${esc(zh(item.required_data))}</dd>
                <dt>评估方案</dt><dd>${join(item.evaluation_protocol)}</dd>
                <dt>对比基线</dt><dd>${join(item.baselines)}</dd>
                <dt>消融实验</dt><dd>${join(item.ablations)}</dd>
                <dt>风险</dt><dd>${join(item.risks)}</dd>
                <dt>证据引用</dt><dd>${join(item.evidence_refs)}</dd>
              </dl>
              </div>
            </details>
          `).join("") || `<div class="empty">本次未生成有证据支撑的研究机会。</div>`}
        </div>
      `;
    };

    const renderSynthesis = () => {
      const synthesis = data.synthesis || null;
      if (!synthesis) {
        document.getElementById("synthesis").innerHTML = `
          <div class="empty">本次还没有生成综合分析。可以运行 autoresearch synthesize <output-dir> 生成。</div>
        `;
        return;
      }
      const source = judgmentSource();
      document.getElementById("synthesis").innerHTML = `
        <div class="toolbar">
          <div>
            <h2>综合分析</h2>
            <p class="subtle">当前判断来源：${esc(source.label)}；${esc(source.note)}</p>
          </div>
          <a class="link-button" href="analysis_report.md">查看分析报告</a>
        </div>
        <article class="card">
          <div class="card-header">
            <h3>总体判断</h3>
            <span class="badge ${badgeClass(synthesis.status)}">${esc(statusLabel(synthesis.status))}</span>
          </div>
          <p>${esc(synthesis.executive_summary)}</p>
          <dl class="kv">
            <dt>判断来源</dt><dd>${esc(source.label)}（${esc(source.mode)}）</dd>
            <dt>领域理解</dt><dd>${esc(synthesis.domain_interpretation)}</dd>
            <dt>信息源判断</dt><dd>${esc(synthesis.search_assessment)}</dd>
            <dt>证据质量</dt><dd>${esc(synthesis.evidence_quality)}</dd>
          </dl>
        </article>
        <div class="grid-2" style="margin-top:14px;">
          <section>
            <h2>MOC 结论</h2>
            ${(synthesis.moc_takeaways || []).map((item, idx) => `
              <article class="card">
                <h3>${idx + 1}. MOC Takeaway</h3>
                <p>${esc(item)}</p>
              </article>
            `).join("") || `<div class="empty">暂无 MOC 结论。</div>`}
          </section>
          <section>
            <h2>下一步</h2>
            <article class="card">
              <ol class="evidence-list">
                ${(synthesis.next_steps || []).map(item => `<li>${esc(item)}</li>`).join("") || "<li>暂无下一步建议。</li>"}
              </ol>
            </article>
            <h2 style="margin-top:16px;">当前限制</h2>
            <article class="card">
              <ol class="evidence-list">
                ${(synthesis.limitations || []).map(item => `<li>${esc(item)}</li>`).join("") || "<li>暂无明确限制。</li>"}
              </ol>
            </article>
          </section>
        </div>
        <h2 style="margin-top:16px;">Gap 判断</h2>
        ${(synthesis.gap_summaries || []).map((gap, idx) => `
          <details class="card fold-card" ${idx === 0 ? "open" : ""}>
            <summary class="fold-summary">
              <div>
                <h3>Gap ${idx + 1}: ${esc(zh(gap.gap))}</h3>
                <p class="subtle">置信度 ${esc(gap.confidence)}；${esc(gap.judgment)}</p>
              </div>
            </summary>
            <div class="fold-content">
              <dl class="kv">
                <dt>判断</dt><dd>${esc(gap.judgment)}</dd>
                <dt>支持证据</dt><dd>${esc(gap.support)}</dd>
                <dt>反证</dt><dd>${esc(gap.counter_evidence)}</dd>
                <dt>证据引用</dt><dd>${join(gap.evidence_refs)}</dd>
              </dl>
            </div>
          </details>
        `).join("") || `<div class="empty">暂无 Gap 判断。</div>`}
        <h2 style="margin-top:16px;">研究机会</h2>
        <article class="card">
          <ol class="evidence-list">
            ${(synthesis.recommended_opportunities || []).map(item => `<li>${esc(item)}</li>`).join("") || "<li>暂无研究机会建议。</li>"}
          </ol>
        </article>
      `;
    };

    const renderAll = () => {
      renderProfileStrip();
      renderSummary();
      renderLlmStrip();
      renderMainline();
      renderOverview();
      renderPapers();
      renderMoc();
      renderGaps();
      renderOpportunities();
      renderSynthesis();
    };

    const setActiveTab = (tab) => {
      document.querySelectorAll(".tab-button").forEach(item => {
        item.classList.toggle("active", item.dataset.tab === tab);
      });
      document.querySelectorAll(".section").forEach(item => {
        item.classList.toggle("active", item.id === tab);
      });
      window.location.hash = tab;
    };

    document.querySelectorAll(".tab-button").forEach(button => {
      button.addEventListener("click", () => {
        setActiveTab(button.dataset.tab);
      });
    });

    renderAll();
    document.querySelectorAll("[data-tab-go]").forEach(button => {
      button.addEventListener("click", () => setActiveTab(button.dataset.tabGo));
    });
    const initialTab = window.location.hash.replace("#", "");
    if (initialTab && document.getElementById(initialTab)) {
      setActiveTab(initialTab);
    }
  </script>
</body>
</html>
"""
