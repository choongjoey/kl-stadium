# Source Notes

This file records the current source status and the reason for each important choice. All checks use public data only.

## Source Evaluation Order

For each enabled source, use the first available option:

1. iCal/ICS.
2. RSS or Atom.
3. Public API JSON.
4. JSON-LD in public HTML.
5. Conservative HTML fallback.

Do not add source-specific parsing until these options fail.

## Current Sources

Latest local run:

- 16 normalized upcoming events.
- 31 configured sources, including manual seeds.
- 0 failed sources.

### Manual Seed Events

Status: enabled.

`data/manual_events.json` contains confirmed events that live sources do not expose in a reliable machine-readable format yet. Keep each entry source-backed and small. Prefer official promoter, ticketing, venue, or sports-body pages.

### KL Events Calendar

Status: enabled.

Use `https://kleventscalendar.my/wp-json/tribe/events/v1/events?per_page=50&search=Bukit%20Jalil`.

Reason: the old `klevents.my` domain no longer resolves. The current site exposes The Events Calendar REST API through public WordPress headers, so API JSON is cleaner than parsing HTML. The source is narrowed to `Bukit Jalil` so venue filtering sees relevant candidates instead of the first page of unrelated Kuala Lumpur events.

### Songkick

Status: enabled.

Use `https://www.songkick.com/venues/94862-tm-national-stadium`.

Reason: the old configured venue ID redirected to an unrelated venue. Search results and live headers show venue ID `94862` as the Bukit Jalil / TM National Stadium page.

Note: Songkick's formal API requires approved access. The project currently reads only the public venue page and treats Songkick as a corroborating source.

`songkick-axiata-arena` reads the public Axiata/Unifi Arena venue page and contributes corroborating concert rows through embedded JSON-LD. `songkick-national-hockey-exo-2026` reads the public EXO event page as a National Hockey Stadium corroborating source.

### Concert Archives

Status: enabled.

Use `https://www.concertarchives.org/venues/axiata-arena--930485`.

Reason: the public venue table is readable through ordinary HTTP and provides date, title, venue, and location rows for Axiata Arena. It is fan-maintained, so it stays low priority and is used only as corroboration or as a hint for events missing from official feeds.

### Concerts50

Status: enabled.

Use `https://concerts50.com/venues/malaysia/kuala-lumpur/axiata-arena`.

Reason: the public venue page exposes event JSON-LD for Axiata Arena, including several events not yet visible on higher-priority official pages. It is restricted to JSON-LD because the page links unrelated JSON alternates such as the web app manifest.

### Expolah

Status: enabled for targeted event detail pages.

Use `https://expolah.com/event/gem-world-tour-2026-stadium-bukit-jalil/` and `https://expolah.com/event/sun-yanzi-in-concert-2026-bukit-jalil/`.

Reason: Expolah event detail pages are readable and expose Event JSON-LD. They are useful as low-priority alternates for Chinese/Mandopop events and for checking Chinese-language artist coverage. The broader Bukit Jalil location listing is not enabled yet because it still lists some rescheduled events under old dates; targeted detail pages are safer.

### Live Nation Malaysia

Status: enabled.

Use `https://www.livenation.my/event/allevents`.

Reason: `/show` returns 404. The current public all-events route is linked from the Live Nation homepage. It does not currently expose simple JSON-LD for every event, so it may report zero raw events until a dedicated parser is added.

`live-nation-post-malone-2026` is a targeted public HTML scrape of the official event detail page. It is restricted to HTML because the page's JSON-LD is not the event payload used by the extractor.

### Live Nation Axiata Arena

Status: enabled.

Use `https://www.livenation.my/axiata-arena-tickets-vdp1009607`.

Reason: Axiata Arena is part of the Bukit Jalil venue cluster and has its own Live Nation venue listing. The source is venue-restricted to Axiata Arena aliases.

`live-nation-lany-2026` is a targeted official event detail page for LANY at Unifi Arena. It is restricted to HTML for the same reason as other Live Nation detail pages.

### Star Planet

Status: enabled.

Use `https://starplanet.com.my/show/gemkl2026/`.

Reason: the public Star Planet event detail page exposes the event title, date, time, and venue in stable server-rendered HTML. It is restricted to HTML because the embedded JSON-LD is generic site metadata rather than an event object.

`starplanet-exo-2026` uses the same public HTML shape for EXO at National Hockey Stadium.

### EverythingBoleh

Status: enabled.

Use `https://everythingboleh.com/event/exo-concert-2026/`.

Reason: the public event detail page exposes event JSON-LD with date, time, venue, and address. It is low priority and restricted to JSON-LD because its iCal alternate currently returns 403 to ordinary public HTTP clients.

### iLasso Tickets

Status: enabled.

Use `https://www.ilassotickets.com/Default`.

Reason: the public default listing page is server-rendered HTML with event cards containing title, venue, and date. It is restricted to HTML because the page exposes no ICS, RSS, Atom, or JSON-LD feeds. Venue-alias filtering keeps only events at tracked venues.

### Hello Universe

Status: enabled.

Use `https://www.hellouniverse.asia/`.

Reason: the public homepage lists upcoming Bukit Jalil National Stadium events in server-rendered HTML, including date, time, venue, and short descriptions.

### Eventbrite

Status: enabled.

The public search page is readable and may expose JSON-LD, but it currently returns zero matching stadium events. If the Eventbrite API is added later, preserve direct Eventbrite links and publish future events only.

### Ticketmelon

Status: enabled.

The public search page is readable but currently yields no structured stadium events through the generic extractor.

### MFL and FAM

Status: enabled as monitored sports sources.

Use `https://www.malaysianfootballleague.com/Home/Sport` and `https://fam.org.my/men-team/results` in addition to the MFL and FAM homepages.

Reason: the official MFL matches page and FAM men's team match listing are more specific than the homepages. The current MFL page renders a public HTML shell without fixture rows, and the FAM page currently lists recent or older matches rather than future Bukit Jalil home fixtures. Keep them enabled with zero-event extraction while searching for an allowed fixture endpoint or adding a narrow parser once future stadium fixtures appear.

### Ticket2U

Status: generic legacy search skipped; public eventlisting API enabled.

`ticket2u-concerts` and `ticket2u-sports` use `https://www.ticket2u.com.my/api/api2.ashx` with the public `eventlisting` POST payload used by Ticket2U's own `/event/list` page. The source fetches paginated concert and sports listings, then the normal venue filter keeps only Bukit Jalil cluster events.

Reason: this is generic enough to discover Ticket2U-listed Axiata Arena, Unifi Arena, National Hockey Stadium, and Bukit Jalil stadium events without adding a source per artist. It also covers Malay, Indonesian, Indian, Chinese, K-pop, and sports listings when Ticket2U carries them.

The old `/events?...` search URL still returns a 404 shell, and the homepage can return Cloudflare 403 to normal public HTTP clients. Do not bypass this. Use the public eventlisting endpoint or search-indexed public event detail pages only.

### JamBase

Status: skipped.

JamBase returns a managed 403 challenge for normal public HTTP clients. Do not bypass this. Use it only for manual research unless a public, allowed feed or API is available.

## Adding A Source

1. Add the source to `data/sources.json`.
2. Prefer a venue-specific, organizer-specific, or API/feed URL.
3. Run the pipeline.
4. Inspect `public/sources.json`.
5. If the source is blocked, set `enabled` to `false` and add a `note`.
6. If extraction succeeds but venue matching rejects events, add a fixture and adjust aliases or parser logic.
