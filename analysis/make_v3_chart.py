"""SVG: scoreboard chart for predictability v3.
   Left half: lag-1 r at single-unit and aggregate levels.
   Right half: % RMSE reduction from conditional model.
   Theme: baseball wins at every level of comparison."""
import json
from pathlib import Path

ANALYSIS = Path(__file__).parent
d = json.load(open(ANALYSIS / "predictability_v3.json"))

# Values
single_snow_r = d["steamboat_single"]["lag1_r"]
single_mets_r = d["mets_single"]["lag1_r"]
agg_snow_r    = d["region_snow"]["lag1_r"]
agg_mlb_r     = d["mlb_league"]["lag1_r"]
snow_lift     = d["region_snow"]["rmse_reduction_pct"]
mlb_lift      = d["mlb_league"]["rmse_reduction_pct"]

W, H = 760, 540
MT, MB = 60, 40
ML = 280
plot_w = W - ML - 80
plot_h = H - MT - MB
panel_h = (plot_h - 80) / 2  # two halves with a gap

SNOW_COLOR = "#2c4a6e"
MLB_COLOR  = "#2a6e3f"
NEG_COLOR  = "#b83a1e"

svg = [f'<svg class="chart" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="\'Roboto Mono\',monospace">']
svg.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ede5d2"/>')

# Title
svg.append(f'<text x="{W/2}" y="{30}" text-anchor="middle" font-family="Playfair Display" font-size="15" font-weight="700" fill="#1a1208">At every level of comparison, baseball wins.</text>')

# ─── Top half: lag-1 correlation, 4 bars ───
TOP_Y = MT
top_h = panel_h
# X scale for r values: -0.1 to 0.8
xv_lo, xv_hi = -0.1, 0.8
def X(v): return ML + (v - xv_lo) / (xv_hi - xv_lo) * plot_w

# Section label
svg.append(f'<text x="20" y="{TOP_Y + 18}" font-family="Playfair Display" font-size="12" font-weight="700" fill="#1a1208" text-transform="uppercase">LAG-1 PERSISTENCE</text>')
svg.append(f'<text x="20" y="{TOP_Y + 34}" font-size="10" fill="#6b5e4a">Does last year predict next year? (Pearson r)</text>')

# Zero line + gridlines
for v in [-0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
    x = X(v)
    color = "#1a1208" if v == 0 else "#c8b99a"
    sw = 2 if v == 0 else 1
    dash = "none" if v == 0 else "3,3"
    svg.append(f'<line x1="{x}" y1="{TOP_Y+50}" x2="{x}" y2="{TOP_Y+top_h+10}" stroke="{color}" stroke-width="{sw}" stroke-dasharray="{dash}"/>')
    svg.append(f'<text x="{x}" y="{TOP_Y+top_h+24}" text-anchor="middle" font-size="10" fill="#1a1208">{v:+.1f}</text>')

# Subsection labels and bars
bars = [
    ("SINGLE UNIT", TOP_Y + 60, "single"),
    ("AGGREGATE",   TOP_Y + 130, "aggregate"),
]
bar_h = 22; bar_gap = 4

def draw_bar(label, value, y, color, neg_color=NEG_COLOR, value_fmt="{:+.3f}"):
    bar_start = X(0)
    bar_end = X(value)
    if value >= 0:
        svg.append(f'<rect x="{bar_start}" y="{y}" width="{bar_end-bar_start}" height="{bar_h}" fill="{color}" fill-opacity="0.85" stroke="#1a1208" stroke-width="1"/>')
        svg.append(f'<text x="{bar_end+6}" y="{y+bar_h/2+4}" text-anchor="start" font-family="Playfair Display" font-size="14" font-weight="700" fill="{color}">{value_fmt.format(value)}</text>')
    else:
        svg.append(f'<rect x="{bar_end}" y="{y}" width="{bar_start-bar_end}" height="{bar_h}" fill="{neg_color}" fill-opacity="0.85" stroke="#1a1208" stroke-width="1"/>')
        svg.append(f'<text x="{bar_end-6}" y="{y+bar_h/2+4}" text-anchor="end" font-family="Playfair Display" font-size="14" font-weight="700" fill="{neg_color}">{value_fmt.format(value)}</text>')
    svg.append(f'<text x="{ML-10}" y="{y+bar_h/2+4}" text-anchor="end" font-family="Roboto Mono" font-size="11" font-weight="600" fill="#1a1208">{label}</text>')

svg.append(f'<text x="{ML-10}" y="{TOP_Y+62}" text-anchor="end" font-family="Playfair Display" font-style="italic" font-size="10" fill="#6b5e4a">single unit</text>')
draw_bar("Steamboat snow", single_snow_r, TOP_Y + 70, SNOW_COLOR)
draw_bar("Mets win pct",   single_mets_r, TOP_Y + 70 + bar_h + bar_gap, MLB_COLOR)
svg.append(f'<text x="{ML-10}" y="{TOP_Y+148}" text-anchor="end" font-family="Playfair Display" font-style="italic" font-size="10" fill="#6b5e4a">aggregated</text>')
draw_bar("CO ski region",  agg_snow_r,    TOP_Y + 156, SNOW_COLOR)
draw_bar("MLB league OPS", agg_mlb_r,     TOP_Y + 156 + bar_h + bar_gap, MLB_COLOR)

# ─── Bottom half: % RMSE reduction (aggregate only) ───
BOT_Y = TOP_Y + top_h + 40
bot_h = panel_h

svg.append(f'<text x="20" y="{BOT_Y + 18}" font-family="Playfair Display" font-size="12" font-weight="700" fill="#1a1208" text-transform="uppercase">CONDITIONAL PREDICTION</text>')
svg.append(f'<text x="20" y="{BOT_Y + 34}" font-size="10" fill="#6b5e4a">Does a profile (ENSO state, league rate vector) beat climatology?</text>')

xv_lo2, xv_hi2 = -10, 60
def X2(v): return ML + (v - xv_lo2) / (xv_hi2 - xv_lo2) * plot_w

for v in [-10, 0, 10, 20, 30, 40, 50, 60]:
    x = X2(v)
    color = "#1a1208" if v == 0 else "#c8b99a"
    sw = 2 if v == 0 else 1
    dash = "none" if v == 0 else "3,3"
    svg.append(f'<line x1="{x}" y1="{BOT_Y+50}" x2="{x}" y2="{BOT_Y+bot_h+10}" stroke="{color}" stroke-width="{sw}" stroke-dasharray="{dash}"/>')
    svg.append(f'<text x="{x}" y="{BOT_Y+bot_h+24}" text-anchor="middle" font-size="10" fill="#1a1208">{v:+d}%</text>')
svg.append(f'<text x="{ML+plot_w/2}" y="{BOT_Y+bot_h+40}" text-anchor="middle" font-size="11" fill="#1a1208" font-weight="600">% RMSE reduction (leave-one-out cross-validation)</text>')

def draw_pct_bar(label, value, y, color):
    bar_start = X2(0); bar_end = X2(value)
    if value >= 0:
        svg.append(f'<rect x="{bar_start}" y="{y}" width="{bar_end-bar_start}" height="{bar_h+8}" fill="{color}" fill-opacity="0.85" stroke="#1a1208" stroke-width="1"/>')
        svg.append(f'<text x="{bar_end+6}" y="{y+(bar_h+8)/2+5}" text-anchor="start" font-family="Playfair Display" font-size="16" font-weight="700" fill="{color}">{value:+.1f}%</text>')
    else:
        svg.append(f'<rect x="{bar_end}" y="{y}" width="{bar_start-bar_end}" height="{bar_h+8}" fill="{NEG_COLOR}" fill-opacity="0.85" stroke="#1a1208" stroke-width="1"/>')
        svg.append(f'<text x="{bar_end-6}" y="{y+(bar_h+8)/2+5}" text-anchor="end" font-family="Playfair Display" font-size="16" font-weight="700" fill="{NEG_COLOR}">{value:+.1f}%</text>')
    svg.append(f'<text x="{ML-10}" y="{y+(bar_h+8)/2+5}" text-anchor="end" font-family="Roboto Mono" font-size="11" font-weight="600" fill="#1a1208">{label}</text>')

draw_pct_bar("CO region + ENSO state",      snow_lift, BOT_Y + 70, SNOW_COLOR)
draw_pct_bar("MLB league + profile match",  mlb_lift,  BOT_Y + 70 + bar_h + 16, MLB_COLOR)

svg.append('</svg>')
(ANALYSIS / "predictability_v3_chart.svg").write_text("\n".join(svg))
print("Wrote predictability_v3_chart.svg")
