#!/usr/bin/env python3
"""Catch a ranking claim that the feed cannot support. Run before any Sunday Edition.

    python3 scripts/check_poll_claims.py published/sunday-023.html
    python3 scripts/check_poll_claims.py --polls        # what actually exists today

WHY THIS EXISTS. On 6 September 2026 a Sunday Edition led with "South Carolina
went from unranked to No. 10 in the AP poll." No such poll existed. Week one ran
through Labor Day, so the first in-season AP poll did not appear until the
Tuesday, and when it did South Carolina was not in it. The issue had already
gone to the list.

The failure was not a misremembered number. The edition was assembled at 4:17am
and asked a web search what the new poll said, and a search summariser will
answer that question whether or not the poll has happened -- reconstructing a
plausible ranking from a previous season. Everything around it was true: the
57-0 score, the opponent, our own 33rd-place ranking. A single fabricated link
inside a chain of verified facts is the hardest kind to see.

So this does one narrow thing well: it finds every sentence in a draft that
asserts a poll position, and checks that position against the CollegeFootballData
rankings feed. A claim about a poll that does not exist is reported as
UNSUPPORTED rather than merely unverified, because that is the more useful word.

It cannot check claims it cannot parse. It is a net under the specific mistake
we made, not a general fact-checker, and the rule in CLAUDE.md is what actually
governs: nothing grades a forecast unless it traces to a primary feed.
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import urllib.request

API = "https://api.collegefootballdata.com"
# "No. 10", "ranked 10th", "to No. 10 in the AP poll", "jumped to 10th"
CLAIM = re.compile(
    r"(?P<team>[A-Z][A-Za-z&.\' ]{2,24}?)\s+"
    r"(?:went from unranked to|jumped to|rose to|climbed to|moved to|is now|are now|sits at|"
    r"is ranked|are ranked|entered at)\s+"
    r"(?:No\.\s*)?(?P<rank>\d{1,2})(?:st|nd|rd|th)?\b", re.I)
# Deliberately narrow. A bare "ranked 33rd" is often OUR OWN metric -- issue #160
# ranked two clubs 33rd and 35th on returning production -- and flagging that is
# noise. Only a named poll counts as a poll claim.
POLLWORD = re.compile(r"\b(AP(?:\s+Top\s*25)?|Coaches\s+Poll|Top\s*25|the\s+poll|"
                      r"in\s+the\s+polls?|CFP\s+rankings?)\b")


def get(url):
    key = os.environ.get("CFBD_KEY")
    if not key:
        raise SystemExit("CFBD_KEY not set; cannot verify against a primary feed")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    return json.load(urllib.request.urlopen(req, timeout=45))


def polls(year):
    """Every poll the feed actually has, newest week first."""
    out = []
    for block in get(f"{API}/rankings?year={year}&seasonType=regular"):
        for p in block.get("polls", []):
            out.append(dict(week=block.get("week"), poll=p.get("poll"),
                            ranks={q["school"]: q["rank"] for q in p.get("ranks", [])}))
    out.sort(key=lambda p: -(p["week"] or 0))
    return out


def text_of(path):
    raw = open(path, encoding="utf-8").read()
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--year", type=int, default=datetime.date.today().year)
    ap.add_argument("--polls", action="store_true")
    a = ap.parse_args()

    ps = polls(a.year)
    if a.polls or not a.paths:
        print(f"\n  polls the feed has for {a.year}:")
        for p in ps:
            print(f"    week {p['week']:<3} {p['poll']:<32}{len(p['ranks'])} clubs")
        top = next((p for p in ps if p["poll"] == "AP Top 25"), None)
        if top:
            print(f"\n  newest AP Top 25 is week {top['week']}. Top 5: "
                  + ", ".join(f"{r}.{s}" for s, r in sorted(top['ranks'].items(), key=lambda kv: kv[1])[:5]))
        if not a.paths:
            return 0

    bad = 0
    for path in a.paths:
        txt = text_of(path)
        print(f"\n  {path.split('/')[-1]}")
        found = 0
        for m in CLAIM.finditer(txt):
            window = txt[max(0, m.start() - 120): m.end() + 120]
            if not POLLWORD.search(window):
                continue                      # not a poll claim; leave it alone
            team, rank = m.group("team").strip(), int(m.group("rank"))
            found += 1
            hits = [p for p in ps if p["ranks"].get(team) == rank]
            if hits:
                print(f"    OK           {team} at No. {rank}  ({hits[0]['poll']}, week {hits[0]['week']})")
                continue
            listed = [(p["poll"], p["week"], p["ranks"][team]) for p in ps if team in p["ranks"]]
            if listed:
                pl, wk, actual = listed[0]
                print(f"    WRONG        {team} claimed No. {rank}; {pl} week {wk} has them No. {actual}")
            else:
                anypoll = any(team in p["ranks"] for p in ps)
                why = "unranked in every poll the feed has" if not anypoll else "not in that poll"
                print(f"    UNSUPPORTED  {team} claimed No. {rank} -- {why}")
            bad += 1
        if not found:
            print("    no poll-position claims detected")
    if bad:
        print(f"\n  {bad} claim(s) the feed does not support. Do not publish until each is "
              f"traced to a primary source or removed.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
