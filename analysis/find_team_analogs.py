"""
For each 2026 team, find nearest historical (team, year) analog.

Method: z-score 6 features across all (team, year) cells 1985-2025,
compute Euclidean distance from each 2026 team to all history,
rank, scan for narrative.

Features: team OPS, team ERA, K_PA, BB_PA, HR_PA, win pct.
"""
import csv, json, math, statistics
from pathlib import Path
from collections import defaultdict

ANALYSIS = Path(__file__).parent

def to_int(x):
    try: return int(x)
    except: return None
def to_float(x):
    try: return float(x) if x not in ("", None) else None
    except: return None

# ──── Load team-season hitting + pitching ────
hit_by = {}
for row in csv.DictReader(open(ANALYSIS / "team_seasons_hitting.csv")):
    key = (int(row["year"]), int(row["team_id"]))
    hit_by[key] = row
pit_by = {}
for row in csv.DictReader(open(ANALYSIS / "team_seasons_pitching.csv")):
    key = (int(row["year"]), int(row["team_id"]))
    pit_by[key] = row

# ──── Load standings (W/L) ────
standings = json.load(open(ANALYSIS / "predictability_data.json"))["mlb"]["team_seasons"]
wp_by = {(int(r["year"]), int(r["team_id"])): r for r in standings}

# 2026 partial standings: pull live? For now, accept that we may have to
# do without a full season win pct. Use existing MLB API standings.
import requests
HEADERS = {"User-Agent": "curl/8.0"}
def pull_2026_standings():
    r = requests.get("https://statsapi.mlb.com/api/v1/standings",
                     params={"leagueId":"103,104","season":2026,"standingsTypes":"regularSeason"},
                     headers=HEADERS, timeout=20)
    if r.status_code != 200: return {}
    out = {}
    for rec in r.json().get("records", []):
        for tr in rec.get("teamRecords", []):
            tid = tr.get("team",{}).get("id")
            w, l = tr.get("wins",0), tr.get("losses",0)
            if w+l < 1: continue
            out[(2026, tid)] = {"wins": w, "losses": l, "team": tr["team"]["name"],
                                "win_pct": round(w/(w+l), 4) if (w+l) else None}
    return out
wp_by.update(pull_2026_standings())

# ──── Build feature vectors ────
def feat(year, tid):
    h = hit_by.get((year, tid)); p = pit_by.get((year, tid)); s = wp_by.get((year, tid))
    if not (h and p and s): return None
    pa = int(h["PA"]); ip = float(p["IP"])
    if pa < 1000 or ip < 200: return None  # require at least some season
    return {
        "OPS": float(h["OPS"]),
        "ERA": float(p["ERA"]),
        "K_PA": int(h["SO"])/pa,
        "BB_PA": int(h["BB"])/pa,
        "HR_PA": int(h["HR"])/pa,
        "win_pct": float(s["win_pct"]),
        "team": h["team"], "year": year,
    }

cells = {}
for (year, tid) in set(hit_by.keys()) | set(pit_by.keys()):
    if year < 1985: continue
    f = feat(year, tid)
    if f: cells[(year, tid)] = f

print(f"Team-season feature cells: {len(cells)}")

# ──── Standardize ────
FEATS = ["OPS","ERA","K_PA","BB_PA","HR_PA","win_pct"]
historical_keys = [k for k in cells if k[0] < 2026]
mu = {f: statistics.mean(cells[k][f] for k in historical_keys) for f in FEATS}
sd = {f: statistics.stdev(cells[k][f] for k in historical_keys) for f in FEATS}

def z(cell):
    return [(cell[f] - mu[f]) / sd[f] for f in FEATS]
def dist(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))

# ──── For each 2026 team, find nearest historical analog ────
teams_2026 = sorted([k for k in cells if k[0] == 2026])
print(f"2026 teams loaded: {len(teams_2026)}")

analogs = {}
for k in teams_2026:
    cv = z(cells[k])
    candidates = []
    for hk in historical_keys:
        d = dist(cv, z(cells[hk]))
        candidates.append((d, hk))
    candidates.sort()
    analogs[k] = {
        "team_2026": cells[k]["team"],
        "vector_2026": {f: round(cells[k][f], 4) for f in FEATS},
        "top_5": [{
            "year": cells[hk]["year"], "team": cells[hk]["team"],
            "distance": round(d, 3),
            "vector": {f: round(cells[hk][f], 4) for f in FEATS},
        } for d, hk in candidates[:5]],
    }

# Print results sorted by 2026 team name
print(f"\n{'='*80}")
print(f"2026 TEAM ANALOGS")
print(f"{'='*80}")
for k in teams_2026:
    a = analogs[k]
    top = a["top_5"][0]
    print(f"\n{a['team_2026']}: {top['year']} {top['team']} (d={top['distance']})")
    print(f"  2026:        OPS {a['vector_2026']['OPS']:.3f}  ERA {a['vector_2026']['ERA']:.2f}  WP {a['vector_2026']['win_pct']:.3f}")
    print(f"  {top['year']}-analog:  OPS {top['vector']['OPS']:.3f}  ERA {top['vector']['ERA']:.2f}  WP {top['vector']['win_pct']:.3f}")
    print(f"  Next 4 analogs: " + ", ".join(f"{x['year']} {x['team'].split()[-1]} ({x['distance']:.2f})" for x in a["top_5"][1:]))

# Save full output
json.dump({"feats": FEATS, "mu": mu, "sd": sd, "analogs": {f"{k[0]}_{k[1]}": v for k, v in analogs.items()}},
          open(ANALYSIS / "team_analogs.json", "w"), indent=2)
print(f"\nWrote team_analogs.json")

# ──── Scan for sharpest narrative ────
print(f"\n{'='*80}")
print(f"SHARPEST MATCHES (lowest distance to closest analog)")
print(f"{'='*80}")
ranked = sorted(teams_2026, key=lambda k: analogs[k]["top_5"][0]["distance"])
for k in ranked[:10]:
    a = analogs[k]
    print(f"  d={a['top_5'][0]['distance']:.2f}  {a['team_2026']:<22} ≈ {a['top_5'][0]['year']} {a['top_5'][0]['team']}")

print(f"\n{'='*80}")
print(f"LOOSEST MATCHES (highest distance to closest analog)")
print(f"{'='*80}")
for k in ranked[-5:]:
    a = analogs[k]
    print(f"  d={a['top_5'][0]['distance']:.2f}  {a['team_2026']:<22} ≈ {a['top_5'][0]['year']} {a['top_5'][0]['team']}")

# Specifically: Mets, Yankees, Mariners, Notre Dame teams of interest
print(f"\n{'='*80}")
print(f"TEAMS OF NEWSLETTER INTEREST")
print(f"{'='*80}")
interest = ["Mets", "Yankees", "Rangers", "Jets", "Mariners", "Bills", "Raiders", "Seahawks"]
for k in teams_2026:
    a = analogs[k]
    if any(name in a["team_2026"] for name in interest):
        top = a["top_5"][0]
        print(f"  {a['team_2026']:<22} → {top['year']} {top['team']} (d={top['distance']:.2f})")
