#!/usr/bin/env python3
"""Build the day's "What to Watch" block across every league we cover.

    python3 scripts/daily_watch.py            # write data/daily-watch.html
    python3 scripts/daily_watch.py --print    # show it, write nothing
    python3 scripts/daily_watch.py --date 2026-09-05

ONE GAME PER LEAGUE, chosen by a measure appropriate to that league, plus a
scored follow-up on what we flagged yesterday.

  BASEBALL uses championship leverage: simulate the remaining season once, then
  split those seasons by who won each of today's games. The gap is how much
  playoff probability rides on it. The biggest game is rarely the one with the
  best teams -- it is the one where both clubs sit nearest a coin flip.

  COLLEGE FOOTBALL cannot use that: twelve games and a committee, not a
  standings table. So it uses INFORMATION instead. A game between clubs the
  ratings already separate tells you nothing you did not know; a close game
  between teams that matter is where the week's knowledge actually moves. Win
  probability comes from the rank-gap model published in Issue #135, and games
  are ranked by how close to a coin flip they are, weighted by how good the
  teams are.

  THE FOLLOW-UP is the honest part. Every day's pick is written to
  data/watch-ledger.json, and the next day's block reports what happened to it.
  A block that makes a claim and never checks it is advertising.

Every section is independently guarded: one league failing must not cost the
others, and the whole thing failing must not cost the issue.
"""
import argparse
import datetime
import json
import math
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "daily-watch.html")
LEDGER = os.path.join(REPO, "data", "watch-ledger.json")
MLB = "https://statsapi.mlb.com/api/v1"
CFBD = "https://api.collegefootballdata.com"
NSIMS, BATCH = 60000, 6000

# Issue #135's fitted model: neutral site is the reference category.
B0, BGAP, BHOME, BAWAY = -0.0744, 0.1064, 0.5179, -0.8887


def jget(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    return json.load(urllib.request.urlopen(req, timeout=90))


def et(iso):
    if not iso or len(iso) < 16:
        return ""
    hh = (int(iso[11:13]) - 4) % 24
    return f"{hh % 12 or 12}:{iso[14:16]}{'am' if hh < 12 else 'pm'} ET"


# --------------------------------------------------------------------------- MLB
def mlb_watch(date):
    import numpy as np
    st = jget(f"{MLB}/standings?leagueId=103,104&season={date[:4]}"
              f"&standingsTypes=regularSeason&date={date}")
    T = {}
    for rec in st["records"]:
        for t in rec["teamRecords"]:
            T[str(t["team"]["id"])] = dict(
                name=t["team"]["name"], w=t["wins"], l=t["losses"],
                div=rec["division"]["id"], lg=rec["league"]["id"],
                rs=int(t["runsScored"]), ra=int(t["runsAllowed"]))
    s = jget(f"{MLB}/schedule?sportId=1&startDate={date}&endDate={date[:4]}-11-15")
    G, today = [], []
    for day in s.get("dates", []):
        for g in day["games"]:
            if g["gameType"] != "R" or g["status"]["detailedState"] in ("Postponed", "Cancelled"):
                continue
            if g["status"]["abstractGameState"] == "Final":
                continue
            G.append((str(g["teams"]["away"]["team"]["id"]), str(g["teams"]["home"]["team"]["id"])))
            if day["date"] == date:
                today.append((len(G) - 1, g.get("gameDate", "")))
    if not today or not G:
        return None
    ids = sorted(T); idx = {t: i for i, t in enumerate(ids)}; n = len(ids)
    W0 = np.array([T[t]["w"] for t in ids], float)
    GP = np.array([T[t]["w"] + T[t]["l"] for t in ids], float)
    PY = np.array([T[t]["rs"] ** 1.83 / (T[t]["rs"] ** 1.83 + T[t]["ra"] ** 1.83) for t in ids])
    ACT = np.array([T[t]["w"] / (T[t]["w"] + T[t]["l"]) for t in ids])
    DIV = np.array([T[t]["div"] for t in ids]); LG = np.array([T[t]["lg"] for t in ids])
    tal = ((.5 * ACT + .5 * PY) * GP + .5 * 69) / (GP + 69); tal *= .5 / tal.mean()
    ga = np.array([idx[a] for a, h in G]); gh = np.array([idx[h] for a, h in G])
    l5 = (tal[gh] - tal[gh] * tal[ga]) / (tal[gh] + tal[ga] - 2 * tal[gh] * tal[ga])
    P = 1 / (1 + np.exp(-(np.log(l5 / (1 - l5)) + math.log(.535 / .465))))
    rng = np.random.default_rng(int(date.replace("-", "")) % 2 ** 31)
    cols = [g for g, _ in today]; MADE, HW = [], []
    for _ in range(NSIMS // BATCH):
        hw = rng.random((BATCH, len(G))) < P
        w = np.zeros((BATCH, n))
        np.add.at(w.T, gh, hw.T.astype(float)); np.add.at(w.T, ga, (~hw).T.astype(float))
        key = W0 + w + rng.random((BATCH, n)) * 1e-6
        inpo = np.zeros((BATCH, n), bool)
        for lg in (103, 104):
            lgm = LG == lg
            for dv in np.unique(DIV[lgm]):
                col = np.where(DIV == dv)[0]
                inpo[np.arange(BATCH), col[key[:, col].argmax(1)]] = True
            cand = np.where(lgm)[0]
            k2 = key[:, cand].copy(); k2[inpo[:, cand]] = -1
            t3 = np.argsort(-k2, 1)[:, :3]
            for j in range(3):
                inpo[np.arange(BATCH), cand[t3[:, j]]] = True
        MADE.append(inpo); HW.append(hw[:, cols])
    made = np.vstack(MADE); hwins = np.vstack(HW)
    best = None
    for k, (gi, when) in enumerate(today):
        a, h = G[gi]; ia, ih = idx[a], idx[h]
        m = hwins[:, k]
        if m.sum() < 500 or (~m).sum() < 500:
            continue
        dh = made[m, ih].mean() - made[~m, ih].mean()
        da = made[m, ia].mean() - made[~m, ia].mean()
        row = dict(sport="Baseball", swing=abs(dh) + abs(da), when=when,
                   home=T[h]["name"], away=T[a]["name"], dh=dh, da=da,
                   hp=float(made[:, ih].mean()), ap=float(made[:, ia].mean()),
                   hrec=f'{T[h]["w"]}-{T[h]["l"]}', arec=f'{T[a]["w"]}-{T[a]["l"]}')
        if best is None or row["swing"] > best["swing"]:
            best = row
    if not best:
        return None
    both = 0.06 < min(best["hp"], best["ap"]) and max(best["hp"], best["ap"]) < 0.94
    best["why"] = (f'{best["swing"]*100:.0f} points of playoff probability ride on it. '
                   + ("Both clubs sit near a coin flip, which is where a single game is worth most."
                      if both else
                      "One club is on the bubble and the other is settled, so the whole swing lands on one side."))
    best["tells"] = (f'If the {best["home"]} win they go to {(best["hp"]+abs(best["dh"])/2)*100:.0f}%; '
                     f'if they lose, {(best["hp"]-abs(best["dh"])/2)*100:.0f}%.')
    return best


# --------------------------------------------------------------------------- CFB
ALIAS = {"Ohio St": "Ohio State", "Penn St": "Penn State", "Miami FL": "Miami",
         "Mississippi": "Ole Miss", "Mississippi St": "Mississippi State",
         "Michigan St": "Michigan State", "Florida St": "Florida State",
         "Oregon St": "Oregon State", "Boise St": "Boise State", "Arizona St": "Arizona State",
         "Iowa St": "Iowa State", "Kansas St": "Kansas State", "N Carolina": "North Carolina",
         "San Diego St": "San Diego State", "Southern Cal": "USC", "Appalachian St": "Appalachian State",
         "Fresno St": "Fresno State", "Washington St": "Washington State", "Oklahoma St": "Oklahoma State"}


def cfb_watch(date):
    key = os.environ.get("CFBD_KEY")
    if not key:
        return None
    path = os.path.join(REPO, "data", "massey-preseason-2026.json")
    if not os.path.exists(path):
        return None
    R = {}
    for t in json.load(open(path)):
        R[ALIAS.get(t["team"], t["team"])] = t["cmp"]
    hdr = {"Authorization": "Bearer " + key}
    games = []
    for wk in range(0, 17):
        try:
            g = jget(f"{CFBD}/games?year={date[:4]}&week={wk}&seasonType=regular", hdr)
        except Exception:
            continue
        hit = [x for x in g if (x.get("startDate") or "")[:10] == date]
        if hit:
            games = hit
            break
    if not games:
        return None
    best = None
    for x in games:
        h, a = x.get("homeTeam"), x.get("awayTeam")
        rh, ra = R.get(h), R.get(a)
        if rh is None or ra is None:
            continue
        if min(rh, ra) > 45:                      # at least one club that matters
            continue
        gap = abs(rh - ra)
        fav_home = rh < ra
        neutral = bool(x.get("neutralSite"))
        lo = B0 + BGAP * gap + (0 if neutral else (BHOME if fav_home else BAWAY))
        p = 1 / (1 + math.exp(-lo))               # chance the better-ranked club wins
        closeness = 1 - abs(p - 0.5) * 2          # 1.0 at a coin flip, 0 at certainty
        quality = 1 - (min(rh, ra) - 1) / 45      # how much the better club matters
        score = closeness * quality
        row = dict(sport="College Football", score=score, when=x.get("startDate", ""),
                   home=h, away=a, rh=rh, ra=ra, p=p, neutral=neutral, gap=gap)
        if best is None or score > best["score"]:
            best = row
    if not best:
        return None
    fav = best["home"] if best["rh"] < best["ra"] else best["away"]
    best["why"] = (f'The ratings put these two {best["gap"]} places apart, making it '
                   f'{"an" if str(int(best["p"]*100))[0] in "18" else "a"} '
                   f'{best["p"]*100:.0f}/{100-best["p"]*100:.0f} game. '
                   + ("Neutral field, so neither side gets the thirteen ranks home advantage is worth."
                      if best["neutral"] else
                      ("Close games between ranked teams are where a week's rankings actually move."
                       if best["p"] < 0.75 else
                       "Nothing on today's card is close, so the ratings are unlikely to learn much.")))
    p = best["p"]
    if p < 0.62:
        best["tells"] = f'{fav} are favoured, and only just.'
    elif p < 0.75:
        best["tells"] = f'{fav} are favoured. Not a coin flip, but the closest thing on the card.'
    else:
        best["tells"] = (f'{fav} are heavy favourites. This is the <em>closest</em> game today involving a '
                         f'ranked side, which tells you how thin the slate is.')
    return best


# --------------------------------------------------------------------------- NFL
def nfl_watch(date):
    """Regular season and playoffs only.

    A preseason game is the one football result that carries no information at
    all -- starters play a series and the outcome is discarded by everyone,
    including the teams. ESPN marks it season.type == 1. An early version of
    this script picked up a preseason game on 2026-08-29 and captioned it "week
    one, the first real information of the season", which was false twice over.
    """
    try:
        d = jget("https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
                 f"?dates={date.replace('-','')}")
    except Exception:
        return None
    live = [e for e in d.get("events", []) if e.get("season", {}).get("type") in (2, 3)]
    if not live:
        return None
    e = live[0]
    c = e["competitions"][0]["competitors"]
    home = next(x["team"]["displayName"] for x in c if x["homeAway"] == "home")
    away = next(x["team"]["displayName"] for x in c if x["homeAway"] == "away")
    wk = (d.get("week") or {}).get("number")
    post = e.get("season", {}).get("type") == 3
    return dict(sport="Pro Football", when=e.get("date", ""), home=home, away=away,
                why=("A playoff game: one loss ends a season." if post
                     else f"Week {wk}. " + ("Opening week, so every result is the first real "
                                            "evidence against a whole summer of expectation."
                                            if wk == 1 else
                                            "Seventeen games is a small sample; each one moves a "
                                            "playoff picture more than a baseball game ever could.")),
                tells="")


# --------------------------------------------------------------------------- yesterday
def yesterday_result(date):
    if not os.path.exists(LEDGER):
        return None
    led = json.load(open(LEDGER))
    prev = (datetime.date.fromisoformat(date) - datetime.timedelta(days=1)).isoformat()
    e = led.get(prev)
    if not e:
        return None
    pick = e.get("mlb")
    if not pick:
        return None
    try:
        s = jget(f"{MLB}/schedule?sportId=1&date={prev}")
        for day in s.get("dates", []):
            for g in day["games"]:
                hn = g["teams"]["home"]["team"]["name"]; an = g["teams"]["away"]["team"]["name"]
                if hn != pick["home"] or an != pick["away"]:
                    continue
                if g["status"]["abstractGameState"] != "Final":
                    continue
                hs = g["teams"]["home"].get("score"); as_ = g["teams"]["away"].get("score")
                if hs is None or as_ is None:
                    continue
                won = hn if hs > as_ else an
                moved = pick["dh"] if won == hn else -pick["dh"]
                direction = "gained" if moved > 0 else "lost"
                return (f'<strong>{an} {as_}, {hn} {hs}.</strong> We flagged this as the day\'s '
                        f'biggest game, worth {pick["swing"]*100:.0f} points. {won} won, so '
                        f'{pick["home"]} {direction} about {abs(pick["dh"])*100:.0f} points of '
                        f'playoff probability and today\'s picture starts from there.')
    except Exception:
        return None
    return None


# --------------------------------------------------------------------------- render
def render(picks, yday, date):
    d = datetime.date.fromisoformat(date)
    rows = ""
    for p in picks:
        rows += (f'<div class="w-row"><div class="w-sport">{p["sport"]}</div>'
                 f'<div class="w-game"><strong>{p["away"]}</strong> at <strong>{p["home"]}</strong>'
                 f'{" &middot; neutral site" if p.get("neutral") else ""}'
                 f'<span class="w-time">{et(p["when"])}</span></div>'
                 f'<div class="w-why">{p["why"]} {p.get("tells","")}</div></div>')
    yblock = (f'<p class="w-yday"><span class="w-ylab">Yesterday</span> {yday}</p>' if yday else "")
    return f'''<div class="watch">
  <div class="watch-label">What to Watch &middot; {d.strftime("%A, %B %-d")}</div>
  {yblock}{rows}
  <p class="watch-note">Baseball is ranked by championship leverage: we simulate the rest of the
     season 60,000 times, then split those seasons by who won each of today's games. College
     football cannot be simulated that way, so it is ranked by how close to a coin flip the
     ratings make it &mdash; a lopsided game teaches you nothing. Tomorrow this block reports what
     happened to today's pick.</p>
</div>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--print", dest="show", action="store_true")
    a = ap.parse_args()
    picks = []
    for fn, label in ((mlb_watch, "MLB"), (cfb_watch, "CFB"), (nfl_watch, "NFL")):
        try:
            r = fn(a.date)
            if r:
                picks.append(r)
                print(f"  {label}: {r['away']} at {r['home']}")
            else:
                print(f"  {label}: no game today")
        except Exception as e:
            print(f"  {label}: FAILED ({type(e).__name__}: {e})")
    if not picks:
        print("  nothing to watch; no block written")
        if os.path.exists(OUT):
            os.remove(OUT)
        return 0
    try:
        yday = yesterday_result(a.date)
    except Exception:
        yday = None
    html = render(picks, yday, a.date)
    if a.show:
        print("\n" + html)
        return 0
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    led = json.load(open(LEDGER)) if os.path.exists(LEDGER) else {}
    m = next((p for p in picks if p["sport"] == "Baseball"), None)
    led[a.date] = {"mlb": {k: m[k] for k in ("home", "away", "swing", "dh", "da")} if m else None}
    with open(LEDGER, "w", encoding="utf-8") as f:
        json.dump(led, f, indent=1)
    print(f"  wrote {os.path.relpath(OUT, REPO)} and updated the ledger")
    return 0


if __name__ == "__main__":
    sys.exit(main())
