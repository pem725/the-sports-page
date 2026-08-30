#!/usr/bin/env python3
"""NFL playoff odds, with the betting market as the prior.

    python3 scripts/build_nfl_odds.py            # writes data/nfl-odds.json
    python3 scripts/build_nfl_odds.py --dry-run  # compute and report, write nothing

WHY THE MARKET AND NOT OUR OWN RATING. Before a season starts we have no
results, so any rating we build is a rating of our own opinions. The closing
spread is the one number that already aggregates injuries, roster moves, coaching
changes and money at risk. Using it is not laziness; it is refusing to pretend we
know something the market does not.

HOW IT WORKS. Roughly 110 of the 272 regular-season games carry a published line
by late August. Those are enough to solve for a rating per club, because a line
is a statement about a DIFFERENCE:

    spread_line  =  rating(home) - rating(away) + home advantage

That is a linear system in 32 unknowns with a hundred-odd equations, so we solve
it by least squares, pinning the ratings to sum to zero and letting the home
advantage fall out as a free parameter. The clubs whose games are not yet priced
still get a rating, because they appear in games that ARE priced.

Then every one of the 272 games is simulated 20,000 times, margins drawn normal
around the predicted spread, and the playoff field is counted: four division
winners and three wild cards per conference.

TIES ARE BROKEN AT RANDOM, not by the real tiebreaker rules, which run to head to
head, common games, conference record and eventually a coin toss. So read
anything near a coin flip as a coin flip -- the same caveat the baseball board
carries.
"""
import argparse
import collections
import csv
import io
import json
import os
import urllib.request

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "nfl-odds.json")
GAMES = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
NSIMS, MARGIN_SD = 20000, 13.2      # NFL game margins scatter about 13 points

DIV = {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"], "AFC North": ["BAL", "CIN", "CLE", "PIT"],
    "AFC South": ["HOU", "IND", "JAX", "TEN"], "AFC West": ["DEN", "KC", "LV", "LAC"],
    "NFC East": ["DAL", "NYG", "PHI", "WAS"], "NFC North": ["CHI", "DET", "GB", "MIN"],
    "NFC South": ["ATL", "CAR", "NO", "TB"], "NFC West": ["ARI", "LA", "SF", "SEA"],
}
TEAM_DIV = {t: d for d, ts in DIV.items() for t in ts}
CONF = {t: d.split()[0] for d, ts in DIV.items() for t in ts}
NAME = {
    "ARI": "Cardinals", "ATL": "Falcons", "BAL": "Ravens", "BUF": "Bills", "CAR": "Panthers",
    "CHI": "Bears", "CIN": "Bengals", "CLE": "Browns", "DAL": "Cowboys", "DEN": "Broncos",
    "DET": "Lions", "GB": "Packers", "HOU": "Texans", "IND": "Colts", "JAX": "Jaguars",
    "KC": "Chiefs", "LAC": "Chargers", "LA": "Rams", "LV": "Raiders", "MIA": "Dolphins",
    "MIN": "Vikings", "NE": "Patriots", "NO": "Saints", "NYG": "Giants", "NYJ": "Jets",
    "PHI": "Eagles", "PIT": "Steelers", "SEA": "Seahawks", "SF": "49ers", "TB": "Buccaneers",
    "TEN": "Titans", "WAS": "Commanders",
}


def load(season):
    req = urllib.request.Request(GAMES, headers={"User-Agent": "Mozilla/5.0"})
    txt = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")
    rows = [r for r in csv.DictReader(io.StringIO(txt))
            if r["season"] == str(season) and r["game_type"] == "REG"]
    if not rows:
        raise SystemExit(f"no {season} regular-season rows in the schedule feed")
    return rows


def ratings(rows, teams):
    """Least squares on the published lines. Returns per-club rating and the
    home advantage the market is implying."""
    idx = {t: i for i, t in enumerate(teams)}
    A, b = [], []
    for r in rows:
        try:
            s = float(r["spread_line"])
        except (TypeError, ValueError):
            continue
        row = np.zeros(len(teams) + 1)
        row[idx[r["home_team"]]] = 1.0
        row[idx[r["away_team"]]] = -1.0
        row[-1] = 1.0                     # home advantage
        A.append(row); b.append(s)
    if len(A) < len(teams):
        raise SystemExit(f"only {len(A)} priced games for {len(teams)} clubs -- too few to solve")
    A = np.vstack(A + [np.append(np.ones(len(teams)), 0.0)])   # pin ratings to sum to zero
    b = np.array(b + [0.0])
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    pred = A[:-1] @ sol
    return dict(zip(teams, sol[:-1])), float(sol[-1]), len(b) - 1, float(np.sqrt(np.mean((pred - b[:-1]) ** 2)))


def simulate(rows, teams, rate, hfa, rng):
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    wins = np.zeros((NSIMS, n))
    played = collections.Counter()
    for r in rows:
        h, a = idx[r["home_team"]], idx[r["away_team"]]
        hs, as_ = r["home_score"], r["away_score"]
        if hs not in ("", None) and as_ not in ("", None):
            won = float(hs) > float(as_)
            wins[:, h if won else a] += 1
            played[r["home_team"]] += 1; played[r["away_team"]] += 1
            continue
        mu = rate[r["home_team"]] - rate[r["away_team"]] + hfa
        hw = rng.normal(mu, MARGIN_SD, NSIMS) > 0
        wins[:, h] += hw
        wins[:, a] += ~hw
    return wins, played


def field(wins, teams, rng):
    """Four division winners and three wild cards per conference. Ties at random."""
    idx = {t: i for i, t in enumerate(teams)}
    jitter = wins + rng.random(wins.shape) * 1e-3
    made = np.zeros(wins.shape, bool)
    div_win = np.zeros(wins.shape, bool)
    for conf in ("AFC", "NFC"):
        champs = []
        for d, ts in DIV.items():
            if not d.startswith(conf):
                continue
            cols = [idx[t] for t in ts]
            best = np.array(cols)[np.argmax(jitter[:, cols], axis=1)]
            champs.append(best)
            div_win[np.arange(len(wins)), best] = True
            made[np.arange(len(wins)), best] = True
        champs = np.column_stack(champs)
        pool = [idx[t] for t in teams if CONF[t] == conf]
        rest = jitter[:, pool].copy()
        for k in range(champs.shape[1]):                       # remove the four winners
            rest[np.arange(len(wins)), [pool.index(c) for c in champs[:, k]]] = -1e9
        top3 = np.argsort(-rest, axis=1)[:, :3]
        for k in range(3):
            made[np.arange(len(wins)), np.array(pool)[top3[:, k]]] = True
    return made, div_win


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = load(args.season)
    teams = sorted(TEAM_DIV)
    seen = {r["home_team"] for r in rows} | {r["away_team"] for r in rows}
    if seen != set(teams):
        raise SystemExit(f"club codes do not match the division map: {seen ^ set(teams)}")

    rate, hfa, npriced, rmse = ratings(rows, teams)
    rng = np.random.default_rng(725)
    wins, played = simulate(rows, teams, rate, hfa, rng)
    made, div_win = field(wins, teams, rng)

    import math
    def sched_for(t):
        """Per-game win probability, for the hover panel. Same normal model as the sim."""
        games = []
        for r in sorted((g for g in rows if t in (g["home_team"], g["away_team"])),
                        key=lambda g: (g["gameday"] or "", int(g["week"]))):
            home = r["home_team"] == t
            opp = r["away_team"] if home else r["home_team"]
            mu = rate[t] - rate[opp] + (hfa if home else -hfa)
            p = 0.5 * (1 + math.erf(mu / (MARGIN_SD * math.sqrt(2))))
            won = None
            if r["home_score"] not in ("", None) and r["away_score"] not in ("", None):
                won = (float(r["home_score"]) > float(r["away_score"])) == home
            games.append(dict(opp=NAME[opp], site="home" if home else "away",
                              date=r["gameday"], p=round(p, 4), won=won))
        return games

    out = []
    for i, t in enumerate(teams):
        out.append(dict(
            team=t, name=NAME[t], div=TEAM_DIV[t], conf=CONF[t], sched=sched_for(t),
            rating=round(float(rate[t]), 2),
            proj=round(float(wins[:, i].mean()), 1),
            played=played[t],
            po=round(float(made[:, i].mean()), 4),
            dv=round(float(div_win[:, i].mean()), 4),
            sos=round(float(np.mean([rate[r["away_team"] if r["home_team"] == t else r["home_team"]]
                                     for r in rows if t in (r["home_team"], r["away_team"])])), 2),
        ))
    out.sort(key=lambda r: -r["po"])
    method = (f"Ratings solved by least squares from {npriced} published point spreads "
              f"(residual {rmse:.2f} points); implied home advantage {hfa:.2f}. "
              f"{NSIMS:,} simulated seasons, margins normal with a {MARGIN_SD}-point spread")
    print(f"  {npriced} priced games -> ratings, residual {rmse:.2f} pts, home advantage {hfa:+.2f}\n")
    print(f"  {'club':<14}{'rating':>8}{'proj W':>8}{'playoffs':>10}{'division':>10}")
    for r in out[:8]:
        print(f"  {r['name']:<14}{r['rating']:>8.1f}{r['proj']:>8.1f}{r['po']*100:>9.0f}%{r['dv']*100:>9.0f}%")
    print("  ...")
    for r in out[-3:]:
        print(f"  {r['name']:<14}{r['rating']:>8.1f}{r['proj']:>8.1f}{r['po']*100:>9.0f}%{r['dv']*100:>9.0f}%")

    if args.dry_run:
        print("\n  dry run, nothing written")
        return
    json.dump({"generated": __import__("datetime").date.today().isoformat(),
               "season": args.season, "method": method, "teams": out},
              open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT}")


if __name__ == "__main__":
    main()
