import json,csv,pathlib
from collections import defaultdict
D = pathlib.Path(__file__).resolve().parent
yrs=defaultdict(list)
for r in csv.DictReader(open(D/'seasons.csv')): yrs[(int(r['cid']),r['school'])].append(int(r['year']))
F=json.load(open(D/'wiki_parsed.json'))
for x in F:
    for s in x['coached']:
        y=yrs[(x['cid'],s)]
        if max(y)<1970: continue
        if s in x['played']:
            print("P", x['name'],'|',s, min(y),max(y),'| played',x['played_years'].get(s),x['src'][s],'|',x['wiki'])
        elif s in x['alma']:
            print("A", x['name'],'|',s, min(y),max(y),'|',x['wiki'])
