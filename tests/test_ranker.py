from autoresearch.domain_profile import generate_domain_profile
from autoresearch.ranker import rank_papers
from autoresearch.reader import build_paper_cards
from autoresearch.schema import PaperRecord, QueryPlan


def _plan(topic: str) -> QueryPlan:
    return QueryPlan(topic=topic, queries=[topic], perspectives=[])


def test_ranker_without_profile_preserves_legacy_evidence_defaults():
    ranked = rank_papers(
        [
            PaperRecord(
                title="Clinical Workflow Agents for PET/CT Triage",
                abstract="This clinical workflow agent supports PET/CT patient triage.",
                source="pubmed",
                source_records=["pubmed"],
            )
        ],
        _plan("GUI agent benchmark real-world workflow"),
        limit=1,
    )

    assert ranked[0].evidence_tier == "unknown"
    assert ranked[0].evidence_tier_score_delta == 0.0
    assert ranked[0].evidence_tier_reasons == []
    assert all(not reason.startswith("evidence_tier=") for reason in ranked[0].score_reasons)


def test_gui_agent_profile_promotes_core_and_downranks_medical_noise():
    profile = generate_domain_profile("GUI agent benchmark real-world workflow")
    papers = [
        PaperRecord(
            title="Clinical Workflow Agents for PET/CT Triage",
            abstract="This clinical system supports PET/CT patient triage and diagnosis workflows.",
            source="pubmed",
            source_records=["pubmed"],
        ),
        PaperRecord(
            title="MobileUse: A Benchmark for GUI Agents in Mobile Environments",
            abstract=(
                "MobileUse evaluates mobile GUI agents on AndroidWorld-style multi-step tasks "
                "and reports task success rate."
            ),
            source="arxiv",
            source_records=["arxiv"],
        ),
    ]

    ranked = rank_papers(papers, _plan("GUI agent benchmark real-world workflow"), limit=2, profile=profile)
    by_title = {row.paper.title: row for row in ranked}

    core = by_title["MobileUse: A Benchmark for GUI Agents in Mobile Environments"]
    noise = by_title["Clinical Workflow Agents for PET/CT Triage"]
    assert ranked[0].paper.title == core.paper.title
    assert core.evidence_tier == "core"
    assert core.evidence_tier_score_delta > 0
    assert noise.evidence_tier == "noise"
    assert noise.evidence_tier_score_delta < 0
    assert any("evidence_tier=core" == reason for reason in core.score_reasons)
    assert any("source_policy=downrank:pubmed" == reason for reason in noise.score_reasons)


def test_medical_vlm_profile_keeps_medical_core_and_downranks_gui_noise():
    profile = generate_domain_profile("medical VLM temporal lesion change analysis")
    papers = [
        PaperRecord(
            title="Planning and Reflection for GUI Agents on WebArena",
            abstract="This work evaluates browser automation and failure recovery for GUI agents.",
            source="openreview",
            source_records=["openreview"],
        ),
        PaperRecord(
            title="Temporal Lesion Change Analysis with Medical Vision-Language Models",
            abstract=(
                "We study longitudinal radiology exams with lesion-level grounding, follow-up "
                "comparison, and temporal change labels."
            ),
            source="pubmed",
            source_records=["pubmed"],
        ),
    ]

    ranked = rank_papers(
        papers,
        _plan("medical VLM temporal lesion change analysis"),
        limit=2,
        profile=profile,
    )
    by_title = {row.paper.title: row for row in ranked}

    core = by_title["Temporal Lesion Change Analysis with Medical Vision-Language Models"]
    noise = by_title["Planning and Reflection for GUI Agents on WebArena"]
    assert ranked[0].paper.title == core.paper.title
    assert core.evidence_tier == "core"
    assert noise.evidence_tier == "noise"
    assert core.relevance_score > noise.relevance_score


def test_paper_cards_inherit_ranked_evidence_tier():
    profile = generate_domain_profile("GUI agent benchmark real-world workflow")
    ranked = rank_papers(
        [
            PaperRecord(
                title="GUI-ReWalk: Benchmarking Failure Recovery for Browser Agents",
                abstract=(
                    "GUI-ReWalk studies browser agent recovery on WebArena and OSWorld tasks "
                    "with trajectory-level failure analysis."
                ),
                source="openalex",
                source_records=["openalex"],
            )
        ],
        _plan("GUI agent benchmark real-world workflow"),
        limit=1,
        profile=profile,
    )

    card = build_paper_cards(ranked, profile=profile)[0]

    assert card.evidence_tier == "core"
    assert card.evidence_tier_score_delta == ranked[0].evidence_tier_score_delta
    assert card.evidence_tier_reasons == ranked[0].evidence_tier_reasons
