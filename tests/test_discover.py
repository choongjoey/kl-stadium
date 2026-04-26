from kl_stadium_calendar.discover import discover_source
from kl_stadium_calendar.models import FetchResult, SourceConfig, SourceMethod


class FakeFetcher:
    def __init__(self, responses):
        self.responses = responses

    def get(self, url):
        return self.responses[url]


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

