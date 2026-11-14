# Sports data source registry

This directory is the **single source of truth** for data providers investigated for TheSportSheet. Update `sources.json` whenever a source is discovered, tested, rejected or integrated.

## Workflow
1. Add a source with a stable `id`, original URL, source type, sports, data types, status and notes.
2. Mark untested sites as `candidate` — never `working` without evidence.
3. When testing, record `last_checked`, concrete request examples, limitations and relevant implementation `code`.
4. Check terms, robots, licensing, attribution and API quotas before enabling automated collection. Avoid bypassing access controls.
5. Preserve blocked and retired entries with the failure reason. Prefer official feeds, then permissioned APIs, then allowable web extraction.
6. Keep fixture kick-off times distinct from television coverage start times. Always normalize to Europe/Dublin at display time.
7. Deduplicate by competition, participating teams, start date and provider identifiers; retain source provenance.
8. Review missing competitions and stale sources weekly. Do not silently represent unavailable data as a fixture-free weekend.

## Data fields
- `id`: stable machine-readable identifier
- `url`: source page or endpoint pattern
- `type`: api, website, official-website
- `sports`: sports or competition coverage
- `data`: fixture, TV, results or other fields offered
- `status`: working, partially-working, used-once, candidate, blocked, retired
- `automation`: implemented, manual, not-implemented
- `notes`: limitations, failures, licensing and validation findings
- `last_checked`: ISO date or null
- `code`: implementing repository file or null

## Roadmap
**Priority 1:** recurring Irish TV listings (Sky Sports, TNT, RTÉ, TG4, Virgin Media, Premier Sports), including verified programme times.

**Priority 2:** PGA, DP World Tour and LPGA daily broadcast sessions; Premier League and major international football; rugby internationals and URC.

**Priority 3:** intercounty GAA, PDC majors, major snooker, F1 sessions, plus validation and completeness reporting.

Target: >=75% of expected top-tier events per weekend, measured against a separate reference inventory, not simply the number of rows returned by a single feed.
