from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class QueryPlan(BaseModel):
    topic: str
    queries: list[str]
    perspectives: list[str]


class CapabilityDimension(BaseModel):
    name: str
    keywords: list[str] = Field(default_factory=list)
    keyword_groups: list[list[str]] = Field(default_factory=list)
    description: str = ""
    required: bool = True


class SourcePolicy(BaseModel):
    preferred_sources: list[str] = Field(default_factory=list)
    neutral_sources: list[str] = Field(default_factory=list)
    downrank_sources: list[str] = Field(default_factory=list)
    disabled_sources: list[str] = Field(default_factory=list)
    source_weight_overrides: dict[str, float] = Field(default_factory=dict)


class EvidencePolicy(BaseModel):
    core_keywords: list[str] = Field(default_factory=list)
    adjacent_keywords: list[str] = Field(default_factory=list)
    negative_keywords: list[str] = Field(default_factory=list)


class DomainProfile(BaseModel):
    domain_id: str
    domain_name: str
    seed_topic: str = ""
    description: str = ""
    core_concepts: list[str] = Field(default_factory=list)
    query_terms: list[str] = Field(default_factory=list)
    task_keywords: list[str] = Field(default_factory=list)
    method_keywords: list[str] = Field(default_factory=list)
    dataset_keywords: list[str] = Field(default_factory=list)
    benchmark_keywords: list[str] = Field(default_factory=list)
    metric_keywords: list[str] = Field(default_factory=list)
    capability_dimensions: list[CapabilityDimension] = Field(default_factory=list)
    gap_lenses: list[str] = Field(default_factory=list)
    source_policy: SourcePolicy = Field(default_factory=SourcePolicy)
    evidence_policy: EvidencePolicy = Field(default_factory=EvidencePolicy)
    generated_by: str = "rule_based"


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


class OpenAccessRecord(BaseModel):
    title: str
    doi: str = ""
    source: str = "unpaywall"
    status: str = "not_attempted"
    is_open_access: bool = False
    landing_page_url: str = ""
    pdf_url: str = ""
    evidence: str = ""
    error: str = ""


class SourceReadiness(BaseModel):
    status: str = "not_evaluated"
    ranked_papers: int = 0
    contributing_sources: int = 0
    moc_groups: int = 0
    reasons: list[str] = Field(default_factory=list)
    failed_sources: list[str] = Field(default_factory=list)


class LLMExtractionRecord(BaseModel):
    title: str
    provider: str = "openai-compatible"
    model: str = ""
    status: str = "not_attempted"
    fields_updated: list[str] = Field(default_factory=list)
    evidence_refs: dict[str, list[str]] = Field(default_factory=dict)
    error: str = ""


class PaperCard(BaseModel):
    title: str
    year: int | None = None
    venue: str = ""
    url: str = ""
    problem: str = ""
    task: str = ""
    method: str = ""
    method_family: str = ""
    core_assumption: str = ""
    evidence_type: str = ""
    dataset: str = ""
    metrics: str = ""
    model_type: str = ""
    claimed_contribution: str = ""
    limitation: str = ""
    missing_capability: str = ""
    relation_to_topic: str = ""
    gap_hint: str = ""
    relevance_score: float = 0.0
    score_reasons: list[str] = Field(default_factory=list)
    evidence_snippets: list[EvidenceSnippet] = Field(default_factory=list)
    field_evidence: dict[str, EvidenceSnippet] = Field(default_factory=dict)
    extraction_status: dict[str, str] = Field(default_factory=dict)
    coverage_tags: list[str] = Field(default_factory=list)
    influence: PaperInfluence | None = None


class PaperInsightCard(BaseModel):
    title: str
    url: str = ""
    group: str = ""
    problem: str = ""
    method_core: str = ""
    evidence: str = ""
    assumption: str = ""
    limitation: str = ""
    relation_to_others: list[str] = Field(default_factory=list)
    inspiration: str = ""
    experimentable_gap: str = ""
    evidence_snippet: EvidenceSnippet | None = None


class FieldMap(BaseModel):
    task_clusters: dict[str, list[str]] = Field(default_factory=dict)
    method_clusters: dict[str, list[str]] = Field(default_factory=dict)
    datasets: dict[str, list[str]] = Field(default_factory=dict)
    metrics: dict[str, list[str]] = Field(default_factory=dict)
    model_types: dict[str, list[str]] = Field(default_factory=dict)
    coverage_notes: list[str] = Field(default_factory=list)


class TopicMOC(BaseModel):
    topic: str
    core_concepts: list[str] = Field(default_factory=list)
    paper_groups: dict[str, list[str]] = Field(default_factory=dict)
    problem_spaces: list[MOCGroup] = Field(default_factory=list)
    common_method_patterns: list[str] = Field(default_factory=list)
    shared_assumptions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    related_themes: list[str] = Field(default_factory=list)


class MOCGroup(BaseModel):
    name: str
    problem_space: str = ""
    representative_papers: list[str] = Field(default_factory=list)
    shared_assumptions: list[str] = Field(default_factory=list)
    method_families: list[str] = Field(default_factory=list)
    datasets_or_benchmarks: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    covered_capabilities: list[str] = Field(default_factory=list)
    missing_capabilities: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    possible_experiments: list[str] = Field(default_factory=list)
    evidence: list[EvidenceSnippet] = Field(default_factory=list)


class ComparisonRow(BaseModel):
    group: str
    problem: str = ""
    representative_papers: list[str] = Field(default_factory=list)
    method_families: list[str] = Field(default_factory=list)
    uses_temporal_input: str = "not explicit"
    uses_lesion_localization: str = "not explicit"
    evaluates_change: str = "not explicit"
    evaluates_location_consistency: str = "not explicit"
    solves: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    benchmark_or_metrics: list[str] = Field(default_factory=list)
    gap_hints: list[str] = Field(default_factory=list)
    evidence: list[EvidenceSnippet] = Field(default_factory=list)


class ComparisonMatrix(BaseModel):
    rows: list[ComparisonRow] = Field(default_factory=list)


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


class GapEvidenceStep(BaseModel):
    paper_title: str
    source_url: str = ""
    role: str = "support"
    claim: str = ""
    missing_dimensions: list[str] = Field(default_factory=list)
    evidence: EvidenceSnippet | None = None


class GapEvidence(BaseModel):
    gap: str
    evidence: list[EvidenceSnippet] = Field(default_factory=list)
    counter_evidence: list[EvidenceSnippet] = Field(default_factory=list)
    evidence_chain: list[GapEvidenceStep] = Field(default_factory=list)
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


class ResearchOpportunity(BaseModel):
    gap: str
    research_question: str = ""
    hypothesis: str = ""
    proposed_method: str = ""
    innovations_bound_to_gap: list[str] = Field(default_factory=list)
    required_data: str = ""
    evaluation_protocol: list[str] = Field(default_factory=list)
    baselines: list[str] = Field(default_factory=list)
    ablations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class SynthesisGapSummary(BaseModel):
    gap: str
    judgment: str = ""
    support: str = ""
    counter_evidence: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class SynthesisReport(BaseModel):
    mode: str = "codex_substituted_llm"
    status: str = "draft"
    executive_summary: str = ""
    domain_interpretation: str = ""
    search_assessment: str = ""
    moc_takeaways: list[str] = Field(default_factory=list)
    gap_summaries: list[SynthesisGapSummary] = Field(default_factory=list)
    recommended_opportunities: list[str] = Field(default_factory=list)
    evidence_quality: str = ""
    limitations: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class SearchArtifacts(BaseModel):
    topic: str
    generated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )
    domain_profile: DomainProfile | None = None
    query_plan: QueryPlan
    source_statuses: list[SourceStatus]
    ranked_papers: list[RankedPaper]
    full_texts: list[FullTextRecord] = Field(default_factory=list)
    influences: list[PaperInfluence] = Field(default_factory=list)
    open_access_records: list[OpenAccessRecord] = Field(default_factory=list)
    llm_extractions: list[LLMExtractionRecord] = Field(default_factory=list)
    source_readiness: SourceReadiness | None = None
    paper_cards: list[PaperCard]
    paper_insights: list[PaperInsightCard] = Field(default_factory=list)
    field_map: FieldMap
    topic_moc: TopicMOC | None = None
    comparison_matrix: ComparisonMatrix | None = None
    gaps: list[GapEvidence]
    research_opportunities: list[ResearchOpportunity] = Field(default_factory=list)
    synthesis: SynthesisReport | None = None
    warnings: list[str] = Field(default_factory=list)

    def write_json(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "search_result.json").write_text(
            self.model_dump_json(indent=2), encoding="utf-8"
        )
        if self.domain_profile:
            (output_dir / "domain_profile.json").write_text(
                self.domain_profile.model_dump_json(indent=2), encoding="utf-8"
            )
        if self.synthesis:
            (output_dir / "synthesis.json").write_text(
                self.synthesis.model_dump_json(indent=2), encoding="utf-8"
            )
        (output_dir / "paper_cards.json").write_text(
            self.model_dump_json(include={"paper_cards"}, indent=2), encoding="utf-8"
        )
        (output_dir / "paper_insights.json").write_text(
            "[" + ",\n".join(row.model_dump_json(indent=2) for row in self.paper_insights) + "]\n",
            encoding="utf-8",
        )
        (output_dir / "influences.json").write_text(
            "[" + ",\n".join(row.model_dump_json(indent=2) for row in self.influences) + "]\n",
            encoding="utf-8",
        )
        (output_dir / "open_access.json").write_text(
            "[" + ",\n".join(row.model_dump_json(indent=2) for row in self.open_access_records) + "]\n",
            encoding="utf-8",
        )
        (output_dir / "llm_extractions.json").write_text(
            "[" + ",\n".join(row.model_dump_json(indent=2) for row in self.llm_extractions) + "]\n",
            encoding="utf-8",
        )
        (output_dir / "field_map.json").write_text(
            self.field_map.model_dump_json(indent=2), encoding="utf-8"
        )
        if self.topic_moc:
            (output_dir / "topic_moc.json").write_text(
                self.topic_moc.model_dump_json(indent=2), encoding="utf-8"
            )
        if self.comparison_matrix:
            (output_dir / "comparison_matrix.json").write_text(
                self.comparison_matrix.model_dump_json(indent=2), encoding="utf-8"
            )
        (output_dir / "gaps.json").write_text(
            "[" + ",\n".join(gap.model_dump_json(indent=2) for gap in self.gaps) + "]\n",
            encoding="utf-8",
        )
        (output_dir / "research_opportunities.json").write_text(
            "["
            + ",\n".join(row.model_dump_json(indent=2) for row in self.research_opportunities)
            + "]\n",
            encoding="utf-8",
        )
