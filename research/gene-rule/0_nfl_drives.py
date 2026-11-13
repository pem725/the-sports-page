#!/usr/bin/env python3
"""Gene's Rule, NFL: every drive since 1999, slimmed to what the test needs.

Streams nflverse play-by-play (regular season) and keeps one row per drive:
game, season, week, offense, defense, home/away, half, seconds left in the half at the
drive's start, how the drive started, how it ended, and the final score.
Output: data/nfl-drives.csv (one season per run is cached in data/raw/).
"""
import csv, gzip, io, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{y}.csv.gz"
csv.field_size_limit(10**8)


def season(y):
    out = os.path.join(RAW, f"drives{y}.csv")
    if os.path.exists(out) and y < 2026:
        return out
    data = urllib.request.urlopen(URL.format(y=y), timeout=300).read()
    rd = csv.DictReader(io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(data)), encoding="utf-8"))
    drives = {}
    for p in rd:
        if p["season_type"] != "REG" or not p["fixed_drive"] or not p["posteam"]:
            continue
        key = (p["game_id"], int(float(p["fixed_drive"])))
        if key not in drives:
            q = int(p["qtr"])
            drives[key] = dict(game=p["game_id"], season=y, week=p["week"], off=p["posteam"], deff=p["defteam"],
                               home=p["home_team"], away=p["away_team"], qtr=q,
                               half=1 if q <= 2 else (2 if q <= 4 else 3),
                               secs=p["half_seconds_remaining"] or "", start=p["drive_start_transition"],
                               result=p["fixed_drive_result"], hs=p["home_score"], as_=p["away_score"])
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["game", "drive", "season", "week", "off", "def", "home", "away", "qtr", "half", "secs",
                    "start", "result", "home_score", "away_score"])
        for (g, d), r in sorted(drives.items()):
            w.writerow([g, d, r["season"], r["week"], r["off"], r["deff"], r["home"], r["away"], r["qtr"],
                        r["half"], r["secs"], r["start"], r["result"], r["hs"], r["as_"]])
    return out


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    years = range(int(sys.argv[1]), int(sys.argv[2]) + 1) if len(sys.argv) > 2 else range(1999, 2027)
    for y in years:
        print(y, season(y), flush=True)
