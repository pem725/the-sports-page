#!/usr/bin/env python3
"""Build print-ready vector merch art for The Sports Page.

Every piece of text is converted to OUTLINES (SVG <path>), so a printer needs
no fonts installed and nothing can reflow or substitute. Canvases are sized in
real millimetres so the art drops into a print layout at 1:1.
"""
import math, os
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen

S = os.environ.get("MERCH_FONT_DIR", os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "merch")
os.makedirs(OUT, exist_ok=True)

NAVY  = "#051954"
CREAM = "#f9f2de"
RUST  = "#b83a1e"

# Garment colours -- NOT brand colours. These exist only so the halo can be set
# to the colour actually behind the art. Sampled from the vendor's own swatch and
# product render; confirm against a physical sample before a run.
#
# Why this matters: the halo where the curve crosses the S is a painted stroke in
# the ground colour, not an absence of ink. A screen printer treats it as a
# knockout and the fabric fills it, so the hex is irrelevant. A DTG printer prints
# the file literally -- a CREAM halo on a NATURAL shirt lays down a visibly
# lighter ring. Always build light-garment art with the garment's own hex.
NATURAL = "#e4dccf"   # Gildan Softstyle "Natural" -- dE 3.5 from the site's --aged

_cache = {}
def load(path, wght):
    key = (path, wght)
    if key not in _cache:
        f = TTFont(os.path.join(S, "fonts", path))
        f = instancer.instantiateVariableFont(f, {"wght": wght})
        _cache[key] = f
    return _cache[key]

PF = lambda w=900: load("Playfair-var.ttf", w)
RM = lambda w=600: load("RobotoMono-var.ttf", w)


def glyphs(font, text):
    """Yield (path_d, advance) per character, in font units."""
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            yield None, font["head"].unitsPerEm * 0.3
            continue
        pen = SVGPathPen(gs)
        gs[gname].draw(pen)
        yield pen.getCommands(), hmtx[gname][0]


def text_width(font, text, size, tracking=0.0):
    upem = font["head"].unitsPerEm
    w = sum(a for _, a in glyphs(font, text)) * size / upem
    return w + tracking * size * max(len(text) - 1, 0)


def text_paths(font, text, size, x, y, fill, tracking=0.0, anchor="start"):
    """Return SVG for `text` as outlines, baseline at y."""
    upem = font["head"].unitsPerEm
    k = size / upem
    total = text_width(font, text, size, tracking)
    if anchor == "middle":
        x -= total / 2
    elif anchor == "end":
        x -= total
    out = []
    cx = x
    for d, adv in glyphs(font, text):
        if d:
            out.append(
                f'<path d="{d}" fill="{fill}" '
                f'transform="translate({cx:.3f},{y:.3f}) scale({k:.6f},{-k:.6f})"/>'
            )
        cx += adv * k + tracking * size
    return "\n".join(out), total


def arc_text(font, text, size, cx, cy, r, fill, tracking=0.0, start_deg=None, sweep_up=True):
    """Place text along a circular arc, centred at top (or bottom if not sweep_up)."""
    upem = font["head"].unitsPerEm
    k = size / upem
    advs = [(d, a * k + tracking * size) for d, a in glyphs(font, text)]
    total = sum(a for _, a in advs)
    total_ang = total / r                      # radians subtended
    ang = (start_deg * math.pi / 180) if start_deg is not None else -total_ang / 2
    out = []
    for d, adv in advs:
        mid = ang + (adv / r) / 2
        deg = mid * 180 / math.pi
        if sweep_up:
            tx, ty, rot = cx, cy, deg
            place = f"translate({tx:.3f},{ty:.3f}) rotate({rot:.4f}) translate(0,{-r:.3f})"
        else:
            place = (f"translate({cx:.3f},{cy:.3f}) rotate({-deg:.4f}) "
                     f"translate(0,{r:.3f}) rotate(180)")
        if d:
            out.append(
                f'<path d="{d}" fill="{fill}" transform="{place} '
                f'translate({-adv/2:.3f},0) scale({k:.6f},{-k:.6f})"/>'
            )
        ang += adv / r
    return "\n".join(out)


def svg(w_mm, h_mm, body, bg=None):
    rect = f'<rect width="{w_mm}" height="{h_mm}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{w_mm}mm" height="{h_mm}mm" viewBox="0 0 {w_mm} {h_mm}">\n'
            f'{rect}\n{body}\n</svg>\n')


def write(name, content):
    p = os.path.join(OUT, name)
    open(p, "w", encoding="utf-8").write(content)
    print(f"  {name}  ({len(content)//1024}kb)")


# ---------------------------------------------------------------- the S mark
def s_mark(cx, cy, height, fill, chart=True, knock=CREAM, weight=0.65,
           span=1.35, amp=0.42, ycen=0.38, sigma=0.34):
    """Playfair 'S' over a histogram and a normal curve.

    How this arrived here, because the failures were instructive:

    * Chart in solid ink over the S merged into the letter and read as a blob.
    * Knocking the chart out of the S read as a *damaged* letter. Scanning the
      rendered glyph showed why -- the S's thickest horizontal band is only about
      32% of its width, so there is not enough ink to cut into.
    * A diagonal trend line fought the letterform no matter how thin: the S's
      spine runs upper-left to lower-right, so any sloped line crosses it at
      close to a right angle. The problem was the ANGLE, not the weight.
    * Equal-length bars hung off a curved line produced a deck over evenly
      spaced piers -- a bridge.

    A normal curve solves all of it at once. It is horizontal and symmetric, so
    it sits *beneath* the S instead of cutting across the diagonal, and a
    histogram under a bell is the most recognisable statistics image there is --
    which is the whole point of the newsletter.
    """
    f = PF(900)
    upem = f["head"].unitsPerEm
    size = height / 0.72
    d, adv = next(iter(glyphs(f, "S")))
    k = size / upem
    w = adv * k
    parts = [f'<path d="{d}" fill="{fill}" '
             f'transform="translate({cx - w/2:.3f},{cy + height/2:.3f}) '
             f'scale({k:.6f},{-k:.6f})"/>']
    if not chart:
        return "\n".join(parts), w

    halo, ink = [], []
    W    = w * span                       # curve spans a little wider than the S
    base = cy + ycen * height             # notional axis (not drawn)
    A    = height * amp                   # peak height above it
    sw   = height * 0.075 * weight        # curve stroke
    hw   = max(sw * 0.55, height * 0.016) # halo gap -- the tightest dimension

    def gauss(u):
        """u runs -1..1 across the span; returns the y of the normal curve."""
        return base - A * math.exp(-(u * u) / (2 * sigma * sigma))

    # Curve only. Histogram bars and a drawn axis were both tried and dropped:
    # they crowded the letterform and were the hardest part of the mark to
    # embroider. A bare bell reads as "statistics" on its own.
    N = 72
    pts = [(cx + W * (-1 + 2*i/N) / 2, gauss(-1 + 2*i/N)) for i in range(N + 1)]
    dpath = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    for col, extra, lst in ((knock, hw * 2, halo), (fill, 0, ink)):
        lst.append(f'<path d="{dpath}" stroke="{col}" stroke-width="{sw+extra:.2f}" '
                   f'stroke-linecap="round" stroke-linejoin="round" fill="none"/>')

    return "\n".join(parts + halo + ink), w


# ---------------------------------------------------------------- 1. badge
def badge_body(size_mm=100, chart=True, ring=True, fill=NAVY, knock=CREAM, s_frac=0.70,
               dx=0.0, dy=0.0):
    """The badge artwork itself, so it can be composed into larger lockups."""
    c = size_mm / 2
    r_out = size_mm * 0.47
    body = []
    if ring:
        body.append(f'<circle cx="{c+dx:.3f}" cy="{c+dy:.3f}" r="{r_out:.3f}" fill="none" '
                    f'stroke="{fill}" stroke-width="{size_mm*0.022:.3f}"/>')
    body.append(arc_text(PF(700), "THE SPORTS PAGE", size_mm * 0.088,
                         c + dx, c + dy, r_out - size_mm * 0.085, fill, tracking=0.10))
    mark, _ = s_mark(c + dx, c + dy + size_mm * 0.055, size_mm * s_frac, fill,
                     chart=chart, knock=knock)
    body.append(mark)
    return "\n".join(body)


def badge(size_mm=100, chart=True, ring=True, fill=NAVY, bg=None, s_frac=0.70, ground=None):
    knock = ground or bg or CREAM   # halo must equal the colour BEHIND the art
    return svg(size_mm, size_mm,
               badge_body(size_mm, chart, ring, fill, knock, s_frac), bg)


def badge_with_url(size_mm=190, fill=NAVY, bg=None, ground=None, chart=True):
    """Badge over the bare domain. Front-of-tee lockup.

    No protocol and no www -- "thesportspage.net" is the whole address anyone
    needs to type, and the extra characters only cost legibility on fabric.
    """
    knock = ground or bg or CREAM
    us = size_mm * 0.062
    gap = size_mm * 0.070
    body = [badge_body(size_mm, chart, True, fill, knock)]
    p, _ = text_paths(RM(600), "THESPORTSPAGE.NET", us, size_mm / 2,
                      size_mm + gap + us * 0.78, fill, tracking=0.16, anchor="middle")
    body.append(p)
    return svg(round(size_mm, 2), round(size_mm + gap + us * 1.15, 2), "\n".join(body), bg)


# ------------------------------------------------------- 2. stacked wordmark
def stacked_body(w_mm, fill, knock, tagline=True):
    """Return (svg_body, total_height) for the stacked lockup."""
    pad = w_mm * 0.05
    col_w = w_mm * 0.58
    size = col_w / max(text_width(PF(900), "SPORTS", 1.0), 0.001)
    lines = ["THE", "SPORTS", "PAGE"]
    lh = size * 0.80
    top = pad + size * 0.72
    body = []
    for i, ln in enumerate(lines):
        p, _ = text_paths(PF(900), ln, size, pad + col_w, top + i * lh, fill, anchor="end")
        body.append(p)
    # Big S tucked against the wordmark, as in the masthead artwork
    s_h = lh * 2.60
    s_cx = pad + col_w + w_mm * 0.195
    s_cy = top + lh * 0.62
    mark, _ = s_mark(s_cx, s_cy, s_h, fill, chart=True, knock=knock)
    body.append(mark)
    h = max(top + 2 * lh, s_cy + s_h / 2) + pad * 0.5
    if tagline:
        ts = w_mm * 0.036
        p, _ = text_paths(PF(700), "A STATISTICAL DISPATCH", ts, w_mm / 2,
                          h + ts * 1.0, fill, tracking=0.07, anchor="middle")
        body.append(p)
        h += ts * 1.6
    return "\n".join(body), h


def wordmark_stacked(w_mm=180, fill=NAVY, bg=None, tagline=True, ground=None):
    body, h = stacked_body(w_mm, fill, ground or bg or CREAM, tagline)
    return svg(round(w_mm, 2), round(h + w_mm * 0.02, 2), body, bg)


# ---------------------------------------------------- 3. horizontal wordmark
def wordmark_horizontal(w_mm=180, fill=NAVY, bg=None):
    pad = w_mm * 0.04
    txt = "THE SPORTS PAGE"
    avail = w_mm - pad * 2
    size = avail / text_width(PF(900), txt, 1.0, tracking=0.04)
    body, _ = text_paths(PF(900), txt, size, w_mm / 2, pad + size * 0.72,
                         fill, tracking=0.04, anchor="middle")
    h = pad * 2 + size * 0.78
    return svg(round(w_mm, 2), round(h, 2), body, bg)


# ------------------------------------------------------------------- 4. tees
def tee_masthead(w_mm=280, fill=NAVY, bg=None, ground=None):
    """Stacked lockup, then a rule, then the URL — composed with explicit
    spacing rather than splicing another SVG's string (which collided)."""
    knock = ground or bg or CREAM
    body, h = stacked_body(w_mm, fill, knock, tagline=True)
    parts = [body]
    rule_y = h + w_mm * 0.026
    parts.append(f'<rect x="{w_mm*0.22:.2f}" y="{rule_y:.2f}" '
                 f'width="{w_mm*0.56:.2f}" height="{w_mm*0.0035:.2f}" fill="{fill}"/>')
    us = w_mm * 0.028
    p, _ = text_paths(RM(600), "THESPORTSPAGE.NET", us, w_mm / 2,
                      rule_y + us * 1.75, fill, tracking=0.16, anchor="middle")
    parts.append(p)
    total = rule_y + us * 1.75 + w_mm * 0.030
    return svg(round(w_mm, 2), round(total, 2), "\n".join(parts), bg)


def tee_denominator(w_mm=280, fill=NAVY, accent=RUST, bg=None):
    pad = w_mm * 0.04
    l1, l2 = "ASK FOR THE", "DENOMINATOR"
    s2 = (w_mm - pad * 2) / text_width(PF(900), l2, 1.0)
    s1 = s2 * 0.52
    y1 = pad + s1 * 0.72
    y2 = y1 + s2 * 0.86
    body = []
    p, _ = text_paths(PF(900), l1, s1, w_mm / 2, y1, fill, tracking=0.02, anchor="middle")
    body.append(p)
    p, _ = text_paths(PF(900), l2, s2, w_mm / 2, y2, accent, anchor="middle")
    body.append(p)
    ry = y2 + s2 * 0.30
    body.append(f'<rect x="{w_mm*0.28:.2f}" y="{ry:.2f}" width="{w_mm*0.44:.2f}" '
                f'height="{w_mm*0.0035:.2f}" fill="{fill}"/>')
    sub = "EVERY RATE HIDES ONE"
    ss = w_mm * 0.030
    p, _ = text_paths(RM(600), sub, ss, w_mm / 2, ry + ss * 1.5, fill,
                      tracking=0.16, anchor="middle")
    body.append(p)
    return svg(round(w_mm, 2), round(ry + ss * 2.4 + pad * 0.5, 2), "\n".join(body), bg)


def tee_founding(w_mm=280, fill=NAVY, accent=RUST, bg=None):
    pad = w_mm * 0.04
    num = "67.5"
    ns = (w_mm - pad * 2) * 0.86 / text_width(PF(900), num, 1.0)
    y = pad + ns * 0.72
    body = []
    p, _ = text_paths(PF(900), num, ns, w_mm / 2, y, accent, anchor="middle")
    body.append(p)
    ry = y + ns * 0.22
    body.append(f'<rect x="{w_mm*0.14:.2f}" y="{ry:.2f}" width="{w_mm*0.72:.2f}" '
                f'height="{w_mm*0.004:.2f}" fill="{fill}"/>')
    cs = w_mm * 0.031
    for i, ln in enumerate(["EARNED RUN AVERAGE", "TWO-THIRDS OF AN INNING",
                            "OPENING DAY 2026"]):
        p, _ = text_paths(RM(600), ln, cs, w_mm / 2, ry + cs * (1.6 + i * 1.45),
                          fill, tracking=0.14, anchor="middle")
        body.append(p)
    h = ry + cs * (1.6 + 2 * 1.45) + pad
    return svg(round(w_mm, 2), round(h, 2), "\n".join(body), bg)


def build():
    print("Building merch art ->", OUT)
    # NOTE: the bar-chart-in-the-S detail from the web logo is deliberately omitted.
    # It was built and tested both as solid ink and as a knockout; at chest size and
    # in a single colour it reads as a damaged letter, not a chart. The plain S is
    # the apparel mark. See merch/README.md.
    write("logo-badge.svg",               badge(100, chart=True))
    write("wordmark-stacked.svg",         wordmark_stacked(180))
    write("wordmark-horizontal.svg",      wordmark_horizontal(180))

    write("polo-01-badge.svg",            badge(82, chart=True))
    write("tee-front-badge-url.svg",      badge_with_url(190))
    write("tee-front-badge-url-reversed.svg",
                                          badge_with_url(190, fill=CREAM, bg=None, ground=NAVY))
    write("polo-02-wordmark.svg",         wordmark_horizontal(82))
    write("polo-01-badge-reversed.svg",   badge(82, chart=True, fill=CREAM, bg=None, ground=NAVY))
    write("polo-02-wordmark-reversed.svg", wordmark_horizontal(82, fill=CREAM, bg=None))

    write("tee-01-masthead.svg",          tee_masthead(280))
    write("tee-02-denominator.svg",       tee_denominator(280))
    write("tee-03-sixty-seven-five.svg",  tee_founding(280))
    write("tee-01-masthead-reversed.svg", tee_masthead(280, fill=CREAM, bg=None, ground=NAVY))
    write("tee-02-denominator-reversed.svg", tee_denominator(280, fill=CREAM, accent="#e8703f", bg=None))
    write("tee-03-sixty-seven-five-reversed.svg", tee_founding(280, fill=CREAM, accent="#e8703f", bg=None))

    # -- THE ORDER: Natural tees. These are the two files that go to the printer.
    # Identical to the light-garment art above except the halo is Natural rather
    # than our cream, so a DTG machine cannot print a pale ring onto the shirt.
    # Named for the garment on purpose -- it should be impossible to send the
    # wrong file by picking the shorter name.
    write("tee-front-badge-url-natural.svg", badge_with_url(190, ground=NATURAL))
    write("tee-01-masthead-natural.svg",     tee_masthead(280, ground=NATURAL))
    print("done")


if __name__ == "__main__":
    build()
