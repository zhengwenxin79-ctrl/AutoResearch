from autoresearch.codex_review import (
    CodexGapResult,
    CodexMOCGroupResult,
    CodexOpportunityResult,
    CodexReviewResult,
    apply_codex_review,
    write_codex_review_packet,
)
from autoresearch.schema import (
    DomainProfile,
    EvidenceSnippet,
    FieldMap,
    GapEvidence,
    PaperCard,
    QueryPlan,
    RankedPaper,
    SearchArtifacts,
    SourceReadiness,
    SourceStatus,
)


def _artifact() -> SearchArtifacts:
    snippet = EvidenceSnippet(
        paper_title="GUI Recovery Benchmark",
        source_url="https://example.com/recovery",
        claim="recovery evidence",
        snippet="The benchmark studies GUI task success and recovery.",
        section="abstract",
    )
    return SearchArtifacts(
        topic="GUI agent failure recovery benchmark",
        domain_profile=DomainProfile(
            domain_id="gui-agent",
            domain_name="GUI Agent",
            core_concepts=["GUI agent", "failure recovery"],
        ),
        query_plan=QueryPlan(topic="GUI agent", queries=["GUI agent recovery"], perspectives=[]),
        source_statuses=[SourceStatus(source="openreview", query="GUI agent", status="ok")],
        ranked_papers=[
            RankedPaper(
                paper={
                    "title": "GUI Recovery Benchmark",
                    "abstract": "We study recovery in GUI agents.",
                    "url": "https://example.com/recovery",
                },
                relevance_score=0.9,
                evidence_tier="core",
                evidence_tier_score_delta=0.18,
                evidence_tier_reasons=["matched core keyword: GUI agent"],
            )
        ],
        source_readiness=SourceReadiness(status="needs_more_evidence"),
        paper_cards=[
            PaperCard(
                title="GUI Recovery Benchmark",
                url="https://example.com/recovery",
                problem="failure recovery and self-correction",
                evidence_tier="core",
                evidence_tier_score_delta=0.18,
                evidence_tier_reasons=["matched core keyword: GUI agent"],
                evidence_snippets=[snippet],
            )
        ],
        field_map=FieldMap(),
        gaps=[GapEvidence(gap="Old rule gap", total_papers=1)],
    )


def _review() -> CodexReviewResult:
    return CodexReviewResult(
        mode="codex_manual_llm_pass",
        status="draft",
        executive_summary="人工 LLM 判断：需要 failure-conditioned evaluation。",
        domain_interpretation="GUI Agent 需要评价长时程任务中的失败恢复。",
        search_assessment="当前证据仍需全文验证。",
        evidence_quality="摘要级证据。",
        moc_takeaways=["MOC 应拆成 recovery benchmark。"],
        moc_groups=[
            CodexMOCGroupResult(
                name="Recovery benchmark",
                problem_space="failure-conditioned recovery evaluation",
                representative_papers=["GUI Recovery Benchmark"],
                shared_assumptions=["aggregate success hides failure modes"],
                method_families=["reflection"],
                datasets_or_benchmarks=["GUIBench"],
                metrics=["recovery success rate"],
                covered_capabilities=["failure recovery"],
                missing_capabilities=["failure taxonomy"],
                open_questions=["Which failure types are recovered?"],
                possible_experiments=["Inject controlled GUI failures."],
            )
        ],
        gaps=[
            CodexGapResult(
                gap="Refined gap: missing failure-conditioned evaluation",
                judgment="成立，但需要全文验证。",
                support="支持证据来自 recovery benchmark 摘要。",
                evidence_refs=["GUI Recovery Benchmark"],
                support_papers=["GUI Recovery Benchmark"],
                confidence=0.7,
                why_it_matters="Aggregate scores hide failures.",
                research_opportunity="Build a diagnostic recovery benchmark.",
                score_reasons=["manual Codex review"],
            )
        ],
        opportunities=[
            CodexOpportunityResult(
                gap="Refined gap: missing failure-conditioned evaluation",
                research_question="Can GUI agents recover from typed failures?",
                hypothesis="Failure-conditioned metrics expose hidden weaknesses.",
                proposed_method="Build typed failure slices.",
                innovations_bound_to_gap=["bound to refined gap"],
                required_data="GUI traces",
                evaluation_protocol=["recovery success rate"],
                baselines=["success-rate-only"],
                ablations=["without verifier"],
                risks=["manual labels may be expensive"],
                evidence_refs=["GUI Recovery Benchmark"],
            )
        ],
        limitations=["Need full text."],
        next_steps=["Read method and experiment sections."],
    )


def test_write_codex_review_packet(tmp_path):
    packet_md, packet_json, template_path = write_codex_review_packet(_artifact(), tmp_path)

    packet_text = packet_md.read_text(encoding="utf-8")

    assert "Codex Manual LLM Review Packet" in packet_text
    assert "审查问题清单" in packet_text
    assert "core evidence" in packet_text
    assert "GUI Recovery Benchmark" in packet_json.read_text(encoding="utf-8")
    assert '"evidence_tier": "core"' in packet_json.read_text(encoding="utf-8")
    assert "codex_manual_llm_pass" in template_path.read_text(encoding="utf-8")


def test_apply_codex_review_updates_research_artifacts():
    artifacts = apply_codex_review(_artifact(), _review())

    assert artifacts.synthesis
    assert artifacts.synthesis.mode == "codex_manual_llm_pass"
    assert artifacts.topic_moc
    assert list(artifacts.topic_moc.paper_groups) == ["Recovery benchmark"]
    assert artifacts.gaps[0].gap.startswith("Refined gap")
    assert artifacts.gaps[0].support_count == 1
    assert artifacts.research_opportunities[0].research_question.startswith("Can GUI agents")
