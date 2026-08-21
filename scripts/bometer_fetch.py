import json, os, urllib.request, time
CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),"cache"); os.makedirs(CACHE,exist_ok=True)
def get(url,key):
    p=os.path.join(CACHE,key+".json")
    if os.path.exists(p): return json.load(open(p))
    for a in range(4):
        try:
            d=json.load(urllib.request.urlopen(url,timeout=120)); json.dump(d,open(p,"w")); return d
        except Exception:
            if a==3: raise
            time.sleep(3)
SEASONS=[2021,2022,2023,2024,2025,2026]
out=[]
for y in SEASONS:
    d=get(f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={y}-03-01&endDate={y}-11-10"
          f"&gameTypes=R&hydrate=linescore&fields=dates,date,games,officialDate,status,detailedState,teams,away,home,score,linescore,currentInning,scheduledInnings,innings,num,runs,team,name",
          f"sched{y}")
    n=0
    for day in d.get("dates",[]):
        for g in day["games"]:
            if g.get("status",{}).get("detailedState")!="Final": continue
            a=g["teams"]["away"].get("score"); h=g["teams"]["home"].get("score")
            if a is None or h is None: continue
            ls=g.get("linescore",{})
            inn=ls.get("currentInning") or 9; sched=ls.get("scheduledInnings") or 9
            # A real walk-off: the home team wins AND the game ends in the bottom
            # half, i.e. they were tied or behind entering their last at-bat. Score
            # the innings BEFORE the last one and check. The earlier flag -- "home
            # won and went the distance" -- counted 9-2 home wins as walk-offs.
            innl = ls.get("innings") or []
            walkoff = False
            if h > a and innl:
                ah = sum((x.get("away") or {}).get("runs",0) for x in innl[:-1])
                hh = sum((x.get("home") or {}).get("runs",0) for x in innl[:-1])
                last = innl[-1]
                home_batted_last = (last.get("home") or {}).get("runs") is not None
                walkoff = home_batted_last and hh <= ah
            out.append(dict(date=g.get("officialDate") or day["date"], season=y,
                            away=a, home=h, margin=abs(a-h), innings=inn, sched=sched,
                            extra=inn>sched, walkoff=walkoff))
            n+=1
    print(f"  {y}: {n} final regular-season games")
json.dump(out, open(os.path.join(CACHE,"games.json"),"w"))
print("total games:", len(out))
