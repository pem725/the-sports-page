#!/usr/bin/env python3
"""BBWAA MVP and Cy Young votes, 2015-2025, from bbwaa.com (the voting body's own pages).
data/votes.csv: award, league, year, name, team, first-place votes, points, share (points / max points)."""
import re, html, csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
FIRST = {'mvp': 14, 'cy': 7}   # points for a first-place vote
rows = []
for y in range(2015, 2026):
    for lg in ('al', 'nl'):
        for aw in ('mvp', 'cy'):
            s = open(os.path.join(HERE, 'raw', f'bb_{y % 100:02d}-{lg}-{aw}.html'), encoding='utf-8', errors='ignore').read()
            t = s[s.find('<table'):s.find('</table>')]
            got = []
            for tr in re.findall(r'<tr.*?</tr>', t, re.S):
                cells = [html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]
                if len(cells) < 3 or not cells[-1].isdigit() or ',' not in cells[0]: continue
                name, team = [x.strip() for x in cells[0].rsplit(',', 1)]
                first = int(cells[1]) if cells[1].isdigit() else 0
                got.append(dict(award=aw, league=lg.upper(), year=y, name=name, team=team, first=first, points=int(cells[-1])))
            voters = sum(g['first'] for g in got)
            for g in got: g['share'] = g['points'] / (voters * FIRST[aw]); rows.append(g)
            print(y, lg, aw, 'candidates', len(got), 'voters', voters, 'top', got[0]['name'] if got else None)
w = csv.DictWriter(open(os.path.join(HERE, 'data', 'votes.csv'), 'w', newline=''), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
