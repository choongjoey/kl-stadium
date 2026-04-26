# Architecture

This project turns public event data into static calendar files. It does not host a server and does not provide a website.

## Pipeline

1. Load confirmed seed events from `data/manual_events.json`.
2. Load source definitions from `data/sources.json`.
3. Skip disabled sources and record the reason in `sources.json`.
4. Fetch each enabled source with a normal public HTTP request.
5. Discover the simplest usable format: iCal, RSS, Atom, API JSON, JSON-LD, then HTML fallback.
6. Extract raw events.
7. Normalize venue aliases, timezone, dates, categories, URLs, and source metadata.
8. Drop historical events and events outside the tracked Bukit Jalil venue cluster.
9. Deduplicate same-date, same-venue title variants.
10. Write static files to `public/`.

## Public Data Boundary

Allowed:

- Public HTML pages.
- Public RSS, Atom, and iCal feeds.
- Public API endpoints linked from page headers or documented by the source.
- JSON-LD or structured data embedded in public pages.
- Search-indexed public event pages used as manual seed references.

Not allowed:

- Login-only pages.
- Queue or checkout-only data.
- CAPTCHA solving.
- Cloudflare or bot-challenge bypass.
- Aggressive crawling.
- Private APIs discovered from authenticated sessions.

If a source blocks ordinary HTTP access, mark it as disabled in `data/sources.json` and explain why in `note`.

## Event Model

The normalized event fields are:

- `id`: stable UID used by iCalendar clients.
- `title`: event name.
- `start`: Malaysia-local event start.
- `end`: optional event end.
- `venue`: normalized to one of the tracked Bukit Jalil venues.
- `address`: venue address when known.
- `url`: best source URL.
- `category`: broad category such as `Concert` or `Sports`.
- `description`: short source-backed note.
- `status`: normally `CONFIRMED`.
- `confidence`: derived from source priority.
- `sources`: source IDs, names, URLs, and extraction methods.

Tracked venues:

- Bukit Jalil National Stadium / TM Stadium Nasional
- Axiata Arena / Unifi Arena
- National Hockey Stadium

## Outputs

- `events.ics`: calendar subscription feed.
- `events.json`: normalized event list.
- `sources.json`: source audit log, including skipped and failed sources.
- `health.json`: generation timestamp, event count, source count, and failed source count.
- `_headers`: Cloudflare Pages response headers for calendar and JSON files.

Generated files are intentionally static so GitHub Pages or Cloudflare Pages can serve them without a backend.

## Calendar Subscriptions

Users should subscribe to the hosted `events.ics` URL instead of importing it. A subscription lets iOS and other calendar clients poll the URL for updates.

The feed includes:

- Stable `UID` values, so clients update existing events.
- `X-PUBLISHED-TTL:PT6H`.
- `REFRESH-INTERVAL;VALUE=DURATION:PT6H`.
- `X-WR-CALNAME` and `X-WR-CALDESC`.

Client polling intervals are controlled by the calendar app. The TTL and refresh fields are hints, not guarantees.
