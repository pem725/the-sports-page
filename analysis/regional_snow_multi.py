"""
Build seasonal snowfall indices for five ski regions and compute the
RIGHT predictor for each: ENSO-conditional model vs climatology baseline,
measured as leave-one-out % RMSE reduction. Same metric for sports uses
lag-1 model vs climatology (league mean) baseline.

Regions and stations (NOAA GHCN-Daily):
  Colorado   — Aspen 1 SW, Crested Butte, Steamboat Springs, Telluride 4 WNW, Vail
  PNW        — Stampede Pass (WA), Snoqualmie Falls (WA), Crater Lake (OR)
  Utah/WY    — Lake Yellowstone (WY), Yellowstone Mammoth (WY), Altamont (UT), Angle (UT)
  New Mexico — Red River, Dulce
  Vermont    — Saint Johnsbury, Island Pond, Burlington Intl
"""
import csv, json, math, statistics
from collections import defaultdict
from pathlib import Path

ANALYSIS = Path(__file__).parent

REGIONS = {
    "Colorado":         [("USC00050372","Aspen 1 SW"), ("USC00051959","Crested Butte"),
                         ("USC00057936","Steamboat Springs"), ("USC00058204","Telluride"),
                         ("USC00058575","Vail")],
    "Pacific Northwest":[("USW00024237","Stampede Pass"), ("USC00457773","Snoqualmie Falls"),
                         ("USC00351946","Crater Lake")],
    "Utah/Wyoming":     [("USC00485345","Lake Yellowstone"), ("USC00489905","Yellowstone Mammoth"),
                         ("USC00420074","Altamont"), ("USC00420168","Angle")],
    "New Mexico":       [("USC00297323","Red River"), ("USC00292608","Dulce")],
    "Vermont":          [("USC00437054","Saint Johnsbury"), ("USC00434120","Island Pond"),
                         ("USW00014742","Burlington Intl")],
}

def parse_station(path):
    """Return {season_start_year: total_snow_mm} for seasons with >=150 days reported."""
    season_snow = defaultdict(float)
    days = defaultdict(int)
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
            if mo in (11, 12):       season = yr
            elif mo in (1, 2, 3, 4): season = yr - 1
            else: continue
            season_snow[season] += s
            days[season] += 1
    return {s: season_snow[s] for s in season_snow if days[s] >= 150}

# Build region indices: mean across stations reporting that season, ≥ floor(stations/2) coverage
region_series = {}
for region, stations in REGIONS.items():
    per_station = {}
    for sid, sname in stations:
        path = Path(f"/tmp/sn_{sid}.csv")
        if not path.exists():
            print(f"  ! missing {region}/{sid} ({sname})")
            continue
        per_station[sid] = parse_station(path)
    if not per_station: continue
    all_seasons = sorted(set().union(*(set(s.keys()) for s in per_station.values())))
    min_stations = max(2, (len(per_station)+1) // 2)
    series = []
    for season in all_seasons:
        if not (1985 <= season <= 2024): continue
        vals = [s[season] for s in per_station.values() if season in s]
        if len(vals) >= min_stations:
            series.append({"season_start": season, "snow_mm": round(statistics.mean(vals), 1),
                           "n_stations": len(vals)})
    region_series[region] = {"stations": [n for _, n in stations], "series": series}
    print(f"  {region:<22} {len(series)} seasons (≥{min_stations} stations)")

# Load ENSO
oni = {}
with open("/tmp/oni.ascii.txt") as f:
    for line in f.readlines()[1:]:
        p = line.split()
        if len(p) < 4 or p[0] != "DJF": continue
        try: oni[int(p[1])] = float(p[3])
        except ValueError: continue

def enso_state(season_start):
    a = oni.get(season_start + 1)
    if a is None: return None
    if a >= 0.5: return "El Niño"
    if a <= -0.5: return "La Niña"
    return "Neutral"

def loocv_rmse(points, predict_fn):
    errs = []
    for i, (k, v, pf) in enumerate(points):
        others = [p for j, p in enumerate(points) if j != i]
        pred = predict_fn(others, pf)
        if pred is None: continue
        errs.append((v - pred)**2)
    return math.sqrt(statistics.mean(errs)) if errs else None, len(errs)

def clim(others, _):
    if not others: return None
    return statistics.mean(v for _, v, _ in others)
def cond(others, pf):
    matched = [v for _, v, p in others if p == pf]
    if not matched: return clim(others, pf)
    return statistics.mean(matched)

def autocorr_lag1(series):
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
    return (num/(dx*dy) if dx and dy else None), n

results_snow = {}
print("\nRegion: lag-1 r + ENSO-conditional % RMSE reduction")
for region, data in region_series.items():
    pts = [(r["season_start"], r["snow_mm"], enso_state(r["season_start"])) for r in data["series"]
           if enso_state(r["season_start"]) is not None]
    r_lag1, n_lag1 = autocorr_lag1(data["series"])
    rmse_c, n = loocv_rmse(pts, clim)
    rmse_e, _ = loocv_rmse(pts, cond)
    lift = 100*(rmse_c - rmse_e)/rmse_c if rmse_c else 0
    # ENSO group means for context
    by_st = defaultdict(list)
    for _, v, st in pts: by_st[st].append(v)
    state_means = {st: round(statistics.mean(vals), 0) for st, vals in by_st.items() if vals}
    results_snow[region] = {
        "n_stations": len(data["stations"]), "n_seasons": len(data["series"]),
        "lag1_r": round(r_lag1, 4) if r_lag1 else None,
        "rmse_climatology": round(rmse_c, 1), "rmse_enso": round(rmse_e, 1),
        "rmse_reduction_pct": round(lift, 2),
        "enso_state_means_mm": state_means, "n_enso_pairs": n,
    }
    print(f"  {region:<22} lag1 r={r_lag1:+.3f}  ENSO lift={lift:+5.1f}%  (n_seas={len(data['series'])}, n_pairs={n})")
    print(f"     state means: " + ", ".join(f"{st}={state_means.get(st,'—')}" for st in ("La Niña","Neutral","El Niño")))

# ─── Sports: OPTIMAL lag-1 model vs climatology baseline, % RMSE reduction ───
# The NAIVE "predict y_{t+1} = y_t" over-predicts variance when r < 1.
# The OPTIMAL linear lag-1 predictor is: y_hat = mean + r*(x - mean), which gives
# RMSE_optimal = RMSE_clim * sqrt(1 - r^2). So % RMSE reduction = 1 - sqrt(1-r^2).
# This is what a regression model fit on the same data would produce.
print("\nSport: OPTIMAL lag-1 % RMSE reduction = 1 - sqrt(1 - r^2)")
all_pairs = json.load(open(ANALYSIS / "predictability_cross_sport.json"))
results_sport = {}
for sport in ("NBA","NHL","MLB","NFL"):
    r = all_pairs[sport]["lag1_r"]
    lift = 100 * (1 - math.sqrt(1 - r*r))
    results_sport[sport] = {
        "lag1_r": r,
        "rmse_reduction_pct": round(lift, 2),
        "n_pairs": all_pairs[sport]["n_pairs"],
    }
    print(f"  {sport:<5}  lag1 r={r:+.3f}  optimal lift={lift:+5.1f}%")

# Save
out = {
    "snow_regions": {r: results_snow[r] for r in REGIONS if r in results_snow},
    "sports": results_sport,
    "snow_series": region_series,
}
json.dump(out, open(ANALYSIS / "predictability_v4.json", "w"), indent=2)
print(f"\nWrote predictability_v4.json")

print("\n" + "="*70)
print("SCOREBOARD — % RMSE reduction by best-domain-appropriate predictor")
print("="*70)
print(f"{'Domain (predictor)':<35} {'% RMSE reduction':>20}")
for sport in ("NBA","NHL","MLB","NFL"):
    print(f"  {sport+' (lag-1: prior year)':<33} {results_sport[sport]['rmse_reduction_pct']:>18.1f}%")
for region in REGIONS:
    if region in results_snow:
        print(f"  {region+' (ENSO state)':<33} {results_snow[region]['rmse_reduction_pct']:>18.1f}%")
