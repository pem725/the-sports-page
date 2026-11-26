#!/usr/bin/env python3
"""Defensive linemen and edge rushers, 2018-2025: per-100-snap rates. data/dl.csv

Sources: nflverse play-by-play (sacks, QB hits, tackles for loss, tackles by play type, forced
fumbles), nflverse snap counts (defensive snaps, the denominator), PFR advanced defense via nflverse
(pressures, hurries, knockdowns, batted passes, missed tackles). Players linked gsis <-> pfr_id with
nflverse players.csv.

TRAP: in the play-by-play, most sacks also carry tackle-for-loss credit (2024: 1,076 of 1,314).
Raw TFL therefore contains sacks. `tfl_run` counts TFL credits on NON-sack plays only.
"""
import csv, gzip, os
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, 'data', 'raw')
pl = {r['gsis_id']: r for r in csv.DictReader(open(os.path.join(RAW, 'rb', 'players.csv')))}
pfr2g = {r['pfr_id']: g for g, r in pl.items() if r['pfr_id']}
S = defaultdict(lambda: defaultdict(float))
def ids(r, keys): return [r[k] for k in keys if r.get(k) not in (None, '', 'NA')]
TK = ['solo_tackle_1_player_id', 'solo_tackle_2_player_id', 'assist_tackle_1_player_id', 'assist_tackle_2_player_id',
      'assist_tackle_3_player_id', 'assist_tackle_4_player_id', 'tackle_with_assist_1_player_id', 'tackle_with_assist_2_player_id']
for y in range(2018, 2026):
    with gzip.open(os.path.join(RAW, 'dl', f'pbp_{y}.csv.gz'), 'rt') as f:
        for r in csv.DictReader(f):
            if r['season_type'] != 'REG' or r['play_type'] not in ('run', 'pass'): continue
            sack = r['sack'] == '1'
            for g in ids(r, ['sack_player_id']): S[(g, y)]['sacks'] += 1
            for g in ids(r, ['half_sack_1_player_id', 'half_sack_2_player_id']): S[(g, y)]['sacks'] += .5
            for g in ids(r, ['qb_hit_1_player_id', 'qb_hit_2_player_id']): S[(g, y)]['qbhit'] += 1
            for g in ids(r, ['tackle_for_loss_1_player_id', 'tackle_for_loss_2_player_id']):
                S[(g, y)]['tfl_all'] += 1
                if not sack: S[(g, y)]['tfl_run'] += 1
            if not sack:
                for g in set(ids(r, TK)): S[(g, y)]['tk_run' if r['play_type'] == 'run' else 'tk_pass'] += 1
            for g in ids(r, ['forced_fumble_player_1_player_id', 'forced_fumble_player_2_player_id']): S[(g, y)]['ff'] += 1
            for g in ids(r, ['pass_defense_1_player_id', 'pass_defense_2_player_id']): S[(g, y)]['pd'] += 1
    print(y, 'pbp done', flush=True)
snaps = defaultdict(float)
for y in range(2018, 2026):
    for r in csv.DictReader(open(os.path.join(RAW, 'dl', f'snaps_{y}.csv'))):
        if r['game_type'] == 'REG' and r['pfr_player_id'] in pfr2g: snaps[(pfr2g[r['pfr_player_id']], y)] += float(r['defense_snaps'] or 0)
adv = {}
for r in csv.DictReader(open(os.path.join(RAW, 'dl', 'advstats_season_def.csv'))):
    if r['pfr_id'] in pfr2g: adv[(pfr2g[r['pfr_id']], int(r['season']))] = r
# position: PFF's role label (ED = edge, DI = interior) describes what a player does; nflverse's
# `position` is his CURRENT label (Garrett and Hendrickson are now 'LB'). Fall back to PFR's season label.
PFF = {'ED': 'edge', 'DI': 'interior'}
PFRPOS = {'DE': 'edge', 'LDE': 'edge', 'RDE': 'edge', 'OLB': 'edge', 'LOLB': 'edge', 'ROLB': 'edge',
          'DT': 'interior', 'LDT': 'interior', 'RDT': 'interior', 'NT': 'interior', 'DL': 'interior'}
out = []
for (g, y), n in snaps.items():
    p = pl.get(g, {}); a = adv.get((g, y))
    grp = PFF.get(p.get('pff_position', '')) or (PFRPOS.get(a['pos']) if a else None)
    if not grp or n < 300 or not a: continue
    s = S[(g, y)]; per = lambda v: 100 * v / n
    num = lambda k: float(a[k]) if a.get(k) not in (None, '', 'NA') else float('nan')
    out.append(dict(gsis=g, name=p.get('display_name'), pos=p.get('pff_position') or (a or {}).get('pos'), grp=grp, year=y, snaps=n,
        prss=per(num('prss')), hrry=per(num('hrry')), qbkd=per(num('qbkd')), bats=per(num('bats')),
        sacks=per(s['sacks']), qbhit=per(s['qbhit']), tfl_run=per(s['tfl_run']), tfl_all=per(s['tfl_all']),
        tk_run=per(s['tk_run']), tk_pass=per(s['tk_pass']), ff=per(s['ff']), pd=per(s['pd']),
        mtkl_pct=num('m_tkl_percent')))
w = csv.DictWriter(open(os.path.join(HERE, 'data', 'dl.csv'), 'w', newline=''), fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print('player-seasons', len(out), ' edge', sum(o['grp'] == 'edge' for o in out), ' interior', sum(o['grp'] == 'interior' for o in out))
