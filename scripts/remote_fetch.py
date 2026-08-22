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
import datetime as dt
import re

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



# ---------------------------------------------------------------------------
# Channel-based volume. The keyword version does not work.
#
# Searching "Michigan football" on a global platform returns Spanish-language
# soccer -- one such clip was 672,435 views and over HALF of Michigan's measured
# total. "Georgia football" matches the national team. Roughly 9-13% of every
# program's keyword results were off-topic, and because views are so skewed,
# that fraction drove the totals.
#
# Dedicated channels fix it: a channel about Notre Dame posts about Notre Dame.
# It is also ~100x cheaper. search.list costs 100 quota units per call;
# playlistItems.list and videos.list cost 1 each per 50 items. Discovery still
# uses search (once per program), but the recurring measurement does not.
# ---------------------------------------------------------------------------

def discover_channels(program, want=8):
    """Find candidate channels for a program. Costs 100 units per program."""
    key = os.environ[YT]
    p = {"part": "snippet", "q": program, "type": "channel",
         "maxResults": 25, "order": "relevance", "key": key}
    _, d = get(f"https://www.googleapis.com/youtube/v3/search?{urllib.parse.urlencode(p)}")
    ids = [i["snippet"]["channelId"] for i in d.get("items", [])]
    if not ids:
        return []
    p = {"part": "snippet,statistics,contentDetails", "id": ",".join(ids[:50]), "key": key}
    _, d = get(f"https://www.googleapis.com/youtube/v3/channels?{urllib.parse.urlencode(p)}")
    out = []
    for c in d.get("items", []):
        st = c.get("statistics", {})
        out.append({
            "channel_id": c["id"],
            "title": c["snippet"]["title"],
            "subscribers": int(st.get("subscriberCount", 0)) if not st.get("hiddenSubscriberCount") else None,
            "video_count": int(st.get("videoCount", 0)),
            "uploads_playlist": c["contentDetails"]["relatedPlaylists"]["uploads"],
        })
    out.sort(key=lambda c: -(c["subscribers"] or 0))
    return out[:want]


FOOTBALL = ("football","qb","quarterback","offense","defense","recruit","depth chart",
            "spring game","fall camp","gameday","kickoff","touchdown","secondary","o-line",
            "d-line","linebacker","wide receiver","running back","transfer portal","signing",
            "bowl","playoff","cfb","gridiron","snap","coordinator","spring ball")
OTHER_SPORT = ("basketball","hoops","volleyball","baseball","softball","soccer","hockey",
               "wrestling","track","gymnastics","swimming","tennis","golf","lacrosse","rowing")


def video_ids_from(urls):
    """Pull video ids out of any YouTube URL form: watch?v=, youtu.be/, /live/,
    /shorts/, or a bare id. Strips tracking params like ?si=."""
    out = []
    for u in re.split(r"[\s,]+", urls.strip()):
        if not u:
            continue
        u = u.split("&")[0]
        m = (re.search(r"[?&]v=([A-Za-z0-9_-]{11})", u)
             or re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", u)
             or re.search(r"/(?:live|shorts|embed)/([A-Za-z0-9_-]{11})", u)
             or re.fullmatch(r"([A-Za-z0-9_-]{11})", u))
        if m:
            out.append(m.group(1))
    return out


def channels_from_videos(urls):
    """Resolve videos to the channels that published them. 1 quota unit per 50.

    This is the antidote to search-based discovery. search.list ranks by YouTube
    relevance, which surfaces big national shows and buries the small
    program-specific channels a fan actually watches -- which is how Notre Dame
    ended up with zero channels while Josh Pate's national show was filed under
    six different programs. A human handing over four links they actually watch
    is better evidence than the algorithm's guess."""
    key = os.environ[YT]
    ids = video_ids_from(urls)
    if not ids:
        raise SystemExit("no video ids found in that input")
    p = {"part": "snippet", "id": ",".join(ids), "key": key}
    _, d = get(f"https://www.googleapis.com/youtube/v3/videos?{urllib.parse.urlencode(p)}")
    found = {}
    for v in d.get("items", []):
        sn = v["snippet"]
        found[sn["channelId"]] = {"channel_id": sn["channelId"], "title": sn["channelTitle"],
                                  "seed_video": v["id"], "seed_title": sn["title"][:90]}
    missing = set(ids) - {v["id"] for v in d.get("items", [])}
    if missing:
        print(f"  could not resolve: {', '.join(sorted(missing))} (private/deleted?)")
    if not found:
        return []
    p = {"part": "snippet,statistics,contentDetails", "id": ",".join(found), "key": key}
    _, d = get(f"https://www.googleapis.com/youtube/v3/channels?{urllib.parse.urlencode(p)}")
    out = []
    for c in d.get("items", []):
        st = c.get("statistics", {})
        base = found[c["id"]]
        out.append({**base,
                    "title": c["snippet"]["title"],
                    "subscribers": int(st.get("subscriberCount", 0)) if not st.get("hiddenSubscriberCount") else None,
                    "video_count": int(st.get("videoCount", 0)),
                    "uploads_playlist": c["contentDetails"]["relatedPlaylists"]["uploads"]})
    return out


NICKNAMES = {
 "Notre Dame":["notre dame","irish","freeman"], "Ohio State":["ohio state","buckeye","osu","day"],
 "Alabama":["alabama","crimson","tide","bama"], "Michigan":["michigan","wolverine"],
 "Georgia":["georgia","bulldog","dawg","uga","kirby"], "Texas":["texas","longhorn","horns","sarkisian"],
 "USC":["usc","trojan","riley"], "Penn State":["penn state","nittany","psu","franklin"],
 "Oregon":["oregon","duck","lanning"], "LSU":["lsu","tiger","kelly"],
 "Nebraska":["nebraska","husker","rhule"], "Clemson":["clemson","tiger","swinney"],
 "Tennessee":["tennessee","vol"], "Florida":["florida","gator"], "Auburn":["auburn"],
 "Oklahoma":["oklahoma","sooner"], "Texas A&M":["texas a&m","aggie"], "Miami":["miami","hurricane"],
 "Florida State":["florida state","seminole","fsu"], "Wisconsin":["wisconsin","badger"],
}

# Locked On runs a per-program daily show with the same format and cadence, which
# makes it a MATCHED comparison rather than an apples-to-oranges one. Handles are
# resolved with channels.list?forHandle at 1 quota unit each, instead of 100 for a
# search -- and the resolved title is verified rather than trusted.
LOCKED_ON = {
 "Notre Dame":["LockedOnIrish","LockedOnNotreDame"], "Ohio State":["LockedOnBuckeyes"],
 "Alabama":["LockedOnCrimsonTide","LockedOnBama","LockedOnAlabama"],
 "Michigan":["LockedOnWolverines","LockedOnMichigan"], "Georgia":["LockedOnBulldogs","LockedOnGeorgia"],
 "Texas":["LockedOnLonghorns","LockedOnTexas"], "USC":["LockedOnTrojans","LockedOnUSC"],
 "Penn State":["LockedOnNittanyLions","LockedOnPennState"], "Oregon":["LockedOnDucks","LockedOnOregon"],
 "LSU":["LockedOnLSU","LockedOnTigersLSU"], "Nebraska":["LockedOnHuskers","LockedOnNebraska"],
 "Clemson":["LockedOnClemson","LockedOnTigers"], "Tennessee":["LockedOnVols","LockedOnTennessee"],
 "Florida":["LockedOnGators","LockedOnFlorida"], "Auburn":["LockedOnAuburn","LockedOnTigersAuburn"],
 "Oklahoma":["LockedOnSooners","LockedOnOklahoma"], "Texas A&M":["LockedOnAggies","LockedOnTexasAM"],
 "Miami":["LockedOnCanes","LockedOnHurricanes"], "Florida State":["LockedOnSeminoles","LockedOnFSU"],
 "Wisconsin":["LockedOnBadgers","LockedOnWisconsin"],
}


def channel_by_handle(handle):
    """Resolve a @handle to a channel. 1 quota unit. Returns None if absent."""
    key = os.environ[YT]
    p = {"part": "snippet,statistics,contentDetails", "forHandle": handle, "key": key}
    try:
        _, d = get(f"https://www.googleapis.com/youtube/v3/channels?{urllib.parse.urlencode(p)}")
    except urllib.error.HTTPError:
        return None
    items = d.get("items") or []
    if not items:
        return None
    c = items[0]; st = c.get("statistics", {})
    return {"channel_id": c["id"], "title": c["snippet"]["title"], "handle": handle,
            "subscribers": int(st.get("subscriberCount", 0)) if not st.get("hiddenSubscriberCount") else None,
            "video_count": int(st.get("videoCount", 0)),
            "uploads_playlist": c["contentDetails"]["relatedPlaylists"]["uploads"]}


def channel_program_share(ch, program, sample=50):
    """What share of recent uploads mention THIS program? ~2 quota units.

    This replaces the football-share filter, which was actively wrong. That test
    read titles for football words and so kept national shows (Josh Pate titles
    every video 'College Football...', scoring 100%) while discarding the very
    channels a fan watches: Notre Dame Daily scored 0% football and Locked On
    Irish 28%, because a daily pod is titled 'Marcus Freeman on the O-line
    rotation'. Program-exclusivity is the question that was always meant."""
    key = os.environ[YT]
    keys = NICKNAMES.get(program, [program.lower()])
    p = {"part": "snippet", "playlistId": ch["uploads_playlist"], "maxResults": min(sample, 50), "key": key}
    try:
        _, d = get(f"https://www.googleapis.com/youtube/v3/playlistItems?{urllib.parse.urlencode(p)}")
    except urllib.error.HTTPError:
        return None
    titles = [i["snippet"]["title"].lower() for i in d.get("items", [])]
    if len(titles) < 5:
        return None
    hit = sum(any(k in t for k in keys) for t in titles)
    return {"sampled": len(titles), "program_share": hit / len(titles)}


def channel_football_share(ch, sample=50):
    """What share of a channel's recent uploads are football? ~2 quota units.

    This is the test for 'football-exclusive'. A name check cannot do it: an
    official athletics channel is called 'Nebraska Huskers' and posts volleyball,
    while 'Eleven Warriors' is entirely Ohio State football. Only the content
    answers it. Heuristic, and stated as such -- it reads titles, not video."""
    key = os.environ[YT]
    p = {"part": "snippet", "playlistId": ch["uploads_playlist"], "maxResults": min(sample,50), "key": key}
    try:
        _, d = get(f"https://www.googleapis.com/youtube/v3/playlistItems?{urllib.parse.urlencode(p)}")
    except urllib.error.HTTPError:
        return None
    titles = [i["snippet"]["title"].lower() for i in d.get("items", [])]
    if len(titles) < 8:
        return None
    fb = sum(any(k in t for k in FOOTBALL) for t in titles)
    ot = sum(any(k in t for k in OTHER_SPORT) for t in titles)
    return {"sampled": len(titles), "football": fb/len(titles), "other_sport": ot/len(titles)}


def channel_volume(channels, days=30):
    """Uploads and views per channel within the last `days`. ~2 units per channel."""
    key = os.environ[YT]
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days))
    vids, seen = [], set()
    for c in channels:
        token, ids = None, []
        while True:
            p = {"part": "contentDetails", "playlistId": c["uploads_playlist"],
                 "maxResults": 50, "key": key}
            if token:
                p["pageToken"] = token
            try:
                _, d = get(f"https://www.googleapis.com/youtube/v3/playlistItems?{urllib.parse.urlencode(p)}")
            except urllib.error.HTTPError:
                break                      # private or empty uploads playlist
            stop = False
            for i in d.get("items", []):
                cd = i["contentDetails"]
                pub = cd.get("videoPublishedAt")
                if not pub:
                    continue
                if dt.datetime.fromisoformat(pub.replace("Z", "+00:00")) < cutoff:
                    stop = True
                    break
                ids.append(cd["videoId"])
            token = d.get("nextPageToken")
            if stop or not token:
                break
        for i in range(0, len(ids), 50):
            p = {"part": "statistics,snippet", "id": ",".join(ids[i:i + 50]), "key": key}
            _, d = get(f"https://www.googleapis.com/youtube/v3/videos?{urllib.parse.urlencode(p)}")
            for v in d.get("items", []):
                if v["id"] in seen:        # a video can sit in two channels' feeds
                    continue
                seen.add(v["id"])
                vids.append({"id": v["id"], "channel": v["snippet"]["channelTitle"],
                             "title": v["snippet"]["title"],
                             "published": v["snippet"]["publishedAt"],
                             "views": int(v.get("statistics", {}).get("viewCount", 0))})
    return vids


def top_programs(n=50, year=2025):
    """Top-N FBS programs by CFBD talent composite -- a defensible, verifiable
    ranking rather than a hand-picked list. Talent is recruiting-based, so it
    measures programs people invest in, which is the right frame for an
    attention study."""
    key = os.environ[CFBD]
    h = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    _, t = get(f"https://api.collegefootballdata.com/talent?year={year}", h)
    _, fbs = get(f"https://api.collegefootballdata.com/teams/fbs?year={year}", h)
    # CFBD is inconsistent: /talent rows carry "team", /teams/fbs carry "school".
    # Reading "school" off a talent row silently yields None for every row, which
    # filtered the whole list to empty rather than erroring.
    ok = {x["school"] for x in fbs}
    rows = [x for x in t if x.get("team") in ok]
    if not rows:
        raise SystemExit(f"no talent rows matched FBS teams "
                         f"(talent n={len(t)}, fbs n={len(fbs)}) -- check the field names")
    rows.sort(key=lambda x: -float(x.get("talent", 0)))
    return [x["team"] for x in rows[:n]]


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
    ap.add_argument("--discover", metavar="PROGRAMS", help="comma-separated; finds channels")
    ap.add_argument("--channel-volume", action="store_true")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, help="discover channels for the top N CFBD programs")
    ap.add_argument("--filter-exclusive", action="store_true",
                    help="keep only channels whose recent uploads are mostly football")
    ap.add_argument("--locked-on", action="store_true", help="build the matched Locked On set")
    ap.add_argument("--lockedon-volume", action="store_true", help="measure the Locked On set")
    ap.add_argument("--seed-videos", metavar="URLS", help="resolve video URLs to channels")
    ap.add_argument("--seed-label", default="seed", help="program label for seeded channels")
    ap.add_argument("--min-football", type=float, default=0.70)
    ap.add_argument("--max-other", type=float, default=0.15)
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)

    if a.check or not (a.cfb or a.youtube or a.discover or a.channel_volume or a.top or a.filter_exclusive or a.seed_videos or a.locked_on or a.lockedon_volume):
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

    if a.lockedon_volume:
        chans = json.load(open(os.path.join(DATA, "youtube-lockedon.json")))
        res = {}
        for prog, c in chans.items():
            vids = channel_volume([c], a.days)
            v = sorted(x["views"] for x in vids)
            res[prog] = {"channel": c["title"], "subscribers": c["subscribers"],
                         "days": a.days, "uploads": len(vids),
                         "views": sum(v), "median_views": (v[len(v)//2] if v else 0),
                         "detail": vids}
            if v:
                print(f"    {prog:<14} {len(v):>3} uploads  {sum(v):>9,} views  "
                      f"median {v[len(v)//2]:>6,}  {sum(v)/len(v):>7,.0f} per upload")
            else:
                print(f"    {prog:<14} no uploads in {a.days} days")
        out = os.path.join(DATA, "youtube-lockedon-volume.json")
        json.dump(res, open(out, "w"), indent=1)
        print(f"  wrote {out}")

    if a.locked_on:
        out, tried = {}, 0
        for prog, handles in LOCKED_ON.items():
            for h in handles:
                tried += 1
                c = channel_by_handle(h)
                if not c:
                    continue
                if "locked on" not in c["title"].lower():   # verify, do not trust
                    print(f"    {prog:<14} @{h} resolved to {c['title'][:30]!r} -- rejected")
                    continue
                sh = channel_program_share(c, prog)
                c["program_share"] = round(sh["program_share"], 3) if sh else None
                out[prog] = c
                print(f"    {prog:<14} {c['title'][:30]:<30} {str(c['subscribers'] or '-'):>8} subs "
                      f"{c['video_count']:>5} vids  program {c['program_share']:.0%}" if sh else "")
                break
            else:
                print(f"    {prog:<14} no Locked On channel found")
        path = os.path.join(DATA, "youtube-lockedon.json")
        json.dump(out, open(path, "w"), indent=1)
        print(f"  resolved {len(out)}/{len(LOCKED_ON)} programs in {tried} handle lookups (~{tried} units)")
        print(f"  wrote {path}")

    if a.seed_videos:
        chans = channels_from_videos(a.seed_videos)
        path = os.path.join(DATA, "youtube-seed-channels.json")
        existing = json.load(open(path)) if os.path.exists(path) else {}
        existing.setdefault(a.seed_label, [])
        have = {c["channel_id"] for c in existing[a.seed_label]}
        for c in chans:
            if c["channel_id"] not in have:
                existing[a.seed_label].append(c)
        json.dump(existing, open(path, "w"), indent=1)
        print(f"  resolved {len(chans)} channels for '{a.seed_label}':")
        for c in chans:
            sh = channel_football_share(c)
            fb = f"{sh['football']:.0%} football, {sh['other_sport']:.0%} other" if sh else "unsampled"
            print(f"    {c['title'][:34]:<34} {str(c['subscribers'] or '-'):>9} subs  {c['video_count']:>6} vids  [{fb}]")
        print(f"  wrote {path}")

    if a.top:
        progs = top_programs(a.top)
        print(f"  top {a.top} programs by CFBD talent: {progs[0]}, {progs[1]}, ... {progs[-1]}")
        print(f"  discovery cost ~{len(progs)*100:,} quota units")
        out = {}
        for i, pr in enumerate(progs, 1):
            try:
                ch = discover_channels(pr + " football")
            except urllib.error.HTTPError as e:
                print(f"    [{i}/{len(progs)}] {pr:<22} HTTP {e.code} -- stopping (quota?)"); break
            out[pr] = ch
            print(f"    [{i}/{len(progs)}] {pr:<22} {len(ch)} channels")
        path = os.path.join(DATA, "youtube-channels.json")
        json.dump(out, open(path, "w"), indent=1)
        print(f"  wrote {path}")

    if a.filter_exclusive:
        path = os.path.join(DATA, "youtube-channels.json")
        chans = json.load(open(path))
        kept, dropped = {}, 0
        for pr, ch in chans.items():
            keep = []
            for c in ch:
                sh = channel_football_share(c)
                if sh is None:
                    dropped += 1; continue
                c["football_share"] = round(sh["football"], 3)
                c["other_sport_share"] = round(sh["other_sport"], 3)
                if sh["football"] >= a.min_football and sh["other_sport"] <= a.max_other:
                    keep.append(c)
                else:
                    dropped += 1
            kept[pr] = keep
            print(f"    {pr:<22} kept {len(keep)}/{len(ch)}")
        json.dump(kept, open(path, "w"), indent=1)
        n=sum(len(v) for v in kept.values())
        print(f"  kept {n} football-exclusive channels, dropped {dropped}")
        print(f"  thresholds: football >= {a.min_football:.0%}, other sport <= {a.max_other:.0%}")

    if a.discover:
        progs = [q.strip() for q in a.discover.split(",") if q.strip()]
        print(f"  discovering channels for {len(progs)} programs (~{len(progs)*100:,} units)")
        out = {}
        for pr in progs:
            ch = discover_channels(pr)
            out[pr] = ch
            print(f"    {pr:<24} {len(ch)} channels, top: {ch[0]['title'][:34] if ch else '-'}")
        path = os.path.join(DATA, "youtube-channels.json")
        json.dump(out, open(path, "w"), indent=1)
        print(f"  wrote {path} -- REVIEW AND EDIT THIS before measuring")

    if a.channel_volume:
        path = os.path.join(DATA, "youtube-channels.json")
        chans = json.load(open(path))
        res = {}
        for pr, ch in chans.items():
            vids = channel_volume(ch, a.days)
            res[pr] = {"channels": [c["title"] for c in ch], "days": a.days,
                       "videos": len(vids), "views": sum(v["views"] for v in vids),
                       "detail": vids}
            print(f"    {pr:<24} {len(vids):>4} uploads  {sum(v['views'] for v in vids):>12,} views"
                  f"  ({len(vids)/a.days:.1f}/day)")
        out = os.path.join(DATA, "youtube-channel-volume.json")
        json.dump(res, open(out, "w"), indent=1)
        print(f"  wrote {out}")

    if a.youtube:
        # Comma-separated queries so a whole comparison set lands in one run.
        # Quota arithmetic, because it is easy to blow through: search.list costs
        # 100 units per page against 10,000/day, videos.list costs 1 per call of
        # up to 50 ids. So N programs x P pages costs about N*P*100 units.
        queries = [q.strip() for q in a.youtube.split(",") if q.strip()]
        cost = len(queries) * a.pages * 100
        print(f"  {len(queries)} queries x {a.pages} pages ~= {cost:,} quota units of 10,000/day")
        if cost > 9000:
            print("  refusing: that would exhaust the daily quota"); return 1
        results = {}
        for q in queries:
            d = youtube_volume(q, a.pages)
            results[q] = d
            print(f"    {q:<26} {d['videos_found']:>4} videos  {d['total_views']:>12,} views")
        if len(queries) == 1:
            slug = "".join(c if c.isalnum() else "-" for c in queries[0].lower()).strip("-")
            out = os.path.join(DATA, f"youtube-{slug}.json"); payload = results[queries[0]]
        else:
            out = os.path.join(DATA, "youtube-programs.json"); payload = results
        json.dump(payload, open(out, "w"), indent=1)
        print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
