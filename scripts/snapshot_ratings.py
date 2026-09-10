#!/usr/bin/env python3
"""Freeze this week's ratings before the games are played.

    python3 scripts/snapshot_ratings.py           # snapshot today
    python3 scripts/snapshot_ratings.py --list    # what we have frozen

WHY THIS EXISTS. On 2026-09-11 we backtested our own pick method on week one and
it returned 15 of 15 against the spread, 120 points from 120. That is not a good
result; it is a symptom. The correlation between our computed edge and the actual
result against the spread was r = +0.842 across 51 games. An honest pregame model
that genuinely beats a closing line sits near r = +0.10 to +0.20, because
sportsbooks are efficient and the edge is thin by construction.

THE CAUSE. CollegeFootballData's /ratings/sp endpoint returns CURRENT ratings,
not the preseason ones. It overwrites as the season goes. We had confirmed the
drift ourselves two days earlier -- Ohio State moved 32.7 to 30.0 -- and then
backtested with the updated numbers anyway. The ratings had already watched the
games they were being asked to predict.

There is no historical endpoint. Once a week passes, the rating that existed
before it is gone. So the only fix is to write it down at the time, which is what
this does: every rating, stamped with the date and the upcoming week, before
kickoff. Run it Thursday.

By November this directory answers the question honestly. Until then, any
backward-looking claim about how our method "would have done" is unsupported and
should be labelled as such.
"""
import argparse
import datetime
import json
import os
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(REPO, "data", "rating-snapshots")
API = "https://api.collegefootballdata.com"


def get(path):
    key = os.environ["CFBD_KEY"]
    return json.load(urllib.request.urlopen(
        urllib.request.Request(f"{API}{path}", headers={"Authorization": f"Bearer {key}"}),
        timeout=90))


def next_week(year):
    """The first week that is genuinely still to come.

    Not simply the lowest week containing an unplayed game: a couple of tiny
    non-FBS fixtures never receive a score and sit "pending" forever, which made
    the first run of this script label a week-2 snapshot as week 1. A week counts
    as upcoming only when MOST of it is unplayed.
    """
    games = get(f"/games?year={year}&seasonType=regular")
    tally = {}
    for g in games:
        played, pend = tally.get(g["week"], (0, 0))
        if g.get("homePoints") is None:
            tally[g["week"]] = (played, pend + 1)
        else:
            tally[g["week"]] = (played + 1, pend)
    for wk in sorted(tally):
        played, pend = tally[wk]
        if pend > played:
            return wk
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=datetime.date.today().year)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    os.makedirs(DIR, exist_ok=True)

    if a.list:
        files = sorted(f for f in os.listdir(DIR) if f.endswith(".json"))
        if not files:
            print("  nothing frozen yet. Run this before Saturday.")
            return
        print(f"  {len(files)} snapshot(s):\n")
        for f in files:
            d = json.load(open(os.path.join(DIR, f)))
            print(f"    {f:<28}taken {d['taken']}  predicts week {d['predicts_week']}  "
                  f"{len(d['sp'])} clubs")
        print("\n  A backtest may only use a snapshot whose predicts_week is the week")
        print("  being scored. Anything else is reading the answer first.")
        return

    wk = next_week(a.year)
    if wk is None:
        raise SystemExit("no unplayed weeks left this season")
    sp = {r["team"]: r["rating"] for r in get(f"/ratings/sp?year={a.year}")}
    try:
        ret = {r["team"]: r.get("percentPPA") for r in get(f"/player/returning?year={a.year}")}
    except Exception:
        ret = {}
    lines = {}
    try:
        for l in get(f"/lines?year={a.year}&week={wk}"):
            s = [float(x["spread"]) for x in (l.get("lines") or []) if x.get("spread") is not None]
            if s:
                lines[f"{l['awayTeam']} @ {l['homeTeam']}"] = round(sum(s) / len(s), 2)
    except Exception:
        pass

    doc = dict(taken=datetime.date.today().isoformat(), season=a.year, predicts_week=wk,
               source="CollegeFootballData /ratings/sp, frozen before kickoff",
               sp=sp, returning=ret, lines=lines)
    path = os.path.join(DIR, f"{a.year}-w{wk:02d}.json")
    if os.path.exists(path):
        print(f"  {os.path.basename(path)} already exists -- NOT overwriting.")
        print("  A snapshot is only worth anything if it is the one taken before the games.")
        return
    json.dump(doc, open(path, "w"), indent=1)
    print(f"  froze {len(sp)} ratings and {len(lines)} lines for week {wk}")
    print(f"  wrote {path}")


if __name__ == "__main__":
    main()
