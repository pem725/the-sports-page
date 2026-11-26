#!/usr/bin/env python3
"""Player-seasons 2015-2025 for hitters (300+ PA) and pitchers, MLB Stats API (box score) merged with
Baseball Savant (tracking) on MLBAM id. Writes data/hitters.csv and data/pitchers.csv.

Primitives go in the measurement model; composites (AVG, OBP, SLG, OPS, ERA, barrel %, hard-hit %)
are carried as CRITERIA only. Counts per PA/BF are square-rooted (steadies a rate's variance),
as in ../baseball-hitting/."""
import csv, json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
MLB = os.path.join(HERE, '..', 'baseball-hitting', 'data', 'raw')
def sv(kind, y):
    out = {}
    for r in csv.DictReader(open(os.path.join(HERE, 'raw', f'sv_{kind}_{y}.csv'), encoding='utf-8-sig')):
        out[int(r['player_id'])] = r
    return out
f = lambda r, k: float(r[k]) if r.get(k) not in (None, '', 'null') else float('nan')
H, P = [], []
for y in range(2015, 2026):
    if y == 2020: pass   # 60-game season: thresholds scaled below
    sc = 60 / 162 if y == 2020 else 1.0
    sb, sp = sv('bat', y), sv('pit', y)
    for s in json.load(open(os.path.join(MLB, f'h{y}.json')))['stats'][0]['splits']:
        t = s['stat']; pa = t['plateAppearances']
        if pa < 300 * sc: continue
        pid = s['player']['id']; v = sb.get(pid, {})
        s1 = t['hits'] - t['doubles'] - t['triples'] - t['homeRuns']; ob = s1 + t['baseOnBalls'] + t['hitByPitch']
        r = lambda x: math.sqrt(x / pa)
        H.append(dict(pid=pid, name=s['player']['fullName'], year=y, pa=pa,
            single=r(s1), double=r(t['doubles']), triple=r(t['triples']), hr=r(t['homeRuns']),
            ubb=r(t['baseOnBalls'] - t['intentionalWalks']), ibb=r(t['intentionalWalks']), hbp=r(t['hitByPitch']),
            so=r(t['strikeOuts']), sbatt=math.sqrt((t['stolenBases'] + t['caughtStealing']) / max(ob, 1)),
            gidp=r(t['groundIntoDoublePlay']), sac=r(t['sacBunts']), pitches=t['numberOfPitches'] / pa,
            goao=math.log((t['groundOuts'] + 1) / (t['airOuts'] + 1)),
            ev=f(v, 'exit_velocity_avg'), la=f(v, 'launch_angle_avg'), chase=f(v, 'oz_swing_percent'),
            zswing=f(v, 'z_swing_percent'), whiff=f(v, 'whiff_percent'), sprint=f(v, 'sprint_speed'),
            barrel=f(v, 'barrel_batted_rate'), hardhit=f(v, 'hard_hit_percent'),
            # criteria (composites and volume)
            avg=float(t['avg']), obp=float(t['obp']), slg=float(t['slg']), ops=float(t['ops']),
            hr_n=t['homeRuns'], rbi_n=t['rbi'], runs_n=t['runs'], hits_n=t['hits'], sb_n=t['stolenBases']))
    for s in json.load(open(os.path.join(MLB, f'p{y}.json')))['stats'][0]['splits']:
        t = s['stat']; bf = t['battersFaced']; ip = float(t['inningsPitched'].split('.')[0]) + int(t['inningsPitched'].split('.')[1]) / 3 if '.' in t['inningsPitched'] else float(t['inningsPitched'])
        g, gs = t['gamesPitched'], t['gamesStarted']
        role = 'SP' if gs >= g / 2 and ip >= 100 * sc else ('RP' if gs <= 2 and ip >= 40 * sc else None)
        if not role: continue
        pid = s['player']['id']; v = sp.get(pid, {})
        bip = bf - t['strikeOuts'] - t['baseOnBalls'] - t['hitByPitch'] - t['homeRuns']
        r = lambda x: math.sqrt(x / bf)
        P.append(dict(pid=pid, name=s['player']['fullName'], year=y, role=role, bf=bf, ip=round(ip, 1), gs=gs,
            so=r(t['strikeOuts']), ubb=r(t['baseOnBalls'] - t['intentionalWalks']), hbp=r(t['hitByPitch']),
            hr=r(t['homeRuns']), wp=r(t['wildPitches']), hbip=(t['hits'] - t['homeRuns']) / max(bip, 1),
            goao=math.log((t['groundOuts'] + 1) / (t['airOuts'] + 1)),
            velo=f(v, 'fastball_avg_speed'), whiff=f(v, 'whiff_percent'), chase=f(v, 'oz_swing_percent'),
            zswing=f(v, 'z_swing_percent'), ev=f(v, 'exit_velocity_avg'), gb=f(v, 'groundballs_percent'),
            barrel=f(v, 'barrel_batted_rate'),
            era=float(t['era']) if t['era'] not in ('-.--', '') else float('nan'), so_n=t['strikeOuts'], w_n=t['wins'], sv_n=t['saves']))
for nm, rows in (('hitters', H), ('pitchers', P)):
    w = csv.DictWriter(open(os.path.join(HERE, 'data', nm + '.csv'), 'w', newline=''), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(nm, len(rows), ' missing Savant:', sum(math.isnan(r['ev'] if 'ev' in r else 0) for r in rows))
print('SP', sum(p['role'] == 'SP' for p in P), 'RP', sum(p['role'] == 'RP' for p in P))
