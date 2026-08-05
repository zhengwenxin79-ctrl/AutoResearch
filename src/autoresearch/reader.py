from __future__ import annotations

import re

from .schema import EvidenceSnippet, FullTextRecord, PaperCard, RankedPaper, TextSection
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


def build_paper_cards(
    ranked: list[RankedPaper],
    full_texts: dict[str, FullTextRecord] | None = None,
) -> list[PaperCard]:
    full_texts = full_texts or {}
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
        evidence = [
            _snippet_for(
                paper.title,
                paper.url,
                evidence_text,
                f"task/method evidence from {evidence_source}",
                section=section,
            )
        ] if evidence_text else []
        cards.append(
            PaperCard(
                title=paper.title,
                year=paper.year,
                venue=paper.venue,
                url=paper.url,
                task=task,
                method=method,
                dataset=", ".join(datasets) if datasets else "not explicit",
                metrics=", ".join(metrics) if metrics else "not explicit",
                model_type="medical VLM / multimodal model"
                if re.search(r"(vlm|vision-language|multimodal)", text, re.IGNORECASE)
                else "not explicit",
                claimed_contribution=contribution,
                limitation=limitation,
                relevance_score=row.relevance_score,
                score_reasons=row.score_reasons,
                evidence_snippets=evidence,
            )
        )
    return cards
