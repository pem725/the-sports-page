"""Generate inline SVG: 30-team scatter of mean OPS vs within-team OPS std dev."""
import csv
from pathlib import Path

ANALYSIS = Path(__file__).parent
rows = list(csv.DictReader(open(ANALYSIS / "team_clustering_2026.csv")))
for r in rows:
    r["mean_ops_paw"] = float(r["mean_ops_paw"])
    r["std_ops_paw"] = float(r["std_ops_paw"])

# Layout
W, H = 760, 520
ML, MR, MT, MB = 80, 50, 50, 60
plot_w = W - ML - MR
plot_h = H - MT - MB

# Axis ranges
xs = [r["mean_ops_paw"] for r in rows]
ys = [r["std_ops_paw"] for r in rows]
x_lo, x_hi = 0.62, 0.81
y_lo, y_hi = 0.05, 0.16

def X(v): return ML + (v - x_lo) / (x_hi - x_lo) * plot_w
def Y(v): return MT + plot_h * (1 - (v - y_lo) / (y_hi - y_lo))

# Quadrant boundaries (MLB medians)
mean_med = sorted(xs)[len(xs)//2]
std_med  = sorted(ys)[len(ys)//2]

svg = [f'<svg class="chart" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Roboto Mono\',monospace">']
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ede5d2"/>')

# Quadrant background shading
xmid = X(mean_med); ymid = Y(std_med)
# Top-right (good mean, high spread) — top-heavy excellence
svg.append(f'<rect x="{xmid}" y="{MT}" width="{ML+plot_w-xmid}" height="{ymid-MT}" fill="#2a6e3f" opacity="0.08"/>')
# Top-left (low mean, high spread) — top-heavy mediocrity
svg.append(f'<rect x="{ML}" y="{MT}" width="{xmid-ML}" height="{ymid-MT}" fill="#b83a1e" opacity="0.08"/>')
# Bottom-right (good mean, low spread) — clustered excellence
svg.append(f'<rect x="{xmid}" y="{ymid}" width="{ML+plot_w-xmid}" height="{MT+plot_h-ymid}" fill="#c9962a" opacity="0.08"/>')
# Bottom-left (low mean, low spread) — clustered mediocrity
svg.append(f'<rect x="{ML}" y="{ymid}" width="{xmid-ML}" height="{MT+plot_h-ymid}" fill="#6b5e4a" opacity="0.10"/>')

# X gridlines
for v in [0.65, 0.70, 0.75, 0.80]:
    x = X(v)
    svg.append(f'<line x1="{x}" y1="{MT}" x2="{x}" y2="{MT+plot_h}" stroke="#c8b99a" stroke-width="1" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{x}" y="{MT+plot_h+18}" text-anchor="middle" font-size="11" fill="#1a1208">{v:.2f}</text>')

# Y gridlines
for v in [0.06, 0.08, 0.10, 0.12, 0.14]:
    y = Y(v)
    svg.append(f'<line x1="{ML}" y1="{y}" x2="{ML+plot_w}" y2="{y}" stroke="#c8b99a" stroke-width="1" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{ML-8}" y="{y+4}" text-anchor="end" font-size="11" fill="#6b5e4a">{v:.2f}</text>')

# Median lines
svg.append(f'<line x1="{xmid}" y1="{MT}" x2="{xmid}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="1" stroke-dasharray="2,4" opacity="0.4"/>')
svg.append(f'<line x1="{ML}" y1="{ymid}" x2="{ML+plot_w}" y2="{ymid}" stroke="#1a1208" stroke-width="1" stroke-dasharray="2,4" opacity="0.4"/>')

# Axis lines
svg.append(f'<line x1="{ML}" y1="{MT}" x2="{ML}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<line x1="{ML}" y1="{MT+plot_h}" x2="{ML+plot_w}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<text x="{ML+plot_w/2}" y="{H-15}" text-anchor="middle" font-size="13" fill="#1a1208" font-weight="600">Team mean OPS (PA-weighted)</text>')
svg.append(f'<text transform="rotate(-90,22,{MT+plot_h/2})" x="22" y="{MT+plot_h/2}" text-anchor="middle" font-size="13" fill="#1a1208" font-weight="600">Within-team OPS standard deviation</text>')

# Quadrant labels (corners)
svg.append(f'<text x="{X(0.795)}" y="{Y(0.155)}" text-anchor="end" font-size="11" font-style="italic" fill="#2a6e3f" font-weight="600">Top-heavy excellence</text>')
svg.append(f'<text x="{X(0.795)}" y="{Y(0.060)}" text-anchor="end" font-size="11" font-style="italic" fill="#c9962a" font-weight="600">Clustered excellence</text>')
svg.append(f'<text x="{X(0.625)}" y="{Y(0.155)}" font-size="11" font-style="italic" fill="#b83a1e" font-weight="600">Top-heavy mediocrity</text>')
svg.append(f'<text x="{X(0.625)}" y="{Y(0.060)}" font-size="11" font-style="italic" fill="#6b5e4a" font-weight="600">Clustered mediocrity</text>')

# Highlighted teams
HIGHLIGHT = {"NYM": "#b83a1e", "HOU": "#c9962a", "LAD": "#2c4a6e", "KCR": "#6b5e4a", "PHI": "#8b1e3f"}

# Plot all team dots
for r in rows:
    x = X(r["mean_ops_paw"]); y = Y(r["std_ops_paw"])
    is_hl = r["abbr"] in HIGHLIGHT
    color = HIGHLIGHT.get(r["abbr"], "#6b5e4a")
    radius = 6 if is_hl else 4
    fill_opacity = 1.0 if is_hl else 0.6
    svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{color}" fill-opacity="{fill_opacity}" stroke="#1a1208" stroke-width="{1.2 if is_hl else 0.6}"/>')

# Highlighted labels (avoid collision via per-team offset)
LABEL_OFFSETS = {"NYM": (10, -7), "HOU": (10, 5), "LAD": (10, 5), "KCR": (-10, 5), "PHI": (10, -5),
                 "BAL": (10, 5), "CHC": (10, -7), "NYY": (10, 5), "ATL": (-10, 5), "OAK": (10, 5),
                 "ATH": (10, 5)}
LABEL_ANCHORS = {"KCR": "end", "ATL": "end"}
for r in rows:
    if r["abbr"] not in HIGHLIGHT and r["abbr"] not in {"BAL","CHC","NYY","ATL","SDP"}: continue
    x = X(r["mean_ops_paw"]); y = Y(r["std_ops_paw"])
    dx, dy = LABEL_OFFSETS.get(r["abbr"], (8, 5))
    anchor = LABEL_ANCHORS.get(r["abbr"], "start")
    weight = "700" if r["abbr"] in HIGHLIGHT else "400"
    color = HIGHLIGHT.get(r["abbr"], "#1a1208")
    svg.append(f'<text x="{x+dx:.1f}" y="{y+dy:.1f}" text-anchor="{anchor}" font-family="Playfair Display" font-size="12" font-weight="{weight}" fill="{color}">{r["abbr"]}</text>')

svg.append('</svg>')

with open(ANALYSIS / "clustering_chart.svg", "w") as f: f.write("\n".join(svg))
print(f"Wrote clustering_chart.svg  ({len(rows)} teams)")
print(f"  Mean OPS median: {mean_med:.3f}")
print(f"  Std OPS median: {std_med:.3f}")
