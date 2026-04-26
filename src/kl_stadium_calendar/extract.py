from __future__ import annotations

import json
import re
from html import unescape
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urljoin
from xml.etree import ElementTree

from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_datetime
from icalendar import Calendar

from .models import DiscoveredSource, RawEvent, SourceMethod


def extract_events(discovered: DiscoveredSource) -> list[RawEvent]:
    match discovered.method:
        case SourceMethod.ICS:
            return _extract_ics(discovered)
        case SourceMethod.RSS | SourceMethod.ATOM:
            return _extract_feed(discovered)
        case SourceMethod.API_JSON:
            return _extract_api_json(discovered)
        case SourceMethod.JSON_LD:
            return _extract_json_ld(discovered)
        case SourceMethod.HTML:
            return _extract_html(discovered)
    return []


def _base_event(discovered: DiscoveredSource, title: str) -> RawEvent:
    return RawEvent(
        title=_clean(unescape(title)),
        source_id=discovered.config.id,
        source_name=discovered.config.name,
        source_url=discovered.url,
        method=discovered.method,
    )


def _extract_ics(discovered: DiscoveredSource) -> list[RawEvent]:
    calendar = Calendar.from_ical(discovered.fetched.text)
    events: list[RawEvent] = []
    for component in calendar.walk("VEVENT"):
        summary = str(component.get("summary", "")).strip()
        if not summary:
            continue
        event = _base_event(discovered, summary)
        event.start = _ical_datetime(component.decoded("dtstart", None))
        event.end = _ical_datetime(component.decoded("dtend", None))
        event.venue = _optional_str(component.get("location"))
        event.description = _optional_str(component.get("description"))
        event.url = _optional_str(component.get("url"))
        events.append(event)
    return events


def _extract_feed(discovered: DiscoveredSource) -> list[RawEvent]:
    root = ElementTree.fromstring(discovered.fetched.text.encode("utf-8"))
    items = root.findall(".//item") or root.findall("{http://www.w3.org/2005/Atom}entry")
    events: list[RawEvent] = []
    for item in items:
        title = _find_text(item, "title")
        if not title:
            continue
        event = _base_event(discovered, title)
        event.url = _find_text(item, "link") or item.findtext("{http://www.w3.org/2005/Atom}link")
        event.description = _find_text(item, "description") or _find_text(item, "summary")
        event.start = _parse_first_date(
            _find_text(item, "startDate"),
            _find_text(item, "eventDate"),
            _find_text(item, "pubDate"),
            _find_text(item, "published"),
            _find_text(item, "updated"),
        )
        event.venue = _find_text(item, "location") or _find_text(item, "venue")
        events.append(event)
    return events


def _extract_api_json(discovered: DiscoveredSource) -> list[RawEvent]:
    payload = json.loads(discovered.fetched.text)
    candidates = _event_candidates(payload)
    return [_event_from_mapping(discovered, candidate) for candidate in candidates if _event_title(candidate)]


def _extract_json_ld(discovered: DiscoveredSource) -> list[RawEvent]:
    soup = BeautifulSoup(discovered.fetched.text, "html.parser")
    events: list[RawEvent] = []
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        if not script.string:
            continue
        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        for candidate in _event_candidates(payload):
            if _event_title(candidate):
                events.append(_event_from_mapping(discovered, candidate))
    return events


def _extract_html(discovered: DiscoveredSource) -> list[RawEvent]:
    if "livenation.my" in discovered.url and "tickets-vdp" in discovered.url:
        events = _extract_livenation_venue_page(discovered)
        if events:
            return events

    json_ld_source = DiscoveredSource(
        discovered.config,
        SourceMethod.JSON_LD,
        discovered.url,
        discovered.reason,
        discovered.fetched,
    )
    events = _extract_json_ld(json_ld_source)
    for event in events:
        event.method = SourceMethod.HTML
    return events


def _extract_livenation_venue_page(discovered: DiscoveredSource) -> list[RawEvent]:
    soup = BeautifulSoup(discovered.fetched.text, "html.parser")
    text_lines = [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]
    event_links = [
        urljoin(discovered.url, link.get("href"))
        for link in soup.find_all("a", href=True)
        if str(link.get("href")).startswith("/event/")
        and str(link.get("href")) not in {"/event/allevents"}
    ]

    events: list[RawEvent] = []
    link_index = 0
    for index, line in enumerate(text_lines):
        if line != "Find Tickets" or index == 0:
            continue
        title = _previous_livenation_title(text_lines, index)
        if not title:
            continue
        date_value = _next_matching_line(text_lines, index + 1, r"\d{1,2}\s+\w+\s+\d{4}")
        if not date_value:
            continue
        time_value = _next_livenation_time_line(text_lines, index + 1)
        event = _base_event(discovered, title)
        event.start = _parse_first_date(_join_date_time(_strip_weekday(date_value), time_value))
        event.venue = discovered.config.venue_aliases[0] if discovered.config.venue_aliases else "Axiata Arena"
        event.address = "217, Bukit Jalil, 57000 Kuala Lumpur, Malaysia"
        event.url = event_links[link_index] if link_index < len(event_links) else discovered.url
        event.category = "Concert"
        event.description = f"{title} at {event.venue}"
        events.append(event)
        link_index += 1
    return events


def _next_matching_line(lines: list[str], start: int, pattern: str) -> str | None:
    regex = re.compile(pattern)
    for line in lines[start : start + 5]:
        if regex.search(line):
            return line
    return None


def _previous_livenation_title(lines: list[str], ticket_index: int) -> str | None:
    ignored = {
        "Find Tickets",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    }
    for line in reversed(lines[max(0, ticket_index - 8) : ticket_index]):
        if line in ignored or re.fullmatch(r"\d{1,4}", line):
            continue
        return line
    return None


def _next_livenation_time_line(lines: list[str], start: int) -> str | None:
    for offset, line in enumerate(lines[start : start + 12]):
        if line != "Time:":
            continue
        if start + offset + 1 < len(lines):
            candidate = lines[start + offset + 1]
            if re.fullmatch(r"\d{1,2}(:\d{2})?\s*(am|pm|AM|PM)", candidate):
                return candidate
    return None


def _join_date_time(date_value: str, time_value: str | None) -> str:
    if not time_value:
        return date_value
    return f"{date_value} {time_value}"


def _strip_weekday(value: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", value).strip()


def _event_candidates(payload: Any) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for item in payload:
            candidates.extend(_event_candidates(item))
    elif isinstance(payload, dict):
        item_type = payload.get("@type") or payload.get("type")
        if isinstance(item_type, list):
            is_event = "Event" in item_type
        else:
            is_event = str(item_type).lower().endswith("event")
        if is_event or {"startDate", "start_date", "name"}.intersection(payload):
            candidates.append(payload)
        for key in ("@graph", "events", "data", "results", "items"):
            if key in payload:
                candidates.extend(_event_candidates(payload[key]))
    return candidates


def _event_from_mapping(discovered: DiscoveredSource, data: dict[str, Any]) -> RawEvent:
    title = _event_title(data) or "Untitled event"
    event = _base_event(discovered, title)
    event.start = _parse_first_date(
        _nested(data, "startDate"),
        _nested(data, "start_date"),
        _nested(data, "start_date", "local"),
        _nested(data, "start", "local"),
        _nested(data, "start", "utc"),
    )
    event.end = _parse_first_date(
        _nested(data, "endDate"),
        _nested(data, "end_date"),
        _nested(data, "end_date", "local"),
        _nested(data, "end", "local"),
        _nested(data, "end", "utc"),
    )
    event.url = _nested(data, "url") or _nested(data, "event_url")
    event.category = _category_name(data)
    event.description = _nested(data, "description") or _nested(data, "summary")
    event.venue = _location_name(data)
    event.address = _location_address(data)
    event.raw = data
    return event


def _event_title(data: dict[str, Any]) -> str | None:
    return _nested(data, "name") or _nested(data, "title")


def _location_name(data: dict[str, Any]) -> str | None:
    location = data.get("location") or data.get("venue")
    if isinstance(location, dict):
        return (
            _nested(location, "name")
            or _nested(location, "venue")
            or _nested(location, "localized_address_display")
        )
    if isinstance(location, str):
        return location
    return None


def _location_address(data: dict[str, Any]) -> str | None:
    location = data.get("location") or data.get("venue")
    if not isinstance(location, dict):
        return None
    address = location.get("address")
    if isinstance(address, str):
        return address
    if isinstance(address, dict):
        parts = [
            address.get("streetAddress"),
            address.get("addressLocality"),
            address.get("addressRegion"),
            address.get("postalCode"),
            address.get("addressCountry"),
        ]
        return ", ".join(str(part) for part in parts if part)
    parts = [
        location.get("address"),
        location.get("city"),
        location.get("province"),
        location.get("zip"),
        location.get("country"),
    ]
    return ", ".join(str(part) for part in parts if part) or None
    return None


def _category_name(data: dict[str, Any]) -> str | None:
    categories = data.get("categories")
    if isinstance(categories, list) and categories:
        names = []
        for category in categories:
            if isinstance(category, dict):
                name = category.get("name")
                if name:
                    names.append(unescape(str(name)))
            elif isinstance(category, str):
                names.append(unescape(category))
        return ", ".join(names) or None
    return _nested(data, "eventAttendanceMode") or _nested(data, "category")


def _nested(data: dict[str, Any], *path: str) -> str | None:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if current is None:
        return None
    return str(current).strip() or None


def _find_text(element: ElementTree.Element, local_name: str) -> str | None:
    for child in element.iter():
        if child.tag.split("}")[-1] == local_name and child.text:
            return child.text.strip()
    return None


def _parse_first_date(*values: str | None) -> datetime | None:
    for value in values:
        if not value:
            continue
        try:
            if "," in value and any(day in value for day in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
                return parsedate_to_datetime(value)
            return parse_datetime(value)
        except (TypeError, ValueError):
            continue
    return None


def _ical_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if hasattr(value, "dt") and isinstance(value.dt, datetime):
        return value.dt
    return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clean(value: str) -> str:
    return " ".join(value.split())
