from __future__ import annotations

from collections import defaultdict

from .schema import FieldMap, PaperCard


def _add(mapping: dict[str, list[str]], key: str, title: str) -> None:
    key = key or "not explicit"
    mapping.setdefault(key, [])
    if title not in mapping[key]:
        mapping[key].append(title)


def build_field_map(cards: list[PaperCard]) -> FieldMap:
    tasks: dict[str, list[str]] = defaultdict(list)
    methods: dict[str, list[str]] = defaultdict(list)
    datasets: dict[str, list[str]] = defaultdict(list)
    metrics: dict[str, list[str]] = defaultdict(list)
    models: dict[str, list[str]] = defaultdict(list)
    for card in cards:
        _add(tasks, card.task, card.title)
        _add(methods, card.method, card.title)
        for dataset in [part.strip() for part in card.dataset.split(",") if part.strip()]:
            _add(datasets, dataset, card.title)
        for metric in [part.strip() for part in card.metrics.split(",") if part.strip()]:
            _add(metrics, metric, card.title)
        _add(models, card.model_type, card.title)

    notes = []
    if "not explicit" in datasets:
        notes.append(
            f"{len(datasets['not explicit'])} papers do not expose dataset names in title/abstract metadata."
        )
    if "not explicit" in metrics:
        notes.append(
            f"{len(metrics['not explicit'])} papers do not expose metrics in title/abstract metadata."
        )
    if len(tasks) <= 2:
        notes.append("Task coverage looks narrow; query refinement or full-text reading may be needed.")
    return FieldMap(
        task_clusters=dict(tasks),
        method_clusters=dict(methods),
        datasets=dict(datasets),
        metrics=dict(metrics),
        model_types=dict(models),
        coverage_notes=notes,
    )

