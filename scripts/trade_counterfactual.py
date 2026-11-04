#!/usr/bin/env python3
"""What did the Bears give up for Jeffery Simmons? The counterfactual, by season.

Two sides, one unit. A STARTER SEASON is 8+ regular-season games playing at
least half of his unit's snaps (nflverse snap counts, 2013 on).

  Simmons side: interior defensive linemen who, THROUGH AGE 28, looked like
    him -- 25 to 60 career sacks and a full season (10+ games) at 28 -- and
    what they did from 29 on. Comps are chosen only on what was known at 28.
    Choosing them by CAREER Pro Bowls instead keeps only the ones who lasted
    (the career is the filter), and that biased version is printed too, as the
    warning it is.

  Pick side: first-round picks 17-32 (where a winning team picks), drafted
    2013-2018, and how often each was a starter in years 1..8.

Inputs: data/draft_picks.csv (in repo) plus nflverse season stats, snap counts
and the players table, cached under ~/.cache/sports-page/nflverse.
Output: data/trades/simmons_counterfactual.txt
"""
import collections, csv, gzip, pathlib, urllib.request
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = pathlib.Path.home() / ".cache/sports-page/nflverse"
REL = "https://github.com/nflverse/nflverse-data/releases/download"
SIMMONS = ("00-0035643", "SimmJe01", 1997)
OUT = ROOT / "data/trades/simmons_counterfactual.txt"


def fetch(name, url):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / name
    if not p.exists():
        urllib.request.urlretrieve(url, p)
    return p


def rows_gz(p):
    try:
        yield from csv.DictReader(gzip.open(p, "rt"))
    except EOFError:  # a truncated upstream file (2012 snaps) is skipped, not half-read
        return


def main():
    lines = []
    say = lambda s="": (print(s), lines.append(s))

    players = {r["gsis_id"]: r for r in csv.DictReader(open(fetch("players.csv", f"{REL}/players/players.csv")))}

    starts = collections.defaultdict(collections.Counter)
    for y in range(2013, 2026):
        for r in rows_gz(fetch(f"snaps_{y}.csv.gz", f"{REL}/snap_counts/snap_counts_{y}.csv.gz")):
            if r["game_type"] == "REG" and max(float(r["offense_pct"] or 0), float(r["defense_pct"] or 0)) >= 0.5:
                starts[r["pfr_player_id"]][y] += 1
    starter = lambda pfr, y: starts[pfr][y] >= 8

    sacks, games = collections.defaultdict(dict), collections.defaultdict(dict)
    for y in range(1999, 2026):
        for r in rows_gz(fetch(f"reg_{y}.csv.gz", f"{REL}/stats_player/stats_player_reg_{y}.csv.gz")):
            if r["position_group"] == "DL":
                sacks[r["player_id"]][y] = float(r["def_sacks"] or 0)
                games[r["player_id"]][y] = int(r["games"] or 0)

    gid, pfr, born = SIMMONS
    say(f"Simmons through age 28 (2025): {sum(v for y, v in sacks[gid].items() if y <= born + 28):g} sacks; "
        f"starter seasons 2019-25: {[int(starter(pfr, y)) for y in range(2019, 2026)]}")

    # -- Simmons side: comps chosen on what was known at 28
    comps = []
    for p_id, ss in sacks.items():
        p = players.get(p_id)
        if not p or not p.get("birth_date") or p.get("position") not in ("DT", "NT", "DL"):
            continue
        b = int(p["birth_date"][:4])
        if not (1984 <= b <= 1993) or games[p_id].get(b + 28, 0) < 10:  # 29-32 all inside snap years
            continue
        cum = sum(v for y, v in ss.items() if y <= b + 28)
        if 25 <= cum <= 60:
            comps.append((p["display_name"], [starter(p.get("pfr_id"), b + a) for a in range(29, 33)]))
    A = np.array([c[1] for c in comps])
    say(f"\nSIMMONS SIDE: {len(comps)} interior linemen like him at 28 (born 1984-93)")
    say(f"  starter at age 29..32: {A.mean(0).round(2).tolist()}")
    say(f"  starter seasons, ages 29-32: mean {A.sum(1).mean():.1f}; one or none: {np.mean(A.sum(1) <= 1):.0%}")
    for name, s in sorted(comps, key=lambda c: -sum(c[1])):
        say(f"    {name:22s} {[int(x) for x in s]}")

    # -- the biased version, kept as the warning
    D = list(csv.DictReader(open(ROOT / "data/draft_picks.csv")))
    stars = [r for r in D if r["position"] in ("DT", "DE", "NT", "DL") and r["round"] == "1"
             and float(r["probowls"] or 0) >= 4 and 1980 <= int(r["season"]) <= 2012 and r["age"] and r["to"]]
    last_age = np.array([float(r["age"]) + int(r["to"]) - int(r["season"]) for r in stars])
    say(f"\nBIASED (comps chosen by CAREER Pro Bowls, 4+): n={len(stars)}, median last season at age "
        f"{np.median(last_age):g}, done by 30: {np.mean(last_age <= 30):.0%}  <- the career is the filter")

    # -- pick side
    say("\nPICK SIDE: first-round picks 17-32, drafted 2013-2018")
    sel = [r for r in D if r["round"] == "1" and 17 <= int(r["pick"]) <= 32 and 2013 <= int(r["season"]) <= 2018]
    by_year = [np.mean([starter(r["pfr_player_id"], int(r["season"]) + k) for r in sel]) for k in range(8)]
    tot7 = np.array([sum(starter(r["pfr_player_id"], int(r["season"]) + k) for k in range(7)) for r in sel])
    say(f"  n={len(sel)}; starter in year 1..8: {np.round(by_year, 2).tolist()}")
    say(f"  starter seasons in first 7 years: mean {tot7.mean():.1f}; one or none: {np.mean(tot7 <= 1):.0%}")
    old = [r for r in D if r["round"] == "1" and 17 <= int(r["pick"]) <= 32 and 1990 <= int(r["season"]) <= 2017]
    pb = np.mean([float(r["probowls"] or 0) > 0 for r in old])
    say(f"  ever a Pro Bowl (1990-2017 picks, n={len(old)}): {pb:.0%}; at least one of two: {1 - (1 - pb) ** 2:.0%}")

    # -- the timeline: expected starters per season
    say("\nTIMELINE, expected starter seasons")
    say("  season  Simmons  two picks")
    simm = dict(zip(range(2026, 2030), A.mean(0)))
    for s in range(2026, 2035):
        picks = sum(by_year[s - d] for d in (2027, 2028) if 0 <= s - d < 8)
        say(f"  {s}    {simm.get(s, float('nan')):5.2f}    {picks:5.2f}")
    thru = lambda last: sum(by_year[s - d] for d in (2027, 2028) for s in range(d, last + 1) if s - d < 8)
    say(f"  through 2029: Simmons {A.mean(0).sum():.1f}, picks {thru(2029):.1f}; through 2034 picks {thru(2034):.1f}")

    OUT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
