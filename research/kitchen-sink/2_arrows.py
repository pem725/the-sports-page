#!/usr/bin/env python3
"""Numbers for each arrow of the time-of-possession DAG, from raw/pbp-lite.csv.gz (2016-2025 REG).
- lead -> run: run share by the offense's score margin (4th quarter, and whole game)
- run -> clock: seconds until the next snap after a run vs a pass (same game, same half)
- run vs pass: yards per play (passes include sacks)"""
import csv, gzip, json, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(gzip.open(os.path.join(HERE, "raw", "pbp-lite.csv.gz"), "rt")))
def band(m):
    m = int(float(m))
    return "behind 9+" if m <= -9 else "behind 1-8" if m < 0 else "tied" if m == 0 else "ahead 1-8" if m <= 8 else "ahead 9+"
ORDER = ["behind 9+", "behind 1-8", "tied", "ahead 1-8", "ahead 9+"]
share = {q: collections.Counter() for q in ("all", "q4")}; runs = {q: collections.Counter() for q in ("all", "q4")}
yds = collections.defaultdict(list); clock = collections.defaultdict(list)
for i, r in enumerate(rows):
    if r["score_differential"] == "": continue
    b = band(r["score_differential"]); isrun = r["play_type"] == "run"
    for q in ("all", "q4") if r["qtr"] == "4" else ("all",):
        share[q][b] += 1; runs[q][b] += isrun
    yds[r["play_type"]].append(float(r["yards_gained"] or 0))
    if i + 1 < len(rows):
        n = rows[i + 1]
        if n["game_id"] == r["game_id"] and n["posteam"] == r["posteam"] and n["qtr"] == r["qtr"] and r["qtr"] in "1234" and r["qtr"]:
            dt = float(r["game_seconds_remaining"]) - float(n["game_seconds_remaining"])
            if 0 <= dt <= 60: clock[r["play_type"]].append(dt)
out = {"plays": len(rows)}
for q in ("all", "q4"):
    out["run_share_" + q] = {b: round(100 * runs[q][b] / share[q][b], 1) for b in ORDER}
    print(q, out["run_share_" + q])
for k in ("run", "pass"):
    out[k] = {"yards_per_play": round(sum(yds[k]) / len(yds[k]), 2), "secs_to_next_snap": round(sum(clock[k]) / len(clock[k]), 1), "n": len(yds[k])}
    print(k, out[k])
json.dump(out, open(os.path.join(HERE, "arrows.json"), "w"), indent=1)
