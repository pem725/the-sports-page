#!/usr/bin/env python3
"""How much of a ranking is settled on the field? NFL vs college football.

The editor, 2026-10-17: the NFL is a randomized trial -- a designed schedule,
settled on the field -- and college football is an observational study, wide
bandwidth and low fidelity, so it runs on belief. This measures it.

For every PAIR of top teams, ask how the pair is connected by games played so far:
  direct  -- they played each other
  proxy   -- no direct game, but at least one common opponent
  belief  -- neither; any ordering of the two is an opinion, not a result

College: the AP Top 25 and its top 12 (the playoff's size), FBS and FCS opponents
both count as common opponents. NFL: the top 12 by record (ties by point
differential), so the playoff-sized groups match, and all 32 clubs.

    python3 scripts/settled_on_field.py            # 2026 to date + 2023-2025 finals
    python3 scripts/settled_on_field.py --game 401754522   # one box score, ESPN vs CFBD

Data: CollegeFootballData (/rankings, /games with seasonType=both), cached under
~/.cache/sports-page/cfbd so a rerun spends no quota; nflverse games.csv.
Output: data/schedule/settled_on_field.txt
"""
import csv, itertools, json, os, pathlib, sys, urllib.parse, urllib.request
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = pathlib.Path.home() / ".cache/sports-page"
OUT = ROOT / "data/schedule/settled_on_field.txt"
NFL_URL = "https://github.com/nflverse/nfldata/raw/master/data/games.csv"
CALLS = []


def cfbd(path):
    """One cached CFBD call. The key is read from the environment and never printed."""
    f = CACHE / "cfbd" / (path.strip("/").replace("/", "_").replace("?", "_").replace("&", "_").replace("=", "-") + ".json")
    if f.exists():
        return json.loads(f.read_text())
    key = os.environ.get("CFBD_KEY") or sys.exit("CFBD_KEY is not set (source ~/.config/secrets/tokens.env)")
    req = urllib.request.Request("https://api.collegefootballdata.com" + path,
                                 headers={"Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=60) as r:
        CALLS.append((path, r.headers.get("X-CallLimit-Remaining")))
        data = json.load(r)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data))
    return data


def ap_poll(year, final):
    """(week, [teams in rank order]) -- the final poll, or the latest regular-season poll."""
    polls = [w for w in cfbd(f"/rankings?year={year}")
             if (w["seasonType"] == "postseason") == final
             and any(p["poll"] == "AP Top 25" for p in w["polls"])]
    w = max(polls, key=lambda w: w["week"])
    ranks = next(p for p in w["polls"] if p["poll"] == "AP Top 25")["ranks"]
    return w["week"], [r["school"] for r in sorted(ranks, key=lambda r: r["rank"])]


def cfb_games(year, before_week=None):
    """Completed games as (home, away). before_week keeps regular-season weeks < before_week."""
    out = []
    for g in cfbd(f"/games?year={year}&seasonType=both"):
        if g.get("homePoints") is None or g.get("awayPoints") is None:
            continue
        if before_week is not None and (g["seasonType"] != "regular" or g["week"] >= before_week):
            continue
        out.append((g["homeTeam"], g["awayTeam"]))
    return out


def nfl(season):
    """(games, top-12 by record) for a season, completed games only (regular + playoffs)."""
    f = CACHE / "nflverse/games.csv"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(NFL_URL, f)
    games, rec = [], defaultdict(lambda: [0.0, 0])
    for r in csv.DictReader(open(f)):
        if int(r["season"]) != season or r["home_score"] in ("", "NA"):
            continue
        h, a, hs, as_ = r["home_team"], r["away_team"], int(r["home_score"]), int(r["away_score"])
        games.append((h, a))
        if r["game_type"] == "REG":
            for t, d in ((h, hs - as_), (a, as_ - hs)):
                rec[t][0] += 1 if d > 0 else 0.5 if d == 0 else 0
                rec[t][1] += d
    weeks = max(int(r["week"]) for r in csv.DictReader(open(f))
                if int(r["season"]) == season and r["game_type"] == "REG" and r["home_score"] not in ("", "NA"))
    order = sorted(rec, key=lambda t: (-rec[t][0], -rec[t][1]))
    return games, order, weeks


def connect(teams, games):
    """Share of pairs that are direct / proxy / belief, plus per-team counts."""
    opp = defaultdict(set)
    for h, a in games:
        opp[h].add(a); opp[a].add(h)
    kind = {}
    for x, y in itertools.combinations(teams, 2):
        kind[(x, y)] = "direct" if y in opp[x] else "proxy" if opp[x] & opp[y] else "belief"
    n = len(kind)
    share = {k: sum(v == k for v in kind.values()) / n for k in ("direct", "proxy", "belief")}
    per = {t: {k: sum(1 for p, v in kind.items() if t in p and v == k) for k in ("direct", "proxy", "belief")}
           for t in teams}
    return share, per, n


BOX = [("first downs", "1st Downs", "firstDowns"), ("total yards", "Total Yards", "totalYards"),
       ("passing yards", "Passing", "netPassingYards"), ("rushing yards", "Rushing", "rushingYards"),
       ("rushes", "Rushing Attempts", "rushingAttempts"), ("comp-att", "Comp/Att", "completionAttempts"),
       ("third downs", "3rd down efficiency", "thirdDownEff"), ("fourth downs", "4th down efficiency", "fourthDownEff"),
       ("turnovers", "Turnovers", "turnovers"), ("penalties", "Penalties", "totalPenaltiesYards"),
       ("possession", "Possession", "possessionTime")]


def game_box(event):
    """Box score of one game on two feeds (ESPN summary, CFBD team stats); flags every disagreement.
    Costs one CFBD call the first time (cached after)."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event={event}"
    e = json.load(urllib.request.urlopen(url, timeout=60))
    comp = e["header"]["competitions"][0]
    if comp["status"]["type"]["state"] != "post":
        sys.exit(f"game {event} is not final yet ({comp['status']['type']['description']})")
    teams = {c["team"]["location"]: c for c in comp["competitors"]}
    print(comp["date"], e["gameInfo"]["venue"]["fullName"])
    for name, c in teams.items():
        print(f"  {name:12s} {c['homeAway']:4s} {c['score']:>3s}  by quarter {[l['displayValue'] for l in c['linescores']]}")
    year = int(e["header"]["season"]["year"])
    some = next(iter(teams))
    cf = next(g for g in cfbd(f"/games/teams?year={year}&team={urllib.parse.quote(some)}&seasonType=both")
              if g["id"] == int(event))
    cfs = {t["team"]: {x["category"]: x["stat"] for x in t["stats"]} for t in cf["teams"]}
    es = {t["team"]["location"]: {s["label"]: s["displayValue"] for s in t["statistics"]} for t in e["boxscore"]["teams"]}
    for name in es:
        cname = next((k for k in cfs if k.startswith(name) or name.startswith(k)), None)
        print(f"\n  {name}")
        for lab, ek, ck in BOX:
            a, b = es[name].get(ek, "?"), (cfs.get(cname) or {}).get(ck, "?")
            same = a.replace("/", "-") == str(b).replace("/", "-")
            print(f"    {lab:14s} ESPN {a:>8s}  CFBD {str(b):>8s}  {'' if same else '<-- DISAGREE'}")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--game":
        return game_box(sys.argv[2])
    lines = []
    say = lambda s="": (print(s), lines.append(s))
    fmt = lambda s: f"direct {s['direct']:.0%}  proxy {s['proxy']:.0%}  belief {s['belief']:.0%}"

    say("2026 TO DATE")
    wk, top25 = ap_poll(2026, final=False)
    g = cfb_games(2026, before_week=wk)
    played = max(x["week"] for x in cfbd("/games?year=2026&seasonType=both")
                 if x["seasonType"] == "regular" and x.get("homePoints") is not None and x["week"] < wk)
    say(f"  CFB: AP poll week {wk}, games through regular-season week {played} ({len(g)} completed games)")
    for k in (12, 25):
        s, per, n = connect(top25[:k], g)
        say(f"  CFB AP top {k:2d} ({n:3d} pairs): {fmt(s)}")
    s, per, _ = connect(top25, g)
    for t in ("Notre Dame",):
        if t in per:
            r = per[t]
            say(f"    {t} (AP No. {top25.index(t) + 1}) vs the other 24: direct {r['direct']}, proxy {r['proxy']}, belief {r['belief']}")
    beliefs = sorted(top25, key=lambda t: -per[t]["belief"])
    say("    most 'belief' pairs: " + ", ".join(f"{t} {per[t]['belief']}" for t in beliefs[:6]))
    say("    fewest: " + ", ".join(f"{t} {per[t]['belief']}" for t in beliefs[-4:]))
    ng, order, nwk = nfl(2026)
    say(f"  NFL: games through week {nwk} ({len(ng)} completed games)")
    for k in (12, 32):
        s, _, n = connect(order[:k], ng)
        say(f"  NFL top {k:2d} ({n:3d} pairs): {fmt(s)}")

    say("\nEND OF SEASON (final AP poll, all games incl. bowls/playoff; NFL incl. playoffs)")
    for y in (2023, 2024, 2025):
        _, fin = ap_poll(y, final=True)
        gy = cfb_games(y)
        s12, _, _ = connect(fin[:12], gy)
        s25, _, _ = connect(fin, gy)
        ngy, oy, _ = nfl(y)
        n12, _, _ = connect(oy[:12], ngy)
        n32, _, _ = connect(oy, ngy)
        say(f"  {y}  CFB top 12: {fmt(s12)} | top 25: {fmt(s25)}")
        say(f"        NFL top 12: {fmt(n12)} | all 32: {fmt(n32)}")

    if CALLS:
        say(f"\nCFBD calls this run: {len(CALLS)}; remaining after last: {CALLS[-1][1]}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
