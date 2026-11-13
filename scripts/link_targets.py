#!/usr/bin/env python3
"""Open a new tab only when the reader is leaving the site.

Set by the editor 2026-11-13, reversing the 2026-06-19 rule that sent EVERY link to a new
tab: "When the content stays the same, let's not start opening up tabs." Those tabs had been
for his own side-by-side comparing, and a reader clicking through the paper ends up with a
row of tabs and a Back button that does nothing. It is also the long-standing usability
advice (Nielsen Norman Group): stay in the same tab; open a new one for a different site,
or when leaving would throw away something the reader is doing.

The rule, per <a> tag:
  - our own pages (relative links, thesportspage.net, in-page #anchors, mailto:) -> same tab
  - another site -> new tab, with rel="noopener"

    python3 scripts/link_targets.py --check     # list violations, exit 1 if any
    python3 scripts/link_targets.py --fix       # rewrite them in place

Skips feed.xml on purpose: email clients ignore target, and that file must stay
byte-stable for Buttondown. Also skips planning/ and anything git ignores.
"""
import argparse, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = re.compile(r"<a\b[^>]*>", re.I | re.S)
HREF = re.compile(r"""\bhref\s*=\s*(["'])(.*?)\1""", re.I | re.S)
TARGET = re.compile(r"""\s+target\s*=\s*(["'])_blank\1""", re.I)
REL = re.compile(r"""\s+rel\s*=\s*(["'])\s*noopener(?:\s+noreferrer)?\s*\1""", re.I)
OURS = re.compile(r"^(?:https?://(?:www\.)?thesportspage\.net(?:/|$)|mailto:|#|\?|[^:]*$)", re.I)
SKIP_DIRS = ("planning/", "node_modules/", ".git/")
# The Sunday template is read-only by rule (CLAUDE.md); the editor decides whether it changes.
SKIP_FILES = ("reserve/sunday-recap-template.html",)


def files():
    out = subprocess.run(["git", "ls-files", "*.html", "*.js"], cwd=REPO, capture_output=True, text=True).stdout
    return [f for f in out.split() if not f.startswith(SKIP_DIRS) and f not in SKIP_FILES]


def internal(href):
    # A link built in JavaScript ('+esc(url)+') points wherever its data says; our data
    # files only hold our own pages, so a quote-plus inside the href counts as ours.
    return bool(OURS.match(href.strip())) or "'+" in href or '"+' in href


def fix_tag(tag):
    m = HREF.search(tag)
    if not m:
        return tag
    has_target = bool(TARGET.search(tag))
    if internal(m.group(2)):
        if has_target:
            tag = REL.sub("", TARGET.sub("", tag))
    elif not has_target:
        tag = tag[:-1].rstrip() + ' target="_blank" rel="noopener">'
    return tag


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--fix", action="store_true")
    a = ap.parse_args()
    total, touched = 0, 0
    for f in files():
        p = os.path.join(REPO, f)
        s = open(p, encoding="utf-8").read()
        new = TAG.sub(lambda m: fix_tag(m.group(0)), s)
        if new != s:
            n = sum(1 for x, y in zip(TAG.findall(s), TAG.findall(new)) if x != y)
            total += n; touched += 1
            if a.fix:
                open(p, "w", encoding="utf-8").write(new)
            else:
                print(f"{f}: {n}")
    print(f"{'fixed' if a.fix else 'found'} {total} link(s) in {touched} file(s)")
    sys.exit(1 if a.check and total else 0)


if __name__ == "__main__":
    main()
