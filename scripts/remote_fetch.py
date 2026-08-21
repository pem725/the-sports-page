#!/usr/bin/env python3
"""Fetch data that needs a credential. Designed to run in GitHub Actions.

WHY THIS RUNS IN CI AND NOT ON A LAPTOP.

GitHub Actions secrets are **write-only**. You can set one and a workflow can use
it, but nothing can read one back out -- not the API, not `gh`, not a local
script. That is the point of them, and it is a genuinely better place for a
credential than a file on a machine.

The consequence is architectural: any code that needs a key has to run *inside*
the workflow. So this script runs there, writes its results into `data/`, and the
workflow commits them. Everything downstream then reads committed data and needs
no credential at all.

That also means a key never has to touch a laptop, and secrets can be rotated
from a phone browser without anyone opening a terminal.

    python3 scripts/remote_fetch.py --check      # credential smoke test only
    python3 scripts/remote_fetch.py --cfb        # ND / CFB data
    python3 scripts/remote_fetch.py --youtube "Notre Dame football"

Nothing here ever prints a key. Failures report status codes and reasons.
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
SALT = b"the-sports-page/check_env/v1"

# The workflow maps repository secrets onto these names. YOUTUBE_API is the name
# used in the repo's secret store; it is exported as YOUTUBE_API_KEY here so the
# code reads naturally. Keep the mapping in the workflow, not in the code.
CFBD = "CFBD_KEY"
YT = "YOUTUBE_API_KEY"


def fp(v):
    return hashlib.sha256(SALT + v.encode()).hexdigest()[:8]


def shape(v, name):
    """Structural diagnostics that reveal nothing about the value.

    A 400 "API key not valid" from Google almost always means the STRING is
    wrong, not that the API is off (a disabled API returns 403 with a different
    message). The usual causes are a truncated paste, surrounding quotes, a
    trailing newline, or an OAuth client ID pasted where an API key belongs.
    None of that is visible from a fingerprint, and all of it is visible from
    the shape. Booleans only -- no characters are ever printed."""
    notes = [f"len {len(v)}"]
    if name.startswith("YOUTUBE"):
        # "AIza" is the universal prefix on every Google API key, so reporting
        # whether it is present discloses nothing that is not already public.
        notes.append("AIza-prefixed" if v.startswith("AIza") else "NOT AIza-prefixed")
        notes.append("39 chars" if len(v) == 39 else f"expected 39")
    if v != v.strip():
        notes.append("HAS SURROUNDING WHITESPACE")
    if v[:1] in "\"'" or v[-1:] in "\"'":
        notes.append("HAS QUOTE CHARACTERS")
    if any(c in v for c in "\n\r"):
        notes.append("CONTAINS A NEWLINE")
    return ", ".join(notes)


def get(url, headers=None, timeout=45):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.load(r)


def check():
    """Smoke-test every credential. Prints status and fingerprint, never a value."""
    ok = True

    key = os.environ.get(CFBD)
    if not key:
        print("  CFBD_KEY         MISSING"); ok = False
    else:
        try:
            st, d = get("https://api.collegefootballdata.com/teams/fbs?year=2026",
                        {"Authorization": f"Bearer {key}", "Accept": "application/json"})
            print(f"  CFBD_KEY         OK   fp {fp(key)}   HTTP {st}, {len(d)} FBS teams")
        except urllib.error.HTTPError as e:
            print(f"  CFBD_KEY         FAIL fp {fp(key)}   HTTP {e.code} {e.reason}"); ok = False
        except Exception as e:
            print(f"  CFBD_KEY         FAIL fp {fp(key)}   {type(e).__name__}"); ok = False

    key = os.environ.get(YT)
    if not key:
        print("  YOUTUBE_API_KEY  MISSING"); ok = False
    else:
        try:
            q = urllib.parse.urlencode({"part": "id", "forUsername": "GoogleDevelopers", "key": key})
            st, d = get(f"https://www.googleapis.com/youtube/v3/channels?{q}")
            print(f"  YOUTUBE_API_KEY  OK   fp {fp(key)}   HTTP {st}, quota responding")
            print(f"                   shape: {shape(key, YT)}")
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = json.load(e).get("error", {}).get("message", "")[:90]
            except Exception:
                pass
            print(f"  YOUTUBE_API_KEY  FAIL fp {fp(key)}   HTTP {e.code} {e.reason}  {body}")
            print(f"                   shape: {shape(key, YT)}"); ok = False
        except Exception as e:
            print(f"  YOUTUBE_API_KEY  FAIL fp {fp(key)}   {type(e).__name__}"); ok = False

    return ok


def youtube_volume(query, pages=3):
    """Aggregate view counts for recent videos matching a query.

    search.list gives ids only -- it does NOT return statistics, which is the
    usual reason a naive 'aggregate views' script returns zeros. videos.list is
    the call that carries viewCount, so ids have to be fetched first and hydrated
    second. search.list also costs 100 quota units per call against a 10,000/day
    default, so this caps itself deliberately.
    """
    key = os.environ[YT]
    ids, token, calls = [], None, 0
    while calls < pages:
        p = {"part": "id", "q": query, "type": "video", "maxResults": 50,
             "order": "date", "key": key}
        if token:
            p["pageToken"] = token
        st, d = get(f"https://www.googleapis.com/youtube/v3/search?{urllib.parse.urlencode(p)}")
        ids += [i["id"]["videoId"] for i in d.get("items", []) if i.get("id", {}).get("videoId")]
        token = d.get("nextPageToken")
        calls += 1
        if not token:
            break

    vids = []
    for i in range(0, len(ids), 50):
        p = {"part": "statistics,snippet", "id": ",".join(ids[i:i + 50]), "key": key}
        st, d = get(f"https://www.googleapis.com/youtube/v3/videos?{urllib.parse.urlencode(p)}")
        for v in d.get("items", []):
            s = v.get("statistics", {})
            vids.append({
                "id": v["id"],
                "title": v["snippet"]["title"],
                "channel": v["snippet"]["channelTitle"],
                "published": v["snippet"]["publishedAt"],
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)) if "likeCount" in s else None,
                "comments": int(s.get("commentCount", 0)) if "commentCount" in s else None,
            })
    vids.sort(key=lambda v: -v["views"])
    return {"query": query, "search_calls": calls, "videos_found": len(vids),
            "total_views": sum(v["views"] for v in vids), "videos": vids}


def cfb():
    key = os.environ[CFBD]
    h = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    out = {}
    _, out["fbs_2026"] = get("https://api.collegefootballdata.com/teams/fbs?year=2026", h)
    _, out["nd_schedule_2026"] = get(
        "https://api.collegefootballdata.com/games?year=2026&team=Notre%20Dame", h)
    try:
        _, out["sp_2026"] = get("https://api.collegefootballdata.com/ratings/sp?year=2026", h)
    except urllib.error.HTTPError as e:
        out["sp_2026"] = {"unavailable": f"HTTP {e.code}"}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--cfb", action="store_true")
    ap.add_argument("--youtube", metavar="QUERY")
    ap.add_argument("--pages", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)

    if a.check or not (a.cfb or a.youtube):
        print("credential smoke test:")
        return 0 if check() else 1

    if a.cfb:
        d = cfb()
        p = os.path.join(DATA, "cfb-2026.json")
        json.dump(d, open(p, "w"), indent=1)
        sp = d.get("sp_2026")
        print(f"  wrote {p}: {len(d['fbs_2026'])} FBS teams, "
              f"{len(d['nd_schedule_2026'])} ND games, "
              f"SP+ {'available' if isinstance(sp, list) else sp}")

    if a.youtube:
        d = youtube_volume(a.youtube, a.pages)
        slug = "".join(c if c.isalnum() else "-" for c in a.youtube.lower()).strip("-")
        p = os.path.join(DATA, f"youtube-{slug}.json")
        json.dump(d, open(p, "w"), indent=1)
        print(f"  wrote {p}: {d['videos_found']} videos, {d['total_views']:,} total views")
    return 0


if __name__ == "__main__":
    sys.exit(main())
