#!/usr/bin/env python3
"""Scorecard No. 3 tables, as HTML fragments in house style (stdout).
    python3 tables3.py            # real: grade-rivalry-2026.json + newest weekly file
    python3 tables3.py --fake     # test on the fake grade
Two tables: (1) our rivalry-weekend playoff calls vs the committee's new ranking;
(2) the committee's top 12 vs our bowl-corrected math (same as No. 1 and No. 2)."""
import json, os, sys
H = os.path.dirname(os.path.abspath(__file__))
g = json.load(open(os.path.join(H, 'grade-rivalry-2026' + ('-FAKE' if '--fake' in sys.argv else '') + '.json')))
wk = sorted(f for f in os.listdir(H) if f.startswith('weekly-') and f.endswith('.json'))[-1]
W = json.load(open(os.path.join(H, wk)))
pct = lambda p: '&lt;1' if p < .005 else ('&gt;99' if p > .995 else f'{round(100 * p):d}')
TH = 'style="font-family:\'Roboto Mono\',monospace;font-size:.68rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);text-align:{a};padding:.3rem .4rem;border-bottom:2px solid var(--ink)"'
TD = 'style="padding:.32rem .4rem;border-bottom:1px solid var(--div);text-align:{a};{x}"'
def table(head, rows, aligns):
    h = ''.join(f'<th {TH.format(a=a)}>{c}</th>' for c, a in zip(head, aligns))
    b = ''.join('<tr>' + ''.join(f'<td {TD.format(a=a, x=x)}>{c}</td>' for (c, x), a in zip(r, aligns)) + '</tr>' for r in rows)
    return f'<table style="width:100%;border-collapse:collapse;font-size:.88rem;margin:1rem 0">\n<thead><tr>{h}</tr></thead>\n<tbody>{b}</tbody></table>'
calls = [c for c in g['calls'] if c['before_in'] >= .05][:16]
rows = []
for c in calls:
    ok = c['in_agree']
    rows.append([(c['team'], 'font-weight:600'), ('won' if c['won'] else 'lost', ''), (pct(c['before_in']), ''),
                 (pct(c['after_in']), 'font-weight:600'), (str(c['cfp'] or 'out'), ''),
                 ('agree' if ok else 'SPLIT', 'color:var(--steel)' if ok else 'color:var(--rust);font-weight:700')])
print('<!-- table 1: our calls, graded -->')
print(table(['team', 'result', 'playoff chance before', 'after the result', 'committee rank', ''], rows, ['left', 'left', 'right', 'right', 'right', 'left']))
top = [r for r in W['rows'] if r['cfp'] and r['cfp'] <= 12]
rows2 = [[(str(r['cfp']), 'font-weight:600'), (r['team'], ''), (r['rec'], ''), (str(r['math']), ''),
          (('+' if r['gap'] > 0 else '') + str(r['gap']) if r['gap'] else 'same', 'color:var(--rust)' if abs(r['gap']) >= 3 else '')] for r in top]
print('<!-- table 2: committee top 12 vs our math -->')
print(table(['CFP', 'team', 'record', 'our math', 'gap'], rows2, ['right', 'left', 'left', 'right', 'right']))
