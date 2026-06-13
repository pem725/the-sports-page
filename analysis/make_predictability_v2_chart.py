"""SVG: two-panel chart for predictability v2:
   Left: snowfall by ENSO state (boxplot-like) — shows ENSO can't distinguish years
   Right: % RMSE reduction comparison bar chart — the takeaway"""
import json
from pathlib import Path
import statistics
from collections import defaultdict

ANALYSIS = Path(__file__).parent

# Load raw snow + ENSO assignments
predict = json.load(open(ANALYSIS / "predictability_v2.json"))
snow_data = json.load(open(ANALYSIS / "predictability_data.json"))["snow"]["series"]

# Re-parse ENSO state per year
oni_djf = {}
with open("/tmp/oni.ascii.txt") as f:
    for line in f.readlines()[1:]:
        parts = line.split()
        if len(parts) < 4: continue
        if parts[0] != "DJF": continue
        try:
            yr = int(parts[1]); anom = float(parts[3])
            oni_djf[yr] = anom
        except ValueError: continue

def state(season_start):
    anom = oni_djf.get(season_start + 1)
    if anom is None: return None
    if anom >= 0.5: return "El Niño"
    if anom <= -0.5: return "La Niña"
    return "Neutral"

by_state = defaultdict(list)
for s in snow_data:
    st = state(s["season_start"])
    if st: by_state[st].append(s["snow_mm"])

# Layout
W, H = 760, 460
PANEL_W = (W - 80) / 2
MT, MB = 50, 70
plot_h = H - MT - MB

# ============ Panel 1: Snowfall by ENSO state (strip plot) ============
P1_ML = 60
plot_w = PANEL_W - 80
states = ["La Niña", "Neutral", "El Niño"]
COLORS = {"La Niña": "#2c4a6e", "Neutral": "#6b5e4a", "El Niño": "#b83a1e"}

y_lo = 1500; y_hi = 7500
def Y(v): return MT + plot_h * (1 - (v - y_lo) / (y_hi - y_lo))
def X1(i, jitter=0): return P1_ML + (i + 0.5 + jitter) * plot_w / 3

svg = [f'<svg class="chart" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Roboto Mono\',monospace">']
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ede5d2"/>')

# Title
svg.append(f'<text x="{P1_ML+plot_w/2}" y="{MT-26}" text-anchor="middle" font-family="Playfair Display" font-size="13" font-weight="700" fill="#1a1208">Steamboat snowfall by ENSO state</text>')
svg.append(f'<text x="{P1_ML+plot_w/2}" y="{MT-10}" text-anchor="middle" font-size="10" fill="#6b5e4a">The most obvious covariate doesn\'t help. The three groups look the same.</text>')

# Y gridlines
for v in [2000, 3000, 4000, 5000, 6000, 7000]:
    y = Y(v)
    svg.append(f'<line x1="{P1_ML}" y1="{y}" x2="{P1_ML+plot_w}" y2="{y}" stroke="#c8b99a" stroke-width="1" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{P1_ML-6}" y="{y+3}" text-anchor="end" font-size="10" fill="#6b5e4a">{v}</text>')

# Axis box
svg.append(f'<line x1="{P1_ML}" y1="{MT}" x2="{P1_ML}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<line x1="{P1_ML}" y1="{MT+plot_h}" x2="{P1_ML+plot_w}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<text transform="rotate(-90,20,{MT+plot_h/2})" x="20" y="{MT+plot_h/2}" text-anchor="middle" font-size="11" fill="#1a1208" font-weight="600">snowfall, Nov–Apr (mm)</text>')

# X labels + group means
import random
random.seed(11)
for i, s in enumerate(states):
    arr = by_state[s]
    if not arr: continue
    cx = X1(i)
    color = COLORS[s]
    # dots
    for v in arr:
        jx = random.uniform(-0.13, 0.13)
        svg.append(f'<circle cx="{X1(i, jx):.1f}" cy="{Y(v):.1f}" r="4" fill="{color}" fill-opacity="0.7" stroke="#1a1208" stroke-width="0.6"/>')
    # mean bar
    mean_v = statistics.mean(arr)
    median_v = statistics.median(arr)
    svg.append(f'<line x1="{cx-30}" y1="{Y(mean_v):.1f}" x2="{cx+30}" y2="{Y(mean_v):.1f}" stroke="#1a1208" stroke-width="3"/>')
    # label below
    svg.append(f'<text x="{cx}" y="{MT+plot_h+16}" text-anchor="middle" font-family="Playfair Display" font-size="13" font-weight="700" fill="{color}">{s}</text>')
    svg.append(f'<text x="{cx}" y="{MT+plot_h+32}" text-anchor="middle" font-size="10" fill="#6b5e4a">n={len(arr)} · mean {int(mean_v)} mm</text>')

# ============ Panel 2: % RMSE reduction bar chart ============
P2_ML = 60 + PANEL_W + 20
plot_w2 = PANEL_W - 80

# Two bars: snow ENSO vs baseball profile match
bars = [
    ("Steamboat snow\n+ ENSO state",     predict["snow"]["rmse_reduction_pct"], "#2c4a6e"),
    ("MLB league OPS\n+ profile match",  predict["mlb"]["rmse_reduction_pct"],  "#2a6e3f"),
]

# Title
svg.append(f'<text x="{P2_ML+plot_w2/2}" y="{MT-26}" text-anchor="middle" font-family="Playfair Display" font-size="13" font-weight="700" fill="#1a1208">% RMSE reduction by profile conditioning</text>')
svg.append(f'<text x="{P2_ML+plot_w2/2}" y="{MT-10}" text-anchor="middle" font-size="10" fill="#6b5e4a">Leave-one-out cross-validation, conditioned-model vs climatology baseline</text>')

# X axis range -10 to 60
xv_lo, xv_hi = -10, 60
def X2(v): return P2_ML + (v - xv_lo) / (xv_hi - xv_lo) * plot_w2

# Zero line + ticks
for v in [-10, 0, 10, 20, 30, 40, 50, 60]:
    x = X2(v)
    color = "#1a1208" if v == 0 else "#c8b99a"
    weight = 2 if v == 0 else 1
    svg.append(f'<line x1="{x}" y1="{MT}" x2="{x}" y2="{MT+plot_h}" stroke="{color}" stroke-width="{weight}" stroke-dasharray="{("none" if v==0 else "3,3")}"/>')
    svg.append(f'<text x="{x}" y="{MT+plot_h+18}" text-anchor="middle" font-size="10" fill="#1a1208">{v:+d}%</text>')

svg.append(f'<text x="{P2_ML+plot_w2/2}" y="{H-15}" text-anchor="middle" font-size="11" fill="#1a1208" font-weight="600">% RMSE reduction (positive = better than climatology)</text>')

# Bars
bar_h = 60
bar_gap = 30
y0 = MT + 50
for i, (label, val, color) in enumerate(bars):
    by = y0 + i * (bar_h + bar_gap)
    bar_start = X2(0)
    bar_end   = X2(val)
    if val >= 0:
        svg.append(f'<rect x="{bar_start}" y="{by}" width="{bar_end-bar_start}" height="{bar_h}" fill="{color}" fill-opacity="0.85" stroke="#1a1208" stroke-width="1.5"/>')
        svg.append(f'<text x="{bar_end-8}" y="{by+bar_h/2+5}" text-anchor="end" font-family="Playfair Display" font-size="22" font-weight="900" fill="#fff">{val:+.1f}%</text>')
    else:
        svg.append(f'<rect x="{bar_end}" y="{by}" width="{bar_start-bar_end}" height="{bar_h}" fill="#b83a1e" fill-opacity="0.85" stroke="#1a1208" stroke-width="1.5"/>')
        svg.append(f'<text x="{bar_end+8}" y="{by+bar_h/2+5}" text-anchor="start" font-family="Playfair Display" font-size="22" font-weight="900" fill="#fff">{val:+.1f}%</text>')

    # Label to left of zero line
    lines = label.split("\n")
    for j, line in enumerate(lines):
        svg.append(f'<text x="{P2_ML-6}" y="{by + bar_h/2 - 3 + j*14}" text-anchor="end" font-family="Roboto Mono" font-size="11" font-weight="600" fill="#1a1208">{line}</text>')

svg.append('</svg>')

(ANALYSIS / "predictability_v2_chart.svg").write_text("\n".join(svg))
print("Wrote predictability_v2_chart.svg")
