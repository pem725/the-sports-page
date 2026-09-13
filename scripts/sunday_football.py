#!/usr/bin/env python3
"""The football-season Sunday Edition, built from feeds instead of memory.

    python3 scripts/sunday_football.py                 # print the blocks
    python3 scripts/sunday_football.py --inject FILE   # swap into the markers
    python3 scripts/sunday_football.py --week 2        # grade a specific week

WHY THIS EXISTS. From September to January the Sunday Edition is not a generic
weekly recap; it sits between the two things readers actually care about. Saturday
just happened and today has a full NFL card. So the edition has a fixed shape:

    1. one line saying whether we owe you a scorecard
    2. what yesterday's college football actually showed, measured
    3. the improbability lesson -- the reason Sunday is the right day for it
    4. what to watch today, and why that game and not the famous one

WHAT IT REFUSES TO DO, and this is the point of building it as a script at all.
The first football-season Sunday we wrote by hand contained three wrong numbers
about one baseball team, two of which contradicted each other inside the same
piece. Numbers recalled in prose at 4am are numbers that will be wrong. Every
figure below comes from a feed at generation time, or it does not appear.

IT GRADES ON FROZEN RATINGS. An upset is only surprising relative to what was
believed BEFORE kickoff, so the week's snapshot from snapshot_ratings.py is
required. If it is missing the script exits rather than falling back to today's
ratings, because grading Saturday on ratings that have already absorbed Saturday
is how you convince yourself you saw it coming. That is the same leakage that
produced a 15-for-15 backtest here (see published/154-no-edge.html).

THE UPSET MATH IS THE LESSON. A 1-in-13 result is startling in its own game and
close to inevitable across a fifty-game card. Summing every underdog's win
probability gives the number of upsets a normal Saturday should produce; printing
that beside the actual count is the whole argument against "nobody saw this
coming." Somebody did. They were just wrong about which game.
"""
import argparse
import datetime
import json
import math
import os
import pathlib
import re
import sys
import urllib.request

CFBD = "https://api.collegefootballdata.com"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
REPO = pathlib.Path(__file__).resolve().parent.parent
SNAPS = REPO / "data" / "rating-snapshots"
HFA, SD_CFB, SD_NFL = 2.5, 16.5, 13.5
YEAR = 2026


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


def cfbd(path):
    req = urllib.request.Request(CFBD + path, headers={"Authorization": f"Bearer {key()}"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def prob(margin, sd):
    return 0.5 * (1 + math.erf(margin / (sd * math.sqrt(2))))


def latest_played_week():
    weeks = [g["week"] for g in cfbd(f"/games?year={YEAR}&seasonType=regular")
             if g.get("homePoints") is not None]
    return max(weeks) if weeks else None


def saturday(week):
    """Grade the week against the ratings frozen before it was played."""
    snap = SNAPS / f"{YEAR}-w{week:02d}.json"
    if not snap.exists():
        raise SystemExit(
            f"no frozen snapshot at {snap}.\n"
            "  Refusing to grade an upset on ratings that have already seen the result.\n"
            "  Run scripts/snapshot_ratings.py on the Thursday before each card.")
    s = json.loads(snap.read_text())
    sp, lines = s["sp"], s.get("lines", {})

    games, expected, actual, rated = [], 0.0, 0, 0
    for g in cfbd(f"/games?year={YEAR}&seasonType=regular&week={week}"):
        if g.get("homePoints") is None:
            continue
        h, a = g["homeTeam"], g["awayTeam"]
        if h not in sp or a not in sp:
            continue          # unrated opponent: no projection, and none invented
        rated += 1
        edge = sp[h] - sp[a] + (0 if g.get("neutralSite") else HFA)
        p_home = prob(edge, SD_CFB)
        p_dog = min(p_home, 1 - p_home)
        expected += p_dog
        margin = g["homePoints"] - g["awayPoints"]
        upset = (margin > 0) != (edge > 0)
        actual += upset
        if upset:
            win, lose = (h, a) if margin > 0 else (a, h)
            ws, ls = (g["homePoints"], g["awayPoints"]) if margin > 0 else (g["awayPoints"], g["homePoints"])
            games.append(dict(p=p_dog, winner=win, loser=lose, ws=ws, ls=ls,
                              line=lines.get(f"{a} @ {h}")))
    games.sort(key=lambda r: r["p"])
    return dict(week=week, taken=s["taken"], rated=rated,
                expected=expected, actual=actual, upsets=games)


def nfl_today(date=None):
    d = (date or datetime.date.today()).strftime("%Y%m%d")
    data = json.load(urllib.request.urlopen(f"{ESPN}?dates={d}", timeout=45))
    out = []
    for e in data.get("events", []):
        c = e["competitions"][0]
        away = [x for x in c["competitors"] if x["homeAway"] == "away"][0]["team"]
        home = [x for x in c["competitors"] if x["homeAway"] == "home"][0]["team"]
        o = (c.get("odds") or [{}])[0]
        det = o.get("details")
        if not det or " " not in det:
            continue
        fav, num = det.rsplit(" ", 1)
        try:
            spread = abs(float(num))
        except ValueError:
            continue
        out.append(dict(away=away["abbreviation"], home=home["abbreviation"],
                        away_name=away.get("displayName"), home_name=home.get("displayName"),
                        fav=fav.strip(), spread=spread, p_fav=prob(spread, SD_NFL),
                        kick=e["status"]["type"]["shortDetail"].split(" - ")[-1],
                        ou=o.get("overUnder")))
    out.sort(key=lambda g: g["spread"])
    return out


def blocks(sat, nfl):
    u = sat["upsets"]
    top = u[0] if u else None
    rows = "".join(
        f'      <tr{" class=\"hl\"" if i == 0 else ""}><td>{g["winner"]} beat {g["loser"]}</td>'
        f'<td class="mono">{g["ws"]}&ndash;{g["ls"]}</td>'
        f'<td class="mono">1 in {1/g["p"]:.0f}</td></tr>\n'
        for i, g in enumerate(u[:5]))
    nfl_rows = "".join(
        f'      <tr><td class="mono">{g["away"]} at {g["home"]}</td>'
        f'<td class="mono">{g["fav"]} by {g["spread"]:.1f}</td>'
        f'<td class="mono">{g["p_fav"]*100:.0f}%</td><td>{g["kick"]}</td></tr>\n'
        for g in nfl[:5])

    cfb = f'''<h2 class="sh">The improbable thing that happened yesterday</h2>

  <p>{"" if not top else f'{top["winner"]} beat {top["loser"]} {top["ws"]}&ndash;{top["ls"]}. That was about a <strong>1 in {1/top["p"]:.0f}</strong> result.'}</p>

  <p><strong>There were {sat["rated"]} rated games on the card.</strong> Add up every underdog&rsquo;s chance of winning its own game and you get <strong>{sat["expected"]:.1f}</strong> &mdash; the number of upsets a normal Saturday should produce. The actual count was <strong>{sat["actual"]}</strong>.</p>

  <p>Notice what that does to the word "improbable." A long shot is unlikely <em>in its own game</em>; across a full card it is close to inevitable that <em>something</em> like it happens. The surprise was never that an upset occurred. The surprise is only ever <em>which one</em>.</p>

  <table class="rec">
    <thead><tr><th>Yesterday&rsquo;s least likely winners</th><th>Score</th><th>Chance</th></tr></thead>
    <tbody>
{rows}    </tbody>
  </table>
  <p style="font-size:.72rem;color:var(--muted)">Chances from our ratings frozen {sat["taken"]}, before any of these were played. Grading an upset on ratings updated <em>after</em> it is how you convince yourself you saw it coming.</p>'''

    watch = f'''<h2 class="sh">What to watch today, and why</h2>

  <p>The best game on a card is rarely the one with the best teams; it is the one nearest a coin flip, because that is where the result carries the most information.</p>

  <table class="rec">
    <thead><tr><th>Closest games</th><th>Line</th><th>Favourite wins</th><th>Kickoff</th></tr></thead>
    <tbody>
{nfl_rows}    </tbody>
  </table>
  <p style="font-size:.72rem;color:var(--muted)">Probabilities from the closing spread with a {SD_NFL}-point standard deviation. Where we hold no forecast of our own, we say so rather than dress a guess up as one.</p>'''
    return cfb, watch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int)
    ap.add_argument("--inject", help="HTML file carrying CFB_RECAP_BLOCK / NFL_WATCH_BLOCK markers")
    a = ap.parse_args()

    week = a.week or latest_played_week()
    if week is None:
        raise SystemExit("no completed weeks yet")
    sat = saturday(week)
    nfl = nfl_today()
    cfb_html, watch_html = blocks(sat, nfl)

    if a.inject:
        p = pathlib.Path(a.inject)
        t = p.read_text()
        for marker, html in (("<!-- CFB_RECAP_BLOCK -->", cfb_html),
                             ("<!-- NFL_WATCH_BLOCK -->", watch_html)):
            if marker not in t:
                print(f"  marker {marker} not present; skipped")
                continue
            t = t.replace(marker, html, 1)
        p.write_text(t)
        print(f"  injected into {p}")
        return 0

    print(f"\n  week {week}: {sat['rated']} rated games, "
          f"{sat['expected']:.1f} expected upsets, {sat['actual']} actual")
    print(f"  ratings frozen {sat['taken']}\n")
    for g in sat["upsets"][:5]:
        line = f", line {g['line']}" if g["line"] else ""
        print(f"    {g['winner'][:22]:<23}beat {g['loser'][:20]:<21}"
              f"{g['ws']}-{g['ls']:<4} 1 in {1/g['p']:.0f}{line}")
    print(f"\n  NFL today, closest first ({len(nfl)} games with a line):\n")
    for g in nfl[:6]:
        print(f"    {g['away']:>4} at {g['home']:<5}{g['fav']} by {g['spread']:<5.1f}"
              f"{g['p_fav']*100:>5.0f}%   {g['kick']}")
    print("\n  --- HTML blocks ---\n")
    print(cfb_html[:400] + "\n  [...]\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
