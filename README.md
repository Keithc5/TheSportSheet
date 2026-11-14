# The Sport Sheet

A personalised Friday–Sunday sports fixture guide for Ireland, designed for GitHub Pages.

## Features
- Friday, Saturday, Sunday and combined views
- Competition filters saved in the browser (horse racing off by default)
- Times in Europe/Dublin, including daylight-saving changes
- Scheduled GitHub Actions data refresh every six hours
- No fabricated fixtures or broadcaster listings

## Publish
1. Go to **Settings → Pages** in this repository.
2. Select **Deploy from a branch**, **main**, **/(root)** and save.
3. Go to **Actions → Refresh weekend fixtures → Run workflow** to populate the initial schedule.
4. If the workflow cannot push, enable **Read and write permissions** in **Settings → Actions → General → Workflow permissions**.
5. Visit https://keithc5.github.io/TheSportSheet/ once Pages has deployed.

## Coverage and limitations
The scraper uses unofficial ESPN endpoints for PGA Tour, DP World Tour, LPGA, Premier League, Champions League, World Cup, NFL, Six Nations and F1. These endpoints are not guaranteed to return all events and can change. The site deliberately does not substitute lower-tier events. GAA, darts, snooker and additional rugby feeds still require reliable providers. Golf tournaments may appear once rather than per daily round. TV broadcaster information for Ireland is not yet integrated and is left blank rather than guessed.

## Development
Run `python fetch.py` and `python -m http.server 8000` locally, then open http://localhost:8000.

## Data source strategy (November 2026)

- **ESPN public scoreboards:** automated fixture collection for selected football, NFL, golf and F1 feeds; endpoint availability and coverage vary.
- **Irish television guides:** a date-specific, source-attributed verified schedule is stored in `data/verified-tv-2026-11-13.json`. Sources: [The42](https://www.the42.ie/tv-guide-weekend-sport-180-7221059-Nov2026/) and [Irish Times](https://www.irishtimes.com/sport/2026/11/08/three-sporting-events-to-watch-this-week-your-handy-guide-to-sport-on-television/). It covers only November 13–15, 2026 and is **not** an automatically renewing TV feed.
- **Additional candidates for future licensed or permission-based integration:** TVGuide.ie sport listings and Onthebox Ireland sports schedules. Check site terms, robots rules, permitted extraction and data rights before building automated importers.
- **Quality:** A TV coverage start is not necessarily an event start; event entries tagged `TV coverage start · Ireland` should be interpreted accordingly. Some NFL fixture feed entries and TV coverage entries may represent the same game and appear separately.
- **Current gap:** reliable recurring Irish broadcaster mapping, additional rugby leagues, GAA, darts, snooker and golf per-round sessions. The weekend snapshot is populated, but the 75% threshold is not yet demonstrated for future weekends.
