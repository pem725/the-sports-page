"""Were the judges right? Fit the margin rating on ALL regular-season games, predict
postseason games, and see whether G5 / SEC teams beat or miss the prediction."""
import json,gzip,collections,random
import numpy as np
CAP,LAM=28,2.0
def grp(c):
    if c in ("SEC","Big Ten","ACC","Big 12","Pac-12"): return "Power"
    if c=="FBS Independents": return "Indep"
    return "Group of 5"
out=collections.defaultdict(list); vs=[]
for y in range(2014,2026):
    G=[g for g in json.load(gzip.open(f"raw/games-{y}.json.gz")) if g["completed"] and g["homePoints"] is not None]
    P=[g for g in json.load(gzip.open(f"raw/post-{y}.json.gz")) if g["completed"] and g["homePoints"] is not None]
    teams=sorted({g["homeTeam"] for g in G}|{g["awayTeam"] for g in G}); ix={t:i for i,t in enumerate(teams)}; n=len(teams)
    X=np.zeros((len(G),n+1)); yv=np.zeros(len(G))
    for k,g in enumerate(G):
        X[k,ix[g["homeTeam"]]]=1; X[k,ix[g["awayTeam"]]]=-1; X[k,n]=0 if g["neutralSite"] else 1
        yv[k]=max(-CAP,min(CAP,g["homePoints"]-g["awayPoints"]))
    b=np.linalg.solve(X.T@X+LAM*np.diag([1]*n+[0]),X.T@yv)
    for g in P:
        h,a=g["homeTeam"],g["awayTeam"]
        if h not in ix or a not in ix: continue
        pred=b[ix[h]]-b[ix[a]]+(0 if g["neutralSite"] else b[n]); act=g["homePoints"]-g["awayPoints"]
        gh,ga=grp(g["homeConference"]),grp(g["awayConference"])
        if {gh,ga}=={"Power","Group of 5"}:
            sign=1 if gh=="Group of 5" else -1
            vs.append((sign*(act-pred), sign*pred, (sign*act)>0))
        if g["homeConference"]=="SEC" and g["awayConference"]!="SEC": out["SEC"].append(act-pred)
        if g["awayConference"]=="SEC" and g["homeConference"]!="SEC": out["SEC"].append(pred-act)
v=np.array([x[0] for x in vs]); p=np.array([x[1] for x in vs]); w=np.array([x[2] for x in vs])
print(f"G5 vs Power bowls/playoff 2014-25: n={len(v)}; G5 beat the math by {v.mean():+.1f} pts (se {v.std()/len(v)**.5:.1f}); math expected G5 margin {p.mean():+.1f}; G5 won {w.sum()} of {len(w)}")
s=np.array(out["SEC"]); print(f"SEC vs non-SEC postseason: n={len(s)}; SEC beat the math by {s.mean():+.1f} (se {s.std()/len(s)**.5:.1f})")
