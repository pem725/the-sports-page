import json, urllib.request, urllib.parse, time, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from wiki import UA
D = pathlib.Path(__file__).resolve().parent
f = D/'wiki/search.json'
store = json.load(open(f)) if f.exists() else {}
for cid,n,schools in json.load(open(D/'unresolved.json')):
    key=str(cid)
    if key in store: continue
    q = f'{n} football coach {schools[0]}'
    u = "https://en.wikipedia.org/w/api.php?"+urllib.parse.urlencode({"action":"query","list":"search","srsearch":q,"srlimit":"5","format":"json"})
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":UA}), timeout=60) as r:
        store[key] = [h["title"] for h in json.load(r)["query"]["search"]]
    json.dump(store, open(f,"w")); time.sleep(0.5)
print(len(store))
