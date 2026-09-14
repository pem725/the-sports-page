#!/usr/bin/env python3
"""Which first-half numbers actually predict a team's second half?

    python3 scripts/nfl_predictive.py
    python3 scripts/nfl_predictive.py --split 8 --min-games 6

THE QUESTION. Time of possession is on the screen every Sunday. Yards per play is
not. One of them is supposed to tell you something about the team; nobody who puts
either on the screen says which. So: measure each against the only thing that
matters, which is what the team does NEXT.

THE DESIGN, and it is the whole point. For every team-season we compute each
metric over the first half of the schedule, then ask how well it predicts the WIN
RATE OVER THE SECOND HALF -- games the metric has never seen. That is an
out-of-sample test by construction. Correlating a metric with the same games it
was computed from would return something impressive and mean nothing; this repo
has already published one 15-for-15 backtest that failed exactly that way
(published/154-no-edge.html).

EVERY METRIC IS A MARGIN, not a raw total. A team's own yards per play is partly a
statement about the defences it faced; own minus opponent removes most of that.
The same applies to possession, which is why "held the ball 36 minutes" is really
"held it 12 more than the other team did".

THE HONEST COMPARISON is against the naive predictor. First-half WIN RATE is free,
requires no box score at all, and any fancier metric has to beat it to be worth
printing. Reporting a metric's correlation without that baseline is how a number
gets called predictive when it is merely not useless.
"""
import argparse
import collections
import csv
import math
import pathlib
import statistics
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "nfl" / "team-games.csv"


def corr(pairs):
    if len(pairs) < 10:
        return None
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    if not den:
        return None
    r = num / den
    n = len(pairs)
    t = r * math.sqrt(n - 2) / math.sqrt(1 - r * r) if abs(r) < 1 else float("nan")
    return r, n, t


def load():
    if not DATA.exists():
        raise SystemExit(f"{DATA} missing. Run scripts/build_nfl_history.py first.")
    rows = list(csv.DictReader(open(DATA)))
    by_game = collections.defaultdict(dict)
    for r in rows:
        by_game[r["game_id"]][r["team"]] = r
    out = []
    for gid, sides in by_game.items():
        if len(sides) != 2:
            continue                      # a half-recorded game explains nothing
        (ta, ra), (tb, rb) = list(sides.items())
        for me, you in ((ra, rb), (rb, ra)):
            p_me, p_you = int(me["plays"]), int(you["plays"])
            if p_me == 0 or p_you == 0:
                continue
            out.append(dict(
                season=int(me["season"]), week=int(me["week"]), team=me["team"],
                win=int(me["win"]),
                ypp_margin=float(me["yards"]) / p_me - float(you["yards"]) / p_you,
                top_margin=(int(me["top_seconds"]) - int(you["top_seconds"])) / 60.0,
                to_margin=int(you["turnovers"]) - int(me["turnovers"]),
                pt_margin=int(me["points_for"]) - int(me["points_against"]),
                plays_margin=p_me - p_you))
    return out


METRICS = [
    ("first-half win rate", "win", "the free baseline -- no box score needed"),
    ("point margin", "pt_margin", "the scoreboard, averaged"),
    ("yards per play margin", "ypp_margin", "efficiency, own minus opponent"),
    ("turnover margin", "to_margin", "takeaways minus giveaways"),
    ("time of possession margin", "top_margin", "minutes, own minus opponent"),
    ("plays run margin", "plays_margin", "snaps, own minus opponent"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=int, default=9, help="first half = weeks < this")
    ap.add_argument("--min-games", type=int, default=6)
    a = ap.parse_args()

    rows = load()
    seasons = sorted({r["season"] for r in rows})
    by_ts = collections.defaultdict(list)
    for r in rows:
        by_ts[(r["season"], r["team"])].append(r)

    data = []
    for (season, team), gs in by_ts.items():
        first = [g for g in gs if g["week"] < a.split]
        second = [g for g in gs if g["week"] >= a.split]
        if len(first) < a.min_games or len(second) < a.min_games:
            continue
        rec = {"later_win_rate": statistics.mean(g["win"] for g in second)}
        for _, key, _ in METRICS:
            rec[key] = statistics.mean(g[key] for g in first)
        data.append(rec)

    print(f"\n  {len(rows)} team-games, {seasons[0]}-{seasons[-1]}, "
          f"{len(data)} team-seasons with {a.min_games}+ games either side of week {a.split}\n")
    print("  DOES THE FIRST HALF PREDICT THE SECOND?  (out of sample by construction)\n")
    print(f"  {'metric':<28}{'r':>8}{'r-squared':>11}{'t':>8}   what it is")
    print(f"  {'-'*28}{'-'*8}{'-'*11}{'-'*8}   {'-'*38}")
    results = []
    for label, key, note in METRICS:
        c = corr([(d[key], d["later_win_rate"]) for d in data])
        if not c:
            continue
        r, n, t = c
        results.append((abs(r), label, r, t, note))
        print(f"  {label:<28}{r:>+8.3f}{r*r*100:>10.1f}%{t:>8.2f}   {note}")

    results.sort(reverse=True)
    best = results[0]
    base = next(x for x in results if x[1] == "first-half win rate")
    top = next(x for x in results if x[1].startswith("time of possession"))
    print(f"\n  strongest: {best[1]} (r = {best[2]:+.3f})")
    print(f"  baseline : first-half win rate (r = {base[2]:+.3f})")
    print(f"  possession explains {top[2]**2*100:.1f}% of the second half"
          f"{' -- indistinguishable from nothing' if abs(top[3]) < 2 else ''}")

    # Does possession add anything ONCE you already know the efficiency margin?
    xs = [d["ypp_margin"] for d in data]
    zs = [d["top_margin"] for d in data]
    ys = [d["later_win_rate"] for d in data]
    r_xz = corr(list(zip(xs, zs)))[0]
    r_zy = corr(list(zip(zs, ys)))[0]
    r_xy = corr(list(zip(xs, ys)))[0]
    denom = math.sqrt((1 - r_xz ** 2) * (1 - r_xy ** 2))
    partial = (r_zy - r_xz * r_xy) / denom if denom else float("nan")
    print(f"\n  AND ONCE YOU KNOW THE EFFICIENCY MARGIN, does possession add anything?")
    print(f"    possession vs efficiency, correlated with each other : r = {r_xz:+.3f}")
    print(f"    possession's PARTIAL correlation with the second half: r = {partial:+.3f}")
    print(f"    {'nothing left over' if abs(partial) < 0.1 else 'some independent signal'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
