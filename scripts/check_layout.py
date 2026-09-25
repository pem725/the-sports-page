#!/usr/bin/env python3
"""The copy editor. Reads the page as printed, not as intended.

    python3 scripts/check_layout.py queue/165-sub-500-champion.html
    python3 scripts/check_layout.py --all
    python3 scripts/check_layout.py --all --quiet     # only failures

THE EDITOR ASKED FOR THIS, 2026-09-25: "The box all the way at the bottom that
starts with the implied probability... why is there no margin? We need to spot
check all of these things to make sure there's no formatting oddities for each
production run. In essence, we need a copy editor."

WHAT HAD GONE WRONG. Twenty published issues used `class="box"` and none of them
defined `.box` in their own <style> block. The class came along when the markup
was copied; the rule did not. The browser applied nothing, so the box lost its
padding and its margin and the text ran to the edge of the panel.

That is the third fault of exactly this shape -- markup moved somewhere its CSS
was not. The topic glyphs blew up to 642px in the archive for the same reason,
and the OG cards fell back to a stat row when an entity killed the SVG. All three
share a property that makes them survive: **the page still renders.** Nothing is
blank, nothing errors, and the result looks like a slightly ugly version of the
intended thing rather than a broken one. A human skimming will not catch it.

So this checks what the page ACTUALLY declares against what it ACTUALLY uses,
which is the one question none of the other checkers ask. check_readability reads
prose, check_voice reads person, check_headline reads the headline, check_spelling
reads vocabulary. None of them look at whether the page will lay out.

HONEST LIMIT, and it matters: this reads the file, not a rendered page. It cannot
see a collision, a cropped figure, or text overflowing a container -- those need a
browser, and the house rule for figures already says render it and look at it.
What this catches is the cheaper and more common fault: a rule that was never
there at all.
"""
import argparse
import glob
import html.parser
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

# Classes that belong to the site chrome injected at publish time, or that exist
# purely as JS hooks, so a page may legitimately use them without a local rule.
EXEMPT = {"tg", "share-section", "hed-glyph", "cc", "cc-i", "watch", "w-row",
          "w-sport", "w-game", "w-time", "w-why", "watch-label", "watch-note",
          "issue", "issue-num", "issue-body", "issue-date", "issue-hed",
          "issue-deck", "issue-tags", "issues", "skip",
          # decorative hooks: the element carries its own inline styles
          "cartoon"}

VOID = {"br", "img", "hr", "meta", "link", "input", "source", "path", "circle",
        "rect", "line", "polyline", "polygon", "ellipse", "use", "stop", "area",
        "col", "embed", "param", "track", "wbr"}


class Scan(html.parser.HTMLParser):
    """Collects what the markup uses, and where the tags do not balance."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.classes, self.ids, self.stack = set(), [], []
        self.unclosed, self.stray, self.nested_a = [], [], 0
        self.a_depth, self.in_svg = 0, 0
        self.empty_href = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        for c in (d.get("class") or "").split():
            self.classes.add(c)
        if d.get("id"):
            self.ids.append(d["id"])
        if tag == "svg":
            self.in_svg += 1
        if tag == "a":
            if self.a_depth:
                self.nested_a += 1
            self.a_depth += 1
            h = (d.get("href") or "").strip()
            if not h or h == "#":
                self.empty_href.append(h)
        if tag not in VOID and not (self.in_svg and tag in VOID):
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag == "a" and self.a_depth:
            self.a_depth -= 1
        if tag == "svg" and self.in_svg:
            self.in_svg -= 1
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.unclosed += [s for s in self.stack[i + 1:]]
                del self.stack[i:]
                return
        self.stray.append((tag, self.getpos()[0]))


def declared_classes(text):
    """Every class name any rule in the page's own <style> blocks can match."""
    out = set()
    for block in re.findall(r"<style[^>]*>(.*?)</style>", text, re.S | re.I):
        block = re.sub(r"/\*.*?\*/", " ", block, flags=re.S)
        for sel in re.findall(r"([^{}]+)\{", block):
            out.update(re.findall(r"\.([A-Za-z_][\w-]*)", sel))
    return out


def declared_vars(text):
    out = set()
    for block in re.findall(r"<style[^>]*>(.*?)</style>", text, re.S | re.I):
        out.update(re.findall(r"(--[\w-]+)\s*:", block))
    return out


def check(path):
    t = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    name = pathlib.Path(path).name
    if name.startswith("_"):          # the template is meant to be full of markers
        return name, [], []
    s = Scan()
    try:
        s.feed(t)
    except Exception as e:
        return name, ["parser died: %s" % e], []

    fails, warns = [], []

    used = {c for c in s.classes if not c.startswith("_")}
    missing = sorted(used - declared_classes(t) - EXEMPT)
    if missing:
        fails.append(f"class used but never defined: {', '.join(missing)} "
                     f"-- the element gets no padding, margin or color")

    vars_used = set(re.findall(r"var\((--[\w-]+)", t))
    vm = sorted(vars_used - declared_vars(t))
    if vm:
        fails.append(f"CSS variable used but not defined: {', '.join(vm)} "
                     f"-- resolves to nothing, usually black or transparent")

    if s.nested_a:
        fails.append(f"{s.nested_a} anchor(s) nested inside another anchor -- invalid, "
                     f"browsers will split them unpredictably")

    dup = sorted({i for i in s.ids if s.ids.count(i) > 1})
    if dup:
        fails.append(f"duplicate id: {', '.join(dup)}")

    if s.unclosed:
        warns.append("never closed: " + ", ".join(f"<{tg}> line {ln}" for tg, ln in s.unclosed[:4]))
    if s.stray:
        warns.append("closing tag with no opener: "
                     + ", ".join(f"</{tg}> line {ln}" for tg, ln in s.stray[:4]))
    if s.empty_href:
        warns.append(f"{len(s.empty_href)} link(s) with an empty or placeholder href")

    # TODO_DATE and TODO_NN are LEGITIMATE in queue/ -- autopublish stamps both at
    # publish time, and it already runs its own leftover guard afterwards. Flagging
    # them here would mean "fixing" files by hardcoding a date the publisher is
    # about to overwrite. Anything else, or anything at all once published, is real.
    FILLED = {"TODO_DATE", "TODO_NN"}
    queued = "queue/" in str(path).replace("\\", "/")
    left = sorted(set(re.findall(r"TODO_[A-Z0-9_]*", t)) - (FILLED if queued else set()))
    if left:
        fails.append("unreplaced template marker: " + ", ".join(left[:6]))
    if "queue/" in str(path) and "<!-- WATCH_BLOCK -->" not in t and "_TEMPLATE" not in name:
        warns.append("no <!-- WATCH_BLOCK --> marker; the issue will publish without one")

    # a figure whose SVG has no viewBox cannot scale on a phone
    for svg in re.findall(r"<svg\b[^>]*>", t):
        if "viewBox" not in svg:
            warns.append("an <svg> has no viewBox and will not scale")
            break
    return name, fails, warns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    files = a.paths
    if a.all or not files:
        files = sorted(glob.glob(str(REPO / "published/*.html"))
                       + glob.glob(str(REPO / "queue/*.html"))
                       + [str(REPO / "index.html")])
    nf = nw = 0
    for f in files:
        name, fails, warns = check(f)
        if fails:
            nf += 1
        if warns:
            nw += 1
        if a.quiet and not fails:
            continue
        if fails or warns or not a.quiet:
            tag = "FAIL" if fails else ("WARN" if warns else "PASS")
            print(f"\n  {name:<36}[{tag}]")
            for x in fails:
                print(f"    FAIL: {x}")
            for x in warns:
                print(f"    warn: {x}")
    print(f"\n  {len(files)} checked   {nf} with layout faults   {nw} with warnings")
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())
