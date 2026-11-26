#!/usr/bin/env python3
"""Dot chart: same player, next season, r with 95% interval (Fisher z), hitters / starters / relievers. fig/reliability.svg"""
import csv, math, os, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
INK, CREAM, STEEL, RUST, MUTED, GRID = '#1a1208', '#f5f0e8', '#2c4a6e', '#b83a1e', '#6b5e4a', '#d9cfba'
def pairs(fn, keyx, keyy, filt=lambda r: True):
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, 'data', fn))) if filt(r)]
    xs, ys = [], []
    for r in rows:
        try: a, b = float(r[keyx]), float(r[keyy])
        except ValueError: continue
        if math.isnan(a) or math.isnan(b): continue
        xs.append(a); ys.append(b)
    return st.correlation(xs, ys), len(xs)
import subprocess
# full set comes from the scored files: rebuild the pairs here so every row uses the same rule
def nextyear(fn, keys, filt):
    R = [r for r in csv.DictReader(open(os.path.join(HERE, 'data', fn))) if filt(r)]
    idx = {(r['pid'], int(r['year'])): r for r in R}; out = {}
    for k in keys:
        xs, ys = [], []
        for (pid, y), r in idx.items():
            n = idx.get((pid, y + 1))
            if not n or y in (2019, 2020): continue
            try: a, b = float(r[k]), float(n[k])
            except ValueError: continue
            if math.isnan(a) or math.isnan(b): continue
            xs.append(a); ys.append(b)
        out[k] = (st.correlation(xs, ys), len(xs))
    return out
H = nextyear('hitters_scored.csv', ['sprint', 'whiff', 'chase', 'so', 'ev', 'construct', 'hr', 'single', 'ops', 'avg'], lambda r: True)
S = nextyear('pitchers_scored.csv', ['velo', 'gb', 'whiff', 'so', 'construct', 'ubb', 'ev', 'hr', 'era', 'hbip'], lambda r: r['role'] == 'SP')
NAMES = {'sprint': 'sprint speed', 'whiff': 'whiff rate', 'chase': 'chase rate', 'so': 'strikeouts', 'ev': 'exit velocity',
         'construct': 'construct score', 'hr': 'home runs', 'single': 'singles', 'ops': 'OPS', 'avg': 'batting average',
         'velo': 'fastball velocity', 'gb': 'ground-ball rate', 'ubb': 'walks', 'era': 'ERA', 'hbip': 'hits on balls in play'}
COMPOSITE = {'ops', 'avg', 'era'}
def ci(r, n): z = math.atanh(r); s = 1 / math.sqrt(n - 3); return math.tanh(z - 1.96 * s), math.tanh(z + 1.96 * s)
W, Hh = 680, 620; x0, x1 = 210, 650; sx = lambda v: x0 + v * (x1 - x0)
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {Hh}" width="{W}" height="{Hh}" font-family="\'Roboto Mono\',monospace"><rect width="{W}" height="{Hh}" fill="{CREAM}"/>',
     f'<text x="16" y="24" font-size="13" font-weight="600" fill="{INK}">Same player, next season: what repeats?</text>']
top, step = 62, 21
def block(title, D, y):
    o.append(f'<text x="16" y="{y}" font-size="12" font-weight="600" fill="{STEEL}">{title}</text>'); y += 14
    for k, (r, n) in sorted(D.items(), key=lambda kv: -kv[1][0]):
        lo, hi = ci(r, n); col = RUST if k in COMPOSITE else STEEL
        o.append(f'<text x="{x0 - 10}" y="{y + 4}" font-size="11" fill="{INK}" text-anchor="end">{NAMES[k]}</text>')
        o.append(f'<line x1="{sx(lo):.1f}" x2="{sx(hi):.1f}" y1="{y}" y2="{y}" stroke="{INK}" stroke-width="1.4"/>')
        o.append(f'<circle cx="{sx(r):.1f}" cy="{y}" r="4.2" fill="{col}" stroke="{CREAM}" stroke-width="0.8"/>')
        o.append(f'<text x="{sx(hi) + 6:.1f}" y="{y + 4}" font-size="10" fill="{MUTED}">{r:.2f}</text>'); y += step
    return y + 10
for t in [0, .2, .4, .6, .8, 1]:
    o.append(f'<line x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{top - 8}" y2="{Hh - 64}" stroke="{GRID}" stroke-width="0.7"/><text x="{sx(t):.1f}" y="{Hh - 48}" font-size="11" fill="{MUTED}" text-anchor="middle">{t:g}</text>')
y = block('Hitters (300+ trips)', H, top); y = block('Starting pitchers', S, y)
o.append(f'<text x="{(x0 + x1) / 2}" y="{Hh - 28}" font-size="12.5" font-weight="600" fill="{INK}" text-anchor="middle">correlation with the same stat next season</text>')
# key: drawn dots (the font has no bullet glyph)
ky = Hh - 12
o.append(f'<circle cx="22" cy="{ky - 4}" r="4.2" fill="{RUST}"/><text x="32" y="{ky}" font-size="10.5" fill="{INK}">composite (AVG, OPS, ERA)</text>')
o.append(f'<circle cx="222" cy="{ky - 4}" r="4.2" fill="{STEEL}"/><text x="232" y="{ky}" font-size="10.5" fill="{INK}">single stat</text>')
o.append(f'<line x1="330" x2="352" y1="{ky - 4}" y2="{ky - 4}" stroke="{INK}" stroke-width="1.4"/><text x="358" y="{ky}" font-size="10.5" fill="{INK}">95% interval  \u00b7  2015\u201325, no 2020 pairs</text>')
o.append('</svg>'); open(os.path.join(HERE, 'fig', 'reliability.svg'), 'w').write('\n'.join(o)); print('wrote reliability.svg')
