#!/usr/bin/env python3
"""Where It Stands: every hitter's season since 1901, placed on a 0-100 scale twice.

Set by the editor 2026-11-13. A raw number means little without its season: 109 RBI in
1968, the year of the pitcher, was as rare as 132 in 2025. So every stat gets
  1. its percentile WITHIN ITS OWN SEASON (leads: it removes rule changes and strategy),
  2. its percentile among EVERY season since the stat was kept (second line),
and every season gets one line saying how big or small that league ran.
Percent of maximum was considered and dropped: one record season sets its ceiling for
everyone (research/constructs/baseball-hitting/README.md).

Population: hitters with 300+ plate appearances, scaled for short seasons (1918, 1981,
1994, 2020). A percentile here means "among regulars", and the page says so. Percentiles
are mid-rank, so ties share a value and the scale runs 0 to 100.

Source: MLB Stats API season hitting lines, no key. Seasons are cached in
research/constructs/baseball-hitting/data/raw/ (shared with the constructs work), so a
rebuild after the first only fetches the newest season. Rebuild once a year, after the
World Series:
    python3 scripts/build_stands.py
Writes data/stands-mlb-hitting.json, read by where-it-stands.html.
"""
import datetime as dt, json, os, time, urllib.request
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "research", "constructs", "baseball-hitting", "data", "raw")
OUT = os.path.join(REPO, "data", "stands-mlb-hitting.json")
URL = ("https://statsapi.mlb.com/api/v1/stats?stats=season&group=hitting&season={y}"
       "&sportId=1&limit=3000&playerPool=ALL")

# key, label, API field, decimals shown, first season both leagues kept it
STATS = [("avg", "Batting average", "avg", 3, 1901), ("obp", "On-base percentage", "obp", 3, 1901),
         ("slg", "Slugging", "slg", 3, 1901), ("ops", "OPS", "ops", 3, 1901),
         ("hr", "Home runs", "homeRuns", 0, 1901), ("rbi", "RBI", "rbi", 0, 1901),
         ("r", "Runs", "runs", 0, 1901), ("h", "Hits", "hits", 0, 1901),
         ("bb", "Walks", "baseOnBalls", 0, 1901), ("so", "Strikeouts", "strikeOuts", 0, 1913),
         ("sb", "Stolen bases", "stolenBases", 0, 1901)]


def season(y, last):
    p = os.path.join(RAW, f"h{y}.json")
    if not os.path.exists(p) or y == last:  # the newest season can still change
        open(p, "wb").write(urllib.request.urlopen(URL.format(y=y), timeout=60).read())
        time.sleep(0.3)
    return json.load(open(p))["stats"][0]["splits"]


def scale(vals):
    """0-100 for display: the mid-rank percentile, floored and capped at 99, with 100
    kept for the top value alone. Rounding would print 100 for a 99.7, which claims a
    season was the best when it was not."""
    top = max(vals)
    return [100 if v == top else min(99, int(p)) for v, p in zip(vals, midrank(vals))]


def midrank(vals):
    """Percent of the group below each value, ties counted half: 0-100."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    out, i = [0.0] * len(vals), 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        for k in range(i, j + 1):
            out[order[k]] = 100 * ((i + j) / 2 + 0.5) / len(vals)
        i = j + 1
    return out


def main():
    os.makedirs(RAW, exist_ok=True)
    today = dt.date.today()
    last = today.year if today.month >= 11 else today.year - 1  # a season counts once it is over
    rows = []
    for y in range(1901, last + 1):
        sp = season(y, last)
        g = max(s["stat"].get("gamesPlayed", 0) for s in sp) or 1
        cut = 300 * g / 162
        for s in sp:
            t = s["stat"]
            if (t.get("plateAppearances") or 0) < cut:
                continue
            v = {}
            for k, _, f, _, y0 in STATS:
                x = t.get(f)
                v[k] = None if x is None or y < y0 or x in ("", "-.--", ".---") else float(x)
            rows.append({"name": s["player"].get("fullName", ""), "pid": s["player"]["id"], "year": y,
                         "team": (s.get("team") or {}).get("name", "") if s.get("numTeams", 1) == 1 else "",
                         "pa": t["plateAppearances"], "v": v})

    # Percentiles: all-time per stat, then within each season.
    for k, *_ in STATS:
        idx = [i for i, r in enumerate(rows) if r["v"][k] is not None]
        for i, p in zip(idx, scale([rows[i]["v"][k] for i in idx])):
            rows[i].setdefault("at", {})[k] = p
        by = defaultdict(list)
        for i in idx:
            by[rows[i]["year"]].append(i)
        for ii in by.values():
            for i, p in zip(ii, scale([rows[i]["v"][k] for i in ii])):
                rows[i].setdefault("ws", {})[k] = p

    # How big did each season run? The league median for each stat, and where that median
    # ranks among every season's median (0 = the smallest season on record).
    seasons = {}
    for k, *_ in STATS:
        med = {}
        for y in sorted({r["year"] for r in rows}):
            xs = sorted(r["v"][k] for r in rows if r["year"] == y and r["v"][k] is not None)
            if xs:
                n = len(xs)
                med[y] = xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2
        ys = list(med)
        for y, p in zip(ys, midrank([med[y] for y in ys])):
            seasons.setdefault(str(y), {})[k] = [med[y], int(p)]

    names = sorted({r["name"] for r in rows})
    ni = {n: i for i, n in enumerate(names)}
    teams = sorted({r["team"] for r in rows})
    ti = {t: i for i, t in enumerate(teams)}
    keys = [s[0] for s in STATS]
    out = {"built": today.isoformat(), "first": 1901, "last": last,
           "population": "hitters with 300 or more plate appearances (scaled for short seasons)",
           "stats": [{"key": k, "label": l, "dp": d, "from": y0} for k, _, l, d, y0 in
                     [(s[0], None, s[1], s[3], s[4]) for s in STATS]],
           "names": names, "teams": teams, "seasons": seasons,
           # one row per player-season: [name, year, team, pa, [value, within-season, all-time] per stat]
           "rows": [[ni[r["name"]], r["year"], ti[r["team"]], r["pa"],
                     [[r["v"][k], r["ws"].get(k), r["at"].get(k)] if r["v"][k] is not None else None for k in keys]]
                    for r in rows]}
    json.dump(out, open(OUT, "w"), separators=(",", ":"))
    print(f"{len(rows)} player-seasons, {len(names)} players, {out['first']}-{last} -> "
          f"{os.path.relpath(OUT, REPO)} ({os.path.getsize(OUT) // 1024} KB)")


if __name__ == "__main__":
    main()
