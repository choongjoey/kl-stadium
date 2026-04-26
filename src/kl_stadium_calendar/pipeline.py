from __future__ import annotations

from datetime import datetime
from pathlib import Path
from traceback import format_exception_only

from .config import load_sources
from .dedupe import dedupe_events
from .discover import discover_source
from .extract import extract_events
from .fetch import Fetcher
from .manual import load_manual_events
from .models import RawEvent
from .normalize import MALAYSIA_TZ, normalize_events
from .publish import write_outputs


def run_pipeline(
    source_config: Path,
    output_dir: Path,
    now: datetime | None = None,
    manual_events_path: Path | None = None,
) -> int:
    sources = load_sources(source_config)
    source_map = {source.id: source for source in sources}
    fetcher = Fetcher()
    raw_events: list[RawEvent] = []
    source_reports: list[dict[str, object]] = []

    manual_sources, manual_events, manual_reports = load_manual_events(
        manual_events_path or Path("data/manual_events.json")
    )
    for source in manual_sources:
        source_map[source.id] = source
    raw_events.extend(manual_events)
    source_reports.extend(manual_reports)

    for source in sources:
        if not source.enabled:
            source_reports.append(
                {
                    "id": source.id,
                    "name": source.name,
                    "status": "skipped",
                    "url": source.url,
                    "reason": source.note or "disabled in source registry",
                }
            )
            continue
        try:
            discovered = discover_source(source, fetcher)
            extracted = extract_events(discovered)
            raw_events.extend(extracted)
            source_reports.append(
                {
                    "id": source.id,
                    "name": source.name,
                    "status": "ok",
                    "url": source.url,
                    "final_url": discovered.url,
                    "method": discovered.method.value,
                    "reason": discovered.reason,
                    "raw_event_count": len(extracted),
                }
            )
        except Exception as error:  # noqa: BLE001 - source isolation is intentional here.
            source_reports.append(
                {
                    "id": source.id,
                    "name": source.name,
                    "status": "error",
                    "url": source.url,
                    "error": "".join(format_exception_only(type(error), error)).strip(),
                }
            )

    run_at = now or datetime.now(MALAYSIA_TZ)
    events = dedupe_events(normalize_events(raw_events, source_map, run_at))
    write_outputs(output_dir, events, source_reports, run_at)
    return 0 if events or any(report["status"] == "ok" for report in source_reports) else 1
