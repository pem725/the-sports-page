#!/usr/bin/env python3
"""Build the hitter data sets from the MLB Stats API (no key).

  data/players.csv  2021-2025, each player's seasons of 300+ PA pooled; split A/B by a hash
                    of the player id (A = discover, B = confirm)
  data/seasons.csv  the same player-seasons, one row each (for year-to-year stability)
  data/old.csv      2016-2019, pooled the same way (the fresh sample; players who also
                    appear in 2021-2025 are dropped in 3_fresh_sample.R)

Every variable is a PRIMITIVE, never a composite: AVG, OBP, SLG, OPS and BABIP are sums
and ratios of these, and putting a sum next to its parts builds the correlation in by
arithmetic. Counts per plate appearance get a square root, which steadies the variance of
a rate.
"""
import hashlib, json, math, os, urllib.request, csv
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
URL = ("https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&season={y}"
       "&sportId=1&limit=3000&playerPool=ALL")
K = ['hits', 'doubles', 'triples', 'homeRuns', 'baseOnBalls', 'intentionalWalks', 'hitByPitch', 'strikeOuts',
     'stolenBases', 'caughtStealing', 'groundIntoDoublePlay', 'sacBunts', 'sacFlies', 'numberOfPitches',
     'groundOuts', 'airOuts', 'plateAppearances', 'runs', 'rbi']
MIN_PA = 300


def season(y):
    d = json.load(urllib.request.urlopen(URL.format(y=y), timeout=60))
    return [s for s in d['stats'][0]['splits'] if s['stat']['plateAppearances'] >= MIN_PA]


def variables(t):
    pa = t['plateAppearances']
    s1 = t['hits'] - t['doubles'] - t['triples'] - t['homeRuns']
    onbase = s1 + t['baseOnBalls'] + t['hitByPitch']
    r = lambda x: math.sqrt(x / pa)
    return {'single': r(s1), 'double': r(t['doubles']), 'triple': r(t['triples']), 'hr': r(t['homeRuns']),
            'ubb': r(t['baseOnBalls'] - t['intentionalWalks']), 'ibb': r(t['intentionalWalks']),
            'hbp': r(t['hitByPitch']), 'so': r(t['strikeOuts']),
            'sbatt': math.sqrt((t['stolenBases'] + t['caughtStealing']) / max(onbase, 1)),  # tries per time on base
            'gidp': r(t['groundIntoDoublePlay']), 'sac': r(t['sacBunts']), 'sf': r(t['sacFlies']),
            'pitches': t['numberOfPitches'] / pa,
            'goao': math.log((t['groundOuts'] + 1) / (t['airOuts'] + 1)),
            'runs': r(t['runs']), 'rbi': r(t['rbi'])}


def pooled(years):
    P, n = defaultdict(lambda: defaultdict(int)), {}
    rows = []
    for y in years:
        for s in season(y):
            pid = s['player']['id']
            for k in K:
                P[pid][k] += s['stat'][k]
            P[pid]['n'] += 1
            n[pid] = s['player']['fullName']
            rows.append({'pid': pid, 'year': y, **variables(s['stat'])})
    return P, n, rows


def write(name, rows):
    with open(os.path.join(HERE, 'data', name), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
    P, names, seasons = pooled(range(2021, 2026))
    write('seasons.csv', seasons)
    write('players.csv', [{'pid': p, 'name': names[p],
                           'half': 'A' if int(hashlib.md5(str(p).encode()).hexdigest(), 16) % 2 == 0 else 'B',
                           'seasons': t['n'], 'pa': t['plateAppearances'], **variables(t)} for p, t in P.items()])
    P, _, _ = pooled(range(2016, 2020))
    write('old.csv', [{'pid': p, **variables(t)} for p, t in P.items()])
    print('built data/players.csv, seasons.csv, old.csv')
