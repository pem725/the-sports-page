#!/usr/bin/env python3
"""Signature figure for What Repeats: horizontal dot chart of repeat rates (same player, next season)
with 95% intervals. Steel = a single stat; rust = a composite outcome stat (AVG, OBP, OPS, ERA).
Writes series/fig_part1_hitters.svg and series/fig_part3_pitchers.svg (inline-ready: class="chart")."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); R = json.load(open(os.path.join(HERE, 'repeat_rates.json')))
INK, STEEL, RUST, MUTED, GRID = '#1a1208', '#2c4a6e', '#b83a1e', '#6b5e4a', '#d9cfba'
def chart(blocks, aria, fn, title):
    W = 680; x0, x1 = 232, 640; step = 22
    nh = sum(1 for b in blocks if b[0]); rows = sum(len(b[1]) for b in blocks) + nh
    top = 52; H = top + rows * step + 16 * nh + 96
    sx = lambda v: x0 + max(0, v) * (x1 - x0)
    o = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{aria}" style="max-width:680px;margin:0 auto;display:block" font-family="\'Roboto Mono\',monospace">',
         f'<text x="{x0}" y="22" font-size="13" font-weight="600" fill="{INK}">{title}</text>']
    yend = top + rows * step + 16 * nh - 10
    for t in [0, .2, .4, .6, .8, 1]:
        o.append(f'<line x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{top - 10}" y2="{yend}" stroke="{GRID}" stroke-width="0.8"/>'
                 f'<text x="{sx(t):.1f}" y="{yend + 16}" font-size="11" fill="{MUTED}" text-anchor="middle">{t:g}</text>')
    y = top
    for head, items in blocks:
        if head:
            o.append(f'<text x="{x0 - 12}" y="{y + 4}" font-size="12" font-weight="600" fill="{STEEL}" text-anchor="end">{head}</text>'); y += step
        for label, d, comp in items:
            col = RUST if comp else STEEL
            o.append(f'<text x="{x0 - 12}" y="{y + 4}" font-size="11.5" fill="{INK}" text-anchor="end">{label}</text>')
            o.append(f'<line x1="{sx(d["lo"]):.1f}" x2="{sx(d["hi"]):.1f}" y1="{y}" y2="{y}" stroke="{INK}" stroke-width="1.5"/>')
            o.append(f'<circle cx="{sx(d["r"]):.1f}" cy="{y}" r="4.6" fill="{col}" stroke="#f5f0e8" stroke-width="0.8"/>')
            lab = f'{d["r"]:.2f}'.replace('0.', '.').replace('-.', '&#8722;.')
            o.append(f'<text x="{sx(d["hi"]) + 7:.1f}" y="{y + 4}" font-size="10.5" fill="{MUTED}">{lab}</text>'); y += step
        y += 16 if head else 0
    cy = (top + yend) / 2
    o.append(f'<text x="16" y="{cy:.1f}" font-size="12.5" font-weight="600" fill="{INK}" text-anchor="middle" transform="rotate(-90 16 {cy:.1f})">the stat</text>')
    o.append(f'<text x="{(x0 + x1) / 2}" y="{yend + 38}" font-size="12.5" font-weight="600" fill="{INK}" text-anchor="middle">how much of it repeats the next season (0 = none, 1 = all)</text>')
    ky = yend + 62
    o.append(f'<circle cx="{x0 - 150}" cy="{ky - 4}" r="4.6" fill="{STEEL}"/><text x="{x0 - 140}" y="{ky}" font-size="10.5" fill="{INK}">one thing the player does</text>')
    o.append(f'<circle cx="{x0 + 80}" cy="{ky - 4}" r="4.6" fill="{RUST}"/><text x="{x0 + 90}" y="{ky}" font-size="10.5" fill="{INK}">a mix of many things</text>')
    o.append(f'<line x1="{x0 + 262}" x2="{x0 + 284}" y1="{ky - 4}" y2="{ky - 4}" stroke="{INK}" stroke-width="1.5"/><text x="{x0 + 290}" y="{ky}" font-size="10.5" fill="{INK}">95% interval</text>')
    o.append('</svg>'); open(os.path.join(HERE, fn), 'w').write('\n'.join(o))
h = R['hitters']
hit = [('sprint speed', h['sprint'], 0), ('swings and misses', h['whiff'], 0), ('chasing bad pitches', h['chase'], 0),
       ('strikeouts', h['so'], 0), ('exit velocity', h['ev'], 0), ('walks', h['ubb'], 0), ('home runs', h['hr'], 0),
       ('singles', h['single'], 0), ('doubles', h['double'], 0), ('on-base percentage', h['obp'], 1), ('OPS', h['ops'], 1),
       ('batting average', h['avg'], 1)]
aria = 'Dot chart of how much of each hitting stat repeats the next season, 2015 to 2025, with 95 percent intervals. ' + '; '.join(f'{a}: {d["r"]:.2f}' for a, d, c in hit) + '.'
chart([(None, hit)], aria, 'fig_part1_hitters.svg', 'Hitters, 300+ trips to the plate, 2015–25')
def pit(g):
    p = R[g]
    return [('fastball velocity', p['velo'], 0), ('ground balls', p['gb'], 0), ('swings and misses', p['whiff'], 0),
            ('strikeouts', p['so'], 0), ('walks', p['ubb'], 0), ('exit velocity allowed', p['ev'], 0),
            ('home runs allowed', p['hr'], 0), ('hits on balls in play', p['hbip'], 0), ('ERA', p['era'], 1)]
aria = ('Dot chart of how much of each pitching stat repeats the next season, starters and relievers, 2015 to 2025, with 95 percent intervals. Starters: '
        + '; '.join(f'{a}: {d["r"]:.2f}' for a, d, c in pit('SP')) + '. Relievers: ' + '; '.join(f'{a}: {d["r"]:.2f}' for a, d, c in pit('RP')) + '.')
chart([('Starters', pit('SP')), ('Relievers', pit('RP'))], aria, 'fig_part3_pitchers.svg', 'Pitchers, 2015–25')
print('ok')
