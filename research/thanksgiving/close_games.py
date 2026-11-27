import csv, random
rows=[x for x in csv.DictReader(open('games.csv')) if x['result'] and x['spread_line'] and 2000<=int(x['season'])<=2025]
# result = home - away; spread_line = home favored by
G=[(float(x['spread_line']),int(x['result'])) for x in rows]
print('games',len(G))
slate=[('CHI@DET',-1.5,-4),('PHI@DAL',8.5,-1),('KC@BUF',3.0,3)]
def near(s,w=1.0): return [m for sp,m in G if abs(sp-s)<=w]
P8=P4=1
for name,s,act in slate:
    ms=near(s); n=len(ms)
    p8=sum(abs(m)<=8 for m in ms)/n; p4=sum(abs(m)<=4 for m in ms)/n
    up=sum((m<0) if s>0 else (m>0) for m in ms if m!=0)/n
    print(f'{name} spread {s:+} n={n} P(|m|<=8)={p8:.2f} P(|m|<=4)={p4:.2f} P(underdog wins)={up:.2f}')
    P8*=p8;P4*=p4
print('all three one-score',round(P8,3),' all three <=4',round(P4,3))
# combined margin <=8 by resampling
random.seed(1); N=200000; pools=[near(s) for _,s,_ in slate]
hit=sum(sum(abs(random.choice(p)) for p in pools)<=8 for _ in range(N))/N
print('sum of margins <=8',round(hit,3))
# base rate: all-season, every week's games individually
allp=sum(abs(m)<=8 for _,m in G)/len(G); print('any game one-score',round(allp,2))
# historical Thanksgivings: 3-game slates since 2006
from collections import defaultdict
tg=defaultdict(list)
for x in rows:
    if x['weekday']=='Thursday' and x['gameday'][5:7]=='11' and 22<=int(x['gameday'][8:])<=28:
        tg[x['gameday']].append(abs(int(x['result'])))
tri=[(d,v) for d,v in sorted(tg.items()) if len(v)==3]
print('3-game Thanksgivings',len(tri),'all one-score:',[d for d,v in tri if max(v)<=8],'sum<=8:',[d for d,v in tri if sum(v)<=8])
