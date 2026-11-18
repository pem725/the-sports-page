#!/usr/bin/env python3
"""Gene's Rule, college football: CFBD drives, one call per season (regular season +
postseason), cached gzipped in data/raw/cfb-drives-YYYY.json.gz so nothing is fetched twice.
Also caches each season's games (for final scores, FBS membership and completion).

Quota: CFBD rate-limits per key and the 4:30am run shares it. Every call is logged to
data/raw/cfb-calls.log; the script stops if X-CallLimit-Remaining drops under 28,000 or
this script has made 250 calls in total.

Usage: python3 0_cfb_drives.py 2014 2026      (key read from os.environ["CFBD_KEY"])
"""
import gzip, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
API = "https://apinext.collegefootballdata.com"
LOG = os.path.join(RAW, "cfb-calls.log")
CAP, FLOOR = 250, 28000


def ncalls():
    return sum(1 for _ in open(LOG)) if os.path.exists(LOG) else 0


def get(path):
    if ncalls() >= CAP:
        sys.exit(f"call cap {CAP} reached")
    req = urllib.request.Request(API + path, headers={"Authorization": "Bearer " + os.environ["CFBD_KEY"],
                                                      "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        left = r.headers.get("X-CallLimit-Remaining")
        data = json.loads(r.read())
    with open(LOG, "a") as f:
        f.write(f"{path}\tremaining={left}\n")
    print(f"  GET {path}: {len(data)} rows, remaining {left}", flush=True)
    if left is not None and int(left) < FLOOR:
        sys.exit(f"quota floor: {left} left")
    return data


def cached(name, path, refresh=False):
    out = os.path.join(RAW, name)
    if os.path.exists(out) and not refresh:
        return json.load(gzip.open(out, "rt"))
    data = get(path)
    json.dump(data, gzip.open(out, "wt"))
    return data


def season(y, refresh=False):
    d = []
    g = []
    for st in (("regular",) if y >= 2026 else ("regular", "postseason")):
        d += cached(f"cfb-drives-{y}-{st}.json.gz", f"/drives?year={y}&seasonType={st}", refresh)
        g += cached(f"cfb-games-{y}-{st}.json.gz", f"/games?year={y}&seasonType={st}", refresh)
    return d, g


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    refresh = "--refresh" in sys.argv
    for y in range(a, b + 1):
        d, g = season(y, refresh and y == 2026)
        print(y, len(d), "drives", len(g), "games", flush=True)
