from autoresearch.collectors.europepmc import _first_full_text_url
from autoresearch.collectors.openreview import _paper_from_note
from autoresearch.open_access import _record_from_payload


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
