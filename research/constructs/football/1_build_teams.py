"""Build data/teams.csv: one row per team-season, both leagues, per-play rates.
College counts a sack as a run; the NFL counts it as a pass. ypc uses the COLLEGE
definition in both leagues; ypc_nfl is the NFL's own. CFBD trap: passesIntercepted
is the DEFENSE's picks; the offense's own are interceptions (turnovers = fumblesLost +
interceptions checks it)."""
import os
HERE=os.path.dirname(os.path.abspath(__file__)); RAW=os.path.join(HERE,"data","raw","teams")
import json,csv,math
rows=[]
def rec(lg,y,t,d,nfl_cstyle=None):
    pass
for y in range(2014,2026):
    T={}
    for x in json.load(open(os.path.join(RAW,f'cfb{y}.json'))):
        T.setdefault(x['team'],{})[x['statName']]=float(x['statValue'])
    for t,s in T.items():
        if s.get('games',0)<8: continue
        ra,pa,sk=s['rushingAttempts'],s['passAttempts'],s.get('sacksOpponent',0)
        plays=ra+pa  # college: sacks are inside rushing attempts
        rows.append(dict(lg='CFB',year=y,team=t,
          ypc=s['rushingYards']/ra, rtd=s['rushingTDs']/ra,
          ypa=s['netPassingYards']/pa, comp=s['passCompletions']/pa, ptd=s['passingTDs']/pa,
          int=s['interceptions']/pa,
          sack=sk/(pa+sk), third=s['thirdDownConversions']/s['thirdDowns'],
          fdpp=s['firstDowns']/plays, fum=s['fumblesLost']/plays, runshare=ra/plays,
          ypc_nfl=float('nan')))
for y in range(2014,2026):
    for s in csv.DictReader(open(os.path.join(RAW,f'nfl{y}.csv'))):
        f=lambda k: float(s[k] or 0)
        ra,pa,sk=f('carries'),f('attempts'),f('sacks_suffered')
        plays=ra+pa+sk
        fd=f('passing_first_downs')+f('rushing_first_downs')
        rows.append(dict(lg='NFL',year=y,team=s['team'],
          ypc=(f('rushing_yards')+f('sack_yards_lost'))/(ra+sk),   # college definition
          ypc_nfl=f('rushing_yards')/ra,                               # NFL's own definition
          rtd=f('rushing_tds')/(ra+sk), ypa=f('passing_yards')/pa, comp=f('completions')/pa,
          ptd=f('passing_tds')/pa, int=f('passing_interceptions')/pa, sack=sk/(pa+sk),
          third=float('nan'), fdpp=fd/plays, fum=f('fumbles_lost_total')/plays, runshare=(ra+sk)/plays))
w=csv.DictWriter(open(os.path.join(HERE,'data','teams.csv'),'w'),fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
import collections;print(collections.Counter(r['lg'] for r in rows))
for lg in ['CFB','NFL']:
    R=[r for r in rows if r['lg']==lg]
    for k in ['ypc','ypc_nfl','sack','ypa','comp','int']:
        v=[r[k] for r in R if r[k]==r[k]]; 
        if not v: continue
        m=sum(v)/len(v); print(lg,k,round(m,3),round((sum((a-m)**2 for a in v)/len(v))**.5,3))
