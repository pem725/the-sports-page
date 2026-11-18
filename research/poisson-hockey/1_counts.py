#!/usr/bin/env python3
"""Poisson and hockey: does a team's goal count in a game follow the Poisson curve?

Reads every regular-season goal since 2015-16 (research/gene-rule/data/raw/nhl-goals-*.csv,
NHL API play-by-play). Counts each team's goals per game three ways: all goals but the
shootout, regulation only (periods 1-3), and regulation minus empty-net goals.
"""
import csv, glob, json, math, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "gene-rule", "data", "raw")

games = {}  # gid -> dict
for fn in sorted(glob.glob(os.path.join(RAW, "nhl-goals-20[12][0-9].csv"))):
    if fn.endswith("2026.csv"): continue  # complete seasons only
    for r in csv.DictReader(open(fn)):
        g = games.setdefault(r["game"], {"season": r["season"], "home": r["home"], "away": r["away"],
                                          "hf": int(r["home_final"]), "af": int(r["away_final"]),
                                          "ended": r["ended"], "goals": []})
        if r["team"]:
            g["goals"].append((int(r["period"]), int(r["t"]), r["team"], r["sit"]))

def empty_net(team, home, sit):
    if len(sit) != 4: return False
    ag, hg = sit[0], sit[3]
    return (hg == "0") if team != home else (ag == "0")

def tally(mode):
    c = collections.Counter(); seasons = collections.defaultdict(collections.Counter)
    for gid, g in games.items():
        for side in ("home", "away"):
            team = g[side]
            n = 0
            for p, t, tm, sit in g["goals"]:
                if tm != team: continue
                if mode != "all" and p > 3: continue
                if mode == "reg_noen" and empty_net(tm, g["home"], sit): continue
                n += 1
            c[n] += 1; seasons[g["season"]][n] += 1
    return c, seasons

def pois(k, lam): return math.exp(-lam) * lam**k / math.factorial(k)

out = {"games": len(games)}
for mode in ("all", "reg", "reg_noen"):
    c, _ = tally(mode)
    N = sum(c.values()); lam = sum(k*v for k, v in c.items())/N
    var = sum(v*(k-lam)**2 for k, v in c.items())/N
    rows = []
    print(f"\n== {mode}: {N} team-games, mean {lam:.3f}, var {var:.3f}, var/mean {var/lam:.3f}")
    chi = 0
    for k in range(0, 11):
        obs = c[k] if k < 10 else sum(v for kk, v in c.items() if kk >= 10)
        exp = N*pois(k, lam) if k < 10 else N*(1-sum(pois(j, lam) for j in range(10)))
        chi += (obs-exp)**2/exp
        rows.append({"k": k, "obs": obs, "exp": round(exp, 1)})
        print(f"{k:>3} {obs:>7} {exp:>9.1f} {obs/exp:6.2f}")
    print("chi2", round(chi, 1), "df 9")
    out[mode] = {"N": N, "mean": lam, "var": var, "rows": rows, "chi2": chi}
json.dump(out, open(os.path.join(HERE, "counts.json"), "w"), indent=1)
