from autoresearch.domain_profile import generate_domain_profile
from autoresearch.gap_finder import find_gaps
from autoresearch.query_planner import plan_queries
from autoresearch.reader import build_paper_cards
from autoresearch.schema import FieldMap, PaperRecord, RankedPaper


def test_auto_profile_detects_gui_agent_topic():
    profile = generate_domain_profile("GUI agent benchmark real-world workflow")
    plan = plan_queries("GUI agent benchmark real-world workflow", profile)

    assert profile.domain_id == "gui-agent"
    assert profile.capability_dimensions[0].name == "real-world long-horizon workflow"
    assert any("GUI agent benchmark" in query for query in plan.queries)


def test_profile_driven_gaps_are_not_medical_only():
    profile = generate_domain_profile("GUI agent benchmark real-world workflow")
    ranked = [
        RankedPaper(
            paper=PaperRecord(
                title="A WebArena benchmark for browser agents",
                abstract=(
                    "We evaluate web navigation agents on WebArena with multi-step workflows "
                    "and report task success rate."
                ),
            ),
            relevance_score=0.9,
        ),
        RankedPaper(
            paper=PaperRecord(
                title="Planning for language agents",
                abstract="We propose a planning method for LLM agents but do not discuss GUI failure recovery.",
            ),
            relevance_score=0.8,
        ),
    ]

    cards = build_paper_cards(ranked, profile=profile)
    gaps = find_gaps(cards, FieldMap(), profile=profile)

    assert any("capability:real-world-long-horizon-workflow" in card.coverage_tags for card in cards)
    assert gaps
    assert all("Lesion-level" not in gap.gap for gap in gaps)
    assert any(gap.gap.startswith("GUI Agent:") for gap in gaps)
