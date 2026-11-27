"""Does the point spread mean what it says? nflverse games, 2006-2025, REG+POST.
spread_line = points the home team is favored by; result = home minus away."""
import csv, math, statistics as st, sys
path=sys.argv[1]
G=[x for x in csv.DictReader(open(path)) if x['result'] and x['spread_line'] and 2006<=int(x['season'])<=2025]
fav=[]  # (spread for favorite >=0, favorite won 1/0/.5, favorite margin)
for x in G:
    s=float(x['spread_line']); r=int(x['result'])
    if s<0: s,r=-s,-r
    fav.append((s, 1.0 if r>0 else 0.0 if r<0 else 0.5, r))
res=[m-s for s,_,m in fav]
sd=st.pstdev(res); print(f'games {len(fav)}  mean(margin - spread) {st.mean(res):+.2f}  sd {sd:.1f}')
Phi=lambda z:0.5*(1+math.erf(z/math.sqrt(2)))
bins=[(0,0.5),(1,2.5),(3,3),(3.5,4.5),(5,6.5),(7,7),(7.5,9.5),(10,13.5),(14,99)]
print('spread      games  fav won   normal says')
for lo,hi in bins:
    b=[(s,w) for s,w,_ in fav if lo<=s<=hi]
    if not b: continue
    won=sum(w for _,w in b)/len(b); pred=st.mean(Phi(s/sd) for s,_ in b)
    print(f'{lo:>4}-{hi:<5} {len(b):6d}   {won*100:4.0f}      {pred*100:4.0f}')
# the house's margin, from moneylines
ov=[]; cal=[]
for x in G:
    try: a=float(x['away_moneyline']); h=float(x['home_moneyline'])
    except: continue
    imp=lambda o: 100/(o+100) if o>0 else -o/(-o+100)
    pa,ph=imp(a),imp(h); ov.append(pa+ph-1)
    r=int(x['result']); cal.append((ph/(pa+ph), 1.0 if r>0 else 0.0 if r<0 else 0.5))
print(f'moneyline games {len(ov)}  built-in margin: median {st.median(ov)*100:.1f} points of probability')
print('chance from line   games  actually won')
for lo in (0.5,0.6,0.7,0.8,0.9):
    b=[(p,w) for p,w in cal for p,w in [(p,w) if p>=0.5 else (1-p,1-w)] if lo<=p<lo+0.1]
    print(f'{int(lo*100)}-{int(lo*100)+9}         {len(b):5d}   {sum(w for _,w in b)/len(b)*100:4.0f}  (avg stated {st.mean(p for p,_ in b)*100:.0f})')
