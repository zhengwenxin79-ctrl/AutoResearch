from autoresearch.collectors.arxiv import _parse_feed
from autoresearch.collectors.europepmc import _first_full_text_url
from autoresearch.collectors.openreview import _paper_from_note
from autoresearch.open_access import _record_from_payload
from autoresearch.schema import PaperRecord, RankedPaper, SourceStatus, TopicMOC
from autoresearch.source_health import evaluate_source_readiness


def test_europepmc_full_text_url_prefers_first_available_url():
    assert (
        _first_full_text_url(
            {
                "fullTextUrlList": {
                    "fullTextUrl": [
                        {"url": ""},
                        {"url": "https://example.com/fulltext.pdf"},
                    ]
                }
            }
        )
        == "https://example.com/fulltext.pdf"
    )


def test_openreview_note_maps_forum_content_to_paper_record():
    paper = _paper_from_note(
        {
            "id": "review-note",
            "forum": "paper-forum",
            "forumContent": {
                "title": {"value": "A Medical VLM Benchmark"},
                "abstract": {"value": "We benchmark medical VLMs."},
                "venue": {"value": "ICLR 2026"},
                "authors": {"value": ["Ada Lovelace"]},
                "pdf": {"value": "/pdf?id=paper-forum"},
            },
        }
    )

    assert paper is not None
    assert paper.title == "A Medical VLM Benchmark"
    assert paper.venue == "ICLR 2026"
    assert paper.authors == ["Ada Lovelace"]
    assert paper.url == "https://openreview.net/forum?id=paper-forum"
    assert paper.pdf_url == "https://openreview.net/pdf?id=paper-forum"


def test_unpaywall_payload_maps_to_open_access_record():
    record = _record_from_payload(
        "A Paper",
        "10.123/test",
        {
            "is_oa": True,
            "oa_status": "gold",
            "best_oa_location": {
                "url_for_landing_page": "https://example.com/article",
                "url_for_pdf": "https://example.com/article.pdf",
                "evidence": "oa repository",
            },
        },
    )

    assert record.status == "ok"
    assert record.is_open_access is True
    assert record.pdf_url == "https://example.com/article.pdf"
    assert record.evidence == "oa repository"


def test_arxiv_feed_parser_extracts_paper_record():
    rows = _parse_feed(
        """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <id>http://arxiv.org/abs/2601.00001v1</id>
            <title>Temporal Medical VLM</title>
            <summary>We study lesion change reasoning.</summary>
            <published>2026-01-01T00:00:00Z</published>
            <author><name>Ada Lovelace</name></author>
            <link href="http://arxiv.org/abs/2601.00001v1" rel="alternate" type="text/html"/>
            <link title="pdf" href="http://arxiv.org/pdf/2601.00001v1" rel="related" type="application/pdf"/>
          </entry>
        </feed>
        """
    )

    assert len(rows) == 1
    assert rows[0].title == "Temporal Medical VLM"
    assert rows[0].year == 2026
    assert rows[0].pdf_url == "http://arxiv.org/pdf/2601.00001v1"


def test_source_readiness_gate_requires_breadth():
    ranked = [
        RankedPaper(
            paper=PaperRecord(
                title=f"Paper {idx}",
                source_records=[source],
            ),
            relevance_score=0.9,
        )
        for idx, source in enumerate(["openalex", "pubmed", "europepmc"] * 3)
    ]
    readiness = evaluate_source_readiness(
        [
            SourceStatus(source="openalex", query="q", status="ok", raw_count=3),
            SourceStatus(source="arxiv", query="q", status="failed", error="429"),
        ],
        ranked,
        TopicMOC(topic="medical VLM", paper_groups={"a": [], "b": [], "c": []}),
    )

    assert readiness.status == "ready_for_preliminary_gap_analysis"
    assert readiness.contributing_sources == 3
    assert "arxiv" in readiness.failed_sources
