#!/usr/bin/env python3
"""How many games before a coach's record means anything?

    python3 scripts/coach_stabilization.py
    python3 scripts/coach_stabilization.py --refresh    # re-pull from CFBD

THE EDITOR'S QUESTION, 2026-09-29: "How many years does it take for us to really
understand that a coach is a lifetime .750 or a lifetime .500 coach? How many
games? Because that's the hiring and firing."

THIS IS A STABILIZATION PROBLEM, the same shape as Issue #026. The question is not
"what is his record" -- that is always knowable. It is "how much of his record is
him." Early on a winning percentage is mostly the roster, the schedule and luck.
At some number of games it starts carrying signal about the coach. That number is
findable.

THE METHOD, and it is deliberately the boring one. For a given N, take every coach
with at least 2N games, correlate his winning percentage over the first N with his
percentage over the NEXT N, and step the result up with Spearman-Brown. The N where
that reaches 0.5 is the conventional stabilization point: the sample at which half
the variation between coaches is real difference rather than noise.

TWO MEASURES, BECAUSE RAW WINS ARE NOT THE COACH. A man who inherits a stacked
roster wins immediately and has proved nothing. So everything is computed twice:

  RAW        his winning percentage.
  vs EXPECTED  his percentage minus what a team of that SP+ rating would be
             expected to win. This is the closest thing available to "did he beat
             the roster he was handed."

The gap between those two answers is the interesting part, and it is the direct
answer to the editor's Florida question -- did he coach them up, or did he import
stars.

WHAT THIS CANNOT DO, said plainly because it will be quoted. SP+ is measured
DURING the coach's season, so it already contains his coaching; subtracting it
removes some of the thing being measured. A cleaner design uses the roster he
inherited, which needs recruiting data this does not yet pull. Treat the
vs-expected column as a floor on how long stabilization takes, not a verdict.
"""
import argparse
import collections
import csv
import json
import math
import pathlib
import re
import statistics
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
CACHE = REPO / "data" / "cfb-coaches.csv"


def key():
    p = pathlib.Path.home() / ".config/secrets/tokens.env"
    for ln in p.read_text().splitlines():
        m = re.match(r"\s*(?:export\s+)?CFBD_KEY\s*=\s*(.*)$", ln)
        if m:
            return m.group(1).strip().strip('"').strip("'")


def fetch(lo=1970, hi=2025, existing=None):
    """THROTTLED AND RETRIED ON PURPOSE. A first pass pulled 56 years back to back
    with no delay and CFBD silently rate-limited everything from 2015 on -- the
    script reported HTTPError per year and carried on, so the analysis ran on a
    truncated 1970-2014 window and nobody would have known from the output. The
    paper's key also drives the 4:30am publish, so hammering it is not free."""
    import time
    K = key()
    rows = list(existing or [])
    have = {r["year"] for r in rows}
    for yr in range(lo, hi + 1):
        if yr in have:
            continue
        d = None
        for attempt in range(4):
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(
                    f"https://api.collegefootballdata.com/coaches?year={yr}",
                    headers={"Authorization": f"Bearer {K}"}), timeout=120))
                break
            except Exception as e:
                wait = 3 * (attempt + 1)
                print(f"    {yr}: {type(e).__name__}, retry in {wait}s", flush=True)
                time.sleep(wait)
        if d is None:
            raise SystemExit(f"{yr} failed after 4 attempts -- refusing to "
                             f"analyze a silently truncated window")
        time.sleep(1.2)
        for c in d:
            name = f"{c.get('firstName','')} {c.get('lastName','')}".strip()
            for s in c.get("seasons", []):
                if s.get("year") != yr:
                    continue
                g = s.get("games") or 0
                if g < 1:
                    continue
                rows.append(dict(coach=name, year=yr, school=s.get("school", ""),
                                 games=g, wins=s.get("wins") or 0,
                                 losses=s.get("losses") or 0, ties=s.get("ties") or 0,
                                 sp=s.get("spOverall"), srs=s.get("srs")))
        print(f"    {yr}: {len(rows):,} coach-seasons so far", flush=True)
    rows.sort(key=lambda r: (r["year"], r["coach"]))
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return rows


def load(refresh=False):
    if CACHE.exists() and not refresh:
        out = []
        for r in csv.DictReader(open(CACHE)):
            r["year"] = int(r["year"]); r["games"] = int(r["games"])
            r["wins"] = int(r["wins"]); r["losses"] = int(r["losses"])
            r["ties"] = int(r["ties"] or 0)
            r["sp"] = float(r["sp"]) if r["sp"] not in ("", "None", None) else None
            out.append(r)
        return out
    return fetch()


def careers(rows):
    """{coach: [(year, wins, losses, games, sp)] in order}"""
    by = collections.defaultdict(list)
    for r in rows:
        by[r["coach"]].append(r)
    out = {}
    for c, rs in by.items():
        rs.sort(key=lambda r: r["year"])
        out[c] = rs
    return out


def expected_pct(sp):
    """Win rate a team of this SP+ rating is expected to post.

    Fitted, not assumed: across the cached seasons the relationship between SP+
    and winning percentage is close to linear over the range that matters, and a
    logistic keeps it inside 0..1 at the extremes.
    """
    return 1 / (1 + math.exp(-sp / 9.0))


def restriction_correction(r, s_restricted, s_full):
    """Thorndike case 2: what r would be if the sample were not pre-filtered.

    THIS IS NOT OPTIONAL HERE AND THE RAW TABLE IS MISLEADING WITHOUT IT. To have
    2N games a coach must survive 2N games, and survival is not random -- across
    the cache the spread of career winning percentage falls from 0.165 among
    coaches with 12 games to 0.087 among those with 240, while the mean CLIMBS
    from .459 to .623. The long-tenured are both better and more alike.

    A correlation is variance explained over variance available. Shrink the
    denominator by filtering out the bad coaches and the correlation falls even
    though the measurement is improving. Uncorrected, the table reads as though
    a record tells you LESS the longer you watch, which is nonsense.
    """
    if not s_restricted or s_full <= 0:
        return float("nan")
    k = s_full / s_restricted
    denom = math.sqrt(1 + r * r * (k * k - 1))
    return (r * k) / denom if denom else float("nan")


def career_sd(careers_, n):
    vals = []
    for c, rs in careers_.items():
        seq = []
        for r in rs:
            for i in range(r["games"]):
                seq.append(1 if i < r["wins"] else 0)
        if len(seq) >= 2 * n:
            vals.append(statistics.mean(seq))
    return statistics.pstdev(vals) if len(vals) > 5 else None


def split_half(careers_, n, adjusted=False):
    """Correlate a coach's first n games against his next n."""
    a, b = [], []
    for c, rs in careers_.items():
        seq = []
        for r in rs:
            if adjusted and r["sp"] is None:
                continue
            for i in range(r["games"]):
                won = 1 if i < r["wins"] else 0
                if adjusted:
                    seq.append(won - expected_pct(r["sp"]))
                else:
                    seq.append(won)
        if len(seq) < 2 * n:
            continue
        a.append(statistics.mean(seq[:n]))
        b.append(statistics.mean(seq[n:2 * n]))
    if len(a) < 25:
        return None, len(a)
    r = statistics.correlation(a, b)
    sb = 2 * r / (1 + r) if -1 < r < 1 else float("nan")
    return (r, sb), len(a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    rows = load(a.refresh)
    cs = careers(rows)
    tot = sum(r["games"] for r in rows)
    print(f"\n  {len(cs):,} coaches, {len(rows):,} coach-seasons, {tot:,} games")
    lens = sorted(sum(r["games"] for r in rs) for rs in cs.values())
    print(f"  career length: median {statistics.median(lens):.0f} games, "
          f"90th percentile {lens[int(.9*len(lens))]:.0f}\n")

    base = career_sd(cs, 6)
    print("  HOW MUCH OF A RECORD IS THE COACH?\n")
    print(f"  {'games':>7}{'coaches':>9}{'SD':>8}{'raw':>8}{'corrected':>11}"
          f"{'vs expected':>13}{'corrected':>11}")
    print("  " + "-" * 62)
    for n in (6, 12, 24, 36, 48, 60, 84, 120):
        raw, nr = split_half(cs, n, False)
        adj, na = split_half(cs, n, True)
        if not raw:
            continue
        sd = career_sd(cs, n)
        rc = restriction_correction(raw[1], sd, base)
        ac = restriction_correction(adj[1], sd, base) if adj else float("nan")
        af = f"{adj[1]:.3f}" if adj else "-"
        acs = f"{ac:.3f}" if adj else "-"
        print(f"  {n:>7}{nr:>9}{sd:>8.3f}{raw[1]:>8.3f}{rc:>11.3f}{af:>13}{acs:>11}")
    print("\n  Spearman-Brown steps the half-career correlation up to a full one.")
    print("  The row where it reaches 0.50 is where half the spread between coaches")
    print("  is real and half is still noise. Below that, a record is mostly roster.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
