#!/usr/bin/env python3
"""Two figures for the time-of-possession piece: the DAG (dag.svg) and fourth-quarter run share
by score (runshare.svg, from arrows.json)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
INK, RUST, STEEL, MUTED, DIV, CREAM = "#1a1208", "#b83a1e", "#2c4a6e", "#6b5e4a", "#c8b99a", "#f5f0e8"
F = "font-family=\"'Roboto Mono',monospace\""

def node(x, y, w, h, label, sub=None, dashed=False):
    s = []
    dash = ' stroke-dasharray="5 4"' if dashed else ''
    s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{CREAM}" stroke="{MUTED if dashed else INK}" stroke-width="1.6"{dash}/>')
    cy = y + h / 2 + (-4 if sub else 5)
    s.append(f'<text x="{x+w/2}" y="{cy}" font-size="14" font-weight="600" fill="{INK}" text-anchor="middle">{label}</text>')
    if sub: s.append(f'<text x="{x+w/2}" y="{cy+17}" font-size="11" fill="{MUTED}" text-anchor="middle">{sub}</text>')
    return s

def arrow(x1, y1, x2, y2, color=INK, dashed=False, mid=None):
    dash = ' stroke-dasharray="6 5"' if dashed else ''
    m = "url(#ah)" if color == INK else "url(#ahr)"
    s = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"{dash} marker-end="{m}"/>']
    if mid: s.append(f'<text x="{(x1+x2)/2+mid[1]}" y="{(y1+y2)/2+mid[2]}" font-size="12" fill="{color}" text-anchor="middle">{mid[0]}</text>')
    return s

s = [f'<svg class="chart" viewBox="0 0 680 270" role="img" aria-label="Diagram of causes. Team quality, which the box score cannot see, leads to a lead and to running well. A lead leads to winning and to running the ball. Running the ball leads to time of possession. A dashed arrow from time of possession to winning, marked with a question mark, is the arrow the broadcast draws." style="max-width:680px;margin:0 auto" {F}>',
     f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z" fill="{INK}"/></marker>'
     f'<marker id="ahr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z" fill="{RUST}"/></marker></defs>']
s += node(10, 100, 170, 64, "Team quality", "hidden: the lines", dashed=True)
s += node(250, 20, 150, 44, "A lead")
s += node(500, 20, 150, 44, "Win")
s += node(250, 200, 150, 44, "Run the ball")
s += node(480, 200, 190, 44, "Time of possession")
s += arrow(180, 118, 248, 52)
s += arrow(180, 148, 248, 212)
s += arrow(400, 42, 498, 42)
s += arrow(325, 64, 325, 198)
s += arrow(400, 222, 478, 222)
s += arrow(560, 198, 570, 66, RUST, dashed=True, mid=("?", 14, 4))
s.append(f'<text x="600" y="140" font-size="11" fill="{RUST}" text-anchor="start">the arrow</text><text x="600" y="155" font-size="11" fill="{RUST}">on TV</text>')
s.append('</svg>')
open(os.path.join(HERE, "dag.svg"), "w").write("\n".join(s))

a = json.load(open(os.path.join(HERE, "arrows.json")))["run_share_q4"]
labels = list(a); W, B, T, L = 680, 230, 30, 40
sy = lambda v: B - (B - T) * v / 100
bw = (W - L - 20) / len(labels)
s = [f'<svg class="chart" viewBox="0 0 {W} 280" role="img" aria-label="Fourth quarter, runs per 100 plays by the offense\'s score: ' + "; ".join(f"{k}: {v:.0f}" for k, v in a.items()) + f'." style="max-width:680px;margin:0 auto" {F}>']
for v in (0, 25, 50, 75, 100):
    s.append(f'<line x1="{L}" x2="{W-20}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{DIV}" stroke-width="{1 if v == 0 else .5}"/>')
    s.append(f'<text x="{L-6}" y="{sy(v)+4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">{v}</text>')
for i, (k, v) in enumerate(a.items()):
    cx = L + bw * i + bw / 2; col = RUST if k.startswith("behind") else STEEL if k.startswith("ahead") else MUTED
    s.append(f'<rect x="{cx-bw*.3:.1f}" y="{sy(v):.1f}" width="{bw*.6:.1f}" height="{B-sy(v):.1f}" fill="{col}"/>')
    s.append(f'<text x="{cx:.1f}" y="{sy(v)-6:.1f}" font-size="14" font-weight="600" fill="{INK}" text-anchor="middle">{v:.0f}</text>')
    s.append(f'<text x="{cx:.1f}" y="{B+18}" font-size="12" fill="{INK}" text-anchor="middle">{k}</text>')
s.append(f'<text x="{L+(W-L-20)/2:.0f}" y="{B+40}" font-size="11" fill="{MUTED}" text-anchor="middle">the offense\'s score, fourth quarter</text>')
s.append(f'<text x="{L}" y="{T-12}" font-size="11" fill="{MUTED}">runs per 100 plays</text>')
s.append('</svg>')
open(os.path.join(HERE, "runshare.svg"), "w").write("\n".join(s))
