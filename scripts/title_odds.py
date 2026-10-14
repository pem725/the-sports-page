#!/usr/bin/env python3
"""Championship odds: play out the rest of the NFL and CFB seasons, then the brackets.

Reads the published game odds in data/nfl-odds.json and data/cfb-odds.json, so it
inherits their ratings and their limits. Written 2026-10-14 for the Bills/Notre Dame
call; re-run at each grading point listed in tracking/open-calls.md.

HONEST LIMIT: the CFP field is a stand-in for the committee -- fewest losses, then
SP+ with noise -- with no conference title games and no automatic bids. College
numbers are rough to a few points. NFL ties are broken by rating, not by the rulebook.

    python3 scripts/title_odds.py
"""
import json,numpy as np
from math import erf,sqrt
rng=np.random.default_rng(2026); N=20000
Phi=lambda z:0.5*(1+erf(z/sqrt(2)))
import os
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data')+os.sep
# ---------- NFL ----------
n=json.load(open(R+'nfl-odds.json')); T=n['teams']; T=list(T.values()) if isinstance(T,dict) else T
SD=13.2; HFA=1.5; rat={t['team']:t['rating'] for t in T}
def pw(a,b,home): return Phi((rat[a]-rat[b]+(HFA if home else 0))/SD)
sb={t['team']:0 for t in T}; made={t['team']:0 for t in T}
for _ in range(N):
    W={}
    for t in T:
        w=0
        for g in t['sched']:
            if g.get('won') is True: w+=1
            elif g.get('won') is None: w+= rng.random()<g['p']
        W[t['team']]=w+rng.random()*0.01+rat[t['team']]*1e-4
    champs={}
    for conf in ('AFC','NFC'):
        cs=[t for t in T if t['conf']==conf]; divs={}
        for t in cs: divs.setdefault(t['div'],[]).append(t['team'])
        dw=sorted([max(v,key=W.get) for v in divs.values()],key=W.get,reverse=True)
        wc=sorted([t['team'] for t in cs if t['team'] not in dw],key=W.get,reverse=True)[:3]
        seeds=dw+wc
        for s in seeds: made[s]+=1
        alive=seeds[:]  # index = seed-1
        # wild card: 2v7,3v6,4v5 ; 1 bye
        def play(a,b): return a if rng.random()<pw(a,b,True) else b
        r=[seeds[0],play(seeds[1],seeds[6]),play(seeds[2],seeds[5]),play(seeds[3],seeds[4])]
        r.sort(key=seeds.index)
        r2=[play(r[0],r[3]),play(r[1],r[2])]; r2.sort(key=seeds.index)
        champs[conf]=play(r2[0],r2[1])
    a,b=champs['AFC'],champs['NFC']
    sb[a if rng.random()<pw(a,b,False) else b]+=1
print('NFL Super Bowl odds:')
for k,v in sorted(sb.items(),key=lambda x:-x[1])[:8]: print(f'  {k:4} {v/N:6.1%}  playoffs {made[k]/N:.0%}')
# ---------- CFB ----------
c=json.load(open(R+'cfb-odds.json')); C=c['teams']; C=list(C.values()) if isinstance(C,dict) else C
SDc=16.5; H=2.5; sp={t['team']:t['sp'] for t in C}
def pc(a,b,home): return Phi((sp[a]-sp[b]+(H if home else 0))/SDc)
ttl={t['team']:0 for t in C}; inn={t['team']:0 for t in C}
for _ in range(N):
    L={}
    for t in C:
        l=t['played']-t['wins']
        for g in t['sched']:
            if g.get('won') is None: l+= rng.random()>g['p']
        L[t['team']]=l
    field=sorted(sp,key=lambda k:(L[k],-sp[k]+rng.normal(0,3)))[:12]   # committee proxy: fewest losses, then strength + noise
    for f in field: inn[f]+=1
    def play(a,b,home=False): return a if rng.random()<pc(a,b,home) else b
    s=field
    r1=[play(s[4],s[11],True),play(s[5],s[10],True),play(s[6],s[9],True),play(s[7],s[8],True)]
    qf=[play(s[0],r1[3]),play(s[1],r1[2]),play(s[2],r1[1]),play(s[3],r1[0])]
    sf=[play(qf[0],qf[3]),play(qf[1],qf[2])]
    ttl[play(sf[0],sf[1])]+=1
print('CFB title odds:')
for k,v in sorted(ttl.items(),key=lambda x:-x[1])[:8]: print(f'  {k:12} {v/N:6.1%}  in field {inn[k]/N:.0%}')
pb=sb['BUF']/N; pn=ttl['Notre Dame']/N
print(f'\nBUF {pb:.3f}  ND {pn:.3f}  both {pb*pn:.4f} (1 in {1/(pb*pn):.0f})')
