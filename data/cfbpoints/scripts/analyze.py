import json, csv, os, math, statistics as S
import numpy as np
from scipy.optimize import minimize_scalar
Y0,Y1=2006,2025
# ---------- CFB games ----------
cg=[]  # team-game rows
games={}
for y in range(Y0,Y1+1):
    for st in ("regular","postseason"):
        for g in json.load(open(f"cache/games_{y}_{st}.json")):
            if g.get("homeClassification")!="fbs" or g.get("awayClassification")!="fbs": continue
            if not g.get("completed") or g["homePoints"] is None or g["awayPoints"] is None: continue
            games[g["id"]]=g
            for me,op in (("home","away"),("away","home")):
                pf,pa=g[me+"Points"],g[op+"Points"]
                cg.append(dict(season=y,st=st,gid=g["id"],team=g[me+"Team"],pf=pf,pa=pa,win=1.0 if pf>pa else (0.5 if pf==pa else 0.0)))
# box scores
box={}
for fn in os.listdir("cache"):
    if not fn.startswith("gt_"): continue
    for g in json.load(open("cache/"+fn)):
        for t in g["teams"]:
            s={x["category"]:x["stat"] for x in t["stats"]}
            try:
                ra=int(s["rushingAttempts"]); pa=int(s["completionAttempts"].split("-")[1]); yd=int(s["totalYards"])
            except Exception: continue
            box[(g["id"],t["team"])]=(ra+pa,yd)

# ESPN box scores (fill-in where CFBD quota ran out)
val={"n_checked":0,"mismatch":[]}
for fn in os.listdir("espn"):
    gid=int(fn[:-5]); g=games.get(gid)
    if not g: continue
    d=json.load(open("espn/"+fn)); ha={c["id"]:c for c in d["competitors"]}
    for c in d["competitors"]:
        mine=g[c["homeAway"]+"Points"]
        val["n_checked"]+=1
        if c["score"] is None or int(c["score"])!=mine: val["mismatch"].append((gid,c["name"],c["score"],mine))
    for t in d["boxscore"]["teams"]:
        c=ha.get(t["id"]); 
        if not c: continue
        s={x["name"]:x["displayValue"] for x in t["statistics"]}
        try:
            ra=int(s["rushingAttempts"]); pa=int(s["completionAttempts"].replace("-","/").split("/")[1]); yd=int(s["totalYards"])
        except Exception: continue
        box[(gid,g[c["homeAway"]+"Team"])]=(ra+pa,yd)
# ---------- NFL ----------
ng=[]
for r in csv.DictReader(open("/home/pem725/GitTemp/the-sports-page/data/nfl/team-games.csv")):
    y=int(r["season"])
    if not (Y0<=y<=Y1): continue
    pf,pa=int(r["points_for"]),int(r["points_against"])
    ng.append(dict(season=y,st="regular" if int(r["week"])<=(17 if y<2021 else 18) else "postseason",gid=r["game_id"],team=r["team"],pf=pf,pa=pa,
                   win=1.0 if pf>pa else (0.5 if pf==pa else 0.0),plays=float(r["plays"] or 0),yards=float(r["yards"] or 0)))
# NFL week<->season-type check via nflverse games
gt={r["game_id"]:r["game_type"] for r in csv.DictReader(open("/home/pem725/GitTemp/the-sports-page/data/nfl/nflverse-games.csv"))}
for r in ng: r["st"]="regular" if gt.get(r["gid"])=="REG" else "postseason"
gid2opp={}
for r in ng: gid2opp.setdefault(r["gid"],[]).append(r)
for gid,rs in gid2opp.items():
    if len(rs)==2:
        a,b=rs; a["opp_plays"],a["opp_yards"]=b["plays"],b["yards"]; b["opp_plays"],b["opp_yards"]=a["plays"],a["yards"]
# CFB allowed yards
for r in cg:
    g=games[r["gid"]]; opp=g["awayTeam"] if g["homeTeam"]==r["team"] else g["homeTeam"]
    o=box.get((r["gid"],opp))
    if o: r["opp_plays"],r["opp_yards"]=o

out={}
def smooth_threshold(rows, target, key="pf"):
    # logistic fit P(win) ~ a + b*x on pf; solve for x
    x=np.array([r[key] for r in rows],float); w=np.array([r["win"] for r in rows],float)
    from scipy.optimize import minimize
    def nll(p):
        z=p[0]+p[1]*x; return np.sum(np.logaddexp(0,z)-w*z)
    p=minimize(nll,[-3,.1]).x
    return {str(t):round(float((math.log(t/(1-t))-p[0])/p[1]),1) for t in target}, [float(p[0]),float(p[1])]
def empirical_threshold(rows,t):
    # smallest x such that P(win | score >= x) ... use P(win | pf == x window +-1)
    best=None
    for x in range(0,80):
        sub=[r["win"] for r in rows if abs(r["pf"]-x)<=1]
        if len(sub)>=50 and S.mean(sub)>=t: return x, len(sub), round(S.mean(sub),3)
    return None
def league(name, rows):
    R={}
    reg=[r for r in rows]
    R["n_team_games"]=len(reg); R["n_games"]=len(reg)//2
    R["ties"]=sum(1 for r in reg if r["win"]==0.5)
    R["mean_pts"]=round(S.mean(r["pf"] for r in reg),1); R["median_pts"]=S.median(r["pf"] for r in reg)
    R["sd_pts"]=round(S.pstdev(r["pf"] for r in reg),1)
    ths=[.5,.75,.9,.95]
    R["logit_thresholds_score"],R["logit"]=smooth_threshold(reg,ths)
    R["logit_thresholds_allow_max"]={str(t):R["logit_thresholds_score"][str(round(1-t,2))] if str(round(1-t,2)) in R["logit_thresholds_score"] else None for t in ths}
    lt,_=smooth_threshold(reg,[.25,.1,.05,.5])
    R["allow_at_most_for"]={"0.75":lt["0.25"],"0.9":lt["0.1"],"0.95":lt["0.05"],"0.5":lt["0.5"]}
    R["empirical_score_threshold_pm1"]={str(t):empirical_threshold(reg,t) for t in ths}
    # P(win | pf==x) table and P(win| pf>=x)
    tab={}
    for x in range(0,71):
        sub=[r["win"] for r in reg if r["pf"]==x]
        if sub: tab[x]=(len(sub),round(S.mean(sub),3))
    R["p_win_scored_exact"]=tab
    # mirror check
    mir=[]
    for x in (10,17,21,24,28,35):
        a=[r["win"] for r in reg if r["pf"]==x]; b=[r["win"] for r in reg if r["pa"]==x]
        if a and b: mir.append((x,round(S.mean(a)+S.mean(b),4)))
    R["mirror_check_sum"]=mir
    # <=14 allowed
    le=[r for r in reg if r["pa"]<=14]
    R["allow_le14"]={"n":len(le),"share_of_team_games":round(len(le)/len(reg),3),"p_win":round(S.mean(r["win"] for r in le),3),
        "p_win_given_scored_le14":round(S.mean(r["win"] for r in reg if r["pf"]<=14),3)}
    for k in (7,10,17,20):
        s=[r for r in reg if r["pa"]<=k]; R[f"allow_le{k}"]={"n":len(s),"share":round(len(s)/len(reg),3),"p_win":round(S.mean(r["win"] for r in s),3)}
    # per-season share <=14 first/last 5 yrs
    R["le14_share_2006_10"]=round(S.mean(1 if r["pa"]<=14 else 0 for r in reg if r["season"]<=2010),3)
    R["le14_share_2021_25"]=round(S.mean(1 if r["pa"]<=14 else 0 for r in reg if r["season"]>=2021),3)
    # YPP allowed
    yy=[r for r in reg if r.get("opp_plays",0)>=30]
    ypp=np.array([r["opp_yards"]/r["opp_plays"] for r in yy]); pa=np.array([r["pa"] for r in yy]); yds=np.array([r["opp_yards"] for r in yy])
    R["ypp"]={"n_team_games":len(yy),"seasons":[min(r["season"] for r in yy),max(r["season"] for r in yy)],
        "r_ypp_allowed_vs_pts_allowed":round(float(np.corrcoef(ypp,pa)[0,1]),3),
        "r2":round(float(np.corrcoef(ypp,pa)[0,1]**2),3),
        "r_total_yards_allowed_vs_pts_allowed":round(float(np.corrcoef(yds,pa)[0,1]),3),
        "spearman_ypp":None,
        "mean_ypp_allowed":round(float(ypp.mean()),2),
        "median_ypp_when_allowed_le14":round(float(np.median(ypp[pa<=14])),2),
        "iqr_ypp_when_allowed_le14":[round(float(np.percentile(ypp[pa<=14],25)),2),round(float(np.percentile(ypp[pa<=14],75)),2)],
        "median_ypp_when_allowed_ge28":round(float(np.median(ypp[pa>=28])),2),
        "slope_pts_per_1ypp":round(float(np.polyfit(ypp,pa,1)[0]),1)}
    from scipy.stats import spearmanr
    R["ypp"]["spearman_ypp"]=round(float(spearmanr(ypp,pa).correlation),3)
    # P(allow<=14 | ypp band)
    bands={}
    for lo in [3,4,4.5,5,5.5,6,6.5,7,8]:
        hi={3:4,4:4.5,4.5:5,5:5.5,5.5:6,6:6.5,6.5:7,7:8,8:20}[lo]
        m=(ypp>=lo)&(ypp<hi)
        if m.sum(): bands[f"{lo}-{hi}"]={"n":int(m.sum()),"p_allow_le14":round(float((pa[m]<=14).mean()),3),"mean_pa":round(float(pa[m].mean()),1)}
    if True:
        m=ypp<3; bands["<3"]={"n":int(m.sum()),"p_allow_le14":round(float((pa[m]<=14).mean()),3),"mean_pa":round(float(pa[m].mean()),1)}
    R["ypp"]["by_band"]=bands
    # ---------- season level (regular season) ----------
    ts={}
    for r in reg:
        if r["st"]!="regular": continue
        k=(r["season"],r["team"]); ts.setdefault(k,[]).append(r)
    seasons=[]
    for (y,t),rs in ts.items():
        if len(rs)<(8 if name=="CFB" else 14): continue
        seasons.append(dict(season=y,team=t,g=len(rs),ppg=S.mean(r["pf"] for r in rs),papg=S.mean(r["pa"] for r in rs),
            wp=S.mean(r["win"] for r in rs),PF=sum(r["pf"] for r in rs),PA=sum(r["pa"] for r in rs)))
    R["n_team_seasons"]=len(seasons)
    # season-centered
    bys={}
    for s in seasons: bys.setdefault(s["season"],[]).append(s)
    for y,L in bys.items():
        m=S.mean(s["ppg"] for s in L)
        for s in L: s["off"]=s["ppg"]-m; s["def"]=m-s["papg"]; s["margin"]=s["ppg"]-s["papg"]; s["tot"]=s["ppg"]+s["papg"]-2*m
    R["sd_ppg"]=round(S.pstdev(s["off"] for s in seasons),2); R["sd_papg"]=round(S.pstdev(s["def"] for s in seasons),2)
    R["corr_ppg_papg"]=round(float(np.corrcoef([s["ppg"] for s in seasons],[s["papg"] for s in seasons])[0,1]),3)
    # pythagorean exponent
    PF=np.array([s["PF"] for s in seasons],float); PA=np.array([s["PA"] for s in seasons],float); WP=np.array([s["wp"] for s in seasons]); G=np.array([s["g"] for s in seasons])
    def sse(k): p=PF**k/(PF**k+PA**k); return float(np.sum(G*(WP-p)**2))
    k=minimize_scalar(sse,bounds=(0.5,10),method="bounded").x
    rmse=math.sqrt(sse(k)/G.sum()); 
    R["pythag_exponent"]=round(float(k),2); R["pythag_rmse_winpct"]=round(float(math.sqrt(np.mean((WP-PF**k/(PF**k+PA**k))**2))),3)
    # regression wp ~ off + def
    X=np.column_stack([np.ones(len(seasons)),[s["off"] for s in seasons],[s["def"] for s in seasons]])
    b,res,_,_=np.linalg.lstsq(X,WP,rcond=None)
    resid=WP-X@b; sig2=resid@resid/(len(WP)-3); cov=sig2*np.linalg.inv(X.T@X)
    R["ols_wp_on_off_def"]={"b_off_per_ppg":round(float(b[1]),4),"b_def_per_ppg":round(float(b[2]),4),
        "se_off":round(float(math.sqrt(cov[1,1])),4),"se_def":round(float(math.sqrt(cov[2,2])),4),
        "diff_def_minus_off":round(float(b[2]-b[1]),4),"se_diff":round(float(math.sqrt(cov[1,1]+cov[2,2]-2*cov[1,2])),4)}
    # wp ~ margin + tot   (tot<0 = defense-led / low-scoring)
    X2=np.column_stack([np.ones(len(seasons)),[s["margin"] for s in seasons],[s["tot"] for s in seasons]])
    b2=np.linalg.lstsq(X2,WP,rcond=None)[0]; r2=WP-X2@b2; c2=(r2@r2/(len(WP)-3))*np.linalg.inv(X2.T@X2)
    R["ols_wp_on_margin_total"]={"b_margin":round(float(b2[1]),4),"b_total":round(float(b2[2]),4),"se_total":round(float(math.sqrt(c2[2,2])),4)}
    # matched-margin comparison: within margin bins, defense-led (off<0? ) define: defense-led = def > off (more of margin from D)
    bins={}
    width=2.0 if name=="CFB" else 1.0
    for s in seasons:
        bk=math.floor(s["margin"]/width)*width
        bins.setdefault(bk,{"D":[],"O":[]})["D" if s["def"]>s["off"] else "O"].append(s["wp"])
    diffs=[];wts=[];tab=[]
    for bk in sorted(bins):
        D,O=bins[bk]["D"],bins[bk]["O"]
        if len(D)>=10 and len(O)>=10:
            d=S.mean(D)-S.mean(O); n=2/(1/len(D)+1/len(O)); diffs.append(d); wts.append(n)
            tab.append({"margin_bin":[bk,bk+width],"n_def_led":len(D),"wp_def_led":round(S.mean(D),3),"n_off_led":len(O),"wp_off_led":round(S.mean(O),3)})
    R["matched_margin"]={"bin_width_ppg":width,"weighted_mean_diff_def_minus_off":round(float(np.average(diffs,weights=wts)),4),"bins":tab}
    # extreme profiles: weak offense (bottom quartile ppg rel season) - how good can they get?
    q=lambda arr,p: float(np.percentile(arr,p))
    offs=[s["off"] for s in seasons]; defs=[s["def"] for s in seasons]
    lo_off=q(offs,25); lo_def=q(defs,25)
    wo=[s for s in seasons if s["off"]<=lo_off]; wd=[s for s in seasons if s["def"]<=lo_def]
    eliteD=[s for s in wo if s["def"]>=q(defs,90)]; eliteO=[s for s in wd if s["off"]>=q(offs,90)]
    def summ(L): return {"n":len(L),"mean_wp":round(S.mean(s["wp"] for s in L),3) if L else None,
        "share_wp_ge_0.75":round(S.mean(1 if s["wp"]>=.75 else 0 for s in L),3) if L else None,
        "share_winning":round(S.mean(1 if s["wp"]>.5 else 0 for s in L),3) if L else None}
    R["weak_offense_bottom25"]=summ(wo); R["weak_defense_bottom25"]=summ(wd)
    R["weak_off_with_top10_def"]=summ(eliteD); R["weak_def_with_top10_off"]=summ(eliteO)
    # among top-wp teams (>=.75 / top 10% wp), how many had bottom-half offense vs bottom-half defense
    top=[s for s in seasons if s["wp"]>=q([x["wp"] for x in seasons],90)]
    R["top10pct_wp_teams"]={"n":len(top),"share_below_median_offense":round(S.mean(1 if s["off"]<q(offs,50) else 0 for s in top),3),
        "share_below_median_defense":round(S.mean(1 if s["def"]<q(defs,50) else 0 for s in top),3)}
    # rank-based: ppg percentile vs papg percentile symmetrical analysis: wp ~ percentile ranks
    from scipy.stats import rankdata
    ro=rankdata(offs)/len(offs); rd=rankdata(defs)/len(defs)
    X3=np.column_stack([np.ones(len(seasons)),ro,rd]); b3=np.linalg.lstsq(X3,WP,rcond=None)[0]
    R["ols_wp_on_percentile_ranks"]={"b_off_pctile":round(float(b3[1]),3),"b_def_pctile":round(float(b3[2]),3)}
    R["_seasons"]=seasons
    return R
out["CFB"]=league("CFB",cg); out["NFL"]=league("NFL",ng)
# NFL box coverage, CFB box coverage
out["CFB"]["box_coverage"]=round(sum(1 for r in cg if r.get("opp_plays",0)>=30)/len(cg),3)
# CFB box coverage by season
cov={}
for r in cg: cov.setdefault(r["season"],[0,0]); cov[r["season"]][0]+=1; cov[r["season"]][1]+= 1 if r.get("opp_plays",0)>=30 else 0
out["CFB"]["box_coverage_by_season"]={y:round(b/a,3) for y,(a,b) in sorted(cov.items())}
out["espn_score_validation"]={"team_scores_checked":val["n_checked"],"mismatches":val["mismatch"][:20],"n_mismatch":len(val["mismatch"])}
seas={k:out[k].pop("_seasons") for k in ("CFB","NFL")}
json.dump(out,open("results.json","w"),indent=1,default=str)
json.dump(seas,open("team_seasons.json","w"))
for k in ("CFB","NFL"):
    R=out[k]; print("=====",k); 
    for kk,v in R.items():
        if kk in ("p_win_scored_exact","box_coverage_by_season"): continue
        print(kk,":",v)
