#!/usr/bin/env python3
"""Rank the statistics a booth cites by whether any of them predict anything.

    python3 scripts/rank_broadcast_stats.py
    python3 scripts/rank_broadcast_stats.py --split 9

TIM'S IDEA, and the right one: a viewer is handed nine or ten numbers a game with
no indication of which carry information. Third down percentage, time of
possession, total yards, penalties, first downs. Nobody ever sorts them. This
sorts them.

THE TEST, and the design is the whole point. Every statistic is measured over the
FIRST half of a team's season and scored against its win rate in the SECOND half
-- games the statistic has never seen. Out of sample by construction, not by
promise. A statistic tested against the games it was computed from will look
magnificent and mean nothing; this paper published a 15-for-15 backtest that
failed exactly that way.

TWO COLUMNS, AND THE SECOND ONE MATTERS MORE.

  on its own     how well the statistic alone predicts the second half
  once you       the same thing after the POINT MARGIN is accounted for
  know the score

Almost everything in a box score correlates with winning, because winning teams
do everything well. The honest question is not "does it correlate" but "does it
add anything you did not already have from the scoreboard". Time of possession
scores +0.216 alone and -0.003 once the margin is known: it was the scoreboard in
a hat.

EVERY STATISTIC IS A MARGIN, own minus opponent. A team's raw third down rate is
partly a statement about the defences it faced; the difference removes most of
that. It is also how a broadcast implicitly frames them anyway -- the graphic
always shows both teams.

THE BASELINE IS THE POINT. First-half WIN RATE is free, needs no box score, and
any statistic that cannot beat it is not earning its place on the screen.
"""
import argparse
import collections
import csv
import math
import pathlib
import statistics
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
BASIC = REPO / "data" / "nfl" / "team-games.csv"
BCAST = REPO / "data" / "nfl" / "broadcast-stats.csv"


def corr(pairs):
    if len(pairs) < 20:
        return None
    xs = [a for a, _ in pairs]; ys = [b for _, b in pairs]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    if not den:
        return None
    r = num / den; n = len(pairs)
    return r, n, (r * math.sqrt(n - 2) / math.sqrt(1 - r * r) if abs(r) < 1 else float("nan"))


def rate(a, b):
    return (a / b) if b else None


def load():
    if not BASIC.exists() or not BCAST.exists():
        raise SystemExit("run build_nfl_history.py and build_nfl_broadcast_stats.py first")
    basic = {(r["game_id"], r["team"]): r for r in csv.DictReader(open(BASIC))}
    bc = {(r["game_id"], r["team"]): r for r in csv.DictReader(open(BCAST))}
    by_game = collections.defaultdict(list)
    for k in basic:
        by_game[k[0]].append(k[1])

    out = []
    for gid, teams in by_game.items():
        if len(teams) != 2:
            continue
        for me, you in ((teams[0], teams[1]), (teams[1], teams[0])):
            a, b = basic.get((gid, me)), basic.get((gid, you))
            ax, bx = bc.get((gid, me)), bc.get((gid, you))
            if not all((a, b, ax, bx)):
                continue
            pa, pb = int(a["plays"]), int(b["plays"])
            if not pa or not pb:
                continue
            f = lambda d, k: int(d[k])
            row = dict(season=int(a["season"]), week=int(a["week"]), team=me,
                       win=int(a["win"]),
                       pt_margin=int(a["points_for"]) - int(a["points_against"]))
            row["yards_per_play"] = float(a["yards"]) / pa - float(b["yards"]) / pb
            row["total_yards"] = float(a["yards"]) - float(b["yards"])
            row["possession"] = (int(a["top_seconds"]) - int(b["top_seconds"])) / 60
            row["turnover_margin"] = int(b["turnovers"]) - int(a["turnovers"])
            row["first_downs"] = f(ax, "first_downs") - f(bx, "first_downs")
            row["penalties"] = f(bx, "penalties") - f(ax, "penalties")          # fewer is better
            row["penalty_yards"] = f(bx, "penalty_yards") - f(ax, "penalty_yards")
            row["sacks"] = f(ax, "sacks_made") - f(ax, "sacks_taken")
            row["explosive_plays"] = f(ax, "explosive") - f(bx, "explosive")
            row["rush_yards"] = f(ax, "rush_yards") - f(bx, "rush_yards")
            row["pass_yards"] = f(ax, "pass_yards") - f(bx, "pass_yards")
            t3a, t3b = rate(f(ax, "third_conv"), f(ax, "third_att")), rate(f(bx, "third_conv"), f(bx, "third_att"))
            row["third_down_pct"] = (t3a - t3b) if (t3a is not None and t3b is not None) else None
            rza, rzb = rate(f(ax, "rz_td"), f(ax, "rz_trips")), rate(f(bx, "rz_td"), f(bx, "rz_trips"))
            row["red_zone_pct"] = (rza - rzb) if (rza is not None and rzb is not None) else None
            ca, cb = rate(f(ax, "completions"), f(ax, "pass_att")), rate(f(bx, "completions"), f(bx, "pass_att"))
            row["completion_pct"] = (ca - cb) if (ca is not None and cb is not None) else None
            out.append(row)
    return out


LABELS = [
    ("win", "first-half win rate", "free -- the baseline to beat"),
    ("pt_margin", "point margin", "the scoreboard, averaged"),
    ("yards_per_play", "yards per play", "efficiency"),
    ("explosive_plays", "explosive plays (20+ yds)", "the analytics favourite"),
    ("total_yards", "total yards", "the oldest graphic there is"),
    ("first_downs", "first downs", "the classic 'who is winning'"),
    ("turnover_margin", "turnover margin", "the coach's cliche"),
    ("third_down_pct", "third down percentage", "the most-cited rate on TV"),
    ("possession", "time of possession", "on screen every week"),
    ("red_zone_pct", "red zone touchdown rate", "the 'finishing drives' number"),
    ("pass_yards", "passing yards", "the halftime lead"),
    ("rush_yards", "rushing yards", "'establishing the run'"),
    ("completion_pct", "completion percentage", "the quarterback number"),
    ("sacks", "sack margin", "the pressure narrative"),
    ("penalties", "penalty margin (fewer better)", "the discipline story"),
    ("penalty_yards", "penalty yards (fewer better)", "the discipline story"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=int, default=9)
    ap.add_argument("--min-games", type=int, default=6)
    a = ap.parse_args()

    rows = load()
    by = collections.defaultdict(list)
    for r in rows:
        by[(r["season"], r["team"])].append(r)

    data = []
    for _, gs in by.items():
        first = [g for g in gs if g["week"] < a.split]
        second = [g for g in gs if g["week"] >= a.split]
        if len(first) < a.min_games or len(second) < a.min_games:
            continue
        rec = {"y": statistics.mean(g["win"] for g in second)}
        for key, _, _ in LABELS:
            vals = [g[key] for g in first if g.get(key) is not None]
            rec[key] = statistics.mean(vals) if vals else None
        data.append(rec)

    print(f"\n  {len(rows)} team-games, {len(data)} team-seasons. "
          f"First half measured against second-half win rate -- out of sample by construction.\n")
    print(f"  {'statistic':<32}{'on its own':>12}{'once you know':>15}{'verdict'}")
    print(f"  {'':<32}{'':>12}{'the score':>15}")
    print(f"  {'-'*32}{'-'*12}{'-'*15}   {'-'*26}")

    base = [(d["pt_margin"], d["y"]) for d in data if d["pt_margin"] is not None]
    r_base = corr(base)[0]
    out = []
    for key, label, note in LABELS:
        pairs = [(d[key], d["y"]) for d in data if d.get(key) is not None]
        c = corr(pairs)
        if not c:
            continue
        r, n, t = c
        if key == "pt_margin":
            partial = None
        else:
            both = [(d[key], d["pt_margin"], d["y"]) for d in data
                    if d.get(key) is not None and d["pt_margin"] is not None]
            rzy = corr([(x[0], x[2]) for x in both])[0]
            rzx = corr([(x[0], x[1]) for x in both])[0]
            rxy = corr([(x[1], x[2]) for x in both])[0]
            den = math.sqrt((1 - rzx ** 2) * (1 - rxy ** 2))
            partial = (rzy - rzx * rxy) / den if den else float("nan")
        if partial is None:
            verdict = "the scoreboard itself"
        elif abs(partial) < 0.05:
            verdict = "adds NOTHING"
        elif abs(partial) < 0.12:
            verdict = "adds a little"
        else:
            verdict = "adds real signal"
        out.append((abs(partial) if partial is not None else 9, label, r, partial, verdict, note))

    for _, label, r, partial, verdict, note in sorted(out, reverse=True):
        p = f"{partial:+.3f}" if partial is not None else "   --"
        print(f"  {label:<32}{r:>+12.3f}{p:>15}   {verdict}")
    print(f"\n  Baseline: point margin alone predicts the second half at r = {r_base:+.3f}.")
    print("  Anything that adds nothing beyond it is decoration, however often it is shown.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
