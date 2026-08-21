import json, os, urllib.request, time, datetime as dt, collections, math, statistics as st
CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),"cache")
def get(url,key):
    p=os.path.join(CACHE,key+".json")
    if os.path.exists(p): return json.load(open(p))
    for a in range(4):
        try:
            d=json.load(urllib.request.urlopen(url,timeout=180)); json.dump(d,open(p,"w")); return d
        except Exception:
            if a==3: raise
            time.sleep(3)
SE=[2021,2022,2023,2024,2025,2026]
doubt=collections.defaultdict(lambda:[0,0])     # team -> [in-doubt, games]
att=collections.defaultdict(list)               # home team -> attendances
for y in SE:
    d=get(f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={y}-03-01&endDate={y}-11-10"
          f"&gameTypes=R&hydrate=linescore,gameInfo", f"full{y}")
    for day in d.get("dates",[]):
        for g in day["games"]:
            if g.get("status",{}).get("detailedState")!="Final": continue
            a=g["teams"]["away"].get("score"); h=g["teams"]["home"].get("score")
            if a is None or h is None: continue
            ls=g.get("linescore",{}); inn=ls.get("currentInning") or 9; sch=ls.get("scheduledInnings") or 9
            innl=ls.get("innings") or []
            wo=False
            if h>a and innl:
                ah=sum((x.get("away") or {}).get("runs",0) for x in innl[:-1])
                hh=sum((x.get("home") or {}).get("runs",0) for x in innl[:-1])
                wo=((innl[-1].get("home") or {}).get("runs") is not None) and hh<=ah
            dbt = abs(a-h)<=1 or inn>sch or wo
            for side in ("away","home"):
                nm=(g["teams"][side].get("team") or {}).get("name")
                if nm: doubt[nm][0]+=dbt; doubt[nm][1]+=1
            hn=(g["teams"]["home"].get("team") or {}).get("name")
            at=(g.get("gameInfo") or {}).get("attendance")
            if hn and at: att[hn].append(at)
rows=[]
for t,(d_,n) in doubt.items():
    if n<400 or t not in att or len(att[t])<200: continue
    rows.append(dict(team=t, bo=100*d_/n, games=n, att=st.mean(att[t]), n_att=len(att[t])))
json.dump(rows, open(os.path.join(CACHE,"teamrows.json"),"w"))
print(f"{len(rows)} teams\n")
p=sum(doubt[r['team']][0] for r in rows)/sum(r['games'] for r in rows)
chi=sum((doubt[r['team']][0]-p*r['games'])**2/(p*(1-p)*r['games']) for r in rows); dfree=len(rows)-1
print(f"do TEAMS differ on the bometer?  pooled {100*p:.2f}%   chi/df {chi/dfree:.2f}   z {(chi-dfree)/math.sqrt(2*dfree):+.2f}")
print(f"   range {min(r['bo'] for r in rows):.1f} ({min(rows,key=lambda r:r['bo'])['team']}) .. {max(r['bo'] for r in rows):.1f} ({max(rows,key=lambda r:r['bo'])['team']})")
bo=[r['bo'] for r in rows]; aa=[r['att'] for r in rows]
mb,ma=st.mean(bo),st.mean(aa)
r_=sum((x-mb)*(y-ma) for x,y in zip(bo,aa))/math.sqrt(sum((x-mb)**2 for x in bo)*sum((y-ma)**2 for y in aa))
print(f"\ncorrelation(bometer, mean attendance) r = {r_:+.3f}  n={len(rows)}")
b=sum((x-mb)*(y-ma) for x,y in zip(bo,aa))/sum((x-mb)**2 for x in bo)
print(f"unstandardized slope: each +1 bometer point = {b:+,.0f} fans per home game")
