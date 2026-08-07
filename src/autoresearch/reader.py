from __future__ import annotations

import re

from .domain_profile import load_domain_profile
from .schema import (
    CapabilityDimension,
    DomainProfile,
    EvidenceSnippet,
    FullTextRecord,
    PaperCard,
    PaperInfluence,
    RankedPaper,
    TextSection,
)
from .utils import clean_text, slugify

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

GENERIC_METRIC_PATTERNS = [
    r"accuracy",
    r"F1",
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


def _profile_patterns(keywords: list[str]) -> list[str]:
    return [re.escape(keyword) for keyword in keywords if keyword]


def _profile_term_hits(text: str, keywords: list[str]) -> list[str]:
    hits = []
    for keyword in keywords:
        if keyword and re.search(re.escape(keyword), text, re.IGNORECASE):
            hits.append(keyword)
    return hits


def capability_tag(name: str) -> str:
    return f"capability:{slugify(name)}"


def _dimension_covered(text: str, dimension: CapabilityDimension) -> bool:
    if dimension.keyword_groups:
        return all(
            any(keyword and re.search(re.escape(keyword), text, re.IGNORECASE) for keyword in group)
            for group in dimension.keyword_groups
        )
    return any(
        keyword and re.search(re.escape(keyword), text, re.IGNORECASE)
        for keyword in dimension.keywords
    )


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
    profile: DomainProfile,
) -> list[str]:
    tags: list[str] = []
    if _has_any(text, TEMPORAL_PATTERNS):
        tags.append("temporal_or_change")
    if profile.domain_id == "medical-vlm" and _has_any(text, LESION_PATTERNS):
        tags.append("lesion_or_localization")
    elif profile.domain_id != "medical-vlm" and _has_any(
        text,
        [r"\blocali[sz]ation\b", r"\bgrounding\b", r"\bmask\b", r"\bregion\b"],
    ):
        tags.append("localization_or_grounding")
    benchmark_patterns = [*BENCHMARK_PATTERNS, *_profile_patterns(profile.benchmark_keywords)]
    if _has_any(text, benchmark_patterns):
        tags.append("benchmark_or_evaluation")
    for dimension in profile.capability_dimensions:
        if _dimension_covered(text, dimension):
            tags.append(capability_tag(dimension.name))
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
    return list(dict.fromkeys(tags))


def _problem_for(task: str, coverage_tags: list[str], profile: DomainProfile) -> str:
    for dimension in profile.capability_dimensions:
        if capability_tag(dimension.name) in coverage_tags:
            return dimension.name
    if profile.domain_id != "medical-vlm":
        if "benchmark_or_evaluation" in coverage_tags:
            return f"{profile.domain_name} benchmark and evaluation"
        return f"general {profile.domain_name} capability"
    if "temporal_or_change" in coverage_tags and "lesion_or_localization" in coverage_tags:
        return "lesion-level temporal change reasoning"
    if "temporal_or_change" in coverage_tags:
        return "longitudinal or temporal medical image understanding"
    if "lesion_or_localization" in coverage_tags:
        return "lesion or finding localization in medical multimodal tasks"
    if task == "medical report generation":
        return "clinical report generation and textual finding description"
    if task in {"diagnosis/classification", "visual question answering"}:
        return "single-study medical VLM diagnosis or question answering"
    if "benchmark_or_evaluation" in coverage_tags:
        return "medical AI evaluation and benchmark construction"
    return f"general {profile.domain_name} capability"


def _method_family_for(method: str, model_type: str, profile: DomainProfile) -> str:
    if "mask" in method:
        if profile.domain_id == "medical-vlm":
            return "lesion- or region-guided modeling"
        return "region- or interface-grounded modeling"
    if "instruction" in method:
        return "instruction-tuned multimodal modeling"
    if "contrastive" in method or "alignment" in method:
        return "contrastive vision-language alignment"
    if "retrieval" in method:
        return "retrieval-augmented multimodal modeling"
    if "vision-language" in method or "multimodal" in model_type:
        if profile.domain_id == "medical-vlm":
            return "medical vision-language foundation model"
        return f"{profile.domain_name} multimodal or agent model"
    return "method family not explicit"


def _core_assumption_for(task: str, coverage_tags: list[str], profile: DomainProfile) -> str:
    covered = [
        dimension.name
        for dimension in profile.capability_dimensions
        if capability_tag(dimension.name) in coverage_tags
    ]
    if covered:
        return f"{covered[0]} can serve as a proxy for the target {profile.domain_name} workflow."
    if profile.domain_id != "medical-vlm":
        if "benchmark_or_evaluation" in coverage_tags:
            return f"benchmark performance transfers to the target {profile.domain_name} workflow."
        return f"broad {profile.domain_name} performance transfers to the target research workflow."
    if "temporal_or_change" in coverage_tags and "lesion_or_localization" in coverage_tags:
        return "localized findings can serve as anchors for comparing disease state across time."
    if "temporal_or_change" in coverage_tags:
        return "temporal clinical change can be captured without always requiring explicit lesion anchors."
    if "lesion_or_localization" in coverage_tags:
        return "static lesion or region grounding is a useful proxy for downstream clinical reasoning."
    if task == "medical report generation":
        return "report text quality is a sufficient proxy for clinically meaningful visual understanding."
    if task in {"diagnosis/classification", "visual question answering"}:
        return "single-study recognition performance transfers to richer clinical reasoning workflows."
    return f"broad {profile.domain_name} performance transfers to the target research workflow."


def _evidence_type_for(
    evidence_source: str,
    datasets: list[str],
    metrics: list[str],
    coverage_tags: list[str],
) -> str:
    parts = ["full-text section evidence" if evidence_source == "full text" else "abstract/metadata evidence"]
    if datasets:
        parts.append("dataset named")
    if metrics:
        parts.append("metric named")
    if "benchmark_or_evaluation" in coverage_tags:
        parts.append("evaluation signal present")
    return "; ".join(parts)


def _missing_capability_for(coverage_tags: list[str], profile: DomainProfile) -> str:
    missing = []
    for dimension in profile.capability_dimensions:
        if dimension.required and capability_tag(dimension.name) not in coverage_tags:
            missing.append(dimension.name)
    if profile.domain_id == "medical-vlm":
        if "temporal_or_change" not in coverage_tags:
            missing.append("explicit temporal/change reasoning")
        if "lesion_or_localization" not in coverage_tags:
            missing.append("lesion-level localization or grounding")
    if "metric_missing" in coverage_tags:
        missing.append("capability-specific metrics")
    if "dataset_missing" in coverage_tags:
        missing.append("explicit dataset or benchmark context")
    return "; ".join(dict.fromkeys(missing)) if missing else "not obvious from extracted metadata"


def _relation_to_topic_for(coverage_tags: list[str], profile: DomainProfile) -> str:
    covered = [
        dimension.name
        for dimension in profile.capability_dimensions
        if capability_tag(dimension.name) in coverage_tags
    ]
    if covered:
        return f"direct evidence for {', '.join(covered[:2])} in the {profile.domain_name} profile"
    has_temporal = "temporal_or_change" in coverage_tags
    has_lesion = "lesion_or_localization" in coverage_tags
    has_localization = "localization_or_grounding" in coverage_tags
    if profile.domain_id != "medical-vlm":
        if has_temporal and has_localization:
            return f"candidate evidence for temporal and grounded {profile.domain_name} workflows"
        if has_temporal:
            return f"temporal or long-horizon candidate for the {profile.domain_name} profile"
        if has_localization:
            return f"grounding or localization candidate for the {profile.domain_name} profile"
        if "benchmark_or_evaluation" in coverage_tags:
            return "evaluation context that may expose benchmark coverage gaps"
        return f"background or adjacent {profile.domain_name} evidence"
    if has_temporal and has_lesion:
        return "direct candidate for the target problem space"
    if has_temporal:
        return "temporal candidate that needs lesion-level grounding comparison"
    if has_lesion:
        return "localization candidate that needs paired temporal comparison"
    if "benchmark_or_evaluation" in coverage_tags:
        return "evaluation context that may expose benchmark coverage gaps"
    return f"background or adjacent {profile.domain_name} evidence"


def _gap_hint_for(
    problem: str,
    missing_capability: str,
    coverage_tags: list[str],
    profile: DomainProfile,
) -> str:
    if profile.domain_id != "medical-vlm":
        if "not obvious" in missing_capability:
            return (
                f"Audit whether {problem} is truly evaluated under the target "
                f"{profile.domain_name} workflow."
            )
        if "capability-specific metrics" in missing_capability:
            return (
                "The paper may support a gap around metrics that miss the target "
                f"{profile.domain_name} capability."
            )
        if "explicit dataset" in missing_capability:
            return "The paper may support a gap around benchmark comparability and dataset transparency."
        if "metric_explicit" in coverage_tags and "dataset_explicit" in coverage_tags:
            return "Use this paper as possible counter-evidence when testing whether the gap still holds."
        return "Use this paper to refine the problem-space map before claiming a gap."
    if "not obvious" in missing_capability:
        return f"Audit whether {problem} is truly evaluated under the target clinical workflow."
    if "temporal/change" in missing_capability and "lesion-level" in missing_capability:
        return "The paper may support a gap around missing lesion-grounded temporal reasoning."
    if "temporal/change" in missing_capability:
        return "The paper may support a gap between static localization and temporal lesion tracking."
    if "lesion-level" in missing_capability:
        return "The paper may support a gap between longitudinal modeling and localized lesion comparison."
    if "capability-specific metrics" in missing_capability:
        return "The paper may support a gap around evaluation metrics that miss fine-grained clinical change."
    if "explicit dataset" in missing_capability:
        return "The paper may support a gap around benchmark comparability and dataset transparency."
    if "metric_explicit" in coverage_tags and "dataset_explicit" in coverage_tags:
        return "Use this paper as possible counter-evidence when testing whether the gap still holds."
    return "Use this paper to refine the problem-space map before claiming a gap."


def build_paper_cards(
    ranked: list[RankedPaper],
    full_texts: dict[str, FullTextRecord] | None = None,
    influences: dict[str, PaperInfluence] | None = None,
    profile: DomainProfile | None = None,
) -> list[PaperCard]:
    full_texts = full_texts or {}
    influences = influences or {}
    profile = profile or load_domain_profile("medical-vlm", "")
    profile_task_patterns = [
        (pattern, keyword)
        for pattern, keyword in zip(
            _profile_patterns(profile.task_keywords),
            profile.task_keywords,
            strict=False,
        )
    ]
    task_patterns = (
        [*TASK_PATTERNS, *profile_task_patterns]
        if profile.domain_id == "medical-vlm"
        else profile_task_patterns
    )
    method_patterns = [
        *METHOD_PATTERNS,
        *[(pattern, keyword) for pattern, keyword in zip(_profile_patterns(profile.method_keywords), profile.method_keywords, strict=False)],
    ]
    dataset_patterns = (
        [*DATASET_PATTERNS, *_profile_patterns([*profile.dataset_keywords, *profile.benchmark_keywords])]
        if profile.domain_id == "medical-vlm"
        else _profile_patterns([*profile.dataset_keywords, *profile.benchmark_keywords])
    )
    metric_patterns = (
        [*METRIC_PATTERNS, *_profile_patterns(profile.metric_keywords)]
        if profile.domain_id == "medical-vlm"
        else [*GENERIC_METRIC_PATTERNS, *_profile_patterns(profile.metric_keywords)]
    )
    cards: list[PaperCard] = []
    for row in ranked:
        paper = row.paper
        full_text = full_texts.get(paper.title)
        extracted_text, evidence_source = _source_text(paper.abstract, full_text)
        text = f"{paper.title} {paper.abstract} {extracted_text}"
        task = _first_match(text, task_patterns, f"general {profile.domain_name} research")
        method = _first_match(text, method_patterns, "not explicit in abstract")
        datasets = _profile_term_hits(text, profile.dataset_keywords)
        if not datasets and profile.domain_id == "medical-vlm":
            datasets = _find_terms(text, DATASET_PATTERNS)
        metrics = _profile_term_hits(text, profile.metric_keywords)
        if not metrics:
            fallback_metric_patterns = (
                METRIC_PATTERNS if profile.domain_id == "medical-vlm" else GENERIC_METRIC_PATTERNS
            )
            metrics = _find_terms(text, fallback_metric_patterns)
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
            [*task_patterns, *method_patterns, *dataset_patterns, *metric_patterns],
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
            "task": _evidence_for_field(
                paper.title, paper.url, full_text, paper.abstract, "task", task_patterns
            ),
            "method": _evidence_for_field(
                paper.title, paper.url, full_text, paper.abstract, "method", method_patterns
            ),
            "dataset": _evidence_for_field(
                paper.title, paper.url, full_text, paper.abstract, "dataset", dataset_patterns
            ),
            "metrics": _evidence_for_field(
                paper.title, paper.url, full_text, paper.abstract, "metrics", metric_patterns
            ),
        }
        field_evidence = {key: value for key, value in field_evidence.items() if value}
        dataset_value = ", ".join(datasets) if datasets else "not explicit"
        metric_value = ", ".join(metrics) if metrics else "not explicit"
        model_type = (
            (
                "medical VLM / multimodal model"
                if profile.domain_id == "medical-vlm"
                else f"{profile.domain_name} multimodal or agent model"
            )
            if re.search(r"(vlm|vision-language|multimodal)", text, re.IGNORECASE)
            else "not explicit"
        )
        coverage_tags = _coverage_tags(text, datasets, metrics, limitation, evidence_source, profile)
        problem = _problem_for(task, coverage_tags, profile)
        method_family = _method_family_for(method, model_type, profile)
        core_assumption = _core_assumption_for(task, coverage_tags, profile)
        evidence_type = _evidence_type_for(evidence_source, datasets, metrics, coverage_tags)
        missing_capability = _missing_capability_for(coverage_tags, profile)
        relation_to_topic = _relation_to_topic_for(coverage_tags, profile)
        gap_hint = _gap_hint_for(problem, missing_capability, coverage_tags, profile)
        cards.append(
            PaperCard(
                title=paper.title,
                year=paper.year,
                venue=paper.venue,
                url=paper.url,
                problem=problem,
                task=task,
                method=method,
                method_family=method_family,
                core_assumption=core_assumption,
                evidence_type=evidence_type,
                dataset=dataset_value,
                metrics=metric_value,
                model_type=model_type,
                claimed_contribution=contribution,
                limitation=limitation,
                missing_capability=missing_capability,
                relation_to_topic=relation_to_topic,
                gap_hint=gap_hint,
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
                    "problem": _status_for(problem, inferred=True),
                    "method_family": _status_for(method_family, inferred=True),
                    "core_assumption": _status_for(core_assumption, inferred=True),
                    "missing_capability": _status_for(missing_capability, inferred=True),
                    "gap_hint": _status_for(gap_hint, inferred=True),
                },
                coverage_tags=coverage_tags,
                influence=influences.get(paper.title),
            )
        )
    return cards
