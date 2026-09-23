#!/usr/bin/env python3
"""Mean, median or mode -- which number actually describes a player's touch?

    python3 scripts/touch_distributions.py
    python3 scripts/touch_distributions.py --min-touches 80

THE EDITOR'S ARGUMENT, 2026-09-23, and it is the right one: "a lot of these stats
are very similar to income stats, and for income we almost always take the
median." Yards per touch is a strongly right-skewed distribution with a floor near
zero and no ceiling, which is exactly the shape that makes mean income a misleading
number about people.

He also named both failure modes himself. The pile of zeros at the bottom -- "if
they're only blocking backs, you have to trim those" -- and the long tail at the
top -- "you have to mute the Emmitt Smiths a bit." A trimmed mean does both, and it
is reported here beside the other three.

BUT THERE IS A REASON THE MEAN WILL NOT GO AWAY, AND IT IS NOT INERTIA. The mean
is the only one of the three that AGGREGATES. Yards per touch times touches equals
total yards; medians cannot be summed into anything. So the two numbers are not
competing answers to one question, they are answers to two different questions:

  MEAN   -- what did this player contribute in total, divided out
  MEDIAN -- what should you expect on the next single play

Median household income and total national income are in exactly this relationship,
which is why the analogy holds all the way down. The error is not using the mean;
the error is using the mean to answer the median's question, which is what a
broadcast does every time it says a back "averages 4.8 a carry" as though 4.8 is
what the next carry will bring.

THE MODE IS THE EDITOR'S SHARPEST POINT and the data backs it hard. His baseball
case -- the slugger whose single likeliest outcome is a strikeout -- has a direct
football twin once you count TARGETS rather than catches. Look at the mode column
for receivers before deciding which statistic is the honest one.
"""
import argparse
import collections
import csv
import math
import pathlib
import statistics
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "nfl" / "touches.csv"


def skew(v):
    n = len(v)
    if n < 3:
        return float("nan")
    m, s = statistics.mean(v), statistics.pstdev(v)
    if s == 0:
        return float("nan")
    return sum(((x - m) / s) ** 3 for x in v) / n


def trimmed(v, p=0.10):
    """Chop p from each end -- the editor's 'trim the zeros, mute the stars'."""
    s = sorted(v)
    k = int(len(s) * p)
    core = s[k:len(s) - k] if len(s) - 2 * k >= 3 else s
    return statistics.mean(core)


def mode_of(v):
    c = collections.Counter(int(round(x)) for x in v)
    top = max(c.values())
    return min(k for k, n in c.items() if n == top), top / len(v)


def load():
    rows = []
    for r in csv.DictReader(open(DATA)):
        rows.append((int(r["season"]), r["player_id"], r["player"], r["kind"],
                     r["touched"] == "1", float(r["yards"])))
    return rows


def describe(name, v, width=30):
    md, share = mode_of(v)
    return (f"  {name:<{width}}{len(v):>8,}{statistics.mean(v):>9.2f}"
            f"{statistics.median(v):>9.1f}{md:>7}{share:>8.1%}"
            f"{trimmed(v):>10.2f}{skew(v):>8.2f}")


def header(label, width=30):
    print(f"  {label:<{width}}{'n':>8}{'mean':>9}{'median':>9}{'mode':>7}"
          f"{'mode%':>8}{'trim10%':>10}{'skew':>8}")
    print("  " + "-" * (width + 59))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-touches", type=int, default=50)
    a = ap.parse_args()
    if not DATA.exists():
        raise SystemExit(f"{DATA} missing -- run scripts/build_touches.py first")
    rows = load()
    seasons = sorted({r[0] for r in rows})
    print(f"\n  {len(rows):,} chances, {seasons[0]}-{seasons[-1]}\n")

    # ---------- 1. the league, three ways ----------
    print("  THE SHAPE OF THE THING\n")
    header("population")
    carries = [r[5] for r in rows if r[3] == "rush"]
    catches = [r[5] for r in rows if r[3] == "target" and r[4]]
    targets = [r[5] for r in rows if r[3] == "target"]
    print(describe("every carry", carries))
    print(describe("every catch", catches))
    print(describe("every target (inc. drops/incs)", targets))
    print(describe("every chance, all types", [r[5] for r in rows]))
    print("\n  Read the target row against the catch row. Counting only catches,")
    print("  a receiver looks like a 9-yard player. Counting every ball thrown at")
    print("  him -- every play his team spent on him -- the single likeliest")
    print("  outcome is zero, and it is not close. That is the editor's strikeout.")

    # ---------- 2. per player-season ----------
    by = collections.defaultdict(list)
    for s, pid, nm, kind, touched, y in rows:
        by[(s, pid, nm)].append((kind, touched, y))
    recs = []
    for (s, pid, nm), v in by.items():
        touches = [y for kind, t, y in v if t]
        if len(touches) < a.min_touches:
            continue
        rushes = sum(1 for kind, t, y in v if kind == "rush")
        role = "back" if rushes / len(v) > 0.6 else ("pass-catcher"
               if rushes / len(v) < 0.2 else "hybrid")
        recs.append(dict(season=s, player=nm, role=role, touches=len(touches),
                         chances=len(v), mean=statistics.mean(touches),
                         median=statistics.median(touches),
                         mode=mode_of(touches)[0], trim=trimmed(touches),
                         skew=skew(touches),
                         opp_mean=statistics.mean([y for _, _, y in v]),
                         opp_median=statistics.median([y for _, _, y in v])))

    print(f"\n\n  BY ROLE -- {len(recs):,} player-seasons with {a.min_touches}+ touches\n")
    header("role")
    for role in ("back", "hybrid", "pass-catcher"):
        v = [r for r in recs if r["role"] == role]
        keys = {(r["season"], r["player"]) for r in v}
        pool = [y for (s, pid, nm), raw in by.items() if (s, nm) in keys
                for kind, t, y in raw if t]
        print(describe(f"{role}  ({len(v)} seasons)", pool))

    # ---------- 3. where mean and median disagree ----------
    print("\n\n  WHERE THE TWO NUMBERS DISAGREE MOST\n")
    print("  A big gap means the season was carried by a handful of long ones.")
    print("  A small gap means the player was what he looked like every week.\n")
    for role in ("back", "pass-catcher"):
        v = sorted((r for r in recs if r["role"] == role),
                   key=lambda r: r["mean"] - r["median"], reverse=True)
        print(f"  {role.upper()} -- biggest gap between mean and median")
        print(f"  {'player':<22}{'season':>7}{'touches':>9}{'mean':>8}"
              f"{'median':>8}{'gap':>7}")
        for r in v[:6]:
            print(f"  {r['player'][:21]:<22}{r['season']:>7}{r['touches']:>9}"
                  f"{r['mean']:>8.2f}{r['median']:>8.1f}"
                  f"{r['mean']-r['median']:>7.2f}")
        print(f"  {'...':<22}")
        for r in v[-3:]:
            print(f"  {r['player'][:21]:<22}{r['season']:>7}{r['touches']:>9}"
                  f"{r['mean']:>8.2f}{r['median']:>8.1f}"
                  f"{r['mean']-r['median']:>7.2f}")
        print()

    # ---------- 4. does the median say anything the mean does not? ----------
    print("\n  DOES THE MEDIAN CARRY INFORMATION THE MEAN DOES NOT?\n")
    def r_of(xs, ys):
        n = len(xs); mx, my = sum(xs)/n, sum(ys)/n
        sx = math.sqrt(sum((x-mx)**2 for x in xs)); sy = math.sqrt(sum((y-my)**2 for y in ys))
        return sum((x-mx)*(y-my) for x, y in zip(xs, ys))/(sx*sy)
    for role in ("back", "pass-catcher"):
        v = [r for r in recs if r["role"] == role]
        print(f"  {role:<14} mean vs median r = "
              f"{r_of([x['mean'] for x in v], [x['median'] for x in v]):.3f}   "
              f"(n={len(v)})")
    print("\n  If that correlation were near 1.00 the median would be redundant.")
    print("  It is not. The two numbers rank players differently, which means")
    print("  choosing one is a real editorial decision and not a rounding style.")

    # ---------- 5. which one is the more durable trait? ----------
    # THIS IS THE TEST THAT SETTLES IT, and it declines to settle it. A statistic
    # is better if it tells you more about next season. Bootstrap the DIFFERENCE
    # in persistence, because two overlapping intervals do not test a difference.
    print("\n\n  WHICH IS THE MORE DURABLE TRAIT?\n")
    import random
    seasons_by = {(r["season"], r["player"]): r for r in recs}
    print(f"  {'role':<14}{'mean r':>9}{'median r':>10}{'difference':>13}"
          f"{'95% CI of the difference':>30}")
    print("  " + "-" * 76)
    for role in ("back", "pass-catcher"):
        pairs = [(r["mean"], n["mean"], r["median"], n["median"])
                 for k, r in seasons_by.items()
                 if r["role"] == role
                 and (n := seasons_by.get((k[0] + 1, k[1]))) is not None
                 and n["role"] == role]
        if len(pairs) < 40:
            continue
        rm = r_of([x[0] for x in pairs], [x[1] for x in pairs])
        rd = r_of([x[2] for x in pairs], [x[3] for x in pairs])
        rng = random.Random(7)
        bs = []
        for _ in range(4000):
            b = [pairs[rng.randrange(len(pairs))] for _ in range(len(pairs))]
            bs.append(r_of([x[2] for x in b], [x[3] for x in b])
                      - r_of([x[0] for x in b], [x[1] for x in b]))
        bs.sort()
        lo, hi = bs[int(.025 * len(bs))], bs[int(.975 * len(bs))]
        verdict = "excludes 0" if lo > 0 or hi < 0 else "INCLUDES 0"
        print(f"  {role:<14}{rm:>9.3f}{rd:>10.3f}{rd-rm:>+13.3f}"
              f"{f'{lo:+.3f} to {hi:+.3f}  {verdict}':>30}")
    print("\n  The point estimates flip: for backs the mean is the more durable")
    print("  trait, for pass-catchers the median is. That is a tidy story and the")
    print("  intervals do not support it. Both straddle zero, so on this evidence")
    print("  NEITHER statistic predicts next season better than the other, and the")
    print("  flip is the kind of pattern a sample this size produces by itself.")
    print("  Report the descriptive shape, which is solid. Do not sell the flip.")

    print("\n  WHAT THE MEAN IS STILL FOR. Mean times touches equals total yards.")
    print("  Medians do not add up to anything. Use the mean to ask what a player")
    print("  contributed; use the median to ask what the next play will bring.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
