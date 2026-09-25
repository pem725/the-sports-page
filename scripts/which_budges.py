#!/usr/bin/env python3
"""You take over a franchise. Do you fix the offense or the defense?

    python3 scripts/which_budges.py
    python3 scripts/which_budges.py --cfb          # college, from CFBD
    python3 scripts/which_budges.py --both

THE EDITOR'S QUESTION, 2026-09-25, and it only becomes askable once the previous
one is settled. Because P(win | allowed x) is exactly 1 - P(win | scored x), the
two curves have identical slopes everywhere. A point of offense and a point of
defense are worth the same in win probability, always, by construction, in any
league. There is nothing left to measure there.

Which leaves the question that actually matters to somebody running a club:
**not which is worth more, but which one moves.** "I take over a franchise. Do I
make it a better offense or a better defense?"

THREE MEASUREMENTS, IN ORDER, BECAUSE THE THIRD IS MEANINGLESS WITHOUT THE FIRST
TWO:

  SPREAD     How far apart are clubs on each side of the ball? Reported as the
             between-team standard deviation within a season, so "one standard
             deviation" means the same distance on both sides.
  NOISE      How much does one team bounce around week to week? A side that
             swings wildly from Sunday to Sunday is measured badly, and a badly
             measured side will LOOK more changeable year over year without
             actually being it.
  MOVEMENT   Year-over-year change in standardized units, and the directional
             version the editor asked for: is gaining a standard deviation on
             offense easier than shedding one on defense?

THE TRAP, AND IT IS THE WHOLE ANALYSIS. Regression to the mean guarantees that a
club at the bottom improves and a club at the top declines, on either side of the
ball, without anybody doing anything. Comparing raw improvement rates would just
rediscover that. So every movement figure here is reported CONDITIONAL ON WHERE
THE CLUB STARTED -- matched starting deciles, offense against defense. Anything
else is measuring the starting point.
"""
import argparse
import collections
import csv
import json
import math
import os
import pathlib
import re
import statistics
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
NFL = REPO / "data" / "nfl" / "team-games.csv"
CFB_CACHE = REPO / "data" / "cfb-team-games.csv"


def cfbd_key():
    p = pathlib.Path.home() / ".config/secrets/tokens.env"
    if p.exists():
        for ln in p.read_text().splitlines():
            m = re.match(r"\s*(?:export\s+)?CFBD_KEY\s*=\s*(.*)$", ln)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    return os.environ.get("CFBD_KEY")


def load_nfl(metric="points"):
    """(season, team, week, offense_value, defense_value).

    For yards per play the defensive figure is the OPPONENT'S offense in the same
    game, joined on game_id -- there is no separate 'yards allowed' column and
    inventing one from the team's own row would silently measure the wrong thing.
    """
    rows = list(csv.DictReader(open(NFL)))
    if metric == "points":
        return [(int(r["season"]), r["team"], int(r["week"]),
                 int(r["points_for"]), int(r["points_against"])) for r in rows]
    off = {}
    for r in rows:
        pl = float(r["plays"] or 0)
        if pl >= 20:
            off[(r["game_id"], r["team"])] = float(r["yards"]) / pl
    out = []
    for r in rows:
        a = off.get((r["game_id"], r["team"]))
        b = off.get((r["game_id"], r["opp"]))
        if a is None or b is None:
            continue
        out.append((int(r["season"]), r["team"], int(r["week"]), a, b))
    return out


def load_cfb(lo=2005, hi=2025):
    if CFB_CACHE.exists():
        return [(int(r["season"]), r["team"], int(r["week"]),
                 int(r["pf"]), int(r["pa"])) for r in csv.DictReader(open(CFB_CACHE))]
    key = cfbd_key()
    if not key:
        raise SystemExit("CFBD_KEY not available")
    rows = []
    for yr in range(lo, hi + 1):
        req = urllib.request.Request(
            f"https://api.collegefootballdata.com/games?year={yr}&seasonType=regular"
            f"&classification=fbs", headers={"Authorization": f"Bearer {key}"})
        for g in json.load(urllib.request.urlopen(req, timeout=120)):
            hp, ap = g.get("homePoints"), g.get("awayPoints")
            if hp is None or ap is None:
                continue
            wk = g.get("week") or 0
            rows.append((yr, g["homeTeam"], wk, hp, ap))
            rows.append((yr, g["awayTeam"], wk, ap, hp))
        print(f"    {yr}: {len(rows):,} team-games so far", flush=True)
    CFB_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(CFB_CACHE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["season", "team", "week", "pf", "pa"])
        w.writerows(rows)
    return rows


def analyse(rows, label, min_games=8):
    print(f"\n{'='*74}\n  {label}\n{'='*74}")
    by = collections.defaultdict(list)
    for s, t, w, pf, pa in rows:
        by[(s, t)].append((pf, pa))
    seasons = collections.defaultdict(dict)
    within_o, within_d = [], []
    for (s, t), g in by.items():
        if len(g) < min_games:
            continue
        o = statistics.mean(x[0] for x in g)
        d = statistics.mean(x[1] for x in g)
        seasons[s][t] = (o, d)
        if len(g) >= 6:
            within_o.append(statistics.pstdev(x[0] for x in g))
            within_d.append(statistics.pstdev(x[1] for x in g))

    # ---- SPREAD and NOISE ----
    bo = [statistics.pstdev([v[0] for v in ts.values()]) for ts in seasons.values() if len(ts) > 8]
    bd = [statistics.pstdev([v[1] for v in ts.values()]) for ts in seasons.values() if len(ts) > 8]
    mo = statistics.mean([v[0] for ts in seasons.values() for v in ts.values()])
    print(f"\n  {len(seasons)} seasons, {sum(len(t) for t in seasons.values()):,} team-seasons"
          f", league mean {mo:.2f}\n")
    print(f"  {'':<22}{'offense':>12}{'defense':>12}")
    print("  " + "-" * 46)
    print(f"  {'between clubs (SD)':<22}{statistics.mean(bo):>12.2f}{statistics.mean(bd):>12.2f}")
    print(f"  {'week to week (SD)':<22}{statistics.mean(within_o):>12.2f}{statistics.mean(within_d):>12.2f}")
    print(f"  {'noise / spread':<22}{statistics.mean(within_o)/statistics.mean(bo):>12.2f}"
          f"{statistics.mean(within_d)/statistics.mean(bd):>12.2f}")
    print("\n  A higher noise-to-spread ratio means the side is measured worse, and a side")
    print("  measured worse will LOOK more changeable without being it.")

    # ---- standardise within season; defense flipped so + is always better ----
    z = {}
    for s, ts in seasons.items():
        if len(ts) < 9:
            continue
        os_, ds_ = [v[0] for v in ts.values()], [v[1] for v in ts.values()]
        mo_, so_ = statistics.mean(os_), statistics.pstdev(os_)
        md_, sd_ = statistics.mean(ds_), statistics.pstdev(ds_)
        for t, (o, d) in ts.items():
            z[(s, t)] = ((o - mo_) / so_, -(d - md_) / sd_)

    pairs = [(z[(s, t)], z[(s + 1, t)]) for (s, t) in z if (s + 1, t) in z]
    if len(pairs) < 50:
        print("\n  too few consecutive-season pairs to go further")
        return
    do = [b[0] - a[0] for a, b in pairs]
    dd = [b[1] - a[1] for a, b in pairs]
    print(f"\n  MOVEMENT, {len(pairs):,} consecutive-season pairs\n")
    print(f"  {'':<26}{'offense':>12}{'defense':>12}")
    print("  " + "-" * 50)
    print(f"  {'year-over-year r':<26}{statistics.correlation([a[0] for a,_ in pairs],[b[0] for _,b in pairs]):>12.3f}"
          f"{statistics.correlation([a[1] for a,_ in pairs],[b[1] for _,b in pairs]):>12.3f}")
    print(f"  {'SD of the change':<26}{statistics.pstdev(do):>12.2f}{statistics.pstdev(dd):>12.2f}")
    print(f"  {'moved up a full SD':<26}{sum(1 for x in do if x>=1)/len(do):>11.1%}"
          f"{sum(1 for x in dd if x>=1)/len(dd):>11.1%}")
    print(f"  {'fell a full SD':<26}{sum(1 for x in do if x<=-1)/len(do):>11.1%}"
          f"{sum(1 for x in dd if x<=-1)/len(dd):>11.1%}")

    # ---- RELIABILITY, so the banding can be corrected ----
    # A side measured with more noise produces more APPARENT regression to the
    # mean: its extreme observed values are more often flukes, so they bounce
    # back harder without anything real having changed. Defense is measured worse
    # than offense here, so banding on the raw z would hand defense a spurious
    # advantage in any "who improves more" comparison.
    #
    # Split-half within season (odd games vs even), stepped up with
    # Spearman-Brown, then shrink each observed z toward zero by that
    # reliability. The shrunken value is the best estimate of where the club
    # TRULY was, and banding on it compares like with like.
    ha, hb, hc, hd = [], [], [], []
    for (s, t_), g in by.items():
        if len(g) < 12 or (s, t_) not in z:
            continue
        odd, even = g[1::2], g[0::2]
        if min(len(odd), len(even)) < 5:
            continue
        ha.append(statistics.mean(x[0] for x in odd)); hb.append(statistics.mean(x[0] for x in even))
        hc.append(statistics.mean(x[1] for x in odd)); hd.append(statistics.mean(x[1] for x in even))
    sb = lambda r: 2 * r / (1 + r)
    rel_o = sb(statistics.correlation(ha, hb))
    rel_d = sb(statistics.correlation(hc, hd))
    print(f"\n  measurement reliability of a full season: "
          f"offense {rel_o:.2f}, defense {rel_d:.2f}")
    print(f"  disattenuated year-over-year r: "
          f"offense {statistics.correlation([a[0] for a,_ in pairs],[b[0] for _,b in pairs])/rel_o:.3f}, "
          f"defense {statistics.correlation([a[1] for a,_ in pairs],[b[1] for _,b in pairs])/rel_d:.3f}")

    # ---- the editor's question, with the banding decoupled from the change ----
    # FIRST ATTEMPT WAS WRONG AND IS WORTH RECORDING. Banding on season t and
    # measuring the change out of season t means the same measurement error sets
    # both the group and the starting point: a club that looks terrible partly by
    # luck is placed in the bottom band AND has an artificially low baseline to
    # rebound from. Shrinking the banding variable made it worse, not better,
    # because the shrunk band no longer matched the unshrunk baseline.
    #
    # The fix is to band on a DIFFERENT SEASON from the one the change is measured
    # over. Group on season t-1; measure the move from season t to t+1. The two
    # share no measurement error, so whatever gap survives is not regression.
    bands = [(-9, -1), (-1, -0.33), (-0.33, 0.33), (0.33, 1), (1, 9)]
    trip = []
    for (s, t_) in z:
        if (s + 1, t_) in z and (s + 2, t_) in z:
            trip.append((z[(s, t_)], z[(s + 1, t_)], z[(s + 2, t_)]))
    print(f"\n  GAINING A STANDARD DEVIATION, BY WHERE YOU STOOD THE YEAR BEFORE")
    print(f"  ({len(trip):,} clubs with three straight seasons; grouped on the first,")
    print(f"   change measured between the second and third)\n")
    print(f"  {'group, year t-1':<18}{'n off':>7}{'n def':>7}{'offense +1SD':>15}{'defense +1SD':>15}{'gap':>9}")
    print("  " + "-" * 71)
    for lo, hi in bands:
        so = [c[0] - b[0] for a, b, c in trip if lo <= a[0] < hi]
        sd_ = [c[1] - b[1] for a, b, c in trip if lo <= a[1] < hi]
        if len(so) < 25 or len(sd_) < 25:
            continue
        po = sum(1 for x in so if x >= 1) / len(so)
        pd = sum(1 for x in sd_ if x >= 1) / len(sd_)
        lab = f"{lo:+.2f} to {hi:+.2f}".replace("-9.00", " worst").replace("+9.00", " best")
        print(f"  {lab:<18}{len(so):>7}{len(sd_):>7}{po:>14.1%}{pd:>15.1%}{po-pd:>+9.1%}")
    allo = [c[0] - b[0] for a, b, c in trip]
    alld = [c[1] - b[1] for a, b, c in trip]
    print(f"  {'every club':<18}{len(allo):>7}{len(alld):>7}"
          f"{sum(1 for x in allo if x>=1)/len(allo):>14.1%}"
          f"{sum(1 for x in alld if x>=1)/len(alld):>15.1%}"
          f"{sum(1 for x in allo if x>=1)/len(allo)-sum(1 for x in alld if x>=1)/len(alld):>+9.1%}")
    print("\n  Positive gap = the offense was likelier to gain a standard deviation than")
    print("  the defense was, among clubs that started in the same place.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cfb", action="store_true")
    ap.add_argument("--both", action="store_true")
    ap.add_argument("--metric", choices=["points", "ypp"], default="points")
    a = ap.parse_args()
    if a.both or not a.cfb:
        unit = "points scored and allowed" if a.metric == "points" else "yards per play, gained and allowed"
        analyse(load_nfl(a.metric), f"NFL, 1999-2025 — {unit}")
    if a.both or a.cfb:
        analyse(load_cfb(), "COLLEGE FOOTBALL (FBS), 2005-2025", min_games=8)
    return 0


if __name__ == "__main__":
    sys.exit(main())
