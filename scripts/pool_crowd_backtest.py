#!/usr/bin/env python3
"""Back-test whether elevating crowd non-favorites improved pool scoring.

READ THE BENCHMARK LINE BEFORE THE STRATEGY LINES. Built by Codex 2026-09-23,
with the random-weight benchmark added afterwards because without it the table
reads backwards.

The benchmark is what you would score by assigning the weights 1..15 AT RANDOM,
which is n_correct x 8 = 224 over these three weeks. Every strategy here lands
below it: Patrick's actual 202, non-favorites-first 213, least-popular-first 219.
The proposed rule does not beat random weighting. It loses to random weighting by
less than the actual entry did, which is a different and much smaller claim.

AND THE RULE'S OWN PREMISE FAILS IN THIS DATA. It promotes crowd non-favorites on
the theory that they are undervalued. In these 45 picks non-favorites went 7/12
(58.3%) and crowd favorites went 21/33 (63.6%). The favorites were the better
group. The +11 comes from which particular non-favorites hit -- Northwestern
alone is +10 -- not from non-favorites hitting more often.

So the honest reading is the opposite of encouraging: this is what noise looks
like when you sort on it afterwards. Treat weeks 1-3 as exploratory, freeze the
rule prospectively, and grade week 4 against the 224-style benchmark rather than
against the actual entry.

The primary rule holds Patrick's selected sides and within-group ordering fixed.
It moves every selected side with <50% CBS support above every selected side with
>=50% support, then reassigns the legal weights 15..1.  The secondary rule ranks
all selected sides from least to most popular, with side name as a pre-outcome
tie-breaker.

Inference uses the exact distribution of weighted scores conditional on each
week's observed number of correct picks.  It asks how unusual a strategy's score
would be if the 1..15 weights were randomly assigned within each week.
"""
from collections import Counter
from fractions import Fraction
from itertools import combinations
import json
import math
import os


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "pool-crowd-backtest.json")


def score(picks, weights):
    return sum(weights[p["side"]] for p in picks if p["correct"])


def actual_weights(picks):
    return {p["side"]: p["weight"] for p in picks}


def primary_weights(picks):
    """Non-favorites first; preserve Patrick's ordering inside both groups."""
    ordered = sorted(picks, key=lambda p: (p["public"] >= 50, -p["weight"]))
    return {p["side"]: 15 - i for i, p in enumerate(ordered)}


def graded_weights(picks):
    """Least popular first; alphabetical tie-break is fixed and outcome-free."""
    ordered = sorted(picks, key=lambda p: (p["public"], p["side"]))
    return {p["side"]: 15 - i for i, p in enumerate(ordered)}


def weekly_null(n_correct):
    """Exact score distribution for choosing n_correct weights from 1..15."""
    dist = Counter(sum(c) for c in combinations(range(1, 16), n_correct))
    return dist


def convolve(a, b):
    out = Counter()
    for sa, ca in a.items():
        for sb, cb in b.items():
            out[sa + sb] += ca * cb
    return out


def upper_tail(dist, observed):
    return Fraction(sum(n for s, n in dist.items() if s >= observed), sum(dist.values()))


def percentile(dist, observed):
    below = sum(n for s, n in dist.items() if s < observed)
    equal = dist.get(observed, 0)
    return Fraction(2 * below + equal, 2 * sum(dist.values()))


def rank(score_value, others):
    return 1 + sum(s > score_value for s in others)


def fisher_two_sided(a, b, c, d):
    """Two-sided Fisher exact p for [[a,b],[c,d]], using fixed margins."""
    r1, r2 = a + b, c + d
    col1, n = a + c, a + b + c + d

    def prob(x):
        return Fraction(math.comb(col1, x) * math.comb(n - col1, r1 - x), math.comb(n, r1))

    lo, hi = max(0, r1 - (n - col1)), min(r1, col1)
    observed = prob(a)
    return sum((prob(x) for x in range(lo, hi + 1) if prob(x) <= observed), Fraction())


def main():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)

    methods = {
        "actual": actual_weights,
        "nonfavorite_first": primary_weights,
        "least_popular_first": graded_weights,
    }
    totals = Counter()
    rows = []
    null = Counter({0: 1})

    for week in data["weeks"]:
        picks = week["picks"]
        assert sorted(p["weight"] for p in picks) == list(range(1, 16))
        assert score(picks, actual_weights(picks)) == week["patrick_score"]
        n_correct = sum(p["correct"] for p in picks)
        null = convolve(null, weekly_null(n_correct))
        row = {"week": week["week"], "correct": n_correct}
        for name, make_weights in methods.items():
            value = score(picks, make_weights(picks))
            row[name] = value
            row[name + "_rank"] = rank(value, week["other_scores"])
            totals[name] += value
        rows.append(row)

    nonfav = [p for w in data["weeks"] for p in w["picks"] if p["public"] < 50]
    favorite = [p for w in data["weeks"] for p in w["picks"] if p["public"] >= 50]
    nf_win = sum(p["correct"] for p in nonfav)
    f_win = sum(p["correct"] for p in favorite)
    fisher = fisher_two_sided(nf_win, len(nonfav) - nf_win,
                              f_win, len(favorite) - f_win)

    print("week correct actual(rank) nonfavorite-first(rank) least-popular-first(rank)")
    for r in rows:
        print(f"{r['week']:>4} {r['correct']:>7} "
              f"{r['actual']:>6}({r['actual_rank']}) "
              f"{r['nonfavorite_first']:>17}({r['nonfavorite_first_rank']}) "
              f"{r['least_popular_first']:>19}({r['least_popular_first_rank']})")

    expected = sum(r["correct"] for r in rows) * 8
    print(f"\nBENCHMARK: random weights 1..15 would expect {expected}")
    print("three-week totals")
    for name in methods:
        p = upper_tail(null, totals[name])
        pct = percentile(null, totals[name])
        print(f"{name:>20}: {totals[name]:>3} ({totals[name]-expected:+d} vs random)  "
              f"exact upper-tail p={float(p):.4f} null percentile={float(pct):.1%}")

    print("\nselection diagnostic -- does the rule's PREMISE hold?")
    print(f"crowd non-favorites: {nf_win}/{len(nonfav)} correct ({nf_win/len(nonfav):.1%})")
    print(f"crowd favorites:     {f_win}/{len(favorite)} correct ({f_win/len(favorite):.1%})")
    print(f"two-sided Fisher exact p={float(fisher):.4f}")
    if nf_win / len(nonfav) < f_win / len(favorite):
        print("NOTE: non-favorites were the WORSE group. The rule promotes them anyway;")
        print("any gain comes from which ones hit, not from how often they hit.")

    print("\noverall placement if substituted for Patrick's actual 202")
    others_ytd = [190, 185, 74, 67, 64, 59, 53, 37, 0]
    for name in methods:
        print(f"{name:>20}: rank {rank(totals[name], others_ytd)}")


if __name__ == "__main__":
    main()
