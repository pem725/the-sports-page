#!/usr/bin/env python3
"""Keep about.html's live numbers live.

    python3 scripts/refresh_about.py

about.html is a hand-written narrative page, and hand-written pages rot. On
2026-08-30 it still cited Issues #5, #7 and #8 as recent while the archive stood
at 155, and mentioned none of the tools built since. Rather than rewrite the
prose on every change, the few facts that actually move are fenced between
ABOUT_STATE markers and regenerated from the repo itself.

Runs from the autopublish workflow, so the page cannot drift again.
"""
import datetime, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(REPO, "about.html")
START, END = "<!-- ABOUT_STATE:start -->", "<!-- ABOUT_STATE:end -->"


def read(p):
    return open(os.path.join(REPO, p), encoding="utf-8").read()


def main():
    t = open(PAGE, encoding="utf-8").read()
    if START not in t or END not in t:
        print("  markers missing; nothing done"); return 0
    issues = read("index.html").count('class="issue-num"')
    concepts = len([f for f in os.listdir(os.path.join(REPO, "concepts"))
                    if f.endswith(".html") and f != "index.html"])
    queued = len([l for l in read("QUEUE_ORDER.txt").splitlines() if l.strip()])
    sundays = len([f for f in os.listdir(os.path.join(REPO, "published")) if f.startswith("sunday-")])
    try:
        led = json.loads(read("data/picks-ledger.json"))
        picks = sum(len(w["picks"]) for w in led["weeks"].values())
    except Exception:
        picks = 0
    block = f'''{START}
  <div class="state">
    <div class="state-l">Where things stand &middot; {datetime.date.today():%-d %B %Y}</div>
    <div class="state-g">
      <div><b>{issues}</b><span>issues published</span></div>
      <div><b>{sundays}</b><span>Sunday editions</span></div>
      <div><b>{concepts}</b><span>concept primers</span></div>
      <div><b>{queued}</b><span>days queued</span></div>
      <div><b>{500-issues}</b><span>to reach 500</span></div>
    </div>
    <p>Newer than most of the page below: an <a href="https://thesportspage.net/odds.html">Odds Board</a>
       that refreshes daily with playoff probabilities for all thirty baseball clubs and season
       projections for the college football top 25; a <a href="https://thesportspage.net/newsroom.html">Newsroom</a>
       page showing how stories are chosen and scored; an
       <a href="https://thesportspage.net/ask.html">open question box</a>, since two of the last
       fifteen issues came from readers asking something they could not settle; and a
       <em>What to Watch</em> block in every issue naming the day&rsquo;s highest-leverage game and
       why. We also keep a public ledger of {picks} of our own forecasts, so the percentages we
       quote can eventually be checked against what happened.</p>
  </div>
  {END}'''
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: block, t, flags=re.S)
    for tag in ("div", "p", "h2"):
        o, c = len(re.findall(rf"<{tag}\b", new)), len(re.findall(rf"</{tag}>", new))
        assert o == c, f"<{tag}> unbalanced after refresh: {o}/{c}"
    open(PAGE, "w", encoding="utf-8").write(new)
    print(f"  about.html refreshed: {issues} issues, {concepts} primers, {queued} queued, {picks} forecasts logged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
