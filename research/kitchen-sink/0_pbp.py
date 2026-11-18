#!/usr/bin/env python3
"""Fetch nflverse play-by-play (regular season) and keep only what the time-of-possession piece
needs: one row per run or pass with score differential, yards, and clock used. raw/pbp-lite.csv.gz"""
import csv, gzip, io, os, urllib.request
URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{y}.csv.gz"
KEEP = ["game_id", "season", "season_type", "week", "posteam", "defteam", "qtr", "game_seconds_remaining",
        "score_differential", "play_type", "yards_gained", "rush", "pass", "qb_kneel", "qb_spike", "drive", "result",
        "home_team", "posteam_type", "wp"]
out = gzip.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw", "pbp-lite.csv.gz"), "wt", newline="")
w = csv.writer(out); w.writerow(KEEP)
for y in range(2016, 2026):
    data = urllib.request.urlopen(URL.format(y=y), timeout=300).read()
    n = 0
    for r in csv.DictReader(io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(data)), encoding="utf-8")):
        if r["season_type"] != "REG" or r["play_type"] not in ("run", "pass"): continue
        if r["qb_kneel"] == "1" or r["qb_spike"] == "1": continue
        w.writerow([r.get(k, "") for k in KEEP]); n += 1
    print(y, n, flush=True)
out.close()
