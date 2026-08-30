#!/usr/bin/env python3
"""Project every top-25 college football season, for the Odds Board's CFB tab.

    python3 scripts/build_cfb_odds.py

WHY SP+ AND NOT OUR RANK MODEL. The rank-gap model published in Issue #135 was
fitted on ranked-versus-ranked games, gaps of 1 to 25. Asked about a gap of 77 it
returns "0%", which is not a probability, it is extrapolation off a cliff. SP+ is
a points-above-average rating, so a difference between two teams IS an expected
margin and converts to a win probability honestly at any gap.

    P(A beats B) = Phi( (SP+_A - SP+_B + home) / 16.5 )

16.5 is the standard deviation of college margin against the spread -- wider than
the NFL's 13.5, because college games are less even. Home field is 2.5 points.

Each team's season is then simulated 20,000 times over its real schedule to give
a win distribution, not just an expected value: the chance of running the table,
of ten wins, of a losing season.
"""
import json, math, os, sys, urllib.request
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "cfb-odds.json")
API = "https://api.collegefootballdata.com"
SD, HFA, NSIMS = 16.5, 2.5, 20000
YEAR = 2026


def cfb(p):
    r = urllib.request.Request(API + p, headers={"Authorization": "Bearer " + os.environ["CFBD_KEY"]})
    return json.load(urllib.request.urlopen(r, timeout=60))


def main():
    sp = {x["team"]: x["rating"] for x in cfb(f"/ratings/sp?year={YEAR}") if x.get("rating") is not None}
    talent = {x["team"]: x["talent"] for x in cfb(f"/talent?year={YEAR}")}
    ret = {x["team"]: x.get("percentPPA") for x in cfb(f"/player/returning?year={YEAR}")}
    games = cfb(f"/games?year={YEAR}&seasonType=regular")
    fbs = {t["school"] for t in cfb(f"/teams/fbs?year={YEAR}")}

    sched = {}
    for g in games:
        h, a = g.get("homeTeam"), g.get("awayTeam")
        if not h or not a:
            continue
        for me, opp, site in ((h, a, "home"), (a, h, "away")):
            if me not in fbs:
                continue
            sched.setdefault(me, []).append(dict(
                opp=opp, site=("neutral" if g.get("neutralSite") else site),
                date=(g.get("startDate") or "")[:10],
                hp=g.get("homePoints"), ap=g.get("awayPoints"),
                won=(None if g.get("homePoints") is None else
                     ((g["homePoints"] > g["awayPoints"]) if me == h else (g["awayPoints"] > g["homePoints"])))))

    order = sorted(sp, key=lambda t: -sp[t])
    rng = np.random.default_rng(7)
    out = []
    for rank, team in enumerate(order[:25], 1):
        gs = sorted(sched.get(team, []), key=lambda x: x["date"])
        if not gs:
            continue
        ps, played, wins_so_far = [], 0, 0
        for g in gs:
            adj = 0 if g["site"] == "neutral" else (HFA if g["site"] == "home" else -HFA)
            diff = sp.get(team, 0) - sp.get(g["opp"], -12.0) + adj      # non-FBS default well below
            p = 0.5 * (1 + math.erf(diff / (SD * math.sqrt(2))))
            g["p"] = round(p, 3)
            if g["won"] is None:
                ps.append(p)
            else:
                played += 1; wins_so_far += int(g["won"])
        sims = wins_so_far + (rng.random((NSIMS, len(ps))) < np.array(ps)).sum(1) if ps else np.full(NSIMS, wins_so_far)
        n = len(gs)
        opp_sp = [sp.get(g["opp"]) for g in gs if sp.get(g["opp"]) is not None]
        out.append(dict(
            rank=rank, team=team, sp=round(sp[team], 1),
            talent=round(talent.get(team, 0), 1),
            ret=(round(ret[team], 3) if ret.get(team) is not None else None),
            games=n, played=played, wins=wins_so_far,
            proj=round(float(sims.mean()), 1),
            undefeated=round(float((sims == n).mean()), 4),
            ten_plus=round(float((sims >= 10).mean()), 3),
            losing=round(float((sims < n / 2).mean()), 3),
            sos=round(float(np.mean(opp_sp)), 1) if opp_sp else None,
            sched=[dict(opp=g["opp"], site=g["site"], date=g["date"], p=g["p"],
                        won=g["won"]) for g in gs]))
    json.dump(dict(generated=__import__("datetime").date.today().isoformat(),
                   method=f"SP+ difference through a normal CDF, sd {SD}, home field {HFA}; "
                          f"{NSIMS:,} season simulations per club",
                   teams=out), open(OUT, "w"), separators=(",", ":"))
    print(f"  wrote {os.path.relpath(OUT, REPO)}  ({len(out)} clubs)")
    print(f"  {'':>3} {'team':<18}{'SP+':>7}{'proj':>7}{'10+':>7}{'unbtn':>8}{'SoS':>7}")
    for t in out[:12]:
        print(f"  {t['rank']:>3} {t['team']:<18}{t['sp']:>7.1f}{t['proj']:>7.1f}"
              f"{t['ten_plus']:>7.0%}{t['undefeated']:>8.1%}{t['sos'] or 0:>7.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
