"""
Phase-2 data pull for the Half-Life series.

Goal: every batter who put up >= 5 qualified seasons (PA >= 502) between 1985-2025.
Process:
  1. Per year, query MLB Stats API for qualified hitters that season.
  2. Accumulate unique player IDs.
  3. Filter to players appearing in >= 5 qualified seasons.
  4. Pull each player's year-by-year career stats + position.
  5. Save to broader_career_data.csv.

Output columns: name, position, year, mlb_yr, age, G, PA, AB, AVG, OBP, SLG, OPS, HR, BB, SO
"""

import requests
import csv
import sys
import time
from pathlib import Path
from collections import defaultdict

HEADERS = {"User-Agent": "curl/8.0"}
SEASON_LEADERS_URL = "https://statsapi.mlb.com/api/v1/stats"
STATS_URL = "https://statsapi.mlb.com/api/v1/people/{pid}/stats?stats=yearByYear&group=hitting"
PERSON_URL = "https://statsapi.mlb.com/api/v1/people/{pid}"

START_YEAR = 1985
END_YEAR = 2025
MIN_QUALIFIED_SEASONS = 5  # filter threshold

PA_QUAL = 502  # MLB official qualified-batter threshold (502 PA, 3.1 PA per scheduled game)


def to_float(s):
    try: return float(s)
    except (ValueError, TypeError): return None


def get_qualified_hitters(season):
    """Return list of (player_id, name) for qualified hitters that season."""
    params = {
        "stats": "season",
        "group": "hitting",
        "season": season,
        "sportIds": 1,
        "playerPool": "qualified",
        "limit": 500,
    }
    r = requests.get(SEASON_LEADERS_URL, params=params, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        print(f"  ! {season}: HTTP {r.status_code}", file=sys.stderr)
        return []
    data = r.json()
    splits = data.get("stats", [{}])[0].get("splits", []) if data.get("stats") else []
    out = []
    for s in splits:
        player = s.get("player", {})
        pid = player.get("id")
        name = player.get("fullName")
        if pid: out.append((pid, name))
    return out


def fetch_person(pid):
    r = requests.get(PERSON_URL.format(pid=pid), headers=HEADERS, timeout=15)
    if r.status_code != 200: return None
    return r.json().get("people", [{}])[0]


def fetch_yearly(pid):
    r = requests.get(STATS_URL.format(pid=pid), headers=HEADERS, timeout=20)
    if r.status_code != 200: return []
    return r.json().get("stats", [{}])[0].get("splits", [])


def main():
    print(f"Step 1: scanning qualified hitters {START_YEAR}-{END_YEAR}")
    appearances = defaultdict(list)  # pid -> list of (year, name)
    for season in range(START_YEAR, END_YEAR + 1):
        qhs = get_qualified_hitters(season)
        for pid, name in qhs:
            appearances[pid].append((season, name))
        print(f"  {season}: {len(qhs)} qualified hitters (cumulative unique={len(appearances)})")
        time.sleep(0.25)  # politeness

    print(f"\nStep 2: filtering to players with >= {MIN_QUALIFIED_SEASONS} qualified seasons")
    targets = {pid: appearances[pid] for pid in appearances if len(appearances[pid]) >= MIN_QUALIFIED_SEASONS}
    print(f"  → {len(targets)} target players")

    print(f"\nStep 3: pulling career stats per player")
    out_rows = []
    failed = []
    for i, (pid, apps) in enumerate(targets.items(), 1):
        name = apps[0][1]
        try:
            person = fetch_person(pid)
            if not person:
                failed.append(name); continue
            debut = person.get("mlbDebutDate", "")
            debut_year = int(debut[:4]) if debut else None
            primary_pos = (person.get("primaryPosition", {}) or {}).get("abbreviation", "")
            splits = fetch_yearly(pid)
            for s in splits:
                yr = int(s.get("season", 0) or 0)
                if yr < 1900 or yr >= 2026: continue
                stat = s.get("stat", {})
                pa = stat.get("plateAppearances")
                if not pa or pa < 100: continue  # skip cup-of-coffee partial seasons
                out_rows.append({
                    "name": name,
                    "pid": pid,
                    "primary_position": primary_pos,
                    "year": yr,
                    "mlb_yr": yr - debut_year + 1 if debut_year else None,
                    "age": stat.get("age"),
                    "G": stat.get("gamesPlayed"),
                    "PA": pa,
                    "AB": stat.get("atBats"),
                    "AVG": to_float(stat.get("avg")),
                    "OBP": to_float(stat.get("obp")),
                    "SLG": to_float(stat.get("slg")),
                    "OPS": to_float(stat.get("ops")),
                    "HR": stat.get("homeRuns"),
                    "BB": stat.get("baseOnBalls"),
                    "SO": stat.get("strikeOuts"),
                })
            if i % 25 == 0:
                print(f"  pulled {i}/{len(targets)} careers ({len(out_rows)} rows so far)")
            time.sleep(0.2)
        except Exception as e:
            print(f"  ! {name}: {e}", file=sys.stderr)
            failed.append(name)

    # Save
    out_path = Path(__file__).parent / "broader_career_data.csv"
    if out_rows:
        with open(out_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            w.writeheader()
            w.writerows(out_rows)
    print(f"\nDone. {len(out_rows)} rows, {len(set(r['name'] for r in out_rows))} players → {out_path}")
    if failed: print(f"Failed: {len(failed)} players")


if __name__ == "__main__":
    sys.exit(main() or 0)
