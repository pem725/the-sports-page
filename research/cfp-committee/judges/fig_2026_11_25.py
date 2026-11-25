#!/usr/bin/env python3
"""Judges' Scorecard No. 2 figures (2026-11-25 ranking).
Panel A: committee rank vs our bowl-corrected math for the committee's top 12 (dumbbell).
Panel B: share of ranked-team pairs each computer orders the same way as the committee, with
95% bootstrap intervals (resampling teams). Massey ratings are read from data/private/ (never
committed, never reproduced); only the derived agreement share is drawn."""
import json, os, random
from itertools import combinations
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(H, "../../.."))
INK, RUST, STEEL, MUTED, DIV, CREAM = "#1a1208", "#b83a1e", "#2c4a6e", "#6b5e4a", "#c8b99a", "#f5f0e8"
F = "font-family=\"'Roboto Mono',monospace\""
w = json.load(open(os.path.join(H, "weekly-2026-11-25.json")))
rows = [r for r in w["rows"] if r["cfp"]]
M = json.load(open(os.path.join(ROOT, "data/private/massey/massey-2026-11-25.json")))["pwr"]
mp = {"Ohio State": "Ohio St", "Miami": "Miami FL", "Ole Miss": "Mississippi", "Boise State": "Boise St"}
mr = {t: i + 1 for i, (t, v) in enumerate(sorted(M.items(), key=lambda x: -x[1]))}
T = [(r["cfp"], r["math"], mr[mp.get(r["team"], r["team"])]) for r in rows]

def agree(S, j):
    c = t = 0
    for x, y in combinations(S, 2):
        s = (x[0] - y[0]) * (x[j] - y[j])
        if s: c += s > 0; t += 1
    return 100 * c / t
est = [agree(T, 1), agree(T, 2)]
random.seed(1); boots = [[], []]
for _ in range(4000):
    S = [random.choice(T) for _ in T]
    boots[0].append(agree(S, 1)); boots[1].append(agree(S, 2))
ci = [(sorted(b)[100], sorted(b)[3899]) for b in boots]
json.dump({"agree": est, "ci95": ci}, open(os.path.join(H, "agree-2026-11-25.json"), "w"), indent=1)
print("agreement", [round(e) for e in est], [(round(a), round(b)) for a, b in ci])

# ---- one SVG, two panels
W, L, R = 680, 140, 600
top12 = sorted(rows, key=lambda r: r["cfp"])[:12]
rh, y0 = 24, 46
sx = lambda rank: L + (R - L) * (rank - 1) / 11      # rank 1..12 across
hA = y0 + len(top12) * rh + 26
yB0 = hA + 40; bh = 26
sxB = lambda v: L + (R - L) * v / 100
h = yB0 + 2 * (bh + 14) + 40
aria = "; ".join(f"{r['team']}: committee {r['cfp']}, our math {r['math']}" for r in top12)
s = [f'<svg class="chart" viewBox="0 0 {W} {h}" role="img" aria-label="Committee rank against our math, top 12. {aria}. Pairs ordered the same as the committee: our math {est[0]:.0f} in 100, Massey power {est[1]:.0f} in 100." style="max-width:680px;margin:0 auto" {F}>']
s.append(f'<text x="{L}" y="18" font-size="12" font-weight="600" fill="{INK}">The committee&#8217;s top 12, and where our math puts them</text>')
for v in range(1, 13):
    s.append(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{y0-10}" y2="{hA-22}" stroke="{DIV}" stroke-width=".5"/>')
    s.append(f'<text x="{sx(v):.1f}" y="{y0-14}" font-size="10" fill="{MUTED}" text-anchor="middle">{v}</text>')
for i, r in enumerate(top12):
    cy = y0 + i * rh + rh / 2
    m = min(r["math"], 12.6)
    hot = r["team"] == "Alabama"
    col = RUST if hot else (INK if abs(r["math"] - r["cfp"]) >= 3 else MUTED)
    s.append(f'<line x1="{sx(r["cfp"]):.1f}" x2="{sx(m):.1f}" y1="{cy:.1f}" y2="{cy:.1f}" stroke="{col}" stroke-width="{3 if hot else 2}"/>')
    s.append(f'<circle cx="{sx(m):.1f}" cy="{cy:.1f}" r="5" fill="{CREAM}" stroke="{col}" stroke-width="1.8"/>')
    s.append(f'<circle cx="{sx(r["cfp"]):.1f}" cy="{cy:.1f}" r="5" fill="{col}"/>')
    s.append(f'<text x="{L-12}" y="{cy+4:.1f}" font-size="12" fill="{RUST if hot else INK}" font-weight="{600 if hot else 400}" text-anchor="end">{r["team"]}</text>')
s.append(f'<text x="{(L+R)/2:.0f}" y="{hA-6}" font-size="10" fill="{MUTED}" text-anchor="middle">rank &#183; filled = committee &#183; open = our math</text>')
s.append(f'<text x="{L}" y="{yB0-12}" font-size="12" font-weight="600" fill="{INK}">Of every 100 pairs of ranked teams, how many each computer puts in the committee&#8217;s order</text>')
for v in (0, 25, 50, 75, 100):
    s.append(f'<line x1="{sxB(v):.1f}" x2="{sxB(v):.1f}" y1="{yB0}" y2="{yB0+2*(bh+14)-8}" stroke="{DIV}" stroke-width=".5"/>')
    s.append(f'<text x="{sxB(v):.1f}" y="{yB0+2*(bh+14)+6}" font-size="10" fill="{MUTED}" text-anchor="middle">{v}</text>')
for i, (lab, e, (lo, hi), col) in enumerate([("Our math", est[0], ci[0], STEEL), ("Massey power", est[1], ci[1], MUTED)]):
    y = yB0 + i * (bh + 14)
    s.append(f'<rect x="{L}" y="{y}" width="{sxB(e)-L:.1f}" height="{bh}" fill="{col}"/>')
    s.append(f'<line x1="{sxB(lo):.1f}" x2="{sxB(hi):.1f}" y1="{y+bh/2}" y2="{y+bh/2}" stroke="{INK}" stroke-width="1"/>')
    s.append(f'<line x1="{sxB(lo):.1f}" x2="{sxB(lo):.1f}" y1="{y+bh/2-4}" y2="{y+bh/2+4}" stroke="{INK}" stroke-width="1"/>')
    s.append(f'<line x1="{sxB(hi):.1f}" x2="{sxB(hi):.1f}" y1="{y+bh/2-4}" y2="{y+bh/2+4}" stroke="{INK}" stroke-width="1"/>')
    s.append(f'<text x="{L-12}" y="{y+bh/2+4}" font-size="12" fill="{INK}" text-anchor="end">{lab}</text>')
    s.append(f'<text x="{sxB(hi)+8:.1f}" y="{y+bh/2+4}" font-size="12" font-weight="600" fill="{INK}">{e:.0f} <tspan font-weight="400" fill="{MUTED}" font-size="10">({lo:.0f}&#8211;{hi:.0f})</tspan></text>')
s.append("</svg>")
open(os.path.join(H, "fig-2026-11-25.svg"), "w").write("\n".join(s))
print("wrote fig-2026-11-25.svg")
