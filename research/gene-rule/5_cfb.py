#!/usr/bin/env python3
"""Gene's Rule, college football (FBS vs FBS, regular season), from CFBD drives.

Same definitions as the NFL (1_nfl.py):
  CHANCE   the drive right after the other team scores a touchdown (offense, defense or
           return), same half, 2+ minutes left in the half, and the drive is ours.
  ANSWERED that drive ends in a touchdown or field goal.
  FAIR     the same team's other drives that began with a kickoff: the game's first drive,
           the first drive of the second half, or a drive right after the other team's FG.

CFBD drives carry no "how the drive started" field, so scoring between drives is read from
the score at the start of each drive (it catches return touchdowns, which happen between
offensive drives). A game is kept only if both teams are FBS and the score after its last
drive matches the final score in CFBD's games table (overtime games: the score at the end
of regulation must be level).

Reads the caches written by 0_cfb_drives.py. Writes data/cfb-results.json.
"""
import gzip, json, os, sys
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
YEARS = range(2014, 2027)


def secs_left(d):
    t = d["startTime"]
    s = (t.get("minutes") or 0) * 60 + (t.get("seconds") or 0)
    return s + (900 if d["startPeriod"] in (1, 3) else 0)


def load(years=YEARS):
    """Return {gameId: dict(season, week, home, away, hp, ap, drives=[...])} for clean FBS-FBS games."""
    out, dropped = {}, defaultdict(int)
    for y in years:
        p = os.path.join(RAW, f"cfb-drives-{y}-regular.json.gz")
        if not os.path.exists(p):
            continue
        drives = json.load(gzip.open(p, "rt"))
        games = {g["id"]: g for g in json.load(gzip.open(os.path.join(RAW, f"cfb-games-{y}-regular.json.gz"), "rt"))}
        by = defaultdict(list)
        for d in drives:
            by[d["gameId"]].append(d)
        for gid, ds in by.items():
            g = games.get(gid)
            if not g or g.get("homeClassification") != "fbs" or g.get("awayClassification") != "fbs":
                dropped["not FBS-FBS"] += 1
                continue
            if not g.get("completed") or g.get("homePoints") is None:
                dropped["not completed"] += 1
                continue
            ds.sort(key=lambda d: d["driveNumber"])
            for d in ds:
                d["hs"] = d["startOffenseScore"] if d["isHomeOffense"] else d["startDefenseScore"]
                d["as"] = d["startDefenseScore"] if d["isHomeOffense"] else d["startOffenseScore"]
                d["he"] = d["endOffenseScore"] if d["isHomeOffense"] else d["endDefenseScore"]
                d["ae"] = d["endDefenseScore"] if d["isHomeOffense"] else d["endOffenseScore"]
            last = ds[-1]
            hp, ap = g["homePoints"], g["awayPoints"]
            reg = [d for d in ds if d["startPeriod"] <= 4]
            ok = (last["he"], last["ae"]) == (hp, ap)
            if not ok and reg and len(g.get("homeLineScores") or []) > 4:
                ok = reg[-1]["he"] == reg[-1]["ae"]  # overtime: regulation ended level
            if not ok:
                dropped["final score mismatch"] += 1
                continue
            out[gid] = dict(season=y, week=g["week"], home=g["homeTeam"], away=g["awayTeam"], hp=hp, ap=ap,
                            date=g["startDate"], drives=ds)
    return out, dropped


def events(games):
    ev = []
    for gid, G in games.items():
        ds = [d for d in G["drives"] if d["startPeriod"] <= 4]
        for i, d in enumerate(ds):
            if d["offense"] not in (G["home"], G["away"]):
                continue
            half = 1 if d["startPeriod"] <= 2 else 2
            if secs_left(d) < 120:
                continue
            me_home = d["offense"] == G["home"]
            kind = "other_nk"
            first = False
            if i == 0 or (half == 2 and ds[i - 1]["startPeriod"] <= 2):
                kind = "other"  # opening kickoff of a half
            else:
                p = ds[i - 1]
                if (1 if p["startPeriod"] <= 2 else 2) == half:
                    # points scored since the previous drive began. Scores only go up, so the
                    # baseline is the LOWER of two readings: the previous drive's start score and
                    # the end score of the drive before that. CFBD sometimes folds a return
                    # touchdown into a start score, and sometimes writes the next score into an
                    # end score; checked against ESPN drive charts in 6_cfb_verify_espn.py.
                    b = ds[i - 2] if i >= 2 else None  # across halftime is fine: no one scores at the break
                    bh, ba = (min(b["he"], p["hs"]), min(b["ae"], p["as"])) if b else (p["hs"], p["as"])
                    gh, ga = d["hs"] - bh, d["as"] - ba
                    them, us = (ga, gh) if me_home else (gh, ga)
                    if them >= 6 and us == 0:
                        kind = "answer"
                        first = bh + ba == 0
                    elif them == 3 and us == 0:
                        kind = "other"  # kickoff after their field goal
            nxt = ds[i + 1] if i + 1 < len(ds) else None
            # did this drive score? CFBD's result label, cross-checked with the score change
            lab = d["driveResult"] in ("TD", "FG")
            gain = (d["he"] - d["hs"]) if me_home else (d["ae"] - d["as"])
            scored = lab or gain >= 3
            margin = (d["hs"] - d["as"]) if me_home else (d["as"] - d["hs"])
            ev.append(dict(team=d["offense"], season=G["season"], week=G["week"], game=gid, kind=kind, margin=margin,
                           first=first, scored=scored, td=d["driveResult"] == "TD" or gain >= 6, lab=lab, gain=gain))
    return ev


def results(games):
    rec = {}
    for gid, G in games.items():
        for t, f, a in ((G["home"], G["hp"], G["ap"]), (G["away"], G["ap"], G["hp"])):
            rec[(t, G["season"], gid)] = (G["week"], 1.0 if f > a else (0.5 if f == a else 0.0), f - a)
    return rec


def rate(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def main():
    games, dropped = load()
    ev = events(games)
    rec = results(games)
    R = {"games": len(games), "dropped": dict(dropped)}
    print(f"{len(games)} clean FBS-vs-FBS games; dropped {dict(dropped)}; {len(ev)} qualifying drives")
    agree = np.mean([e["lab"] == (e["gain"] >= 3) for e in ev])
    print(f"drive label vs score change agree on {agree:.4f} of drives")
    R["label_agree"] = agree
    hist = [e for e in ev if e["season"] <= 2025]
    for k in ("answer", "other", "other_nk"):
        xs = [e for e in hist if e["kind"] == k]
        print(f"{k:9s} n={len(xs):6d}  scored {rate([e['scored'] for e in xs]):.3f}  TD {rate([e['td'] for e in xs]):.3f}")
    R["league"] = {k: [len([e for e in hist if e["kind"] == k]), rate([e["scored"] for e in hist if e["kind"] == k]),
                       rate([e["td"] for e in hist if e["kind"] == k])] for k in ("answer", "other", "other_nk")}
    gg = defaultdict(lambda: defaultdict(list))
    for e in hist:
        if e["kind"] in ("answer", "other"):
            gg[(e["game"], e["team"])][e["kind"]].append(e["scored"])
    both = [v for v in gg.values() if v["answer"] and v["other"]]
    a = np.mean([np.mean(v["answer"]) for v in both]); o = np.mean([np.mean(v["other"]) for v in both])
    print(f"same game, same opponent ({len(both)} team-games): answer {a:.3f}  other kickoff {o:.3f}")
    R["samegame"] = [len(both), a, o]
    # the gap is bigger than the NFL's; how much of it is the scoreboard? An answer drive
    # usually starts further behind. Reweight the kickoff drives to the answer drives' mix of
    # score margins (bins of a score or so).
    bins = ((-99, -22), (-21, -15), (-14, -8), (-7, -1), (0, 0), (1, 7), (8, 14), (15, 99))
    ans = [e for e in hist if e["kind"] == "answer"]; oth = [e for e in hist if e["kind"] == "other"]
    adj, w = 0.0, 0
    for lo, hi in bins:
        a_ = [e["scored"] for e in ans if lo <= e["margin"] <= hi]
        o_ = [e["scored"] for e in oth if lo <= e["margin"] <= hi]
        if a_ and o_:
            adj += len(a_) * rate(o_); w += len(a_)
            print(f"  margin {lo:+d}..{hi:+d}: answer {rate(a_):.3f} (n={len(a_)})  kickoff {rate(o_):.3f} (n={len(o_)})")
    print(f"kickoff drives at the answer drives' score margins: {adj / w:.3f} (answer {rate([e['scored'] for e in ans]):.3f}); "
          f"mean margin answer {np.mean([e['margin'] for e in ans]):+.1f}, kickoff {np.mean([e['margin'] for e in oth]):+.1f}")
    R["margin_adj"] = dict(answer=rate([e["scored"] for e in ans]), other_at_answer_margins=adj / w,
                           mean_margin_answer=float(np.mean([e["margin"] for e in ans])),
                           mean_margin_other=float(np.mean([e["margin"] for e in oth])))
    print("\nby season: answer vs kickoff-other")
    R["by_season"] = {}
    for y in YEARS:
        x = [e["scored"] for e in ev if e["kind"] == "answer" and e["season"] == y]
        z = [e["scored"] for e in ev if e["kind"] == "other" and e["season"] == y]
        if x:
            print(f"  {y}: answer {rate(x):.3f} (n={len(x)})  other kickoff {rate(z):.3f} (n={len(z)})")
            R["by_season"][y] = [len(x), rate(x), len(z), rate(z)]

    # team-season table (weeks 1-7 vs 8+ for the forecast)
    ts = defaultdict(lambda: defaultdict(list))
    for e in hist:
        h = "A" if e["week"] <= 7 else "B"
        k = (e["team"], e["season"])
        ts[k][e["kind"] + h].append(e["scored"]); ts[k][e["kind"]].append(e["scored"])
    res = defaultdict(lambda: defaultdict(list))
    for (t, s, g), (w, win, pd) in rec.items():
        h = "A" if w <= 7 else "B"
        res[(t, s)]["win" + h].append(win); res[(t, s)]["pd" + h].append(pd)
        res[(t, s)]["win"].append(win); res[(t, s)]["pd"].append(pd)
    rows = []
    for key, d in ts.items():
        r = res[key]
        if len(r["win"]) < 8 or len(d["answer"]) < 5:
            continue  # FBS-vs-FBS schedule too thin to call a season
        rows.append(dict(team=key[0], season=key[1], n_ans=len(d["answer"]), ans=rate(d["answer"]),
                         base=rate(d["other"] + d["other_nk"]), kick=rate(d["other"]), win=rate(r["win"]),
                         pd=rate(r["pd"]), ansA=rate(d["answerA"]), baseA=rate(d["otherA"] + d["other_nkA"]),
                         pdA=rate(r["pdA"]), winA=rate(r["winA"]), winB=rate(r["winB"])))
    X = {k: np.array([r[k] for r in rows], dtype=float) for k in rows[0] if k != "team"}
    c = lambda a, b: np.corrcoef(a, b)[0, 1]
    prem = X["ans"] - X["base"]
    print(f"\n{len(rows)} team-seasons 2014-2025; chances per season median {np.median(X['n_ans']):.0f}")
    for name, v in (("answer rate", X["ans"]), ("scoring on other drives", X["base"]), ("answer premium", prem)):
        print(f"corr({name}, win%) {c(v, X['win']):.2f}")
    by = {(r["team"], r["season"]): r for r in rows}
    pairs = [(by[k], by[(k[0], k[1] + 1)]) for k in by if (k[0], k[1] + 1) in by]
    yty = {}
    for k in ("ans", "base", "win"):
        yty[k] = c(np.array([a[k] for a, b in pairs]), np.array([b[k] for a, b in pairs]))
    yty["prem"] = c(np.array([a["ans"] - a["base"] for a, b in pairs]), np.array([b["ans"] - b["base"] for a, b in pairs]))
    print("year to year:", {k: round(v, 2) for k, v in yty.items()}, f"({len(pairs)} pairs)")
    ok = ~np.isnan(X["ansA"]) & ~np.isnan(X["winB"]) & ~np.isnan(X["pdA"]) & ~np.isnan(X["baseA"])
    y = X["winB"][ok]

    def r2(cols):
        A = np.column_stack([np.ones(ok.sum())] + [X[k][ok] for k in cols])
        b, *_ = np.linalg.lstsq(A, y, rcond=None)
        return 1 - (y - A @ b).var() / y.var()
    fore = {n: r2(cs) for n, cs in (("pd", ["pdA"]), ("ans", ["ansA"]), ("pd_ans", ["pdA", "ansA"]))}
    print("forecast weeks 8+ win% from weeks 1-7, R^2:", {k: round(v, 3) for k, v in fore.items()})
    R.update(n_teamseasons=len(rows), corr=dict(ans_win=c(X["ans"], X["win"]), base_win=c(X["base"], X["win"]),
                                                  prem_win=c(prem, X["win"]), ans_base=c(X["ans"], X["base"])),
             yty=yty, n_pairs=len(pairs), fore=fore)

    # the fan's version: other side scored the game's first touchdown (as the first score)
    win = defaultdict(list)
    for e in hist:
        if e["first"]:
            w = rec[(e["team"], e["season"], e["game"])][1]
            win["answered" if e["scored"] else "did not"].append(w)
            win["TD" if e["td"] else ("FG" if e["scored"] else "none")].append(w)
    print()
    for k, v in win.items():
        print(f"down after the first TD, {k:9s}: n={len(v):5d}  won {np.mean(v):.3f}")
    R["fan"] = {k: [len(v), float(np.mean(v))] for k, v in win.items()}

    # 2026, every FBS team
    cur = [e for e in ev if e["season"] == 2026]
    t26 = defaultdict(lambda: defaultdict(list))
    for e in cur:
        t26[e["team"]]["ans" if e["kind"] == "answer" else "oth"].append(e["scored"])
    rec26 = defaultdict(lambda: [0, 0])
    for (tm, ss, g), (w, wn, pd) in rec.items():
        if ss == 2026:
            rec26[tm][0 if wn == 1 else 1] += 1
    teams = {tm: dict(n=len(d["ans"]), made=int(sum(d["ans"])), other=rate(d["oth"]), n_other=len(d["oth"]),
                      fbs_rec=rec26[tm]) for tm, d in t26.items()}
    last = max(G["date"] for G in games.values() if G["season"] == 2026) if cur else None
    R["y2026"] = dict(teams=teams, through=last, league=rate([e["scored"] for e in cur if e["kind"] == "answer"]),
                      other=rate([e["scored"] for e in cur if e["kind"] == "other"]),
                      n=len([e for e in cur if e["kind"] == "answer"]))
    json.dump(dict(R=R, rows=rows), open(os.path.join(HERE, "data", "cfb-results.json"), "w"), indent=0, default=float)


if __name__ == "__main__":
    main()
