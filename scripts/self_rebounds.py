#!/usr/bin/env python3
"""Self-rebounds ("mebounds"): offensive rebounds off the rebounder's own miss.

Tim's question, 2026-10-26: what share of Angel Reese's rebounds came off her
own missed shots? He arrived with an AI-written brief whose ranges contradicted
its own counts. Nobody publishes the stat, so this counts it from ESPN
play-by-play, for every player in the league, so a number has something to be
compared against.

How a rebound is attributed: walk back from each offensive rebound to the last
shot, block or rebound. "X misses ..." makes X the shooter; "Y blocks X 's ..."
also makes X the shooter, because a blocked shot is a missed field goal in the
box score. The --plain flag drops the blocked ones, the one judgment call here.

Checks itself: each player's play-by-play offensive rebounds are compared with
the ESPN box score, and the mismatch count is printed. 2026: 5,615 of 5,615
league-wide, six players off by one.

Usage:
  python3 scripts/self_rebounds.py                     # 2026 regular season, top 15
  python3 scripts/self_rebounds.py --player "Angel Reese"
  python3 scripts/self_rebounds.py --season 2025 --min-oreb 60 --plain
"""
import argparse, collections, datetime as dt, json, os, re, statistics, time, urllib.request

API = "https://site.api.espn.com/apis/site/v2/sports/basketball/wnba"
CACHE = os.path.expanduser("~/.cache/sports-page/wnba-pbp")


def get(url):
    req = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
    for _ in range(3):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=30).read())
        except (OSError, ValueError):
            time.sleep(3)
    return None


def season_games(season):
    """Regular-season finals, one scoreboard call a day (ESPN refuses date ranges)."""
    f = os.path.join(CACHE, f"games-{season}.json")
    if os.path.exists(f):
        return json.load(open(f))
    ids, d = [], dt.date(season, 5, 1)
    while d <= dt.date(season, 9, 30):
        for e in (get(f"{API}/scoreboard?dates={d:%Y%m%d}") or {}).get("events", []):
            # season type 2 is the regular season; the All-Star Game rides along and is dropped in tally()
            if e["season"]["type"] == 2 and e["status"]["type"]["name"] == "STATUS_FINAL":
                ids.append(e["id"])
        d += dt.timedelta(days=1)
    json.dump(ids, open(f, "w"))
    return ids


def summary(gid):
    f = os.path.join(CACHE, f"{gid}.json")
    if not os.path.exists(f):
        d = get(f"{API}/summary?event={gid}")
        if not d or "plays" not in d:
            return None
        json.dump(d, open(f, "w"))
        time.sleep(0.25)
    return json.load(open(f))


def tally(games, plain):
    P = collections.defaultdict(collections.Counter)
    name, missing = {}, []
    for gid in games:
        d = summary(gid)
        if d is None:
            missing.append(gid); continue
        teams = [t["team"].get("abbreviation", "") for t in d["boxscore"].get("players", [])]
        if any(len(t) > 3 for t in teams):                   # All-Star exhibition squads
            continue
        for t in d["boxscore"]["players"]:
            for st in t["statistics"]:
                for a in st["athletes"]:
                    if not a.get("stats") or a.get("didNotPlay"):
                        continue
                    bx, i = dict(zip(st["keys"], a["stats"])), a["athlete"]["id"]
                    name[i] = a["athlete"]["displayName"]
                    fgm, fga = map(int, bx.get("fieldGoalsMade-fieldGoalsAttempted", "0-0").split("-"))
                    P[i].update(gp=1, oreb=int(bx.get("offensiveRebounds") or 0),
                                dreb=int(bx.get("defensiveRebounds") or 0), fgmiss=fga - fgm)
        plays = d["plays"]
        for k, p in enumerate(plays):
            parts = [x["athlete"]["id"] for x in p.get("participants", [])]
            if p["type"]["text"] != "Offensive Rebound" or not parts:
                continue
            r = parts[0]
            P[r]["oreb_pbp"] += 1
            j = k - 1
            while j >= 0 and not (plays[j].get("shootingPlay") or "Rebound" in plays[j]["type"]["text"]
                                  or " blocks " in plays[j].get("text", "")):
                j -= 1
            t = plays[j]["text"] if j >= 0 else ""
            blk = re.match(r".+? blocks (.+?) ?'s ", t)
            shooter = blk.group(1).strip() if blk else t.split(" misses ")[0].strip() if " misses " in t else None
            if shooter and shooter == name.get(r) and not (plain and blk):
                P[r]["self"] += 1
                P[r]["self_blocked"] += bool(blk)
    return P, name, missing


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--min-oreb", type=int, default=60)
    ap.add_argument("--player")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--plain", action="store_true", help="do not count rebounds of the player's own blocked shot")
    a = ap.parse_args()
    os.makedirs(CACHE, exist_ok=True)
    P, name, missing = tally(season_games(a.season), a.plain)

    oreb = sum(c["oreb"] for c in P.values()); own = sum(c["self"] for c in P.values())
    off = sum(1 for c in P.values() if c["oreb"] != c["oreb_pbp"])
    print(f"{a.season}: {oreb} offensive rebounds, {own} off the rebounder's own miss ({own / oreb:.0%})"
          f"{' (blocked shots excluded)' if a.plain else ''}")
    print(f"box vs play-by-play: {off} player(s) disagree; games ESPN could not serve: {missing or 'none'}\n")

    rows = [dict(n=name[i], **c) for i, c in P.items() if i in name]
    q = sorted((r for r in rows if r["oreb"] >= a.min_oreb), key=lambda r: -r["self"])
    print(f"{len(q)} players with {a.min_oreb}+ offensive rebounds; "
          f"median share of their offensive rebounds that were their own: "
          f"{statistics.median(r['self'] / r['oreb'] for r in q):.0%}\n")
    show = [r for r in rows if r["n"] == a.player] if a.player else q[:a.top]
    print(f"{'player':<22}{'GP':>4}{'REB':>5}{'OREB':>5}{'own':>5}{'blk':>5}  {'of OREB':>8}{'of REB':>8}{'own misses back':>17}")
    for r in show:
        reb = r["oreb"] + r["dreb"]
        print(f"{r['n']:<22}{r['gp']:>4}{reb:>5}{r['oreb']:>5}{r['self']:>5}{r['self_blocked']:>5}  "
              f"{r['self'] / max(r['oreb'], 1):>8.0%}{r['self'] / max(reb, 1):>8.0%}{r['self'] / max(r['fgmiss'], 1):>17.0%}")


if __name__ == "__main__":
    main()
