#!/usr/bin/env python3
"""Fetch authentic third-party brand assets from their published Wikimedia Commons files.
Run in GitHub Actions (network access); no invented or traced logos.
"""
import json
import hashlib
import pathlib
import time
import urllib.parse
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT=pathlib.Path(__file__).resolve().parent
DEST=ROOT/"assets"/"sports"
FILES={
 "gaa-official.jpg":"Official Gaelic Athletic Association logo.jpg",
 "irfu-official.svg":"Irish rugby union textlogo.svg",
 "snooker-federation.svg":"World Snooker Federation logo.svg",
 "pdc-official.png":"Professional Darts Corporation logo.png",
 "darts-world-series.svg":"World Series of Darts - Logo (no background).svg",
 "rugby-world-cup.svg":"Rugby World Cup footer logo (post-2023).svg",
 "racing-jockey-club.png":"The Jockey Club UK logo.png",
}
def request(url):
 req=urllib.request.Request(url,headers={"User-Agent":"TheSportSheet/1.0 (sports fixture listing; contact via github.com/Keithc5/TheSportSheet)"})
 for attempt in range(5):
  try:
   with urllib.request.urlopen(req,timeout=30) as r:return r.read()
  except urllib.error.HTTPError as exc:
   if exc.code not in (429,503) or attempt==4:raise
   time.sleep(8*(attempt+1))
def fetch(filename,title):
 normalized=title.replace(" ","_")
 digest=hashlib.md5(normalized.encode("utf-8")).hexdigest()
 url="https://upload.wikimedia.org/wikipedia/commons/"+digest[0]+"/"+digest[:2]+"/"+urllib.parse.quote(normalized)
 blob=request(url)
 if len(blob)<100 or len(blob)>2_000_000:raise ValueError("Unexpected asset size")
 if filename.endswith(".svg"):
  if not blob.lstrip().startswith((b"<svg",b"<?xml",b"<!--")):raise ValueError("Expected SVG")
  ET.fromstring(blob)
 elif filename.endswith(".png"):
  if not blob[:8]==bytes([137,80,78,71,13,10,26,10]):raise ValueError("Expected PNG")
 elif filename.endswith(".jpg"):
  if not blob[:2]==bytes([255,216]):raise ValueError("Expected JPEG")
 (DEST/filename).write_bytes(blob)
 print("Saved",filename,len(blob),"bytes",url)
 return {"file":filename,"title":title,"source":url,"commons_page":"https://commons.wikimedia.org/wiki/File:"+urllib.parse.quote(title.replace(" ","_"))}
def main():
 DEST.mkdir(parents=True,exist_ok=True)
 manifest=[];failed=[]
 for name,title in FILES.items():
  if (DEST/name).exists():
   print("Already stored:",name)
   manifest.append({"file":name,"title":title,"commons_page":"https://commons.wikimedia.org/wiki/File:"+urllib.parse.quote(title.replace(" ","_"))})
   continue
  time.sleep(2)
  try:manifest.append(fetch(name,title))
  except Exception as e:failed.append({"file":name,"reason":str(e)});print("ERROR",name,str(e))
 (DEST/"official-sources.json").write_text(json.dumps({"assets":manifest,"failed":failed},indent=2)+"\n")
 if failed:raise SystemExit("Some official brand assets failed to download; successful files retained")
if __name__=="__main__":main()
