from kl_stadium_calendar.extract import extract_events
from kl_stadium_calendar.models import DiscoveredSource, FetchResult, SourceConfig, SourceMethod


def discovered(method, text, content_type="text/html", url="https://example.test/events"):
    config = SourceConfig("example", "Example", url)
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


def test_extracts_live_nation_venue_page_events():
    html = """
    <html><body>
      <a href="/event/one-ok-rock-detox-asia-tour-2026-in-kuala-lumpur-kuala-lumpur-tickets-edp1624599">Find Tickets</a>
      <a href="/event/laufey-a-matter-of-time-tour-kuala-lumpur-tickets-edp1657037">Find Tickets</a>
      <main>
        <h1>Axiata Arena</h1>
        <p>Apr</p>
        <h2>ONE OK ROCK DETOX Asia Tour 2026 in Kuala Lumpur</h2>
        <span>Find Tickets</span>
        <p>29 April 2026 (Wednesday)</p>
        <p>Axiata Arena</p>
        <p>Jun</p>
        <h2>Laufey: A Matter of Time Tour</h2>
        <span>Find Tickets</span>
        <p>2 June 2026 (Tuesday)</p>
        <p>Time:</p>
        <p>8pm</p>
        <p>Axiata Arena</p>
      </main>
    </body></html>
    """

    events = extract_events(
        discovered(
            SourceMethod.HTML,
            html,
            url="https://www.livenation.my/axiata-arena-tickets-vdp1009607",
        )
    )

    assert len(events) == 2
    assert events[0].title == "ONE OK ROCK DETOX Asia Tour 2026 in Kuala Lumpur"
    assert events[0].venue == "Axiata Arena"
    assert events[0].url.endswith("tickets-edp1624599")
    assert events[1].start.hour == 20
