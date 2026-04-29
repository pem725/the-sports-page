#!/usr/bin/env python3
"""
Generate feed.xml at the repo root from every file in published/.

Buttondown polls this feed and emails subscribers when new items appear.
The feed lives at https://pem725.github.io/the-sports-page/feed.xml.

Idempotent: running multiple times overwrites the same file with the same
content. Safe to call from autopublish.py after every publish.
"""
import datetime
import html
import os
import re
import sys
from email.utils import formatdate

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLISHED = os.path.join(REPO, "published")
OUT = os.path.join(REPO, "feed.xml")
SITE = "https://pem725.github.io/the-sports-page"

# Issue # → publication date map, derived from index.html so pubDates match
# what readers see in the archive
INDEX_HTML = os.path.join(REPO, "index.html")


def clean_text(s):
    """Strip HTML, resolve entities, collapse whitespace."""
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    return " ".join(s.split())


def extract_meta(filepath):
    """Return (title, deck, issue_num) from a published HTML file."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    hed_m = re.search(r'<h1\s+class="hed">(.*?)</h1>', content, re.DOTALL)
    deck_m = re.search(r'<div\s+class="deck">\s*(.*?)\s*</div>', content, re.DOTALL)
    title = clean_text(hed_m.group(1)) if hed_m else os.path.basename(filepath)
    deck = clean_text(deck_m.group(1)) if deck_m else ""
    return title, deck


def get_index_dates():
    """Map filename -> (issue_num, ISO date) by parsing index.html entries."""
    if not os.path.isfile(INDEX_HTML):
        return {}
    with open(INDEX_HTML, encoding="utf-8") as f:
        idx = f.read()
    # Each issue block: <div class="issue-num">NN</div> ... <div class="issue-date">Month DD, YYYY</div> ... href="published/FILE"
    pattern = (
        r'<div class="issue-num">(\d+)</div>.*?'
        r'<div class="issue-date">([^<]+)</div>.*?'
        r'href="published/([^"]+)"'
    )
    result = {}
    for m in re.finditer(pattern, idx, re.DOTALL):
        num, date_str, filename = m.group(1), m.group(2).strip(), m.group(3)
        try:
            dt = datetime.datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            try:
                dt = datetime.datetime.strptime(date_str, "%B %-d, %Y")
            except ValueError:
                continue
        result[filename] = (int(num), dt)
    return result


def main():
    if not os.path.isdir(PUBLISHED):
        print(f"ERROR: {PUBLISHED} not found", file=sys.stderr)
        sys.exit(1)

    dates = get_index_dates()
    items = []
    files = sorted(f for f in os.listdir(PUBLISHED) if f.endswith(".html"))
    for fname in files:
        if fname not in dates:
            continue  # not in index.html → skip
        num, dt = dates[fname]
        title, deck = extract_meta(os.path.join(PUBLISHED, fname))
        items.append({
            "num": num,
            "title": f"#{num}: {title}",
            "deck": deck,
            "link": f"{SITE}/published/{fname}",
            "guid": f"{SITE}/published/{fname}",
            "pubDate": formatdate(dt.timestamp(), usegmt=True),
        })

    items.sort(key=lambda x: -x["num"])  # newest first

    rss_items = "\n".join(
        f"""    <item>
      <title>{html.escape(it['title'])}</title>
      <link>{html.escape(it['link'])}</link>
      <description>{html.escape(it['deck'])}</description>
      <pubDate>{it['pubDate']}</pubDate>
      <guid isPermaLink="true">{html.escape(it['guid'])}</guid>
    </item>"""
        for it in items
    )

    now = formatdate(datetime.datetime.now().timestamp(), usegmt=True)
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>The Sports Page</title>
    <link>{SITE}/</link>
    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml" />
    <description>One strange sports statistic per issue, explained. Five pieces a week, with a Sunday Edition that scores our predictions against reality.</description>
    <language>en-us</language>
    <lastBuildDate>{now}</lastBuildDate>
{rss_items}
  </channel>
</rss>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(feed)
    print(f"Wrote {OUT} with {len(items)} items")


if __name__ == "__main__":
    main()
