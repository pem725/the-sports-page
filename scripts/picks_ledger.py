#!/usr/bin/env python3
"""Track the family confidence pool, and check whether the model is calibrated.

    python3 scripts/picks_ledger.py --update    # fill in results from finished games
    python3 scripts/picks_ledger.py --report    # standings + calibration table

THE POINT IS CALIBRATION, NOT THE SCORE. A single 71% pick losing tells you
nothing -- 71% picks are supposed to lose 29% of the time. What is worth knowing
is whether, across a whole season, the picks we called 71% actually win about
71%. That takes twenty or thirty games before it says anything, which is exactly
why it needs a ledger rather than a memory.

Results come from ESPN's scoreboard, which updates live, rather than the
CollegeFootballData API, which lags several hours behind a finished game.
"""
import argparse
import json
import math
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "data", "picks-ledger.json")
ESPN = ("https://site.api.espn.com/apis/site/v2/sports/football/college-football"
        "/scoreboard?dates={}&groups=80&limit=300")

# our ledger name -> names ESPN might use
ALIAS = {"Miami": {"Miami", "Miami (FL)", "Miami Hurricanes"},
         "NC State": {"NC State", "North Carolina State"},
         "North Dakota State": {"North Dakota State", "North Dakota St"},
         "South Dakota State": {"South Dakota State", "South Dakota St"}}


def names(c):
    t = c["team"]
    return {t.get("displayName", ""), t.get("shortDisplayName", ""),
            t.get("name", ""), t.get("location", "")}


def matches(label, comp):
    want = ALIAS.get(label, {label})
    got = names(comp)
    return bool(want & got) or any(w in g for w in want for g in got if g)


def fetch(day):
    try:
        return json.load(urllib.request.urlopen(ESPN.format(day), timeout=45)).get("events", [])
    except Exception:
        return []


def update(led):
    days = []
    for d in range(20260826, 20260832):
        days.append(str(d))
    days += [f"2026090{d}" for d in range(1, 10)] + [f"202609{d}" for d in range(10, 31)]
    events = []
    seen = set()
    for d in days:
        for e in fetch(d):
            if e["id"] not in seen:
                seen.add(e["id"]); events.append(e)
    n = 0
    for wk in led["weeks"].values():
        for p in wk["picks"]:
            if p["correct"] is not None:
                continue
            for e in events:
                c = e["competitions"][0]
                if c["status"]["type"]["state"] != "post":
                    continue
                cs = c["competitors"]
                if not (any(matches(p["pick"], x) for x in cs)
                        and any(matches(p["opp"], x) for x in cs)):
                    continue
                win = max(cs, key=lambda x: int(x.get("score", 0)))
                lose = min(cs, key=lambda x: int(x.get("score", 0)))
                p["correct"] = bool(matches(p["pick"], win))
                p["result"] = win["team"]["displayName"]
                p["score"] = f'{win["team"]["shortDisplayName"]} {win.get("score")}-{lose.get("score")} {lose["team"]["shortDisplayName"]}'
                n += 1
                break
    return n


def report(led):
    allp = [p for wk in led["weeks"].values() for p in wk["picks"]]
    done = [p for p in allp if p["correct"] is not None]
    if not done:
        print("  nothing final yet")
        pend = sorted(allp, key=lambda x: -x["pts"])[:5]
        print("  next up:")
        for p in pend:
            print(f'    {p["pts"]:>2} pts  {p["pick"]} over {p["opp"]}  ({p["model_p"]:.0%})')
        return
    got = sum(p["pts"] for p in done if p["correct"])
    poss = sum(p["pts"] for p in done)
    hit = sum(1 for p in done if p["correct"])
    print(f"  {hit} of {len(done)} correct   {got} of {poss} points banked\n")
    print(f"  {'pts':>4} {'pick':<20}{'model':>7}{'result':>8}   score")
    for p in sorted(done, key=lambda x: -x["pts"]):
        print(f'  {p["pts"]:>4} {p["pick"]:<20}{p["model_p"]:>7.0%}'
              f'{"  WIN " if p["correct"] else "  loss":>8}   {p["score"]}')
    print("\n  === CALIBRATION: do the percentages mean anything? ===")
    band = [(.90, 1.01, "90-100%"), (.75, .90, "75-90%"), (.65, .75, "65-75%")]
    print(f"  {'we said':<10}{'n':>4}{'we won':>9}{'expected':>10}")
    for lo, hi, lab in band:
        g = [p for p in done if lo <= p["model_p"] < hi]
        if not g:
            continue
        act = sum(1 for p in g if p["correct"]) / len(g)
        exp = sum(p["model_p"] for p in g) / len(g)
        print(f"  {lab:<10}{len(g):>4}{act:>9.0%}{exp:>10.0%}")
    exp_tot = sum(p["model_p"] for p in done)
    print(f"\n  expected correct {exp_tot:.1f}, actual {hit}."
          f"  {'Ahead of' if hit > exp_tot else 'Behind'} the model by {abs(hit-exp_tot):.1f}.")
    if len(done) < 25:
        print(f"  {len(done)} games is far too few to judge calibration. It needs 25+ before"
              f"\n  any of the rows above mean anything. Reporting it now so the habit is set.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    led = json.load(open(LEDGER))
    if a.update:
        n = update(led)
        json.dump(led, open(LEDGER, "w"), indent=1)
        print(f"  resolved {n} newly finished game(s)")
    if a.report or not a.update:
        report(led)
    return 0


if __name__ == "__main__":
    sys.exit(main())
