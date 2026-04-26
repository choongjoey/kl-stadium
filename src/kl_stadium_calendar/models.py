from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class SourceMethod(StrEnum):
    MANUAL = "manual"
    ICS = "ics"
    RSS = "rss"
    ATOM = "atom"
    API_JSON = "api_json"
    JSON_LD = "json_ld"
    HTML = "html"


@dataclass(frozen=True)
class SourceConfig:
    id: str
    name: str
    url: str
    priority: int = 50
    allowed_methods: tuple[SourceMethod, ...] = ()
    venue_aliases: tuple[str, ...] = ()
    enabled: bool = True
    note: str | None = None


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    status_code: int
    content_type: str
    text: str
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DiscoveredSource:
    config: SourceConfig
    method: SourceMethod
    url: str
    reason: str
    fetched: FetchResult


@dataclass
class RawEvent:
    title: str
    source_id: str
    source_name: str
    source_url: str
    method: SourceMethod
    start: datetime | None = None
    end: datetime | None = None
    venue: str | None = None
    address: str | None = None
    url: str | None = None
    category: str | None = None
    description: str | None = None
    status: str = "CONFIRMED"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    title: str
    start: datetime
    end: datetime | None
    venue: str
    address: str | None
    url: str | None
    category: str | None
    description: str | None
    status: str
    sources: list[dict[str, str]]
    confidence: int
