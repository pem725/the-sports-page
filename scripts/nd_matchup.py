#!/usr/bin/env python3
"""The Notre Dame dossier: one opponent, measured rather than described.

    python3 scripts/nd_matchup.py Rice
    python3 scripts/nd_matchup.py --all          # every 2026 opponent, ranked
    python3 scripts/nd_matchup.py Miami --json   # machine-readable

WHY THIS EXISTS. Notre Dame is the one team this paper covers year-round, and a
season preview written in adjectives is worth nothing. Every opponent gets the
same treatment in the same order, so that "they looked great" has to survive
contact with a number, and so that twelve dossiers are comparable to each other.

WHAT IT REFUSES TO DO. It will not rate a game against an unrated opponent.
SP+ covers FBS only, so an FCS result produces no projection at all -- it prints
UNRATEABLE and says why. This matters more than it sounds: a 77-7 win over an
FCS side is the single most over-read result in the sport, and the honest answer
to "what did that tell us" is *nothing measurable*, not a smaller number.

ON USING CURRENT RATINGS. CollegeFootballData serves SP+ as it stands today and
overwrites it as the season goes. For a FORWARD projection that is exactly what
you want -- the best current estimate of a team. It is only poison when used to
"predict" a game already played, which is how a backtest here once returned 15
for 15 (see published/154-no-edge.html). Projecting forward: correct. Grading
backward with it: leakage. The distinction is the whole ballgame.

The margin model is deliberately plain: SP+ difference plus 2.5 for home field,
win probability from a normal with SD 16.5 points, which is the observed spread
of college football results around the number. No secret sauce, and the piece
should say so.
"""
import argparse
import json
import math
import os
import pathlib
import re
import statistics
import sys
import urllib.parse
import urllib.request

API = "https://api.collegefootballdata.com"
YEAR = 2026
HFA = 2.5
SD = 16.5
ND = "Notre Dame"


def key():
    """The paper's key. Read the file, not the environment.

    A running agent session inherits its environment at launch and never re-reads
    ~/.zshrc, so a rotated key looks absent for hours. The file is the truth.
    """
    k = os.environ.get("CFBD_KEY")
    p = pathlib.Path.home() / ".config/secrets/tokens.env"
    if p.exists():
        for ln in p.read_text().splitlines():
            m = re.match(r"\s*(?:export\s+)?CFBD_KEY\s*=\s*(.*)$", ln)
            if m:
                k = m.group(1).strip().strip('"').strip("'")
    if not k:
        raise SystemExit("CFBD_KEY not available")
    return k


_cache = {}


def get(path):
    if path in _cache:
        return _cache[path]
    req = urllib.request.Request(API + path, headers={"Authorization": f"Bearer {key()}"})
    try:
        _cache[path] = json.load(urllib.request.urlopen(req, timeout=60))
    except Exception:
        _cache[path] = []
    return _cache[path]


def ranked(vals, team, reverse=True):
    """Rank a team within a dict of team->value. Defence ranks ascending."""
    order = sorted((v for v in vals.values() if v is not None), reverse=reverse)
    v = vals.get(team)
    return (order.index(v) + 1 if v in order else None), v


def win_prob(margin):
    return 0.5 * (1 + math.erf(margin / (SD * math.sqrt(2))))


def schedule(team):
    out = []
    for g in get(f"/games?year={YEAR}&seasonType=regular"):
        if team in (g["homeTeam"], g["awayTeam"]):
            home = g["homeTeam"] == team
            hp, ap = g.get("homePoints"), g.get("awayPoints")
            us, them = ((hp, ap) if home else (ap, hp)) if hp is not None else (None, None)
            out.append(dict(week=g["week"], home=home,
                            opp=g["awayTeam"] if home else g["homeTeam"],
                            neutral=bool(g.get("neutralSite")),
                            us=us, them=them, date=(g.get("startDate") or "")[:10]))
    return sorted(out, key=lambda r: r["week"])


def dossier(opp):
    sp = {r["team"]: r for r in get(f"/ratings/sp?year={YEAR}")}
    overall = {t: r.get("rating") for t, r in sp.items()}
    off = {t: (r.get("offense") or {}).get("rating") for t, r in sp.items()}
    dfn = {t: (r.get("defense") or {}).get("rating") for t, r in sp.items()}
    talent = {r["team"]: float(r["talent"]) for r in get(f"/talent?year={YEAR}")}

    d = {"opponent": opp, "rated": opp in sp, "n_fbs": len(sp)}
    for label, tbl, rev in (("overall", overall, True), ("offense", off, True), ("defense", dfn, False)):
        for who, name in ((ND, "nd"), (opp, "opp")):
            rk, v = ranked(tbl, who, rev)
            d[f"{name}_{label}"] = v
            d[f"{name}_{label}_rank"] = rk
    for who, name in ((ND, "nd"), (opp, "opp")):
        d[f"{name}_talent"] = talent.get(who)
        rk, _ = ranked(talent, who, True)
        d[f"{name}_talent_rank"] = rk

    # the game itself
    game = next((g for g in schedule(ND) if g["opp"] == opp), None)
    d["game"] = game
    if game and d["rated"]:
        site = 0 if game["neutral"] else (HFA if game["home"] else -HFA)
        d["margin"] = d["nd_overall"] - d["opp_overall"] + site
        d["nd_win_prob"] = win_prob(d["margin"])
    else:
        d["margin"] = d["nd_win_prob"] = None

    # how each side has played RELATIVE TO ITS OWN RATING, rated games only
    def resume(team):
        rows = []
        for g in schedule(team):
            if g["us"] is None or g["opp"] not in sp:
                rows.append(dict(opp=g["opp"], rateable=False,
                                 played=g["us"] is not None,
                                 actual=(g["us"] - g["them"]) if g["us"] is not None else None))
                continue
            site = 0 if g["neutral"] else (HFA if g["home"] else -HFA)
            exp = overall[team] - overall[g["opp"]] + site
            rows.append(dict(opp=g["opp"], rateable=True, played=True,
                             opp_rank=ranked(overall, g["opp"], True)[0],
                             actual=g["us"] - g["them"], expected=exp,
                             over=g["us"] - g["them"] - exp))
        return rows
    d["nd_resume"] = [r for r in resume(ND) if r["played"]]
    d["opp_resume"] = [r for r in resume(opp) if r["played"]]

    # players: usage and PPA, the closest thing to "who actually does the work"
    def players(team):
        use = {p["name"]: p for p in get(f"/player/usage?year={YEAR}&team={urlq(team)}")}
        ppa = {p["name"]: p for p in get(f"/ppa/players/season?year={YEAR}&team={urlq(team)}")}
        out = []
        for n, u in use.items():
            usage = (u.get("usage") or {}).get("overall")
            a = (ppa.get(n, {}).get("averagePPA") or {})
            out.append(dict(name=n, pos=u.get("position"), usage=usage,
                            ppa_all=a.get("all"), ppa_rush=a.get("rush"), ppa_pass=a.get("pass")))
        return sorted([o for o in out if o["usage"]], key=lambda o: -o["usage"])
    d["nd_players"] = players(ND)
    d["opp_players"] = players(opp)

    m = get(f"/teams/matchup?team1={urlq(ND)}&team2={urlq(opp)}")
    if isinstance(m, dict) and m.get("games"):
        d["series"] = dict(nd=m.get("team1Wins"), opp=m.get("team2Wins"), ties=m.get("ties"),
                           last=[dict(season=g.get("season"), home=g.get("homeTeam"),
                                      away=g.get("awayTeam"), hs=g.get("homeScore"),
                                      as_=g.get("awayScore")) for g in m["games"][-5:]])
    return d


def urlq(s):
    return urllib.parse.quote(s)


def show(d):
    o = d["opponent"]
    g = d["game"]
    where = "neutral" if (g and g["neutral"]) else ("home" if (g and g["home"]) else "away")
    print(f"\n{'='*74}\n  NOTRE DAME vs {o.upper()}"
          + (f"   week {g['week']}, {g['date']}, {where}" if g else "   [not on the 2026 schedule]")
          + f"\n{'='*74}")

    if not d["rated"]:
        print(f"\n  UNRATEABLE. {o} is not in the SP+ set ({d['n_fbs']} FBS teams), which means")
        print("  it is not FBS. No projection is possible and none should be invented.")
    else:
        print(f"\n  {'':<12}{'Notre Dame':>22}{o:>22}")
        for lab, k in (("SP+ overall", "overall"), ("  offense", "offense"), ("  defense", "defense")):
            nd_v, nd_r = d[f"nd_{k}"], d[f"nd_{k}_rank"]
            op_v, op_r = d[f"opp_{k}"], d[f"opp_{k}_rank"]
            f = lambda v, r: f"{v:+.1f} (#{r})" if v is not None else "--"
            print(f"  {lab:<12}{f(nd_v,nd_r):>22}{f(op_v,op_r):>22}")
        f2 = lambda v, r: f"{v:.1f} (#{r})" if v is not None else "--"
        print(f"  {'talent':<12}{f2(d['nd_talent'],d['nd_talent_rank']):>22}"
              f"{f2(d['opp_talent'],d['opp_talent_rank']):>22}")
        if d["margin"] is not None:
            print(f"\n  PROJECTION   Notre Dame by {d['margin']:.1f}   "
                  f"win probability {d['nd_win_prob']*100:.0f}%")
            print(f"               SP+ gap {d['nd_overall']-d['opp_overall']:+.1f}, "
                  f"home field {'+2.5' if where=='home' else ('-2.5' if where=='away' else '0.0')}, "
                  f"SD {SD} points")

    for who, rows in (("NOTRE DAME", d["nd_resume"]), (o.upper(), d["opp_resume"])):
        if not rows:
            continue
        print(f"\n  {who} SO FAR -- performance against its OWN rating")
        for r in rows:
            if not r["rateable"]:
                print(f"    {r['opp']:<24}{r['actual']:>+5}   UNRATEABLE opponent, tells us nothing")
            else:
                print(f"    {r['opp']:<24}{r['actual']:>+5}   expected {r['expected']:>+6.1f}"
                      f"   {r['over']:>+6.1f} vs its rating   (opp #{r['opp_rank']})")
        rate = [r for r in rows if r["rateable"]]
        if rate:
            mean = statistics.mean(r["over"] for r in rate)
            print(f"    {'':<24}{'':>5}   mean {mean:+.1f} over {len(rate)} rated game"
                  f"{'s' if len(rate)!=1 else ''}"
                  + ("  -- one game. This is a rumour, not a finding." if len(rate) == 1 else ""))

    for who, ps in (("NOTRE DAME", d["nd_players"]), (o.upper(), d["opp_players"])):
        if not ps:
            continue
        print(f"\n  {who} -- who actually does the work (usage share, PPA per play)")
        print(f"    {'player':<26}{'pos':<5}{'usage':>8}{'PPA/play':>10}")
        for p in ps[:8]:
            ppa = f"{p['ppa_all']:+.2f}" if p["ppa_all"] is not None else "--"
            print(f"    {p['name'][:25]:<26}{(p['pos'] or ''):<5}{p['usage']*100:>7.1f}%{ppa:>10}")

    s = d.get("series")
    if s:
        print(f"\n  SERIES   Notre Dame {s['nd']} - {s['opp']} {o}"
              + (f", {s['ties']} ties" if s["ties"] else ""))
        for g in s["last"]:
            print(f"    {g['season']}  {g['away']} {g['as_']} @ {g['home']} {g['hs']}")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("opponent", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.all:
        opps = [g["opp"] for g in schedule(ND)]
        out = [dossier(o) for o in opps]
        if a.json:
            print(json.dumps(out, indent=1))
            return 0
        print(f"\n  NOTRE DAME 2026 -- all {len(out)} opponents, hardest first\n")
        print(f"  {'wk':<4}{'opponent':<20}{'site':<9}{'SP+':>7}{'proj':>9}{'ND win':>9}")
        for d in sorted(out, key=lambda x: (x["margin"] is None, x["margin"])):
            g = d["game"]
            site = "neutral" if g["neutral"] else ("home" if g["home"] else "away")
            if d["margin"] is None:
                print(f"  {g['week']:<4}{d['opponent']:<20}{site:<9}{'--':>7}{'UNRATEABLE':>9}")
            else:
                print(f"  {g['week']:<4}{d['opponent']:<20}{site:<9}{d['opp_overall']:>+7.1f}"
                      f"{d['margin']:>+9.1f}{d['nd_win_prob']*100:>8.0f}%")
        print()
        return 0

    if not a.opponent:
        ap.error("name an opponent, or use --all")
    d = dossier(a.opponent)
    print(json.dumps(d, indent=1)) if a.json else show(d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
