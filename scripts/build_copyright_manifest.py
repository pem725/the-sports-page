#!/usr/bin/env python3
"""Build the deposit materials and manifest for copyright registration.

GRTX -- the Copyright Office's group option for short online literary works --
wants four things per work: title, filename, publication date, and word count.
All four are derivable from the repository exactly, so none of them should ever
be typed by hand into a government form under penalty of perjury.

What this produces, in filing/copyright/:

  deposits/<slug>.txt   one plain-text copy of each issue, which is the thing
                        actually deposited. Text only, matching what GRTX covers.
  manifest.csv          every issue: title, filename, date, words, eligibility
  batches/              one folder per application, each with its own CSV and a
                        ZIP of exactly the files in that application

Batching obeys two independent constraints:

  * GRTX rule -- every work in one application must be published within a
    three-consecutive-calendar-month period, and no more than 50 works.
  * 17 U.S.C. 412 -- statutory damages and attorney's fees require registration
    within three months of first publication. That is the same three months,
    which is why calendar quarters are the natural batching unit.

Run: python3 scripts/build_copyright_manifest.py
"""
import os, re, csv, sys, html, json, zipfile, subprocess
from datetime import date, datetime
from collections import defaultdict

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("needs beautifulsoup4:  pip install beautifulsoup4")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB  = os.path.join(REPO, "published")
OUT  = os.path.join(REPO, "filing", "copyright")
DEP  = os.path.join(OUT, "deposits")
BAT  = os.path.join(OUT, "batches")

MIN_WORDS, MAX_WORDS = 50, 17500      # GRTX eligibility band
MAX_PER_APP          = 50             # GRTX ceiling

MONTHS = ("January February March April May June July August September "
          "October November December").split()


def parse_date(text):
    """'August 11, 2026' -> date(2026, 8, 11). Returns None if unparseable."""
    m = re.search(r"([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})", text or "")
    if not m or m.group(1) not in MONTHS:
        return None
    return date(int(m.group(3)), MONTHS.index(m.group(1)) + 1, int(m.group(2)))


DRAFT_DIRS = ("queue/", "reserve/", "frames/")


_HISTORY = None


def history():
    """{path: (first-seen date, rename source or None)} for every add/rename.

    Built in ONE pass over the whole log rather than one `git log -- <path>` per
    file. That is not just faster: a path-limited log prunes the rename SOURCE
    out of the diff, so git stops reporting the rename at all and every move
    looks like a fresh add. The bug that hid behind that was issues 001 and 002
    appearing to be published on 2 April when they went live on 29 March.
    """
    global _HISTORY
    if _HISTORY is not None:
        return _HISTORY
    out = subprocess.run(
        ["git", "-C", REPO, "log", "-M", "--reverse", "--diff-filter=AR",
         "--format=@%ad", "--date=short", "--name-status"],
        capture_output=True, text=True, timeout=120).stdout
    hist, when = {}, None
    for line in out.splitlines():                     # --reverse: oldest first
        if line.startswith("@"):
            when = line[1:].strip()
        elif line.strip() and when:
            f = line.split("\t")
            dest = f[-1].strip()
            src = f[1].strip() if f[0].startswith("R") and len(f) > 2 else None
            hist.setdefault(dest, (when, src))        # first sighting wins
    _HISTORY = hist
    return hist


def git_first_seen(path, _depth=0):
    """Earliest date this work existed at a PUBLICLY REACHABLE path.

    Copyright publication is distribution to the public, so the question is not
    when the file was written but when it first became reachable on the site.
    Two wrong answers were tried first, and the second was the dangerous one:

      * --diff-filter=A with --follow returns the date the DRAFT was created in
        queue/, which can be weeks early.
      * --follow at all is unsafe on this corpus. Every issue shares the same
        CSS and masthead boilerplate, so git's similarity heuristic happily
        matches unrelated works -- it traced 011-infield-hitting back through
        queue/005-draft-combinatorics to mets_500_newsletter on a 60% match.
        Three different issues. A publication date is a sworn fact on the
        application; it cannot rest on a fuzzy match.

    So renames are chased ONE EXPLICIT STEP AT A TIME, path-limited, and only
    when the source was itself a public path. In practice that matters for
    exactly two files: issues 001 and 002 went live at the repository root on
    29 March 2026 and were only moved into published/ during the 2 April
    restructure.
    """
    rel = os.path.relpath(path, REPO)
    rec = history().get(rel)
    if rec is None:
        return None
    when, src = rec
    if src and not src.startswith(DRAFT_DIRS) and _depth < 8:
        earlier = git_first_seen(os.path.join(REPO, src), _depth + 1)
        if earlier:
            return earlier
    return datetime.strptime(when, "%Y-%m-%d").date()


def extract(path):
    soup = BeautifulSoup(open(path, encoding="utf-8").read(), "html.parser")

    og = soup.find("meta", property="og:title")
    hed = soup.find(class_="hed")
    title = ((og.get("content") if og else None)
             or (hed.get_text(" ", strip=True) if hed else None)
             or (soup.title.get_text(strip=True) if soup.title else ""))
    title = re.sub(r"\s+", " ", html.unescape(title)).strip()

    bar = soup.find(class_="datebar")
    stated = parse_date(bar.get_text(" ", strip=True) if bar else "")

    body = soup.find(id="main-content") or soup.body
    if body:
        body = BeautifulSoup(str(body), "html.parser")
        # Strip anything that is furniture rather than the work itself.
        for sel in ("script", "style", "nav", "svg"):
            for t in body.find_all(sel):
                t.decompose()
        for cls in ("footer", "skip-link"):
            for t in body.find_all(class_=cls):
                t.decompose()
        text = body.get_text("\n", strip=True)
    else:
        text = ""
    text = re.sub(r"\n{3,}", "\n\n", text)
    return title, stated, text


def quarter(d):
    return f"{d.year}-Q{(d.month - 1)//3 + 1}"


def main():
    for d in (DEP, BAT):
        os.makedirs(d, exist_ok=True)

    # Both directories are publicly served and separately authored, so both are
    # registrable text. concepts/ was missed on the first pass -- 26 primers that
    # are as original as the issues and cost nothing extra to include, since the
    # fee is per application rather than per work.
    sources = []
    for d, kind in ((PUB, "issue"), (os.path.join(REPO, "concepts"), "primer")):
        if os.path.isdir(d):
            sources += [(os.path.join(d, f), kind, os.path.relpath(d, REPO))
                        for f in sorted(os.listdir(d)) if f.endswith(".html")]

    rows = []
    for full, kind, srcdir in sources:
        path = os.path.basename(full)
        title, stated, text = extract(full)
        git_date = git_first_seen(full)
        pub = stated or git_date
        words = len(text.split())
        slug = path[:-5]

        note, conflict = [], False
        if not stated:
            # Primers are reference pages and carry no datebar by design, so
            # falling back to git is the expected path, not a problem to review.
            note.append("no datebar (by design for primers); date from git"
                        if kind == "primer" else "no date in datebar; used git")
            conflict = kind != "primer"
        elif git_date and abs((git_date - stated).days) > 2:
            note.append(f"datebar {stated} vs git {git_date}")
            conflict = True
        if words < MIN_WORDS:
            note.append("BELOW 50 words - INELIGIBLE for GRTX")
        if words > MAX_WORDS:
            note.append("OVER 17,500 words - INELIGIBLE for GRTX")

        # concepts/ and published/ could collide on a basename; keep them distinct
        dep = (slug if kind == "issue" else f"concept-{slug}") + ".txt"
        open(os.path.join(DEP, dep), "w", encoding="utf-8").write(text)
        rows.append(dict(title=title, filename=dep, source=f"{srcdir}/{path}",
                         kind=kind,
                         published=pub.isoformat() if pub else "",
                         words=words, quarter=quarter(pub) if pub else "",
                         eligible="yes" if MIN_WORDS <= words <= MAX_WORDS else "NO",
                         notes="; ".join(note), review="yes" if conflict else ""))

    rows.sort(key=lambda r: (r["published"], r["filename"]))
    with open(os.path.join(OUT, "manifest.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # ---- batch into applications: one quarter, split at the 50-work ceiling
    byq = defaultdict(list)
    for r in rows:
        if r["eligible"] == "yes":
            byq[r["quarter"]].append(r)

    batches = []
    for q in sorted(byq):
        chunk = byq[q]
        parts = [chunk[i:i+MAX_PER_APP] for i in range(0, len(chunk), MAX_PER_APP)]
        for i, part in enumerate(parts, 1):
            name = f"{q}" + (f"-{i}of{len(parts)}" if len(parts) > 1 else "")
            d = os.path.join(BAT, name)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "works.csv"), "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=["title", "filename", "published", "words"],
                                   extrasaction="ignore")
                w.writeheader(); w.writerows(part)
            with zipfile.ZipFile(os.path.join(d, "deposit.zip"), "w",
                                 zipfile.ZIP_DEFLATED) as z:
                for r in part:
                    z.write(os.path.join(DEP, r["filename"]), r["filename"])
            batches.append(dict(application=name, works=len(part),
                                earliest=part[0]["published"],
                                latest=part[-1]["published"], fee_usd=65))

    ineligible = [r for r in rows if r["eligible"] != "yes"]
    summary = dict(
        generated=date.today().isoformat(),
        issues_found=len(rows),
        eligible=len(rows) - len(ineligible),
        ineligible=[{k: r[k] for k in ("filename", "words", "notes")} for r in ineligible],
        applications=batches,
        total_fee_usd=sum(b["fee_usd"] for b in batches),
        needs_review=[{k: r[k] for k in ("filename", "published", "notes")}
                      for r in rows if r["review"]],
    )
    json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=1)

    print(f"{len(rows)} issues -> {len(rows)-len(ineligible)} GRTX-eligible")
    for b in batches:
        print(f"   {b['application']:<16} {b['works']:>3} works  "
              f"{b['earliest']} .. {b['latest']}   ${b['fee_usd']}")
    print(f"   {'TOTAL':<16} {summary['eligible']:>3} works  "
          f"{'':<24} ${summary['total_fee_usd']}")
    if ineligible:
        print(f"\n{len(ineligible)} INELIGIBLE:")
        for r in ineligible:
            print(f"   {r['filename']}  {r['words']} words  {r['notes']}")
    print(f"\n   dates from the printed datebar: "
          f"{sum(1 for r in rows if not r['notes'])}/{len(rows)}")
    if summary["needs_review"]:
        print(f"{len(summary['needs_review'])} dates needing human review:")
        for r in summary["needs_review"][:12]:
            print(f"   {r['filename']}  {r['notes']}")


if __name__ == "__main__":
    main()
