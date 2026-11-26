#!/usr/bin/env python3
"""AP All-Pro QB, WR, TE 2018-2025 from Wikipedia "YYYY All-Pro Team" wikitext (ONE source). data/allpro.csv"""
import json, re, csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
POS = {'Quarterback': 'QB', 'Wide receiver': 'WR', 'Tight end': 'TE'}
rows = []
for y in range(2018, 2026):
    t = json.load(open(os.path.join(HERE, 'raw', f'ap_{y}.json')))['parse']['wikitext']
    for label, pos in POS.items():
        m = re.search(r'\|\s*\[\[' + label + r'(?:\|[^\]]*)?\]\]\s*\n(.*?)\n\|-', t, re.S)
        if not m: print(y, pos, 'NOT FOUND'); continue
        cells = [c for c in re.split(r'\n\|', '\n' + m.group(1)) if c.strip()]
        for team, cell in zip(('1', '2'), cells[:2]):
            for ent in re.split(r'<br\s*/?>', cell, flags=re.I):
                nm = re.search(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', ent); tags = re.search(r'\(([^)]*)\)\s*$', ent.strip())
                if not nm or not tags: continue
                tg = [x.strip() for x in tags.group(1).split(',')]
                ap = (any(re.fullmatch(r'AP-?t?', x) for x in tg) and team == '1') or (any(re.fullmatch(r'AP-2t?', x) for x in tg) and team == '2')   # 't' = tied
                if ap:
                    name = nm.group(2) or nm.group(1); name = re.sub(r'\s*\(.*\)$', '', name)
                    rows.append(dict(year=y, pos=pos, team=team, name=name))
w = csv.DictWriter(open(os.path.join(HERE, 'data', 'allpro.csv'), 'w', newline=''), fieldnames=['year', 'pos', 'team', 'name']); w.writeheader(); w.writerows(rows)
for y in range(2018, 2026): print(y, [(r['pos'], r['team'], r['name']) for r in rows if r['year'] == y])
