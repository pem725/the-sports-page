#!/usr/bin/env python3
"""Gene's Rule, baseball analog: after the other team scores in a half-inning, do you score
in your very next turn at bat? (The "answer back"; its mirror is the "shutdown inning".)

OPPORTUNITY: the opponent scores 1+ runs in a half-inning and our next half-inning is played.
ANSWERED: we score 1+ runs in it. Baseline: our other half-innings. Retrosheet line scores.
"""
import csv, json, os
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def halves(r):
    v = [None if x == "x" else int(x) for x in r["v_line"].split()]
    h = [None if x == "x" else int(x) for x in r["h_line"].split()]
    seq = []  # (team, runs) in batting order
    for i in range(max(len(v), len(h))):
        if i < len(v) and v[i] is not None: seq.append((r["visitor"], v[i]))
        if i < len(h) and h[i] is not None: seq.append((r["home"], h[i]))
    return seq


ev = []
res = {}
for r in csv.DictReader(open(os.path.join(HERE, "data", "raw", "mlb-lines.csv"))):
    s = int(r["season"]); g = r["date"] + r["home"] + r["visitor"]
    seq = halves(r)
    vr, hr = int(r["v_runs"]), int(r["h_runs"])
    res[(r["visitor"], s, g)] = 1.0 if vr > hr else 0.0
    res[(r["home"], s, g)] = 1.0 if hr > vr else 0.0
    for i, (t, runs) in enumerate(seq):
        prev = seq[i - 1] if i else None
        ans = bool(prev and prev[0] != t and prev[1] > 0)
        ev.append((t, s, g, ans, runs > 0))

E = np.array([(a, sc) for _, _, _, a, sc in ev])
print(f"{len(ev)} half-innings; answer-backs {E[:,0].sum():.0f}: scored {E[E[:,0]==1,1].mean():.3f}; other halves {E[E[:,0]==0,1].mean():.3f}")
ts = defaultdict(lambda: [[], []])
for t, s, g, a, sc in ev:
    ts[(t, s)][int(a)].append(sc)
wins = defaultdict(list)
for (t, s, g), w in res.items():
    wins[(t, s)].append(w)
rows = [dict(team=t, season=s, n=len(d[1]), ans=np.mean(d[1]), base=np.mean(d[0]), win=np.mean(wins[(t, s)]))
        for (t, s), d in ts.items()]
X = {k: np.array([r[k] for r in rows]) for k in ("ans", "base", "win", "n")}
c = lambda a, b: float(np.corrcoef(a, b)[0, 1])
prem = X["ans"] - X["base"]
by = {(r["team"], r["season"]): r for r in rows}
pairs = [(by[k], by[(k[0], k[1] + 1)]) for k in by if (k[0], k[1] + 1) in by]
yty = lambda f: c(np.array([f(a) for a, b in pairs]), np.array([f(b) for a, b in pairs]))
out = dict(n_half=len(ev), ans=float(E[E[:,0]==1,1].mean()), other=float(E[E[:,0]==0,1].mean()),
           corr=dict(ans_win=c(X["ans"], X["win"]), base_win=c(X["base"], X["win"]), prem_win=c(prem, X["win"])),
           yty=dict(ans=yty(lambda r: r["ans"]), base=yty(lambda r: r["base"]), prem=yty(lambda r: r["ans"] - r["base"])),
           n_opp_median=float(np.median(X["n"])))
print(json.dumps(out, indent=1))
for key in (("NYN", 1986), ("NYN", 2024), ("NYN", 2025)):
    r = by.get(key)
    if r: print(key, f"answered {r['ans']:.3f} of {r['n']} chances; other halves {r['base']:.3f}; won {r['win']:.3f}")
top = sorted(rows, key=lambda r: -r["ans"])[:8]
for r in top: print("top", r["team"], r["season"], f"{r['ans']:.3f} n={r['n']} base {r['base']:.3f} win {r['win']:.3f}")
json.dump(dict(R=out, rows=rows), open(os.path.join(HERE, "data", "mlb-results.json"), "w"), default=float)
