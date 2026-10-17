#!/usr/bin/env python3
"""How hard did a schedule look -- before, during and after the season?

    python3 scripts/schedule_belief.py --champions          # CFP-era champions, pre vs post
    python3 scripts/schedule_belief.py --team "Notre Dame" --year 2026 [--weekly]
    python3 scripts/schedule_belief.py --all-years 2014-2025 # every team: pre vs post
    python3 scripts/schedule_belief.py --json OUT.json       # write everything for figures

The editor, 2026-10-17, after Kirk Herbstreit called Notre Dame's schedule "an
embarrassment": compare championship schedules "after the fact, not ahead of the
fact... How tough does the season look at the beginning of the season and after
the season? ... And then during a season." A schedule's strength is a BELIEF about
the opponents, and beliefs update. This measures how much.

THE MEASURE. The AP Top 25 (via CollegeFootballData), read three ways. Elo was
the first choice and was dropped: CFBD returns Elo AFTER week w, so "week 1"
already contains week-one results and there is no true preseason Elo. The poll
is also the belief people actually argue from:
  * preseason  = the AP preseason poll (CFBD regular-season week 1)
  * in-season  = the AP poll released before week w
  * final      = the final AP poll, after the bowls and playoff
An opponent counts as a REAL TEST when it is in the AP Top 25 at that moment. We
count tests rather than averaging ratings, because a count is what the argument
is about ("two real tests") and a reader can check it. Regular season only
(conference title games included); bowls and playoff games are not "schedule".

Limits, also in the piece:
  * The final poll includes each opponent's game AGAINST the team being measured,
    so a champion that beats everyone drags its opponents' final ranks down a
    little. That biases the "after" count low for exactly the dominant teams.
  * A poll is a vote, not a model. It is the public's belief, which is the point
    here, but it overweights record and brand. Top-25 is a hard edge: No. 26 is
    not a test and No. 25 is.
"""
import argparse
import json
import os
import sys
import urllib.request
from functools import lru_cache

API = "https://api.collegefootballdata.com"
TOP = 25

# CFP-era national champions, verified against CFBD title-game results by
# champions() below rather than trusted from memory.
TITLE_YEARS = range(2014, 2026)


def get(path):
    key = os.environ.get("CFBD_KEY")
    if not key:
        sys.exit("CFBD_KEY is not set (source ~/.config/secrets/tokens.env)")
    req = urllib.request.Request(API + path, headers={"Authorization": "Bearer " + key})
    return json.load(urllib.request.urlopen(req, timeout=60))


@lru_cache(maxsize=None)
def _polls(year):
    return get(f"/rankings?year={year}")


def ap(year, week=None):
    """{team: (points, rank)} from the AP Top 25. week=1 is the PRESEASON poll;
    week=None is the FINAL poll (postseason). Same shape as elo() on purpose."""
    for w in _polls(year):
        hit = (w["seasonType"] == "postseason") if week is None else \
              (w["seasonType"] == "regular" and w["week"] == week)
        if not hit:
            continue
        for p in w["polls"]:
            if p["poll"] == "AP Top 25":
                return {r["school"]: (r["points"], r["rank"]) for r in p["ranks"]}
    return {}


@lru_cache(maxsize=None)
def elo(year, week=None):
    """{team: (elo, rank)} -- rank 1 = best among FBS teams that have a rating."""
    rows = get(f"/ratings/elo?year={year}" + (f"&week={week}" if week else ""))
    rows = [r for r in rows if r.get("elo") is not None]
    rows.sort(key=lambda r: -r["elo"])
    return {r["team"]: (r["elo"], i + 1) for i, r in enumerate(rows)}


@lru_cache(maxsize=None)
def games(year):
    rows = get(f"/games?year={year}&seasonType=regular") + get(f"/games?year={year}&seasonType=postseason")
    return [g for g in rows if g.get("homePoints") is not None or year >= 2026]


def schedule(team, year, regular_only=False):
    out = []
    for g in games(year):
        if regular_only and g.get("seasonType") != "regular":
            continue
        if team not in (g["homeTeam"], g["awayTeam"]):
            continue
        opp = g["awayTeam"] if g["homeTeam"] == team else g["homeTeam"]
        out.append({"opp": opp, "week": g["week"], "season_type": g.get("seasonType"),
                    "played": g.get("homePoints") is not None})
    return out


def tests(team, year, ratings, regular_only=False):
    """Count opponents ranked top-25 in `ratings`. Returns (tests, fbs_opps, fcs_opps, names)."""
    sched = schedule(team, year, regular_only)
    ranked = [s for s in sched if s["opp"] in ratings and ratings[s["opp"]][1] <= TOP]
    names = sorted({s["opp"] for s in ranked})
    return len(ranked), len(sched), 0, names


def champions():
    out = {}
    for y in TITLE_YEARS:
        post = [g for g in games(y) if g.get("seasonType") == "postseason" and g.get("notes")
                and "national championship" in g["notes"].lower()]
        if len(post) != 1:
            print(f"  {y}: could not identify a single title game ({len(post)} found)", file=sys.stderr)
            continue
        g = post[0]
        out[y] = g["homeTeam"] if g["homePoints"] > g["awayPoints"] else g["awayTeam"]
    return out


def pre_post(team, year, regular_only=True):
    pre, post = ap(year, 1), ap(year)
    a = tests(team, year, pre, regular_only)
    b = tests(team, year, post, regular_only)
    return {"team": team, "year": year, "pre_tests": a[0], "post_tests": b[0], "fbs": a[1],
            "fcs": a[2], "pre_names": a[3], "post_names": b[3]}


def weekly(team, year, last_week):
    rows = []
    for w in range(1, last_week + 1):
        r = ap(year, w)
        if not r:
            continue
        n, fbs, fcs, names = tests(team, year, r, regular_only=True)
        rows.append({"week": w, "tests": n, "names": names})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--champions", action="store_true")
    parser.add_argument("--team")
    parser.add_argument("--year", type=int)
    parser.add_argument("--weekly", type=int, metavar="LAST_WEEK")
    parser.add_argument("--all-years")
    parser.add_argument("--json")
    a = parser.parse_args()
    dump = {}

    if a.champions:
        rows = []
        for y, t in champions().items():
            r = pre_post(t, y)
            rows.append(r)
            print(f"{y} {t:14} tests before {r['pre_tests']:>2}  after {r['post_tests']:>2}   "
                  f"({r['fbs']} regular-season games)")
            print(f"      before: {', '.join(r['pre_names'])}")
            print(f"      after:  {', '.join(r['post_names'])}")
        dump["champions"] = rows

    if a.team and a.year:
        if a.weekly:
            rows = weekly(a.team, a.year, a.weekly)
            for r in rows:
                print(f"  week {r['week']:>2}: {r['tests']} tests  {', '.join(r['names'])}")
            dump.setdefault("weekly", {})[a.team] = rows
        else:
            r = pre_post(a.team, a.year)
            print(r)

    if a.all_years:
        y0, y1 = map(int, a.all_years.split("-"))
        rows = []
        for y in range(y0, y1 + 1):
            pre, post = ap(y, 1), ap(y)
            pre_top = {t for t, (_, k) in pre.items() if k <= TOP}
            post_top = {t for t, (_, k) in post.items() if k <= TOP}
            kept = len(pre_top & post_top)
            rows.append({"year": y, "kept": kept})
            print(f"{y}: {kept} of {TOP} preseason top-25 teams finished top-25")
        dump["persistence"] = rows

    if a.json:
        with open(a.json, "w") as f:
            json.dump(dump, f, indent=1)


if __name__ == "__main__":
    main()
