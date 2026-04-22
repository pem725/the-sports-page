#!/usr/bin/env python3
"""
Build the CFB ranked-matchup dataset for JND analysis.

For every FBS regular-season + bowl game in which BOTH teams were in the AP
Top 25 in the poll released for the week of the game, record:
  year, week, home_team, away_team, home_rank, away_rank, winner, loser,
  winner_rank, loser_rank, rank_delta (= |home_rank - away_rank|),
  higher_rank_won (bool), home_score, away_score, is_neutral.

Usage:
  CFBD_KEY=... python3 scripts/build_cfb_jnd_dataset.py
"""
import csv
import json
import os
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict

API = "https://apinext.collegefootballdata.com"
KEY = os.environ.get("CFBD_KEY")
if not KEY:
    print("ERROR: set CFBD_KEY env var", file=sys.stderr)
    sys.exit(1)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = os.path.join(REPO, "scripts", "data", "cfb-ranked-matchups.csv")

YEARS = list(range(1995, 2025))  # 30 seasons


def fetch(path):
    req = urllib.request.Request(
        API + path,
        headers={"Authorization": f"Bearer {KEY}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def build_ap_map(year):
    """Return {(week, team_name): rank} for AP Top 25, regular + postseason."""
    m = {}
    for st in ("regular", "postseason"):
        try:
            polls = fetch(f"/rankings?year={year}&seasonType={st}")
        except urllib.error.HTTPError as e:
            print(f"  rankings {year}/{st}: HTTP {e.code}", file=sys.stderr)
            continue
        for entry in polls:
            wk = entry.get("week")
            season_type = entry.get("seasonType", st)
            for poll in entry.get("polls", []):
                if poll.get("poll") != "AP Top 25":
                    continue
                for r in poll.get("ranks", []):
                    m[(season_type, wk, r["school"])] = r["rank"]
    return m


def fetch_games(year, season_type):
    try:
        return fetch(f"/games?year={year}&seasonType={season_type}")
    except urllib.error.HTTPError as e:
        print(f"  games {year}/{season_type}: HTTP {e.code}", file=sys.stderr)
        return []


def main():
    rows = []
    for year in YEARS:
        print(f"Fetching {year}...", file=sys.stderr)
        ap = build_ap_map(year)
        for st in ("regular", "postseason"):
            games = fetch_games(year, st)
            for g in games:
                hw = g.get("week")
                ht = g.get("homeTeam")
                at = g.get("awayTeam")
                if not (ht and at and hw is not None):
                    continue
                hr = ap.get((st, hw, ht))
                ar = ap.get((st, hw, at))
                if hr is None or ar is None:
                    continue  # need BOTH ranked
                hp = g.get("homePoints")
                ap_ = g.get("awayPoints")
                if hp is None or ap_ is None:
                    continue  # unplayed / canceled
                home_won = hp > ap_
                winner = ht if home_won else at
                loser  = at if home_won else ht
                wr = hr if home_won else ar
                lr = ar if home_won else hr
                delta = abs(hr - ar)
                higher_rank_won = wr < lr  # lower rank number = higher rank
                rows.append({
                    "year": year, "season_type": st, "week": hw,
                    "home_team": ht, "away_team": at,
                    "home_rank": hr, "away_rank": ar,
                    "home_score": hp, "away_score": ap_,
                    "winner": winner, "loser": loser,
                    "winner_rank": wr, "loser_rank": lr,
                    "rank_delta": delta,
                    "higher_rank_won": higher_rank_won,
                    "neutral_site": bool(g.get("neutralSite")),
                })
        time.sleep(0.2)

    # Write CSV
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"\nWrote {len(rows)} ranked-vs-ranked games to {OUT_CSV}\n")

    # Summary: win rate by rank-delta bucket
    buckets = [
        ("1-2",   1,  2),
        ("3-5",   3,  5),
        ("6-10",  6, 10),
        ("11-15", 11, 15),
        ("16-20", 16, 20),
        ("21+",   21, 99),
    ]
    print(f"{'Δ bucket':<10} {'n':>4} {'higher won':>11} {'rate':>7}   signal")
    print("-" * 58)
    for label, lo, hi in buckets:
        games = [r for r in rows if lo <= r["rank_delta"] <= hi]
        n = len(games)
        if n == 0:
            print(f"{label:<10} {n:>4}        --      --")
            continue
        hw = sum(1 for r in games if r["higher_rank_won"])
        rate = hw / n
        # Simple SDT-ish signal indicator
        signal = "ABOVE JND" if rate >= 0.75 else ("approaching" if rate >= 0.65 else "noise")
        print(f"{label:<10} {n:>4} {hw:>6} / {n:<3} {rate:>6.1%}   {signal}")
    print()

    # Per-delta table
    print("Per-delta detail:")
    by_delta = defaultdict(lambda: [0, 0])  # delta -> [higher_won, total]
    for r in rows:
        by_delta[r["rank_delta"]][1] += 1
        if r["higher_rank_won"]:
            by_delta[r["rank_delta"]][0] += 1
    print(f"{'delta':>6} {'n':>5} {'higher won':>12} {'rate':>7}")
    for d in sorted(by_delta):
        hw, n = by_delta[d]
        print(f"{d:>6} {n:>5} {hw:>8} / {n:<3} {hw/n:>6.1%}")

    # Totals
    tot = len(rows)
    tot_hw = sum(1 for r in rows if r["higher_rank_won"])
    print(f"\nOverall: higher rank won {tot_hw}/{tot} = {tot_hw/tot:.1%}")

    # Secondary: JND curve by week-of-season phase
    def phase(r):
        if r["season_type"] == "postseason":
            return "bowls/CFP"
        w = r["week"]
        if w <= 4:
            return "early (wk 1-4)"
        if w <= 9:
            return "mid (wk 5-9)"
        return "late (wk 10+)"

    print("\n\nSECONDARY ANALYSIS — JND by season phase")
    print("-" * 70)
    phases = ["early (wk 1-4)", "mid (wk 5-9)", "late (wk 10+)", "bowls/CFP"]
    buckets_small = [("<=10", 1, 10), ("11+", 11, 99)]
    print(f"{'phase':<18} {'bucket':<8} {'n':>4} {'higher won':>11} {'rate':>7}")
    for ph in phases:
        ph_rows = [r for r in rows if phase(r) == ph]
        for label, lo, hi in buckets_small:
            games = [r for r in ph_rows if lo <= r["rank_delta"] <= hi]
            n = len(games)
            if n == 0:
                print(f"{ph:<18} {label:<8} {n:>4}        --      --")
                continue
            hw = sum(1 for r in games if r["higher_rank_won"])
            print(f"{ph:<18} {label:<8} {n:>4} {hw:>6} / {n:<3} {hw/n:>6.1%}")

    # Overall JND by year (is the JND stable over 30 years?)
    print("\nBy year (higher-rank win rate at Δ >= 11):")
    for y in sorted(set(r["year"] for r in rows)):
        yr_rows = [r for r in rows if r["year"] == y]
        sig = [r for r in yr_rows if r["rank_delta"] >= 11]
        if not sig:
            continue
        hw = sum(1 for r in sig if r["higher_rank_won"])
        n_all = len(yr_rows)
        print(f"  {y}: {hw}/{len(sig)} = {hw/len(sig):.1%}  (total ranked matchups: {n_all})")


if __name__ == "__main__":
    main()
