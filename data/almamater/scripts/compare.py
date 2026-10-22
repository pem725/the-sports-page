import json, pathlib, statistics as st, random
D = pathlib.Path(__file__).resolve().parent
T=json.load(open(D/'tenures.json'))
era=[o for o in T if 1970<=o['first_year']<=2025 and o['win_pct']!='']
alma_schools={o['school'] for o in era if o['group']=='played'}
random.seed(1)
def boot(a,b,n=4000):
    d=[]
    for _ in range(n):
        x=[random.choice(a) for _ in a]; y=[random.choice(b) for _ in b]; d.append(st.mean(x)-st.mean(y))
    d.sort(); return d[int(.025*n)], d[int(.975*n)]
def summ(label, rows):
    g={k:[o for o in rows if o['group']==k] for k in ('played','attended_only','other')}
    print(f"\n== {label}")
    for k,v in g.items():
        if not v: continue
        wp=[o['win_pct'] for o in v]; ch=[o['change_vs_prior5'] for o in v if o['change_vs_prior5']!='']
        done=[o['seasons'] for o in v if not o['ongoing']]
        W=sum(o['W'] for o in v); L=sum(o['L'] for o in v); Tt=sum(o['T'] for o in v)
        print(f"{k:14s} n={len(v):4d} mean_pct={st.mean(wp):.3f} pooled={(W+.5*Tt)/(W+L+Tt):.3f} | change n={len(ch)} mean={st.mean(ch):+.3f} median={st.median(ch):+.3f} | seasons(completed n={len(done)}) mean={st.mean(done):.2f} median={st.median(done)} | 1-season share={sum(o['seasons']==1 for o in v)/len(v):.2f}")
    a=[o['win_pct'] for o in g['played']]; b=[o['win_pct'] for o in g['other']]
    print("diff win pct played-other: %+.3f CI %s" % (st.mean(a)-st.mean(b), tuple(round(x,3) for x in boot(a,b))))
    a=[o['change_vs_prior5'] for o in g['played'] if o['change_vs_prior5']!='']; b=[o['change_vs_prior5'] for o in g['other'] if o['change_vs_prior5']!='']
    print("diff change played-other: %+.3f CI %s" % (st.mean(a)-st.mean(b), tuple(round(x,3) for x in boot(a,b))))
    a=[o['seasons'] for o in g['played'] if not o['ongoing']]; b=[o['seasons'] for o in g['other'] if not o['ongoing']]
    print("diff seasons played-other (completed): %+.2f CI %s" % (st.mean(a)-st.mean(b), tuple(round(x,2) for x in boot(a,b))))
same=[o for o in era if o['school'] in alma_schools]
print("schools with >=1 played alma-mater hire 1970-2025:", len(alma_schools))
summ("same schools, all tenures 1970-2025", same)
summ("same schools, tenures >=3 seasons", [o for o in same if o['seasons']>=3])
summ("same schools, >=3 seasons, completed (not ongoing)", [o for o in same if o['seasons']>=3 and not o['ongoing']])
summ("all FBS schools, >=3 seasons", [o for o in era if o['seasons']>=3])
# baseline levels
for k in ('played','other'):
    v=[o['prior5_pct'] for o in same if o['group']==k and o['seasons']>=3 and o['prior5_pct']!='']
    print(k,"prior5 baseline mean (>=3 seasons):", round(st.mean(v),3), len(v))
# by decade
print()
for dec in range(1970,2030,10):
    v=[o for o in era if dec<=o['first_year']<dec+10]
    p=sum(o['group']=='played' for o in v); print(dec, "hires", len(v), "played", p, f"{p/len(v):.2f}", " >=3 seasons:", sum(o['group']=='played' and o['seasons']>=3 for o in v), "/", sum(o['seasons']>=3 for o in v))

import numpy as np
for label,cond in (("same schools >=3 seasons", lambda o:o['school'] in alma_schools and o['seasons']>=3), ("same schools all", lambda o:o['school'] in alma_schools)):
    v=[o for o in era if cond(o) and o['group'] in ('played','other') and o['prior5_pct']!='']
    y=np.array([o['win_pct'] for o in v]); b=np.array([o['prior5_pct'] for o in v]); p=np.array([o['group']=='played' for o in v],float)
    X=np.column_stack([np.ones_like(y),b,p]); beta,res,_,_=np.linalg.lstsq(X,y,rcond=None)
    e=y-X@beta; s2=e@e/(len(y)-3); se=np.sqrt(np.diag(s2*np.linalg.inv(X.T@X)))
    print(f"\nOLS tenure win pct ~ prior5 + played [{label}] n={len(y)} (played={int(p.sum())}): played coef {beta[2]:+.3f} (SE {se[2]:.3f}); prior5 slope {beta[1]:.2f} (SE {se[1]:.2f})")
