#!/usr/bin/env python3
"""
Generate feed.xml at the repo root from every file in published/.

Buttondown polls this feed and emails subscribers when new items appear.
The feed lives at https://thesportspage.net/feed.xml.

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

# Inline the design-system CSS into the email body so layout survives clients
# that strip the page's <head><style>. Graceful fallback: if anything goes
# wrong importing it, emails still send (just unstyled) -- never crash the bot.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from email_inline import inline_for_email
except Exception:
    def inline_for_email(b):  # noqa: E704
        return b
SITE = "https://thesportspage.net/"

# Issue # → publication date map, derived from index.html so pubDates match
# what readers see in the archive
INDEX_HTML = os.path.join(REPO, "index.html")


def clean_text(s):
    """Strip HTML, resolve entities, collapse whitespace."""
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    return " ".join(s.split())


def extract_meta(filepath):
    """Return (title, deck, full_html_body) from a published HTML file.

    full_html_body is the article's <main> contents (paragraphs, charts,
    tables, headings, pull quotes — everything a reader expects in the
    issue), with relative URLs absolutized and the email-irrelevant
    bits (nav, footer, share section, skip-link) stripped out.
    """
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # Headline and deck — accept either <h1 class="hed"> (older) or
    # <h2 class="hed"> (newer Python-templated issues).
    hed_m = re.search(r'<h[12]\s+class="hed"[^>]*>(.*?)</h[12]>', content, re.DOTALL)
    # Deck can be either <div class="deck"> or <p class="deck">
    deck_m = re.search(r'<(?:div|p)\s+class="deck"[^>]*>\s*(.*?)\s*</(?:div|p)>',
                       content, re.DOTALL)
    title = clean_text(hed_m.group(1)) if hed_m else os.path.basename(filepath)
    deck = clean_text(deck_m.group(1)) if deck_m else ""

    # Article body — prefer <main> if present (newer issues), fall back
    # to <div id="main-content" class="paper"> or <div class="paper"> (older).
    body_m = (
        re.search(r'<main[^>]*>(.*?)</main>', content, re.DOTALL)
        or re.search(r'<div[^>]*\bid="main-content"[^>]*>(.*?)</div>\s*(?:<!-- SHARE)',
                     content, re.DOTALL)
        or re.search(r'<div[^>]*\bclass="paper"[^>]*>(.*?)</div>\s*(?:<!-- SHARE|</body>)',
                     content, re.DOTALL)
    )
    body = body_m.group(1) if body_m else f"<h2>{title}</h2><p>{deck}</p>"

    # Absolutize relative URLs so images / links work in an email context.
    body = re.sub(r'src="\.\./assets/', f'src="{SITE}assets/', body)
    body = re.sub(r'href="\.\./assets/', f'href="{SITE}assets/', body)
    body = re.sub(r'href="\.\./tools/', f'href="{SITE}tools/', body)
    body = re.sub(r'href="\.\./published/', f'href="{SITE}published/', body)
    body = re.sub(r'href="\.\./concepts/', f'href="{SITE}concepts/', body)
    body = re.sub(r'href="\.\./index\.html"', f'href="{SITE}"', body)
    # Site-root references that survived earlier passes
    body = body.replace('href="../', f'href="{SITE}')
    body = body.replace('src="../', f'src="{SITE}')

    # Inline the design-system styles so the layout renders in email.
    body = inline_for_email(body)

    return title, deck, body


def hero_image_html(fname, title):
    """Prepend the issue's OG card as a clickable hero image in the email body.

    OG cards live at /assets/og/<slug>.png with the same slug as the HTML
    filename. They're 1200×630 and designed as a visual hook for social
    previews — perfect doubling as an email lede.
    """
    slug = fname[:-5]  # strip ".html"
    og_path = os.path.join(REPO, "assets", "og", f"{slug}.png")
    if not os.path.isfile(og_path):
        return ""
    return (
        f'<p style="text-align:center;margin:0 0 32px;">'
        f'<a href="{SITE}published/{fname}" style="display:inline-block;">'
        f'<img src="{SITE}assets/og/{slug}.png" '
        f'alt="{html.escape(title)}" '
        f'style="max-width:100%;height:auto;display:block;margin:0 auto;'
        f'border:1px solid #c9962a;">'
        f'</a></p>'
    )


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
        title, deck, body = extract_meta(os.path.join(PUBLISHED, fname))
        body = hero_image_html(fname, title) + body
        items.append({
            "num": num,
            "title": f"#{num}: {title}",
            "deck": deck,
            "body": body,
            "link": f"{SITE}published/{fname}",
            "guid": f"{SITE}published/{fname}",
            "pubDate": formatdate(dt.timestamp(), usegmt=True),
        })

    items.sort(key=lambda x: -x["num"])  # newest first

    # CDATA-wrap the body HTML so XML doesn't choke on inline HTML/SVG.
    # Need to escape any literal "]]>" in the body to avoid breaking CDATA.
    def cdata(body):
        body = body.replace("]]>", "]]]]><![CDATA[>")
        return f"<![CDATA[{body}]]>"

    rss_items = "\n".join(
        f"""    <item>
      <title>{html.escape(it['title'])}</title>
      <link>{html.escape(it['link'])}</link>
      <description>{html.escape(it['deck'])}</description>
      <content:encoded>{cdata(it['body'])}</content:encoded>
      <pubDate>{it['pubDate']}</pubDate>
      <guid isPermaLink="true">{html.escape(it['guid'])}</guid>
    </item>"""
        for it in items
    )

    now = formatdate(datetime.datetime.now().timestamp(), usegmt=True)
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>The Sports Page</title>
    <link>{SITE}</link>
    <atom:link href="{SITE}feed.xml" rel="self" type="application/rss+xml" />
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
