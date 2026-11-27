#!/usr/bin/env python3
"""Brier-score every college forecast we froze before kickoff (TASKS.md C4b).

The Sunday scorecard grades HIT / MISS, which cannot tell a 79-in-100 call that
lost (a little wrong) from a 99-in-100 call that lost (very wrong). The Brier
score can: the squared gap between the stated chance and what happened (1 or 0),
averaged over every call. LOWER IS BETTER. Always saying 50 in 100 scores .250.

Three forecasters, scored on the same games:
  ours   - SP+ ratings frozen before the week (data/rating-snapshots/), the
           numbers every Sunday Edition's upset arithmetic was built on
  crowd  - the point spread frozen beside them, read as a prior (no-gambling
           rule: a spread is the crowd's judgment, translated into a chance)
  coin   - 50 in 100 for everybody

Only calls that carried a probability AT THE TIME are scored. Weeks without a
frozen snapshot are reported as "not scorable", never back-filled. The crowd
comparison uses only games that had a frozen line, and so does "ours" on that
row, so the two are always scored on identical games.

Results come from CollegeFootballData (one call per week, cached in
data/brier/cfb-results-2026.json so a rerun costs nothing).

  python3 scripts/brier_scorecard.py              # season table
  python3 scripts/brier_scorecard.py --week 13    # one week + season line
  python3 scripts/brier_scorecard.py --refresh    # re-pull unfinished weeks
  python3 scripts/brier_scorecard.py --json       # machine-readable
"""
import argparse
import json
import math
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from sunday_football import cfbd, prob, HFA, SD_CFB, SNAPS, YEAR  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
CACHE = REPO / "data" / "brier" / f"cfb-results-{YEAR}.json"


def results(week, cache, refresh):
    k = str(week)
    if k in cache and not (refresh and not cache[k]["complete"]):
        return cache[k]["games"]
    games, complete = [], True
    for g in cfbd(f"/games?year={YEAR}&seasonType=regular&week={week}"):
        if g.get("homePoints") is None:
            complete = False
            continue
        games.append(dict(home=g["homeTeam"], away=g["awayTeam"],
                          neutral=bool(g.get("neutralSite")),
                          hp=g["homePoints"], ap=g["awayPoints"]))
    cache[k] = dict(complete=complete, games=games)
    return games


def score_week(week, cache, refresh):
    snap = json.loads((SNAPS / f"{YEAR}-w{week:02d}.json").read_text())
    sp, lines = snap["sp"], snap.get("lines", {})
    rows = []
    for g in results(week, cache, refresh):
        h, a = g["home"], g["away"]
        if h not in sp or a not in sp or g["hp"] == g["ap"]:
            continue                      # unrated team: no forecast, none invented
        y = 1.0 if g["hp"] > g["ap"] else 0.0
        p_ours = prob(sp[h] - sp[a] + (0 if g["neutral"] else HFA), SD_CFB)
        line = lines.get(f"{a} @ {h}")    # home spread: negative = home favored
        p_crowd = None if line is None else prob(-line, SD_CFB)
        rows.append(dict(week=week, game=f"{a} @ {h}", y=y,
                         ours=p_ours, crowd=p_crowd))
    return rows


def brier(rows, key):
    return sum((r[key] - r["y"]) ** 2 for r in rows) / len(rows)


def gap_interval(rows, a, b, n=4000, seed=7):
    """95% bootstrap interval for Brier(a) - Brier(b), resampling games."""
    rng = random.Random(seed)
    d = [(r[a] - r["y"]) ** 2 - (r[b] - r["y"]) ** 2 for r in rows]
    means = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(n))
    return means[int(.025 * n)], means[int(.975 * n)]


def summarize(rows):
    both = [r for r in rows if r["crowd"] is not None]
    out = dict(games=len(rows), ours=brier(rows, "ours"), coin=0.25,
               lined=len(both))
    if both:
        out.update(ours_lined=brier(both, "ours"), crowd_lined=brier(both, "crowd"),
                   gap=gap_interval(both, "ours", "crowd"))
    return out


def cut(b):
    """Share of a coin flip's error removed, as "N in 100" -- what a reader can hold."""
    return round(100 * (0.25 - b) / 0.25)


def verdict(s):
    """One plain line for the Sunday Edition. Lower is better, said every time.
    Two digits only (house rule on significant digits)."""
    line = (f"Across {s['games']} college games, our frozen forecasts scored "
            f"{s['ours']:.2f}; always saying 50 in 100 scores .25. Lower is better. "
            f"That removes about {cut(s['ours'])} in 100 of a coin flip's error.")
    if s.get("lined"):
        lo, hi = s["gap"]
        if hi < 0:
            cmp = "we beat the crowd"
        elif lo > 0:
            cmp = "the crowd beat us"
        else:
            cmp = "too close to call"
        line += (f" The crowd's point spread, on the same {s['lined']} games, scored "
                 f"{s['crowd_lined']:.2f} (about {cut(s['crowd_lined'])} in 100): {cmp}.")
    return line


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    weeks = sorted(int(p.stem.split("-w")[1]) for p in SNAPS.glob(f"{YEAR}-w*.json"))
    if args.week:
        weeks = [w for w in weeks if w <= args.week]
    allrows, per = [], {}
    for w in weeks:
        rows = score_week(w, cache, args.refresh)
        if rows:
            per[w] = summarize(rows)
            allrows += rows
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1))

    season = summarize(allrows)
    missing = [w for w in range(1, max(weeks) + 1) if w not in per]
    if args.json:
        print(json.dumps(dict(weeks=per, season=season, not_scorable=missing), indent=1))
        return
    print(f"{'week':>4} {'games':>5} {'ours':>6} {'coin':>5} | {'lined':>5} {'ours':>6} {'crowd':>6}")
    for w, s in per.items():
        print(f"{w:>4} {s['games']:>5} {s['ours']:.3f} {.25:.3f} | {s['lined']:>5} "
              f"{s.get('ours_lined', float('nan')):.3f} {s.get('crowd_lined', float('nan')):.3f}")
    print(f"{'all':>4} {season['games']:>5} {season['ours']:.3f} {.25:.3f} | {season['lined']:>5} "
          f"{season['ours_lined']:.3f} {season['crowd_lined']:.3f}")
    lo, hi = season["gap"]
    print(f"\nours minus crowd, 95% interval (games resampled): {lo:+.3f} to {hi:+.3f}")
    print(f"not scorable (no frozen snapshot): weeks {', '.join(map(str, missing))}")
    if args.week and args.week in per:
        print(f"\nweek {args.week}: {verdict(per[args.week])}")
    print(f"\nseason: {verdict(season)}")


if __name__ == "__main__":
    main()
