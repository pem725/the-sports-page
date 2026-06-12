"""
Pull year-by-year hitting stats for the Half-Life series Part I cohort.
Source: MLB Stats API (statsapi.mlb.com) — official public, no auth.

Output: analysis/half_life_data.csv with one row per player-season.
"""

import requests
import csv
import json
import sys
from pathlib import Path

HEADERS = {"User-Agent": "curl/8.0"}
SEARCH_URL = "https://statsapi.mlb.com/api/v1/people/search"
STATS_URL = "https://statsapi.mlb.com/api/v1/people/{pid}/stats?stats=yearByYear&group=hitting"
PERSON_URL = "https://statsapi.mlb.com/api/v1/people/{pid}"

# Players to pull. Position label here is canonical primary position;
# the API also returns position per season which we'll capture.
# (name, position_label, birth_year) — birth year disambiguates name collisions
COHORT = [
    ("Pete Alonso", "1B", 1994),
    ("Manny Machado", "3B/SS", 1992),
    # 1B historicals
    ("Albert Pujols", "1B", 1980),
    ("Jeff Bagwell", "1B", 1968),
    ("Jim Thome", "1B", 1970),
    ("Frank Thomas", "1B", 1968),
    ("Mark Teixeira", "1B", 1980),
    ("Paul Goldschmidt", "1B", 1987),
    ("Joey Votto", "1B", 1983),
    ("Ryan Howard", "1B", 1979),
    ("Fred McGriff", "1B", 1963),
    ("John Olerud", "1B", 1968),
    # 3B/SS historicals
    ("Adrian Beltre", "3B", 1979),
    ("Chipper Jones", "3B", 1972),
    ("Scott Rolen", "3B", 1975),
    ("Evan Longoria", "3B", 1985),
    ("David Wright", "3B", 1982),
    ("Alex Rodriguez", "SS/3B", 1975),
    ("Derek Jeter", "SS", 1974),
    ("Cal Ripken Jr.", "SS/3B", 1960),
]


def lookup_id(name, birth_year=None):
    """Search MLB API for a player by name; disambiguate by birth year if multiple matches."""
    # MLB search has limited fuzzy capability; try the full name first
    r = requests.get(SEARCH_URL, params={"names": name}, headers=HEADERS, timeout=15)
    r.raise_for_status()
    people = r.json().get("people", [])
    if not people:
        return None, None
    # Filter by birth year if provided
    if birth_year is not None:
        matches = [p for p in people if (p.get("birthDate", "")[:4] == str(birth_year))]
        if matches:
            people = matches
    # Prefer the player with the most recent debut (modern era)
    def debut_key(p):
        d = p.get("mlbDebutDate", "")
        return int(d[:4]) if d else 0
    people.sort(key=debut_key, reverse=True)
    p = people[0]
    return p["id"], p.get("mlbDebutDate", "")[:4]


def fetch_person_meta(pid):
    """Get debut year and birth year for MLB-year-of-service computation."""
    r = requests.get(PERSON_URL.format(pid=pid), headers=HEADERS, timeout=15)
    r.raise_for_status()
    p = r.json().get("people", [{}])[0]
    debut = p.get("mlbDebutDate", "")
    debut_year = int(debut[:4]) if debut else None
    birth = p.get("birthDate", "")
    birth_year = int(birth[:4]) if birth else None
    return debut_year, birth_year


def fetch_yearly(pid):
    """Get year-by-year hitting splits."""
    r = requests.get(STATS_URL.format(pid=pid), headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("stats", [{}])[0].get("splits", [])


def to_float(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def main():
    out = []
    for name, pos_label, expected_birth_year in COHORT:
        try:
            pid, debut_year_str = lookup_id(name, expected_birth_year)
            if pid is None:
                print(f"  ✗ {name}: no MLB ID found", file=sys.stderr)
                continue
            debut_year, birth_year = fetch_person_meta(pid)
            # Sanity check
            if expected_birth_year and birth_year != expected_birth_year:
                print(f"  ! {name}: birth year mismatch — expected {expected_birth_year}, got {birth_year}; skipping", file=sys.stderr)
                continue
            splits = fetch_yearly(pid)
            seasons = 0
            for s in splits:
                year = int(s.get("season", 0))
                # only completed seasons (don't include in-progress 2026)
                if year >= 2026:
                    continue
                # mlb year of service: debut year = 1
                mlb_yr = year - debut_year + 1 if debut_year else None
                stat = s.get("stat", {})
                # team and position info
                team = s.get("team", {}).get("name", "")
                row = {
                    "name": name,
                    "position_label": pos_label,
                    "year": year,
                    "mlb_yr": mlb_yr,
                    "age": stat.get("age"),
                    "team": team,
                    "G": stat.get("gamesPlayed"),
                    "PA": stat.get("plateAppearances"),
                    "AB": stat.get("atBats"),
                    "AVG": to_float(stat.get("avg")),
                    "OBP": to_float(stat.get("obp")),
                    "SLG": to_float(stat.get("slg")),
                    "OPS": to_float(stat.get("ops")),
                    "HR": stat.get("homeRuns"),
                    "BB": stat.get("baseOnBalls"),
                    "SO": stat.get("strikeOuts"),
                }
                out.append(row)
                seasons += 1
            print(f"  ✓ {name} (id={pid}): debut={debut_year}, {seasons} seasons pulled")
        except Exception as e:
            print(f"  ✗ {name}: {e}", file=sys.stderr)

    out_path = Path(__file__).parent / "half_life_data.csv"
    if not out:
        print("No data pulled.", file=sys.stderr)
        return 1
    fieldnames = list(out[0].keys())
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out)
    print(f"\nWrote {len(out)} rows across {len(set(r['name'] for r in out))} players → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
