"""Momentum study, FBS college football. Tests A, B, C per research/momentum/SPEC.md.

Inputs (cached, no refetch):
  ../../cfp-committee/judges/raw/games-YYYY.json.gz  regular season 2014-2026 (CFBD /games)
  ../../cfp-committee/judges/raw/post-YYYY.json.gz   postseason 2014-2025
  raw/lines-YYYY.json.gz                             CFBD /lines seasonType=both (0_fetch_lines.py)
  raw/espn-rankings-2026-11-18.json                  ESPN rankings feed (CFP committee, 2026-11-17)
Outputs: results.json
"""
import gzip, json, math, datetime as dt
from collections import defaultdict
import numpy as np
from scipy.optimize import minimize_scalar, minimize
from scipy.stats import norm

RAW = "../../cfp-committee/judges/raw"
YEARS = range(2014, 2027)
CUTOFF_2026 = "2026-11-15T23:59"   # week 11 (Sat Nov 14) incl. Oklahoma-Ole Miss stamped 11-15 18:00Z
rng = np.random.default_rng(20261118)

def et(s):  # US Eastern approx (UTC-5); enough to assign calendar month
    return (dt.datetime.fromisoformat(s.replace("Z", "+00:00")) - dt.timedelta(hours=5)).replace(tzinfo=None)

# ---------------- load ----------------
games = []
for y in YEARS:
    for kind in ("games", "post"):
        if kind == "post" and y == 2026: continue
        for g in json.load(gzip.open(f"{RAW}/{kind}-{y}.json.gz")):
            if not g["completed"] or g["homePoints"] is None: continue
            if y == 2026 and (g["startDate"] > CUTOFF_2026 or g["week"] > 11): continue
            g["post"] = (kind == "post")
            games.append(g)

def consensus_spread(lines):
    sp = [l["spread"] for l in lines if l.get("spread") is not None and l["provider"] == "consensus"]
    if sp: return sp[0]
    sp = [l["spread"] for l in lines if l.get("spread") is not None]
    return float(np.median(sp)) if sp else None

spread = {}
for y in YEARS:
    for g in json.load(gzip.open(f"raw/lines-{y}.json.gz")):
        s = consensus_spread(g["lines"])
        if s is not None: spread[g["id"]] = s
for g in games: g["spread"] = spread.get(g["id"])   # home spread, negative = home favored

fbsfbs = lambda g: g["homeClassification"] == "fbs" and g["awayClassification"] == "fbs"

# ---------------- calibrate benchmarks (2014-2025 regular, FBS v FBS) ----------------
cal = [g for g in games if fbsfbs(g) and not g["post"] and g["season"] < 2026
       and g["homePregameElo"] is not None and g["awayPregameElo"] is not None]
hw = np.array([g["homePoints"] > g["awayPoints"] for g in cal], float)
dE = np.array([g["homePregameElo"] - g["awayPregameElo"] for g in cal], float)
nn = np.array([0.0 if g["neutralSite"] else 1.0 for g in cal])
def nll_elo(h, k=1.0):
    p = 1 / (1 + 10 ** (-k * (dE + h * nn) / 400)); p = np.clip(p, 1e-9, 1 - 1e-9)
    return -np.sum(hw * np.log(p) + (1 - hw) * np.log(1 - p))
HFA = minimize_scalar(nll_elo, bounds=(0, 200), method="bounded").x
fit2 = minimize(lambda v: nll_elo(v[0], v[1]), [HFA, 1.0])
HFA2, KSCALE = fit2.x

cs = [g for g in cal if g["spread"] is not None]
sp_arr = np.array([g["spread"] for g in cs]); hw2 = np.array([g["homePoints"] > g["awayPoints"] for g in cs], float)
def nll_sd(sd):
    p = np.clip(norm.cdf(-sp_arr / sd), 1e-9, 1 - 1e-9)
    return -np.sum(hw2 * np.log(p) + (1 - hw2) * np.log(1 - p))
SD = minimize_scalar(nll_sd, bounds=(5, 30), method="bounded").x

def p_elo(g, side, k=1.0, h=None):
    if g["homePregameElo"] is None or g["awayPregameElo"] is None: return None
    h = HFA if h is None else h
    d = g["homePregameElo"] - g["awayPregameElo"] + (0 if g["neutralSite"] else h)
    ph = 1 / (1 + 10 ** (-k * d / 400))
    return ph if side == "home" else 1 - ph
def p_mkt(g, side):
    if g["spread"] is None: return None
    ph = norm.cdf(-g["spread"] / SD)
    return ph if side == "home" else 1 - ph
def exp_margin(g, side):
    if g["spread"] is None: return None
    return -g["spread"] if side == "home" else g["spread"]

# calibration table for Elo (standard curve) by decile
def calib(ps, ws, nb=10):
    o = np.argsort(ps); out = []
    for ch in np.array_split(o, nb):
        out.append({"n": int(len(ch)), "expected_per100": round(100 * ps[ch].mean(), 1), "actual_per100": round(100 * ws[ch].mean(), 1)})
    return out
pe = np.array([p_elo(g, "home") for g in cal])
pm = np.array([p_mkt(g, "home") for g in cs])

# ---------------- team-game rows ----------------
rows = []   # one row per (team, game) for FBS teams
for g in games:
    for side, opp in (("home", "away"), ("away", "home")):
        if g[f"{side}Classification"] != "fbs": continue
        pts, opts = g[f"{side}Points"], g[f"{opp}Points"]
        rows.append(dict(gid=g["id"], season=g["season"], post=g["post"], date=g["startDate"], et=et(g["startDate"]),
                         team=g[f"{side}Team"], tid=g[f"{side}Id"], opp=g[f"{opp}Team"], fbsfbs=fbsfbs(g),
                         win=int(pts > opts), margin=pts - opts,
                         pe=p_elo(g, side), pec=p_elo(g, side, KSCALE, HFA2), pm=p_mkt(g, side), em=exp_margin(g, side),
                         notes=g.get("notes")))
# streaks: regular season only, reset each season, all opponents count
by_ts = defaultdict(list)
for r in rows:
    if not r["post"]: by_ts[(r["season"], r["tid"])].append(r)
for k, lst in by_ts.items():
    lst.sort(key=lambda r: r["date"]); s = 0
    for r in lst:
        r["streak"] = s
        s = (s + 1 if s > 0 else 1) if r["win"] else (s - 1 if s < 0 else -1)
    for r in lst: r["streak_after_last"] = s

# ---------------- Test A ----------------
A = [r for r in rows if not r["post"] and r["fbsfbs"]]
buckets = {"W5+": lambda s: s >= 5, "W3+": lambda s: s >= 3, "none (-2..+2)": lambda s: -2 <= s <= 2,
           "L3+": lambda s: s <= -3, "L5+": lambda s: s <= -5}
def bucket_stats(sub, pkey, outcome="win"):
    sub = [r for r in sub if r[pkey] is not None]
    n = len(sub)
    if n == 0: return None
    res = defaultdict(float)
    if outcome == "win":
        for r in sub: res[r["gid"]] += r["win"] - r[pkey]
        act = 100 * np.mean([r["win"] for r in sub]); exp = 100 * np.mean([r[pkey] for r in sub])
    else:   # points beyond the spread
        for r in sub: res[r["gid"]] += r["margin"] - r["em"]
        act = np.mean([r["margin"] for r in sub]); exp = np.mean([r["em"] for r in sub])
    gap = sum(res.values()) / n
    se = math.sqrt(sum(v * v for v in res.values())) / n   # clustered by game
    m = 100 if outcome == "win" else 1
    return {"n_games": n, "actual": round(act, 1), "expected": round(exp, 1), "gap": round(m * gap, 1), "se": round(m * se, 1)}

testA = {}
for bname, f in buckets.items():
    sub = [r for r in A if f(r["streak"])]
    testA[bname] = {
        "elo_standard": bucket_stats(sub, "pe"),
        "elo_recalibrated": bucket_stats(sub, "pec"),
        "market_spread": bucket_stats(sub, "pm"),
        "points_vs_spread": bucket_stats([r for r in sub if r["em"] is not None], "em", outcome="margin"),
    }
# same, 2014-2025 only (2026 partial)  and ex-2020
testA_ex2020 = {b: bucket_stats([r for r in A if f(r["streak"]) and r["season"] != 2020], "pm") for b, f in buckets.items()}

# ---------------- Test B ----------------
def ts_form(season, tid):
    lst = [r for r in by_ts.get((season, tid), []) if r["fbsfbs"]]
    pre = [r for r in lst if r["et"] < dt.datetime(season, 11, 1)]
    nov = [r for r in lst if r["et"].month == 11 and r["et"].year == season]
    if len(pre) < 4 or len(nov) < 2: return None
    nov_ats = [r["margin"] - r["em"] for r in nov if r["em"] is not None]
    return dict(pre=np.mean([r["margin"] for r in pre]), nov=np.mean([r["margin"] for r in nov]),
                novwp=np.mean([r["win"] for r in nov]), novats=np.mean(nov_ats) if len(nov_ats) >= 2 else None,
                n_pre=len(pre), n_nov=len(nov))

def paired_rows(filter_fn):
    out = []
    for g in games:
        if not fbsfbs(g) or not filter_fn(g): continue
        y = g["season"]
        fh, fa = ts_form(y, g["homeId"]), ts_form(y, g["awayId"])
        if fh is None or fa is None: continue
        ph, pmh = p_elo(g, "home"), p_mkt(g, "home")
        out.append(dict(gid=g["id"], season=y, home=g["homeTeam"], away=g["awayTeam"],
                        win=float(g["homePoints"] > g["awayPoints"]), margin=g["homePoints"] - g["awayPoints"],
                        pe=ph, pm=pmh, em=exp_margin(g, "home"),
                        d_pre=fh["pre"] - fa["pre"], d_nov=fh["nov"] - fa["nov"], d_novwp=fh["novwp"] - fa["novwp"],
                        d_novats=(fh["novats"] - fa["novats"]) if fh["novats"] is not None and fa["novats"] is not None else None))
    return out

def ols(y, X):
    X = np.column_stack([np.ones(len(y))] + X); b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b; r2 = 1 - r.var() / y.var()
    return b, r2

SCALE = {"d_nov": 10.0, "d_novats": 10.0, "d_novwp": 0.5}   # beta reported per 10 pts/game, or per 50 win-pct points
def analyse(P, outcome, form_key, nboot=2000):
    """Each game enters twice (both orientations) so the arbitrary home/away label cancels;
    bootstrap resamples GAMES."""
    P = [p for p in P if p[form_key] is not None and (outcome not in ("res_mkt", "ats") or p["em"] is not None)]
    def yv(p):
        return {"win": p["win"], "res_elo": p["win"] - p["pe"], "res_mkt": p["win"] - p["pm"], "ats": p["margin"] - p["em"]}[outcome]
    y0 = np.array([yv(p) for p in P]); pre0 = np.array([p["d_pre"] for p in P]); f0 = np.array([p[form_key] for p in P])
    yflip = (1 - y0) if outcome == "win" else -y0
    n = len(y0)
    def stats(idx):
        yy = np.concatenate([y0[idx], yflip[idx]]); pp = np.concatenate([pre0[idx], -pre0[idx]]); ff = np.concatenate([f0[idx], -f0[idx]])
        b1, r2a = ols(yy, [pp]); b2, r2b = ols(yy, [pp, ff])
        bf = np.polyfit(pp, ff, 1); fres = ff - np.polyval(bf, pp)
        t1, t2 = np.percentile(fres, [33.3, 66.7])
        return np.corrcoef(ff, yy)[0, 1], b2[2], r2b - r2a, yy[fres >= t2].mean(), yy[fres <= t1].mean()
    r, beta, dr2, hot, cold = stats(np.arange(n))
    boots = np.array([stats(rng.integers(0, n, n)) for _ in range(nboot)])
    lo, hi = np.percentile(boots[:, 1], [2.5, 97.5])
    dlo, dhi = np.percentile(boots[:, 3] - boots[:, 4], [2.5, 97.5])
    m = 100 if outcome != "ats" else 1; s = SCALE[form_key]
    return {"n_games": n, "corr_form_outcome": round(r, 2), "beta_form_given_strength": round(m * s * beta, 1),
            "beta_95ci": [round(m * s * lo, 1), round(m * s * hi, 1)], "delta_R2": round(dr2, 3),
            "hotter_third_mean": round(m * hot, 1), "colder_third_mean": round(m * cold, 1),
            "hot_minus_cold": round(m * (hot - cold), 1), "hot_minus_cold_95ci": [round(m * dlo, 1), round(m * dhi, 1)]}

post_pairs = paired_rows(lambda g: g["post"] and g["season"] < 2026)
dec_pairs = paired_rows(lambda g: (not g["post"]) and et(g["startDate"]).month == 12)
testB = {}
for label, P in (("postseason", post_pairs), ("december_regular", dec_pairs)):
    testB[label] = {}
    for fk in ("d_nov", "d_novwp", "d_novats"):
        testB[label][fk] = {o: analyse(P, o, fk) for o in ("win", "res_elo", "res_mkt", "ats")}
cfp_pairs = paired_rows(lambda g: g["post"] and g["season"] < 2026 and g.get("playoff"))
testB["cfp_only"] = {fk: {o: analyse(cfp_pairs, o, fk) for o in ("win", "res_mkt", "ats")} for fk in ("d_nov", "d_novats")}
testB["postseason_ex2020"] = {o: analyse([p for p in post_pairs if p["season"] != 2020], o, "d_nov") for o in ("res_mkt", "ats")}

# ---------------- Test C: 2026 CFP top 25 ----------------
espn = json.load(open("raw/espn-rankings-2026-11-18.json"))
cfp = [r for r in espn["rankings"] if r["name"] == "Playoff Committee Rankings"][0]
testC = []
for rk in cfp["ranks"]:
    tid = int(rk["team"]["id"]); lst = by_ts.get((2026, tid), [])
    W = sum(r["win"] for r in lst); L = len(lst) - W
    nov = [r for r in lst if r["et"].month == 11]
    novf = [r for r in nov if r["fbsfbs"]]
    last3 = lst[-3:]
    fb = [r for r in lst if r["fbsfbs"]]
    pre = [r for r in fb if r["et"] < dt.datetime(2026, 11, 1)]
    def ats(rs):
        v = [r["margin"] - r["em"] for r in rs if r["em"] is not None]
        return round(float(np.mean(v)), 1) if v else None
    testC.append(dict(cfp=rk["current"], team=rk["team"]["location"], espn_record=rk.get("recordSummary"),
                      cfbd_record=f"{W}-{L}", record_match=(rk.get("recordSummary") == f"{W}-{L}"),
                      streak=lst[-1]["streak_after_last"] if lst else None,
                      nov_games=[f"{'W' if r['win'] else 'L'} {r['margin']:+d} v {r['opp']} (spread-exp {r['em']:+.1f})" if r["em"] is not None else f"{'W' if r['win'] else 'L'} {r['margin']:+d} v {r['opp']}" for r in nov],
                      nov_margin=round(float(np.mean([r["margin"] for r in nov])), 1) if nov else None,
                      nov_vs_spread=ats(nov), nov_fbs_margin=round(float(np.mean([r["margin"] for r in novf])), 1) if novf else None,
                      nov_fbs_vs_spread=ats(novf), last3_vs_spread=ats(last3),
                      pre_nov_margin_fbs=round(float(np.mean([r["margin"] for r in pre])), 1) if pre else None))

out = dict(
    generated="2026-11-18", data_through_2026="week 11 (Saturday 2026-11-14); CFBD cache pulled 2026-11-18 04:58 holds 3 week-12 MAC games (Nov 17), excluded",
    benchmarks=dict(elo_home_edge_points=round(HFA, 1), elo_recalibrated=dict(home_edge=round(HFA2, 1), scale_k=round(KSCALE, 3)),
                    spread_sd_points=round(SD, 1), n_calibration_games_elo=len(cal), n_calibration_games_spread=len(cs),
                    elo_calibration_deciles=calib(pe, hw), market_calibration_deciles=calib(pm, hw2),
                    line_coverage_testA=round(np.mean([r["pm"] is not None for r in A]), 3)),
    testA=testA, testA_market_ex2020=testA_ex2020, testB=testB, testC=testC)
json.dump(out, open("results.json", "w"), indent=1, default=float)
print(json.dumps({k: out[k] for k in ("benchmarks",)}, indent=1, default=float)[:3000])
print(json.dumps(testA, indent=0))
for lab in testB:
    print(lab, json.dumps(testB[lab], indent=0)[:4000])
for c in testC: print(c)
