#!/usr/bin/env python3
"""How good was Saturday for one team's fans? Expected rooting wins against actual.

    python3 scripts/fan_saturday.py --date 2026-11-07
    python3 scripts/fan_saturday.py --date 2026-11-07 --team "Notre Dame" --json

WHAT IT MEASURES. A fan's Saturday has two parts: our own game, and everyone
else's. For the second part the standing rules in data/rooting-rules.json say
which result we want in each game -- teams ranked above us lose, teams within a
few spots of us lose, teams we beat beat teams ranked above us, rivals lose. The
vig-free moneyline gives the chance of each wished-for result, so their sum is
the number a normal Saturday hands you. The count that actually happened is set
against it, with the chance of doing at least that well.

It is the Sunday Edition's upset arithmetic pointed at one fan base: one long
shot coming in is ordinary; several on one card is what a fan calls Christmas.

Lines come from ESPN's game pages (the scoreboard drops them once games end);
a game with neither a moneyline nor a spread is listed but not scored.
Ranks are the ones ESPN shows on the day, so a week's games are judged
against the ranking that stood when they kicked off.
"""
import argparse, json, math, os, sys, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = os.path.join(REPO, "data", "rooting-rules.json")
SITE = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
SD = 16.5


def get(url):
    return json.load(urllib.request.urlopen(url, timeout=30))


def implied(ml):
    ml = float(ml)
    return 100 / (ml + 100) if ml > 0 else -ml / (-ml + 100)


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def win_prob(event_id, side):
    """Pregame chance that `side` ('home'/'away') wins, or None."""
    pcs = get(f"{SITE}/summary?event={event_id}").get("pickcenter") or []
    other = "away" if side == "home" else "home"
    for pc in pcs:
        try:
            a = implied(pc[side + "TeamOdds"]["moneyLine"])
            b = implied(pc[other + "TeamOdds"]["moneyLine"])
            return a / (a + b)
        except (KeyError, TypeError, ValueError):
            pass
        if pc.get("spread") is not None:
            home_p = phi(-float(pc["spread"]) / SD)
            return home_p if side == "home" else 1 - home_p
    return None


def names(team):
    t = team["team"]
    return {t.get("location"), t.get("shortDisplayName"), t.get("displayName"), t.get("abbreviation")}


def rank(c):
    r = c.get("curatedRank", {}).get("current", 99)
    return r if 0 < r <= 25 else 99


def beaten_opponents(espn_id, season, before):
    """Teams our side has beaten this season, in games before `before` (YYYYMMDD)."""
    out = set()
    for ev in get(f"{SITE}/teams/{espn_id}/schedule?season={season}").get("events", []):
        if ev["date"][:10].replace("-", "") >= before:
            continue
        comp = ev["competitions"][0]
        us = [x for x in comp["competitors"] if str(x["id"]) == str(espn_id)]
        them = [x for x in comp["competitors"] if str(x["id"]) != str(espn_id)]
        if us and them and us[0].get("winner"):
            out.add(them[0]["team"]["location"])
    return out


def wish(team_c, opp_c, our_rank, rules, beaten):
    """Why we want team_c to LOSE this game, or None."""
    r, ro = rank(team_c), rank(opp_c)
    if names(team_c) & set(rules.get("rivals_always_lose", [])):
        return "rival"
    if team_c["team"]["location"] in beaten and ro < our_rank and rules.get("beaten_opponents_beat_teams_above_us"):
        return None  # this side we want to WIN; handled from the other side
    if opp_c["team"]["location"] in beaten and r < our_rank:
        return f"No. {r}, above us, against a team we beat"
    if rules.get("above_us_lose") and r < our_rank:
        return f"No. {r}, above us"
    if r != 99 and abs(r - our_rank) <= rules.get("bubble_spots", 0):
        return f"No. {r}, on our bubble"
    return None


def at_least(ps, k):
    """Poisson-binomial: P(at least k of these independent wishes come true)."""
    dist = [1.0]
    for p in ps:
        nxt = [0.0] * (len(dist) + 1)
        for i, q in enumerate(dist):
            nxt[i] += q * (1 - p)
            nxt[i + 1] += q * p
        dist = nxt
    return sum(dist[k:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD, the Saturday")
    ap.add_argument("--team", default="Notre Dame")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    rules = json.load(open(RULES))[a.team]
    day = a.date.replace("-", "")
    board = get(f"{SITE}/scoreboard?groups=80&limit=300&dates={day}")
    beaten = beaten_opponents(rules["espn_id"], a.date[:4], day) if rules.get("beaten_opponents_beat_teams_above_us") else set()

    our_rank, ours = 99, None
    for ev in board["events"]:
        for c in ev["competitions"][0]["competitors"]:
            if str(c["id"]) == str(rules["espn_id"]):
                our_rank, ours = rank(c), ev

    games = []
    for ev in board["events"]:
        if ev is ours:
            continue
        comp = ev["competitions"][0]
        if not comp["status"]["type"].get("completed"):
            continue
        h, w = comp["competitors"]
        whys = [(x, y, wish(x, y, our_rank, rules, beaten)) for x, y in ((h, w), (w, h))]
        whys = [t for t in whys if t[2]]
        if not whys:
            continue
        if len(whys) == 2:  # both sides on the lose list: neutral unless one is a rival
            whys = [t for t in whys if t[2] == "rival"]
            if len(whys) != 1:
                continue
        loser_wanted, winner_wanted, why = whys[0]
        p = win_prob(ev["id"], winner_wanted["homeAway"])
        got = bool(winner_wanted.get("winner"))
        games.append({
            "want": f"{winner_wanted['team']['location']} over {loser_wanted['team']['location']}",
            "why": why, "p": p, "got": got,
            "score": f"{winner_wanted['score']}-{loser_wanted['score']}",
        })

    scored = [g for g in games if g["p"] is not None]
    expected = sum(g["p"] for g in scored)
    actual = sum(g["got"] for g in scored)
    tail = at_least([g["p"] for g in scored], actual) if scored else None

    own = None
    if ours:
        comp = ours["competitions"][0]
        us = next(x for x in comp["competitors"] if str(x["id"]) == str(rules["espn_id"]))
        them = next(x for x in comp["competitors"] if x is not us)
        own = {"vs": them["team"]["location"], "won": bool(us.get("winner")),
               "score": f"{us['score']}-{them['score']}", "p": win_prob(ours["id"], us["homeAway"])}

    out = {"team": a.team, "date": a.date, "rank": our_rank, "own": own, "games": games,
           "expected": expected, "actual": actual, "p_at_least": tail}
    if a.json:
        print(json.dumps(out, indent=2))
        return
    print(f"{a.team} (No. {our_rank}) on {a.date}")
    if own:
        pr = "?" if own["p"] is None else f"{own['p']:.0%}"
        print(f"  Our game: {'W' if own['won'] else 'L'} {own['score']} vs {own['vs']} (we were {pr} to win)")
    for g in sorted(games, key=lambda g: (g["p"] is None, g["p"] or 0)):
        pr = "  ?" if g["p"] is None else f"{g['p']:.0%}"
        print(f"  {'YES' if g['got'] else ' no'}  {pr:>4}  wanted {g['want']} ({g['why']})  {g['score'] if g['got'] else ''}")
    if scored:
        print(f"  Expected wishes granted: {expected:.1f} of {len(scored)}. Granted: {actual}. "
              f"Chance of at least that many: {tail:.0%}")


if __name__ == "__main__":
    main()
