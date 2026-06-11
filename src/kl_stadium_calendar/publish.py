from __future__ import annotations

import json
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

from icalendar import Calendar, Event as ICalEvent, vText

from .models import Event


def write_outputs(
    output_dir: Path,
    events: list[Event],
    source_reports: list[dict[str, object]],
    now: datetime | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_at = now or datetime.now(UTC)
    (output_dir / "events.json").write_text(
        json.dumps([_event_dict(event) for event in events], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "sources.json").write_text(
        json.dumps(source_reports, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "health.json").write_text(
        json.dumps(
            {
                "generated_at": run_at.isoformat(),
                "event_count": len(events),
                "source_count": len(source_reports),
                "failed_source_count": sum(1 for report in source_reports if report["status"] == "error"),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "events.ics").write_bytes(_calendar(events, run_at).to_ical())
    (output_dir / "_headers").write_text(_headers(), encoding="utf-8")


def _calendar(events: list[Event], run_at: datetime) -> Calendar:
    calendar = Calendar()
    calendar.add("prodid", "-//kl-stadium-calendar//Bukit Jalil Events//EN")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("method", "PUBLISH")
    calendar.add("x-wr-calname", "Bukit Jalil Stadium Events")
    calendar.add("x-wr-caldesc", "Upcoming events at Bukit Jalil National Stadium")
    calendar.add("x-wr-timezone", "Asia/Kuala_Lumpur")
    calendar.add("x-published-ttl", "PT6H")
    calendar.add("refresh-interval", timedelta(hours=6), parameters={"VALUE": "DURATION"})

    for event in events:
        component = ICalEvent()
        component.add("uid", event.id)
        component.add("dtstamp", run_at)
        _add_event_dates(component, event)
        component.add("summary", event.title)
        component.add("location", event.address or event.venue)
        component.add("status", event.status)
        if event.url:
            component.add("url", event.url)
        if event.category:
            component.add("categories", event.category)
        description = _description(event)
        if description:
            component.add("description", description)
        component["LOCATION"].params["ALTREP"] = vText(event.venue)
        calendar.add_component(component)
    return calendar


def _add_event_dates(component: ICalEvent, event: Event) -> None:
    if event.end and event.end - event.start >= timedelta(days=1):
        component.add("dtstart", event.start.date())
        end_date = event.end.date()
        if event.end.time() != time.min:
            end_date += timedelta(days=1)
        component.add("dtend", end_date)
        return

    component.add("dtstart", event.start)
    if event.end:
        component.add("dtend", event.end)


def _description(event: Event) -> str:
    parts = []
    if event.description:
        parts.append(event.description)
    parts.append("Sources:")
    for source in event.sources:
        parts.append(f"- {source['name']}: {source['url']} ({source['method']})")
    return "\n".join(parts)


def _headers() -> str:
    return """/events.ics
  Content-Type: text/calendar; charset=utf-8
  Cache-Control: public, max-age=3600
  Access-Control-Allow-Origin: *

/events.json
  Content-Type: application/json; charset=utf-8
  Cache-Control: public, max-age=3600

/sources.json
  Content-Type: application/json; charset=utf-8
  Cache-Control: public, max-age=3600

/health.json
  Content-Type: application/json; charset=utf-8
  Cache-Control: public, max-age=300
"""


def _event_dict(event: Event) -> dict[str, object]:
    return {
        "id": event.id,
        "title": event.title,
        "start": event.start.isoformat(),
        "end": event.end.isoformat() if event.end else None,
        "venue": event.venue,
        "address": event.address,
        "url": event.url,
        "category": event.category,
        "description": event.description,
        "status": event.status,
        "confidence": event.confidence,
        "sources": event.sources,
    }
