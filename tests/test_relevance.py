import json
from pathlib import Path

from autoresearch.domain_profile import generate_domain_profile, load_domain_profile
from autoresearch.relevance import score_evidence_tier
from autoresearch.schema import DomainProfile, PaperRecord

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _paper_from_fixture(row: dict) -> PaperRecord:
    return PaperRecord(
        title=row["title"],
        abstract=row.get("abstract", ""),
        source=row.get("source", ""),
        source_records=row.get("source_records", []),
    )


def test_generated_profiles_include_source_and_evidence_policy():
    gui_profile = generate_domain_profile("GUI agent benchmark real-world workflow")
    medical_profile = generate_domain_profile("medical VLM temporal lesion change analysis")

    assert gui_profile.source_policy.preferred_sources == ["arxiv", "openreview", "openalex"]
    assert "pubmed" in gui_profile.source_policy.downrank_sources
    assert "MobileUse" in gui_profile.evidence_policy.core_keywords
    assert "PET/CT" in gui_profile.evidence_policy.negative_keywords

    assert medical_profile.source_policy.preferred_sources == ["pubmed", "europepmc", "openalex"]
    assert "medical VLM" in medical_profile.evidence_policy.core_keywords
    assert "GUI agent" in medical_profile.evidence_policy.negative_keywords


def test_profile_json_policy_loads_from_disk():
    profile = load_domain_profile(REPO_ROOT / "profiles" / "gui-agent.json", "GUI agent benchmark")

    assert profile.domain_id == "gui-agent"
    assert profile.source_policy.source_weight_overrides["arxiv"] == 0.14
    assert "OSWorld" in profile.evidence_policy.core_keywords


def test_legacy_profile_without_policy_fields_still_loads():
    profile = DomainProfile.model_validate({"domain_id": "legacy", "domain_name": "Legacy"})
    paper = PaperRecord(title="Unrelated Study", abstract="No profile-specific evidence.")
    score = score_evidence_tier(paper, profile)

    assert profile.source_policy.preferred_sources == []
    assert profile.evidence_policy.core_keywords == []
    assert score.tier == "unknown"
    assert score.score_delta == 0.0


def test_gui_agent_evidence_tiers_match_fixture():
    profile = generate_domain_profile("GUI agent benchmark real-world workflow")
    results = {}

    for row in _load_fixture("gui_agent_relevance.json"):
        score = score_evidence_tier(_paper_from_fixture(row), profile)
        results[row["title"]] = score
        assert score.tier == row["expected_tier"], row["reason"]
        assert score.reasons

    assert results["MobileUse: A Benchmark for GUI Agents in Mobile Environments"].score_delta > 0
    assert any(
        "source_policy=downrank:pubmed" in reason
        for reason in results["Clinical Workflow Agents for PET/CT Triage"].reasons
    )


def test_medical_vlm_evidence_tiers_match_fixture():
    profile = generate_domain_profile("medical VLM temporal lesion change analysis")
    results = {}

    for row in _load_fixture("medical_vlm_relevance.json"):
        score = score_evidence_tier(_paper_from_fixture(row), profile)
        results[row["title"]] = score
        assert score.tier == row["expected_tier"], row["reason"]
        assert score.reasons

    assert (
        results["Temporal Lesion Change Analysis with Medical Vision-Language Models"].score_delta
        > results["Planning and Reflection for GUI Agents on WebArena"].score_delta
    )
