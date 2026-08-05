from autoresearch.dedupe import dedupe_papers
from autoresearch.schema import PaperRecord


def test_dedupe_by_doi_merges_sources():
    rows = [
        PaperRecord(title="A Paper", doi="10.1/test", source="openalex", source_records=["openalex"]),
        PaperRecord(title="A Paper", doi="10.1/test", source="crossref", source_records=["crossref"]),
    ]

    deduped = dedupe_papers(rows)

    assert len(deduped) == 1
    assert deduped[0].source_records == ["crossref", "openalex"]

