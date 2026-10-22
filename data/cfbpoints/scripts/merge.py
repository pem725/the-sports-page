import json, statistics as S
exec(open("analyze.py").read().split("out={}")[0])
res=json.load(open("results.json")); ex=json.load(open("extra.json")); yp=json.load(open("ypp_split.json"))
for L,rows in (("CFB",cg),("NFL",ng)):
    ts={}
    for r in rows:
        if r["st"]=="regular": ts.setdefault((r["season"],r["team"]),[]).append(r)
    ts={k:v for k,v in ts.items() if len(v)>=(8 if L=="CFB" else 14)}
    allg=[k for k,v in ts.items() if all(r["pa"]<=14 for r in v)]
    shares=sorted(S.mean(1 if r["pa"]<=14 else 0 for r in v) for v in ts.values())
    res[L]["hold_everyone_le14"]={"team_seasons":len(ts),"seasons_all_games_le14":len(allg),"examples":allg[:10],
        "median_team_share_games_le14":round(S.median(shares),3),"p90_team_share":round(shares[int(.9*len(shares))],3)}
    for x in (14,15,17):
        s=[r["win"] for r in rows if r["pa"]==x]; res[L][f"p_win_allowed_exactly_{x}"]=[len(s),round(S.mean(s),3)]
    res[L]["thresholds_window"]=ex[L]; res[L]["ypp_split"]={k:v for k,v in yp.items() if k.startswith(L)}
res["validation"]={"espn_crosscheck":res.pop("espn_score_validation"),
  "note":"1,775 FBS-vs-FBS games (2011 wk12+, 2024, 2025) cross-checked team-by-team vs ESPN summary: 0 score errors; 2 games (2024 Myrtle Beach Bowl, 2024 Las Vegas Bowl) have home/away labels swapped between sources, scores identical.",
  "spot_checks":[["2006 Fiesta Bowl","Boise State 43, Oklahoma 42","match"],["2013 Iron Bowl","Auburn 34, Alabama 28","match"],["2019 CFP final","LSU 42, Clemson 25","match"]]}
res["data_notes"]={"cfb_games":"CFBD /games 2006-2025 regular+postseason, both teams classification fbs, completed",
  "cfb_box":"CFBD /games/teams 2006 through 2011 week 11; CFBD monthly quota exhausted mid-pull (X-CallLimit-Remaining 0); filled 2011 remainder + 2024 + 2025 from ESPN summary API. 2012-2023 box scores NOT pulled.",
  "cfb_plays":"rushingAttempts + pass attempts (college counts sacks as rushes, so sacks included)",
  "nfl":"data/nfl/team-games.csv (nflverse-derived, scrimmage plays incl. sacks), 2006-2025, REG+POST for per-game; REG only for team-seasons; ties = 0.5 win",
  "season_level":"regular season only; CFB team-season requires >=8 FBS-vs-FBS games; PPG/PAPG over FBS opponents only, centered on each season's mean"}
json.dump(res,open("results.json","w"),indent=1,default=str)
for L in ("CFB","NFL"): print(L,res[L]["hold_everyone_le14"],[res[L][f"p_win_allowed_exactly_{x}"] for x in (14,15,17)])
