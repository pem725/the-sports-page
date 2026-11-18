"""1936 major-college games from James Howell's pages (second feed), as team-games."""
import re,pathlib,html
P=pathlib.Path.home()/".cache/sports-page/howell/pages"
HDR=re.compile(r'<a name=(\d{4})>')
ROW=re.compile(r'<tr><td[^>]*>([\d/]+)</td><td[^>]*>(vs\.|@|n)[^<]*</td><td[^>]*>(?:<a[^>]*>)?([^<]*)(?:</a>)?([^<]*)</td><td[^>]*>([WLT])</td><td[^>]*>(\d+)</td><td[^>]*>(\d+)</td></tr>')
tg=[]
for f in P.glob("*.htm"):
    s=f.read_text(encoding="latin-1")
    hs=list(HDR.finditer(s))
    for i,h in enumerate(hs):
        if h.group(1)!="1936": continue
        seg=s[h.end(): hs[i+1].start() if i+1<len(hs) else len(s)]
        for m in ROW.finditer(seg):
            tg.append((f.stem,m.group(3),m.group(4),m.group(5),int(m.group(6)),int(m.group(7))))
maj=[t for t in tg if "non-IA" not in t[2]]
print(len(tg),"team-games;",len(maj),"vs major opponents ->",len(maj)//2,"games")
print("pts per team",round(sum(t[4] for t in maj)/len(maj),1),"ties",sum(t[3]=="T" for t in maj)//2,"shutouts (team-games held to 0)",sum(t[4]==0 for t in maj))
