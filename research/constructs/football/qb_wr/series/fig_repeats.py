#!/usr/bin/env python3
"""What Repeats: the signature dot chart (repeat rate, same player next season, 95% Fisher-z interval).
Steel = single stat; rust = composite outcome stat. Writes an inline-ready <svg class="chart">."""
import math
INK, CREAM, STEEL, RUST, MUTED, GRID = '#1a1208', '#f5f0e8', '#2c4a6e', '#b83a1e', '#6b5e4a', '#d9cfba'
def ci(r, n): z = math.atanh(r); s = 1 / math.sqrt(n - 3); return math.tanh(z - 1.96 * s), math.tanh(z + 1.96 * s)
def chart(rows, n, title, aria, W=680):
    step = 26; top = 58; Hh = top + step * len(rows) + 96
    x0, x1 = 228, 640; sx = lambda v: x0 + v * (x1 - x0)
    o = [f'<svg class="chart" viewBox="0 0 {W} {Hh}" role="img" aria-label="{aria}" style="max-width:680px;margin:0 auto" font-family="\'Roboto Mono\',monospace">',
         f'<rect width="{W}" height="{Hh}" fill="{CREAM}"/>',
         f'<text x="16" y="26" font-size="13" font-weight="600" fill="{INK}">{title}</text>']
    yb = top + step * len(rows)
    for t in (0, .2, .4, .6, .8, 1):
        o.append(f'<line x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{top - 14}" y2="{yb - 8}" stroke="{GRID}" stroke-width="0.7"/>'
                 f'<text x="{sx(t):.1f}" y="{yb + 10}" font-size="11" fill="{MUTED}" text-anchor="middle">{t:g}</text>')
    y = top
    for label, r, comp in rows:
        lo, hi = ci(r, n); col = RUST if comp else STEEL
        o.append(f'<text x="{x0 - 12}" y="{y + 4}" font-size="11.5" fill="{INK}" text-anchor="end">{label}</text>')
        o.append(f'<line x1="{sx(lo):.1f}" x2="{sx(hi):.1f}" y1="{y}" y2="{y}" stroke="{INK}" stroke-width="1.4"/>')
        o.append(f'<circle cx="{sx(r):.1f}" cy="{y}" r="5" fill="{col}" stroke="{CREAM}" stroke-width="0.8"/>')
        o.append(f'<text x="{sx(hi) + 7:.1f}" y="{y + 4}" font-size="10.5" fill="{MUTED}">{r:.2f}</text>')
        y += step
    o.append(f'<text x="{(x0 + x1) / 2:.0f}" y="{yb + 34}" font-size="12.5" font-weight="600" fill="{INK}" text-anchor="middle">repeat rate: same player, next season (1 = repeats perfectly)</text>')
    o.append(f'<text x="18" y="{(top + yb) / 2:.0f}" font-size="12.5" font-weight="600" fill="{INK}" text-anchor="middle" transform="rotate(-90 18 {(top + yb) / 2:.0f})">stat</text>')
    ky = yb + 62
    o.append(f'<circle cx="22" cy="{ky - 4}" r="5" fill="{STEEL}"/><text x="32" y="{ky}" font-size="10.5" fill="{INK}">single stat</text>')
    o.append(f'<circle cx="150" cy="{ky - 4}" r="5" fill="{RUST}"/><text x="160" y="{ky}" font-size="10.5" fill="{INK}">blend of other stats</text>')
    o.append(f'<line x1="330" x2="352" y1="{ky - 4}" y2="{ky - 4}" stroke="{INK}" stroke-width="1.4"/><text x="358" y="{ky}" font-size="10.5" fill="{INK}">95% interval · {n} pairs of seasons</text>')
    o.append('</svg>')
    return '\n'.join(o)
if __name__ == '__main__':
    import os
    H = os.path.dirname(os.path.abspath(__file__))
    qb = [('scrambles', .80, 0), ('time to throw', .64, 0), ('throwaways', .51, 0), ('bad throws', .48, 0), ('first downs', .46, 0),
          ('points added per dropback', .46, 1), ('sacks', .45, 0), ('completions over expected', .43, 0), ('adjusted yards per pass', .41, 1), ('touchdown passes', .38, 0),
          ('interceptions', .18, 0)]
    open(os.path.join(H, 'fig_qb_repeats.svg'), 'w').write(chart(qb, 187, 'What repeats for a quarterback?',
        'Repeat rates for quarterback stats, same quarterback in consecutive seasons, 2018 to 2025, 187 pairs, with 95 percent intervals. Scrambles 0.80, time to throw 0.64, throwaways 0.51, bad throws 0.48, first downs 0.46, points added per dropback 0.46, sacks 0.45, completions over expected 0.43, adjusted yards per pass 0.41, touchdown passes 0.38, interceptions 0.18.'))
    wr = [('depth of target', .67, 0), ('targets per snap', .62, 0), ('separation', .60, 0), ('yards per snap', .52, 1), ('cushion', .47, 0),
          ('catches per target', .45, 0), ('yards after catch', .45, 0), ('first downs', .30, 0), ('yards per target', .26, 1),
          ('touchdown catches', .23, 0), ('drops', .13, 0)]
    open(os.path.join(H, 'fig_wr_repeats.svg'), 'w').write(chart(wr, 401, 'What repeats for a receiver?',
        'Repeat rates for wide receiver stats, same receiver in consecutive seasons, 2018 to 2025, 401 pairs, with 95 percent intervals. Depth of target 0.67, targets per snap 0.62, separation 0.60, yards per snap 0.52, cushion 0.47, catches per target 0.45, yards after catch 0.45, first downs 0.30, yards per target 0.26, touchdown catches 0.23, drops 0.13.'))
    print('ok')
