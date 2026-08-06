from autoresearch.enrichment import _influence_from_payload


def test_semantic_scholar_payload_maps_to_influence():
    influence = _influence_from_payload(
        {
            "paperId": "abc123",
            "url": "https://www.semanticscholar.org/paper/abc123",
            "citationCount": 42,
            "influentialCitationCount": 7,
            "referenceCount": 30,
            "venue": "Test Venue",
            "isOpenAccess": True,
            "openAccessPdf": {"url": "https://example.com/paper.pdf"},
            "fieldsOfStudy": ["Medicine"],
            "s2FieldsOfStudy": [{"category": "Computer Science"}],
            "tldr": {"text": "A short summary."},
        }
    )

    assert influence.status == "ok"
    assert influence.paper_id == "abc123"
    assert influence.citation_count == 42
    assert influence.influential_citation_count == 7
    assert influence.reference_count == 30
    assert influence.open_access_pdf == "https://example.com/paper.pdf"
    assert influence.fields_of_study == ["Medicine", "Computer Science"]
