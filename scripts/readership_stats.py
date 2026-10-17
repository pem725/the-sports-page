#!/usr/bin/env python3
"""The count: how many people the paper reaches, for the top of the board.

    python3 scripts/readership_stats.py          # print the numbers
    stats()                                      # dict, used by build_budget.py

The editor, 2026-10-17: "by the time we hit 500 issues... we need a few thousand
readers... I need this thing to start humming." A goal nobody can see is a goal
nobody steers by, so the board now opens with the count, rebuilt every
publishing day.

Read at build time and never written to the repository: the repo is public, and
subscriber numbers belong on the locked board, not in a JSON file on GitHub. For
the same reason this never touches an email address -- it counts rows.

Each source is optional. A missing key or a dead API drops that number and keeps
the rest, because a board that fails to build over a vanity metric is worse than
a board missing one.
"""
import datetime
import json
import os
import re
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOAL_READERS = 2000      # "a few thousand readers" -- the low end, by issue 500
GOAL_ISSUE = 500
BD = "https://api.buttondown.com/v1"
GC = "https://thesportspage.goatcounter.com/api/v0"


def _get(url, auth):
    req = urllib.request.Request(url, headers={"Authorization": auth, "Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def _when(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def buttondown(now):
    key = os.environ.get("BUTTONDOWN_KEY")
    if not key:
        return {}
    auth = f"Token {key}"
    out = {}
    week_ago = now - datetime.timedelta(days=7)
    url = f"{BD}/subscribers?type=regular&page_size=100&ordering=-creation_date"
    first = _get(url, auth)
    out["subscribers"] = first["count"]
    new, page = 0, first
    while True:
        fresh = [r for r in page["results"] if _when(r["creation_date"]) >= week_ago]
        new += len(fresh)
        if len(fresh) < len(page["results"]) or not page.get("next"):
            break
        page = _get(page["next"], auth)
    out["new_7d"] = new
    emails = _get(f"{BD}/emails?page_size=7&ordering=-publish_date", auth)["results"][:7]
    opens = [(e.get("analytics") or {}).get("opens") for e in emails]
    opens = [o for o in opens if o is not None]
    if opens:
        out["opens_avg"] = sum(opens) / len(opens)
    return out


def goatcounter(today):
    tok = os.environ.get("GOATCOUNTER_TOKEN")
    if not tok:
        return {}
    auth = f"Bearer {tok}"
    end = today - datetime.timedelta(days=1)
    out = {}
    for key, e in (("views_7d", end), ("views_prev_7d", end - datetime.timedelta(days=7))):
        s = e - datetime.timedelta(days=6)
        out[key] = _get(f"{GC}/stats/total?start={s}&end={e}", auth)["total"]
    s = end - datetime.timedelta(days=6)
    hits = _get(f"{GC}/stats/hits?start={s}&end={end}&limit=200", auth).get("hits", [])
    issues = {}
    for h in hits:
        p = re.sub(r"^/the-sports-page", "", h.get("path", ""))
        if p.startswith("/published/") and p.endswith(".html"):
            issues[p] = issues.get(p, 0) + h.get("count", 0)
    if issues:
        p, n = max(issues.items(), key=lambda kv: kv[1])
        hed = p.rsplit("/", 1)[-1]
        f = REPO / p.lstrip("/")
        if f.exists():
            m = re.search(r'<h[12] class="hed"[^>]*>(.*?)</h[12]>', f.read_text(encoding="utf-8"), re.S)
            if m:
                hed = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
        out["top"] = {"path": p, "hed": hed, "views": n}
    return out


def stats(published=None):
    now = datetime.datetime.now(datetime.timezone.utc)
    out = {}
    for name, fn, arg in (("buttondown", buttondown, now), ("goatcounter", goatcounter, now.date())):
        try:
            out.update(fn(arg))
        except Exception as e:                       # one dead source drops one number
            out.setdefault("errors", []).append(f"{name}: {type(e).__name__}")
    if published is not None and "subscribers" in out:
        weeks_left = max((GOAL_ISSUE - published) / 7, 1)
        out["pace_needed"] = (GOAL_READERS - out["subscribers"]) / weeks_left
        out["weeks_left"] = weeks_left
    return out


if __name__ == "__main__":
    idx = (REPO / "index.html").read_text(encoding="utf-8")
    print(json.dumps(stats(idx.count('class="issue-num"')), indent=1, default=str))
