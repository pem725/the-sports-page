#!/usr/bin/env python3
"""The October bracket: seeds, matchups, and the odds for every series.

    python3 scripts/build_bracket.py             # writes data/bracket.json
    python3 scripts/build_bracket.py --dry-run

BEFORE THE FIELD IS SET this projects the bracket from the standings as they
stand and says so. Once every seed is decided it reports the real thing. The
page reads one flag, `settled`, and changes its own wording -- nobody has to
remember to edit anything on clinch night.

WHY THE MATH RUNS IN LOG-ODDS. Two adjustments have to be combined here: how
good a club is, and whether it is at home. In probability space you cannot add
them -- a five-point home edge means something different to a .500 club than to
a .700 one, and adding it can push a probability past 1. In log-odds space they
simply add, and nothing can leave the interval, because the transform maps the
whole real line onto (0,1). That is the entire reason the log exists here and it
is not a mathematical nicety; it is what makes "home field is worth this much"
a single number rather than a table.

    logit(p) = ln(p / (1-p))          odds -> log-odds
    p = 1 / (1 + e^-x)                back again

Home advantage is one constant, +0.140 in log-odds, taken from the .535 home win
rate between evenly matched clubs. Add it to the home side, subtract nothing,
convert back. It behaves correctly at every strength.

CLUB STRENGTH blends the actual record with the Pythagorean estimate from runs
scored and allowed (exponent 1.83), then regresses toward .500 with a prior worth
69 games -- the same treatment the odds board uses, so the two never disagree.
"""
import argparse
import json
import math
import os
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "bracket.json")
API = "https://statsapi.mlb.com/api/v1"
SEASON = 2026
K = 69                       # games of prior; empirical-Bayes shrinkage toward .500
PYTH = 1.83
HFA = math.log(0.535 / 0.465) / 2    # home edge in log-odds, split between the sides
LEAGUE = {103: "American League", 104: "National League"}

logit = lambda p: math.log(p / (1 - p))
expit = lambda x: 1 / (1 + math.exp(-x))


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def team_stats():
    """Season hitting and pitching, MLB only -- sportId=1 or the feed hands back
    college clubs, which it did on the first attempt here."""
    out = {}
    for grp in ("hitting", "pitching"):
        d = get(f"{API}/teams/stats?season={SEASON}&group={grp}&stats=season&gameType=R&sportId=1")
        for s in d["stats"][0]["splits"]:
            t = out.setdefault(s["team"]["id"], {})
            st = s["stat"]
            if grp == "hitting":
                t["ops"] = st.get("ops"); t["runs"] = int(st.get("runs", 0))
                t["avg"] = st.get("avg"); t["hr"] = int(st.get("homeRuns", 0))
            else:
                t["era"] = st.get("era"); t["whip"] = st.get("whip")
                t["ra"] = int(st.get("runs", 0)); t["k"] = int(st.get("strikeOuts", 0))
    return out


def strength(w, l, rs, ra):
    g = w + l
    actual = w / g if g else 0.5
    pyth = rs ** PYTH / (rs ** PYTH + ra ** PYTH) if rs and ra else actual
    blend = 0.5 * actual + 0.5 * pyth
    return (blend * g + 0.5 * K) / (g + K)          # regress toward .500


def series(pa, pb, pattern):
    """Probability the first club wins, given a home/away pattern of 'H'/'A'.

    Strength is combined by log5 -- the standard way to turn two winning
    percentages into a head-to-head -- then home field is added in log-odds.
    """
    base = (pa - pa * pb) / (pa + pb - 2 * pa * pb) if (pa + pb - 2 * pa * pb) else 0.5
    x = logit(min(max(base, 1e-6), 1 - 1e-6))
    pg = [expit(x + (HFA if s == "H" else -HFA)) for s in pattern]
    need = len(pattern) // 2 + 1
    # exact: walk every sequence, stop when either side clinches
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def rec(i, a, b):
        if a == need: return 1.0
        if b == need: return 0.0
        p = pg[i]
        return p * rec(i + 1, a + 1, b) + (1 - p) * rec(i + 1, a, b + 1)
    return rec(0, 0, 0)


PATTERNS = {3: "HHH", 5: "HHAAH", 7: "HHAAAHH"}      # higher seed's perspective


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stats = team_stats()
    st = get(f"{API}/standings?leagueId=103,104&season={SEASON}&standingsTypes=regularSeason")
    clubs = {}
    for rec in st["records"]:
        lg = rec["league"]["id"]
        for tr in rec["teamRecords"]:
            tid = tr["team"]["id"]
            s = stats.get(tid, {})
            rs, ra = s.get("runs", 0), s.get("ra", 0)
            clubs[tid] = dict(
                id=tid, name=tr["team"]["name"], lg=lg,
                w=tr["wins"], l=tr["losses"], div=rec["division"]["id"],
                divrank=int(tr.get("divisionRank", 9)),
                gp=tr["wins"] + tr["losses"],
                rs=rs, ra=ra, ops=s.get("ops"), era=s.get("era"),
                whip=s.get("whip"), avg=s.get("avg"), hr=s.get("hr"), k=s.get("k"),
                p=strength(tr["wins"], tr["losses"], rs, ra))

    total = 162
    settled = all(c["gp"] >= total for c in clubs.values())

    brackets = {}
    for lg in (103, 104):
        pool = [c for c in clubs.values() if c["lg"] == lg]
        pool.sort(key=lambda c: (-(c["w"] / max(c["gp"], 1)), -c["w"]))
        winners = []
        for d in sorted({c["div"] for c in pool}):
            dv = [c for c in pool if c["div"] == d]
            winners.append(max(dv, key=lambda c: (c["w"] / max(c["gp"], 1), c["w"])))
        winners.sort(key=lambda c: (-(c["w"] / max(c["gp"], 1)), -c["w"]))
        wc = [c for c in pool if c not in winners][:3]
        seeds = winners + wc
        for i, c in enumerate(seeds, 1):
            c["seed"] = i
        brackets[lg] = dict(league=LEAGUE[lg], seeds=[
            {k: c[k] for k in ("id", "name", "seed", "w", "l", "rs", "ra", "ops", "era",
                               "whip", "avg", "hr", "k", "p")} for c in seeds])
        # first round: 3v6 and 4v5, best of three, all at the higher seed
        rounds = []
        for hi, lo in ((3, 6), (4, 5)):
            a, b = seeds[hi - 1], seeds[lo - 1]
            rounds.append(dict(round="Wild Card", best_of=3, hi=a["seed"], lo=b["seed"],
                               hi_name=a["name"], lo_name=b["name"],
                               p=round(series(a["p"], b["p"], PATTERNS[3]), 4)))
        # division series, against the projected survivor of each first-round pair
        for top, pair in ((1, (4, 5)), (2, (3, 6))):
            a = seeds[top - 1]
            for opp in pair:
                b = seeds[opp - 1]
                rounds.append(dict(round="Division Series", best_of=5, hi=a["seed"], lo=b["seed"],
                                   hi_name=a["name"], lo_name=b["name"], conditional=True,
                                   p=round(series(a["p"], b["p"], PATTERNS[5]), 4)))
        brackets[lg]["matchups"] = rounds

    doc = dict(generated=__import__("datetime").date.today().isoformat(),
               season=SEASON, settled=settled,
               note=("Final seeding" if settled else
                     "Projected from the standings as they stand; seeds are not yet decided"),
               hfa_logodds=round(HFA, 4), brackets={str(k): v for k, v in brackets.items()})

    for lg in (103, 104):
        b = brackets[lg]
        print(f"\n  {b['league']}{'' if settled else '  (projected)'}")
        print(f"  {'seed':<5}{'club':<24}{'W-L':>8}{'OPS':>7}{'ERA':>7}{'strength':>10}")
        for c in b["seeds"]:
            print(f"  {c['seed']:<5}{c['name']:<24}{str(c['w'])+'-'+str(c['l']):>8}"
                  f"{c['ops'] or '--':>7}{c['era'] or '--':>7}{c['p']:>10.3f}")
        print("  first round:")
        for m in b["matchups"][:2]:
            print(f"    {m['hi']} {m['hi_name']} vs {m['lo']} {m['lo_name']}"
                  f"  -> {m['p']*100:.0f}% / {(1-m['p'])*100:.0f}%  (best of {m['best_of']})")

    if args.dry_run:
        print("\n  dry run, nothing written"); return
    json.dump(doc, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT}  (settled={settled})")


if __name__ == "__main__":
    main()
