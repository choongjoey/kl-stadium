# Bukit Jalil Stadium Calendar

Aggregates upcoming events for the Bukit Jalil venue cluster and publishes static calendar files.

The project intentionally has no website UI. The public contract is:

- `public/events.ics` - iCalendar subscription feed
- `public/events.json` - normalized events
- `public/sources.json` - source fetch and parser audit
- `public/health.json` - run health summary

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the pipeline design and [docs/SOURCES.md](docs/SOURCES.md) for source maintenance notes.

Tracked venues:

- Bukit Jalil National Stadium / TM Stadium Nasional
- Axiata Arena / Unifi Arena
- National Hockey Stadium

## Progress

Current generated status:

- 16 normalized upcoming events
- 30 configured sources, including manual seeds
- 0 failed sources in the latest local run

Working live sources now include Live Nation, Star Planet, Hello Universe, KL Events Calendar, Songkick, Concert Archives, Concerts50, EverythingBoleh, Expolah, and generic Ticket2U concert/sports listings. Blocked or unsuitable sources stay disabled or documented instead of using workarounds.

## Calendar Subscription

Subscribe to the hosted `events.ics` URL. Do not download and import the file, because imports are one-time copies.

For iOS:

1. Copy the published `https://.../events.ics` URL.
2. Open Calendar settings.
3. Add a subscription calendar.
4. Paste the URL.

You can also use the `webcal://` form of the same URL if the host supports opening calendar subscription links.

## Source Policy

Every configured source is evaluated in this order:

1. Native iCal/ICS feed
2. RSS/Atom feed
3. Official JSON/API endpoint
4. JSON-LD embedded in HTML
5. Stable HTML fallback parsing

Full site-specific parsing should be added only when none of the simpler formats are available.

The project uses public data only. Do not bypass login walls, queues, Cloudflare challenges, CAPTCHAs, rate limits, or anti-bot pages. If a source blocks normal HTTP access, mark it as skipped and document the reason.

## Local Run

```bash
rtk python3 -m venv .venv
rtk .venv/bin/pip install -e ".[dev]"
rtk .venv/bin/kl-stadium-calendar --output public
```

Run tests:

```bash
rtk .venv/bin/pytest
```

Run lint:

```bash
rtk .venv/bin/ruff check .
```

## Deployment

The included GitHub Actions workflow runs daily and publishes `public/` to GitHub Pages. Enable Pages in the repository with GitHub Actions as the source.

If `https://choongjoey.github.io/kl-stadium/events.ics` returns a GitHub Pages 404 while the workflow succeeds, check the repository's Pages setting. The source must be `GitHub Actions`; `Deploy from a branch` serves the README/Jekyll site and will not expose the generated `public/` files.

Cloudflare Pages can serve the same `public/` directory. The generated `_headers` file sets `events.ics` to `text/calendar` and adds cache headers. GitHub Pages ignores `_headers`, but still serves the static file at a stable URL.

## Source Configuration

Edit `data/sources.json` to add or tune sources. Prefer source URLs that are already narrowed to the stadium, organizer, or event category.

Each source supports:

- `id`: stable source identifier
- `name`: display name
- `url`: page/feed/API endpoint
- `priority`: lower numbers win conflicts
- `allowed_methods`: optional list of method names
- `venue_aliases`: optional venue names that should be accepted for that source
- `enabled`: optional boolean; set `false` for blocked or unsuitable public sources
- `note`: optional explanation for skipped sources
- `request_json`: optional POST JSON payload for public JSON endpoints
- `request_pages`: optional page count for paginated POST JSON sources

`data/manual_events.json` contains high-confidence seed events from official or near-official pages. Keep this file small and source-backed; it exists because several Malaysian event sites do not expose reliable feeds or JSON-LD.

## Maintenance Loop

1. Run `rtk .venv/bin/kl-stadium-calendar --output public`.
2. Check `public/health.json` for event and failure counts.
3. Check `public/sources.json` for each source's method and error.
4. Promote confirmed events from official pages into `data/manual_events.json` only when live extraction cannot read them.
5. Add tests when a new extractor or source shape is introduced.
