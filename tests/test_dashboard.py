from autoresearch.dashboard import load_artifacts, write_dashboard
from autoresearch.schema import (
    EvidenceSnippet,
    FieldMap,
    GapEvidence,
    GapEvidenceStep,
    PaperCard,
    QueryPlan,
    RankedPaper,
    SearchArtifacts,
    SourceReadiness,
    SourceStatus,
    TopicMOC,
)


def _artifact() -> SearchArtifacts:
    return SearchArtifacts(
        topic="medical VLM temporal lesion change analysis",
        query_plan=QueryPlan(topic="medical VLM", queries=["medical VLM"], perspectives=[]),
        source_statuses=[
            SourceStatus(source="openalex", query="medical VLM", status="ok", raw_count=2)
        ],
        ranked_papers=[
            RankedPaper(
                paper={
                    "title": "Temporal lesion VLM",
                    "source_records": ["openalex"],
                },
                relevance_score=0.9,
                evidence_tier="core",
                evidence_tier_score_delta=0.18,
                evidence_tier_reasons=["matched core keyword: lesion"],
            )
        ],
        source_readiness=SourceReadiness(
            status="ready_for_preliminary_gap_analysis",
            ranked_papers=1,
            contributing_sources=1,
            moc_groups=1,
        ),
        paper_cards=[
            PaperCard(
                title="Temporal lesion VLM",
                problem="lesion-level temporal change reasoning",
                gap_hint="Validate paired lesion change reasoning.",
                evidence_tier="core",
                evidence_tier_score_delta=0.18,
                evidence_tier_reasons=["matched core keyword: lesion"],
            )
        ],
        field_map=FieldMap(),
        topic_moc=TopicMOC(topic="medical VLM", paper_groups={"candidate": ["Temporal lesion VLM"]}),
        gaps=[
            GapEvidence(
                gap="Temporal lesion reasoning is weakly covered.",
                evidence_chain=[
                    GapEvidenceStep(
                        paper_title="Temporal lesion VLM",
                        claim="supporting evidence",
                        evidence=EvidenceSnippet(
                            paper_title="Temporal lesion VLM",
                            source_url="https://example.com",
                            claim="abstract evidence",
                            snippet="We study lesion change.",
                            section="abstract",
                        ),
                    )
                ],
            )
        ],
    )


def test_write_dashboard_creates_static_html(tmp_path):
    path = write_dashboard(_artifact(), tmp_path)
    html = path.read_text(encoding="utf-8")

    assert path.name == "dashboard.html"
    assert "<html lang=\"zh-CN\">" in html
    assert "AutoResearch 调研看板" in html
    assert "研究主线" in html
    assert "核心结论" in html
    assert "从论文到 Gap 的链条" in html
    assert "推荐切入点" in html
    assert "证据分层板" in html
    assert "当前领域 Profile" in html
    assert "论文卡片" in html
    assert "Gap 证据链" in html
    assert "综合分析" in html
    assert "判断来源" in html
    assert "证据层级分布" in html
    assert "核心证据" in html
    assert "相邻证据" in html
    assert "噪声/需降权" in html
    assert "层级原因" in html
    assert "排序影响" in html
    assert "命中核心关键词" in html
    assert "Rule-generated" in html
    assert "Codex-reviewed" in html
    assert "LLM 抽取概况" in html
    assert "data-tab-go=\"gaps\"" in html
    assert "fold-summary" in html
    assert "错误/提示" in html
    assert "对比基线" in html
    assert "打开 Markdown" not in html


def test_load_artifacts_accepts_output_directory(tmp_path):
    artifact = _artifact()
    artifact.write_json(tmp_path)

    loaded = load_artifacts(tmp_path)

    assert loaded.topic == "medical VLM temporal lesion change analysis"
