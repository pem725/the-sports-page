"""
Pull two data sources and compute lag-1 autocorrelation:
  1. Steamboat Springs CO seasonal snowfall (NOAA GHCN)
  2. MLB team win pct year-over-year (MLB Stats API)

Goal: answer "is weather more predictable than the Mets?"
Outputs: predictability_data.json with both series + correlations.
"""
import requests, csv, json
from pathlib import Path
from collections import defaultdict

ANALYSIS = Path(__file__).parent
HEADERS = {"User-Agent": "curl/8.0"}

# ─── 1) Snowfall: Steamboat Springs, CO (already downloaded) ───
SNOW_CSV = "/tmp/test_steamboat.csv"

# Build season totals: Nov 1 of year Y through Apr 30 of year Y+1 = "ski season starting in year Y"
season_snow = defaultdict(float)
season_days = defaultdict(int)
with open(SNOW_CSV) as f:
    reader = csv.DictReader(f)
    for row in reader:
        date = row.get("DATE", "")
        if not date or len(date) < 10: continue
        try:
            yr = int(date[:4]); mo = int(date[5:7])
        except ValueError: continue
        snow = row.get("SNOW", "").strip()
        if not snow: continue
        try: s = float(snow)
        except ValueError: continue
        if s < 0: continue  # NOAA uses negative for missing
        # Season label: Nov-Dec belong to that calendar year's season; Jan-Apr belong to prior calendar year
        if mo in (11, 12):
            season = yr
        elif mo in (1, 2, 3, 4):
            season = yr - 1
        else:
            continue
        season_snow[season] += s  # mm (NOAA daily totals)
        season_days[season] += 1

# Keep only seasons with most days reported (e.g. >= 150 of ~182 winter days)
snow_series = []
for season in sorted(season_snow):
    d = season_days[season]
    if d >= 150 and 1985 <= season <= 2024:
        snow_series.append({"season_start": season, "snow_mm": round(season_snow[season], 1), "days": d})
print(f"Steamboat snowfall series: {len(snow_series)} seasons (Nov-Apr, >=150 days reported)")

# ─── 2) MLB team standings 1985-2025 ───
mlb_records = []
print("Pulling MLB standings 1985-2025…")
for yr in range(1985, 2026):
    r = requests.get(
        "https://statsapi.mlb.com/api/v1/standings",
        params={"leagueId": "103,104", "season": yr, "standingsTypes": "regularSeason"},
        headers=HEADERS, timeout=20)
    if r.status_code != 200:
        print(f"  ! {yr}: HTTP {r.status_code}"); continue
    data = r.json()
    for rec in data.get("records", []):
        for tr in rec.get("teamRecords", []):
            team = tr.get("team", {})
            w = tr.get("wins", 0); l = tr.get("losses", 0)
            gp = w + l
            if gp < 50: continue  # strike/pandemic years OK but skip if too thin
            mlb_records.append({
                "year": yr,
                "team_id": team.get("id"),
                "team": team.get("name"),
                "wins": w, "losses": l, "games": gp,
                "win_pct": round(w / gp, 4) if gp else None,
            })
print(f"  → {len(mlb_records)} team-seasons")

# ─── 3) Compute lag-1 autocorrelation ───
def autocorr_lag1(values_by_key):
    """values_by_key: {key: ordered list of (period, value)}; returns Pearson r of v(t), v(t+1)."""
    xs, ys = [], []
    for key, pairs in values_by_key.items():
        pairs = sorted(pairs)
        for i in range(len(pairs) - 1):
            p1, v1 = pairs[i]
            p2, v2 = pairs[i+1]
            if p2 - p1 == 1 and v1 is not None and v2 is not None:
                xs.append(v1); ys.append(v2)
    return xs, ys

def pearson(xs, ys):
    n = len(xs)
    if n < 2: return None
    mx = sum(xs)/n; my = sum(ys)/n
    num = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    den_x = sum((x-mx)**2 for x in xs)**0.5
    den_y = sum((y-my)**2 for y in ys)**0.5
    return num / (den_x * den_y) if den_x and den_y else None

# Snow: single series
snow_pairs = {"steamboat": [(r["season_start"], r["snow_mm"]) for r in snow_series]}
sx, sy = autocorr_lag1(snow_pairs)
r_snow = pearson(sx, sy)
print(f"\nSteamboat snowfall lag-1 r: {r_snow:.3f}  (n={len(sx)})")

# Baseball: pooled across all teams (team_id keyed)
by_team = defaultdict(list)
for r in mlb_records:
    by_team[r["team_id"]].append((r["year"], r["win_pct"]))
bx, by = autocorr_lag1(by_team)
r_mlb = pearson(bx, by)
print(f"Pooled MLB win-pct lag-1 r: {r_mlb:.3f}  (n={len(bx)})")

# Mets specifically
mets = [r for r in mlb_records if "Mets" in r["team"]]
mets_pairs = {"mets": [(r["year"], r["win_pct"]) for r in mets]}
mx, my = autocorr_lag1(mets_pairs)
r_mets = pearson(mx, my)
print(f"Mets-only win-pct lag-1 r: {r_mets:.3f}  (n={len(mx)})")

# ─── 4) Save ───
out = {
    "snow": {
        "station": "Steamboat Springs, CO (USC00057936)",
        "series": snow_series,
        "lag1_r": round(r_snow, 4) if r_snow else None,
        "lag1_n": len(sx),
        "lag1_pairs": [{"prev": x, "next": y} for x, y in zip(sx, sy)],
    },
    "mlb": {
        "team_seasons": mlb_records,
        "pooled_lag1_r": round(r_mlb, 4) if r_mlb else None,
        "pooled_lag1_n": len(bx),
        "pooled_lag1_pairs": [{"prev": x, "next": y} for x, y in zip(bx, by)],
        "mets_lag1_r": round(r_mets, 4) if r_mets else None,
        "mets_lag1_n": len(mx),
    },
}
json.dump(out, open(ANALYSIS / "predictability_data.json", "w"), indent=2)
print(f"\nWrote predictability_data.json")
