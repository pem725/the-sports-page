import json,os,gzip,urllib.request,sys
API="https://apinext.collegefootballdata.com"
for path,out in (("/games?year=1936","raw/cfb-games-1936.json.gz"),("/rankings?year=1936","raw/cfb-rank-1936.json.gz")):
    if os.path.exists(out): continue
    r=urllib.request.urlopen(urllib.request.Request(API+path,headers={"Authorization":"Bearer "+os.environ["CFBD_KEY"],"User-Agent":"thesportspage.net"}),timeout=120)
    print(path,"remaining",r.headers.get("X-CallLimit-Remaining"),file=sys.stderr); gzip.open(out,"wt").write(r.read().decode())
