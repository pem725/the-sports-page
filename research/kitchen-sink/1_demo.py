#!/usr/bin/env python3
"""Kitchen-sink regression on NFL team-games, 1999-2025 (data/nfl/team-games.csv, nflverse).

Part 1, retrospective: win ~ same-game box stats. Watch the coefficient on plays flip sign once
time of possession enters, and yards flip once yards per play enters. With ~14,000 team-games
every flip is "significant": power does not rescue a confused model.
Part 2, prospective: win ~ season-to-date differences known before kickoff (week 4 on), fit on
1999-2017, scored on 2018-2025. One variable (season-to-date point margin) vs everything.
Needs pandas + statsmodels.
"""
import pandas as pd, statsmodels.formula.api as smf

d = pd.read_csv("data/nfl/team-games.csv")
d["top"] = d.top_seconds / 60; d["ypp"] = d.yards / d.plays; d["margin"] = d.points_for - d.points_against
r = d[d.points_for != d.points_against]
print(r[["plays", "yards", "top", "turnovers", "ypp"]].corr().round(2))
for f in ["win~plays", "win~top", "win~plays+top", "win~plays+top+yards", "win~plays+top+yards+ypp+turnovers"]:
    m = smf.logit(f, r).fit(disp=0)
    print("RETRO", f, {k: f"{v:.3f} (z {m.tvalues[k]:.0f})" for k, v in m.params.items() if k != "Intercept"})

cols = ["plays", "yards", "top", "turnovers", "ypp", "margin"]
d = d.sort_values(["season", "team", "week"])
for c in cols:
    d["pre_" + c] = d.groupby(["season", "team"])[c].transform(lambda s: s.shift().expanding().mean())
o = d[["game_id", "team"] + ["pre_" + c for c in cols]].rename(columns={"team": "opp", **{"pre_" + c: "opp_" + c for c in cols}})
d = d.merge(o, on=["game_id", "opp"])
for c in cols: d["dif_" + c] = d["pre_" + c] - d["opp_" + c]
d = d[(d.week >= 4) & (d.points_for != d.points_against)].dropna()
tr, te = d[d.season < 2018], d[d.season >= 2018]
for f in ["win~dif_margin+home", "win~dif_ypp+dif_turnovers+home",
          "win~dif_plays+dif_yards+dif_top+dif_turnovers+dif_ypp+dif_margin+home"]:
    m = smf.logit(f, tr).fit(disp=0)
    print("PRO", f, "out-of-sample", round(((m.predict(te) > .5) == te.win).mean(), 3),
          {k: round(v, 3) for k, v in m.params.items() if k.startswith("dif")})
