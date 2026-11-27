"""Calibration of in-game win probability at the extremes, nflverse pbp 2006-2025, REG+POST.
For each team in each game, the FIRST play its win chance reaches each threshold;
expected losses = sum(1 - wp at that play); actual = games it then lost (tie = half).
Two models: nflverse wp (no market) and vegas_wp (blends the closing line).
Model-free check: biggest lead held by each team after halftime, and how often it was lost."""
import csv, gzip, os, json
csv.field_size_limit(10**9)
D=os.path.expanduser('~/.cache/sports-page/nflverse/pbp')
TH=[0.90,0.95,0.98,0.99,0.995]
def num(x):
    try: return float(x)
    except: return None
acc={m:{t:[0,0.0,0.0] for t in TH} for m in ('wp','vegas')}   # n, expected losses, actual losses
lead={}  # lead size bucket -> [n, lost]
seasons=range(2006,2026)
for y in seasons:
    G={}
    with gzip.open(f'{D}/play_by_play_{y}.csv.gz','rt') as f:
        r=csv.reader(f); h=next(r); ix={k:i for i,k in enumerate(h)}
        for row in r:
            gid=row[ix['game_id']]
            g=G.setdefault(gid,{'wp':[],'vw':[],'m2':[],'res':None})
            hw=num(row[ix['home_wp']]); vw=num(row[ix['vegas_home_wp']])
            if hw is not None: g['wp'].append(hw)
            if vw is not None: g['vw'].append(vw)
            q=num(row[ix['qtr']]); hs=num(row[ix['total_home_score']]); as_=num(row[ix['total_away_score']])
            if q and q>=3 and hs is not None: g['m2'].append(hs-as_)
            res=num(row[ix['result']])
            if res is not None: g['res']=res
    for gid,g in G.items():
        if g['res'] is None: continue
        home_out = 1.0 if g['res']>0 else 0.0 if g['res']<0 else 0.5
        for m,seq in (('wp',g['wp']),('vegas',g['vw'])):
            for side in ('home','away'):
                s=[p if side=='home' else 1-p for p in seq]
                out=home_out if side=='home' else 1-home_out
                for t in TH:
                    p=next((x for x in s if x>=t),None)
                    if p is None: continue
                    a=acc[m][t]; a[0]+=1; a[1]+=1-p; a[2]+=1-out
        if g['m2']:
            for side,sg in (('home',1),('away',-1)):
                mx=max(sg*x for x in g['m2'])
                out=home_out if side=='home' else 1-home_out
                for b in (14,17,21,24,28):
                    if mx>=b:
                        L=lead.setdefault(b,[0,0.0]); L[0]+=1; L[1]+=1-out
    print(y,len(G),flush=True)
res={'seasons':'2006-2025','models':{m:{str(t):dict(n=v[0],expected=round(v[1],1),actual=v[2]) for t,v in d.items()} for m,d in acc.items()},
     'second_half_leads':{str(b):dict(n=v[0],lost=v[1]) for b,v in lead.items()}}
json.dump(res,open('calib.json','w'),indent=1)
for m,d in acc.items():
    print('model',m)
    for t,(n,e,a) in d.items(): print(f'  reached {t:.3f}: n={n:5d} expected losses {e:6.1f} actual {a:5.1f}  ratio {a/e if e else 0:.2f}  1 in {n/a if a else 0:.0f}')
for b,(n,l) in sorted(lead.items()): print(f'led by {b}+ after halftime: n={n} lost {l} -> 1 in {n/l if l else 0:.0f}')
