#!/usr/bin/env python3
"""Inline SVG: title chances per 100 seasons, from results.json. Prints the <svg>."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
r = json.load(open(os.path.join(HERE, "results.json")))
rows = [x for x in r["rows"] if x["title"] >= 0.0095][:13]
W, top, rh, lx, scale = 680, 34, 25, 190, 12.0
H = top + rh * len(rows) + 30
aria = "Title chances per 100 seasons: " + "; ".join(f"{x['team']} {round(x['title']*100)}" for x in rows)
out = [f'<svg class="chart" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{aria}." '
       f'style="max-width:100%;height:auto;display:block;margin:0 auto;font-family:\'Roboto Mono\',monospace">',
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
    out.append(f'<text x="{lx+max(v*scale,2)+6:.0f}" y="{y+15}" font-size="12" font-weight="600" fill="#1a1208">{v}</text>')
yb = top + rh * len(rows) + 4
out.append(f'<line x1="{lx}" y1="{top}" x2="{lx}" y2="{yb}" stroke="#1a1208" stroke-width="1"/>')
out.append(f'<text x="8" y="{yb+18}" font-size="11" fill="#6b5e4a">Left: committee rank, Nov. 17. Not shown: under 1 in 100.</text>')
out.append('</svg>')
print("\n".join(out))
