#!/usr/bin/env python3
"""Do runs go up after a pitching change? Compared with what the situation was already worth.

The editor's bet (2026-10-19): runs rise after a change in innings 4-6, not in
the 8th and 9th.

THE TRAP is selection. A pitcher is pulled in the middle of an inning mostly
when he is being hit, so the new man walks into runners on base. Runs in the
rest of that inning will look high next to an ordinary inning even if the new
pitcher is perfectly average. So the naive comparison (runs after the change vs
an average half-inning) is printed first, as the warning, and then the fair one:

  FAIR = runs actually scored from the change to the end of the inning
         minus the RUN EXPECTANCY of the base-out state he inherited
         (RE24, built from the same seasons: for every state with 0/1/2 outs
          and the eight base patterns, the average runs scored from that point
          to the end of the half-inning).

A positive gap means the new pitcher allowed more than an average pitcher would
from the same spot; negative means fewer.

Two kinds of change are reported separately:
  * MID-INNING: a new pitcher takes over with 0-2 outs (the state is inherited)
  * NEW INNING: a new pitcher starts a half-inning (state = 0 outs, empty)

Data: MLB Stats API play-by-play, regular season, 2023-2025 (the pitch-clock
era, so all three seasons share the extra-inning runner rule and the rules on
pickoffs). Per-game summaries are cached under ~/.cache/sports-page/mlb-pbp.
Output: data/mlb/pitching_change_runs.txt

Limits (also in the piece):
  * Extra innings are left out (they start with a runner on second), and so is
    the bottom of the 9th (a walk-off ends the inning early, which would cut
    runs short). The 9th means the TOP of the 9th.
  * A change is detected when the pitcher of record differs from the previous
    plate appearance in the same half-inning; the state is the one at the end
    of that previous plate appearance. A runner who moves on a steal before the
    first pitch of the new man is counted in the new man's runs.
  * Runs are runs, earned or not. An inherited runner who scores counts here,
    because the question is runs for the team, not the pitcher's ERA.
  * Intervals are 95% bootstrap ranges, resampling whole games.

  python3 scripts/pitching_change_runs.py --fetch     # download (polite, cached)
  python3 scripts/pitching_change_runs.py             # analyze the cache
"""
import argparse, collections, json, pathlib, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = pathlib.Path.home() / ".cache/sports-page/mlb-pbp"
OUT = ROOT / "data/mlb/pitching_change_runs.txt"
SEASONS = (2023, 2024, 2025)
API = "https://statsapi.mlb.com/api/v1"
BASES = {"1B": 1, "2B": 2, "3B": 4}


def get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 + 3 * i)
    raise RuntimeError(url)


def summarize(pbp):
    """Half-innings as lists of plate appearances: [pitcher, outs_before, bases_before, runs_on_play]."""
    halves, cur, key = [], None, None
    away = home = 0
    for p in pbp.get("allPlays", []):
        a = p["about"]
        k = (a["inning"], a["isTopInning"])
        if k != key:
            if cur:
                halves.append(cur)
            key, cur = k, {"inn": a["inning"], "top": a["isTopInning"], "pa": [], "outs": 0}
            outs, bases = 0, {}
        r = p["result"]
        ra, rh = r.get("awayScore", away), r.get("homeScore", home)
        runs = (ra - away) if a["isTopInning"] else (rh - home)
        away, home = ra, rh
        mask = sum(BASES[b] for b in bases.values())
        cur["pa"].append([p["matchup"]["pitcher"]["id"], outs, mask, runs])
        # base state after the play: each runner's last movement wins
        where = dict(bases)  # runner id -> base
        for m in p.get("runners", []):
            rid = m["details"]["runner"]["id"]
            end = m["movement"].get("end")
            where[rid] = end if (not m["movement"].get("isOut") and end in BASES) else None
        bases = {rid: b for rid, b in where.items() if b}
        outs = p["count"]["outs"]
        cur["outs"] = outs
    if cur:
        halves.append(cur)
    return halves


def fetch():
    CACHE.mkdir(parents=True, exist_ok=True)
    pks = []
    for y in SEASONS:
        d = get(f"{API}/schedule?sportId=1&season={y}&gameType=R")
        for day in d["dates"]:
            for g in day["games"]:
                if g["status"]["detailedState"] in ("Final", "Completed Early", "Game Over"):
                    pks.append((y, g["gamePk"]))
    pks = sorted(set(pks))
    todo = [(y, pk) for y, pk in pks if not (CACHE / f"{pk}.json").exists()]
    print(f"{len(pks)} games, {len(todo)} to fetch", file=sys.stderr)

    def one(item):
        y, pk = item
        h = summarize(get(f"{API}/game/{pk}/playByPlay"))
        (CACHE / f"{pk}.json").write_text(json.dumps({"season": y, "halves": h}))
        time.sleep(0.15)

    with ThreadPoolExecutor(4) as ex:
        for i, _ in enumerate(ex.map(one, todo)):
            if i % 500 == 0:
                print(f"  {i}/{len(todo)}", file=sys.stderr)


def usable(h):
    # regulation, complete half-innings; the 9th means the top of the 9th
    return h["outs"] == 3 and (h["inn"] <= 8 or (h["inn"] == 9 and h["top"]))


def analyze():
    games = []
    for f in sorted(CACHE.glob("*.json")):
        g = json.loads(f.read_text())
        if g["season"] in SEASONS:
            games.append([h for h in g["halves"] if usable(h)])
    say_lines = []
    say = lambda s="": (print(s), say_lines.append(s))

    # RE24 from every plate appearance in usable half-innings
    tot, cnt = collections.Counter(), collections.Counter()
    for halves in games:
        for h in halves:
            pa = h["pa"]
            rest = np.cumsum([p[3] for p in pa][::-1])[::-1]
            for p, r in zip(pa, rest):
                tot[(p[1], p[2])] += r
                cnt[(p[1], p[2])] += 1
    RE = {s: tot[s] / cnt[s] for s in cnt}
    say(f"{len(games)} games, {sum(len(h) for h in games)} usable half-innings, seasons {SEASONS[0]}-{SEASONS[-1]}")
    say("RE24 (runs to end of inning):  bases 0=empty 1=1B 2=2B 4=3B, summed")
    for o in range(3):
        say("  outs %d: " % o + "  ".join(f"{b}:{RE[(o, b)]:.2f}" for b in range(8)))
    avg_half = RE[(0, 0)]

    # every pitching change, per game: (kind, inning, actual, expected)
    rows = []
    for gi, halves in enumerate(games):
        for h in halves:
            pa = h["pa"]
            rest = np.cumsum([p[3] for p in pa][::-1])[::-1]
            for i, p in enumerate(pa):
                if i == 0:
                    continue  # a new-inning change is found by comparing with the previous half (below)
                if p[0] != pa[i - 1][0]:
                    rows.append((gi, "mid", h["inn"], rest[i], RE[(p[1], p[2])], p[1], p[2]))
        # new-inning changes: pitcher of the first PA differs from the last PA of the same team's previous defensive half
        last = {}
        for h in sorted(halves, key=lambda h: (h["inn"], not h["top"])):
            side = h["top"]
            first = h["pa"][0][0]
            if side in last and last[side] != first and h["inn"] == last.get(("inn", side), 0) + 1:
                rows.append((gi, "new", h["inn"], sum(p[3] for p in h["pa"]), RE[(0, 0)], 0, 0))
            last[side], last[("inn", side)] = h["pa"][-1][0], h["inn"]
    R = np.array([(r[0], 1 if r[1] == "mid" else 0, r[2], r[3], r[4], r[5], r[6]) for r in rows], float)
    rng = np.random.default_rng(20261104)
    G = len(games)
    boot = [rng.integers(0, G, G) for _ in range(2000)]

    def ci(mask, val):
        idx = R[mask, 0].astype(int)
        v = val[mask]
        by = np.bincount(idx, weights=v, minlength=G)
        n = np.bincount(idx, minlength=G)
        est = by.sum() / n.sum()
        bs = [by[b].sum() / max(n[b].sum(), 1) for b in boot]
        return est, np.percentile(bs, 2.5), np.percentile(bs, 97.5), int(mask.sum())

    gap = R[:, 3] - R[:, 4]
    groups = [("1-3", (1, 3)), ("4-6", (4, 6)), ("7", (7, 7)), ("8", (8, 8)), ("9 (top)", (9, 9))]
    for kind, k in (("MID-INNING changes", 1), ("NEW-INNING changes", 0)):
        say(f"\n{kind}")
        say("  inning   n      runs after   expected   naive vs avg inning   FAIR gap (95%)")
        for lab, (lo, hi) in groups:
            m = (R[:, 1] == k) & (R[:, 2] >= lo) & (R[:, 2] <= hi)
            if m.sum() < 30:
                continue
            a = ci(m, R[:, 3]); e = ci(m, R[:, 4]); g = ci(m, gap)
            say(f"  {lab:8s} {a[3]:6d}   {a[0]:.2f}        {e[0]:.2f}       {a[0] - avg_half:+.2f}              "
                f"{g[0]:+.3f} ({g[1]:+.3f} to {g[2]:+.3f})")
        m = R[:, 1] == k
        g = ci(m, gap); a = ci(m, R[:, 3])
        say(f"  all      {g[3]:6d}   {a[0]:.2f}        {ci(m, R[:, 4])[0]:.2f}       {a[0] - avg_half:+.2f}              "
            f"{g[0]:+.3f} ({g[1]:+.3f} to {g[2]:+.3f})")

    # mid-inning: share inheriting runners, and the state mix
    mid = R[:, 1] == 1
    say(f"\nMid-inning changes inheriting at least one runner: {np.mean(R[mid, 6] > 0):.0%}")
    say(f"Average half-inning (RE at 0 outs, empty): {avg_half:.3f} runs")
    say(f"Games with at least one change of either kind: {len(set(R[:, 0].astype(int)))} of {G}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(say_lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    if a.fetch:
        fetch()
    analyze()
