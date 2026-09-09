#!/usr/bin/env python3
"""Log the games nobody's model saw coming, with everything that might explain them.

    python3 scripts/outlier_watch.py                 # latest completed week
    python3 scripts/outlier_watch.py --week 3
    python3 scripts/outlier_watch.py --report        # everything logged so far

WHY KEEP A CATALOGUE AT ALL. An outlier is where an omitted variable announces
itself. A rating is a compressed claim about what matters; when it misses by five
touchdowns, something it does not contain just moved the game. One such miss is a
story. Forty of them, logged with their covariates attached, is a dataset that can
answer whether the thing we suspect is real.

The catalogue exists because the alternative is arguing from anecdote. In week
one of 2026 Penn State returned 7.6% of its production, hired a new head coach,
and won 45-0; Clemson returned 41%, kept its staff, and lost by 41. That pairing
is vivid and it is worth exactly nothing on its own -- two games, chosen after the
fact because they point the way we already suspected. Accumulate a season and the
question becomes answerable instead of arguable.

WHAT GETS RECORDED, and why each is a candidate for the thing SP+ leaves out:

  returning production   share of last year's output back (SP+ already uses this,
                         so it is a check on OVER-weighting, not an omission)
  transfers in / out     roster churn in both directions
  imported_from          mean rating of the PROGRAMMES the incomers left. A club
                         that takes twenty players from a good programme is not
                         the same as one that takes twenty from bad ones, and no
                         public rating separates those.
  new head coach         first season in post
  talent                 recruiting composite, for the obvious control

CAUTION BUILT IN. Candidates are logged, never scored as findings. The report
prints the correlation of each against surprise WITH its sample size and t, so a
promising number cannot be read without seeing how thin it is. Anything under
about 150 games should be treated as a rumour.
"""
import argparse
import collections
import json
import math
import os
import statistics
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "data", "outliers.json")
API = "https://api.collegefootballdata.com"
SD, HFA = 16.5, 2.5
THRESHOLD = 17.0        # points of miss before a game is worth logging


def get(url):
    key = os.environ["CFBD_KEY"]
    return json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"}), timeout=90))


def covariates(year):
    sp = {r["team"]: r["rating"] for r in get(f"{API}/ratings/sp?year={year}")}
    ret = {r["team"]: r.get("percentPPA") for r in get(f"{API}/player/returning?year={year}")}
    try:
        talent = {r["team"]: float(r["talent"]) for r in get(f"{API}/talent?year={year}")}
    except Exception:
        talent = {}
    inn, out, origin = collections.Counter(), collections.Counter(), collections.defaultdict(list)
    try:
        for p in get(f"{API}/player/portal?year={year}"):
            d, o = p.get("destination"), p.get("origin")
            if d:
                inn[d] += 1
                if o in sp:
                    origin[d].append(sp[o])
            if o:
                out[o] += 1
    except Exception:
        pass
    firstyear = {}
    try:
        for c in get(f"{API}/coaches?year={year}"):
            for s in c.get("seasons", []):
                if s.get("year") == year:
                    firstyear[s["school"]] = int((c.get("hireDate") or "")[:4] in (str(year), str(year - 1)))
    except Exception:
        pass
    return dict(sp=sp, ret=ret, talent=talent, inn=inn, out=out, firstyear=firstyear,
                imported={t: round(statistics.mean(v), 2) for t, v in origin.items() if v})


def scan(year, week, cov):
    rows = []
    for g in get(f"{API}/games?year={year}&seasonType=regular&week={week}"):
        if g.get("homePoints") is None:
            continue
        h, a = g["homeTeam"], g["awayTeam"]
        if h not in cov["sp"] or a not in cov["sp"]:
            continue
        exp = cov["sp"][h] - cov["sp"][a] + (0 if g.get("neutralSite") else HFA)
        act = g["homePoints"] - g["awayPoints"]
        surprise = act - exp
        d = lambda m, k=None: (m.get(h, k) if isinstance(m, dict) else m[h])
        rows.append(dict(
            year=year, week=week, home=h, away=a, hp=g["homePoints"], ap=g["awayPoints"],
            expected=round(exp, 1), actual=act, surprise=round(surprise, 1),
            d_ret=(None if cov["ret"].get(h) is None or cov["ret"].get(a) is None
                   else round(cov["ret"][h] - cov["ret"][a], 3)),
            d_talent=(None if h not in cov["talent"] or a not in cov["talent"]
                      else round(cov["talent"][h] - cov["talent"][a], 1)),
            d_tin=cov["inn"][h] - cov["inn"][a],
            d_tout=cov["out"][h] - cov["out"][a],
            d_imported=(None if h not in cov["imported"] or a not in cov["imported"]
                        else round(cov["imported"][h] - cov["imported"][a], 2)),
            d_newhc=cov["firstyear"].get(h, 0) - cov["firstyear"].get(a, 0)))
    return rows


def corr(pairs):
    if len(pairs) < 8:
        return None
    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    if not den:
        return None
    r = num / den
    n = len(pairs)
    t = r * math.sqrt(n - 2) / math.sqrt(1 - r * r) if abs(r) < 1 else float("nan")
    return r, n, t


def report(rows):
    print(f"\n  {len(rows)} games logged across "
          f"{len(set((r['year'], r['week']) for r in rows))} week(s)\n")
    big = sorted(rows, key=lambda r: -abs(r["surprise"]))
    print("  THE MISSES THEMSELVES\n")
    print(f"  {'matchup':<40}{'score':>9}{'exp':>8}{'miss':>8}")
    for r in big[:12]:
        print(f"  {(r['away'][:17]+' at '+r['home'][:17]):<40}"
              f"{str(r['ap'])+'-'+str(r['hp']):>9}{r['expected']:>+8.1f}{r['surprise']:>+8.1f}")
    print("\n  CANDIDATE OMITTED VARIABLES -- correlation with the miss\n")
    print(f"  {'variable (home minus away)':<38}{'r':>8}{'n':>6}{'t':>7}   verdict")
    labels = [("d_ret", "returning production"), ("d_talent", "recruiting talent"),
              ("d_tin", "transfers in"), ("d_tout", "transfers out"),
              ("d_imported", "quality of programmes left"), ("d_newhc", "new head coach")]
    for k, lab in labels:
        c = corr([(r[k], r["surprise"]) for r in rows if r.get(k) is not None])
        if not c:
            continue
        r_, n, t = c
        v = ("RUMOUR -- too few games" if n < 150 else
             "worth pursuing" if abs(t) > 2.5 else
             "nothing here")
        print(f"  {lab:<38}{r_:>+8.3f}{n:>6}{t:>+7.2f}   {v}")
    print("\n  Nothing above is a finding. Correlations on a few dozen games move")
    print("  wildly week to week; the catalogue exists so that by November they")
    print("  do not have to.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--week", type=int)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--threshold", type=float, default=THRESHOLD)
    a = ap.parse_args()

    ledger = json.load(open(LEDGER)) if os.path.exists(LEDGER) else {"games": []}
    if a.report:
        if not ledger["games"]:
            raise SystemExit("nothing logged yet")
        report(ledger["games"])
        return

    week = a.week
    if week is None:
        done = [g["week"] for g in get(f"{API}/games?year={a.year}&seasonType=regular")
                if g.get("homePoints") is not None]
        week = max(done) if done else 1

    cov = covariates(a.year)
    rows = scan(a.year, week, cov)
    keep = [r for r in rows if abs(r["surprise"]) >= a.threshold]
    have = {(g["year"], g["week"], g["home"], g["away"]) for g in ledger["games"]}
    new = [r for r in keep if (r["year"], r["week"], r["home"], r["away"]) not in have]
    ledger["games"] += new
    # every rated game is kept for the correlations; the threshold only decides
    # what counts as an OUTLIER worth naming in the write-up
    ledger.setdefault("all", [])
    seen = {(g["year"], g["week"], g["home"], g["away"]) for g in ledger["all"]}
    ledger["all"] += [r for r in rows if (r["year"], r["week"], r["home"], r["away"]) not in seen]
    json.dump(ledger, open(LEDGER, "w"), indent=1)

    print(f"\n  week {week}: {len(rows)} rated games, {len(keep)} missed by "
          f"{a.threshold:.0f}+ points, {len(new)} newly logged")
    report(ledger["all"])


if __name__ == "__main__":
    main()
