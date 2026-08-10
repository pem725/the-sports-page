#!/usr/bin/env python3
"""
CFB Pre-Season Simulation engine (The Sports Page tentpole, late August each year).

Two modes, one prior (SP+ team-strength ratings from CollegeFootballData):

  --mode bayes  (DEFAULT, the one to publish)
    A Bayesian Monte Carlo. Each team's TRUE strength is uncertain; SP+ is our best
    estimate, not gospel. So each iteration DRAWS a strength for every team from its
    prior, theta_i ~ Normal(SP+_i, TAU), then plays the full regular season with
    game-level noise, builds the 12-team Playoff, and simulates the bracket to a
    champion. Thousands of iterations give POSTERIOR-style distributions: a win total
    with a credible interval (not a false-precise 10.7), and honest probabilities of
    making the Playoff, winning the league, and winning it all. This is the "report a
    range, not a decimal" philosophy baked into the method (see feedback: significant
    digits, at most 2; concepts communicating-uncertainty No. 18, information No. 20).

  --mode jnd
    A single deterministic pass with the just-noticeable-difference rule: a game is a
    CONFIDENT CALL only if the favorite clears P=0.75 (the threshold Issue #022 fit to
    ranked-matchup data); everything inside [0.25, 0.75] is an explicit COIN FLIP. Good
    for the "how many games can we even call?" honesty line.

Run the last weekend of August with that year's posted SP+. Smoke-test on a past year:

  CFBD_KEY=... python3 scripts/cfb_preseason_sim.py --year 2025 --mode bayes
  CFBD_KEY=... python3 scripts/cfb_preseason_sim.py --year 2026            # once SP+ 2026 posts
"""
import os, sys, json, math, argparse, random, urllib.request
from statistics import NormalDist
from collections import defaultdict

API = "https://apinext.collegefootballdata.com"
KEY = os.environ.get("CFBD_KEY")
SIGMA = 13.5          # single-game margin noise, points (standard CFB value)
HFA = 2.5             # home-field advantage, points
TAU = 6.0             # prior SD on true team strength around its SP+ estimate (preseason uncertainty)
JND_P = 0.75          # confident-call boundary for --mode jnd
INDEP = {"FBS Independents", None, ""}
P4 = {"ACC", "Big Ten", "Big 12", "SEC"}   # power conferences; the rest are Group-of-5
MIN_CONF_TEAMS = 4    # a realignment remnant (2025 Pac-12 had 2 teams) can't award an auto-bid
ATLARGE_W = 8.0       # SP+ points worth one win when ranking at-large candidates
NORM = NormalDist(0, SIGMA)


def fetch(path):
    if not KEY:
        sys.exit("ERROR: set CFBD_KEY env var")
    req = urllib.request.Request(API + path,
                                 headers={"Authorization": f"Bearer {KEY}", "Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=90))


PRIOR_LABEL = "SP+"      # set by load(); reported so the issue can disclose it


def _sd(vals):
    m = sum(vals) / len(vals)
    return (sum((v - m) ** 2 for v in vals) / len(vals)) ** 0.5


def load(year):
    """Load the team-strength prior, preferring SP+ and falling back to FPI.

    SP+ is what TAU/SIGMA were tuned against, so it is always tried first. But
    SP+ posts late (2026 was still empty on Aug 9 while FPI already had all 138
    teams), and a scheduled routine that dies on a missing prior is worse than
    one that substitutes a comparable rating and says so.

    FPI measures the same quantity as SP+ -- points above an average team -- but
    on a slightly tighter spread. It is rescaled to the most recent season's SP+
    standard deviation so the engine's tuned constants keep their meaning
    instead of silently changing it.
    """
    global PRIOR_LABEL
    ratings = {x["team"]: x["rating"] for x in fetch(f"/ratings/sp?year={year}")
               if isinstance(x.get("rating"), (int, float)) and x.get("team")}
    PRIOR_LABEL = "SP+"

    if not ratings:
        fpi = {x["team"]: float(x["fpi"]) for x in fetch(f"/ratings/fpi?year={year}")
               if x.get("fpi") is not None and x.get("team")}
        if not fpi:
            sys.exit(f"Neither SP+ nor FPI is posted for {year}. No prior available.")
        # calibrate against the newest season that actually has SP+
        target = None
        for back in range(1, 4):
            prev = [x["rating"] for x in fetch(f"/ratings/sp?year={year-back}")
                    if isinstance(x.get("rating"), (int, float))]
            if len(prev) > 50:
                target = _sd(prev)
                ref_year = year - back
                break
        vals = list(fpi.values())
        mean, sd = sum(vals) / len(vals), _sd(vals)
        if target and sd > 0:
            k = target / sd
            ratings = {t: (v - mean) * k for t, v in fpi.items()}
            PRIOR_LABEL = f"ESPN FPI, rescaled x{k:.2f} to {ref_year} SP+ spread"
        else:
            ratings = {t: v - mean for t, v in fpi.items()}
            PRIOR_LABEL = "ESPN FPI (uncalibrated -- no SP+ season found to scale against)"
        print(f"  NOTE: SP+ not posted for {year}; using {PRIOR_LABEL}.", file=sys.stderr)

    conf = {t.get("school"): t.get("conference") for t in fetch(f"/teams/fbs?year={year}")}
    games = fetch(f"/games?year={year}&seasonType=regular")
    rated = [(g["homeTeam"], g["awayTeam"], bool(g.get("neutralSite")))
             for g in games if g.get("homeTeam") in ratings and g.get("awayTeam") in ratings]
    if not rated:
        sys.exit(f"No {year} games matched the rating table -- schedule may not be posted yet.")
    return ratings, conf, rated


# ---------- Bayesian Monte Carlo ----------

def play(theta, a, b, hfa_a):
    """Return winner of a vs b; hfa_a is the point edge applied to a (0 at neutral)."""
    return a if (theta[a] - theta[b] + hfa_a + random.gauss(0, SIGMA)) > 0 else b


def conference_champions(wins, theta, conf):
    """Decide each conference's champion by playing its title game.

    The top two finishers meet at a neutral site, so the regular-season leader
    is a favourite and not a certainty -- which is how the bid actually works.
    Conferences below MIN_CONF_TEAMS are skipped entirely.
    """
    standings = defaultdict(list)
    for t in sorted(wins, key=lambda t: (-wins[t], -theta[t])):
        c = conf.get(t)
        if c and c not in INDEP:
            standings[c].append(t)
    champs = {}
    for c, ts in standings.items():
        if len(ts) < MIN_CONF_TEAMS:
            continue
        champs[c] = ts[0] if len(ts) == 1 else play(theta, ts[0], ts[1], 0)
    return champs


def build_field(wins, theta, champs_by_conf):
    """champs_by_conf comes from conference_champions() -- resolved ONCE per
    iteration by the caller, so the champion seeded here is the same one the
    conference-title tally counts."""
    ranked = sorted(champs_by_conf.items(), key=lambda kv: -theta[kv[1]])
    # Five auto-bids: the four best champions, plus the highest-rated Group-of-5
    # champion, which the format guarantees the non-power conferences.
    top4 = [t for _, t in ranked[:4]]
    g5 = next((t for c, t in ranked if c not in P4 and t not in top4), None)
    champs = top4 + ([g5] if g5 else [])
    cset = set(champs)
    rank = lambda t: -(wins[t] + theta[t] / ATLARGE_W)
    at_large = sorted((t for t in wins if t not in cset), key=rank)[:12 - len(champs)]
    seeds = sorted(champs, key=lambda t: -theta[t]) + sorted(at_large, key=rank)
    return seeds  # index 0..11 == seeds 1..12


def sim_bracket(seeds, theta):
    """Fixed 12-team CFP bracket. Byes to 1-4; round 1 hosted by higher seed (HFA); rest neutral."""
    s = seeds  # s[0]=seed1 ... s[11]=seed12
    # first round at higher seed's home
    w8v9  = play(theta, s[7], s[8], HFA)
    w5v12 = play(theta, s[4], s[11], HFA)
    w6v11 = play(theta, s[5], s[10], HFA)
    w7v10 = play(theta, s[6], s[9], HFA)
    # quarterfinals (neutral)
    qf1 = play(theta, s[0], w8v9, 0)
    qf2 = play(theta, s[3], w5v12, 0)
    qf3 = play(theta, s[2], w6v11, 0)
    qf4 = play(theta, s[1], w7v10, 0)
    # semis + final (neutral)
    sf1 = play(theta, qf1, qf2, 0)
    sf2 = play(theta, qf3, qf4, 0)
    return play(theta, sf1, sf2, 0)


def simulate_bayes(year, n_iter, seed):
    ratings, conf, rated = load(year)
    random.seed(seed)
    teams = list(ratings)
    win_samples = defaultdict(list)
    playoff = defaultdict(int)
    champ = defaultdict(int)
    confchamp = defaultdict(int)
    for _ in range(n_iter):
        theta = {t: random.gauss(ratings[t], TAU) for t in teams}   # draw true strengths
        wins = dict.fromkeys(teams, 0)
        for h, a, neutral in rated:
            w = play(theta, h, a, 0 if neutral else HFA)
            wins[w] += 1
        for t in teams:
            win_samples[t].append(wins[t])
        # resolve the conference title games once, then use that same result for
        # both the Playoff field and the conference-champion tally
        champs_by_conf = conference_champions(wins, theta, conf)
        seeds = build_field(wins, theta, champs_by_conf)
        for t in seeds:
            playoff[t] += 1
        for t in champs_by_conf.values():
            confchamp[t] += 1
        champ[sim_bracket(seeds, theta)] += 1
    return dict(year=year, n=n_iter, ratings=ratings, conf=conf,
                win_samples=win_samples, playoff=playoff, champ=champ, confchamp=confchamp,
                games_per=lambda t: sum(1 for h, a, _ in rated if t in (h, a)))


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))]


def report_bayes(r):
    y, N = r["year"], r["n"]
    ratings = r["ratings"]
    exp = {t: sum(v) / N for t, v in r["win_samples"].items()}
    order = sorted(exp, key=lambda t: (-r["champ"][t], -r["playoff"][t], -exp[t]))
    print(f"\n{'='*72}\n  CFB PRE-SEASON SIMULATION (Bayesian)  ·  {y}  ·  The Sports Page engine\n{'='*72}")
    print(f"  Prior: {PRIOR_LABEL} ({len(ratings)} FBS teams), "
          f"true strength ~ Normal(prior, tau={TAU:.0f}).")
    print(f"  {N:,} season simulations · game noise SD ~ {SIGMA:.0f} pts · HFA {HFA:.1f} pts.")
    print(f"  Reported as ranges, not point estimates -- 2 significant figures.\n")
    print(f"  {'TEAM':<17}{'WINS (80% range)':<20}{'PLAYOFF':>9}{'TITLE':>8}")
    for t in order[:16]:
        ws = r["win_samples"][t]
        lo, hi, md = pct(ws, 10), pct(ws, 90), pct(ws, 50)
        po = 100 * r["playoff"][t] / N
        ti = 100 * r["champ"][t] / N
        print(f"  {t:<17}{'~'+str(md)+'  ('+str(lo)+'-'+str(hi)+')':<20}{po:>7.0f}%{ti:>7.0f}%")
    top = order[0]
    print(f"\n  TITLE PICK: {top}  ~{100*r['champ'][top]/N:.0f}% to win it all "
          f"(the model's favorite, but far from a lock).")
    print(f"  A reminder in the newsletter's own voice: a favorite at ~{100*r['champ'][top]/N:.0f}% "
          f"means the field is more likely than not to win instead.\n")


# ---------- Deterministic JND pass ----------

def simulate_jnd(year):
    ratings, conf, rated = load(year)
    exp = dict.fromkeys(ratings, 0.0)
    n_games = n_calls = n_flips = 0
    flips = []
    for h, a, neutral in rated:
        margin = (ratings[h] - ratings[a]) + (0.0 if neutral else HFA)
        p = NORM.cdf(margin)
        exp[h] += p; exp[a] += (1 - p); n_games += 1
        if max(p, 1 - p) >= JND_P:
            n_calls += 1
        else:
            n_flips += 1
            if len(flips) < 8:
                fav, dog = (h, a) if p >= .5 else (a, h)
                flips.append((fav, dog, round(max(p, 1 - p), 2)))
    return ratings, exp, n_games, n_calls, n_flips, flips


def report_jnd(year):
    ratings, exp, n_games, n_calls, n_flips, flips = simulate_jnd(year)
    print(f"\n  JND honesty pass ({year}): of {n_games} rated games, {n_calls} are confident "
          f"calls and {n_flips} ({100*n_flips/n_games:.0f}%) are coin flips.")
    print("  Sample games the model refuses to call:")
    for fav, dog, p in flips:
        print(f"    {fav} vs {dog}  (favorite only {p*100:.0f}%)")
    print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--mode", choices=["bayes", "jnd"], default="bayes")
    ap.add_argument("--iters", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=725)   # fixed for reproducibility
    a = ap.parse_args()
    if a.mode == "bayes":
        report_bayes(simulate_bayes(a.year, a.iters, a.seed))
        report_jnd(a.year)
    else:
        report_jnd(a.year)
