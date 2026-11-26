#!/usr/bin/env python3
"""Every correlation reported, plotted (crisp SVG, house style). fig/*.svg"""
import csv, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from hs_scatter import scatter
INK, CREAM, STEEL, RUST, MUTED, GRID = '#1a1208', '#f5f0e8', '#2c4a6e', '#b83a1e', '#6b5e4a', '#d9cfba'
F = lambda p: os.path.join(HERE, p)
def pairs(fn, a, b, mult=1):
    R = [r for r in csv.DictReader(open(F(fn))) if r[a] not in ('', 'NA') and r[b] not in ('', 'NA')]
    return [float(r[a]) * mult for r in R], [float(r[b]) * mult for r in R], [r['name'] for r in R]
def save(name, svg): open(F(f'fig/{name}.svg'), 'w').write(svg); print('fig', name)
x, y, n = pairs('data/qb_pairs.csv', 'scr', 'scr.n', 100)
save('qb_scrambles_next_season', scatter(x, y, n, title='QB scrambles, one season to the next', xlab='scrambles per 100 dropbacks, this season', ylab='scrambles per 100, next season', diagonal=True))
x, y, n = pairs('data/qb_pairs.csv', 'accuracy', 'accuracy.n')
save('qb_accuracy_next_season', scatter(x, y, n, title='QB accuracy, one season to the next', xlab='accuracy score, this season', ylab='accuracy score, next season', diagonal=True))
x, y, n = pairs('data/qb_pairs.csv', 'chains', 'chains.n')
save('qb_chains_next_season', scatter(x, y, n, title='QB moves the chains, season to season', xlab='chain-moving score, this season', ylab='chain-moving score, next season', diagonal=True))
x, y, n = pairs('data/qb_pairs.csv', 'int', 'int.n', 100)
save('qb_interceptions_next_season', scatter(x, y, n, title='QB interceptions, one season to the next', xlab='interceptions per 100 throws, this season', ylab='per 100 throws, next season', diagonal=True))
x, y, n = pairs('data/rec_pairs.csv', 'sep', 'sep.n')
save('wr_separation_next_season', scatter(x, y, n, title='WR separation, one season to the next', xlab='yards of separation, this season', ylab='yards of separation, next season', diagonal=True))
x, y, n = pairs('data/rec_pairs.csv', 'catch', 'catch.n', 100)
save('wr_catch_next_season', scatter(x, y, n, title='WR catch rate, one season to the next', xlab='catches per 100 targets, this season', ylab='per 100 targets, next season', diagonal=True))
x, y, n = pairs('data/rec_pairs.csv', 'drop', 'drop.n', 100)
save('wr_drops_next_season', scatter(x, y, n, title='WR drops, one season to the next', xlab='drops per 100 targets, this season', ylab='drops per 100 targets, next season', diagonal=True))
x, y, n = pairs('data/rec_pairs.csv', 'construct', 'construct.n')
save('wr_construct_next_season', scatter(x, y, n, title='WR overall score, season to season', xlab='receiver score, this season', ylab='receiver score, next season', diagonal=True))

def dotplot(rows, title, xlab, name, xmin=0, xmax=1, ref=None, ref_label=''):
    """Labeled dot-and-interval chart: one row per measure, 95% interval as a line."""
    W, rowh = 680, 24; top, left, right = 56, 190, 640; H = top + rowh * len(rows) + 64
    sx = lambda v: left + (v - xmin) / (xmax - xmin) * (right - left)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="\'Roboto Mono\',monospace">', f'<rect width="{W}" height="{H}" fill="{CREAM}"/>',
         f'<text x="{left}" y="24" font-size="13" font-weight="600" fill="{INK}">{title}</text>']
    yb = top + rowh * len(rows)
    for k in range(11):
        v = xmin + (xmax - xmin) * k / 10
        o.append(f'<line x1="{sx(v):.1f}" x2="{sx(v):.1f}" y1="{top - 8}" y2="{yb}" stroke="{GRID}" stroke-width="0.7"/><text x="{sx(v):.1f}" y="{yb + 16}" font-size="11" fill="{MUTED}" text-anchor="middle">{v:.1f}</text>')
    if ref is not None:
        o.append(f'<line x1="{sx(ref):.1f}" x2="{sx(ref):.1f}" y1="{top - 8}" y2="{yb}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="4 3"/><text x="{sx(ref) + 4:.1f}" y="{top - 12}" font-size="10.5" fill="{MUTED}">{ref_label}</text>')
    for i, (lab, v, lo, hi, hl) in enumerate(rows):
        y = top + rowh * i + rowh / 2
        col = RUST if hl else STEEL
        o.append(f'<text x="{left - 10}" y="{y + 4:.1f}" font-size="11.5" fill="{INK}" text-anchor="end">{lab}</text>')
        o.append(f'<line x1="{sx(lo):.1f}" x2="{sx(hi):.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="2"/><circle cx="{sx(v):.1f}" cy="{y:.1f}" r="4.2" fill="{col}" stroke="{CREAM}" stroke-width="0.8"/>')
        o.append(f'<text x="{min(sx(hi) + 6, right + 4):.1f}" y="{y + 4:.1f}" font-size="10.5" fill="{MUTED}">{v:.2f}</text>')
    o.append(f'<text x="{(left + right) / 2:.1f}" y="{yb + 40}" font-size="12.5" font-weight="600" fill="{INK}" text-anchor="middle">{xlab}</text>')
    o.append(f'<text transform="translate(18,{(top + yb) / 2:.1f}) rotate(-90)" font-size="12.5" font-weight="600" fill="{INK}" text-anchor="middle">measure</text>')
    o.append('</svg>'); save(name, '\n'.join(o))
NAMES = {'comp': 'completion rate', 'cpoe': 'completion over exp.', 'bad': 'bad-throw rate', 'ttt': 'time to throw', 'scr': 'scramble rate',
         'throwaway': 'throwaway rate', 'td': 'TD rate', 'fd': 'first-down rate', 'sack': 'sack rate', 'int': 'interception rate', 'adot': 'depth of target',
         'aggr': 'tight-window rate', 'yac': 'yards after catch', 'accuracy': 'ACCURACY', 'holds': 'HOLDS THE BALL', 'chains': 'MOVES THE CHAINS',
         'ypa': 'yards per attempt', 'anya': 'ANY/A', 'epa_db': 'EPA per dropback', 'tps': 'targets per snap', 'catch': 'catch rate', 'drop': 'drop rate',
         'yacoe': 'YAC over expected', 'brk': 'broken tackles', 'sep': 'separation', 'cush': 'cushion', 'after': 'AFTER THE CATCH', 'open': 'GETS OPEN',
         'hands': 'HANDS', 'deep': 'DEEP THREAT', 'construct': 'RECEIVER SCORE', 'ypt': 'yards per target', 'yps': 'yards per snap', 'epa_t': 'EPA per target',
         'yds': 'receiving yards', 'tgt': 'targets', 'tds': 'touchdowns', 'db': 'dropbacks'}
CONSTRUCTS = {'accuracy', 'holds', 'chains', 'construct', 'after', 'open', 'hands', 'deep'}
for fn, title, name in (('data/qb_reliability.csv', 'QB: same player, next season (95% intervals)', 'qb_reliability'),
                        ('data/rec_reliability.csv', 'WR: same player, next season (95% intervals)', 'wr_reliability')):
    R = sorted(csv.DictReader(open(F(fn))), key=lambda r: -float(r['r']))
    dotplot([(NAMES.get(r['v'], r['v']), float(r['r']), float(r['lo']), float(r['hi']), r['v'] in CONSTRUCTS) for r in R],
            title, 'correlation with the same player next season (r)', name, xmin=-0.1, xmax=0.9)
for fn, title, name in (('data/qb_auc.csv', 'QB: how well each measure picks AP All-Pros, 2018-25', 'qb_allpro_auc'),
                        ('data/rec_auc.csv', 'WR: how well each measure picks AP All-Pros, 2018-25', 'wr_allpro_auc')):
    R = sorted(csv.DictReader(open(F(fn))), key=lambda r: -float(r['auc']))
    dotplot([(NAMES.get(r['v'], r['v']), float(r['auc']), float(r['lo']), float(r['hi']), r['v'] in CONSTRUCTS) for r in R],
            title, 'AUC (0.5 = coin flip, 1 = picks every All-Pro)', name, xmin=0, xmax=1, ref=0.5, ref_label='coin flip')
