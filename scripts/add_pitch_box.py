#!/usr/bin/env python3
"""
Add the Pitch a Story box to every published piece that doesn't have one.

The box routes reader story ideas to GitHub Issues (primary, with the
`story-idea` label so they accumulate where Claude can process them) and
to Patrick's email (fallback for non-GitHub readers).

Inserts before <div id="share"> if present; otherwise before </body>.
Skips:
  - files that already have <div id="pitch">
  - Deeper Dive companions (-deeper.html)
  - Sunday Editions (sunday-*.html) — they have a different structure
"""

import os
import sys
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLISHED = os.path.join(REPO, "published")

PITCH_BOX = """<!-- PITCH BOX -->
<div id="pitch" style="max-width:820px;margin:1.5rem auto 0;background:var(--cream);border:2px solid var(--gold);padding:2rem 2.5rem;text-align:center">
  <div style="font-family:'Roboto Mono',monospace;font-size:.7rem;letter-spacing:.22em;text-transform:uppercase;color:var(--gold);font-weight:700;margin-bottom:.6rem">Pitch a Story to The Sports Page</div>
  <h3 style="font-family:'Playfair Display',serif;font-size:clamp(1.4rem,3.5vw,1.8rem);font-weight:900;color:var(--ink);margin-bottom:.5rem;line-height:1.2">Got a stat that doesn&rsquo;t make sense?</h3>
  <p style="font-family:'Libre Baskerville',serif;font-style:italic;color:var(--muted);font-size:1rem;margin-bottom:1.4rem;line-height:1.5">Send it. We&rsquo;ll find what the math is hiding &mdash; and we just might write the next issue about it.</p>
  <div style="display:flex;gap:.8rem;justify-content:center;flex-wrap:wrap">
    <a href="https://github.com/pem725/the-sports-page/issues/new?labels=story-idea&title=Story+Idea%3A+&body=**Your+name%3A**+%0A%0A**Sport%3A**+%0A%0A**The+stat+or+story%3A**+%0A%0A**Why+it+matters%3A**+%0A%0A**Timeliness%3A**+breaking+%2F+this+week+%2F+anytime" target="_blank" rel="noopener" style="display:inline-block;padding:.75rem 1.4rem;background:var(--steel);color:var(--cream);text-decoration:none;font-family:'Roboto Mono',monospace;font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;font-weight:600">Submit via GitHub &rarr;</a>
    <a href="mailto:pem725@gmail.com?subject=The+Sports+Page+%E2%80%94+Story+Idea&body=Hi+Patrick%2C%0A%0AI+have+an+idea+for+a+piece%3A%0A%0A" style="display:inline-block;padding:.75rem 1.4rem;background:transparent;color:var(--ink);text-decoration:none;font-family:'Roboto Mono',monospace;font-size:.78rem;letter-spacing:.1em;text-transform:uppercase;font-weight:600;border:2px solid var(--ink)">Or Email Patrick</a>
  </div>
</div>
"""


def should_skip(filename):
    if filename.endswith("-deeper.html"):
        return True, "deeper-dive companion"
    if filename.startswith("sunday-"):
        return True, "Sunday Edition (different structure)"
    return False, None


def insert_pitch_box(content):
    """Insert pitch box before <div id="share"> if present, else before </body>."""
    if 'id="pitch"' in content:
        return content, False
    if '<div id="share"' in content:
        new_content = content.replace(
            '<div id="share"',
            PITCH_BOX + '<div id="share"',
            1,
        )
        return new_content, True
    if "</body>" in content:
        new_content = content.replace("</body>", PITCH_BOX + "\n</body>", 1)
        return new_content, True
    return content, False


def main():
    dry_run = "--dry-run" in sys.argv
    files = sorted(os.listdir(PUBLISHED))
    changed = 0
    skipped_known = 0
    skipped_already = 0
    no_anchor = 0
    for fn in files:
        if not fn.endswith(".html"):
            continue
        skip, reason = should_skip(fn)
        if skip:
            print(f"  skip  {fn}  ({reason})")
            skipped_known += 1
            continue
        path = os.path.join(PUBLISHED, fn)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        new_content, did_change = insert_pitch_box(content)
        if not did_change and 'id="pitch"' in content:
            skipped_already += 1
            continue
        if not did_change:
            print(f"  warn  {fn}  (no anchor — needs manual edit)")
            no_anchor += 1
            continue
        if dry_run:
            print(f"  WOULD ADD  {fn}")
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"  added {fn}")
        changed += 1
    print(f"\nSummary: {changed} {'would change' if dry_run else 'updated'}, "
          f"{skipped_already} already had pitch box, "
          f"{skipped_known} skipped (deeper/sunday), "
          f"{no_anchor} need manual edit")


if __name__ == "__main__":
    main()
