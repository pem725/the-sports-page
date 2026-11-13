#!/usr/bin/env python3
"""Where It Stands: every hitter's and pitcher's season since 1901, on 0-100 twice.

Set by the editor 2026-11-13. A raw number means little without its season: 109 RBI in
1968, the year of the pitcher, was as rare as 132 in 2025. So every stat gets
  1. its percentile WITHIN ITS OWN SEASON (leads: it removes rule changes and strategy),
  2. its percentile among EVERY season since the stat was kept (second line),
and every season gets one line saying how big or small that league ran.
Percent of maximum was considered and dropped: one record season sets its ceiling for
everyone (research/constructs/baseball-hitting/README.md).

Who is compared with whom, so that a percentile means something:
  hitters    300+ plate appearances
  starters   started at least half their games, 100+ innings
  relievers  started fewer than half, 40+ innings
All scaled for short seasons (1918, 1981, 1994, 2020). A starter is never ranked against
relievers: their ERAs and strikeout rates live in different worlds. Before the 1950s a
"reliever" by this rule was mostly a swingman who also started (61 of them in 1926,
averaging 113 innings), and the page says the line is blurrier then. A group-season with
fewer than 20 pitchers gets no within-season percentile.

Every percentile runs in the direction of its sentence: "had a better ERA than 90 of
every 100" ranks low ERAs high; "struck out more than 90" ranks high strikeouts high.
Mid-rank, floored, capped at 99, with 100 kept for the single top value.

Source: MLB Stats API season lines, no key, cached in
research/constructs/baseball-hitting/data/raw/ (shared with the constructs work). Rebuild
once a year, after the World Series:
    python3 scripts/build_stands.py
Writes data/stands-mlb-hitting.json and data/stands-mlb-pitching.json.
"""
import datetime as dt, json, os, time, unicodedata, urllib.request
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "research", "constructs", "baseball-hitting", "data", "raw")
URL = ("https://statsapi.mlb.com/api/v1/stats?stats=season&group={g}&season={y}"
       "&sportId=1&limit=3000&playerPool=ALL")
MIN_GROUP = 20

# key, label, API field (or a function of the stat line), decimals shown, first season
# both leagues kept it, which way is "more" in the sentence, and the sentence's verb.
HIT = [("avg", "Batting average", "avg", 3, 1901, "high", "beat"),
       ("obp", "On-base percentage", "obp", 3, 1901, "high", "beat"),
       ("slg", "Slugging", "slg", 3, 1901, "high", "beat"),
       ("ops", "OPS", "ops", 3, 1901, "high", "beat"),
       ("hr", "Home runs", "homeRuns", 0, 1901, "high", "beat"),
       ("rbi", "RBI", "rbi", 0, 1901, "high", "beat"),
       ("r", "Runs", "runs", 0, 1901, "high", "beat"),
       ("h", "Hits", "hits", 0, 1901, "high", "beat"),
       ("bb", "Walks", "baseOnBalls", 0, 1901, "high", "walked more than"),
       ("so", "Strikeouts", "strikeOuts", 0, 1913, "high", "struck out more than"),
       ("sb", "Stolen bases", "stolenBases", 0, 1901, "high", "stole more than")]


def ip(t):
    """'201.1' means 201 and one third innings."""
    s = str(t.get("inningsPitched") or "0")
    w, _, f = s.partition(".")
    return int(w or 0) + int(f or 0) / 3


def per9(field):
    return lambda t: 9 * t[field] / ip(t) if ip(t) and t.get(field) is not None else None


PITCH = [("era", "ERA", "era", 2, 1901, "low", "had a better ERA than"),
         ("whip", "WHIP", "whip", 2, 1901, "low", "had a better WHIP than"),
         ("k9", "Strikeouts per 9", per9("strikeOuts"), 1, 1913, "high", "struck out more batters than"),
         ("bb9", "Walks per 9", per9("baseOnBalls"), 1, 1901, "low", "walked fewer batters than"),
         ("hr9", "Home runs per 9", per9("homeRuns"), 2, 1901, "low", "allowed fewer home runs than"),
         ("so", "Strikeouts", "strikeOuts", 0, 1913, "high", "struck out more than"),
         ("ip", "Innings", ip, 1, 1901, "high", "pitched more innings than"),
         ("w", "Wins", "wins", 0, 1901, "high", "won more than"),
         ("sv", "Saves", "saves", 0, 1969, "high", "saved more than")]
# Saves became an official statistic in 1969; earlier totals are reconstructions.


def season(group, y, last):
    p = os.path.join(RAW, f"{group[0]}{y}.json")
    if not os.path.exists(p) or y == last:  # the newest season can still change
        open(p, "wb").write(urllib.request.urlopen(URL.format(g=group, y=y), timeout=60).read())
        time.sleep(0.3)
    return json.load(open(p))["stats"][0]["splits"]


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


def scale(vals):
    """0-100 for display: the mid-rank percentile, floored and capped at 99, with 100
    kept for a top value nobody else matched (ten kickers making every extra point are not
    each "the best"). Rounding would print 100 for a 99.7, which claims a
    season was the best when it was not."""
    top = max(vals)
    alone = sum(1 for v in vals if v == top) == 1  # a tie at the top is not "the best"
    return [100 if (v == top and alone) else min(99, int(p)) for v, p in zip(vals, midrank(vals))]


def value(t, f):
    x = f(t) if callable(f) else t.get(f)
    if x in (None, "", "-.--", ".---", "*.**", "-"):
        return None
    try:
        return float(x)
    except ValueError:
        return None


def build(kind, stats, rows, groups):
    """rows carry 'grp'; percentiles are computed within group, within group-season."""
    for k, _, _, _, _, way, _ in stats:
        sign = 1 if way == "high" else -1
        for g in groups:
            idx = [i for i, r in enumerate(rows) if r["grp"] == g and r["v"][k] is not None]
            if not idx:
                continue
            for i, p in zip(idx, scale([sign * rows[i]["v"][k] for i in idx])):
                rows[i].setdefault("at", {})[k] = p
            by = defaultdict(list)
            for i in idx:
                by[rows[i]["year"]].append(i)
            for ii in by.values():
                if len(ii) < MIN_GROUP:
                    continue
                for i, p in zip(ii, scale([sign * rows[i]["v"][k] for i in ii])):
                    rows[i].setdefault("ws", {})[k] = p

    # How big did each season run, per group? The median, and where that median ranks among
    # every season's (in plain value order: 0 = the lowest season on record).
    seasons = {}
    for g in groups:
        for k, *_ in stats:
            med = {}
            for y in sorted({r["year"] for r in rows}):
                xs = sorted(r["v"][k] for r in rows if r["grp"] == g and r["year"] == y and r["v"][k] is not None)
                if len(xs) >= MIN_GROUP:
                    n = len(xs)
                    med[y] = xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2
            ys = list(med)
            for y, p in zip(ys, midrank([med[y] for y in ys])):
                seasons.setdefault(g, {}).setdefault(str(y), {})[k] = [round(med[y], 3), int(p)]
    counts = defaultdict(int)
    for r in rows:
        counts[f'{r["grp"]}|{r["year"]}'] += 1

    # Players are keyed by MLB id, never by name: there are two Pedro Martinezes, and a
    # merged lookup once showed a 1994 Padres reliever for Pedro of the Red Sox. A name
    # shared by more than one player is labeled with that player's span of seasons.
    span = defaultdict(list)
    for r in rows:
        span[r["pid"]].append(r["year"])
    name_of = {r["pid"]: r["name"] for r in rows}
    # Compare names without accents: the feed spells one Pedro "Martinez" and the other
    # "Martínez", and the page's search ignores accents.
    plain = lambda n: unicodedata.normalize("NFD", n).encode("ascii", "ignore").decode().lower()
    shared = defaultdict(set)
    for pid, n in name_of.items():
        shared[plain(n)].add(pid)
    def label(pid):
        n = name_of[pid]
        return n if len(shared[plain(n)]) == 1 else f"{n} ({min(span[pid])}\u2013{max(span[pid])})"
    pids = sorted(name_of, key=lambda p: (name_of[p], min(span[p])))
    names = [label(p) for p in pids]
    ni = {p: i for i, p in enumerate(pids)}
    teams = sorted({r["team"] for r in rows})
    ti = {t: i for i, t in enumerate(teams)}
    keys = [s[0] for s in stats]
    years = [r["year"] for r in rows]
    return {"kind": kind, "built": dt.date.today().isoformat(), "first": min(years), "last": max(years),
            "minGroup": MIN_GROUP, "groups": groups,
            "stats": [{"key": k, "label": l, "dp": d, "from": y0, "way": w, "verb": vb}
                      for k, l, _, d, y0, w, vb in stats],
            "names": names, "teams": teams, "seasons": seasons, "counts": counts,
            # [player index into names, year, team, group index, playing time,
            #  [value, within-season, all-time] per stat]
            "rows": [[ni[r["pid"]], r["year"], ti[r["team"]], groups.index(r["grp"]), r["pt"],
                      [[round(r["v"][k], 3), r.get("ws", {}).get(k), r["at"].get(k)] if r["v"][k] is not None else None
                       for k in keys]] for r in rows]}


def main():
    os.makedirs(RAW, exist_ok=True)
    today = dt.date.today()
    last = today.year if today.month >= 11 else today.year - 1  # a season counts once it is over
    hit, pit = [], []
    for y in range(1901, last + 1):
        hs = season("hitting", y, last)
        g = max(s["stat"].get("gamesPlayed", 0) for s in hs) or 1
        f = g / 162  # short-season scaling
        for s in hs:
            t = s["stat"]
            if (t.get("plateAppearances") or 0) < 300 * f:
                continue
            hit.append({"name": s["player"].get("fullName", ""), "pid": s["player"]["id"], "year": y, "grp": "hitters",
                        "team": (s.get("team") or {}).get("name", "") if s.get("numTeams", 1) == 1 else "",
                        "pt": t["plateAppearances"],
                        "v": {k: (value(t, fld) if y >= y0 else None) for k, _, fld, _, y0, _, _ in HIT}})
        for s in season("pitching", y, last):
            t = s["stat"]
            gp, gs, inn = t.get("gamesPitched") or 0, t.get("gamesStarted") or 0, ip(t)
            grp = "starters" if gp and gs >= gp / 2 else "relievers"
            if inn < (100 if grp == "starters" else 40) * f:
                continue
            pit.append({"name": s["player"].get("fullName", ""), "pid": s["player"]["id"], "year": y, "grp": grp,
                        "team": (s.get("team") or {}).get("name", "") if s.get("numTeams", 1) == 1 else "",
                        "pt": round(inn, 1),
                        # Saves rank relievers only; a starter's zero says nothing.
                        "v": {k: (value(t, fld) if y >= y0 and not (k == "sv" and grp == "starters") else None)
                              for k, _, fld, _, y0, _, _ in PITCH}})
    for name, data in (("hitting", build("hitting", HIT, hit, ["hitters"])),
                       ("pitching", build("pitching", PITCH, pit, ["starters", "relievers"]))):
        out = os.path.join(REPO, "data", f"stands-mlb-{name}.json")
        json.dump(data, open(out, "w"), separators=(",", ":"))
        print(f"{name}: {len(data['rows'])} seasons, {len(data['names'])} players -> "
              f"{os.path.relpath(out, REPO)} ({os.path.getsize(out) // 1024} KB)")


if __name__ == "__main__":
    main()
