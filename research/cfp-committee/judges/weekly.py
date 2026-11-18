"""The Judges' Scorecard, weekly numbers. Run Tuesday night after the CFP ranking:

    set -a; . ~/.config/secrets/tokens.env; set +a
    python3 research/cfp-committee/judges/weekly.py --refresh    # 2 CFBD calls

Prints this week's table (committee vs bowl-corrected math), the movers, the biggest
gaps, and the season tally of who picked more winners: the committee's order or ours.
Writes weekly-<date>.json. The prose is written by a human from this output."""
import json, gzip, os, sys, subprocess, urllib.request, datetime
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
Y=2026
def fetch(path,out):
    r=urllib.request.urlopen(urllib.request.Request("https://apinext.collegefootballdata.com"+path,
        headers={"Authorization":"Bearer "+os.environ["CFBD_KEY"],"User-Agent":"thesportspage.net"}),timeout=120)
    print(path,"remaining",r.headers.get("X-CallLimit-Remaining"),file=sys.stderr)
    gzip.open(out,"wt").write(r.read().decode())
if "--refresh" in sys.argv:
    fetch(f"/games?year={Y}&seasonType=regular&classification=fbs",f"raw/games-{Y}.json.gz")
    fetch(f"/rankings?year={Y}&seasonType=regular",f"raw/rank-{Y}.json.gz")
env=dict(os.environ,G5PEN="6",SECB="3.5",OUT="rows_adj.json")
subprocess.run([sys.executable,"1_build.py"],env=env,check=True,stdout=subprocess.DEVNULL)
R=[r for r in json.load(open("rows_adj.json")) if r["year"]==Y]
weeks=sorted({r["week"] for r in R}); w=weeks[-1]; pw=weeks[-2] if len(weeks)>1 else None
cur={r["team"]:r for r in R if r["week"]==w}; prev={r["team"]:r for r in R if r["week"]==pw} if pw else {}
print(f"\nCFP ranking, CFBD week {w} (previous week {pw})")
print(f"{'CFP':>3} {'prev':>4} {'team':<17}{'rec':<6}{'math':>5}{'gap':>5}{'math move':>10}")
rows=[]
for t,r in sorted(cur.items(),key=lambda x:(x[1]["cfp"] or 99,x[1]["math"])):
    if not r["cfp"] and r["math"]>20: continue
    p=prev.get(t,{}); mm=(p.get("math")-r["math"]) if p.get("math") else None
    gap=(min(r["math"],26)-(r["cfp"] or 26))
    rows.append(dict(team=t,cfp=r["cfp"],prev=p.get("cfp"),rec=f'{r["w"]}-{r["l"]}',math=r["math"],gap=gap,math_move=mm,conf=r["conf"]))
    print(f'{r["cfp"] or "-":>3} {p.get("cfp") or "-":>4} {t:<17}{r["w"]}-{r["l"]:<4}{r["math"]:>5}{gap:>+5}{(mm if mm is not None else ""):>10}')
# who picked more winners: games after each ranking, until the next one, both teams in the union set
G=[g for g in json.load(gzip.open(f"raw/games-{Y}.json.gz")) if g["completed"] and g["homePoints"] is not None]
tally={"committee":[0,0],"math":[0,0]}; disagree=[]
for i,wk in enumerate(weeks):
    nxt=weeks[i+1] if i+1<len(weeks) else 99
    snap={r["team"]:r for r in R if r["week"]==wk}
    for g in G:
        if not (wk<=g["week"]<nxt): continue
        h,a=g["homeTeam"],g["awayTeam"]
        if h not in snap or a not in snap or g["homePoints"]==g["awayPoints"]: continue
        win=h if g["homePoints"]>g["awayPoints"] else a
        ch=min((h,a),key=lambda t:snap[t]["cfp"] or 26); mh=min((h,a),key=lambda t:snap[t]["math"])
        if (snap[h]["cfp"] or 26)!=(snap[a]["cfp"] or 26):
            tally["committee"][0]+=ch==win; tally["committee"][1]+=1
        tally["math"][0]+=mh==win; tally["math"][1]+=1
        if ch!=mh: disagree.append(dict(week=g["week"],game=f"{a} at {h}",committee=ch,math=mh,winner=win))
print("\nSeason tally, games between two teams in either top 25:")
for k,(a,b) in tally.items(): print(f"  {k:<10} picked {a} of {b}")
print("When they disagreed:")
for d in disagree: print(f"  wk{d['week']} {d['game']}: committee {d['committee']}, math {d['math']} -> {d['winner']}")
json.dump(dict(date=str(datetime.date.today()),week=w,rows=rows,tally=tally,disagree=disagree),open(f"weekly-{datetime.date.today()}.json","w"),indent=1)
