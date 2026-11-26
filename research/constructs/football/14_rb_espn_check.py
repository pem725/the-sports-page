#!/usr/bin/env python3
"""Second feed for the same-back comparison: ESPN career rushing (college window 2014+, NFL through 2025)."""
import csv, json, urllib.request, concurrent.futures as cf, os
HERE = os.path.dirname(os.path.abspath(__file__))
L = [r for r in csv.DictReader(open(os.path.join(HERE, 'data', 'rb_link.csv'))) if float(r['cfb_car']) >= 200 and float(r['nfl_car']) >= 200]
def tot(lg, eid, y0, y1):
    u = f"https://site.web.api.espn.com/apis/common/v3/sports/football/{lg}/athletes/{eid}/stats"
    try: d = json.load(urllib.request.urlopen(u, timeout=30))
    except Exception: return None
    for c in d.get('categories', []):
        if c['name'] == 'rushing':
            car = yds = 0
            i_car, i_yds = c['labels'].index('CAR'), c['labels'].index('YDS')
            num = lambda v: float(v.replace(',', '')) if v not in ('-', '') else 0.0
            for s in c['statistics']:
                yr = s['season']['year']
                if y0 <= yr <= y1:
                    car += num(s['stats'][i_car]); yds += num(s['stats'][i_yds])
            return car, yds
def one(r):
    return r, tot('college-football', r['espn'], 2014, 2025), tot('nfl', r['espn'], 2014, 2025)
out = []
with cf.ThreadPoolExecutor(8) as ex:
    for r, c, n in ex.map(one, L):
        out.append(dict(name=r['name'], ours_cfb=float(r['cfb_ypc']), ours_nfl=float(r['nfl_ypc']),
            espn_cfb=c[1]/c[0] if c and c[0] else '', espn_nfl=n[1]/n[0] if n and n[0] else '', espn_cfb_car=c[0] if c else '', espn_nfl_car=n[0] if n else ''))
w = csv.DictWriter(open(os.path.join(HERE, 'data', 'rb_link_espn.csv'), 'w', newline=''), fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
ok = [o for o in out if o['espn_cfb'] != '' and o['espn_nfl'] != '']
print('backs', len(out), 'with ESPN both leagues', len(ok))
big = [o for o in ok if abs(o['espn_cfb'] - o['ours_cfb']) > .15 or abs(o['espn_nfl'] - o['ours_nfl']) > .15]
for o in big: print('DIFF', o['name'], round(o['ours_cfb'], 2), round(o['espn_cfb'], 2), '|', round(o['ours_nfl'], 2), round(o['espn_nfl'], 2))
import statistics as st
dr = [o['espn_cfb'] - o['espn_nfl'] for o in ok]
print('ESPN: college', round(st.mean(o['espn_cfb'] for o in ok), 2), 'NFL', round(st.mean(o['espn_nfl'] for o in ok), 2), 'drop', round(st.mean(dr), 2), 'dropped', sum(x > 0 for x in dr), 'of', len(ok))
x = [o['espn_cfb'] for o in ok]; y = [o['espn_nfl'] for o in ok]; print('ESPN r =', round(st.correlation(x, y), 2))
