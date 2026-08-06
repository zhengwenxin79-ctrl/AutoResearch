from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class QueryPlan(BaseModel):
    topic: str
    queries: list[str]
    perspectives: list[str]


class SourceStatus(BaseModel):
    source: str
    query: str
    status: str
    raw_count: int = 0
    error: str = ""


class PaperRecord(BaseModel):
    title: str
    abstract: str = ""
    year: int | None = None
    venue: str = ""
    authors: list[str] = Field(default_factory=list)
    url: str = ""
    pdf_url: str = ""
    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    arxiv_id: str = ""
    openalex_id: str = ""
    citation_count: int = 0
    source: str = ""
    source_records: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class RankedPaper(BaseModel):
    paper: PaperRecord
    relevance_score: float
    score_reasons: list[str] = Field(default_factory=list)


class EvidenceSnippet(BaseModel):
    paper_title: str
    source_url: str
    claim: str
    snippet: str
    section: str = ""


class TextSection(BaseModel):
    heading: str
    text: str


class FullTextRecord(BaseModel):
    title: str
    source_url: str = ""
    fetched_url: str = ""
    raw_path: str = ""
    text_path: str = ""
    status: str = "not_attempted"
    content_type: str = ""
    sections: list[TextSection] = Field(default_factory=list)
    error: str = ""


class PaperInfluence(BaseModel):
    source: str = ""
    paper_id: str = ""
    url: str = ""
    citation_count: int = 0
    influential_citation_count: int = 0
    reference_count: int = 0
    venue: str = ""
    is_open_access: bool = False
    open_access_pdf: str = ""
    fields_of_study: list[str] = Field(default_factory=list)
    tldr: str = ""
    status: str = "not_attempted"
    error: str = ""


class PaperCard(BaseModel):
    title: str
    year: int | None = None
    venue: str = ""
    url: str = ""
    task: str = ""
    method: str = ""
    dataset: str = ""
    metrics: str = ""
    model_type: str = ""
    claimed_contribution: str = ""
    limitation: str = ""
    relevance_score: float = 0.0
    score_reasons: list[str] = Field(default_factory=list)
    evidence_snippets: list[EvidenceSnippet] = Field(default_factory=list)
    field_evidence: dict[str, EvidenceSnippet] = Field(default_factory=dict)
    extraction_status: dict[str, str] = Field(default_factory=dict)
    coverage_tags: list[str] = Field(default_factory=list)
    influence: PaperInfluence | None = None


class FieldMap(BaseModel):
    task_clusters: dict[str, list[str]] = Field(default_factory=dict)
    method_clusters: dict[str, list[str]] = Field(default_factory=dict)
    datasets: dict[str, list[str]] = Field(default_factory=dict)
    metrics: dict[str, list[str]] = Field(default_factory=dict)
    model_types: dict[str, list[str]] = Field(default_factory=dict)
    coverage_notes: list[str] = Field(default_factory=list)


class GapPaperJudgment(BaseModel):
    paper_title: str
    source_url: str
    decision: str = "unclear"
    role: str = "unclear"
    rationale: str = ""
    evidence: EvidenceSnippet | None = None
    missing_evidence: list[str] = Field(default_factory=list)
    influence_score: float = 0.0
    influence_reasons: list[str] = Field(default_factory=list)


class GapEvidence(BaseModel):
    gap: str
    evidence: list[EvidenceSnippet] = Field(default_factory=list)
    counter_evidence: list[EvidenceSnippet] = Field(default_factory=list)
    confidence: float = 0.0
    support_count: int = 0
    counter_count: int = 0
    unclear_count: int = 0
    total_papers: int = 0
    support_ratio: float = 0.0
    counter_ratio: float = 0.0
    full_text_evidence_count: int = 0
    score_reasons: list[str] = Field(default_factory=list)
    paper_judgments: list[GapPaperJudgment] = Field(default_factory=list)
    why_it_matters: str = ""
    research_opportunity: str = ""


class SearchArtifacts(BaseModel):
    topic: str
    generated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )
    query_plan: QueryPlan
    source_statuses: list[SourceStatus]
    ranked_papers: list[RankedPaper]
    full_texts: list[FullTextRecord] = Field(default_factory=list)
    influences: list[PaperInfluence] = Field(default_factory=list)
    paper_cards: list[PaperCard]
    field_map: FieldMap
    gaps: list[GapEvidence]
    warnings: list[str] = Field(default_factory=list)

    def write_json(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "search_result.json").write_text(
            self.model_dump_json(indent=2), encoding="utf-8"
        )
        (output_dir / "paper_cards.json").write_text(
            self.model_dump_json(include={"paper_cards"}, indent=2), encoding="utf-8"
        )
        (output_dir / "influences.json").write_text(
            "[" + ",\n".join(row.model_dump_json(indent=2) for row in self.influences) + "]\n",
            encoding="utf-8",
        )
        (output_dir / "field_map.json").write_text(
            self.field_map.model_dump_json(indent=2), encoding="utf-8"
        )
        (output_dir / "gaps.json").write_text(
            "[" + ",\n".join(gap.model_dump_json(indent=2) for gap in self.gaps) + "]\n",
            encoding="utf-8",
        )
