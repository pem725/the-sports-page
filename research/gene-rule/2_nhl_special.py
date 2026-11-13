#!/usr/bin/env python3
"""The editor's Rangers point: Gene teams in hockey "took opportunities when they came, so
they tended to be really good on power plays. And surprisingly ... stingy at defending
power plays." Four tests, 2015-16 to 2025-26 regular seasons:
  1. Do power play and penalty kill go together (good at one, good at the other)?
  2. Do answering teams have better special teams, and is that beyond scoring (GF%)?
  3. Are answer goals more often power-play goals than goals in general?
  4. How stable is each from one year to the next?
Special teams from the NHL stats API (team/powerplay, team/penaltykill); power-play goals
also counted from the play-by-play situation codes as a second source.
"""
import csv, glob, json, os, urllib.request
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.nhle.com/stats/rest/en/team/{k}?cayenneExp=seasonId={s}%20and%20gameTypeId=2"
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "sports-page-research"}), timeout=60))
tri = {t["id"]: t["triCode"] for t in get("https://api.nhle.com/stats/rest/en/team")["data"]}

cache = os.path.join(HERE, "data", "raw", "nhl-special.json")
if os.path.exists(cache):
    ST = json.load(open(cache))
else:
    ST = {}
    for y in range(2015, 2027):
        sid = f"{y}{y + 1}"
        pp = {tri[r["teamId"]]: r for r in get(API.format(k="powerplay", s=sid))["data"]}
        pk = {tri[r["teamId"]]: r for r in get(API.format(k="penaltykill", s=sid))["data"]}
        for t in pp:
            ST[f"{t}|{y}"] = dict(pp=pp[t]["powerPlayPct"], ppg=pp[t]["powerPlayGoalsFor"], ppo=pp[t]["ppOpportunities"],
                                  pk=pk[t]["penaltyKillPct"], ppga=pk[t]["ppGoalsAgainst"], tsh=pk[t]["timesShorthanded"])
    json.dump(ST, open(cache, "w"))


def on_pp(sit, home_scored):
    """situationCode: away goalie, away skaters, home skaters, home goalie."""
    if len(sit) != 4:
        return None
    ag, a, h, hg = (int(c) for c in sit)
    own, opp, goalie = (h, a, hg) if home_scored else (a, h, ag)
    return goalie == 1 and own > opp


goals = defaultdict(list)
for p in sorted(glob.glob(os.path.join(HERE, "data", "raw", "nhl-goals-*.csv"))):
    for r in csv.DictReader(open(p)):
        if r["t"]:
            goals[(r["game"], int(r["season"]) // 10000, r["home"], r["away"])].append(
                (int(r["t"]), r["team"], on_pp(r["sit"], r["team"] == r["home"])))
T = defaultdict(lambda: dict(ans=[], ans_pp=[], gf=0, ga=0, ppg=0))
lg = dict(ans_goals=0, ans_goals_pp=0, all_goals=0, all_pp=0)
for (g, s, h, a), gs in goals.items():
    gs.sort()
    for i, (t, team, pp) in enumerate(gs):
        lg["all_goals"] += 1; lg["all_pp"] += bool(pp)
        T[(team, s)]["gf"] += 1; T[(team, s)]["ppg"] += bool(pp)
        other = a if team == h else h
        T[(other, s)]["ga"] += 1
        nxt = gs[i + 1] if i + 1 < len(gs) else None
        ours = bool(nxt and nxt[1] == other)
        T[(other, s)]["ans"].append(ours)
        if ours:
            lg["ans_goals"] += 1; lg["ans_goals_pp"] += bool(nxt[2])
            T[(other, s)]["ans_pp"].append(bool(nxt[2]))

rows = []
for (team, s), d in T.items():
    k = f"{team}|{s}"
    if s == 2026 or k not in ST or not d["ans"]:
        continue
    st = ST[k]
    rows.append(dict(team=team, season=s, ans=np.mean(d["ans"]), gf=d["gf"] / (d["gf"] + d["ga"]),
                     pp=st["pp"], pk=st["pk"], ppg_api=st["ppg"], ppg_pbp=d["ppg"]))
X = {k: np.array([r[k] for r in rows]) for k in ("ans", "gf", "pp", "pk", "ppg_api", "ppg_pbp")}
X["prem"] = X["ans"] - X["gf"]
c = lambda a, b: float(np.corrcoef(a, b)[0, 1])


def partial(a, b, z):
    """corr(a, b) holding z fixed"""
    ra = a - np.polyval(np.polyfit(z, a, 1), z); rb = b - np.polyval(np.polyfit(z, b, 1), z)
    return c(ra, rb)


by = {(r["team"], r["season"]): r for r in rows}
pairs = [(by[k], by[(k[0], k[1] + 1)]) for k in by if (k[0], k[1] + 1) in by]
yty = lambda f: c(np.array([f(x) for x, _ in pairs]), np.array([f(y) for _, y in pairs]))
out = dict(
    n=len(rows),
    ppg_check=dict(r=c(X["ppg_api"], X["ppg_pbp"]), mean_gap=float(np.mean(np.abs(X["ppg_api"] - X["ppg_pbp"])))),
    pp_pk=c(X["pp"], X["pk"]),
    ans_pp=c(X["ans"], X["pp"]), ans_pk=c(X["ans"], X["pk"]),
    ans_pp_given_gf=partial(X["ans"], X["pp"], X["gf"]), ans_pk_given_gf=partial(X["ans"], X["pk"], X["gf"]),
    prem_pp=c(X["prem"], X["pp"]), prem_pk=c(X["prem"], X["pk"]),
    gf_pp=c(X["gf"], X["pp"]), gf_pk=c(X["gf"], X["pk"]),
    yty=dict(pp=yty(lambda r: r["pp"]), pk=yty(lambda r: r["pk"]), ans=yty(lambda r: r["ans"]), gf=yty(lambda r: r["gf"])),
    share_pp=dict(answers=lg["ans_goals_pp"] / lg["ans_goals"], all=lg["all_pp"] / lg["all_goals"],
                  n_answers=lg["ans_goals"], n_all=lg["all_goals"]))
print(json.dumps(out, indent=1))
# Is "good at both" more common than chance? top third on PP and top third on PK
q = lambda v, p: np.quantile(v, p)
both = np.mean((X["pp"] >= q(X["pp"], 2 / 3)) & (X["pk"] >= q(X["pk"], 2 / 3)))
print(f"top third on both: {both:.3f} (chance: {1/9:.3f})")
out["top_both"] = float(both)
rank = lambda k, r: 1 + sum(1 for x in rows if x["season"] == r["season"] and x[k] > r[k])
nteams = lambda s: sum(1 for x in rows if x["season"] == s)
print("\nRangers, rank in the league (1 = best):")
ny = []
for r in sorted((r for r in rows if r["team"] == "NYR"), key=lambda r: r["season"]):
    row = dict(season=r["season"], teams=nteams(r["season"]), ans=rank("ans", r), pp=rank("pp", r), pk=rank("pk", r),
               gf=rank("gf", r), pp_pct=r["pp"], pk_pct=r["pk"], ans_rate=r["ans"])
    ny.append(row)
    print(f"  {r['season']}-{str(r['season'] + 1)[2:]}  answer #{row['ans']:2d}  GF% #{row['gf']:2d}  PP #{row['pp']:2d} ({r['pp']:.3f})  PK #{row['pk']:2d} ({r['pk']:.3f})  of {row['teams']}")
out["rangers"] = ny
json.dump(out, open(os.path.join(HERE, "data", "nhl-special-results.json"), "w"), indent=1, default=float)
