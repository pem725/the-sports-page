#!/usr/bin/env python3
"""Pull the analytic core of every published regular issue (not Sunday Editions):
headline, deck, the Reader's-Contract question/answer lines, the methods box, and the first
paragraphs if there is no methods box. Writes cores.jsonl (one issue per line), ~400 words each."""
import re, json, html, os, glob
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
idx = open(os.path.join(ROOT, 'index.html')).read()
num = {}
for m in re.finditer(r'class="issue-num">([^<]+)<.*?href="published/([^"]+)"', idx, re.S):
    num[m.group(2)] = m.group(1).strip()
from html.parser import HTMLParser
KEYS = re.compile(r'how (we|this was) (did|measured|know)|notes (&|and) sources|methods?|the math|caveats|sources|how we did it', re.I)
class M(HTMLParser):
    """Collect text inside div.math / div.methods / div.box, and inside sections whose heading
    names the method (Notes & sources, How this was measured, ...) until the next h2."""
    def __init__(s): super().__init__(); s.depth = 0; s.buf = []; s.head = None; s.insec = False
    def handle_starttag(s, t, a):
        c = dict(a).get('class', '') or ''
        if t == 'div' and (s.depth or any(k in c.split() for k in ('math', 'methods', 'box'))): s.depth += 1
        if t in ('h2', 'h3'): s.head = t; s.htxt = ''
    def handle_endtag(s, t):
        if t == 'div' and s.depth: s.depth -= 1
        if t in ('h2', 'h3') and s.head == t:
            s.head = None
            if KEYS.search(s.htxt): s.insec = True
            elif t == 'h2': s.insec = False
    def handle_data(s, d):
        if s.head: s.htxt += d
        if s.depth or s.insec: s.buf.append(d)
def methods_text(h):
    m = M(); m.feed(h); return re.sub(r'\s+', ' ', ' '.join(m.buf)).strip()
def text(s): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()
out = []
for p in sorted(glob.glob(os.path.join(ROOT, 'published', '*.html'))):
    f = os.path.basename(p)
    if f.startswith('sunday-') or f not in num: continue
    s = open(p, encoding='utf-8').read()
    s = re.sub(r'<(script|style|svg)[^>]*>.*?</\1>', ' ', s, flags=re.S)
    hed = text((re.search(r'<h[12] class="hed"[^>]*>(.*?)</h[12]>', s, re.S) or re.search(r'<title>(.*?)</title>', s, re.S)).group(1))
    deck = text((re.search(r'class="deck"[^>]*>(.*?)</div>', s, re.S) or re.search(r'(?!)', '')) .group(1)) if re.search(r'class="deck"', s) else ''
    qa = ' '.join(text(m) for m in re.findall(r'<p><strong>The (?:question|answer):</strong>(.*?)</p>', s, re.S))
    meth = methods_text(s)
    paras = [text(x) for x in re.findall(r'<p>(.*?)</p>', s, re.S)][:4]
    box = bool(meth)
    words = (' '.join(paras).split())[:150] + ['|| METHODS:'] + (meth.split())[:300]
    out.append(dict(issue=num[f], file=f, headline=hed, deck=deck[:600], qa=qa[:600], methods=' '.join(words), has_box=bool(box)))
with open(os.path.join(os.path.dirname(__file__), 'cores.jsonl'), 'w') as w:
    for o in out: w.write(json.dumps(o) + '\n')
print(len(out), 'issues;', sum(o['has_box'] for o in out), 'with a methods box;', 'words ~', sum(len((o['methods'] + o['deck'] + o['qa']).split()) for o in out))
