from __future__ import annotations

import hashlib
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import DEFAULT_VENUE_ALIASES, VENUE_ALIAS_GROUPS
from .models import Event, RawEvent, SourceConfig

MALAYSIA_TZ = ZoneInfo("Asia/Kuala_Lumpur")

EXCLUDED_EVENT_URL_PARTS = (
    "/event/50519/lgra-x-mitogels-sub-2.30-half-marathon-training-running-class",
)

STABLE_ID_VENUE_NAMES = {
    "Unifi Arena": "Axiata Arena",
}


def normalize_events(
    raw_events: list[RawEvent],
    sources: dict[str, SourceConfig],
    now: datetime | None = None,
) -> list[Event]:
    cutoff = now or datetime.now(MALAYSIA_TZ)
    normalized: list[Event] = []
    for raw in raw_events:
        if _excluded_event(raw):
            continue
        if raw.start is None:
            continue
        start = _localize(raw.start)
        end = _localize(raw.end) if raw.end else None
        if end is not None and end <= start:
            end = None
        if start < cutoff:
            continue
        source = sources[raw.source_id]
        venue = _resolve_venue(raw.venue, source.venue_aliases)
        if venue is None:
            continue
        event_id = _stable_id(raw.title, start, _stable_id_venue(venue))
        normalized.append(
            Event(
                id=event_id,
                title=raw.title,
                start=start,
                end=end,
                venue=venue,
                address=raw.address,
                url=raw.url or raw.source_url,
                category=raw.category,
                description=raw.description,
                status=raw.status,
                confidence=max(1, 100 - source.priority),
                sources=[
                    {
                        "id": raw.source_id,
                        "name": raw.source_name,
                        "url": raw.source_url,
                        "method": raw.method.value,
                    }
                ],
            )
        )
    return normalized


def _localize(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=MALAYSIA_TZ)
    return value.astimezone(MALAYSIA_TZ)


def _excluded_event(raw: RawEvent) -> bool:
    urls = (raw.url, raw.source_url)
    return any(
        blocked in url
        for url in urls
        if url
        for blocked in EXCLUDED_EVENT_URL_PARTS
    )


def _resolve_venue(venue: str | None, source_aliases: tuple[str, ...]) -> str | None:
    if not venue:
        return None
    aliases = source_aliases or DEFAULT_VENUE_ALIASES
    allowed_aliases = {_norm(alias) for alias in aliases}
    normalized_venue = _norm(venue)
    for canonical, canonical_aliases in VENUE_ALIAS_GROUPS.items():
        for alias in canonical_aliases:
            normalized_alias = _norm(alias)
            if normalized_alias not in allowed_aliases:
                continue
            if normalized_alias in normalized_venue or normalized_venue in normalized_alias:
                return canonical
    return None


def dedupe_key(event: Event) -> tuple[str, str, str]:
    return (event.start.date().isoformat(), _norm(event.venue), _title_fingerprint(event.title))


def _stable_id(title: str, start: datetime, venue: str) -> str:
    key = f"{start.date().isoformat()}|{_norm(venue)}|{_title_fingerprint(title)}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return f"{digest}@kl-stadium-calendar"


def _stable_id_venue(venue: str) -> str:
    return STABLE_ID_VENUE_NAMES.get(venue, venue)


def _title_fingerprint(title: str) -> str:
    stopwords = {"world", "tour", "live", "concert", "malaysia", "kuala", "lumpur"}
    words = [word for word in re.findall(r"[a-z0-9]+", title.lower()) if word not in stopwords]
    return " ".join(words[:8]) or _norm(title)


def _norm(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))
