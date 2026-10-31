#!/usr/bin/env python3
"""Will I outlive Woody Johnson's ownership of the Jets?

The question (a Jets fan's): fans of bad teams treat an old owner's mortality as
the exit.  Is it?  Two parts:
  1. When an NFL controlling owner dies, does the team leave the family?  Every
     change of controlling ownership 1980-today, by cause, from
     data/ownership/transitions.csv (hand-built, two sources per row).
  2. How long will the owner live, and how long will the fan?  SSA period life
     table, national and wealth-adjusted.  Then combine: the chance the TEAM
     leaves the family within the fan's lifetime.

Sources
  data/ownership/transitions.csv     one row per change; sources in each row
  data/ownership/current_owners.csv  the 32 current controlling owners
  SSA Actuarial Life Table (table4c6: the 2023 period life table as used in the
    2026 Trustees Report).  ssa.gov refuses scripted downloads (HTTP 403), so it
    is fetched from the Internet Archive's copy of the same page (snapshot
    2026-10-25) and cached under ~/.cache/sports-page/ownership/.
  Chetty et al. 2016, JAMA 315(16):1750-66, doi:10.1001/jama.2016.4226:
    men in the top 1% of household income, at age 40, expect to live to 87.3
    (bottom 1%: 72.7; gap 14.6).  87.3 is from the authors' slides and Fortune
    (2016-04-11); the 14.6 gap is in the abstract.
  NO web-search numbers, no CollegeFootballData, no secrets.

Method
  * Owner survival: SSA male q(x), starting from the owner's EXACT age (the
    first partial year gets (1-q)^(fraction left)).  Wealth adjustment: one
    proportional-hazard multiplier HR on every age (1-q -> (1-q)^HR), chosen so
    a 40-year-old man's life expectancy on the SSA table equals Chetty's top-1%
    figure, 87.3.  Simple and stated, not a model of the rich.
  * Fan: male, national table, ages 30/45/60.  Independent lifetimes.
  * History: a "death event" = a controlling owner who died in control, 1980 on.
    Outcome = sold to outsiders (by estate, trust, or the heirs) and how long
    after the death, or still in the family today (censored).
  * Team-leaves-family model, three pieces, all estimated from the history:
      - while the owner lives: sale at constant yearly rate LAMBDA = sales to
        outsiders by living owners / franchise-years at risk, 1980-today;
      - in the W=5 years after a death: sold with probability P_W (deaths with
        a full five years of follow-up), at a delay drawn from the observed
        delays;
      - after that, back to LAMBDA (heirs are owners too: Randy Lerner sold
        ten years after his father died).
    Uncertainty: P_W ~ Beta(k+1/2, n-k+1/2), LAMBDA ~ Gamma(m+1/2)/exposure
    (Jeffreys), propagated by simulation; 90% intervals.

Traps (reported in analysis.txt)
  * "The estate sold" is often the owner's own decision: Hess's and Cooke's
    wills ordered a sale, Allen's will directed one.  A death that sells is
    usually a death that was planned to sell.  Nothing like that is reported
    for the Johnsons.
  * Control can leave before death: Bowlen's trust took over in 2014 (he died
    2019); Dean Spanos ran the Chargers from 1994 (Alex died 2018).  Both
    counted as deaths, with a sensitivity check dropping them.
  * Giants are 50/50: two 2005 deaths, each half a team; the 1991 sale of Tim
    Mara's half counts as half a sale.  Vikings 1984-98 had no single
    controlling owner; their sales still count as sales.
  * The SSA period table is a snapshot of 2023 mortality, not a cohort
    forecast; Chetty's 87.3 is 2001-14 data, race-adjusted, and leans on
    Gompertz extrapolation past 76.  The wealth multiplier is an order of
    magnitude, not a measurement of any person.
  * Two significant digits throughout.

Usage:
  python3 scripts/owner_succession.py            # fetch life table if needed
  python3 scripts/owner_succession.py --offline  # cache only
  options: --as-of 2026-10-31 --sims 4000

Outputs: data/ownership/analysis.txt
"""
import argparse, csv, datetime as dt, gzip, html, math, pathlib, re, sys, urllib.request
from collections import Counter

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "ownership"
CACHE = pathlib.Path.home() / ".cache" / "sports-page" / "ownership"
UA = "TheSportsPage-research/1.0 (owner study; https://thesportspage.net; ideas@thesportspage.net)"
SSA_URL = ("https://web.archive.org/web/20261025061021id_/"
           "https://www.ssa.gov/oact/STATS/table4c6.html")
WOODY_DOB = dt.date(1947, 4, 12)     # Wikipedia/Wikidata; ages in CBS 2017-06-23 (70)
                                     # and ESPN 2025-01-06 (77) bracket it to Jan-Jun 1947
CHETTY_TOP1_MEN_AT40 = 87.3
W = 5                                # post-death window, years
FAN_AGES = (30, 45, 60)
OFFLINE = False
LOG = []

def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.append(s)

def sig2(x):
    """At most two significant digits."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    if x == 0:
        return "0"
    d = 2 - int(math.floor(math.log10(abs(x)))) - 1
    v = round(x, d)
    return ("%d" % v) if d <= 0 else ("%.*f" % (d, v))

def pct(p):
    return sig2(100 * p) + "%"

# ------------------------------------------------------------------ life table
def fetch_ssa():
    f = CACHE / "table4c6.html"
    if not (f.exists() and f.stat().st_size > 5000):
        if OFFLINE:
            raise SystemExit("offline mode and %s is not cached" % f)
        CACHE.mkdir(parents=True, exist_ok=True)
        print("  fetching", SSA_URL, file=sys.stderr)
        req = urllib.request.Request(SSA_URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            b = r.read()
        if b[:2] == b"\x1f\x8b":
            b = gzip.decompress(b)
        f.write_bytes(b)
    t = f.read_text(encoding="utf-8", errors="replace")
    if "Access Denied" in t[:500]:
        raise SystemExit("cached life table is an error page; delete %s" % f)
    m = re.search(r"the (\d{4}) period life table.*?as used in the (\d{4}) Trustees", t, re.S)
    label = "SSA %s period life table (%s Trustees Report)" % m.groups() if m else "SSA period life table"
    q = {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S | re.I):
        c = [html.unescape(re.sub(r"<[^>]*>", "", x)).strip().replace(",", "")
             for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S | re.I)]
        if len(c) == 7 and c[0].isdigit():
            q[int(c[0])] = (float(c[1]), float(c[3]))   # male q(x), male e(x)
    if len(q) != 120 or abs(q[0][1] - 70) > 15:
        raise SystemExit("life table did not parse (%d rows)" % len(q))
    return q, label

def survival(q, age, hr=1.0, years=125):
    """S(t) at t = 0,1,2,... years from EXACT age `age` (float)."""
    a0 = int(age); frac = age - a0
    S = [1.0]
    s = (1 - q[a0][0]) ** (hr * (1 - frac))
    S.append(s)                      # end of the current age-year (t = 1-frac)
    a = a0 + 1
    while a < 120 and len(S) < years:
        s *= (1 - q[a][0]) ** hr
        S.append(s); a += 1
    S.append(0.0)
    # times: 0, 1-frac, 2-frac, ...
    T = [0.0] + [k + 1 - frac for k in range(len(S) - 1)]
    return np.array(T), np.array(S)

def S_at(T, S, t):
    return float(np.interp(t, T, S))

def life_exp(q, age, hr=1.0):
    T, S = survival(q, age, hr)
    return float(np.trapezoid(S, T)) if hasattr(np, "trapezoid") else float(np.trapz(S, T))

def median_left(T, S):
    i = int(np.argmax(S < 0.5))
    return float(T[i - 1] + (S[i - 1] - 0.5) / (S[i - 1] - S[i]) * (T[i] - T[i - 1]))

def solve_hr(q, target_e40):
    lo, hi = 0.05, 1.0
    for _ in range(80):
        m = (lo + hi) / 2
        if 40 + life_exp(q, 40, m) > target_e40: lo = m
        else: hi = m
    return (lo + hi) / 2

def sample_lifetimes(rng, T, S, n):
    """Inverse-CDF draws of remaining life (years), linear within intervals."""
    u = rng.random(n)
    # S decreasing; find t with S(t) = u
    return np.interp(-u, -S, T)

def p_outlive(T_o, S_o, T_f, S_f):
    """P(fan outlives owner) for independent lifetimes, by numeric integration."""
    t = np.linspace(0, 100, 20001)
    So = np.interp(t, T_o, S_o); Sf = np.interp(t, T_f, S_f)
    fo = -np.gradient(So, t)
    return float(np.sum(fo * Sf) * (t[1] - t[0]))

# ------------------------------------------------------------------ history
def load_history(as_of):
    rows = list(csv.DictReader(open(OUT / "transitions.csv", newline="")))
    year_now = as_of.year + (as_of.timetuple().tm_yday - 1) / 365.25
    ev = {}
    for r in rows:
        k = r["death_event"]
        if not k:
            continue
        e = ev.setdefault(k, {"team": r["team"], "death_year": None, "sold_after": None,
                              "cause_rows": []})
        e["cause_rows"].append(r["cause"])
        dy = int(k.split()[-1])
        if r["date"] and r["cause"] == "b":
            d = dt.date.fromisoformat(r["date"])
            e["death_year"] = d.year + (d.timetuple().tm_yday - 1) / 365.25
        if r["cause"] == "c" and r["years_after_death"]:
            e["sold_after"] = float(r["years_after_death"])
        if e["death_year"] is None:
            e["death_year"] = dy + 0.5
    for k, e in ev.items():
        e["followup"] = year_now - e["death_year"]
        e["half"] = k in ("Wellington Mara 2005", "Bob Tisch 2005")
        e["control_left_earlier"] = k in ("Pat Bowlen 2019", "Alex Spanos 2018")
    return rows, ev, year_now

FRANCHISE_START = {"CAR": 1993.8, "JAX": 1993.9, "CLE": 1998.7, "HOU": 1999.8}
TEAMS = ("ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET HOU IND JAX KC LV LAC LAR "
         "MIA MIN NE NO NYG NYJ PHI PIT SF SEA TB TEN WAS").split()   # GB excluded

def alive_sale_rate(rows, ev, year_now, drop=()):
    sales = 0.0
    for r in rows:
        if r["cause"] == "a":
            sales += 0.5 if (r["team"] == "NYG" and r["year"] == "1991") else 1.0
    late = [e for e in ev.values() if e["sold_after"] is not None and e["sold_after"] > W]
    sales += len(late)
    expo = sum(year_now - max(1980.0, FRANCHISE_START.get(t, 1980.0)) for t in TEAMS)
    # time spent inside a post-death window is covered by P_W, not by LAMBDA
    for k, e in ev.items():
        if k in drop:
            continue
        span = min(W, e["followup"], e["sold_after"] if e["sold_after"] is not None else 99)
        expo -= span * (0.5 if e["half"] else 1.0)
    return sales, expo

def window_rate(ev, drop=()):
    k = n = 0.0
    delays = []
    for key, e in ev.items():
        if key in drop:
            continue
        wgt = 0.5 if e["half"] else 1.0
        if e["sold_after"] is not None and e["sold_after"] <= W:
            k += wgt; n += wgt; delays.append(e["sold_after"])
        elif e["followup"] >= W:
            n += wgt
    return k, n, delays

# ------------------------------------------------------------------ simulation
def simulate(rng, To, So, Tf, Sf, pw, lam, delays, n):
    """Return P(team leaves family before the fan dies) for fixed parameters."""
    owner = sample_lifetimes(rng, To, So, n)
    fan = sample_lifetimes(rng, Tf, Sf, n)
    alive_sale = rng.exponential(1 / lam, n)
    leave = np.where(alive_sale < owner, alive_sale, np.inf)
    dead = ~np.isfinite(leave)
    sold_w = rng.random(n) < pw
    d = rng.choice(np.asarray(delays), n)
    later = owner + W + rng.exponential(1 / lam, n)
    after = np.where(sold_w, owner + d, later)
    leave = np.where(dead, after, leave)
    return float(np.mean(leave < fan)), float(np.mean(owner < fan))

def main():
    global OFFLINE
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--offline", action="store_true", help="read only the cache; never download")
    ap.add_argument("--as-of", default="2026-10-31")
    ap.add_argument("--sims", type=int, default=4000, help="parameter draws for intervals")
    a = ap.parse_args()
    OFFLINE = a.offline
    as_of = dt.date.fromisoformat(a.as_of)
    rng = np.random.default_rng(20261031)

    q, label = fetch_ssa()
    say("OWNER SUCCESSION -- will the fan outlive the owner, and does it matter?")
    say("as of", as_of.isoformat(), "| life table:", label)
    say("")

    # ---------------- history
    rows, ev, year_now = load_history(as_of)
    causes = Counter(r["cause"] for r in rows)
    say("1. CHANGES OF CONTROL, 1980-%d (data/ownership/transitions.csv, %d rows)" % (as_of.year, len(rows)))
    say("   rows by cause: a sale while alive %d | b died, stayed in family %d | "
        "c died, estate/heirs sold %d | d other %d | not a change %d"
        % (causes["a"], causes["b"], causes["c"], causes["d"], causes["n"]))
    unconf = [r for r in rows if not r["confirmed"].startswith("yes")]
    say("   rows not fully two-source confirmed: %d (%s)" % (
        len(unconf), ", ".join("%s %s" % (r["team"], r["year"]) for r in unconf)))
    say("")
    n_d = len(ev)
    sold = sorted(((e["sold_after"], k) for k, e in ev.items() if e["sold_after"] is not None))
    stayed = [k for k, e in ev.items() if e["sold_after"] is None]
    say("2. OWNERS WHO DIED IN CONTROL SINCE 1980: %d" % n_d)
    say("   still in the family today: %d of %d" % (len(stayed), n_d))
    say("   sold to outsiders eventually: %d of %d" % (len(sold), n_d))
    for yrs, k in sold:
        say("     %-24s sold %s years after the death" % (k, sig2(yrs) if yrs >= 1 else "%.1f" % yrs))
    say("   sold within 1 year: %d   within 5 years: %d   median delay among sales: %s years"
        % (sum(1 for y, _ in sold if y <= 1), sum(1 for y, _ in sold if y <= 5),
           sig2(float(np.median([y for y, _ in sold])))))
    say("   stayed:", ", ".join(sorted(stayed, key=lambda s: s[-4:])))
    k, n, delays = window_rate(ev)
    say("   P(sold within %d years | death), deaths with %d+ years of follow-up: %s of %s = %s"
        % (W, W, sig2(k), sig2(n), pct(k / n)))
    drop = ("Pat Bowlen 2019", "Alex Spanos 2018")
    k2, n2, _ = window_rate(ev, drop)
    say("     sensitivity, dropping Bowlen and Spanos (control left before death): %s" % pct(k2 / n2))
    m, expo = alive_sale_rate(rows, ev, year_now)
    lam = m / expo
    say("   sales to outsiders by LIVING owners (incl. heirs selling >%d yrs after a death): %s"
        " over %s franchise-years = %s a year" % (W, sig2(m), sig2(expo), pct(lam)))
    tot_sales = causes["a"] + len(sold)
    say("   all sales to outsiders since 1980: %d; %d of them followed an owner's death"
        % (tot_sales, len(sold)))
    say("   how %d ends of a controlling tenure happened: sale while alive %d, death %d, "
        "handed to family while alive %d" % (causes["a"] + n_d + causes["d"], causes["a"], n_d, causes["d"]))
    say("")

    # ---------------- current owners
    cur = list(csv.DictReader(open(OUT / "current_owners.csv", newline="")))
    acq = Counter(r["acquired"] for r in cur)
    say("3. CURRENT CONTROLLING OWNERS (%d teams)" % len(cur))
    say("   bought %d | inherited on a death %d | handed over by family while alive %d | public %d | founders %d"
        % (acq["bought"], acq["inherited"], acq["family_transfer"], acq["public"], acq["founded"]))
    say("   family successors (inherited + family transfer): %d of %d privately held"
        % (acq["inherited"] + acq["family_transfer"], len(cur) - acq["public"]))
    ages = sorted(((as_of.year - int(r["birth_year"]), r["team"], r["controlling_owner"])
                   for r in cur if r["birth_year"]), reverse=True)
    say("   oldest: " + "; ".join("%s %s (%d)" % (t, o.split(" (")[0], g) for g, t, o in ages[:8]))
    gm = [r for r in cur if r["owner_gm"] == "yes"]
    say("   owner is also de facto GM: " + "; ".join("%s %s %s" % (r["team"], r["controlling_owner"], r["owner_gm_years"]) for r in gm))
    say("")

    # ---------------- life table
    age = (as_of - WOODY_DOB).days / 365.2425
    hr = solve_hr(q, CHETTY_TOP1_MEN_AT40)
    say("4. THE OWNER'S CLOCK -- a man aged %.1f (Woody Johnson, b. %s)" % (age, WOODY_DOB))
    say("   wealth adjustment: hazard x %s at every age reproduces Chetty's top-1%% "
        "life expectancy at 40 (%.1f; SSA table gives %s)"
        % (sig2(hr), CHETTY_TOP1_MEN_AT40, sig2(40 + life_exp(q, 40))))
    tabs = {}
    for name, h in (("national", 1.0), ("wealth-adjusted", hr)):
        T, S = survival(q, age, h)
        tabs[name] = (T, S)
        say("   %-16s median years left %s | alive in 5 yrs %s, 10 yrs %s, 15 yrs %s | expectancy %s"
            % (name, sig2(median_left(T, S)), pct(S_at(T, S, 5)), pct(S_at(T, S, 10)),
               pct(S_at(T, S, 15)), sig2(life_exp(q, age, h))))
    say("")

    # ---------------- combine
    say("5. THE FAN (male, national table) vs THE OWNER and vs THE FAMILY")
    say("   model: owner sells while alive at %s/yr; after death, P(sold within %d yrs) = %s at "
        "observed delays; then %s/yr again. 90%% intervals from parameter uncertainty."
        % (pct(lam), W, pct(k / n), pct(lam)))
    draws_pw = rng.beta(k + 0.5, n - k + 0.5, a.sims)
    draws_lam = rng.gamma(m + 0.5, 1.0, a.sims) / expo
    for name, (To, So) in tabs.items():
        say("   owner table: %s" % name)
        for fa in FAN_AGES:
            Tf, Sf = survival(q, fa)
            p_out = p_outlive(To, So, Tf, Sf)
            p_leave, _ = simulate(rng, To, So, Tf, Sf, k / n, lam, delays, 400000)
            sims = np.array([simulate(rng, To, So, Tf, Sf, pw, lm, delays, 2000)[0]
                             for pw, lm in zip(draws_pw[:a.sims], draws_lam[:a.sims])])
            lo, hi = np.percentile(sims, [5, 95])
            naive = p_out * (k / n)
            say("     fan %d: outlives the owner %s | naive P(outlive) x P(sold<=5y) = %s | "
                "team leaves the family in his lifetime %s (90%% %s-%s)"
                % (fa, pct(p_out), pct(naive), pct(p_leave), pct(lo), pct(hi)))
    say("")
    say("Assumptions: independent lifetimes; the fan is male (a woman lives longer, so higher);")
    say("history 1980-today is the base rate for the Johnsons, for whom no sale plan,")
    say("will directive or sale process is reported; constant sale rate by living owners;")
    say("SSA 2023 period mortality, not a cohort projection; the wealth multiplier is a")
    say("single proportional hazard fitted at age 40.")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "analysis.txt").write_text("\n".join(LOG) + "\n")

if __name__ == "__main__":
    main()
