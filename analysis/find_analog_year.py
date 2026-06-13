"""
For each MLB season 1985-2026 (2026 partial), compute league rate stats:
  K_PA, BB_PA, HR_PA, OPS_PAW, ERA, K_9, BB_9, HR_9
Then z-score across years and find the nearest neighbor to 2026.

Outputs:
  league_features_by_year.csv
  prints nearest neighbor analysis
"""
import csv, json, statistics, math
from collections import defaultdict
from pathlib import Path

ANALYSIS = Path(__file__).parent

def to_int(x):
    try: return int(x)
    except: return None
def to_float(x):
    try: return float(x) if x not in ("", None) else None
    except: return None

# ---------- Hitter aggregates per year ----------
hit_year = defaultdict(lambda: {"PA":0,"AB":0,"H":0,"HR":0,"BB":0,"SO":0,
                                "OPS_num":0.0,"OPS_den":0,
                                "OBP_num":0.0,"OBP_den":0,
                                "SLG_num":0.0,"SLG_den":0,
                                "AVG_num":0.0,"AVG_den":0})

def add_hit_row(year, row):
    d = hit_year[year]
    pa = to_int(row.get("PA")) or 0
    if pa < 1: return
    ab = to_int(row.get("AB")) or 0
    d["PA"] += pa
    d["AB"] += ab
    # H may not be in historical CSV — derive from AVG × AB
    h_field = to_int(row.get("H"))
    if h_field is not None:
        d["H"] += h_field
    else:
        avg = to_float(row.get("AVG"))
        if avg is not None and ab:
            d["H"] += round(avg * ab)
    d["HR"] += to_int(row.get("HR")) or 0
    d["BB"] += to_int(row.get("BB")) or 0
    d["SO"] += to_int(row.get("SO")) or 0
    ops = to_float(row.get("OPS"))
    if ops is not None:
        d["OPS_num"] += ops * pa; d["OPS_den"] += pa

# Historical: 1985-2025 from all_hitters_seasons.csv
for row in csv.DictReader(open(ANALYSIS / "all_hitters_seasons.csv")):
    add_hit_row(int(row["year"]), row)

# 2026 partial
for row in csv.DictReader(open(ANALYSIS / "all_hitters_2026_partial.csv")):
    add_hit_row(2026, row)

# ---------- Pitcher aggregates per year ----------
pit_year = defaultdict(lambda: {"IP":0.0,"K":0,"BB":0,"HR":0,"ER":0})

def add_pit_row(year, row):
    d = pit_year[year]
    ip = to_float(row.get("IP")) or 0
    if ip < 0.1: return
    d["IP"] += ip
    d["K"]  += to_int(row.get("K")) or 0
    d["BB"] += to_int(row.get("BB")) or 0
    d["HR"] += to_int(row.get("HR")) or 0
    # ER may not be in historical CSV — derive from ERA × IP / 9
    er = to_int(row.get("ER"))
    if er is not None:
        d["ER"] += er
    else:
        era = to_float(row.get("ERA"))
        if era is not None and ip:
            d["ER"] += era * ip / 9

for row in csv.DictReader(open(ANALYSIS / "all_pitchers_seasons.csv")):
    add_pit_row(int(row["year"]), row)
for row in csv.DictReader(open(ANALYSIS / "all_pitchers_2026_partial.csv")):
    add_pit_row(2026, row)

# ---------- Build feature matrix ----------
years = sorted(set(hit_year) & set(pit_year))
features = {}
for y in years:
    h = hit_year[y]; p = pit_year[y]
    if h["PA"] < 1000 or p["IP"] < 100: continue
    features[y] = {
        "OPS":   round(h["OPS_num"]/h["OPS_den"], 4) if h["OPS_den"] else None,
        "K_PA":  round(h["SO"]/h["PA"], 5),
        "BB_PA": round(h["BB"]/h["PA"], 5),
        "HR_PA": round(h["HR"]/h["PA"], 5),
        "AVG":   round(h["H"]/h["AB"], 4) if h["AB"] else None,
        "ERA":   round(p["ER"]*9/p["IP"], 3),
        "K_9":   round(p["K"]*9/p["IP"], 3),
        "BB_9":  round(p["BB"]*9/p["IP"], 3),
        "HR_9":  round(p["HR"]*9/p["IP"], 3),
    }

# Print table
print("League rate features by year:")
keys = list(features[years[0]].keys())
print("year " + " ".join(f"{k:>8}" for k in keys))
for y in years:
    f = features[y]
    print(f"{y} " + " ".join(f"{f[k]:>8}" for k in keys))

# ---------- Standardize + nearest neighbor to 2026 ----------
FEATURES_USED = ["OPS","K_PA","BB_PA","HR_PA","ERA","K_9","BB_9","HR_9"]
hist_years = [y for y in years if y != 2026]
target_year = 2026

# Compute mean/std across historical years for each feature
mu = {k: statistics.mean(features[y][k] for y in hist_years) for k in FEATURES_USED}
sd = {k: statistics.stdev(features[y][k] for y in hist_years) for k in FEATURES_USED}

def z_vec(y):
    return [(features[y][k] - mu[k]) / sd[k] for k in FEATURES_USED]

def dist(va, vb):
    return math.sqrt(sum((a-b)**2 for a, b in zip(va, vb)))

t_vec = z_vec(target_year)
dists = [(y, dist(z_vec(y), t_vec)) for y in hist_years]
dists.sort(key=lambda x: x[1])

print(f"\nNearest historical analogs to {target_year} (z-Euclidean distance):")
for y, d in dists[:10]:
    print(f"  {y}: distance={d:.3f}")

# Print 2026 vs nearest year side-by-side
near = dists[0][0]
print(f"\n2026 vs {near} side-by-side:")
print(f"  feature  | {target_year:>8} | {near:>8} | diff")
for k in FEATURES_USED:
    a = features[target_year][k]; b = features[near][k]
    print(f"  {k:<8} | {a:>8} | {b:>8} | {a-b:+.4f}")

# Save
with open(ANALYSIS / "league_features_by_year.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["year"]+keys)
    w.writeheader()
    for y in years:
        row = {"year": y}; row.update(features[y]); w.writerow(row)

# Also save full distance ranking + per-year z-vectors
out = {
    "years": years,
    "features": features,
    "z_features": {y: z_vec(y) for y in years},
    "mu": mu, "sd": sd,
    "features_used": FEATURES_USED,
    "ranking_2026": [{"year": y, "distance": round(d, 4)} for y, d in dists],
}
json.dump(out, open(ANALYSIS / "analog_year_results.json", "w"), indent=2)
print(f"\nWrote league_features_by_year.csv and analog_year_results.json")
