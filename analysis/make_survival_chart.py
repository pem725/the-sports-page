"""Generate inline SVG: survival curves by position."""
import json

d = json.load(open("half_life_by_position.json"))
BUCKETS = d["buckets"]
POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]

# Layout
W, H = 720, 400
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 60, 130, 40, 60
plot_w = W - MARGIN_L - MARGIN_R
plot_h = H - MARGIN_T - MARGIN_B

# Colors per position (visually distinguishable; matches site palette where possible)
COLORS = {
    "C":  "#b83a1e",  # rust
    "1B": "#2c4a6e",  # steel
    "2B": "#c9962a",  # gold
    "3B": "#2a6e3f",  # green
    "SS": "#8b1e3f",  # claret
    "LF": "#5e4b8b",  # plum
    "CF": "#1f6b78",  # teal
    "RF": "#a85a1c",  # sienna
    "DH": "#6b5e4a",  # muted
}

def x_of(i): return MARGIN_L + i * (plot_w / (len(BUCKETS) - 1))
def y_of(pct): return MARGIN_T + plot_h * (1 - pct)

svg = [f'<svg class="chart" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Roboto Mono\',monospace">']

# Background
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ede5d2"/>')

# Y gridlines + labels (0, 25, 50, 75, 100%)
for p in [0, 0.25, 0.5, 0.75, 1.0]:
    y = y_of(p)
    svg.append(f'<line x1="{MARGIN_L}" y1="{y}" x2="{MARGIN_L+plot_w}" y2="{y}" stroke="#c8b99a" stroke-width="1" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{MARGIN_L-8}" y="{y+4}" text-anchor="end" font-size="11" fill="#6b5e4a">{int(p*100)}%</text>')

# Highlight the 50% line (half-life threshold)
y50 = y_of(0.5)
svg.append(f'<line x1="{MARGIN_L}" y1="{y50}" x2="{MARGIN_L+plot_w}" y2="{y50}" stroke="#b83a1e" stroke-width="1.5" stroke-dasharray="6,4" opacity="0.6"/>')
svg.append(f'<text x="{MARGIN_L+plot_w+6}" y="{y50+4}" font-size="10" fill="#b83a1e" font-weight="600">half-life</text>')

# X axis labels
for i, b in enumerate(BUCKETS):
    x = x_of(i)
    svg.append(f'<text x="{x}" y="{H-MARGIN_B+18}" text-anchor="middle" font-size="11" fill="#1a1208">yrs {b}</text>')

# Axis lines
svg.append(f'<line x1="{MARGIN_L}" y1="{MARGIN_T}" x2="{MARGIN_L}" y2="{MARGIN_T+plot_h}" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<line x1="{MARGIN_L}" y1="{MARGIN_T+plot_h}" x2="{MARGIN_L+plot_w}" y2="{MARGIN_T+plot_h}" stroke="#1a1208" stroke-width="2"/>')

# Axis titles
svg.append(f'<text x="{MARGIN_L+plot_w/2}" y="{H-12}" text-anchor="middle" font-size="12" fill="#1a1208" font-weight="600">MLB years of service</text>')
svg.append(f'<text transform="rotate(-90,18,{MARGIN_T+plot_h/2})" x="18" y="{MARGIN_T+plot_h/2}" text-anchor="middle" font-size="12" fill="#1a1208" font-weight="600">% of debut cohort still a regular (300+ PA season)</text>')

# Lines per position
legend_y = MARGIN_T + 10
for pos in POSITIONS:
    sc = d["survival_curve"].get(pos)
    if not sc: continue
    pts = []
    for i, b in enumerate(BUCKETS):
        rate = sc["survival_rate"].get(b, 0)
        pts.append(f"{x_of(i):.1f},{y_of(rate):.1f}")
    color = COLORS[pos]
    svg.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2.2"/>')
    # endpoint marker
    last_pt = pts[-1].split(",")
    svg.append(f'<circle cx="{last_pt[0]}" cy="{last_pt[1]}" r="3.5" fill="{color}"/>')
    # Legend entry
    svg.append(f'<line x1="{W-MARGIN_R+10}" y1="{legend_y}" x2="{W-MARGIN_R+28}" y2="{legend_y}" stroke="{color}" stroke-width="2.2"/>')
    svg.append(f'<text x="{W-MARGIN_R+34}" y="{legend_y+4}" font-size="11" fill="#1a1208">{pos} (n={sc["cohort_size"]})</text>')
    legend_y += 18

svg.append('</svg>')

with open("survival_chart.svg", "w") as f: f.write("\n".join(svg))
print("Wrote survival_chart.svg")
