from __future__ import annotations

import json
from pathlib import Path

from .models import SourceConfig, SourceMethod

DEFAULT_VENUE_ALIASES = (
    "Bukit Jalil National Stadium",
    "National Stadium Bukit Jalil",
    "Stadium Nasional Bukit Jalil",
    "TM National Stadium",
    "TM Stadium Nasional",
    "Stadium Nasional",
)


def load_sources(path: Path) -> list[SourceConfig]:
    raw_sources = json.loads(path.read_text(encoding="utf-8"))
    sources: list[SourceConfig] = []
    for item in raw_sources:
        allowed = tuple(SourceMethod(method) for method in item.get("allowed_methods", []))
        aliases = tuple(item.get("venue_aliases") or DEFAULT_VENUE_ALIASES)
        sources.append(
            SourceConfig(
                id=item["id"],
                name=item["name"],
                url=item["url"],
                priority=int(item.get("priority", 50)),
                allowed_methods=allowed,
                venue_aliases=aliases,
                enabled=bool(item.get("enabled", True)),
                note=item.get("note"),
            )
        )
    return sources
