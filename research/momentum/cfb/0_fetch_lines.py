"""Fetch CFBD betting lines, one call per year (seasonType=both), cached. Cap 15 calls."""
import json, os, gzip, urllib.request, sys
API="https://apinext.collegefootballdata.com"
years=[int(a) for a in sys.argv[1:]] or list(range(2014,2027))
calls=0
for y in years:
    out=f"raw/lines-{y}.json.gz"
    if os.path.exists(out): continue
    if calls>=15: break
    req=urllib.request.Request(API+f"/lines?year={y}&seasonType=both",
        headers={"Authorization":"Bearer "+os.environ["CFBD_KEY"],"User-Agent":"thesportspage.net"})
    r=urllib.request.urlopen(req,timeout=180); calls+=1
    body=r.read().decode()
    print(y,"remaining",r.headers.get("X-CallLimit-Remaining"),"n",len(json.loads(body)),file=sys.stderr)
    gzip.open(out,"wt").write(body)
