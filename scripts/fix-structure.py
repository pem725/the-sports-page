#!/usr/bin/env python3
"""
fix-structure.py — Revert broken semantic HTML changes and fix masthead consistency.

The regex-based header/main/footer replacements broke file structure in files
with complex layouts (multiple paper divs, nested sections). This script:

1. Reverts <header class="masthead"> → <div class="masthead">
2. Reverts <main id="main-content" class="paper"> → <div class="paper">
3. Reverts </main> → </div>, </header> → </div>, </footer> → </div>
4. Reverts <footer class="footer"> → <div class="footer">
5. Keeps: skip link, nav bar, clickable title (these are additive, not structural)
6. Standardizes masthead CSS across all article pages to match homepage
"""

import os
import re
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Homepage masthead CSS (the correct version)
HOMEPAGE_TITLE_CSS = "font-size:clamp(2rem,5vw,3.2rem);font-weight:700;line-height:1.1;letter-spacing:.04em;text-transform:uppercase;margin:.1rem 0"
ARTICLE_TITLE_CSS_PATTERNS = [
    r"font-size:clamp\(3rem,8vw,5\.5rem\);font-weight:900;line-height:1;letter-spacing:-\.02em",
    r"font-size:clamp\(3rem,8vw,5\.5rem\);font-weight:900;line-height:1;letter-spacing:-.02em",
]


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. Revert semantic elements back to divs
    content = content.replace('<header class="masthead">', '<div class="masthead">')
    content = content.replace('</header>', '</div>')
    content = content.replace('<main id="main-content" class="paper">', '<div id="main-content" class="paper">')
    content = content.replace('</main>', '</div>')
    content = content.replace('<footer class="footer">', '<div class="footer">')
    # Note: </footer> was already handled by </header> replacement above if it matched,
    # but let's be explicit
    content = content.replace('</footer>', '</div>')

    # 2. Fix the skip link target (id stays on the paper div)
    # Already correct: <div id="main-content" class="paper">

    # 3. Standardize masthead .title CSS to match homepage
    for pattern in ARTICLE_TITLE_CSS_PATTERNS:
        content = re.sub(
            r'\.title\{font-family:\'Playfair Display\',serif;' + pattern + r'\}',
            ".title{font-family:'Playfair Display',serif;" + HOMEPAGE_TITLE_CSS + "}",
            content
        )

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  FIXED: {os.path.basename(filepath)}")
        return True

    print(f"  OK: {os.path.basename(filepath)}")
    return False


def main():
    print("Reverting broken semantic HTML and standardizing masthead...")
    print()

    files = (
        [os.path.join(REPO, 'index.html')]
        + sorted(glob.glob(os.path.join(REPO, 'published', '*.html')))
        + sorted(glob.glob(os.path.join(REPO, 'queue', '*.html')))
        + sorted(glob.glob(os.path.join(REPO, 'reserve', '*.html')))
    )

    updated = 0
    for f in files:
        if process_file(f):
            updated += 1

    print(f"\nDone. Fixed {updated} files.")
    print("\nKept: skip link, nav bar, clickable title")
    print("Reverted: header/main/footer semantic elements → divs")
    print("Standardized: masthead .title CSS to homepage style")


if __name__ == '__main__':
    main()
