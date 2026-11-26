#!/usr/bin/env python3
"""Every reported correlation, plotted (house style, crisp SVG). fig/*.svg"""
import csv, math, os, sys, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from hs_scatter import scatter
F = os.path.join(HERE, 'fig')
def rd(fn): return list(csv.DictReader(open(os.path.join(HERE, 'data', fn))))
def save(name, svg): open(os.path.join(F, name), 'w').write(svg); print('wrote', name)
hp = rd('hit_pairs.csv'); pp = rd('pitch_pairs.csv')
x = lambda rows, k, f=float: [f(r[k]) for r in rows]
sq100 = lambda v: 100 * float(v) ** 2   # stored as sqrt(rate): back to per-100
save('hit_strikeouts_next.svg', scatter([sq100(r['so.x']) for r in hp], [sq100(r['so.y']) for r in hp], title='Strikeouts repeat',
     xlab='strikeouts per 100 trips, this season', ylab='strikeouts per 100 trips, next season', diagonal=True))
save('hit_avg_next.svg', scatter(x(hp, 'avg.x'), x(hp, 'avg.y'), title='Batting average barely repeats',
     xlab='batting average, this season', ylab='batting average, next season', diagonal=True))
save('hit_construct_next.svg', scatter(x(hp, 'construct.x'), x(hp, 'construct.y'), title='Hitting construct score repeats',
     xlab='construct score, this season', ylab='construct score, next season', diagonal=True))
sp = [r for r in pp if r['role'] == 'SP' and r['era.x'] not in ('', 'NA') and r['era.y'] not in ('', 'NA')]
rp = [r for r in pp if r['role'] == 'RP' and r['era.x'] not in ('', 'NA') and r['era.y'] not in ('', 'NA')]
save('sp_era_next.svg', scatter(x(sp, 'era.x'), x(sp, 'era.y'), title='Starters: ERA barely repeats',
     xlab='ERA, this season', ylab='ERA, next season', diagonal=True))
save('rp_era_next.svg', scatter(x(rp, 'era.x'), x(rp, 'era.y'), title='Relievers: ERA does not repeat',
     xlab='ERA, this season', ylab='ERA, next season', diagonal=True))
save('sp_hbip_next.svg', scatter([100 * float(r['hbip.x']) for r in sp], [100 * float(r['hbip.y']) for r in sp], title='Starters: hits on balls in play',
     xlab='hits per 100 balls in play, this season', ylab='hits per 100 in play, next season', diagonal=True))
save('sp_strikeouts_next.svg', scatter([sq100(r['so.x']) for r in sp], [sq100(r['so.y']) for r in sp], title='Starters: strikeouts repeat',
     xlab='strikeouts per 100 batters, this season', ylab='strikeouts per 100 batters, next', diagonal=True))
