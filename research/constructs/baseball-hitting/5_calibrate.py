#!/usr/bin/env python3
"""Calibrate every hitting stat: where does a season stand?

The editor's idea, 2026-11-13: put each number on a relative continuum. For every
player-season since 1901 with 300+ PA (scaled for short seasons: 1918, 1981, 1994, 2020)
this writes, per stat:
  _hp    percentile among every season in history (from the year the stat was kept)
  _sp    percentile within its own season (removes the era)
  _sz    that within-season percentile as a normal score (the psychometric convention)
  _pomp  percent of the maximum possible, (x - min)/(max - min) over history
POMP is a linear rescale, so it cannot change a correlation or a factor model; and one
extreme season (Hack Wilson's 191 RBI) sets its ceiling for everyone.

Downloads 125 seasons from the MLB Stats API (no key) into data/raw/ the first time.
Writes data/calibrated.csv (not committed: about 40 MB, rebuilt in a minute).
"""
import os, urllib.request, time
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'data', 'raw')
os.makedirs(RAW, exist_ok=True)
URL = "https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&season={y}&sportId=1&limit=3000&playerPool=ALL"
for _y in range(1901, 2026):
    _p = os.path.join(RAW, f'h{_y}.json')
    if not os.path.exists(_p):
        open(_p, 'wb').write(urllib.request.urlopen(URL.format(y=_y), timeout=60).read()); time.sleep(0.3)
os.chdir(RAW)
import json,csv,math,glob
from collections import defaultdict
from statistics import NormalDist
N=NormalDist()
START={'so':1913,'sbatt':1951,'gidp':1939,'ubb':1955,'ibb':1955,'sf':1954,'pitches':1988,'goao':1988}
rows=[]
for y in range(1901,2026):
  sp=json.load(open(f'h{y}.json'))['stats'][0]['splits']
  G=max(s['stat'].get('gamesPlayed',0) for s in sp); G=max(G,1)
  cut=300*G/162   # 300 PA in a 162-game season, scaled for short ones (1918, 1981, 1994, 2020)
  for s in sp:
    t=s['stat']; pa=t.get('plateAppearances') or 0
    if pa<cut: continue
    g=lambda k: t.get(k)
    s1=t['hits']-t['doubles']-t['triples']-t['homeRuns']
    r={'pid':s['player']['id'],'name':s['player'].get('fullName',''),'year':y,'pa':pa,'rbi_total':g('rbi'),'hr_total':g('homeRuns')}
    def rate(x): return None if x is None else x/pa
    ubb=None if g('intentionalWalks') is None else t['baseOnBalls']-t['intentionalWalks']
    onb=s1+t['baseOnBalls']+(t.get('hitByPitch') or 0)
    r.update({'single':rate(s1),'double':rate(t['doubles']),'triple':rate(t['triples']),'hr':rate(t['homeRuns']),
      'bb':rate(t['baseOnBalls']),'ubb':rate(ubb),'ibb':rate(g('intentionalWalks')),'hbp':rate(g('hitByPitch')),'so':rate(g('strikeOuts')),
      'sbatt':None if g('caughtStealing') is None else (t['stolenBases']+t['caughtStealing'])/max(onb,1),
      'gidp':rate(g('groundIntoDoublePlay')),'sac':rate(g('sacBunts')),'sf':rate(g('sacFlies')),
      'pitches':rate(g('numberOfPitches')),'goao':None if g('groundOuts') is None or g('airOuts') is None else math.log((t['groundOuts']+1)/(t['airOuts']+1)),
      'runs':rate(g('runs')),'rbi':rate(g('rbi'))})
    # Start each stat when both leagues kept it reliably; before that a zero can mean "not recorded".
    for k,y0 in START.items():
      if y<y0: r[k]=None
    rows.append(r)
V=['single','double','triple','hr','bb','ubb','ibb','hbp','so','sbatt','gidp','sac','sf','pitches','goao','runs','rbi','rbi_total','hr_total']
def pct(vals):
  # mid-rank percentile, ties shared
  order=sorted(range(len(vals)),key=lambda i:vals[i]); out=[0]*len(vals); i=0
  while i<len(order):
    j=i
    while j+1<len(order) and vals[order[j+1]]==vals[order[i]]: j+=1
    p=(i+j)/2+0.5
    for k in range(i,j+1): out[order[k]]=p/len(vals)
    i=j+1
  return out
for v in V:
  idx=[i for i,r in enumerate(rows) if r[v] is not None]
  vals=[rows[i][v] for i in idx]; P=pct(vals); lo,hi=min(vals),max(vals)
  for i,p in zip(idx,P): rows[i][v+'_hp']=p; rows[i][v+'_pomp']=(rows[i][v]-lo)/(hi-lo) if hi>lo else None
  bys=defaultdict(list)
  for i in idx: bys[rows[i]['year']].append(i)
  for y,ii in bys.items():
    P=pct([rows[i][v] for i in ii])
    for i,p in zip(ii,P): rows[i][v+'_sp']=p; rows[i][v+'_sz']=N.inv_cdf(min(max(p,0.001),0.999))
cols=['pid','name','year','pa']+[c for v in V for c in (v,v+'_hp',v+'_sp',v+'_sz',v+'_pomp')]
with open(os.path.join(HERE,'data','calibrated.csv'),'w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
print('player-seasons',len(rows))
first={v:min(r['year'] for r in rows if r[v] is not None) for v in V}; print(first)
