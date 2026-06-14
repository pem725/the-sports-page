"""
Re-score the cross-domain comparison using Pearson r × 100 as the common
metric. For each domain:
  - Sports: lag-1 r (already have it; the optimal-lag-1 prediction is
    perfectly correlated with last year's value, so the skill r == lag1 r)
  - Snow: LOOCV-predict each season using its ENSO state's mean (excluding
    self), then compute Pearson r between predictions and actuals. This is
    the standard "anomaly correlation" / forecast-skill correlation.

The result is a signed metric bounded -100% to +100%, where the absolute
value tells you how informative the predictor is and the sign tells you
the direction.
"""
import json, math, statistics
from collections import defaultdict
from pathlib import Path

ANALYSIS = Path(__file__).parent
d = json.load(open(ANALYSIS / "predictability_v4.json"))

# Parse ENSO from ASCII
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

def pearson(xs, ys):
    n = len(xs)
    if n < 3: return None
    mx, my = sum(xs)/n, sum(ys)/n
    num = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    dx = sum((x-mx)**2 for x in xs)**0.5
    dy = sum((y-my)**2 for y in ys)**0.5
    return num/(dx*dy) if dx and dy else None

# Snow: LOOCV skill correlation per region
snow_skill = {}
for region, info in d["snow_series"].items():
    series = info["series"]
    pts = [(r["season_start"], r["snow_mm"]) for r in series]
    states = [enso_state(yr) for yr, _ in pts]
    preds, actuals = [], []
    for i, (yr, v) in enumerate(pts):
        st = states[i]
        if st is None: continue
        others = [v2 for j, (yr2, v2) in enumerate(pts)
                  if j != i and states[j] == st]
        if not others: continue
        preds.append(statistics.mean(others))
        actuals.append(v)
    r_skill = pearson(preds, actuals)
    snow_skill[region] = {"skill_r": round(r_skill, 4) if r_skill else None, "n": len(preds)}

print("Snow ENSO skill correlation (LOOCV predicted vs actual):")
for region, s in snow_skill.items():
    print(f"  {region:<22} r = {s['skill_r']:+.3f}  ({s['n']} predictions)")

# Sports lag-1: the optimal-lag-1 prediction is perfectly proportional to
# last year's value, so the Pearson r between predictions and actuals equals
# the lag-1 r itself.
sports_skill = {}
for sport in ("NBA","NHL","MLB","NFL"):
    sports_skill[sport] = {"skill_r": d["sports"][sport]["lag1_r"],
                            "n": d["sports"][sport]["n_pairs"]}

print("\nSports lag-1 skill correlation (== lag-1 r):")
for sport, s in sports_skill.items():
    print(f"  {sport}  r = {s['skill_r']:+.3f}  ({s['n']} pairs)")

# Save
out = {"sports": sports_skill, "snow": snow_skill,
       "snow_state_means": {r: d["snow_regions"][r].get("enso_state_means_mm", {})
                             for r in d["snow_regions"]}}
json.dump(out, open(ANALYSIS / "predictability_v5.json", "w"), indent=2)
print("\nWrote predictability_v5.json")

print("\n" + "="*60)
print("SCOREBOARD — Pearson r × 100 (signed, bounded -100 to +100)")
print("="*60)
for sport in ("NBA","NHL","MLB","NFL"):
    print(f"  {sport:<5} (lag-1):  {sports_skill[sport]['skill_r']*100:+6.1f}")
for region in ("Utah/Wyoming","Pacific Northwest","Colorado","Vermont","New Mexico"):
    if region in snow_skill:
        r = snow_skill[region]["skill_r"]
        if r is not None:
            print(f"  {region:<22} (ENSO):  {r*100:+6.1f}")
