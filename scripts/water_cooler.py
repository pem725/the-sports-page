#!/usr/bin/env python3
"""The water-cooler ledger: which numbers does the sports press lean on?

The editor's question, 2026-10-25: in 1998 everybody counted home runs while
doubles, walks and Barry Bonds went unseen. Sports writing has fads. Which
numbers are people using to argue their points right now, and how does that
change over time?

This builds the evidence one article at a time. For each new item in a set of
sports news feeds it fetches the article, hands the text to the local AI box, and
records the numbers the piece uses -- what each counts, who it is about, the
point it supports, and which single number the piece leans on hardest. Run it
daily and the ledger becomes a time series of the press's favorite stats.

What is stored, and what is not:
  - stored: outlet, sport, date, headline, URL, and the extracted claims
  - NOT stored: the article text. It is read in memory and discarded. The ledger
    is about which statistics get used, not a copy of anyone's writing.

The model is an extractor here, never a source. A claim in the ledger means "this
article said this", not "this is true". Anything that reaches print is checked
against a primary feed like every other number in the paper.

LAN-only (see cold_read.py): runs from the workstation, never in GitHub Actions.

Usage:
  python3 scripts/water_cooler.py                 # collect new articles from all feeds
  python3 scripts/water_cooler.py --limit 10      # at most 10 new articles this run
  python3 scripts/water_cooler.py --report        # tally the ledger by stat and sport
"""
import argparse, collections, datetime as dt, email.utils, html, json, os, re, sys, time
import urllib.request

HOST = os.environ.get("AIBOX", "http://192.168.0.65:11434")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "data", "watercooler", "claims.jsonl")
UA = "Mozilla/5.0 (compatible; TheSportsPage-research/1.0; +https://thesportspage.net/)"

FEEDS = [  # (outlet, sport, url)
    ("ESPN", "MLB", "https://www.espn.com/espn/rss/mlb/news"),
    ("ESPN", "NFL", "https://www.espn.com/espn/rss/nfl/news"),
    ("ESPN", "CFB", "https://www.espn.com/espn/rss/ncf/news"),
    ("ESPN", "NHL", "https://www.espn.com/espn/rss/nhl/news"),
    ("CBS", "MLB", "https://www.cbssports.com/rss/headlines/mlb/"),
    ("CBS", "NFL", "https://www.cbssports.com/rss/headlines/nfl/"),
    ("CBS", "CFB", "https://www.cbssports.com/rss/headlines/college-football/"),
    ("CBS", "NHL", "https://www.cbssports.com/rss/headlines/nhl/"),
    ("Yahoo", "MLB", "https://sports.yahoo.com/mlb/rss/"),
    ("Yahoo", "NFL", "https://sports.yahoo.com/nfl/rss/"),
    ("Yahoo", "CFB", "https://sports.yahoo.com/college-football/rss/"),
    ("MLB Trade Rumors", "MLB", "https://www.mlbtraderumors.com/feed"),
]

# Canonical stat families, so "dingers", "homers" and "HRs" land in one bucket.
# The model may answer "other: <name>"; the report shows those so the list can grow.
COMMON = "game score, series status, drought (years since), "
FAMILIES = {
    "MLB": "home runs, RBI, batting average, hits, doubles, triples, walks, on-base percentage, slugging, OPS, "
           "stolen bases, runs scored, strikeouts (batter), ERA, wins (pitcher), saves, strikeouts (pitcher), "
           "innings pitched, WHIP, velocity, exit velocity, launch angle, WAR, contract money, payroll, "
           "team record, games back, playoff odds, streak, age, attendance, injury timeline",
    "NFL": "passing yards, passing touchdowns, interceptions, passer rating, QBR, completion percentage, "
           "QB wins, rushing yards, yards per carry, receiving yards, receptions, touchdowns, sacks, tackles, "
           "turnovers, points scored, points allowed, time of possession, third-down rate, red-zone rate, "
           "team record, point spread, playoff odds, contract money, salary cap, draft pick, age, injury timeline, streak",
    "CFB": "passing yards, rushing yards, touchdowns, points scored, points allowed, team record, AP ranking, "
           "CFP ranking, recruiting ranking, NIL money, coach salary, coach record, transfer portal, point spread, "
           "win probability, strength of schedule, attendance, streak, injury timeline",
    "NHL": "goals, assists, points, plus/minus, save percentage, goals-against average, shots, ice time, "
           "power-play rate, penalty minutes, team record, standings points, playoff odds, contract money, "
           "streak, age, injury timeline",
}

PROMPT = """You are cataloguing the NUMBERS a sports article uses. You are an extractor, not a fact-checker.
Do not judge whether numbers are true. Do not add numbers that are not in the text.

For every number in the article that describes sports performance, money, standing or odds, record it.
Skip dates, jersey numbers, ages of no consequence, and times of day.

Map each to ONE stat family from this list, or write "other: <short name>":
{families}

Reply with JSON only:
{{"claims": [{{"number": "as written", "family": "...", "about": "player or team", "role": "argument|description",
              "supports": "the point this number is used to make, in under 12 words"}}],
  "lead_family": "the stat family the article leans on hardest to make its main point, or none",
  "lead_number": "that number as written, or none",
  "main_point": "the article's main claim in under 15 words"}}
"role" is "argument" when the number is used as evidence for an opinion or prediction, "description" when it just reports what happened.

HEADLINE: {title}
ARTICLE:
{text}"""


def get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def items(feed_xml):
    for it in re.findall(r"(?s)<item\b.*?</item>", feed_xml):
        g = lambda tag: (re.search(rf"(?s)<{tag}[^>]*>(.*?)</{tag}>", it) or [None, ""])[1]
        unc = lambda x: html.unescape(re.sub(r"<!\[CDATA\[|\]\]>", "", x)).strip()
        link = unc(g("link")) or unc(g("guid"))
        if link.startswith("http"):
            yield dict(title=unc(g("title")), link=link.split("?")[0], pub=unc(g("pubDate")))


def body_text(page, cap=2500):
    page = re.sub(r"(?s)<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>", " ", page)
    paras = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in re.findall(r"(?s)<p\b[^>]*>(.*?)</p>", page)]
    paras = [p for p in paras if len(p.split()) >= 8]          # drop bylines, captions, nav crumbs
    words = " ".join(paras).split()
    return " ".join(words[:cap])


def extract(title, text, sport, model):
    prompt = PROMPT.format(families=COMMON + FAMILIES.get(sport, FAMILIES["MLB"]), title=title, text=text)
    payload = {"model": model, "stream": False, "format": "json", "think": "low",
               "options": {"temperature": 0.1, "num_ctx": 16384},
               "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(f"{HOST}/api/chat", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(json.load(r)["message"]["content"])


def iso(pub):
    try:
        return email.utils.parsedate_to_datetime(pub).date().isoformat()
    except (TypeError, ValueError):
        return dt.date.today().isoformat()


def collect(limit, model):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    seen = set()
    if os.path.exists(LEDGER):
        seen = {json.loads(l)["url"] for l in open(LEDGER) if l.strip()}
    new = 0
    for outlet, sport, url in FEEDS:
        try:
            feed = get(url)
        except OSError as e:
            print(f"  feed down: {outlet} {sport} ({e})"); continue
        for it in items(feed):
            if it["link"] in seen or new >= limit:
                continue
            seen.add(it["link"])
            try:
                text = body_text(get(it["link"]))
            except OSError as e:
                print(f"  skip (fetch): {it['link']} ({e})"); continue
            if len(text.split()) < 120:                     # video pages, paywalls, slideshows
                continue
            try:
                r = extract(it["title"], text, sport, model)
            except (OSError, ValueError, KeyError) as e:
                print(f"  skip (model): {it['title'][:60]} ({type(e).__name__})"); continue
            rec = dict(url=it["link"], outlet=outlet, sport=sport, date=iso(it["pub"]), title=it["title"],
                       words=len(text.split()), collected=dt.date.today().isoformat(), model=model,
                       claims=[c for c in r.get("claims", []) if isinstance(c, dict)], lead_family=r.get("lead_family"),
                       lead_number=r.get("lead_number"), main_point=r.get("main_point"))
            with open(LEDGER, "a") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            new += 1
            print(f"  {outlet:>5} {sport}  {len(rec['claims']):2d} numbers  lead: {rec['lead_family']}  | {it['title'][:60]}", flush=True)
            time.sleep(1)                                    # be a polite reader
    print(f"{new} new article(s) added to {os.path.relpath(LEDGER, REPO)}")


def report():
    R = [json.loads(l) for l in open(LEDGER) if l.strip()]
    junk = sum(1 for r in R for c in r["claims"] if not isinstance(c, dict))   # model returned a fragment, not a claim
    for r in R:
        r["claims"] = [c for c in r["claims"] if isinstance(c, dict)]
    print(f"{len(R)} articles, {sum(len(r['claims']) for r in R)} numbers, "
          f"{min(r['date'] for r in R)} to {max(r['date'] for r in R)}"
          + (f"; {junk} malformed claim(s) skipped" if junk else "") + "\n")
    for sport in sorted({r["sport"] for r in R}):
        S = [r for r in R if r["sport"] == sport]
        lead = collections.Counter((r.get("lead_family") or "none").lower() for r in S)
        # Count ARTICLES that argue with a family, not numbers: one betting table once
        # supplied 147 of 229 NFL "point spread" arguments by itself.
        arg = collections.Counter(f for r in S for f in {c.get("family", "?").lower() for c in r["claims"]
                                                          if c.get("role") == "argument"})
        print(f"{sport}  ({len(S)} articles)")
        print("  leaned on hardest: " + ", ".join(f"{k} {v}" for k, v in lead.most_common(8)))
        print("  argued with (articles): " + ", ".join(f"{k} {v}" for k, v in arg.most_common(8)) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--model", default="gpt-oss:20b")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.report:
        return report()
    try:
        urllib.request.urlopen(f"{HOST}/api/tags", timeout=5)
    except OSError as e:
        sys.exit(f"AI box not reachable at {HOST} ({e}). This is a LAN-only desk tool.")
    collect(a.limit, a.model)


if __name__ == "__main__":
    main()
