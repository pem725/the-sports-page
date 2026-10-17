#!/usr/bin/env python3
"""
Fetch last week's readership from GoatCounter and render the top-5 issues
as an HTML block in broadsheet style, optionally injecting it into a
Sunday Edition draft file by replacing a <!-- READERSHIP_BLOCK --> marker.

Usage:
  # Print the HTML block for last week (Sun..Sat) to stdout
  GOATCOUNTER_TOKEN=... python3 scripts/fetch_readership.py

  # Inject into a Sunday file (replaces <!-- READERSHIP_BLOCK --> marker)
  GOATCOUNTER_TOKEN=... python3 scripts/fetch_readership.py \\
      --inject queue/sunday-003.html

  # Custom date range (defaults to most recent Sunday..Saturday)
  GOATCOUNTER_TOKEN=... python3 scripts/fetch_readership.py \\
      --start 2026-04-14 --end 2026-04-20

  # What the daily GitHub run does: the seven days ending yesterday, cached
  GOATCOUNTER_TOKEN=... python3 scripts/fetch_readership.py --last7 --write

WHY THE CACHE. From late August every Sunday Edition printed "data pending".
The Sunday routine runs in a cloud sandbox that has no secrets store, so its
prompt carried the token inline -- and the sandbox's safety check refused to run
a command with a credential pasted into it, every week. The fix is to fetch where
the secret legitimately lives: the daily GitHub Actions run writes the block to
data/readership-block.html, and `--inject` with no token uses that file. On
Sunday the newest cache is Saturday's: the seven days ending Friday.
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.request
import urllib.error
import urllib.parse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://thesportspage.goatcounter.com/api/v0"
MARKER = "<!-- READERSHIP_BLOCK -->"
MAX_ISSUES = 5
CACHE = os.path.join(REPO, "data", "readership-block.html")
STAMP = re.compile(r"<!-- readership-cache (\d{4}-\d{2}-\d{2}) -->")
CACHE_MAX_AGE_DAYS = 8


def default_week():
    """Return (start, end) for most recent completed Sunday..Saturday."""
    today = datetime.date.today()
    # Python: Monday=0 ... Sunday=6
    # We want the Sunday before this past Saturday.
    # If today is Sunday, "last week" is the week just ended (today - 7 to today - 1)
    days_since_sunday = (today.weekday() + 1) % 7  # 0 if today is Sunday
    last_saturday = today - datetime.timedelta(days=days_since_sunday + 1) if days_since_sunday == 0 \
                    else today - datetime.timedelta(days=days_since_sunday + 1)
    # Simpler: last completed Sat = today - ((today.weekday()+2) % 7 or 7)? Too cute.
    # Just compute last Sun and last Sat cleanly:
    # last_sat = most recent Sat on or before (today - 1)
    yest = today - datetime.timedelta(days=1)
    last_sat = yest - datetime.timedelta(days=(yest.weekday() - 5) % 7)
    last_sun = last_sat - datetime.timedelta(days=6)
    return last_sun, last_sat


def fetch_hits(token, start, end):
    # limit=200: a busy week (a campaign, a post that travels) can easily touch
    # more than 50 distinct paths, and the API truncates silently rather than
    # erroring — the dropped rows would just look like pages nobody visited.
    url = (f"{API}/stats/hits?"
           f"start={start.isoformat()}&end={end.isoformat()}&limit=200")
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def extract_headline(filepath):
    """Return plain-text headline from <h1 class="hed">...</h1> or filename."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return os.path.basename(filepath).replace(".html", "")
    m = re.search(r'<h1\s+class="hed">(.*?)</h1>', content, re.DOTALL)
    if not m:
        return os.path.basename(filepath).replace(".html", "")
    raw = m.group(1)
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '', raw)
    # Resolve common entities
    text = (text.replace("&mdash;", "—").replace("&ndash;", "–")
                .replace("&rsquo;", "'").replace("&lsquo;", "'")
                .replace("&amp;", "&"))
    return " ".join(text.split())


def normalize_path(path):
    """Collapse the legacy GitHub Pages prefix onto the custom-domain path.

    The site lived at pem725.github.io/the-sports-page/ before moving to
    thesportspage.net, so the analytics history holds the same issue under two
    paths. The old filter required a leading "/published/", which meant every
    legacy hit was DISCARDED rather than merely split off — and at these volumes
    a three-view difference silently reorders the entire top five.

    ALSO FOLDS /index.html INTO /. Added 2026-09-27: the homepage was being
    counted four ways -- /, /index.html, /the-sports-page and
    /the-sports-page/index.html -- and across six months that split 243 views of
    one page into four entries. The tracking snippet now normalizes before
    sending, so this only has to repair the history.
    """
    if path.startswith("/the-sports-page/"):
        path = path[len("/the-sports-page"):]
    elif path == "/the-sports-page":
        path = "/"
    if path.endswith("/index.html"):
        path = path[:-len("index.html")]
    return path or "/"


def build_block(hits, start, end):
    """Render the top-N issues as an HTML block matching broadsheet style."""
    # Merge both path namespaces, then filter to /published/*.html
    totals = {}
    for h in hits:
        path = normalize_path(h.get("path", ""))
        if not path.startswith("/published/") or not path.endswith(".html"):
            continue
        totals[path] = totals.get(path, 0) + h.get("count", 0)
    issues = sorted(totals.items(), key=lambda x: -x[1])[:MAX_ISSUES]

    if not issues:
        return (
            '<h2 class="sh">What Readers Read &middot; '
            f'{start.strftime("%b %-d")}&ndash;{end.strftime("%b %-d")}</h2>\n'
            '<p><em>Readership data pending &mdash; the analytics pipeline '
            'installed recently, and last week&rsquo;s counts were not '
            'captured. This section will populate starting with the first '
            'full week of data.</em></p>\n'
        )

    rows = []
    for rank, (path, count) in enumerate(issues, 1):
        filepath = os.path.join(REPO, path.lstrip("/"))
        hed = extract_headline(filepath)
        # Truncate long headlines for table width
        display_hed = hed if len(hed) < 75 else hed[:72] + "..."
        rows.append(
            f'  <tr><td class="mono">#{rank}</td>'
            f'<td><a href="https://thesportspage.net{path}" '
            f'target="_blank" rel="noopener">{display_hed}</a></td>'
            f'<td class="mono">{count}</td></tr>'
        )
    rows_html = "\n".join(rows)

    return (
        f'<h2 class="sh">What Readers Read &middot; '
        f'{start.strftime("%B %-d")} &ndash; {end.strftime("%B %-d")}</h2>\n'
        f'<table class="rec">\n'
        f'  <thead><tr><th>Rank</th><th>Issue</th><th>Reads</th></tr></thead>\n'
        f'  <tbody>\n{rows_html}\n  </tbody>\n'
        f'</table>\n'
        f'<p style="font-size:.82rem;color:var(--muted);margin-top:-.4rem">'
        f'<em>Counts are unique pageviews per GoatCounter, with author visits '
        f'excluded. Pulled {datetime.date.today().isoformat()}.</em></p>\n'
    )


def inject(path, block):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    if MARKER not in content:
        print(f"ERROR: marker {MARKER} not found in {path}", file=sys.stderr)
        sys.exit(2)
    new = content.replace(MARKER, block, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    print(f"Injected readership block into {path}", file=sys.stderr)


def read_cache():
    """The cached block if it is recent enough to call 'last week', else None."""
    try:
        text = open(CACHE, encoding="utf-8").read()
    except OSError:
        return None
    m = STAMP.search(text)
    if not m:
        return None
    age = (datetime.date.today() - datetime.date.fromisoformat(m.group(1))).days
    return text if age <= CACHE_MAX_AGE_DAYS else None


def emit(block, args):
    if args.inject:
        inject(args.inject, block)
    else:
        print(block)


def fallback(args, start, end, why):
    """No live data: use a recent cache, else the honest 'pending' block."""
    cached = read_cache()
    if cached:
        print(f"{why}; using cached block from {CACHE}", file=sys.stderr)
        emit(cached, args)
    else:
        print(f"{why}; no recent cache, writing the pending block", file=sys.stderr)
        emit(build_block([], start, end), args)
    sys.exit(0)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", help="YYYY-MM-DD (default: last Sunday)")
    p.add_argument("--end", help="YYYY-MM-DD (default: last Saturday)")
    p.add_argument("--last7", action="store_true", help="the seven days ending yesterday")
    p.add_argument("--inject", help="Path to Sunday HTML; replace marker with block")
    p.add_argument("--write", action="store_true",
                   help=f"save the block to {os.path.relpath(CACHE, REPO)} (only if it has data)")
    args = p.parse_args()

    if args.start and args.end:
        start = datetime.date.fromisoformat(args.start)
        end = datetime.date.fromisoformat(args.end)
    elif args.last7:
        end = datetime.date.today() - datetime.timedelta(days=1)
        start = end - datetime.timedelta(days=6)
    else:
        start, end = default_week()

    token = os.environ.get("GOATCOUNTER_TOKEN")
    if not token:
        if args.write:
            print("ERROR: --write needs GOATCOUNTER_TOKEN", file=sys.stderr)
            sys.exit(1)
        fallback(args, start, end, "GOATCOUNTER_TOKEN not set")

    print(f"Fetching readership {start} to {end}...", file=sys.stderr)
    try:
        data = fetch_hits(token, start, end)
    except (urllib.error.URLError, TimeoutError) as e:
        fallback(args, start, end, f"API error: {e}")

    hits = data.get("hits", [])
    print(f"  API returned {len(hits)} paths", file=sys.stderr)
    block = build_block(hits, start, end)

    if args.write:
        if "Readership data pending" in block:
            print("  no issue pages in the window; cache left as it was", file=sys.stderr)
        else:
            with open(CACHE, "w", encoding="utf-8") as f:
                f.write(f"<!-- readership-cache {datetime.date.today().isoformat()} -->\n{block}")
            print(f"  wrote {CACHE}", file=sys.stderr)
        return
    emit(block, args)


if __name__ == "__main__":
    main()
