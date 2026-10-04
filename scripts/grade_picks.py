#!/usr/bin/env python3
"""Grade pool picks against the spread, from a primary feed.

    python3 scripts/grade_picks.py --week 2026-w4 --dry-run
    python3 scripts/grade_picks.py --week 2026-w4

Weeks 3, 4 and 5 of 2026 sat ungraded in data/picks-ledger.json while the
season-to-date line still read "16-14, 136 of 240" from week 2. A scorecard that
stops updating is worse than no scorecard: it reports a stale number with the
authority of a current one.

SCORES COME FROM CFBD, NEVER FROM A SEARCH. This is the rule that exists because
Sunday Edition 022 led with a fabricated poll ranking. Anything that grades a
forecast has to trace to a primary feed.

THE SPREAD CONVENTION, because it is the thing that will be got wrong. Each pick
carries the line FROM THE PICKED TEAM'S POINT OF VIEW: negative means laying
points, positive means taking them. A pick covers when

    (picked_team_score - opponent_score) + spread > 0

A result of exactly zero is a push -- graded as neither win nor loss, and
excluded from the record rather than counted as a half.

TEAM NAMES ARE THE OTHER TRAP. CFBD and a hand-written sheet disagree constantly
(Ole Miss / Mississippi, UConn / Connecticut, Miami (OH) / Miami Ohio). Matching
is normalized and aliased, and anything that still fails to match is REPORTED
rather than silently dropped -- a pick that quietly vanishes looks like a pick
that was never made, which flatters the record.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
LEDGER = REPO / "data" / "picks-ledger.json"

ALIAS = {
    "ole miss": "mississippi", "uconn": "connecticut", "usc": "southern california",
    "miami oh": "miami ohio", "ucf": "central florida", "smu": "southern methodist",
    "pitt": "pittsburgh", "nc state": "north carolina state",
    "southern miss": "southern mississippi", "umass": "massachusetts",
    "app state": "appalachian state", "fiu": "florida international",
    "fau": "florida atlantic", "utsa": "texas san antonio",
    "nmexst": "new mexico state", "wky": "western kentucky",
    "washst": "washington state", "arizst": "arizona state",
    "iowast": "iowa state", "vatech": "virginia tech", "psu": "penn state",
    "nwest": "northwestern", "wvu": "west virginia", "af": "air force",
    "fsu": "florida state", "emich": "eastern michigan", "mizzou": "missouri",
    "sc": "south carolina", "uk": "kentucky", "tcu": "texas christian",
    "ntexas": "north texas", "fresno": "fresno state", "minn": "minnesota",
    "mich": "michigan", "cal": "california", "byu": "brigham young",
}


def norm(s):
    s = re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()
    s = re.sub(r"\s+", " ", s)
    s = ALIAS.get(s, s)
    for pre in ("university of ", "the "):
        s = s[len(pre):] if s.startswith(pre) else s
    return s


def key():
    p = pathlib.Path.home() / ".config/secrets/tokens.env"
    if os.environ.get("CFBD_KEY"):
        return os.environ["CFBD_KEY"]
    for ln in p.read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?CFBD_KEY\s*=\s*(.*)$", ln)
        if m:
            return m.group(1).strip().strip('"').strip("'")


def fetch_games(year, lo, hi):
    """Every FBS game in a week range, both classifications included."""
    K = key()
    out = []
    for wk in range(lo, hi + 1):
        u = (f"https://api.collegefootballdata.com/games?year={year}"
             f"&week={wk}&seasonType=regular")
        req = urllib.request.Request(u, headers={"Authorization": f"Bearer {K}"})
        out += json.load(urllib.request.urlopen(req, timeout=90))
    return [g for g in out if g.get("homePoints") is not None]


def find(games, a, b):
    """The game between these two, either orientation."""
    na, nb = norm(a), norm(b)
    for g in games:
        h, w = norm(g.get("homeTeam")), norm(g.get("awayTeam"))
        if {h, w} == {na, nb}:
            return g
    # fall back to containment, which catches "Miami" vs "Miami (OH)" style gaps
    for g in games:
        h, w = norm(g.get("homeTeam")), norm(g.get("awayTeam"))
        if (na in (h, w) or any(na in x for x in (h, w))) and \
           (nb in (h, w) or any(nb in x for x in (h, w))):
            return g
    return None


def grade(pick, opp, spread, g):
    """(correct, cover_margin, score_str) -- None,None when it is a push."""
    h, a = norm(g["homeTeam"]), norm(g["awayTeam"])
    if norm(pick) == h or norm(pick) in h:
        ps, os_ = g["homePoints"], g["awayPoints"]
    else:
        ps, os_ = g["awayPoints"], g["homePoints"]
    margin = (ps - os_) + spread
    score = (f'{g["awayTeam"]} {g["awayPoints"]}-{g["homePoints"]} {g["homeTeam"]}')
    if margin == 0:
        return None, 0.0, score
    return margin > 0, margin, score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", required=True, help="e.g. 2026-w4")
    ap.add_argument("--cfb-weeks", default="", help="CFBD week range, e.g. 4-5")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    led = json.loads(LEDGER.read_text())
    wk = led["weeks"].get(a.week)
    if not wk:
        raise SystemExit(f"{a.week} not in the ledger")
    picks = wk["picks"]

    year = int(a.week.split("-")[0])
    if a.cfb_weeks:
        lo, hi = (int(x) for x in a.cfb_weeks.split("-"))
    else:
        n = int(a.week.split("w")[1])
        lo, hi = n, n + 1
    games = fetch_games(year, lo, hi)
    print(f"  {len(games)} completed games pulled from CFBD, weeks {lo}-{hi}\n")

    hit = miss = push = 0
    pts = 0
    unmatched = []
    for p in picks:
        g = find(games, p["pick"], p["opp"])
        if not g:
            unmatched.append(f'{p["pick"]} vs {p["opp"]}')
            continue
        ok, cm, score = grade(p["pick"], p["opp"], float(p["spread"]), g)
        p["score"] = score
        p["cover_margin"] = round(cm, 1)
        p["correct"] = ok
        p["result"] = "push" if ok is None else ("win" if ok else "loss")
        if ok is None:
            push += 1
        elif ok:
            hit += 1; pts += p["pts"]
        else:
            miss += 1
        flag = "PUSH" if ok is None else ("WIN " if ok else "loss")
        print(f'  {p["pts"]:>2}  {flag}  {p["pick"]:<20} {p["spread"]:>5}  '
              f'{cm:>+6.1f}   {score[:48]}')

    if unmatched:
        print(f"\n  UNMATCHED ({len(unmatched)}) -- graded nothing for these:")
        for u in unmatched:
            print(f"    {u}")

    avail = sum(p["pts"] for p in picks)
    wk["ats_record"] = f"{hit}-{miss}" + (f"-{push}" if push else "")
    wk["points_earned"] = pts
    wk["points_available"] = avail
    wk["graded"] = {"on": datetime.date.today().isoformat(),
                    "source": "CollegeFootballData games endpoint",
                    "unmatched": unmatched}
    print(f"\n  {a.week}: {hit}-{miss}" + (f"-{push} push" if push else "") +
          f", {pts} of {avail} points")

    if a.dry_run:
        print("\n  --- DRY RUN, ledger not written ---")
        return 0
    LEDGER.write_text(json.dumps(led, indent=1) + "\n")
    print(f"  wrote {LEDGER.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
