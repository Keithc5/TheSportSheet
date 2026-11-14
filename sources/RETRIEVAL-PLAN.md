# Retrieval architecture and verification policy

## Implemented (14 November 2026)

1. **Early-week research window**: scheduled Monday, Tuesday and Wednesday at 05:17 UTC; Thursday through Sunday every six hours. All requests fetch the upcoming/current Friday–Sunday.
2. **Multi-competition discovery**: ESPN scoreboard adapters for PGA, DP World Tour, LPGA, Premier League, Champions League, international football, Nations League, NFL, Six Nations, URC, international rugby and F1. These are **candidate league identifiers**, not all confirmed working.
3. **Provenance**: each API event records provider URL and start time. Editorial TV entries record their separate source and coverage time.
4. **Conservative merging**: match only identical category, normalized full event name and local calendar date. Unmatched TV listings remain separate; ambiguous matches are not silently merged.
5. **Conflict flagging**: when independent start times differ, preserve both and flag in `data/source-health.json`. Never silently select a winner.
6. **Health monitoring**: log successful and failed requests, per-source counts, verified starts, TV-only listings, corroborated events and conflicts in `data/source-health.json`.
7. **Safety**: reject an all-sources-failed run rather than publish an empty schedule as if confirmed. Never synthesize a kickoff time from a TV listing.
8. **Automated checks**: unit tests run before the collector in GitHub Actions.

## Known gaps and next integrations

- **GAA**: official [GAA fixtures](https://www.gaa.ie/fixtures-results), provincial sites and [RTÉ GAA fixtures](https://www.rte.ie/sport/results/gaa/) are priority cross-checks. No general-purpose licensed machine-readable GAA API has been confirmed. Existing hand-checked weekend throw-ins are date-specific.
- **Rugby**: test the newly added URC and international rugby identifiers; add official URC, EPCR and international calendars as permitted.
- **Darts/snooker**: PDC and World Snooker Tour official session schedules; no recurring structured feed implemented.
- **Golf**: tournament listing dates are not daily round tee times or broadcast start times. Require distinct verified daily session times.
- **Irish TV**: investigate rights-compliant recurring schedules and broadcaster programme guides. Do not automatically scrape sites until usage terms are reviewed.
- **Independent corroboration**: ESPN alone is a single source. An extra request to the same provider is not independent corroboration.
- **Completeness**: no 75% claim without independent expected-event list by competition and weekend.

## Reliability rules

- Only show actual kick-off/throw-in/tee times when supported by source data.
- If start and coverage times conflict, preserve both and mark for review.
- Treat a successful empty response as **unknown completeness**, not proof there are no events.
- Record HTTP errors and provider failures for later investigation.
- Use local Europe/Dublin timezone for user display, retain offset-aware source timestamps.
- Never bypass paywalls, access restrictions, robots directives or API usage conditions.
