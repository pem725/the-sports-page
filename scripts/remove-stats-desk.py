#!/usr/bin/env python3
"""
remove-stats-desk.py — Remove the 'Ask the Stats Desk' interactive form
from all published, queued, and template pages. Leaves CSS (harmless).
Idempotent — skips files that don't have the desk section.
"""

import os
import re
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'class="desk"' not in content:
        print(f"  SKIP (no desk section): {os.path.basename(filepath)}")
        return False

    # Remove the desk div and its associated askDesk script.
    # Pattern: optional comment, <div class="desk">...</div>, then <script>...askDesk...</script>
    # Use a regex that matches from the comment (or desk div) through the script.
    pattern = r'\n*<!-- ASK THE STATS DESK -->\n*<div class="desk">.*?</div>\s*<script>.*?</script>\s*'
    new_content = re.sub(pattern, '\n\n', content, flags=re.DOTALL)

    # Fallback: if the comment wasn't there, try without it
    if new_content == content:
        pattern = r'\n*<div class="desk">.*?</div>\s*<script>.*?</script>\s*'
        new_content = re.sub(pattern, '\n\n', content, flags=re.DOTALL)

    if new_content == content:
        print(f"  WARN: desk found but regex didn't match: {os.path.basename(filepath)}")
        return False

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"  UPDATED: {os.path.basename(filepath)}")
    return True


def main():
    print("Removing 'Ask the Stats Desk' form from all pages...")
    print()

    files = (
        sorted(glob.glob(os.path.join(REPO, 'published', '*.html')))
        + sorted(glob.glob(os.path.join(REPO, 'queue', '*.html')))
        + sorted(glob.glob(os.path.join(REPO, 'reserve', '*.html')))
    )

    updated = 0
    for f in files:
        if process_file(f):
            updated += 1

    print(f"\nDone. Updated {updated} files.")


if __name__ == '__main__':
    main()
