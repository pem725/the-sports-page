#!/usr/bin/env python3
"""The NFL misery slide: which club has the least to look forward to?

The question (editor, 2026-10-31): with about seven games played, which team has
the lowest probability of success from here, now that there is real evidence?
Measure it, do not assume it. The Jets, Browns and Falcons were named as
candidates; the model is not told that.

Method, in plain terms
  * Every club has one number, its STRENGTH in points against an average club.
    Home field is one more number, the same for everybody. A game's expected
    margin is  strength(home) - strength(away) + home field.
  * PRIOR. Before Week 1 the betting market already had an opinion. The paper's
    own NFL board solved it on 2026-09-08, the day before kickoff, from 112
    published point spreads (git commit b4774d4, data/nfl-odds.json). That is
    each club's prior mean. It is frozen in data/nfl/preseason-ratings-2026.json
    so a later rerun cannot quietly use lines that have since absorbed results.
  * PRIOR SD (how far a preseason rating is allowed to be wrong). Fitted, not
    picked: for 2015-2025, the strength implied by Weeks 1-3 closing spreads is
    the stand-in prior (nflverse keeps closing lines only, so true preseason
    lines for past years are gone), and the SD that makes Weeks 3-7 margins most
    likely (empirical Bayes, maximum marginal likelihood) is 3.5 points. A
    Week-3 line knows two weeks more than a preseason line; in 2026 the two
    differ by an RMS of 1.6 points, and because a market's updates are
    uncorrelated with its remaining error the variances add:
    sqrt(3.5^2 + 1.6^2) = 3.8. Home field gets its own prior, SD 1 point.
  * LIKELIHOOD. Every 2026 final score: margin ~ Normal(expected margin, 13.2).
    13.2 points is the house figure for how far an NFL result lands from its
    expectation (closing-line residuals 2015-2025 run 12.7).
  * POSTERIOR. Normal prior, normal likelihood, linear model: the posterior is
    exactly a 33-dimensional normal (32 strengths and home field), computed in
    closed form. No MCMC, no tuning.
  * SIMULATION. 40,000 seasons. Each one first draws all 33 numbers from the
    posterior, so the uncertainty about how good a club IS flows through, then
    plays every remaining game with Normal(margin, 13.2) noise. Playoffs are
    counted with scripts/build_nfl_odds.py's field(): four division winners and
    three wild cards a conference, ties broken at random.
  * MISERY. Two rankings, the editor picks. (1) Lowest projected final winning
    percentage. (2) The SLIDE: preseason expected wins minus projected wins --
    the paper's "fandom misery" idea, hope minus reality.

Out-of-sample check (2023-2025, never used to fit the prior SD, which for this
check is refitted on 2015-2022 only): same procedure at the same point of the
season, then score every Week 8-18 game. Compared against the prior alone, the
market's own ratings at that moment (solved from Weeks 6-8 closing spreads), and
each game's closing spread (which knows injuries and results we do not -- a
ceiling, not a rival).

Traps
  * Strength is held fixed for the rest of the season. Injuries, a benched
    quarterback, a fired coach: none of it is in the model. The market knows;
    we do not. That is the main reason the closing line beats us.
  * Ties are broken at random in the playoff count, not by the NFL's rules.
  * A tie on the field (Giants-Commanders, Week 5) counts half a win.
  * Relocated franchises: nflverse spells old seasons OAK/SD/STL; mapped to
    LV/LAC/LA so the 32 slots line up across years.
  * 2026 itself prefers a smaller prior SD (its own maximum is at the bottom of
    the grid, margins have landed only 11.8 points from the preseason lines).
    One season of ~110 games is a noisy estimate; the 11-season fit is used and
    the sensitivity at SD 2 is printed.

Sources: nflverse schedules games.csv (scores and closing spreads), and the
paper's own 2026-09-08 market solve from that same feed. No web-search numbers,
no CollegeFootballData, no secrets.

Usage
  python3 scripts/nfl_misery.py            # fetch the schedule, model, write JSON + page
  python3 scripts/nfl_misery.py --offline  # cached schedule only
  python3 scripts/nfl_misery.py --dry-run  # report, write nothing
Outputs: data/nfl-misery.json, nfl-misery.html
"""
import argparse
import csv
import datetime as dt
import html
import io
import json
import math
import os
import pathlib
import re
import subprocess
import sys
import urllib.request

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_nfl_odds import DIV, TEAM_DIV, CONF, field  # noqa: E402

GAMES = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
CACHE = pathlib.Path.home() / ".cache" / "sports-page" / "nfl" / "games.csv"
FALLBACK = ROOT / "data" / "nfl" / "nflverse-games.csv"
PRESEASON = ROOT / "data" / "nfl" / "preseason-ratings-2026.json"
PRESEASON_COMMIT = "b4774d4"          # 2026-09-08 board refresh, day before kickoff
OUT_JSON = ROOT / "data" / "nfl-misery.json"
OUT_HTML = ROOT / "nfl-misery.html"

SIGMA = 13.2           # game-margin noise, points
HFA_SD = 1.0           # prior SD on home field
NSIMS = 40000
SEASON = 2026
TAUS = np.arange(0.5, 8.01, 0.25)
RELOC = {"OAK": "LV", "SD": "LAC", "STL": "LA"}

TEAMS = sorted(TEAM_DIV)
IDX = {t: i for i, t in enumerate(TEAMS)}
FULL = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LAC": "Los Angeles Chargers", "LA": "Los Angeles Rams",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}
# One chart color per club, for the highlighted line only (plain hex, no marks).
COLOR = {
    "ARI": "#97233f", "ATL": "#a71930", "BAL": "#241773", "BUF": "#00338d", "CAR": "#0085ca",
    "CHI": "#c83803", "CIN": "#fb4f14", "CLE": "#ff3c00", "DAL": "#003594", "DEN": "#fb4f14",
    "DET": "#0076b6", "GB": "#203731", "HOU": "#a71930", "IND": "#002c5f", "JAX": "#006778",
    "KC": "#e31837", "LAC": "#0080c6", "LA": "#003594", "LV": "#4b4b4b", "MIA": "#008e97",
    "MIN": "#4f2683", "NE": "#c60c30", "NO": "#9f8958", "NYG": "#0b2265", "NYJ": "#125740",
    "PHI": "#004c54", "PIT": "#c69214", "SEA": "#2f6f33", "SF": "#aa0000", "TB": "#d50a0a",
    "TEN": "#4b92db", "WAS": "#5a1414",
}


def say(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- data
def load(offline):
    if not offline:
        try:
            req = urllib.request.Request(GAMES, headers={"User-Agent": "Mozilla/5.0"})
            txt = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            CACHE.write_text(txt)
        except Exception as e:                      # fall through to the cache
            say(f"  fetch failed ({e}); using cache")
    src = CACHE if CACHE.exists() else FALLBACK
    if not src.exists():
        raise SystemExit("no cached schedule; run once without --offline")
    rows = [r for r in csv.DictReader(io.StringIO(src.read_text()))
            if r["game_type"] == "REG"]
    for r in rows:
        r["home_team"] = RELOC.get(r["home_team"], r["home_team"])
        r["away_team"] = RELOC.get(r["away_team"], r["away_team"])
        r["week"] = int(r["week"])
    return rows, src


def season(rows, s):
    return [r for r in rows if r["season"] == str(s)]


def weeks(rows, a, b):
    return [r for r in rows if a <= r["week"] <= b]


def done(r):
    return r["home_score"] not in ("", None) and r["away_score"] not in ("", None)


def margin(r):
    return float(r["home_score"]) - float(r["away_score"])


def design(rows):
    A = np.zeros((len(rows), 33))
    for k, r in enumerate(rows):
        A[k, IDX[r["home_team"]]] = 1.0
        A[k, IDX[r["away_team"]]] = -1.0
        A[k, 32] = 1.0
    return A


def solve_lines(rows, ridge=0.05):
    """Market strengths from closing spreads (spread_line > 0 = home favored),
    least squares, strengths pinned to sum to zero, a light ridge so a thin week
    of lines cannot produce a wild rating."""
    rows = [r for r in rows if r["spread_line"] not in ("", None)]
    A = design(rows)
    b = np.array([float(r["spread_line"]) for r in rows])
    R = ridge * np.eye(33)
    R[32, 32] = 0.0
    A2 = np.vstack([A, 10 * np.append(np.ones(32), 0.0), R])
    b2 = np.concatenate([b, [0.0], np.zeros(33)])
    return np.linalg.lstsq(A2, b2, rcond=None)[0]


def preseason_prior():
    """The paper's own market solve from 2026-09-08 (112 spreads, before kickoff).
    Frozen to a data file the first time, from git history."""
    if PRESEASON.exists():
        d = json.loads(PRESEASON.read_text())
    else:
        raw = subprocess.check_output(["git", "show", f"{PRESEASON_COMMIT}:data/nfl-odds.json"],
                                      cwd=ROOT)
        od = json.loads(raw)
        hfa = float(re.search(r"home advantage (-?\d+\.\d+)", od["method"]).group(1))
        d = {"source": f"git {PRESEASON_COMMIT}:data/nfl-odds.json (generated {od['generated']})",
             "method": od["method"], "hfa": hfa,
             "ratings": {t["team"]: t["rating"] for t in od["teams"]}}
        PRESEASON.write_text(json.dumps(d, indent=1))
    return np.array([d["ratings"][t] for t in TEAMS] + [d["hfa"]]), d


# ---------------------------------------------------------------- model
def posterior(m0, tau, rows):
    """Exact normal-normal update. Returns posterior mean and covariance (33-d)."""
    P0 = np.diag([1 / tau ** 2] * 32 + [1 / HFA_SD ** 2])
    if not rows:
        return m0.copy(), np.linalg.inv(P0)
    A = design(rows)
    y = np.array([margin(r) for r in rows])
    P = P0 + A.T @ A / SIGMA ** 2
    C = np.linalg.inv(P)
    m = C @ (P0 @ m0 + A.T @ y / SIGMA ** 2)
    return m, C


def loglik(m0, tau, rows):
    """Marginal log-likelihood of the margins under the prior (empirical Bayes)."""
    A = design(rows)
    y = np.array([margin(r) for r in rows])
    S0 = np.diag([tau ** 2] * 32 + [HFA_SD ** 2])
    C = A @ S0 @ A.T + SIGMA ** 2 * np.eye(len(y))
    d = y - A @ m0
    return -0.5 * (np.linalg.slogdet(C)[1] + d @ np.linalg.solve(C, d))


def Phi(x):
    return 0.5 * (1 + np.vectorize(math.erf)(np.asarray(x) / math.sqrt(2)))


def game_prob(m, C, r):
    """P(home wins), integrating over strength uncertainty."""
    x = design([r])[0]
    return float(Phi((x @ m) / math.sqrt(SIGMA ** 2 + x @ C @ x)))


def fit_tau(rows, years):
    tot = np.zeros(len(TAUS))
    per = {}
    for s in years:
        g = season(rows, s)
        m0 = solve_lines(weeks(g, 1, 3))
        l = np.array([loglik(m0, t, [r for r in weeks(g, 3, 7) if done(r)]) for t in TAUS])
        tot += l
        per[s] = float(TAUS[np.argmax(l)])
    return float(TAUS[np.argmax(tot)]), per


# ---------------------------------------------------------------- check
def backtest(rows, tau):
    """2023-2025: prior = Weeks 1-3 market, update on Weeks 3-7, score Weeks 8-18."""
    out = {"seasons": [2023, 2024, 2025], "tau": tau, "models": {}}
    preds = {"prior": [], "posterior": [], "market_now": [], "closing_line": []}
    ys = []
    for s in out["seasons"]:
        g = season(rows, s)
        m0 = solve_lines(weeks(g, 1, 3))
        C0 = np.diag([tau ** 2] * 32 + [HFA_SD ** 2])
        m1, C1 = posterior(m0, tau, [r for r in weeks(g, 3, 7) if done(r)])
        mk = solve_lines(weeks(g, 6, 8))
        for r in weeks(g, 8, 18):
            if not done(r) or margin(r) == 0:
                continue
            ys.append(1.0 if margin(r) > 0 else 0.0)
            preds["prior"].append(game_prob(m0, C0, r))
            preds["posterior"].append(game_prob(m1, C1, r))
            preds["market_now"].append(float(Phi((design([r])[0] @ mk) / SIGMA)))
            preds["closing_line"].append(float(Phi(float(r["spread_line"]) / SIGMA)))
    y = np.array(ys)
    for k, p in preds.items():
        p = np.array(p)
        bins = []
        for lo in range(0, 100, 10):
            sel = (p * 100 >= lo) & (p * 100 < lo + 10 if lo < 90 else p * 100 <= 100)
            if sel.sum():
                bins.append({"bin": f"{lo}-{lo + 10}%", "n": int(sel.sum()),
                             "predicted": round(float(p[sel].mean()), 3),
                             "actual": round(float(y[sel].mean()), 3)})
        fav = np.where(p >= 0.5, y, 1 - y)
        out["models"][k] = {"brier": round(float(np.mean((p - y) ** 2)), 4),
                            "favorite_won": round(float(fav.mean()), 3),
                            "calibration": bins}
    out["games"] = int(len(y))
    out["home_win_rate"] = round(float(y.mean()), 3)
    out["brier_coin"] = 0.25
    return out


# ---------------------------------------------------------------- 2026
def run_season(rows, m0, tau, rng):
    g = season(rows, SEASON)
    seen = {r["home_team"] for r in g} | {r["away_team"] for r in g}
    if seen != set(TEAMS):
        raise SystemExit(f"club codes do not match the division map: {seen ^ set(TEAMS)}")
    played = [r for r in g if done(r)]
    left = [r for r in g if not done(r)]
    m, C = posterior(m0, tau, played)

    # wins by week: actual for played games, simulated for the rest
    W = np.zeros((NSIMS, 32, 19), dtype=np.float32)
    for r in played:
        h, a, w, d = IDX[r["home_team"]], IDX[r["away_team"]], r["week"], margin(r)
        W[:, h, w] += 1.0 if d > 0 else 0.5 if d == 0 else 0.0
        W[:, a, w] += 1.0 if d < 0 else 0.5 if d == 0 else 0.0
    L = np.linalg.cholesky(C + 1e-12 * np.eye(33))
    theta = m + rng.standard_normal((NSIMS, 33)) @ L.T
    for r in left:
        h, a, w = IDX[r["home_team"]], IDX[r["away_team"]], r["week"]
        mu = theta[:, h] - theta[:, a] + theta[:, 32]
        hw = (mu + rng.normal(0, SIGMA, NSIMS)) > 0
        W[:, h, w] += hw
        W[:, a, w] += ~hw
    cum = np.cumsum(W, axis=2)                     # cum[:, t, w] = wins through week w
    final = cum[:, :, 18]
    made, _ = field(final.astype(float), TEAMS, rng)

    C0 = np.diag([tau ** 2] * 32 + [HFA_SD ** 2])
    teams = []
    for t in TEAMS:
        i = IDX[t]
        games = sorted((r for r in g if t in (r["home_team"], r["away_team"])), key=lambda r: r["week"])
        wk_game = {r["week"]: r for r in games}
        wins = losses = ties = 0
        prior_exp = 0.0
        sched = []
        for r in games:
            home = r["home_team"] == t
            opp = r["away_team"] if home else r["home_team"]
            ph = game_prob(m0, C0, r)
            prior_exp += ph if home else 1 - ph
            row = {"wk": r["week"], "date": r["gameday"], "opp": opp, "home": home}
            if done(r):
                d = margin(r) * (1 if home else -1)
                us = int(float(r["home_score"] if home else r["away_score"]))
                them = int(float(r["away_score"] if home else r["home_score"]))
                res = "W" if d > 0 else "T" if d == 0 else "L"
                wins += res == "W"; losses += res == "L"; ties += res == "T"
                row.update(res=res, score=f"{us}-{them}")
            else:
                ph = game_prob(m, C, r)
                row["p"] = round(ph if home else 1 - ph, 3)
            sched.append(row)
        # last week through which this club's results are all known
        known = 0
        for w in range(1, 19):
            if w in wk_game and not done(wk_game[w]):
                break
            known = w
        traj = []
        for w in range(1, 19):
            c = cum[:, i, w]
            r = wk_game.get(w)
            pt = {"wk": w, "mean": round(float(c.mean()), 2),
                  "lo": float(np.percentile(c, 10)), "med": float(np.median(c)),
                  "hi": float(np.percentile(c, 90))}
            if w <= known:
                pt["actual"] = float(c[0])
            if r is None:
                pt["bye"] = True
            elif not done(r):
                home = r["home_team"] == t
                ph = game_prob(m, C, r)
                pt["p"] = round(ph if home else 1 - ph, 3)
            traj.append(pt)
        f = final[:, i]
        proj = float(f.mean())
        teams.append({
            "team": t, "name": FULL[t], "color": COLOR[t], "div": TEAM_DIV[t], "conf": CONF[t],
            "w": wins, "l": losses, "t": ties, "gp": wins + losses + ties, "known": known,
            "prior_rating": round(float(m0[i]), 2), "post_rating": round(float(m[i]), 2),
            "post_sd": round(float(math.sqrt(C[i, i])), 2),
            "evidence": round(1 - C[i, i] / tau ** 2, 2),
            "prior_wins": round(prior_exp, 2), "proj": round(proj, 2),
            "proj_lo": float(np.percentile(f, 10)), "proj_hi": float(np.percentile(f, 90)),
            "pct": round(proj / 17, 3), "slide": round(prior_exp - proj, 2),
            "p_le4": round(float((f <= 4).mean()), 4), "p_le3": round(float((f <= 3).mean()), 4),
            "p_po": round(float(made[:, i].mean()), 4),
            "cdf": [round(float((f <= n).mean()), 4) for n in range(18)],
            "sched": sched, "traj": traj,
        })
    last = max(played, key=lambda r: (r["gameday"], r["week"]))
    meta = {"played": len(played), "left": len(left), "hfa_post": round(float(m[32]), 2),
            "hfa_post_sd": round(float(math.sqrt(C[32, 32])), 2),
            "last_date": last["gameday"], "last_week": last["week"],
            "full_weeks": max(w for w in range(1, 19) if all(done(r) for r in weeks(g, 1, w)))}
    return teams, meta


# ---------------------------------------------------------------- formatting
def pct(p):
    """At most two significant digits, honest at the ends."""
    if p < 0.005:
        return "<1%"
    if p > 0.995:
        return ">99%"
    return f"{p * 100:.0f}%" if p >= 0.095 else f"{p * 100:.1g}%"


def wins_fmt(x):
    return f"{x:.1f}" if abs(x) < 9.95 else f"{x:.0f}"


def rec(t):
    return f"{t['w']}-{t['l']}" + (f"-{t['t']}" if t["t"] else "")


# ---------------------------------------------------------------- page
def build_page(data):
    T = data["teams"]
    by_pct = sorted(T, key=lambda t: (t["pct"], -t["p_le4"]))
    by_slide = sorted(T, key=lambda t: -t["slide"])
    worst, slid, best = by_pct[0], by_slide[0], by_pct[-1]
    bt = data["backtest"]["models"]
    m = data["meta"]
    tau = data["tau"]
    E = html.escape
    week_txt = (f"Week {m['full_weeks']}" + (f" and part of Week {m['last_week']}"
                                             if m["last_week"] > m["full_weeks"] else ""))
    upd = dt.date.fromisoformat(data["generated"]).strftime("%B %-d, %Y")
    deck = (f"After {week_txt}, the {E(worst['name'])} project to {wins_fmt(worst['proj'])} wins "
            f"(80% range {worst['proj_lo']:.0f} to {worst['proj_hi']:.0f}), the fewest in the league. "
            f"The biggest fall from August belongs to the {E(slid['name'])}: "
            f"{wins_fmt(slid['prior_wins'])} wins expected then, {wins_fmt(slid['proj'])} now.")
    b_post, b_prior = bt["posterior"]["brier"], bt["prior"]["brier"]
    b_mkt, b_close = bt["market_now"]["brier"], bt["closing_line"]["brier"]
    verdict = ("the market's own ratings at the same moment did better" if b_mkt < b_post else
               "it matched or beat the market's own ratings at the same moment")
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    style = """
:root{--ink:#1a1208;--cream:#f5f0e8;--aged:#e0d8c5;--rust:#b83a1e;--steel:#2c4a6e;--gold:#c9962a;
--muted:#6b5e4a;--div:#c8b99a;--card:#ede5d2;--line:#b9ad94;--band:rgba(44,74,110,.14)}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--aged);color:var(--ink);font-family:'Libre Baskerville',Georgia,serif;font-size:16px;line-height:1.7;padding:1.5rem 1rem 3rem}
.masthead{max-width:1000px;margin:0 auto;text-align:center;border-top:4px solid var(--ink);padding:.5rem 0 0}
.kicker{font-family:'Roboto Mono',monospace;font-size:.68rem;letter-spacing:.22em;text-transform:uppercase;color:var(--muted)}
.title{font-family:'Playfair Display',serif;font-size:clamp(1.6rem,4vw,2.6rem);font-weight:700;letter-spacing:.04em;text-transform:uppercase;margin:.1rem 0}
.title a{color:inherit;text-decoration:none}
.tagline{font-family:'Playfair Display',serif;font-style:italic;font-size:.95rem;color:var(--muted);margin:.2rem 0 .4rem}
.datebar{display:flex;justify-content:space-between;gap:.6rem;flex-wrap:wrap;font-family:'Roboto Mono',monospace;font-size:.65rem;color:var(--muted);letter-spacing:.1em;border-top:1px solid var(--ink);border-bottom:3px double var(--ink);padding:.3rem 0;margin-top:.3rem}
.paper{max-width:1000px;margin:.8rem auto 0;background:var(--cream);padding:2rem 2.2rem 2.4rem;box-shadow:0 6px 40px rgba(0,0,0,.2);border:1px solid var(--div);display:grid;gap:1.1rem;min-width:0}
.paper>*{min-width:0}
@media(max-width:600px){.paper{padding:1.2rem 1rem}}
h1{font-family:'Playfair Display',serif;font-size:clamp(1.8rem,4.4vw,2.7rem);font-weight:900;line-height:1.1;text-wrap:balance}
h1 em{color:var(--rust)}
.deck{font-style:italic;font-size:1.02rem;color:var(--muted);border-left:3px solid var(--rust);padding-left:.9rem;line-height:1.55;max-width:66ch}
.bar{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:center;border-top:2px solid var(--ink);border-bottom:1px solid var(--div);padding:10px 0}
button,select{font-family:'Roboto Mono',monospace;font-size:13px;color:var(--ink);background:var(--cream);border:1px solid var(--muted);border-radius:3px;padding:6px 10px;max-width:100%}
button{cursor:pointer}
button:focus-visible,select:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.seg{display:inline-flex}
.seg button{border-radius:0}.seg button:first-child{border-radius:3px 0 0 3px}.seg button:last-child{border-radius:0 3px 3px 0;border-left:0}
.seg button[aria-pressed="true"]{background:var(--steel);color:var(--cream);border-color:var(--steel)}
.chartbox{position:relative;width:100%}
svg.chart{width:100%;height:auto;display:block;touch-action:manipulation}
svg.chart text{font-family:'Roboto Mono',monospace;fill:var(--muted)}
.hit{fill:none;stroke:transparent;stroke-width:12;cursor:pointer;pointer-events:stroke}
.card{background:var(--card);border:1px solid var(--div);border-left:4px solid var(--rust);padding:12px 14px;font-size:14px}
.card h3{font-family:'Playfair Display',serif;font-size:1.25rem;line-height:1.2;margin-bottom:4px}
.stats{display:flex;flex-wrap:wrap;gap:4px 18px;font-family:'Roboto Mono',monospace;font-size:12.5px;color:var(--muted);margin:6px 0 8px}
.stats b{color:var(--ink);font-weight:600}
.sched{width:100%;border-collapse:collapse;font-size:13px}
.sched td{padding:2px 4px 2px 0;border-bottom:1px dotted var(--div)}
.sched td.num{font-family:'Roboto Mono',monospace;text-align:right;white-space:nowrap}
.pbar{display:inline-block;height:8px;background:var(--steel);vertical-align:middle;margin-left:6px;opacity:.7}
.cols{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:24px}
@media(max-width:820px){.cols{grid-template-columns:minmax(0,1fr)}}
h2{font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;border-bottom:2px solid var(--rust);padding-bottom:.2rem;margin-bottom:.7rem}
table.rank{width:100%;border-collapse:collapse;font-size:13.5px}
.rank th{font-family:'Roboto Mono',monospace;font-size:11px;font-weight:600;text-align:right;color:var(--muted);border-bottom:2px solid var(--ink);padding:3px 0 3px 6px;white-space:nowrap}
.rank th:nth-child(2){text-align:left}
.rank td{padding:4px 0 4px 6px;border-bottom:1px dotted var(--div);vertical-align:top}
.rank td.num{font-family:'Roboto Mono',monospace;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.rank tbody tr{cursor:pointer}
.rank tbody tr:hover{background:var(--card)}
.rank tr.sel{background:#e9dcc0}
.sw{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:0}
@media(max-width:520px){.rank .opt,.rank small{display:none}.rank{font-size:12.5px}}
.notes p{margin:0 0 .8rem;max-width:66ch}
.legend{display:flex;flex-wrap:wrap;gap:6px 20px;font-family:'Roboto Mono',monospace;font-size:12px;color:var(--muted)}
.src{font-family:'Roboto Mono',monospace;font-size:11.5px;line-height:1.6;color:var(--muted);border-top:1px solid var(--div);padding-top:10px}
.src a,.notes a{color:var(--steel)}
.foot{display:flex;justify-content:space-between;flex-wrap:wrap;gap:.3rem;border-top:3px double var(--ink);padding-top:.7rem;font-family:'Roboto Mono',monospace;font-size:.63rem;color:var(--muted);letter-spacing:.07em}
.foot a{color:var(--rust);text-decoration:none}
"""
    calib_rows = "".join(
        f"<tr><td>{b['bin']}</td><td class='num'>{b['n']}</td><td class='num'>{b['predicted'] * 100:.0f}%</td>"
        f"<td class='num'>{b['actual'] * 100:.0f}%</td></tr>"
        for b in bt["posterior"]["calibration"])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Sports Page &mdash; The NFL Misery Slide</title>
<meta name="description" content="Every NFL club's season, played and still to play: actual wins so far, then a Bayesian projection of every remaining game.">
<meta property="og:title" content="The NFL Misery Slide">
<meta property="og:description" content="Which NFL club has the least to look forward to? Every remaining game, projected.">
<meta property="og:url" content="https://thesportspage.net/nfl-misery.html">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Sports Page">
<meta name="robots" content="noindex">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Roboto+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>{style}</style>
<script data-goatcounter="https://thesportspage.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<script src="assets/sitenav.js" defer></script>
</head>
<body>
<div class="masthead">
  <div class="kicker">NFL &middot; {SEASON} Season</div>
  <div class="title"><a href="https://thesportspage.net/" target="_blank" rel="noopener">The Sports Page</a></div>
  <div class="tagline">Making the numbers mean something since the first pitch</div>
  <div class="datebar"><span>The Misery Slide</span><span>{m['played']} games played &middot; {m['left']} to go</span><span>Updated {upd}</span></div>
</div>
<div class="paper">
  <h1>Who Has the Least to Look Forward To? <em>The Misery Slide.</em></h1>
  <p class="deck">{deck}</p>

  <div class="bar">
    <div class="seg" role="group" aria-label="View">
      <button type="button" id="v-wins" aria-pressed="true">Win % by week</button>
      <button type="button" id="v-cdf" aria-pressed="false">Chance of N or fewer</button>
    </div>
    <select id="pick" aria-label="Choose a team"></select>
  </div>

  <div class="chartbox"><svg class="chart" id="chart" viewBox="0 0 640 400" role="img" aria-label="Winning percentage by week for every NFL club, with projections"></svg></div>
  <div class="legend" id="legend"></div>
  <div class="card" id="card" aria-live="polite"></div>

  <div class="cols">
    <section>
      <h2>The Misery Slide</h2>
      <div class="seg" role="group" aria-label="Sort" style="margin-bottom:8px">
        <button type="button" id="s-pct" aria-pressed="true">Fewest projected wins</button>
        <button type="button" id="s-slide" aria-pressed="false">Biggest fall from August</button>
      </div>
      <table class="rank" id="rank"></table>
      <p class="src" style="border:0;padding:6px 0 0">Projected wins: the average of {NSIMS:,} simulated seasons, with the range that holds 8 seasons in 10. vs Aug.: today&rsquo;s projection minus the wins expected in August. Tap a row to follow a club.</p>
    </section>
    <section class="notes">
      <h2>How to read it</h2>
      <p><b>What is the question?</b> With about seven games played, which club can expect the least from the rest of its season? Notice that this is not the same as which club is worst so far. A bad record against a hard schedule can still have an easy run left.</p>
      <p><b>The solid part of each line is what happened:</b> the club&rsquo;s winning percentage after each week. The dashed part is the projection: where that percentage is expected to go, game by game, on the real remaining schedule. A flat stretch is a bye. Tap a line, or pick a club, to see its band and every remaining game.</p>
      <p><b>The other view is the cumulative one.</b> For each club it plots the chance of finishing with N wins or fewer. A curve that shoots up early on the left is a club whose season is close to settled.</p>
      <p><b>How we built it.</b> We started every club where the betting market had it the day before kickoff, then let this season&rsquo;s scores move it. How far the scores are allowed to move a club depends on how wrong August usually is: we measured that from 2015&ndash;2025 at {tau:.1f} points of strength. Then we played the rest of the season {NSIMS:,} times.</p>
      <p><b>Does it work?</b> We ran the same recipe on 2023&ndash;2025 at the same point of the season and scored the {data['backtest']['games']} games that followed. Updating on results beat the August view alone (Brier score {b_post:.3f} against {b_prior:.3f}; lower is better, a coin scores 0.250). But {verdict} ({b_mkt:.3f}), and each game&rsquo;s closing line, which knows about injuries we do not, scored {b_close:.3f}. Read this as a fair summary of the scores, not as a better forecast than the market.</p>
      <table class="sched" style="max-width:340px"><tr><td><b>We said</b></td><td class="num">games</td><td class="num">predicted</td><td class="num">won</td></tr>{calib_rows}</table>
      <p class="src" style="border:0;padding:4px 0 0">Calibration, 2023&ndash;2025, home club&rsquo;s chance of winning.</p>
    </section>
  </div>

  <p class="src">What it leaves out: injuries, quarterback changes and coaching changes after today. Strength is held fixed for the rest of the season. Playoff ties are broken at random, not by the NFL&rsquo;s rules. A tie counts half a win. Scores and closing spreads: <a href="https://github.com/nflverse/nflverse-data/releases/tag/schedules" target="_blank" rel="noopener">nflverse schedules</a>. Data through {E(m['last_date'])}.</p>

  <div class="foot">
    <span>The Sports Page</span>
    <span><a href="https://thesportspage.net/" target="_blank" rel="noopener">&larr; Back to the Archive</a></span>
    <span>One Question Per Issue, Answered With Numbers.</span>
  </div>
</div>
<script>const D={payload};</script>
<script>{JS}</script>
</body>
</html>
"""


JS = r"""
(function(){
const T=D.teams, BY={}; T.forEach(t=>{BY[t.team]=t;
  // games played through each week (byes add none), so wins become a winning percentage
  const gp={};let n=0;for(let w=1;w<=18;w++){if(t.sched.some(s=>s.wk===w))n++;gp[w]=n;}t.gpw=gp;});
const P_=(t,wk,v)=>t.gpw[wk]?v/t.gpw[wk]:null;
const svg=document.getElementById('chart'), NS='http://www.w3.org/2000/svg';
let W=640,H=400;const ML=40,MR=14,MT=30,MB=34;
let view='wins', sel=null, sortBy='pct';
const pct=p=>p<0.005?'<1%':p>0.995?'>99%':(p>=0.095?Math.round(p*100)+'%':(+(p*100).toPrecision(1))+'%');
const wf=x=>Math.abs(x)<9.95?x.toFixed(1):x.toFixed(0);
const rec=t=>t.w+'-'+t.l+(t.t?'-'+t.t:'');
function el(n,a,p){const e=document.createElementNS(NS,n);for(const k in a)e.setAttribute(k,a[k]);if(p)p.appendChild(e);return e}
function draw(){
  svg.innerHTML='';
  const cw=svg.clientWidth||640; if(cw<560){W=360;H=440}else{W=640;H=400} svg.setAttribute('viewBox','0 0 '+W+' '+H);
  const xmax=view==='wins'?18:17, x0=view==='wins'?1:0, ymax=1;
  const X=v=>ML+(v-x0)/(xmax-x0)*(W-ML-MR), Y=v=>H-MB-v/ymax*(H-MT-MB);
  const g=el('g',{},svg);
  const yt=[0,.25,.5,.75,1];
  yt.forEach(v=>{el('line',{x1:ML,x2:W-MR,y1:Y(v),y2:Y(v),stroke:'#ddd2bb','stroke-width':1},g);
    const t=el('text',{x:ML-6,y:Y(v)+4,'text-anchor':'end','font-size':11},g);t.textContent=view==='wins'?(v===1?'1.000':'.'+String(Math.round(v*1000)).padStart(3,'0')):Math.round(v*100)+'%';});
  if(view==='wins')el('line',{x1:ML,x2:W-MR,y1:Y(.5),y2:Y(.5),stroke:'#6b5e4a','stroke-width':1,'stroke-dasharray':'2 3'},g);
  const xt=view==='wins'?[1,4,7,10,13,16,18]:[0,2,4,6,8,10,12,14,17];
  xt.forEach(v=>{const t=el('text',{x:X(v),y:H-MB+16,'text-anchor':'middle','font-size':11},g);t.textContent=v;});
  const xl=el('text',{x:(ML+W-MR)/2,y:H-4,'text-anchor':'middle','font-size':11},g);
  xl.textContent=view==='wins'?'week':'final wins (N)';
  const yl=el('text',{x:4,y:14,'font-size':11},g); yl.textContent=view==='wins'?'win %':'P(N or fewer)';
  if(view==='wins'&&sel){
    const t=BY[sel], k=Math.max(t.known,1), pts=t.traj.filter(p=>p.wk>=k&&t.gpw[p.wk]);
    const up=pts.map(p=>X(p.wk)+','+Y(P_(t,p.wk,p.hi))).join(' '), dn=pts.slice().reverse().map(p=>X(p.wk)+','+Y(P_(t,p.wk,p.lo))).join(' ');
    el('polygon',{points:up+' '+dn,fill:t.color,opacity:.16},g);
  }
  const order=T.slice().sort((a,b)=>(a.team===sel)-(b.team===sel));
  order.forEach(t=>{
    const on=t.team===sel, c=on?t.color:'#b9ad94', sw=on?3:1.2, op=sel&&!on?.55:.9;
    const lg=el('g',{opacity:op},g);
    let dAll;
    if(view==='wins'){
      const act=t.traj.filter(p=>p.actual!==undefined&&t.gpw[p.wk]), k=t.known;
      const dA=act.map((p,i)=>(i?'L':'M')+X(p.wk)+' '+Y(P_(t,p.wk,p.actual))).join('');
      const pr=t.traj.filter(p=>p.wk>=Math.max(k,1)&&t.gpw[p.wk]);
      const dP=pr.map((p,i)=>(i?'L':'M')+X(p.wk)+' '+Y(P_(t,p.wk,p.wk<=k?p.actual:p.mean))).join('');
      if(dA)el('path',{d:dA,fill:'none',stroke:c,'stroke-width':sw,'stroke-linejoin':'round'},lg);
      el('path',{d:dP,fill:'none',stroke:c,'stroke-width':sw,'stroke-dasharray':on?'6 4':'3 3'},lg);
      dAll=dA+dP.replace(/^M/,'L');
      if(on){const last=t.traj[17];const tx=el('text',{x:X(18)-2,y:Y(P_(t,18,last.mean))-8,'text-anchor':'end','font-size':12,'font-weight':600},lg);tx.style.fill=t.color;tx.textContent=t.name;}
    }else{
      let d='';t.cdf.forEach((p,n)=>{d+=(n?'L'+X(n)+' '+Y(t.cdf[n-1])+'L':'M')+X(n)+' '+Y(p);});
      el('path',{d:d,fill:'none',stroke:c,'stroke-width':sw},lg); dAll=d;
      if(on){const tx=el('text',{x:X(17)-2,y:Y(0.06),'text-anchor':'end','font-size':12,'font-weight':600},lg);tx.style.fill=t.color;tx.textContent=t.name;}
    }
    const hit=el('path',{d:dAll,class:'hit'},g);
    const ttl=el('title',{},hit); ttl.textContent=t.name;
    hit.addEventListener('click',()=>select(t.team));
  });
  legend();
}
function legend(){
  const L=document.getElementById('legend');
  L.innerHTML=view==='wins'
    ?'<span>&#9472;&#9472; winning percentage so far</span><span>- - - projected (average)</span><span>&middot;&middot;&middot; .500</span><span>shaded: 8 seasons in 10 land here (selected club)</span>'
    :'<span>each step: chance of finishing with that many wins or fewer</span>';
}
function card(){
  const C=document.getElementById('card');
  if(!sel){C.innerHTML='<b>Tap a line</b> or a row to follow one club.';C.style.borderLeftColor='var(--rust)';return}
  const t=BY[sel]; C.style.borderLeftColor=t.color;
  const rows=t.sched.map(s=>{const o=BY[s.opp].name, at=s.home?'vs':'at';
    if(s.res)return `<tr><td>Wk ${s.wk}</td><td>${at} ${o}</td><td class="num">${s.res} ${s.score}</td></tr>`;
    return `<tr><td>Wk ${s.wk}</td><td>${at} ${o}</td><td class="num">${pct(s.p)}<span class="pbar" style="width:${Math.round(s.p*40)}px"></span></td></tr>`}).join('');
  C.innerHTML=`<h3>${t.name}</h3>
  <div class="stats"><span>record <b>${rec(t)}</b></span><span>expected in August <b>${wf(t.prior_wins)}</b> wins</span>
  <span>projected <b>${wf(t.proj)}</b> wins (8 in 10: ${t.proj_lo}&ndash;${t.proj_hi})</span>
  <span>4 or fewer <b>${pct(t.p_le4)}</b></span><span>3 or fewer <b>${pct(t.p_le3)}</b></span><span>playoffs <b>${pct(t.p_po)}</b></span>
  <span>strength <b>${t.post_rating>0?'+':''}${t.post_rating.toFixed(1)}</b> pts (August ${t.prior_rating>0?'+':''}${t.prior_rating.toFixed(1)})</span></div>
  <table class="sched">${rows}</table>`;
}
function table(){
  const R=document.getElementById('rank');
  const s=T.slice().sort(sortBy==='pct'?(a,b)=>a.pct-b.pct||b.p_le4-a.p_le4:(a,b)=>b.slide-a.slide);
  R.innerHTML='<thead><tr><th>#</th><th>Club</th><th class="opt">Record</th><th>Proj. wins</th><th>&le;4 wins</th><th>vs Aug.</th><th class="opt">Playoffs</th></tr></thead><tbody>'+
    s.map((t,i)=>`<tr data-t="${t.team}" class="${t.team===sel?'sel':''}"><td class="num">${i+1}</td><td><i class="sw" style="background:${t.color}"></i>${t.name}</td><td class="num opt">${rec(t)}</td><td class="num">${wf(t.proj)} <small>(${t.proj_lo}&ndash;${t.proj_hi})</small></td><td class="num">${pct(t.p_le4)}</td><td class="num">${t.slide>0?'&minus;':'+'}${wf(Math.abs(t.slide))}</td><td class="num opt">${pct(t.p_po)}</td></tr>`).join('')+'</tbody>';
  R.querySelectorAll('tbody tr').forEach(tr=>tr.addEventListener('click',()=>select(tr.dataset.t)));
}
function select(t){sel=(sel===t&&t)?null:t;document.getElementById('pick').value=sel||'';draw();card();table();}
const P=document.getElementById('pick');
P.innerHTML='<option value="">Choose a club&hellip;</option>'+T.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(t=>`<option value="${t.team}">${t.name}</option>`).join('');
P.addEventListener('change',()=>{sel=P.value||null;draw();card();table();});
function seg(a,b,f){a.addEventListener('click',()=>{a.setAttribute('aria-pressed','true');b.setAttribute('aria-pressed','false');f();});}
const vw=document.getElementById('v-wins'),vc=document.getElementById('v-cdf');
seg(vw,vc,()=>{view='wins';draw();});seg(vc,vw,()=>{view='cdf';draw();});
const sp=document.getElementById('s-pct'),ss=document.getElementById('s-slide');
seg(sp,ss,()=>{sortBy='pct';table();});seg(ss,sp,()=>{sortBy='slide';table();});
sel=T.slice().sort((a,b)=>a.pct-b.pct)[0].team; P.value=sel;
draw();card();table();
let rz;addEventListener('resize',()=>{clearTimeout(rz);rz=setTimeout(draw,150);});
})();
"""


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--offline", action="store_true", help="use the cached schedule only")
    ap.add_argument("--dry-run", action="store_true", help="report, write nothing")
    ap.add_argument("--tau", type=float, default=None, help="override the fitted prior SD")
    ap.add_argument("--seed", type=int, default=1031)
    args = ap.parse_args()

    rows, src = load(args.offline)
    say(f"  schedule: {src}")
    m0, pre = preseason_prior()
    say(f"  prior: {pre['source']}; home field {m0[32]:+.2f}")

    tau_proxy, per = fit_tau(rows, range(2015, 2026))
    g26 = season(rows, SEASON)
    gap = float(np.sqrt(np.mean((solve_lines(weeks(g26, 1, 3))[:32] - m0[:32]) ** 2)))
    tau_fit = round(math.sqrt(tau_proxy ** 2 + gap ** 2), 1)
    tau = args.tau or tau_fit
    l26 = np.array([loglik(m0, t, [r for r in g26 if done(r)]) for t in TAUS])
    say(f"  prior SD: Weeks 1-3 proxy fit {tau_proxy} (2015-25, per season {per}); "
        f"proxy-vs-preseason gap {gap:.2f} -> {tau_fit}; 2026 alone prefers {TAUS[np.argmax(l26)]}"
        f" (log-lik at {tau_fit}: {np.interp(tau_fit, TAUS, l26) - l26.max():+.1f}); using {tau}")

    tau_bt, _ = fit_tau(rows, range(2015, 2023))
    bt = backtest(rows, tau_bt)
    say(f"\n  out of sample 2023-25, {bt['games']} games, Weeks 8-18 (prior SD {tau_bt}, fit 2015-22):")
    for k, v in bt["models"].items():
        say(f"    {k:<13} Brier {v['brier']:.4f}   favorite won {v['favorite_won']:.3f}")
    for b in bt["models"]["posterior"]["calibration"]:
        say(f"      posterior {b['bin']:>8}  n={b['n']:<4} said {b['predicted']:.2f}  won {b['actual']:.2f}")

    rng = np.random.default_rng(args.seed)
    teams, meta = run_season(rows, m0, tau, rng)
    say(f"\n  2026: {meta['played']} games played (all of Weeks 1-{meta['full_weeks']}, last {meta['last_date']}), "
        f"{meta['left']} left; home field posterior {meta['hfa_post']:+.2f} (sd {meta['hfa_post_sd']})")
    say(f"\n  {'club':<24}{'rec':>6}{'Aug':>6}{'proj':>6}{'80%':>8}{'<=4':>6}{'<=3':>6}{'fall':>6}{'PO':>6}{'str':>7}")
    srt = sorted(teams, key=lambda t: t["pct"])
    for t in srt:
        say(f"  {t['name']:<24}{rec(t):>6}{t['prior_wins']:>6.1f}{t['proj']:>6.1f}"
            f"{t['proj_lo']:>4.0f}-{t['proj_hi']:<3.0f}{pct(t['p_le4']):>6}{pct(t['p_le3']):>6}"
            f"{t['slide']:>6.1f}{pct(t['p_po']):>6}{t['post_rating']:>7.1f}")

    data = {"generated": dt.date.today().isoformat(), "season": SEASON, "tau": tau,
            "tau_note": {"proxy_fit_2015_2025": tau_proxy, "per_season": per,
                         "proxy_gap_2026": round(gap, 2), "fit": tau_fit,
                         "season_2026_alone": float(TAUS[np.argmax(l26)])},
            "sigma": SIGMA, "nsims": NSIMS, "prior_source": pre["source"],
            "meta": meta, "backtest": bt, "teams": teams}
    if args.dry_run:
        say("\n  dry run, nothing written")
        return
    OUT_JSON.write_text(json.dumps(data, indent=1))
    OUT_HTML.write_text(build_page(data))
    say(f"\n  wrote {OUT_JSON.relative_to(ROOT)} and {OUT_HTML.relative_to(ROOT)}")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "add_emblem.py"), str(OUT_HTML)], check=False)


if __name__ == "__main__":
    main()
