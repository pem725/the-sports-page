#!/usr/bin/env python3
"""generate_figures.py — Rasterize each issue's inline chart SVG to a PNG.

WHY THIS EXISTS
---------------
Issue figures are authored as inline <svg> for the website, where they
render crisply. But email clients (Gmail and Outlook especially) STRIP
inline SVG entirely, so the figure silently vanishes from the emailed
edition. generate_rss.py swaps each chart <svg> for an <img> pointing at
the PNG this script produces, so the figure survives in email.

The website HTML is never touched — it keeps the vector SVG. Only the
email/feed body (built by generate_rss.py) uses the PNG.

HOW IT WORKS
------------
Rasterization is done with headless Google Chrome, which is available both
on dev machines and on GitHub Actions' ubuntu-latest runners (Chrome is
preinstalled), so this needs NO extra Python or system dependencies — unlike
cairosvg, which is not installed in CI.

Only true chart figures are rendered, never the social-share button icons:
chart figures use a large viewBox (width >= 200); share icons are 24x24.
generate_rss.py applies the IDENTICAL filter so fig-numbering lines up.

OUTPUT
------
assets/figures/<slug>-fig<N>.png   (N is 1-based, in document order)
Rendered at 2x device scale on the broadsheet cream background.

USAGE
-----
  python3 scripts/generate_figures.py                 # all published issues
  python3 scripts/generate_figures.py 069-*           # matching glob (published)
  python3 scripts/generate_figures.py queue/088-*.html  # explicit path(s)
"""
import glob
import os
import re
import subprocess
import sys
import tempfile
from html.entities import html5

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLISHED = os.path.join(REPO, "published")
FIG_DIR = os.path.join(REPO, "assets", "figures")

CREAM = "#f5f0e8"          # broadsheet paper background (matches .chart bg)
SCALE = 2                   # device scale factor -> crisp on retina/email zoom
MIN_VIEWBOX_W = 200         # below this is a share icon (24x24), not a figure

# Shared with generate_rss.py: an <svg>...</svg> element, non-greedy.
SVG_RE = re.compile(r"<svg\b[^>]*>.*?</svg>", re.DOTALL | re.IGNORECASE)
VIEWBOX_RE = re.compile(r'viewBox\s*=\s*"[\d.+-]+\s+[\d.+-]+\s+([\d.]+)\s+([\d.]+)"',
                        re.IGNORECASE)


def find_chrome():
    for b in ("google-chrome", "google-chrome-stable", "chromium",
              "chromium-browser"):
        path = _which(b)
        if path:
            return path
    return None


def _which(name):
    for d in os.environ.get("PATH", "").split(os.pathsep):
        p = os.path.join(d, name)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def chart_svgs(html):
    """Yield (index, svg_text, width, height) for each chart figure SVG.

    Filters out social-share icons by viewBox width. Index is 1-based in
    document order, matching generate_rss.py's <img> numbering.
    """
    n = 0
    for m in SVG_RE.finditer(html):
        svg = m.group(0)
        vb = VIEWBOX_RE.search(svg)
        if not vb:
            continue
        w, h = float(vb.group(1)), float(vb.group(2))
        if w < MIN_VIEWBOX_W:
            continue  # share icon, not a figure
        n += 1
        yield n, svg, w, h


def xml_safe_entities(svg):
    """Convert HTML named entities to Unicode so the SVG parses as strict XML.

    A standalone .svg is parsed as XML, which defines only five entities
    (amp/lt/gt/quot/apos). Typographic entities the figures use -- &rsquo;,
    &mdash;, &middot;, &ldquo;, etc. -- are undefined in XML and abort the
    render. Replace each named entity with its actual character; leave the
    five XML built-ins alone so markup stays valid.
    """
    def repl(m):
        name = m.group(1)
        if name in ("amp", "lt", "gt", "quot", "apos"):
            return m.group(0)
        ch = html5.get(name + ";") or html5.get(name)
        return ch if ch is not None else m.group(0)
    return re.sub(r"&([a-zA-Z][a-zA-Z0-9]+);", repl, svg)


def standalone_svg(svg, w, h):
    """Make a self-contained SVG: explicit pixel size + cream background."""
    svg = xml_safe_entities(svg)
    # Force width/height so Chrome renders at the intended pixel size.
    svg = re.sub(r'\swidth\s*=\s*"[^"]*"', "", svg, count=1)
    svg = re.sub(r'\sheight\s*=\s*"[^"]*"', "", svg, count=1)
    svg = re.sub(r"<svg\b",
                 f'<svg width="{int(w)}" height="{int(h)}"', svg, count=1)
    # Inject a full-bleed cream rectangle as the first child so the figure
    # sits on the broadsheet paper colour rather than transparent/white.
    bg = f'<rect x="0" y="0" width="{w}" height="{h}" fill="{CREAM}"/>'
    svg = re.sub(r"(<svg\b[^>]*>)", r"\1" + bg, svg, count=1)
    return svg


def rasterize(chrome, svg, w, h, out_png):
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False,
                                     encoding="utf-8") as tf:
        tf.write(svg)
        tmp = tf.name
    try:
        with tempfile.TemporaryDirectory() as profile:
            subprocess.run(
                [chrome, "--headless", "--disable-gpu", "--no-sandbox",
                 f"--force-device-scale-factor={SCALE}",
                 f"--user-data-dir={profile}",
                 f"--window-size={int(w)},{int(h)}",
                 f"--screenshot={out_png}", tmp],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=60, check=False,
            )
        return os.path.isfile(out_png) and os.path.getsize(out_png) > 0
    finally:
        os.unlink(tmp)


def resolve_targets(args):
    if not args:
        return sorted(glob.glob(os.path.join(PUBLISHED, "*.html")))
    targets = []
    for a in args:
        if os.path.sep in a or a.endswith(".html"):
            targets.extend(glob.glob(a if os.path.isabs(a)
                                     else os.path.join(REPO, a)))
        else:
            targets.extend(glob.glob(os.path.join(PUBLISHED, a)))
    return sorted(set(targets))


def main():
    chrome = find_chrome()
    if not chrome:
        print("generate_figures: no Chrome/Chromium found; skipping "
              "(figures will fall back to a 'view online' link in email).",
              file=sys.stderr)
        return 0  # graceful — never crash the publish pipeline

    os.makedirs(FIG_DIR, exist_ok=True)
    targets = resolve_targets(sys.argv[1:])
    total = 0
    for path in targets:
        if not path.endswith(".html"):
            continue
        slug = os.path.basename(path)[:-5]
        with open(path, encoding="utf-8") as f:
            html = f.read()
        figs = list(chart_svgs(html))
        for idx, svg, w, h in figs:
            out = os.path.join(FIG_DIR, f"{slug}-fig{idx}.png")
            ok = rasterize(chrome, standalone_svg(svg, w, h), w, h, out)
            if ok:
                total += 1
                print(f"  {slug}-fig{idx}.png  ({int(w*SCALE)}x{int(h*SCALE)})")
            else:
                print(f"  FAILED: {slug}-fig{idx}", file=sys.stderr)
    print(f"generate_figures: wrote {total} figure PNG(s) to assets/figures/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
