#!/usr/bin/env python3
"""Gene's Rule, hockey analog: every regular-season goal since 2015-16, from the NHL API.

One row per goal: game, season, date, period, seconds into the game, scoring team, the
two teams, the strength (situationCode: away goalie, away skaters, home skaters, home
goalie) and the final. Shootout "goals" are left out. Output: data/raw/nhl-goals-SSSS.csv.
"""
import concurrent.futures as cf, csv, json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
URL = "https://api-web.nhle.com/v1/gamecenter/{g}/play-by-play"


def secs(t):
    m, s = t.split(":")
    return int(m) * 60 + int(s)


def game(gid):
    for tries in range(4):
        try:
            req = urllib.request.Request(URL.format(g=gid), headers={"User-Agent": "sports-page-research"})
            d = json.load(urllib.request.urlopen(req, timeout=30))
            break
        except Exception as e:
            if getattr(e, "code", None) == 404:
                return None
            time.sleep(2 + 3 * tries)
    else:
        return None
    if d.get("gameState") not in ("OFF", "FINAL"):
        return None
    h, a = d["homeTeam"], d["awayTeam"]
    rows = []
    for p in d["plays"]:
        if p["typeDescKey"] != "goal":
            continue
        pd = p["periodDescriptor"]
        if pd.get("periodType") == "SO":
            continue
        t = (pd["number"] - 1) * 1200 + secs(p["timeInPeriod"])
        team = h["abbrev"] if p["details"].get("eventOwnerTeamId") == h["id"] else a["abbrev"]
        rows.append([gid, d["season"], d["gameDate"], pd["number"], t, team, h["abbrev"], a["abbrev"],
                     p.get("situationCode", ""), h.get("score"), a.get("score"),
                     (d.get("gameOutcome") or {}).get("lastPeriodType", "")])
    if not rows:  # a 0-0 into a shootout still counts as a game
        rows.append([gid, d["season"], d["gameDate"], "", "", "", h["abbrev"], a["abbrev"], "", h.get("score"),
                     a.get("score"), (d.get("gameOutcome") or {}).get("lastPeriodType", "")])
    return rows


def season(start):
    out = os.path.join(RAW, f"nhl-goals-{start}.csv")
    if os.path.exists(out) and start < 2026:
        return out
    n = 1312 if start >= 2021 else (1271 if start >= 2017 else 1230)
    if start == 2019: n = 1082
    if start == 2020: n = 868
    ids = [f"{start}02{i:04d}" for i in range(1, n + 1)]
    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(game, ids))
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["game", "season", "date", "period", "t", "team", "home", "away", "sit", "home_final", "away_final", "ended"])
        for r in res:
            for row in r or []:
                w.writerow(row)
    return out


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (2015, 2025)
    for s in range(a, b + 1):
        print(s, season(s), flush=True)
