#!/usr/bin/env python3
"""Render a published Sports Page issue (HTML) to a podcast MP3 using the shared
Piper deep-narrator pipeline (scripts/tts_render.py).

It extracts the *readable* prose from the issue's main content -- the headline,
deck, intro, section headers, body paragraphs, list items, and pull quotes --
and skips everything that does not narrate cleanly: the nav, the inline
figure/SVG, raw data tables, the stat-card row, the byline, the share section,
the pitch form, the footer, and the "readership pending" placeholder. Concept
"(i)" markers are dropped.

Output: audio/<slug>.mp3  (audio/ is gitignored; upload the MP3 to Spotify and
link the episode from the page).

Usage:
  render_issue_audio.py published/sunday-011.html            # render mp3
  render_issue_audio.py published/sunday-011.html --text     # preview narration
  render_issue_audio.py published/sunday-011.html out.mp3    # custom output path
"""
import sys, os, re, html
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr'}
SKIP_TAGS = {'script', 'style', 'svg', 'figure', 'table', 'aside',
             'nav', 'form', 'button', 'select', 'textarea', 'option', 'head'}
SKIP_CLASSES = {'byline', 'stat-row', 'sc', 'datebar', 'footer',
                'issue-tags', 'skip-link', 'tagline'}
BLOCK_TAGS = {'h1', 'h2', 'h3', 'h4', 'p', 'li', 'blockquote', 'cite'}
BLOCK_DIV_CLASSES = {'deck', 'intro'}
# narration noise to drop even if it parses cleanly
DENY = re.compile(r'(readership data pending|analytics pipeline|^what readers read)', re.I)


class IssueExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []          # one dict per open (non-void) element
        self.active = False      # inside #main-content, before #share
        self.skip_depth = 0      # number of open skip-root ancestors
        self.cur = []            # current block's text fragments
        self.blocks = []

    def _flush(self):
        text = re.sub(r'\s+', ' ', ' '.join(self.cur)).strip()
        if text:
            self.blocks.append(text)
        self.cur = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        ad = dict(attrs)
        cls = set((ad.get('class') or '').split())
        if ad.get('id') == 'main-content':
            self.active = True
        if ad.get('id') == 'share':
            self.active = False
        is_block = (tag in BLOCK_TAGS) or (tag == 'div' and bool(cls & BLOCK_DIV_CLASSES))
        is_skip = (tag in SKIP_TAGS) or bool(cls & SKIP_CLASSES) or ('cc-i' in cls)
        # close the prior block before opening a new one
        if self.skip_depth == 0 and self.active and is_block:
            self._flush()
        if is_skip:
            self.skip_depth += 1
        self.stack.append({'tag': tag, 'skip': is_skip, 'block': is_block})

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        idx = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]['tag'] == tag:
                idx = i
                break
        if idx is None:
            return
        popped = self.stack[idx:]
        self.stack = self.stack[:idx]
        for el in popped:
            if el['skip']:
                self.skip_depth -= 1
        if self.skip_depth == 0 and self.active and popped[0]['block']:
            self._flush()

    def handle_data(self, data):
        if self.skip_depth or not self.active:
            return
        if data.strip():
            self.cur.append(data)


def clean(text):
    text = html.unescape(text)
    text = (text.replace('—', ' -- ').replace('–', '-')
                .replace('’', "'").replace('‘', "'")
                .replace('“', '"').replace('”', '"')
                .replace('…', '...').replace(' ', ' ')
                .replace('→', ' to '))         # arrow -> "to"
    text = text.replace(' > ', ' over ').replace(' < ', ' under ')
    text = re.sub(r'#(\d)', r'number \1', text)      # "#79" -> "number 79"
    text = re.sub(r'\bvs\.?\b', 'versus', text)      # "vs." -> "versus"
    text = text.replace('/concepts/', 'our concepts page')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract(html_path):
    raw = open(html_path, encoding='utf-8').read()
    p = IssueExtractor()
    p.feed(raw)
    blocks = []
    for b in p.blocks:
        c = clean(b)
        if c and not DENY.search(c):
            blocks.append(c)
    hed = blocks[0] if blocks else 'The Sports Page'
    m = re.search(r'Issue No\.?\s*(\d+)', raw)
    m2 = re.search(r'Sunday Edition No\.?\s*(\d+)', raw)
    return {'blocks': blocks, 'hed': hed,
            'issue_no': m.group(1) if m else None,
            'sunday_no': m2.group(1) if m2 else None}


def build_narration(info):
    lead = ['The Sports Page. A statistical dispatch.']
    if info['sunday_no']:
        lead.append(f"Sunday Edition, number {info['sunday_no']}.")
    elif info['issue_no']:
        lead.append(f"Issue number {info['issue_no']}.")
    return '\n\n'.join(lead + info['blocks'])


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    src = args[0]
    text_only = '--text' in args
    out = next((a for a in args[1:] if not a.startswith('--')), None)

    info = extract(src)
    narration = build_narration(info)

    if text_only:
        print(narration)
        wc = len(narration.split())
        print(f"\n--- {len(info['blocks'])} blocks, ~{wc} words, "
              f"~{wc/150:.1f} min at 150 wpm ---", file=sys.stderr)
        return

    if out is None:
        slug = os.path.splitext(os.path.basename(src))[0]
        out = os.path.join(REPO, 'audio', f'{slug}.mp3')
    os.makedirs(os.path.dirname(out), exist_ok=True)

    sys.path.insert(0, HERE)
    from tts_render import render_to_mp3
    meta = {'title': info['hed'], 'artist': 'The Sports Page',
            'album': 'The Sports Page', 'genre': 'Podcast'}
    if info['issue_no']:
        meta['track'] = info['issue_no']
    dur = render_to_mp3(narration, out, meta)
    print(f"{out}  ({dur/60:.1f} min)")


if __name__ == '__main__':
    main()
