#!/usr/bin/env python3
"""Every NFL running-back season 1999-2025 (nflverse), any carries, with age on Sept 1.
data/rb_hist.csv"""
import csv, os
from datetime import date
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, 'data', 'raw')
born = {r['gsis_id']: r['birth_date'] for r in csv.DictReader(open(os.path.join(RAW, 'rb', 'players.csv')))}
rows = []
for y in range(1999, 2026):
    for r in csv.DictReader(open(os.path.join(RAW, f'reg{y}.csv'))):
        if r.get('position') != 'RB': continue
        f = lambda k: float(r.get(k) or 0)
        if f('carries') < 1: continue
        b = born.get(r['player_id'], '')
        age = (date(y, 9, 1) - date.fromisoformat(b)).days / 365.25 if b else ''
        rows.append(dict(gsis=r['player_id'], name=r['player_display_name'], year=y, games=f('games'), car=f('carries'),
                         yds=f('rushing_yards'), rec=f('receptions'), recyds=f('receiving_yards'), age=age,
                         sched=16 if y < 2021 else 17))
w = csv.DictWriter(open(os.path.join(HERE, 'data', 'rb_hist.csv'), 'w', newline=''), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows))
