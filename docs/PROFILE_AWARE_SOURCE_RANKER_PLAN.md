# Profile-Aware Source / Ranker Plan

## 目标

这一阶段只解决一个问题：

```text
用户输入某个研究方向后，AutoResearch 应该优先保留目标领域核心论文，
把相邻领域论文标成 adjacent evidence，把明显噪声论文降权或过滤。
```

这不是为了替代 Codex Review。相反，它是为了让 Codex Review 拿到更干净的证据包。

## 当前问题

现在的 pipeline 有三个容易导致方向漂移的点：

1. `pipeline.py` 对所有领域都跑同一组 sources：

```text
arxiv, openalex, pubmed, europepmc, crossref, openreview
```

这导致 GUI Agent 这种 AI/agent 方向也会检索 PubMed / Europe PMC。

2. `ranker.py` 目前有硬编码的 medical / VLM / temporal 逻辑：

```text
wants_medical
wants_vlm
wants_temporal
MEDICAL_TERMS
VLM_TERMS
TEMPORAL_TERMS
```

这对医学 VLM demo 有帮助，但对 GUI Agent、LLM Agent 等非医学方向不够干净。

3. 现在只有 relevance score，没有显式证据层级：

```text
core evidence
adjacent evidence
possible noise
```

所以后面的 MOC / Gap Finder 会把相邻论文也当成同等强度证据。

## 非目标

本阶段不做这些事：

- 不接本地模型。
- 不重写整个 ranker。
- 不删除 Codex Review。
- 不直接进入 Auto Writing。
- 不追求一次性解决所有领域。

当前主线仍然是：

```text
Search -> Paper Cards -> MOC -> Gap Evidence -> Codex Review -> Dashboard
```

## 执行状态

截至 2026-08-08，前六个小步已经完成：

```text
Step 1: relevance fixtures -> done
Step 2: profile policy schema -> done
Step 3: standalone evidence tier scoring -> done
Step 4: ranker profile-aware integration -> done
Step 5: pipeline profile-aware ranker integration -> done
Step 6: Dashboard evidence tier display -> done
```

当前已经把 evidence tier 接入 `rank_papers`、`pipeline.py`、`PaperCard` 和 Codex Review Packet。
Dashboard 已经展示证据层级分布、论文卡片层级、排序影响和层级原因。

## 设计原则

1. **先标记，后过滤**

第一版不要激进删除论文。先给每篇论文打：

```text
core / adjacent / noise
```

这样用户和 Codex 都能看到系统为什么保留或降权某篇论文。

2. **Profile 决定 source policy**

不同领域应该有不同 source 权重。

例如 GUI Agent：

```text
preferred: arxiv, openreview, openalex
neutral: crossref
downrank: pubmed, europepmc
```

医学 VLM：

```text
preferred: pubmed, europepmc, openalex
neutral: arxiv, crossref, openreview
```

3. **Profile 决定关键词方向**

每个 profile 应该有：

```text
core_keywords
adjacent_keywords
negative_keywords
preferred_sources
downrank_sources
```

4. **所有判断都要写入 reasons**

排名不是黑箱。每个降权或升权都要体现在 `score_reasons` 里。

## 建议数据结构

先不急着实现，计划中的结构如下。

### Source Policy

```json
{
  "preferred_sources": ["arxiv", "openreview", "openalex"],
  "neutral_sources": ["crossref"],
  "downrank_sources": ["pubmed", "europepmc"],
  "disabled_sources": [],
  "source_weight_overrides": {
    "arxiv": 0.14,
    "openreview": 0.14,
    "openalex": 0.10,
    "crossref": 0.05,
    "pubmed": -0.08,
    "europepmc": -0.08
  }
}
```

### Evidence Policy

```json
{
  "core_keywords": [
    "GUI agent",
    "web navigation",
    "desktop control",
    "mobile agent",
    "OSWorld",
    "WebArena",
    "AndroidWorld"
  ],
  "adjacent_keywords": [
    "workflow automation",
    "tool agent",
    "computer use",
    "browser automation"
  ],
  "negative_keywords": [
    "clinical",
    "PET/CT",
    "ophthalmic",
    "patient",
    "radiology"
  ]
}
```

### Evidence Tier

每篇论文增加一个可解释标签：

```json
{
  "evidence_tier": "core",
  "evidence_tier_reasons": [
    "matched core keyword: GUI agent",
    "matched benchmark keyword: AndroidWorld",
    "preferred source: arxiv"
  ]
}
```

可选值：

```text
core
adjacent
noise
unknown
```

## 小步实施计划

### Step 1: 增加评估 fixture

先做测试数据，不改真实 ranking。

新增：

```text
tests/fixtures/gui_agent_relevance.json
tests/fixtures/medical_vlm_relevance.json
```

每条记录人工标注：

```json
{
  "title": "...",
  "expected_tier": "core",
  "reason": "direct GUI Agent benchmark paper"
}
```

验收标准：

- GUI Agent fixture 至少包含：
  - `MobileUse`
  - `LongHorizonUI`
  - `GUI-ReWalk`
  - 一个医疗 workflow adjacent/noise 例子
- Medical VLM fixture 至少包含：
  - 医学 VLM core paper
  - 泛 AI / 非医学 adjacent/noise 例子

### Step 2: 给 Domain Profile 加 policy 字段

只加 schema 和 profile seed，不改变 pipeline 行为。

涉及文件：

```text
src/autoresearch/schema.py
src/autoresearch/domain_profile.py
profiles/medical-vlm.json
profiles/gui-agent.json
tests/test_domain_profile.py
```

新增概念：

```text
source_policy
evidence_policy
```

验收标准：

- `autoresearch profile "GUI agent benchmark" --profile-id gui-agent` 能输出 source/evidence policy。
- 旧 profile JSON 仍能加载。
- 测试覆盖默认值，不破坏已有 SearchArtifacts。

### Step 3: 实现 evidence tier 打分函数

先独立实现，不接入最终 ranking。

建议新增：

```text
src/autoresearch/relevance.py
```

函数：

```python
class EvidenceTierScore:
    tier: str
    score_delta: float
    reasons: list[str]

score_evidence_tier(paper, profile) -> EvidenceTierScore
```

验收标准：

- GUI Agent:
  - MobileUse -> core
  - LongHorizonUI -> core
  - GUI-ReWalk -> core 或 adjacent
  - PET/CT workflow paper -> adjacent 或 noise
- Medical VLM:
  - radiology / lesion / medical VLM paper -> core
  - generic agent paper -> noise 或 adjacent

### Step 4: Ranker 接入 profile，但保持旧接口兼容

修改：

```python
rank_papers(papers, plan, limit, profile=None)
```

如果 `profile is None`，走旧逻辑。

如果有 profile：

```text
final_score = old_score + source_policy_delta + evidence_tier_delta
```

score reasons 增加：

```text
evidence_tier=core
source_policy=preferred:openreview
negative_keyword=clinical
```

验收标准：

- GUI Agent top-k 中 core paper 排名上升。
- 医疗 workflow paper 不再排在 GUI Agent top 3。
- Medical VLM 排名不退化。
- 所有被降权论文仍可追踪原因。

### Step 5: Pipeline 接入 profile-aware ranker

修改：

```text
src/autoresearch/pipeline.py
```

从：

```python
rank_papers(deduped, plan, limit=limit)
```

到：

```python
rank_papers(deduped, plan, limit=limit, profile=domain_profile)
```

验收标准：

- GUI Agent demo 重新跑后，source drift 降低。
- `score_reasons` 能解释 source/evidence tier。
- Dashboard 中可以看到每篇论文为什么是 core/adjacent/noise。

### Step 6: Dashboard 显示 evidence tier

给论文卡片显示：

```text
Evidence Tier: core / adjacent / noise
Tier Reasons: ...
```

验收标准：

- 用户不用打开 JSON，也能判断论文是否支撑核心 Gap。
- Codex Review packet 里同步包含 evidence tier。

### Step 7: Source coverage 升级成 source quality

当前 `source_coverage.md` 只统计来源数量。

下一步增加：

```text
source -> core papers
source -> adjacent papers
source -> noise papers
```

验收标准：

- GUI Agent 里 PubMed / Europe PMC 如果贡献的多是 noise，会在 source quality 中暴露。
- 后续可以基于这个决定是否禁用某些 source。

### Step 8: 再考虑 source gating

只有当 evidence tier 稳定后，才考虑跳过某些 source。

第一版建议：

```text
disabled_sources 默认为空
downrank_sources 只降权，不跳过
```

第二版再考虑：

```bash
autoresearch search "..." --strict-profile-sources
```

验收标准：

- 默认不丢失旁证。
- strict 模式才减少 source/query 调用。

## GUI Agent 的预期变化

当前问题：

```text
GUI Agent demo 混入 PET/CT、ophthalmic diagnosis、clinical workflow 等论文。
```

目标效果：

```text
MobileUse -> core
LongHorizonUI -> core
GUI-ReWalk -> core/adjacent
VX desktop genome viewer -> adjacent
PET/CT workflow agent -> adjacent/noise
ophthalmic diagnosis agent -> adjacent/noise
clinical workflow commentary -> noise
```

这样 Codex Review 看到的不是一堆平权论文，而是：

```text
core evidence: 可支撑 GUI Agent Gap
adjacent evidence: 可做旁证
noise: 不应进入核心 Gap 证据链
```

## 最小可执行顺序

建议下一轮只执行前三步：

```text
1. relevance fixture
2. profile policy schema
3. evidence tier scoring function
```

不要一次性改 pipeline 和 dashboard。

这三个小步做完后，再由用户检查：

```text
evidence tier 是否符合直觉？
GUI Agent 的医疗论文是否被正确降权？
Medical VLM 是否没有被误伤？
```

通过后再接入 ranker。

## 风险

1. **过度过滤**

有些 adjacent paper 可能提供真实 workflow 复杂性的旁证，不能直接删除。

缓解：

```text
先标记，后过滤。
```

2. **关键词规则太脆**

只靠关键词可能误判。

缓解：

```text
保留 Codex Review；evidence tier 是辅助，不是最终判断。
```

3. **不同领域 profile 质量不一致**

新领域一开始可能没有好 policy。

缓解：

```text
generic fallback profile 只做轻量 source prior，不做强负面过滤。
```

## 验收总标准

这个阶段完成后，AutoResearch 应该能回答：

```text
这篇论文为什么被检索进来？
它是目标领域核心证据，还是相邻证据？
它为什么被升权或降权？
它是否应该进入 Gap evidence chain？
```

如果这些问题在 Dashboard 和 Codex Review Packet 里都能看清楚，就可以进入下一阶段：

```text
Codex-reviewed MOC refinement
```
