"""Robustness for Test A: is the streak gap a calibration artifact of the log5 benchmark?
Compares streak rows with ALL rows at the same expected probability (binned), and repeats
with a run/goal-differential (Pythagorean) strength measure."""
import json, math, sys
import numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
import momentum as M

def pyth_rows(seasons, expo):
    rows = []
    for s, games in seasons.items():
        seq = M.team_seqs(games)
        RS = {t: sum(max(x['d'],0) for x in v) for t,v in seq.items()}
        # need runs scored/allowed: rebuild
        rf = {t: 0 for t in seq}; ra = {t: 0 for t in seq}
        for g in games:
            rf[g['home']] += g['hd']; ra[g['home']] += g['ad']; rf[g['away']] += g['ad']; ra[g['away']] += g['hd']
        for t, v in seq.items():
            streak = 0
            # cumulative per-game runs for exclusion
            for k, x in enumerate(v):
                if k >= 5:
                    g = games[x['i']]
                    my_f = g['hd'] if x['home']==1 else g['ad']; my_a = g['ad'] if x['home']==1 else g['hd']
                    lastf = lasta = 0
                    for y in v[k-5:k]:
                        gg = games[y['i']]
                        lastf += gg['hd'] if y['home']==1 else gg['ad']; lasta += gg['ad'] if y['home']==1 else gg['hd']
                    o = x['opp']
                    S = (rf[t]-my_f-lastf)**expo/((rf[t]-my_f-lastf)**expo+(ra[t]-my_a-lasta)**expo)
                    O = (rf[o]-my_a)**expo/((rf[o]-my_a)**expo+(ra[o]-my_f)**expo)
                    rows.append(dict(w=x['w'], home=x['home'], streak=streak, xp=M.logit(M.log5(S,O))))
                streak = (streak+1 if streak>0 else 1) if x['w'] else (streak-1 if streak<0 else -1)
    return rows

def binned(rows, key, cal):
    b,a = cal
    p = np.array([M.sig(b*r[key]+a*r['home']) for r in rows]); y = np.array([r['w'] for r in rows])
    edges = np.quantile(p, np.linspace(0,1,21)); idx = np.clip(np.searchsorted(edges, p, side='right')-1, 0, 19)
    base = {i: y[idx==i].mean() for i in range(20)}
    out = {}
    for name, f in (('W5+',lambda s:s>=5),('W3+',lambda s:s>=3),('L3+',lambda s:s<=-3),('L5+',lambda s:s<=-5)):
        m = np.array([f(r['streak']) for r in rows])
        bench = np.array([base[i] for i in idx[m]])
        gap = y[m].mean()-bench.mean()
        se = math.sqrt((bench*(1-bench)).sum())/m.sum()
        out[name] = dict(games=int(m.sum()), actual=round(100*y[m].mean(),1), same_bin_all_teams=round(100*bench.mean(),1), gap=round(100*gap,1), se=round(100*se,1))
    # calibration of top/bottom deciles overall
    out['calib_top_bin'] = [round(100*p[idx==19].mean(),1), round(100*y[idx==19].mean(),1)]
    out['calib_bottom_bin'] = [round(100*p[idx==0].mean(),1), round(100*y[idx==0].mean(),1)]
    return out

res = {}
reg = M.mlb_regular(); nreg, _ = M.nhl_load(); nreg.pop(2026, None)
for sport, seasons, expo in (('mlb', reg, 1.83), ('nhl', nreg, 2.0)):
    rows = M.team_game_rows(seasons)
    cal = M.calib(rows, 'x5')
    res[sport+'_winpct_binned'] = binned(rows, 'x5', cal)
    pr = pyth_rows(seasons, expo)
    calp = M.calib(pr, 'xp')
    res[sport+'_pyth'] = dict(calibration=calp, binned=binned(pr, 'xp', calp))
json.dump(res, open('robustness.json','w'), indent=1)
print(json.dumps(res, indent=1))
