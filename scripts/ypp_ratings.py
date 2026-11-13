#!/usr/bin/env python3
"""Yards per play, offense and defense, adjusted for the schedule.

Set by the editor 2026-11-12: yards per play is one of the best predictors in football,
and yards against a top defense should count for more than yards against a weak one.

THE MODEL. Every team-game is one row: the offense's yards per play in that game.
    ypp = league average + offense(team) + defense(opponent) + home edge
fit by least squares, each row weighted by its plays. A defense that allows 4 yards a play
to everybody makes 6 yards against it worth more than 6 against a defense that allows 7.
Every team's two numbers are pulled toward average by one game's worth of plays (ridge),
so a team with five games is not read as precisely as one with ten. Chosen by the test
below: between half a game and two games of shrinkage the test barely moves.

THE TEST, printed with the numbers because the card must not print an untested rate.
Walk forward through the season: fit on games through week k, then use each team's
adjusted net yards per play (offense minus defense) to call week k+1's winners. The same is
done with points (the same model on points scored), so a reader can see whether yards per
play earns its place. Through week 10 of 2026 college: both called about 66 of every 100
next-week winners, and yards per play adds information points do not have.

Sources, cross-checked 2026-11-12 (all 18 Indiana team-games, CFBD vs ESPN: yards and
plays identical but one yard in one game):
  college  CollegeFootballData /games/teams, one call per week (cached; only the last
           two weeks are refetched each day). Plays = rushing attempts + pass attempts;
           college counts sacks as runs, so sacks are in.
  NFL      nflverse play-by-play: every pass (sacks included) and run.

Output: data/ypp-ratings.json, read by game.html and the programs. Keys are ESPN team ids,
which CFBD shares. A failed league keeps yesterday's numbers.

    python3 scripts/ypp_ratings.py            # both leagues
    python3 scripts/ypp_ratings.py --only cfb
"""
import argparse, csv, datetime as dt, gzip, io, json, os, sys, urllib.request
from collections import defaultdict
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "ypp-ratings.json")
CACHE = os.path.join(REPO, "data", "ypp-cfb-games.json")
CFBD = "https://api.collegefootballdata.com"
PBP = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{y}.csv.gz"
ESPN_NFL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
LAM = 1.0  # shrinkage, in games' worth of plays

# nflverse abbreviations that differ from ESPN's
NFLV_TO_ESPN = {"LA": "LAR", "WAS": "WSH"}


def fetch(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "thesportspage.net", **(headers or {})})
    return urllib.request.urlopen(req, timeout=90).read()


def cfbd(path):
    return json.loads(fetch(CFBD + path, {"Authorization": "Bearer " + os.environ["CFBD_KEY"]}))


# A row: (week, team_id, opp_id, home, plays, yards, points, opp_points)
#   home is +1 at home, -1 away, 0 at a neutral site.

def fit(rows, stat="ypp", lam=LAM):
    """Least squares with ridge. Returns (mean, offense, defense, home) with offense and
    defense as offsets from the mean, keyed by team id."""
    teams = sorted({r[1] for r in rows} | {r[2] for r in rows})
    ix = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    X = np.zeros((len(rows), 2 * n + 1))
    y = np.zeros(len(rows))
    w = np.ones(len(rows))
    for k, r in enumerate(rows):
        X[k, ix[r[1]]] = 1
        X[k, n + ix[r[2]]] = 1
        X[k, 2 * n] = r[3]
        if stat == "ypp":
            y[k], w[k] = r[5] / r[4], r[4]
        else:
            y[k] = r[6]
    mu = float(np.average(y, weights=w))
    sw = np.sqrt(w)
    A, b = X * sw[:, None], (y - mu) * sw
    pen = lam * float(np.mean(w))
    beta = np.linalg.solve(A.T @ A + pen * np.eye(2 * n + 1), A.T @ b)
    return mu, {t: beta[ix[t]] for t in teams}, {t: beta[n + ix[t]] for t in teams}, float(beta[2 * n])


def walk_forward(rows, ranked, first_week):
    """Call each week's winners from the games before it. Returns counts, never rates alone."""
    out = {"ypp": [0, 0], "points": [0, 0], "r_ypp": None, "r_points": None}
    xs, ps, ys = [], [], []
    last = max(r[0] for r in rows)
    for k in range(first_week, last):
        past = [r for r in rows if r[0] <= k]
        nxt = [r for r in rows if r[0] == k + 1 and r[3] >= 0 and r[1] in ranked and r[2] in ranked
               and r[6] != r[7]]
        if not nxt:
            continue
        _, o, d, h = fit(past)
        _, po, pd, ph = fit(past, "points")
        for r in nxt:
            a, b = r[1], r[2]
            if a not in o or b not in o:
                continue
            x = (o[a] + d[b]) - (o[b] + d[a]) + 2 * h * r[3]
            p = (po[a] + pd[b]) - (po[b] + pd[a]) + 2 * ph * r[3]
            m = r[6] - r[7]
            out["ypp"][0] += (x > 0) == (m > 0); out["ypp"][1] += 1
            out["points"][0] += (p > 0) == (m > 0); out["points"][1] += 1
            xs.append(x); ps.append(p); ys.append(m)
    if len(ys) > 20:
        out["r_ypp"] = round(float(np.corrcoef(xs, ys)[0, 1]), 2)
        out["r_points"] = round(float(np.corrcoef(ps, ys)[0, 1]), 2)
    out["ypp"] = {"right": int(out["ypp"][0]), "n": out["ypp"][1]}
    out["points"] = {"right": int(out["points"][0]), "n": out["points"][1]}
    out["weeks"] = [first_week + 1, last]
    return out


def summarize(rows, names, ranked):
    mu, o, d, h = fit(rows)
    raw_o, raw_d = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    games = defaultdict(int)
    for r in rows:
        raw_o[r[1]][0] += r[5]; raw_o[r[1]][1] += r[4]
        raw_d[r[2]][0] += r[5]; raw_d[r[2]][1] += r[4]
        games[r[1]] += 1
    pool = [t for t in ranked if t in o]
    rank_o = {t: i + 1 for i, t in enumerate(sorted(pool, key=lambda t: -o[t]))}
    rank_d = {t: i + 1 for i, t in enumerate(sorted(pool, key=lambda t: d[t]))}
    teams = {}
    for t in pool:
        teams[str(t)] = {"name": names.get(t, str(t)), "games": games[t],
                         "off": round(mu + o[t], 1), "def": round(mu + d[t], 1),
                         "offRaw": round(raw_o[t][0] / raw_o[t][1], 1), "defRaw": round(raw_d[t][0] / raw_d[t][1], 1),
                         "offRank": rank_o[t], "defRank": rank_d[t]}
    return {"mean": round(mu, 1), "home": round(h, 2), "of": len(pool),
            "through_week": max(r[0] for r in rows), "teams": teams}


def slim(g):
    """Keep only what the model reads: [id, [[team id, name, home/away, plays, yards, points], ...]]."""
    T = []
    for t in g["teams"]:
        st = {s["category"]: s["stat"] for s in t["stats"]}
        try:
            plays = int(st["rushingAttempts"]) + int(st["completionAttempts"].split("-")[1])
            T.append([t["teamId"], t["team"], t["homeAway"], plays, int(st["totalYards"]), t["points"]])
        except (KeyError, ValueError, IndexError):
            return [g["id"], []]
    return [g["id"], T]


def cfb(year):
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    if cache.get("year") != year:
        cache = {"year": year, "weeks": {}}
    games = cfbd(f"/games?year={year}&seasonType=regular")
    info = {g["id"]: g for g in games}
    done = sorted({g["week"] for g in games if g.get("completed")})
    for w in done:
        # Refetch the last two completed weeks: late stat corrections land there.
        if str(w) not in cache["weeks"] or w >= done[-1] - 1:
            cache["weeks"][str(w)] = [slim(g) for g in cfbd(f"/games/teams?year={year}&week={w}&classification=fbs")]
    json.dump(cache, open(CACHE, "w"), separators=(",", ":"))

    rows, names = [], {}
    fbs = {g["homeId"] for g in games if g.get("homeClassification") == "fbs"} | \
          {g["awayId"] for g in games if g.get("awayClassification") == "fbs"}
    for w, week in cache["weeks"].items():
        for gid, T in week:
            gm = info.get(gid)
            if not gm or len(T) != 2 or min(T[0][3], T[1][3]) == 0:
                continue
            for t in T:
                names[t[0]] = t[1]
            T = [(t[0], t[2], t[3], t[4], t[5]) for t in T]
            for a, b in ((0, 1), (1, 0)):
                home = 0 if gm.get("neutralSite") else (1 if T[a][1] == "home" else -1)
                rows.append((gm["week"], T[a][0], T[b][0], home, T[a][2], T[a][3], T[a][4], T[b][4]))
    out = summarize(rows, names, fbs)
    out["test"] = walk_forward(rows, fbs, 4)
    out["source"] = "CollegeFootballData team box scores; FBS ranks"
    return out


def nfl(year):
    espn = json.loads(fetch(ESPN_NFL))["sports"][0]["leagues"][0]["teams"]
    ids = {t["team"]["abbreviation"]: t["team"]["id"] for t in espn}
    names = {t["team"]["id"]: t["team"]["shortDisplayName"] for t in espn}
    g = {}
    data = csv.DictReader(io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(fetch(PBP.format(y=year)))), "utf-8"))
    for r in data:
        if r["season_type"] != "REG":
            continue
        x = g.setdefault(r["game_id"], {"week": int(r["week"]), "home": r["home_team"], "away": r["away_team"],
                                        "neutral": r.get("location") == "Neutral",
                                        "yds": defaultdict(float), "plays": defaultdict(int), "final": None})
        if r["home_score"] and r["away_score"]:
            x["final"] = (int(r["home_score"]), int(r["away_score"]))
        if r["play_type"] in ("pass", "run") and r["posteam"] and r["yards_gained"]:
            x["yds"][r["posteam"]] += float(r["yards_gained"])
            x["plays"][r["posteam"]] += 1
    rows = []
    for x in g.values():
        if not x["final"] or not all(x["plays"][t] for t in (x["home"], x["away"])):
            continue
        tid = {s: ids[NFLV_TO_ESPN.get(x[s], x[s])] for s in ("home", "away")}
        pts = {"home": x["final"][0], "away": x["final"][1]}
        for s, o in (("home", "away"), ("away", "home")):
            home = 0 if x["neutral"] else (1 if s == "home" else -1)
            rows.append((x["week"], tid[s], tid[o], home, x["plays"][x[s]], x["yds"][x[s]], pts[s], pts[o]))
    out = summarize(rows, names, set(names))
    out["test"] = walk_forward(rows, set(names), 3)
    out["source"] = "nflverse play-by-play (passes, sacks and runs)"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["cfb", "nfl"])
    a = ap.parse_args()
    today = dt.date.today()
    year = today.year if today.month >= 8 else today.year - 1
    data = json.load(open(OUT)) if os.path.exists(OUT) else {}
    failed = []
    for lg, fn in (("cfb", cfb), ("nfl", nfl)):
        if a.only and a.only != lg:
            continue
        try:
            data[lg] = fn(year)
            t = data[lg]["test"]
            print(f"{lg}: {len(data[lg]['teams'])} teams through week {data[lg]['through_week']}; "
                  f"next-week winners, yards per play {t['ypp']['right']}/{t['ypp']['n']}, "
                  f"points {t['points']['right']}/{t['points']['n']} (r {t['r_ypp']} vs {t['r_points']})")
        except Exception as e:  # keep yesterday's numbers for this league
            print(f"{lg}: FAILED ({e}); keeping the previous numbers", file=sys.stderr)
            failed.append(lg)
    data["season"], data["built"] = year, today.isoformat()
    json.dump(data, open(OUT, "w"), indent=1)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
