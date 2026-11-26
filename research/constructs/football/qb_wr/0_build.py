#!/usr/bin/env python3
"""Quarterbacks and receivers, NFL regular seasons 2018-2026 (2026 to date). data/qb.csv, data/rec.csv

Counted from nflverse play-by-play by player id, then joined to PFR charting (via nflverse
pfr_advstats; pfr_id <-> gsis through players.csv) and Next Gen Stats (gsis id).

QB TRAPS handled here:
 - A dropback is qb_dropback == 1: pass attempts + sacks + scrambles. Rates use dropbacks or
   attempts as stated, never mixed.
 - Sacks are not pass attempts in the NFL; their yards are not passing yards.
 - Spikes are pass attempts and incompletions in the official line; removed here.
 - Scrambles are rushes in the box score but dropbacks here (passer_id covers them).
RECEIVER TRAPS: targets are pass attempts with a receiver named (sacks, throwaways with no target
and spikes are not targets); air yards count on every target, caught or not.
"""
import csv, gzip, os
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); FB = os.path.dirname(HERE)
pl = {r['gsis_id']: r for r in csv.DictReader(open(os.path.join(FB, 'data', 'raw', 'rb', 'players.csv')))}
pfr2g = {r['pfr_id']: g for g, r in pl.items() if r['pfr_id']}
Q = defaultdict(lambda: defaultdict(float)); R = defaultdict(lambda: defaultdict(float))
f0 = lambda v: float(v) if v not in (None, '', 'NA') else 0.0
for y in range(2018, 2027):
    fn = os.path.join(FB, 'data', 'raw', 'dl', f'pbp_{y}.csv.gz') if y < 2026 else os.path.join(HERE, 'raw', 'play_by_play_2026.csv.gz')
    with gzip.open(fn, 'rt') as f:
        for r in csv.DictReader(f):
            if r['season_type'] != 'REG' or r['qb_dropback'] != '1' or r['qb_spike'] == '1': continue
            qb = r['passer_id'] if r['passer_id'] not in ('', 'NA') else None
            if not qb: continue
            q = Q[(qb, y)]; q['db'] += 1; q['epa'] += f0(r['epa'])
            if r['sack'] == '1': q['sk'] += 1; q['sk_yds'] += f0(r['yards_gained']); continue
            if r['qb_scramble'] == '1': q['scr'] += 1; continue
            if r['pass_attempt'] != '1': continue
            q['att'] += 1; q['cmp'] += f0(r['complete_pass']); q['int'] += f0(r['interception']); q['td'] += f0(r['pass_touchdown'])
            q['yds'] += f0(r['passing_yards']) if r.get('passing_yards') not in (None, '', 'NA') else (f0(r['yards_gained']) if r['complete_pass'] == '1' else 0)
            q['fd'] += f0(r['first_down_pass'])
            rid = r['receiver_id'] if r['receiver_id'] not in ('', 'NA') else None
            if rid:
                q['air'] += f0(r['air_yards']); q['tgt_att'] += 1
                if r['complete_pass'] == '1': q['yac'] += f0(r['yards_after_catch'])
                c = R[(rid, y)]; c['tgt'] += 1; c['air'] += f0(r['air_yards']); c['rec'] += f0(r['complete_pass'])
                c['td'] += f0(r['pass_touchdown']); c['fd'] += f0(r['first_down_pass']); c['epa'] += f0(r['epa'])
                if r['complete_pass'] == '1': c['yds'] += f0(r['yards_gained']); c['yac'] += f0(r['yards_after_catch'])
    print(y, 'pbp', flush=True)
snaps = defaultdict(float)
for y in range(2018, 2027):
    fn = os.path.join(FB, 'data', 'raw', 'dl', f'snaps_{y}.csv') if y < 2026 else os.path.join(HERE, 'raw', 'snaps_2026.csv')
    for r in csv.DictReader(open(fn)):
        if r['game_type'] == 'REG' and r['pfr_player_id'] in pfr2g: snaps[(pfr2g[r['pfr_player_id']], y)] += f0(r['offense_snaps'])
def pfr(fn):
    out = {}
    for r in csv.DictReader(open(os.path.join(HERE, 'raw', fn))):
        if r['pfr_id'] in pfr2g: out[(pfr2g[r['pfr_id']], int(r['season']))] = r
    return out
padv, radv = pfr('advstats_season_pass.csv'), pfr('advstats_season_rec.csv')
def ngs(fn):
    out = {}
    with gzip.open(os.path.join(HERE, 'raw', fn), 'rt') as f:
        for r in csv.DictReader(f):
            if r['season_type'] == 'REG' and r['week'] == '0': out[(r['player_gsis_id'], int(r['season']))] = r
    return out
npass, nrec = ngs('ngs_passing.csv.gz'), ngs('ngs_receiving.csv.gz')
# 2026: PFR season passing charting not yet published. Approximate bad-throw % from the weekly file:
# 100 * weekly bad throws / (attempts * (1 - league throwaway rate in 2025)). Weekly sums can run a
# few percent under the season total (checked on 2025), so 2026 accuracy is slightly flattered.
s25 = [r for r in csv.DictReader(open(os.path.join(HERE, 'raw', 'advstats_season_pass.csv'))) if r['season'] == '2025']
TR25 = sum(float(r['throwaways'] or 0) for r in s25) / sum(float(r['pass_attempts']) for r in s25)
wk26 = defaultdict(float)
for r in csv.DictReader(open(os.path.join(HERE, 'raw', 'advstats_week_pass_2026.csv'))):
    if r['game_type'] == 'REG' and r['pfr_player_id'] in pfr2g: wk26[pfr2g[r['pfr_player_id']]] += float(r['passing_bad_throws'] or 0)
nan = float('nan')
def g(d, k):
    v = (d or {}).get(k); 
    try: return float(v)
    except (TypeError, ValueError): return nan
qrows = []
for (pid, y), q in Q.items():
    if q['db'] < 200 or q['att'] < 150: continue
    p = pl.get(pid, {}); a = padv.get((pid, y)); n = npass.get((pid, y))
    qrows.append(dict(gsis=pid, name=p.get('display_name'), year=y, db=q['db'], att=q['att'],
        comp=q['cmp'] / q['att'], adot=q['air'] / q['tgt_att'], yac=q['yac'] / max(q['cmp'], 1),
        td=q['td'] / q['att'], int=q['int'] / q['att'], sack=q['sk'] / q['db'], scr=q['scr'] / q['db'],
        fd=q['fd'] / q['att'],
        bad=g(a, 'bad_throw_pct') if y < 2026 else (100 * wk26[pid] / (q['att'] * (1 - TR25)) if pid in wk26 else nan), press=g(a, 'pressure_pct'), pocket=g(a, 'pocket_time'),
        throwaway=g(a, 'throwaways') / q['att'] if a else nan,
        ttt=g(n, 'avg_time_to_throw'), aggr=g(n, 'aggressiveness'), cpoe=g(n, 'completion_percentage_above_expectation'),
        # criteria (composites), kept out of the measurement model
        ypa=q['yds'] / q['att'], epa_db=q['epa'] / q['db'],
        anya=(q['yds'] + 20 * q['td'] - 45 * q['int'] + q['sk_yds']) / (q['att'] + q['sk']),
        yds=q['yds']))
rrows = []
for (pid, y), c in R.items():
    p = pl.get(pid, {}); pos = p.get('position', '')
    if pos not in ('WR', 'TE') or c['tgt'] < 50: continue
    a = radv.get((pid, y)); n = nrec.get((pid, y)); sn = snaps.get((pid, y), 0)
    rrows.append(dict(gsis=pid, name=p.get('display_name'), pos=pos, year=y, tgt=c['tgt'], snaps=sn,
        tps=c['tgt'] / sn if sn >= 200 else nan, catch=c['rec'] / c['tgt'], adot=c['air'] / c['tgt'],
        yac=c['yac'] / max(c['rec'], 1), td=c['td'] / c['tgt'], fd=c['fd'] / c['tgt'],
        drop=g(a, 'drop_percent'), brk=g(a, 'brk_tkl') / max(c['rec'], 1) if a else nan,
        sep=g(n, 'avg_separation'), cush=g(n, 'avg_cushion'), yacoe=g(n, 'avg_yac_above_expectation'),
        ypt=c['yds'] / c['tgt'], yps=c['yds'] / sn if sn >= 200 else nan, epa_t=c['epa'] / c['tgt'], yds=c['yds']))
for nm, rows in (('qb', qrows), ('rec', rrows)):
    w = csv.DictWriter(open(os.path.join(HERE, 'data', nm + '.csv'), 'w', newline=''), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(nm, len(rows))
