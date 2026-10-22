import json, os, time, urllib.request, sys
ids=[]
have=set()
for fn in os.listdir("cache"):
    if fn.startswith("gt_"):
        for g in json.load(open("cache/"+fn)): have.add(g["id"])
for y in (2011,2024,2025):
    for st in ("regular","postseason"):
        for g in json.load(open(f"cache/games_{y}_{st}.json")):
            if g.get("homeClassification")=="fbs" and g.get("awayClassification")=="fbs" and g.get("completed") and g["id"] not in have:
                ids.append(g["id"])
print(len(ids), flush=True)
for i,gid in enumerate(ids):
    p=f"espn/{gid}.json"
    if os.path.exists(p): continue
    url=f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event={gid}"
    for a in range(3):
        try:
            d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=30)); break
        except Exception as e:
            print("err",gid,e,flush=True); time.sleep(5*(a+1)); d=None
    if d is None: continue
    keep={"boxscore":{"teams":[{"team":t["team"].get("displayName"),"id":t["team"].get("id"),"statistics":t.get("statistics",[])} for t in d.get("boxscore",{}).get("teams",[])]},
          "competitors":[{"id":c["team"]["id"],"name":c["team"]["displayName"],"score":c.get("score"),"homeAway":c.get("homeAway")} for c in d["header"]["competitions"][0]["competitors"]]}
    json.dump(keep,open(p,"w")); time.sleep(0.25)
    if i%200==0: print(i,flush=True)
print("done",flush=True)
