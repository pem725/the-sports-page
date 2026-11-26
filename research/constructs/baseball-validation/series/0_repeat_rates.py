#!/usr/bin/env python3
"""What Repeats, Parts 1 and 3: same player, next season, for hitters, starters and relievers.
r with a 95% interval (Fisher z). Pairs touching 2020 are dropped (60-game season), the same rule
as ../8_reliability_chart.py. Writes series/repeat_rates.json (aggregates only; no per-player data)."""
import csv, json, math, os, statistics as st
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def nextyear(fn, keys, filt):
    R = [r for r in csv.DictReader(open(os.path.join(HERE, 'data', fn))) if filt(r)]
    idx = {(r['pid'], int(r['year'])): r for r in R}; out = {}
    for k in keys:
        xs, ys = [], []
        for (pid, y), r in idx.items():
            n = idx.get((pid, y + 1))
            if not n or y in (2019, 2020): continue
            try: a, b = float(r[k]), float(n[k])
            except ValueError: continue
            if math.isnan(a) or math.isnan(b): continue
            xs.append(a); ys.append(b)
        r = st.correlation(xs, ys); z = math.atanh(r); s = 1 / math.sqrt(len(xs) - 3)
        out[k] = dict(r=r, lo=math.tanh(z - 1.96 * s), hi=math.tanh(z + 1.96 * s), n=len(xs))
    return out
O = dict(
  hitters=nextyear('hitters_scored.csv', ['sprint', 'whiff', 'chase', 'so', 'ev', 'ubb', 'hr', 'single', 'double', 'triple', 'ops', 'avg', 'obp', 'slg', 'rbi_n', 'runs_n'], lambda r: True),
  SP=nextyear('pitchers_scored.csv', ['velo', 'gb', 'whiff', 'so', 'chase', 'ubb', 'ev', 'hr', 'hbip', 'era'], lambda r: r['role'] == 'SP'),
  RP=nextyear('pitchers_scored.csv', ['velo', 'gb', 'whiff', 'so', 'chase', 'ubb', 'ev', 'hr', 'hbip', 'era'], lambda r: r['role'] == 'RP'))
json.dump(O, open(os.path.join(HERE, 'series', 'repeat_rates.json'), 'w'), indent=1)
for g, D in O.items():
    print(g); [print(f'  {k:8s} {v["r"]:.2f} [{v["lo"]:.2f},{v["hi"]:.2f}] n={v["n"]}') for k, v in sorted(D.items(), key=lambda kv: -kv[1]['r'])]
