#!/usr/bin/env python3
"""Check every score in a piece against two independent feeds.

Written 2026-11-02 after Sunday Edition No. 030 printed the Notre Dame-Navy
halftime score two different ways, both wrong (Navy "led 13-7 at halftime" in
one paragraph and "trailed 13-7 at halftime" in another; Notre Dame led 14-13),
plus a 7-6 first quarter that was 7-3 and an 8-1 record that was 7-1. Every
number in that edition sat inside accurate context, which is why nobody caught
it. The editor's instruction: double-check all scores, every time.

What it does
  1. Pulls every game in the window (default: the 10 days up to the piece's
     date) for CFB, NFL, MLB, NHL, men's college basketball and the WNBA from
     ESPN's scoreboard, then pulls a SECOND, independent feed for each game the
     piece mentions: CollegeFootballData (CFB), the MLB Stats API (MLB),
     nflverse (NFL), the NHL's own API (NHL). Basketball has no second feed yet
     and is marked single-source.
  2. Finds every score-shaped number (13-7, 35-13, 7-1) in the prose and tables,
     works out which game it belongs to from the team names around it, and
     checks it against the right moment: the final, halftime, the end of a
     quarter/period/inning, or any score the game actually passed through
     ("Navy led 13-7").
  3. Records ("Now 7-1") are checked against the team's record in the feed.
  4. --aibox adds a second extractor: the AI box lists the score claims it can
     find, including ones written in words ("led by six at the half"). The box
     only POINTS at claims; every claim is still settled by the feeds, and a
     quote it returns that is not in the piece word for word is thrown away.

Verdicts
  OK        matches the feed (both feeds where there are two)
  WRONG     a named game, and the number is not a score it ever had at that moment
  RECORD?   looks like a record and does not match the team's record
  DISAGREE  the two feeds disagree with each other: settle by hand
  CHECK     only one team is named, and none of its games ended that way:
            look at it (does not fail the run)
  UNCHECKED no game in the window matches (old seasons, series results, other
            sports); listed so a person can see what was not checked

Exit status 1 if anything is WRONG, RECORD? or DISAGREE, so it can gate a publish.

Text inside an element marked data-scorecheck="skip" is ignored. Use it on a
correction box, which quotes the wrong score on purpose.

Usage
  python3 scripts/check_scores.py published/sunday-030.html
  python3 scripts/check_scores.py queue/*.html --date 2026-11-01 --days 14
  python3 scripts/check_scores.py published/sunday-030.html --aibox
"""
import argparse, csv, datetime as dt, html, io, json, os, pathlib, re, sys, time, urllib.request

CACHE = pathlib.Path.home() / ".cache/sports-page/scores"
UA = {"User-Agent": "TheSportsPage-scorecheck/1.0"}
AIBOX = os.environ.get("AIBOX", "http://192.168.0.65:11434")

# league key -> (espn path, extra query, halftime period, period word)
LEAGUES = {
    "cfb":  ("football/college-football", "&groups=80", 2, "quarter"),
    "fcs":  ("football/college-football", "&groups=81", 2, "quarter"),
    "nfl":  ("football/nfl", "", 2, "quarter"),
    "mlb":  ("baseball/mlb", "", None, "inning"),
    "nhl":  ("hockey/nhl", "", None, "period"),
    "cbb":  ("basketball/mens-college-basketball", "&groups=50", 1, "half"),
    "wnba": ("basketball/wnba", "", 2, "quarter"),
}
WORDNUM = {"one": 1, "first": 1, "1st": 1, "two": 2, "second": 2, "2nd": 2, "three": 3,
           "third": 3, "3rd": 3, "four": 4, "fourth": 4, "4th": 4, "five": 5, "fifth": 5,
           "six": 6, "sixth": 6, "seven": 7, "seventh": 7, "eight": 8, "eighth": 8}
NUMWORD = {"six": 6, "seven": 7, "three": 3, "two": 2, "one": 1, "four": 4, "five": 5,
           "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "fourteen": 14, "twenty": 20}


# ---------------------------------------------------------------- fetching
def fetch(url, cache_name=None, final=True, headers=None, raw=False):
    p = CACHE / cache_name if cache_name else None
    if p and p.exists():
        return p.read_text() if raw else json.loads(p.read_text())
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read().decode()
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)
    if p and final:
        CACHE.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    return body if raw else json.loads(body)


def espn_day(lg, day):
    path, extra, _, _ = LEAGUES[lg]
    ds = day.strftime("%Y%m%d")
    old = day < dt.date.today() - dt.timedelta(days=1)
    try:
        d = fetch(f"https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard?dates={ds}&limit=500{extra}",
                  f"espn-{lg}-{ds}.json", final=old)
    except Exception:
        return []
    games = []
    for e in d.get("events", []):
        c = e["competitions"][0]
        if not c["status"]["type"].get("completed"):
            continue
        teams = []
        for t in c["competitors"]:
            tm = t["team"]
            rec = next((r["summary"] for r in t.get("records", []) if r.get("type") in ("total", None)), None) \
                or (t.get("records") or [{}])[0].get("summary")
            teams.append(dict(
                id=tm["id"], name=tm.get("displayName", ""), short=tm.get("shortDisplayName", ""),
                loc=tm.get("location", ""), nick=tm.get("name", ""), abbr=tm.get("abbreviation", ""),
                score=int(float(t.get("score") or 0)), lines=[int(float(l.get("value", 0))) for l in t.get("linescores", [])],
                record=rec, home=t.get("homeAway") == "home"))
        games.append(dict(lg=lg, id=e["id"], date=day, name=e["name"], teams=teams, plays=None))
    return games


def espn_states(g):
    """Every score the game passed through, from ESPN's scoring plays (lazy)."""
    if g["plays"] is None:
        path = LEAGUES[g["lg"]][0]
        g["plays"] = []
        try:
            d = fetch(f"https://site.api.espn.com/apis/site/v2/sports/{path}/summary?event={g['id']}",
                      f"espn-sum-{g['lg']}-{g['id']}.json")
            for p in d.get("scoringPlays", []):
                g["plays"].append((p["awayScore"], p["homeScore"]))
        except Exception:
            pass
    home = [t for t in g["teams"] if t["home"]] or g["teams"][1:]
    away = [t for t in g["teams"] if not t["home"]] or g["teams"][:1]
    if not home or not away:
        return set()
    out = set()
    for a, h in g["plays"]:
        out.add(frozenset_pair(away[0]["id"], a, home[0]["id"], h))
    return out


def frozenset_pair(id1, s1, id2, s2):
    return ((id1, s1), (id2, s2)) if id1 < id2 else ((id2, s2), (id1, s1))


def period_states(g):
    """{period: (scoreA, scoreB)} cumulative at the end of each period."""
    a, b = g["teams"]
    out, ca, cb = {}, 0, 0
    for i, (x, y) in enumerate(zip(a["lines"], b["lines"]), 1):
        ca += x; cb += y
        out[i] = (ca, cb)
    return out


# ---------------------------------------------------------------- second feeds
def second_source(g):
    """(feed name, scoreA, scoreB, linesA or None, linesB or None) or None."""
    a, b = g["teams"]
    try:
        if g["lg"] in ("cfb", "fcs"):
            return cfbd(g, a, b)
        if g["lg"] == "mlb":
            return mlbapi(g, a, b)
        if g["lg"] == "nfl":
            return nflverse(g, a, b)
        if g["lg"] == "nhl":
            return nhlapi(g, a, b)
    except Exception as ex:
        return ("error: %s" % str(ex)[:60], None, None, None, None)
    return None


def _match(n1, n2):
    n1, n2 = n1.lower(), n2.lower()
    return n1 == n2 or n1 in n2 or n2 in n1


def cfbd(g, a, b):
    key = os.environ.get("CFBD_KEY")
    if not key:
        return ("CFBD (no key in environment)", None, None, None, None)
    yr = g["date"].year
    games = fetch(f"https://api.collegefootballdata.com/games?year={yr}&team={urllib.parse.quote(a['loc'])}",
                  f"cfbd-{yr}-{a['loc'].replace(' ', '_')}.json",
                  final=g["date"] < dt.date.today() - dt.timedelta(days=1),
                  headers={"Authorization": f"Bearer {key}"})
    for x in games:
        if not x.get("completed"):
            continue
        h, aw = x["homeTeam"], x["awayTeam"]
        for ta, tb in ((a, b), (b, a)):
            if _match(h, ta["loc"]) and _match(aw, tb["loc"]):
                d = dt.date.fromisoformat(x["startDate"][:10])
                if abs((d - g["date"]).days) <= 1:
                    la, lb = x.get("homeLineScores"), x.get("awayLineScores")
                    if ta is a:
                        return ("CollegeFootballData", x["homePoints"], x["awayPoints"], la, lb)
                    return ("CollegeFootballData", x["awayPoints"], x["homePoints"], lb, la)
    return ("CollegeFootballData (game not found)", None, None, None, None)


def mlbapi(g, a, b):
    ds = g["date"].isoformat()
    d = fetch(f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={ds}&hydrate=linescore",
              f"mlb-{ds}.json", final=g["date"] < dt.date.today() - dt.timedelta(days=1))
    for day in d.get("dates", []):
        for x in day["games"]:
            t = x["teams"]
            for ta, tb, s1, s2 in ((a, b, "home", "away"), (b, a, "home", "away")):
                if _match(t[s1]["team"]["name"], ta["name"]) and _match(t[s2]["team"]["name"], tb["name"]):
                    inn = x.get("linescore", {}).get("innings", [])
                    l1 = [i.get(s1, {}).get("runs", 0) for i in inn]
                    l2 = [i.get(s2, {}).get("runs", 0) for i in inn]
                    if ta is a:
                        return ("MLB Stats API", t[s1].get("score"), t[s2].get("score"), l1, l2)
                    return ("MLB Stats API", t[s2].get("score"), t[s1].get("score"), l2, l1)
    return ("MLB Stats API (game not found)", None, None, None, None)


def nflverse(g, a, b):
    raw = fetch("https://github.com/nflverse/nfldata/raw/master/data/games.csv",
                f"nflverse-games-{dt.date.today()}.csv", raw=True)
    for x in csv.DictReader(io.StringIO(raw)):
        if x["gameday"] and abs((dt.date.fromisoformat(x["gameday"]) - g["date"]).days) <= 1 and x["home_score"]:
            for ta, tb in ((a, b), (b, a)):
                if x["home_team"] == _nflabbr(ta["abbr"]) and x["away_team"] == _nflabbr(tb["abbr"]):
                    hs, as_ = int(x["home_score"]), int(x["away_score"])
                    return ("nflverse", hs, as_, None, None) if ta is a else ("nflverse", as_, hs, None, None)
    return ("nflverse (game not found)", None, None, None, None)


def _nflabbr(e):
    return {"WSH": "WAS", "LAR": "LA", "JAX": "JAX"}.get(e, e)


def nhlapi(g, a, b):
    ds = g["date"].isoformat()
    d = fetch(f"https://api-web.nhle.com/v1/score/{ds}", f"nhl-{ds}.json",
              final=g["date"] < dt.date.today() - dt.timedelta(days=1))
    for x in d.get("games", []):
        h, aw = x["homeTeam"], x["awayTeam"]
        for ta, tb in ((a, b), (b, a)):
            if h.get("abbrev") == ta["abbr"] and aw.get("abbrev") == tb["abbr"]:
                return ("NHL API", h["score"], aw["score"], None, None) if ta is a else ("NHL API", aw["score"], h["score"], None, None)
    return ("NHL API (game not found)", None, None, None, None)


# ---------------------------------------------------------------- text
def units(path):
    """Prose and table rows as checkable units, with the paragraph each sits in."""
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"(?s)<!--.*?-->|<style.*?</style>|<script.*?</script>|<svg.*?</svg>|<head.*?</head>", " ", s)
    s = re.sub(r'(?s)<(\w+)[^>]*data-scorecheck="skip".*?</\1>', " ", s)
    # A correction box quotes the wrong number on purpose.
    s = re.sub(r'(?s)<div[^>]*>\s*<h3[^>]*>\s*Correction.*?</div>', " ", s)
    s = re.sub(r"(?s)<div class=\"footer\".*", " ", s)
    blocks = re.split(r"(?i)</(?:p|tr|li|h1|h2|h3|div|figcaption)>", s)
    out = []
    for b in blocks:
        b = re.sub(r"(?i)</t[dh]>", " | ", b)
        t = html.unescape(re.sub(r"<[^>]+>", " ", b))
        t = re.sub(r"\s+", " ", t).strip()
        if not t:
            continue
        # Do not end a sentence at "vs." or "No." -- "Mets won 4-3 vs. Angels on
        # May 2" must stay one sentence or the date never meets the score.
        t2 = re.sub(r"\b(vs|No|Nos|St|Jr|Sr|Mt|Dr|Mr|Ms|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|a\.m|p\.m|U\.S)\.",
                    lambda mm: mm.group(1) + "\u2024", t)
        for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z\"“])", t2):
            out.append((sent.replace("\u2024", "."), t))
    return out


def piece_date(path):
    s = open(path, encoding="utf-8").read()
    m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)"
                  r"\s+(\d{1,2}),\s+(\d{4})", re.sub(r"<[^>]+>", " ", s[:20000]))
    if m:
        return dt.datetime.strptime(" ".join(m.groups()), "%B %d %Y").date()
    return dt.date.today()


SCORE = re.compile(r"(?<![\d.$,/–—-])(\d{1,3})\s?[–—-]\s?(\d{1,3})(?![\d%,]|\s?[–—-]\s?\d|\s?(?:yard|yd|point|run|minute|game|win|loss|pick|seed)s?\b)")


def aliases(t):
    out = set()
    for k in ("name", "short", "loc", "nick"):
        v = t[k].strip()
        if len(v) >= 4 and v.lower() not in ("state", "city", "team", "united"):
            out.add(v)
    return out


def mentioned(text, games):
    hits = {}
    for g in games:
        for i, t in enumerate(g["teams"]):
            for al in aliases(t):
                if re.search(r"(?<![A-Za-z])" + re.escape(al) + r"(?![A-Za-z])", text):
                    hits.setdefault(g["id"], set()).add(i)
            if t["abbr"] and len(t["abbr"]) >= 2 and re.search(r"(?<![A-Za-z])" + re.escape(t["abbr"]) + r"(?![A-Za-z])", text) \
                    and t["abbr"] not in ("A", "AT", "IN", "ON", "OR", "US", "SO", "NO", "TO", "OK"):
                hits.setdefault(g["id"], set()).add(i)
    return hits


MOMENT = re.compile(r"half ?time|at the half|at half\b|after (?:the )?(one|two|three|four|five|six|seven|eight|first|second|third)"
                    r"\s*(quarters?|periods?|innings?|half)\b|end of (?:the )?(first|second|third|fourth|1st|2nd|3rd)"
                    r"\s*(quarter|period|inning)?|(first|second|third)[- ](quarter|period) (?:score|lead)", re.I)


def moment(text, start, end, lg):
    """'H', ('P', n) or None. Each moment phrase belongs to the score nearest it,
    so in "trailed 7-3 after one quarter and led 13-7 with 1:52 left" the quarter
    goes to the 7-3 and the 13-7 gets no moment (any score the game passed through)."""
    scores = [(o.start(), o.end()) for o in SCORE.finditer(text)] or [(start, end)]
    def dist(ph, sc):
        return sc[0] - ph.end() if ph.end() <= sc[0] else (ph.start() - sc[1] if ph.start() >= sc[1] else 0)
    best = None
    for m in MOMENT.finditer(text):
        near = min(scores, key=lambda sc: (dist(m, sc), sc[0] < m.start()))
        if near != (start, end) or dist(m, near) > 70:
            continue
        d = dist(m, near)
        if best is not None and d >= best[0]:
            continue
        g = m.group(0).lower()
        if "half" in g and ("time" in g or "at the half" in g or "at half" in g):
            best = (d, "H")
        else:
            n = next(WORDNUM[w.lower()] for w in (m.group(1), m.group(3), m.group(5)) if w)
            unit = (m.group(2) or m.group(4) or m.group(6) or "").lower()
            best = (d, "H") if unit == "half" else (d, ("P", n))
    return best[1] if best else None


# ---------------------------------------------------------------- checking
WIN_VERB = re.compile(r"\b(won|wins|win|beat|beats|beating|defeated|defeats|defeating|topped|tops|edged|edges|routed|"
                      r"routs|blanked|shut out|led|leads|leading|ahead)\b", re.I)
LOSE_VERB = re.compile(r"\b(lost|loses|lose|losing|fell|falls|dropped|trailed|trails|trailing|behind)\b", re.I)


def direction(sent, start, g, clause_start=0):
    """(team index, 'win'|'lose') for "X beat Y 7-3" / "X trailed 3-7", else None.
    The verb nearest before the score decides; its subject is the team of this
    game named nearest before the verb."""
    pre = sent[:start]
    # the verb must sit in this score's own clause; its subject may come earlier
    # ("Navy trailed 7-3 after one quarter and led 13-7")
    verbs = [(m.start(), "win") for m in WIN_VERB.finditer(pre) if m.start() >= clause_start] + \
            [(m.start(), "lose") for m in LOSE_VERB.finditer(pre) if m.start() >= clause_start]
    if not verbs:
        return None
    vpos, dirn = max(verbs)
    if start - vpos > 70:
        return None
    best = None
    for i, t in enumerate(g["teams"]):
        for al in aliases(t):
            for m in re.finditer(r"(?<![A-Za-z])" + re.escape(al) + r"(?![A-Za-z])", pre[:vpos]):
                # "Massachusetts went to Rutgers and won": Rutgers is the object.
                if re.search(r"\b(to|at|visit(?:ed|ing|s)?|host(?:ed|ing|s)?|against|vs\.?|over|from|beat|beating)\s+(?:the\s+|No\. \d+\s+)?$",
                             pre[max(0, m.start() - 22):m.start()], re.I):
                    continue
                if best is None or m.end() > best[0]:
                    best = (m.end(), i)
    if best is None or vpos - best[0] > 60:
        return None
    return best[1], dirn


def _dir_ok(mine, theirs, dirn):
    return mine == theirs or (mine > theirs) == (dirn == "win")


def check_pair(g, x, y, mom, text, subj=None):
    """Return (verdict, detail) for the pair (x, y) in game g. With subj=(i, dir),
    also check who was ahead: a score printed the wrong way round is wrong."""
    a, b = g["teams"]
    pa, pb = a["score"], b["score"]
    per = period_states(g)
    half = LEAGUES[g["lg"]][2]
    pair = sorted((x, y))
    label = f"{a['short'] or a['loc']} {pa}, {b['short'] or b['loc']} {pb}"

    def backwards(sa, sb, when):
        if not subj:
            return None
        i, dirn = subj
        mine, theirs = (sa, sb) if i == 0 else (sb, sa)
        if _dir_ok(mine, theirs, dirn):
            return None
        who = g["teams"][i]
        verb = {"win": "won/led", "lose": "lost/trailed"}[dirn]
        return ("WRONG", f"backwards: the piece says {who['loc']} {verb}, but {when} was "
                         f"{a['loc']} {sa}, {b['loc']} {sb}")

    if mom is not None:
        n = half if mom == "H" else mom[1]
        if n is None or n not in per:
            return ("UNCHECKED", f"no {('halftime' if mom == 'H' else 'period %d' % n)} line in feed")
        sa, sb = per[n]
        want = "halftime" if mom == "H" else f"after {n}"
        if sorted((sa, sb)) == pair:
            return backwards(sa, sb, want) or ("OK", f"{want}: {a['loc']} {sa}, {b['loc']} {sb}")
        return ("WRONG", f"{want} was {a['loc']} {sa}, {b['loc']} {sb} (final {label})")
    if sorted((pa, pb)) == pair:
        return backwards(pa, pb, "the final") or ("OK", f"final {label}")
    finalwords = re.search(r"\b(won|wins|beat|beats|defeated|final|lost|loses|fell|routed|edged|topped)\b", text, re.I)
    states = [(sa, sb) for sa, sb in per.values()]
    for st in espn_states(g):
        d = dict(st)
        states.append((d.get(a["id"]), d.get(b["id"])))
    hits = [st for st in states if None not in st and sorted(st) == pair]
    if hits and not finalwords:
        for sa, sb in hits:
            if not backwards(sa, sb, "that score"):
                return ("OK", f"a score the game passed through (final {label})")
        return backwards(*hits[0], "that score")
    if hits:
        return ("WRONG", f"that was a score during the game, not the final ({label})")
    return ("WRONG", f"never a score in this game ({label})")


def family(lg):
    return {"fcs": "cfb"}.get(lg, lg)


def record_check(t, lg, x, y, all_games):
    """Did this team hold the record x-y at any point in the window? A Sunday
    Edition talks about last week as well as today, so 'Florida had been 4-0'
    is right if Florida was 4-0 before its latest game."""
    held, latest = set(), None
    for g in sorted(all_games, key=lambda g: g["date"]):
        if family(g["lg"]) != family(lg):
            continue
        for tm in g["teams"]:
            if tm["id"] != t["id"] or not tm["record"]:
                continue
            w = [int(n) for n in re.findall(r"\d+", tm["record"])]
            if len(w) < 2:
                continue
            other = [o for o in g["teams"] if o is not tm][0]
            won = tm["score"] > other["score"]
            held.add((w[0], w[1]))
            held.add((w[0] - 1, w[1]) if won else (w[0], w[1] - 1))
            latest = tm["record"]
    if latest is None:
        return None
    if (x, y) in held:
        return ("OK", f"{t['loc']} held {x}-{y} in the window (now {latest})")
    return ("RECORD?", f"{t['loc']} was never {x}-{y} in the window (now {latest})")


def nearest_record(sent, pos, x, y, games):
    """A record belongs to a team named before it in the sentence. OK if any
    team named there held it ("Notre Dame ... beating North Carolina 37-26 to
    move to 5-0"); otherwise flag, naming the nearest team. Teams that share a
    name (the Raiders of Las Vegas and of Colgate) are all tried."""
    found = []
    for g in games:
        for t in g["teams"]:
            names = aliases(t) | ({t["abbr"]} if len(t["abbr"]) >= 3 else set())
            for al in names:
                for mm in re.finditer(r"(?<![A-Za-z])" + re.escape(al) + r"(?![A-Za-z])", sent[:pos]):
                    found.append((mm.end(), al))
    if not found:
        return None
    nearest = max(found)[1]
    checks = {}
    for g in games:
        for t in g["teams"]:
            for end, al in found:
                if al in aliases(t) or al == t["abbr"]:
                    key = (family(g["lg"]), t["id"])
                    if key not in checks:
                        checks[key] = (record_check(t, g["lg"], x, y, games), al == nearest)
    ok = [c for c, _ in checks.values() if c and c[0] == "OK"]
    if ok:
        return ok[0]
    flag = [c for c, near in checks.values() if c and near]
    return ("RECORD?", "; ".join(c[1] for c in flag[:3])) if flag else None


SKIP_PRE = re.compile(r"\b(swe(?:pt|ep)|series|alds|alcs|nlds|nlcs|wild card|best-of|stanley cup|the final|finals|"
                      r"playoffs?|postseason|game [1-7]\b|games [1-7]\b|since the break|over these|over the last|"
                      r"in (?:his|her|their) first (?:\d+|two|three|four|five|six|seven|eight|nine|ten|\w+ (?:games|starts|seasons|weeks))|last (?:year|season)|\bago\b|\bcup\b|stretch|"
                      r"over (?:their|the|its) last|(?:last|over) (?:ten|twenty|thirty|\d+)\b|at (?:ten|twenty|thirty)\b|"
                      r"through (?:\w+ )?(?:of those )?games|need(?:s|ed)? to go|would go|"
                      r"to finish|projected|projection|pace|outscored|combined|aggregate|all-time|since \d{4})\b", re.I)
SKIP_POST = re.compile(r"^[\s,)]*(?:in |against |vs\.? |on the |at )?(?:the )?(sec|acc|big ten|big 12|pac-12|mwc|aac|"
                       r"conference|league|in-conference|at home|on the road|road|away|ats|against the spread|"
                       r"off a bye|since|all-time|series|in games|in one-score|in close|when|as a|as an|lifetime|career|"
                       r"head-to-head|in the series|sec play|acc play|big ten play|in (?:sec|acc|big ten|big 12|conference) play)\b"
                       r"|^[^.]{0,40}\b(next (?:two|three|four) games|game [1-7]\b|in game|series|playoffs?|postseason|"
                       r"since the|over (?:these|the last)|in (?:the )?(?:month|week)s?|this (?:month|week)|last (?:year|season)|"
                       r"over (?:ten|twenty|thirty|\w+ games)|in extra|in one-run|in (?:their|the) last|with an? (?:\d|era)|era\b|"
                       r"as a starter|in (?:his|her) (?:starts|career))\b", re.I)
SCORE_CUE = re.compile(r"\b(beat|beats|beating|won|win|wins|defeated|defeating|lost|lose|loses|losing|fell|falls|edged|"
                       r"topped|routed|over|led|leads|leading|trailed|trails|trailing|lead|final|scored|shutout|blowout|"
                       r"loss|victory|win over|close to|cut it to|pulled within|tied it at|made it|tied|scoreline)\b", re.I)
REC_CUE_PRE = re.compile(r"(\b(now|is|are|was|were|at|stays?|stands?|improved to|improves to|fell to|falls to|drops? to|"
                         r"dropped to|moves? to|moved to|went|goes to|go to|to|had been|been|sits? at|record of|record)\s*|\()$", re.I)
REC_CUE_POST = re.compile(r"^\s*[,)]?\s*(record|on the season|overall|this season|heading into|going into|entering|start|team)\b", re.I)
# Only a record stated as CURRENT can fail; anything else passes if the team held
# it in the window and is otherwise listed, not judged.
REC_NOW = re.compile(r"\b(now|is|are|stays?|stands?|sits? at|at|improved to|improves to|moves? to|moved to|move to|"
                     r"fell to|falls to|drops? to|dropped to|record now|record is)\s*\(?$", re.I)


def series_tally(cands_games, games, x, y):
    """'The Padres beat the Cubs 2-0' is a series, not a game. Accept any running
    tally of wins between the two teams across the window."""
    for g in cands_games:
        ids = {t["id"] for t in g["teams"]}
        meet = sorted((h for h in games if h["lg"] == g["lg"] and {t["id"] for t in h["teams"]} == ids),
                      key=lambda h: (h["date"], h["id"]))
        if len(meet) < 2:
            continue
        w = {i: 0 for i in ids}
        for h in meet:
            win = max(h["teams"], key=lambda t: t["score"])["id"]
            w[win] += 1
            if sorted(w.values()) == sorted((x, y)):
                a, b = g["teams"]
                return ("OK", f"series tally {a['loc']} {w[a['id']]}, {b['loc']} {w[b['id']]} after {h['date']}")
    return None


def record_for(sent, para, pos, x, y, games):
    """A record belongs to a team named before it: first in its own sentence,
    then anywhere earlier in the paragraph or table row ("Notre Dame ... Lost to
    No. 8 BYU 28-24 on Oct 17. Now 6-1.")."""
    r = nearest_record(sent, pos, x, y, games)
    if (r is None or r[0] != "OK") and para.find(sent) > 0:
        r2 = nearest_record(para, para.find(sent) + pos, x, y, games)
        if r2 and (r2[0] == "OK" or r is None):
            r = r2
    return r


MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def named_date(text, start, end, window_end):
    """A date written beside the score ("on May 2", "Oct. 17", "on Saturday"), else None."""
    win = text[max(0, start - 40):end + 40]
    m = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})\b", win, re.I)
    if m:
        try:
            return dt.date(window_end.year, MONTHS[m.group(1).lower()[:3]], int(m.group(2)))
        except ValueError:
            return None
    m = re.search(r"\bon (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", win, re.I)
    if m:
        k = WEEKDAYS.index(m.group(1).lower())
        return window_end - dt.timedelta(days=(window_end.weekday() - k) % 7)
    return None


def verify(claims_text, games, lgs_seen, window_end=None):
    """Classify each score-shaped number, then check only what it claims to be.
    A number is treated as a GAME SCORE only with a score word next to it (beat,
    led, trailed, final) or a moment (at halftime); as a RECORD only with a
    record word (now, is, stays, moved to); series, conference, season and
    projected numbers are listed, not judged. Precision over recall: a checker
    that cries wolf gets switched off."""
    results = []
    for sent, para in claims_text:
        prev_end = 0
        for m in SCORE.finditer(sent):
            x, y = int(m.group(1)), int(m.group(2))
            pre_all = sent[max(0, m.start() - 70):m.start()].split(" | ")[-1]   # never read into the next table cell
            prev_start = prev_end
            pre = sent[max(prev_end, m.start() - 45):m.start()]       # do not borrow the previous score's verb
            post = sent[m.end():m.end() + 45]
            prev_end = m.end()
            quote = sent[max(0, m.start() - 70):m.end() + 50].strip()
            if x > 200 or y > 200:
                continue
            hits = mentioned(sent, games)
            both = [gid for gid, st in hits.items() if len(st) == 2]
            if not both:
                ph = mentioned(para, games)
                both = [gid for gid, st in ph.items() if len(st) == 2]
            cand = [g for g in games if g["id"] in both]
            when0 = named_date(sent, m.start(), m.end(), window_end) if window_end else None
            if not cand and when0 and hits:
                cand = [g for g in games if g["id"] in hits and g["date"] == when0]
            if SKIP_PRE.search(pre_all) or SKIP_POST.search(post):
                st = series_tally(cand, games, x, y) if cand else None
                results.append((st[0], f"{x}-{y}", quote, st[1]) if st else
                               ("UNCHECKED", f"{x}-{y}", quote, "series, conference, split or projection"))
                continue
            mom = moment(sent, m.start(), m.end(), cand[0]["lg"]) if cand else None
            is_score = bool(SCORE_CUE.search(pre) or mom)
            is_record = bool(REC_CUE_PRE.search(pre) or REC_CUE_POST.search(post)) and not mom
            # "went 3-9 last year", "had been 4-0", "went 12-12 in the month since":
            # a past stretch. Fine if the team held it in the window; never flagged.
            past = bool(re.search(r"\b(went|was|were|had been|been|finished|ended|qualified at|entered at|started)\s*$", pre, re.I))
            mlb_like = cand and all(g["lg"] in ("mlb", "nhl") for g in cand) and max(x, y) > 30
            if mlb_like:
                is_score, is_record = False, True
            if is_record or not is_score:
                r = record_for(sent, para, m.start(), x, y, games)
                if r and (r[0] == "OK" or is_record):
                    if r[0] != "OK" and (past or not REC_NOW.search(pre)):
                        r = ("UNCHECKED", "not stated as a current record: " + r[1])
                    if r[0] != "OK" and x + y >= 40:
                        r = ("UNCHECKED", r[1] + "; a season record, check it against the standings")
                    results.append((r[0], f"{x}-{y}", quote, r[1]))
                    continue
                if not is_score:
                    why = "season record; check against standings" if x + y >= 40 else \
                          ("no score or record word beside it" if cand else "no game in the window names both teams")
                    results.append(("UNCHECKED", f"{x}-{y}", quote, why))
                    continue
            if not cand:
                results.append(("UNCHECKED", f"{x}-{y}", quote, "no game in the window names both teams"))
                continue
            verdicts = []
            for g in cand:
                v = check_pair(g, x, y, moment(sent, m.start(), m.end(), g["lg"]), sent,
                               direction(sent, m.start(), g, prev_start))
                verdicts.append((v, g))
            when = when0
            if when:
                # The piece says which day; only that day's game counts.
                dated = [vg for vg in verdicts if vg[1]["date"] == when]
                other_ok = [vg for vg in verdicts if vg[1]["date"] != when and vg[0][0] == "OK"]
                if dated and dated[0][0][0] == "OK":
                    verdicts = dated
                elif other_ok:
                    g_ok = other_ok[0][1]
                    extra = f"; on {when:%b %-d} it was {dated[0][0][1]}" if dated else ""
                    results.append(("WRONG", f"{x}-{y}", quote,
                                    f"that score is the {g_ok['date']:%b %-d} game, not {when:%b %-d}{extra}"))
                    continue
                elif dated:
                    v, g = dated[0]
                    lgs_seen.setdefault(g["id"], g)
                    results.append((v[0], f"{x}-{y}", quote, f"{g['name']}, {g['date']}: {v[1]}"))
                    continue
            ok = [vg for vg in verdicts if vg[0][0] == "OK"]
            v, g = (ok or verdicts)[0]
            if v[0] != "OK" and not moment(sent, m.start(), m.end(), g["lg"]):
                st = series_tally(cand, games, x, y)
                if st:
                    results.append((st[0], f"{x}-{y}", quote, st[1]))
                    continue
                ids = {t["id"] for t in g["teams"]}
                meets = sum(1 for h in games if h["lg"] == g["lg"] and {t["id"] for t in h["teams"]} == ids)
                if meets >= 2 and max(x, y) <= 4 and g["lg"] in ("mlb", "nhl", "cbb", "wnba"):
                    results.append(("UNCHECKED", f"{x}-{y}", quote, "looks like a series tally; the series began before the window"))
                    continue
            named_here = any(len(mentioned(sent, [c]).get(c["id"], ())) == 2 for c in cand)
            if v[0] == "WRONG" and not named_here and not moment(sent, m.start(), m.end(), g["lg"]):
                # Only one team named in this sentence: we may have the wrong game.
                # Try every game of a team named here before saying anything.
                own = [h for h in games if h["id"] in hits]
                if any(sorted((h["teams"][0]["score"], h["teams"][1]["score"])) == sorted((x, y)) for h in own):
                    results.append(("OK", f"{x}-{y}", quote, "final of a game by a team named here"))
                else:
                    results.append(("CHECK", f"{x}-{y}", quote, f"no game in the window by a team named here ended {x}-{y}; "
                                    f"nearest guess {g['name']} ({v[1]})"))
                continue
            lgs_seen.setdefault(g["id"], g)
            results.append((v[0], f"{x}-{y}", quote, f"{g['name']}, {g['date']}: {v[1]}"))
    return results


def cross_check(gs):
    out = []
    for g in gs:
        a, b = g["teams"]
        src = second_source(g)
        if src is None:
            out.append(("OK*", g, "single source (no second feed for this league yet)"))
            continue
        name, s1, s2, l1, l2 = src
        if s1 is None:
            out.append(("OK*", g, f"second feed unavailable: {name}"))
            continue
        if (s1, s2) != (a["score"], b["score"]):
            out.append(("DISAGREE", g, f"ESPN {a['score']}-{b['score']}, {name} {s1}-{s2}"))
            continue
        reg = 9 if g["lg"] == "mlb" else 3 if g["lg"] == "nhl" else 2 if g["lg"] == "cbb" else 4
        n1, n2 = min(reg, len(l1 or []), len(a["lines"])), min(reg, len(l2 or []), len(b["lines"]))
        if l1 and l2 and a["lines"] and (list(l1[:n1]) != a["lines"][:n1] or list(l2[:n2]) != b["lines"][:n2]
                                         or sum(l1) != sum(a["lines"]) or sum(l2) != sum(b["lines"])):
            out.append(("DISAGREE", g, f"line scores differ: ESPN {a['lines']}/{b['lines']}, {name} {l1}/{l2}"))
            continue
        out.append(("OK", g, f"ESPN and {name} agree" + (" (line score too)" if l1 else " (final)")))
    return out


# ---------------------------------------------------------------- AI box
AIPROMPT = """List every claim in this article about a game's score, a lead, a margin,
or a team's win-loss record. Include claims written in words ("led by six at the half").
Reply with JSON: {"claims": [{"quote": exact words copied from the article (under 25 words),
"teams": [team names as written], "numbers": [the numbers in the claim, as integers],
"kind": "score" | "margin" | "record", "moment": "final" | "halftime" | "quarter N" | "period N" | "inning N" | "during" }]}
Copy quotes exactly. Do not add claims that are not in the article.

ARTICLE:
"""


def aibox_claims(path, model="gpt-oss:20b"):
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    from cold_read import article_text
    text = article_text(path)
    payload = {"model": model, "stream": False, "format": "json",
               "options": {"temperature": 0.1, "num_ctx": 16384},
               "messages": [{"role": "user", "content": AIPROMPT + text}]}
    if model.startswith("gpt-oss"):
        payload["think"] = "low"
    req = urllib.request.Request(f"{AIBOX}/api/chat", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        out = json.loads(json.load(r)["message"]["content"])
    flat = re.sub(r"\s+", " ", text)
    return [c for c in out.get("claims", []) if c.get("quote") and re.sub(r"\s+", " ", c["quote"]) in flat], text


def check_margins(claims, games):
    """Word-form claims the regex cannot see: 'led by six at the half'."""
    res = []
    for c in claims:
        q = c["quote"]
        if SCORE.search(q) or c.get("kind") != "margin":
            continue
        nums = c.get("numbers") or []
        m = re.search(r"\bby (\d+|" + "|".join(NUMWORD) + r")\b", q, re.I)
        if not m and not nums:
            continue
        n = int(m.group(1)) if m and m.group(1).isdigit() else (NUMWORD.get(m.group(1).lower()) if m else nums[0])
        hits = mentioned(" ".join(c.get("teams", [])) + " " + q, games)
        cand = [g for g in games if len(hits.get(g["id"], ())) >= 1]
        if not cand:
            res.append(("UNCHECKED", f"by {n}", q, "AI box claim; no game found"))
            continue
        g = cand[0]
        mom = moment(q, 0, len(q), g["lg"])
        per = period_states(g)
        if mom:
            k = LEAGUES[g["lg"]][2] if mom == "H" else mom[1]
            if k in per:
                d = abs(per[k][0] - per[k][1])
                res.append(("OK" if d == n else "WRONG", f"by {n}", q, f"{g['name']}: margin then was {d} ({per[k][0]}-{per[k][1]})"))
                continue
        a, b = g["teams"]
        d = abs(a["score"] - b["score"])
        res.append(("OK" if d == n else "UNCHECKED", f"by {n}", q, f"{g['name']}: final margin {d}"))
    return res


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Check every score in a piece against two feeds.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--date", help="last day of games to check (default: the day before the piece's datebar date)")
    ap.add_argument("--days", type=int, default=10, help="window length in days (default 10)")
    ap.add_argument("--leagues", default=",".join(LEAGUES))
    ap.add_argument("--aibox", action="store_true", help="also let the AI box point at claims written in words")
    ap.add_argument("--quiet", action="store_true", help="hide OK and UNCHECKED lines")
    a = ap.parse_args()
    bad_total = 0
    day_cache = {}
    for f in a.files:
        # A piece is written before its own date's games are played (the Sunday
        # Edition goes out at dawn), so the window ends the day before.
        end = dt.date.fromisoformat(a.date) if a.date else piece_date(f) - dt.timedelta(days=1)
        days = [end - dt.timedelta(days=i) for i in range(a.days + 1)]
        games = []
        for lg in a.leagues.split(","):
            for d in days:
                if (lg, d) not in day_cache:
                    day_cache[(lg, d)] = espn_day(lg, d)
                games += day_cache[(lg, d)]
        seen = {}
        res = verify(units(f), games, seen, end)
        if a.aibox:
            try:
                claims, _ = aibox_claims(f)
                res += check_margins(claims, games)
                res.append(("NOTE", "", "", f"AI box pointed at {len(claims)} claim(s); feeds settled them"))
            except Exception as ex:
                res.append(("NOTE", "", "", f"AI box unreachable ({str(ex)[:60]}); feed check above still stands"))
        xc = cross_check(list(seen.values()))
        bad = [r for r in res if r[0] in ("WRONG", "RECORD?")] + [x for x in xc if x[0] == "DISAGREE"]
        bad_total += len(bad)
        verdict = "FAIL" if bad else "PASS"
        print("=" * 72)
        print(f"{os.path.basename(f)}   [{verdict}]   window {days[-1]} to {end}, {len(games)} games in feeds")
        order = {"WRONG": 0, "RECORD?": 1, "CHECK": 2, "OK": 3, "UNCHECKED": 4, "NOTE": 5}
        for v, num, quote, why in sorted(res, key=lambda r: order.get(r[0], 9)):
            if a.quiet and v in ("OK", "UNCHECKED", "NOTE"):
                continue
            print(f"  {v:<9} {num:<7} {why}")
            if quote and v != "OK":
                print(f"            “…{quote}…”")
        if xc:
            print("  second feed:")
            for v, g, why in xc:
                if a.quiet and v != "DISAGREE":
                    continue
                print(f"    {v:<9} {g['name']} ({g['date']}): {why}")
        n_ok = sum(r[0] == "OK" for r in res)
        n_un = sum(r[0] == "UNCHECKED" for r in res)
        n_ck = sum(r[0] == "CHECK" for r in res)
        print(f"  {n_ok} verified, {len(bad)} problem(s), {n_ck} to look at, {n_un} not checkable from the feeds")
    sys.exit(1 if bad_total else 0)


if __name__ == "__main__":
    import urllib.parse
    main()
