import json, urllib.request, urllib.parse, pathlib, time, hashlib
D = pathlib.Path(__file__).resolve().parent/"wiki"
UA = "TheSportsPage-research/1.0 (https://thesportspage.net; ideas@thesportspage.net)"
STORE = D/"pages.json"
def load():
    return json.load(open(STORE)) if STORE.exists() else {}
def fetch(titles):
    """returns dict requested_title -> {'title':final, 'text':wikitext or None}"""
    store = load()
    todo = [t for t in dict.fromkeys(titles) if t not in store]
    for i in range(0, len(todo), 50):
        batch = todo[i:i+50]
        q = urllib.parse.urlencode({"action":"query","prop":"revisions","rvprop":"content","rvslots":"main",
             "redirects":"1","format":"json","formatversion":"2","titles":"|".join(batch)})
        req = urllib.request.Request("https://en.wikipedia.org/w/api.php?"+q, headers={"User-Agent":UA})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r: data = json.load(r); break
            except Exception as e:
                print("retry", e); time.sleep(5*(attempt+1))
        if "continue" in data: print("WARN continue present", data["continue"])
        qd = data["query"]
        m = {t:t for t in batch}
        for n in qd.get("normalized",[]):
            for k,v in m.items():
                if v==n["from"]: m[k]=n["to"]
        for rd in qd.get("redirects",[]):
            for k,v in m.items():
                if v==rd["from"]: m[k]=rd["to"]
        pages = {p["title"]:p for p in qd["pages"]}
        for t in batch:
            p = pages.get(m[t])
            txt = None
            if p and not p.get("missing") and p.get("revisions"):
                txt = p["revisions"][0]["slots"]["main"].get("content")
            store[t] = {"title": m[t], "text": txt}
        json.dump(store, open(STORE,"w"))
        time.sleep(1)
    return {t: store[t] for t in titles}

RSTORE = D/"resolve.json"
def resolve(titles):
    store = json.load(open(RSTORE)) if RSTORE.exists() else {}
    todo = [t for t in dict.fromkeys(titles) if t and t not in store]
    for i in range(0, len(todo), 50):
        batch = todo[i:i+50]
        q = urllib.parse.urlencode({"action":"query","redirects":"1","format":"json","formatversion":"2","titles":"|".join(batch)})
        req = urllib.request.Request("https://en.wikipedia.org/w/api.php?"+q, headers={"User-Agent":UA})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r: data = json.load(r); break
            except Exception as e:
                print("retry", e); time.sleep(5*(attempt+1))
        qd = data["query"]; m = {t:t for t in batch}
        for key in ("normalized","redirects"):
            for n in qd.get(key,[]):
                for k,v in m.items():
                    if v==n["from"]: m[k]=n["to"]
        # strip section anchors
        for t in batch: store[t] = m[t].split("#")[0]
        json.dump(store, open(RSTORE,"w")); time.sleep(1)
    return {t: store.get(t, t) for t in titles}
