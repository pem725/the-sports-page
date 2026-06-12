"""Generate full-cohort survival chart SVG for Part I (revised)."""
import json
from collections import defaultdict

d = json.load(open("full_cohort_data.json"))
POSITIONS = ["C","1B","2B","3B","SS","LF","CF","RF","DH"]
COLORS = {
    "C":  "#b83a1e", "1B": "#2c4a6e", "2B": "#c9962a", "3B": "#2a6e3f",
    "SS": "#8b1e3f", "LF": "#5e4b8b", "CF": "#1f6b78", "RF": "#a85a1c",
    "DH": "#6b5e4a",
}

# Survival per position, all debutants
debut_count = defaultdict(int)
active = defaultdict(lambda: defaultdict(int))
for p in d["players_hit"]:
    pos = p["pos"]
    if pos not in POSITIONS: continue
    debut_count[pos] += 1
    for s in p["seasons"]:
        if s["PA"] >= 1 and s["svc"] <= 18:
            active[pos][s["svc"]] += 1

W, H = 740, 420
ML, MR, MT, MB = 60, 130, 40, 60
plot_w = W - ML - MR
plot_h = H - MT - MB

MAX_SVC = 18
def X(svc): return ML + (svc - 1) / (MAX_SVC - 1) * plot_w
def Y(p):   return MT + plot_h * (1 - p)

svg = [f'<svg class="chart" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Roboto Mono\',monospace">']
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ede5d2"/>')

# Y gridlines + labels
for p in [0, 0.25, 0.5, 0.75, 1.0]:
    y = Y(p)
    svg.append(f'<line x1="{ML}" y1="{y}" x2="{ML+plot_w}" y2="{y}" stroke="#c8b99a" stroke-width="1" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{ML-8}" y="{y+4}" text-anchor="end" font-size="11" fill="#6b5e4a">{int(p*100)}%</text>')

# 50% line emphasized
y50 = Y(0.5)
svg.append(f'<line x1="{ML}" y1="{y50}" x2="{ML+plot_w}" y2="{y50}" stroke="#b83a1e" stroke-width="1.5" stroke-dasharray="6,4" opacity="0.6"/>')
svg.append(f'<text x="{ML+plot_w+6}" y="{y50+4}" font-size="10" fill="#b83a1e" font-weight="600">half-life</text>')

# X labels (every 2 years)
for svc in range(1, MAX_SVC+1):
    if svc % 2 != 1 and svc != MAX_SVC: continue
    x = X(svc)
    svg.append(f'<line x1="{x}" y1="{MT+plot_h-4}" x2="{x}" y2="{MT+plot_h+4}" stroke="#1a1208"/>')
    svg.append(f'<text x="{x}" y="{MT+plot_h+18}" text-anchor="middle" font-size="11" fill="#1a1208">{svc}</text>')

# Axis lines
svg.append(f'<line x1="{ML}" y1="{MT}" x2="{ML}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<line x1="{ML}" y1="{MT+plot_h}" x2="{ML+plot_w}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<text x="{ML+plot_w/2}" y="{H-12}" text-anchor="middle" font-size="12" fill="#1a1208" font-weight="600">MLB year of service</text>')
svg.append(f'<text transform="rotate(-90,18,{MT+plot_h/2})" x="18" y="{MT+plot_h/2}" text-anchor="middle" font-size="12" fill="#1a1208" font-weight="600">% of every debutant still in MLB (≥1 PA)</text>')

# Lines
legend_y = MT + 10
for pos in POSITIONS:
    n = debut_count[pos]
    if n < 5: continue
    pts = []
    for svc in range(1, MAX_SVC+1):
        rate = active[pos][svc] / n
        pts.append(f"{X(svc):.1f},{Y(rate):.1f}")
    color = COLORS[pos]
    svg.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2.2"/>')
    last_pt = pts[-1].split(",")
    svg.append(f'<circle cx="{last_pt[0]}" cy="{last_pt[1]}" r="3.5" fill="{color}"/>')
    svg.append(f'<line x1="{W-MR+10}" y1="{legend_y}" x2="{W-MR+28}" y2="{legend_y}" stroke="{color}" stroke-width="2.2"/>')
    svg.append(f'<text x="{W-MR+34}" y="{legend_y+4}" font-size="11" fill="#1a1208">{pos} (n={n})</text>')
    legend_y += 17

svg.append('</svg>')
with open("survival_chart_v2.svg", "w") as f: f.write("\n".join(svg))
print("Wrote survival_chart_v2.svg")
print(f"\nDebut cohort sizes (debut year >= 1985):")
for pos in POSITIONS:
    print(f"  {pos}: {debut_count[pos]}")
