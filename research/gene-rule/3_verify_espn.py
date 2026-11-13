#!/usr/bin/env python3
"""Second feed for the 2026 Gene-team counts: ESPN drive charts, same definition.
Prints each team's answered/chances from ESPN beside nflverse's."""
import json, os, re, urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SB = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=2&week={w}&dates=2026"
SUM = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={e}"
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "sports-page"}), timeout=30))
FIX = {"WSH": "WAS", "LAR": "LA"}


def secs(clock):
    m, s = clock.split(":"); return int(m) * 60 + int(s)


cnt = defaultdict(lambda: [0, 0])
for w in range(1, 19):
    evs = [e for e in get(SB.format(w=w))["events"] if e["status"]["type"]["completed"]]
    for e in evs:
        d = get(SUM.format(e=e["id"])).get("drives", {}).get("previous", [])
        for i in range(1, len(d)):
            p, c = d[i - 1], d[i]
            per = c["start"]["period"]["number"]
            if per > 4 or p["start"]["period"]["number"] > 4:
                continue
            if (per <= 2) != (p["end"]["period"]["number"] <= 2):
                continue
            left = secs(c["start"]["clock"]["displayValue"]) + (900 if per in (1, 3) else 0)
            if left < 120:
                continue
            res = (p.get("result") or p.get("displayResult") or "").upper()
            pt, ct = FIX.get(p["team"]["abbreviation"], p["team"]["abbreviation"]), FIX.get(c["team"]["abbreviation"], c["team"]["abbreviation"])
            scorer = pt if res == "TD" else (ct if re.search(r"(INT|FUMBLE|PUNT|BLOCKED).*TD", res) else None)
            if scorer and scorer != ct:
                cr = (c.get("result") or c.get("displayResult") or "").upper()
                cnt[ct][1] += 1
                cnt[ct][0] += cr in ("TD", "FG")
mine = {t["team"]: (t["made"], t["n"]) for t in json.load(open(os.path.join(HERE, "data", "nfl-2026.json")))["teams"]}
for t in sorted(mine, key=lambda t: -mine[t][0] / max(mine[t][1], 1)):
    print(f"{t:4s} nflverse {mine[t][0]:2d}/{mine[t][1]:2d}   ESPN {cnt[t][0]:2d}/{cnt[t][1]:2d}")

# records, second feed
st = get("https://site.api.espn.com/apis/v2/sports/football/nfl/standings?season=2026")
espn_rec = {}
def walk(n):
    for c in n.get("children", []): walk(c)
    for e in n.get("standings", {}).get("entries", []):
        v = {x["name"]: x.get("value") for x in e["stats"]}
        a = FIX.get(e["team"]["abbreviation"], e["team"]["abbreviation"])
        espn_rec[a] = [int(v.get("wins", 0)), int(v.get("losses", 0)), int(v.get("ties", 0))]
walk(st)
mine = {t["team"]: t["rec"] for t in json.load(open(os.path.join(HERE, "data", "nfl-2026.json")))["teams"]}
bad = {t: (mine[t], espn_rec.get(t)) for t in mine if mine[t] != espn_rec.get(t)}
print("records differing from ESPN:", bad or "none")
json.dump(dict(counts=cnt, records=espn_rec), open(os.path.join(HERE, "data", "nfl-2026-espn.json"), "w"))
