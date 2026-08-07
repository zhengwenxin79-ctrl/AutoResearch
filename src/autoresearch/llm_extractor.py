from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from .schema import EvidenceSnippet, LLMExtractionRecord, PaperCard
from .utils import clean_text

LLM_FIELDS = [
    "problem",
    "task",
    "method",
    "method_family",
    "core_assumption",
    "dataset",
    "metrics",
    "claimed_contribution",
    "limitation",
    "missing_capability",
    "relation_to_topic",
    "gap_hint",
]


class LLMFieldValue(BaseModel):
    value: str = ""
    evidence_ids: list[str] = Field(default_factory=list)


class LLMCardPatch(BaseModel):
    problem: LLMFieldValue | None = None
    task: LLMFieldValue | None = None
    method: LLMFieldValue | None = None
    method_family: LLMFieldValue | None = None
    core_assumption: LLMFieldValue | None = None
    dataset: LLMFieldValue | None = None
    metrics: LLMFieldValue | None = None
    claimed_contribution: LLMFieldValue | None = None
    limitation: LLMFieldValue | None = None
    missing_capability: LLMFieldValue | None = None
    relation_to_topic: LLMFieldValue | None = None
    gap_hint: LLMFieldValue | None = None


def _api_key() -> str:
    return os.environ.get("AUTORESEARCH_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY", "")


def _base_url() -> str:
    return os.environ.get("AUTORESEARCH_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")


def _model(model: str = "") -> str:
    return model or os.environ.get("AUTORESEARCH_LLM_MODEL", "")


def _evidence_pack(card: PaperCard) -> dict[str, EvidenceSnippet]:
    pack: dict[str, EvidenceSnippet] = {}
    for idx, snippet in enumerate(card.evidence_snippets[:3], start=1):
        pack[f"primary_{idx}"] = snippet
    for field, snippet in sorted(card.field_evidence.items()):
        pack[f"field_{field}"] = snippet
    return pack


def _prompt(card: PaperCard, evidence_pack: dict[str, EvidenceSnippet]) -> list[dict[str, str]]:
    evidence_lines = []
    for evidence_id, snippet in evidence_pack.items():
        section = f"section={snippet.section or 'unknown'}"
        evidence_lines.append(
            f"[{evidence_id}] {section}; claim={snippet.claim}; text={clean_text(snippet.snippet, 700)}"
        )
    current = {
        field: getattr(card, field)
        for field in LLM_FIELDS
    }
    user_content = {
        "paper": {
            "title": card.title,
            "year": card.year,
            "venue": card.venue,
            "url": card.url,
            "current_card": current,
        },
        "allowed_evidence": evidence_lines,
        "output_schema": {
            field: {
                "value": "short extracted value, or keep current value if evidence is insufficient",
                "evidence_ids": ["one or more allowed evidence ids"],
            }
            for field in LLM_FIELDS
        },
    }
    return [
        {
            "role": "system",
            "content": (
                "You extract evidence-grounded research paper cards. Return JSON only. "
                "Every non-empty field must cite at least one allowed evidence id. "
                "Do not invent datasets, metrics, limitations, assumptions, or gaps. "
                "If evidence is insufficient, keep the current value and cite the closest evidence."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(user_content, ensure_ascii=False),
        },
    ]


def _extract_json_payload(text: str) -> dict[str, Any]:
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, flags=re.DOTALL)
    if fenced:
        stripped = fenced.group(1)
    return json.loads(stripped)


def _call_openai_compatible(
    messages: list[dict[str, str]],
    *,
    model: str,
    timeout: float,
) -> dict[str, Any]:
    response = httpx.post(
        f"{_base_url()}/chat/completions",
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    content = payload["choices"][0]["message"]["content"]
    return _extract_json_payload(content)


def apply_llm_patch(
    card: PaperCard,
    patch: LLMCardPatch,
    evidence_pack: dict[str, EvidenceSnippet],
    *,
    model: str,
) -> LLMExtractionRecord:
    fields_updated = []
    evidence_refs: dict[str, list[str]] = {}
    for field in LLM_FIELDS:
        value: LLMFieldValue | None = getattr(patch, field)
        if not value:
            continue
        cleaned = clean_text(value.value, 500)
        valid_ids = [evidence_id for evidence_id in value.evidence_ids if evidence_id in evidence_pack]
        if not cleaned or not valid_ids:
            continue
        current = getattr(card, field)
        if cleaned != current:
            setattr(card, field, cleaned)
            fields_updated.append(field)
        card.field_evidence[field] = EvidenceSnippet(
            paper_title=card.title,
            source_url=card.url,
            claim=f"LLM evidence-grounded extraction for {field}",
            snippet=evidence_pack[valid_ids[0]].snippet,
            section=evidence_pack[valid_ids[0]].section,
        )
        card.extraction_status[field] = "llm_evidence_grounded"
        evidence_refs[field] = valid_ids
    if fields_updated and "llm_extracted" not in card.coverage_tags:
        card.coverage_tags.append("llm_extracted")
    return LLMExtractionRecord(
        title=card.title,
        model=model,
        status="ok" if fields_updated else "no_update",
        fields_updated=fields_updated,
        evidence_refs=evidence_refs,
    )


def enhance_paper_cards_with_llm(
    cards: list[PaperCard],
    *,
    limit: int = 0,
    model: str = "",
    timeout: float = 45.0,
) -> list[LLMExtractionRecord]:
    if limit <= 0:
        return []
    selected = cards[:limit]
    resolved_model = _model(model)
    if not _api_key():
        return [
            LLMExtractionRecord(
                title=card.title,
                model=resolved_model,
                status="skipped",
                error="AUTORESEARCH_LLM_API_KEY or OPENAI_API_KEY is not configured",
            )
            for card in selected
        ]
    if not resolved_model:
        return [
            LLMExtractionRecord(
                title=card.title,
                status="skipped",
                error="AUTORESEARCH_LLM_MODEL or --llm-model is not configured",
            )
            for card in selected
        ]

    records: list[LLMExtractionRecord] = []
    for card in selected:
        evidence_pack = _evidence_pack(card)
        if not evidence_pack:
            records.append(
                LLMExtractionRecord(
                    title=card.title,
                    model=resolved_model,
                    status="skipped",
                    error="no evidence snippets available for grounded extraction",
                )
            )
            continue
        try:
            payload = _call_openai_compatible(
                _prompt(card, evidence_pack),
                model=resolved_model,
                timeout=timeout,
            )
            patch = LLMCardPatch.model_validate(payload)
            records.append(apply_llm_patch(card, patch, evidence_pack, model=resolved_model))
        except (httpx.HTTPError, KeyError, json.JSONDecodeError, ValidationError) as exc:
            records.append(
                LLMExtractionRecord(
                    title=card.title,
                    model=resolved_model,
                    status="failed",
                    error=str(exc),
                )
            )
    return records
