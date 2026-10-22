import os, sys, json, urllib.request, pathlib
D = pathlib.Path(sys.argv[0]).resolve().parent / "cache"
log = D / "calls.log"
chunks = [(int(a), int(b)) for a, b in (c.split("-") for c in sys.argv[1:])]
for a, b in chunks:
    f = D / f"coaches_{a}_{b}.json"
    if f.exists():
        print("cached", f.name); continue
    req = urllib.request.Request(f"https://api.collegefootballdata.com/coaches?minYear={a}&maxYear={b}",
        headers={"Authorization": "Bearer " + os.environ["CFBD_KEY"], "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            rem = r.headers.get("X-CallLimit-Remaining"); data = r.read()
            f.write_bytes(data)
            msg = f"{a}-{b} status={r.status} remaining={rem} n={len(json.loads(data))}"
    except urllib.error.HTTPError as e:
        msg = f"{a}-{b} HTTPError {e.code} remaining={e.headers.get('X-CallLimit-Remaining')}"
    print(msg)
    with open(log, "a") as L: L.write(msg + "\n")
