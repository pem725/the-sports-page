#!/usr/bin/env python3
"""A hundred dollars a week, bet or invested, across 56 real seasons.

    python3 scripts/cost_of_fandom.py
    python3 scripts/cost_of_fandom.py --weekly 100 --years 10

THE EDITOR'S QUESTION, 2026-09-25: "You're willing to spend a hundred dollars a
week to bet on a pool. What would happen if you took that hundred dollars and
invested it in a relatively stable asset, something like an index fund? Nothing
sexy. What would it look like week to week, year to year, over a lifetime? That
would be the cost of fandom."

NO ASSUMED RATE OF RETURN. The obvious way to write this is to pick 8% and
compound it, and that would be a worked example rather than a finding. This uses
the actual weekly closes of the S&P 500 from 1970, so every figure below is a
thing that happened to a real person who started in a real year. The spread
between the best and worst starting year is most of the point: the average
outcome is not the outcome, and anybody selling you a single number for a
forty-year horizon is selling you the average of a distribution they have not
shown you.

WHAT IS BEING COMPARED. Two people with identical habits and identical money.
Each commits the same amount every week of the football season -- the regular
season plus the playoffs, about 21 weeks, September to early February. One puts
it through a confidence pool at standard -110 pricing. The other buys the index
and does nothing.

THE BETTOR IS MODELLED TWICE, because people bet in two different ways and the
answers differ enormously:

  FLAT      stakes the same amount every week and pockets what comes back. The
            loss is the vigorish on the handle and nothing else -- the honest
            price of the entertainment.
  LET IT RIDE  puts the whole bankroll back through every week. Same edge, same
            price per cycle, and a completely different destination, because a
            4.545% haircut applied over and over is a compounding loss.

THE HOUSE EDGE IS EXACT, NOT ESTIMATED. Two sides at -110 imply 52.381% each and
sum to 104.76%. A bettor who picks at a true 50% returns 100p - 110(1-p) on a
$110 stake, which is -$5.00, and -$5.00 on $110 risked is 4.545%. That number is
arithmetic. It does not depend on being good or bad at picking; it is what the
price costs before any skill is applied.

THREE HONEST LIMITS, ALL OF WHICH FAVOUR THE BETTOR:

  1. ^GSPC is a PRICE index. It excludes dividends, historically worth around
     two points a year. The investor's real result is BETTER than what is
     printed here, and by a lot over forty years.
  2. No tax, no fees, no inflation adjustment, on either side. Both columns are
     nominal dollars.
  3. The bettor is assumed to pick at exactly 50%. Our own testing says that is
     about right -- 50.2% against the spread over 2,278 college games -- but a
     genuinely skilled bettor would do better than this shows, and a bad one
     worse.
"""
import argparse
import csv
import datetime
import io
import json
import pathlib
import statistics
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
CACHE = REPO / "data" / "sp500-weekly.csv"
URL = ("https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
       "?period1=0&period2=2000000000&interval=1wk")

VIG = 0.04545          # cost of one cycle through a -110 market, exact
SEASON_WEEKS = 21      # regular season plus playoffs


def fetch():
    if CACHE.exists():
        rows = list(csv.DictReader(open(CACHE)))
        return [(datetime.date.fromisoformat(r["date"]), float(r["close"])) for r in rows]
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    d = json.load(urllib.request.urlopen(req, timeout=120))
    r = d["chart"]["result"][0]
    out = []
    for ts, cl in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]):
        if cl:
            out.append((datetime.date.fromtimestamp(ts), float(cl)))
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "close"])
        w.writerows([(d_.isoformat(), c) for d_, c in out])
    return out


def season_weeks(bars, start_year):
    """The football season's weeks: September of start_year to early February."""
    a = datetime.date(start_year, 9, 1)
    b = datetime.date(start_year + 1, 2, 10)
    w = [x for x in bars if a <= x[0] <= b]
    return w[:SEASON_WEEKS]


def run(bars, start_year, years, weekly):
    """Returns (invested, flat_bettor_net, ride_bettor_balance, total_paid_in)."""
    inv = ride = 0.0
    paid = 0.0
    flat_loss = 0.0
    for y in range(start_year, start_year + years):
        wk = season_weeks(bars, y)
        if len(wk) < SEASON_WEEKS - 3:
            return None
        for i, (_, close) in enumerate(wk):
            inv += weekly
            ride = (ride + weekly) * (1 - VIG)
            flat_loss += weekly * VIG
            paid += weekly
            if i + 1 < len(wk):
                inv *= wk[i + 1][1] / close
    return inv, flat_loss, ride, paid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weekly", type=float, default=100.0)
    ap.add_argument("--years", type=int, default=10)
    a = ap.parse_args()
    bars = fetch()
    print(f"\n  S&P 500 weekly closes, {bars[0][0]} to {bars[-1][0]} "
          f"({len(bars):,} weeks). Price index -- dividends NOT included.\n")

    w = a.weekly
    season_cost = w * SEASON_WEEKS
    print(f"  ${w:,.0f} a week for {SEASON_WEEKS} weeks = ${season_cost:,.0f} through the window "
          f"every season.\n")

    for years in (1, 10, 20, 40):
        runs = []
        for y0 in range(1970, 2026 - years + 1):
            r = run(bars, y0, years, w)
            if r:
                runs.append((y0,) + r)
        if not runs:
            continue
        inv = [r[1] for r in runs]
        paid = runs[0][4]
        flat = runs[0][2]
        ride = runs[0][3]
        best = max(runs, key=lambda r: r[1])
        worst = min(runs, key=lambda r: r[1])
        print(f"  ── {years} SEASON{'S' if years > 1 else ''} "
              f"── ${paid:,.0f} put in ── {len(runs)} real starting years ──\n")
        print(f"     {'invested in the index':<30}{'median':>12}{'worst year':>14}{'best year':>13}")
        print(f"     {'':<30}{statistics.median(inv):>11,.0f}"
              f"{worst[1]:>13,.0f}{best[1]:>13,.0f}")
        print(f"     {'':<30}{'':>12}{'(from '+str(worst[0])+')':>14}{'(from '+str(best[0])+')':>13}")
        print()
        print(f"     {'bet it, flat stake':<30}{paid - flat:>11,.0f}"
              f"      lost ${flat:,.0f} to the price")
        print(f"     {'bet it, letting it ride':<30}{ride:>11,.0f}"
              f"      lost ${paid - ride:,.0f} of ${paid:,.0f}")
        med = statistics.median(inv)
        print(f"\n     the gap, median index vs flat betting: "
              f"${med - (paid - flat):,.0f}")
        print(f"     share of starting years where the index beat the bettor: "
              f"{sum(1 for x in inv if x > paid - flat) / len(inv):.0%}\n")

    print("  Read the worst column, not the median. A forty-year horizon has only a")
    print("  handful of genuinely independent starting points in 56 years of data, so")
    print("  the spread is the honest part and the median is the advertisement.")
    print("\n  Dividends are excluded, so the index column understates itself by roughly")
    print("  two points a year. Every simplification here favours the bettor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
