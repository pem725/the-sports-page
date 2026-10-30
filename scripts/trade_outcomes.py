#!/usr/bin/env python3
"""Do blockbuster trades pan out?  (Gene's question: MLB and the NFL.)

The question, in two parts:
  1. Did the team that got the star get what it paid for?  The star's value FOR
     THE NEW TEAM over the next three seasons (shorter if he left), against what
     his previous three seasons predicted.
  2. Who won the trade?  Everything each side received, valued by what it
     produced for the team that received it, over the same window.

Sources, and only these (public downloads, cached under
~/.cache/sports-page/trades/, fetched once; --offline reads only the cache):
  MLB  Retrosheet transaction database, tranDB.zip (trades = type "T"/"Tp";
       one trade = all rows sharing a transaction id).  It ends with the 2021
       season (a handful of early-2022 rows), so trades run 1980-2021.
       Baseball-Reference war_daily_bat.txt + war_daily_pitch.txt: bWAR per
       player-season-team stint.  Total bWAR = batting WAR + pitching WAR.
       Chadwick register (people-*.csv) maps Retrosheet ids to B-R ids.
  NFL  nflverse trades.csv (2002 on; one row per asset per direction; a pick
       row names the player eventually drafted with it), nflverse
       pfr_rosters.csv (Pro Football Reference Approximate Value, AV, per
       player-TEAM-season; rows run to 2022 but AV is blank
       for 2022, so 2002-2021), draft_picks.csv (who drafted whom),
       games.csv (kickoff dates and team records).
  NO CollegeFootballData calls, no secrets, no web-search numbers.

Method
  * Effective season S.  MLB: Oct-Dec trade -> S = next year (offseason);
    Jan-Mar -> S = that year (offseason); Apr-Sep -> in-season S.  "Deadline"
    = July or August.  NFL: in-season if after that season's first regular-
    season kickoff, else offseason S = calendar year.
  * Prior = player's total value (all teams) in S-3..S-1.  Window = S..S+2
    (sensitivity: S..S+5), counting only value produced for the RECEIVING team,
    and for in-season trades only the part of season S after the trade (B-R and
    PFR both split a season by team).  A player with no row counts 0.
  * Expected value = prior per season x seasons in the window, with strike /
    pandemic seasons weighted by games (1981 .66, 1994 .71, 1995 .89, 2020 .37)
    and an in-season trade's first season pro-rated by days remaining.
  * Blockbuster, MLB: some player sent had >= 8 bWAR in S-3..S-1 (also 6, 12).
    Blockbuster, NFL: a veteran with >= 30 AV over S-3..S-1 (about 10 a
    season, the level of a Pro Bowl-type starter; also 24, 36), OR any
    first-round pick changing hands.  NFL veteran priors need 2002 data, so the
    NFL window is trades with S = 2005-2019 (AV ends 2021).
  * Margin for the star-getting team A = value A received (for A) minus value
    of everything A sent away (for whoever received it).  "Even" = within 2 WAR
    (MLB) or 5 AV (NFL, about most of one starter's season); both varied.
  * Picks are valued by the player drafted with them, for the team that drafted
    him.  If the pick was flipped again, that is still the asset's value (and is
    flagged); unresolved picks (never used / beyond the data) count 0.
  * Regression baseline: EVERY player (traded or not) clearing the same prior
    bar, value over the next three seasons on any team / expected, by age band.
    That is how much decline the past alone predicts.

Traps handled (and reported in analysis.txt)
  * Survivorship: every trade over the bar, not the famous ones.
  * Regression to the mean: the baseline above.
  * Rentals: deadline deals are split out; a two-month rental cannot be judged
    on three seasons.
  * Prospects: a 6-season window as a sensitivity check.
  * Retrosheet names minor leaguers by string, not id.  Those who reached the
    majors later are matched to the register by name when the match is unique;
    the rest count 0 (they never produced in the majors, or debuted after the
    register snapshot).  Unnamed rows ("player to be named", cash) count 0 and
    are counted.
  * nflverse pfr_rosters lists a relocated franchise's seasons twice (OAK and
    LV, STL and LA, ...).  Summed naively, Khalil Mack's 2015-17 AV doubles to
    84.  Deduped on PFR's franchise code.
  * NFL AV is a coarse, position-blind measure of a season's value; for
    offensive linemen it is largely team-derived.  It is the only per-team-
    season value measure nflverse carries; snap counts start 2013 and measure
    playing time, not quality.

Usage:
  python3 scripts/trade_outcomes.py            # fetch if needed, analyze
  python3 scripts/trade_outcomes.py --offline  # cache only

Outputs: data/trades/mlb_blockbusters.csv, data/trades/nfl_blockbusters.csv,
         data/trades/analysis.txt, data/trades/handcheck.txt
"""
import argparse, csv, datetime as dt, math, pathlib, random, statistics, sys, time
import urllib.request, zipfile, io
from collections import defaultdict, Counter

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "trades"
CACHE = pathlib.Path.home() / ".cache" / "sports-page" / "trades"
UA = "TheSportsPage-research/1.0 (trade study; https://thesportspage.net; ideas@thesportspage.net)"
NFLV = "https://github.com/nflverse/nflverse-data/releases/download/"
SOURCES = {
    "tranDB.zip": "https://www.retrosheet.org/transactions/tranDB.zip",
    "war_daily_bat.txt": "https://www.baseball-reference.com/data/war_daily_bat.txt",
    "war_daily_pitch.txt": "https://www.baseball-reference.com/data/war_daily_pitch.txt",
    "trades.csv": NFLV + "trades/trades.csv",
    "draft_picks.csv": NFLV + "draft_picks/draft_picks.csv",
    "pfr_rosters.csv": NFLV + "misc/pfr_rosters.csv",
    "games.csv": NFLV + "schedules/games.csv",
}
for _c in "0123456789abcdef":
    SOURCES["chadwick/people-%s.csv" % _c] = (
        "https://raw.githubusercontent.com/chadwickbureau/register/master/data/people-%s.csv" % _c)
OFFLINE = False
LOG = []          # analysis.txt lines

def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.append(s)

def fetch(name):
    f = CACHE / name
    if f.exists() and f.stat().st_size > 0:
        return f
    if OFFLINE:
        raise SystemExit("offline mode and %s is not cached" % name)
    f.parent.mkdir(parents=True, exist_ok=True)
    print("  fetching", SOURCES[name], file=sys.stderr)
    req = urllib.request.Request(SOURCES[name], headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r:
        f.write_bytes(r.read())
    time.sleep(2)
    return f

# ------------------------------------------------------------------ statistics
def sig2(x):
    """At most two significant digits."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    if x == 0:
        return "0"
    d = 2 - int(math.floor(math.log10(abs(x)))) - 1
    v = round(x, d)
    return ("%d" % v) if d <= 0 else ("%.*f" % (d, v))

def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0, c - h), min(1, c + h)

def pct(k, n):
    p, lo, hi = wilson(k, n)
    if n == 0:
        return "n/a (n=0)"
    return "%s%% (%s-%s%%)" % (sig2(100 * p), sig2(100 * lo), sig2(100 * hi))

def boot(xs, stat=statistics.median, B=2000, seed=1):
    xs = list(xs)
    if not xs:
        return "n/a"
    rng = random.Random(seed)
    est = stat(xs)
    bs = sorted(stat([rng.choice(xs) for _ in xs]) for _ in range(B))
    return "%s (%s to %s)" % (sig2(est), sig2(bs[int(.025 * B)]), sig2(bs[int(.975 * B) - 1]))

def quart(xs):
    xs = sorted(xs)
    if not xs:
        return "n/a"
    q = lambda p: xs[min(len(xs) - 1, int(p * len(xs)))]
    return "IQR %s to %s" % (sig2(q(.25)), sig2(q(.75)))

# ======================================================================== MLB
FRAN = {"CAL": "ANA", "LAA": "ANA", "CHA": "CHW", "CHN": "CHC", "FLO": "MIA", "FLA": "MIA",
        "KCA": "KCR", "LAN": "LAD", "NYA": "NYY", "NYN": "NYM", "SDN": "SDP", "SFN": "SFG",
        "SLN": "STL", "TBA": "TBR", "TBD": "TBR", "MON": "WSN", "WAS": "WSN", "ATH": "OAK"}
for _t in ("ANA ARI ATL BAL BOS CHW CHC CIN CLE COL DET HOU KCR LAD MIA MIL MIN NYY NYM OAK "
           "PHI PIT SDP SEA SFG STL TBR TEX TOR WSN").split():
    FRAN[_t] = _t
WEIGHT = {1981: 107 / 162, 1994: 115 / 162, 1995: 144 / 162, 2020: 60 / 162}
W = lambda y: WEIGHT.get(y, 1.0)
LAST_WAR = 2025      # last complete B-R season used
LAST_TRADE_YEAR = 2021

def load_register():
    retro, byname, name_of = {}, defaultdict(list), {}
    for c in "0123456789abcdef":
        for r in csv.DictReader(open(fetch("chadwick/people-%s.csv" % c), encoding="utf-8")):
            if r["key_bbref"] and r["mlb_played_first"]:
                if r["key_retro"]:
                    retro[r["key_retro"]] = r["key_bbref"]
                nm = (r["name_first"] + " " + r["name_last"]).lower()
                byname[nm].append((r["key_bbref"], int(r["mlb_played_first"])))
                name_of[r["key_bbref"]] = r["name_first"] + " " + r["name_last"]
    return retro, byname, name_of

def load_war():
    team, tot, age, name, pitw = defaultdict(float), defaultdict(float), {}, {}, defaultdict(float)
    for fn in ("war_daily_bat.txt", "war_daily_pitch.txt"):
        for r in csv.DictReader(open(fetch(fn), encoding="utf-8")):
            y = int(r["year_ID"])
            if y < 1970 or y > LAST_WAR:
                continue
            w = 0.0 if r["WAR"] in ("NULL", "") else float(r["WAR"])
            pid, fr = r["player_ID"], FRAN.get(r["team_ID"], r["team_ID"])
            team[pid, y, fr] += w
            tot[pid, y] += w
            if fn.endswith("pitch.txt"):
                pitw[pid] += w
            if r["age"] not in ("NULL", ""):
                age[pid, y] = int(r["age"])
            name[pid] = r["name_common"]
    return team, tot, age, name, pitw

def mlb_dates(d):
    y, m, dd = int(d[:4]), int(d[4:6]), int(d[6:8])
    if m == 0 or m <= 3:
        return y, y, "offseason", 0.0
    if m >= 10:
        return y, y + 1, "offseason", 0.0
    day = date_ok(y, m, dd or 15)
    f = max(0.0, min(1.0, (dt.date(y, 9, 30) - day).days / 183))
    return y, y, ("deadline" if m in (7, 8) else "in-season"), f

def date_ok(y, m, d):
    while True:
        try:
            return dt.date(y, m, d)
        except ValueError:
            d -= 1

def load_mlb_trades(retro, byname):
    z = zipfile.ZipFile(fetch("tranDB.zip"))
    txt = z.read([n for n in z.namelist() if n.lower().endswith("tran.txt")][0]).decode("latin-1")
    groups = defaultdict(list)
    cov = Counter()
    years = Counter()
    for r in csv.reader(io.StringIO(txt)):
        if len(r) < 12:
            continue
        years[r[0][:4]] += 1
        if r[7].strip() not in ("T", "Tp"):
            continue
        frm, to = FRAN.get(r[8].strip()), FRAN.get(r[10].strip())
        if not frm or not to:
            continue
        y = int(r[0][:4])
        if y < 1979 or y > LAST_TRADE_YEAR:
            continue
        pl = r[6].strip()
        pid, kind = None, "unnamed"
        if pl:
            if len(pl) == 8 and pl in retro:
                pid, kind = retro[pl], "id"
            else:
                cands = [b for b, first in byname.get(pl.lower(), []) if first >= y]
                if len(cands) == 1:
                    pid, kind = cands[0], "name-matched"
                else:
                    kind = "never-MLB-or-unmatched"
        cov[kind] += 1
        groups[r[5]].append(dict(date=r[0], player=pl, pid=pid, frm=frm, to=to, kind=kind))
    return groups, cov, years

def mlb_analysis():
    say("=" * 72)
    say("MLB")
    say("=" * 72)
    retro, byname, name_of = load_register()
    team, tot, age, name, pitw = load_war()
    groups, cov, years = load_mlb_trades(retro, byname)
    last = max(y for y, n in years.items() if n > 500)
    say("Retrosheet transaction file: last full year %s (%d rows in %s)." %
        (last, years[str(int(last) + 1)], int(last) + 1))
    say("Trade rows 1979-2021 between MLB clubs: %d; player id from Retrosheet %d, "
        "name-matched minor leaguer %d, never-MLB/unmatched name %d, unnamed (PTBNL/cash) %d." %
        (sum(cov.values()), cov["id"], cov["name-matched"], cov["never-MLB-or-unmatched"], cov["unnamed"]))
    nid = sum(1 for g in groups.values() for r in g if r["kind"] == "id")
    hit = sum(1 for g in groups.values() for r in g if r["kind"] == "id" and any(
        (r["pid"], y) in tot for y in range(1970, LAST_WAR + 1)))
    say("Retrosheet-id rows that join to a B-R WAR row: %d of %d (%s%%)." % (hit, nid, sig2(100 * hit / nid)))

    prior = lambda p, S: sum(tot.get((p, y), 0.0) for y in range(S - 3, S))
    rows = []
    for tid, g in groups.items():
        d0 = min(r["date"] for r in g)
        ycal, S, phase, f = mlb_dates(d0)
        if ycal < 1980 or S + 2 > LAST_WAR:
            continue
        def val(r, n):
            if not r["pid"]:
                return 0.0
            ys = range(S, S + n)
            return sum(team.get((r["pid"], y, r["to"]), 0.0) for y in ys)
        named = [r for r in g if r["pid"]]
        if not named:
            continue
        pri = {r["pid"]: prior(r["pid"], S) for r in named}
        star = max(named, key=lambda r: pri[r["pid"]])
        sp = star["pid"]
        A, B = star["to"], star["frm"]
        rate = pri[sp] / sum(W(y) for y in range(S - 3, S))
        def pw(n):
            ys = list(range(S, S + n))
            return (f if phase != "offseason" else 1.0) * W(ys[0]) + sum(W(y) for y in ys[1:])
        out = dict(trade_id=tid, date=d0, season=S, phase=phase, teams="/".join(sorted({r["frm"] for r in g} | {r["to"] for r in g})),
                   multi_team=int(len({r["frm"] for r in g} | {r["to"] for r in g}) > 2),
                   star=name.get(sp, name_of.get(sp, sp)), star_id=sp, star_to=A, star_from=B,
                   star_age=(age.get((sp, S)) or (age.get((sp, S - 1), -99) + 1)),
                   star_pitcher=int(pitw.get(sp, 0) > 0.5 * sum(tot.get((sp, y), 0) for y in range(1970, LAST_WAR + 1))),
                   star_prior3=round(pri[sp], 1), n_over_8=sum(1 for v in pri.values() if v >= 8),
                   unnamed=sum(1 for r in g if r["kind"] == "unnamed"),
                   players=len(g), ids="|".join(sorted({r["pid"] for r in g if r["pid"]})))
        for n in (3, 6):
            if S + n - 1 > LAST_WAR:
                for k in ("expected", "star_new", "star_any", "got", "gave", "margin"):
                    out["%s%d" % (k, n)] = ""
                continue
            out["expected%d" % n] = round(rate * pw(n), 2)
            out["star_new%d" % n] = round(val(star, n), 2)
            out["star_any%d" % n] = round(sum(tot.get((sp, y), 0) for y in range(S, S + n)) -
                                          (sum(team.get((sp, S, fr), 0) for fr in (B,)) if phase != "offseason" else 0), 2)
            got = sum(val(r, n) for r in g if r["to"] == A)
            gave = sum(val(r, n) for r in g if r["frm"] == A)
            out["got%d" % n], out["gave%d" % n], out["margin%d" % n] = round(got, 2), round(gave, 2), round(got - gave, 2)
        rows.append(out)
    nall = len(rows)
    say("Trades 1980-2021 with at least one major leaguer named: %d." % nall)
    bb = [r for r in rows if r["star_prior3"] >= 6]
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "mlb_blockbusters.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(bb[0].keys()))
        w.writeheader()
        for r in sorted(bb, key=lambda r: r["date"]):
            w.writerow(r)

    # ---- regression baseline: every player over the bar, any team
    def baseline(thr):
        out = defaultdict(list)
        players = {p for (p, y) in tot}
        for S in range(1980, 2023):
            for p in players:
                pr = prior(p, S)
                if pr < thr:
                    continue
                exp = pr / sum(W(y) for y in range(S - 3, S)) * sum(W(y) for y in range(S, S + 3))
                a = age.get((p, S)) or age.get((p, S - 1), 0) + 1
                out[band(a)].append(sum(tot.get((p, y), 0) for y in range(S, S + 3)) / exp)
                out["all"].append(out[band(a)][-1])
        return out

    BL = {}

    def report(sel, label, even=2.0, n=3, short=False):
        sel = [r for r in sel if r["expected%d" % n] != ""]
        say("\n-- %s  (n=%d trades, window %d seasons)" % (label, len(sel), n))
        if not sel:
            return
        k = sum(1 for r in sel if r["star_new%d" % n] >= r["expected%d" % n])
        say("  1. star delivered >= his prior pace for the new team: %s" % pct(k, len(sel)))
        if n == 3 and BL:
            reg = lambda r: r["expected3"] * statistics.median(BL[band(r["star_age"])])
            say("     star delivered >= what regression alone predicts (age-matched, all MLB players over "
                "the same bar): for new team %s; on any team %s" % (
                    pct(sum(r["star_new3"] >= reg(r) for r in sel), len(sel)),
                    pct(sum(r["star_any3"] >= reg(r) for r in sel), len(sel))))
        say("     median ratio delivered/expected (for new team): %s" %
            boot([r["star_new%d" % n] / r["expected%d" % n] for r in sel if r["expected%d" % n] > 0]))
        if not short:
            say("     same, any team (separates leaving from declining): %s" %
                boot([r["star_any%d" % n] / r["expected%d" % n] for r in sel if r["expected%d" % n] > 0]))
            say("     median star age %s; median prior 3-yr WAR %s; median expected %s; median delivered %s" % (
                sig2(statistics.median(r["star_age"] for r in sel)), sig2(statistics.median(r["star_prior3"] for r in sel)),
                sig2(statistics.median(r["expected%d" % n] for r in sel)), sig2(statistics.median(r["star_new%d" % n] for r in sel))))
        m = [r["margin%d" % n] for r in sel]
        won, ev, lost = sum(x > even for x in m), sum(abs(x) <= even for x in m), sum(x < -even for x in m)
        say("  2. star-getting side (even = within %s WAR): won %s, even %s, lost %s" % (
            sig2(even), pct(won, len(m)), pct(ev, len(m)), pct(lost, len(m))))
        if not short:
            say("     margin (WAR, star side minus other side): median %s, %s; median |margin| %s; "
                "share |margin| > 10 WAR: %s" % (boot(m), quart(m), boot([abs(x) for x in m]),
                                                pct(sum(abs(x) > 10 for x in m), len(m))))

    for thr in (8, 6, 12):
        sel = [r for r in rows if r["star_prior3"] >= thr]
        BL.clear()
        BL.update(baseline(thr))
        say("\n######## Blockbuster threshold: >= %d bWAR in the 3 prior seasons" % thr)
        report(sel, "all blockbusters", short=(thr != 8))
        if thr == 8:
            report([r for r in sel if r["phase"] == "offseason"], "offseason trades only")
            report([r for r in sel if r["phase"] == "deadline"], "deadline (Jul-Aug) trades: rentals included")
            report([r for r in sel if r["phase"] == "in-season"], "other in-season (Apr-Jun, Sep)")
            report(sel, "6-season window (trades through 2020)", n=6)
            report([r for r in sel if not r["multi_team"]], "two-team trades only", short=True)
            report([r for r in sel if r["unnamed"] == 0], "no unnamed player/cash rows", short=True)
            report(sel, "'even' band = 1 WAR", even=1, short=True)
            report(sel, "'even' band = 4 WAR", even=4, short=True)
            for a, b in ((1980, 1994), (1995, 2009), (2010, 2021)):
                report([r for r in sel if a <= int(r["date"][:4]) <= b], "trades %d-%d" % (a, b), short=True)
            say("\n  Who the stars were: %d of %d pitchers; %d trades sent two or more 8-WAR players." % (
                sum(r["star_pitcher"] for r in sel), len(sel), sum(r["n_over_8"] >= 2 for r in sel)))
            say("  Regression baseline: every MLB player with >= 8 bWAR in S-3..S-1, S=1980-2022, "
                "total WAR S..S+2 on any team / expected:")
            bl = BL
            say("     all players: median %s (n=%d)" % (boot(bl["all"]), len(bl["all"])))
            off = [r for r in sel if r["phase"] == "offseason"]
            for bnd in ("<=27", "28-30", "31-33", "34+"):
                st = [r for r in off if band(r["star_age"]) == bnd]
                say("     age %-5s  everyone: median %s (n=%d) | traded stars (offseason), any team: %s, for new team: %s (n=%d)" % (
                    bnd, sig2(statistics.median(bl[bnd])) if bl[bnd] else "n/a", len(bl[bnd]),
                    sig2(statistics.median([r["star_any3"] / r["expected3"] for r in st])) if st else "n/a",
                    sig2(statistics.median([r["star_new3"] / r["expected3"] for r in st])) if st else "n/a", len(st)))
            # age-matched: the share of everyone at the stars' ages who reached their prior pace
            say("     share of EVERYONE over the bar who matched prior pace (any team): %s" %
                pct(sum(x >= 1 for x in bl["all"]), len(bl["all"])))
    return rows, name

def band(a):
    return "<=27" if a <= 27 else "28-30" if a <= 30 else "31-33" if a <= 33 else "34+"

# ======================================================================== NFL
NFR = {"STL": "LA", "LAR": "LA", "SD": "LAC", "SDG": "LAC", "OAK": "LV", "LVR": "LV", "JAC": "JAX",
       "GNB": "GB", "KAN": "KC", "NOR": "NO", "NWE": "NE", "SFO": "SF", "TAM": "TB"}
nf = lambda t: NFR.get(t, t)
LAST_AV = 2021      # pfr_rosters carries 2022 rows, but every AV in them is blank

def nfl_analysis():
    say("\n" + "=" * 72)
    say("NFL")
    say("=" * 72)
    av, avt, nage, nname = defaultdict(float), defaultdict(float), {}, {}
    seen, dups = set(), 0
    for r in csv.DictReader(open(fetch("pfr_rosters.csv"), encoding="utf-8")):
        y = int(r["season"])
        # TRAP: a relocated franchise's every season appears twice, once under
        # each nflverse code (OAK and LV, STL and LA, SD and LAC, JAC and JAX).
        # Dedupe on PFR's own franchise code, which does not change.
        k = (y, r["pfr"], r["pfr_player_id"])
        if k in seen:
            dups += 1
            continue
        seen.add(k)
        if y > LAST_AV:
            continue
        v = float(r["av"]) if r["av"] not in ("", "NA") else 0.0
        av[r["pfr_player_id"], y, nf(r["nfl"])] += v
        avt[r["pfr_player_id"], y] += v
        if r["age"] not in ("", "NA"):
            nage[r["pfr_player_id"], y] = int(float(r["age"]))
        nname[r["pfr_player_id"]] = r["player"]
    say("PFR AV per player-team-season from nflverse pfr_rosters.csv: seasons %d-%d "
        "(2022 rows exist but AV is blank); %d duplicate relocated-franchise rows dropped." %
        (min(y for _, y in avt), max(y for _, y in avt), dups))
    dp_by_pick, dp_by_player = {}, {}
    for r in csv.DictReader(open(fetch("draft_picks.csv"), encoding="utf-8")):
        k = (int(r["season"]), int(r["pick"]))
        dp_by_pick[k] = (r["pfr_player_id"], nf(r["team"]), r["pfr_player_name"])
        if r["pfr_player_id"]:
            dp_by_player[r["pfr_player_id"]] = (int(r["season"]), nf(r["team"]))
    kick, wins = {}, defaultdict(lambda: [0.0, 0])
    for r in csv.DictReader(open(fetch("games.csv"), encoding="utf-8")):
        if r["game_type"] != "REG":
            continue
        s = int(r["season"])
        d = dt.date.fromisoformat(r["gameday"])
        kick[s] = min(kick.get(s, d), d)
        kick["end", s] = max(kick.get(("end", s), d), d)
        if r["result"] not in ("", "NA"):
            res = float(r["result"])   # home minus away
            for t, sgn in ((nf(r["home_team"]), 1), (nf(r["away_team"]), -1)):
                wins[t, s][0] += 1.0 if res * sgn > 0 else 0.5 if res == 0 else 0.0
                wins[t, s][1] += 1
    groups = defaultdict(list)
    for r in csv.DictReader(open(fetch("trades.csv"), encoding="utf-8")):
        groups[r["trade_id"]].append(r)
    say("nflverse trades.csv: %d rows, %d trades, %s-%s." % (
        sum(len(g) for g in groups.values()), len(groups),
        min(g[0]["season"] for g in groups.values()), max(g[0]["season"] for g in groups.values())))
    cov = Counter()
    rows = []
    for tid, g in groups.items():
        d = dt.date.fromisoformat(g[0]["trade_date"])
        y = d.year
        insea = y in kick and kick[y] <= d <= kick["end", y]
        S = y
        if S < 2005 or S + 2 > LAST_AV:
            continue
        f = ((kick["end", y] - d).days / max(1, (kick["end", y] - kick[y]).days)) if insea else 1.0
        assets = []
        for r in g:
            a = dict(frm=nf(r["gave"]), to=nf(r["received"]), pick=bool(r["pick_round"]),
                     rnd=int(r["pick_round"]) if r["pick_round"] else None,
                     pseason=int(r["pick_season"]) if r["pick_season"] else None,
                     pnum=int(r["pick_number"]) if r["pick_number"] else None,
                     pid=r["pfr_id"] or None, name=r["pfr_name"], flipped=0, vteam=None)
            if a["pick"]:
                if not a["pid"] and a["pnum"] and (a["pseason"], a["pnum"]) in dp_by_pick:
                    a["pid"] = dp_by_pick[a["pseason"], a["pnum"]][0] or None
                if a["pid"] and a["pid"] in dp_by_player:
                    a["vteam"] = dp_by_player[a["pid"]][1]
                    a["flipped"] = int(a["vteam"] != a["to"])
                    cov["pick resolved to draftee"] += 1
                    cov["  of which flipped again"] += a["flipped"]
                else:
                    a["pid"] = None
                    cov["pick unresolved (counts 0)"] += 1
            else:
                a["vteam"] = a["to"]
                cov["player row"] += 1
                if a["pid"] and any((a["pid"], s) in avt for s in range(2002, LAST_AV + 1)):
                    cov["  player joins to AV"] += 1
            assets.append(a)
        def val(a, n):
            if not a["pid"]:
                return 0.0
            return sum(av.get((a["pid"], s, a["vteam"]), 0.0) for s in range(S, S + n))
        prior = lambda p: sum(avt.get((p, s), 0.0) for s in range(S - 3, S))
        vets = [a for a in assets if not a["pick"] and a["pid"]]
        star = max(vets, key=lambda a: prior(a["pid"])) if vets else None
        sprior = prior(star["pid"]) if star else 0.0
        firsts = [a for a in assets if a["pick"] and a["rnd"] == 1]
        if star and sprior >= 24:
            kind, A, B = "veteran", star["to"], star["frm"]
        elif firsts:
            top = min(firsts, key=lambda a: (a["pseason"] or 9999, a["pnum"] or 99))
            kind, A, B = "first-round pick", top["to"], top["frm"]
        else:
            continue
        out = dict(trade_id=tid, date=str(d), season=S, phase="in-season" if insea else "offseason", kind=kind,
                   teams="/".join(sorted({a["frm"] for a in assets} | {a["to"] for a in assets})),
                   star=nname.get(star["pid"], star["name"]) if star else "", star_id=star["pid"] if star else "",
                   star_age=(nage.get((star["pid"], S - 1), -99) + 1) if star else "", star_prior3=round(sprior, 1),
                   getter=A, other=B, n_first_round=len(firsts), flipped_picks=sum(a["flipped"] for a in assets),
                   assets=len(assets), ids="|".join(sorted({a["pid"] for a in assets if a["pid"]})))
        for n in (3, 6):
            if S + n - 1 > LAST_AV:
                for k in ("expected", "star_new", "star_any", "got", "gave", "margin"):
                    out["%s%d" % (k, n)] = ""
                continue
            if star:
                out["expected%d" % n] = round(sprior / 3 * (f + n - 1), 2)
                out["star_new%d" % n] = round(val(star, n), 2)
                out["star_any%d" % n] = round(sum(avt.get((star["pid"], s), 0) for s in range(S, S + n)) -
                                              (av.get((star["pid"], S, star["frm"]), 0) if insea else 0), 2)
            else:
                out["expected%d" % n] = out["star_new%d" % n] = out["star_any%d" % n] = ""
            got = sum(val(a, n) for a in assets if a["to"] == A)
            gave = sum(val(a, n) for a in assets if a["frm"] == A)
            out["got%d" % n], out["gave%d" % n], out["margin%d" % n] = round(got, 1), round(gave, 1), round(got - gave, 1)
        # team record change (offseason veteran deals only): season S vs S-1
        wa, wb = wins.get((A, S)), wins.get((A, S - 1))
        out["win_pct_before"] = round(wb[0] / wb[1], 3) if wb and wb[1] else ""
        out["win_pct_after"] = round(wa[0] / wa[1], 3) if wa and wa[1] else ""
        rows.append(out)
    for k, v in cov.items():
        say("  %s: %d" % (k, v))
    with open(OUT / "nfl_blockbusters.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in sorted(rows, key=lambda r: r["date"]):
            w.writerow(r)

    NBL = {}

    def report(sel, label, even=5.0, n=3, short=False):
        sel = [r for r in sel if r["got%d" % n] != ""]
        say("\n-- %s  (n=%d trades, window %d seasons)" % (label, len(sel), n))
        if not sel:
            return
        st = [r for r in sel if r["expected%d" % n] not in ("", 0)]
        if st and st[0]["kind"] == "veteran":
            k = sum(1 for r in st if r["star_new%d" % n] >= r["expected%d" % n])
            say("  1. star delivered >= his prior AV pace for the new team: %s" % pct(k, len(st)))
            if n == 3 and NBL:
                reg = lambda r: r["expected3"] * statistics.median(NBL[nband(r["star_age"])])
                say("     star delivered >= what regression alone predicts (age-matched): new team %s; any team %s" % (
                    pct(sum(r["star_new3"] >= reg(r) for r in st), len(st)),
                    pct(sum(r["star_any3"] >= reg(r) for r in st), len(st))))
            say("     median ratio delivered/expected (new team): %s" %
                boot([r["star_new%d" % n] / r["expected%d" % n] for r in st]))
            if not short:
                say("     same, any team: %s" % boot([r["star_any%d" % n] / r["expected%d" % n] for r in st]))
                say("     median star age %s; median prior 3-yr AV %s; median expected %s; median delivered %s" % (
                    sig2(statistics.median(r["star_age"] for r in st)), sig2(statistics.median(r["star_prior3"] for r in st)),
                    sig2(statistics.median(r["expected%d" % n] for r in st)), sig2(statistics.median(r["star_new%d" % n] for r in st))))
        m = [r["margin%d" % n] for r in sel]
        won, ev, lost = sum(x > even for x in m), sum(abs(x) <= even for x in m), sum(x < -even for x in m)
        say("  2. %s side (even = within %s AV): won %s, even %s, lost %s" % (
            "star-getting" if sel[0]["kind"] == "veteran" else "first-rounder-getting",
            sig2(even), pct(won, len(m)), pct(ev, len(m)), pct(lost, len(m))))
        if not short:
            say("     margin (AV): median %s, %s; median |margin| %s; share |margin| > 20 AV: %s" % (
                boot(m), quart(m), boot([abs(x) for x in m]), pct(sum(abs(x) > 20 for x in m), len(m))))

    vet = lambda thr: [r for r in rows if r["kind"] == "veteran" and r["star_prior3"] >= thr]
    players = {p for (p, s) in avt}

    def nbaseline(thr):
        bl = defaultdict(list)
        for S in range(2005, LAST_AV - 1):
            for p in players:
                pr = sum(avt.get((p, s), 0) for s in range(S - 3, S))
                if pr >= thr:
                    x = sum(avt.get((p, s), 0) for s in range(S, S + 3)) / pr
                    a = nage.get((p, S - 1), 0) + 1
                    bl["all"].append(x)
                    bl[nband(a)].append(x)
        return bl
    say("\nNFL trade window: effective seasons 2005-2019 (3-season outcome through 2021).")
    for thr in (30, 24, 36):
        NBL.clear()
        NBL.update(nbaseline(thr))
        say("\n######## Veteran blockbuster: >= %d AV in the 3 prior seasons" % thr)
        report(vet(thr), "veteran blockbusters", short=(thr != 30))
        if thr == 30:
            report([r for r in vet(30) if r["phase"] == "offseason"], "offseason", short=True)
            report([r for r in vet(30) if r["phase"] == "in-season"], "in-season (deadline)", short=True)
            report(vet(30), "6-season window (trades through 2016)", n=6)
            report(vet(30), "'even' band = 3 AV", even=3, short=True)
            report(vet(30), "'even' band = 10 AV", even=10, short=True)
            bl = NBL
            say("  Regression baseline: every NFL player with >= 30 AV in S-3..S-1, S=2005-2019, total AV S..S+2 / prior:")
            say("     all: median %s (n=%d); share matching prior pace %s" % (
                boot(bl["all"]), len(bl["all"]), pct(sum(x >= 1 for x in bl["all"]), len(bl["all"]))))
            off = [r for r in vet(30) if r["phase"] == "offseason"]
            for b in ("<=25", "26-28", "29-31", "32+"):
                st = [r for r in off if nband(r["star_age"]) == b]
                say("     age %-5s everyone: %s (n=%d) | traded stars, any team: %s, new team: %s (n=%d)" % (
                    b, sig2(statistics.median(bl[b])) if bl[b] else "n/a", len(bl[b]),
                    sig2(statistics.median([r["star_any3"] / r["expected3"] for r in st])) if st else "n/a",
                    sig2(statistics.median([r["star_new3"] / r["expected3"] for r in st])) if st else "n/a", len(st)))
            # team record, optional measure
            allch = []
            for (t, s), (wv, gv) in wins.items():
                if (t, s - 1) in wins and 2003 <= s <= 2021:
                    pw0 = wins[t, s - 1][0] / wins[t, s - 1][1]
                    allch.append((pw0, wv / gv - pw0))
            mx = statistics.mean(x for x, _ in allch)
            my = statistics.mean(y for _, y in allch)
            b = sum((x - mx) * (y - my) for x, y in allch) / sum((x - mx) ** 2 for x, _ in allch)
            res = [r["win_pct_after"] - r["win_pct_before"] - (my + b * (r["win_pct_before"] - mx))
                   for r in off if r["win_pct_after"] != "" and r["win_pct_before"] != ""]
            say("  3. Team record, offseason veteran blockbusters: next-season win%% change beyond what the "
                "league-wide regression predicts (slope %s): mean %s win%% points (n=%d) %s" % (
                    sig2(b), boot([100 * x for x in res], stat=statistics.mean),
                    len(res), "= %s wins per 17 games" % sig2(17 * statistics.mean(res))))
    NBL.clear()
    fr = [r for r in rows if r["kind"] == "first-round pick"]
    say("\n######## First-round-pick trades with no 24-AV veteran (side that got the earliest first-rounder)")
    report(fr, "first-round pick trades")
    report([r for r in fr if r["date"][5:7] == "04"], "April (draft-week) trades", short=True)
    report(fr, "6-season window", n=6)
    report(fr, "'even' band = 10 AV", even=10, short=True)
    return rows

def nband(a):
    return "<=25" if a <= 25 else "26-28" if a <= 28 else "29-31" if a <= 31 else "32+"

# ================================================================ hand checks
MLB_CHECK = [("stantmi03", "2017"), ("santajo02", "2008"), ("rodrial01", "2004"), ("griffke02", "2000"),
             ("schilcu01", "2003"), ("hallaro01", "2009"), ("cabremi01", "2007"), ("gonzaad01", "2010"),
             ("sabatc.01", "2008"), ("bettsmo01", "2020"), ("machama01", "2018"), ("donaljo02", "2014")]
NFL_CHECK = [("MackKh00", "2018"), ("RamsJa00", "2019"), ("TunsLa00", "2019"), ("AdamJa00", "2020"), ("WatsDe00", "2017"), ("CookBr00", "2017"), ("CookBr00", "2018"),
             ("BeckOd00", "2019"), ("CutlJa00", "2009"), ("ReviDa99", "2013"), ("LyncMa00", "2010")]

def handcheck(mlb, nfl):
    lines = ["HAND CHECK: famous trades as the data record them", "",
             "MLB (window = 3 seasons; WAR for the new team; margin = star side got minus gave)",
             "%-22s %-10s %-9s %-11s %5s %6s %6s %6s %6s %6s" % ("star", "date", "teams", "phase", "age",
                                                            "prior", "exp", "new", "got", "margin")]
    for pid, yr in MLB_CHECK:
        hit = [r for r in mlb if pid in r["ids"].split("|") and r["date"][:4] == yr]
        if not hit:
            lines.append("%-22s %s  NOT FOUND among trades over 6 bWAR" % (pid, yr))
            continue
        for r in hit:
            if r["star_id"] != pid:
                lines.append("%-22s (in this trade; the bigger prior belonged to the row below)" % pid)
            lines.append("%-22s %-10s %-9s %-11s %5s %6s %6s %6s %6s %6s" % (
                r["star"][:22], r["date"], r["star_from"] + ">" + r["star_to"], r["phase"], r["star_age"],
                sig2(r["star_prior3"]), sig2(r["expected3"]), sig2(r["star_new3"]), sig2(r["got3"]), sig2(r["margin3"])))
    lines += ["", "NFL (window = 3 seasons; AV for the new team; 'kind' says whether the trade cleared the",
              "veteran bar (>= 24 AV prior) or counts as a first-round-pick trade, in which case 'teams'",
              "is the side that got the earliest first-rounder and exp/new describe the top veteran)",
              "%-22s %-10s %-9s %-9s %5s %6s %6s %6s %6s %6s" % ("star", "date", "teams", "phase", "age",
                                                           "prior", "exp", "new", "got", "margin")]
    for pid, yr in NFL_CHECK:
        hit = [r for r in nfl if pid in r["ids"].split("|") and r["date"][:4] == yr]
        if not hit:
            lines.append("%-22s %s  NOT FOUND (outside window or below the 24-AV bar)" % (pid, yr))
            continue
        for r in hit:
            lines.append("%-22s %-10s %-9s %-9s %5s %6s %6s %6s %6s %6s  %s" % (
                (r["star"] or "(no veteran)")[:22], r["date"], r["other"] + ">" + r["getter"], r["phase"], r["star_age"],
                sig2(r["star_prior3"]), sig2(r["expected3"] or 0), sig2(r["star_new3"] or 0), sig2(r["got3"]), sig2(r["margin3"]), r["kind"]))
    (OUT / "handcheck.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))

def main():
    global OFFLINE
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--offline", action="store_true", help="read only the cache; never download")
    a = ap.parse_args()
    OFFLINE = a.offline
    OUT.mkdir(parents=True, exist_ok=True)
    mlb, _ = mlb_analysis()
    nfl = nfl_analysis()
    (OUT / "analysis.txt").write_text("\n".join(LOG) + "\n")
    handcheck(mlb, nfl)

if __name__ == "__main__":
    main()
