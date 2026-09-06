#!/usr/bin/env python3
"""What week N actually did, against what the preseason number said it would.

    python3 scripts/cfb_week_review.py              # latest completed week
    python3 scripts/cfb_week_review.py --week 3
    python3 scripts/cfb_week_review.py --json data/cfb-week.json

RUN THIS EVERY MONDAY IN SEASON. It is the standing brief for the weekly college
football piece, and it exists so the piece is built on measured surprise rather
than on whatever game happened to be on television.

WHAT "UNEXPECTED" MEANS HERE, precisely. Every game gets an expected margin from
the preseason SP+ ratings plus home field. The surprise is the actual margin
minus that. A club winning by 40 when it was meant to win by 38 is not news; a
club losing by 16 when it was meant to win by 38 is the whole story.

TWO SEPARATE QUESTIONS, and confusing them is the usual error:

  - WHICH GAME was most surprising -> the largest gap on a single result.
  - WHETHER THE WEEK was surprising -> the MEAN absolute gap across every rated
    game. That is a property of the week, not of any club, and it is the number
    that answers "is this year different". A week can contain a shocking upset
    and still be an ordinary week.

Both are reported, and the second is compared against the same week in prior
seasons so "crazy things are happening" becomes a figure rather than a feeling.

The market is pulled where available as an INDEPENDENT check on SP+. When a
result contradicts both a rating system and three bookmakers, it is not a
modelling artefact.
"""
import argparse
import json
import math
import os
import statistics
import urllib.request

API = "https://api.collegefootballdata.com"
SD, HFA = 16.5, 2.5          # points; matches build_cfb_odds.py so the two agree


def get(url):
    key = os.environ["CFBD_KEY"]          # by name only, never expanded
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def rated_games(year, week):
    sp = {r["team"]: r["rating"] for r in get(f"{API}/ratings/sp?year={year}")}
    games = [g for g in get(f"{API}/games?year={year}&seasonType=regular&week={week}")
             if g.get("homePoints") is not None]
    out = []
    for g in games:
        h, a = g["homeTeam"], g["awayTeam"]
        if h not in sp or a not in sp:
            continue                       # one side unrated: no expectation to beat
        exp = sp[h] - sp[a] + (0 if g.get("neutralSite") else HFA)
        act = g["homePoints"] - g["awayPoints"]
        out.append(dict(home=h, away=a, hp=g["homePoints"], ap=g["awayPoints"],
                        exp=round(exp, 1), act=act, surprise=round(act - exp, 1),
                        p_home=round(0.5 * (1 + math.erf(exp / (SD * math.sqrt(2)))), 4),
                        upset=(act > 0) != (exp > 0),
                        total=g["homePoints"] + g["awayPoints"]))
    return out, len(games)


def week_stats(rows):
    err = [abs(r["surprise"]) for r in rows]
    return dict(n=len(rows),
                upsets=sum(1 for r in rows if r["upset"]),
                mean_miss=round(statistics.mean(err), 1),
                median_miss=round(statistics.median(err), 1),
                mean_total=round(statistics.mean(r["total"] for r in rows), 1))


def lines_for(year, week, team):
    try:
        out = []
        for l in get(f"{API}/lines?year={year}&week={week}&team={team}"):
            for ln in l.get("lines", []):
                if ln.get("spread") is not None:
                    out.append((ln.get("provider"), float(ln["spread"])))
        return out
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--week", type=int)
    ap.add_argument("--back", type=int, default=2, help="prior seasons to compare")
    ap.add_argument("--json")
    a = ap.parse_args()

    week = a.week
    if week is None:
        done = [g["week"] for g in get(f"{API}/games?year={a.year}&seasonType=regular")
                if g.get("homePoints") is not None]
        if not done:
            raise SystemExit("no completed games yet this season")
        week = max(done)

    rows, total_games = rated_games(a.year, week)
    if not rows:
        raise SystemExit(f"week {week} has no games with both clubs rated")
    st = week_stats(rows)

    print(f"\n  COLLEGE FOOTBALL, WEEK {week} OF {a.year}")
    print(f"  {total_games} games played, {st['n']} with both clubs rated\n")

    print("  MOST UNEXPECTED RESULTS  (actual margin minus the preseason number)\n")
    print(f"  {'matchup':<42}{'score':>10}{'expected':>10}{'actual':>8}{'miss':>8}")
    for r in sorted(rows, key=lambda r: -abs(r["surprise"]))[:10]:
        mu = f"{r['away'][:18]} at {r['home'][:18]}"
        print(f"  {mu:<42}{str(r['ap'])+'-'+str(r['hp']):>10}"
              f"{r['exp']:>+10.1f}{r['act']:>+8d}{r['surprise']:>+8.1f}")

    ups = [r for r in rows if r["upset"]]
    print(f"\n  OUTRIGHT UPSETS: {len(ups)} of {st['n']} ({len(ups)/st['n']*100:.0f}%)\n")
    for r in sorted(ups, key=lambda r: abs(r["p_home"] - .5), reverse=True)[:6]:
        won, lost = (r["home"], r["away"]) if r["act"] > 0 else (r["away"], r["home"])
        pw = r["p_home"] if r["act"] > 0 else 1 - r["p_home"]
        print(f"    {won[:22]:<24}beat {lost[:22]:<24}{pw*100:>5.1f}% chance")

    # the market, as a second opinion on the single biggest shock
    top = max(rows, key=lambda r: abs(r["surprise"]))
    ls = lines_for(a.year, week, top["home"])
    if ls:
        sp_ = statistics.mean(s for _, s in ls)
        print(f"\n  THE MARKET AGREED IT WAS ABSURD. {top['away']} at {top['home']}:")
        print(f"    books had {top['home']} by {abs(sp_):.1f} ({len(ls)} quotes); SP+ had "
              f"{abs(top['exp']):.1f}; the result was {top['act']:+d}.")

    print(f"\n  WAS THE WEEK ITSELF UNUSUAL? Mean absolute miss is a property of the")
    print(f"  week, not of any one club.\n")
    print(f"  {'season':<10}{'rated':>7}{'upsets':>9}{'mean miss':>12}{'median':>9}{'points/gm':>11}")
    hist = []
    for y in range(a.year - a.back, a.year + 1):
        try:
            rr, _ = rated_games(y, week)
            s = week_stats(rr)
        except Exception:
            continue
        hist.append((y, s))
        mark = "  <-- this week" if y == a.year else ""
        print(f"  {y:<10}{s['n']:>7}{s['upsets']:>4} ({s['upsets']/s['n']*100:>3.0f}%)"
              f"{s['mean_miss']:>12.1f}{s['median_miss']:>9.1f}{s['mean_total']:>11.1f}{mark}")
    if len(hist) > 1:
        prior = statistics.mean(s["mean_miss"] for y, s in hist[:-1])
        d = (st["mean_miss"] - prior) / prior * 100
        verdict = ("HARDER to predict than usual" if d > 10 else
                   "EASIER to predict than usual" if d < -10 else "about normal")
        print(f"\n  This week missed by {st['mean_miss']:.1f} points on average against "
              f"{prior:.1f} in prior years -- {d:+.0f}%. {verdict}.")

    if a.json:
        json.dump(dict(year=a.year, week=week, stats=st, games=rows,
                       history=[dict(year=y, **s) for y, s in hist]),
                  open(a.json, "w"), indent=1)
        print(f"\n  wrote {a.json}")


if __name__ == "__main__":
    main()
