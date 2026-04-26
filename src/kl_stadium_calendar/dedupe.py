from __future__ import annotations

import re

from .models import Event
from .normalize import dedupe_key


def dedupe_events(events: list[Event]) -> list[Event]:
    merged: dict[tuple[str, str, str], Event] = {}
    for event in sorted(events, key=lambda item: (-item.confidence, item.start, item.title)):
        key = dedupe_key(event)
        key = _matching_key(merged, event) or key
        existing = merged.get(key)
        if existing is None:
            merged[key] = event
            continue
        _append_sources(existing, event)
        existing.confidence = max(existing.confidence, event.confidence)
        if not existing.url and event.url:
            existing.url = event.url
        if not existing.description and event.description:
            existing.description = event.description
        if not existing.address and event.address:
            existing.address = event.address
        if existing.end is None and event.end is not None:
            existing.end = event.end
    return sorted(merged.values(), key=lambda item: (item.start, item.title))


def _append_sources(existing: Event, event: Event) -> None:
    seen = {
        (source.get("id"), source.get("url"), source.get("method"))
        for source in existing.sources
    }
    for source in event.sources:
        key = (source.get("id"), source.get("url"), source.get("method"))
        if key in seen:
            continue
        seen.add(key)
        existing.sources.append(source)


def _matching_key(merged: dict[tuple[str, str, str], Event], event: Event) -> tuple[str, str, str] | None:
    event_date = event.start.date()
    event_venue = _norm(event.venue)
    for key, existing in merged.items():
        if existing.start.date() != event_date or _norm(existing.venue) != event_venue:
            continue
        if _similar_title(existing.title, event.title):
            return key
    return None


def _similar_title(left: str, right: str) -> bool:
    left_tokens = _tokens(left)
    right_tokens = _tokens(right)
    if not left_tokens or not right_tokens:
        return False
    overlap = left_tokens & right_tokens
    smaller = min(len(left_tokens), len(right_tokens))
    return len(overlap) / smaller >= 0.8


def _tokens(value: str) -> set[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "at",
        "arena",
        "axiata",
        "bukit",
        "concert",
        "hockey",
        "in",
        "jalil",
        "live",
        "malaysia",
        "national",
        "stadium",
        "the",
        "tm",
        "tour",
        "unifi",
        "world",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if token not in stopwords and not re.fullmatch(r"20\d{2}", token)
    }


def _norm(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))
