#!/usr/bin/env python3
"""World Series droughts against a fair lottery.

Question (editor, 2026-10-31): the Brewers' 2026 title leaves four clubs that
have never won a World Series (Mariners, Padres, Rays, Rockies), and one, the
Mariners, that has never played in one. How much of that is bad luck?

Two baselines, both computed on the real list of clubs in each season:

  1. LOTTERY FROM BIRTH. Every club in a league has the same chance of the
     pennant each season (1/N in its league) and of the title (1/N overall).
     This is what "it's all luck" would predict.
  2. LOTTERY ONCE YOU'RE IN. Only the club's actual playoff trips count, and
     each trip is a fair draw among that league's playoff field (1/k for the
     pennant, 1/K for the title). This separates getting there (the regular
     season, mostly skill) from winning once there (October, mostly luck).
     The 2012-2021 wild-card game losers count as playoff trips, which is
     slightly generous to them.

Sources
  * Lahman Baseball Database, Teams table 1903-2025 (R package build, cached
    by scripts/work_stoppages.py at ~/.cache/sports-page/stoppages/raw/).
  * 2026 from the MLB Stats API: regular-season standings and the postseason
    series list (Brewers beat the Rays 4-1, final game 2026-10-28).

Seasons with no World Series (1904, 1994) give no title draw; 1904 still
gives a pennant draw, 1994 gives neither.

Usage:  python3 scripts/ws_droughts.py        (writes data/ws-droughts/)
"""
import csv, json, math, pathlib, random, urllib.request
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ws-droughts"
LAHMAN = pathlib.Path.home() / ".cache/sports-page/stoppages/raw/Teams_Rlahman.csv"
API = "https://statsapi.mlb.com/api/v1/"
NO_WS = {1904, 1994}
NSIM = 100_000

# MLB Stats API short names (2026) -> Lahman franchID
API2FR = {"Rays": "TBD", "Yankees": "NYY", "Red Sox": "BOS", "Orioles": "BAL",
          "Blue Jays": "TOR", "Guardians": "CLE", "White Sox": "CHW", "Twins": "MIN",
          "Tigers": "DET", "Royals": "KCR", "Astros": "HOU", "Rangers": "TEX",
          "Mariners": "SEA", "Athletics": "OAK", "Angels": "ANA", "Braves": "ATL",
          "Phillies": "PHI", "Marlins": "FLA", "Nationals": "WSN", "Mets": "NYM",
          "Brewers": "MIL", "Cubs": "CHC", "Pirates": "PIT", "Cardinals": "STL",
          "Reds": "CIN", "Dodgers": "LAD", "Padres": "SDP", "D-backs": "ARI",
          "Giants": "SFG", "Rockies": "COL"}


def get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": "TheSportsPage-research/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def load_rows():
    if not LAHMAN.exists():
        raise SystemExit("missing %s -- run scripts/work_stoppages.py --fetch first" % LAHMAN)
    rows = []
    for x in csv.DictReader(open(LAHMAN)):
        y = int(x["yearID"])
        if y < 1903 or x["lgID"] not in ("AL", "NL"):
            continue
        rows.append(dict(year=y, lg=x["lgID"], fr=x["franchID"], name=x["name"],
                         w=int(x["W"]), l=int(x["L"]),
                         playoff=int("Y" in (x["DivWin"], x["WCWin"], x["LgWin"])),
                         pennant=int(x["LgWin"] == "Y"), title=int(x["WSWin"] == "Y")))
    # 2026 from MLB's own feeds
    lg_of = {r["fr"]: r["lg"] for r in rows if r["year"] == 2025}
    names = {r["fr"]: r["name"] for r in rows if r["year"] == 2025}
    st = get("standings?leagueId=103,104&season=2026&standingsTypes=regularSeason")
    ps = get("schedule/postseason/series?season=2026&sportId=1")
    inn, pen, champ = set(), set(), None
    for s in ps["series"]:
        for g in s["games"]:
            for side in ("home", "away"):
                fr = _short(g["teams"][side]["team"]["name"])
                inn.add(fr)
                if g["gameType"] == "W":
                    pen.add(fr)
    wins = defaultdict(int)
    for s in ps["series"]:
        for g in s["games"]:
            if g["gameType"] == "W" and g["status"]["detailedState"] == "Final":
                t = g["teams"]
                wins[_short(t["home" if t["home"].get("isWinner") else "away"]["team"]["name"])] += 1
    champ = max(wins, key=wins.get)
    assert wins[champ] == 4 and len(pen) == 2, (wins, pen)
    n26 = 0
    for rec in st["records"]:
        for t in rec["teamRecords"]:
            fr = API2FR[t["team"]["name"]]
            n26 += 1
            rows.append(dict(year=2026, lg=lg_of[fr], fr=fr, name=names[fr],
                             w=t["wins"], l=t["losses"], playoff=int(fr in inn),
                             pennant=int(fr in pen), title=int(fr == champ)))
    assert n26 == 30 and len(inn) == 12
    return rows


def _short(full):
    for k, v in API2FR.items():
        if full.endswith(k) or (k == "D-backs" and "Diamondbacks" in full):
            return v
    raise KeyError(full)


def main():
    rows = load_rows()
    by_year = defaultdict(list)
    for r in rows:
        by_year[r["year"]].append(r)
    # sanity: one champion per WS season, one pennant per league
    for y, rs in by_year.items():
        assert sum(r["title"] for r in rs) == (0 if y in NO_WS else 1), y
        for lg in ("AL", "NL"):
            assert sum(r["pennant"] for r in rs if r["lg"] == lg) == (0 if y == 1994 else 1), (y, lg)

    current = sorted({r["fr"] for r in by_year[2026]})
    name = {r["fr"]: r["name"] for r in by_year[2026]}
    stats = {}
    for f in current:
        s = dict(first=None, seasons=0, w=0, l=0, titles=0, pennants=0, trips=0,
                 exp_t=0.0, p0_t=1.0, exp_p=0.0, p0_p=1.0,
                 exp_trips=0.0, in_exp_p=0.0, in_p0_p=1.0, in_exp_t=0.0, in_p0_t=1.0)
        stats[f] = s
    for y in sorted(by_year):
        rs = by_year[y]
        n = len(rs)
        nlg = {lg: sum(r["lg"] == lg for r in rs) for lg in ("AL", "NL")}
        klg = {lg: sum(r["playoff"] for r in rs if r["lg"] == lg) for lg in ("AL", "NL")}
        K = sum(klg.values())
        for r in rs:
            if r["fr"] not in stats:
                continue
            s = stats[r["fr"]]
            s["first"] = s["first"] or y
            s["seasons"] += 1
            s["w"] += r["w"]; s["l"] += r["l"]
            s["titles"] += r["title"]; s["pennants"] += r["pennant"]; s["trips"] += r["playoff"]
            if y != 1994:
                s["exp_p"] += 1 / nlg[r["lg"]]; s["p0_p"] *= 1 - 1 / nlg[r["lg"]]
                s["exp_trips"] += klg[r["lg"]] / nlg[r["lg"]]
            if y not in NO_WS:
                s["exp_t"] += 1 / n; s["p0_t"] *= 1 - 1 / n
            if r["playoff"]:
                s["in_exp_p"] += 1 / klg[r["lg"]]; s["in_p0_p"] *= 1 - 1 / klg[r["lg"]]
                if y not in NO_WS:
                    s["in_exp_t"] += 1 / K; s["in_p0_t"] *= 1 - 1 / K

    # Simulate whole histories: how many of today's 30 clubs come up empty?
    rng = random.Random(20261031)
    years = sorted(by_year)
    zero_t, zero_p, max_t = defaultdict(int), defaultdict(int), defaultdict(int)
    for _ in range(NSIM):
        t = defaultdict(int); p = defaultdict(int)
        for y in years:
            rs = by_year[y]
            if y not in NO_WS:
                t[rng.choice(rs)["fr"]] += 1
            if y != 1994:
                for lg in ("AL", "NL"):
                    p[rng.choice([r for r in rs if r["lg"] == lg])["fr"]] += 1
        zero_t[sum(t[f] == 0 for f in current)] += 1
        zero_p[sum(p[f] == 0 for f in current)] += 1
        max_t[max(t[f] for f in current)] += 1

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "seasons.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(sorted(rows, key=lambda r: (r["year"], r["lg"], r["fr"])))
    with open(OUT / "franchises.csv", "w", newline="") as fh:
        cols = ["fr", "name", "first", "seasons", "w", "l", "pct", "trips", "exp_trips",
                "pennants", "exp_p", "p0_p", "titles", "exp_t", "p0_t",
                "in_exp_p", "in_p0_p", "in_exp_t", "in_p0_t"]
        w = csv.writer(fh); w.writerow(cols)
        for f in sorted(current, key=lambda f: stats[f]["first"]):
            s = stats[f]
            s["pct"] = s["w"] / (s["w"] + s["l"])
            w.writerow([f, name[f]] + [round(s[c], 4) if isinstance(s[c], float) else s[c] for c in cols[2:]])

    L = []
    def mean(d): return sum(k * v for k, v in d.items()) / NSIM
    def atleast(d, k): return sum(v for kk, v in d.items() if kk >= k) / NSIM
    L.append("WORLD SERIES DROUGHTS vs A FAIR LOTTERY  (AL/NL 1903-2026, %d simulated histories)\n" % NSIM)
    L.append("Clubs with zero titles:   actual %d   lottery mean %.2f   P(>=%d) %.2f"
             % (sum(stats[f]["titles"] == 0 for f in current), mean(zero_t),
                sum(stats[f]["titles"] == 0 for f in current), atleast(zero_t, sum(stats[f]["titles"] == 0 for f in current))))
    L.append("Clubs with zero pennants: actual %d   lottery mean %.2f   P(>=1) %.2f"
             % (sum(stats[f]["pennants"] == 0 for f in current), mean(zero_p), atleast(zero_p, 1)))
    L.append("Most titles by one club:  actual %d   lottery mean %.1f   P(>=%d) %.5f\n"
             % (max(stats[f]["titles"] for f in current), mean(max_t),
                max(stats[f]["titles"] for f in current), atleast(max_t, max(stats[f]["titles"] for f in current))))
    L.append("%-4s %-5s %4s %5s | %5s %5s | %3s %5s %5s | %3s %5s %5s | once in: %5s %5s %5s %5s"
             % ("fr", "first", "yrs", "pct", "trips", "exp", "pen", "exp", "P0", "ws", "exp", "P0",
                "expP", "P0p", "expT", "P0t"))
    for f in sorted(current, key=lambda f: (stats[f]["titles"], stats[f]["first"])):
        s = stats[f]
        L.append("%-4s %-5d %4d %.3f | %5d %5.1f | %3d %5.1f %5.2f | %3d %5.1f %5.2f |          %5.2f %5.2f %5.2f %5.2f"
                 % (f, s["first"], s["seasons"], s["pct"], s["trips"], s["exp_trips"],
                    s["pennants"], s["exp_p"], s["p0_p"], s["titles"], s["exp_t"], s["p0_t"],
                    s["in_exp_p"], s["in_p0_p"], s["in_exp_t"], s["in_p0_t"]))
    (OUT / "analysis.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
