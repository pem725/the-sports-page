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
    url = (f"{API}/stats/hits?"
           f"start={start.isoformat()}&end={end.isoformat()}&limit=50")
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


def build_block(hits, start, end):
    """Render the top-N issues as an HTML block matching broadsheet style."""
    # Filter to /published/*.html paths
    issues = []
    for h in hits:
        path = h.get("path", "")
        count = h.get("count", 0)
        if not path.startswith("/published/") or not path.endswith(".html"):
            continue
        issues.append((path, count))
    issues = sorted(issues, key=lambda x: -x[1])[:MAX_ISSUES]

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
            f'<td><a href="..{path}">{display_hed}</a></td>'
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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", help="YYYY-MM-DD (default: last Sunday)")
    p.add_argument("--end", help="YYYY-MM-DD (default: last Saturday)")
    p.add_argument("--inject", help="Path to Sunday HTML; replace marker with block")
    args = p.parse_args()

    token = os.environ.get("GOATCOUNTER_TOKEN")
    if not token:
        print("ERROR: set GOATCOUNTER_TOKEN env var", file=sys.stderr)
        sys.exit(1)

    if args.start and args.end:
        start = datetime.date.fromisoformat(args.start)
        end = datetime.date.fromisoformat(args.end)
    else:
        start, end = default_week()

    print(f"Fetching readership {start} to {end}...", file=sys.stderr)

    try:
        data = fetch_hits(token, start, end)
    except urllib.error.HTTPError as e:
        print(f"API error: HTTP {e.code} — {e.reason}", file=sys.stderr)
        # Graceful fallback: emit the "pending" block
        block = build_block([], start, end)
        if args.inject:
            inject(args.inject, block)
        else:
            print(block)
        sys.exit(0)

    hits = data.get("hits", [])
    total = data.get("total", 0)
    print(f"  API returned {len(hits)} paths, {total} total hits", file=sys.stderr)

    block = build_block(hits, start, end)

    if args.inject:
        inject(args.inject, block)
    else:
        print(block)


if __name__ == "__main__":
    main()
