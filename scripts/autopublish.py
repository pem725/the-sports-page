#!/usr/bin/env python3
"""
autopublish.py — Deterministic Mon-Sat publisher for The Sports Page.

Reads the queue, updates metadata, inserts into index.html, moves the file,
commits, and pushes. No AI, no web calls, no dependencies beyond stdlib.

Usage:
    python scripts/autopublish.py            # live publish
    python scripts/autopublish.py --dry-run  # preview without changes
"""

import datetime
import html
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_DIR = os.path.join(REPO, "queue")
PUBLISHED_DIR = os.path.join(REPO, "published")
INDEX_HTML = os.path.join(REPO, "index.html")
QUEUE_ORDER = os.path.join(REPO, "QUEUE_ORDER.txt")
CLAUDE_MD = os.path.join(REPO, "CLAUDE.md")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd, check=True):
    """Run a shell command from the repo root."""
    return subprocess.run(
        cmd, shell=True, cwd=REPO, capture_output=True, text=True, check=check
    )


def fail(msg):
    """Print error, create a GitHub issue (if gh is available), and exit."""
    print(f"ERROR: {msg}", file=sys.stderr)
    today = datetime.date.today().strftime("%Y-%m-%d")
    title = f"Publish failure: {today}"
    body = f"Autopublish script failed.\n\n**Error:** {msg}\n\n**Date:** {today}"
    run(
        f'gh issue create --title "{title}" --label "publish-failure" --body "{body}"',
        check=False,
    )
    sys.exit(1)


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------------------
# Step 0: Day-of-week gate
# ---------------------------------------------------------------------------

def check_day():
    today = datetime.date.today()
    if today.weekday() == 6:  # Sunday = 6
        print("Today is Sunday. Skipping — Sunday Editions are manual.")
        sys.exit(0)
    return today


# ---------------------------------------------------------------------------
# Step 1: Pick the next file from the queue
# ---------------------------------------------------------------------------

def pick_file(last_topic):
    """Read QUEUE_ORDER.txt and return (filename, full_path) for the next
    publishable file, respecting the variety rule."""
    if not os.path.isfile(QUEUE_ORDER):
        fail("QUEUE_ORDER.txt not found.")

    lines = [l.strip() for l in read_file(QUEUE_ORDER).splitlines() if l.strip()]
    if not lines:
        fail("QUEUE_ORDER.txt is empty — no articles to publish.")

    for filename in lines:
        if filename.startswith("sunday-"):
            continue
        path = os.path.join(QUEUE_DIR, filename)
        if not os.path.isfile(path):
            print(f"  Skipping {filename} (file not in queue/)")
            continue

        # Check for Sal byline — never auto-publish Sal
        content = read_file(path)
        if re.search(r'By\s+Sal\b', content, re.IGNORECASE):
            print(f"  Skipping {filename} (Sal byline — requires manual publish)")
            continue

        # Variety check
        meta = parse_meta(content)
        topic = meta.get("topic", "")
        if topic and topic.lower() == last_topic.lower():
            print(f"  Skipping {filename} (same topic as yesterday: {topic})")
            continue

        return filename, path

    fail("No publishable file found in QUEUE_ORDER.txt after variety/Sal checks.")


# ---------------------------------------------------------------------------
# Step 2: Parse metadata from queue file
# ---------------------------------------------------------------------------

def parse_meta(content):
    """Extract PUBLISH-META comment block from HTML content."""
    m = re.search(r'<!--\s*PUBLISH-META\s*\n(.*?)\n\s*-->', content, re.DOTALL)
    if not m:
        return {}
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip().lower()] = val.strip()
    return meta


def parse_tags(tags_str):
    """Parse 'MLB:mlb, Analytics, CFB:cfb' into [(text, css_class), ...]"""
    tags = []
    for part in tags_str.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            text, css = part.rsplit(":", 1)
            tags.append((text.strip(), css.strip()))
        else:
            tags.append((part, ""))
    return tags


# ---------------------------------------------------------------------------
# Step 3: Extract headline and deck from the HTML
# ---------------------------------------------------------------------------

def extract_headline(content):
    """Get text from <h1 class="hed">...</h1>, stripping HTML tags."""
    m = re.search(r'<h1\s+class="hed">(.*?)</h1>', content, re.DOTALL)
    if not m:
        fail("Could not find <h1 class=\"hed\"> in the article.")
    raw = m.group(1).strip()
    # Keep the raw HTML for the index entry (it has &rsquo; etc.)
    return raw


def extract_deck(content):
    """Get text from <div class="deck">...</div>."""
    m = re.search(r'<div\s+class="deck">\s*(.*?)\s*</div>', content, re.DOTALL)
    if not m:
        fail("Could not find <div class=\"deck\"> in the article.")
    return m.group(1).strip()


# ---------------------------------------------------------------------------
# Step 4: Derive issue number from index.html
# ---------------------------------------------------------------------------

def get_next_issue_number():
    idx = read_file(INDEX_HTML)
    count = len(re.findall(r'class="issue-num"', idx))
    return count + 1


# ---------------------------------------------------------------------------
# Step 5: Get last published topic from index.html
# ---------------------------------------------------------------------------

def get_last_topic():
    """Extract the topic of the most recent issue in index.html.
    Checks data-topic attribute first (set by autopublish), falls back to first tag text."""
    idx = read_file(INDEX_HTML)
    # Try data-topic on the first issue div
    m = re.search(r'<div class="issue"[^>]*data-topic="([^"]*)"', idx)
    if m:
        return m.group(1)
    # Fallback: first tag text from the most recent issue
    m = re.search(r'<div class="issue-tags">\s*(.*?)\s*</div>', idx, re.DOTALL)
    if not m:
        return ""
    tags = re.findall(r'class="tag[^"]*">(.*?)</span>', m.group(1))
    return tags[0] if tags else ""


# ---------------------------------------------------------------------------
# Step 6: Update issue number and date in the article HTML
# ---------------------------------------------------------------------------

def update_article(content, issue_num, today):
    date_str = today.strftime("%B %-d, %Y")  # e.g., "April 18, 2026"

    # Update <title>
    content = re.sub(
        r'<title>.*?</title>',
        f'<title>The Sports Page — Issue No. {issue_num} — {date_str}</title>',
        content,
    )

    # Update Issue No. in datebar and footer (handles "Issue No. __", "Issue No. 11", etc.)
    content = re.sub(
        r'Issue No\.\s*[_\d]+',
        f'Issue No. {issue_num}',
        content,
    )

    # Update date in datebar <span> — match common date patterns
    # Pattern: Month DD, YYYY or Month __, YYYY or Month YYYY
    date_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(?:_+|\d{1,2})?,?\s*\d{4}'
    content = re.sub(date_pattern, date_str, content)

    # Remove the PUBLISH-META comment from the published file (cleanup)
    content = re.sub(r'<!--\s*PUBLISH-META\s*\n.*?\n\s*-->\s*\n?', '', content, flags=re.DOTALL)

    return content


# ---------------------------------------------------------------------------
# Step 7: Insert new entry into index.html
# ---------------------------------------------------------------------------

def insert_index_entry(issue_num, today, filename, headline, deck, tags, topic):
    date_str = today.strftime("%B %-d, %Y")

    # Build tags HTML
    tag_spans = []
    for text, css in tags:
        cls = f'tag {css}' if css else 'tag'
        tag_spans.append(f'          <span class="{cls}">{text}</span>')
    tags_html = "\n".join(tag_spans)

    entry = f"""    <div class="issue" data-topic="{topic}">
      <div class="issue-num">{issue_num}</div>
      <div class="issue-body">
        <div class="issue-date">{date_str}</div>
        <div class="issue-hed"><a href="published/{filename}">{headline}</a></div>
        <div class="issue-deck">{deck}</div>
        <div class="issue-tags">
{tags_html}
        </div>
      </div>
    </div>

"""

    idx = read_file(INDEX_HTML)
    # Insert right after <div class="issues">
    marker = '<div class="issues">'
    pos = idx.find(marker)
    if pos == -1:
        fail('Could not find <div class="issues"> in index.html')
    insert_at = pos + len(marker) + 1  # after the newline
    idx = idx[:insert_at] + "\n" + entry + idx[insert_at:]
    write_file(INDEX_HTML, idx)


# ---------------------------------------------------------------------------
# Step 8: Update QUEUE_ORDER.txt
# ---------------------------------------------------------------------------

def remove_from_queue_order(filename):
    lines = read_file(QUEUE_ORDER).splitlines()
    lines = [l for l in lines if l.strip() != filename]
    write_file(QUEUE_ORDER, "\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# Step 9: Update CLAUDE.md current state
# ---------------------------------------------------------------------------

def update_claude_md(issue_num, filename, headline_plain, today):
    md = read_file(CLAUDE_MD)
    date_str = today.strftime("%B %-d, %Y")

    # List remaining queue files
    remaining = sorted(os.listdir(QUEUE_DIR)) if os.path.isdir(QUEUE_DIR) else []
    remaining = [f for f in remaining if f.endswith(".html") and f != filename]
    queue_desc = f"{len(remaining)} articles ready ({', '.join(f.replace('.html','') for f in remaining)})" if remaining else "empty"

    # Update published count
    md = re.sub(r'Published:\s*\d+\s*issues.*', f'Published: {issue_num} issues (#1-{issue_num})', md)
    # Update queue
    md = re.sub(r'Queue:\s*.*', f'Queue: {queue_desc}', md)
    # Update goal
    md = re.sub(r'Goal:\s*\d+\s*issues.*', f'Goal: {500 - issue_num} issues remaining of 500', md)
    # Update last published
    md = re.sub(
        r'Last published:.*',
        f'Last published: Issue #{issue_num} — "{headline_plain}" ({filename}) on {date_str}',
        md,
    )

    write_file(CLAUDE_MD, md)


# ---------------------------------------------------------------------------
# Step 10: Cross-reference check
# ---------------------------------------------------------------------------

def check_cross_references(content, issue_num):
    """Warn about references to unpublished issues."""
    refs = re.findall(r'Issue\s*#?\s*(\d+)', content)
    warnings = []
    for ref in refs:
        ref_num = int(ref)
        if ref_num >= issue_num:
            warnings.append(f"  Warning: references Issue #{ref_num} which is not yet published")
    return warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("The Sports Page — Autopublish")
    print("=" * 60)

    # Step 0: Day check
    today = check_day()
    print(f"Date: {today.strftime('%A, %B %-d, %Y')}")

    # Step 1: Get last topic and pick file
    last_topic = get_last_topic()
    print(f"Last published topic: {last_topic or '(none)'}")

    filename, filepath = pick_file(last_topic)
    print(f"Selected: {filename}")

    # Step 2: Parse metadata
    content = read_file(filepath)
    meta = parse_meta(content)
    topic = meta.get("topic", "Unknown")
    tags_str = meta.get("tags", topic)
    tags = parse_tags(tags_str)
    print(f"Topic: {topic}")
    print(f"Tags: {[t[0] for t in tags]}")

    if not meta:
        fail(f"{filename} is missing PUBLISH-META comment. Add metadata before publishing.")

    # Step 3: Extract headline and deck
    headline = extract_headline(content)
    deck = extract_deck(content)
    # Plain-text headline for commit message and CLAUDE.md
    headline_plain = re.sub(r'<[^>]+>', '', html.unescape(headline))
    print(f"Headline: {headline_plain[:80]}...")

    # Step 4: Get issue number
    issue_num = get_next_issue_number()
    print(f"Issue number: #{issue_num}")

    # Step 5: Cross-reference check
    warnings = check_cross_references(content, issue_num)
    for w in warnings:
        print(w)

    # Step 6: Update the article HTML
    updated_content = update_article(content, issue_num, today)

    if dry_run:
        print("\n--- DRY RUN ---")
        print(f"Would publish: {filename} as Issue #{issue_num}")
        print(f"Headline: {headline_plain}")
        print(f"Tags: {tags_str}")
        print("No changes made.")
        return

    # Write the updated article
    write_file(filepath, updated_content)

    # Step 7: Insert into index.html
    insert_index_entry(issue_num, today, filename, headline, deck, tags, topic)
    print("Updated index.html")

    # Step 8: Move file
    run(f'git mv "queue/{filename}" "published/{filename}"')
    print(f"Moved queue/{filename} → published/{filename}")

    # Step 9: Update QUEUE_ORDER.txt
    remove_from_queue_order(filename)
    print("Updated QUEUE_ORDER.txt")

    # Step 10: Update CLAUDE.md
    update_claude_md(issue_num, filename, headline_plain, today)
    print("Updated CLAUDE.md")

    # Step 11: Commit and push
    run(f'git add index.html "published/{filename}" QUEUE_ORDER.txt CLAUDE.md')
    commit_msg = f"Publish Issue #{issue_num}: {headline_plain[:60]}"
    run(f'git commit -m "{commit_msg}"')
    run("git push origin main")

    print()
    print(f"Published Issue #{issue_num}: {headline_plain[:60]}")
    print(f"Live at: https://pem725.github.io/the-sports-page/published/{filename}")
    print("Done.")


if __name__ == "__main__":
    main()
