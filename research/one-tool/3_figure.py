#!/usr/bin/env python3
"""Figure: share of decisions changed or lost under the one-tool analyst, by kind of question,
with 95% Wilson intervals. Horizontal bars, labeled axes, house palette, crisp SVG."""
import json, glob, math, os
H = os.path.dirname(os.path.abspath(__file__))
C = {}
for f in glob.glob(os.path.join(H, 'codes', 'coder[ABCD].jsonl')):
    for l in open(f): o = json.loads(l); C[str(o['issue'])] = o
NAMES = [('group-difference', 'comparing two groups'), ('descriptive-history', 'describing the record'),
         ('association', 'does X go with Y?'), ('small-sample-rate', 'a rate on few tries'),
         ('causal', 'does X cause Y?'), ('measurement', 'what a stat measures'),
         ('forecast-probability', 'forecasts and chances')]
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h
rows = []
for key, lab in NAMES:
    v = [o for o in C.values() if o['question_type'] == key]
    k = sum(o['verdict'] in ('CHANGED', 'CANNOT-ASK') for o in v); lo, hi = wilson(k, len(v))
    rows.append((lab, k, len(v), k / len(v), lo, hi))
INK, CREAM, STEEL, RUST, MUTED, GRID = '#1a1208', '#f5f0e8', '#2c4a6e', '#b83a1e', '#6b5e4a', '#d9cfba'
W, Hh = 680, 400; x0, x1 = 230, 590; sx = lambda v: x0 + v * (x1 - x0); top, step = 52, 40
o = [f'<svg class="chart" viewBox="0 0 {W} {Hh}" role="img" aria-label="Share of our decisions that change or vanish when only t-tests and ANOVA are allowed, by kind of question, with 95 percent intervals: '
     + '; '.join(f'{r[0]}: {r[1]} of {r[2]}' for r in rows) + f'." style="max-width:680px;margin:0 auto" font-family="\'Roboto Mono\',monospace">']
for t in (0, .25, .5, .75, 1):
    o.append(f'<line x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{top - 14}" y2="{top + step * len(rows) - 10}" stroke="{GRID}" stroke-width="0.8"/>'
             f'<text x="{sx(t):.1f}" y="{top + step * len(rows) + 6}" font-size="11" fill="{MUTED}" text-anchor="middle">{int(t * 100)}</text>')
for i, (lab, k, n, p, lo, hi) in enumerate(rows):
    y = top + i * step; col = STEEL if i == 0 else (MUTED if i == 1 else RUST)
    o.append(f'<text x="{x0 - 10}" y="{y + 4}" font-size="11.5" fill="{INK}" text-anchor="end">{lab}</text>')
    o.append(f'<rect x="{x0}" y="{y - 11}" width="{max(1.5, sx(p) - x0):.1f}" height="22" fill="{col}"/>')
    o.append(f'<line x1="{sx(lo):.1f}" x2="{sx(hi):.1f}" y1="{y}" y2="{y}" stroke="{INK}" stroke-width="1.5"/>'
             f'<line x1="{sx(lo):.1f}" x2="{sx(lo):.1f}" y1="{y - 5}" y2="{y + 5}" stroke="{INK}" stroke-width="1.2"/><line x1="{sx(hi):.1f}" x2="{sx(hi):.1f}" y1="{y - 5}" y2="{y + 5}" stroke="{INK}" stroke-width="1.2"/>')
    o.append(f'<text x="{W - 12}" y="{y + 4}" font-size="11" font-weight="600" fill="{INK}" text-anchor="end">{k} of {n}</text>')
o.append(f'<text x="{(x0 + x1) / 2}" y="{Hh - 30}" font-size="12.5" font-weight="600" fill="{INK}" text-anchor="middle">decisions changed or lost, per 100</text>')
o.append(f'<text x="16" y="{Hh - 10}" font-size="10.5" fill="{MUTED}">lines: 95% intervals \u00b7 blue: what ANOVA is for \u00b7 gray: no inference \u00b7 red: the rest</text>')
o.append(f'<text x="16" y="22" font-size="12.5" font-weight="600" fill="{INK}">kind of question</text></svg>')
open(os.path.join(H, 'fig_by_question.svg'), 'w').write('\n'.join(o))
for r in rows: print(r[0], r[1], r[2], round(r[4] * 100), round(r[5] * 100))
