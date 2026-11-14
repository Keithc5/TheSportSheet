"""Collect weekend fixtures with provenance, conservative validation and source health.
Run with Python 3.12. No third-party dependencies. Never infer missing start times.
"""
import concurrent.futures
import datetime as dt
import json
import pathlib
import re
import urllib.request
from collections import Counter, defaultdict
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).parent
TZ = ZoneInfo("Europe/Dublin")
ESPN = "https://site.api.espn.com/apis/site/v2/sports"
LEAGUES = {
 "golf-pga": ("golf","pga","Golf","PGA Tour"),
 "golf-euro": ("golf","eur","Golf","DP World Tour"),
 "golf-lpga": ("golf","lpga","Golf","LPGA"),
 "soccer-eng.1": ("soccer","eng.1","Football","Premier League"),
 "soccer-uefa.champions": ("soccer","uefa.champions","Football","Champions League"),
 "soccer-fifa.world": ("soccer","fifa.world","Football","International"),
 "soccer-nations": ("soccer","uefa.nations","Football","UEFA Nations League"),
 "football-nfl": ("football","nfl","NFL","NFL"),
 "rugby": ("rugby","six-nations","Rugby","Six Nations"),
 "rugby-urc": ("rugby","united-rugby-championship","Rugby","URC"),
 "rugby-autumn": ("rugby","international","Rugby","International Rugby"),
 "racing-f1": ("racing","f1","Formula 1","Formula 1"),
}
def weekend():
 today = dt.datetime.now(TZ).date()
 friday = today + dt.timedelta(days=(4-today.weekday())%7)
 if today.weekday() in (5,6): friday = today-dt.timedelta(days=today.weekday()-4)
 return [friday+dt.timedelta(days=i) for i in range(3)]

def fetch_one(item):
 category,day = item
 sport,league,label,competition=LEAGUES[category]
 url=f"{ESPN}/{sport}/{league}/scoreboard?dates={day:%Y%m%d}&limit=250"
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"TheSportSheet/1.1 (public fixture research)","Accept":"application/json"})
  with urllib.request.urlopen(req,timeout=18) as resp: payload=json.load(resp)
  if not isinstance(payload.get("events"),list): raise ValueError("No events array")
 except Exception as exc:
  return [],{"source":category,"date":str(day),"status":"error","message":str(exc)[:180],"count":0}
 result=[]
 for event in payload["events"]:
  try:
   start=dt.datetime.fromisoformat(event["date"].replace("Z","+00:00"))
   if start.astimezone(TZ).date()!=day: continue
   if not event.get("id"): continue
   match=(event.get("competitions") or [{}])[0]
   competitors=match.get("competitors") or []
   teams=[c.get("team",{}).get("displayName") or c.get("athlete",{}).get("displayName") for c in competitors]
   teams=[t for t in teams if t]
   name=" vs ".join(teams[:2]) if len(teams)==2 else event.get("name") or event.get("shortName") or competition
   if not name: continue
   result.append({"id":f'{category}-{event["id"]}',"category":category,"sport":label,
    "competition":competition,"name":name,"start":start.isoformat(),"start_time":start.isoformat(),
    "start_source":url,"sources":[{"provider":"espn","url":url,"field":"start_time"}],
    "verification":"single-source","detail":"","channel":""})
  except (KeyError,TypeError,ValueError,AttributeError): continue
 return result,{"source":category,"date":str(day),"status":"ok","count":len(result),"url":url}

def norm(name):
 return re.sub(r"[^a-z0-9]+"," ",name.casefold()).strip()
def attach_tv(events,days):
 """Only exact-name, exact-date matches are safe. Never guess from a broadcast title."""
 index=defaultdict(list)
 for event in events:
  key=(event["category"],norm(event["name"]),event["start"][:10])
  index[key].append(event)
 unmatched=[]
 p=ROOT/"data"/"verified-tv-2026-11-13.json"
 if not p.exists(): return unmatched
 for tv in json.loads(p.read_text()):
  try: date=dt.datetime.fromisoformat(tv["start"]).astimezone(TZ).date()
  except (KeyError,ValueError): continue
  if date not in days: continue
  tv=dict(tv)
  tv.setdefault("coverage_time",tv["start"] if not tv.get("start_time") else None)
  tv.setdefault("start_time",None)
  tv.setdefault("coverage_source",tv.get("source") if tv.get("coverage_time") else None)
  tv.setdefault("start_source",None)
  tv["verification"]="single-source" if tv.get("start_time") else "coverage-only"
  tv["sources"]=[{"provider":"editorial-tv","url":tv.get("source"),"field":"coverage_time"}]
  if tv.get("start_source"):
   tv["sources"].append({"provider":"official-or-broadcaster","url":tv["start_source"],"field":"start_time"})
   tv["verification"]="cross-referenced"
  matches=index.get((tv["category"],norm(tv["name"]),str(date)),[])
  if len(matches)==1:
   target=matches[0]
   target["channel"]=tv.get("channel") or target["channel"]
   target["coverage_time"]=tv.get("coverage_time")
   target["coverage_source"]=tv.get("coverage_source")
   target["sources"]+=tv["sources"]
   if tv.get("start_time") and tv["start_time"]!=target["start_time"]:
    target["time_conflict"]={"fixture":target["start_time"],"secondary":tv["start_time"]}
    target["verification"]="conflict"
   elif tv.get("start_time"): target["verification"]="cross-referenced"
  else: unmatched.append(tv)
 return unmatched

def main():
 days=weekend()
 jobs=[(cat,day) for cat in LEAGUES for day in days]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  batches=list(pool.map(fetch_one,jobs))
 events=[e for batch,_ in batches for e in batch]
 health=[h for _,h in batches]
 tv=attach_tv(events,days)
 events.extend(tv)
 unique={e["id"]:e for e in events}
 events=sorted(unique.values(),key=lambda e:e.get("start_time") or e.get("coverage_time") or e["start"])
 counts=dict(Counter(e["category"] for e in events))
 now=dt.datetime.now(dt.timezone.utc).isoformat()
 audit={"updated":now,"weekend":[str(d) for d in days],
  "total_events":len(events),"by_category":counts,
  "source_requests":health,"successful_requests":sum(x["status"]=="ok" for x in health),
  "failed_requests":sum(x["status"]=="error" for x in health),
  "verified_start_times":sum(bool(e.get("start_time")) for e in events),
  "coverage_only":sum(not e.get("start_time") for e in events),
  "cross_referenced":sum(e.get("verification")=="cross-referenced" for e in events),
  "conflicts":[{"id":e["id"],"name":e["name"],"times":e["time_conflict"]} for e in events if e.get("time_conflict")],
  "limitations":["Empty API results do not prove no events are scheduled.",
  "ESPN endpoints are unofficial; successful HTTP responses may omit competitions.",
  "TV guide supplement is manually curated for 13–15 November only.",
  "Coverage percentage cannot be calculated without independent expected-event inventory."]}
 out=ROOT/"data";out.mkdir(exist_ok=True)
 (out/"events.json").write_text(json.dumps({"updated":now,"events":events},indent=2)+"\n")
 (out/"source-health.json").write_text(json.dumps(audit,indent=2)+"\n")
 print("Fixtures",len(events),"verified starts",audit["verified_start_times"],
       "coverage only",audit["coverage_only"],"failed requests",audit["failed_requests"])
 if not any(x["status"]=="ok" for x in health): raise SystemExit("All sources failed; refusing to publish as success")
if __name__=="__main__":main()
