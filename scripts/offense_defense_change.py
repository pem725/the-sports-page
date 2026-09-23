#!/usr/bin/env python3
"""Which is easier to move by a full standard deviation -- your offense or your defense?

    python3 scripts/offense_defense_change.py
    python3 scripts/offense_defense_change.py --metric ypp

THE EDITOR'S QUESTION, 2026-09-23: "What is easier to change by one standard
deviation? Your offensive productivity or your defensive stinginess? Show game to
game, year to year, which shows the easiest replicability, but also can be
altered."

Those are the same coin. A unit that repeats itself year after year is a unit you
cannot change; a unit that scatters is one that moves. So one number answers both,
and the interesting part is which side of the ball each belongs to.

THE TRAP, AND IT IS THE WHOLE REASON THIS SCRIPT IS LONGER THAN IT LOOKS. A low
year-over-year correlation has two completely different causes that look identical
in the output:

  1. the unit really does change from year to year, or
  2. the unit is measured badly, so neither year's number means much.

Defense could look "easier to alter" purely because defensive performance is
noisier to observe over sixteen games. That is not a fact about football; it is a
fact about our ruler. Reporting it as the former would be exactly the error this
paper exists to slow down.

So this measures the ruler first. Split each team-season into odd and even games,
correlate the halves, and step that up with Spearman-Brown to get the reliability
of a FULL season. Then divide the year-over-year correlation by that reliability
-- the standard correction for attenuation -- to separate "changed" from "never
measured it properly in the first place".

Report both. If the raw numbers say defense changes more and the corrected numbers
say the two sides are the same, then the honest finding is that defense is harder
to MEASURE, not easier to FIX, and that is a better story anyway.

EVERYTHING IS STANDARDISED WITHIN SEASON, against that year's other 31 teams.
Scoring has inflated since 1999; a "standard deviation" in 2004 is not the same
number of points as in 2024, and the editor asked in standard deviations for
exactly that reason.

ONE HONEST DEFECT, STATED IN THE OUTPUT TOO. `points_for` includes points the
defense and special teams scored. A pick-six is credited to the offense here. The
`--metric ypp` run has no such contamination, which is why both are printed.
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


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def spearman_brown(r_half):
    """Odd-vs-even correlates HALF seasons. Step it up to a full season."""
    if r_half <= -1 or r_half >= 1 or math.isnan(r_half):
        return float("nan")
    return 2 * r_half / (1 + r_half)


def fisher_ci(r, n, z=1.96):
    """Confidence interval on a correlation, via Fisher's z."""
    if math.isnan(r) or abs(r) >= 1 or n < 4:
        return float("nan"), float("nan")
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1 / math.sqrt(n - 3)
    lo, hi = zr - z * se, zr + z * se
    t = lambda v: (math.exp(2 * v) - 1) / (math.exp(2 * v) + 1)
    return t(lo), t(hi)


def load(metric):
    """Return games[(season, team)] = list of (off_value, def_value) per game."""
    games = collections.defaultdict(list)
    for r in csv.DictReader(open(DATA)):
        s, t = int(r["season"]), r["team"]
        plays = float(r["plays"] or 0)
        if metric == "points":
            off, dfn = float(r["points_for"]), float(r["points_against"])
        else:
            if plays < 20:
                continue
            off = float(r["yards"]) / plays
            dfn = None  # filled from the opponent's row below
        games[(s, t)].append([off, dfn, r["game_id"], r["opp"]])
    if metric == "ypp":
        # a team's defensive yards per play IS its opponent's offensive number
        byg = {}
        for (s, t), rows in games.items():
            for row in rows:
                byg[(row[2], t)] = row[0]
        for (s, t), rows in games.items():
            for row in rows:
                row[1] = byg.get((row[2], row[3]))
        for k in list(games):
            games[k] = [r for r in games[k] if r[1] is not None]
    return games


def season_z(games):
    """Per team-season means, standardised against that season's league."""
    seas = collections.defaultdict(dict)
    for (s, t), rows in games.items():
        if len(rows) < 8:
            continue
        seas[s][t] = (statistics.mean(r[0] for r in rows),
                      statistics.mean(r[1] for r in rows))
    z = {}
    for s, teams in seas.items():
        offs = [v[0] for v in teams.values()]
        defs = [v[1] for v in teams.values()]
        mo, so = statistics.mean(offs), statistics.pstdev(offs)
        md, sd = statistics.mean(defs), statistics.pstdev(defs)
        for t, (o, d) in teams.items():
            # defence flipped so that HIGHER IS BETTER on both sides
            z[(s, t)] = ((o - mo) / so, -(d - md) / sd)
    return z


def split_half(games, idx):
    """Reliability of a full season's measurement, odd games vs even games."""
    a, b = [], []
    for (s, t), rows in sorted(games.items()):
        if len(rows) < 12:
            continue
        odd = [r[idx] for i, r in enumerate(rows) if i % 2]
        even = [r[idx] for i, r in enumerate(rows) if not i % 2]
        if len(odd) < 5 or len(even) < 5:
            continue
        a.append(statistics.mean(odd))
        b.append(statistics.mean(even))
    return spearman_brown(pearson(a, b)), len(a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", choices=["points", "ypp"], default="points")
    a = ap.parse_args()
    if not DATA.exists():
        raise SystemExit(f"{DATA} missing -- run scripts/build_nfl_history.py")

    games = load(a.metric)
    z = season_z(games)
    seasons = sorted({s for s, _ in z})
    unit = "points per game" if a.metric == "points" else "yards per play"

    print(f"\n  OFFENSE vs DEFENSE -- which one moves?   [{unit}]")
    print(f"  {len(z)} team-seasons, {seasons[0]}-{seasons[-1]}. "
          f"Standardised within each season.\n")

    # ---- year over year ----
    pairs = {0: ([], []), 1: ([], [])}
    for (s, t), v in z.items():
        nxt = z.get((s + 1, t))
        if nxt:
            for i in (0, 1):
                pairs[i][0].append(v[i])
                pairs[i][1].append(nxt[i])

    print("  YEAR TO YEAR -- how much of last season carries into this one\n")
    print(f"  {'side':<12}{'r':>8}{'95% interval':>18}{'reliability':>14}"
          f"{'r corrected':>14}")
    print("  " + "-" * 66)
    rel = {}
    out = {}
    for i, name in ((0, "offense"), (1, "defense")):
        r = pearson(*pairs[i])
        lo, hi = fisher_ci(r, len(pairs[i][0]))
        rl, _ = split_half(games, i)
        corrected = r / rl if rl and not math.isnan(rl) else float("nan")
        rel[name], out[name] = rl, (r, corrected)
        print(f"  {name:<12}{r:>8.3f}{f'{lo:.3f} to {hi:.3f}':>18}"
              f"{rl:>14.3f}{corrected:>14.3f}")
    print(f"\n  n = {len(pairs[0][0])} consecutive-season pairs.")
    print("  reliability = split-half within season, stepped up (Spearman-Brown).")
    print("  r corrected = r / reliability: what the correlation would be if we")
    print("  could measure each season perfectly. It separates a unit that really")
    print("  changes from one we simply cannot pin down in sixteen games.")

    # ---- how often does a side actually move a full SD? ----
    print("\n  HOW OFTEN DOES A SIDE MOVE A FULL STANDARD DEVIATION?\n")
    print(f"  {'side':<12}{'>=1 SD':>10}{'>=1.5 SD':>11}{'>=2 SD':>9}"
          f"{'median move':>14}")
    print("  " + "-" * 56)
    for i, name in ((0, "offense"), (1, "defense")):
        d = [abs(b - a_) for a_, b in zip(*pairs[i])]
        n = len(d)
        print(f"  {name:<12}{sum(x>=1 for x in d)/n:>9.1%}"
              f"{sum(x>=1.5 for x in d)/n:>11.1%}{sum(x>=2 for x in d)/n:>9.1%}"
              f"{statistics.median(d):>14.2f}")

    # ---- game to game ----
    print("\n  GAME TO GAME -- which side is noisier week to week?\n")
    print(f"  {'side':<12}{'within-season SD':>20}{'in season-SD units':>22}")
    print("  " + "-" * 54)
    for i, name in ((0, "offense"), (1, "defense")):
        within, across = [], []
        byseason = collections.defaultdict(list)
        for (s, t), rows in games.items():
            if len(rows) < 12:
                continue
            within.append(statistics.pstdev(r[i] for r in rows))
            byseason[s].append(statistics.mean(r[i] for r in rows))
        team_sd = statistics.mean(statistics.pstdev(v) for v in byseason.values()
                                  if len(v) > 4)
        w = statistics.mean(within)
        print(f"  {name:<12}{w:>20.2f}{w/team_sd:>22.2f}")
    print("\n  The right-hand column is the one that matters: a single game's")
    print("  wobble measured against the spread between teams. Above 1.0 means one")
    print("  game tells you less than nothing about which team you are watching.")

    if a.metric == "points":
        print("\n  CAVEAT, and it is a real one: points_for includes points scored BY")
        print("  the defense and special teams, so a pick-six is credited to the")
        print("  offense here. Run --metric ypp for the uncontaminated version.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
