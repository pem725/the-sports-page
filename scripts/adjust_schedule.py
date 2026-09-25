#!/usr/bin/env python3
"""Strip the schedule out of a team's yards per play, then ask the question again.

    python3 scripts/adjust_schedule.py
    python3 scripts/adjust_schedule.py --check       # does the adjustment work?

OPEN TASK C6, and the limit that every previous piece had to declare. A unit that
improved may simply have faced worse opponents. Nothing in this paper's
offense-versus-defense work has separated those, and until it does, "the defense
got better" and "the defense played the Panthers twice" are the same number.

THE MODEL IS THE SIMPLEST ONE THAT CAN WORK. For each game, the yards per play
that team i's offense gains against team j's defense is treated as

    ypp(i attacking j) = mu + off[i] + def[j]

where mu is the league's mean, off[i] is how much better than average i's offense
is, and def[j] is how much MORE than average j's defense concedes. Solve for both
by alternating: hold the defenses fixed and average each offense over the
defenses it met, then hold the offenses fixed and do the reverse. Repeat until
nothing moves. This is the same idea as a simple rating system, applied to a rate
rather than to a margin.

WHAT IT CANNOT DO, STATED HERE BECAUSE IT WILL BE QUOTED. It has no home-field
term, it treats every game as equally informative, and it cannot see WHY a unit
was good. It assumes the schedule is the only confound worth removing, which is
false but is a great deal better than assuming there is none. With 17 games and
32 clubs the connectivity is thin; with a college season it is thinner and worse,
because whole conferences barely play each other.

THE CHECK MATTERS MORE THAN THE ADJUSTMENT. `--check` reports whether adjusted
figures predict the next season better than raw ones. If they do not, the
adjustment is decoration and should be said so rather than quietly kept.
"""
import argparse
import collections
import csv
import pathlib
import statistics
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
NFL = REPO / "data" / "nfl" / "team-games.csv"


def games(metric="ypp"):
    """(season, team, opponent, offensive value in that game)."""
    rows = list(csv.DictReader(open(NFL)))
    if metric == "ypp":
        val = {}
        for r in rows:
            pl = float(r["plays"] or 0)
            if pl >= 20:
                val[(r["game_id"], r["team"])] = float(r["yards"]) / pl
    else:
        val = {(r["game_id"], r["team"]): float(r["points_for"]) for r in rows}
    out = []
    for r in rows:
        v = val.get((r["game_id"], r["team"]))
        if v is not None and (r["game_id"], r["opp"]) in val:
            out.append((int(r["season"]), r["team"], r["opp"], v))
    return out


def solve(season_games, iters=200, tol=1e-9):
    """Alternating least squares for ypp = mu + off[i] + def[j]."""
    teams = sorted({g[0] for g in season_games} | {g[1] for g in season_games})
    mu = statistics.mean(g[2] for g in season_games)
    off = dict.fromkeys(teams, 0.0)
    dfn = dict.fromkeys(teams, 0.0)
    byoff = collections.defaultdict(list)
    bydef = collections.defaultdict(list)
    for i, j, v in season_games:
        byoff[i].append((j, v))
        bydef[j].append((i, v))
    for _ in range(iters):
        move = 0.0
        for i in teams:
            if byoff[i]:
                new = statistics.mean(v - mu - dfn[j] for j, v in byoff[i])
                move = max(move, abs(new - off[i])); off[i] = new
        # centre so the two halves cannot drift apart together
        m = statistics.mean(off.values())
        for i in teams: off[i] -= m
        for j in teams:
            if bydef[j]:
                new = statistics.mean(v - mu - off[i] for i, v in bydef[j])
                move = max(move, abs(new - dfn[j])); dfn[j] = new
        m = statistics.mean(dfn.values())
        for j in teams: dfn[j] -= m
        if move < tol:
            break
    return mu, off, dfn


def build(metric="ypp"):
    """{(season, team): (raw_off, raw_def, adj_off, adj_def)} -- higher is better on all four."""
    g = games(metric)
    by = collections.defaultdict(list)
    for s, t, o, v in g:
        by[s].append((t, o, v))
    out = {}
    for s, gs in by.items():
        mu, off, dfn = solve(gs)
        ro = collections.defaultdict(list); rd = collections.defaultdict(list)
        for t, o, v in gs:
            ro[t].append(v); rd[o].append(v)
        for t in off:
            if len(ro[t]) >= 8:
                out[(s, t)] = (statistics.mean(ro[t]), -statistics.mean(rd[t]),
                               off[t], -dfn[t])
    return out


def z(d, idx):
    """Standardise one column within each season."""
    bys = collections.defaultdict(dict)
    for (s, t), v in d.items():
        bys[s][t] = v[idx]
    out = {}
    for s, ts in bys.items():
        m, sd = statistics.mean(ts.values()), statistics.pstdev(ts.values())
        for t, v in ts.items():
            out[(s, t)] = (v - m) / sd
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--metric", default="ypp", choices=["ypp", "points"])
    a = ap.parse_args()
    d = build(a.metric)
    print(f"\n  {len(d):,} team-seasons, {a.metric}\n")

    cols = {"raw offense": 0, "raw defense": 1, "adjusted offense": 2, "adjusted defense": 3}
    Z = {k: z(d, i) for k, i in cols.items()}

    print("  HOW MUCH DID THE ADJUSTMENT MOVE ANYBODY?\n")
    for a_, b_ in (("raw offense", "adjusted offense"), ("raw defense", "adjusted defense")):
        ks = [k for k in Z[a_] if k in Z[b_]]
        r = statistics.correlation([Z[a_][k] for k in ks], [Z[b_][k] for k in ks])
        shift = [abs(Z[a_][k] - Z[b_][k]) for k in ks]
        print(f"  {a_:<18} vs {b_:<20} r={r:.3f}   median move "
              f"{statistics.median(shift):.2f} SD   worst {max(shift):.2f} SD")

    print("\n  DOES IT PREDICT NEXT SEASON ANY BETTER?\n")
    print(f"  {'':<20}{'raw':>9}{'adjusted':>11}{'change':>9}")
    print("  " + "-" * 50)
    for side, rawk, adjk in (("offense", "raw offense", "adjusted offense"),
                             ("defense", "raw defense", "adjusted defense")):
        pr = [(Z[rawk][(s, t)], Z[rawk][(s + 1, t)]) for (s, t) in Z[rawk] if (s + 1, t) in Z[rawk]]
        pa = [(Z[adjk][(s, t)], Z[adjk][(s + 1, t)]) for (s, t) in Z[adjk] if (s + 1, t) in Z[adjk]]
        rr = statistics.correlation([x for x, _ in pr], [y for _, y in pr])
        ra = statistics.correlation([x for x, _ in pa], [y for _, y in pa])
        print(f"  {side + ' persists':<20}{rr:>9.3f}{ra:>11.3f}{ra - rr:>+9.3f}")
    # cross-predict: does ADJUSTED this year beat RAW this year at predicting RAW next year?
    print()
    for side, rawk, adjk in (("offense", "raw offense", "adjusted offense"),
                             ("defense", "raw defense", "adjusted defense")):
        ks = [(s, t) for (s, t) in Z[rawk] if (s + 1, t) in Z[rawk] and (s, t) in Z[adjk]]
        rr = statistics.correlation([Z[rawk][k] for k in ks], [Z[rawk][(k[0] + 1, k[1])] for k in ks])
        ra = statistics.correlation([Z[adjk][k] for k in ks], [Z[rawk][(k[0] + 1, k[1])] for k in ks])
        print(f"  predicting next year's RAW {side:<8} from raw {rr:.3f}, from adjusted {ra:.3f}"
              f"  ({ra - rr:+.3f})")
    print("\n  If the adjusted column does not beat the raw one, the adjustment is")
    print("  decoration. Say so rather than keeping it because it sounds rigorous.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
