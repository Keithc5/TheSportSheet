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
