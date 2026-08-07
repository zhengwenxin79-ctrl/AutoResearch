from __future__ import annotations

from .domain_profile import load_domain_profile
from .schema import DomainProfile, QueryPlan

PERSPECTIVES = [
    "core task and problem formulation",
    "methods and model architectures",
    "datasets and benchmarks",
    "evaluation metrics and baselines",
    "limitations gaps challenges",
    "survey review recent progress",
]


def _profile_queries(topic: str, profile: DomainProfile) -> list[str]:
    queries = [topic]
    for term in profile.query_terms[:6]:
        queries.append(term)
        if term.lower() not in topic.lower():
            queries.append(f"{topic} {term}")
    for dimension in profile.capability_dimensions[:4]:
        if dimension.name.lower() not in topic.lower():
            queries.append(f"{topic} {dimension.name}")
    for keyword in [*profile.benchmark_keywords[:3], *profile.metric_keywords[:2]]:
        queries.append(f"{topic} {keyword}")
    return queries


def plan_queries(topic: str, profile: DomainProfile | None = None) -> QueryPlan:
    normalized = " ".join(topic.split())
    profile = profile or load_domain_profile("auto", normalized)
    queries = _profile_queries(normalized, profile)

    if profile.domain_id == "medical-vlm" or any(
        term in normalized.lower() for term in ["medical", "clinical", "lesion", "radiology"]
    ):
        queries.extend(
            [
                "medical vision language model lesion temporal change",
                "radiology vision-language model longitudinal change lesion",
                "medical multimodal model temporal lesion analysis",
                "lesion-level temporal reasoning medical VLM",
                "medical image longitudinal lesion change benchmark",
                "radiology report temporal change lesion dataset",
            ]
        )
    if profile.domain_id == "medical-vlm" and any(
        term in normalized.lower() for term in ["vlm", "vision language", "multimodal"]
    ):
        queries.extend(
            [
                "medical vision-language model benchmark dataset",
                "multimodal medical foundation model lesion localization",
            ]
        )
    queries.extend(f"{normalized} {perspective}" for perspective in PERSPECTIVES[:4])

    seen = set()
    unique = [query for query in queries if not (query.lower() in seen or seen.add(query.lower()))]
    return QueryPlan(topic=topic, queries=unique[:10], perspectives=PERSPECTIVES)
