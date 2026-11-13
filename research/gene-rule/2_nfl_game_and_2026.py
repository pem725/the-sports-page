#!/usr/bin/env python3
"""Gene's Rule, NFL, two follow-ups:
1. The fan's version: when the other team scores the game's first touchdown, how often does
   the team that answers on its next drive win, against the team that does not?
2. The 2026 Gene teams: answer rate this season, shrunk toward the league with a
   Beta-Binomial prior (about one season of opportunities' worth of league average, since
   year-to-year r is only .27), beside the plain scoring rate on every other drive.
"""
import importlib.util, json, os
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("nfl", os.path.join(HERE, "1_nfl.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
games = m.load(); ev = m.events(games); rec = m.results(games)

# 1. the fan's version
win = defaultdict(list)
for e in ev:
    if e["first"]:
        w = rec[(e["team"], e["season"], e["game"])][1]
        win["answered" if e["scored"] else "did not"].append(w)
        win[("TD" if e["td"] else ("FG" if e["scored"] else "none"))].append(w)
for k, v in win.items():
    print(f"down after the first TD, {str(k):9s}: n={len(v):5d}  won {np.mean(v):.3f}")

# 2. 2026
cur = [e for e in ev if e["season"] == 2026]
league = np.mean([e["scored"] for e in ev if e["kind"] == "answer" and e["season"] >= 2020])
K = 34  # prior weight, in opportunities
t = defaultdict(lambda: defaultdict(list))
for e in cur:
    t[e["team"]]["ans" if e["kind"] == "answer" else "oth"].append(e["scored"])
rows = []
for team, d in t.items():
    n, a = len(d["ans"]), sum(d["ans"])
    rows.append(dict(team=team, n=n, made=a, raw=a / n if n else None, shrunk=(a + K * league) / (n + K),
                     other=np.mean(d["oth"]), n_other=len(d["oth"])))
rows.sort(key=lambda r: -r["shrunk"])
print(f"\n2026 through {max(e['week'] for e in cur)} weeks; league answer rate since 2020 {league:.3f}")
for r in rows:
    print(f"{r['team']:4s} answered {r['made']:2d} of {r['n']:2d} ({r['raw']:.2f})  shrunk {r['shrunk']:.2f}   other drives {r['other']:.2f} (n={r['n_other']})")
rec26 = defaultdict(lambda: [0, 0, 0])
for (tm, ss, g), (w, wn, pd) in rec.items():
    if ss == 2026:
        rec26[tm][0 if wn == 1 else (1 if wn == 0 else 2)] += 1
for r in rows:
    r["rec"] = rec26[r["team"]]
json.dump(dict(fan={str(k): [len(v), float(np.mean(v))] for k, v in win.items()}, league=league, K=K, teams=rows,
               week=max(e['week'] for e in cur)), open(os.path.join(HERE, "data", "nfl-2026.json"), "w"), indent=1, default=float)
