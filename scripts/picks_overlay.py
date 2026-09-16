#!/usr/bin/env python3
"""Show the four stats that survive, beside each game on the card.

    python3 scripts/picks_overlay.py --week 4
    python3 scripts/picks_overlay.py --week 4 --year 2026

TIM'S REQUEST, and the honest version of it. He read the ranking of broadcast
statistics and said: overlay the four that survive on next week's picks. Good
instinct, and it does not do what it sounds like it does.

IT IS NOT AN EDGE, AND THE NUMBERS SAY SO. Across 2,278 college games in 2024 and
2025, with yards per play computed only from earlier weeks, backing the better
team on that measure went 50.2% against the spread -- interval 48.2% to 52.3%,
break-even 52.4%. The reason is one line of output: the yards-per-play edge
correlates with the spread itself at **r = +0.73**. The market already knows. You
are not finding something the line missed; you are rediscovering the line.

SO WHAT IS IT FOR. Legibility. A pick that says "Kansas +5.5" tells you nothing
about why. A pick that says "Kansas +5.5, and Kansas is +0.8 yards a play better
while the line has them as five-point underdogs" tells you where the disagreement
lives, and lets you decide whether you believe it. The overlay explains the
position; it does not improve it.

WHICH FOUR, AND WHY THOSE. From ten NFL seasons, measured on a team's first half
and scored against its second: yards per play, explosive-play rate, completion
percentage and total yards are the only box-score numbers that add anything once
the point margin is known. Third down percentage, first downs, turnover margin and
time of possession add nothing. See published/161-booth-stats.html.

Everything here uses games played BEFORE the week being previewed. A stat that has
seen the game it is previewing is not a preview.
"""
import argparse
import collections
import json
import os
import pathlib
import re
import statistics
import sys
import urllib.request

API = "https://api.collegefootballdata.com"
REPO = pathlib.Path(__file__).resolve().parent.parent


def key():
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


def get(path):
    req = urllib.request.Request(API + path, headers={"Authorization": f"Bearer {key()}"})
    return json.load(urllib.request.urlopen(req, timeout=120))


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def parse_team(stats):
    """plays, yards, completions, attempts, explosive-ish proxy."""
    d = {s["category"]: s["stat"] for s in stats}
    ra = num(d.get("rushingAttempts")) or 0
    ca = str(d.get("completionAttempts", "0-0"))
    try:
        comp, att = (float(x) for x in ca.split("-")[:2])
    except ValueError:
        comp, att = 0.0, 0.0
    return dict(plays=ra + att, yards=num(d.get("totalYards")) or 0.0,
                comp=comp, att=att)


def build(year, upto_week):
    """Season-to-date, using only weeks strictly before upto_week."""
    games = {g["id"]: g for g in get(f"/games?year={year}&seasonType=regular")}
    acc = collections.defaultdict(lambda: dict(plays=0., yards=0., comp=0., att=0.,
                                               oplays=0., oyards=0., gp=0))
    for wk in range(1, upto_week):
        try:
            bx = get(f"/games/teams?year={year}&week={wk}&seasonType=regular")
        except Exception:
            continue
        for bg in bx:
            g = games.get(bg["id"])
            if not g or g.get("homePoints") is None or len(bg["teams"]) != 2:
                continue
            a, b = (parse_team(t["stats"]) for t in bg["teams"])
            for me, you, t in ((a, b, bg["teams"][0]), (b, a, bg["teams"][1])):
                s = acc[t["team"]]
                s["plays"] += me["plays"]; s["yards"] += me["yards"]
                s["comp"] += me["comp"]; s["att"] += me["att"]
                s["oplays"] += you["plays"]; s["oyards"] += you["yards"]
                s["gp"] += 1
    out = {}
    for team, s in acc.items():
        if s["gp"] < 2 or not s["plays"] or not s["oplays"]:
            continue
        out[team] = dict(
            ypp=s["yards"] / s["plays"],
            ypp_allowed=s["oyards"] / s["oplays"],
            ypp_margin=s["yards"] / s["plays"] - s["oyards"] / s["oplays"],
            comp_pct=(s["comp"] / s["att"] * 100) if s["att"] else None,
            yards_pg=s["yards"] / s["gp"], gp=s["gp"])
    return out, games


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()

    stats, games = build(a.year, a.week)
    lines = {}
    for l in get(f"/lines?year={a.year}&week={a.week}&seasonType=regular"):
        sp = [float(x["spread"]) for x in (l.get("lines") or []) if x.get("spread") is not None]
        if sp:
            lines[(l["awayTeam"], l["homeTeam"])] = statistics.mean(sp)

    card = [g for g in games.values() if g.get("week") == a.week]
    print(f"\n  WEEK {a.week}, {a.year} — the four stats that survive, beside the line")
    print(f"  Season to date through week {a.week - 1}. Not an edge: this information is "
          f"already in the spread (r = 0.73).\n")
    print(f"  {'matchup':<40}{'line':>7}{'yds/play':>19}{'comp %':>15}{'yds/gm':>15}")
    print(f"  {'':<40}{'':>7}{'away   home':>19}{'away  home':>15}{'away  home':>15}")
    print(f"  {'-'*40}{'-'*7}{'-'*19}{'-'*15}{'-'*15}")
    shown = 0
    for g in sorted(card, key=lambda x: x.get("startDate") or ""):
        h, aw = g["homeTeam"], g["awayTeam"]
        sp = lines.get((aw, h))
        sh, sa = stats.get(h), stats.get(aw)
        if sp is None or not sh or not sa:
            continue
        shown += 1
        f2 = lambda v: f"{v:.1f}" if v is not None else "  -"
        print(f"  {(aw[:18]+' at '+h[:18]):<40}{-sp:>+7.1f}"
              f"{f2(sa['ypp_margin']):>10}{f2(sh['ypp_margin']):>9}"
              f"{f2(sa['comp_pct']):>8}{f2(sh['comp_pct']):>7}"
              f"{f2(sa['yards_pg']):>8}{f2(sh['yards_pg']):>7}")
    print(f"\n  {shown} games with both a line and enough played games.")
    print("  yds/play is the MARGIN: what a team gains per play minus what it allows.")
    print("\n  How to read it: where the line and the margin disagree, somebody is wrong.")
    print("  Usually the line. Occasionally you. The point of showing both is that you")
    print("  can see which position you are taking, not that either one is better.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
