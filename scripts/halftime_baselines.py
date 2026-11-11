#!/usr/bin/env python3
"""Backtest the halftime checks a game card prints, on this season's games.

    python3 scripts/halftime_baselines.py            # writes data/halftime-baselines.json
    python3 scripts/halftime_baselines.py --print    # report only

WHY. Rule 3 of the Bills-Vikings post-mortem: no checkpoint goes on a card
without its hit rate, measured on this season. game.html reads this file and
prints the numbers beside the live halftime check, so a viewer sees how often
"the team ahead at the half" actually wins, and how much yards per play adds.

SOURCES.
  NFL      nflverse play-by-play: halftime score and first-half yards per play.
  College  ESPN's scoreboard line scores, one request per Saturday: halftime
           score only. There is no free college play-by-play we trust for yards
           per play, so the card prints no yards-per-play rate for college,
           rather than borrowing the NFL's.
  NHL      ESPN's scoreboard line scores, one request per day: the score after
           two periods, hockey's checkpoint. Overtime and shootout wins count
           as wins, because that is how the game ends for the viewer.

A "one-score game" is one within 8 points at the half; in hockey, a one-goal
game after two. Ties at the checkpoint are left out of the leader rates and
counted separately. Each league is built on its own: if one feed fails, the
other leagues still update and the failed one keeps yesterday's numbers.
"""
import argparse, csv, datetime as dt, gzip, io, json, os, sys, urllib.request
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "halftime-baselines.json")
PBP = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{y}.csv.gz"
CFB = ("https://site.api.espn.com/apis/site/v2/sports/football/college-football/"
       "scoreboard?groups=80&limit=300&dates={d}")
NHL = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={d}"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "thesportspage.net"})
    return urllib.request.urlopen(req, timeout=60).read()


def rate(wins, n):
    return {"won": wins, "n": n, "pct": round(100 * wins / n) if n else None}


def nfl(season):
    """Per game: halftime score, first-half yards per play, final winner."""
    rows = csv.DictReader(io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(fetch(PBP.format(y=season)))), "utf-8"))
    g = {}
    for r in rows:
        if r["season_type"] != "REG":
            continue
        x = g.setdefault(r["game_id"], {"home": r["home_team"], "away": r["away_team"], "h1": (0, 0), "date": r["game_date"],
                                        "yds": defaultdict(float), "plays": defaultdict(int), "final": None})
        if r["home_score"] and r["away_score"]:
            x["final"] = (int(r["home_score"]), int(r["away_score"]))
        if r["game_half"] == "Half1" and r["total_home_score"]:
            x["h1"] = (int(float(r["total_home_score"])), int(float(r["total_away_score"])))
            if r["play_type"] in ("pass", "run") and r["posteam"] and r["yards_gained"]:
                x["yds"][r["posteam"]] += float(r["yards_gained"])
                x["plays"][r["posteam"]] += 1
    out = []
    for gid, x in g.items():
        if not x["final"] or x["final"][0] == x["final"][1]:
            continue  # unfinished, or a tie: no winner to check against
        ypp = {t: x["yds"][t] / x["plays"][t] for t in (x["home"], x["away"]) if x["plays"][t]}
        if len(ypp) < 2:
            continue
        out.append({"lead": x["h1"][0] - x["h1"][1], "ypp": ypp[x["home"]] - ypp[x["away"]], "date": x["date"],
                    "home_won": x["final"][0] > x["final"][1]})
    return out


def cfb(season):
    """Per game: halftime score and final winner, from ESPN line scores, FBS games only."""
    day = dt.date(season, 8, 22)
    while day.weekday() != 5:
        day += dt.timedelta(days=1)
    out, today = [], dt.date.today()
    while day < today:
        for d in (day - dt.timedelta(days=2), day - dt.timedelta(days=1), day):  # Thu, Fri, Sat
            for ev in json.loads(fetch(CFB.format(d=d.strftime("%Y%m%d")))).get("events", []):
                c = ev["competitions"][0]
                if not c["status"]["type"].get("completed"):
                    continue
                t = {x["homeAway"]: x for x in c["competitors"]}
                try:
                    ls = {k: [float(q["value"]) for q in t[k]["linescores"]] for k in ("home", "away")}
                except (KeyError, TypeError):
                    continue
                if len(ls["home"]) < 2 or len(ls["away"]) < 2:
                    continue
                fh, fa = float(t["home"]["score"]), float(t["away"]["score"])
                if fh == fa:
                    continue
                out.append({"lead": sum(ls["home"][:2]) - sum(ls["away"][:2]), "home_won": fh > fa,
                            "date": d.isoformat()})
        day += dt.timedelta(days=7)
    return out


def nhl(season):
    """Per game: score after two periods, final winner, and whether it went past regulation."""
    day, out, today = dt.date(season, 9, 15), [], dt.date.today()
    while day < today:
        for ev in json.loads(fetch(NHL.format(d=day.strftime("%Y%m%d")))).get("events", []):
            if ev.get("season", {}).get("type") != 2:
                continue  # regular season only
            c = ev["competitions"][0]
            if not c["status"]["type"].get("completed"):
                continue
            t = {x["homeAway"]: x for x in c["competitors"]}
            try:
                ls = {k: [float(q["value"]) for q in t[k]["linescores"]] for k in ("home", "away")}
            except (KeyError, TypeError):
                continue
            if len(ls["home"]) < 3 or len(ls["away"]) < 3:
                continue
            out.append({"lead": sum(ls["home"][:2]) - sum(ls["away"][:2]), "home_won": bool(t["home"].get("winner")),
                        "extra": len(ls["home"]) > 3, "date": day.isoformat()})
        day += dt.timedelta(days=1)
    return out


def summarize_nhl(games):
    led = [g for g in games if g["lead"] != 0]
    tied = [g for g in games if g["lead"] == 0]
    won = lambda g: (g["lead"] > 0) == g["home_won"]
    one = [g for g in led if abs(g["lead"]) == 1]
    more = [g for g in led if abs(g["lead"]) >= 2]
    return {"games": len(games), "through": max(g["date"] for g in games), "tied_at_half": len(tied),
            "leader_wins": rate(sum(map(won, led)), len(led)),
            "leader_wins_one_score": rate(sum(map(won, one)), len(one)),
            "leader_wins_two_plus": rate(sum(map(won, more)), len(more)),
            "tied_goes_to_extra": rate(sum(g["extra"] for g in tied), len(tied))}


def summarize(games, with_ypp):
    led = [g for g in games if g["lead"] != 0]
    close = [g for g in led if abs(g["lead"]) <= 8]
    won = lambda g: (g["lead"] > 0) == g["home_won"]
    s = {"games": len(games), "through": max(g["date"] for g in games), "tied_at_half": len(games) - len(led),
         "leader_wins": rate(sum(map(won, led)), len(led)),
         "leader_wins_one_score": rate(sum(map(won, close)), len(close))}
    if with_ypp:
        agree = [g for g in close if g["ypp"] != 0 and (g["ypp"] > 0) == (g["lead"] > 0)]
        disagree = [g for g in close if g["ypp"] != 0 and (g["ypp"] > 0) != (g["lead"] > 0)]
        s["one_score_ypp_agrees"] = rate(sum(map(won, agree)), len(agree))
        s["one_score_ypp_disagrees"] = rate(sum(map(won, disagree)), len(disagree))
    return s


def main():
    ap = argparse.ArgumentParser()
    # A season is named by the year it starts: January football and hockey belong to last year's season.
    today = dt.date.today()
    ap.add_argument("--season", type=int, default=today.year if today.month >= 8 else today.year - 1)
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args()
    try:
        old = json.load(open(OUT))
    except (OSError, ValueError):
        old = {}
    out = {"season": a.season, "built": today.isoformat(),
           "one_score": "within 8 points at the half; in hockey, one goal after two periods"}
    build = {"nfl": lambda: summarize(nfl(a.season), True), "cfb": lambda: summarize(cfb(a.season), False),
             "nhl": lambda: summarize_nhl(nhl(a.season))}
    failed = []
    for lg, f in build.items():
        try:
            out[lg] = f()
        except Exception as e:  # one dead feed must not cost the other leagues their numbers
            failed.append(lg)
            print(f"{lg}: {e}", file=sys.stderr)
            if lg in old and old.get("season") == a.season:
                out[lg] = old[lg]
    print(json.dumps(out, indent=2))
    if not a.print:
        with open(OUT, "w") as f:
            json.dump(out, f, indent=2)
            f.write("\n")
    return 1 if len(failed) == len(build) else 0


if __name__ == "__main__":
    sys.exit(main())
