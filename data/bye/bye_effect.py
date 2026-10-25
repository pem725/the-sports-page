"""Is a bye week worth anything? College (CFBD, 2005-2025) and NFL (nflverse, 1999-2025).

Strength control that knows nothing about rest:
  college -> CFBD pregame Elo (and, as a check, each team's season margin with this game left out)
  NFL     -> each team's season margin with this game left out
Symmetric models, no intercept: home=1 at a true home site, 0 at neutral sites.
"bye" = 12-16 days since the team's last game; "normal" = 6-9; first games and longer gaps dropped.
Usage: python3 data/bye/bye_effect.py RAW_CFBD_DIR   (raw = /games?year=Y&seasonType=regular&classification=fbs JSON)
"""
import json, glob, csv, collections, datetime as dt, sys, pathlib
import numpy as np
D = pathlib.Path(__file__).resolve().parent
RAW = sys.argv[1]
def ols(X, y):
    b = np.linalg.lstsq(X, y, rcond=None)[0]; e = y - X @ b
    return b, np.sqrt(np.diag(e @ e / (len(y) - X.shape[1]) * np.linalg.inv(X.T @ X)))
def logit(X, y):
    b = np.zeros(X.shape[1])
    for _ in range(60):
        p = 1/(1+np.exp(-X@b)); H = X.T @ (X*(p*(1-p))[:,None]); b += np.linalg.solve(H, X.T@(y-p))
    return b, np.sqrt(np.diag(np.linalg.inv(H)))
out = {}
# ---------- college ----------
rows = [g for f in sorted(glob.glob(f"{RAW}/g*.json")) for g in json.load(open(f)) if g.get('completed') and g.get('homePoints') is not None]
gbt = collections.defaultdict(list)
for g in rows:
    d = dt.datetime.fromisoformat(g['startDate'].replace('Z', '+00:00'))
    for s in ('home', 'away'): gbt[(g['season'], g[s+'Team'])].append((d, g['id']))
rest, prevres = {}, {}
byid = {g['id']: g for g in rows}
for k, l in gbt.items():
    l.sort()
    for i, (d, gid) in enumerate(l):
        if i == 0: rest[(gid, k[1])] = None; continue
        rest[(gid, k[1])] = (d - l[i-1][0]).total_seconds()/86400
        pg = byid[l[i-1][1]]; me = pg['homePoints'] if pg['homeTeam'] == k[1] else pg['awayPoints']; op = pg['awayPoints'] if pg['homeTeam'] == k[1] else pg['homePoints']
        prevres[(gid, k[1])] = 'L' if me < op else 'W'
cat = lambda r: None if r is None else 'short' if r < 5.5 else 'normal' if r < 9.5 else 'bye' if 11.5 <= r < 16.5 else 'other'
G = []
for g in rows:
    if g.get('homeClassification') != 'fbs' or g.get('awayClassification') != 'fbs': continue
    if g['homePoints'] == g['awayPoints'] or g.get('homePregameElo') is None or g.get('awayPregameElo') is None: continue
    ch, ca = cat(rest[(g['id'], g['homeTeam'])]), cat(rest[(g['id'], g['awayTeam'])])
    if ch is None or ca is None or 'other' in (ch, ca): continue
    G.append(dict(g=g, ch=ch, ca=ca, m=g['homePoints']-g['awayPoints']))
X = np.array([[(r['g']['homePregameElo']-r['g']['awayPregameElo'])/100, 0 if r['g']['neutralSite'] else 1,
               int(r['ch']=='bye')-int(r['ca']=='bye'), int(r['ch']=='short')-int(r['ca']=='short')] for r in G], float)
M = np.array([r['m'] for r in G], float); W = (M > 0).astype(float)
bm, sm = ols(X, M); bl, sl = logit(X, W)
pexp = 1/(1+np.exp(-(X[:, [0,1,3]] @ bl[[0,1,3]])))
one = [i for i, r in enumerate(G) if (r['ch']=='bye') != (r['ca']=='bye')]
def tally(idx):
    won = sum(W[i] if G[i]['ch']=='bye' else 1-W[i] for i in idx); ex = sum(pexp[i] if G[i]['ch']=='bye' else 1-pexp[i] for i in idx)
    return dict(n=len(idx), won=int(won), won_pct=round(won/len(idx), 3), expected_pct=round(ex/len(idx), 3))
def team(i): return G[i]['g']['homeTeam'] if G[i]['ch']=='bye' else G[i]['g']['awayTeam']
cfb = dict(games=len(G), seasons='2005-2025', bye_points=round(bm[2], 2), bye_points_se=round(sm[2], 2), home_points=round(bm[1], 2), home_points_se=round(sm[1],2),
           bye_logodds=round(bl[2], 3), bye_logodds_se=round(bl[2]*0+sl[2], 3), one_side_bye=tally(one),
           after_loss=tally([i for i in one if prevres.get((G[i]['g']['id'], team(i)))=='L']),
           after_win=tally([i for i in one if prevres.get((G[i]['g']['id'], team(i)))=='W']),
           bye_team_underdog_share=round(sum(1 for i in one if (pexp[i] if G[i]['ch']=='bye' else 1-pexp[i]) < .5)/len(one), 2))
# loss-split in points
for lab in ('L', 'W'):
    idx = [i for i in one if prevres.get((G[i]['g']['id'], team(i)))==lab]
    sgn = np.array([1 if G[i]['ch']=='bye' else -1 for i in idx]); resid = (M - X @ np.r_[bm[:2], 0, bm[3]])[idx]*sgn
    cfb[f'points_after_{lab}'] = [round(resid.mean(), 2), round(resid.std(ddof=1)/np.sqrt(len(idx)), 2)]
# check: leave-one-out season margin as strength
tot = collections.defaultdict(lambda: [0, 0])
for r in G:
    g = r['g']; tot[(g['season'], g['homeTeam'])][0] += r['m']; tot[(g['season'], g['homeTeam'])][1] += 1; tot[(g['season'], g['awayTeam'])][0] -= r['m']; tot[(g['season'], g['awayTeam'])][1] += 1
keep, X2 = [], []
for i, r in enumerate(G):
    g = r['g']; a1, n1 = tot[(g['season'], g['homeTeam'])]; a2, n2 = tot[(g['season'], g['awayTeam'])]
    if n1 < 2 or n2 < 2: continue
    keep.append(i); X2.append([(a1-r['m'])/(n1-1) - (a2+r['m'])/(n2-1), X[i,1], X[i,2], X[i,3]])
b2, s2 = ols(np.array(X2), M[keep]); cfb['check_loo_bye_points'] = [round(b2[2], 2), round(s2[2], 2)]
out['cfb'] = cfb
# ---------- NFL ----------
N = [r for r in csv.DictReader(open(D.parent/'nfl'/'nflverse-games.csv')) if r['game_type']=='REG' and r['home_score'] not in ('', None) and int(r['season']) <= 2025]
for r in N: r['m'] = int(r['home_score'])-int(r['away_score'])
tot = collections.defaultdict(lambda: [0, 0])
for r in N:
    tot[(r['season'], r['home_team'])][0] += r['m']; tot[(r['season'], r['home_team'])][1] += 1; tot[(r['season'], r['away_team'])][0] -= r['m']; tot[(r['season'], r['away_team'])][1] += 1
NX, NM, NK = [], [], []
for r in N:
    hr, ar = int(r['home_rest']), int(r['away_rest'])
    if int(r['week']) == 1 or hr >= 20 or ar >= 20: continue
    a1, n1 = tot[(r['season'], r['home_team'])]; a2, n2 = tot[(r['season'], r['away_team'])]
    bh, ba = int(hr >= 13), int(ar >= 13)
    NX.append([(a1-r['m'])/(n1-1) - (a2+r['m'])/(n2-1), int(r['location']=='Home'), bh-ba]); NM.append(r['m']); NK.append((r, bh, ba))
NX = np.array(NX, float); NM = np.array(NM, float)
nb, ns = ols(NX, NM)
nfl = dict(games=len(NM), seasons='1999-2025', bye_points=round(nb[2], 2), bye_points_se=round(ns[2], 2), home_points=round(nb[1], 2), home_points_se=round(ns[1], 2))
nz = NM != 0; lb, ls = logit(NX[nz], (NM[nz] > 0).astype(float)); pe = 1/(1+np.exp(-(NX[nz][:, :2] @ lb[:2])))
kk = [NK[i] for i in np.where(nz)[0]]; yy = (NM[nz] > 0)
idx = [j for j, k in enumerate(kk) if k[1] != k[2]]
won = sum(yy[j] if kk[j][1] else 1-yy[j] for j in idx); ex = sum(pe[j] if kk[j][1] else 1-pe[j] for j in idx)
nfl['one_side_bye'] = dict(n=len(idx), won=int(won), won_pct=round(won/len(idx), 3), expected_pct=round(ex/len(idx), 3))
c = n = 0
for r, bh, ba in NK:
    if bh == ba or r['spread_line'] == '': continue
    ats = r['m'] - float(r['spread_line'])
    if ats == 0: continue
    n += 1; c += (ats > 0) if bh else (ats < 0)
nfl['bye_team_ats'] = [c, n, round(c/n, 3)]
for lo, hi in [(1999, 2010), (2011, 2025)]:
    ii = [i for i, (r, _, _) in enumerate(NK) if lo <= int(r['season']) <= hi]
    b_, s_ = ols(NX[ii], NM[ii]); nfl[f'bye_points_{lo}_{hi}'] = [round(b_[2], 2), round(s_[2], 2)]
out['nfl'] = nfl
json.dump(out, open(D/'bye-effect.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
