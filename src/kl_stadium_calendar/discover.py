from __future__ import annotations

import copy
import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .fetch import Fetcher
from .models import DiscoveredSource, FetchResult, SourceConfig, SourceMethod

METHOD_ORDER = (
    SourceMethod.ICS,
    SourceMethod.RSS,
    SourceMethod.ATOM,
    SourceMethod.API_JSON,
    SourceMethod.JSON_LD,
    SourceMethod.HTML,
)


def discover_source(source: SourceConfig, fetcher: Fetcher) -> DiscoveredSource:
    if source.request_json is not None:
        fetched = _fetch_json_request(source, fetcher)
        method = _classify_direct(fetched)
        if method and _allowed(source, method):
            return DiscoveredSource(source, method, fetched.final_url, f"direct {method.value}", fetched)

    first = fetcher.get(source.url)
    method = _classify_direct(first)
    if method and _allowed(source, method):
        return DiscoveredSource(source, method, first.final_url, f"direct {method.value}", first)

    alternates = _discover_alternates(first)
    for wanted in METHOD_ORDER:
        if not _allowed(source, wanted):
            continue
        for method, url in alternates:
            if method != wanted:
                continue
            fetched = fetcher.get(url)
            actual_method = _classify_direct(fetched) or method
            if _allowed(source, actual_method):
                return DiscoveredSource(
                    source,
                    actual_method,
                    fetched.final_url,
                    f"alternate {actual_method.value} discovered from {first.final_url}",
                    fetched,
                )

    if _allowed(source, SourceMethod.JSON_LD) and _has_json_ld(first):
        return DiscoveredSource(source, SourceMethod.JSON_LD, first.final_url, "embedded JSON-LD", first)

    if _allowed(source, SourceMethod.HTML):
        return DiscoveredSource(source, SourceMethod.HTML, first.final_url, "HTML fallback", first)

    raise ValueError(f"{source.id}: no supported source method discovered")


def _fetch_json_request(source: SourceConfig, fetcher: Fetcher) -> FetchResult:
    first = fetcher.post_json(source.url, source.request_json or {})
    pages = max(1, source.request_pages)
    if pages == 1:
        return first

    try:
        payload = json.loads(first.text)
    except json.JSONDecodeError:
        return first
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        return first

    for page in range(2, pages + 1):
        request_json = copy.deepcopy(source.request_json or {})
        data = request_json.setdefault("data", {})
        if not isinstance(data, dict):
            break
        data["currentpage"] = page
        page_result = fetcher.post_json(source.url, request_json)
        try:
            page_payload = json.loads(page_result.text)
        except json.JSONDecodeError:
            break
        page_data = page_payload.get("data") if isinstance(page_payload, dict) else None
        if not page_data:
            break
        if isinstance(page_data, list):
            payload["data"].extend(page_data)

    return FetchResult(
        url=first.url,
        final_url=first.final_url,
        status_code=first.status_code,
        content_type=first.content_type,
        text=json.dumps(payload),
        headers=first.headers,
    )


def _allowed(source: SourceConfig, method: SourceMethod) -> bool:
    return not source.allowed_methods or method in source.allowed_methods


def _classify_direct(fetch: FetchResult) -> SourceMethod | None:
    content_type = fetch.content_type.lower()
    prefix = fetch.text[:200].lstrip().lower()
    if "text/calendar" in content_type or fetch.text.lstrip().startswith("BEGIN:VCALENDAR"):
        return SourceMethod.ICS
    if "application/rss+xml" in content_type or prefix.startswith("<rss"):
        return SourceMethod.RSS
    if "application/atom+xml" in content_type or prefix.startswith("<feed"):
        return SourceMethod.ATOM
    if "application/json" in content_type or prefix.startswith("{") or prefix.startswith("["):
        return SourceMethod.API_JSON
    if "html" in content_type:
        return None
    return None


def _discover_alternates(fetch: FetchResult) -> list[tuple[SourceMethod, str]]:
    soup = BeautifulSoup(fetch.text, "html.parser")
    alternates: list[tuple[SourceMethod, str]] = []

    for tag in soup.find_all(["link", "a"]):
        href = tag.get("href")
        if not href:
            continue
        type_value = (tag.get("type") or "").lower()
        rel = " ".join(tag.get("rel") or []).lower()
        label = f"{type_value} {rel} {href}".lower()
        method = _method_from_label(label)
        if method:
            alternates.append((method, urljoin(fetch.final_url, href)))

    return _dedupe_alternates(alternates)


def _method_from_label(label: str) -> SourceMethod | None:
    if (
        "text/calendar" in label
        or ".ics" in label
        or "webcal:" in label
        or re.search(r"(^|[?&/_=-])ical($|[&/_.=-])", label)
        or "icalendar" in label
    ):
        return SourceMethod.ICS
    if "application/rss+xml" in label or "/feed" in label or "rss" in label:
        return SourceMethod.RSS
    if "application/atom+xml" in label or "atom" in label:
        return SourceMethod.ATOM
    if "application/json" in label or ".json" in label:
        return SourceMethod.API_JSON
    return None


def _dedupe_alternates(items: list[tuple[SourceMethod, str]]) -> list[tuple[SourceMethod, str]]:
    seen: set[tuple[SourceMethod, str]] = set()
    deduped: list[tuple[SourceMethod, str]] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _has_json_ld(fetch: FetchResult) -> bool:
    soup = BeautifulSoup(fetch.text, "html.parser")
    return bool(soup.find("script", {"type": "application/ld+json"}))
