from autoresearch.fulltext import split_sections
from autoresearch.reader import build_paper_cards
from autoresearch.schema import FullTextRecord, PaperRecord, RankedPaper, TextSection


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

