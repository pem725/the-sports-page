#!/usr/bin/env python3
"""95% intervals for the per-100 bars in figure.svg: bootstrap whole GAMES (the two team-games in
one game share a night, a rink and each other's goals). 2,000 resamples. Writes intervals.json."""
import csv, glob, json, os, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "gene-rule", "data", "raw")
g = collections.defaultdict(collections.Counter); sides = {}
for fn in sorted(glob.glob(os.path.join(RAW, "nhl-goals-20[12][0-9].csv"))):
    if fn.endswith("2026.csv"): continue
    for r in csv.DictReader(open(fn)):
        sides[r["game"]] = (r["home"], r["away"])
        if r["team"]: g[r["game"]][r["team"]] += 1
K = 9  # 0..7, 8+
A = np.zeros((len(sides), K))
for i, (gid, (h, a)) in enumerate(sides.items()):
    for t in (h, a): A[i, min(g[gid][t], 8)] += 1
rng = np.random.default_rng(20261118)
bs = np.array([(lambda s: 100 * s / s.sum())(A[rng.integers(0, len(A), len(A))].sum(0)) for _ in range(2000)])
pt = 100 * A.sum(0) / A.sum()
out = {"games": len(A), "rows": []}
for k in range(K):
    lo, hi = np.percentile(bs[:, k], [2.5, 97.5])
    out["rows"].append({"k": k, "per100": pt[k], "lo": lo, "hi": hi})
    print(k, round(pt[k], 2), round(lo, 2), round(hi, 2))
json.dump(out, open(os.path.join(HERE, "intervals.json"), "w"), indent=1)
