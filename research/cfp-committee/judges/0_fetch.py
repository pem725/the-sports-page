"""Pull CFBD games and polls, 2014-2026, cached. ~26 calls."""
import json, os, gzip, urllib.request, sys
API="https://apinext.collegefootballdata.com"
def get(path, out):
    if os.path.exists(out): return
    req=urllib.request.Request(API+path, headers={"Authorization":"Bearer "+os.environ["CFBD_KEY"],"User-Agent":"thesportspage.net"})
    r=urllib.request.urlopen(req,timeout=120)
    print(path, "remaining", r.headers.get("X-CallLimit-Remaining"), file=sys.stderr)
    gzip.open(out,"wt").write(r.read().decode())
for y in range(2014,2027):
    get(f"/games?year={y}&seasonType=regular&classification=fbs", f"raw/games-{y}.json.gz")
    get(f"/games?year={y}&seasonType=postseason&classification=fbs", f"raw/post-{y}.json.gz")
    get(f"/rankings?year={y}&seasonType=regular", f"raw/rank-{y}.json.gz")
    get(f"/rankings?year={y}&seasonType=postseason", f"raw/rankpost-{y}.json.gz")
