"""Retrieve top-tier weekend fixtures from ESPN's unofficial public endpoints.
Missing feeds remain empty; no events or Irish broadcasters are invented.
"""
import datetime as dt
import json
import pathlib
import urllib.request
import concurrent.futures
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Dublin")
LEAGUES = {
    "golf-pga": ("golf", "pga", "Golf", "PGA Tour"),
    "golf-euro": ("golf", "eur", "Golf", "DP World Tour"),
    "golf-lpga": ("golf", "lpga", "Golf", "LPGA"),
    "soccer-eng.1": ("soccer", "eng.1", "Football", "Premier League"),
    "soccer-uefa.champions": ("soccer", "uefa.champions", "Football", "Champions League"),
    "soccer-fifa.world": ("soccer", "fifa.world", "Football", "International"),
    "football-nfl": ("football", "nfl", "NFL", "NFL"),
    "rugby": ("rugby", "six-nations", "Rugby", "Six Nations"),
    "racing-f1": ("racing", "f1", "Formula 1", "Formula 1"),
}

def get(category, day):
    sport, league, label, competition = LEAGUES[category]
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates={day:%Y%m%d}&limit=250"
    req = urllib.request.Request(url, headers={"User-Agent": "TheSportSheet/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            payload = json.load(response)
    except Exception as exc:
        print("Unavailable", category, day, repr(exc))
        return []
    output = []
    for event in payload.get("events", []):
        try:
            start = dt.datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
            if start.astimezone(TZ).date() != day:
                continue
            match = (event.get("competitions") or [{}])[0]
            competitors = match.get("competitors") or []
            teams = [c.get("team", {}).get("displayName") or c.get("athlete", {}).get("displayName") for c in competitors]
            teams = [team for team in teams if team]
            name = " vs ".join(teams[:2]) if len(teams) == 2 else event.get("name") or event.get("shortName") or competition
            output.append({
                "id": f'{category}-{event.get("id")}', "category": category,
                "sport": label, "competition": competition, "name": name,
                "start": start.isoformat(), "start_time": start.isoformat(), "start_source": url, "detail": "", "channel": ""
            })
        except (KeyError, TypeError, ValueError):
            continue
    return output

today = dt.datetime.now(TZ).date()
friday = today + dt.timedelta(days=(4 - today.weekday()) % 7)
if today.weekday() in (5, 6):
    friday = today - dt.timedelta(days=today.weekday() - 4)
days = [friday + dt.timedelta(days=i) for i in range(3)]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    futures = [pool.submit(get, category, day) for category in LEAGUES for day in days]
    events = [event for future in futures for event in future.result()]
# Verified, date-specific Irish television coverage supplements fixture feeds.
# Keep TV programme starts distinct from match kick-off times.
verified_path = pathlib.Path(__file__).parent / "data" / "verified-tv-2026-11-13.json"
if verified_path.exists():
    for event in json.loads(verified_path.read_text()):
        if dt.datetime.fromisoformat(event["start"]).astimezone(TZ).date() in days:
            # These entries record broadcast starts, not event start times.
            event["coverage_time"] = event.get("coverage_time", event["start"] if not event.get("start_time") else None)
            event.setdefault("start_time", None)
            event["coverage_source"] = event.get("source") if event.get("coverage_time") else None
            events.append(event)
unique = {event["id"]: event for event in events}
path = pathlib.Path(__file__).parent / "data" / "events.json"
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps({
    "updated": dt.datetime.now(dt.timezone.utc).isoformat(),
    "events": list(unique.values())
}, indent=2) + "\n")
print("Wrote", len(unique), "events")
