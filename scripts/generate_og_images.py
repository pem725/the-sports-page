#!/usr/bin/env python3
"""generate_og_images.py — Render per-issue 1200×630 Open Graph cards.

Each card lifts a striking visual from the actual article (not a repeat
of the headline) and pairs it with a tight branding strip.

Hero priority:
  1. Inline chart SVG (best for analytical pieces)
  2. Stat-row (the 3 big-number grid most issues have)
  3. Pull quote (the styled article quote)
  4. Deck (fallback — narrative italic)

Branding:
  - Top: "THE SPORTS PAGE · A STATISTICAL DISPATCH"
  - Bottom: rust accent + "thesportspage.net"

Usage:
  python3 scripts/generate_og_images.py             # render all
  python3 scripts/generate_og_images.py 064-*       # render matching glob
"""
import io
import re
import sys
from pathlib import Path
from html import unescape

from PIL import Image, ImageDraw, ImageFont
import cairosvg

REPO = Path(__file__).resolve().parent.parent
OG_DIR = REPO / "assets" / "og"
FONTS = REPO / "assets" / "fonts"

W, H = 1200, 630

INK = "#1a1208"
CREAM = "#f5f0e8"
CARD = "#ede5d2"
AGED = "#e0d8c5"
GOLD = "#c9962a"
RUST = "#b83a1e"
STEEL = "#2c4a6e"
GREEN = "#2a6e3f"
MUTED = "#6b5e4a"
DIV = "#c8b99a"

TOP_STRIPE_H = 56
BOTTOM_STRIPE_H = 56
PADDING_X = 80


def fonts():
    return {
        "kicker": ImageFont.truetype(str(FONTS / "RobotoMono-Bold.ttf"), 18),
        "url":    ImageFont.truetype(str(FONTS / "RobotoMono-Bold.ttf"), 20),
        "value_xl": ImageFont.truetype(str(FONTS / "PlayfairDisplay-Black.ttf"), 120),
        "value":    ImageFont.truetype(str(FONTS / "PlayfairDisplay-Black.ttf"), 90),
        "label":    ImageFont.truetype(str(FONTS / "RobotoMono-Bold.ttf"), 13),
        "pull_xl":  ImageFont.truetype(str(FONTS / "LibreBaskerville-Italic.ttf"), 44),
        "pull_l":   ImageFont.truetype(str(FONTS / "LibreBaskerville-Italic.ttf"), 36),
        "pull_m":   ImageFont.truetype(str(FONTS / "LibreBaskerville-Italic.ttf"), 30),
        "deck":     ImageFont.truetype(str(FONTS / "LibreBaskerville-Italic.ttf"), 32),
    }


TAG_STRIP = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def clean(html):
    if not html:
        return ""
    return WS.sub(" ", unescape(TAG_STRIP.sub(" ", html))).strip()


def extract_chart_svg(text):
    """Return the first inline <svg class='chart'>...</svg> block, or None.
    Convert HTML entities to Unicode characters so cairosvg's XML parser
    doesn't choke on &mdash; &ndash; &middot; etc."""
    m = re.search(r'<svg class="chart"[^>]*>.*?</svg>', text, re.DOTALL)
    if not m:
        return None
    svg = m.group(0)
    # Unescape named HTML entities (&mdash; etc.) but PRESERVE the XML-required
    # entities (&amp; &lt; &gt; &quot; &apos;).
    def replace_entity(match):
        entity = match.group(0)
        if entity in ("&amp;", "&lt;", "&gt;", "&quot;", "&apos;"):
            return entity
        return unescape(entity)
    svg = re.sub(r"&[a-zA-Z]+;|&#\d+;|&#x[\da-fA-F]+;", replace_entity, svg)
    return svg


def extract_stat_row(text):
    """Find the stat-row block by extracting its <div class='sc'> children
    individually. Avoids the nested-div trap of regex-matching the wrapper's
    closing tag."""
    # First isolate the stat-row region by anchoring after its opening tag
    # and before the next major structural element.
    start = text.find('<div class="stat-row">')
    if start < 0:
        return None
    # End at the next <h3, <p (non-byline), or <div class="paper"/... that's not "sc"
    # Simpler: stop at first occurrence of </div> followed by <h, <p, or another major block
    region = text[start:start + 5000]  # generous slice — stat-rows are small
    cards = re.findall(
        r'<div class="sc">\s*<div class="v[^"]*">(.+?)</div>\s*<div class="l">(.+?)</div>\s*</div>',
        region, re.DOTALL,
    )
    return [(clean(v), clean(l)) for v, l in cards] if cards else None


def extract_pull(text):
    """Return the first pull quote text."""
    m = re.search(r'<div class="pull">\s*<p>(.+?)</p>', text, re.DOTALL)
    return clean(m.group(1)) if m else None


def extract_deck(text):
    m = re.search(r'<p class="deck">(.+?)</p>', text, re.DOTALL)
    return clean(m.group(1)) if m else None


def extract_hed(text):
    m = re.search(r'<h[12] class="hed"[^>]*>(.+?)</h[12]>', text, re.DOTALL)
    return clean(m.group(1)) if m else None


def wrap(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
                cur = [w]
            else:
                lines.append(w)
                cur = []
    if cur:
        lines.append(" ".join(cur))
    return lines


def pick_pull_font(draw, text, fs, max_width, max_lines):
    for key in ("pull_xl", "pull_l", "pull_m"):
        lines = wrap(draw, text, fs[key], max_width)
        if len(lines) <= max_lines:
            return fs[key], lines
    # Truncate to fit
    font = fs["pull_m"]
    lines = wrap(draw, text, font, max_width)[:max_lines]
    if lines:
        lines[-1] = lines[-1].rstrip(".,;: ") + "…"
    return font, lines


# ---------- branding strips (top + bottom) ----------
def draw_branding(img, draw, fs, accent_color=GOLD):
    # Top strip
    draw.rectangle([0, 0, W, TOP_STRIPE_H], fill=INK)
    kicker = "THE SPORTS PAGE"
    sub = "A STATISTICAL DISPATCH"
    sep = "·"
    full = f"{kicker}   {sep}   {sub}"
    bbox = draw.textbbox((0, 0), full, font=fs["kicker"])
    draw.text(
        ((W - (bbox[2] - bbox[0])) // 2, (TOP_STRIPE_H - (bbox[3] - bbox[1])) // 2 - 4),
        full, fill=GOLD, font=fs["kicker"],
    )

    # Bottom strip — rust accent line then ink with URL
    draw.rectangle([0, H - BOTTOM_STRIPE_H, W, H - BOTTOM_STRIPE_H + 5], fill=RUST)
    draw.rectangle([0, H - BOTTOM_STRIPE_H + 5, W, H], fill=INK)
    url = "thesportspage.net"
    ubox = draw.textbbox((0, 0), url, font=fs["url"])
    draw.text(
        ((W - (ubox[2] - ubox[0])) // 2,
         H - BOTTOM_STRIPE_H + 5 + ((BOTTOM_STRIPE_H - 5) - (ubox[3] - ubox[1])) // 2 - 4),
        url, fill=GOLD, font=fs["url"],
    )


# ---------- hero renderers ----------
def render_chart(img, draw, fs, svg_text):
    """Rasterize the inline SVG, place centered in the hero zone."""
    hero_top = TOP_STRIPE_H + 20
    hero_bottom = H - BOTTOM_STRIPE_H - 20
    hero_w = W - 80
    hero_h = hero_bottom - hero_top

    # Render the SVG at a generous resolution so it stays crisp.
    png_bytes = cairosvg.svg2png(
        bytestring=svg_text.encode("utf-8"),
        output_width=hero_w * 2,
        background_color="transparent",
    )
    chart = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    # Scale to fit
    scale = min(hero_w / chart.width, hero_h / chart.height)
    new_w = int(chart.width * scale)
    new_h = int(chart.height * scale)
    chart = chart.resize((new_w, new_h), Image.LANCZOS)
    paste_x = (W - new_w) // 2
    paste_y = hero_top + (hero_h - new_h) // 2
    img.paste(chart, (paste_x, paste_y), chart)


def render_stat_row(img, draw, fs, cards):
    """Render the 3-up stat grid in the hero zone, matching the issue's own design."""
    hero_top = TOP_STRIPE_H + 60
    hero_bottom = H - BOTTOM_STRIPE_H - 60
    hero_h = hero_bottom - hero_top

    n = len(cards[:3])
    if n == 0:
        return False
    cards = cards[:n]
    pad = 24
    avail_w = W - 2 * PADDING_X - (n - 1) * pad
    cell_w = avail_w // n

    # Pick value font size: if any value is wide, downsize
    value_font = fs["value_xl"]
    for v, _ in cards:
        bbox = draw.textbbox((0, 0), v, font=value_font)
        if bbox[2] - bbox[0] > cell_w - 30:
            value_font = fs["value"]
            break

    for i, (v, label) in enumerate(cards):
        x0 = PADDING_X + i * (cell_w + pad)
        x1 = x0 + cell_w
        cy = hero_top + hero_h // 2

        # Card background
        draw.rectangle([x0, hero_top, x1, hero_bottom], fill=CARD)

        # Value text — centered
        vbox = draw.textbbox((0, 0), v, font=value_font)
        vw = vbox[2] - vbox[0]
        vh = vbox[3] - vbox[1]
        vx = x0 + (cell_w - vw) // 2
        vy = cy - vh // 2 - 30
        # Color heuristic: gold for now (matches site .v default)
        draw.text((vx, vy), v, fill=INK, font=value_font)

        # Label below
        # Wrap label to fit
        label_font = fs["label"]
        label_lines = wrap(draw, label.upper(), label_font, cell_w - 30)
        lbox = draw.textbbox((0, 0), label_lines[0], font=label_font)
        lh = lbox[3] - lbox[1]
        ly = vy + vh + 24
        for ln in label_lines[:2]:
            lnbox = draw.textbbox((0, 0), ln, font=label_font)
            lx = x0 + (cell_w - (lnbox[2] - lnbox[0])) // 2
            draw.text((lx, ly), ln, fill=MUTED, font=label_font)
            ly += lh + 6

    return True


def render_pull(img, draw, fs, text):
    """Render a centered pull quote with quotation marks."""
    hero_top = TOP_STRIPE_H + 50
    hero_bottom = H - BOTTOM_STRIPE_H - 50
    hero_h = hero_bottom - hero_top
    max_width = W - 2 * PADDING_X - 80

    quote_text = f'"{text}"' if not text.startswith(("“", '"')) else text
    font, lines = pick_pull_font(draw, quote_text, fs, max_width, max_lines=5)
    line_h = int(font.size * 1.35)
    block_h = line_h * len(lines)
    y = hero_top + (hero_h - block_h) // 2

    # Tasteful side accent bars (gold)
    bar_top = y + 10
    bar_bottom = y + block_h - 10
    draw.rectangle([PADDING_X - 10, bar_top, PADDING_X - 4, bar_bottom], fill=RUST)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lx = (W - (bbox[2] - bbox[0])) // 2
        draw.text((lx, y), line, fill=STEEL, font=font)
        y += line_h


def render_deck_hero(img, draw, fs, text):
    """Fallback when nothing else available: render the deck centered."""
    hero_top = TOP_STRIPE_H + 60
    hero_bottom = H - BOTTOM_STRIPE_H - 60
    hero_h = hero_bottom - hero_top
    max_width = W - 2 * PADDING_X

    font, lines = pick_pull_font(draw, text, fs, max_width, max_lines=5)
    line_h = int(font.size * 1.4)
    block_h = line_h * len(lines)
    y = hero_top + (hero_h - block_h) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lx = (W - (bbox[2] - bbox[0])) // 2
        draw.text((lx, y), line, fill=INK, font=font)
        y += line_h


# ---------- main composition ----------
def render_card(path, fs):
    text = path.read_text()
    img = Image.new("RGB", (W, H), AGED)
    # The paper-ish background area (between the strips)
    img_inset = Image.new("RGB", (W, H - TOP_STRIPE_H - BOTTOM_STRIPE_H), CREAM)
    img.paste(img_inset, (0, TOP_STRIPE_H))
    draw = ImageDraw.Draw(img)

    chart = extract_chart_svg(text)
    if chart:
        try:
            render_chart(img, draw, fs, chart)
            hero_kind = "chart"
        except Exception as e:
            print(f"  ⚠ chart render failed for {path.name}: {e}; falling back", file=sys.stderr)
            chart = None
    if not chart:
        cards = extract_stat_row(text)
        if cards and len(cards) >= 2:
            ok = render_stat_row(img, draw, fs, cards)
            if ok:
                hero_kind = "stat-row"
            else:
                cards = None
        else:
            cards = None
        if not cards:
            pull = extract_pull(text)
            if pull and len(pull) >= 40:
                render_pull(img, draw, fs, pull)
                hero_kind = "pull"
            else:
                deck = extract_deck(text)
                if deck:
                    render_deck_hero(img, draw, fs, deck)
                    hero_kind = "deck"
                else:
                    # Truly degenerate — render the headline
                    hed = extract_hed(text) or "The Sports Page"
                    render_deck_hero(img, draw, fs, hed)
                    hero_kind = "headline"

    # Redraw branding so it sits on top of any overflow
    draw_branding(img, draw, fs)
    return img, hero_kind


def main():
    OG_DIR.mkdir(parents=True, exist_ok=True)
    fs = fonts()
    glob = sys.argv[1] if len(sys.argv) > 1 else "*.html"

    targets = list((REPO / "queue").glob(glob)) + list((REPO / "published").glob(glob))
    counts = {"chart": 0, "stat-row": 0, "pull": 0, "deck": 0, "headline": 0}
    ok = 0
    skipped = []
    for path in sorted(targets):
        try:
            img, kind = render_card(path, fs)
            out = OG_DIR / (path.stem + ".png")
            img.save(out, "PNG", optimize=True)
            counts[kind] += 1
            ok += 1
        except Exception as e:
            skipped.append((path.name, str(e)))

    print(f"✓ Rendered {ok} cards")
    print(f"  by hero element: {counts}")
    if skipped:
        print(f"⚠ {len(skipped)} skipped:")
        for n, m in skipped[:5]:
            print(f"    {n}: {m}")


if __name__ == "__main__":
    main()
