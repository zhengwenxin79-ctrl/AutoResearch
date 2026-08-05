from __future__ import annotations

import re

from .schema import EvidenceSnippet, PaperCard, RankedPaper
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


def _snippet_for(title: str, url: str, abstract: str, claim: str) -> EvidenceSnippet:
    return EvidenceSnippet(
        paper_title=title,
        source_url=url,
        claim=claim,
        snippet=clean_text(abstract, 420),
    )


def build_paper_cards(ranked: list[RankedPaper]) -> list[PaperCard]:
    cards: list[PaperCard] = []
    for row in ranked:
        paper = row.paper
        text = " ".join([paper.title, paper.abstract])
        task = _first_match(text, TASK_PATTERNS, "general medical AI / multimodal research")
        method = _first_match(text, METHOD_PATTERNS, "not explicit in abstract")
        datasets = _find_terms(text, DATASET_PATTERNS)
        metrics = _find_terms(text, METRIC_PATTERNS)
        limitation = ""
        if re.search(r"\b(single|static|one-time|cross-sectional)\b", text, flags=re.IGNORECASE):
            limitation = "appears to emphasize single-timepoint/static analysis"
        elif not datasets:
            limitation = "dataset/evaluation details are not explicit in metadata or abstract"
        contribution = clean_text(paper.abstract, 260)
        evidence = [
            _snippet_for(paper.title, paper.url, paper.abstract, "task/method evidence from abstract")
        ] if paper.abstract else []
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

