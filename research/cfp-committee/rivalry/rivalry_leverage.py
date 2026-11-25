#!/usr/bin/env python3
"""Which rivalry-week game moves the most College Football Playoff probability?

    python3 research/cfp-committee/rivalry/rivalry_leverage.py --refresh \
        --inject queue/206-rivalry-leverage.html

--refresh pulls three things fresh and then runs:
  * the committee's LATEST ranking, parsed from collegefootballplayoff.com/rankings
    (the primary source; saved as cfp-ranking-YYYY-MM-DD.json beside this file)
  * SP+ from CollegeFootballData (ONE call; saved as sp-YYYY-MM-DD.json)
  * every regular-season game and result from ESPN's public scoreboard (no quota)
Without --refresh it reuses the newest saved ranking and ratings.

LEVERAGE, per game:  for each team, P(bid | it wins) - P(bid | it loses),
summed over the two teams. One simulation of the rest of the season, split by
each game's result -- the daily_watch.py trick, exact because games are
independent given the ratings.

THE FIELD (2026-27 format, confirmed on collegefootballplayoff.com/sports/2024/5/29/12-team-format):
12 teams. The ACC, Big Ten, Big 12 and SEC champions; the highest-ranked champion
of the American, C-USA, MAC, Mountain West, Pac-12 and Sun Belt; Notre Dame if it is
ranked in the top 12; the rest at-large by ranking.

THE COMMITTEE STAND-IN (judgment, stated as such). Every team STARTS where the
committee put it in the latest ranking. Results after that move it by how much they
change its strength of record: wins minus the wins an average top-25 team would
expect against the same schedule, plus a small SP+ credit (the cfp_sim.py proxy).
Concretely, the committee's order is mapped onto the proxy's own scale (the No. k
team is given the k-th best proxy score), each team carries its offset forward, and
simulated results add to it. Unranked teams keep their raw proxy, capped just under
No. 25. Conference title games: the top two by conference record (ties to the
better resume) meet once more on a neutral field; the winner gets a win's credit.
It knows nothing of head-to-head, injuries or the eye test.
"""
import argparse, glob, html, json, math, os, re, sys, urllib.request
from datetime import date
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import cfp_sim  # read-only reuse: load_season (ESPN), load_conferences (ESPN)

SD, HFA, FCS_SP, SP_CREDIT = 16.5, 2.5, -30.0, 0.03
POWER = {"acc", "big10", "big12", "sec"}
GROUP5 = {"American", "usa", "midam", "mwest", "pac12", "belt"}
ALIAS = {"Southern California": "USC", "Miami (FL)": "Miami", "Mississippi": "Ole Miss"}
MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
                                      "Sep", "Oct", "Nov", "Dec"], 1)}


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


vphi = np.vectorize(phi)


# ---------------------------------------------------------------- fetching
def fetch_ranking(year=2026):
    req = urllib.request.Request("https://collegefootballplayoff.com/rankings",
                                 headers={"User-Agent": "Mozilla/5.0"})
    t = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    i = t.find("CFP Selection Committee Rankings")
    m = re.search(r"2014 (\w{3})\.? (\d{1,2}) ", t[i:])
    released = date(year, MONTHS[m.group(1)], int(m.group(2))).isoformat()
    body = t[t.find("Full Rankings", i):]
    body = body[:body.find("Related News")]
    rows = re.findall(r"(\d{1,2}) ([A-Z][A-Za-z.&'() ]+?) (\d{1,2})-(\d{1,2})", body)
    rank = []
    for r, team, w, l in rows:
        if int(r) == len(rank) + 1:
            rank.append({"rank": int(r), "team": ALIAS.get(team.strip(), team.strip()),
                         "record": f"{w}-{l}"})
    if len(rank) != 25:
        sys.exit(f"parsed {len(rank)} ranked teams, expected 25; refusing")
    out = {"released": released, "source": "https://collegefootballplayoff.com/rankings", "top25": rank}
    json.dump(out, open(os.path.join(HERE, f"cfp-ranking-{released}.json"), "w"), indent=1)
    return out


def fetch_sp(year=2026):
    req = urllib.request.Request(f"https://api.collegefootballdata.com/ratings/sp?year={year}",
                                 headers={"Authorization": "Bearer " + os.environ["CFBD_KEY"]})
    resp = urllib.request.urlopen(req, timeout=60)
    left = resp.headers.get("X-CallLimit-Remaining")
    sp = {x["team"]: x["rating"] for x in json.load(resp) if x.get("rating") is not None}
    today = date.today().isoformat()
    json.dump({"taken": today, "source": "CollegeFootballData /ratings/sp", "sp": sp},
              open(os.path.join(HERE, f"sp-{today}.json"), "w"), indent=0)
    print(f"  CFBD calls left this month: {left}")
    return sp


def newest(prefix):
    files = sorted(glob.glob(os.path.join(HERE, prefix + "*.json")))
    if not files:
        sys.exit(f"no saved {prefix}*.json; run with --refresh")
    return json.load(open(files[-1]))


# ---------------------------------------------------------------- model
def run(n, lo, hi, seed=7):
    ranking, sp = newest("cfp-ranking-"), newest("sp-")["sp"]
    games = [g for g in cfp_sim.load_season(2026) if not g["title"]]
    conf = cfp_sim.load_conferences()
    teams = sorted(conf)
    idx = {t: i for i, t in enumerate(teams)}
    T = len(teams)
    spv = np.array([sp.get(t, FCS_SP) for t in teams])
    spof = lambda t: sp.get(t, FCS_SP)
    ref = sorted(spv, reverse=True)[24]  # an average top-25 team
    unmatched = [r["team"] for r in ranking["top25"] if r["team"] not in idx]
    if unmatched:
        sys.exit(f"ranked teams not found in ESPN's FBS list: {unmatched}")

    def ref_p(opp, home, neutral):
        return phi((ref - spof(opp) + (0 if neutral else (HFA if home else -HFA))) / SD)

    # proxy as of the ranking's release (results the committee had seen)
    rel = ranking["released"]
    wins0, exp0 = np.zeros(T), np.zeros(T)
    for g in games:
        if g["done"] and g["date"] < rel:
            for t, o, home, won in ((g["home"], g["away"], True, g["home_won"]),
                                    (g["away"], g["home"], False, not g["home_won"])):
                if t in idx:
                    wins0[idx[t]] += won; exp0[idx[t]] += ref_p(o, home, g["neutral"])
    proxy0 = wins0 - exp0 + SP_CREDIT * spv
    ladder = np.sort(proxy0)[::-1][:25]
    offset = np.zeros(T)
    ranked = {idx[r["team"]]: r["rank"] for r in ranking["top25"]}
    for i, r in ranked.items():
        offset[i] = ladder[r - 1] - proxy0[i]
    cap = ladder[24] - 1e-6
    for i in range(T):
        if i not in ranked and proxy0[i] > cap:
            offset[i] = cap - proxy0[i]

    # simulate every unplayed regular-season game
    rng = np.random.default_rng(seed)
    G = len(games)
    H = np.zeros((n, G), dtype=bool)
    wins, expect = np.zeros((n, T)), np.zeros(T)
    cw, cl = np.zeros((n, T)), np.zeros((n, T))
    for j, g in enumerate(games):
        if g["done"]:
            H[:, j] = g["home_won"]
        else:
            ph = phi((spof(g["home"]) - spof(g["away"]) + (0 if g["neutral"] else HFA)) / SD)
            H[:, j] = rng.random(n) < ph
        for t, o, home, won in ((g["home"], g["away"], True, H[:, j]),
                                (g["away"], g["home"], False, ~H[:, j])):
            if t not in idx:
                continue
            k = idx[t]
            wins[:, k] += won; expect[k] += ref_p(o, home, g["neutral"])
            if g["conf"]:
                cw[:, k] += won; cl[:, k] += ~won
    score = wins - expect + SP_CREDIT * spv + offset
    rows = np.arange(n)
    champ = {}
    for c in sorted(set(conf.values())):
        if c == "ind":
            continue
        m = np.array([idx[t] for t in teams if conf[t] == c])
        key = (cw[:, m] - cl[:, m]) * 100 + score[:, m]
        o = np.argsort(-key, axis=1)
        t1, t2 = m[o[:, 0]], m[o[:, 1]]
        w1 = rng.random(n) < vphi((spv[t1] - spv[t2]) / SD)
        win = np.where(w1, t1, t2)
        score[rows, win] += 1
        score[rows, t1] -= vphi((ref - spv[t2]) / SD)
        score[rows, t2] -= vphi((ref - spv[t1]) / SD)
        champ[c] = win
    order = np.argsort(-score, axis=1)
    rank = np.empty_like(order); rank[rows[:, None], order] = np.arange(T)[None, :]
    inf = np.zeros((n, T), dtype=bool)
    for c in POWER & set(champ):
        inf[rows, champ[c]] = True
    g5 = np.stack([champ[c] for c in GROUP5 & set(champ)], axis=1)
    inf[rows, g5[rows, np.argmin(rank[rows[:, None], g5], axis=1)]] = True
    nd = idx["Notre Dame"]
    inf[:, nd] |= rank[:, nd] < 12
    for k in range(T):
        need = inf.sum(1) < 12
        if not need.any():
            break
        inf[rows[need], order[need, k]] = True
    assert (inf.sum(1) == 12).all()
    bye = np.zeros((n, T), dtype=bool)  # top four seeds: straight ranking order among the 12
    seeds = np.where(inf[rows[:, None], order], 1, 0).cumsum(1)
    for k in range(T):
        top = (seeds[:, k] <= 4) & inf[rows, order[:, k]]
        bye[rows[top], order[top, k]] = True

    p_in = inf.mean(0)
    out = []
    for j, g in enumerate(games):
        if g["done"] or not (lo <= g["date"] <= hi):
            continue
        hw = H[:, j]
        ph = hw.mean()
        if ph in (0, 1):
            continue
        sides = []
        for t, won in ((g["home"], hw), (g["away"], ~hw)):
            if t not in idx:
                sides.append({"team": t, "p_win": float(won.mean()), "in": 0, "if_win": 0, "if_lose": 0, "swing": 0})
                continue
            k = idx[t]
            a, b = inf[won, k].mean(), inf[~won, k].mean()
            sides.append({"team": t, "p_win": float(won.mean()), "in": float(p_in[k]),
                          "if_win": float(a), "if_lose": float(b), "swing": float(a - b),
                          "bye": float(bye[:, k].mean()), "bye_if_win": float(bye[won, k].mean()),
                          "bye_if_lose": float(bye[~won, k].mean()) if (~won).any() else 0.0})
        # everyone else: probability that changes hands among third parties
        d = inf[hw].mean(0) - inf[~hw].mean(0)   # home-win minus away-win, every club
        playing = {idx.get(g["home"]), idx.get(g["away"])}
        third = float(sum(abs(d[k]) for k in range(T) if k not in playing))
        movers = [{"team": teams[k], "if_home_wins": float(d[k])}
                  for k in np.argsort(-np.abs(d)) if k not in playing][:4]
        out.append({"date": g["date"], "home": g["home"], "away": g["away"],
                    "hrank": g["hrank"], "arank": g["arank"], "neutral": g["neutral"],
                    "sides": sides, "leverage": sum(s["swing"] for s in sides), "third": third, "movers": movers,
                    # expected size of the move once the result is known: stake x closeness
                    "expected_move": 2 * ph * (1 - ph) * sum(s["swing"] for s in sides)})
    out.sort(key=lambda r: -r["leverage"])
    board = sorted(({"team": t, "in": float(p_in[idx[t]]), "bye": float(bye[:, idx[t]].mean()),
                     "cfp": ranked.get(idx[t])} for t in teams), key=lambda b: -b["in"])[:24]
    return {"run": date.today().isoformat(), "ranking_released": rel, "sp_taken": newest("sp-")["taken"],
            "n": n, "window": [lo, hi], "games": out, "board": board}


def svg(res, rows=8):
    """Two bars per game: what rides on it (light) and how far it is expected to
    move the two teams' chances once played (dark) = stake x closeness to a coin flip."""
    gs = res["games"][:rows]
    top = max(gs, key=lambda g: g["expected_move"])
    W, x0, x1, y0, rh = 640, 236, 590, 58, 36
    H = y0 + rh * len(gs) + 46
    hi = max(70, 10 * math.ceil(max(100 * g["leverage"] for g in gs) / 10))
    X = lambda v: x0 + (x1 - x0) * v / hi
    day = lambda d: date.fromisoformat(d).strftime("%a")
    f_mono, f_body = "font-family=\"'Roboto Mono',monospace\"", "font-family=\"'Libre Baskerville',serif\""
    label = (f"Points of playoff chance riding on each rivalry-week game, and how far each is "
             f"expected to move. {top['away']} at {top['home']} is expected to move the most.")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" class="chart" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{html.escape(label)}">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#f5f0e8"/>',
         f'<text x="{W//2}" y="22" text-anchor="middle" {f_mono} font-size="12" fill="#1a1208">What rides on each game, and how much it is expected to move</text>',
         f'<g {f_mono} font-size="11"><rect x="{x0}" y="34" width="14" height="10" fill="#e0d8c5" stroke="#c8b99a"/>'
         f'<text x="{x0+20}" y="43" fill="#6b5e4a">riding on it</text>'
         f'<rect x="{x0+130}" y="34" width="14" height="10" fill="#2c4a6e"/>'
         f'<text x="{x0+150}" y="43" fill="#2c4a6e">expected move</text></g>']
    for i, g in enumerate(gs):
        y = y0 + i * rh
        fav = max(g["sides"], key=lambda s: s["p_win"])
        st, mv = 100 * g["leverage"], 100 * g["expected_move"]
        col = "#b83a1e" if g is top else "#2c4a6e"
        o.append(f'<text x="8" y="{y+13}" {f_body} font-size="13" fill="#1a1208">{html.escape(g["away"])} at {html.escape(g["home"])}</text>')
        o.append(f'<text x="8" y="{y+27}" {f_mono} font-size="10" fill="#6b5e4a">{day(g["date"])} &#183; {html.escape(fav["team"])} wins {100*fav["p_win"]:.0f} of 100</text>')
        o.append(f'<rect x="{x0}" y="{y+4}" width="{X(st)-x0:.1f}" height="22" fill="#e0d8c5" stroke="#c8b99a"/>')
        o.append(f'<rect x="{x0}" y="{y+4}" width="{X(mv)-x0:.1f}" height="22" fill="{col}"/>')
        o.append(f'<text x="{X(mv)+4:.1f}" y="{y+19}" {f_mono} font-size="11" fill="{col}" font-weight="600">{mv:.0f}</text>')
        o.append(f'<text x="{X(st)+5:.1f}" y="{y+19}" {f_mono} font-size="11" fill="#6b5e4a">{st:.0f}</text>')
    yb = y0 + rh * len(gs) + 6
    o.append(f'<line x1="{x0}" y1="{yb}" x2="{x1}" y2="{yb}" stroke="#6b5e4a"/>')
    for v in range(0, hi + 1, 10):
        o.append(f'<text x="{X(v):.1f}" y="{yb+14}" text-anchor="middle" {f_mono} font-size="10" fill="#6b5e4a">{v}</text>')
    o.append(f'<text x="{(x0+x1)//2}" y="{yb+32}" text-anchor="middle" {f_mono} font-size="10" fill="#6b5e4a">points of playoff chance, out of 100</text>')
    o.append('</svg>')
    return "\n".join(o)


def inject(path, block):
    s = open(path).read()
    a, b = "<!-- LEVERAGE_FIG -->", "<!-- /LEVERAGE_FIG -->"
    if s.count(a) != 1 or s.count(b) != 1:
        sys.exit(f"{path}: need exactly one {a} ... {b} pair")
    i, j = s.index(a) + len(a), s.index(b)
    open(path, "w").write(s[:i] + "\n" + block + "\n" + s[j:])
    print(f"  figure injected into {os.path.relpath(path, REPO)}")


def backtest(old_path):
    """Anchor on an OLDER committee ranking, apply the real results since, and
    compare the stand-in's order with the newest saved committee ranking."""
    old, new, sp = json.load(open(old_path)), newest("cfp-ranking-"), newest("sp-")["sp"]
    games = [g for g in cfp_sim.load_season(2026) if not g["title"]]
    teams = sorted(cfp_sim.load_conferences())
    spof = lambda t: sp.get(t, FCS_SP)
    ref = sorted((spof(t) for t in teams), reverse=True)[24]
    ref_p = lambda o, h, nu: phi((ref - spof(o) + (0 if nu else (HFA if h else -HFA))) / SD)

    def proxy(through):
        s = {t: SP_CREDIT * spof(t) for t in teams}
        for g in games:
            if g["done"] and g["date"] < through:
                for t, o, h, w in ((g["home"], g["away"], True, g["home_won"]),
                                   (g["away"], g["home"], False, not g["home_won"])):
                    if t in s:
                        s[t] += w - ref_p(o, h, g["neutral"])
        return s
    p0, p1 = proxy(old["released"]), proxy(new["released"])
    ladder = sorted(p0.values(), reverse=True)[:25]
    oldr = {r["team"]: r["rank"] for r in old["top25"]}
    score = {}
    for t in teams:
        off = ladder[oldr[t] - 1] - p0[t] if t in oldr else min(0, ladder[24] - 1e-6 - p0[t])
        score[t] = p1[t] + off
    pred = sorted(teams, key=lambda t: -score[t])
    real = [r["team"] for r in new["top25"]]
    hit12 = len(set(pred[:12]) & set(real[:12]))
    hit25 = len(set(pred[:25]) & set(real))
    err = [abs(pred.index(t) - i) for i, t in enumerate(real)]
    naive = [abs((oldr.get(t, 26) - 1) - i) for i, t in enumerate(real)]
    print(f"Anchor {old['released']} + real results -> predicted {new['released']}:")
    print(f"  top 12 shared: {hit12} of 12;  top 25 shared: {hit25} of 25")
    print(f"  median miss in rank: {np.median(err):.0f} spots (just carrying last week's rank: {np.median(naive):.0f})")
    for i, t in enumerate(real[:16]):
        print(f"   committee {i+1:>2}  stand-in {pred.index(t)+1:>3}  {t}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backtest", help="older committee ranking JSON to anchor on")
    ap.add_argument("--inject", help="queue file whose LEVERAGE_FIG markers get the new figure")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--n", type=int, default=60000)
    ap.add_argument("--from", dest="lo", default="2026-11-26")
    ap.add_argument("--to", dest="hi", default="2026-11-28")
    a = ap.parse_args()
    if a.backtest:
        return backtest(a.backtest)
    if a.refresh:
        r = fetch_ranking(); print(f"  ranking released {r['released']}: " + ", ".join(x["team"] for x in r["top25"][:12]))
        fetch_sp()
    res = run(a.n, a.lo, a.hi)
    json.dump(res, open(os.path.join(HERE, "leverage.json"), "w"), indent=1)
    fig = svg(res)
    open(os.path.join(HERE, "figure.svg"), "w").write(fig)
    if a.inject:
        inject(a.inject, fig)
    pct = lambda x: f"{100 * x:3.0f}"
    print(f"\nCommittee ranking of {res['ranking_released']}, SP+ of {res['sp_taken']}, {res['n']:,} seasons")
    print("Rivalry week, by leverage (points of playoff chance that change hands):")
    for g in res["games"][:15]:
        a_, h_ = g["sides"][1], g["sides"][0]
        rk = lambda r: f"#{r} " if r <= 25 else ""
        print(f"  {100*g['leverage']:4.0f}  {rk(g['arank'])}{g['away']} at {rk(g['hrank'])}{g['home']}"
              f" ({g['date']})   {a_['team']}: {pct(a_['if_win'])}/{pct(a_['if_lose'])}"
              f"  {h_['team']}: {pct(h_['if_win'])}/{pct(h_['if_lose'])}  win {pct(a_['p_win'])}/{pct(h_['p_win'])}"
              f"  [moves {100*g['expected_move']:.0f}; others {100*g['third']:.0f}]")
    print("\nPlayoff chance now (bid / bye):")
    for b in res["board"]:
        print(f"  {str(b['cfp'] or '-'):>3} {b['team']:<16} {pct(b['in'])} {pct(b['bye'])}")


if __name__ == "__main__":
    main()
