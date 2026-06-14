"""Scoreboard chart v5: Pearson r × 100 on a symmetric -70 to +70 scale.
   Sign = direction; magnitude = how informative the predictor is."""
import json
from pathlib import Path

ANALYSIS = Path(__file__).parent
d = json.load(open(ANALYSIS / "predictability_v5.json"))

sports_order = ["NBA","NHL","MLB","NFL"]
snow_order = ["Utah/Wyoming","New Mexico","Vermont","Pacific Northwest","Colorado"]

items = []
SPORT_COLOR = {"NBA":"#c9962a","NHL":"#2c4a6e","MLB":"#2a6e3f","NFL":"#8b1e3f"}
for s in sports_order:
    r = d["sports"][s]["skill_r"] * 100
    items.append((s, "lag-1: prior year", r, d["sports"][s]["n"], SPORT_COLOR[s]))
for region in snow_order:
    if region not in d["snow"]: continue
    r = d["snow"][region]["skill_r"] * 100
    items.append((region, "ENSO state", r, d["snow"][region]["n"], "#6b5e4a"))

W, H = 820, 600
ML, MR, MT, MB = 260, 60, 80, 60
plot_w = W - ML - MR
plot_h = H - MT - MB

xv_lo, xv_hi = -70, 70
def X(v): return ML + (v - xv_lo) / (xv_hi - xv_lo) * plot_w

svg = [f'<svg class="chart" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Roboto Mono\',monospace">']
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ede5d2"/>')

# Title
svg.append(f'<text x="{W/2}" y="30" text-anchor="middle" font-family="Playfair Display" font-size="15" font-weight="700" fill="#1a1208">How informative is each domain\'s natural predictor?</text>')
svg.append(f'<text x="{W/2}" y="50" text-anchor="middle" font-size="11" fill="#6b5e4a">Pearson correlation between predictor and outcome, scaled to −100 ↔ +100. Sign = direction. Magnitude = informativeness.</text>')

# Vertical gridlines and tick labels
for v in [-70, -50, -25, 0, 25, 50, 70]:
    x = X(v)
    color = "#1a1208" if v == 0 else "#c8b99a"
    sw = 2 if v == 0 else 1
    dash = "none" if v == 0 else "3,3"
    svg.append(f'<line x1="{x}" y1="{MT}" x2="{x}" y2="{MT+plot_h+5}" stroke="{color}" stroke-width="{sw}" stroke-dasharray="{dash}"/>')
    svg.append(f'<text x="{x}" y="{MT+plot_h+22}" text-anchor="middle" font-size="11" fill="#1a1208">{v:+d}</text>')

svg.append(f'<text x="{ML+plot_w/2}" y="{MT+plot_h+44}" text-anchor="middle" font-size="12" fill="#1a1208" font-weight="600">Predictor–outcome correlation × 100  (perfect = +100; useless = 0)</text>')

# Reference labels above plot
for v, label, color in [(50, "strong", "#2a6e3f"), (-50, "strong reversed", "#b83a1e"), (25, "modest", "#c9962a"), (-25, "modest reversed", "#b83a1e")]:
    x = X(v)
    svg.append(f'<text x="{x}" y="{MT-8}" text-anchor="middle" font-family="Playfair Display" font-style="italic" font-size="10" fill="{color}">{label}</text>')

# Section divider
divider_y = MT + 4 * 38 + 8
svg.append(f'<line x1="0" y1="{divider_y}" x2="{W}" y2="{divider_y}" stroke="#1a1208" stroke-width="1" stroke-dasharray="6,4" opacity="0.4"/>')
svg.append(f'<text x="22" y="{MT + 2*38 + 14}" font-family="Playfair Display" font-style="italic" font-size="11" fill="#6b5e4a" font-weight="700">SPORTS</text>')
svg.append(f'<text x="22" y="{divider_y + 2*38 + 14}" font-family="Playfair Display" font-style="italic" font-size="11" fill="#6b5e4a" font-weight="700">SNOW</text>')

# Bars
bar_h = 28
bar_gap = 10
y_start = MT + 6
INSIDE_BAR_MIN_WIDTH = 70

for i, (name, predictor, val, n, color) in enumerate(items):
    y = y_start + i * (bar_h + bar_gap)
    if i >= 4: y += 16
    x0 = X(0); xv = X(val)
    label_pct = f"{val:+.0f}"
    if val >= 0:
        bar_w = xv - x0
        svg.append(f'<rect x="{x0}" y="{y}" width="{bar_w}" height="{bar_h}" fill="{color}" fill-opacity="0.88" stroke="#1a1208" stroke-width="1"/>')
        if bar_w >= INSIDE_BAR_MIN_WIDTH:
            svg.append(f'<text x="{xv-8}" y="{y+bar_h/2+5}" text-anchor="end" font-family="Playfair Display" font-size="17" font-weight="700" fill="#fff">{label_pct}</text>')
        else:
            svg.append(f'<text x="{xv+6}" y="{y+bar_h/2+5}" font-family="Playfair Display" font-size="17" font-weight="700" fill="{color}">{label_pct}</text>')
    else:
        bar_w = x0 - xv
        svg.append(f'<rect x="{xv}" y="{y}" width="{bar_w}" height="{bar_h}" fill="#b83a1e" fill-opacity="0.85" stroke="#1a1208" stroke-width="1"/>')
        if bar_w >= INSIDE_BAR_MIN_WIDTH:
            svg.append(f'<text x="{xv+8}" y="{y+bar_h/2+5}" text-anchor="start" font-family="Playfair Display" font-size="17" font-weight="700" fill="#fff">{label_pct}</text>')
        else:
            svg.append(f'<text x="{xv-6}" y="{y+bar_h/2+5}" text-anchor="end" font-family="Playfair Display" font-size="17" font-weight="700" fill="#b83a1e">{label_pct}</text>')
    # Left column: domain (bold) + predictor type (small)
    svg.append(f'<text x="{ML-12}" y="{y+bar_h/2-2}" text-anchor="end" font-family="Playfair Display" font-size="14" font-weight="700" fill="#1a1208">{name}</text>')
    svg.append(f'<text x="{ML-12}" y="{y+bar_h/2+12}" text-anchor="end" font-family="Roboto Mono" font-size="9" fill="#6b5e4a">predictor: {predictor} &middot; n={n}</text>')

svg.append('</svg>')
(ANALYSIS / "cross_sport_chart.svg").write_text("\n".join(svg))
print("Wrote cross_sport_chart.svg")
