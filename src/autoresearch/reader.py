from __future__ import annotations

import re

from .schema import (
    EvidenceSnippet,
    FullTextRecord,
    PaperCard,
    PaperInfluence,
    RankedPaper,
    TextSection,
)
from .utils import clean_text

TASK_PATTERNS = [
    (r"(temporal|longitudinal|change).{0,80}(analysis|detection|reasoning)", "temporal change analysis"),
    (r"(visual question answering|vqa)", "visual question answering"),
    (r"(report generation|radiology report)", "medical report generation"),
    (r"(segmentation|lesion mask)", "lesion segmentation/localization"),
    (r"(diagnosis|classification)", "diagnosis/classification"),
]

METHOD_PATTERNS = [
    (r"(vision-language|vlm|multimodal large language)", "vision-language model"),
    (r"(instruction tuning|fine-tuning)", "instruction tuning"),
    (r"(contrastive|alignment)", "contrastive/alignment learning"),
    (r"(retrieval|rag)", "retrieval-augmented method"),
    (r"(segmentation|mask-guided|mask guided)", "mask-guided modeling"),
]

DATASET_PATTERNS = [
    r"MIMIC[- ]?CXR",
    r"CheXpert",
    r"PadChest",
    r"NIH ChestXray14",
    r"BraTS",
    r"DeepLesion",
    r"RadImageNet",
    r"PMC[- ]?VQA",
    r"ROCO",
]

METRIC_PATTERNS = [
    r"accuracy",
    r"AUC",
    r"F1",
    r"BLEU",
    r"ROUGE",
    r"BERTScore",
    r"Dice",
    r"IoU",
]

TEMPORAL_PATTERNS = [
    r"\btemporal\b",
    r"\blongitudinal\b",
    r"\bfollow[- ]?up\b",
    r"\bchange\b",
    r"\bprogression\b",
]

LESION_PATTERNS = [
    r"\blesion\b",
    r"\bfinding\b",
    r"\blocali[sz]ation\b",
    r"\bsegmentation\b",
    r"\bmask\b",
]

BENCHMARK_PATTERNS = [
    r"\bbenchmark\b",
    r"\bdataset\b",
    r"\bevaluation\b",
    r"\bbaseline\b",
]

SECTION_PRIORITY = {
    "methods": 5,
    "method": 5,
    "materials and methods": 5,
    "experiments": 4,
    "experimental setup": 4,
    "evaluation": 4,
    "results": 3,
    "discussion": 2,
    "limitations": 2,
    "limitation": 2,
    "abstract": 1,
    "body": 0,
}


def _first_match(text: str, patterns: list[tuple[str, str]], fallback: str) -> str:
    lowered = text.lower()
    for pattern, label in patterns:
        if re.search(pattern, lowered, flags=re.IGNORECASE):
            return label
    return fallback


def _find_terms(text: str, patterns: list[str]) -> list[str]:
    hits = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(re.sub(r"\\", "", pattern).replace("[- ]?", "-"))
    return hits


def _snippet_for(title: str, url: str, text: str, claim: str, section: str = "") -> EvidenceSnippet:
    return EvidenceSnippet(
        paper_title=title,
        source_url=url,
        claim=claim,
        snippet=clean_text(text, 420),
        section=section,
    )


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _section_text(full_text: FullTextRecord | None) -> str:
    if not full_text or full_text.status != "ok":
        return ""
    prioritized = sorted(
        full_text.sections,
        key=lambda section: SECTION_PRIORITY.get(section.heading.lower(), 0),
        reverse=True,
    )
    return " ".join(section.text for section in prioritized[:8])


def _best_section(
    full_text: FullTextRecord | None,
    patterns: list[str] | list[tuple[str, str]],
) -> TextSection | None:
    if not full_text or full_text.status != "ok":
        return None
    regexes = [item[0] if isinstance(item, tuple) else item for item in patterns]
    sections = sorted(
        full_text.sections,
        key=lambda section: SECTION_PRIORITY.get(section.heading.lower(), 0),
        reverse=True,
    )
    for section in sections:
        if any(re.search(pattern, section.text, re.IGNORECASE) for pattern in regexes):
            return section
    return sections[0] if sections else None


def _source_text(paper_abstract: str, full_text: FullTextRecord | None) -> tuple[str, str]:
    full = _section_text(full_text)
    if full:
        return full, "full text"
    return paper_abstract, "abstract"


def _evidence_for_field(
    paper_title: str,
    paper_url: str,
    full_text: FullTextRecord | None,
    abstract: str,
    field: str,
    patterns: list[str] | list[tuple[str, str]],
) -> EvidenceSnippet | None:
    section = _best_section(full_text, patterns)
    if section:
        return _snippet_for(
            paper_title,
            paper_url,
            section.text,
            f"{field} evidence from full text",
            section=section.heading,
        )
    if abstract:
        return _snippet_for(
            paper_title,
            paper_url,
            abstract,
            f"{field} evidence from abstract",
            section="abstract",
        )
    return None


def _status_for(value: str, inferred: bool = False) -> str:
    if value == "not explicit" or not value:
        return "not_explicit"
    return "inferred" if inferred else "explicit"


def _coverage_tags(
    text: str,
    datasets: list[str],
    metrics: list[str],
    limitation: str,
    evidence_source: str,
) -> list[str]:
    tags: list[str] = []
    if _has_any(text, TEMPORAL_PATTERNS):
        tags.append("temporal_or_change")
    if _has_any(text, LESION_PATTERNS):
        tags.append("lesion_or_localization")
    if _has_any(text, BENCHMARK_PATTERNS):
        tags.append("benchmark_or_evaluation")
    if datasets:
        tags.append("dataset_explicit")
    else:
        tags.append("dataset_missing")
    if metrics:
        tags.append("metric_explicit")
    else:
        tags.append("metric_missing")
    if "single-timepoint" in limitation or "static" in limitation:
        tags.append("static_or_single_timepoint")
    tags.append("full_text_read" if evidence_source == "full text" else "abstract_only")
    return tags


def build_paper_cards(
    ranked: list[RankedPaper],
    full_texts: dict[str, FullTextRecord] | None = None,
    influences: dict[str, PaperInfluence] | None = None,
) -> list[PaperCard]:
    full_texts = full_texts or {}
    influences = influences or {}
    cards: list[PaperCard] = []
    for row in ranked:
        paper = row.paper
        full_text = full_texts.get(paper.title)
        extracted_text, evidence_source = _source_text(paper.abstract, full_text)
        text = f"{paper.title} {paper.abstract} {extracted_text}"
        task = _first_match(text, TASK_PATTERNS, "general medical AI / multimodal research")
        method = _first_match(text, METHOD_PATTERNS, "not explicit in abstract")
        datasets = _find_terms(text, DATASET_PATTERNS)
        metrics = _find_terms(text, METRIC_PATTERNS)
        limitation = ""
        limitation_scope = " ".join([paper.title, paper.abstract, extracted_text[:5000]])
        if re.search(
            r"\b(single[- ]timepoint|single[- ]time[- ]point|single image|static analysis|one-time|cross-sectional)\b",
            limitation_scope,
            flags=re.IGNORECASE,
        ):
            limitation = "appears to emphasize single-timepoint/static analysis"
        elif not datasets:
            limitation = "dataset/evaluation details are not explicit in metadata or abstract"
        contribution = clean_text(paper.abstract or extracted_text, 260)
        best_section = _best_section(
            full_text,
            [*TASK_PATTERNS, *METHOD_PATTERNS, *DATASET_PATTERNS, *METRIC_PATTERNS],
        )
        evidence_text = best_section.text if best_section else paper.abstract
        section = best_section.heading if best_section else "abstract"
        primary_evidence = [
            _snippet_for(
                paper.title,
                paper.url,
                evidence_text,
                f"task/method evidence from {evidence_source}",
                section=section,
            )
        ] if evidence_text else []
        field_evidence = {
            "task": _evidence_for_field(paper.title, paper.url, full_text, paper.abstract, "task", TASK_PATTERNS),
            "method": _evidence_for_field(
                paper.title, paper.url, full_text, paper.abstract, "method", METHOD_PATTERNS
            ),
            "dataset": _evidence_for_field(
                paper.title, paper.url, full_text, paper.abstract, "dataset", DATASET_PATTERNS
            ),
            "metrics": _evidence_for_field(
                paper.title, paper.url, full_text, paper.abstract, "metrics", METRIC_PATTERNS
            ),
        }
        field_evidence = {key: value for key, value in field_evidence.items() if value}
        dataset_value = ", ".join(datasets) if datasets else "not explicit"
        metric_value = ", ".join(metrics) if metrics else "not explicit"
        model_type = (
            "medical VLM / multimodal model"
            if re.search(r"(vlm|vision-language|multimodal)", text, re.IGNORECASE)
            else "not explicit"
        )
        cards.append(
            PaperCard(
                title=paper.title,
                year=paper.year,
                venue=paper.venue,
                url=paper.url,
                task=task,
                method=method,
                dataset=dataset_value,
                metrics=metric_value,
                model_type=model_type,
                claimed_contribution=contribution,
                limitation=limitation,
                relevance_score=row.relevance_score,
                score_reasons=row.score_reasons,
                evidence_snippets=primary_evidence,
                field_evidence=field_evidence,
                extraction_status={
                    "task": _status_for(task, inferred=True),
                    "method": _status_for(method, inferred=True),
                    "dataset": _status_for(dataset_value),
                    "metrics": _status_for(metric_value),
                    "model_type": _status_for(model_type, inferred=True),
                    "limitation": _status_for(limitation, inferred=True),
                },
                coverage_tags=_coverage_tags(text, datasets, metrics, limitation, evidence_source),
                influence=influences.get(paper.title),
            )
        )
    return cards
