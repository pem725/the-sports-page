"""
Pull EVERY MLB hitter and pitcher 1985-2025, not just the qualified ones.

Uses playerPool=all to capture flameouts and bench players. One API call
per year per group (~82 calls total). Each call returns ~600-1000 rows.

Output:
  all_hitters_seasons.csv — every MLB hitter, every season they batted
  all_pitchers_seasons.csv — every MLB pitcher, every season they threw
"""

import requests, csv, time, sys
from pathlib import Path
from collections import defaultdict

HEADERS = {"User-Agent": "curl/8.0"}
SEASON_URL = "https://statsapi.mlb.com/api/v1/stats"

START_YEAR = 1985
END_YEAR = 2025

def to_float(x):
    try: return float(x) if x not in ("", None, "-.--") else None
    except (TypeError, ValueError): return None

def to_int(x):
    try: return int(x)
    except (TypeError, ValueError): return None

def ip_decimal(s):
    if s in (None, "", "-.--"): return None
    try:
        s = str(s)
        if "." in s:
            w, f = s.split("."); return int(w) + int(f)/3.0
        return float(s)
    except: return None


def fetch_year(year, group):
    params = {
        "stats": "season",
        "group": group,
        "season": year,
        "sportIds": 1,
        "playerPool": "all",
        "limit": 2000,
    }
    r = requests.get(SEASON_URL, params=params, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        print(f"  ! {year} {group}: HTTP {r.status_code}", file=sys.stderr)
        return []
    return r.json().get("stats", [{}])[0].get("splits", []) if r.json().get("stats") else []


def hitter_row(year, s):
    p = s.get("player", {})
    pid = p.get("id"); name = p.get("fullName")
    if not pid: return None
    pos = (s.get("position") or {}).get("abbreviation", "")
    st = s.get("stat", {})
    pa = to_int(st.get("plateAppearances")) or 0
    if pa < 1: return None
    return {
        "name": name, "pid": pid, "year": year,
        "position": pos,
        "age": st.get("age"),
        "G":   to_int(st.get("gamesPlayed")),
        "PA":  pa,
        "AB":  to_int(st.get("atBats")),
        "AVG": to_float(st.get("avg")),
        "OBP": to_float(st.get("obp")),
        "SLG": to_float(st.get("slg")),
        "OPS": to_float(st.get("ops")),
        "HR":  to_int(st.get("homeRuns")),
        "BB":  to_int(st.get("baseOnBalls")),
        "SO":  to_int(st.get("strikeOuts")),
    }


def pitcher_row(year, s):
    p = s.get("player", {})
    pid = p.get("id"); name = p.get("fullName")
    if not pid: return None
    st = s.get("stat", {})
    ip = ip_decimal(st.get("inningsPitched"))
    if ip is None or ip < 0.1: return None
    g = to_int(st.get("gamesPlayed")) or 0
    gs = to_int(st.get("gamesStarted")) or 0
    role = "SP" if (g and gs/g >= 0.5) else "RP"
    k = to_int(st.get("strikeOuts")) or 0
    bb = to_int(st.get("baseOnBalls")) or 0
    hr = to_int(st.get("homeRuns")) or 0
    return {
        "name": name, "pid": pid, "year": year, "role": role,
        "age": st.get("age"),
        "G": g, "GS": gs, "IP": round(ip, 2),
        "ERA":  to_float(st.get("era")),
        "WHIP": to_float(st.get("whip")),
        "K": k, "BB": bb, "HR": hr,
        "K_per_9":  round(9*k/ip, 3) if ip else None,
        "BB_per_9": round(9*bb/ip, 3) if ip else None,
        "HR_per_9": round(9*hr/ip, 3) if ip else None,
    }


def main():
    out_dir = Path(__file__).parent

    print(f"Pulling all hitters {START_YEAR}-{END_YEAR}")
    hit_rows = []
    for yr in range(START_YEAR, END_YEAR + 1):
        splits = fetch_year(yr, "hitting")
        for s in splits:
            row = hitter_row(yr, s)
            if row: hit_rows.append(row)
        if yr % 5 == 0 or yr == END_YEAR:
            print(f"  {yr}: cumulative {len(hit_rows)} hitter-seasons, "
                  f"{len(set(r['pid'] for r in hit_rows))} unique hitters")
        time.sleep(0.3)

    with open(out_dir / "all_hitters_seasons.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(hit_rows[0].keys()))
        w.writeheader(); w.writerows(hit_rows)
    print(f"  → all_hitters_seasons.csv ({len(hit_rows)} rows)")

    print(f"\nPulling all pitchers {START_YEAR}-{END_YEAR}")
    pit_rows = []
    for yr in range(START_YEAR, END_YEAR + 1):
        splits = fetch_year(yr, "pitching")
        for s in splits:
            row = pitcher_row(yr, s)
            if row: pit_rows.append(row)
        if yr % 5 == 0 or yr == END_YEAR:
            print(f"  {yr}: cumulative {len(pit_rows)} pitcher-seasons, "
                  f"{len(set(r['pid'] for r in pit_rows))} unique pitchers")
        time.sleep(0.3)

    with open(out_dir / "all_pitchers_seasons.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pit_rows[0].keys()))
        w.writeheader(); w.writerows(pit_rows)
    print(f"  → all_pitchers_seasons.csv ({len(pit_rows)} rows)")


if __name__ == "__main__":
    main()
