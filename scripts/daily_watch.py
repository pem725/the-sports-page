#!/usr/bin/env python3
"""Build the day's "What to Watch" block: the game that matters most, and why.

    python3 scripts/daily_watch.py            # writes data/daily-watch.html
    python3 scripts/daily_watch.py --print    # print the reasoning, write nothing

IMPORTANCE IS MEASURED, NOT ASSERTED. For every game on today's card we compute
championship leverage: how much playoff probability changes hands depending on
who wins. One simulation of the whole remaining season is run, then each game's
outcome is used to split those seasons in two -- the clubs' playoff rates when
the home side won against when it lost. The difference is the swing.

Conditioning inside one run rather than re-simulating each game twice is exact,
because games are independent given team strength, and it is ~30x cheaper.
Checked against the brute-force version on 2026-08-29: the conditional method
gave +7.0/-7.9 for Mariners-Blue Jays, forced re-simulation gave +7.1/-7.6.

The result is usually counterintuitive in a useful way. The biggest game is
rarely the one with the best teams; it is the one where BOTH clubs sit near a
coin flip, because that is where a single win moves the most.
"""
import argparse
import datetime
import json
import math
import pathlib
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "daily-watch.html"
API = "https://statsapi.mlb.com/api/v1"
NSIMS, BATCH = 60000, 6000


def get(p):
    return json.load(urllib.request.urlopen(API + p, timeout=90))


def build(date):
    import numpy as np
    st = get(f"/standings?leagueId=103,104&season={date[:4]}"
             f"&standingsTypes=regularSeason&date={date}")
    T = {}
    for rec in st["records"]:
        for t in rec["teamRecords"]:
            T[str(t["team"]["id"])] = dict(
                name=t["team"]["name"], w=t["wins"], l=t["losses"],
                div=rec["division"]["id"], lg=rec["league"]["id"],
                rs=int(t["runsScored"]), ra=int(t["runsAllowed"]))
    s = get(f"/schedule?sportId=1&startDate={date}&endDate={date[:4]}-11-15")
    G, today = [], []
    for day in s.get("dates", []):
        for g in day["games"]:
            if g["gameType"] != "R":
                continue
            if g["status"]["detailedState"] in ("Postponed", "Cancelled"):
                continue
            if g["status"]["abstractGameState"] == "Final":
                continue
            G.append((str(g["teams"]["away"]["team"]["id"]),
                      str(g["teams"]["home"]["team"]["id"])))
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
    tal = (( .5 * ACT + .5 * PY) * GP + .5 * 69) / (GP + 69); tal *= .5 / tal.mean()
    ga = np.array([idx[a] for a, h in G]); gh = np.array([idx[h] for a, h in G])
    l5 = (tal[gh] - tal[gh] * tal[ga]) / (tal[gh] + tal[ga] - 2 * tal[gh] * tal[ga])
    P = 1 / (1 + np.exp(-(np.log(l5 / (1 - l5)) + math.log(.535 / .465))))

    rng = np.random.default_rng(int(date.replace("-", "")) % 2 ** 31)
    cols = [g for g, _ in today]
    MADE, HW = [], []
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

    rows = []
    for k, (gi, when) in enumerate(today):
        a, h = G[gi]; ia, ih = idx[a], idx[h]
        m = hwins[:, k]
        if m.sum() < 500 or (~m).sum() < 500:
            continue
        dh = made[m, ih].mean() - made[~m, ih].mean()
        da = made[m, ia].mean() - made[~m, ia].mean()
        rows.append(dict(swing=abs(dh) + abs(da), home=T[h]["name"], away=T[a]["name"],
                         dh=dh, da=da, when=when,
                         hw=T[h]["w"], hl=T[h]["l"], aw=T[a]["w"], al=T[a]["l"],
                         hp=made[:, ih].mean(), ap=made[:, ia].mean()))
    rows.sort(key=lambda r: -r["swing"])
    # a doubleheader appears twice with identical clubs; number them so the list reads sensibly
    from collections import Counter
    pair = Counter((r["away"], r["home"]) for r in rows)
    order = Counter()
    for r in sorted(rows, key=lambda z: z["when"]):
        k = (r["away"], r["home"])
        if pair[k] > 1:
            order[k] += 1
            r["game_no"] = order[k]
    return rows


def et(iso):
    if not iso or len(iso) < 16:
        return ""
    hh = (int(iso[11:13]) - 4) % 24
    ampm = "am" if hh < 12 else "pm"
    h12 = hh % 12 or 12
    return f"{h12}:{iso[14:16]}{ampm} ET"


def render(rows, date):
    top = rows[0]
    both = min(top["hp"], top["ap"]) > 0.06 and max(top["hp"], top["ap"]) < 0.94
    why = ("Both clubs sit near a coin flip, which is exactly where one game is worth most."
           if both else
           "One club is on the bubble and the other is already settled, so the whole swing lands on one side.")
    others = "".join(
        f'<li><strong>{r["away"]}</strong> at <strong>{r["home"]}</strong>'
        f'{" (game " + str(r["game_no"]) + ")" if r.get("game_no") else ""} '
        f'<span class="wt">{et(r["when"])}</span> &mdash; {r["swing"]*100:.0f} points</li>'
        for r in rows[1:4])
    mover = top["home"] if abs(top["dh"]) >= abs(top["da"]) else top["away"]
    md = top["dh"] if abs(top["dh"]) >= abs(top["da"]) else top["da"]
    base = top["hp"] if mover == top["home"] else top["ap"]
    return f'''<div class="watch">
  <div class="watch-label">What to Watch &middot; {datetime.date.fromisoformat(date).strftime("%A, %B %-d")}</div>
  <p class="watch-lede">The game that matters most today is
     <strong>{top["away"]} ({top["aw"]}-{top["al"]}) at {top["home"]} ({top["hw"]}-{top["hl"]})</strong>{" game " + str(top["game_no"]) if top.get("game_no") else ""},
     {et(top["when"])}.</p>
  <p><strong>{top["swing"]*100:.0f} points</strong> of playoff probability change hands on it. {why}
     The {mover} move {abs(md)*100:.0f} points either way, from a standing start of {base*100:.0f}%.</p>
  <ul class="watch-rest">{others}</ul>
  <p class="watch-note">Importance here is measured, not asserted: we simulate every remaining game
     60,000 times, then split those seasons by who won each of today's games. The gap between the two
     halves is what the game is worth. The biggest game is rarely the one with the best teams &mdash;
     it is the one where both clubs are closest to a coin flip.</p>
</div>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--print", dest="show", action="store_true")
    a = ap.parse_args()
    rows = build(a.date)
    if not rows:
        print("  no games today; nothing written")
        if OUT.exists():
            OUT.unlink()
        return 0
    print(f"  {len(rows)} games, top swing {rows[0]['swing']*100:.1f} points")
    for r in rows[:5]:
        print(f"    {r['away']+' at '+r['home']:<32}{r['swing']*100:>6.1f}"
              f"   {r['home'][:3]} {r['dh']*100:+.1f}   {r['away'][:3]} {r['da']*100:+.1f}")
    html = render(rows, a.date)
    if a.show:
        print("\n" + html)
        return 0
    OUT.write_text(html, encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
