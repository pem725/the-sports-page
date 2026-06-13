"""Trajectory chart: 5 Astros analog teams' win pct trajectories post-analog."""
from pathlib import Path

ANALYSIS = Path(__file__).parent

# Post-analog win pcts for each analog team (year 0 = analog year)
analogs = {
    "2018 Blue Jays":   {"color": "#2a6e3f", "wps": [0.451, 0.414, 0.533, 0.562, 0.568, 0.549, 0.457, 0.580]},
    "2017 Mets":        {"color": "#8b1e3f", "wps": [0.432, 0.475, 0.531, 0.433, 0.475, 0.624, 0.463, 0.549]},
    "2021 Twins":       {"color": "#c9962a", "wps": [0.451, 0.481, 0.537, 0.506, 0.432]},
    "2023 Cardinals":   {"color": "#2c4a6e", "wps": [0.438, 0.512, 0.481]},
    "2019 Angels":      {"color": "#6b5e4a", "wps": [0.444, 0.433, 0.475, 0.451, 0.451, 0.389, 0.444]},
}
# Astros prior decade for context
astros_recent = [0.531, 0.518, 0.624, 0.636, 0.660, 0.483, 0.586, 0.654, 0.556, 0.547, 0.537, 0.451]
astros_now = 0.451

W, H = 760, 480
ML, MR, MT, MB = 70, 145, 50, 60
plot_w = W - ML - MR
plot_h = H - MT - MB

x_lo, x_hi = 0, 7
y_lo, y_hi = 0.38, 0.66

def X(yr): return ML + (yr - x_lo) / (x_hi - x_lo) * plot_w
def Y(p):  return MT + plot_h * (1 - (p - y_lo) / (y_hi - y_lo))

svg = [f'<svg class="chart" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Roboto Mono\',monospace">']
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ede5d2"/>')

# Title
svg.append(f'<text x="{ML+plot_w/2}" y="30" text-anchor="middle" font-family="Playfair Display" font-size="14" font-weight="700" fill="#1a1208">Five teams have looked like the 2026 Astros. None won a title afterward.</text>')

# Y gridlines + key reference lines
for v in [0.40, 0.45, 0.50, 0.55, 0.60, 0.65]:
    y = Y(v)
    if v == 0.50:
        svg.append(f'<line x1="{ML}" y1="{y}" x2="{ML+plot_w}" y2="{y}" stroke="#1a1208" stroke-width="1.5" stroke-dasharray="5,4" opacity="0.5"/>')
    elif v == 0.55:
        svg.append(f'<line x1="{ML}" y1="{y}" x2="{ML+plot_w}" y2="{y}" stroke="#2a6e3f" stroke-width="1" stroke-dasharray="4,4" opacity="0.4"/>')
    else:
        svg.append(f'<line x1="{ML}" y1="{y}" x2="{ML+plot_w}" y2="{y}" stroke="#c8b99a" stroke-width="1" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{ML-8}" y="{y+3}" text-anchor="end" font-size="11" fill="#6b5e4a">{v:.2f}</text>')
svg.append(f'<text x="{ML+plot_w-5}" y="{Y(0.50)-5}" text-anchor="end" font-size="10" fill="#6b5e4a" font-style="italic">.500</text>')
svg.append(f'<text x="{ML+plot_w-5}" y="{Y(0.55)-5}" text-anchor="end" font-size="10" fill="#2a6e3f" font-style="italic">playoff bubble (~.550)</text>')

# X gridlines
for yr in range(0, 8):
    x = X(yr)
    if yr > 0:
        svg.append(f'<line x1="{x}" y1="{MT}" x2="{x}" y2="{MT+plot_h}" stroke="#c8b99a" stroke-width="1" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{x}" y="{MT+plot_h+18}" text-anchor="middle" font-size="11" fill="#1a1208">{yr}</text>')

svg.append(f'<text x="{ML+plot_w/2}" y="{H-15}" text-anchor="middle" font-size="12" fill="#1a1208" font-weight="600">years after the analog season (year 0 = analog itself)</text>')
svg.append(f'<text transform="rotate(-90,20,{MT+plot_h/2})" x="20" y="{MT+plot_h/2}" text-anchor="middle" font-size="12" fill="#1a1208" font-weight="600">winning percentage</text>')

# Axis lines
svg.append(f'<line x1="{ML}" y1="{MT}" x2="{ML}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<line x1="{ML}" y1="{MT+plot_h}" x2="{ML+plot_w}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')

# 5 trajectory lines
for label, info in analogs.items():
    wps = info["wps"]; color = info["color"]
    pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(wps))
    svg.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>')
    for i, v in enumerate(wps):
        svg.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3" fill="{color}" stroke="#fff" stroke-width="0.8"/>')

# 2026 Astros marker at year 0
svg.append(f'<circle cx="{X(0):.1f}" cy="{Y(astros_now):.1f}" r="10" fill="#b83a1e" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<circle cx="{X(0):.1f}" cy="{Y(astros_now):.1f}" r="4" fill="#fff"/>')
svg.append(f'<text x="{X(0)+15:.1f}" y="{Y(astros_now)+4:.1f}" font-family="Playfair Display" font-size="13" font-weight="700" fill="#b83a1e">2026 Astros are here</text>')

# Legend on right
lg_x = ML + plot_w + 12; lg_y = MT + 12
svg.append(f'<rect x="{lg_x}" y="{lg_y-8}" width="135" height="160" fill="#fff" stroke="#c8b99a" stroke-width="1"/>')
for i, (label, info) in enumerate(analogs.items()):
    y = lg_y + i * 20 + 8
    svg.append(f'<line x1="{lg_x+8}" y1="{y}" x2="{lg_x+25}" y2="{y}" stroke="{info["color"]}" stroke-width="2.5"/>')
    svg.append(f'<text x="{lg_x+30}" y="{y+4}" font-size="11" fill="#1a1208">{label}</text>')
y = lg_y + 5 * 20 + 18
svg.append(f'<circle cx="{lg_x+17}" cy="{y}" r="6" fill="#b83a1e" stroke="#1a1208" stroke-width="1"/>')
svg.append(f'<text x="{lg_x+30}" y="{y+4}" font-size="11" fill="#1a1208" font-weight="700">2026 Astros</text>')

svg.append('</svg>')
(ANALYSIS / "astros_analog_chart.svg").write_text("\n".join(svg))
print("Wrote astros_analog_chart.svg")
