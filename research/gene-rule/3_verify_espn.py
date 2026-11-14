#!/usr/bin/env python3
"""Second feed for the 2026 Gene-team counts: ESPN drive charts, same definition.
Prints each team's answered/chances from ESPN beside nflverse's."""
import csv, datetime, json, os, re, urllib.request
from zoneinfo import ZoneInfo
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SB = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=2&week={w}&dates=2026"
SUM = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={e}"
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "sports-page"}), timeout=30))
FIX = {"WSH": "WAS", "LAR": "LA"}


def secs(clock):
    m, s = clock.split(":"); return int(m) * 60 + int(s)


# Only games nflverse already has. Its play-by-play can trail ESPN by a night (Monday night
# especially), and comparing two different sets of games would fail on the lag, not an error.
NV = {(int(r["week"]), r["away"], r["home"]) for r in csv.DictReader(open(os.path.join(HERE, "data", "raw", "drives2026.csv")))}
ab = lambda c: FIX.get(c["team"]["abbreviation"], c["team"]["abbreviation"])
cnt = defaultdict(lambda: [0, 0])
game = defaultdict(lambda: [0, 0])  # (team, week) -> ESPN answered, chances
rec_same = defaultdict(lambda: [0, 0, 0])
last, lag = None, []
for w in range(1, 19):
    evs = [e for e in get(SB.format(w=w))["events"] if e["status"]["type"]["completed"]]
    for e in evs:
        cs = {c["homeAway"]: c for c in e["competitions"][0]["competitors"]}
        if (w, ab(cs["away"]), ab(cs["home"])) not in NV:
            lag.append(e["shortName"]); continue
        a, h = int(cs["away"]["score"]), int(cs["home"]["score"])
        for me, mine_pts, their in ((ab(cs["away"]), a, h), (ab(cs["home"]), h, a)):
            rec_same[me][0 if mine_pts > their else (1 if mine_pts < their else 2)] += 1
        day = datetime.datetime.fromisoformat(e["date"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York")).date()
        last = max(last or day, day)
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
                game[(ct, w)][1] += 1
                game[(ct, w)][0] += cr in ("TD", "FG")
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
# Records on the same games, from ESPN's scores. The standings must agree too whenever
# nflverse has caught up; while it lags they are one game ahead by design.
same = {t: list(v) for t, v in rec_same.items()}
bad = {t: (mine[t], same.get(t)) for t in mine if mine[t] != same.get(t)}
print("records differing from ESPN:", bad or "none")
if not lag:
    off = {t: (mine[t], espn_rec.get(t)) for t in mine if mine[t] != espn_rec.get(t)}
    print("records differing from ESPN standings:", off or "none")
else:
    print("nflverse has not caught up on:", ", ".join(lag))
# Game by game against nflverse. The piece claims agreement "within one drive in every game";
# season totals can drift further, one edge case (a safety, a split drive) per game at most.
import importlib.util
spec = importlib.util.spec_from_file_location("nfl", os.path.join(HERE, "1_nfl.py"))
nf = importlib.util.module_from_spec(spec); spec.loader.exec_module(nf)
nvg = defaultdict(lambda: [0, 0])
for ev in nf.events({g: d for g, d in nf.load().items() if g.startswith("2026_")}):
    if ev["kind"] == "answer":
        k = (ev["team"], int(ev["week"])); nvg[k][1] += 1; nvg[k][0] += ev["scored"]
keys = set(nvg) | set(game)
gap = {f"{t} wk{w}": (nvg[(t, w)], game[(t, w)]) for t, w in keys
       if max(abs(nvg[(t, w)][0] - game[(t, w)][0]), abs(nvg[(t, w)][1] - game[(t, w)][1])) > 0}
worst = max([max(abs(a[0] - b[0]), abs(a[1] - b[1])) for a, b in gap.values()] or [0])
print(f"games where the feeds differ: {len(gap)}; largest gap in one game: {worst} drive(s)")
M = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]
json.dump(dict(counts=cnt, game_gaps=gap, max_game_gap=worst, records=same, standings=espn_rec, lag=lag,
               through=f"{M[last.month - 1]} {last.day}", through_iso=last.isoformat()),
          open(os.path.join(HERE, "data", "nfl-2026-espn.json"), "w"))
