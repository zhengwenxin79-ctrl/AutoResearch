from __future__ import annotations

import re
from datetime import UTC, datetime

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-]{1,}|[\u4e00-\u9fff]{2,}")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "research-topic"


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def tokens(value: str | None) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(value or "")]


def current_year() -> int:
    return datetime.now(UTC).year


def clean_text(value: str | None, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text

