"""Generate inline SVG: K_PA vs BB_PA scatter over 1985-2026, showing 2026 next to 2021."""
import json
from pathlib import Path

d = json.load(open(Path(__file__).parent / "analog_year_results.json"))
features = d["features"]
years = sorted(int(y) for y in features.keys() if int(y) >= 1985)

# Map year -> (K_PA, BB_PA)
pts = {y: (features[str(y)]["K_PA"], features[str(y)]["BB_PA"]) for y in years}

# Layout
W, H = 760, 460
ML, MR, MT, MB = 70, 50, 40, 60
plot_w = W - ML - MR
plot_h = H - MT - MB

x_lo, x_hi = 0.13, 0.245
y_lo, y_hi = 0.075, 0.098

def X(v): return ML + (v - x_lo) / (x_hi - x_lo) * plot_w
def Y(v): return MT + plot_h * (1 - (v - y_lo) / (y_hi - y_lo))

svg = [f'<svg class="chart" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Roboto Mono\',monospace">']
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ede5d2"/>')

# X gridlines + labels
for v in [0.14, 0.16, 0.18, 0.20, 0.22, 0.24]:
    x = X(v)
    svg.append(f'<line x1="{x}" y1="{MT}" x2="{x}" y2="{MT+plot_h}" stroke="#c8b99a" stroke-width="1" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{x}" y="{MT+plot_h+18}" text-anchor="middle" font-size="11" fill="#1a1208">{int(v*100)}%</text>')

# Y gridlines + labels
for v in [0.080, 0.085, 0.090, 0.095]:
    y = Y(v)
    svg.append(f'<line x1="{ML}" y1="{y}" x2="{ML+plot_w}" y2="{y}" stroke="#c8b99a" stroke-width="1" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{ML-8}" y="{y+4}" text-anchor="end" font-size="11" fill="#6b5e4a">{v*100:.1f}%</text>')

# Axis lines
svg.append(f'<line x1="{ML}" y1="{MT}" x2="{ML}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<line x1="{ML}" y1="{MT+plot_h}" x2="{ML+plot_w}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<text x="{ML+plot_w/2}" y="{H-15}" text-anchor="middle" font-size="13" fill="#1a1208" font-weight="600">Strikeouts per plate appearance</text>')
svg.append(f'<text transform="rotate(-90,22,{MT+plot_h/2})" x="22" y="{MT+plot_h/2}" text-anchor="middle" font-size="13" fill="#1a1208" font-weight="600">Walks per plate appearance</text>')

# Connect years with light line in time order
path_pts = [f"{X(pts[y][0]):.1f},{Y(pts[y][1]):.1f}" for y in years]
svg.append(f'<polyline points="{" ".join(path_pts)}" fill="none" stroke="#6b5e4a" stroke-width="1.2" opacity="0.35"/>')

# Highlighted years
HL = {2026: "#b83a1e", 2021: "#c9962a", 2020: "#c9962a", 2018: "#2c4a6e", 2023: "#2c4a6e", 2025: "#2c4a6e",
      2014: "#6b5e4a", 1985: "#6b5e4a", 1994: "#8b1e3f", 2000: "#6b5e4a"}

# Plot all years
for y in years:
    kx, bb = pts[y]
    x = X(kx); yy = Y(bb)
    is_hl = y in HL
    color = HL.get(y, "#6b5e4a")
    radius = 6 if is_hl else 3
    opacity = 1.0 if is_hl else 0.5
    svg.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="{radius}" fill="{color}" fill-opacity="{opacity}" stroke="#1a1208" stroke-width="{1.2 if is_hl else 0.4}"/>')

# Labels
LABEL_OFFSETS = {
    2026: (10, -4, "start", "700"),
    2021: (-9, -8, "end", "700"),
    2020: (10, 4, "start", "400"),
    2018: (-9, 4, "end", "400"),
    2023: (-9, -8, "end", "400"),
    2025: (10, 4, "start", "400"),
    2014: (10, 4, "start", "400"),
    1985: (10, 4, "start", "400"),
    1994: (10, -4, "start", "400"),
    2000: (-9, 4, "end", "400"),
}
for y in years:
    if y not in LABEL_OFFSETS: continue
    kx, bb = pts[y]
    x = X(kx); yy = Y(bb)
    dx, dy, anchor, weight = LABEL_OFFSETS[y]
    color = HL.get(y, "#1a1208")
    svg.append(f'<text x="{x+dx:.1f}" y="{yy+dy:.1f}" text-anchor="{anchor}" font-family="Playfair Display" font-size="13" font-weight="{weight}" fill="{color}">{y}</text>')

# Era arrows / annotations
svg.append(f'<text x="{X(0.14)+5}" y="{Y(0.084)}" font-family="Playfair Display" font-style="italic" font-size="11" fill="#6b5e4a">contact era</text>')
svg.append(f'<text x="{X(0.22)-5}" y="{Y(0.077)}" text-anchor="end" font-family="Playfair Display" font-style="italic" font-size="11" fill="#6b5e4a">strikeout era</text>')

# Bracket showing 2026's analog cluster
xc = X(0.219); yc = Y(0.0905)
svg.append(f'<circle cx="{xc:.1f}" cy="{yc:.1f}" r="40" fill="none" stroke="#b83a1e" stroke-width="1.4" stroke-dasharray="4,3" opacity="0.6"/>')
svg.append(f'<text x="{xc+45}" y="{yc-30}" font-family="Playfair Display" font-style="italic" font-size="12" font-weight="700" fill="#b83a1e">2026\'s neighborhood</text>')

svg.append('</svg>')
with open(Path(__file__).parent / "analog_chart.svg", "w") as f: f.write("\n".join(svg))
print("Wrote analog_chart.svg")
