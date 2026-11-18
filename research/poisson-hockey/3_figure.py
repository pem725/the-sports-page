#!/usr/bin/env python3
"""Figure for the piece: per 100 team-games, how many scored k goals (bars) against the
Poisson curve drawn from the average alone (dots). Reads counts.json from 1_counts.py.
Writes figure.svg and prints every number the prose quotes."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
c = json.load(open(os.path.join(HERE, "counts.json")))
a = c["all"]; N = a["N"]
obs = [r["obs"] for r in a["rows"]]; exp = [r["exp"] for r in a["rows"]]
# fold 8, 9, 10+ into "8+"
o = obs[:8] + [sum(obs[8:])]; e = exp[:8] + [sum(exp[8:])]
po = [100*x/N for x in o]; pe = [100*x/N for x in e]
labels = [str(k) for k in range(8)] + ["8+"]
for l, x, y in zip(labels, po, pe):
    print(f"{l:>3}  real {x:5.2f}  poisson {y:5.2f}")
print("team-games", N, "games", N//2, "mean", round(a["mean"], 2), "var", round(a["var"], 2))
print("8+ real", sum(obs[8:]), "poisson", round(sum(exp[8:])))
ne = c["reg_noen"]; print("no-EN mean", round(ne["mean"], 2), "var", round(ne["var"], 2),
                          "zeros", ne["rows"][0])

W, H, L, B, T = 680, 300, 50, 250, 30
ymax = 25; sy = lambda v: B - (B - T) * v / ymax
bw = (W - L - 20) / len(labels)
s = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="Out of every 100 NHL team-games since 2015-16, how many ended with each number of goals, beside the Poisson curve drawn from the average alone. '
     + "; ".join(f"{l} goals: {x:.0f} real, {y:.0f} predicted" for l, x, y in zip(labels, po, pe))
     + '." style="max-width:680px;margin:0 auto;font-family:\'Roboto Mono\',monospace">']
for v in (0, 5, 10, 15, 20, 25):
    s.append(f'<line x1="{L}" x2="{W-20}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="#c8b99a" stroke-width="{1 if v == 0 else 0.5}"/>')
    s.append(f'<text x="{L-8}" y="{sy(v)+4:.1f}" font-size="11" fill="#6b5e4a" text-anchor="end">{v}</text>')
pts = []
for i, (l, x, y) in enumerate(zip(labels, po, pe)):
    cx = L + bw * i + bw / 2
    s.append(f'<rect x="{cx-bw*0.32:.1f}" y="{sy(x):.1f}" width="{bw*0.64:.1f}" height="{B-sy(x):.1f}" fill="#2c4a6e"/>')
    s.append(f'<text x="{cx:.1f}" y="{B+18}" font-size="12" fill="#1a1208" text-anchor="middle">{l}</text>')
    pts.append((cx, sy(y)))
s.append('<polyline fill="none" stroke="#b83a1e" stroke-width="2" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '"/>')
for x, y in pts:
    s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#f5f0e8" stroke="#b83a1e" stroke-width="2"/>')
s.append(f'<text x="{L+(W-L-20)/2:.0f}" y="{B+38}" font-size="11" fill="#6b5e4a" text-anchor="middle">goals scored by one team in one game</text>')
s.append(f'<text x="{L-8}" y="{T-12}" font-size="11" fill="#6b5e4a" text-anchor="start" dx="-30">per 100 team-games</text>')
lx = W - 250
s.append(f'<rect x="{lx}" y="{T}" width="14" height="14" fill="#2c4a6e"/><text x="{lx+20}" y="{T+12}" font-size="12" fill="#1a1208">what happened</text>')
s.append(f'<circle cx="{lx+7}" cy="{T+30}" r="4.5" fill="#f5f0e8" stroke="#b83a1e" stroke-width="2"/><text x="{lx+20}" y="{T+34}" font-size="12" fill="#1a1208">Poisson, from the average</text>')
s.append('</svg>')
open(os.path.join(HERE, "figure.svg"), "w").write("\n".join(s))
