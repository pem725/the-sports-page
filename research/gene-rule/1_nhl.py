#!/usr/bin/env python3
"""Gene's Rule, hockey analog: after the other team scores, is the NEXT goal yours, and how
fast? Shootouts excluded. The fair comparison is the same team's share of next goals after
it scored itself, and its share of all goals (GF%).
Hockey has a known wrinkle: a trailing team presses and outshoots ("score effects"), so a
league-wide answer edge would be expected even if no team has a special gift for it.
"""
import csv, glob, json, os
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
QUICK = 300  # five minutes of game time
goals = defaultdict(list); final = {}
for p in sorted(glob.glob(os.path.join(HERE, "data", "raw", "nhl-goals-*.csv"))):
    for r in csv.DictReader(open(p)):
        g = r["game"]; s = int(r["season"]) // 10000
        final[g] = (s, r["home"], r["away"], int(r["home_final"]), int(r["away_final"]), r["ended"])
        if r["t"]:
            goals[g].append((int(r["t"]), r["team"]))
ev = []  # (team, season, game, kind, next_is_ours, quick)
for g, (s, h, a, hf, af, ended) in final.items():
    gs = sorted(goals[g])
    for i, (t, team) in enumerate(gs):
        nxt = gs[i + 1] if i + 1 < len(gs) else None
        for side in (h, a):
            kind = "answer" if team != side else "after_own"
            ours = bool(nxt and nxt[1] == side)
            ev.append((side, s, g, kind, ours, ours and nxt[0] - t <= QUICK))
E = defaultdict(list)
for side, s, g, kind, ours, q in ev:
    E[kind].append((ours, q))
for k, v in E.items():
    v = np.array(v)
    print(f"{k:9s} n={len(v)}  next goal ours {v[:,0].mean():.3f}  within 5 min {v[:,1].mean():.3f}")
ts = defaultdict(lambda: defaultdict(list)); res = defaultdict(list)
for side, s, g, kind, ours, q in ev:
    ts[(side, s)][kind].append(ours); ts[(side, s)][kind + "_q"].append(q)
for g, (s, h, a, hf, af, ended) in final.items():
    res[(h, s)].append((1.0 if hf > af else 0.0, hf, af)); res[(a, s)].append((1.0 if af > hf else 0.0, af, hf))
rows = []
for k, d in ts.items():
    if k[1] == 2026 or not d["answer"]:
        continue
    w = np.array(res[k])
    rows.append(dict(team=k[0], season=k[1], n=len(d["answer"]), ans=np.mean(d["answer"]), quick=np.mean(d["answer_q"]),
                     own=np.mean(d["after_own"]), gf=w[:, 1].sum() / (w[:, 1].sum() + w[:, 2].sum()), win=w[:, 0].mean()))
X = {k: np.array([r[k] for r in rows]) for k in ("ans", "quick", "own", "gf", "win", "n")}
c = lambda a, b: float(np.corrcoef(a, b)[0, 1])
by = {(r["team"], r["season"]): r for r in rows}
pairs = [(by[k], by[(k[0], k[1] + 1)]) for k in by if (k[0], k[1] + 1) in by]
yty = lambda f: c(np.array([f(a) for a, b in pairs]), np.array([f(b) for a, b in pairs]))
out = dict(n_games=len(final), league={k: [len(v), float(np.mean([x[0] for x in v])), float(np.mean([x[1] for x in v]))] for k, v in E.items()},
           corr=dict(ans_win=c(X["ans"], X["win"]), quick_win=c(X["quick"], X["win"]), gf_win=c(X["gf"], X["win"]),
                     prem_win=c(X["ans"] - X["gf"], X["win"])),
           yty=dict(ans=yty(lambda r: r["ans"]), gf=yty(lambda r: r["gf"]), prem=yty(lambda r: r["ans"] - r["gf"])),
           n_median=float(np.median(X["n"])))
print(json.dumps(out, indent=1))
for r in sorted(rows, key=lambda r: -r["ans"])[:6]:
    print("top", r["team"], r["season"], f"next goal {r['ans']:.3f} of {r['n']}, quick {r['quick']:.3f}, GF% {r['gf']:.3f}, win {r['win']:.3f}")
for r in rows:
    if r["team"] == "NYR": print("NYR", r["season"], f"{r['ans']:.3f} n={r['n']} quick {r['quick']:.3f} GF% {r['gf']:.3f} win {r['win']:.3f}")
json.dump(dict(R=out, rows=rows), open(os.path.join(HERE, "data", "nhl-results.json"), "w"), default=float)
