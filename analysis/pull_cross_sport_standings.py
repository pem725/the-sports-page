"""
Pull team-season win pct for NFL, NHL, NBA across 1985-2024 (or as far back as
ESPN API goes). Save to cross_sport_standings.csv.

Note: ESPN season convention varies. NFL season YYYY = year played; NBA/NHL
season YYYY = year that the season ENDED (so 2024 = 2023-24 season).
We label everything by the YEAR THE SEASON ENDED for cross-sport alignment.
"""
import requests, csv, time, sys
from pathlib import Path

HEADERS = {"User-Agent": "curl/8.0"}
ANALYSIS = Path(__file__).parent

ESPN_URLS = {
    "NFL": "http://site.api.espn.com/apis/v2/sports/football/nfl/standings",
    "NBA": "http://site.api.espn.com/apis/v2/sports/basketball/nba/standings",
    "NHL": "http://site.api.espn.com/apis/v2/sports/hockey/nhl/standings",
}

def stat(entry, name):
    for s in entry.get("stats", []):
        if s.get("name") == name:
            return s.get("value")
    return None

rows = []

for sport, url in ESPN_URLS.items():
    print(f"\n=== {sport} ===")
    for season in range(1985, 2026):
        try:
            r = requests.get(url, params={"season": season}, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                print(f"  ! {sport} {season}: HTTP {r.status_code}", file=sys.stderr); continue
            data = r.json()
            n_teams = 0
            for conf in data.get("children", []):
                for e in conf.get("standings", {}).get("entries", []):
                    team = e.get("team", {})
                    wins = stat(e, "wins"); losses = stat(e, "losses"); ties = stat(e, "ties") or 0
                    wp = stat(e, "winPercent")
                    if wins is None or losses is None: continue
                    rows.append({
                        "sport": sport,
                        "season_end": season,
                        "team_id": team.get("id"),
                        "team": team.get("displayName"),
                        "abbr": team.get("abbreviation"),
                        "wins": int(wins),
                        "losses": int(losses),
                        "ties": int(ties),
                        "win_pct": round(wp, 4) if wp else None,
                    })
                    n_teams += 1
            if season % 5 == 0:
                print(f"  {season}: {n_teams} teams ({len(rows)} cumulative rows)")
        except Exception as e:
            print(f"  ! {sport} {season}: {e}", file=sys.stderr)
        time.sleep(0.15)

if rows:
    with open(ANALYSIS / "cross_sport_standings.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nWrote {len(rows)} rows to cross_sport_standings.csv")
    # Quick summary
    from collections import defaultdict
    by_sport_yr = defaultdict(int)
    for r in rows: by_sport_yr[(r["sport"], r["season_end"])] += 1
    print(f"\n{'sport':<5} years_covered  teams_per_year_range")
    by_sport = defaultdict(list)
    for (s, y), n in by_sport_yr.items(): by_sport[s].append((y, n))
    for sport, lst in by_sport.items():
        years = sorted(y for y, _ in lst)
        ns = [n for _, n in lst]
        print(f"  {sport:<5} {min(years)}-{max(years)} ({len(years)})  {min(ns)}-{max(ns)}")
