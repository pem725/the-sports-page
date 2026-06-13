"""
Compute pooled lag-1 autocorrelation of team win pct per sport: MLB, NFL, NHL, NBA.
For comparison: Steamboat single-station snowfall, CO regional snowfall, S&P 500 annual returns.

Output: predictability_cross_sport.json with r values and pair lists for charting.
"""
import csv, json, math, statistics
from pathlib import Path
from collections import defaultdict

ANALYSIS = Path(__file__).parent

def to_int(x):
    try: return int(x)
    except: return None
def to_float(x):
    try: return float(x)
    except: return None

# ── MLB (from earlier predictability_data) ──
mlb = json.load(open(ANALYSIS / "predictability_data.json"))["mlb"]["team_seasons"]
mlb_pairs_by_team = defaultdict(list)
for r in mlb:
    mlb_pairs_by_team[r["team_id"]].append((int(r["year"]), float(r["win_pct"])))

# ── NFL/NBA/NHL ──
by_sport_by_team = defaultdict(lambda: defaultdict(list))
for row in csv.DictReader(open(ANALYSIS / "cross_sport_standings.csv")):
    wp = to_float(row["win_pct"])
    if wp is None:
        # NHL: compute from wins/losses/ties since ESPN doesn't return winPercent
        w = to_int(row["wins"]); l = to_int(row["losses"]); t = to_int(row["ties"]) or 0
        if w is None or l is None: continue
        gp = w + l + t
        if gp < 10: continue
        wp = (w + 0.5*t) / gp
    by_sport_by_team[row["sport"]][row["team_id"]].append((int(row["season_end"]), wp))

def lag1(pairs_by_key):
    xs, ys = [], []
    for k, lst in pairs_by_key.items():
        lst = sorted(lst)
        for i in range(len(lst)-1):
            (y1, v1), (y2, v2) = lst[i], lst[i+1]
            if y2 - y1 == 1:
                xs.append(v1); ys.append(v2)
    n = len(xs)
    if n < 2: return None, 0, []
    mx, my = sum(xs)/n, sum(ys)/n
    num = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    dx = sum((x-mx)**2 for x in xs)**0.5; dy = sum((y-my)**2 for y in ys)**0.5
    r = num/(dx*dy) if dx and dy else None
    pairs = [{"prev": x, "next": y} for x, y in zip(xs, ys)]
    return r, n, pairs

results = {}
for sport, tname in [("MLB","MLB"),("NFL","NFL"),("NBA","NBA"),("NHL","NHL")]:
    src = mlb_pairs_by_team if sport == "MLB" else by_sport_by_team[sport]
    r, n, pairs = lag1(src)
    results[sport] = {"lag1_r": round(r, 4), "n_pairs": n, "pairs": pairs}
    print(f"{sport}: lag-1 r = {r:.3f}  (n={n})")

# ── Steamboat snow + CO region snow ──
snow_single = json.load(open(ANALYSIS / "predictability_data.json"))["snow"]
results["Steamboat snow"] = {"lag1_r": snow_single["lag1_r"], "n_pairs": snow_single["lag1_n"],
                              "pairs": snow_single["lag1_pairs"]}
snow_region = json.load(open(ANALYSIS / "predictability_v3.json"))["region_snow"]
pairs = sorted([(r["season_start"], r["snow_mm"]) for r in snow_region["series"]])
xs, ys = [], []
for i in range(len(pairs)-1):
    if pairs[i+1][0] - pairs[i][0] == 1:
        xs.append(pairs[i][1]); ys.append(pairs[i+1][1])
results["CO ski region snow"] = {"lag1_r": snow_region["lag1_r"], "n_pairs": snow_region["lag1_n"],
                                  "pairs": [{"prev": x, "next": y} for x, y in zip(xs, ys)]}

# ── S&P 500 annual returns ──
# Yahoo Finance: ^GSPC historical. Use Stooq mirror for ease.
import requests
print("\nPulling S&P 500 daily from Stooq...")
r = requests.get("https://stooq.com/q/d/l/?s=^spx&i=d", headers={"User-Agent":"curl/8.0"}, timeout=30)
if r.status_code == 200 and len(r.text) > 1000:
    # CSV: Date,Open,High,Low,Close,Volume
    annual_close = {}
    for line in r.text.splitlines()[1:]:
        parts = line.split(",")
        if len(parts) < 5: continue
        date = parts[0]; close = parts[4]
        try:
            yr = int(date[:4]); c = float(close)
        except ValueError: continue
        # Last quote of the year wins (we'll see all year's data)
        annual_close[yr] = c
    # Annual return = (close_y - close_{y-1}) / close_{y-1}
    years = sorted(annual_close.keys())
    returns = []
    for i in range(1, len(years)):
        if years[i] - years[i-1] == 1 and 1985 <= years[i] <= 2025:
            ret = (annual_close[years[i]] - annual_close[years[i-1]]) / annual_close[years[i-1]]
            returns.append((years[i], ret))
    # Lag-1 on returns
    pairs = sorted(returns)
    xs, ys = [], []
    for i in range(len(pairs)-1):
        if pairs[i+1][0] - pairs[i][0] == 1:
            xs.append(pairs[i][1]); ys.append(pairs[i+1][1])
    n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    num = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    dx = sum((x-mx)**2 for x in xs)**0.5; dy = sum((y-my)**2 for y in ys)**0.5
    r_sp = num/(dx*dy) if dx and dy else None
    results["S&P 500 ann ret"] = {"lag1_r": round(r_sp, 4), "n_pairs": n,
                                   "pairs": [{"prev": x, "next": y} for x, y in zip(xs, ys)],
                                   "note": "annual returns; mean-reverting by design"}
    print(f"S&P 500 ann returns: lag-1 r = {r_sp:.3f} (n={n})")
else:
    print(f"S&P pull failed: HTTP {r.status_code}")

json.dump(results, open(ANALYSIS / "predictability_cross_sport.json", "w"), indent=2)
print(f"\nWrote predictability_cross_sport.json")
print(f"\n{'system':<22} {'lag-1 r':<10} {'n pairs':<10}")
print("-"*45)
for k, v in results.items():
    print(f"  {k:<20} {v['lag1_r']:+.3f}     {v['n_pairs']}")
