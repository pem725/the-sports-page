import numpy as np, json
exec(open("analyze.py").read().split("out={}")[0])
res={}
for lab,rows,f in (("CFB 2006-2011",cg,lambda y:y<=2011),("CFB 2024-2025",cg,lambda y:y>=2024),("NFL 2006-2025",ng,lambda y:True),("NFL 2006-2011",ng,lambda y:y<=2011),("NFL 2024-2025",ng,lambda y:y>=2024)):
    yy=[r for r in rows if f(r["season"]) and r.get("opp_plays",0)>=30]
    ypp=np.array([r["opp_yards"]/r["opp_plays"] for r in yy]); pa=np.array([r["pa"] for r in yy]); yd=np.array([r["opp_yards"] for r in yy])
    pl=np.array([r["opp_plays"] for r in yy])
    res[lab]={"n":len(yy),"r_ypp_pts":round(float(np.corrcoef(ypp,pa)[0,1]),3),"r_yards_pts":round(float(np.corrcoef(yd,pa)[0,1]),3),
      "r_plays_pts":round(float(np.corrcoef(pl,pa)[0,1]),3),"mean_ypp":round(float(ypp.mean()),2),"mean_plays":round(float(pl.mean()),1),
      "median_ypp_le14":round(float(np.median(ypp[pa<=14])),2),"p_le14_given_ypp_lt4":round(float((pa[ypp<4]<=14).mean()),3),"n_ypp_lt4":int((ypp<4).sum()),
      "p_le14_given_ypp_ge6":round(float((pa[ypp>=6]<=14).mean()),3),"n_ypp_ge6":int((ypp>=6).sum()),
      "slope_pts_per_ypp":round(float(np.polyfit(ypp,pa,1)[0]),1)}
    # partial: does YPP add beyond yards? multiple R with ypp+plays
    X=np.column_stack([np.ones(len(yy)),ypp,pl]); b=np.linalg.lstsq(X,pa,rcond=None)[0]; pred=X@b
    res[lab]["R_ypp_plus_plays"]=round(float(np.corrcoef(pred,pa)[0,1]),3)
    print(lab,res[lab])
json.dump(res,open("ypp_split.json","w"),indent=1)
