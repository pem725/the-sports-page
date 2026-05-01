#!/usr/bin/env python3
"""
NFL Draft Dataset — shared infrastructure for the "After the Jets" 4-part series.

Pulls the canonical nflverse draft_picks.csv (which already contains HoF, AV,
Pro Bowls, seasons-started, and a separate AV for time spent with the
drafting team), filters to the modern era (1976-2025), normalizes franchise
codes across relocations, applies the three Issue #25 bust definitions,
and emits two CSVs:

  data/nfl_picks.csv         one row per pick, with bust flags
  data/nfl_team_summary.csv  one row per consolidated franchise

Bust definitions (from Issue #25):
  A: never made a Pro Bowl                              probowls == 0
  B: career AV below the slot-expectation curve         w_av < expected(pick)
  C: fewer than 4 seasons as a starter for drafter      seasons_started < 4
                                                        (using dr_av tier)

A "triple bust" trips all three. A "clean hit" trips zero.

Source: https://github.com/nflverse/nflverse-data/releases/tag/draft_picks
"""

import csv
import os
import urllib.request
from collections import defaultdict
from statistics import median

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "data", "draft_picks.csv")
PICKS_OUT = os.path.join(REPO, "data", "nfl_picks.csv")
TEAMS_OUT = os.path.join(REPO, "data", "nfl_team_summary.csv")
SOURCE_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/"
    "draft_picks/draft_picks.csv"
)

# Franchise normalization: map historical / relocation codes to a single
# stable code. Rams (STL/LARM/LAR/RAM all → LAR), Cards (PHO/ARZ → ARI),
# Raiders (OAK/RAI → LV), Titans (HOU pre-1997 → TEN), Ravens (BAL post-1996),
# Browns (CLE → BAL pre-1996 then re-expansion CLE 1999+), etc.
TEAM_CANONICAL = {
    "STL": "LAR",  # Rams 1995-2015 St. Louis era
    "LARM": "LAR",  # Some sources use LARM for 1980s LA Rams
    "RAM": "LAR",
    "PHO": "ARI",   # Cards in Phoenix 1988-93
    "ARZ": "ARI",
    "OAK": "LV",
    "RAI": "LV",
    "SDG": "LAC",   # Chargers in San Diego
    "SD":  "LAC",
    "RAV": "BAL",
    "TAM": "TB",
    "GNB": "GB",
    "KAN": "KC",
    "NWE": "NE",
    "NOR": "NO",
    "SFO": "SF",
}
# Pre-1996 BAL was the Colts → IND. Pre-1997 HOU was the Oilers → TEN.
# These can't be handled by a simple code map; we use (team, year) overrides.
YEAR_TEAM_OVERRIDES = {
    # All Houston Oilers picks before the 1997 move are Titans franchise
    ("HOU", range(1976, 1997)): "TEN",
    # All Baltimore Colts picks before 1984 move are Indianapolis franchise
    ("BAL", range(1976, 1984)): "IND",
    # Cleveland Browns 1996-98: franchise was suspended; post-1999 picks
    # are the new Browns expansion. Pre-1996 CLE picks are arguably the
    # Ravens lineage but for this analysis we keep CLE as Cleveland.
}


def normalize_team(team: str, year: int) -> str:
    """Map a (team_code, year) to a single canonical franchise code."""
    for (raw, year_range), canon in YEAR_TEAM_OVERRIDES.items():
        if team == raw and year in year_range:
            return canon
    return TEAM_CANONICAL.get(team, team)


def download_if_missing():
    if os.path.isfile(RAW):
        return
    os.makedirs(os.path.dirname(RAW), exist_ok=True)
    print(f"Downloading {SOURCE_URL} ...")
    urllib.request.urlretrieve(SOURCE_URL, RAW)
    print(f"  saved to {RAW}")


def load_first_round(year_lo=1976, year_hi=2025):
    rows = []
    with open(RAW) as f:
        for r in csv.DictReader(f):
            try:
                year = int(r["season"])
                rnd = int(r["round"])
            except (ValueError, KeyError):
                continue
            if rnd != 1 or not (year_lo <= year <= year_hi):
                continue
            r["season"] = year
            r["pick"] = int(r["pick"]) if r["pick"] else None
            r["team"] = normalize_team(r["team"], year)
            for k in ("probowls", "seasons_started", "w_av", "dr_av", "w_av", "games"):
                r[k] = int(r[k]) if r.get(k) else 0
            r["hof"] = r.get("hof", "FALSE") == "TRUE"
            rows.append(r)
    return rows


def slot_expected_av(rows):
    """Build a smoothed slot expectation: median career AV by pick number,
    over a 5-pick rolling window. Recent picks (active careers) inflate the
    curve at the late picks; we restrict the curve to the cohort drafted
    1976-2015 to give every player at least 10 years post-pick."""
    cohort = [r for r in rows if r["season"] <= 2015]
    by_pick = defaultdict(list)
    for r in cohort:
        if r["pick"]:
            by_pick[r["pick"]].append(r["w_av"])
    # Smooth with a 5-pick rolling window
    expected = {}
    picks = sorted(by_pick.keys())
    for p in picks:
        window = [v for q in range(max(1, p - 2), p + 3) for v in by_pick.get(q, [])]
        expected[p] = median(window) if window else 0
    return expected


def apply_bust_flags(rows, expected):
    """Adds bust_a, bust_b, bust_c, triple_bust, clean_hit to each row.
    Active players (drafted 2020+) are skipped from B and C — too early to
    judge — but kept in the file with a flag."""
    for r in rows:
        active = r["season"] >= 2020
        r["active"] = 1 if active else 0
        r["bust_a"] = 1 if r["probowls"] == 0 else 0
        slot_av = expected.get(r["pick"], 30)
        r["bust_b"] = 1 if (not active and r["w_av"] < slot_av * 0.5) else 0
        r["bust_c"] = 1 if (not active and r["seasons_started"] < 4) else 0
        if active:
            r["triple_bust"] = 0
            r["clean_hit"] = 0
        else:
            r["triple_bust"] = 1 if (r["bust_a"] and r["bust_b"] and r["bust_c"]) else 0
            r["clean_hit"] = 1 if (not r["bust_a"] and not r["bust_b"] and not r["bust_c"]) else 0
    return rows


def write_picks_csv(rows):
    cols = [
        "season", "team", "pick", "pfr_player_name", "position",
        "hof", "probowls", "seasons_started", "w_av", "dr_av", "games",
        "active", "bust_a", "bust_b", "bust_c", "triple_bust", "clean_hit",
    ]
    with open(PICKS_OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Wrote {len(rows)} picks to {PICKS_OUT}")


def write_team_summary(rows):
    by_team = defaultdict(list)
    for r in rows:
        by_team[r["team"]].append(r)
    cols = [
        "team", "n_picks", "n_judged", "n_hof", "n_bust_a", "n_bust_b",
        "n_bust_c", "n_triple_bust", "n_clean_hit",
        "rate_bust_a", "rate_bust_b", "rate_bust_c",
        "rate_triple_bust", "rate_clean_hit", "hof_per_pick",
    ]
    with open(TEAMS_OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for team in sorted(by_team):
            picks = by_team[team]
            judged = [r for r in picks if not r["active"]]
            n_picks = len(picks)
            n_judged = len(judged)
            if n_judged == 0:
                continue
            row = {
                "team": team,
                "n_picks": n_picks,
                "n_judged": n_judged,
                "n_hof": sum(1 for r in picks if r["hof"]),
                "n_bust_a": sum(r["bust_a"] for r in judged),
                "n_bust_b": sum(r["bust_b"] for r in judged),
                "n_bust_c": sum(r["bust_c"] for r in judged),
                "n_triple_bust": sum(r["triple_bust"] for r in judged),
                "n_clean_hit": sum(r["clean_hit"] for r in judged),
            }
            for k in ("a", "b", "c", "triple_bust", "clean_hit"):
                cnt_key = f"n_bust_{k}" if k in ("a", "b", "c") else f"n_{k}"
                rate_key = f"rate_bust_{k}" if k in ("a", "b", "c") else f"rate_{k}"
                row[rate_key] = round(row[cnt_key] / n_judged, 4)
            row["hof_per_pick"] = round(row["n_hof"] / n_picks, 4)
            w.writerow(row)
    print(f"Wrote team summary to {TEAMS_OUT}")


def main():
    download_if_missing()
    rows = load_first_round(1976, 2025)
    print(f"Loaded {len(rows)} first-round picks 1976-2025")
    expected = slot_expected_av(rows)
    print(f"Slot expectation curve covers picks {min(expected)}-{max(expected)}")
    rows = apply_bust_flags(rows, expected)
    write_picks_csv(rows)
    write_team_summary(rows)


if __name__ == "__main__":
    main()
