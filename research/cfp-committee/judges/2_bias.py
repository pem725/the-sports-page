import json, random, collections
import numpy as np
R=json.load(open("rows.json"))
def grp(c):
    if c in ("SEC","Big Ten","ACC","Big 12","Pac-12"): return c
    if c=="FBS Independents": return "Indep"
    return "Group of 5"
def gap(r,col="cfp"):
    m=min(r["math"],26); c=r[col] if r[col] else 26
    return m-c
def table(rows,col,label):
    by=collections.defaultdict(list)
    for r in rows: by[(grp(r["conf"]))].append(r)
    print(f"\n{label}: spots the judges put a team ABOVE the math (both capped at 26)")
    for g,rs in sorted(by.items(),key=lambda x:-np.mean([gap(r,col) for r in x[1]])):
        # cluster bootstrap over team-seasons
        cl=collections.defaultdict(list)
        for r in rs: cl[(r["team"],r["year"])].append(gap(r,col))
        keys=list(cl); bs=[]
        random.seed(1)
        for _ in range(2000):
            s=[v for k in random.choices(keys,k=len(keys)) for v in cl[k]]; bs.append(np.mean(s))
        print(f"  {g:<11} {np.mean([gap(r,col) for r in rs]):+5.1f}  [{np.percentile(bs,2.5):+.1f},{np.percentile(bs,97.5):+.1f}]  n={len(rs)} rankings, {len(keys)} team-seasons")
hist=[r for r in R if r["year"]<2026]
table(hist,"cfp","Committee 2014-2025")
table([r for r in hist if r["ap"] is not None or r["cfp"] or r["math"]<=25],"ap","AP poll, same weeks")
table([r for r in R if r["year"]==2026],"cfp","Committee 2026 (3 rankings)")
