#!/usr/bin/env python3
"""
fix-navigation.py — Add navigation, semantic HTML, and accessibility
to all pages. Implements:

1. Clickable masthead title → links to homepage
2. "← Back to Archive" nav link on article pages
3. Semantic HTML: header, main, nav, footer elements
4. Skip-to-content link
5. Proper form labels on pitch form
6. ARIA landmarks

Idempotent — skips files already updated.
"""

import os
import re
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_home_path(filepath):
    """Return relative path to index.html based on file location."""
    if '/published/' in filepath or '/queue/' in filepath or '/reserve/' in filepath:
        return '../index.html'
    return '#'


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if already has nav link
    if 'Back to Archive' in content or 'skip-link' in content:
        print(f"  SKIP (already updated): {os.path.basename(filepath)}")
        return False

    home = get_home_path(filepath)
    is_homepage = (home == '#')
    modified = False

    # 1. Add skip link after <body>
    if '<a href="#main-content" class="skip-link">' not in content:
        skip_css = (
            '.skip-link{position:absolute;top:-40px;left:0;background:var(--ink);color:var(--cream);'
            'padding:.5rem 1rem;z-index:100;font-family:"Roboto Mono",monospace;font-size:.75rem;'
            'transition:top .2s}.skip-link:focus{top:0}'
        )
        # Add skip link CSS to the style block
        content = content.replace('</style>', f'{skip_css}\n</style>')
        content = content.replace(
            '<body>',
            '<body>\n<a href="#main-content" class="skip-link">Skip to main content</a>'
        )
        modified = True

    # 2. Make masthead title clickable (link to home)
    # Match: <div class="title">The Sports Page</div>
    if not is_homepage:
        old_title = '<div class="title">The Sports Page</div>'
        new_title = f'<div class="title"><a href="{home}" style="color:inherit;text-decoration:none">The Sports Page</a></div>'
        if old_title in content:
            content = content.replace(old_title, new_title)
            modified = True

    # 3. Add navigation bar after datebar (on article pages only)
    if not is_homepage and '<!-- NAV -->' not in content:
        nav_html = (
            '\n<!-- NAV -->\n'
            f'<nav style="max-width:820px;margin:.4rem auto 0;font-family:\'Roboto Mono\',monospace;font-size:.7rem;letter-spacing:.08em">'
            f'<a href="{home}" style="color:var(--rust);text-decoration:none;border-bottom:1px solid rgba(184,58,30,.3)">'
            f'&larr; Back to Archive</a></nav>\n'
        )
        # Insert after closing </div> of datebar, before the paper div
        # The datebar is inside the masthead, so insert after </div>\n</div>\n (end of masthead)
        masthead_end = re.search(r'(</div>\s*\n\s*</div>\s*\n)(\s*<!--\s*PAPER\s*-->|<div class="paper">)', content)
        if masthead_end:
            insert_pos = masthead_end.start(2)
            content = content[:insert_pos] + nav_html + '\n' + content[insert_pos:]
            modified = True

    # 4. Upgrade semantic HTML
    # div.masthead → header.masthead
    if '<div class="masthead">' in content and '<header class="masthead">' not in content:
        # Find the masthead div and its closing tag
        # The masthead ends with </div> before the nav or paper section
        content = content.replace('<div class="masthead">', '<header class="masthead">', 1)
        # Need to find the correct closing </div> for masthead
        # It's the </div> right before <!-- NAV --> or <!-- PAPER --> or <div class="paper">
        # Use a targeted replacement
        content = re.sub(
            r'</div>(\s*\n\s*<!-- NAV -->)',
            r'</header>\1',
            content,
            count=1
        )
        if '</header>' not in content:
            # Fallback: replace the closing div before paper
            content = re.sub(
                r'</div>(\s*\n\s*(?:<!-- PAPER -->|<(?:div|main) class="paper">))',
                r'</header>\1',
                content,
                count=1
            )
        modified = True

    # div.paper → main#main-content.paper
    if '<div class="paper">' in content:
        content = content.replace(
            '<div class="paper">',
            '<main id="main-content" class="paper">',
            1
        )
        # Find the matching closing </div> for paper
        # It's the </div> right before <!-- SHARE SECTION --> or the pitch form's parent closing
        # This is tricky because paper contains many nested divs
        # Strategy: find the last </div> before <!-- SHARE SECTION --> or </body>
        # Actually, let's find the closing by looking for the pattern after the footer
        content = re.sub(
            r'</div>(\s*\n\s*(?:<!-- STORY IDEAS|<!-- SHARE SECTION|</body>|\n<!-- SHARE))',
            r'</main>\1',
            content,
            count=1
        )
        modified = True

    # div.footer → footer.footer (inside main/paper)
    if '<div class="footer">' in content:
        content = content.replace('<div class="footer">', '<footer class="footer">', 1)
        # The footer div closes with </div> — find the right one
        # It's typically 3-4 lines after the opening
        # Replace the first </div> after <footer class="footer">
        parts = content.split('<footer class="footer">', 1)
        if len(parts) == 2:
            after = parts[1]
            after = after.replace('</div>', '</footer>', 1)
            content = parts[0] + '<footer class="footer">' + after
        modified = True

    # 5. Fix form labels on pitch form
    if 'id="pitch-form"' in content and 'for="pitch-name"' not in content:
        content = content.replace(
            'placeholder="Your name" required',
            'id="pitch-name" placeholder="Your name" required'
        )
        content = content.replace(
            'placeholder="Sport (MLB, NFL, NHL, CFB, WNBA, etc.)"',
            'id="pitch-sport" placeholder="Sport (MLB, NFL, NHL, CFB, WNBA, etc.)"'
        )
        modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  UPDATED: {os.path.basename(filepath)}")
        return True

    return False


def main():
    print("Fixing navigation, semantic HTML, and accessibility...")
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

    print(f"\nDone. Updated {updated} files.")


if __name__ == '__main__':
    main()
