#!/usr/bin/env python3
"""
spurious-correlation.py — Compute phi coefficients between MLB team W/L
and S&P 500 daily direction to find the most absurd spurious correlation.
"""

import math

# S&P 500 daily direction: 1 = UP, 0 = DOWN
# Source: Investing.com historical data, March 26 - April 17, 2026
sp500 = {
    "Mar 26": 0,  # -1.74%
    "Mar 27": 0,  # -1.67%
    # Mar 28-29: weekend
    "Mar 30": 0,  # -0.39%
    "Mar 31": 1,  # +2.91%
    "Apr 01": 1,  # +0.72%
    "Apr 02": 1,  # +0.11%
    # Apr 03: Good Friday (market closed)
    # Apr 04-05: weekend + Easter
    "Apr 06": 1,  # +0.44%
    "Apr 07": 1,  # +0.08%
    "Apr 08": 1,  # +2.51%
    "Apr 09": 1,  # +0.62%
    "Apr 10": 0,  # -0.11%
    # Apr 11: data gap (may be incomplete from source)
    # Apr 12-13 (Sun): weekend
    "Apr 13": 1,  # +1.02%
    "Apr 14": 1,  # +1.18%
    "Apr 15": 1,  # +0.80%
    "Apr 16": 1,  # +0.26%
    "Apr 17": 1,  # +1.20%
}

# Team game results: {date: 1=Win, 0=Loss}
# Source: ESPN team schedule pages

teams = {
    "New York Mets": {
        "Mar 26": 1, "Mar 30": 1, "Mar 31": 0, "Apr 01": 0,
        "Apr 02": 0, "Apr 07": 1, "Apr 08": 0, "Apr 09": 0,
        "Apr 10": 0, "Apr 13": 0, "Apr 14": 0, "Apr 15": 0,
        "Apr 17": 0,
        # Games on non-trading days excluded: Mar 28(W), Mar 29(L),
        # Apr 3(W), Apr 4(W), Apr 5(W), Apr 11(L), Apr 12(L), Apr 18(L)
    },
    "Los Angeles Dodgers": {
        "Mar 26": 1, "Mar 27": 1, "Mar 30": 0, "Mar 31": 1,
        "Apr 01": 0, "Apr 07": 1, "Apr 08": 0, "Apr 10": 1,
        "Apr 13": 1, "Apr 14": 1, "Apr 15": 1, "Apr 17": 1,
        # Non-trading: Mar 28(W), Apr 6(W@TOR), Apr 12(L)
    },
    "Pittsburgh Pirates": {
        "Mar 26": 0, "Mar 30": 0, "Mar 31": 1, "Apr 01": 1,
        "Apr 06": 0, "Apr 07": 1, "Apr 08": 0, "Apr 10": 1,
        "Apr 13": 1, "Apr 14": 0, "Apr 15": 1, "Apr 16": 0,
        "Apr 17": 1,
    },
    "Atlanta Braves": {
        "Mar 27": 1, "Mar 30": 1, "Mar 31": 0, "Apr 01": 1,
        "Apr 02": 1, "Apr 06": 0, "Apr 07": 1, "Apr 08": 1,
        "Apr 10": 1, "Apr 13": 0, "Apr 14": 1, "Apr 15": 1,
        "Apr 17": 1,
    },
    "Cincinnati Reds": {
        "Mar 26": 0, "Mar 30": 1, "Mar 31": 0, "Apr 01": 0,
        "Apr 06": 1, "Apr 07": 1, "Apr 08": 0, "Apr 09": 0,
        "Apr 10": 0, "Apr 14": 1, "Apr 15": 1, "Apr 16": 0,
        "Apr 17": 1,
    },
    "Tampa Bay Rays": {
        "Mar 26": 0, "Mar 30": 1, "Mar 31": 0, "Apr 01": 0,
        "Apr 06": 1, "Apr 07": 0, "Apr 08": 0, "Apr 10": 1,
        "Apr 14": 1, "Apr 15": 1, "Apr 16": 1, "Apr 17": 0,
    },
}


def phi_coefficient(team_results, market_data):
    """Compute phi coefficient between team W/L and market UP/DOWN.
    Only uses dates where both a game was played AND the market was open."""

    # Find overlapping dates
    dates = sorted(set(team_results.keys()) & set(market_data.keys()))
    n = len(dates)
    if n == 0:
        return 0, 0, {}

    # 2x2 contingency table
    # a = market UP & team WIN
    # b = market UP & team LOSS
    # c = market DOWN & team WIN
    # d = market DOWN & team LOSS
    a = b = c = d = 0
    for date in dates:
        mkt = market_data[date]
        team = team_results[date]
        if mkt == 1 and team == 1: a += 1
        elif mkt == 1 and team == 0: b += 1
        elif mkt == 0 and team == 1: c += 1
        else: d += 1

    # Phi = (ad - bc) / sqrt((a+b)(c+d)(a+c)(b+d))
    denom = math.sqrt((a+b) * (c+d) * (a+c) * (b+d)) if (a+b)*(c+d)*(a+c)*(b+d) > 0 else 1
    phi = (a*d - b*c) / denom

    # Chi-square = n * phi^2
    chi2 = n * phi**2

    # p-value approximation (1 df chi-square)
    # Using Wilson-Hilferty approximation
    if chi2 > 0:
        # Simple lookup for common values
        if chi2 >= 6.635: p = "< 0.01"
        elif chi2 >= 3.841: p = "< 0.05"
        elif chi2 >= 2.706: p = "< 0.10"
        else: p = "> 0.10"
    else:
        p = "1.00"

    table = {"a": a, "b": b, "c": c, "d": d, "n": n}
    return phi, chi2, p, table


print("=" * 70)
print("SPURIOUS CORRELATION ANALYSIS")
print("S&P 500 Daily Direction vs MLB Team Win/Loss")
print("Period: March 26 – April 17, 2026")
print("=" * 70)
print()

results = []
for team, games in teams.items():
    phi, chi2, p, table = phi_coefficient(games, sp500)
    results.append((abs(phi), phi, chi2, p, table, team))
    direction = "POSITIVE" if phi > 0 else "NEGATIVE" if phi < 0 else "NONE"
    print(f"{team:25s}  phi = {phi:+.3f}  chi2 = {chi2:.2f}  p {p:>8s}  "
          f"n={table['n']}  [{table['a']}/{table['b']}/{table['c']}/{table['d']}]  {direction}")

print()
print("-" * 70)
results.sort(reverse=True)
winner = results[0]
print(f"\nSTRONGEST SPURIOUS CORRELATION:")
print(f"  {winner[5]}")
print(f"  Phi coefficient: {winner[1]:+.3f}")
print(f"  Chi-square: {winner[2]:.2f} (p {winner[3]})")
print(f"  Direction: {'Market UP → Team LOSES' if winner[1] < 0 else 'Market UP → Team WINS'}")
print(f"  Matched days: {winner[4]['n']}")
print()

# Interpretation for the Mets specifically
mets_phi, mets_chi2, mets_p, mets_table = phi_coefficient(teams["New York Mets"], sp500)
print("METS DEEP DIVE:")
print(f"  When S&P goes UP:  Mets win {mets_table['a']}x, lose {mets_table['b']}x ({mets_table['a']/(mets_table['a']+mets_table['b'])*100:.0f}% win rate)")
print(f"  When S&P goes DOWN: Mets win {mets_table['c']}x, lose {mets_table['d']}x ({mets_table['c']/(mets_table['c']+mets_table['d'])*100:.0f}% win rate)")
print(f"  On UP market days, Mets lose {mets_table['b']/(mets_table['a']+mets_table['b'])*100:.0f}% of the time")
print(f"  Phi = {mets_phi:+.3f}, p {mets_p}")
