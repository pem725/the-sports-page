#!/usr/bin/env python3
"""How many points do you need, and has that changed?

    python3 scripts/win_prob_by_era.py
    python3 scripts/win_prob_by_era.py --eras 1999-2005,2006-2012,2013-2019,2020-2026

THE QUESTION, from the editorial meeting of 2026-09-18. Patrick jr asked for "a
probability curve where the y-axis is the probability of winning and the x-axis is
the total points scored by the team", and the editor made a prediction on the
spot: "if the team scores 35 points, the probability that they won the game is
higher than 0.75."

He was right, and low. Scoring 35 or more wins about 91% of games. The 75% line is
crossed at 24.

"MAKE IT BY ERA" was the other half of the ask, and it is the half that matters.
A single curve across all seasons would answer a question nobody asked: it would
average together the game as it was and the game as it is. If scoring inflates,
the same 24 points buys less, and the curve should slide right. That is a
measurable claim, and this measures it.

WHY POINTS SCORED AND NOT POINT MARGIN. Margin is a better predictor and a worse
question -- of course you win when you outscore people. The interesting version is
the one a fan can use from a single number on a scoreboard: my team has 24, how
worried should I be? Margin requires knowing both scores, at which point you
already know who won.

READ THE CONFIDENCE INTERVALS, not the point estimates. Split ten thousand games
into four eras and seven scoring bands and some cells get thin. A band with forty
games in it will bounce several points between eras for no reason at all, and the
interval is the only thing that tells you which movements to believe.
"""
import argparse
import collections
import csv
import math
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "nfl" / "team-games.csv"
BANDS = [(0, 9), (10, 16), (17, 20), (21, 23), (24, 27), (28, 34), (35, 999)]


def label(lo, hi):
    return f"{lo}+" if hi > 900 else (f"{lo}-{hi}" if lo != hi else str(lo))


def wilson(w, n):
    """Wilson interval. Normal approximation lies badly near 0 and 1, and the
    whole top of this table sits near 1."""
    if not n:
        return 0.0, 0.0, 0.0
    p = w / n
    z = 1.96
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def load():
    if not DATA.exists():
        raise SystemExit(f"{DATA} missing -- run scripts/build_nfl_history.py first")
    rows = []
    for r in csv.DictReader(open(DATA)):
        rows.append((int(r["season"]), int(r["points_for"]), int(r["win"])))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eras", default="")
    a = ap.parse_args()
    rows = load()
    seasons = sorted({s for s, _, _ in rows})
    if a.eras:
        eras = []
        for chunk in a.eras.split(","):
            lo, hi = chunk.split("-")
            eras.append((int(lo), int(hi)))
    else:
        # four roughly equal spans across whatever is loaded
        n = len(seasons)
        size = max(1, n // 4)
        eras = [(seasons[i], seasons[min(i + size - 1, n - 1)])
                for i in range(0, n, size)][:4]
        eras[-1] = (eras[-1][0], seasons[-1])

    print(f"\n  {len(rows):,} team-games, {seasons[0]}-{seasons[-1]}")
    print("  P(win | points your team scored). Wilson 95% intervals.\n")
    head = f"  {'points':<10}"
    for lo, hi in eras:
        head += f"{f'{lo}-{hi}':>18}"
    print(head)
    print("  " + "-" * (10 + 18 * len(eras)))

    for blo, bhi in BANDS:
        line = f"  {label(blo, bhi):<10}"
        for elo, ehi in eras:
            sel = [(p, w) for s, p, w in rows if elo <= s <= ehi and blo <= p <= bhi]
            n = len(sel)
            w = sum(x[1] for x in sel)
            if n < 25:
                line += f"{'-':>18}"
            else:
                pt, lo_, hi_ = wilson(w, n)
                line += f"{f'{pt*100:.0f}% ({lo_*100:.0f}-{hi_*100:.0f})':>18}"
        print(line)

    print(f"\n  {'':<10}" + "".join(
        f"{f'n={sum(1 for s,_,_ in rows if e0<=s<=e1):,}':>18}" for e0, e1 in eras))

    # where does each era cross 75%?
    print("\n  WHERE 75% IS CROSSED -- the number a fan can actually use\n")
    print(f"  {'era':<14}{'points needed':>15}{'games':>10}")
    for elo, ehi in eras:
        era_rows = [(p, w) for s, p, w in rows if elo <= s <= ehi]
        cross = None
        for pt in range(10, 60):
            sel = [x for x in era_rows if x[0] >= pt]
            if len(sel) < 100:
                break
            if sum(x[1] for x in sel) / len(sel) >= 0.75:
                cross = pt
                break
        print(f"  {f'{elo}-{ehi}':<14}{(str(cross) if cross else '?'):>15}{len(era_rows):>10,}")
    print("\n  If scoring has inflated, this column climbs. If it has not, it does not.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
