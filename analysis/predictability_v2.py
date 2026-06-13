"""
Conditional prediction comparison:
  Q1: Does ENSO state predict ski-season snowfall better than climatology baseline?
  Q2: Does profile-matching predict next-year MLB league OPS better than climatology baseline?

Both are tested via leave-one-out cross-validation. Metric: RMSE,
plus % reduction from baseline.
"""
import json, csv, math
from pathlib import Path
from collections import defaultdict
import statistics

ANALYSIS = Path(__file__).parent

# ──────────────── ENSO STATE PER YEAR ────────────────
# Parse NOAA ONI ascii. Format: " SEAS  YR   TOTAL   ANOM"
oni_djf = {}  # year -> DJF anomaly (DJF YR = Dec YR-1 + Jan YR + Feb YR)
with open("/tmp/oni.ascii.txt") as f:
    for line in f.readlines()[1:]:  # skip header
        parts = line.split()
        if len(parts) < 4: continue
        seas, yr_s, total_s, anom_s = parts[0], parts[1], parts[2], parts[3]
        if seas != "DJF": continue
        try:
            yr = int(yr_s); anom = float(anom_s)
        except ValueError: continue
        oni_djf[yr] = anom

def enso_state(anom):
    if anom is None: return None
    if anom >= 0.5:  return "El Niño"
    if anom <= -0.5: return "La Niña"
    return "Neutral"

# Map ski-season-start-year → ENSO state via DJF of year+1
def season_enso(season_start):
    anom = oni_djf.get(season_start + 1)
    return enso_state(anom)

# ──────────────── SNOW DATA ────────────────
snow_data = json.load(open(ANALYSIS / "predictability_data.json"))["snow"]["series"]
print("Steamboat ski seasons (Nov→Apr) by ENSO state:")
counts = defaultdict(int); means = defaultdict(list)
for s in snow_data:
    yr = s["season_start"]; sn = s["snow_mm"]
    state = season_enso(yr)
    if state is None: continue
    counts[state] += 1
    means[state].append(sn)
for state in ("El Niño", "La Niña", "Neutral"):
    arr = means[state]
    if arr:
        print(f"  {state:<10} n={len(arr):<3} mean={statistics.mean(arr):.0f}mm  median={statistics.median(arr):.0f}mm")

# ──────────────── LOOCV: SNOW ────────────────
# Build (yr, snow, state) only for years with valid state
snow_pts = [(s["season_start"], s["snow_mm"], season_enso(s["season_start"]))
            for s in snow_data if season_enso(s["season_start"]) is not None]

def loocv_rmse(points, predict_fn):
    """points: [(key, value, profile)]. predict_fn(other_points, target_profile) -> prediction."""
    errs = []
    for i, (k, v, pf) in enumerate(points):
        others = [p for j, p in enumerate(points) if j != i]
        pred = predict_fn(others, pf)
        if pred is None: continue
        errs.append((v - pred)**2)
    return math.sqrt(statistics.mean(errs)) if errs else None, len(errs)

def predict_climatology(others, target_profile=None):
    return statistics.mean(v for _, v, _ in others) if others else None

def predict_by_profile(others, target_profile):
    matched = [v for _, v, pf in others if pf == target_profile]
    if not matched: return predict_climatology(others)
    return statistics.mean(matched)

rmse_clim_snow, n_snow = loocv_rmse(snow_pts, predict_climatology)
rmse_enso_snow, _ = loocv_rmse(snow_pts, predict_by_profile)
lift_snow = 100 * (rmse_clim_snow - rmse_enso_snow) / rmse_clim_snow

print(f"\nSnowfall LOOCV (n={n_snow})")
print(f"  RMSE climatology only   : {rmse_clim_snow:.0f} mm")
print(f"  RMSE ENSO-conditioned   : {rmse_enso_snow:.0f} mm")
print(f"  % reduction in RMSE     : {lift_snow:+.1f}%")

# ──────────────── LOOCV: MLB BY PROFILE-MATCH ────────────────
# Predict each year's league OPS from k=3 nearest *prior* years.
features = json.load(open(ANALYSIS / "analog_year_results.json"))
year_features = features["features"]  # str(year) -> {...}
FEATS = ["K_PA","BB_PA","HR_PA","ERA","K_9","BB_9","HR_9"]  # exclude OPS — it's the target
years = sorted(int(y) for y in year_features.keys() if int(y) <= 2025)

def z_vec(year, mu, sd):
    return [(year_features[str(year)][k] - mu[k]) / sd[k] for k in FEATS]

def dist(va, vb):
    return math.sqrt(sum((a-b)**2 for a, b in zip(va, vb)))

errs_clim = []; errs_prof = []
# We need a warm-up: at least 10 prior years to have a meaningful baseline
for i, yr in enumerate(years):
    prior = years[:i]
    if len(prior) < 10: continue
    target_ops = year_features[str(yr)]["OPS"]
    # Climatology: mean OPS of all prior years
    clim = statistics.mean(year_features[str(y)]["OPS"] for y in prior)
    errs_clim.append((target_ops - clim)**2)
    # Profile: standardize across prior years only, find k nearest
    mu = {k: statistics.mean(year_features[str(y)][k] for y in prior) for k in FEATS}
    sd = {k: statistics.stdev(year_features[str(y)][k] for y in prior) for k in FEATS}
    target_vec = z_vec(yr, mu, sd)
    dists = sorted((dist(z_vec(y, mu, sd), target_vec), y) for y in prior)
    k = 3
    neighbors = [y for _, y in dists[:k]]
    prof = statistics.mean(year_features[str(y)]["OPS"] for y in neighbors)
    errs_prof.append((target_ops - prof)**2)

rmse_clim_mlb = math.sqrt(statistics.mean(errs_clim))
rmse_prof_mlb = math.sqrt(statistics.mean(errs_prof))
lift_mlb = 100 * (rmse_clim_mlb - rmse_prof_mlb) / rmse_clim_mlb

print(f"\nMLB league OPS LOOCV (n={len(errs_clim)})")
print(f"  RMSE climatology only          : {rmse_clim_mlb:.4f}")
print(f"  RMSE 3-nearest profile match   : {rmse_prof_mlb:.4f}")
print(f"  % reduction in RMSE            : {lift_mlb:+.1f}%")

# ──────────────── SAVE ────────────────
out = {
    "snow": {
        "by_state": {s: {"n": len(means[s]), "mean": round(statistics.mean(means[s]),1),
                         "median": round(statistics.median(means[s]),1),
                         "std": round(statistics.stdev(means[s]),1) if len(means[s])>1 else None}
                    for s in ("El Niño","La Niña","Neutral") if means[s]},
        "rmse_climatology": round(rmse_clim_snow, 1),
        "rmse_enso":         round(rmse_enso_snow, 1),
        "rmse_reduction_pct": round(lift_snow, 2),
        "n_pairs": n_snow,
    },
    "mlb": {
        "rmse_climatology": round(rmse_clim_mlb, 4),
        "rmse_profile":     round(rmse_prof_mlb, 4),
        "rmse_reduction_pct": round(lift_mlb, 2),
        "n_pairs": len(errs_clim),
    },
}
json.dump(out, open(ANALYSIS / "predictability_v2.json", "w"), indent=2)
print(f"\nWrote predictability_v2.json")
print(f"\n========================================")
print(f"  SUMMARY: WHICH SYSTEM REWARDS CONDITIONING MORE?")
print(f"  Snowfall: {lift_snow:+.1f}% RMSE reduction by ENSO")
print(f"  Baseball: {lift_mlb:+.1f}% RMSE reduction by profile match")
print(f"========================================")
