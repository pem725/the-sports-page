#!/usr/bin/env python3
"""Could the AL West champion finish under .500, and has that ever happened?

    python3 scripts/sub500_division.py
    python3 scripts/sub500_division.py --from 1969

THE SITUATION, 2026-09-25. Houston and Texas are both 79-80 with three games
left, they do not play each other, and neither can reach .500 without sweeping.
One of them is going to the playoffs as a division champion.

TWO QUESTIONS, AND THEY NEED DIFFERENT TOOLS. What is likely to happen is a
forecast, so it gets a simulation with the per-game probabilities written down.
Whether it has happened before is a fact, so it gets pulled from the MLB Stats
API season by season rather than recalled -- this paper published a fabricated
ranking once because a search summariser answered a question about a poll that
did not exist, and the rule since is that anything establishing a fact comes from
a primary feed.

THE HISTORICAL COMPARISON IS NOT CLEAN AND THE SCRIPT SAYS SO. Divisions began in
1969. Four seasons were shortened by labour disputes or a pandemic -- 1981, 1994,
1995, 2020 -- and a .500 record means something different across 60, 114 and 162
games. They are reported separately rather than averaged in, because a strike-year
leader at 52-62 is a different animal from a full-season club at 80-82.

WIN PROBABILITIES COME FROM LOG5, not from a hunch. Each club's season winning
percentage against its opponent's, with a small road adjustment. Both clubs
finish on the road, which is worth stating because it pushes both sweeps slightly
further out of reach.
"""
import argparse
import json
import sys
import urllib.request

API = "https://statsapi.mlb.com/api/v1"
ROAD = 0.020          # home field is worth about 4 points of win pct; both are away
SHORT = {1981: "players' strike", 1994: "strike, season ended Aug 11",
         1995: "strike-shortened, 144 games", 2020: "pandemic, 60 games"}
# The standings payload carries only a division id and a link -- no name. Two
# divisions per league until 1994, three after.
DIV = {200: "AL West", 201: "AL East", 202: "AL Central",
       203: "NL West", 204: "NL East", 205: "NL Central"}


def get(path):
    return json.load(urllib.request.urlopen(API + path, timeout=90))


def log5(pa, pb):
    """Odds team A beats team B, both of known quality."""
    d = pa + pb - 2 * pa * pb
    return (pa - pa * pb) / d if d else 0.5


def simulate(clubs, trials=200_000, seed=7):
    """clubs: list of (name, w, l, p_per_game, games_left). Returns outcome table."""
    import random
    rng = random.Random(seed)
    from collections import Counter
    champ_pct, champ_who = Counter(), Counter()
    for _ in range(trials):
        finals = []
        for name, w, l, p, g in clubs:
            add = sum(1 for _ in range(g) if rng.random() < p)
            finals.append((w + add, l + (g - add), name))
        best = max(f[0] for f in finals)
        tied = [f for f in finals if f[0] == best]
        win = tied[rng.randrange(len(tied))]        # a tiebreaker game is a coin flip
        champ_pct[win[0]] += 1
        champ_who[win[2]] += 1
    return champ_pct, champ_who, trials


def history(lo, hi):
    """Worst division winner, by season, straight from the API."""
    out = []
    for yr in range(lo, hi + 1):
        try:
            d = get(f"/standings?leagueId=103,104&season={yr}"
                    f"&standingsTypes=regularSeason&hydrate=team")
        except Exception:
            continue
        for rec in d.get("records", []):
            lead = None
            for t in rec.get("teamRecords", []):
                if t.get("divisionRank") == "1" or t.get("gamesBack") == "-":
                    lead = t
                    break
            if not lead:
                continue
            w, l = lead["wins"], lead["losses"]
            if w + l < 50:
                continue
            dv = rec.get("division", {}).get("id")
            out.append((yr, lead["team"].get("name", "?"), w, l, w / (w + l),
                        DIV.get(dv, f"div {dv}")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="lo", type=int, default=1969)
    ap.add_argument("--to", dest="hi", type=int, default=2025)
    a = ap.parse_args()

    # KEY ON TEAM ID, NOT NAME. Without hydrate=team the API returns "Astros",
    # with it "Houston Astros"; ids never move.
    st = get("/standings?leagueId=103&season=2026&standingsTypes=regularSeason&hydrate=team")
    west = next(r for r in st["records"] if r["division"]["id"] == 200)
    rows = {t["team"]["id"]: t for t in west["teamRecords"]}

    OPP = {117: 133, 140: 142}          # Houston->Athletics, Texas->Minnesota
    tw = get("/standings?leagueId=103,104&season=2026&standingsTypes=regularSeason&hydrate=team")
    allpct = {t["team"]["id"]: t["wins"] / (t["wins"] + t["losses"])
              for r in tw["records"] for t in r["teamRecords"]}
    allname = {t["team"]["id"]: t["team"]["name"]
               for r in tw["records"] for t in r["teamRecords"]}
    pct = {i: t["wins"] / (t["wins"] + t["losses"]) for i, t in rows.items()}

    clubs = []
    print("\n  THE LAST THREE GAMES\n")
    print(f"  {'club':<18}{'record':>9}{'left':>6}{'opponent':>20}{'opp pct':>9}{'p(win)':>9}")
    print("  " + "-" * 71)
    for tid, oid in OPP.items():
        t = rows[tid]
        name, opp = allname[tid], allname[oid]
        left = 162 - (t["wins"] + t["losses"])
        p = max(0.05, min(0.95, log5(pct[tid], allpct[oid]) - ROAD))
        clubs.append((name, t["wins"], t["losses"], p, left))
        print(f"  {name:<18}{t['wins']:>4}-{t['losses']:<4}{left:>6}{opp:>20}"
              f"{allpct[oid]:>9.3f}{p:>9.3f}")
    for tid, t in rows.items():
        if tid not in OPP:
            clubs.append((allname[tid], t["wins"], t["losses"], 0.45,
                          162 - (t["wins"] + t["losses"])))

    champ_pct, champ_who, n = simulate(clubs)
    print(f"\n  WHERE THE CHAMPION FINISHES  ({n:,} simulated seasons)\n")
    print(f"  {'final record':>14}{'win pct':>10}{'chance':>10}")
    print("  " + "-" * 34)
    below = at = above = 0.0
    for w in sorted(champ_pct, reverse=True):
        share = champ_pct[w] / n
        p = w / 162
        print(f"  {f'{w}-{162-w}':>14}{p:>10.3f}{share:>10.1%}")
        if p > 0.5: above += share
        elif p == 0.5: at += share
        else: below += share
    print("\n  " + "-" * 34)
    print(f"  {'above .500':>14}{above:>20.1%}")
    print(f"  {'exactly .500':>14}{at:>20.1%}")
    print(f"  {'BELOW .500':>14}{below:>20.1%}")
    print("\n  who wins it:", ", ".join(f"{k} {v/n:.0%}" for k, v in champ_who.most_common()))

    print(f"\n\n  HAS A DIVISION WINNER EVER FINISHED BELOW .500?  ({a.lo}-{a.hi})\n")
    h = history(a.lo, a.hi)
    full = [x for x in h if x[0] not in SHORT]
    short = [x for x in h if x[0] in SHORT]
    worst = sorted(full, key=lambda x: x[4])[:6]
    print(f"  {'season':>7}  {'club':<24}{'record':>9}{'pct':>8}   division")
    print("  " + "-" * 66)
    for yr, nm, w, l, p, dv in worst:
        print(f"  {yr:>7}  {nm[:23]:<24}{w:>4}-{l:<4}{p:>8.3f}   {dv}")
    sub = [x for x in full if x[4] < 0.5]
    print(f"\n  {len(full)} full-season division winners examined.")
    print(f"  finished below .500: {len(sub)}"
          + ("" if not sub else "  -> " + ", ".join(f"{x[0]} {x[1]}" for x in sub)))
    if short:
        print(f"\n  shortened seasons reported separately, not averaged in:")
        for yr, nm, w, l, p, dv in sorted(short, key=lambda x: x[4])[:4]:
            print(f"    {yr} {nm[:22]:<23}{w:>3}-{l:<3} {p:.3f}  ({SHORT[yr]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
