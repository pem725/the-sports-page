#!/usr/bin/env python3
"""Running backs, college and NFL, 2014-2025 (and 2026 to date for the NFL).

data/rb_cfb.csv   FBS running backs, one row per season with 100+ carries (CFBD)
data/rb_nfl.csv   NFL running backs, one row per regular season with 100+ carries (nflverse + NGS)
data/rb_link.csv  the same back in both leagues: pooled college carries vs pooled NFL carries.
                  Linked by ESPN athlete id (CFBD playerId == nflverse players.espn_id).

A running back's carries never include sacks in either league, so the definitional trap of the
team-level comparison does not apply here.
"""
import csv, gzip, json, os, math
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, 'data', 'raw', 'rb')
MIN = 100

# ---------- college ----------
P = defaultdict(lambda: defaultdict(float)); meta = {}
for y in range(2014, 2026):
    for cat in ('rushing', 'receiving', 'fumbles'):
        for x in json.load(open(os.path.join(RAW, f'cfb_{cat}_{y}.json'))):
            k = (x['playerId'], y)
            try: v = float(x['stat'])
            except ValueError: continue
            P[k][cat + '_' + x['statType']] = v
            meta[k] = (x['player'], x['position'], x['team'], x['conference'])
cfb = []
for (pid, y), s in P.items():
    name, pos, team, conf = meta[(pid, y)]
    car = s.get('rushing_CAR', 0)
    if pos not in ('RB', '?') or car < 1: continue
    rec = s.get('receiving_REC', 0)
    cfb.append(dict(pid=pid, name=name, year=y, team=team, conf=conf, car=car, yds=s.get('rushing_YDS', 0),
        rtd=s.get('rushing_TD', 0), long=s.get('rushing_LONG', 0), rec=rec, recyds=s.get('receiving_YDS', 0),
        rectd=s.get('receiving_TD', 0), fum=s.get('fumbles_FUM', float('nan')) if y >= 2016 else float('nan')))
# ---------- NFL ----------
ngs = {}
with gzip.open(os.path.join(RAW, 'ngs_rushing.csv.gz'), 'rt') as f:
    for r in csv.DictReader(f):
        if r['season_type'] == 'REG' and r['week'] == '0': ngs[(r['player_gsis_id'], int(r['season']))] = r
nfl = []
files = [(y, os.path.join(HERE, 'data', 'raw', f'reg{y}.csv')) for y in range(2014, 2026)] + [(2026, os.path.join(RAW, 'stats_player_reg_2026.csv'))]
for y, fn in files:
    for r in csv.DictReader(open(fn)):
        pos = r.get('position') or ''
        f = lambda k: float(r.get(k) or 0)
        if pos != 'RB' or f('carries') < (MIN if y < 2026 else 60): continue
        g = ngs.get((r['player_id'], y), {})
        nf = lambda k: float(g[k]) if g.get(k) not in (None, '', 'NA') else float('nan')
        nfl.append(dict(gsis=r['player_id'], name=r['player_display_name'], year=y, team=r.get('recent_team') or r.get('team', ''),
            games=f('games'), car=f('carries'), yds=f('rushing_yards'), rtd=f('rushing_tds'), fd=f('rushing_first_downs'),
            r10=f('rushing_10'), r20=f('rushing_20'), epa=f('rushing_epa'), fum=f('rushing_fumbles') + f('receiving_fumbles'),
            tgt=f('targets'), rec=f('receptions'), recyds=f('receiving_yards'), rectd=f('receiving_tds'), yac=f('receiving_yards_after_catch'),
            ryoe=nf('rush_yards_over_expected_per_att'), roe_pct=nf('rush_pct_over_expected'), eff=nf('efficiency'),
            box8=nf('percent_attempts_gte_eight_defenders'), ttl=nf('avg_time_to_los')))
# ---------- link ----------
esp = {}
for r in csv.DictReader(open(os.path.join(RAW, 'players.csv'))):
    if r['espn_id']: esp[r['gsis_id']] = (r['espn_id'], r['college_name'], r['draft_round'], r['rookie_season'])
C = defaultdict(lambda: [0, 0, 0, ''])
for r in cfb: c = C[r['pid']]; c[0] += r['car']; c[1] += r['yds']; c[2] += 1; c[3] = r['name']
N = defaultdict(lambda: [0, 0, 0, '', ''])
ALLN = set(r['gsis'] for r in nfl)   # backs who had at least one 100-carry NFL season
for y in range(2014, 2026):
    for r in csv.DictReader(open(os.path.join(HERE, 'data', 'raw', f'reg{y}.csv'))):
        if r['player_id'] not in ALLN or r.get('position') != 'RB' or not float(r.get('carries') or 0): continue
        n = N[r['player_id']]; n[0] += float(r['carries']); n[1] += float(r['rushing_yards'] or 0); n[2] += 1; n[3] = r['player_display_name']
link = []
for g, n in N.items():
    if g not in esp: continue
    e = esp[g]
    if e[0] in C:
        c = C[e[0]]
        link.append(dict(gsis=g, espn=e[0], name=n[3], college=e[1], draft_round=e[2], rookie=e[3],
            cfb_car=c[0], cfb_ypc=c[1] / c[0], cfb_seasons=c[2], nfl_car=n[0], nfl_ypc=n[1] / n[0], nfl_seasons=n[2]))
# fallback: CFBD uses its own ids for older players, so join on name plus college
import re, unicodedata
def norm(x): x = unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode().lower(); return re.sub(r'[^a-z]', '', re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', x))
ALIAS = {'texaselpaso': 'utep', 'miamifl': 'miami', 'centralflorida': 'ucf', 'brighamyoung': 'byu', 'louisianastateuniversity': 'lsu',
         'southerncalifornia': 'usc', 'mississippi': 'olemiss', 'southernmethodist': 'smu', 'texaschristian': 'tcu'}
team_of = defaultdict(set); byname = defaultdict(set)
for r in cfb: team_of[r['pid']].add(norm(r['team'])); byname[norm(r['name'])].add(r['pid'])
done = {r['gsis'] for r in link}
for g, n in N.items():
    if g in done or g not in esp: continue
    e = esp[g]; colleges = {ALIAS.get(norm(c), norm(c)) for c in e[1].split(';')}
    cands = [pid for pid in byname.get(norm(n[3]), ()) if team_of[pid] & colleges or len(byname[norm(n[3])]) == 1 and any(c in t or t in c for t in team_of[pid] for c in colleges)]
    if len(cands) != 1: continue
    c = C[cands[0]]
    link.append(dict(gsis=g, espn=e[0], name=n[3], college=e[1], draft_round=e[2], rookie=e[3],
        cfb_car=c[0], cfb_ypc=c[1] / c[0], cfb_seasons=c[2], nfl_car=n[0], nfl_ypc=n[1] / n[0], nfl_seasons=n[2]))
cfb = [r for r in cfb if r['car'] >= MIN]
for nm, rows in (('rb_cfb', cfb), ('rb_nfl', nfl), ('rb_link', link)):
    with open(os.path.join(HERE, 'data', nm + '.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(nm, len(rows))
