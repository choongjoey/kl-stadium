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

### Live Nation Malaysia

Status: enabled.

Use `https://www.livenation.my/event/allevents`.

Reason: `/show` returns 404. The current public all-events route is linked from the Live Nation homepage. It does not currently expose simple JSON-LD for every event, so it may report zero raw events until a dedicated parser is added.

### Live Nation Axiata Arena

Status: enabled.

Use `https://www.livenation.my/axiata-arena-tickets-vdp1009607`.

Reason: Axiata Arena is part of the Bukit Jalil venue cluster and has its own Live Nation venue listing. The source is venue-restricted to Axiata Arena aliases.

### Eventbrite

Status: enabled.

The public search page is readable and may expose JSON-LD, but it currently returns zero matching stadium events. If the Eventbrite API is added later, preserve direct Eventbrite links and publish future events only.

### Ticketmelon

Status: enabled.

The public search page is readable but currently yields no structured stadium events through the generic extractor.

### MFL and FAM

Status: enabled.

Both public homepages are readable. They currently need sport-specific fixture parsing or better fixture endpoints before they can contribute events automatically.

### Ticket2U

Status: skipped.

The generic Ticket2U search URL returns 404, and the homepage returns Cloudflare 403 to normal public HTTP clients. Do not bypass this. Use search-indexed public event detail pages as manual seed references unless Ticket2U exposes a stable public feed or API.

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
