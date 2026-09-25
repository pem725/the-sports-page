#!/usr/bin/env python3
"""Put a small generic sport mark beside the headline.

    python3 scripts/add_topic_glyph.py queue/*.html
    python3 scripts/add_topic_glyph.py --check queue/*.html

TIM'S SUGGESTION, 2026-09-17: "Could the headline include a tiny graphic
indicating the sport/level... Headlines don't mention the information currently.
A tiny graphic would make the point without expanding the headline, keeping its
neat uniformity."

He is right that the information is missing where it is needed. The sport IS
named, in the kicker above the masthead and in the archive tags -- but not next to
the headline, which is the one line a reader actually decides on, and not on the
social card at all. And the constraint he adds is the whole design brief: it
cannot lengthen the headline, which has just been cut to third-grade vocabulary.

HIS TRADEMARK POINT IS THE IMPORTANT ONE and it is correct. League shields, team
marks and wordmarks are all protected. Everything here is a generic sporting
object drawn from scratch: a ball, a puck, a set of bars, a balance. Nobody owns
the shape of a football.

THE LEVEL PROBLEM, solved by the object rather than by a label. A college football
carries two white stripes and a professional one does not. That is a real,
observable difference between the two balls and it belongs to nobody, so college
gets the striped ball and the pros get the plain one. A football fan reads it
without being told; anyone else still has the kicker.

DRAWN, NOT DOWNLOADED. Each glyph is a handful of SVG primitives inlined into the
page, so there is no request, no external dependency and nothing to break a strict
CSP. They use `currentColor`, which means each inherits the topic colour the
stylesheet already defines and themes correctly on its own.

SIZED FOR 20 PIXELS, checked at 20 pixels. The first pair of footballs had laces
drawn as a line plus three ticks; at display size that merged into a blob. Detail
that survives a preview at 4x is not detail that survives the page.
"""
import argparse
import glob
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
GLYPHS = REPO / "assets" / "glyph"

TOPIC_TO_GLYPH = {
    "cfb": "cfb", "college football": "cfb", "ncaa": "cfb",
    "nfl": "nfl", "pro football": "nfl",
    "mlb": "mlb", "baseball": "mlb",
    "nhl": "nhl", "hockey": "nhl",
    "markets": "markets", "betting": "markets",
    "methods": "methods", "statistics": "methods",
}
TOPIC_TO_COLOUR = {
    "cfb": "var(--rust)", "nfl": "var(--steel)", "mlb": "var(--steel)",
    "nhl": "var(--muted)", "markets": "var(--gold)", "methods": "var(--muted)",
}

CSS = """
.hed-glyph{display:inline-flex;align-items:center;vertical-align:-0.08em;margin-right:.44rem}
.hed-glyph svg{width:.66em;height:.51em}
"""

MARKER = '<span class="hed-glyph"'


def topic_of(text):
    m = re.search(r"^topic:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else None


def apply(path, check=False):
    p = pathlib.Path(path)
    t = p.read_text(encoding="utf-8")
    topic = topic_of(t)
    if not topic:
        return f"{p.name}: no topic in PUBLISH-META"
    key = TOPIC_TO_GLYPH.get(topic.strip().lower())
    if not key:
        return f"{p.name}: no glyph for topic {topic!r}"
    if MARKER in t:
        return f"{p.name}: already has a glyph"
    if check:
        return f"{p.name}: would add {key}"

    svg = (GLYPHS / f"{key}.svg").read_text().strip()
    # INTRINSIC SIZE, NOT JUST CSS. An <svg> with a viewBox and no width/height
    # expands to fill its container when the stylesheet is not there. The glyph
    # markup gets copied verbatim into index.html and into feed.xml, neither of
    # which carries .hed-glyph -- so the archive rendered these at 642x494 px.
    # Explicit attributes make the glyph correct anywhere it is pasted; CSS then
    # scales it where the stylesheet exists.
    svg = svg.replace('<svg class="tg" viewBox',
                      '<svg class="tg" width="26" height="20" viewBox', 1)
    colour = TOPIC_TO_COLOUR.get(key, "var(--muted)")
    span = f'<span class="hed-glyph" style="color:{colour}" title="{topic}">{svg}</span>'

    m = re.search(r'(<h[12] class="hed">)', t)
    if not m:
        return f"{p.name}: no headline found"
    t = t[:m.end()] + span + t[m.end():]

    if ".hed-glyph" not in t:
        t = t.replace("</style>", CSS + "</style>", 1)
    p.write_text(t, encoding="utf-8")
    return f"{p.name}: added {key} ({topic})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    files = [f for pat in a.paths for f in glob.glob(pat)]
    for f in sorted(files):
        print("  " + apply(f, a.check))
    return 0


if __name__ == "__main__":
    sys.exit(main())
