#!/usr/bin/env python3
"""
CFB Pre-Season Simulation engine (The Sports Page tentpole, late August each year).

Methodology (see CLAUDE.md "Pre-Season Simulation Framework" + Issue #022 JND work):
  * PRIOR: a consensus team-strength rating (SP+ from CollegeFootballData). SP+ is a
    points-above-average number; the expected margin of a game is the rating gap plus
    home-field advantage.
  * WIN PROBABILITY: p(home win) = Phi(expected_margin / SIGMA), the standard normal
    margin model (SIGMA ~ 13.5 for CFB).
  * JUST-NOTICEABLE DIFFERENCE: a game is a CONFIDENT CALL only if the favorite's win
    probability clears the JND boundary of 0.75 (the same P=0.75 threshold Issue #022
    fit to ranked-matchup data). Anything inside [0.25, 0.75] is an explicit COIN FLIP
    -- the model refuses to fake a call it has not earned.
  * OUTPUTS: expected wins per team (sum of per-game win probabilities), projected
    conference leaders, a projected 12-team Playoff, a title pick, and -- honestly --
    the count of games that are coin flips rather than calls.

This is the ENGINE. It is meant to be run the last weekend of August with that year's
posted SP+ ratings. Run with an older year to smoke-test it against known outcomes:

  CFBD_KEY=... python3 scripts/cfb_preseason_sim.py --year 2025
  CFBD_KEY=... python3 scripts/cfb_preseason_sim.py --year 2026   # once SP+ 2026 posts
"""
import os, sys, json, math, argparse, urllib.request
from statistics import NormalDist

API = "https://apinext.collegefootballdata.com"
KEY = os.environ.get("CFBD_KEY")
SIGMA = 13.5          # CFB margin-vs-expectation standard deviation (points)
HFA = 2.5             # home-field advantage (points)
JND_P = 0.75          # confident-call boundary: favorite must clear this or it's a coin flip
NORM = NormalDist(0, SIGMA)


def fetch(path):
    if not KEY:
        sys.exit("ERROR: set CFBD_KEY env var")
    req = urllib.request.Request(path if path.startswith("http") else API + path,
                                 headers={"Authorization": f"Bearer {KEY}", "Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=90))


def win_prob(margin):
    """P(home team wins) given expected margin in points."""
    return NORM.cdf(margin)


def load(year):
    ratings = {x["team"]: x["rating"] for x in fetch(f"/ratings/sp?year={year}")
               if isinstance(x.get("rating"), (int, float)) and x.get("team")}
    # team -> conference (FBS only)
    conf = {}
    for t in fetch(f"/teams/fbs?year={year}"):
        conf[t.get("school")] = t.get("conference")
    games = fetch(f"/games?year={year}&seasonType=regular")
    return ratings, conf, games


def simulate(year):
    ratings, conf, games = load(year)
    if not ratings:
        sys.exit(f"No SP+ ratings posted for {year} yet -- the prior is not available. "
                 f"This is expected before late August. Try an earlier year to test the engine.")

    exp_wins = {t: 0.0 for t in ratings}
    games_played = {t: 0 for t in ratings}
    n_calls = n_flips = n_games = 0
    flip_examples = []

    for g in games:
        h, a = g.get("homeTeam"), g.get("awayTeam")
        if h not in ratings or a not in ratings:      # skip FBS-vs-FCS / unrated
            continue
        neutral = g.get("neutralSite")
        margin = (ratings[h] - ratings[a]) + (0.0 if neutral else HFA)
        p = win_prob(margin)                          # P(home win)
        exp_wins[h] += p
        exp_wins[a] += (1 - p)
        games_played[h] += 1
        games_played[a] += 1
        n_games += 1
        fav_p = max(p, 1 - p)
        if fav_p >= JND_P:
            n_calls += 1
        else:
            n_flips += 1
            if len(flip_examples) < 12:
                fav, dog = (h, a) if p >= 0.5 else (a, h)
                flip_examples.append((g.get("week"), fav, dog, round(fav_p, 3)))

    # standings
    board = sorted(exp_wins, key=lambda t: -exp_wins[t])

    # projected conference leader = highest expected wins in each conference.
    # Independents (e.g. Notre Dame) have no conference title to win, so they are
    # excluded from champ logic and can only reach the field as an at-large.
    INDEP = {"FBS Independents", None, ""}
    conf_leader = {}
    for t in board:
        c = conf.get(t)
        if c and c not in INDEP and c not in conf_leader:
            conf_leader[c] = t

    # 12-team Playoff: 5 highest-rated conference champions get in as champs (top 4
    # seeded 1-4 with byes), then 7 at-large. At-large is chosen by TEAM QUALITY (SP+),
    # not raw expected wins -- otherwise a Group-of-5 team padding wins against a soft
    # schedule steals a bid from a stronger team. This mirrors how the committee weighs
    # quality over raw record.
    champs = sorted(conf_leader.values(), key=lambda t: -ratings[t])[:5]
    champ_set = set(champs)
    at_large = sorted([t for t in board if t not in champ_set],
                      key=lambda t: -ratings[t])[:7]
    # seed: champions ranked by rating take 1-5, then at-large by rating for 6-12
    seeds = sorted(champs, key=lambda t: -ratings[t]) + sorted(at_large, key=lambda t: -ratings[t])

    return dict(year=year, ratings=ratings, conf=conf, exp_wins=exp_wins, games_played=games_played,
                board=board, conf_leader=conf_leader, seeds=seeds, champ_set=champ_set,
                n_games=n_games, n_calls=n_calls, n_flips=n_flips, flip_examples=flip_examples)


def report(r):
    y = r["year"]
    print(f"\n{'='*66}\n  CFB PRE-SEASON SIMULATION  ·  {y}  ·  The Sports Page engine\n{'='*66}")
    print(f"  Prior: SP+ ratings ({len(r['ratings'])} FBS teams) · sigma={SIGMA} · HFA={HFA}")
    print(f"  JND boundary: a game is a 'call' only if the favorite clears {int(JND_P*100)}%\n")

    quality = sorted(r["board"], key=lambda t: -r["ratings"][t])
    print("  PROJECTED TOP 15 (by team strength, SP+):")
    for i, t in enumerate(quality[:15], 1):
        gp = r["games_played"][t]
        print(f"   {i:>2}. {t:<18} SP+ {r['ratings'][t]:+5.1f}"
              f"   ({r['exp_wins'][t]:4.1f} exp. wins of {gp:>2})")

    print(f"\n  PROJECTED 12-TEAM PLAYOFF FIELD (seeded):")
    for i, t in enumerate(r["seeds"], 1):
        tag = "conf champ" if t in r["champ_set"] else "at-large"
        bye = "  <-- first-round bye" if i <= 4 else ""
        print(f"   {i:>2}. {t:<18} {r['exp_wins'][t]:4.1f} exp. wins  [{tag}]{bye}")

    title = r["seeds"][0]
    print(f"\n  TITLE PICK: {title}  (SP+ {r['ratings'][title]:+.1f}, "
          f"{r['exp_wins'][title]:.1f} projected wins)")

    frac = r["n_flips"] / r["n_games"] if r["n_games"] else 0
    print(f"\n  HONESTY LINE: of {r['n_games']} rated games, {r['n_calls']} are confident calls "
          f"and {r['n_flips']} ({frac*100:.0f}%) are coin flips.")
    print("  Sample coin-flip games the model refuses to call:")
    for wk, fav, dog, p in r["flip_examples"][:8]:
        print(f"    Wk{wk:>2}  {fav} vs {dog}   (favorite only {p*100:.0f}%)")
    print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    a = ap.parse_args()
    report(simulate(a.year))
