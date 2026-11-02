#!/usr/bin/env python3
"""Staff drain: does a head coach fall off after his assistants leave?

The reverse of scripts/coach_tree.py. That script asked whether assistants of
winners win (answer: within role, the boss adds nothing). This one asks the
editor's 2026-11-02 question: are some head coaches "propped up" by a staff,
so that when the staff is hired away the head coach is exposed?

Event: an assistant on head coach B's FBS staff leaves to take his FIRST FBS
head job (the edges in data/coachtree/prior_jobs.csv, high confidence only).
Season Y = the assistant's last season with B. Outcome: B's win% at the same
school in Y+1, against every other B-season that had no such departure.

The trap is regression to the mean. Staffs get raided after GOOD seasons, and
any team coming off a good season tends to slip, raid or no raid. So the naive
"he lost his coordinators and fell off" comparison is printed first, then the
fair one: next season regressed on this season and the three before it.

What the data cannot see, stated so nobody over-reads it:
  * departures to the NFL, to coordinator jobs elsewhere, or to a second head
    job (Joe Brady left LSU for the Panthers' staff; he is not in here);
  * who replaced them. A raid with a good replacement looks like no raid.

No network calls: reads data/coachtree/prior_jobs.csv and
data/almamater/seasons.csv. Writes data/coachtree/drain.txt.
"""
import csv, pathlib, random
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "coachtree" / "drain.txt"
SEED, NBOOT = 20261102, 10_000


def pct(w, l, t):
    g = w + l + t
    return (w + t / 2) / g if g else None


def ols(X, y):
    """Least squares with intercept; returns coefficients (intercept first)."""
    import numpy as np
    A = np.column_stack([np.ones(len(y))] + [np.asarray(c, float) for c in X])
    b, *_ = np.linalg.lstsq(A, np.asarray(y, float), rcond=None)
    return b


def main():
    seasons = defaultdict(dict)          # (cid, school) -> {year: pct}
    cid_of = {}
    for x in csv.DictReader(open(REPO / "data/almamater/seasons.csv")):
        p = pct(int(x["w"]), int(x["l"]), int(x["t"] or 0))
        if p is None:
            continue
        seasons[(x["cid"], x["school"])][int(x["year"])] = p
        cid_of[(x["first"] + " " + x["last"]).strip()] = x["cid"]

    # departure events: (boss cid, school, last season with boss) -> list of roles
    events = defaultdict(list)
    for r in csv.DictReader(open(REPO / "data/coachtree/prior_jobs.csv")):
        if (r["parse_confidence"] != "high" or r["prior_level"] != "FBS"
                or r["prior_role_class"] not in ("coordinator", "position")
                or r["boss"] not in cid_of or r["first_hc_interim"] == "yes"):
            continue
        last = int(r["prior_years"].split("-")[-1])
        if int(r["first_hc_year"]) - last > 1:
            continue
        events[(cid_of[r["boss"]], r["prior_school"], last)].append(
            (r["prior_role_class"], r["coach"]))

    # every boss-season with a next season and 1-3 before it at the same school (mean of those)
    rows = []
    for (cid, sch), yp in seasons.items():
        for y, p in yp.items():
            back = [yp[y - k] for k in (1, 2, 3) if y - k in yp]
            if y < 1969 or y + 1 not in yp or not back:
                continue
            ev = events.get((cid, sch, y), [])
            nxt3 = sum(yp[y + k] for k in (1, 2, 3)) / 3 if all(y + k in yp for k in (1, 2, 3)) else None
            rows.append(dict(cid=cid, sch=sch, y=y, now=p, nxt=yp[y + 1], nxt3=nxt3,
                             prior3=sum(back) / len(back),
                             n=len(ev), coord=sum(e[0] == "coordinator" for e in ev),
                             who=[e[1] for e in ev]))
    used = {(r["cid"], r["sch"], r["y"]) for r in rows}
    lost = [k for k in events if k not in used]

    rng = random.Random(SEED)

    def effect(sel):
        X = [[r["now"] for r in sel], [r["prior3"] for r in sel], [int(r["n"] > 0) for r in sel]]
        return ols(X, [r["nxt"] for r in sel])

    def boot(fn, sel):
        vals = sorted(fn([sel[rng.randrange(len(sel))] for _ in sel]) for _ in range(NBOOT))
        return vals[int(.025 * NBOOT)], vals[int(.975 * NBOOT)]

    L = []
    hit = [r for r in rows if r["n"] > 0]
    miss = [r for r in rows if r["n"] == 0]
    m = lambda v: sum(v) / len(v)
    L.append("STAFF DRAIN -- does a head coach fall off after an assistant leaves for a first FBS head job?")
    L.append("Boss-seasons 1969-2024 with 1-3 prior seasons and a next season at the same school: %d" % len(rows))
    L.append("Seasons where >=1 assistant left: %d (raids not usable: %d, mostly because the boss left too)\n" % (len(hit), len(lost)))
    L.append("THE NAIVE VIEW (what fans see)")
    L.append("  win%% the raided season        %.3f   vs others %.3f" % (m([r["now"] for r in hit]), m([r["now"] for r in miss])))
    L.append("  win%% the season after         %.3f   vs others %.3f" % (m([r["nxt"] for r in hit]), m([r["nxt"] for r in miss])))
    d_hit, d_miss = m([r["nxt"] - r["now"] for r in hit]), m([r["nxt"] - r["now"] for r in miss])
    L.append("  change, raided vs not          %+.1f vs %+.1f pts" % (100 * d_hit, 100 * d_miss))
    b = effect(rows)
    lo, hi = boot(lambda s: effect(s)[3], rows)
    L.append("\nTHE FAIR VIEW: next ~ this season + prior 3 + raided")
    L.append("  slope on this season %.2f, on prior 3 %.2f" % (b[1], b[2]))
    L.append("  raided effect %+.1f pts (95%% CI %+.1f to %+.1f)" % (100 * b[3], 100 * lo, 100 * hi))

    # good seasons only: compare like with like
    good = [r for r in rows if r["now"] >= .75]
    gh, gm = [r for r in good if r["n"]], [r for r in good if not r["n"]]
    L.append("\nLIKE WITH LIKE: seasons at .750 or better")
    L.append("  raided n=%d  next %.3f   not raided n=%d  next %.3f" % (len(gh), m([r["nxt"] for r in gh]), len(gm), m([r["nxt"] for r in gm])))

    # dose: two or more gone, or coordinators specifically
    for label, f in (("2+ assistants gone", lambda r: r["n"] >= 2), ("a coordinator gone", lambda r: r["coord"] >= 1)):
        sel = [r for r in rows if r["n"] == 0 or f(r)]
        X = [[r["now"] for r in sel], [r["prior3"] for r in sel], [int(f(r)) for r in sel]]
        bb = ols(X, [r["nxt"] for r in sel])
        lo, hi = boot(lambda s: ols([[r["now"] for r in s], [r["prior3"] for r in s], [int(f(r)) for r in s]],
                                    [r["nxt"] for r in s])[3], sel)
        L.append("  %-22s n=%3d  effect %+.1f pts (95%% CI %+.1f to %+.1f)" % (label, sum(map(f, sel)), 100 * bb[3], 100 * lo, 100 * hi))

    # slow erosion: the editor's Bowden point is about the years after, not the year after
    r3 = [r for r in rows if r["nxt3"] is not None]
    f3 = lambda s: ols([[r["now"] for r in s], [r["prior3"] for r in s], [int(r["n"] > 0) for r in s]],
                       [r["nxt3"] for r in s])[3]
    lo, hi = boot(f3, r3)
    L.append("\nSLOW EROSION: average of the next THREE seasons, same model")
    L.append("  n=%d (raided %d)  raided effect %+.1f pts (95%% CI %+.1f to %+.1f)"
             % (len(r3), sum(r["n"] > 0 for r in r3), 100 * f3(r3), 100 * lo, 100 * hi))
    g3 = [r for r in r3 if r["now"] >= .75]
    L.append("  .750+ seasons: next-3 avg raided %.3f (n=%d) vs not %.3f (n=%d)"
             % (m([r["nxt3"] for r in g3 if r["n"]]), sum(1 for r in g3 if r["n"]),
                m([r["nxt3"] for r in g3 if not r["n"]]), sum(1 for r in g3 if not r["n"])))
    L.append("\nNAMED CASES (boss, school, season, who left, win% that season -> next)")
    for r in sorted(hit, key=lambda r: (-r["n"], r["y"])):
        if r["n"] >= 2 or any(n in " ".join(r["who"]) for n in ("Elliott", "Venables", "Aranda", "Richt", "Amato", "Silverfield", "Smart")):
            L.append("  %s %-16s %d  %-40s %.3f -> %.3f" % (r["cid"], r["sch"], r["y"], ", ".join(r["who"])[:40], r["now"], r["nxt"]))
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
