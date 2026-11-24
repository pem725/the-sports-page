"""2026 Thanksgiving leverage from the Odds Board's own game probabilities (data/nfl-odds.json).
Simplified seeding: 4 division winners + 3 wild cards per conference by wins, ties broken at random
(the real tiebreakers are not modeled). Leverage = P(playoffs | win TG game) - P(playoffs | lose)."""
import json, os
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(H, '..', '..'))
odds = json.load(open(f'{REPO}/data/nfl-odds.json')); T = odds['teams']
byname = {t['name']: t['team'] for t in T}; idx = {t['team']: i for i, t in enumerate(T)}
wins0 = np.array([sum(1.0 if g['won'] else 0.0 for g in t['sched'] if g['won'] is not None) for t in T])
# ties in feed? count half if us==them
for i, t in enumerate(T):
    wins0[i] += sum(0.5 for g in t['sched'] if g['won'] is False and g['us'] == g['them'] and g['us'] is not None)
games = {}
for t in T:
    for g in t['sched']:
        if g['won'] is not None: continue
        a, b = t['team'], byname[g['opp']]
        key = (g['date'], tuple(sorted((a, b))))
        if key not in games: games[key] = (a, b, g['p'])
G = list(games.items()); N = 200000
rng = np.random.default_rng(7)
W = np.tile(wins0, (N, 1)); outc = {}
for (date, pair), (a, b, p) in G:
    r = rng.random(N) < p
    W[:, idx[a]] += r; W[:, idx[b]] += ~r
    outc[(date, a)] = r; outc[(date, b)] = ~r
W = W + rng.random(W.shape) * 1e-3
po = np.zeros(W.shape, bool)
for conf in ('AFC', 'NFC'):
    ci = [i for i, t in enumerate(T) if t['conf'] == conf]
    winners = []
    for dv in sorted({T[i]['div'] for i in ci}):
        di = [i for i in ci if T[i]['div'] == dv]
        w = np.array(di)[np.argmax(W[:, di], axis=1)]; po[np.arange(N), w] = True
    rest = W[:, ci].copy(); rest[po[:, ci]] = -1
    top3 = np.argsort(-rest, axis=1)[:, :3]
    for k in range(3): po[np.arange(N), np.array(ci)[top3[:, k]]] = True
res = dict(note=__doc__.strip(), sims=N, odds_generated=odds['generated'], games=[])
calib = []
for t in T:
    calib.append((t['team'], round(float(po[:, idx[t['team']]].mean()), 3), t['po']))
res['calibration_max_abs_gap_vs_board'] = round(max(abs(a - b) for _, a, b in calib), 3)
for a, b in (('CHI', 'DET'), ('PHI', 'DAL'), ('KC', 'BUF')):
    g = {'game': f'{a} at {b}'}; tot = 0
    for tm in (a, b):
        win = outc[('2026-11-26', tm)]; col = po[:, idx[tm]]
        lev = col[win].mean() - col[~win].mean(); tot += lev
        g[tm] = dict(p_playoffs=round(float(col.mean()), 3), if_win=round(float(col[win].mean()), 3), if_lose=round(float(col[~win].mean()), 3),
                     leverage_pts=round(100 * float(lev), 1))
    g['game_leverage_pts'] = round(100 * tot, 1); res['games'].append(g)
# compare: every other week-13ish game (Nov 26 - Nov 30) for context
other = []
for (date, pair), (a, b, p) in G:
    if '2026-11-26' <= date <= '2026-11-30' and date != '2026-11-26':
        tot = sum(po[:, idx[tm]][outc[(date, tm)]].mean() - po[:, idx[tm]][~outc[(date, tm)]].mean() for tm in (a, b))
        other.append((f'{date} {a}-{b}', round(100 * float(tot), 1)))
res['other_games_same_week'] = sorted(other, key=lambda x: -x[1])
json.dump(res, open(f'{H}/data/sim_2026.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
