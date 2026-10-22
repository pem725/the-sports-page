import os,urllib.request,urllib.error
req=urllib.request.Request("https://api.collegefootballdata.com/games/teams?year=2011&week=12&seasonType=regular",headers={"Authorization":"Bearer "+os.environ["CFBD_KEY"]})
try:
    r=urllib.request.urlopen(req,timeout=60); h=r.headers; print("ok",r.status)
except urllib.error.HTTPError as e:
    h=e.headers; print("http",e.code, e.read()[:300])
for k in h.keys():
    if "limit" in k.lower() or "retry" in k.lower() or "rate" in k.lower(): print(k,h[k])
