import json, csv, pathlib, statistics as st, random
from collections import defaultdict
D = pathlib.Path(__file__).resolve().parent
S = list(csv.DictReader(open(D/'seasons.csv')))
for r in S:
    for k in ('cid','year','games','w','l','t'): r[k]=int(r[k])
F = {x['cid']:x for x in json.load(open(D/'wiki_parsed.json'))}
MANUAL_PLAYED = {(1444,'Louisiana Tech'):('c.1954–1957 (graduated 1958)','prose-manual'), (993,'Oklahoma State'):('','prose-manual')}
NOTE_ATT = {147:'graduate degree only (Ed.D.)', 313:'graduate degree only (M.A.)', 828:'undergraduate (B.A. 1978), did not play',
            1491:'alma mater Cal; college playing not listed (CFL only) -- unverified', 1180:'B.A. Nevada', 1767:'alumnus, did not play', 760:'alma mater listed'}
# school-year totals
sy = defaultdict(lambda:[0,0,0,0])
for r in S:
    a=sy[(r['school'],r['year'])]; a[0]+=r['w']; a[1]+=r['l']; a[2]+=r['t']; a[3]+=r['games']
def pct(w,l,t):
    g=w+l+t; return (w+0.5*t)/g if g else None
# tenures: contiguous runs per coach-school
by = defaultdict(list)
for r in S: by[(r['cid'],r['school'])].append(r)
ten=[]
for (cid,sch),rs in by.items():
    rs.sort(key=lambda r:r['year']); run=[rs[0]]
    for r in rs[1:]:
        if r['year']==run[-1]['year']+1: run.append(r)
        else: ten.append((cid,sch,run)); run=[r]
    ten.append((cid,sch,run))
career = defaultdict(lambda:[0,0,0])
for r in S:
    c=career[r['cid']]; c[0]+=r['w']; c[1]+=r['l']; c[2]+=r['t']
out=[]
for cid,sch,run in ten:
    w=sum(r['w'] for r in run); l=sum(r['l'] for r in run); t=sum(r['t'] for r in run)
    y0,y1=run[0]['year'],run[-1]['year']
    pw=[sy.get((sch,y)) for y in range(y0-5,y0)]
    base=None
    if all(pw): base=pct(sum(p[0] for p in pw),sum(p[1] for p in pw),sum(p[2] for p in pw))
    x=F.get(cid)
    played = x is not None and sch in x['played']; ptype=x['src'].get(sch) if played else ''
    pyrs = x['played_years'].get(sch,'') if played else ''
    if (cid,sch) in MANUAL_PLAYED: played=True; pyrs,ptype=MANUAL_PLAYED[(cid,sch)]
    attended = (not played) and x is not None and sch in x['alma']
    cw,cl,ct = career[cid]
    out.append(dict(coach=f"{run[0]['first']} {run[0]['last']}", cid=cid, school=sch, wiki=x['wiki'] if x else '',
        group='played' if played else ('attended_only' if attended else ('unresolved' if x is None else 'other')),
        playing_years=pyrs, playing_source=ptype, attended_note=NOTE_ATT.get(cid,'') if attended else '',
        first_year=y0, last_year=y1, seasons=len(run), W=w, L=l, T=t, win_pct=round(pct(w,l,t),3) if pct(w,l,t) is not None else '',
        W_elsewhere=cw-w, L_elsewhere=cl-l, T_elsewhere=ct-t,
        prior5_pct=round(base,3) if base is not None else '', change_vs_prior5=round(pct(w,l,t)-base,3) if base is not None and pct(w,l,t) is not None else '',
        ongoing = y1==2025))
json.dump(out, open(D/'tenures.json','w'))
cols=list(out[0])
am=[o for o in out if o['group'] in('played','attended_only') and o['last_year']>=1970]
am.sort(key=lambda o:(o['group'],o['school'],o['first_year']))
with open(D/'almamater.csv','w',newline='') as fh:
    wr=csv.DictWriter(fh,fieldnames=cols); wr.writeheader(); wr.writerows(am)
pre=[o for o in out if o['group'] in('played','attended_only') and o['last_year']<1970]
with open(D/'almamater_pre1970.csv','w',newline='') as fh:
    wr=csv.DictWriter(fh,fieldnames=cols); wr.writeheader(); wr.writerows(sorted(pre,key=lambda o:(o['school'],o['first_year'])))
with open(D/'all_tenures.csv','w',newline='') as fh:
    wr=csv.DictWriter(fh,fieldnames=cols); wr.writeheader(); wr.writerows(sorted(out,key=lambda o:(o['school'],o['first_year'])))
print("alma tenures overlapping 1970+:", sum(o['group']=='played' for o in am), "played;", sum(o['group']=='attended_only' for o in am),"attended-only")
print("distinct played coaches 1970+:", len({o['cid'] for o in am if o['group']=='played'}))
print("pre-1970 played tenures:", sum(o['group']=='played' for o in pre), "attended:", sum(o['group']=='attended_only' for o in pre))
