#!/usr/bin/env python3
"""Did he coach them up, or did he inherit them?

    python3 scripts/inherited_roster.py
    python3 scripts/inherited_roster.py --refresh

THE EDITOR, 2026-09-29, on Florida and Mississippi State: "Are these guys great
coaches or did they just land phenomenal athletes? In Florida's case I think he
inherited most of the team."

And Sean McKnight, the same day, describing the same problem from the other end:
an attribution meter beside every new coach reading "inherited program 90%, new
coach 10%" on day one and moving as the roster turns over. He called the numbers
illustrative. This makes them real.

THE MODEL. A college roster is roughly the last four recruiting classes. So for a
coach who arrived in year A, his season in year Y is built from the classes signed
in Y-1 through Y-4, and a class counts as HIS only if it was signed in year A or
later. That gives an attribution weight with no judgement in it:

    first season      0% his roster    (every class predates him)
    second            25%
    third             50%
    fourth            75%
    fifth onward     100%

WHY THIS BEATS THE SP+ VERSION. The previous pass subtracted a team's SP+ rating,
which is measured DURING the coach's season and therefore already contains his
coaching -- subtracting it removed part of the thing being measured. Recruiting
classes signed before he was hired cannot contain his coaching. They are the
cleanest available statement of what he was handed.

THE QUESTION THIS CAN FINALLY ASK. Not "is he winning" but "is he winning more
than the talent he was given should win, and does that hold up once the roster
becomes his?" A coach who beats expectation on an inherited roster and then
regresses when it is his own is a different animal from one who does the reverse.

WHAT IT STILL CANNOT DO. Recruiting rankings are a market forecast, not a
measurement -- they price the same hype that the coach's reputation feeds. They
ignore transfers entirely, which in the portal era is a large hole and gets worse
every season. And attrition is not random: bad teams lose their best players.
Every one of those pushes toward crediting the coach for talent he did not
develop, so read the residual as generous to the coach.
"""
import argparse
import collections
import csv
import json
import math
import pathlib
import re
import statistics
import sys
import time
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
RECRUIT = REPO / "data" / "cfb-recruiting.csv"
COACHES = REPO / "data" / "cfb-coaches.csv"


def key():
    for ln in (pathlib.Path.home() / ".config/secrets/tokens.env").read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?CFBD_KEY\s*=\s*(.*)$", ln)
        if m:
            return m.group(1).strip().strip('"').strip("'")


def fetch_recruiting(lo=2000, hi=2025):
    """Throttled, and it refuses rather than returning a window with a hole."""
    K = key()
    rows = []
    for yr in range(lo, hi + 1):
        d = None
        for attempt in range(4):
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(
                    f"https://api.collegefootballdata.com/recruiting/teams?year={yr}",
                    headers={"Authorization": f"Bearer {K}"}), timeout=120))
                break
            except Exception as e:
                time.sleep(3 * (attempt + 1))
        if d is None:
            raise SystemExit(f"recruiting {yr} failed -- refusing a gapped window")
        time.sleep(1.2)
        for x in d:
            if x.get("points"):
                rows.append(dict(year=yr, team=x["team"], points=float(x["points"])))
        print(f"    recruiting {yr}: {len(rows):,} rows", flush=True)
    RECRUIT.parent.mkdir(parents=True, exist_ok=True)
    with open(RECRUIT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["year", "team", "points"])
        w.writeheader()
        w.writerows(rows)
    return rows


def load_recruiting(refresh=False):
    if RECRUIT.exists() and not refresh:
        return [dict(year=int(r["year"]), team=r["team"], points=float(r["points"]))
                for r in csv.DictReader(open(RECRUIT))]
    return fetch_recruiting()


def load_coaches():
    out = []
    for r in csv.DictReader(open(COACHES)):
        if int(r["games"]) < 6:
            continue
        out.append(dict(coach=r["coach"], year=int(r["year"]), school=r["school"],
                        games=int(r["games"]), wins=int(r["wins"])))
    return out


def z_by_year(rec):
    """Recruiting points standardized within each year -- classes are not
    comparable across years in raw points."""
    by = collections.defaultdict(dict)
    for r in rec:
        by[r["year"]][r["team"]] = r["points"]
    out = {}
    for yr, teams in by.items():
        v = list(teams.values())
        m, s = statistics.mean(v), statistics.pstdev(v)
        for t, p in teams.items():
            out[(yr, t)] = (p - m) / s if s else 0.0
    return out


def build():
    rec = z_by_year(load_recruiting())
    cos = load_coaches()
    # tenure start: first year this coach appears at this school, contiguous
    spell = {}
    for r in sorted(cos, key=lambda r: (r["coach"], r["school"], r["year"])):
        k = (r["coach"], r["school"])
        if k not in spell:
            spell[k] = r["year"]
    rows = []
    for r in cos:
        k = (r["coach"], r["school"])
        arrive = spell[k]
        yr, sch = r["year"], r["school"]
        classes = [(yr - i, rec.get((yr - i, sch))) for i in (1, 2, 3, 4)]
        have = [(cy, z) for cy, z in classes if z is not None]
        if len(have) < 3:
            continue
        talent = statistics.mean(z for _, z in have)
        own = sum(1 for cy, _ in have if cy >= arrive) / len(have)
        rows.append(dict(coach=r["coach"], school=sch, year=yr,
                         games=r["games"], wins=r["wins"],
                         pct=r["wins"] / r["games"], talent=talent,
                         own=own, tenure=yr - arrive + 1))
    return rows


def fit(rows):
    """Wins-per-game predicted by inherited/roster talent. Plain least squares."""
    x = [r["talent"] for r in rows]
    y = [r["pct"] for r in rows]
    mx, my = statistics.mean(x), statistics.mean(y)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    return my - b * mx, b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    if a.refresh:
        fetch_recruiting()
    rows = build()
    a0, b = fit(rows)
    for r in rows:
        r["exp"] = a0 + b * r["talent"]
        r["resid"] = r["pct"] - r["exp"]
    print(f"\n  {len(rows):,} coach-seasons with 3+ recruiting classes on file, "
          f"{len({r['coach'] for r in rows}):,} coaches")
    print(f"  talent -> win rate:1 SD of recruiting is worth {b:.3f} of win "
          f"percentage ({b*12:.1f} wins over a 12-game season)\n")

    print("  DOES A COACH BEAT HIS ROSTER, AND WHOSE ROSTER IS IT?\n")
    print(f"  {'season':<10}{'his share':>11}{'n':>7}{'mean residual':>16}{'SD':>8}")
    print("  " + "-" * 53)
    for t in (1, 2, 3, 4, 5):
        g = [r for r in rows if r["tenure"] == t]
        if len(g) < 25:
            continue
        lab = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth+"}[t]
        if t == 5:
            g = [r for r in rows if r["tenure"] >= 5]
        print(f"  {lab:<10}{statistics.mean(r['own'] for r in g):>10.0%}{len(g):>7}"
              f"{statistics.mean(r['resid'] for r in g):>+16.3f}"
              f"{statistics.pstdev(r['resid'] for r in g):>8.3f}")

    print("\n\n  DOES BEATING YOUR ROSTER PERSIST?\n")
    by = collections.defaultdict(dict)
    for r in rows:
        by[r["coach"]][r["year"]] = r
    pairs = [(v[y]["resid"], v[y + 1]["resid"])
             for v in by.values() for y in v if y + 1 in v]
    print(f"  season to next season, {len(pairs):,} pairs: "
          f"r = {statistics.correlation([p[0] for p in pairs],[p[1] for p in pairs]):.3f}")
    early = [(v[y]["resid"], v[y + 1]["resid"]) for v in by.values() for y in v
             if y + 1 in v and v[y]["own"] <= 0.25]
    late = [(v[y]["resid"], v[y + 1]["resid"]) for v in by.values() for y in v
            if y + 1 in v and v[y]["own"] >= 0.75]
    for lab, p in (("on an INHERITED roster", early), ("on HIS OWN roster", late)):
        if len(p) > 30:
            print(f"  {lab:<26}{len(p):>6} pairs   r = "
                  f"{statistics.correlation([q[0] for q in p],[q[1] for q in p]):+.3f}")
    print("\n  A high correlation means beating the roster is a property of the coach.")
    print("  A low one means it was the season, not the man.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
