from __future__ import annotations

from .schema import QueryPlan


PERSPECTIVES = [
    "core task and problem formulation",
    "methods and model architectures",
    "datasets and benchmarks",
    "evaluation metrics and baselines",
    "limitations gaps challenges",
    "survey review recent progress",
]


def plan_queries(topic: str) -> QueryPlan:
    normalized = " ".join(topic.split())
    queries = [normalized]

    if any(term in normalized.lower() for term in ["medical", "clinical", "lesion", "radiology"]):
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
    if any(term in normalized.lower() for term in ["vlm", "vision language", "multimodal"]):
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
