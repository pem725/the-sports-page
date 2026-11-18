#!/usr/bin/env python3
"""95% intervals for fourth-quarter run share by score band, by bootstrapping GAMES (plays inside
one game are not independent, so a plain binomial interval would be too narrow). 2,000 resamples.
Writes intervals.json; 3_figures.py draws them as error bars."""
import csv, gzip, json, os, collections
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = ["behind 9+", "behind 1-8", "tied", "ahead 1-8", "ahead 9+"]
def band(m):
    m = int(float(m))
    return 0 if m <= -9 else 1 if m < 0 else 2 if m == 0 else 3 if m <= 8 else 4
g = collections.defaultdict(lambda: np.zeros((5, 2)))  # game -> [band][runs, plays]
for r in csv.DictReader(gzip.open(os.path.join(HERE, "raw", "pbp-lite.csv.gz"), "rt")):
    if r["qtr"] != "4" or r["score_differential"] == "": continue
    b = band(r["score_differential"]); g[r["game_id"]][b] += (r["play_type"] == "run", 1)
A = np.stack(list(g.values()))  # games x 5 x 2
rng = np.random.default_rng(20261118)
boots = []
for _ in range(2000):
    s = A[rng.integers(0, len(A), len(A))].sum(0)
    boots.append(100 * s[:, 0] / s[:, 1])
boots = np.array(boots); tot = A.sum(0)
out = {"games": len(A), "resamples": 2000}
for i, k in enumerate(ORDER):
    lo, hi = np.percentile(boots[:, i], [2.5, 97.5])
    out[k] = {"share": 100 * tot[i, 0] / tot[i, 1], "lo": lo, "hi": hi, "plays": int(tot[i, 1])}
    print(f"{k:11} {out[k]['share']:5.1f}  [{lo:5.1f}, {hi:5.1f}]  plays {int(tot[i,1])}")
json.dump(out, open(os.path.join(HERE, "intervals.json"), "w"), indent=1)

# Same game-level bootstrap for the numbers quoted in the text: yards per run / per pass,
# seconds to the next snap after a run / pass (all quarters), and Q4 seconds per snap ahead 9+ / behind 9+.
rows = list(csv.DictReader(gzip.open(os.path.join(HERE, "raw", "pbp-lite.csv.gz"), "rt")))
G = collections.defaultdict(lambda: np.zeros(12))  # sums,counts for 6 quantities
for i, r in enumerate(rows):
    v = G[r["game_id"]]; k = 0 if r["play_type"] == "run" else 1
    v[2*k] += float(r["yards_gained"] or 0); v[2*k+1] += 1
    if i + 1 < len(rows):
        n = rows[i + 1]
        if n["game_id"] == r["game_id"] and n["posteam"] == r["posteam"] and n["qtr"] == r["qtr"] and r["qtr"] in ("1", "2", "3", "4"):
            dt = float(r["game_seconds_remaining"]) - float(n["game_seconds_remaining"])
            if 0 <= dt <= 60:
                v[4+2*k] += dt; v[5+2*k] += 1
                if r["qtr"] == "4" and r["score_differential"] != "":
                    m = int(float(r["score_differential"]))
                    if m >= 9: v[8] += dt; v[9] += 1
                    if m <= -9: v[10] += dt; v[11] += 1
B = np.stack(list(G.values())); names = ["yds_run", "yds_pass", "secs_run", "secs_pass", "q4secs_ahead9", "q4secs_behind9"]
bs = np.array([(lambda s: s[0::2] / s[1::2])(B[rng.integers(0, len(B), len(B))].sum(0)) for _ in range(2000)])
pt = B.sum(0); pt = pt[0::2] / pt[1::2]
for j, nm in enumerate(names):
    lo, hi = np.percentile(bs[:, j], [2.5, 97.5]); out[nm] = {"est": pt[j], "lo": lo, "hi": hi}
    print(f"{nm:15} {pt[j]:5.2f} [{lo:5.2f}, {hi:5.2f}]")
json.dump(out, open(os.path.join(HERE, "intervals.json"), "w"), indent=1)
