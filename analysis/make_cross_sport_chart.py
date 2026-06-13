"""Horizontal bar chart: lag-1 r for MLB/NFL/NHL/NBA + snow (single + regional)."""
import json
from pathlib import Path

ANALYSIS = Path(__file__).parent
d = json.load(open(ANALYSIS / "predictability_cross_sport.json"))

# Order from highest to lowest persistence
items = [
    ("NBA",                d["NBA"]["lag1_r"],   d["NBA"]["n_pairs"],   "#c9962a", "small rosters, dominant superstars"),
    ("NHL",                d["NHL"]["lag1_r"],   d["NHL"]["n_pairs"],   "#2c4a6e", "moderate roster carry-over"),
    ("MLB",                d["MLB"]["lag1_r"],   d["MLB"]["n_pairs"],   "#2a6e3f", "deep rosters, individual stars dilute"),
    ("NFL",                d["NFL"]["lag1_r"],   d["NFL"]["n_pairs"],   "#8b1e3f", "17-game season, hard cap, draft parity"),
    ("CO ski region",      d["CO ski region snow"]["lag1_r"], d["CO ski region snow"]["n_pairs"], "#6b5e4a", "aggregate of 5 stations, no signal"),
    ("Steamboat snow",     d["Steamboat snow"]["lag1_r"],     d["Steamboat snow"]["n_pairs"],     "#6b5e4a", "single station, no signal"),
]

W, H = 760, 480
ML, MR, MT, MB = 200, 250, 60, 70
plot_w = W - ML - MR
plot_h = H - MT - MB
xv_lo, xv_hi = -0.05, 0.75

def X(v): return ML + (v - xv_lo) / (xv_hi - xv_lo) * plot_w

svg = [f'<svg class="chart" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Roboto Mono\',monospace">']
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ede5d2"/>')

svg.append(f'<text x="{W/2}" y="30" text-anchor="middle" font-family="Playfair Display" font-size="15" font-weight="700" fill="#1a1208">Year-over-year persistence: same test, six different systems</text>')
svg.append(f'<text x="{W/2}" y="48" text-anchor="middle" font-size="11" fill="#6b5e4a">Pooled lag-1 Pearson correlation of team win pct (sports) or seasonal total (snow), 1985–2025</text>')

# Vertical gridlines
for v in [-0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
    x = X(v)
    if v < xv_lo or v > xv_hi: continue
    color = "#1a1208" if v == 0 else "#c8b99a"
    sw = 2 if v == 0 else 1
    dash = "none" if v == 0 else "3,3"
    svg.append(f'<line x1="{x}" y1="{MT}" x2="{x}" y2="{MT+plot_h+5}" stroke="{color}" stroke-width="{sw}" stroke-dasharray="{dash}"/>')
    svg.append(f'<text x="{x}" y="{MT+plot_h+22}" text-anchor="middle" font-size="11" fill="#1a1208">{v:+.1f}</text>')

svg.append(f'<text x="{ML+plot_w/2}" y="{MT+plot_h+44}" text-anchor="middle" font-size="12" fill="#1a1208" font-weight="600">Pearson r — does last year predict next year?</text>')

# Bars
bar_h = 30
gap = 12
y_start = MT + 10
for i, (name, r, n, color, note) in enumerate(items):
    y = y_start + i * (bar_h + gap)
    x0 = X(0); xv = X(r)
    if r >= 0:
        svg.append(f'<rect x="{x0}" y="{y}" width="{xv-x0}" height="{bar_h}" fill="{color}" fill-opacity="0.88" stroke="#1a1208" stroke-width="1"/>')
        svg.append(f'<text x="{xv+6}" y="{y+bar_h/2+5}" font-family="Playfair Display" font-size="18" font-weight="700" fill="{color}">r = {r:+.3f}</text>')
    else:
        svg.append(f'<rect x="{xv}" y="{y}" width="{x0-xv}" height="{bar_h}" fill="#b83a1e" fill-opacity="0.85" stroke="#1a1208" stroke-width="1"/>')
        svg.append(f'<text x="{xv-6}" y="{y+bar_h/2+5}" text-anchor="end" font-family="Playfair Display" font-size="18" font-weight="700" fill="#b83a1e">r = {r:+.3f}</text>')
    # Left label
    svg.append(f'<text x="{ML-12}" y="{y+bar_h/2}" text-anchor="end" font-family="Playfair Display" font-size="15" font-weight="700" fill="#1a1208">{name}</text>')
    svg.append(f'<text x="{ML-12}" y="{y+bar_h/2+13}" text-anchor="end" font-family="Roboto Mono" font-size="9" fill="#6b5e4a">n={n} pairs</text>')
    # Right side annotation
    note_x = X(0.72)
    svg.append(f'<text x="{note_x}" y="{y+bar_h/2+5}" text-anchor="start" font-family="Libre Baskerville" font-style="italic" font-size="10" fill="#6b5e4a">{note}</text>')

svg.append('</svg>')

(ANALYSIS / "cross_sport_chart.svg").write_text("\n".join(svg))
print("Wrote cross_sport_chart.svg")
