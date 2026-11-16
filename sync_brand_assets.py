#!/usr/bin/env python3
"""Fetch authentic third-party brand assets from their published Wikimedia Commons files.
Run in GitHub Actions (network access); no invented or traced logos.
"""
import json
import pathlib
import urllib.parse
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
 req=urllib.request.Request(url,headers={"User-Agent":"TheSportSheet-asset-sync/1.0 (GitHub Pages sports listings; Wikimedia Commons attribution)"})
 with urllib.request.urlopen(req,timeout=25) as r:return r.read()
def fetch(filename,title):
 params=urllib.parse.urlencode({"action":"query","format":"json","prop":"imageinfo","iiprop":"url|mime|size","titles":"File:"+title})
 data=json.loads(request("https://commons.wikimedia.org/w/api.php?"+params))
 page=next(iter(data["query"]["pages"].values()))
 info=page["imageinfo"][0]
 url=info["url"]
 blob=request(url)
 if len(blob)<100 or len(blob)>2_000_000:raise ValueError("Unexpected asset size")
 if filename.endswith(".svg"):
  if info["mime"]!="image/svg+xml":raise ValueError("Expected SVG")
  ET.fromstring(blob)
 elif filename.endswith(".png"):
  if not blob.startswith(b"\\x89PNG\\r\\n\\x1a\\n"):raise ValueError("Expected PNG")
 elif filename.endswith(".jpg"):
  if not blob.startswith(b"\\xff\\xd8"):raise ValueError("Expected JPEG")
 (DEST/filename).write_bytes(blob)
 print("Saved",filename,len(blob),"bytes",url)
 return {"file":filename,"title":title,"source":url,"commons_page":"https://commons.wikimedia.org/wiki/File:"+urllib.parse.quote(title.replace(" ","_"))}
def main():
 DEST.mkdir(parents=True,exist_ok=True)
 manifest=[];failed=[]
 for name,title in FILES.items():
  try:manifest.append(fetch(name,title))
  except Exception as e:failed.append({"file":name,"reason":str(e)});print("ERROR",name,str(e))
 (DEST/"official-sources.json").write_text(json.dumps({"assets":manifest,"failed":failed},indent=2)+"\\n")
 if failed:raise SystemExit("Some official brand assets failed to download; successful files retained")
if __name__=="__main__":main()
