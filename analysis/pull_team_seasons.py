"""
Per-team-per-season aggregates 1985-2025 + 2026 partial.
Pulls hitting + pitching team aggregates via MLB Stats API.

Approach: one call per (year, group) using statGroup=team.
"""
import requests, csv, time, sys
from pathlib import Path
from collections import defaultdict

HEADERS = {"User-Agent": "curl/8.0"}
URL = "https://statsapi.mlb.com/api/v1/teams/stats"

def to_int(x):
    try: return int(x)
    except: return None
def to_float(x):
    try: return float(x) if x not in ("", None, "-.--") else None
    except: return None
def ip_dec(s):
    if s in (None, "", "-.--"): return None
    s = str(s)
    if "." in s:
        w, f = s.split("."); return int(w) + int(f)/3.0
    return float(s)

def fetch_team_year(year, group):
    params = {"stats":"season","group":group,"sportIds":1,"season":year}
    r = requests.get(URL, params=params, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        print(f"  ! {year} {group}: HTTP {r.status_code}", file=sys.stderr)
        return []
    data = r.json()
    splits = []
    for stat_block in data.get("stats", []):
        splits.extend(stat_block.get("splits", []))
    return splits

ANALYSIS = Path(__file__).parent
hitting = []; pitching = []
print("Pulling team-year hitting + pitching 1985-2026 …")
for yr in range(1985, 2027):
    h = fetch_team_year(yr, "hitting")
    for s in h:
        team = s.get("team", {}); st = s.get("stat", {})
        pa = to_int(st.get("plateAppearances")) or 0
        if pa < 100: continue
        hitting.append({
            "year": yr, "team_id": team.get("id"), "team": team.get("name"),
            "PA": pa, "AB": to_int(st.get("atBats")),
            "HR": to_int(st.get("homeRuns")), "BB": to_int(st.get("baseOnBalls")),
            "SO": to_int(st.get("strikeOuts")), "R": to_int(st.get("runs")),
            "AVG": to_float(st.get("avg")), "OBP": to_float(st.get("obp")),
            "SLG": to_float(st.get("slg")), "OPS": to_float(st.get("ops")),
        })
    p = fetch_team_year(yr, "pitching")
    for s in p:
        team = s.get("team", {}); st = s.get("stat", {})
        ip = ip_dec(st.get("inningsPitched"))
        if not ip or ip < 50: continue
        pitching.append({
            "year": yr, "team_id": team.get("id"), "team": team.get("name"),
            "IP": round(ip, 2),
            "K": to_int(st.get("strikeOuts")), "BB": to_int(st.get("baseOnBalls")),
            "HR": to_int(st.get("homeRuns")), "ER": to_int(st.get("earnedRuns")),
            "R": to_int(st.get("runs")), "ERA": to_float(st.get("era")),
            "WHIP": to_float(st.get("whip")),
        })
    if yr % 5 == 0 or yr == 2026:
        print(f"  {yr}: {len(hitting)} hit rows, {len(pitching)} pit rows so far")
    time.sleep(0.2)

with open(ANALYSIS / "team_seasons_hitting.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(hitting[0].keys()))
    w.writeheader(); w.writerows(hitting)
with open(ANALYSIS / "team_seasons_pitching.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(pitching[0].keys()))
    w.writeheader(); w.writerows(pitching)
print(f"\nWrote team_seasons_hitting.csv ({len(hitting)}) and team_seasons_pitching.csv ({len(pitching)})")
