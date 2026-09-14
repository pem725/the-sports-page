#!/usr/bin/env python3
"""Aggregate nflverse play-by-play into one row per team per game.

    python3 scripts/build_nfl_history.py                 # 2016-2025
    python3 scripts/build_nfl_history.py --from 2020
    python3 scripts/build_nfl_history.py --season 2026   # in-season refresh

WHY THIS EXISTS. Every Sunday broadcast puts time of possession on the screen as
though it were evidence. On 2026-09-13 Buffalo won at Houston while holding the
ball for 23:43 against 36:17, and two people watching the same game came away with
opposite readings of how good the Bills are. Settling that needs a season of data
and not an opinion, and nothing in this repo had NFL history in it.

WHAT IT KEEPS, per team per game:
    plays, yards      scrimmage only -- the yards-per-play denominator has to
                      exclude kicks or a good punt team looks like an offence
    top_seconds       summed over that team's drives, parsed from drive-level
                      "M:SS" strings and deduplicated by drive id
    turnovers         interceptions plus lost fumbles
    points_for/against, win

STREAMED, NOT LOADED. The season files are ~19MB compressed and roughly 300MB
open, and this repo has no pandas -- deliberately, since CI installs from
requirements.txt and a dependency added for one analysis is a dependency forever.
The stdlib csv module over a GzipFile handles it in one pass.

ONE THING TO BE CAREFUL OF. A drive's time of possession appears on EVERY row of
that drive, so summing the column directly inflates the total by the number of
plays. Deduplicate on (game_id, fixed_drive) first. The bug is silent: it yields
plausible-looking totals that are simply eight times too large.
"""
import argparse
import csv
import gzip
import io
import os
import pathlib
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "nfl" / "team-games.csv"
URL = ("https://github.com/nflverse/nflverse-data/releases/download/pbp/"
       "play_by_play_{year}.csv.gz")
FIELDS = ["season", "week", "game_id", "team", "opp", "home",
          "plays", "yards", "top_seconds", "turnovers",
          "points_for", "points_against", "win"]


def mmss(s):
    """'5:23' -> 323 seconds. Blank or malformed -> None."""
    if not s or ":" not in s:
        return None
    try:
        m, sec = s.split(":")
        return int(m) * 60 + int(sec)
    except ValueError:
        return None


def season_rows(year):
    """One pass over a season, yielding aggregated team-game dicts."""
    req = urllib.request.Request(URL.format(year=year),
                                 headers={"User-Agent": "the-sports-page/1.0"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        gz = gzip.GzipFile(fileobj=resp)
        rdr = csv.DictReader(io.TextIOWrapper(gz, encoding="utf-8", errors="replace"))

        games, drives = {}, set()
        for r in rdr:
            if r.get("season_type") != "REG":
                continue
            gid, off = r.get("game_id"), r.get("posteam")
            if not gid:
                continue
            home, away = r.get("home_team"), r.get("away_team")
            g = games.setdefault(gid, {
                "week": r.get("week"), "home": home, "away": away,
                "hs": r.get("home_score"), "as": r.get("away_score"),
                "t": {home: dict(plays=0, yards=0.0, top=0, to=0),
                      away: dict(plays=0, yards=0.0, top=0, to=0)}})
            if off not in g["t"]:
                continue

            # scrimmage plays only -- a punt is not an offensive snap
            is_scrimmage = (r.get("rush_attempt") == "1" or r.get("pass_attempt") == "1"
                            or r.get("sack") == "1")
            if is_scrimmage and r.get("play_type") in ("run", "pass", "qb_kneel", "qb_spike"):
                g["t"][off]["plays"] += 1
                try:
                    g["t"][off]["yards"] += float(r.get("yards_gained") or 0)
                except ValueError:
                    pass
            if r.get("interception") == "1":
                g["t"][off]["to"] += 1
            if r.get("fumble_lost") == "1":
                g["t"][off]["to"] += 1

            # drive TOP repeats on every row of the drive; count each drive once
            dkey = (gid, r.get("fixed_drive"), off)
            if r.get("fixed_drive") and dkey not in drives:
                secs = mmss(r.get("drive_time_of_possession"))
                if secs is not None:
                    drives.add(dkey)
                    g["t"][off]["top"] += secs

    for gid, g in games.items():
        try:
            hs, as_ = int(float(g["hs"])), int(float(g["as"]))
        except (TypeError, ValueError):
            continue
        for team, opp, pf, pa in ((g["home"], g["away"], hs, as_),
                                  (g["away"], g["home"], as_, hs)):
            d = g["t"][team]
            yield dict(season=year, week=g["week"], game_id=gid, team=team, opp=opp,
                       home=int(team == g["home"]), plays=d["plays"],
                       yards=round(d["yards"], 1), top_seconds=d["top"],
                       turnovers=d["to"], points_for=pf, points_against=pa,
                       win=int(pf > pa))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", type=int, default=2016)
    ap.add_argument("--to", dest="end", type=int, default=2025)
    ap.add_argument("--season", type=int, help="just this one, appended")
    a = ap.parse_args()
    years = [a.season] if a.season else list(range(a.start, a.end + 1))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    have = set()
    existing = []
    if OUT.exists():
        with open(OUT) as fh:
            for r in csv.DictReader(fh):
                existing.append(r)
                have.add(int(r["season"]))

    rows = list(existing)
    for y in years:
        if y in have:
            print(f"  {y}  already present, skipping")
            continue
        try:
            got = list(season_rows(y))
        except Exception as e:
            print(f"  {y}  FAILED: {type(e).__name__} {e}")
            continue
        rows.extend(got)
        tp = sum(r["plays"] for r in got) / max(len(got), 1)
        tt = sum(r["top_seconds"] for r in got) / max(len(got), 1)
        print(f"  {y}  {len(got):>4} team-games   mean {tp:.1f} plays, "
              f"{tt/60:.1f} min possession")
        if not 20 <= tt / 60 <= 40:
            print(f"        WARNING: mean possession {tt/60:.1f} min is not plausible; "
                  "check the drive deduplication")

    rows.sort(key=lambda r: (int(r["season"]), int(r["week"]), r["game_id"], r["team"]))
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"\n  wrote {len(rows)} team-games -> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
