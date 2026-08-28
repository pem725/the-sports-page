#!/usr/bin/env python3
"""Recompute today's playoff odds and rebuild the Odds Board.

    python3 scripts/refresh_odds.py            # normal daily run
    python3 scripts/refresh_odds.py --dry-run  # compute and report, write nothing

Run from the autopublish workflow rather than its own schedule, because a second
scheduled workflow would inherit the same GitHub cron delays that already push
the daily issue hours late. Piggybacking means the board refreshes whenever the
issue does.

CADENCE. The stored trajectory is a WEEKLY grid anchored to the first snapshot.
That matters: the page's smoother uses a bandwidth counted in points, so mixing
weekly points early with daily points late would silently change how much time
the smoother averages over. So this script recomputes today's odds every day but
only APPENDS a new point once seven days have passed; otherwise it overwrites
the most recent point in place. Headline numbers are always current; the curve
stays evenly spaced.

Fails loudly. If the API is unreachable or the reconciliation check fails, it
exits non-zero without touching the data, and the previous board stays up.
"""
import argparse
import datetime
import json
import math
import pathlib
import subprocess
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "playoff-odds-trajectory.json"
API = "https://statsapi.mlb.com/api/v1"
NSIMS, BATCH = 20000, 5000


def get(path, timeout=90):
    return json.load(urllib.request.urlopen(API + path, timeout=timeout))


def season_state(date):
    """Standings and remaining schedule as of `date`, reconciled to 162 games."""
    d = get(f"/standings?leagueId=103,104&season={date[:4]}"
            f"&standingsTypes=regularSeason&date={date}")
    T = {}
    for rec in d["records"]:
        for t in rec["teamRecords"]:
            T[str(t["team"]["id"])] = dict(
                name=t["team"]["name"], w=t["wins"], l=t["losses"],
                div=rec["division"]["id"], lg=rec["league"]["id"],
                rs=int(t["runsScored"]), ra=int(t["runsAllowed"]),
                gb=0.0)
    s = get(f"/schedule?sportId=1&startDate={date}&endDate={date[:4]}-11-15")
    games = []
    for day in s.get("dates", []):
        for g in day["games"]:
            if g["gameType"] != "R":
                continue
            if g["status"]["detailedState"] in ("Postponed", "Cancelled"):
                continue
            if g["status"]["abstractGameState"] == "Final":
                continue
            games.append((str(g["teams"]["away"]["team"]["id"]),
                          str(g["teams"]["home"]["team"]["id"])))
    left = {t: 0 for t in T}
    for a, h in games:
        if a in left: left[a] += 1
        if h in left: left[h] += 1
    bad = [T[t]["name"] for t in T if T[t]["w"] + T[t]["l"] + left[t] != 162]
    if bad:
        raise SystemExit(f"REFUSING: these clubs do not reconcile to 162 games: {bad}")
    # games ahead(+) / behind(-) within the division
    for dv in {v["div"] for v in T.values()}:
        grp = sorted((k for k in T if T[k]["div"] == dv),
                     key=lambda k: -(T[k]["w"] - T[k]["l"]))
        top, second = T[grp[0]], T[grp[1]]
        for k in grp:
            ref = second if k == grp[0] else top
            T[k]["gb"] = round(((T[k]["w"] - ref["w"]) + (ref["l"] - T[k]["l"])) / 2, 1)
    return T, games


def simulate(T, games, seed=0):
    import numpy as np
    ids = sorted(T)
    idx = {t: i for i, t in enumerate(ids)}
    n = len(ids)
    W0 = np.array([T[t]["w"] for t in ids], float)
    GP = np.array([T[t]["w"] + T[t]["l"] for t in ids], float)
    PY = np.array([T[t]["rs"] ** 1.83 / (T[t]["rs"] ** 1.83 + T[t]["ra"] ** 1.83) for t in ids])
    ACT = np.array([T[t]["w"] / (T[t]["w"] + T[t]["l"]) for t in ids])
    DIV = np.array([T[t]["div"] for t in ids])
    LG = np.array([T[t]["lg"] for t in ids])
    blend = 0.5 * ACT + 0.5 * PY
    tal = (blend * GP + 0.5 * 69) / (GP + 69)
    tal *= 0.5 / tal.mean()
    ga = np.array([idx[a] for a, h in games])
    gh = np.array([idx[h] for a, h in games])
    pa, ph = tal[ga], tal[gh]
    l5 = (ph - ph * pa) / (ph + pa - 2 * ph * pa)
    P = 1 / (1 + np.exp(-(np.log(l5 / (1 - l5)) + math.log(.535 / .465))))
    rng = np.random.default_rng(seed)
    div = np.zeros(n); po = np.zeros(n)
    for _ in range(NSIMS // BATCH):
        hw = rng.random((BATCH, len(games))) < P
        add = np.zeros((BATCH, n))
        np.add.at(add.T, gh, hw.T.astype(float))
        np.add.at(add.T, ga, (~hw).T.astype(float))
        key = W0 + add + rng.random((BATCH, n)) * 1e-6
        inpo = np.zeros((BATCH, n), bool)
        for lg in (103, 104):
            lgm = LG == lg
            for dv in np.unique(DIV[lgm]):
                col = np.where(DIV == dv)[0]
                win = col[key[:, col].argmax(1)]
                inpo[np.arange(BATCH), win] = True
                np.add.at(div, win, 1)
            cand = np.where(lgm)[0]
            k2 = key[:, cand].copy(); k2[inpo[:, cand]] = -1
            top = np.argsort(-k2, 1)[:, :3]
            for j in range(3):
                inpo[np.arange(BATCH), cand[top[:, j]]] = True
        po += inpo.sum(0)
    return ({t: float(po[idx[t]]) / NSIMS for t in ids},
            {t: float(div[idx[t]]) / NSIMS for t in ids})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    a = ap.parse_args()

    D = json.loads(DATA.read_text())
    last = D["dates"][-1]
    gap = (datetime.date.fromisoformat(a.date) - datetime.date.fromisoformat(last)).days
    if gap < 0:
        print(f"  {a.date} is before the last snapshot {last}; nothing to do")
        return 0

    T, games = season_state(a.date)
    missing = [t for t in D["teams"] if t not in T]
    if missing:
        raise SystemExit(f"REFUSING: clubs in the file are missing from the API: {missing}")
    po, div = simulate(T, games)

    append = gap >= 7
    if append:
        D["dates"].append(a.date)
    else:
        D["dates"][-1] = a.date
    for tid, t in D["teams"].items():
        row = [T[tid]["w"], T[tid]["l"], T[tid]["gb"]]
        if append:
            t["po"].append(round(po[tid], 4))
            t["dv"].append(round(div[tid], 4))
            t["rec"].append(row)
        else:
            t["po"][-1] = round(po[tid], 4)
            t["dv"][-1] = round(div[tid], 4)
            t["rec"][-1] = row
        t["w"], t["l"] = T[tid]["w"], T[tid]["l"]
    D["generated"] = a.date

    n = len(D["dates"])
    assert all(len(t["po"]) == n and len(t["dv"]) == n and len(t["rec"]) == n
               for t in D["teams"].values()), "series lengths diverged"

    print(f"  {a.date}: {'appended a new weekly point' if append else 'updated the current point'}"
          f" ({n} points, {len(games)} games left)")
    for tid in sorted(D["teams"], key=lambda k: -po[k])[:3]:
        print(f"    {D['teams'][tid]['name']:<12}{po[tid]:>7.1%} playoffs  {div[tid]:>6.1%} division")
    if a.dry_run:
        print("  --dry-run: nothing written")
        return 0
    DATA.write_text(json.dumps(D, separators=(",", ":")))
    subprocess.run([sys.executable, str(REPO / "scripts" / "build_odds_page.py")], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
