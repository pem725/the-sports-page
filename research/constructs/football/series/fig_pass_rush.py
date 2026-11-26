#!/usr/bin/env python3
"""What Repeats, Part 4: pass rushers. Same player, next season, 95% intervals (Fisher z).
Writes series/fig_pass_rush.svg (inline-ready: class="chart", no width:100%, no paint-order)."""
import csv, math, os, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, '..', 'data', 'dl.csv')
INK, CREAM, STEEL, RUST, MUTED, GRID = '#1a1208', '#f5f0e8', '#2c4a6e', '#b83a1e', '#6b5e4a', '#d9cfba'
d = list(csv.DictReader(open(DATA))); by = {(r['gsis'], int(r['year'])): r for r in d}
pairs = [(r, by[(g, y + 1)]) for (g, y), r in by.items() if (g, y + 1) in by]
def rep(f):
    x, y = [], []
    for a, b in pairs:
        u, v = f(a), f(b)
        if u is not None and v is not None: x.append(u); y.append(v)
    r = st.correlation(x, y); z = math.atanh(r); s = 1 / math.sqrt(len(x) - 3)
    return r, math.tanh(z - 1.96 * s), math.tanh(z + 1.96 * s), len(x)
col = lambda k: (lambda r: float(r[k]))
ROWS = [('pressures (all three added up)', col('prss'), True), ('tackles on running plays', col('tk_run'), False),
        ('knockdowns', col('qbkd'), False), ('hurries', col('hrry'), False), ('sacks', col('sacks'), False),
        ('run stuffs (non-sack tackles for loss)', col('tfl_run'), False), ('forced fumbles', col('ff'), False),
        ('sacks per pressure (the finish)', lambda r: float(r['sacks']) / float(r['prss']) if float(r['prss']) > 0 else None, False)]
R = [(lab, *rep(f), comp) for lab, f, comp in ROWS]
W, H = 680, 430; x0, x1 = 300, 650; top, step = 58, 34
sx = lambda v: x0 + v * (x1 - x0)
o = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="Same pass rusher, next season: how closely each stat repeats, with 95 percent intervals. Pressures 0.68, tackles on running plays 0.60, knockdowns 0.48, hurries 0.46, sacks 0.43, run stuffs 0.24, forced fumbles 0.23, sacks per pressure 0.01." style="max-width:680px;margin:0 auto" font-family="\'Roboto Mono\',monospace">',
     f'<rect width="{W}" height="{H}" fill="{CREAM}"/>']
yend = top + step * (len(R) - 1)
for t in [0, .2, .4, .6, .8, 1]:
    o.append(f'<line x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{top - 18}" y2="{yend + 16}" stroke="{GRID}" stroke-width="0.7"/>')
    o.append(f'<text x="{sx(t):.1f}" y="{yend + 34}" font-size="11" fill="{MUTED}" text-anchor="middle">{t:g}</text>')
o.append(f'<text x="16" y="24" font-size="13" font-weight="600" fill="{INK}">Same pass rusher, next season: what repeats?</text>')
y = top
for lab, r, lo, hi, n, comp in R:
    c = RUST if comp else STEEL
    o.append(f'<text x="{x0 - 12}" y="{y + 4}" font-size="11.5" fill="{INK}" text-anchor="end">{lab}</text>')
    o.append(f'<line x1="{sx(max(lo, 0)):.1f}" x2="{sx(hi):.1f}" y1="{y}" y2="{y}" stroke="{INK}" stroke-width="1.4"/>')
    o.append(f'<circle cx="{sx(max(r, 0)):.1f}" cy="{y}" r="5" fill="{c}" stroke="{CREAM}" stroke-width="0.8"/>')
    o.append(f'<text x="{sx(hi) + 8:.1f}" y="{y + 4}" font-size="11" fill="{INK}">{r:.2f}</text>')
    y += step
o.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{yend + 56}" font-size="12.5" font-weight="600" fill="{INK}" text-anchor="middle">correlation with the same stat next season</text>')
o.append(f'<text x="16" y="{(top + yend) / 2:.1f}" font-size="12.5" font-weight="600" fill="{INK}" transform="rotate(-90 16 {(top + yend) / 2:.1f})" text-anchor="middle">stat</text>')
ky = H - 14
o.append(f'<circle cx="22" cy="{ky - 4}" r="5" fill="{RUST}"/><text x="32" y="{ky}" font-size="10.5" fill="{INK}">a sum of other stats</text>')
o.append(f'<circle cx="202" cy="{ky - 4}" r="5" fill="{STEEL}"/><text x="212" y="{ky}" font-size="10.5" fill="{INK}">a single stat</text>')
o.append(f'<line x1="322" x2="344" y1="{ky - 4}" y2="{ky - 4}" stroke="{INK}" stroke-width="1.4"/><text x="350" y="{ky}" font-size="10.5" fill="{INK}">95% interval &#183; 1,078 player pairs, 2018&#8211;2025</text>')
o.append('</svg>')
open(os.path.join(HERE, 'fig_pass_rush.svg'), 'w').write('\n'.join(o))
for lab, r, lo, hi, n, comp in R: print(f'{lab:40s} {r:.2f} [{lo:.2f}, {hi:.2f}] n={n}')
