#!/usr/bin/env python3
"""House-style scatterplot as crisp SVG (vector, never raster), for the constructs research.

    from hs_scatter import scatter
    svg = scatter(x, y, labels=None, title=..., xlab=..., ylab=..., size=None, highlight=set(), diagonal=True)

Cream paper, ink text, steel dots (opaque, small, thin cream edge so overlaps stay legible),
rust for anything highlighted, a least-squares line in steel, the r printed in the title.
No R defaults, no translucency blur, no black frame.
"""
import math, statistics as st
INK, CREAM, STEEL, RUST, MUTED, GRID = '#1a1208', '#f5f0e8', '#2c4a6e', '#b83a1e', '#6b5e4a', '#d9cfba'
def _nice(lo, hi, n=6):
    span = hi - lo; step = 10 ** math.floor(math.log10(span / n)); 
    for m in (1, 2, 2.5, 5, 10):
        if span / (step * m) <= n: step *= m; break
    a = math.floor(lo / step) * step; t = []
    while a <= hi + 1e-9: t.append(round(a, 6)); a += step
    return t
def _esc(s): return str(s).replace('&', '&amp;').replace('<', '&lt;').replace("'", '&#8217;')
def scatter(x, y, labels=None, title='', xlab='', ylab='', size=None, highlight=(), diagonal=False,
            xlim=None, ylim=None, W=680, H=440, label_if=None):
    x0, x1, y0, y1 = 62, W - 22, H - 52, 46
    xl, xh = xlim or (min(x), max(x)); yl, yh = ylim or (min(y), max(y))
    px, py = (xh - xl) * .04, (yh - yl) * .04; xl, xh, yl, yh = xl - px, xh + px, yl - py, yh + py
    sx = lambda v: x0 + (v - xl) / (xh - xl) * (x1 - x0); sy = lambda v: y0 - (v - yl) / (yh - yl) * (y0 - y1)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="\'Roboto Mono\',monospace">',
         f'<rect width="{W}" height="{H}" fill="{CREAM}"/>']
    for t in _nice(xl, xh):
        if xl <= t <= xh: o.append(f'<line x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{y0}" y2="{y1}" stroke="{GRID}" stroke-width="0.7"/><text x="{sx(t):.1f}" y="{y0 + 17}" font-size="11" fill="{MUTED}" text-anchor="middle">{t:g}</text>')
    for t in _nice(yl, yh):
        if yl <= t <= yh: o.append(f'<line x1="{x0}" x2="{x1}" y1="{sy(t):.1f}" y2="{sy(t):.1f}" stroke="{GRID}" stroke-width="0.7"/><text x="{x0 - 7}" y="{sy(t) + 4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">{t:g}</text>')
    if diagonal:
        a, b = max(xl, yl), min(xh, yh)
        o.append(f'<line x1="{sx(a):.1f}" y1="{sy(a):.1f}" x2="{sx(b):.1f}" y2="{sy(b):.1f}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="4 3"/>')
    mx, my = st.mean(x), st.mean(y); sxx = sum((v - mx) ** 2 for v in x)
    bb = sum((u - mx) * (v - my) for u, v in zip(x, y)) / sxx; aa = my - bb * mx
    r = st.correlation(x, y)
    lo, hi = max(min(x), xl), min(max(x), xh)          # keep the trend inside the frame
    o.append(f'<line x1="{sx(lo):.1f}" y1="{sy(aa + bb * lo):.1f}" x2="{sx(hi):.1f}" y2="{sy(aa + bb * hi):.1f}" stroke="{STEEL}" stroke-width="2.2"/>')
    hl = set(highlight)
    order = sorted(range(len(x)), key=lambda i: (labels[i] in hl) if labels else 0)
    for i in order:
        rad = 3.2 if size is None else max(2.4, min(8, math.sqrt(size[i]) / 5.5))
        col = RUST if labels and labels[i] in hl else STEEL
        o.append(f'<circle cx="{sx(x[i]):.1f}" cy="{sy(y[i]):.1f}" r="{rad:.1f}" fill="{col}" stroke="{CREAM}" stroke-width="0.8"/>')
    if labels and label_if:
        for i in range(len(x)):
            if not label_if(i): continue
            wide = len(labels[i]) * 6.6
            right = sx(x[i]) + 8 + wide <= x1               # flip to the left if it would run off the edge
            tx, an = (sx(x[i]) + 8, 'start') if right else (sx(x[i]) - 8, 'end')
            o.append(f'<text x="{tx:.1f}" y="{sy(y[i]) - 6:.1f}" font-size="10.5" font-weight="600" fill="{RUST if labels[i] in hl else INK}" text-anchor="{an}">{_esc(labels[i])}</text>')
    o.append(f'<text x="{x0}" y="22" font-size="13" font-weight="600" fill="{INK}">{_esc(title)}  <tspan fill="{STEEL}">r = {r:.2f}, n = {len(x)}</tspan></text>')
    o.append(f'<text x="{x0}" y="38" font-size="11" fill="{MUTED}">{_esc(ylab)}</text>')
    o.append(f'<text x="{(x0 + x1) / 2}" y="{H - 14}" font-size="11" fill="{MUTED}" text-anchor="middle">{_esc(xlab)}</text></svg>')
    return '\n'.join(o)
