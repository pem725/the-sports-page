"""Trajectory chart: 2012 Mariners vs 2014 Cubs over 10 years post-analog."""
from pathlib import Path

ANALYSIS = Path(__file__).parent

# Win pcts from year 0 (analog year) through year 10
mariners = [0.463, 0.438, 0.537, 0.469, 0.531, 0.482, 0.549, 0.420, 0.450, 0.556, 0.556]
cubs     = [0.451, 0.599, 0.640, 0.568, 0.583, 0.519, 0.567, 0.438, 0.457, 0.512, 0.512]
mets_now = 0.449  # 2026 Mets as of pull (this is whatever the API gave us)

# Layout
W, H = 760, 460
ML, MR, MT, MB = 70, 130, 50, 60
plot_w = W - ML - MR
plot_h = H - MT - MB

x_lo, x_hi = 0, 10
y_lo, y_hi = 0.38, 0.66

def X(yr): return ML + (yr - x_lo) / (x_hi - x_lo) * plot_w
def Y(p):  return MT + plot_h * (1 - (p - y_lo) / (y_hi - y_lo))

svg = [f'<svg class="chart" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Roboto Mono\',monospace">']
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ede5d2"/>')

# Title
svg.append(f'<text x="{W/2}" y="30" text-anchor="middle" font-family="Playfair Display" font-size="14" font-weight="700" fill="#1a1208">From the same starting point, two different outcomes</text>')

# Y gridlines
for v in [0.40, 0.45, 0.50, 0.55, 0.60, 0.65]:
    y = Y(v)
    color = "#c8b99a" if v != 0.50 else "#1a1208"
    sw = 1 if v != 0.50 else 1.5
    dash = "3,3" if v != 0.50 else "5,4"
    svg.append(f'<line x1="{ML}" y1="{y}" x2="{ML+plot_w}" y2="{y}" stroke="{color}" stroke-width="{sw}" stroke-dasharray="{dash}" opacity="{0.5 if v == 0.50 else 1}"/>')
    svg.append(f'<text x="{ML-8}" y="{y+3}" text-anchor="end" font-size="11" fill="#6b5e4a">{v:.2f}</text>')
svg.append(f'<text x="{ML+plot_w+5}" y="{Y(0.50)+3}" font-size="10" fill="#6b5e4a" font-style="italic">.500</text>')

# X gridlines (every year)
for yr in range(0, 11):
    x = X(yr)
    if yr > 0:
        svg.append(f'<line x1="{x}" y1="{MT}" x2="{x}" y2="{MT+plot_h}" stroke="#c8b99a" stroke-width="1" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{x}" y="{MT+plot_h+18}" text-anchor="middle" font-size="11" fill="#1a1208">{yr}</text>')

svg.append(f'<text x="{ML+plot_w/2}" y="{H-12}" text-anchor="middle" font-size="12" fill="#1a1208" font-weight="600">years after the analog season</text>')
svg.append(f'<text transform="rotate(-90,20,{MT+plot_h/2})" x="20" y="{MT+plot_h/2}" text-anchor="middle" font-size="12" fill="#1a1208" font-weight="600">winning percentage</text>')

# Axis lines
svg.append(f'<line x1="{ML}" y1="{MT}" x2="{ML}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<line x1="{ML}" y1="{MT+plot_h}" x2="{ML+plot_w}" y2="{MT+plot_h}" stroke="#1a1208" stroke-width="2"/>')

# Mariners line
mar_pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(mariners))
svg.append(f'<polyline points="{mar_pts}" fill="none" stroke="#2c4a6e" stroke-width="2.5"/>')
for i, v in enumerate(mariners):
    svg.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.5" fill="#2c4a6e" stroke="#fff" stroke-width="1"/>')

# Cubs line
cubs_pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(cubs))
svg.append(f'<polyline points="{cubs_pts}" fill="none" stroke="#c9962a" stroke-width="2.5"/>')
for i, v in enumerate(cubs):
    svg.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3.5" fill="#c9962a" stroke="#fff" stroke-width="1"/>')

# Mets at year 0
svg.append(f'<circle cx="{X(0):.1f}" cy="{Y(mets_now):.1f}" r="9" fill="#b83a1e" stroke="#1a1208" stroke-width="2"/>')
svg.append(f'<circle cx="{X(0):.1f}" cy="{Y(mets_now):.1f}" r="4" fill="#fff"/>')

# Annotations
# Cubs WS year (year 2)
svg.append(f'<text x="{X(2):.1f}" y="{Y(cubs[2])-12:.1f}" text-anchor="middle" font-family="Playfair Display" font-size="12" font-weight="700" fill="#c9962a">2016 WS champs</text>')
# Mariners playoff drought ends (year 10)
svg.append(f'<text x="{X(10):.1f}" y="{Y(mariners[10])-12:.1f}" text-anchor="end" font-family="Playfair Display" font-size="12" font-weight="700" fill="#2c4a6e">first playoffs in 21 yrs</text>')

# Mets label
svg.append(f'<text x="{X(0)+18:.1f}" y="{Y(mets_now)+4:.1f}" text-anchor="start" font-family="Playfair Display" font-size="13" font-weight="700" fill="#b83a1e">2026 Mets are here</text>')

# Legend
lg_x = ML + plot_w + 10; lg_y = MT + 20
svg.append(f'<rect x="{lg_x}" y="{lg_y-10}" width="115" height="100" fill="#fff" stroke="#c8b99a" stroke-width="1"/>')
svg.append(f'<line x1="{lg_x+8}" y1="{lg_y+6}" x2="{lg_x+28}" y2="{lg_y+6}" stroke="#c9962a" stroke-width="2.5"/>')
svg.append(f'<text x="{lg_x+33}" y="{lg_y+10}" font-size="11" fill="#1a1208">2014 Cubs</text>')
svg.append(f'<text x="{lg_x+8}" y="{lg_y+26}" font-size="9" fill="#6b5e4a" font-style="italic">d=1.02 from Mets</text>')

svg.append(f'<line x1="{lg_x+8}" y1="{lg_y+46}" x2="{lg_x+28}" y2="{lg_y+46}" stroke="#2c4a6e" stroke-width="2.5"/>')
svg.append(f'<text x="{lg_x+33}" y="{lg_y+50}" font-size="11" fill="#1a1208">2012 Mariners</text>')
svg.append(f'<text x="{lg_x+8}" y="{lg_y+64}" font-size="9" fill="#6b5e4a" font-style="italic">d=0.90 from Mets</text>')

svg.append(f'<circle cx="{lg_x+18}" cy="{lg_y+82}" r="6" fill="#b83a1e" stroke="#1a1208" stroke-width="1"/>')
svg.append(f'<text x="{lg_x+33}" y="{lg_y+86}" font-size="11" fill="#1a1208" font-weight="700">2026 Mets</text>')

svg.append('</svg>')
(ANALYSIS / "mets_analog_chart.svg").write_text("\n".join(svg))
print(f"Wrote mets_analog_chart.svg")
