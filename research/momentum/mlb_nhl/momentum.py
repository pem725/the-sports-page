#!/usr/bin/env python3
"""Momentum study, MLB and NHL (spec: research/momentum/SPEC.md).

Test A  streak test: does a team on a W/L streak win its next game more often than its
        pregame strength says? Benchmark = log5 of the two clubs' season win%, EXCLUDING the
        game being predicted (and, for the focal club, excluding the streak games themselves,
        which would otherwise inflate a winning club's benchmark), calibrated by a logistic fit
        on all games (slope shrinks raw win% toward .500; intercept = home edge).
Test B  late form (MLB final 30 games, NHL final 20) vs postseason series won and postseason
        wins against a log5 expectation, controlling for full-season differential.
Test C  NHL 2026-27 now; MLB 2026 postseason vs September form.

Sources: Retrosheet game logs (MLB 1998-2025 regular + postseason), MLB Stats API (2026),
NHL stats API /stats/rest/en/game (2005-06 onward).
The information used here was obtained free of charge from and is copyrighted by
Retrosheet. Interested parties may contact Retrosheet at www.retrosheet.org.
"""
import csv, io, json, math, os, zipfile
from collections import defaultdict
import numpy as np
from scipy.stats import spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
RNG = np.random.default_rng(20261118)
RETRO = ("The information used here was obtained free of charge from and is copyrighted by "
         "Retrosheet. Interested parties may contact Retrosheet at www.retrosheet.org.")


def logit(p):
    p = min(max(p, 0.01), 0.99)
    return math.log(p / (1 - p))


def sig(x):
    return 1 / (1 + math.exp(-x))


def log5(a, b):
    a = min(max(a, 0.01), 0.99); b = min(max(b, 0.01), 0.99)
    return a * (1 - b) / (a * (1 - b) + b * (1 - a))


def fit_logit(X, y, iters=25):
    X = np.asarray(X, float); y = np.asarray(y, float)
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ w))
        H = X.T @ (X * (p * (1 - p))[:, None])
        w += np.linalg.solve(H, X.T @ (y - p))
    return w


# ---------------------------------------------------------------- data
def mlb_regular():
    """{season: [game dict in order]} from Retrosheet game logs."""
    out = {}
    for y in range(1998, 2026):
        z = zipfile.ZipFile(os.path.join(RAW, "retro", f"gl{y}.zip"))
        rows = []
        for r in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin-1")):
            v, h = int(r[9]), int(r[10])
            if v == h:  # ties (called games never completed) are not results
                continue
            rows.append(dict(date=r[0], n=int(r[1] or 0), home=r[6], away=r[3], hs=h, as_=v, hd=h, ad=v))
        rows.sort(key=lambda g: (g["date"], g["n"]))
        out[y] = rows
    return out


def mlb_post():
    """[(year, round, home, away, hs, as)] from Retrosheet postseason logs, 1998-2025."""
    out = []
    for rnd in ("wc", "dv", "lc", "ws"):
        z = zipfile.ZipFile(os.path.join(RAW, "retro", f"gl{rnd}.zip"))
        for r in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin-1")):
            y = int(r[0][:4])
            if 1998 <= y <= 2025:
                out.append(dict(year=y, rnd=rnd, date=r[0], n=int(r[1] or 0), home=r[6], away=r[3],
                                hs=int(r[10]), as_=int(r[9]), lg=(r[4], r[7])))
    out.sort(key=lambda g: (g["date"], g["n"]))
    return out


def mlb_2026():
    d = json.load(open(os.path.join(RAW, "mlb-2026-R.json")))
    seen, rows = set(), []
    for x in d["dates"]:
        for g in x["games"]:
            a, h = g["teams"]["away"], g["teams"]["home"]
            if g["status"]["abstractGameState"] != "Final" or g["gamePk"] in seen:
                continue
            if a.get("score") is None or h.get("score") is None or a["score"] == h["score"]:
                continue
            seen.add(g["gamePk"])
            rows.append(dict(date=g["gameDate"], n=g.get("gameNumber", 1), home=h["team"]["name"],
                             away=a["team"]["name"], hs=h["score"], as_=a["score"], hd=h["score"], ad=a["score"]))
    rows.sort(key=lambda g: (g["date"], g["n"]))
    p = json.load(open(os.path.join(RAW, "mlb-2026-P.json")))
    post, seen = [], set()
    for x in p["dates"]:
        for g in x["games"]:
            a, h = g["teams"]["away"], g["teams"]["home"]
            if g["status"]["abstractGameState"] != "Final" or g["gamePk"] in seen or a.get("score") is None:
                continue
            seen.add(g["gamePk"])
            post.append(dict(year=2026, rnd=g["gameType"], date=g["gameDate"], home=h["team"]["name"],
                             away=a["team"]["name"], hs=h["score"], as_=a["score"]))
    return rows, post


def nhl_load():
    g = json.load(open(os.path.join(RAW, "nhl-games-all.json")))["data"]
    teams = {t["id"]: t["triCode"] for t in json.load(open(os.path.join(RAW, "nhl-teams.json")))["data"]}
    reg, post = defaultdict(list), defaultdict(list)
    for x in g:
        if x["season"] < 20052006 or x["gameStateId"] != 7 or x["gameType"] not in (2, 3):
            continue
        hs, as_ = x["homeScore"], x["visitingScore"]
        hd, ad = hs, as_
        if x["period"] == 5 and x["gameType"] == 2:  # shootout: the extra "goal" is not a goal
            if hs > as_: hd -= 1
            else: ad -= 1
        row = dict(date=x["easternStartTime"], n=x["id"], home=teams.get(x["homeTeamId"], str(x["homeTeamId"])),
                   away=teams.get(x["visitingTeamId"], str(x["visitingTeamId"])), hs=hs, as_=as_, hd=hd, ad=ad,
                   so=x["period"] == 5, ot=x["period"] >= 4)
        (reg if x["gameType"] == 2 else post)[x["season"] // 10000].append(row)
    for d in (reg, post):
        for s in d:
            d[s].sort(key=lambda r: (r["date"], r["n"]))
    return dict(reg), dict(post)


# ---------------------------------------------------------------- per-team sequences
def team_seqs(games):
    seq = defaultdict(list)
    for i, g in enumerate(games):
        hw = g["hs"] > g["as_"]
        seq[g["home"]].append(dict(i=i, w=int(hw), home=1, opp=g["away"], d=g["hd"] - g["ad"]))
        seq[g["away"]].append(dict(i=i, w=int(not hw), home=-1, opp=g["home"], d=g["ad"] - g["hd"]))
    return seq


# ---------------------------------------------------------------- Test A
BUCKETS = [("W5+", lambda s: s >= 5, 5), ("W3+", lambda s: s >= 3, 3), ("none", lambda s: abs(s) < 3, 3),
           ("L3+", lambda s: s <= -3, 3), ("L5+", lambda s: s <= -5, 5)]


def team_game_rows(seasons):
    rows = []
    for s, games in seasons.items():
        seq = team_seqs(games)
        W = {t: sum(x["w"] for x in v) for t, v in seq.items()}
        G = {t: len(v) for t, v in seq.items()}
        for t, v in seq.items():
            streak = 0
            for k, x in enumerate(v):
                if k >= 5:
                    o = x["opp"]
                    last3 = sum(y["w"] for y in v[k - 3:k]); last5 = sum(y["w"] for y in v[k - 5:k])
                    S0 = (W[t] - x["w"]) / (G[t] - 1)
                    S3 = (W[t] - x["w"] - last3) / (G[t] - 4)
                    S5 = (W[t] - x["w"] - last5) / (G[t] - 6)
                    O = (W[o] - (1 - x["w"])) / (G[o] - 1)
                    rows.append(dict(season=s, team=t, w=x["w"], home=x["home"], streak=streak,
                                     wpct_incl=W[t] / G[t], x0=logit(log5(S0, O)), x3=logit(log5(S3, O)),
                                     x5=logit(log5(S5, O))))
                streak = (streak + 1 if streak > 0 else 1) if x["w"] else (streak - 1 if streak < 0 else -1)
    return rows


def calib(rows, key):
    X = [[r[key], r["home"]] for r in rows]
    y = [r["w"] for r in rows]
    b, a = fit_logit(X, y)
    return float(b), float(a)


def test_a(rows):
    cal = {k: calib(rows, k) for k in ("x0", "x3", "x5")}
    out = {"calibration": {k: dict(slope=round(v[0], 3), home_logodds=round(v[1], 3),
                                   home_win_per_100_even=round(100 * sig(v[1]), 1)) for k, v in cal.items()},
           "buckets": []}
    for name, f, k in BUCKETS:
        sub = [r for r in rows if f(r["streak"])]
        n = len(sub)
        if not n:
            continue
        key = f"x{k}"; b, a = cal[key]
        ex = np.array([sig(b * r[key] + a * r["home"]) for r in sub])
        b0, a0 = cal["x0"]
        ex0 = np.array([sig(b0 * r["x0"] + a0 * r["home"]) for r in sub])
        act = np.array([r["w"] for r in sub])
        se = math.sqrt(float((ex * (1 - ex)).sum())) / n
        out["buckets"].append(dict(
            bucket=name, games=n, actual_per100=round(100 * act.mean(), 1),
            expected_per100=round(100 * ex.mean(), 1), gap_per100=round(100 * (act.mean() - ex.mean()), 1),
            se_per100=round(100 * se, 1),
            expected_if_streak_games_left_in=round(100 * ex0.mean(), 1),
            season_wpct_incl_game_per100=round(100 * np.mean([r["wpct_incl"] for r in sub]), 1)))
    return out


# ---------------------------------------------------------------- Test B
def series_from_games(post_games, min_games=1):
    """Group postseason games into series keyed by (round, team pair)."""
    ser = defaultdict(lambda: dict(games=[], wins=defaultdict(int)))
    for g in post_games:
        key = (g.get("rnd"), frozenset((g["home"], g["away"])))
        w = g["home"] if g["hs"] > g["as_"] else g["away"]
        ser[key]["games"].append(g); ser[key]["wins"][w] += 1
    out = []
    for (rnd, pair), v in ser.items():
        if len(v["games"]) < min_games:
            continue
        a, b = sorted(pair)
        win = a if v["wins"][a] > v["wins"][b] else b
        out.append(dict(rnd=rnd, teams=(a, b), winner=win, n=len(v["games"])))
    return out


def late_table(seasons, K):
    """{season: {team: dict(full, early, late, wpct, late_wpct, G)}}"""
    out = {}
    for s, games in seasons.items():
        seq = team_seqs(games)
        out[s] = {}
        for t, v in seq.items():
            G = len(v); late = v[-K:]; early = v[:-K]
            out[s][t] = dict(full=sum(x["d"] for x in v) / G, early=sum(x["d"] for x in early) / max(len(early), 1),
                             late=sum(x["d"] for x in late) / len(late), wpct=sum(x["w"] for x in v) / G,
                             late_wpct=sum(x["w"] for x in late) / len(late), G=G)
    return out


def ols(y, X):
    X = np.column_stack([np.ones(len(y))] + list(X)); y = np.asarray(y, float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    r2 = 1 - (res ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return beta, r2


def test_b(late, post_by_season, cal0, label_late):
    """post_by_season: {season: [games]} ; cal0 = (slope, home) from regular season S0 fit."""
    teams = []
    b, a = cal0
    for s, games in post_by_season.items():
        if s not in late:
            continue
        L = late[s]
        sers = series_from_games(games)
        rec = defaultdict(lambda: dict(series_won=0, series=0, g=0, w=0, ex=0.0))
        for se in sers:
            for t in se["teams"]:
                rec[t]["series"] += 1
                rec[t]["series_won"] += int(se["winner"] == t)
        for g in games:
            if g["home"] not in L or g["away"] not in L:
                continue
            ph = sig(b * logit(log5(L[g["home"]]["wpct"], L[g["away"]]["wpct"])) + a)
            hw = int(g["hs"] > g["as_"])
            for t, w, p in ((g["home"], hw, ph), (g["away"], 1 - hw, 1 - ph)):
                rec[t]["g"] += 1; rec[t]["w"] += w; rec[t]["ex"] += p
        for t, r in rec.items():
            if t in L:
                teams.append(dict(season=s, team=t, **r, **L[t]))
    n = len(teams)
    full = np.array([t["full"] for t in teams]); lateg = np.array([t["late"] for t in teams])
    early = np.array([t["early"] for t in teams])
    sw = np.array([t["series_won"] for t in teams], float)
    exc = np.array([(t["w"] - t["ex"]) for t in teams]); gms = np.array([t["g"] for t in teams], float)

    def block(y, ctrl, wts=None):
        _, r2a = ols(y, [ctrl]); beta, r2b = ols(y, [ctrl, lateg])
        # partial correlation of late with y given ctrl
        ra = y - np.column_stack([np.ones(n), ctrl]) @ np.linalg.lstsq(np.column_stack([np.ones(n), ctrl]), y, rcond=None)[0]
        rl = lateg - np.column_stack([np.ones(n), ctrl]) @ np.linalg.lstsq(np.column_stack([np.ones(n), ctrl]), lateg, rcond=None)[0]
        pc = float(np.corrcoef(ra, rl)[0, 1])
        boots = []
        for _ in range(2000):
            ix = RNG.integers(0, n, n)
            bb, _ = ols(y[ix], [ctrl[ix], lateg[ix]]); boots.append(bb[2])
        lo, hi = np.percentile(boots, [2.5, 97.5])
        return dict(r_late_raw=round(float(np.corrcoef(lateg, y)[0, 1]), 3), r2_ctrl=round(float(r2a), 3),
                    r2_ctrl_plus_late=round(float(r2b), 3), delta_r2=round(float(r2b - r2a), 4),
                    partial_r=round(pc, 3), late_coef=round(float(beta[2]), 3),
                    late_coef_95ci=[round(float(lo), 3), round(float(hi), 3)])

    # matched comparison: late form residualized on full-season differential, terciles
    rl = lateg - np.column_stack([np.ones(n), full]) @ np.linalg.lstsq(np.column_stack([np.ones(n), full]), lateg, rcond=None)[0]
    q1, q2 = np.percentile(rl, [100 / 3, 200 / 3])
    groups = {}
    for name, m in (("cold (bottom third, late form vs own season)", rl <= q1),
                    ("middle", (rl > q1) & (rl < q2)), ("hot (top third)", rl >= q2)):
        groups[name] = dict(teams=int(m.sum()), mean_full_diff_per_game=round(float(full[m].mean()), 2),
                            mean_late_diff_per_game=round(float(lateg[m].mean()), 2),
                            series_won_per_team=round(float(sw[m].mean()), 2),
                            postseason_games=int(gms[m].sum()),
                            wins_per100_actual=round(100 * sum(t["w"] for t, k in zip(teams, m) if k) / gms[m].sum(), 1),
                            wins_per100_expected=round(100 * sum(t["ex"] for t, k in zip(teams, m) if k) / gms[m].sum(), 1))
    # bootstrap of hot-minus-cold excess wins per 100 games
    hot, cold = rl >= q2, rl <= q1
    def d(ix):
        h = ix[hot[ix]]; c = ix[cold[ix]]
        return 100 * (exc[h].sum() / gms[h].sum() - exc[c].sum() / gms[c].sum())
    bs = [d(RNG.integers(0, n, n)) for _ in range(2000)]
    idx = np.arange(n)
    return dict(team_seasons=n, late_window=label_late, postseason_games=int(gms.sum()) // 2,
                series_won=dict(control_full_season=block(sw, full), control_rest_of_season=block(sw, early)),
                excess_wins=dict(control_full_season=block(exc / np.maximum(gms, 1), full)),
                matched=groups,
                hot_minus_cold_excess_wins_per100=round(float(d(idx)), 1),
                hot_minus_cold_95ci=[round(float(x), 1) for x in np.percentile(bs, [2.5, 97.5])],
                teams=teams)


# ---------------------------------------------------------------- main
def main():
    res = {"notice": RETRO, "built": "2026-11-18"}

    # ---------- MLB
    reg = mlb_regular()
    rowsA = team_game_rows(reg)
    A = test_a(rowsA)
    A["seasons"] = "1998-2025 regular season"; A["team_games"] = len(rowsA)
    res["mlb_test_a"] = A
    cal0 = (A["calibration"]["x0"]["slope"], A["calibration"]["x0"]["home_logodds"])
    late = late_table(reg, 30)
    post = mlb_post()
    pb = defaultdict(list)
    for g in post:
        pb[g["year"]].append(g)
    B = test_b(late, dict(pb), cal0, "final 30 regular-season games, run differential per game")
    B["seasons"] = "1998-2025"
    teamsB = B.pop("teams")
    res["mlb_test_b"] = B

    # MLB 2026
    r26, p26 = mlb_2026()
    l26 = late_table({2026: r26}, 30)[2026]
    sers = series_from_games(p26)
    rec = defaultdict(lambda: [0, 0, None])
    order = {"F": 1, "D": 2, "L": 3, "W": 4}
    names = {"F": "lost Wild Card Series", "D": "lost Division Series", "L": "lost LCS", "W": "lost World Series"}
    for se in sers:
        for t in se["teams"]:
            rec[t][0] += 1; rec[t][1] += int(se["winner"] == t)
            last = rec[t][2]
            if last is None or order[se["rnd"]] > order[last[0]]:
                rec[t][2] = (se["rnd"], se["winner"] == t)
    rows26 = []
    for t, (ns, nw, last) in rec.items():
        fate = "won World Series" if last == ("W", True) else names[last[0]]
        x = l26[t]
        rows26.append(dict(team=t, late30_run_diff_per_game=round(x["late"], 2), late30_wpct=round(x["late_wpct"], 3),
                           season_run_diff_per_game=round(x["full"], 2), season_wpct=round(x["wpct"], 3),
                           series_won=nw, fate=fate))
    rows26.sort(key=lambda r: -r["late30_run_diff_per_game"])
    hot_rank = {r["team"]: i for i, r in enumerate(rows26)}
    res["mlb_2026_postseason"] = dict(source="MLB Stats API schedule, 2026 regular season and postseason",
                                      regular_games=len(r26), postseason_games=len(p26),
                                      teams=rows26,
                                      spearman_late_vs_series_won=round(float(spearmanr([r["late30_run_diff_per_game"] for r in rows26], [r["series_won"] for r in rows26])[0]), 2),
                                      spearman_season_vs_series_won=round(float(spearmanr([r["season_run_diff_per_game"] for r in rows26], [r["series_won"] for r in rows26])[0]), 2))

    # ---------- NHL
    nreg, npost = nhl_load()
    cur = nreg.pop(2026, [])
    rowsN = team_game_rows(nreg)
    AN = test_a(rowsN)
    AN["seasons"] = "2005-06 to 2025-26 regular season; OT and shootout results count as wins/losses"
    AN["team_games"] = len(rowsN)
    res["nhl_test_a"] = AN
    calN = (AN["calibration"]["x0"]["slope"], AN["calibration"]["x0"]["home_logodds"])
    lateN = late_table({s: g for s, g in nreg.items() if s != 2019}, 20)
    BN = test_b(lateN, {s: g for s, g in npost.items() if s != 2019}, calN,
                "final 20 regular-season games, goal differential per game (shootout goal removed)")
    BN["seasons"] = "2005-06 to 2025-26, excluding 2019-20 (four-month pause, bubble playoffs)"
    BN.pop("teams")
    res["nhl_test_b"] = BN

    # NHL now
    seq = team_seqs(cur)
    now = []
    for t, v in seq.items():
        s = 0
        for x in v:
            s = (s + 1 if s > 0 else 1) if x["w"] else (s - 1 if s < 0 else -1)
        l10 = v[-10:]
        now.append(dict(team=t, gp=len(v), w=sum(x["w"] for x in v), streak=s,
                        last10_w=sum(x["w"] for x in l10), last10_goal_diff_per_game=round(sum(x["d"] for x in l10) / len(l10), 2),
                        season_goal_diff_per_game=round(sum(x["d"] for x in v) / len(v), 2)))
    now.sort(key=lambda r: -(r["last10_goal_diff_per_game"] - r["season_goal_diff_per_game"]))
    res["nhl_now"] = dict(source="NHL stats API /stats/rest/en/game, games final as of fetch 2026-11-18",
                          games=len(cur), last_game=max(g["date"] for g in cur)[:10], teams=now,
                          note="streak counts OT/shootout wins as wins, OT/shootout losses as losses")

    json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=1)
    return res


if __name__ == "__main__":
    r = main()
    for k in ("mlb_test_a", "nhl_test_a"):
        print(k, r[k]["team_games"], json.dumps(r[k]["calibration"]))
        for b in r[k]["buckets"]:
            print("  ", b)
    for k in ("mlb_test_b", "nhl_test_b"):
        x = r[k]
        print(k, x["team_seasons"], x["postseason_games"])
        print("  series", json.dumps(x["series_won"]))
        print("  excess", json.dumps(x["excess_wins"]))
        for g, v in x["matched"].items():
            print("  ", g, v)
        print("  hot-cold", x["hot_minus_cold_excess_wins_per100"], x["hot_minus_cold_95ci"])
    print(json.dumps(r["mlb_2026_postseason"], indent=0)[:3000])
    n = r["nhl_now"]; print(n["games"], n["last_game"])
    for t in sorted(n["teams"], key=lambda t: -t["streak"]):
        print(t)
