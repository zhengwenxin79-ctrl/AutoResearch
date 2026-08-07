from autoresearch.gap_finder import build_research_opportunities, find_gaps
from autoresearch.moc import (
    GROUP_DIAGNOSIS,
    GROUP_TEMPORAL_LESION,
    build_research_space,
    group_for_card,
)
from autoresearch.reader import build_paper_cards
from autoresearch.schema import FieldMap, PaperRecord, RankedPaper


def test_group_for_card_identifies_temporal_lesion_candidate():
    ranked = [
        RankedPaper(
            paper=PaperRecord(
                title="Temporal lesion VLM",
                abstract="We evaluate temporal lesion change analysis with accuracy.",
                url="https://example.com/temporal",
            ),
            relevance_score=0.9,
        )
    ]

    card = build_paper_cards(ranked)[0]

    assert card.problem == "lesion-level temporal change reasoning"
    assert card.core_assumption
    assert "explicit dataset" in card.missing_capability
    assert group_for_card(card) == GROUP_TEMPORAL_LESION


def test_build_research_space_creates_moc_and_comparison_rows():
    ranked = [
        RankedPaper(
            paper=PaperRecord(
                title="Static medical VLM",
                abstract="We propose a medical vision-language model for diagnosis.",
                url="https://example.com/static",
            ),
            relevance_score=0.8,
        ),
        RankedPaper(
            paper=PaperRecord(
                title="Medical VQA model",
                abstract="We propose a medical visual question answering model for diagnosis.",
                url="https://example.com/vqa",
            ),
            relevance_score=0.7,
        ),
        RankedPaper(
            paper=PaperRecord(
                title="Temporal lesion VLM",
                abstract="We evaluate temporal lesion change analysis on MIMIC-CXR with accuracy.",
                url="https://example.com/temporal",
            ),
            relevance_score=0.9,
        ),
    ]
    cards = build_paper_cards(ranked)
    gaps = find_gaps(cards, FieldMap())

    insights, topic_moc, comparison = build_research_space("medical VLM temporal lesion", cards, gaps)

    assert len(insights) == 3
    assert GROUP_DIAGNOSIS in topic_moc.paper_groups
    assert GROUP_TEMPORAL_LESION in topic_moc.paper_groups
    assert topic_moc.problem_spaces
    assert topic_moc.problem_spaces[0].representative_papers
    assert topic_moc.open_questions
    assert {row.group for row in comparison.rows} == {GROUP_DIAGNOSIS, GROUP_TEMPORAL_LESION}
    assert all(row.solves for row in comparison.rows)
    assert all(row.missing for row in comparison.rows)
    assert all(row.problem for row in comparison.rows)
    assert all(row.gap_hints for row in comparison.rows)

    opportunities = build_research_opportunities(gaps)
    assert opportunities
    assert opportunities[0].evidence_refs
