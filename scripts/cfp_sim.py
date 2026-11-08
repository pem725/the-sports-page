#!/usr/bin/env python3
"""How much did one Saturday move a team's playoff chances? Simulate and see.

    python3 scripts/cfp_sim.py --day 2026-11-07 --team "Notre Dame"
    python3 scripts/cfp_sim.py --check-week 10      # the committee proxy vs the real ranking

THE QUESTION. A fan wakes up asking "how good was yesterday?" The answer worth
printing is not a feeling, it is a difference: the team's chance of a playoff bid
(and of a bye) with that Saturday still to play, against the same chance once its
results are in. Each game's share is the gap between the two worlds in which it
went either way -- the conditioning trick from daily_watch.py: one simulation,
split by each game's result, which is exact because games are independent given
the ratings.

THE PIECES, and the weak one.
  * Game odds: P(home wins) = Phi((SP+_h - SP+_a + 2.5) / 16.5), no home edge at
    a neutral site. Ratings are the FROZEN pre-week snapshot, so Saturday is
    judged on what was known before it.
  * Conference titles: the top two by conference record (ties to the better
    resume) play once more.
  * Field: four power-conference champions and the best other champion, then
    the next seven by ranking; the top four by ranking get byes.
  * THE COMMITTEE, which nobody can simulate. The stand-in is strength of
    record -- wins minus the wins an average top-25 team would expect against
    the same schedule -- plus a small credit for SP+. It knows nothing of head-
    to-head, injuries or the eye test. --check-week scores it against the
    committee's real ranking; read that before trusting a decimal here.

Schedules, results and conferences come from ESPN's public feed (no CFBD quota).
"""
import argparse, json, math, os, sys, urllib.request
from datetime import datetime, timedelta, timezone
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(REPO, "data", "rating-snapshots")
SITE = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
STAND = "https://site.api.espn.com/apis/v2/sports/football/college-football/standings?group=80"
SD, HFA, FCS_SP = 16.5, 2.5, -30.0
SP_CREDIT = 0.03          # resume wins per SP+ point; 10 points ~ a third of a win
POWER = ("ACC", "Big Ten", "Big 12", "SEC")
ET = timezone(timedelta(hours=-5))


def get(url):
    req = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


_erf = np.vectorize(math.erf)


def vphi(z):
    return 0.5 * (1 + _erf(np.asarray(z) / math.sqrt(2)))


def load_season(year):
    games, seen = [], set()
    for wk in range(1, 16):
        d = get(f"{SITE}/scoreboard?groups=80&limit=400&seasontype=2&week={wk}&dates={year}")
        for ev in d.get("events", []):
            if ev["id"] in seen:
                continue
            seen.add(ev["id"])
            c = ev["competitions"][0]
            h = next(x for x in c["competitors"] if x["homeAway"] == "home")
            a = next(x for x in c["competitors"] if x["homeAway"] == "away")
            if "TBD" in (h["team"].get("location"), a["team"].get("location")):
                continue
            done = c["status"]["type"].get("completed", False)
            games.append({
                "id": ev["id"], "week": wk,
                "date": datetime.fromisoformat(ev["date"].replace("Z", "+00:00")).astimezone(ET).date().isoformat(),
                "home": h["team"]["location"], "away": a["team"]["location"],
                "hrank": h.get("curatedRank", {}).get("current", 99),
                "arank": a.get("curatedRank", {}).get("current", 99),
                "neutral": bool(c.get("neutralSite")), "conf": bool(c.get("conferenceCompetition")),
                "done": done, "home_won": bool(h.get("winner")) if done else None,
                "title": "championship" in " ".join(n.get("headline", "") for n in c.get("notes", [])).lower(),
            })
    return games


def load_conferences():
    conf = {}

    def walk(node, name=None):
        nm = node.get("abbreviation") or node.get("name")
        for e in node.get("standings", {}).get("entries", []):
            conf[e["team"]["location"]] = name or nm
        for ch in node.get("children", []):
            walk(ch, name or ch.get("abbreviation") or ch.get("name"))

    for ch in get(STAND).get("children", []):
        walk(ch, ch.get("abbreviation") or ch.get("name"))
    return conf


def snapshot(week):
    path = os.path.join(SNAP, f"2026-w{week:02d}.json")
    if not os.path.exists(path):
        sys.exit(f"no frozen ratings for week {week} ({path}); refusing to grade on later ratings")
    return json.load(open(path))["sp"]


class Season:
    def __init__(self, games, conf, sp):
        self.conf = conf
        self.fbs = sorted(conf)
        self.idx = {t: i for i, t in enumerate(self.fbs)}
        self.sp = np.array([sp.get(t, FCS_SP) for t in self.fbs])
        self.spof = lambda t: sp.get(t, FCS_SP)
        self.games = [g for g in games if not g["title"]]
        top = sorted(self.sp, reverse=True)
        self.ref = top[24]                    # an average top-25 team
        self.missing = sorted(t for t in self.fbs if t not in sp)

    def p_home(self, g):
        return phi((self.spof(g["home"]) - self.spof(g["away"]) + (0 if g["neutral"] else HFA)) / SD)

    def ref_p(self, opp, at_home, neutral):
        edge = 0 if neutral else (HFA if at_home else -HFA)
        return phi((self.ref - self.spof(opp) + edge) / SD)

    def simulate(self, fixed, n=20000, seed=7):
        """fixed(g) -> True/False home won, or None to simulate. Returns per-sim outcomes too."""
        rng = np.random.default_rng(seed)
        T, G = len(self.fbs), len(self.games)
        H = np.zeros((n, G), dtype=bool)
        for j, g in enumerate(self.games):
            f = fixed(g)
            H[:, j] = f if f is not None else rng.random(n) < self.p_home(g)
        wins = np.zeros((n, T)); cw = np.zeros((n, T)); cl = np.zeros((n, T))
        expect = np.zeros(T)
        for j, g in enumerate(self.games):
            hi, ai = self.idx.get(g["home"]), self.idx.get(g["away"])
            for ti, opp, home, won in ((hi, g["away"], True, H[:, j]), (ai, g["home"], False, ~H[:, j])):
                if ti is None:
                    continue
                wins[:, ti] += won
                expect[ti] += self.ref_p(opp, home, g["neutral"])
                if g["conf"]:
                    cw[:, ti] += won; cl[:, ti] += ~won
        resume = wins - expect + SP_CREDIT * self.sp
        # conference title games
        champ = {}
        confs = sorted({c for c in self.conf.values() if c})
        rows = np.arange(n)
        for c in confs:
            members = [self.idx[t] for t in self.fbs if self.conf[t] == c]
            if len(members) < 2 or c.lower().startswith("fbs ind") or "independent" in c.lower():
                continue
            m = np.array(members)
            key = (cw[:, m] - cl[:, m]) * 100 + resume[:, m]
            order = np.argsort(-key, axis=1)
            t1, t2 = m[order[:, 0]], m[order[:, 1]]
            w1 = rng.random(n) < vphi((self.sp[t1] - self.sp[t2]) / SD)
            winner = np.where(w1, t1, t2)
            resume[rows, winner] += 1
            # what an average top-25 team would expect from the same neutral-site game
            resume[rows, t1] -= vphi((self.ref - self.sp[t2]) / SD)
            resume[rows, t2] -= vphi((self.ref - self.sp[t1]) / SD)
            champ[c] = winner
        order = np.argsort(-resume, axis=1)
        rank = np.empty_like(order); rank[rows[:, None], order] = np.arange(T)[None, :]
        inf = np.zeros((n, T), dtype=bool); bye = rank < 4
        power = [c for c in champ if any(c.startswith(p) or p in c for p in POWER)]
        other = [c for c in champ if c not in power]
        for c in power:
            inf[rows, champ[c]] = True
        if other:
            oc = np.stack([champ[c] for c in other], axis=1)
            best = oc[rows, np.argmin(rank[rows[:, None], oc], axis=1)]
            inf[rows, best] = True
        # seven at-large by ranking
        for k in range(T):
            need = inf.sum(axis=1) < 12
            if not need.any():
                break
            t = order[:, k]
            inf[rows[need], t[need]] = True
        return H, inf, bye, rank


def day_report(team, day, n):
    year = int(day[:4])
    games = load_season(year)
    conf = load_conferences()
    wk = next(g["week"] for g in games if g["date"] == day)
    S = Season(games, conf, snapshot(wk))
    ti = S.idx[team]
    today = [j for j, g in enumerate(S.games) if g["date"] == day and g["done"]]

    def before(g):
        return g["home_won"] if g["done"] and g["date"] < day else None

    def after(g):
        return g["home_won"] if g["done"] and g["date"] <= day else None

    H, inf, bye, _ = S.simulate(before, n)
    _, inf2, bye2, rank2 = S.simulate(after, n, seed=11)
    board = []
    for t in S.fbs:
        k = S.idx[t]
        board.append({"team": t, "no1": (rank2[:, k] == 0).mean(), "bye": bye2[:, k].mean(),
                      "in": inf2[:, k].mean(), "med_rank": float(np.median(rank2[:, k])) + 1})
    board = sorted(board, key=lambda b: -b["in"])[:20]
    # the stand-in's ranking today: results through the day, nothing simulated
    played = [g for g in S.games if g["done"] and g["date"] <= day]
    w = {t: 0 for t in S.fbs}; e = {t: 0.0 for t in S.fbs}
    for g in played:
        for t, o, home, won in ((g["home"], g["away"], True, g["home_won"]), (g["away"], g["home"], False, not g["home_won"])):
            if t in w:
                w[t] += won; e[t] += S.ref_p(o, home, g["neutral"])
    now = sorted(S.fbs, key=lambda t: -(w[t] - e[t] + SP_CREDIT * S.spof(t)))[:25]
    pre_in, pre_bye = inf[:, ti].mean(), bye[:, ti].mean()
    post_in, post_bye = inf2[:, ti].mean(), bye2[:, ti].mean()

    rows = []
    for j in today:
        g = S.games[j]
        hw = H[:, j]
        if hw.all() or (~hw).all():
            continue
        dh = inf[hw, ti].mean() - inf[~hw, ti].mean()
        db = bye[hw, ti].mean() - bye[~hw, ti].mean()
        act = hw if g["home_won"] else ~hw
        got_in = inf[act, ti].mean() - pre_in
        got_bye = bye[act, ti].mean() - pre_bye
        # standard error of a conditional-minus-overall difference
        k = act.sum()
        se = lambda x: math.sqrt(max(x.mean() * (1 - x.mean()), 1e-9) * (1 / k - 1 / n)) if k < n else 0
        se_in, se_bye = se(inf[:, ti]), se(bye[:, ti])
        winner, loser = (g["home"], g["away"]) if g["home_won"] else (g["away"], g["home"])
        rows.append({"game": f"{winner} over {loser}", "swing_in": abs(dh), "got_in": got_in,
                     "swing_bye": abs(db), "got_bye": got_bye,
                     "se_in": se_in, "se_bye": se_bye,
                     "p_actual": act.mean(), "ours": team in (g["home"], g["away"])})
    rows.sort(key=lambda r: -(abs(r["got_in"]) + abs(r["got_bye"])))
    return {"team": team, "day": day, "week": wk, "n": n,
            "pre": {"in": pre_in, "bye": pre_bye}, "post": {"in": post_in, "bye": post_bye},
            "games": rows, "unrated": S.missing, "board": board, "now": now}


def check_week(week, year=2026):
    """Proxy ranking on results before week `week`, against the committee rank ESPN shows in that week."""
    games = load_season(year)
    S = Season(games, load_conferences(), snapshot(week))
    fixed = lambda g: g["home_won"] if g["done"] and g["week"] < week else None
    played = [g for g in S.games if g["done"] and g["week"] < week]
    wins = {t: 0 for t in S.fbs}; exp = {t: 0.0 for t in S.fbs}
    for g in played:
        for t, o, home, won in ((g["home"], g["away"], True, g["home_won"]), (g["away"], g["home"], False, not g["home_won"])):
            if t in wins:
                wins[t] += won; exp[t] += S.ref_p(o, home, g["neutral"])
    score = {t: wins[t] - exp[t] + SP_CREDIT * S.spof(t) for t in S.fbs}
    proxy = sorted(S.fbs, key=lambda t: -score[t])
    real = {}
    for g in S.games:
        if g["week"] == week:
            if g["hrank"] <= 25: real[g["home"]] = g["hrank"]
            if g["arank"] <= 25: real[g["away"]] = g["arank"]
    top12 = {t for t, r in real.items() if r <= 12}
    hit = len(top12 & set(proxy[:12]))
    print(f"Committee top 12 (as ESPN shows it in week {week}) vs proxy top 12: {hit} of {len(top12)} shared")
    for t, r in sorted(real.items(), key=lambda kv: kv[1]):
        print(f"  committee {r:>2}  proxy {proxy.index(t) + 1:>3}  {t}")
    print("  proxy top 12:", ", ".join(proxy[:12]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day")
    ap.add_argument("--team", default="Notre Dame")
    ap.add_argument("--n", type=int, default=100000)
    ap.add_argument("--check-week", type=int)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.check_week:
        return check_week(a.check_week)
    r = day_report(a.team, a.day, a.n)
    if a.json:
        print(json.dumps(r, indent=2, default=float)); return
    pct = lambda x: f"{100 * x:.0f}%"
    print(f"{r['team']}, {r['day']} (week {r['week']} ratings, {r['n']:,} seasons each way)")
    print(f"  Playoff bid: {pct(r['pre']['in'])} before the day -> {pct(r['post']['in'])} after")
    print(f"  Bye (top 4): {pct(r['pre']['bye'])} before the day -> {pct(r['post']['bye'])} after")
    print("  The games that moved it (points of bid / bye from the actual result):")
    hidden = 0
    for g in r["games"]:
        if abs(g["got_in"]) < 2 * g["se_in"] and abs(g["got_bye"]) < 2 * g["se_bye"]:
            hidden += 1
            continue
        tag = "  <- ours" if g["ours"] else ""
        print(f"    {100*g['got_in']:+5.1f} / {100*g['got_bye']:+5.1f}  {g['game']} ({pct(g['p_actual'])} pregame){tag}")
    if hidden:
        print(f"  ({hidden} more games moved it by less than the simulation can tell from zero)")
    print("  Final ranking, after the day (No. 1 / bye / bid / median final rank):")
    for b in r["board"]:
        print(f"    {b['team']:16} {pct(b['no1']):>4} {pct(b['bye']):>4} {pct(b['in']):>4}   {b['med_rank']:.0f}")
    print("  Stand-in ranking now, nothing simulated:", ", ".join(f"{i+1} {t}" for i, t in enumerate(r["now"])))
    if r["unrated"]:
        print(f"  ({len(r['unrated'])} FBS teams had no frozen SP+ and were rated as FCS)")


if __name__ == "__main__":
    main()
