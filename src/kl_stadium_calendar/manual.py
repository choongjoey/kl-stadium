from __future__ import annotations

import json
from pathlib import Path

from dateutil.parser import parse as parse_datetime

from .models import RawEvent, SourceConfig, SourceMethod


def load_manual_events(path: Path) -> tuple[list[SourceConfig], list[RawEvent], list[dict[str, object]]]:
    if not path.exists():
        return [], [], []

    payload = json.loads(path.read_text(encoding="utf-8"))
    source_configs: dict[str, SourceConfig] = {}
    events: list[RawEvent] = []
    reports: dict[str, dict[str, object]] = {}

    for item in payload:
        source = item["source"]
        source_id = source["id"]
        source_configs[source_id] = SourceConfig(
            id=source_id,
            name=source["name"],
            url=source["url"],
            priority=int(source.get("priority", 5)),
        )
        reports.setdefault(
            source_id,
            {
                "id": source_id,
                "name": source["name"],
                "status": "ok",
                "url": source["url"],
                "final_url": source["url"],
                "method": SourceMethod.MANUAL.value,
                "reason": "confirmed seed event",
                "raw_event_count": 0,
            },
        )
        reports[source_id]["raw_event_count"] = int(reports[source_id]["raw_event_count"]) + 1

        events.append(
            RawEvent(
                title=item["title"],
                source_id=source_id,
                source_name=source["name"],
                source_url=source["url"],
                method=SourceMethod.MANUAL,
                start=parse_datetime(item["start"]),
                end=parse_datetime(item["end"]) if item.get("end") else None,
                venue=item.get("venue"),
                address=item.get("address"),
                url=item.get("url") or source["url"],
                category=item.get("category"),
                description=item.get("description"),
                status=item.get("status", "CONFIRMED"),
            )
        )

    return list(source_configs.values()), events, list(reports.values())

