#!/usr/bin/env python3
"""Gene's Rule, NFL: does a team that answers a touchdown turn out to be a good team, and
does answering tell you anything that ordinary scoring does not?

An OPPORTUNITY: the opponent scores a touchdown (offense, defense or return) and the very
next drive, in the same half with 2+ minutes left, is ours. ANSWERED: that drive ends in a
touchdown or field goal. The fair comparison is our OTHER drives that began with a kickoff
(after a field goal, or to open a half): same field position, no fresh wound.
"""
import csv, glob, json, os, random
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCORE = {"Touchdown", "Field goal"}


def load():
    games = defaultdict(list)
    for p in sorted(glob.glob(os.path.join(HERE, "data", "raw", "drives*.csv"))):
        for r in csv.DictReader(open(p)):
            r["drive"] = int(r["drive"]); r["half"] = int(r["half"])
            r["secs"] = float(r["secs"] or 0)
            games[r["game"]].append(r)
    for g in games.values():
        g.sort(key=lambda r: r["drive"])
    return games


def events(games):
    """Yield one record per qualifying drive: team, season, week, game, kind, scored, td."""
    out = []
    for gid, ds in games.items():
        nscores = 0  # scores before the current drive
        for i, d in enumerate(ds):
            before = nscores
            if d["half"] > 2 or d["secs"] < 120:
                kind = None
            else:
                prev = ds[i - 1] if i else None
                kind = "other"
                if prev and prev["half"] == d["half"]:
                    scorer = prev["off"] if prev["result"] == "Touchdown" else (prev["def"] if prev["result"] == "Opp touchdown" else None)
                    if scorer and scorer != d["off"]:
                        kind = "answer"
                    elif scorer == d["off"]:
                        kind = "other"
                if kind == "other" and d["start"] != "KICKOFF":
                    kind = "other_nk"  # began after a punt or turnover: different field position
                # Gene's original: the opponent's touchdown was the game's first score
                kind_first = kind == "answer" and before == 1
            if kind:
                out.append(dict(team=d["off"], season=int(d["season"]), week=int(d["week"]), game=gid, kind=kind,
                                first=kind == "answer" and kind_first, scored=d["result"] in SCORE,
                                td=d["result"] == "Touchdown", pts=0))
            if d["result"] in SCORE or d["result"] in ("Opp touchdown", "Safety"):
                nscores += 1
    return out


def results(games):
    """Per team-season: games, wins (ties half), point differential; by game too."""
    rec = {}
    for gid, ds in games.items():
        d = ds[-1]
        hs, as_ = float(d["home_score"]), float(d["away_score"])
        for t, f, a in ((d["home"], hs, as_), (d["away"], as_, hs)):
            rec[(t, int(d["season"]), gid)] = (int(d["week"]), 1.0 if f > a else (0.5 if f == a else 0.0), f - a)
    return rec


def rate(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def main():
    games = load()
    ev = events(games)
    rec = results(games)
    R = {}
    print(f"{len(games)} games, {len(ev)} qualifying drives\n")
    for k in ("answer", "other", "other_nk"):
        xs = [e for e in ev if e["kind"] == k]
        print(f"{k:9s} n={len(xs):6d}  scored {rate([e['scored'] for e in xs]):.3f}  TD {rate([e['td'] for e in xs]):.3f}")
    fx = [e for e in ev if e["first"]]
    print(f"first-TD answers n={len(fx)} scored {rate([e['scored'] for e in fx]):.3f}")
    R["league"] = {k: [len([e for e in ev if e["kind"] == k]), rate([e["scored"] for e in ev if e["kind"] == k])]
                   for k in ("answer", "other", "other_nk")}
    R["league"]["first"] = [len(fx), rate([e["scored"] for e in fx])]
    # same game, same opponent: answer drives vs that team's other kickoff drives
    gg = defaultdict(lambda: defaultdict(list))
    for e in ev:
        if e["kind"] in ("answer", "other"):
            gg[(e["game"], e["team"])][e["kind"]].append(e["scored"])
    both = [v for v in gg.values() if v["answer"] and v["other"]]
    a = np.mean([np.mean(v["answer"]) for v in both]); o = np.mean([np.mean(v["other"]) for v in both])
    print(f"same game, same opponent ({len(both)} team-games): answer {a:.3f}  other kickoff {o:.3f}")
    R["samegame"] = [len(both), a, o]
    # by era
    print("\nby season block: answer vs kickoff-other")
    for a, b in ((1999, 2005), (2006, 2012), (2013, 2019), (2020, 2026)):
        x = [e["scored"] for e in ev if e["kind"] == "answer" and a <= e["season"] <= b]
        y = [e["scored"] for e in ev if e["kind"] == "other" and a <= e["season"] <= b]
        print(f"  {a}-{b}: answer {rate(x):.3f} (n={len(x)})  other kickoff {rate(y):.3f} (n={len(y)})")

    # team-season table, split into the season's first and second halves by week
    ts = defaultdict(lambda: defaultdict(list))
    for e in ev:
        half = "A" if e["week"] <= 9 else "B"
        ts[(e["team"], e["season"])][e["kind"] + half].append(e["scored"])
        ts[(e["team"], e["season"])][e["kind"]].append(e["scored"])
        ts[(e["team"], e["season"])]["all" + half].append(e["scored"])
        ts[(e["team"], e["season"])]["all"].append(e["scored"])
    res = defaultdict(lambda: defaultdict(list))
    for (t, s, g), (w, win, pd) in rec.items():
        h = "A" if w <= 9 else "B"
        res[(t, s)]["win" + h].append(win); res[(t, s)]["pd" + h].append(pd)
        res[(t, s)]["win"].append(win); res[(t, s)]["pd"].append(pd)
    rows = []
    for key, d in ts.items():
        if key[1] == 2026:
            continue
        r = res[key]
        rows.append(dict(team=key[0], season=key[1], n_ans=len(d["answer"]), ans=rate(d["answer"]),
                         base=rate(d["other"] + d["other_nk"]), kick=rate(d["other"]),
                         win=rate(r["win"]), pd=rate(r["pd"]),
                         ansA=rate(d["answerA"]), baseA=rate(d["otherA"] + d["other_nkA"]), pdA=rate(r["pdA"]),
                         winA=rate(r["winA"]), winB=rate(r["winB"]), nA=len(d["answerA"])))
    X = {k: np.array([r[k] for r in rows]) for k in rows[0] if k != "team"}
    c = lambda a, b: np.corrcoef(a, b)[0, 1]
    print(f"\n{len(rows)} team-seasons 1999-2025; answer opportunities per season: median {np.median(X['n_ans']):.0f}")
    print(f"corr(answer rate, win%)          {c(X['ans'], X['win']):.2f}")
    print(f"corr(scoring on other drives, win%) {c(X['base'], X['win']):.2f}")
    print(f"corr(answer rate, other-drive rate) {c(X['ans'], X['base']):.2f}")
    prem = X["ans"] - X["base"]
    print(f"corr(answer premium, win%)        {c(prem, X['win']):.2f}")
    # how much of a season's answer rate is signal? split-half reliability by odd/even game
    # year to year
    by = {(r["team"], r["season"]): r for r in rows}
    pairs = [(by[k], by[(k[0], k[1] + 1)]) for k in by if (k[0], k[1] + 1) in by]
    for k in ("ans", "base", "win"):
        print(f"year-to-year r, {k:5s}: {c(np.array([a[k] for a, b in pairs]), np.array([b[k] for a, b in pairs])):.2f}")
    pa = np.array([a["ans"] - a["base"] for a, b in pairs]); pb = np.array([b["ans"] - b["base"] for a, b in pairs])
    print(f"year-to-year r, premium: {c(pa, pb):.2f}   ({len(pairs)} pairs)")

    # forecast: second-half win% from first-half numbers
    ok = ~np.isnan(X["ansA"]) & ~np.isnan(X["winB"]) & ~np.isnan(X["pdA"])
    y = X["winB"][ok]

    def r2(cols):
        A = np.column_stack([np.ones(ok.sum())] + [X[k][ok] if isinstance(k, str) else k[ok] for k in cols])
        b, *_ = np.linalg.lstsq(A, y, rcond=None)
        e = y - A @ b
        return 1 - e.var() / y.var()
    premA = X["ansA"] - X["baseA"]
    print("\npredicting weeks 10+ win% from weeks 1-9 (R^2):")
    for name, cols in (("point diff", ["pdA"]), ("answer rate", ["ansA"]), ("scoring on other drives", ["baseA"]),
                       ("point diff + answer rate", ["pdA", "ansA"]), ("point diff + premium", ["pdA", premA]),
                       ("win% so far", ["winA"])):
        print(f"  {name:28s} {r2(cols):.3f}")
    R["n_teamseasons"] = len(rows)
    R["corr"] = dict(ans_win=c(X["ans"], X["win"]), base_win=c(X["base"], X["win"]), prem_win=c(prem, X["win"]),
                     ans_base=c(X["ans"], X["base"]))
    R["yty"] = dict(ans=c(np.array([a["ans"] for a, b in pairs]), np.array([b["ans"] for a, b in pairs])),
                    base=c(np.array([a["base"] for a, b in pairs]), np.array([b["base"] for a, b in pairs])),
                    prem=c(pa, pb))
    R["fore"] = {n: r2(cs) for n, cs in (("pd", ["pdA"]), ("ans", ["ansA"]), ("pd_ans", ["pdA", "ansA"]), ("pd_prem", ["pdA", premA]))}
    json.dump(dict(R=R, rows=rows), open(os.path.join(HERE, "data", "nfl-results.json"), "w"), indent=0, default=float)


if __name__ == "__main__":
    main()
