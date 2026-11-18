#!/usr/bin/env python3
"""Who wins the 2026 national title? Simulate the rest of the season and the bracket.

    python3 sim.py [--loss-penalty 6] [--nsims 40000] [--seed 2026]

Inputs (raw/, fetched by fetch.py and by curl on 2026-11-18):
  sp.json            CFBD SP+ ratings, 2026
  games.json         CFBD 2026 FBS regular season (completed + remaining)
  espn_rankings.json ESPN rankings feed; "Playoff Committee Rankings", 2026-11-17
  format_extract.txt the 12-team format, from collegefootballplayoff.com

Model
  P(A beats B) = Phi((SP+_A - SP+_B + home) / 16.5), home = 2.5 (0 if neutral).
  Ratings are held fixed within a simulated season. With --rating-draws R (editor's rule,
  2026-11-18: every bar gets an error bar), each team's true rating is first drawn from
  Normal(SP+, 16.5 / sqrt(games played)) -- the game-level scatter divided by the games
  behind the rating -- and nsims/R seasons are played on that draw. The spread of title
  chances across draws gives the 95% interval; the point estimate is the mean over draws.

  Remaining regular-season games are simulated. Each FBS conference's title game
  is its top two by conference record (ties broken at random -- real tiebreakers
  are not modeled), neutral site.

  Committee model (judgment, stated): each team's score = 26 - current CFP rank
  (unranked = 0), minus LOSS_PENALTY per new loss (a title-game loss costs half),
  plus 2 for winning a conference title, plus small noise (sd 1). Final order by score.

  Field (official format): 4 power champions (ACC, Big Ten, Big 12, SEC) + highest-
  ranked champion of American/CUSA/MAC/MW/Pac-12/Sun Belt; then the next highest-
  ranked teams to 12. Seeded straight by committee order; auto-bids ranked outside
  the top 12 go at the bottom. Seeds 1-4 bye. First round at the higher seed (2.5),
  the rest neutral. Bracket: 1 v 8/9, 4 v 5/12, 2 v 7/10, 3 v 6/11; semis 1/8/9 v
  4/5/12 and 2/7/10 v 3/6/11. No reseeding.
"""
import argparse, collections, json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SD, HFA = 16.5, 2.5
POWER = ["ACC", "Big Ten", "Big 12", "SEC"]
GROUP5 = ["American Athletic", "Conference USA", "Mid-American", "Mountain West", "Pac-12", "Sun Belt"]


def phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def pwin(a, b, sp, home=0.0):
    return phi((sp[a] - sp[b] + home) / SD)


def load():
    sp = {x["team"]: x["rating"] for x in json.load(open(os.path.join(HERE, "raw/sp.json"))) if x.get("rating") is not None}
    games = json.load(open(os.path.join(HERE, "raw/games.json")))
    E = json.load(open(os.path.join(HERE, "raw/espn_rankings.json")))
    cfp = [r for r in E["rankings"] if "Playoff" in r["name"]][0]
    rank = {t["team"]["location"]: t["current"] for t in cfp["ranks"]}
    return sp, games, rank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loss-penalty", type=float, default=6.0)
    ap.add_argument("--nsims", type=int, default=40000)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--today-field", action="store_true", help="skip season; seed today's committee top 12 straight")
    ap.add_argument("--out", default=None)
    ap.add_argument("--rating-draws", type=int, default=0, help="redraw ratings R times (0 = fixed SP+)")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    sp, games, rank = load()
    lowest = min(sp.values())
    for t in rank:
        assert t in sp, t

    conf = {}
    for g in games:
        for side in ("home", "away"):
            if g[side + "Classification"] == "fbs":
                conf[g[side + "Team"]] = g[side + "Conference"]
    for t in list(conf):
        sp.setdefault(t, lowest)

    cw0, cl0 = collections.Counter(), collections.Counter()
    for g in games:
        if g["completed"] and g["conferenceGame"]:
            h, w = g["homeTeam"], g["awayTeam"]
            hw = g["homePoints"] > g["awayPoints"]
            (cw0 if hw else cl0)[h] += 1
            (cl0 if hw else cw0)[w] += 1
    remaining = [g for g in games if not g["completed"]]
    for g in remaining:
        sp.setdefault(g["homeTeam"], lowest); sp.setdefault(g["awayTeam"], lowest)
    played = collections.Counter()
    for g in games:
        if g["completed"]:
            played[g["homeTeam"]] += 1; played[g["awayTeam"]] += 1
    sp0 = dict(sp)
    se = {t: SD / math.sqrt(max(1, played[t])) for t in sp0}

    def build_rem(sp):
        return [(g["homeTeam"], g["awayTeam"], pwin(g["homeTeam"], g["awayTeam"], sp, 0 if g["neutralSite"] else HFA),
                 g["conferenceGame"]) for g in remaining]
    rem = build_rem(sp)
    R = max(1, a.rating_draws); per = a.nsims // R
    draw_titles = []

    title = collections.Counter()
    final_ = collections.Counter()
    make = collections.Counter()
    seedcount = collections.defaultdict(collections.Counter)
    title_by_seed = collections.Counter()
    seed_n = collections.Counter()
    ref_field = None

    for s in range(per * R):
        if a.rating_draws and s % per == 0:
            if s: draw_titles.append(title - prev)
            prev = title.copy()
            sp = {t: sp0[t] + rng.normal(0, se[t]) for t in sp0}
            rem = build_rem(sp)
        newL = collections.Counter()
        cw, cl = cw0.copy(), cl0.copy()
        if not a.today_field:
            u = rng.random(len(rem))
            for (h, w, p, cg), x in zip(rem, u):
                win, lose = (h, w) if x < p else (w, h)
                newL[lose] += 1
                if cg:
                    cw[win] += 1; cl[lose] += 1
            champs, ccg_loser = {}, set()
            for c in POWER + GROUP5:
                members = [t for t in conf if conf[t] == c]
                members.sort(key=lambda t: (cw[t] / max(1, cw[t] + cl[t]), rng.random()), reverse=True)
                t1, t2 = members[0], members[1]
                w_ = t1 if rng.random() < pwin(t1, t2, sp) else t2
                l_ = t2 if w_ == t1 else t1
                champs[c] = w_; ccg_loser.add(l_)
                newL[l_] += 1
            score = {}
            for t in conf:
                base = 26 - rank[t] if t in rank else 0.0
                pen = a.loss_penalty * newL[t]
                if t in ccg_loser:
                    pen -= a.loss_penalty / 2  # a title-game loss costs half
                bonus = 2.0 if t in champs.values() else 0.0
                score[t] = base - pen + bonus + rng.normal(0, 1.0) + sp[t] * 1e-3
            order = sorted(conf, key=lambda t: score[t], reverse=True)
            g5c = [champs[c] for c in GROUP5]
            g5 = min(g5c, key=lambda t: order.index(t))
            autos = [champs[c] for c in POWER] + [g5]
            field = list(autos)
            for t in order:
                if len(field) == 12:
                    break
                if t not in field:
                    field.append(t)
            # Notre Dame clause is subsumed: if ND is top 12 it is in the order above the cut.
            top12 = set(order[:12])
            inside = [t for t in order if t in field and t in top12]
            outside = [t for t in order if t in field and t not in top12]
            # field may have fewer than 12 inside if autos sit outside; fill seeds in order
            seeds = sorted(field, key=lambda t: order.index(t))
            seeds = [t for t in seeds if t not in outside] + outside
        else:
            seeds = sorted(rank, key=rank.get)[:12]
        if ref_field is None:
            ref_field = seeds
        S = {i + 1: t for i, t in enumerate(seeds)}
        for i, t in S.items():
            make[t] += 1; seedcount[t][i] += 1
        def play(x, y, home=0.0):
            return x if rng.random() < pwin(x, y, sp, home) else y
        r1 = {k: play(S[k], S[17 - k], HFA) for k in (5, 6, 7, 8)}
        q = {1: play(S[1], r1[8]), 4: play(S[4], r1[5]), 2: play(S[2], r1[7]), 3: play(S[3], r1[6])}
        f1, f2 = play(q[1], q[4]), play(q[2], q[3])
        ch = play(f1, f2)
        final_[f1] += 1; final_[f2] += 1
        title[ch] += 1
        seed_of = {t: k for k, t in S.items()}
        title_by_seed[seed_of[ch]] += 1

    if a.rating_draws:
        draw_titles.append(title - prev)
    N = per * R
    teams = sorted(set(make) | set(title), key=lambda t: -title[t])
    rows = []
    for t in teams:
        modal = seedcount[t].most_common(1)[0][0] if seedcount[t] else None
        rows.append(dict(team=t, cfp_rank=rank.get(t), sp=round(sp0[t], 1), make=make[t] / N,
                         final=final_[t] / N, title=title[t] / N, modal_seed=modal))
        if a.rating_draws:
            v = np.array([d[t] / per for d in draw_titles])
            rows[-1].update(title_lo=float(np.percentile(v, 2.5)), title_hi=float(np.percentile(v, 97.5)),
                            se_rating=round(se[t], 1))
    fav = collections.Counter()
    for d in draw_titles:
        if d: fav[max(d, key=d.get)] += 1
    out_fav = {k: v / len(draw_titles) for k, v in fav.most_common()} if a.rating_draws else {}
    if out_fav: print("favorite across rating draws:", {k: round(v, 2) for k, v in list(out_fav.items())[:6]})
    out = dict(favorite_share=out_fav, nsims=N, rating_draws=a.rating_draws, per_draw=per, loss_penalty=a.loss_penalty, today_field=a.today_field,
               title_by_seed={k: title_by_seed[k] / N for k in range(1, 13)}, rows=rows)
    if a.out:
        json.dump(out, open(os.path.join(HERE, a.out), "w"), indent=1)
    print(f"nsims={N} loss_penalty={a.loss_penalty} today_field={a.today_field}")
    print(f"{'team':16s} cfp  sp+   make  final  title  seed")
    for r in rows[:30]:
        print(f"{r['team']:16s} {str(r['cfp_rank'] or '-'):>3s} {r['sp']:5.1f} {r['make']:6.3f} {r['final']:6.3f} {r['title']:6.3f}  {r['modal_seed']}"
              + (f"  [{r['title_lo']:.3f}, {r['title_hi']:.3f}] se {r['se_rating']}" if 'title_lo' in r else ""))
    print("title by seed:", {k: round(v, 3) for k, v in out["title_by_seed"].items()})


if __name__ == "__main__":
    main()
