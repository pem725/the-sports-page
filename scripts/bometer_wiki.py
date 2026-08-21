import json, os, time, urllib.request, urllib.parse, math, statistics as st
CACHE=os.path.join(os.path.dirname(os.path.abspath(__file__)),"cache")
UA="TheSportsPage/1.0 (pem725@gmail.com) research"
rows=json.load(open(os.path.join(CACHE,"teamrows.json")))
# Wikipedia titles are not the API team names. "Texas Rangers" is a
# disambiguation-adjacent article about the law-enforcement agency; the club is
# "Texas Rangers (baseball)". Caught because its 93,333 views were two orders of
# magnitude below every other club -- a validity check, not a guess.
ALIAS={"Athletics":"Oakland_Athletics",
       "Texas Rangers":"Texas_Rangers_(baseball)"}
def views(title):
    key="wiki_"+title.replace("/","_")
    p=os.path.join(CACHE,key+".json")
    if os.path.exists(p): return json.load(open(p))
    url=("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
         f"all-access/user/{urllib.parse.quote(title,safe='')}/monthly/2021010100/2026083100")
    req=urllib.request.Request(url, headers={"User-Agent":UA})
    for a in range(3):
        try:
            d=json.load(urllib.request.urlopen(req,timeout=60)); json.dump(d,open(p,"w")); return d
        except Exception as e:
            if a==2: return None
            time.sleep(2)
out=[]
for r in rows:
    t=ALIAS.get(r["team"], r["team"].replace(" ","_"))
    d=views(t)
    if not d or not d.get("items"): print("  MISS", r["team"]); continue
    tot=sum(x["views"] for x in d["items"])
    out.append(dict(**r, wiki=tot, months=len(d["items"]), title=t))
    time.sleep(0.12)
json.dump(out, open(os.path.join(CACHE,"teamwiki.json"),"w"))
print(f"{len(out)} teams with pageviews\n")
bo=[x["bo"] for x in out]; wv=[math.log10(x["wiki"]) for x in out]
mb,mw=st.mean(bo),st.mean(wv)
r_=sum((a-mb)*(b-mw) for a,b in zip(bo,wv))/math.sqrt(sum((a-mb)**2 for a in bo)*sum((b-mw)**2 for b in wv))
slope=sum((a-mb)*(b-mw) for a,b in zip(bo,wv))/sum((a-mb)**2 for a in bo)
print(f"correlation(bometer, log10 wiki views) r = {r_:+.3f}   n={len(out)}")
print(f"unstandardized: +1 bometer point = x{10**slope:.3f} pageviews  ({(10**slope-1)*100:+.1f}%)")
print("\n  most looked-up:"); 
for x in sorted(out,key=lambda x:-x["wiki"])[:5]: print(f"    {x['team']:<24} {x['wiki']:>10,}  bo {x['bo']:.1f}")
print("  least looked-up:")
for x in sorted(out,key=lambda x:x["wiki"])[:5]: print(f"    {x['team']:<24} {x['wiki']:>10,}  bo {x['bo']:.1f}")
