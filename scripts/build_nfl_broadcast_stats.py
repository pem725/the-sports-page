#!/usr/bin/env python3
"""Aggregate the statistics a television booth actually cites, per team per game.

    python3 scripts/build_nfl_broadcast_stats.py               # 2016-2025
    python3 scripts/build_nfl_broadcast_stats.py --from 2024

WHY THIS EXISTS. Tim's idea, and it is a good one: rank the numbers a broadcast
throws at you by whether any of them predict anything. A viewer is handed nine or
ten figures a game — third down percentage, time of possession, total yards,
turnover margin, penalties — with no indication of which carry information and
which are decoration. Nobody sorts them, so we will.

The companion `build_nfl_history.py` already covers plays, yards, possession and
turnovers. This adds the rest of the broadcast furniture:

    third down      converted and attempted, the most-cited rate on television
    fourth down     converted and attempted
    first downs     the oldest "who is winning" proxy there is
    penalties       count and yards, the discipline narrative
    sacks           taken and recorded
    explosive plays gains of 20+ yards, the modern analytics favourite
    red zone        trips inside the 20 and how many produced a touchdown
    completions     attempts and completion rate
    rush/pass yards the split every halftime show leads with

WHAT COUNTS AS A PLAY. Scrimmage only — run, pass, sack, kneel, spike. A punt is
not an offensive snap, and including kicks makes a good punt team look like an
offence. Penalties are credited to the team that committed them, read from
`penalty_team` rather than assumed to be the offence, because a defensive hold is
the defence's foul and half of all penalties are not the offence's.

RED ZONE IS COUNTED BY DRIVE, NOT BY PLAY. A drive that reaches the twenty is one
trip regardless of how many snaps it takes; counting plays inside the twenty
rewards teams that stall there, which is precisely backwards.

Streamed with the stdlib. This repo has no pandas on purpose — CI installs from
requirements.txt and a dependency added for one analysis is a dependency forever.
"""
import argparse
import csv
import gzip
import io
import pathlib
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "nfl" / "broadcast-stats.csv"
URL = ("https://github.com/nflverse/nflverse-data/releases/download/pbp/"
       "play_by_play_{year}.csv.gz")
FIELDS = ["season", "week", "game_id", "team", "opp",
          "third_att", "third_conv", "fourth_att", "fourth_conv", "first_downs",
          "penalties", "penalty_yards", "sacks_taken", "sacks_made",
          "explosive", "rz_trips", "rz_td", "pass_att", "completions",
          "rush_yards", "pass_yards"]


def one(v):
    return v == "1" or v == "1.0" or v is True


def season_rows(year):
    req = urllib.request.Request(URL.format(year=year),
                                 headers={"User-Agent": "the-sports-page/1.0"})
    with urllib.request.urlopen(req, timeout=420) as resp:
        rdr = csv.DictReader(io.TextIOWrapper(gzip.GzipFile(fileobj=resp),
                                              encoding="utf-8", errors="replace"))
        games, rz_seen, td_seen = {}, set(), set()
        for r in rdr:
            if r.get("season_type") != "REG":
                continue
            gid, off, dfn = r.get("game_id"), r.get("posteam"), r.get("defteam")
            if not gid:
                continue
            home, away = r.get("home_team"), r.get("away_team")
            g = games.setdefault(gid, {"week": r.get("week"), "home": home, "away": away,
                                       "t": {home: dict.fromkeys(FIELDS[5:], 0),
                                             away: dict.fromkeys(FIELDS[5:], 0)}})
            # penalties belong to whoever committed them, offence or defence
            pt = r.get("penalty_team")
            if one(r.get("penalty")) and pt in g["t"]:
                g["t"][pt]["penalties"] += 1
                try:
                    g["t"][pt]["penalty_yards"] += int(float(r.get("penalty_yards") or 0))
                except ValueError:
                    pass
            if off not in g["t"]:
                continue
            o = g["t"][off]
            down = r.get("down")
            if down == "3":
                if one(r.get("third_down_converted")):
                    o["third_att"] += 1; o["third_conv"] += 1
                elif one(r.get("third_down_failed")):
                    o["third_att"] += 1
            if down == "4":
                if one(r.get("fourth_down_converted")):
                    o["fourth_att"] += 1; o["fourth_conv"] += 1
                elif one(r.get("fourth_down_failed")):
                    o["fourth_att"] += 1
            if one(r.get("first_down")):
                o["first_downs"] += 1
            if one(r.get("sack")):
                o["sacks_taken"] += 1
                if dfn in g["t"]:
                    g["t"][dfn]["sacks_made"] += 1
            if one(r.get("pass_attempt")) and not one(r.get("sack")):
                o["pass_att"] += 1
                if one(r.get("complete_pass")):
                    o["completions"] += 1
            try:
                yds = float(r.get("yards_gained") or 0)
            except ValueError:
                yds = 0.0
            scrimmage = r.get("play_type") in ("run", "pass", "qb_kneel", "qb_spike")
            if scrimmage:
                if yds >= 20:
                    o["explosive"] += 1
                if one(r.get("rush_attempt")):
                    o["rush_yards"] += int(yds)
                elif one(r.get("pass_attempt")):
                    o["pass_yards"] += int(yds)
            # red zone, counted once per drive
            try:
                y100 = float(r.get("yardline_100") or 999)
            except ValueError:
                y100 = 999
            dkey = (gid, r.get("fixed_drive"), off)
            if y100 <= 20 and dkey not in rz_seen:
                rz_seen.add(dkey); o["rz_trips"] += 1
            if y100 <= 20 and dkey in rz_seen and dkey not in td_seen:
                if (r.get("drive_end_transition") or "").upper().startswith("TOUCHDOWN") \
                   or one(r.get("touchdown")):
                    td_seen.add(dkey); o["rz_td"] += 1

    for gid, g in games.items():
        for team, opp in ((g["home"], g["away"]), (g["away"], g["home"])):
            row = dict(season=year, week=g["week"], game_id=gid, team=team, opp=opp)
            row.update(g["t"][team])
            yield row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", type=int, default=2016)
    ap.add_argument("--to", dest="end", type=int, default=2025)
    a = ap.parse_args()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    have, rows = set(), []
    if OUT.exists():
        with open(OUT) as fh:
            for r in csv.DictReader(fh):
                rows.append(r); have.add(int(r["season"]))

    for y in range(a.start, a.end + 1):
        if y in have:
            print(f"  {y}  already present, skipping"); continue
        try:
            got = list(season_rows(y))
        except Exception as e:
            print(f"  {y}  FAILED: {type(e).__name__} {e}"); continue
        rows.extend(got)
        n = max(len(got), 1)
        t3 = sum(int(r["third_att"]) for r in got) / n
        fd = sum(int(r["first_downs"]) for r in got) / n
        print(f"  {y}  {len(got):>4} team-games   mean {t3:.1f} third downs, {fd:.1f} first downs")
        if not 8 <= t3 <= 20 or not 12 <= fd <= 30:
            print("        WARNING: those averages are not plausible; check the parsing")

    rows.sort(key=lambda r: (int(r["season"]), int(r["week"]), r["game_id"], r["team"]))
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    print(f"\n  wrote {len(rows)} team-games -> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
