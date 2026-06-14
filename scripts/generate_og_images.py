#!/usr/bin/env python3
"""generate_og_images.py — Render per-issue 1200×630 Open Graph cards.

Reads each queued and published issue, extracts the headline + deck, composes
a social-preview card in the broadsheet aesthetic, saves to assets/og/.

Design:
  - Cream background (matches site --cream #f5f0e8)
  - Top stripe (40px) in ink with "THE SPORTS PAGE" in gold Roboto Mono
  - Headline in Playfair Display Black, auto-wrapped to fit
  - Deck in Libre Baskerville Italic below (optional)
  - Bottom-right corner: "thesportspage.net" in gold Roboto Mono
  - Bottom rust accent line for visual seal

Usage:
  python3 scripts/generate_og_images.py             # render all
  python3 scripts/generate_og_images.py 064-*       # render matching files
"""
import re
import sys
from pathlib import Path
from html import unescape

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
OG_DIR = REPO / "assets" / "og"
FONTS = REPO / "assets" / "fonts"

# Card dimensions (standard OG/Twitter Card)
W, H = 1200, 630

# Palette — straight from the site CSS vars
INK = "#1a1208"
CREAM = "#f5f0e8"
GOLD = "#c9962a"
RUST = "#b83a1e"
MUTED = "#6b5e4a"

# Layout constants
PADDING_X = 80
TOP_STRIPE_H = 50
BOTTOM_STRIPE_H = 8


def load_fonts():
    return {
        "headline": ImageFont.truetype(str(FONTS / "PlayfairDisplay-Black.ttf"), 64),
        "headline_small": ImageFont.truetype(str(FONTS / "PlayfairDisplay-Black.ttf"), 54),
        "headline_tight": ImageFont.truetype(str(FONTS / "PlayfairDisplay-Black.ttf"), 46),
        "deck": ImageFont.truetype(str(FONTS / "LibreBaskerville-Italic.ttf"), 26),
        "kicker": ImageFont.truetype(str(FONTS / "RobotoMono-Bold.ttf"), 16),
        "url": ImageFont.truetype(str(FONTS / "RobotoMono-Bold.ttf"), 18),
    }


# Extract headline + deck from an issue file
TAG_STRIP = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")


def clean(html):
    if not html:
        return ""
    return WS.sub(" ", unescape(TAG_STRIP.sub(" ", html))).strip()


def extract(path):
    text = path.read_text()
    m_hed = re.search(r'<h[12] class="hed"[^>]*>(.+?)</h[12]>', text, re.DOTALL)
    m_deck = re.search(r'<p class="deck">(.+?)</p>', text, re.DOTALL)
    return clean(m_hed.group(1)) if m_hed else None, clean(m_deck.group(1)) if m_deck else None


def wrap_text(draw, text, font, max_width):
    """Greedy word-wrap. Returns list of lines."""
    words = text.split()
    lines = []
    cur = []
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


def pick_headline_font(draw, text, fonts, max_width, max_lines):
    """Choose the largest headline font that fits inside (max_width × max_lines)."""
    for size_key in ("headline", "headline_small", "headline_tight"):
        font = fonts[size_key]
        lines = wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
    # Last resort: tight font, truncate to fit
    font = fonts["headline_tight"]
    lines = wrap_text(draw, text, font, max_width)
    return font, lines[:max_lines]


def truncate_deck(draw, text, font, max_width, max_lines):
    lines = wrap_text(draw, text, font, max_width)
    if len(lines) <= max_lines:
        return lines
    # Truncate with ellipsis on the last line
    lines = lines[:max_lines]
    last = lines[-1]
    while True:
        test = last + "…"
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width or " " not in last:
            lines[-1] = test
            return lines
        last = last.rsplit(" ", 1)[0]


def render_card(filename, hed, deck, fonts):
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)

    # Top stripe (ink)
    draw.rectangle([0, 0, W, TOP_STRIPE_H], fill=INK)
    kicker_text = "THE SPORTS PAGE"
    kbox = draw.textbbox((0, 0), kicker_text, font=fonts["kicker"])
    draw.text(
        (PADDING_X, (TOP_STRIPE_H - (kbox[3] - kbox[1])) // 2 - 3),
        kicker_text,
        fill=GOLD,
        font=fonts["kicker"],
    )
    # Issue label on the right
    issue_label = "A Statistical Dispatch"
    ibox = draw.textbbox((0, 0), issue_label, font=fonts["kicker"])
    draw.text(
        (W - PADDING_X - (ibox[2] - ibox[0]), (TOP_STRIPE_H - (ibox[3] - ibox[1])) // 2 - 3),
        issue_label,
        fill="#a09070",
        font=fonts["kicker"],
    )

    # Headline placement
    max_width = W - 2 * PADDING_X
    hed_font, hed_lines = pick_headline_font(draw, hed, fonts, max_width, max_lines=4)
    # Line height = font.size * 1.05
    line_h = int(hed_font.size * 1.05)
    block_h = line_h * len(hed_lines)
    # Compose: top stripe + headline + deck + bottom URL strip
    headline_top = TOP_STRIPE_H + 60

    y = headline_top
    for line in hed_lines:
        draw.text((PADDING_X, y), line, fill=INK, font=hed_font)
        y += line_h

    # Rust accent line below headline
    accent_y = y + 18
    draw.rectangle(
        [PADDING_X, accent_y, PADDING_X + 80, accent_y + 4], fill=RUST
    )

    # Deck (italic, muted)
    if deck:
        deck_top = accent_y + 26
        # How many deck lines fit before bottom URL strip
        url_strip_h = 60
        max_deck_lines = max(1, (H - deck_top - url_strip_h - 20) // int(fonts["deck"].size * 1.5))
        deck_lines = truncate_deck(draw, deck, fonts["deck"], max_width, max_deck_lines)
        deck_line_h = int(fonts["deck"].size * 1.5)
        y = deck_top
        for line in deck_lines:
            draw.text((PADDING_X, y), line, fill=MUTED, font=fonts["deck"])
            y += deck_line_h

    # Bottom: rust accent + URL on the right
    draw.rectangle([0, H - BOTTOM_STRIPE_H, W, H], fill=INK)
    url_text = "thesportspage.net"
    ubox = draw.textbbox((0, 0), url_text, font=fonts["url"])
    draw.text(
        (W - PADDING_X - (ubox[2] - ubox[0]), H - BOTTOM_STRIPE_H - 30),
        url_text,
        fill=GOLD,
        font=fonts["url"],
    )

    return img


def main():
    OG_DIR.mkdir(parents=True, exist_ok=True)
    fonts = load_fonts()

    # Optional glob filter from command line
    glob = sys.argv[1] if len(sys.argv) > 1 else "*.html"

    targets = list((REPO / "queue").glob(glob)) + list((REPO / "published").glob(glob))
    ok = 0
    skipped = []
    for path in sorted(targets):
        hed, deck = extract(path)
        if not hed:
            skipped.append(path.name)
            continue
        img = render_card(path.name, hed, deck, fonts)
        out = OG_DIR / (path.stem + ".png")
        img.save(out, "PNG", optimize=True)
        ok += 1
    print(f"✓ Generated {ok} OG cards in {OG_DIR.relative_to(REPO)}")
    if skipped:
        print(f"⚠ {len(skipped)} skipped (no headline):")
        for n in skipped[:5]:
            print(f"    {n}")
        if len(skipped) > 5:
            print(f"    … and {len(skipped) - 5} more")


if __name__ == "__main__":
    main()
