from datetime import date, datetime
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


def test_keeps_specific_bukit_jalil_venue():
    sources = {"official": SourceConfig("official", "Official", "https://example.test", priority=10)}
    item = raw("ONE OK ROCK")
    item.venue = "Axiata Arena"

    events = normalize_events(
        [item],
        sources,
        now=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
    )

    assert len(events) == 1
    assert events[0].venue == "Axiata Arena"


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


def test_dedupes_titles_with_venue_suffixes():
    sources = {
        "official": SourceConfig("official", "Official", "https://example.test", priority=10),
        "aggregator": SourceConfig("aggregator", "Aggregator", "https://example.test", priority=80),
    }
    event_a = raw("EXO PLANET #6 - EXhOrizon in KUALA LUMPUR", "official")
    event_a.venue = "National Hockey Stadium"
    event_b = raw("EXO @ National Hockey Stadium", "aggregator")
    event_b.venue = "National Hockey Stadium"

    events = dedupe_events(
        normalize_events(
            [event_a, event_b],
            sources,
            now=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
        )
    )

    assert len(events) == 1
    assert len(events[0].sources) == 2


def test_dedupes_generic_event_listing_title():
    sources = {
        "official": SourceConfig("official", "Official", "https://example.test", priority=10),
        "aggregator": SourceConfig("aggregator", "Aggregator", "https://example.test", priority=80),
    }
    event_a = raw("EXO PLANET #6 - EXhOrizon in KUALA LUMPUR", "official")
    event_a.venue = "National Hockey Stadium"
    event_b = raw("EXO Concert 2026 (Kuala Lumpur, Malaysia)", "aggregator")
    event_b.venue = "National Hockey Stadium"

    events = dedupe_events(
        normalize_events(
            [event_a, event_b],
            sources,
            now=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
        )
    )

    assert len(events) == 1
    assert len(events[0].sources) == 2


def test_dedupes_stylized_artist_name_listing():
    sources = {
        "official": SourceConfig("official", "Official", "https://example.test", priority=10),
        "aggregator": SourceConfig("aggregator", "Aggregator", "https://example.test", priority=80),
    }
    event_a = raw("DATO M.N47IR CIPTA 4", "official")
    event_a.venue = "Axiata Arena"
    event_a.start = datetime(2026, 5, 16, 20, 30, tzinfo=MALAYSIA_TZ)
    event_a.end = datetime(2026, 5, 16, 23, 0, tzinfo=MALAYSIA_TZ)
    event_b = raw("M. Nasir", "aggregator")
    event_b.venue = "Axiata Arena"
    event_b.start = datetime(2026, 5, 16, 20, 30, tzinfo=MALAYSIA_TZ)

    events = dedupe_events(
        normalize_events(
            [event_a, event_b],
            sources,
            now=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
        )
    )

    assert len(events) == 1
    assert len(events[0].sources) == 2
    assert events[0].end == datetime(2026, 5, 16, 23, 0, tzinfo=MALAYSIA_TZ)


def test_keeps_distinct_overlapping_events():
    sources = {
        "official": SourceConfig("official", "Official", "https://example.test", priority=10),
        "aggregator": SourceConfig("aggregator", "Aggregator", "https://example.test", priority=80),
    }
    event_a = raw("Post Malone", "official")
    event_a.venue = "Axiata Arena"
    event_a.start = datetime(2026, 9, 27, 20, 0, tzinfo=MALAYSIA_TZ)
    event_a.end = datetime(2026, 9, 27, 22, 30, tzinfo=MALAYSIA_TZ)
    event_b = raw("Corporate Dinner", "aggregator")
    event_b.venue = "Axiata Arena"
    event_b.start = datetime(2026, 9, 27, 20, 30, tzinfo=MALAYSIA_TZ)
    event_b.end = datetime(2026, 9, 27, 23, 0, tzinfo=MALAYSIA_TZ)

    events = dedupe_events(
        normalize_events(
            [event_a, event_b],
            sources,
            now=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
        )
    )

    assert len(events) == 2


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


def test_writes_multi_day_events_as_all_day(tmp_path):
    sources = {"official": SourceConfig("official", "Official", "https://example.test", priority=10)}
    item = raw("Malaysia Autoshow")
    item.start = datetime(2026, 9, 27, 10, 0, tzinfo=MALAYSIA_TZ)
    item.end = datetime(2026, 9, 29, 18, 0, tzinfo=MALAYSIA_TZ)
    events = normalize_events(
        [item],
        sources,
        now=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
    )

    write_outputs(tmp_path, events, [{"id": "official", "status": "ok"}])

    ics = (tmp_path / "events.ics").read_bytes()
    calendar = Calendar.from_ical(ics)
    vevent = next(component for component in calendar.walk() if component.name == "VEVENT")
    assert vevent.decoded("dtstart") == date(2026, 9, 27)
    assert vevent.decoded("dtend") == date(2026, 9, 30)
    assert b"DTSTART;VALUE=DATE:20260927" in ics
    assert b"DTEND;VALUE=DATE:20260930" in ics


def test_writes_midnight_ended_multi_day_events_with_exclusive_end_date(tmp_path):
    sources = {"official": SourceConfig("official", "Official", "https://example.test", priority=10)}
    item = raw("Tournament")
    item.start = datetime(2026, 9, 27, 10, 0, tzinfo=MALAYSIA_TZ)
    item.end = datetime(2026, 9, 29, 0, 0, tzinfo=MALAYSIA_TZ)
    events = normalize_events(
        [item],
        sources,
        now=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
    )

    write_outputs(tmp_path, events, [{"id": "official", "status": "ok"}])

    calendar = Calendar.from_ical((tmp_path / "events.ics").read_bytes())
    vevent = next(component for component in calendar.walk() if component.name == "VEVENT")
    assert vevent.decoded("dtstart") == date(2026, 9, 27)
    assert vevent.decoded("dtend") == date(2026, 9, 29)


def test_preserves_timed_overnight_events(tmp_path):
    sources = {"official": SourceConfig("official", "Official", "https://example.test", priority=10)}
    item = raw("Late Night Concert")
    item.start = datetime(2026, 9, 27, 20, 30, tzinfo=MALAYSIA_TZ)
    item.end = datetime(2026, 9, 28, 1, 0, tzinfo=MALAYSIA_TZ)
    events = normalize_events(
        [item],
        sources,
        now=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Kuala_Lumpur")),
    )

    write_outputs(tmp_path, events, [{"id": "official", "status": "ok"}])

    ics = (tmp_path / "events.ics").read_bytes()
    calendar = Calendar.from_ical(ics)
    vevent = next(component for component in calendar.walk() if component.name == "VEVENT")
    assert vevent.decoded("dtstart") == datetime(2026, 9, 27, 20, 30, tzinfo=MALAYSIA_TZ)
    assert vevent.decoded("dtend") == datetime(2026, 9, 28, 1, 0, tzinfo=MALAYSIA_TZ)
    assert b"DTSTART;VALUE=DATE" not in ics
    assert b"DTEND;VALUE=DATE" not in ics


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
