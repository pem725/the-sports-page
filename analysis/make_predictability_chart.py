"""Two-panel SVG: Snow lag-1 scatter | MLB win-pct lag-1 scatter, with regression lines and r."""
import json
from pathlib import Path
import statistics

import random
random.seed(7)
d = json.load(open(Path(__file__).parent / "predictability_data.json"))
snow_pairs = d["snow"]["lag1_pairs"]
mlb_pairs_all = d["mlb"]["pooled_lag1_pairs"]
# Subsample MLB to ~300 for chart readability/size (correlation stays clear at any sample)
mlb_pairs = random.sample(mlb_pairs_all, min(300, len(mlb_pairs_all)))
r_snow = d["snow"]["lag1_r"]
r_mlb  = d["mlb"]["pooled_lag1_r"]
r_mets = d["mlb"]["mets_lag1_r"]

def fit(pairs):
    xs = [p["prev"] for p in pairs]; ys = [p["next"] for p in pairs]
    n = len(xs)
    mx = sum(xs)/n; my = sum(ys)/n
    sxx = sum((x-mx)**2 for x in xs); sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    slope = sxy/sxx if sxx else 0
    intercept = my - slope*mx
    return slope, intercept, mx, my

# Layout
W, H = 760, 420
PANEL_W = (W - 80) / 2  # two panels with gap
MT, MB = 40, 70
plot_h = H - MT - MB

panels = [
    {"title": "Steamboat snowfall, season T vs season T+1",
     "subtitle": f"Pearson r = {r_snow:.3f} · n = {d['snow']['lag1_n']} season pairs",
     "x_label": "snow (mm), season t",
     "y_label": "snow (mm), season t+1",
     "pairs": snow_pairs,
     "color": "#2c4a6e",
     "x_lo": 0, "x_hi": max(max(p["prev"] for p in snow_pairs), max(p["next"] for p in snow_pairs)) * 1.05,
     "y_lo": 0, "y_hi": max(max(p["prev"] for p in snow_pairs), max(p["next"] for p in snow_pairs)) * 1.05,
    },
    {"title": "MLB team win pct, year T vs year T+1",
     "subtitle": f"All teams pooled · Pearson r = {r_mlb:.3f} · n = {d['mlb']['pooled_lag1_n']} team-pairs",
     "x_label": "win pct, year t",
     "y_label": "win pct, year t+1",
     "pairs": mlb_pairs,
     "color": "#b83a1e",
     "x_lo": 0.25, "x_hi": 0.75, "y_lo": 0.25, "y_hi": 0.75,
    },
]

svg = [f'<svg class="chart" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Roboto Mono\',monospace">']
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ede5d2"/>')

for i, p in enumerate(panels):
    ML = 60 + i * (PANEL_W + 20)
    plot_w = PANEL_W - 80
    def X(v): return ML + (v - p["x_lo"]) / (p["x_hi"] - p["x_lo"]) * plot_w
    def Y(v): return MT + plot_h * (1 - (v - p["y_lo"]) / (p["y_hi"] - p["y_lo"]))

    # Title
    svg.append(f'<text x="{ML + plot_w/2}" y="{MT-22}" text-anchor="middle" font-family="Playfair Display" font-size="13" font-weight="700" fill="#1a1208">{p["title"]}</text>')
    svg.append(f'<text x="{ML + plot_w/2}" y="{MT-6}" text-anchor="middle" font-size="10" fill="#6b5e4a">{p["subtitle"]}</text>')

    # Gridlines
    if i == 0:
        x_ticks = [0, 1000, 2000, 3000]
        y_ticks = [0, 1000, 2000, 3000]
    else:
        x_ticks = [0.30, 0.40, 0.50, 0.60, 0.70]
        y_ticks = [0.30, 0.40, 0.50, 0.60, 0.70]
    for v in x_ticks:
        if v < p["x_lo"] or v > p["x_hi"]: continue
        x = X(v)
        svg.append(f'<line x1="{x}" y1="{MT}" x2="{x}" y2="{MT+plot_h}" stroke="#c8b99a" stroke-width="1" stroke-dasharray="3,3"/>')
        label = f"{int(v)}" if i == 0 else f"{v:.2f}"
        svg.append(f'<text x="{x}" y="{MT+plot_h+16}" text-anchor="middle" font-size="10" fill="#1a1208">{label}</text>')
    for v in y_ticks:
        if v < p["y_lo"] or v > p["y_hi"]: continue
        y = Y(v)
        svg.append(f'<line x1="{ML}" y1="{y}" x2="{ML+plot_w}" y2="{y}" stroke="#c8b99a" stroke-width="1" stroke-dasharray="3,3"/>')
        label = f"{int(v)}" if i == 0 else f"{v:.2f}"
        svg.append(f'<text x="{ML-6}" y="{y+3}" text-anchor="end" font-size="10" fill="#6b5e4a">{label}</text>')

    # Diagonal y=x line (faint)
    svg.append(f'<line x1="{X(p["x_lo"])}" y1="{Y(p["y_lo"])}" x2="{X(p["x_hi"])}" y2="{Y(p["y_hi"])}" stroke="#6b5e4a" stroke-width="1" stroke-dasharray="2,4" opacity="0.3"/>')

    # Axis box
    svg.append(f'<line x1="{ML}" y1="{MT}" x2="{ML}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')
    svg.append(f'<line x1="{ML}" y1="{MT+plot_h}" x2="{ML+plot_w}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')
    svg.append(f'<text x="{ML+plot_w/2}" y="{H-28}" text-anchor="middle" font-size="11" fill="#1a1208" font-weight="600">{p["x_label"]}</text>')
    svg.append(f'<text transform="rotate(-90,{ML-40},{MT+plot_h/2})" x="{ML-40}" y="{MT+plot_h/2}" text-anchor="middle" font-size="11" fill="#1a1208" font-weight="600">{p["y_label"]}</text>')

    # Dots
    for pair in p["pairs"]:
        x = X(pair["prev"]); y = Y(pair["next"])
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{p["color"]}" fill-opacity="0.55"/>')

    # Regression line
    slope, intercept, mx, my = fit(p["pairs"])
    x0 = p["x_lo"]; x1 = p["x_hi"]
    y0 = slope*x0 + intercept; y1 = slope*x1 + intercept
    svg.append(f'<line x1="{X(x0)}" y1="{Y(y0)}" x2="{X(x1)}" y2="{Y(y1)}" stroke="{p["color"]}" stroke-width="2.5"/>')

    # Big r label
    svg.append(f'<text x="{ML+plot_w-8}" y="{MT+16}" text-anchor="end" font-family="Playfair Display" font-size="22" font-weight="700" fill="{p["color"]}">r = {(r_snow if i==0 else r_mlb):.3f}</text>')

svg.append('</svg>')

with open(Path(__file__).parent / "predictability_chart.svg", "w") as f: f.write("\n".join(svg))
print("Wrote predictability_chart.svg")
print(f"  r_snow = {r_snow:.3f}, r_mlb_pooled = {r_mlb:.3f}, r_mets = {r_mets:.3f}")
print(f"  Ratio: MLB persistence is {r_mlb/r_snow:.1f}× the Steamboat number")
