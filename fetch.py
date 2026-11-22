"""Collect weekend fixtures with provenance, conservative validation and source health.
Run with Python 3.12. No third-party dependencies. Never infer missing start times.
"""
import concurrent.futures
import datetime as dt
import json
import pathlib
import os
import re
import urllib.request
from html.parser import HTMLParser
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
 "rugby-nations": ("rugby","nations-championship","Rugby","Nations Championship"),
 "rugby-premiership": ("rugby","english-premiership","Rugby","Premiership Rugby"),
 "rugby-top14": ("rugby","french-top-14","Rugby","Top 14"),
 "rugby-champions": ("rugby","european-rugby-champions-cup","Rugby","Champions Cup"),
 "soccer-esp.1": ("soccer","esp.1","Football","La Liga"),
 "soccer-ger.1": ("soccer","ger.1","Football","Bundesliga"),
 "soccer-ita.1": ("soccer","ita.1","Football","Serie A"),
 "soccer-fra.1": ("soccer","fra.1","Football","Ligue 1"),
 "soccer-por.1": ("soccer","por.1","Football","Primeira Liga"),
 "soccer-ned.1": ("soccer","ned.1","Football","Eredivisie"),
 "soccer-bel.1": ("soccer","bel.1","Football","Belgian Pro League"),
 "soccer-eng.2": ("soccer","eng.2","Football","Championship"),
 "soccer-uefa.europa": ("soccer","uefa.europa","Football","Europa League"),
 "racing-f1": ("racing","f1","Formula 1","Formula 1"),
}
def weekend():
 today = dt.datetime.now(TZ).date()
 friday = today + dt.timedelta(days=(4-today.weekday())%7)
 if today.weekday() in (5,6): friday = today-dt.timedelta(days=today.weekday()-4)
 return [friday+dt.timedelta(days=i) for i in range(3)]

def collection_days():
 today = dt.datetime.now(TZ).date()
 next_monday = today + dt.timedelta(days=7-today.weekday())
 return sorted(set([today-dt.timedelta(days=i) for i in range(7)] + [today+dt.timedelta(days=i) for i in range(9)] + weekend() + [next_monday + dt.timedelta(days=i) for i in range(7)]))

def valid_start(value, day):
 """Require a timezone-aware, plausible kickoff/session time on the Irish display day."""
 try:
  parsed=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
  return parsed.tzinfo is not None and parsed.astimezone(TZ).date()==day
 except (ValueError,AttributeError,TypeError): return False

F1_DISPLAY_SESSIONS = frozenset(("Qualifying", "Sprint Qualifying", "Sprint", "Race"))

def official_f1_sessions(days):
 """Load individually timed official F1 sessions; never interpret weekend starts as race starts."""
 path=ROOT/"data"/"official-f1-sessions.json"
 if not path.exists(): return [],[]
 result=[];issues=[]
 for row in json.loads(path.read_text()):
  try:
   start=dt.datetime.fromisoformat(row["start"].replace("Z","+00:00"))
   if start.tzinfo is None: raise ValueError("Timezone missing")
   if start.astimezone(TZ).date() not in days: continue
   if row["session"] in ("Practice 1","Practice 2","Practice 3"): continue
   if row["session"] not in F1_DISPLAY_SESSIONS: raise ValueError("Invalid session")
   if not row["source"].startswith("https://www.formula1.com/"): raise ValueError("Not an official F1 source")
   result.append({"id":"racing-f1-"+row["event_id"]+"-"+re.sub(r"[^a-z0-9]+","-",row["session"].lower()).strip("-"),"category":"racing-f1","sport":"Formula 1","competition":"Formula 1","name":row["grand_prix"]+" — "+row["session"],"session":row["session"],"start":start.isoformat(),"start_time":start.isoformat(),"start_source":row["source"],"sources":[{"provider":"formula1-official","url":row["source"],"field":"session_start"}],"verification":"official-schedule","detail":row["session"],"channel":""})
  except (KeyError,ValueError,TypeError,AttributeError) as exc: issues.append({"record":str(row)[:100],"reason":str(exc)})
 return result,issues

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
   if category=="football-nfl":
    # US Sunday night games fall on Monday in Ireland; the ESPN scoreboard
    # can attach them to the preceding US calendar date.
    local_day=start.astimezone(TZ).date()
    if local_day not in collection_days(): continue
    if local_day!=day and local_day!=day+dt.timedelta(days=1):continue
   elif start.astimezone(TZ).date()!=day: continue
   if category.startswith("golf-"): continue  # Tournament start is not a TV coverage time; use dated golf coverage only
   if category=="racing-f1": continue  # ESPN event.date is a meeting start, NOT a race/session time
   if not event.get("id"): continue
   match=(event.get("competitions") or [{}])[0]
   competitors=match.get("competitors") or []
   teams=[c.get("team",{}).get("displayName") or c.get("athlete",{}).get("displayName") for c in competitors]
   teams=[t for t in teams if t]
   name=" vs ".join(teams[:2]) if len(teams)==2 else event.get("name") or event.get("shortName") or competition
   if not name: continue
   state=(event.get("status") or {}).get("type") or {}
   completed=state.get("completed") is True
   scores=[]
   if completed and len(competitors)==2:
    for team in competitors[:2]:
     value=team.get("score")
     if isinstance(value,dict): value=value.get("displayValue") or value.get("value")
     if value is None or str(value).strip()=="": scores=[];break
     scores.append(str(value))
   result_text=" – ".join(scores) if len(scores)==2 else None
   team_logos=[]
   if category.startswith("soccer-") and len(competitors)==2:
    for competitor in competitors[:2]:
     logo=(competitor.get("team") or {}).get("logo") or ""
     team_logos.append(logo if isinstance(logo,str) and logo.startswith("https://a.espncdn.com/i/teamlogos/soccer/") else "")
   league_logos=(payload.get("leagues") or [{}])[0].get("logos") or []
   league_logo=next((logo.get("href") for logo in league_logos if isinstance(logo,dict) and str(logo.get("href","")).startswith("https://a.espncdn.com/")),"") if category.startswith("soccer-") else ""
   result.append({"id":f'{category}-{event["id"]}',"category":category,"sport":label,
    "competition":competition,"name":name,"start":start.isoformat(),"start_time":start.isoformat(),
    "start_source":url,"sources":[{"provider":"espn","url":url,"field":"start_time"}],
    "verification":"single-source","detail":"","channel":"",
    "completed":completed,"result":result_text,**({"team_logos":team_logos,"competition_logo":league_logo} if category.startswith("soccer-") else {})})
  except (KeyError,TypeError,ValueError,AttributeError): continue
 return result,{"source":category,"date":str(day),"status":"ok","count":len(result),"url":url}

def norm(name):
 return re.sub(r"[^a-z0-9]+"," ",name.casefold()).strip()
# Broadcaster discovery: Irish football TV, independent of ESPN fixture data.
# Match only an exact local date, kickoff time and BOTH club names; otherwise leave unconfirmed.
BROADCAST_GUIDES = [
 ("Sky Sports","https://www.skysports.com/watch/football-on-sky/competitions/premier-league","soccer-eng.1"),
]
SOCCER_ALIASES={"man utd":"manchester united","man united":"manchester united",
 "man city":"manchester city","spurs":"tottenham hotspur",
 "nott'm forest":"nottingham forest","nottm forest":"nottingham forest",
 "brighton and hove albion":"brighton hove albion",
 "bournemouth":"afc bournemouth","wolves":"wolverhampton wanderers"}
def _club_key(value):
 value=norm(value).replace(" fc "," ").removesuffix(" fc")
 return SOCCER_ALIASES.get(value,value)
def _fixture_parts(event):
 parts=re.split(r"\\s+(?:vs\\.?|v\\.?|versus)\\s+",event.get("name",""),flags=re.I)
 return [_club_key(p) for p in parts] if len(parts)==2 else []
def _sky_guide_entries(text):
 """Extract dated, timed match blocks from Sky's competition TV guide."""
 entries=[];date=None
 month_names={m.lower():i for i,m in enumerate(("January","February","March","April","May","June","July","August","September","October","November","December"),1)}
 lines=[re.sub(r"\\s+"," ",x).strip() for x in text.splitlines()]
 for i,line in enumerate(lines):
  day=re.search(r"\\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\\s+(\\d{1,2})(?:st|nd|rd|th)?\\s+([A-Za-z]+)",line,re.I)
  if day and day.group(2).lower() in month_names:
   month=month_names[day.group(2).lower()]
   today=dt.datetime.now(TZ).date()
   year=today.year
   if month<today.month-6:year+=1
   elif month>today.month+6:year-=1
   try:date=dt.date(year,month,int(day.group(1)))
   except ValueError:date=None
   continue
  if date is None:continue
  clock=re.fullmatch(r"(\\d{1,2}):(\\d{2})",line)
  if not clock or i<1 or i+1>=len(lines):continue
  home=next((x for x in reversed(lines[max(0,i-4):i]) if x and x.lower() not in ("match preview","remote record")),None)
  away=next((x for x in lines[i+1:i+5] if x and x.lower() not in ("match preview","remote record")),None)
  if not home or not away:continue
  segment=" ".join(lines[i+1:i+12])
  channels=list(dict.fromkeys(re.findall(r"Sky Sports(?: Main Event| Premier League| Football| Action| Arena| Cricket|\\+)",segment,re.I)))
  if not channels:continue
  entries.append({"date":date.isoformat(),"time":clock.group(0),"teams":[_club_key(home),_club_key(away)],"channels":channels})
 return entries
def attach_broadcaster_tv(events):
 """Independently verify fixtures against a live broadcaster guide; never infer a channel."""
 health=[]
 for provider,url,category in BROADCAST_GUIDES:
  try:
   entries=_sky_guide_entries(_sky_text(url))
   matched=0
   for e in events:
    if e.get("category")!=category:continue
    parts=_fixture_parts(e)
    if len(parts)!=2:continue
    start=dt.datetime.fromisoformat(e["start"]).astimezone(TZ)
    matches=[x for x in entries if x["date"]==start.date().isoformat() and x["time"]==start.strftime("%H:%M") and x["teams"]==parts]
    if len(matches)!=1:continue
    row=matches[0]
    existing=[x.strip() for x in e.get("channel","").split(" / ") if x.strip() and x.strip()!="Sky Sports"]
    e["channel"]=" / ".join(dict.fromkeys(existing+row["channels"]))
    e["tv_source"]=url
    e["tv_verification"]="broadcaster-fixture-and-time"
    e.setdefault("sources",[]).append({"provider":provider,"url":url,"field":"channel"})
    matched+=1
   health.append({"provider":provider,"status":"ok","parsed":len(entries),"matched":matched,"url":url})
  except Exception as exc:
   health.append({"provider":provider,"status":"error","message":str(exc)[:160],"url":url})
 return health

def attach_premier_league_tv(events):
 """Apply fixture-specific Irish TV selections without guessing by kickoff slot."""
 path=ROOT/"data"/"premier-league-tv-verified.json"
 if not path.exists():return {"verified_listings":0,"matched_fixtures":0,"missing_fixture_ids":[]}
 records=json.loads(path.read_text())
 index={(e.get("id"),dt.datetime.fromisoformat(e["start"]).astimezone(TZ).date().isoformat()):e for e in events if e.get("category")=="soccer-eng.1"}
 matched=0;missing=[]
 for row in records:
  if row.get("territory")!="IE" or not row.get("channels") or not row.get("source","").startswith("https://"):continue
  e=index.get((row.get("id"),row.get("date")))
  if e is None:
   missing.append(row.get("id"))
   continue
  e["channel"]=" / ".join(row["channels"])
  e["tv_source"]=row["source"]
  e["tv_verification"]="fixture-specific-irish-listing"
  e.setdefault("sources",[]).append({"provider":"irish-tv-guide","url":row["source"],"field":"channel"})
  matched+=1
 return {"verified_listings":len(records),"matched_fixtures":matched,"missing_fixture_ids":missing}

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


SKY_NFL_GUIDE = "https://www.skysports.com/nfl/news/13582747/nfl-2026-season-live-on-sky-sports-fixtures-kick-off-times-tv-channel-for-games-this-week-and-weekend"
SKY_NFL_TV = "https://www.skysports.com/watch/nfl-on-sky"
class _Text(HTMLParser):
 def __init__(self): super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style"): self.skip+=1
  if tag in ("p","h2","h3","li","br"): self.parts.append("\n")
 def handle_endtag(self,tag):
  if tag in ("script","style") and self.skip:self.skip-=1
  if tag in ("p","h2","h3","li"):self.parts.append("\n")
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
def _sky_text(url):
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; TheSportSheet/1.0)","Accept":"text/html"})
 with urllib.request.urlopen(req,timeout=16) as response:
  parser=_Text();parser.feed(response.read(2_000_000).decode("utf-8","replace"))
 return re.sub(r"[ \t]+"," ","".join(parser.parts))
def _nfl_pair(name):
 parts=re.split(r"\s+(?:@|vs\.?|v\.?|at|versus)\s+",name,flags=re.I)
 return frozenset(norm(x) for x in parts) if len(parts)==2 else frozenset()
def _sky_channels(text):
 channels=[]
 for c in ("Sky Sports NFL","Sky Sports Main Event","Sky Sports+"):
  if re.search(re.escape(c).replace(r"\+","\s*\+"),text,re.I):channels.append(c)
 return channels
def sky_nfl_listings():
 """Parse broadcaster's dated weekly article; do not infer Sky from NFL Game Pass."""
 try: raw=_sky_text(SKY_NFL_GUIDE)
 except Exception as exc:return [],{"status":"error","message":str(exc)[:180]}
 listings=[]
 # Match lines are explicitly dated within the WEEK section, not generic article prose.
 day=None
 for line in raw.splitlines():
  line=line.strip()
  matchday=re.search(r"^(?:Thursday|Friday|Saturday|Sunday|Monday|Tuesday|Wednesday)\s+(?:November|December|January|February|September|October)\s+(\d{1,2})",line,re.I)
  if matchday:
   month=re.search(r"(November|December|January|February|September|October)",line,re.I).group(1)
   year=2026 if month in ("September","October","November","December") else 2027
   day=dt.date(year,dt.datetime.strptime(month,"%B").month,int(matchday.group(1)))
   continue
  m=re.search(r"([A-Za-z .'-]+?)\s+@\s+([A-Za-z .'-]+?)\s+-\s+KO\s+",line,re.I)
  if not m or not day:continue
  pair=frozenset((norm(m.group(1)),norm(m.group(2))))
  channels=_sky_channels(line)
  if channels:listings.append({"day":day,"pair":pair,"channels":channels,"source":SKY_NFL_GUIDE})
 return listings,{"status":"ok","count":len(listings),"source":SKY_NFL_GUIDE}
def attach_nfl_tv(events):
 """Match both teams and Irish game date, never assign channels by kickoff slot."""
 listings,health=sky_nfl_listings()
 curated_path=ROOT/"data"/"nfl-tv-verified.json"
 if curated_path.exists():
  for row in json.loads(curated_path.read_text()):
   try:
    listings.append({"day":dt.date.fromisoformat(row["date"]),"pair":frozenset(norm(t) for t in row["teams"]),"channels":row["channels"],"source":row["source"],"coverage_time":row.get("coverage_time")})
   except (KeyError,ValueError,TypeError):continue
 updated=0
 for e in events:
  if e.get("category")!="football-nfl":continue
  pair=_nfl_pair(e.get("name",""))
  if not pair:continue
  day=dt.datetime.fromisoformat(e["start"]).astimezone(TZ).date()
  matches=[x for x in listings if x["day"]==day and x["pair"]==pair]
  if not matches:continue
  # Curated verified rows override the live article when both exist.
  listing=matches[-1]
  e["channel"]=" / ".join(listing["channels"])
  e["tv_source"]=listing["source"]
  e["tv_verification"]="broadcaster-confirmed"
  if listing.get("coverage_time"):e["coverage_time"]=listing["coverage_time"];e["coverage_source"]=listing["source"]
  e.setdefault("sources",[]).append({"provider":"sky-sports","url":listing["source"],"field":"channel"})
  updated+=1
 health["matched_fixtures"]=updated
 return health

def attach_gaa_crests(events):
 """Use only locally vetted club crests; aliases are exact, never fuzzy."""
 path=ROOT/"data"/"gaa-crests.json"
 if not path.exists():return {"matched":0,"missing":[]}
 registry=json.loads(path.read_text())
 clubs=registry.get("clubs",{})
 aliases={alias.casefold():key for key,info in clubs.items() for alias in [key]+info.get("aliases",[])}
 matched=0;missing=set()
 for e in events:
  if e.get("category")!="gaa":continue
  names=re.split(r"\s+(?:vs\.?|v\.?|versus)\s+",e.get("name",""),flags=re.I)
  if len(names)!=2:continue
  logos=[]
  for name in names:
   info=clubs.get(aliases.get(name.strip().casefold(),"")) or {}
   asset=info.get("asset","")
   if asset and re.fullmatch(r"assets/gaa/[a-z0-9_-]+\.(?:png|webp|svg)",asset) and (ROOT/asset).is_file():
    logos.append(asset);matched+=1
   else:logos.append("");missing.add(name)
  e["team_logos"]=logos
 return {"matched_team_appearances":matched,"missing_clubs":sorted(missing)}

def verified_golf_coverage(days):
 """Dated broadcast sessions; coverage start is NOT a tournament tee time."""
 path=ROOT/"data"/"golf-tv-sessions.json"
 if not path.exists():return []
 rows=[]
 for item in json.loads(path.read_text()):
  try:
   when=dt.datetime.fromisoformat(item["coverage_time"].replace("Z","+00:00"))
   if when.tzinfo is None or when.astimezone(TZ).date() not in days:continue
   rows.append({"id":item["id"],"category":item["category"],"sport":"Golf",
    "competition":item["competition"],"name":item["name"],"start":when.isoformat(),
    "start_time":None,"coverage_time":when.isoformat(),"coverage_source":item["source"],
    "start_source":None,"channel":item.get("channel",""),
    "watch_url":item.get("watch_url",""),"streaming_note":item.get("streaming_note",""),
    "sources":[{"provider":"dated-golf-broadcast","url":item["source"],"field":"coverage_time"}],
    "verification":"coverage-only","detail":"TV coverage, not tee time"})
  except (KeyError,ValueError,TypeError):continue
 return rows

def curated_fixtures(days):
 """Load dated, source-attributed verified fixtures; never invent future matches."""
 path=ROOT/"data"/"verified-fixtures.json"
 if not path.exists(): return [],[]
 rows=json.loads(path.read_text())
 result=[];issues=[]
 for row in rows:
  try:
   start=dt.datetime.fromisoformat(row["start"].replace("Z","+00:00"))
   if start.tzinfo is None: raise ValueError("Missing timezone")
   if start.astimezone(TZ).date() not in days: continue
   if not row.get("start_source","").startswith("https://"): raise ValueError("Missing source")
   entry=dict(row)
   entry.setdefault("category","rugby")
   entry.setdefault("sport","Rugby")
   entry.setdefault("detail","")
   entry.setdefault("channel","")
   entry["start"]=start.isoformat()
   entry["start_time"]=start.isoformat()
   entry["verification"]="cross-referenced" if len(entry.get("sources",[]))>1 else "official-schedule"
   entry.setdefault("sources",[{"provider":"verified-schedule","url":entry["start_source"],"field":"start_time"}])
   result.append(entry)
  except (KeyError,ValueError,TypeError,AttributeError) as exc:
   issues.append({"record":str(row)[:100],"reason":str(exc)})
 return result,issues

def merge_curated(events, curated):
 """Curated fixture takes precedence; remove same-day duplicate provider entries."""
 for row in curated:
  day=dt.datetime.fromisoformat(row["start"]).astimezone(TZ).date()
  pair={norm(t) for t in row["name"].split(" vs ")}
  if len(pair)==2:
   events[:]=[e for e in events if not (
    e.get("sport")==row["sport"] and
    dt.datetime.fromisoformat(e["start"]).astimezone(TZ).date()==day and
    {norm(t) for t in e.get("name","").split(" vs ")}==pair)]
  events.append(row)

def validate_inventory(events, curated, days):
 """Detect omitted fixtures and coverage gaps without treating empty feeds as proof of no games."""
 by_id={e.get("id"):e for e in events}
 missing=[r["id"] for r in curated if r["id"] not in by_id]
 missing_channels=[r["id"] for r in curated if r.get("channel") and not by_id.get(r["id"],{}).get("channel")]
 rugby_days={str(day):{"total":0,"with_tv":0,"without_tv":0} for day in days}
 for e in events:
  if e.get("sport")!="Rugby": continue
  try: day=str(dt.datetime.fromisoformat(e["start"]).astimezone(TZ).date())
  except (ValueError,TypeError,KeyError): continue
  if day not in rugby_days: continue
  rugby_days[day]["total"]+=1
  rugby_days[day]["with_tv" if e.get("channel") else "without_tv"]+=1
 return {"missing_curated":missing,"missing_curated_channels":missing_channels,
         "rugby_by_day":rugby_days,
         "no_rugby_dates":[d for d,v in rugby_days.items() if v["total"]==0]}

def validate_output(events):
 """Reject malformed events and duplicate IDs before overwriting published data."""
 seen=set()
 for event in events:
  identifier=event.get("id")
  if not identifier or identifier in seen: raise ValueError("Missing/duplicate fixture ID: "+str(identifier))
  seen.add(identifier)
  if not event.get("name") or not event.get("category"): raise ValueError("Incomplete fixture "+identifier)
  if not event.get("start_time") and not event.get("coverage_time"):
   raise ValueError("No usable time for "+identifier)
  value=event.get("start_time") or event.get("coverage_time")
  if dt.datetime.fromisoformat(value.replace("Z","+00:00")).tzinfo is None:
   raise ValueError("Naive time for "+identifier)

def main():
 days=collection_days()
 jobs=[(cat,day) for cat in LEAGUES for day in days]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  batches=list(pool.map(fetch_one,jobs))
 events=[e for batch,_ in batches for e in batch]
 f1,official_issues=official_f1_sessions(days)
 events.extend(f1)
 golf_coverage=verified_golf_coverage(days)
 events.extend(golf_coverage)
 curated,curated_issues=curated_fixtures(days)
 merge_curated(events,curated)
 health=[h for _,h in batches]
 if not any(x["status"]=="ok" for x in health):
  raise SystemExit("All sources failed; preserving previously published fixtures")
 events=list({e["id"]:e for e in events}.values())  # ESPN US/Irish date overlap must not duplicate events
 tv=attach_tv(events,days)
 premier_league_tv_health=attach_premier_league_tv(events)
 broadcaster_tv_health=attach_broadcaster_tv(events)
 nfl_tv_health=attach_nfl_tv(events)
 events.extend(tv)
 gaa_crest_health=attach_gaa_crests(events)
 unique={e["id"]:e for e in events}
 events=sorted(unique.values(),key=lambda e:e.get("start_time") or e.get("coverage_time") or e["start"])
 validate_output(events)
 inventory=validate_inventory(events,curated,days)
 if inventory["missing_curated"] or inventory["missing_curated_channels"]:
  raise SystemExit("Curated fixtures or broadcasters lost; refusing to overwrite published feed: "+str(inventory))
 counts=dict(Counter(e["category"] for e in events))
 now=dt.datetime.now(dt.timezone.utc).isoformat()
 audit={"updated":now,"collection_dates":[str(d) for d in days],
  "total_events":len(events),"by_category":counts,
  "gaa_crest_source":gaa_crest_health,
  "source_requests":health,"successful_requests":sum(x["status"]=="ok" for x in health),
  "failed_requests":sum(x["status"]=="error" for x in health),
  "verified_start_times":sum(bool(e.get("start_time")) for e in events),
  "coverage_only":sum(not e.get("start_time") for e in events),
  "cross_referenced":sum(e.get("verification")=="cross-referenced" for e in events),
  "official_schedule_issues":official_issues+curated_issues,
  "curated_fixtures":len(curated),
  "inventory":inventory,
  "tv_confirmed":sum(bool(e.get("channel")) for e in events),
  "nfl_tv_source":nfl_tv_health,
  "premier_league_tv_source":premier_league_tv_health,
  "broadcaster_tv_source":broadcaster_tv_health,
  "tv_unconfirmed":sum(not e.get("channel") for e in events),
  "f1_official_sessions":len(f1),
  "golf_verified_coverage_sessions":len(golf_coverage),
  "unverified_start_times":sum(e.get("verification")=="single-source" for e in events),
  "conflicts":[{"id":e["id"],"name":e["name"],"times":e["time_conflict"]} for e in events if e.get("time_conflict")],
  "limitations":["Empty API results do not prove no events are scheduled.",
  "ESPN endpoints are unofficial; successful HTTP responses may omit competitions.",
  "F1 sessions are included only when independently listed in the curated official Formula 1 timetable; ESPN meeting dates are rejected.",
  "Official F1 timetable must be refreshed as each new Grand Prix approaches.",
  "Single-source ESPN fixture times are provisional, not independently confirmed.",
  "NFL Sky Sports broadcast selections are refreshed from the dated weekly Sky guide with verified fallback records; unlisted games are not assumed to be on Sky.",
  "Coverage percentage cannot be calculated without independent expected-event inventory.",
  "TV channels are only confirmed when supplied by a verified, dated source; blank means unconfirmed, not unavailable."]}
 out=ROOT/"data";out.mkdir(exist_ok=True)
 (out/"events.json").write_text(json.dumps({"updated":now,"events":events},indent=2)+"\n")
 (out/"source-health.json").write_text(json.dumps(audit,indent=2)+"\n")
 print("Fixtures",len(events),"verified starts",audit["verified_start_times"],
       "coverage only",audit["coverage_only"],"failed requests",audit["failed_requests"])
if __name__=="__main__":main()
