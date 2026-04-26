from kl_stadium_calendar.extract import extract_events
from kl_stadium_calendar.models import DiscoveredSource, FetchResult, SourceConfig, SourceMethod


def discovered(method, text, content_type="text/html"):
    config = SourceConfig("example", "Example", "https://example.test/events")
    fetched = FetchResult(
        url=config.url,
        final_url=config.url,
        status_code=200,
        content_type=content_type,
        text=text,
    )
    return DiscoveredSource(config, method, config.url, "test", fetched)


def test_extracts_json_ld_event():
    html = """
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "MusicEvent",
      "name": "Post Malone",
      "startDate": "2026-09-27T20:00:00+08:00",
      "location": {
        "@type": "Place",
        "name": "TM Stadium Nasional",
        "address": {
          "addressLocality": "Bukit Jalil",
          "addressCountry": "MY"
        }
      },
      "url": "https://example.test/post-malone"
    }
    </script>
    """

    events = extract_events(discovered(SourceMethod.JSON_LD, html))

    assert len(events) == 1
    assert events[0].title == "Post Malone"
    assert events[0].venue == "TM Stadium Nasional"
    assert events[0].start.year == 2026


def test_extracts_ics_event():
    ics = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:test@example
DTSTART:20260606T200000Z
SUMMARY:G.E.M. I AM GLORIA
LOCATION:Bukit Jalil National Stadium
URL:https://example.test/gem
END:VEVENT
END:VCALENDAR
"""

    events = extract_events(discovered(SourceMethod.ICS, ics, "text/calendar"))

    assert len(events) == 1
    assert events[0].title == "G.E.M. I AM GLORIA"
    assert events[0].url == "https://example.test/gem"


def test_extracts_the_events_calendar_api_event():
    payload = """
    {
      "events": [
        {
          "title": "G.E.M. I AM GLORIA World Tour 2.0",
          "start_date": "2026-06-06 20:00:00",
          "end_date": "2026-06-06 22:00:00",
          "url": "https://example.test/gem",
          "venue": {
            "venue": "National Stadium Bukit Jalil",
            "address": "Jalan Barat, Bukit Jalil",
            "city": "Kuala Lumpur",
            "country": "Malaysia"
          },
          "categories": [{"name": "Entertainment"}]
        }
      ]
    }
    """

    events = extract_events(discovered(SourceMethod.API_JSON, payload, "application/json"))

    assert len(events) == 1
    assert events[0].start.year == 2026
    assert events[0].venue == "National Stadium Bukit Jalil"
    assert events[0].category == "Entertainment"
