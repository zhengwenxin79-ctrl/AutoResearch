from autoresearch.llm_extractor import (
    LLMCardPatch,
    LLMFieldValue,
    _extract_json_payload,
    apply_llm_patch,
    enhance_paper_cards_with_llm,
)
from autoresearch.schema import EvidenceSnippet, PaperCard


def test_extract_json_payload_accepts_fenced_json():
    payload = _extract_json_payload(
        """```json
        {"problem": {"value": "temporal lesion reasoning", "evidence_ids": ["primary_1"]}}
        ```"""
    )

    assert payload["problem"]["value"] == "temporal lesion reasoning"


def test_apply_llm_patch_requires_valid_evidence_id():
    card = PaperCard(
        title="A Paper",
        url="https://example.com",
        problem="general medical multimodal foundation capability",
    )
    evidence = {
        "primary_1": EvidenceSnippet(
            paper_title="A Paper",
            source_url="https://example.com",
            claim="abstract evidence",
            snippet="We study temporal lesion change reasoning.",
            section="abstract",
        )
    }

    record = apply_llm_patch(
        card,
        LLMCardPatch(
            problem=LLMFieldValue(
                value="lesion-level temporal change reasoning",
                evidence_ids=["primary_1"],
            ),
            task=LLMFieldValue(value="unsupported task", evidence_ids=["missing_id"]),
        ),
        evidence,
        model="test-model",
    )

    assert record.status == "ok"
    assert record.fields_updated == ["problem"]
    assert card.problem == "lesion-level temporal change reasoning"
    assert card.task == ""
    assert card.extraction_status["problem"] == "llm_evidence_grounded"
    assert "llm_extracted" in card.coverage_tags


def test_enhance_paper_cards_skips_without_key(monkeypatch):
    monkeypatch.delenv("AUTORESEARCH_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cards = [
        PaperCard(
            title="A Paper",
            evidence_snippets=[
                EvidenceSnippet(
                    paper_title="A Paper",
                    source_url="https://example.com",
                    claim="abstract evidence",
                    snippet="We study medical VLMs.",
                    section="abstract",
                )
            ],
        )
    ]

    records = enhance_paper_cards_with_llm(cards, limit=1, model="test-model")

    assert records[0].status == "skipped"
    assert "not configured" in records[0].error
