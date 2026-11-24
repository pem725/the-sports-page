#!/usr/bin/env python3
"""Dumbbell figure for the Family Table piece: each Thanksgiving team's playoff chance if it loses
(open circle) and if it wins (filled), from data/family_2026.json. Writes family.svg."""
import json, math, os
H = os.path.dirname(os.path.abspath(__file__))
INK, RUST, STEEL, MUTED, DIV, CREAM = "#1a1208", "#b83a1e", "#2c4a6e", "#6b5e4a", "#c8b99a", "#f5f0e8"
F = "font-family=\"'Roboto Mono',monospace\""
NAME = {"CHI": "Bears", "DET": "Lions", "PHI": "Eagles", "DAL": "Cowboys", "KC": "Chiefs", "BUF": "Bills"}
r = json.load(open(os.path.join(H, "data", "family_2026.json")))
N = r["sims"]
rows = []
for g in r["games"][:3]:
    a, b = g["game"].split(" at ")
    rows.append((g["game"], [(t, g[t]) for t in (a, b)], g["game_leverage_pts"]))

W, L, R, top, rh, gap = 680, 120, 600, 40, 30, 22
sx = lambda v: L + (R - L) * v / 100
h = top + len(rows) * (2 * rh + gap) + 30
aria = "; ".join(f"{NAME[t]}: {100*d['if_lose']:.0f} if they lose, {100*d['if_win']:.0f} if they win" for _, ts, _ in rows for t, d in ts)
s = [f'<svg class="chart" viewBox="0 0 {W} {h}" role="img" aria-label="Chance of making the playoffs, by Thanksgiving result. {aria}." style="max-width:680px;margin:0 auto" {F}>']
for v in (0, 25, 50, 75, 100):
    s.append(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{top-8}" y2="{h-30}" stroke="{DIV}" stroke-width=".5"/>')
    s.append(f'<text x="{sx(v):.1f}" y="{top-14}" font-size="11" fill="{MUTED}" text-anchor="middle">{v}</text>')
y = top
for game, ts, lev in rows:
    for i, (t, d) in enumerate(ts):
        cy = y + i * rh + rh / 2
        lo, hi = 100 * d["if_lose"], 100 * d["if_win"]
        # Monte Carlo 95% half-width for each conditional chance (it is tiny; drawn to true scale)
        for q, n in ((d["if_win"], N * 0.5), (d["if_lose"], N * 0.5)):
            hw = 196 * math.sqrt(max(q * (1 - q), 1e-6) / n)
            s.append(f'<line x1="{sx(100*q-hw):.1f}" x2="{sx(100*q+hw):.1f}" y1="{cy:.1f}" y2="{cy:.1f}" stroke="{INK}" stroke-width="1"/>')
        col = RUST if hi - lo >= 5 else MUTED
        s.append(f'<line x1="{sx(lo):.1f}" x2="{sx(hi):.1f}" y1="{cy:.1f}" y2="{cy:.1f}" stroke="{col}" stroke-width="3"/>')
        s.append(f'<circle cx="{sx(lo):.1f}" cy="{cy:.1f}" r="5" fill="{CREAM}" stroke="{col}" stroke-width="1.8"/>')
        s.append(f'<circle cx="{sx(hi):.1f}" cy="{cy:.1f}" r="5" fill="{col}"/>')
        s.append(f'<text x="{L-10}" y="{cy+4:.1f}" font-size="13" fill="{INK}" text-anchor="end">{NAME[t]}</text>')
    s.append(f'<text x="{R+40}" y="{y+rh+4:.1f}" font-size="15" font-weight="600" fill="{RUST if lev >= 5 else MUTED}">{lev:.0f}</text>')
    y += 2 * rh + gap
s.append(f'<text x="{R+40}" y="{top-14}" font-size="11" fill="{MUTED}">swing</text>')
s.append(f'<text x="{(L+R)/2:.0f}" y="{h-8}" font-size="11" fill="{MUTED}" text-anchor="middle">chance of making the playoffs, per 100 &#183; open = if they lose, filled = if they win</text>')
s.append('</svg>')
open(os.path.join(H, "family.svg"), "w").write("\n".join(s))
print("wrote family.svg")
