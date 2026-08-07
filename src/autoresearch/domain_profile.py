from __future__ import annotations

from pathlib import Path

from .schema import CapabilityDimension, DomainProfile, EvidencePolicy, SourcePolicy
from .utils import slugify, tokens

DEFAULT_GAP_LENSES = [
    "coverage gap",
    "benchmark gap",
    "metric gap",
    "assumption gap",
    "contradiction gap",
    "failure-analysis gap",
    "real-world-transfer gap",
]


def _medical_source_policy() -> SourcePolicy:
    return SourcePolicy(
        preferred_sources=["pubmed", "europepmc", "openalex"],
        neutral_sources=["arxiv", "crossref", "openreview"],
        downrank_sources=[],
        disabled_sources=[],
        source_weight_overrides={
            "pubmed": 0.12,
            "europepmc": 0.11,
            "openalex": 0.08,
            "arxiv": 0.06,
            "crossref": 0.05,
            "openreview": 0.03,
        },
    )


def _medical_evidence_policy() -> EvidencePolicy:
    return EvidencePolicy(
        core_keywords=[
            "medical VLM",
            "medical vision-language",
            "radiology vision-language",
            "medical multimodal",
            "radiology",
            "medical imaging",
            "lesion",
            "temporal change",
            "longitudinal",
            "follow-up",
            "MIMIC-CXR",
            "CheXpert",
            "DeepLesion",
            "CTLesionVQA",
        ],
        adjacent_keywords=[
            "vision-language model",
            "multimodal large language model",
            "report generation",
            "segmentation",
            "clinical workflow",
            "foundation model",
            "visual question answering",
        ],
        negative_keywords=[
            "GUI agent",
            "web navigation",
            "desktop control",
            "browser automation",
            "computer use",
            "tool use",
            "function calling",
            "seismic",
            "remote sensing",
        ],
    )


def _gui_source_policy() -> SourcePolicy:
    return SourcePolicy(
        preferred_sources=["arxiv", "openreview", "openalex"],
        neutral_sources=["crossref"],
        downrank_sources=["pubmed", "europepmc"],
        disabled_sources=[],
        source_weight_overrides={
            "arxiv": 0.14,
            "openreview": 0.14,
            "openalex": 0.1,
            "crossref": 0.05,
            "pubmed": -0.08,
            "europepmc": -0.08,
        },
    )


def _gui_evidence_policy() -> EvidencePolicy:
    return EvidencePolicy(
        core_keywords=[
            "GUI agent",
            "web navigation",
            "desktop control",
            "mobile agent",
            "computer use agent",
            "browser agent",
            "OSWorld",
            "WebArena",
            "AndroidWorld",
            "VisualWebArena",
            "Mind2Web",
            "WorkArena",
            "MobileUse",
            "LongHorizonUI",
            "GUI-ReWalk",
        ],
        adjacent_keywords=[
            "workflow automation",
            "tool agent",
            "computer use",
            "browser automation",
            "LLM agent",
            "multimodal agent",
            "task success rate",
            "long-horizon task",
            "interactive task",
        ],
        negative_keywords=[
            "medical",
            "clinical",
            "PET/CT",
            "ophthalmic",
            "patient",
            "radiology",
            "lesion",
            "diagnosis",
            "disease",
        ],
    )


def _llm_agent_source_policy() -> SourcePolicy:
    return SourcePolicy(
        preferred_sources=["arxiv", "openreview", "openalex"],
        neutral_sources=["crossref"],
        downrank_sources=["pubmed", "europepmc"],
        disabled_sources=[],
        source_weight_overrides={
            "arxiv": 0.12,
            "openreview": 0.12,
            "openalex": 0.09,
            "crossref": 0.05,
            "pubmed": -0.06,
            "europepmc": -0.06,
        },
    )


def _llm_agent_evidence_policy() -> EvidencePolicy:
    return EvidencePolicy(
        core_keywords=[
            "LLM agent",
            "tool use",
            "function calling",
            "multi-turn workflow",
            "agent benchmark",
            "ToolBench",
            "API-Bank",
            "BFCL",
            "tau-bench",
            "VitaBench",
            "AgentBench",
            "GAIA",
        ],
        adjacent_keywords=[
            "planning",
            "reflection",
            "memory",
            "verifier",
            "harness",
            "workflow evaluation",
            "task success rate",
        ],
        negative_keywords=[
            "medical imaging",
            "radiology",
            "lesion",
            "PET/CT",
            "ophthalmic",
            "seismic",
            "remote sensing",
        ],
    )


def _generic_source_policy() -> SourcePolicy:
    return SourcePolicy(
        preferred_sources=["openalex", "arxiv"],
        neutral_sources=["crossref", "openreview", "pubmed", "europepmc"],
        downrank_sources=[],
        disabled_sources=[],
        source_weight_overrides={
            "openalex": 0.08,
            "arxiv": 0.08,
            "openreview": 0.06,
            "crossref": 0.05,
            "pubmed": 0.03,
            "europepmc": 0.03,
        },
    )


def _generic_evidence_policy(topic: str) -> EvidencePolicy:
    topic_terms = [term for term in tokens(topic) if len(term) > 2][:8]
    return EvidencePolicy(
        core_keywords=topic_terms,
        adjacent_keywords=["benchmark", "dataset", "evaluation", "survey", "baseline"],
        negative_keywords=[],
    )


def _dimension(
    name: str,
    keywords: list[str],
    *,
    description: str = "",
    keyword_groups: list[list[str]] | None = None,
    required: bool = True,
) -> CapabilityDimension:
    return CapabilityDimension(
        name=name,
        keywords=keywords,
        keyword_groups=keyword_groups or [],
        description=description,
        required=required,
    )


def _medical_vlm(topic: str = "") -> DomainProfile:
    return DomainProfile(
        domain_id="medical-vlm",
        domain_name="Medical VLM",
        seed_topic=topic,
        description="Medical vision-language and multimodal models for clinical image understanding.",
        core_concepts=[
            "medical VLM",
            "radiology",
            "medical imaging",
            "lesion",
            "temporal change",
            "longitudinal study",
            "report generation",
        ],
        query_terms=[
            "medical vision-language model",
            "radiology vision language model",
            "medical multimodal foundation model",
            "lesion temporal change",
            "longitudinal medical image analysis",
            "medical VLM benchmark dataset",
        ],
        task_keywords=[
            "temporal change analysis",
            "visual question answering",
            "report generation",
            "lesion segmentation",
            "diagnosis",
            "classification",
        ],
        method_keywords=[
            "vision-language model",
            "multimodal large language model",
            "instruction tuning",
            "contrastive learning",
            "retrieval augmented",
            "mask-guided",
            "region grounding",
        ],
        dataset_keywords=[
            "MIMIC-CXR",
            "CheXpert",
            "PadChest",
            "NIH ChestXray14",
            "BraTS",
            "DeepLesion",
            "RadImageNet",
            "PMC-VQA",
            "ROCO",
            "CTLesionVQA",
        ],
        benchmark_keywords=[
            "benchmark",
            "dataset",
            "evaluation",
            "baseline",
            "leaderboard",
        ],
        metric_keywords=[
            "accuracy",
            "AUC",
            "F1",
            "BLEU",
            "ROUGE",
            "BERTScore",
            "Dice",
            "IoU",
            "change label accuracy",
            "location consistency",
        ],
        capability_dimensions=[
            _dimension(
                "lesion-level temporal change reasoning",
                [
                    "temporal",
                    "longitudinal",
                    "follow-up",
                    "change",
                    "progression",
                    "lesion",
                    "finding",
                    "localization",
                    "segmentation",
                    "mask",
                ],
                keyword_groups=[
                    ["temporal", "longitudinal", "follow-up", "change", "progression"],
                    ["lesion", "finding", "localization", "segmentation", "mask"],
                ],
                description="Whether papers jointly cover temporal/change reasoning and lesion-level grounding.",
            ),
            _dimension(
                "paired-study benchmark coverage",
                ["paired", "follow-up", "longitudinal", "benchmark", "dataset", "evaluation"],
                description="Whether evaluation uses paired or longitudinal clinical studies.",
            ),
            _dimension(
                "clinical consistency metrics",
                ["change label accuracy", "finding consistency", "location consistency", "BERTScore"],
                description="Whether metrics separate finding, location, and change-direction correctness.",
            ),
        ],
        gap_lenses=DEFAULT_GAP_LENSES,
        source_policy=_medical_source_policy(),
        evidence_policy=_medical_evidence_policy(),
    )


def _gui_agent(topic: str = "") -> DomainProfile:
    return DomainProfile(
        domain_id="gui-agent",
        domain_name="GUI Agent",
        seed_topic=topic,
        description="LLM or multimodal agents that operate GUI, browser, desktop, or mobile workflows.",
        core_concepts=[
            "GUI agent",
            "web navigation",
            "desktop control",
            "mobile agent",
            "workflow automation",
            "environment interaction",
            "failure recovery",
        ],
        query_terms=[
            "GUI agent benchmark",
            "web navigation agent benchmark",
            "desktop control agent",
            "real-world workflow automation agent",
            "long-horizon GUI task",
            "computer use agent evaluation",
        ],
        task_keywords=[
            "web navigation",
            "desktop control",
            "mobile control",
            "workflow automation",
            "computer use",
            "interactive task",
        ],
        method_keywords=[
            "LLM agent",
            "multimodal agent",
            "planning",
            "reflection",
            "memory",
            "tool use",
            "browser automation",
            "vision-language model",
        ],
        dataset_keywords=[
            "WebArena",
            "OSWorld",
            "Mind2Web",
            "MiniWoB++",
            "AndroidWorld",
            "VisualWebArena",
            "WorkArena",
        ],
        benchmark_keywords=[
            "benchmark",
            "environment",
            "task suite",
            "leaderboard",
            "evaluation",
            "simulator",
        ],
        metric_keywords=[
            "task success rate",
            "success rate",
            "step success",
            "action accuracy",
            "trajectory length",
            "recovery rate",
            "human evaluation",
        ],
        capability_dimensions=[
            _dimension(
                "real-world long-horizon workflow",
                [
                    "real-world",
                    "workflow",
                    "long-horizon",
                    "multi-step",
                    "desktop",
                    "web",
                    "browser",
                ],
                description="Whether papers evaluate realistic multi-step workflows rather than toy tasks.",
            ),
            _dimension(
                "failure recovery and self-correction",
                ["failure", "recovery", "self-correction", "reflection", "repair", "retry"],
                description="Whether papers explain and evaluate recovery from GUI/action failures.",
            ),
            _dimension(
                "environment reproducibility",
                ["environment", "simulator", "reproducible", "state", "reset", "deterministic"],
                description="Whether benchmark environments are reproducible and comparable across agents.",
            ),
        ],
        gap_lenses=DEFAULT_GAP_LENSES,
        source_policy=_gui_source_policy(),
        evidence_policy=_gui_evidence_policy(),
    )


def _llm_agent(topic: str = "") -> DomainProfile:
    return DomainProfile(
        domain_id="llm-agent",
        domain_name="LLM Agent",
        seed_topic=topic,
        description="LLM agents for tool use, function calling, planning, memory, and workflow execution.",
        core_concepts=[
            "LLM agent",
            "tool use",
            "function calling",
            "planning",
            "memory",
            "multi-turn workflow",
            "agent benchmark",
        ],
        query_terms=[
            "LLM agent benchmark",
            "tool use benchmark",
            "function calling benchmark",
            "multi-turn agent workflow",
            "agent failure analysis",
            "workflow evaluation LLM agent",
        ],
        task_keywords=[
            "tool use",
            "function calling",
            "planning",
            "multi-turn dialogue",
            "workflow execution",
            "retrieval augmented generation",
        ],
        method_keywords=[
            "planning",
            "reflection",
            "memory",
            "tool selection",
            "function calling",
            "retrieval",
            "verifier",
            "harness",
        ],
        dataset_keywords=[
            "BFCL",
            "ToolBench",
            "API-Bank",
            "tau-bench",
            "VitaBench",
            "AgentBench",
            "GAIA",
        ],
        benchmark_keywords=[
            "benchmark",
            "leaderboard",
            "evaluation",
            "test suite",
            "harness",
            "simulator",
        ],
        metric_keywords=[
            "success rate",
            "pass rate",
            "tool call accuracy",
            "exact match",
            "trajectory",
            "cost",
            "latency",
        ],
        capability_dimensions=[
            _dimension(
                "realistic multi-step workflow",
                ["workflow", "multi-step", "multi-turn", "long-horizon", "task completion"],
                description="Whether the benchmark measures realistic multi-step agent workflows.",
            ),
            _dimension(
                "failure-conditioned evaluation",
                ["failure", "error", "recovery", "repair", "ablation", "taxonomy"],
                description="Whether papers explain which failure types are fixed by an agent method.",
            ),
            _dimension(
                "tool and environment generalization",
                ["unseen tool", "generalization", "environment", "api", "function calling"],
                description="Whether evaluation covers transfer to unseen tools, APIs, or environments.",
            ),
        ],
        gap_lenses=DEFAULT_GAP_LENSES,
        source_policy=_llm_agent_source_policy(),
        evidence_policy=_llm_agent_evidence_policy(),
    )


def _generic(topic: str = "") -> DomainProfile:
    topic_tokens = [term for term in tokens(topic) if len(term) > 2][:8]
    return DomainProfile(
        domain_id=slugify(topic)[:60],
        domain_name="Generic Research Domain",
        seed_topic=topic,
        description="Rule-generated fallback profile for an arbitrary research direction.",
        core_concepts=topic_tokens,
        query_terms=[
            topic,
            f"{topic} benchmark",
            f"{topic} dataset",
            f"{topic} evaluation",
            f"{topic} limitations",
            f"{topic} survey",
        ],
        task_keywords=topic_tokens,
        method_keywords=["method", "model", "framework", "architecture", "algorithm"],
        dataset_keywords=[],
        benchmark_keywords=["benchmark", "dataset", "evaluation", "baseline", "leaderboard"],
        metric_keywords=["accuracy", "F1", "AUC", "success rate", "human evaluation", "ablation"],
        capability_dimensions=[
            _dimension(
                "target capability coverage",
                topic_tokens,
                description="Whether papers directly cover the user's stated target capability.",
            ),
            _dimension(
                "benchmark coverage",
                ["benchmark", "dataset", "evaluation", "baseline"],
                description="Whether papers make benchmark or dataset coverage explicit.",
            ),
            _dimension(
                "metric specificity",
                ["metric", "accuracy", "F1", "success rate", "human evaluation", "ablation"],
                description="Whether papers expose specific metrics for the target capability.",
            ),
        ],
        gap_lenses=DEFAULT_GAP_LENSES,
        source_policy=_generic_source_policy(),
        evidence_policy=_generic_evidence_policy(topic),
    )


BUILTIN_PROFILES = {
    "medical-vlm": _medical_vlm,
    "gui-agent": _gui_agent,
    "llm-agent": _llm_agent,
    "generic": _generic,
}


def infer_profile_id(topic: str) -> str:
    lowered = topic.lower()
    if any(term in lowered for term in ["medical", "clinical", "radiology", "lesion"]):
        return "medical-vlm"
    if any(term in lowered for term in ["gui", "browser", "desktop", "web navigation", "computer use"]):
        return "gui-agent"
    if any(term in lowered for term in ["agent", "tool use", "function calling", "workflow"]):
        return "llm-agent"
    return "generic"


def generate_domain_profile(topic: str, profile_id: str = "auto") -> DomainProfile:
    resolved_id = infer_profile_id(topic) if profile_id in {"", "auto"} else profile_id
    factory = BUILTIN_PROFILES.get(resolved_id, _generic)
    profile = factory(topic)
    if resolved_id not in BUILTIN_PROFILES:
        profile.domain_id = slugify(resolved_id)
        profile.domain_name = resolved_id.replace("-", " ").title()
    return profile


def load_domain_profile(value: str | Path | None, topic: str) -> DomainProfile:
    if value is None or str(value).strip() in {"", "auto"}:
        return generate_domain_profile(topic)
    profile_value = str(value)
    candidates = [
        Path(profile_value),
        Path.cwd() / "profiles" / profile_value,
        Path.cwd() / "profiles" / f"{profile_value}.json",
    ]
    for path in candidates:
        if path.exists():
            return DomainProfile.model_validate_json(path.read_text(encoding="utf-8"))
    return generate_domain_profile(topic, profile_value)


def save_domain_profile(profile: DomainProfile, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")
    return path
