#!/usr/bin/env python3
"""Second feed for What Repeats parts 2 and 5: ESPN season stats for every QB and WR in our data.
Recomputes interception-rate and TD-rate repeat correlations from ESPN alone (same player-seasons).
Writes series/espn_qb.csv, series/espn_wr.csv and prints the comparison."""
import csv, json, os, urllib.request, concurrent.futures as cf, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, '..', 'data')
pl = {r['gsis_id']: r['espn_id'] for r in csv.DictReader(open(os.path.join(HERE, '..', '..', 'data', 'raw', 'rb', 'players.csv'))) if r['espn_id']}
def espn(eid):
    u = f"https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{eid}/stats"
    try: d = json.load(urllib.request.urlopen(u, timeout=30))
    except Exception: return {}
    out = {}
    for c in d.get('categories', []):
        if c['name'] in ('passing', 'receiving'):
            L = c['labels']
            for s in c['statistics']:
                y = s['season']['year']; num = lambda k: float(s['stats'][L.index(k)].replace(',', '')) if s['stats'][L.index(k)] not in ('-', '') else 0.0
                if c['name'] == 'passing': out.setdefault(y, {}).update(att=num('ATT'), int=num('INT'), td=num('TD'))
                else: out.setdefault(y, {}).update(tgt=num('TGTS'), rtd=num('TD'), rec=num('REC'), ryds=num('YDS'))
    return out
def ci(r, n): z = math.atanh(r); s = 1 / math.sqrt(n - 3); return round(math.tanh(z - 1.96 * s), 2), round(math.tanh(z + 1.96 * s), 2)
def run(fn, key_rate, ours_cols, out_name, min_key):
    R = list(csv.DictReader(open(os.path.join(D, fn))))
    ids = sorted({r['gsis'] for r in R if r['gsis'] in pl})
    with cf.ThreadPoolExecutor(8) as ex: E = dict(zip(ids, ex.map(lambda g: espn(pl[g]), ids)))
    have = {(r['gsis'], int(r['year'])) for r in R}
    rows = []
    for g, e in E.items():
        for y, s in e.items():
            if (g, y) in have and s.get(min_key, 0) > 0: rows.append(dict(gsis=g, year=y, **s))
    w = csv.DictWriter(open(os.path.join(HERE, out_name), 'w', newline=''), fieldnames=sorted({k for r in rows for k in r})); w.writeheader(); w.writerows(rows)
    by = {(r['gsis'], r['year']): r for r in rows}
    for nm, f in key_rate.items():
        P = [(f(a), f(by[(g, y + 1)])) for (g, y), a in by.items() if (g, y + 1) in by and y + 1 <= 2025]
        r = st.correlation([p[0] for p in P], [p[1] for p in P]); print(f'  ESPN {nm}: r = {r:.2f} {ci(r, len(P))}  pairs {len(P)}')
    return by
print('QBs')
qb = run('qb.csv', {'interceptions per attempt': lambda s: s['int'] / s['att'], 'TD passes per attempt': lambda s: s['td'] / s['att']}, None, 'espn_qb.csv', 'att')
print('WRs')
wr = run('rec.csv', {'TD catches per target': lambda s: s['rtd'] / s['tgt'], 'catches per target': lambda s: s['rec'] / s['tgt']}, None, 'espn_wr.csv', 'tgt')
