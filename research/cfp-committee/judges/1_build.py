"""For every CFP committee ranking 2014-2026: fit a margin rating and a resume score
on games played BEFORE that ranking, then compare. Output rows.json."""
import json, gzip, math
import numpy as np
from statistics import NormalDist
import os
CAP, LAM, SD = 28, 2.0, 15.0
G5PEN=float(os.environ.get("G5PEN",0)); SECB=float(os.environ.get("SECB",0))
P5 = {"SEC","Big Ten","ACC","Big 12","Pac-12"}
rows=[]
for y in range(2014,2027):
    G=[g for g in json.load(gzip.open(f"raw/games-{y}.json.gz")) if g["completed"] and g["homePoints"] is not None]
    R=json.load(gzip.open(f"raw/rank-{y}.json.gz"))
    conf={}
    for g in G:
        conf[g["homeTeam"]]=g["homeConference"] if g["homeClassification"]=="fbs" else "FCS"
        conf[g["awayTeam"]]=g["awayConference"] if g["awayClassification"]=="fbs" else "FCS"
    for wk in R:
        cfp=[p for p in wk["polls"] if p["poll"]=="Playoff Committee Rankings"]
        if not cfp: continue
        W=wk["week"]; cr={r["school"]:r["rank"] for r in cfp[0]["ranks"]}
        ap=[p for p in wk["polls"] if p["poll"]=="AP Top 25"]
        apr={r["school"]:r["rank"] for r in ap[0]["ranks"]} if ap else {}
        gs=[g for g in G if g["week"]<W]
        teams=sorted({g["homeTeam"] for g in gs}|{g["awayTeam"] for g in gs})
        ix={t:i for i,t in enumerate(teams)}; n=len(teams)
        X=np.zeros((len(gs),n+1)); yv=np.zeros(len(gs))
        for k,g in enumerate(gs):
            X[k,ix[g["homeTeam"]]]=1; X[k,ix[g["awayTeam"]]]=-1
            X[k,n]=0 if g["neutralSite"] else 1
            yv[k]=max(-CAP,min(CAP,g["homePoints"]-g["awayPoints"]))
        A=X.T@X+LAM*np.diag([1]*n+[0]); b=np.linalg.solve(A,X.T@yv)
        rat={t:b[ix[t]] for t in teams}; hfa=b[n]
        for t in teams:
            if conf.get(t) not in P5|{"FBS Independents","FCS"}: rat[t]-=G5PEN
            if conf.get(t)=="SEC": rat[t]+=SECB
        fbs=[t for t in teams if conf.get(t)!="FCS"]
        order=sorted(fbs,key=lambda t:-rat[t]); bench=rat[order[11]]
        N=NormalDist(0,SD); res={t:0.0 for t in fbs}; rec={t:[0,0] for t in fbs}
        for g in gs:
            for me,op,home,won in ((g["homeTeam"],g["awayTeam"],1,g["homePoints"]>g["awayPoints"]),(g["awayTeam"],g["homeTeam"],-1,g["awayPoints"]>g["homePoints"])):
                if me not in res: continue
                h=0 if g["neutralSite"] else home*hfa
                res[me]+=won-N.cdf(bench-rat[op]+h); rec[me][0 if won else 1]+=1
        z=lambda d:{t:(d[t]-np.mean([d[u] for u in fbs]))/np.std([d[u] for u in fbs]) for t in fbs}
        zr,zs=z(rat),z(res)
        comp={t:(zr[t]+zs[t])/2 for t in fbs}
        def rk(d): return {t:i+1 for i,t in enumerate(sorted(fbs,key=lambda t:-d[t]))}
        mr,rr,sr=rk(comp),rk(rat),rk(res)
        for t in fbs:
            if t in cr or mr[t]<=30:
                rows.append(dict(year=y,week=W,team=t,conf=conf[t],cfp=cr.get(t),ap=apr.get(t),math=mr[t],
                                 rating_rk=rr[t],resume_rk=sr[t],rating=round(rat[t],1),resume=round(res[t],2),
                                 w=rec[t][0],l=rec[t][1],nweek=None))
json.dump(rows,open(os.environ.get("OUT","rows.json"),"w"))
print(len(rows),"rows")
