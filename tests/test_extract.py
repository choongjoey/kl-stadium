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


def test_extracts_json_ld_ignores_site_metadata():
    html = """
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@graph": [
        {"@type": "Organization", "name": "Promoter"},
        {"@type": "BreadcrumbList", "name": "All Events"},
        {
          "@type": "MusicEvent",
          "name": "EXO PLANET #6",
          "startDate": "2026-06-20T20:00:00+08:00",
          "location": {"@type": "Place", "name": "National Hockey Stadium"}
        }
      ]
    }
    </script>
    """

    events = extract_events(discovered(SourceMethod.JSON_LD, html))

    assert len(events) == 1
    assert events[0].title == "EXO PLANET #6"


def test_ignores_concerts50_venue_page_address():
    html = """
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "MusicEvent",
      "name": "M. Nasir",
      "startDate": "2026-07-04T20:30:00+08:00",
      "location": {
        "@type": "Place",
        "name": "Axiata Arena",
        "address": {
          "streetAddress": "L2-E-10, Enterprise 4, Technology Park Malaysia, Lebuhraya Bukit Jalil, Bukit Jalil",
          "addressLocality": "Kuala Lumpur",
          "postalCode": "57000",
          "addressCountry": "MY"
        }
      },
      "url": "https://concerts50.com/events/m-nasir"
    }
    </script>
    """

    events = extract_events(
        discovered(
            SourceMethod.JSON_LD,
            html,
            url="https://concerts50.com/venues/malaysia/kuala-lumpur/axiata-arena",
        )
    )

    assert len(events) == 1
    assert events[0].venue == "Axiata Arena"
    assert events[0].address is None


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


def test_extracts_ticket2u_eventlisting_api_rows():
    payload = """
    {
      "data": [
        {
          "row": {
            "titlename": "DEWA 19 - Cintaku TerTinggal di Malaysia",
            "datefrom": "2026-06-06T20:30:00",
            "dateto": "2026-06-06T22:30:00",
            "locname": "Axiata Arena Bukit Jalil",
            "eventcat": "Entertainments, Concerts, and Shows Event",
            "link": "event/48826/dewa-19-cintaku-tertinggal-di-malaysia"
          }
        }
      ]
    }
    """

    events = extract_events(
        discovered(
            SourceMethod.API_JSON,
            payload,
            "application/json",
            url="https://www.ticket2u.com.my/api/api2.ashx",
        )
    )

    assert len(events) == 1
    assert events[0].title == "DEWA 19 - Cintaku TerTinggal di Malaysia"
    assert events[0].start.hour == 20
    assert events[0].venue == "Axiata Arena Bukit Jalil"
    assert events[0].url == "https://www.ticket2u.com.my/event/48826/dewa-19-cintaku-tertinggal-di-malaysia"


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
    assert events[0].venue == "Unifi Arena"
    assert events[0].url.endswith("tickets-edp1624599")
    assert events[1].start.hour == 20


def test_extracts_live_nation_event_detail_page():
    html = """
    <html><body>
      <h1>Post Malone Presents The BIG Stadium World Tour</h1>
      <p>Show Date:</p>
      <p>27 September 2026</p>
      <p>(Sunday), 8:30PM</p>
      <p>Venue Name:</p>
      <p>TM Stadium Nasional (Previously known as National Stadium Bukit Jalil)</p>
      <p>Venue Address:</p>
      <p>Jalan Barat, Bukit Jalil, 57000 Kuala Lumpur</p>
    </body></html>
    """

    events = extract_events(
        discovered(
            SourceMethod.HTML,
            html,
            url="https://www.livenation.my/event/post-malone-kuala-lumpur-tickets",
        )
    )

    assert len(events) == 1
    assert events[0].title == "Post Malone Presents The BIG Stadium World Tour"
    assert events[0].start.hour == 20
    assert events[0].start.minute == 30
    assert events[0].venue.startswith("TM Stadium Nasional")


def test_extracts_live_nation_event_detail_page_with_inline_weekday_and_time():
    html = """
    <html><body>
      <h1>LANY: soft world tour</h1>
      <p>Show Date:</p>
      <p>1 November 2026 (Sunday), 8PM</p>
      <p>Venue Name:</p>
      <p>Unifi Arena</p>
      <p>Venue Address:</p>
      <p>Bukit Jalil, Kuala Lumpur</p>
    </body></html>
    """

    events = extract_events(
        discovered(
            SourceMethod.HTML,
            html,
            url="https://www.livenation.my/event/lany-soft-world-tour-kuala-lumpur-tickets",
        )
    )

    assert len(events) == 1
    assert events[0].start.hour == 20
    assert events[0].venue == "Unifi Arena"


def test_extracts_starplanet_show_page():
    html = """
    <html><body>
      <h1>06 June: G.E.M. I AM GLORIA World Tour 2.0 - Kuala Lumpur 2026</h1>
      <p>06 Jun 2026, Sat 8:00 pm</p>
      <p>TM National Stadium Bukit Jalil, KL</p>
    </body></html>
    """

    events = extract_events(
        discovered(SourceMethod.HTML, html, url="https://starplanet.com.my/show/gemkl2026/")
    )

    assert len(events) == 1
    assert events[0].title == "G.E.M. I AM GLORIA World Tour 2.0 - Kuala Lumpur 2026"
    assert events[0].start.hour == 20
    assert events[0].venue == "TM National Stadium Bukit Jalil, KL"


def test_extracts_hello_universe_upcoming_events():
    html = """
    <html><body>
      <h2>Upcoming Events</h2>
      <p>Nov</p><p>19</p>
      <p>Rock</p><p>International</p><p>Concert</p>
      <h3>My Chemical Romance</h3>
      <p>Live in Kuala Lumpur 2026 - Day 1</p>
      <p>08:00 PM</p>
      <p>Bukit Jalil National Stadium</p>
      <p>The legendary rock band returns.</p>
      <h2>Who We Are</h2>
    </body></html>
    """

    events = extract_events(
        discovered(SourceMethod.HTML, html, url="https://www.hellouniverse.asia/")
    )

    assert len(events) == 1
    assert events[0].title == "My Chemical Romance Live in Kuala Lumpur 2026 - Day 1"
    assert events[0].start.month == 11
    assert events[0].venue == "Bukit Jalil National Stadium"


def test_extracts_concert_archives_venue_table():
    html = """
    <html><body>
      <table id="band-show-table-condensed">
        <tbody>
          <tr>
            <td><span>Jun 06, 2026</span></td>
            <td>
              <strong><a href="/concerts/dewa-19">Dewa 19</a></strong>
              <p class="tour-title">Dewa 19 - Cintaku Tertinggal di Malaysia</p>
            </td>
            <td><a>Axiata Arena</a></td>
            <td><a>Bukit Jalil, Kuala Lumpur, Malaysia</a></td>
            <td></td>
          </tr>
        </tbody>
      </table>
    </body></html>
    """

    events = extract_events(
        discovered(
            SourceMethod.HTML,
            html,
            url="https://www.concertarchives.org/venues/axiata-arena--930485",
        )
    )

    assert len(events) == 1
    assert events[0].title == "Dewa 19 - Cintaku Tertinggal di Malaysia"
    assert events[0].venue == "Axiata Arena"
    assert events[0].url == "https://www.concertarchives.org/concerts/dewa-19"


def test_extracts_ticket2u_event_detail_page():
    html = """
    <html><head><title>DEWA 19 - Cintaku TerTinggal di Malaysia | Ticket2u</title></head>
    <body>
      <p>DEWA 19 - Cintaku TerTinggal di Malaysia</p>
      <p>{{$t("Ticket")}}</p>
      <p>Axiata Arena Bukit Jalil</p>
      <p>L2-E-10, Enterprise 4, Technology Park Malaysia, Lebuhraya Bukit Jalil, Bukit Jalil</p>
      <p>Map</p>
      <p>Waze</p>
      <p>Google Maps</p>
      <p>Axiata Arena Bukit Jalil</p>
      <p>6 Jun 2026, 8:30PM</p>
      <p>#Entertainments, Concerts, and Shows Event</p>
      <p>#Concert</p>
    </body></html>
    """

    events = extract_events(
        discovered(SourceMethod.HTML, html, url="https://www.ticket2u.com.my/event/48826")
    )

    assert len(events) == 1
    assert events[0].title == "DEWA 19 - Cintaku TerTinggal di Malaysia"
    assert events[0].start.hour == 20
    assert events[0].start.minute == 30
    assert events[0].venue == "Axiata Arena Bukit Jalil"
