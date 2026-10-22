import os, json, time, urllib.request, sys
K=os.environ["CFBD_KEY"]; B="https://api.collegefootballdata.com"
def get(path, fn):
    p=f"cache/{fn}.json"
    if os.path.exists(p): return json.load(open(p))
    req=urllib.request.Request(B+path, headers={"Authorization":"Bearer "+K,"Accept":"application/json"})
    for a in range(4):
        try:
            d=json.load(urllib.request.urlopen(req, timeout=60)); break
        except Exception as e:
            print("err",path,e, file=sys.stderr); time.sleep(5*(a+1))
    else: raise SystemExit("fail "+path)
    json.dump(d, open(p,"w")); time.sleep(0.4); return d
mode=sys.argv[1]
if mode=="games":
    for y in range(2006,2026):
        for st in ("regular","postseason"):
            d=get(f"/games?year={y}&seasonType={st}", f"games_{y}_{st}")
            print(y,st,len(d))
elif mode=="probe":
    d=get("/games/teams?year=2006&week=1","gt_2006_regular_1"); print(len(d)); print(json.dumps(d[0])[:1500])
elif mode=="gt":
    for y in range(2006,2026):
        for w in range(1,17):
            d=get(f"/games/teams?year={y}&week={w}&seasonType=regular", f"gt_{y}_regular_{w}")
        d=get(f"/games/teams?year={y}&week=1&seasonType=postseason", f"gt_{y}_postseason_1")
        print(y, flush=True)
