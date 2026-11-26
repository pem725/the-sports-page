#!/usr/bin/env python3
"""Redraw the RB scatterplots as crisp house-style SVG (they were blurry default-R PNGs)."""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from hs_scatter import scatter
F = os.path.join(HERE, 'fig')
h = [r for r in csv.DictReader(open(os.path.join(HERE, 'data', 'rb_hist.csv')))]
by = {(r['gsis'], int(r['year'])): r for r in h}
def pairs(mn):
    out = []
    for (g, y), r in by.items():
        n = by.get((g, y + 1))
        if n and float(r['car']) >= mn and float(n['car']) >= mn:
            out.append((float(r['yds']) / float(r['car']), float(n['yds']) / float(n['car'])))
    return out
for mn in (100, 250):
    P = pairs(mn)
    open(os.path.join(F, f'ypc_next_year_{mn}.svg'), 'w').write(scatter([p[0] for p in P], [p[1] for p in P],
        title=f'Same back, next season ({mn}+ carries both years)', xlab='yards per carry, this season',
        ylab='yards per carry, next season', diagonal=True, xlim=(2.5, 7), ylim=(2.5, 7)))
L = [r for r in csv.DictReader(open(os.path.join(HERE, 'data', 'rb_link.csv'))) if float(r['cfb_car']) >= 200 and float(r['nfl_car']) >= 200]
X = [float(r['cfb_ypc']) for r in L]; Y = [float(r['nfl_ypc']) for r in L]; N = [r['name'] for r in L]
show = {'Darrell Henderson', 'Derrick Henry', 'Jahmyr Gibbs', "De'Von Achane", 'Isiah Pacheco'}
open(os.path.join(F, 'college_to_nfl.svg'), 'w').write(scatter(X, Y, labels=N, size=[float(r['nfl_car']) for r in L],
    highlight={'Darrell Henderson'}, diagonal=True, title='The same back in two leagues',
    xlab='yards per carry in college (2014+ seasons) · dot size = NFL carries', ylab='NFL yards per carry (every carry)',
    label_if=lambda i: N[i] in show))
print('ok')
