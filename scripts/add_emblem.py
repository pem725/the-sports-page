#!/usr/bin/env python3
"""Put The Sports Page emblem (the navy S with the normal curve through it) on a page.

Editor, 2026-10-15: "Every page that's committed needs to have our emblem." Before
this, only the homepage carried it -- 250-odd issues, primers, tools and desks
did not.

    python3 scripts/add_emblem.py FILE [FILE ...]     # stamp these
    python3 scripts/add_emblem.py --all               # every tracked public page
    python3 scripts/add_emblem.py --check             # list pages still missing it; exit 1 if any

Idempotent: a page already carrying `data-emblem` is left alone, so the publisher
can run it on every file it ships.

The pages have grown four masthead shapes, so there are four placements, tried in
order. Each puts the emblem where the paper's name is, never somewhere new:

  1. a `.title` element      -> inline, just before the name, sized in em so it
                                scales with whatever size that page sets its title
  2. a `.kick` line (the     -> its own small line above the kicker, left-aligned
     Pool Desk / Engine pages)  like the rest of those pages
  3. a `.masthead` kicker    -> centered above the kicker
  4. the first `<h1>`        -> its own line above it

The markup carries explicit width/height and inline styles. CSS-free on purpose:
this repo has broken a component three times by copying markup somewhere its
stylesheet did not follow (see CLAUDE.md, topic glyphs).

The homepage is NOT stamped: it has its own, larger lockup beside the masthead.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://thesportspage.net/'
SRC = (f'src="{BASE}assets/logo-badge.png" '
       f'srcset="{BASE}assets/logo-badge.png 1x, {BASE}assets/logo-badge@2x.png 2x"')

# Not reader pages: the homepage has its own lockup, data/ holds a fragment that
# gets injected into issues, board/ and merch/ are private working pages, and
# reserve/ holds the read-only Sunday template (the Sunday workflow stamps the copy).
SKIP_FILES = {'index.html'}
SKIP_DIRS = ('data/', 'board/', 'merch/', 'analysis/', 'frames/', 'reserve/')


# On a phone the name already fills the line, and an emblem beside it pushed
# "THE SPORTS PAGE" onto two lines (measured 2026-10-15: 35px tall -> 72px).
# So below 520px it steps up onto its own line above the name. The inline style
# is the fallback if this rule is ever lost: beside the name, which still works.
NARROW = ('<style>@media(max-width:520px){img[data-emblem]{display:block!important;'
          'height:1.25em!important;margin:0 auto .2rem!important}}</style>')


def inline_img():
    return (NARROW + f'<img data-emblem {SRC} alt="" width="40" height="40" '
            'style="display:inline-block;height:1.05em;width:auto;vertical-align:-.17em;'
            'margin-right:.28em;border:none">')


def block_img(px, align):
    return (f'<a data-emblem href="{BASE}" target="_blank" rel="noopener" '
            f'style="display:block;text-align:{align};border:none;text-decoration:none;'
            f'margin:0 0 .5rem;line-height:0">'
            f'<img {SRC} alt="The Sports Page" width="{px}" height="{px}" '
            f'style="width:{px}px;height:{px}px;border:none;display:inline-block"></a>')


def stamp(html):
    """Return (new_html, placement) or (html, None) when no placement fits."""
    if 'data-emblem' in html:
        return html, 'already'

    # 1. the paper's name, inline. Go inside a wrapping link so the emblem is
    #    clickable along with the name.
    m = re.search(r'<(div|h1)\s+class="title"[^>]*>(\s*<a\b[^>]*>)?', html)
    if m:
        return html[:m.end()] + inline_img() + html[m.end():], 'title'

    # 2. the Pool Desk / Engine / interactive layout: a left-aligned kicker line.
    m = re.search(r'<(div|p)\s+class="kick"', html)
    if m:
        return html[:m.start()] + block_img(44, 'left') + '\n' + html[m.start():], 'kick'

    # 3. a masthead with a kicker but no title element (Sunday No. 13).
    m = re.search(r'<div\s+class="kicker"', html)
    if m and 'class="masthead"' in html[:m.start()]:
        return html[:m.start()] + block_img(56, 'center') + '\n  ' + html[m.start():], 'kicker'

    # 4. anything else with a headline.
    m = re.search(r'<h1\b', html)
    if m:
        return html[:m.start()] + block_img(44, 'left') + '\n  ' + html[m.start():], 'h1'

    return html, None


def public_pages():
    out = subprocess.run(['git', 'ls-files', '*.html'], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.split()
    return [ROOT / p for p in out
            if p not in SKIP_FILES and not p.startswith(SKIP_DIRS)
            and not Path(p).name.startswith('view-source_')]


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == '--check':
        missing = [p for p in public_pages() if 'data-emblem' not in p.read_text()]
        for p in missing:
            print('missing emblem:', p.relative_to(ROOT))
        print(f'{len(missing)} page(s) missing the emblem')
        return 1 if missing else 0

    files = public_pages() if argv[0] == '--all' else [Path(a) for a in argv]
    counts, failed = {}, []
    for f in files:
        html = f.read_text()
        new, where = stamp(html)
        if where is None:
            failed.append(f)
            continue
        if new != html:
            f.write_text(new)
        counts[where] = counts.get(where, 0) + 1
    print('placements:', ', '.join(f'{k} {v}' for k, v in sorted(counts.items())))
    for f in failed:
        print('NO PLACEMENT FOUND:', f)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
