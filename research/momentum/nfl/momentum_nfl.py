#!/usr/bin/env python3
"""Momentum study, NFL. Follows research/momentum/SPEC.md (Tests A, B, C).

Data: nflverse games.csv refreshed 2026-11-18 into ./data/games.csv (cache was 2026-11-04).
Pregame expectation: vig-free moneyline where both prices exist, else spread_line through a
normal curve (sd 13.5). nflverse spread_line is positive when the HOME team is favored.
"""
import csv, json, math, random, statistics as st
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAMES = HERE / "data" / "games.csv"
random.seed(20261118)
POST = {"WC", "DIV", "CON", "SB"}


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def ml_prob(ml):
    ml = float(ml)
    return 100 / (ml + 100) if ml > 0 else -ml / (-ml + 100)


def load():
    rows = []
    src = defaultdict(int)
    for r in csv.DictReader(open(GAMES)):
        if r["home_score"] == "" or r["away_score"] == "":
            continue
        s = int(r["season"])
        if s < 1999:
            continue
        p = None
        if r["home_moneyline"] not in ("", "NA") and r["away_moneyline"] not in ("", "NA"):
            ph, pa = ml_prob(r["home_moneyline"]), ml_prob(r["away_moneyline"])
            p = ph / (ph + pa); how = "moneyline"
        elif r["spread_line"] not in ("", "NA"):
            p = phi(float(r["spread_line"]) / 13.5); how = "spread"
        else:
            how = "none"
        src[(s <= 2025, how)] += 1
        hs, as_ = int(r["home_score"]), int(r["away_score"])
        rows.append(dict(season=s, gt=r["game_type"], week=int(r["week"]), date=r["gameday"],
                         home=r["home_team"], away=r["away_team"], hs=hs, as_=as_, p=p, how=how))
    rows.sort(key=lambda g: (g["date"], g["home"]))
    return rows, src


def team_games(rows):
    """Per team per season, chronological list of team-game records."""
    tg = defaultdict(list)
    for g in rows:
        for side in ("home", "away"):
            me = g[side]; opp = g["away" if side == "home" else "home"]
            pf = g["hs"] if side == "home" else g["as_"]
            pa = g["as_"] if side == "home" else g["hs"]
            res = 1.0 if pf > pa else 0.0 if pf < pa else 0.5
            p = None if g["p"] is None else (g["p"] if side == "home" else 1 - g["p"])
            tg[(g["season"], me)].append(dict(date=g["date"], gt=g["gt"], week=g["week"], opp=opp,
                                               pf=pf, pa=pa, res=res, p=p, diff=pf - pa, how=g["how"]))
    return tg


def ols(X, y):
    """Plain least squares, returns coefficients and R^2. X includes intercept column."""
    k = len(X[0])
    XtX = [[sum(r[i] * r[j] for r in X) for j in range(k)] for i in range(k)]
    Xty = [sum(r[i] * yy for r, yy in zip(X, y)) for i in range(k)]
    # gaussian elimination
    A = [row[:] + [b] for row, b in zip(XtX, Xty)]
    for i in range(k):
        piv = max(range(i, k), key=lambda r: abs(A[r][i])); A[i], A[piv] = A[piv], A[i]
        for r in range(k):
            if r != i:
                f = A[r][i] / A[i][i]
                A[r] = [a - f * b for a, b in zip(A[r], A[i])]
    beta = [A[i][k] / A[i][i] for i in range(k)]
    yh = [sum(b * x for b, x in zip(beta, r)) for r in X]
    my = st.mean(y)
    sst = sum((v - my) ** 2 for v in y); sse = sum((v - h) ** 2 for v, h in zip(y, yh))
    return beta, 1 - sse / sst


def corr(a, b):
    return st.correlation(a, b)


def partial_r(y, x, z):
    rxy, rxz, ryz = corr(x, y), corr(x, z), corr(y, z)
    return (rxy - rxz * ryz) / math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))


def boot(units, fn, reps=2000):
    vals = []
    n = len(units)
    for _ in range(reps):
        smp = [units[random.randrange(n)] for _ in range(n)]
        try:
            vals.append(fn(smp))
        except Exception:
            pass
    vals.sort()
    return dict(se=st.pstdev(vals), lo=vals[int(.025 * len(vals))], hi=vals[int(.975 * len(vals)) - 1])


# ---------------------------------------------------------------- Test A
def test_a(tg, seasons, how=None):
    buckets = {k: [] for k in ("W5+", "W3+", "none", "L3+", "L5+")}
    naive = {k: [] for k in buckets}
    for (s, t), gl in tg.items():
        if s not in seasons:
            continue
        streak = 0
        for g in gl:
            if g["gt"] != "REG":
                continue
            if g["p"] is not None and (how is None or g["how"] == how):
                keys = []
                if streak >= 3: keys.append("W3+")
                if streak >= 5: keys.append("W5+")
                if streak <= -3: keys.append("L3+")
                if streak <= -5: keys.append("L5+")
                if -2 <= streak <= 2: keys.append("none")
                for k in keys:
                    buckets[k].append((g["res"], g["p"]))
            # update streak (a tie ends any streak)
            if g["res"] == 1: streak = streak + 1 if streak > 0 else 1
            elif g["res"] == 0: streak = streak - 1 if streak < 0 else -1
            else: streak = 0
    out = {}
    for k, v in buckets.items():
        n = len(v)
        act = sum(r for r, _ in v) / n; exp = sum(p for _, p in v) / n
        se = math.sqrt(sum(p * (1 - p) for _, p in v)) / n
        out[k] = dict(games=n, actual_per100=round(100 * act, 1), expected_per100=round(100 * exp, 1),
                      gap_per100=round(100 * (act - exp), 1), se_per100=round(100 * se, 1),
                      z=round((act - exp) / se, 2))
    return out


# ---------------------------------------------------------------- Test B
def season_units(tg, seasons, late_n=5):
    units = []
    for (s, t), gl in tg.items():
        if s not in seasons:
            continue
        reg = [g for g in gl if g["gt"] == "REG"]
        post = [g for g in gl if g["gt"] in POST]
        if not post:
            continue
        late, early = reg[-late_n:], reg[:-late_n]
        u = dict(season=s, team=t,
                 season_diff=st.mean(g["diff"] for g in reg),
                 early_diff=st.mean(g["diff"] for g in early),
                 late_diff=st.mean(g["diff"] for g in late),
                 late_wpct=st.mean(g["res"] for g in late),
                 season_wpct=st.mean(g["res"] for g in reg),
                 post_games=len(post), post_wins=sum(g["res"] for g in post),
                 post_exp=sum(g["p"] for g in post if g["p"] is not None),
                 champion=any(g["gt"] == "SB" and g["res"] == 1 for g in post),
                 last5_record=f"{sum(g['res']==1 for g in late)}-{sum(g['res']==0 for g in late)}")
        u["post_woe"] = u["post_wins"] - u["post_exp"]
        units.append(u)
    return units


def test_b(units):
    def stats(us, late_key, base_key, outcome):
        y = [u[outcome] for u in us]; x = [u[late_key] for u in us]; z = [u[base_key] for u in us]
        _, r2_base = ols([[1, a] for a in z], y)
        beta, r2_full = ols([[1, a, b] for a, b in zip(z, x)], y)
        return dict(r_late=corr(x, y), r_base=corr(z, y), partial_r=partial_r(y, x, z),
                    delta_r2=r2_full - r2_base, beta_late=beta[2], beta_base=beta[1])

    res = {}
    for late_key in ("late_diff", "late_wpct"):
        for base_key in ("season_diff", "early_diff"):
            for outcome in ("post_wins", "post_woe"):
                key = f"{late_key}|{base_key}|{outcome}"
                pt = stats(units, late_key, base_key, outcome)
                b = boot(units, lambda us: stats(us, late_key, base_key, outcome)["partial_r"])
                bd = boot(units, lambda us: stats(us, late_key, base_key, outcome)["beta_late"])
                res[key] = {k: round(v, 3) for k, v in pt.items()}
                res[key]["partial_r_boot"] = {k: round(v, 3) for k, v in b.items()}
                res[key]["beta_late_boot"] = {k: round(v, 3) for k, v in bd.items()}
    # matched comparison: late form beyond season strength (residual of late on early), top vs bottom quarter
    x = [u["late_diff"] for u in units]; z = [u["early_diff"] for u in units]
    beta, _ = ols([[1, a] for a in z], x)
    for u in units:
        u["late_resid"] = u["late_diff"] - (beta[0] + beta[1] * u["early_diff"])
    srt = sorted(units, key=lambda u: u["late_resid"])
    q = len(srt) // 4
    def grp(g):
        ng = sum(u["post_games"] for u in g)
        return dict(team_seasons=len(g), post_games=ng,
                    wins_per100=round(100 * sum(u["post_wins"] for u in g) / ng, 1),
                    market_expected_per100=round(100 * sum(u["post_exp"] for u in g) / ng, 1),
                    mean_early_diff=round(st.mean(u["early_diff"] for u in g), 1),
                    mean_late_diff=round(st.mean(u["late_diff"] for u in g), 1),
                    mean_post_wins=round(st.mean(u["post_wins"] for u in g), 2))
    hot, cold = srt[-q:], srt[:q]
    dif = boot([(1, u) for u in hot] + [(0, u) for u in cold],
               lambda us: (sum(u["post_wins"] for h, u in us if h) / sum(u["post_games"] for h, u in us if h)
                           - sum(u["post_wins"] for h, u in us if not h) / sum(u["post_games"] for h, u in us if not h)))
    dwoe = boot([(1, u) for u in hot] + [(0, u) for u in cold],
               lambda us: (sum(u["post_woe"] for h, u in us if h) / sum(u["post_games"] for h, u in us if h)
                           - sum(u["post_woe"] for h, u in us if not h) / sum(u["post_games"] for h, u in us if not h)))
    hw = sum(u["post_woe"] for u in hot) / sum(u["post_games"] for u in hot)
    cw = sum(u["post_woe"] for u in cold) / sum(u["post_games"] for u in cold)
    res["matched_quarters_over_market"] = dict(hot_minus_cold_per100=round(100 * (hw - cw), 1),
                                               se_per100=round(100 * dwoe["se"], 1))
    res["matched_quarters"] = dict(note="late form residualized on season-minus-last-5 diff/game; top vs bottom quarter of playoff teams",
                                   hot=grp(hot), cold=grp(cold),
                                   hot_minus_cold_winrate_per100_se=round(100 * dif["se"], 1))
    return res


def super_bowl(units):
    by = defaultdict(list)
    for u in units:
        by[u["season"]].append(u)
    # conditional logit on season strength: P(champ_i) = exp(b*s_i)/sum exp(b*s_j), fit b by grid MLE
    def ll(b):
        tot = 0
        for s, us in by.items():
            den = sum(math.exp(b * u["season_diff"]) for u in us)
            ch = [u for u in us if u["champion"]][0]
            tot += b * ch["season_diff"] - math.log(den)
        return tot
    b = max((i / 1000 for i in range(0, 400)), key=ll)
    obs = 0; exp_strength = 0; exp_naive = 0; var = 0; detail = []
    for s, us in sorted(by.items()):
        n = len(us); k = math.ceil(n / 4)
        top = sorted(us, key=lambda u: -u["late_diff"])[:k]
        topset = {u["team"] for u in top}
        den = sum(math.exp(b * u["season_diff"]) for u in us)
        pe = sum(math.exp(b * u["season_diff"]) / den for u in us if u["team"] in topset)
        ch = [u for u in us if u["champion"]][0]
        hit = ch["team"] in topset
        obs += hit; exp_strength += pe; exp_naive += k / n; var += pe * (1 - pe)
        rank = sorted(us, key=lambda u: -u["late_diff"]).index(ch) + 1
        detail.append(dict(season=s, champion=ch["team"], late_diff=round(ch["late_diff"], 1),
                           late_rank=rank, playoff_teams=n, top_quarter=hit, last5=ch["last5_record"]))
    return dict(champions=len(by), observed_top_quarter=obs,
                expected_from_season_strength=round(exp_strength, 1), sd=round(math.sqrt(var), 1),
                expected_if_random=round(exp_naive, 1), strength_coef=b, detail=detail)


# ---------------------------------------------------------------- forward: November -> December
def nov_dec(tg, seasons):
    units = []
    for (s, t), gl in tg.items():
        if s not in seasons:
            continue
        reg = [g for g in gl if g["gt"] == "REG"]
        nov = [g for g in reg if g["date"][5:7] == "11"]
        dec = [g for g in reg if g["date"][5:7] == "12"]
        pre = [g for g in reg if g["date"] < f"{s}-12-01"]
        if len(nov) < 2 or len(dec) < 2:
            continue
        units.append(dict(season=s, team=t, pre_diff=st.mean(g["diff"] for g in pre),
                          nov_diff=st.mean(g["diff"] for g in nov), nov_wpct=st.mean(g["res"] for g in nov),
                          dec_diff=st.mean(g["diff"] for g in dec), dec_wpct=st.mean(g["res"] for g in dec),
                          dec_woe=sum(g["res"] - g["p"] for g in dec if g["p"] is not None),
                          dec_games=len(dec), nov_games=len(nov)))
    res = dict(team_seasons=len(units), nov_games_mean=round(st.mean(u["nov_games"] for u in units), 1),
               dec_games_mean=round(st.mean(u["dec_games"] for u in units), 1))
    for late in ("nov_diff", "nov_wpct"):
        for out in ("dec_diff", "dec_wpct", "dec_woe"):
            y = [u[out] for u in units]; x = [u[late] for u in units]; z = [u["pre_diff"] for u in units]
            _, r2b = ols([[1, a] for a in z], y)
            beta, r2f = ols([[1, a, b] for a, b in zip(z, x)], y)
            pb = boot(units, lambda us: partial_r([u[out] for u in us], [u[late] for u in us], [u["pre_diff"] for u in us]))
            res[f"{late}->{out}"] = dict(r_late=round(corr(x, y), 3), r_pre=round(corr(z, y), 3),
                                         partial_r=round(partial_r(y, x, z), 3), partial_r_se=round(pb["se"], 3),
                                         partial_r_ci=[round(pb["lo"], 3), round(pb["hi"], 3)],
                                         delta_r2=round(r2f - r2b, 4), beta_late=round(beta[2], 3),
                                         beta_pre=round(beta[1], 3))
    # what fraction of November form "carries" into December, in points per game
    return res


# ---------------------------------------------------------------- Test C
def test_c(tg):
    out = []
    for (s, t), gl in tg.items():
        if s != 2026:
            continue
        reg = [g for g in gl if g["gt"] == "REG"]
        streak = 0
        for g in reg:
            if g["res"] == 1: streak = streak + 1 if streak > 0 else 1
            elif g["res"] == 0: streak = streak - 1 if streak < 0 else -1
            else: streak = 0
        last5 = reg[-5:]; nov = [g for g in reg if g["date"][5:7] == "11"]
        w = sum(g["res"] == 1 for g in reg); l = sum(g["res"] == 0 for g in reg); tie = sum(g["res"] == .5 for g in reg)
        out.append(dict(team=t, record=f"{w}-{l}" + (f"-{tie}" if tie else ""), games=len(reg),
                        streak=("W" if streak > 0 else "L" if streak < 0 else "-") + str(abs(streak)),
                        streak_n=streak,
                        season_diff=round(st.mean(g["diff"] for g in reg), 1),
                        early_diff=round(st.mean(g["diff"] for g in reg[:-5]), 1) if len(reg) > 5 else None,
                        last5_diff=round(st.mean(g["diff"] for g in last5), 1),
                        last5_record=f"{sum(g['res']==1 for g in last5)}-{sum(g['res']==0 for g in last5)}",
                        nov_games=len(nov), nov_diff=round(st.mean(g["diff"] for g in nov), 1) if nov else None,
                        nov_record=f"{sum(g['res']==1 for g in nov)}-{sum(g['res']==0 for g in nov)}",
                        last5_wins_over_market=round(sum(g["res"] - g["p"] for g in last5 if g["p"] is not None), 2)))
    for u in out:
        u["late_minus_early"] = round(u["last5_diff"] - u["early_diff"], 1) if u["early_diff"] is not None else None
    out.sort(key=lambda u: -u["last5_diff"])
    return out


def main():
    rows, src = load()
    tg = team_games(rows)
    hist = set(range(1999, 2026))
    a = test_a(tg, hist)
    a_ml = test_a(tg, hist, "moneyline"); a_sp = test_a(tg, hist, "spread")
    units = season_units(tg, hist)
    b = test_b(units)
    sb = super_bowl(units)
    nd = nov_dec(tg, hist)
    c = test_c(tg)
    srcs = {("1999-2025" if k[0] else "2026") + ":" + k[1]: v for k, v in src.items()}
    res = dict(generated="2026-11-18", data="nflverse games.csv refreshed 2026-11-18; 2026 through MNF 2026-11-16",
               expectation_sources=srcs, test_a=a, test_a_moneyline_only=a_ml, test_a_spread_only=a_sp,
               test_b=dict(team_seasons=len(units), postseason_games=sum(u["post_games"] for u in units) // 2,
                           results=b, super_bowl=sb),
               test_b_forward_nov_dec=nd, test_c_2026=c)
    json.dump(res, open(HERE / "results.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "test_c_2026"}, indent=1)[:12000])
    for u in c:
        print(u["team"], u["record"], u["streak"], "L5", u["last5_record"], u["last5_diff"], "early", u["early_diff"],
              "nov", u["nov_record"], u["nov_diff"], "season", u["season_diff"], "L5woe", u["last5_wins_over_market"])


if __name__ == "__main__":
    main()
