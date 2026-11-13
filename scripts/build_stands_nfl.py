#!/usr/bin/env python3
"""Where It Stands, football: every NFL player's season since 1999 on 0-100 twice.

The same design as scripts/build_stands.py (baseball): each stat's percentile within its
own season leads, all time comes second, and a line says how big that season ran. Every
player is ranked only against his own position, the way pitchers are split into starters
and relievers: a quarterback's rushing yards and a running back's mean different things.

Regulars, per 16 games (scaled to 17 from 2021):
  QB  200+ pass attempts      RB  100+ carries        WR  50+ targets
  TE  40+ targets             DL, LB, DB  10+ games   K   15+ field-goal tries
Defensive players have no snap counts in this feed, so "10+ games" is a weak bar and the
page says so: a defensive percentile mixes starters and rotation players.

Source: nflverse player stats (stats_player_reg_YYYY.csv), regular season only, 1999 on.
Rebuild after each Super Bowl:
    python3 scripts/build_stands_nfl.py
Writes data/stands-nfl.json, read by where-it-stands.html.
"""
import csv, datetime as dt, json, os, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_stands import build  # noqa: E402  same percentile and season logic as baseball

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "research", "constructs", "football", "data", "raw")
URL = "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_reg_{y}.csv"
FIRST = 1999


def n(t, k):
    try:
        return float(t.get(k) or 0)
    except ValueError:
        return 0.0


def ratio(a, b, scale=1.0):
    return lambda t: scale * n(t, a) / n(t, b) if n(t, b) else None


def passer_rating(t):
    att = n(t, "attempts")
    if not att:
        return None
    c = lambda x: max(0.0, min(2.375, x))
    a = c((n(t, "completions") / att - 0.3) * 5)
    b = c((n(t, "passing_yards") / att - 3) * 0.25)
    d = c(n(t, "passing_tds") / att * 20)
    e = c(2.375 - n(t, "passing_interceptions") / att * 25)
    return (a + b + d + e) / 6 * 100


def get(k):
    return lambda t: n(t, k)


def tackles(t):
    return n(t, "def_tackles_solo") + n(t, "def_tackle_assists")


def scrimmage(t):
    return n(t, "rushing_yards") + n(t, "receiving_yards")


# key, label, function, decimals, first season, way, verb
REC = [("rec", "Receptions", get("receptions"), 0, FIRST, "high", "caught more passes than"),
       ("ryd", "Receiving yards", get("receiving_yards"), 0, FIRST, "high", "gained more receiving yards than"),
       ("ypc", "Yards per catch", ratio("receiving_yards", "receptions"), 1, FIRST, "high", "averaged more per catch than"),
       ("crate", "Catch rate", ratio("receptions", "targets", 100), 0, FIRST, "high", "caught a bigger share of targets than"),
       ("yac", "Yards after catch, per catch", ratio("receiving_yards_after_catch", "receptions"), 1, 2006, "high", "gained more after the catch than"),
       ("rtd", "Receiving TDs", get("receiving_tds"), 0, FIRST, "high", "scored more receiving TDs than")]
GROUPS = {
    "QB": ("quarterback", "quarterbacks", "pass attempts", lambda t: n(t, "attempts"), 200, [
        ("pyd", "Passing yards", get("passing_yards"), 0, FIRST, "high", "threw for more yards than"),
        ("ptd", "Passing TDs", get("passing_tds"), 0, FIRST, "high", "threw more TDs than"),
        ("ypa", "Yards per attempt", ratio("passing_yards", "attempts"), 1, FIRST, "high", "gained more per throw than"),
        ("cmp", "Completion %", ratio("completions", "attempts", 100), 1, FIRST, "high", "completed a bigger share than"),
        ("intr", "Interceptions per 100 throws", ratio("passing_interceptions", "attempts", 100), 1, FIRST, "low", "threw interceptions less often than"),
        ("rate", "Passer rating", passer_rating, 1, FIRST, "high", "had a better passer rating than"),
        ("sackr", "Sacks per 100 dropbacks", lambda t: 100 * n(t, "sacks_suffered") / (n(t, "attempts") + n(t, "sacks_suffered")) if n(t, "attempts") else None, 1, FIRST, "low", "was sacked less often than"),
        ("qbrush", "Rushing yards", get("rushing_yards"), 0, FIRST, "high", "ran for more yards than")]),
    "RB": ("running back", "running backs", "carries", lambda t: n(t, "carries"), 100, [
        ("rush", "Rushing yards", get("rushing_yards"), 0, FIRST, "high", "ran for more yards than"),
        ("ypcar", "Yards per carry", ratio("rushing_yards", "carries"), 1, FIRST, "high", "gained more per carry than"),
        ("rutd", "Rushing TDs", get("rushing_tds"), 0, FIRST, "high", "scored more rushing TDs than"),
        ("scrim", "Yards from scrimmage", scrimmage, 0, FIRST, "high", "gained more total yards than"),
        ("rec", "Receptions", get("receptions"), 0, FIRST, "high", "caught more passes than"),
        ("fum", "Fumbles lost per 100 touches", lambda t: 100 * (n(t, "rushing_fumbles_lost") + n(t, "receiving_fumbles_lost")) / (n(t, "carries") + n(t, "receptions")) if n(t, "carries") else None, 1, FIRST, "low", "fumbled less often than")]),
    "WR": ("wide receiver", "wide receivers", "targets", lambda t: n(t, "targets"), 50, REC),
    "TE": ("tight end", "tight ends", "targets", lambda t: n(t, "targets"), 40, REC),
    "DL": ("defensive lineman", "defensive linemen", "games", lambda t: n(t, "games"), 10, None),
    "LB": ("linebacker", "linebackers", "games", lambda t: n(t, "games"), 10, None),
    "DB": ("defensive back", "defensive backs", "games", lambda t: n(t, "games"), 10, None),
    "K": ("kicker", "kickers", "field-goal tries", lambda t: n(t, "fg_att"), 15, [
        ("fgp", "Field-goal %", ratio("fg_made", "fg_att", 100), 1, FIRST, "high", "made a bigger share than"),
        ("fgm", "Field goals made", get("fg_made"), 0, FIRST, "high", "made more field goals than"),
        ("fg50", "Made from 50+", lambda t: n(t, "fg_made_50_59") + n(t, "fg_made_60_"), 0, FIRST, "high", "made more from 50-plus than"),
        ("long", "Longest", get("fg_long"), 0, FIRST, "high", "had a longer best kick than"),
        ("patp", "Extra-point %", ratio("pat_made", "pat_att", 100), 1, FIRST, "high", "made a bigger share of extra points than")])}
DEF = [("tkl", "Tackles", tackles, 0, FIRST, "high", "made more tackles than"),
       ("tfl", "Tackles for loss", get("def_tackles_for_loss"), 0, FIRST, "high", "made more tackles for loss than"),
       ("sck", "Sacks", get("def_sacks"), 1, FIRST, "high", "had more sacks than"),
       ("qbh", "QB hits", get("def_qb_hits"), 0, 2006, "high", "hit the QB more than"),
       ("int", "Interceptions", get("def_interceptions"), 0, FIRST, "high", "intercepted more than"),
       ("pd", "Passes defended", get("def_pass_defended"), 0, FIRST, "high", "defended more passes than"),
       ("ff", "Forced fumbles", get("def_fumbles_forced"), 0, FIRST, "high", "forced more fumbles than")]
for g in ("DL", "LB", "DB"):
    GROUPS[g] = GROUPS[g][:5] + (DEF,)


def fetch(y):
    p = os.path.join(RAW, f"reg{y}.csv")
    if not os.path.exists(p):
        open(p, "wb").write(urllib.request.urlopen(URL.format(y=y), timeout=90).read())
    return list(csv.DictReader(open(p, encoding="utf-8")))


def main():
    os.makedirs(RAW, exist_ok=True)
    today = dt.date.today()
    last = today.year - 1 if today.month >= 3 else today.year - 2  # a season is over after the Super Bowl
    # One stat list for the whole file: the union, in group order, so every group's row has
    # a slot for every stat (empty where the stat does not apply).
    stats, seen = [], set()
    for g in GROUPS.values():
        for s in g[5]:
            if s[0] not in seen:
                seen.add(s[0]); stats.append(s)
    applies = {g: {s[0] for s in v[5]} for g, v in GROUPS.items()}
    rows = []
    for y in range(FIRST, last + 1):
        games = 17 if y >= 2021 else 16
        for t in fetch(y):
            # Kickers sit in the "SPEC" group with punters and long snappers; take them by position.
            g = "K" if t.get("position") == "K" else (t.get("position_group") or t.get("position"))
            if g not in GROUPS:
                continue
            sing, plur, ptl, pt, bar, _ = GROUPS[g]
            if pt(t) < bar * games / 16:
                continue
            v = {}
            for k, _, f, _, y0, _, _ in stats:
                x = f(t) if (k in applies[g] and y >= y0) else None
                v[k] = None if x is None else float(x)
            rows.append({"name": t["player_display_name"] or t["player_name"], "pid": t["player_id"], "year": y,
                         "grp": g, "team": t.get("recent_team", ""), "pt": round(pt(t), 1), "v": v})
    data = build("nfl", stats, rows, list(GROUPS))
    data["groupNames"] = {g: [v[0], v[1]] for g, v in GROUPS.items()}
    data["ptLabel"] = {g: v[2] for g, v in GROUPS.items()}
    data["applies"] = {g: sorted(a) for g, a in applies.items()}
    out = os.path.join(REPO, "data", "stands-nfl.json")
    json.dump(data, open(out, "w"), separators=(",", ":"))
    print(f"nfl: {len(rows)} seasons, {len(data['names'])} players, {FIRST}-{last} -> "
          f"{os.path.relpath(out, REPO)} ({os.path.getsize(out) // 1024} KB)")


if __name__ == "__main__":
    main()
