"""
Region vs league apples-to-apples predictability test.
Pull 4 Colorado ski-belt stations, average them per season — this gives
a regional snow index analogous to MLB league OPS (both are aggregates).

Compare:
  * Region snowfall index — lag-1 + ENSO-conditional vs climatology baseline
  * MLB league OPS — lag-1 + 7-feature profile vs climatology baseline

Both aggregate-level. Apples-to-apples.

Bonus: also report the SINGLE-UNIT comparison (Steamboat + ENSO) and
(Mets + their own prior-2-year roster profile) for context.
"""
import csv, json, math, statistics, requests
from collections import defaultdict
from pathlib import Path

ANALYSIS = Path(__file__).parent
STATIONS = [
    ("USC00050372", "Aspen 1 SW"),
    ("USC00051959", "Crested Butte"),
    ("USC00057936", "Steamboat Springs"),
    ("USC00058204", "Telluride"),
    ("USC00058575", "Vail"),
]
# All four CSVs are already downloaded to /tmp/sn_<id>.csv

def parse_station_snow(path):
    by_season = defaultdict(float)
    by_season_days = defaultdict(int)
    with open(path) as f:
        for row in csv.DictReader(f):
            date = row.get("DATE", "")
            if len(date) < 10: continue
            try:
                yr, mo = int(date[:4]), int(date[5:7])
            except ValueError: continue
            snow = row.get("SNOW", "").strip()
            if not snow: continue
            try: s = float(snow)
            except ValueError: continue
            if s < 0: continue
            if mo in (11, 12):    season = yr
            elif mo in (1, 2, 3, 4): season = yr - 1
            else: continue
            by_season[season] += s
            by_season_days[season] += 1
    return {season: by_season[season] for season in by_season if by_season_days[season] >= 150}

print("Per-station seasonal snowfall (Nov–Apr):")
per_station = {}
for sid, name in STATIONS:
    series = parse_station_snow(f"/tmp/sn_{sid}.csv")
    per_station[sid] = (name, series)
    yrs_in_range = [y for y in series if 1985 <= y <= 2024]
    print(f"  {name:<22} {len(yrs_in_range)} seasons in 1985-2024")

# Build regional index = average of stations that have data that season
# Require at least 3 of the 4 stations reporting
all_seasons = sorted(set().union(*(set(s.keys()) for _, s in per_station.values())))
region_series = []
for season in all_seasons:
    if not (1985 <= season <= 2024): continue
    vals = [s[season] for _, s in per_station.values() if season in s]
    if len(vals) >= 3:
        region_series.append({"season_start": season, "snow_mm": round(statistics.mean(vals), 1),
                              "n_stations": len(vals)})
print(f"\nColorado regional snow index: {len(region_series)} seasons (≥3 stations each)")

# ENSO assignment (same as before)
oni_djf = {}
with open("/tmp/oni.ascii.txt") as f:
    for line in f.readlines()[1:]:
        p = line.split()
        if len(p) < 4 or p[0] != "DJF": continue
        try: oni_djf[int(p[1])] = float(p[3])
        except ValueError: continue
def enso_state(yr):
    a = oni_djf.get(yr+1)
    if a is None: return None
    if a >= 0.5: return "El Niño"
    if a <= -0.5: return "La Niña"
    return "Neutral"

region_pts = [(r["season_start"], r["snow_mm"], enso_state(r["season_start"])) for r in region_series
              if enso_state(r["season_start"]) is not None]

# Group means by ENSO state
print("\nRegional snow by ENSO state:")
by_state = defaultdict(list)
for _, v, st in region_pts: by_state[st].append(v)
for st in ("El Niño","La Niña","Neutral"):
    arr = by_state[st]
    if arr: print(f"  {st:<10} n={len(arr):<3} mean={statistics.mean(arr):.0f}  median={statistics.median(arr):.0f}")

# LOOCV
def loocv(points, predict_fn):
    errs = []
    for i, (k, v, pf) in enumerate(points):
        others = [p for j, p in enumerate(points) if j != i]
        pred = predict_fn(others, pf)
        if pred is None: continue
        errs.append((v - pred)**2)
    return math.sqrt(statistics.mean(errs)) if errs else None, len(errs)

def clim(others, _): return statistics.mean(v for _,v,_ in others) if others else None
def cond(others, pf):
    m = [v for _,v,p in others if p == pf]
    return statistics.mean(m) if m else clim(others, pf)

rmse_clim, n = loocv(region_pts, clim)
rmse_enso, _ = loocv(region_pts, cond)
lift = 100*(rmse_clim - rmse_enso)/rmse_clim
print(f"\nRegional snow LOOCV (n={n}):")
print(f"  Climatology RMSE : {rmse_clim:.1f} mm")
print(f"  ENSO RMSE        : {rmse_enso:.1f} mm")
print(f"  % reduction      : {lift:+.1f}%")

# Lag-1 r for region
def autocorr_lag1_series(series):
    pairs = sorted([(r["season_start"], r["snow_mm"]) for r in series])
    xs, ys = [], []
    for i in range(len(pairs)-1):
        if pairs[i+1][0] - pairs[i][0] == 1:
            xs.append(pairs[i][1]); ys.append(pairs[i+1][1])
    n = len(xs)
    if n < 2: return None, 0
    mx, my = sum(xs)/n, sum(ys)/n
    num = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    dx = sum((x-mx)**2 for x in xs)**0.5; dy = sum((y-my)**2 for y in ys)**0.5
    return num/(dx*dy) if dx and dy else None, n

r_region, n_region = autocorr_lag1_series(region_series)
print(f"\nRegional snow lag-1 r: {r_region:.3f}  (n={n_region} pairs)")

# Save
out = {
    "region_snow": {
        "stations": [s[1] for s in STATIONS],
        "series": region_series,
        "by_state": {st: {"n":len(by_state[st]),"mean":round(statistics.mean(by_state[st]),1),
                          "median":round(statistics.median(by_state[st]),1)} for st in by_state},
        "lag1_r": round(r_region, 4) if r_region else None,
        "lag1_n": n_region,
        "rmse_climatology": round(rmse_clim, 1),
        "rmse_enso":         round(rmse_enso, 1),
        "rmse_reduction_pct": round(lift, 2),
        "n_pairs": n,
    },
}

# Also stitch in the MLB league results from the v2 analysis
v2 = json.load(open(ANALYSIS / "predictability_v2.json"))
out["mlb_league"] = v2["mlb"]
# And the single-unit lag-1 numbers
v1 = json.load(open(ANALYSIS / "predictability_data.json"))
out["steamboat_single"] = {
    "lag1_r": v1["snow"]["lag1_r"], "n": v1["snow"]["lag1_n"],
}
out["mets_single"] = {
    "lag1_r": v1["mlb"]["mets_lag1_r"], "n": v1["mlb"]["mets_lag1_n"],
}

json.dump(out, open(ANALYSIS / "predictability_v3.json", "w"), indent=2)
print(f"\nWrote predictability_v3.json")
print(f"\n=== AGGREGATE-LEVEL COMPARISON (apples-to-apples) ===")
print(f"  CO regional snow lag-1 r:  {r_region:+.3f}  vs MLB league lag-1... (need to compute)")
print(f"  CO regional snow ENSO lift: {lift:+.1f}%   vs MLB league profile lift: {out['mlb_league']['rmse_reduction_pct']:+.1f}%")
print(f"\n=== SINGLE-UNIT COMPARISON (also apples-to-apples) ===")
print(f"  Steamboat lag-1 r: {out['steamboat_single']['lag1_r']:+.3f}")
print(f"  Mets lag-1 r:      {out['mets_single']['lag1_r']:+.3f}")
