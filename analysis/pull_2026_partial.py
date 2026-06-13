"""Pull 2026 partial-season hitting + pitching for everyone (playerPool=all).
Saves to all_hitters_2026_partial.csv and all_pitchers_2026_partial.csv.
"""
import requests, csv, time
from pathlib import Path

HEADERS = {"User-Agent": "curl/8.0"}
URL = "https://statsapi.mlb.com/api/v1/stats"

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

ANALYSIS = Path(__file__).parent

# Hitters
params = {"stats":"season","group":"hitting","season":2026,"sportIds":1,"playerPool":"all","limit":2000}
r = requests.get(URL, params=params, headers=HEADERS, timeout=30)
splits = r.json().get("stats", [{}])[0].get("splits", [])
rows = []
for s in splits:
    p = s.get("player", {}); st = s.get("stat", {})
    pa = to_int(st.get("plateAppearances")) or 0
    if pa < 1: continue
    rows.append({
        "pid": p.get("id"), "name": p.get("fullName"),
        "team": (s.get("team") or {}).get("name", ""),
        "PA": pa, "AB": to_int(st.get("atBats")),
        "H": to_int(st.get("hits")),
        "HR": to_int(st.get("homeRuns")), "BB": to_int(st.get("baseOnBalls")),
        "SO": to_int(st.get("strikeOuts")),
        "AVG": to_float(st.get("avg")), "OBP": to_float(st.get("obp")),
        "SLG": to_float(st.get("slg")), "OPS": to_float(st.get("ops")),
    })
with open(ANALYSIS / "all_hitters_2026_partial.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(f"Wrote all_hitters_2026_partial.csv  ({len(rows)} rows)")

time.sleep(0.4)

# Pitchers
params = {"stats":"season","group":"pitching","season":2026,"sportIds":1,"playerPool":"all","limit":2000}
r = requests.get(URL, params=params, headers=HEADERS, timeout=30)
splits = r.json().get("stats", [{}])[0].get("splits", [])
rows = []
for s in splits:
    p = s.get("player", {}); st = s.get("stat", {})
    ip = ip_dec(st.get("inningsPitched"))
    if ip is None or ip < 0.1: continue
    rows.append({
        "pid": p.get("id"), "name": p.get("fullName"),
        "team": (s.get("team") or {}).get("name", ""),
        "IP": round(ip, 2), "G": to_int(st.get("gamesPlayed")),
        "GS": to_int(st.get("gamesStarted")),
        "K": to_int(st.get("strikeOuts")), "BB": to_int(st.get("baseOnBalls")),
        "HR": to_int(st.get("homeRuns")), "ER": to_int(st.get("earnedRuns")),
        "ERA": to_float(st.get("era")), "WHIP": to_float(st.get("whip")),
    })
with open(ANALYSIS / "all_pitchers_2026_partial.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(f"Wrote all_pitchers_2026_partial.csv  ({len(rows)} rows)")
