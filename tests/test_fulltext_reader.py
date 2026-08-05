from autoresearch.fulltext import split_sections
from autoresearch.gap_finder import find_gaps
from autoresearch.reader import build_paper_cards
from autoresearch.schema import FieldMap, FullTextRecord, PaperRecord, RankedPaper, TextSection


def test_split_sections_detects_common_headings():
    sections = split_sections(
        """
Abstract
This is an abstract.
Methods
We evaluate on MIMIC-CXR with accuracy and F1.
Limitations
This is single-timepoint.
"""
    )

    assert [section.heading for section in sections] == ["Abstract", "Methods", "Limitations"]


def test_reader_uses_full_text_for_dataset_and_metric():
    ranked = [
        RankedPaper(
            paper=PaperRecord(
                title="Medical VLM for lesion change",
                abstract="We propose a medical vision-language model.",
                url="https://example.com/paper",
            ),
            relevance_score=0.9,
        )
    ]
    full_texts = {
        "Medical VLM for lesion change": FullTextRecord(
            title="Medical VLM for lesion change",
            status="ok",
            sections=[
                TextSection(
                    heading="Methods",
                    text="We evaluate temporal lesion reasoning on MIMIC-CXR using accuracy and F1.",
                )
            ],
        )
    }

    cards = build_paper_cards(ranked, full_texts=full_texts)

    assert cards[0].dataset == "MIMIC-CXR"
    assert "accuracy" in cards[0].metrics
    assert cards[0].evidence_snippets[0].section == "Methods"
    assert "temporal_or_change" in cards[0].coverage_tags
    assert "lesion_or_localization" in cards[0].coverage_tags
    assert cards[0].extraction_status["dataset"] == "explicit"
    assert cards[0].field_evidence["dataset"].section == "Methods"


def test_gap_finder_scores_support_and_counter_evidence():
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
                title="Temporal lesion VLM",
                abstract="We evaluate temporal lesion change analysis on MIMIC-CXR with accuracy.",
                url="https://example.com/temporal",
            ),
            relevance_score=0.9,
        ),
    ]

    cards = build_paper_cards(ranked)
    gaps = find_gaps(cards, FieldMap())

    lesion_gap = gaps[0]

    assert lesion_gap.total_papers == 2
    assert lesion_gap.support_count == 1
    assert lesion_gap.counter_count == 1
    assert lesion_gap.support_ratio == 0.5
    assert lesion_gap.counter_ratio == 0.5
    assert lesion_gap.score_reasons
