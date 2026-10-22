import json, math, statistics as S, numpy as np, random
exec(open("analyze.py").read().split("out={}")[0])  # reuse loaders -> cg, ng
def cross(rows, t, key, win=2):
    # P(win | key==x) smoothed with +-win window; for pf find first x where >=t; for pa find last x where >=t
    xs=range(0,75); P={}
    for x in xs:
        sub=[r["win"] for r in rows if abs(r[key]-x)<=win]
        if len(sub)>=40: P[x]=(S.mean(sub),len(sub))
    ks=sorted(P)
    if key=="pf":
        for a,b in zip(ks,ks[1:]):
            if P[a][0]<t<=P[b][0]: return round(a+(t-P[a][0])/(P[b][0]-P[a][0]),1), P[b][1]
    else:
        for a,b in zip(ks,ks[1:]):
            if P[a][0]>=t>P[b][0]: return round(a+(P[a][0]-t)/(P[a][0]-P[b][0]),1), P[a][1]
    return None
res={}
for name,rows in (("CFB",cg),("NFL",ng)):
    R={}
    for era,f in (("2006-2025",lambda y:True),("2006-2010",lambda y:y<=2010),("2021-2025",lambda y:y>=2021)):
        rr=[r for r in rows if f(r["season"])]
        R[era]={"n_team_games":len(rr),"mean_pts":round(S.mean(r["pf"] for r in rr),1),
            "score_for":{str(t):cross(rr,t,"pf") for t in (.5,.75,.9,.95)},
            "allow_at_most":{str(t):cross(rr,t,"pa") for t in (.5,.75,.9,.95)},
            "p_win_allow_le14":round(S.mean(r["win"] for r in rr if r["pa"]<=14),3),
            "share_allow_le14":round(S.mean(1 if r["pa"]<=14 else 0 for r in rr),3)}
    res[name]=R
# season-level extras
seas=json.load(open("team_seasons.json"))
def wilson(k,n):
    if n==0: return None
    p=k/n; z=1.96; d=1+z*z/n; c=p+z*z/(2*n); h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)); return [round((c-h)/d,3),round((c+h)/d,3)]
for name,L in seas.items():
    offs=np.array([s["off"] for s in L]); defs=np.array([s["def"] for s in L])
    q=lambda a,p: float(np.percentile(a,p))
    E={}
    for lab,cond in (("bottom25_off",lambda s:s["off"]<=q(offs,25)),("bottom25_def",lambda s:s["def"]<=q(defs,25)),
                     ("bottomhalf_off_top25_def",lambda s:s["off"]<=q(offs,50) and s["def"]>=q(defs,75)),
                     ("bottomhalf_def_top25_off",lambda s:s["def"]<=q(defs,50) and s["off"]>=q(offs,75))):
        sub=[s for s in L if cond(s)]; k=sum(1 for s in sub if s["wp"]>.5); k75=sum(1 for s in sub if s["wp"]>=.75)
        E[lab]={"n":len(sub),"mean_wp":round(S.mean(s["wp"] for s in sub),3),"winning_record":k,"share_winning":round(k/len(sub),3),"ci95":wilson(k,len(sub)),
                "wp_ge_75":k75,"share_ge_75":round(k75/len(sub),3),"ci95_75":wilson(k75,len(sub))}
    # extreme profiles at matched margin: residual of wp on margin, compare tot terciles
    m=np.array([s["margin"] for s in L]); tot=np.array([s["tot"] for s in L]); wp=np.array([s["wp"] for s in L])
    b=np.polyfit(m,wp,3); resid=wp-np.polyval(b,m)
    lo=tot<=np.percentile(tot,20); hi=tot>=np.percentile(tot,80)
    # bootstrap CI of mean resid diff
    rng=np.random.default_rng(1); diffs=[]
    for _ in range(4000):
        a=rng.choice(resid[lo],lo.sum()); c=rng.choice(resid[hi],hi.sum()); diffs.append(a.mean()-c.mean())
    E["matched_margin_extreme_quintiles"]={"def_led_lowest_total_quintile_n":int(lo.sum()),"off_led_highest_total_quintile_n":int(hi.sum()),
        "mean_resid_def_led":round(float(resid[lo].mean()),4),"mean_resid_off_led":round(float(resid[hi].mean()),4),
        "diff_def_minus_off_winpct":round(float(resid[lo].mean()-resid[hi].mean()),4),"ci95":[round(float(np.percentile(diffs,2.5)),4),round(float(np.percentile(diffs,97.5)),4)],
        "games_per_season_equiv":"diff x games"}
    E["mean_games"]=round(S.mean(s["g"] for s in L),1)
    E["sd_off_ppg"]=round(float(offs.std()),2); E["sd_def_ppg"]=round(float(defs.std()),2)
    # pythag-implied: at margin +7, total low vs high
    res[name]["season"]=E
json.dump(res,open("extra.json","w"),indent=1)
print(json.dumps(res,indent=1))
