from kl_stadium_calendar.discover import discover_source
from kl_stadium_calendar.models import FetchResult, SourceConfig, SourceMethod


class FakeFetcher:
    def __init__(self, responses):
        self.responses = responses
        self.posted = []

    def get(self, url):
        return self.responses[url]

    def post_json(self, url, payload):
        self.posted.append((url, payload))
        return self.responses[(url, payload["data"]["currentpage"])]


def result(url, text, content_type="text/html"):
    return FetchResult(
        url=url,
        final_url=url,
        status_code=200,
        content_type=content_type,
        text=text,
    )


def test_prefers_ics_alternate_before_json_ld():
    html = """
    <html>
      <head>
        <link rel="alternate" type="application/rss+xml" href="/feed.xml">
        <link rel="alternate" type="text/calendar" href="/events.ics">
        <script type="application/ld+json">{"@type":"Event","name":"HTML Event"}</script>
      </head>
    </html>
    """
    fetcher = FakeFetcher(
        {
            "https://example.test/events": result("https://example.test/events", html),
            "https://example.test/feed.xml": result(
                "https://example.test/feed.xml", "<rss><channel /></rss>", "application/rss+xml"
            ),
            "https://example.test/events.ics": result(
                "https://example.test/events.ics", "BEGIN:VCALENDAR\nEND:VCALENDAR", "text/calendar"
            ),
        }
    )

    discovered = discover_source(SourceConfig("example", "Example", "https://example.test/events"), fetcher)

    assert discovered.method == SourceMethod.ICS
    assert discovered.url == "https://example.test/events.ics"


def test_uses_json_ld_before_html_fallback():
    html = '<script type="application/ld+json">{"@type":"Event","name":"JSON-LD Event"}</script>'
    fetcher = FakeFetcher({"https://example.test/events": result("https://example.test/events", html)})

    discovered = discover_source(SourceConfig("example", "Example", "https://example.test/events"), fetcher)

    assert discovered.method == SourceMethod.JSON_LD


def test_discovers_paginated_post_json_source():
    first = """
    {
      "data": [
        {"row": {"titlename": "First", "datefrom": "2026-06-06T20:00:00"}}
      ]
    }
    """
    second = """
    {
      "data": [
        {"row": {"titlename": "Second", "datefrom": "2026-06-07T20:00:00"}}
      ]
    }
    """
    fetcher = FakeFetcher(
        {
            ("https://example.test/api", 1): result("https://example.test/api", first, "application/json"),
            ("https://example.test/api", 2): result(
                "https://example.test/api", second, "application/json"
            ),
        }
    )
    source = SourceConfig(
        "example",
        "Example",
        "https://example.test/api",
        request_json={"method": "eventlisting", "data": {"currentpage": 1}},
        request_pages=2,
    )

    discovered = discover_source(source, fetcher)

    assert discovered.method == SourceMethod.API_JSON
    assert "First" in discovered.fetched.text
    assert "Second" in discovered.fetched.text
