from datetime import datetime
from zoneinfo import ZoneInfo

from icalendar import Calendar

from kl_stadium_calendar.dedupe import dedupe_events
from kl_stadium_calendar.models import RawEvent, SourceConfig, SourceMethod
from kl_stadium_calendar.normalize import MALAYSIA_TZ, normalize_events
from kl_stadium_calendar.publish import write_outputs


def raw(title, source_id="official"):
    return RawEvent(
        title=title,
        source_id=source_id,
        source_name="Official",
        source_url="https://example.test/event",
        method=SourceMethod.JSON_LD,
        start=datetime(2026, 9, 27, 20, 0, tzinfo=MALAYSIA_TZ),
        venue="TM Stadium Nasional",
        url="https://example.test/event",
    )


def test_filters_past_and_accepts_venue_alias():
    sources = {"official": SourceConfig("official", "Official", "https://example.test", priority=10)}

    events = normalize_events(
        [raw("Post Malone")],
        sources,
        now=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
    )

    assert len(events) == 1
    assert events[0].venue == "Bukit Jalil National Stadium"


def test_dedupes_same_event_same_date():
    sources = {
        "official": SourceConfig("official", "Official", "https://example.test", priority=10),
        "aggregator": SourceConfig("aggregator", "Aggregator", "https://example.test", priority=80),
    }
    event_a = raw("Post Malone", "official")
    event_b = raw("Post Malone Live in Malaysia", "aggregator")

    events = dedupe_events(
        normalize_events(
            [event_a, event_b],
            sources,
            now=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
        )
    )

    assert len(events) == 1
    assert len(events[0].sources) == 2


def test_writes_valid_calendar(tmp_path):
    sources = {"official": SourceConfig("official", "Official", "https://example.test", priority=10)}
    events = normalize_events(
        [raw("Post Malone")],
        sources,
        now=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
    )

    write_outputs(tmp_path, events, [{"id": "official", "status": "ok"}])

    calendar = Calendar.from_ical((tmp_path / "events.ics").read_bytes())
    vevents = [component for component in calendar.walk() if component.name == "VEVENT"]
    assert len(vevents) == 1
    assert str(vevents[0].get("summary")) == "Post Malone"
    assert str(calendar.get("x-published-ttl")) == "PT6H"
    assert b"REFRESH-INTERVAL;VALUE=DURATION:PT6H" in (tmp_path / "events.ics").read_bytes()


def test_writes_static_host_headers(tmp_path):
    write_outputs(tmp_path, [], [{"id": "official", "status": "ok"}])

    headers = (tmp_path / "_headers").read_text(encoding="utf-8")
    assert "/events.ics" in headers
    assert "Content-Type: text/calendar; charset=utf-8" in headers


def test_drops_end_before_start():
    sources = {"official": SourceConfig("official", "Official", "https://example.test", priority=10)}
    item = raw("Post Malone")
    item.end = datetime(2026, 9, 27, 0, 0, tzinfo=MALAYSIA_TZ)

    events = normalize_events(
        [item],
        sources,
        now=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
    )

    assert events[0].end is None
