#!/usr/bin/env python3
"""Inline SVG: title chances per 100 seasons, from results.json. Prints the <svg>."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
r = json.load(open(os.path.join(HERE, "results_ci.json")))  # rating-uncertainty run (sim.py --rating-draws 400)
rows = [x for x in r["rows"] if x["title"] >= 0.0095][:13]
W, top, rh, lx, scale = 680, 34, 25, 190, 6.4
lo_ = lambda x: "&lt;1" if x < 0.005 else str(round(x * 100))
H = top + rh * len(rows) + 30
aria = "Title chances per 100 seasons, with 95 percent intervals allowing for error in the ratings: " + "; ".join(f"{x['team']} {round(x['title']*100)} ({lo_(x['title_lo']).replace('&lt;', 'under ')} to {round(x['title_hi']*100)})" for x in rows)
out = [f'<svg class="chart" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{aria}." '
       f'style="max-width:680px;margin:0 auto;font-family:\'Roboto Mono\',monospace">',
       f'<rect x="0" y="0" width="{W}" height="{H}" fill="#f5f0e8"/>',
       f'<text x="{lx}" y="18" font-size="12" fill="#6b5e4a">National titles per 100 simulated seasons</text>']
for i, x in enumerate(rows):
    y = top + i * rh
    v = round(x["title"] * 100)
    col = "#b83a1e" if x["team"] == "Georgia" else "#2c4a6e"
    rk = f"No. {x['cfp_rank']}" if x["cfp_rank"] else ""
    out.append(f'<text x="8" y="{y+15}" font-size="11" fill="#6b5e4a">{rk}</text>')
    out.append(f'<text x="{lx-10}" y="{y+15}" font-size="12" text-anchor="end" fill="#1a1208">{x["team"]}</text>')
    out.append(f'<rect x="{lx}" y="{y+3}" width="{max(v*scale,2):.0f}" height="{rh-8}" fill="{col}"/>')
    x1, x2 = lx + x["title_lo"] * 100 * scale, lx + x["title_hi"] * 100 * scale
    out.append(f'<line x1="{x1:.1f}" x2="{x2:.1f}" y1="{y+11.5}" y2="{y+11.5}" stroke="#1a1208" stroke-width="1.2"/>')
    out.append(f'<text x="{x2+6:.0f}" y="{y+15}" font-size="12" font-weight="600" fill="#1a1208">{v}<tspan font-size="10" font-weight="400" fill="#6b5e4a"> ({lo_(x["title_lo"])}&#8211;{round(x["title_hi"]*100)})</tspan></text>')
yb = top + rh * len(rows) + 4
out.append(f'<line x1="{lx}" y1="{top}" x2="{lx}" y2="{yb}" stroke="#1a1208" stroke-width="1"/>')
out.append(f'<text x="8" y="{yb+18}" font-size="11" fill="#6b5e4a">Left: committee rank, Nov. 17. Thin line and ( ): 95% interval. Not shown: under 1 in 100.</text>')
out.append('</svg>')
print("\n".join(out))
