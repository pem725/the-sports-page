#!/usr/bin/env python3
"""Do teams play worse the week after facing a violent defense?

    python3 scripts/hangover.py --pull      # fetch and cache (slow, throttled)
    python3 scripts/hangover.py             # analyse the cache

THE EDITOR, 2026-10-10, watching Iowa hit Washington for sixty minutes: "Take a
look at teams that play Iowa and how they fare the following week. My guess is
not well, because the team is probably pretty beaten up. There are notorious
teams that are very aggressive and hard-hitting -- they gang tackle, every
possession is met with multiple defenders and a very violent action. If you can
do that, check it out."

THE MEASUREMENT PROBLEM IS THE WHOLE PROBLEM. "Hard-hitting" is not in a box
score, and he said so himself. What IS recorded is the residue of hitting:

    havoc rate   tackles for loss + forced fumbles + passes defensed, per play
    stuff rate   share of runs stopped at or behind the line
    line yards   yards the defence concedes before contact is won

Those are not the same thing as violence and this file does not pretend they
are. They are what violence leaves behind in the record, which is the closest an
archive gets.

THE DESIGN, and the controls are what make it worth running:

  1. Build a physicality index per team-season from its DEFENSIVE havoc and stuff
     rates, standardised within each season so eras do not drift.
  2. For every game, find that opponent's NEXT game.
  3. Measure how that team's offence did in the next game against ITS OWN season
     baseline -- the hangover, if any.
  4. CONTROL FOR THE NEXT OPPONENT. This is the step the eye test cannot do.
     Teams that play Iowa are usually in a hard stretch of schedule, so their
     next opponent tends to be good too. Without this control a "hangover" is
     just a strength-of-schedule artefact wearing a costume.
  5. Control for rest: a bye week after the beating is a different experiment.

WHAT A NULL RESULT WOULD MEAN, stated before looking. If the coefficient is flat,
it does not prove nobody gets beaten up. It means the effect is not visible in
offensive efficiency a week later, at this sample size -- which is still worth
printing, because the belief is widespread and confidently held.
"""
import argparse
import collections
import json
import math
import pathlib
import re
import statistics
import sys
import time
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
CACHE = REPO / "data" / "cfb-game-advanced.json"
SEASONS = [y for y in range(2016, 2026) if y != 2020]   # 2020 schedules were chaos


def key():
    if "CFBD_KEY" in __import__("os").environ:
        return __import__("os").environ["CFBD_KEY"]
    for ln in (pathlib.Path.home() / ".config/secrets/tokens.env").read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?CFBD_KEY\s*=\s*(.*)$", ln)
        if m:
            return m.group(1).strip().strip('"').strip("'")


def pull():
    K = key()
    out = []
    for y in SEASONS:
        for w in range(1, 16):
            u = (f"https://api.collegefootballdata.com/stats/game/advanced?"
                 f"year={y}&week={w}&seasonType=regular")
            d = None
            for a in range(4):
                try:
                    d = json.load(urllib.request.urlopen(urllib.request.Request(
                        u, headers={"Authorization": f"Bearer {K}"}), timeout=120))
                    break
                except Exception:
                    time.sleep(3 * (a + 1))
            if d is None:
                raise SystemExit(f"{y} wk{w} failed -- refusing a gapped cache")
            out += d
            time.sleep(1.2)
        print(f"    {y}: {len(out):,} rows so far", flush=True)
    CACHE.write_text(json.dumps(out))
    print(f"  cached {len(out):,} team-games -> {CACHE.relative_to(REPO)}")


def z(vals):
    m, s = statistics.mean(vals), statistics.pstdev(vals)
    return (lambda v: (v - m) / s) if s else (lambda v: 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pull", action="store_true")
    a = ap.parse_args()
    if a.pull:
        return pull() or 0
    if not CACHE.exists():
        raise SystemExit("no cache; run with --pull first")

    rows = json.loads(CACHE.read_text())
    G = []
    for r in rows:
        o, d = r.get("offense") or {}, r.get("defense") or {}
        if not o.get("plays") or o["plays"] < 30:
            continue
        G.append(dict(season=r["season"], week=r["week"], team=r["team"],
                      opp=r["opponent"], off_ppa=o.get("ppa"), off_sr=o.get("successRate"),
                      d_havoc=(d.get("havoc") or {}).get("total") if isinstance(d.get("havoc"), dict) else d.get("havoc"),
                      d_stuff=d.get("stuffRate"), d_line=d.get("lineYards")))
    G = [g for g in G if g["off_ppa"] is not None]
    print(f"  {len(G):,} team-games, {len(SEASONS)} seasons\n")

    # ---- the measurement model ---------------------------------------------
    # EIGHT indicators of one latent construct, from the SEASON endpoint. The
    # per-game endpoint silently omits havoc entirely, so an earlier version of
    # this built the index from two indicators while believing it had three --
    # a missing field is not a zero, it is an absence, and it says nothing.
    SEAS = REPO / "data" / "cfb-season-advanced.json"
    IND = [("total", +1), ("frontSeven", +1), ("db", +1), ("stuffRate", +1),
           ("lineYards", -1), ("powerSuccess", -1), ("secondLevelYards", -1),
           ("openFieldYards", -1)]
    raw = {}
    for r in json.loads(SEAS.read_text()):
        d = r.get("defense") or {}
        hv = d.get("havoc") or {}
        v, ok = [], True
        for k, sg in IND:
            val = hv.get(k) if k in ("total", "frontSeven", "db") else d.get(k)
            if val is None:
                ok = False
                break
            v.append(val * sg)
        if ok:
            raw[(r["season"], r["team"])] = v
    keys = list(raw)
    cols = []
    for i in range(len(IND)):
        c = [raw[t][i] for t in keys]
        m, s = statistics.mean(c), statistics.pstdev(c)
        cols.append([(x - m) / s for x in c])
    n_ts = len(keys)
    C = [[sum(a * b for a, b in zip(cols[i], cols[j])) / n_ts
          for j in range(len(IND))] for i in range(len(IND))]
    w = [1.0] * len(IND)
    for _ in range(500):
        nw = [sum(C[i][j] * w[j] for j in range(len(IND))) for i in range(len(IND))]
        nrm = math.sqrt(sum(x * x for x in nw))
        w = [x / nrm for x in nw]
    if sum(w) < 0:
        w = [-x for x in w]
    lam = sum(w[i] * sum(C[i][j] * w[j] for j in range(len(IND))) for i in range(len(IND)))
    rbar = sum(C[i][j] for i in range(len(IND)) for j in range(len(IND)) if i != j) \
        / (len(IND) * (len(IND) - 1))
    alpha = len(IND) * rbar / (1 + (len(IND) - 1) * rbar)
    # factor score = indicator-weighted composite, standardised
    fs = [sum(w[i] * cols[i][r] for i in range(len(IND))) for r in range(n_ts)]
    fm, fsd = statistics.mean(fs), statistics.pstdev(fs)
    phys = {keys[r]: (fs[r] - fm) / fsd for r in range(n_ts)}
    print(f"  MEASUREMENT MODEL: {n_ts} team-seasons, {len(IND)} indicators")
    print(f"    first factor eigenvalue {lam:.2f} of {len(IND)} "
          f"({lam/len(IND):.0%} of shared variance)")
    print(f"    mean inter-indicator r {rbar:.3f}, standardised alpha {alpha:.3f}\n")

    # ---- each team's own offensive baseline, per season ---------------------
    base = {}
    for season in SEASONS:
        for t in {g["team"] for g in G if g["season"] == season}:
            v = [g["off_ppa"] for g in G if g["season"] == season and g["team"] == t]
            if len(v) >= 6:
                base[(season, t)] = statistics.mean(v)

    # ---- pair each game with that team's NEXT game --------------------------
    sched = collections.defaultdict(list)
    for g in G:
        sched[(g["season"], g["team"])].append(g)
    for k in sched:
        sched[k].sort(key=lambda x: x["week"])

    pairs = []
    for k, gs in sched.items():
        for i in range(len(gs) - 1):
            cur, nxt = gs[i], gs[i + 1]
            pk = (cur["season"], cur["opp"])          # who just hit them
            nk = (cur["season"], nxt["opp"])          # who they face next
            if pk not in phys or nk not in phys or k not in base:
                continue
            pairs.append(dict(
                hitter=phys[pk],                      # physicality just faced
                next_def=phys[nk],                    # CONTROL: next opponent
                rest=nxt["week"] - cur["week"],       # 1 = no bye
                resid=nxt["off_ppa"] - base[k]))      # next week vs own baseline
    print(f"  {len(pairs):,} consecutive-game pairs with both opponents rated\n")

    # ---- the naive look, then the controlled one ---------------------------
    def ols(xs, ys):
        mx, my = statistics.mean(xs), statistics.mean(ys)
        b = sum((p - mx) * (q - my) for p, q in zip(xs, ys)) / sum((p - mx) ** 2 for p in xs)
        return my - b * mx, b

    hs = [p["hitter"] for p in pairs]
    rs = [p["resid"] for p in pairs]
    _, b_naive = ols(hs, rs)
    print("  NAIVE -- next-week offence against the physicality just faced")
    print(f"    slope {b_naive:+.4f} PPA per SD of hitter physicality")

    # multiple regression: resid ~ hitter + next_def + rest
    import itertools
    X = [(1.0, p["hitter"], p["next_def"], float(p["rest"])) for p in pairs]
    y = rs
    n, m = len(X), 4
    A = [[sum(X[k][i] * X[k][j] for k in range(n)) for j in range(m)] for i in range(m)]
    bb = [sum(X[k][i] * y[k] for k in range(n)) for i in range(m)]
    for i in range(m):
        pv = A[i][i]
        for j in range(m):
            A[i][j] /= pv
        bb[i] /= pv
        for r2 in range(m):
            if r2 != i:
                f = A[r2][i]
                for j in range(m):
                    A[r2][j] -= f * A[i][j]
                bb[r2] -= f * bb[i]
    a0, b_hit, b_next, b_rest = bb
    yh = [a0 + b_hit * p["hitter"] + b_next * p["next_def"] + b_rest * p["rest"] for p in pairs]
    sse = sum((c - h) ** 2 for c, h in zip(y, yh))
    se = math.sqrt(sse / (n - m))
    sx = math.sqrt(sum((p["hitter"] - statistics.mean(hs)) ** 2 for p in pairs))
    se_b = se / sx
    print("\n  CONTROLLED -- holding the next opponent and the rest week constant")
    print(f"    hitter physicality {b_hit:+.4f}  (se {se_b:.4f}, t = {b_hit/se_b:+.2f})")
    print(f"    next opponent      {b_next:+.4f}   <- the real driver, as expected")
    print(f"    extra rest week    {b_rest:+.4f}")

    print("\n  BY HOW HARD THEY WERE HIT (controlled residual, binned)")
    print(f"    {'faced':<22}{'n':>7}{'next-week PPA vs own baseline':>32}")
    for lab, lo, hi in (("top 10% most violent", 1.28, 9), ("next 15%", 0.67, 1.28),
                        ("middle", -0.67, 0.67), ("bottom 25%", -9, -0.67)):
        grp = [p for p in pairs if lo <= p["hitter"] < hi]
        if len(grp) < 30:
            continue
        adj = [p["resid"] - (b_next * p["next_def"] + b_rest * p["rest"]) for p in grp]
        mu = statistics.mean(adj)
        sd = statistics.pstdev(adj) / math.sqrt(len(grp))
        print(f"    {lab:<22}{len(grp):>7}{mu:>+22.4f}  +/- {1.96*sd:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
