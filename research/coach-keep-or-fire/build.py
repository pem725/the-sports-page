#!/usr/bin/env python3
"""Keep the coach or change? Build the bad-year panel and the first-pass risks.

Source: data/cfb-coaches.csv (one row per coach-season, 1970-2025, wins, losses,
SP+, SRS). No API calls.

Definitions (set with the editor 2026-11-27):
- school-season: all coach rows for a school and year summed; the PRIMARY coach
  is the one who coached the most games.
- BAD YEAR: the season fell 3+ wins short of the school's own trailing 5-year
  average, measured per game and scaled to this season's games:
      shortfall = (avg win% over t-5..t-1  -  win% in t) * games in t  >= 3
  The five prior seasons must all be in the file (contiguous).
- Trigger also requires the primary coach to be in year 2+ at the school (a
  first-year coach's bad year is a different decision); --include-year1 relaxes it.
- A season with a mid-season coaching change is EXCLUDED as a trigger: the
  decision we study is the one made after the season, and that one was already made.
- CHANGED: primary coach in t+1 differs from t. The file cannot tell fired from
  left for a better job or retired; all count as changed (say so).

Outcomes, three horizons:
  sink   next season's win% below the bad year's (sank further)
  era    mean win% over t+1..t+5 below the pre-slump 5-year average (lost era)
  back   6+ wins and .500+ in t+1 or t+2 (back to bowl-eligible form; a proxy,
         since bowl slots were far fewer before the 1990s)

Prints raw risks for kept vs changed, the relative risk (changed / kept) and
the odds ratio, each with a 95% bootstrap interval resampling programs'
bad years. Writes the panel to panel.json for the matched pass.
"""
import argparse
import collections
import csv
import json
import pathlib
import random

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parents[1] / "data" / "cfb-coaches.csv"


def seasons():
    rows = collections.defaultdict(list)
    for r in csv.DictReader(open(SRC)):
        rows[(r["school"], int(r["year"]))].append(r)
    out = {}
    for (school, year), rs in rows.items():
        g = sum(int(r["games"]) for r in rs)
        w = sum(int(r["wins"]) for r in rs) + 0.5 * sum(int(r["ties"]) for r in rs)
        prim = max(rs, key=lambda r: int(r["games"]))
        out[(school, year)] = dict(school=school, year=year, games=g, wins=w,
                                   pct=w / g if g else None, coach=prim["coach"],
                                   midseason=len(rs) > 1,
                                   sp=float(prim["sp"]) if prim["sp"] else None)
    return out


def tenure(S):
    """Years the primary coach has led this school, counting this one."""
    for (school, year), s in sorted(S.items(), key=lambda kv: kv[0][1]):
        prev = S.get((school, year - 1))
        s["tenure"] = prev["tenure"] + 1 if prev and prev["coach"] == s["coach"] else 1


def panel(S, include_year1):
    P, floor, eligible = [], 0, 0
    for (school, t), s in S.items():
        prior = [S.get((school, t - k)) for k in range(1, 6)]
        after = [S.get((school, t + k)) for k in range(1, 6)]
        if not all(prior) or not s["pct"] or not after[0]:
            continue
        avg5 = sum(p["pct"] for p in prior) / 5
        eligible += 1
        if avg5 * s["games"] < 3:
            floor += 1                       # too weak already to fall 3 wins
        short = (avg5 - s["pct"]) * s["games"]
        if short < 3 or s["midseason"] or (s["tenure"] < 2 and not include_year1):
            continue
        nxt = after[0]
        era = (sum(a["pct"] for a in after) / 5 < avg5) if all(after) else None
        back = any(a and a["wins"] >= 6 and a["pct"] >= .5 for a in after[:2])
        P.append(dict(school=school, year=t, coach=s["coach"], tenure=s["tenure"],
                      games=s["games"], wins=s["wins"], avg5=avg5, shortfall=short,
                      sp=s["sp"], changed=nxt["coach"] != s["coach"],
                      sink=nxt["pct"] < s["pct"], era=era, back=back))
    return P, floor, eligible


def risk(rows, k):
    rs = [r[k] for r in rows if r[k] is not None]
    return (sum(rs) / len(rs), len(rs)) if rs else (None, 0)


def rr_or(rows, k):
    pc, _ = risk([r for r in rows if r["changed"]], k)
    pk, _ = risk([r for r in rows if not r["changed"]], k)
    if pc in (None, 0, 1) or pk in (None, 0, 1):
        return None, None
    return pc / pk, (pc / (1 - pc)) / (pk / (1 - pk))


def boot(rows, k, n=2000, seed=11):
    """Resample schools, not seasons: one program's bad years are not independent."""
    rng = random.Random(seed)
    by = collections.defaultdict(list)
    for r in rows:
        by[r["school"]].append(r)
    keys = list(by)
    rrs, ors = [], []
    for _ in range(n):
        smp = [r for s in (rng.choice(keys) for _ in keys) for r in by[s]]
        a, b = rr_or(smp, k)
        if a:
            rrs.append(a), ors.append(b)
    q = lambda v: (sorted(v)[int(.025 * len(v))], sorted(v)[int(.975 * len(v))])
    return q(rrs), q(ors)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-year1", action="store_true")
    a = ap.parse_args()
    S = seasons()
    tenure(S)
    P, floor, eligible = panel(S, a.include_year1)
    ch = [r for r in P if r["changed"]]
    print(f"school-seasons with 5 prior years and a next year: {eligible}")
    print(f"  of which too weak to ever fall 3 wins (avg5 x games < 3): {floor}")
    print(f"bad years (trigger): {len(P)}  changed {len(ch)}  kept {len(P) - len(ch)}"
          f"  {'(incl. year-1 coaches)' if a.include_year1 else '(coach year 2+)'}\n")
    names = dict(sink="sank further next year", era="lost era (next 5 below pre-slump)",
                 back="back to 6+ wins within 2 years")
    for k, label in names.items():
        pc, nc = risk(ch, k)
        pk, nk = risk([r for r in P if not r["changed"]], k)
        rr, orr = rr_or(P, k)
        (rl, rh), (ol, oh) = boot(P, k)
        print(f"{label:38s} changed {pc:.0%} (n={nc})  kept {pk:.0%} (n={nk})")
        print(f"{'':38s} RR {rr:.2f} [{rl:.2f}-{rh:.2f}]  OR {orr:.2f} [{ol:.2f}-{oh:.2f}]")
    (HERE / "panel.json").write_text(json.dumps(P, indent=1))


if __name__ == "__main__":
    main()
