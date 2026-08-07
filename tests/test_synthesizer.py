from autoresearch.schema import (
    DomainProfile,
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
)
from autoresearch.synthesizer import build_synthesis, write_analysis_report


def _artifact() -> SearchArtifacts:
    gap = GapEvidence(
        gap="GUI Agent: failure recovery and self-correction is weakly covered by the retrieved literature.",
        evidence_chain=[
            GapEvidenceStep(
                paper_title="GUI Agent Benchmark",
                role="support",
                claim="failure recovery is not explicit",
                evidence=EvidenceSnippet(
                    paper_title="GUI Agent Benchmark",
                    source_url="https://example.com",
                    claim="failure recovery is not explicit",
                    snippet="We evaluate task success rate on web navigation tasks.",
                    section="abstract",
                ),
            )
        ],
        support_count=1,
        counter_count=0,
        total_papers=1,
        confidence=0.58,
        why_it_matters="Recovery is important for real GUI workflows.",
    )
    return SearchArtifacts(
        topic="GUI agent benchmark real-world workflow",
        domain_profile=DomainProfile(
            domain_id="gui-agent",
            domain_name="GUI Agent",
            core_concepts=["GUI agent", "failure recovery"],
        ),
        query_plan=QueryPlan(topic="GUI agent", queries=["GUI agent benchmark"], perspectives=[]),
        source_statuses=[SourceStatus(source="openreview", query="GUI agent", status="ok", raw_count=1)],
        ranked_papers=[
            RankedPaper(
                paper={"title": "GUI Agent Benchmark", "source_records": ["openreview"]},
                relevance_score=0.9,
            )
        ],
        source_readiness=SourceReadiness(status="ready_for_preliminary_gap_analysis"),
        paper_cards=[PaperCard(title="GUI Agent Benchmark")],
        field_map=FieldMap(),
        gaps=[gap],
    )


def test_build_synthesis_creates_chinese_summary():
    synthesis = build_synthesis(_artifact())

    assert synthesis.mode == "codex_substituted_llm"
    assert synthesis.status == "ready"
    assert "GUI Agent" in synthesis.domain_interpretation
    assert "候选 Gap" in synthesis.executive_summary
    assert synthesis.gap_summaries[0].gap.startswith("GUI Agent:")


def test_write_analysis_report(tmp_path):
    artifacts = _artifact()
    artifacts.synthesis = build_synthesis(artifacts)

    path = write_analysis_report(artifacts, tmp_path)
    text = path.read_text(encoding="utf-8")

    assert path.name == "analysis_report.md"
    assert "AutoResearch 综合分析" in text
    assert "Codex 代替外部 LLM" in text
