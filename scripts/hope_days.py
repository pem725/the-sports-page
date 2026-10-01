#!/usr/bin/env python3
"""How much hope did a season actually deliver?

    python3 scripts/hope_days.py
    python3 scripts/hope_days.py --pair NYM CHC

THE EDITOR'S QUESTION, 2026-10-01: "Are you happier as a Mets fan who knew the
season was over in July, or a Cubs fan who had so much hope only to have the
season end unceremoniously two games into the playoffs?"

That is a real question and it has a measurable half. We cannot say which fan
felt better -- nobody surveyed them. We CAN say exactly how much live hope each
season delivered, because this paper has been storing every club's playoff
probability on a weekly grid since April.

THE UNIT. Integrate playoff probability over time and you get probability-DAYS.
A 50% chance held for 100 days is 50 hope-days: the same quantity of belief you
would have had from 50 days of certainty. It is the area under the hope curve,
and it is the thing a season actually hands you.

    hope-days = INTEGRAL P(playoff) dt       over the measured season

WHY THIS SETTLES SOMETHING. Kahneman's PEAK-END RULE says people retrieve an
experience by its worst moment and its final moment, not by its sum. Integrated
("experienced") utility says the sum is what you lived. These two routinely
disagree, and almost every argument about fandom is an unstated fight over which
one counts. Here they disagree maximally: both 2026 seasons ended at zero, and
one of them contained 126 times more hope than the other.

FOUR LIMITS, AND THE FIRST IS THE ONE THAT MATTERS.

1. THE GRID STARTS 15 APRIL, so opening-day optimism is NOT captured. Every club
   begins a season somewhere near its preseason forecast, and for a club that
   collapses early that lost hope is real and uncounted. Read every figure here
   as "from mid-April onward," never as "all year." This cuts hardest against
   exactly the clubs the piece is least kind to.
2. PROBABILITY IS NOT FEELING. Fans are not calibrated and do not want to be. A
   supporter sitting at 2% may believe entirely, which is most of what being a
   supporter is. We measure what was delivered, not what was experienced.
3. THE GRID IS WEEKLY and the integral interpolates linearly between points, so
   a collapse and recovery inside a single week is invisible.
4. PLAYOFF PROBABILITY IS NOT THE ONLY HOPE. A club out of the race can still
   sell a rookie, a chase, a rivalry. This measures one kind of hope, the kind
   the standings price.
"""
import argparse
import datetime
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
TRAJ = REPO / "data" / "playoff-odds-trajectory.json"


def load():
    d = json.loads(TRAJ.read_text())
    dates = [datetime.date.fromisoformat(x) for x in d["dates"]]
    return dates, d["teams"]


def hope_days(dates, po):
    """Trapezoidal area under the playoff-probability curve, in probability-days.

    Trapezoid rather than a rectangle sum because the grid is weekly and a club
    moving from 20% to 80% across one week was not at either value for the whole
    of it. The rectangle version overstates whichever endpoint you pick.
    """
    return sum((po[i] + po[i + 1]) / 2 * (dates[i + 1] - dates[i]).days
               for i in range(len(po) - 1))


def summarize(dates, teams):
    span = (dates[-1] - dates[0]).days
    out = []
    for t in teams.values():
        po = t["po"]
        # The day hope ended: first grid point at (effectively) zero that is
        # never again non-zero. Reported as a date because "it was over in June"
        # is the claim fans actually make, and it is checkable.
        dead = None
        for i in range(len(po)):
            if po[i] < 0.005 and all(p < 0.005 for p in po[i:]):
                dead = dates[i]
                break
        out.append(dict(abbr=t["abbr"], name=t["name"], w=t["w"], l=t["l"],
                        hope=hope_days(dates, po), share=hope_days(dates, po) / span,
                        peak=max(po), end=po[-1], dead=dead))
    out.sort(key=lambda r: -r["hope"])
    return out, span


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", nargs=2, metavar=("A", "B"))
    a = ap.parse_args()
    dates, teams = load()
    rows, span = summarize(dates, teams)

    print(f"\n  HOPE-DAYS, 2026 -- area under each club's playoff-probability curve")
    print(f"  grid {dates[0]} to {dates[-1]} = {span} days, {len(dates)} weekly points")
    print(f"  ceiling is {span} hope-days (certainty from the first measurement on)\n")
    print(f"  {'club':<13}{'W-L':>9}{'hope-days':>11}{'of max':>8}{'peak':>7}  {'hope died':<11}")
    print("  " + "-" * 62)
    for i, r in enumerate(rows):
        d = r["dead"].strftime("%-d %b") if r["dead"] else "-"
        print(f"  {r['name']:<13}{r['w']}-{r['l']:<5}{r['hope']:>10.0f}"
              f"{r['share']:>8.0%}{r['peak']:>7.0%}  {d:<11}")

    if a.pair:
        A, B = [next(r for r in rows if r["abbr"] == x) for x in a.pair]
        print(f"\n\n  {A['name'].upper()} vs {B['name'].upper()}\n")
        hi, lo = (A, B) if A["hope"] >= B["hope"] else (B, A)
        print(f"  {hi['name']:<10}{hi['hope']:>7.0f} hope-days   peak {hi['peak']:.0%}")
        print(f"  {lo['name']:<10}{lo['hope']:>7.0f} hope-days   peak {lo['peak']:.0%}")
        ratio = hi["hope"] / lo["hope"] if lo["hope"] else float("inf")
        print(f"\n  ratio {ratio:,.0f}x   difference {hi['hope']-lo['hope']:.0f} days")
        print(f"  Both finished the season with no championship. The ENDING was")
        print(f"  identical; the AREA differed by {hi['hope']-lo['hope']:.0f} days.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
