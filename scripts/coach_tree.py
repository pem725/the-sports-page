#!/usr/bin/env python3
"""Coaching DNA: do assistants of winners win?

For every coach whose FIRST major-college (FBS / CFBD-listed) head job began
1970-2025, find the job he held immediately before it -- school, role, level,
and the head coach he worked under -- then test whether coaches who came off a
winning boss's staff beat the program's prior-five-year baseline more often.

Sources, and only these:
  * data/almamater/all_tenures.csv and seasons.csv (already in the repo; built
    from CollegeFootballData coaching records for Issue #185). NO CFBD calls.
  * English Wikipedia, via the MediaWiki API: each coach's infobox "coaching
    career" list (body text used as a cross-check), and team-season pages
    ("2005 Denver Broncos season", "2022 Incarnate Word Cardinals football
    team") for bosses outside the FBS data.

Every page is cached under ~/.cache/sports-page/coachtree/.  Requests carry a
descriptive User-Agent, batch up to 50 titles, and wait >= 1.1 s between calls.
Re-running with a warm cache makes no network requests at all.

Usage:
  python3 scripts/coach_tree.py            # fetch (if needed), parse, analyze
  python3 scripts/coach_tree.py --offline  # cache only; fail if a page is missing
  python3 scripts/coach_tree.py --sample 15  # print a random hand-check sample

Outputs: data/coachtree/prior_jobs.csv, data/coachtree/coverage.txt,
         data/coachtree/analysis.txt, data/coachtree/morris_kinne.txt
"""
import argparse, csv, hashlib, json, math, pathlib, random, re, sys, time
import urllib.parse, urllib.request
from collections import defaultdict, Counter

REPO = pathlib.Path(__file__).resolve().parent.parent
AM = REPO / "data" / "almamater"
OUT = REPO / "data" / "coachtree"
CACHE = pathlib.Path.home() / ".cache" / "sports-page" / "coachtree"
PAGES = CACHE / "pages"
UA = ("TheSportsPage-research/1.0 (coach-tree study; https://thesportspage.net; "
      "ideas@thesportspage.net) python-urllib")
API = "https://en.wikipedia.org/w/api.php"
NOW = 2026  # "present" in an infobox
OFFLINE = False
_last_call = [0.0]

# ----------------------------------------------------------------- fetching
def _key(title):
    return hashlib.sha1(title.encode()).hexdigest()

def _api(params):
    if OFFLINE:
        raise RuntimeError("offline mode and a page is not cached: %s" % params.get("titles", "")[:80])
    wait = 1.1 - (time.time() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            _last_call[0] = time.time()
            return data
        except Exception as e:  # network hiccup or 429: back off
            print("  retry", attempt + 1, e, file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("Wikipedia API failed repeatedly")

def fetch(titles):
    """title -> {'title': final title after redirects, 'text': wikitext or None}.
    Same approach as data/almamater/scripts/wiki.py, but one cache file per page."""
    PAGES.mkdir(parents=True, exist_ok=True)
    out, todo = {}, []
    for t in dict.fromkeys(x for x in titles if x):
        f = PAGES / (_key(t) + ".json")
        if f.exists():
            out[t] = json.load(open(f))
        else:
            todo.append(t)
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        data = _api({"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
                     "redirects": "1", "format": "json", "formatversion": "2", "titles": "|".join(batch)})
        qd = data["query"]
        m = {t: t for t in batch}
        for key in ("normalized", "redirects"):
            for n in qd.get(key, []):
                for k, v in m.items():
                    if v == n["from"]:
                        m[k] = n["to"]
        pages = {p["title"]: p for p in qd.get("pages", [])}
        for t in batch:
            final = m[t].split("#")[0]
            p = pages.get(final) or pages.get(m[t])
            txt = None
            if p and not p.get("missing") and p.get("revisions"):
                txt = p["revisions"][0]["slots"]["main"].get("content")
            rec = {"requested": t, "title": final, "text": txt}
            json.dump(rec, open(PAGES / (_key(t) + ".json"), "w"))
            out[t] = rec
        print("  fetched %d/%d pages" % (min(i + 50, len(todo)), len(todo)), file=sys.stderr)
    return out

def resolve(titles):
    """Redirect-resolve link targets without downloading content."""
    f = CACHE / "redirects.json"
    store = json.load(open(f)) if f.exists() else {}
    todo = [t for t in dict.fromkeys(titles) if t and t not in store]
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        data = _api({"action": "query", "redirects": "1", "format": "json", "formatversion": "2",
                     "titles": "|".join(batch)})
        qd = data["query"]
        m = {t: t for t in batch}
        for key in ("normalized", "redirects"):
            for n in qd.get(key, []):
                for k, v in m.items():
                    if v == n["from"]:
                        m[k] = n["to"]
        for t in batch:
            store[t] = m[t].split("#")[0]
        json.dump(store, open(f, "w"))
    return {t: store.get(t, t) for t in titles}

# ------------------------------------------------------------------ parsing
def infobox(text):
    """Return (template name, {field: value}) for the first infobox."""
    i = text.find("{{Infobox")
    if i < 0:
        return None, {}
    depth, j = 0, i
    while j < len(text):
        if text.startswith("{{", j):
            depth += 1; j += 2; continue
        if text.startswith("}}", j):
            depth -= 1; j += 2
            if depth == 0:
                break
            continue
        j += 1
    box = text[i:j]
    name = re.match(r"\{\{Infobox\s*([^\n|]*)", box).group(1).strip()
    f = {}
    for m in re.finditer(r"\n\s*\|\s*([A-Za-z_0-9 ]+?)\s*=(.*?)(?=\n\s*\|\s*[A-Za-z_0-9 ]+?\s*=|\n?\}\}$)", box, re.S):
        f[m.group(1).strip()] = m.group(2).strip()
    return name, f

def body_of(text):
    i = text.find("{{Infobox")
    if i < 0:
        return text
    depth, j = 0, i
    while j < len(text):
        if text.startswith("{{", j):
            depth += 1; j += 2; continue
        if text.startswith("}}", j):
            depth -= 1; j += 2
            if depth == 0:
                break
            continue
        j += 1
    return text[j:]

LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]")

def clean(s):
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"<ref[^>]*/>|<ref.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"\{\{\s*efn.*?\}\}|\{\{\s*refn.*?\}\}|\{\{\s*sfn.*?\}\}", "", s, flags=re.S | re.I)
    # year templates: {{nfly|1979}}, {{NFL Year|1981}}, {{NFL Year|2013|2015}}, {{CFL Year|2016}}
    s = re.sub(r"\{\{\s*[A-Za-z ]*?(?:y|year)\s*\|\s*(\d{4})\s*\|\s*(\d{4})[^}]*\}\}", r"\1–\2", s, flags=re.I)
    s = re.sub(r"\{\{\s*[A-Za-z ]*?(?:y|year)\s*\|\s*(\d{4})[^}]*\}\}", r"\1", s, flags=re.I)
    s = s.replace("&ndash;", "–").replace("&nbsp;", " ")
    return s.strip()

def disp(s):
    """Wikitext -> display text."""
    s = LINK.sub(lambda m: (m.group(2) or m.group(1)), s)
    s = re.sub(r"\{\{.*?\}\}", "", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", s).strip()

def years(span):
    span = span.replace("—", "–").replace("-", "–")
    ys = [int(y) for y in re.findall(r"(?<!\d)(1[89]\d\d|20\d\d)(?!\d)", span)]
    if not ys:
        return None, None
    start = ys[0]
    end = ys[-1]
    m2 = re.search(r"(1[89]\d\d|20\d\d)\s*–\s*(\d{2})(?!\d)", span)
    if len(ys) == 1 and m2:
        end = int(str(start)[:2] + m2.group(2))
    if re.search(r"present|current", span, re.I):
        end = NOW
    return start, max(end, start)

def coaching_rows(fields):
    """List of dicts: start, end, team_wikitext, link, display, role_text, raw."""
    rows = []
    # Format 1: Infobox college coach -- coach_yearsN / coach_teamN
    idx = sorted({int(m.group(1)) for k in fields for m in [re.fullmatch(r"coach_team(\d+)", k)] if m})
    for n in idx:
        team = clean(fields.get("coach_team%d" % n, ""))
        span = clean(fields.get("coach_years%d" % n, ""))
        if not team:
            continue
        rows.append(_row(team, span, fmt="college"))
    if rows:
        return rows, "coach_teamN"
    # Format 2: bulleted lists (Infobox gridiron/NFL biography). Handles "**" sub-bullets and
    # {{ubl|...}} lists, where the first item is the team and later items are "Role (years)".
    ROLEWORD = re.compile(r"coach|coordinator|assistant|analyst|intern|director|consultant|quality control|"
                          r"graduate|specialist|head coach|\bHC\b", re.I)
    for key in ("pastcoaching", "coaching_teams", "coachteams", "coach_teams", "coaching"):
        v = fields.get(key)
        if not v:
            continue
        v = clean(v)
        v = re.sub(r"\{\{\s*(?:ubl|unbulleted list|plainlist|plain list)\s*\|", "\n* ", v, flags=re.I)
        v = re.sub(r"\}\}", "", v)
        items = []
        for line in v.split("\n"):
            for part in re.split(r"\|(?![^\[]*\]\])", line):
                part = part.strip()
                if part:
                    items.append(part)
        header = None
        for it in items:
            it = it.lstrip("*").strip()
            m = re.match(r"(.*?)\(([^()]*\d{4}[^()]*)\)(.*)", it, re.S)
            if not m:
                continue
            team, span, role = m.group(1), m.group(2), m.group(3)
            role = re.sub(r"^\s*<br\s*/?>", "", role.strip(), flags=re.I)
            role = re.split(r"<br\s*/?>", role, flags=re.I)[0]
            is_sub = header is not None and not LINK.search(team) and ROLEWORD.search(disp(team)) \
                and not re.search(r"high school|university|college", team, re.I)
            if is_sub:
                r = dict(header)
                s_, e_ = years(span)
                r.update(start=s_, end=e_, span=span, role_text=disp(team), sub=True)
                if header.get("_has_sub") is False and rows and rows[-1] is header:
                    rows.pop()  # replace the header row by its sub-rows
                header["_has_sub"] = True
                rows.append(r)
            else:
                r = _row(team.strip(), span, fmt="bullets")
                r["role_text"] = disp(role)
                r["_has_sub"] = False
                header = r
                rows.append(r)
        if rows:
            return rows, key
    return rows, None

STATES = set("AL AK AZ AR CA CO CT FL HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND "
             "OH OK OR PA RI SC SD TN TX UT VT WA WV WI WY Ohio Florida California Pennsylvania Texas Minnesota "
             "Indiana Kentucky Maryland Virginia".split())
AMBIG = {"GA", "DE"}  # Georgia / graduate assistant; Delaware / defensive end

def _split_role(text):
    """'Miami (OH) (DC)' -> ('Miami (OH)', 'DC'); 'Athens Christian (GA)' -> ('Athens Christian (GA)', '')
    when GA is the only group and the team looks like a school name, else role GA."""
    groups = list(re.finditer(r"\(([^()]*)\)", text))
    if not groups:
        return text.strip(), ""
    team = text[:groups[0].start()].strip()
    rest = []
    for i, g in enumerate(groups):
        c = g.group(1).strip()
        last = i == len(groups) - 1
        if not rest and (c in STATES or (c in AMBIG and not last)):
            team += " (%s)" % c
        elif not rest and c in AMBIG and last and re.search(r"\bHS\b|High|School|Christian|Academy|Prep", team):
            team += " (%s)" % c
        else:
            rest.append(c)
    return team, (rest[-1] if rest else "")

def _row(team, span, fmt):
    s, e = years(span)
    t = team.strip()
    lm = LINK.match(t)
    if lm:
        link = lm.group(1).strip()
        head = disp(lm.group(0))
        tail = disp(t[lm.end():])
        extra, role = _split_role("X " + tail) if tail else ("X", "")
        team_disp = head + extra[1:]
    else:
        link = None
        team_disp, role = _split_role(disp(t))
    if fmt != "college":
        role = ""
    return dict(start=s, end=e, span=span, raw=team, link=link,
                display=team_disp.strip(" ,"), role_text=role, fmt=fmt)

# ---------------------------------------------------------- classification
NFL_CITIES = (r"Arizona|Atlanta|Baltimore|Boston|Buffalo|Carolina|Chicago|Cincinnati|Cleveland|Dallas|Denver|"
              r"Detroit|Green Bay|Houston|Indianapolis|Jacksonville|Kansas City|Las Vegas|Los Angeles|Miami|"
              r"Minnesota|New England|New Orleans|New York|Oakland|Philadelphia|Phoenix|Pittsburgh|San Diego|"
              r"San Francisco|Seattle|St\. Louis|Tampa Bay|Tennessee|Washington")
NFL_NICK = (r"Cardinals|Falcons|Ravens|Colts|Patriots|Bills|Panthers|Bears|Bengals|Browns|Cowboys|Texans|Broncos|"
            r"Lions|Packers|Oilers|Jaguars|Chiefs|Raiders|Rams|Chargers|Dolphins|Vikings|Saints|Giants|Jets|"
            r"Eagles|Steelers|49ers|Seahawks|Buccaneers|Titans|Redskins|Commanders|Football Team")
NFL_RE = re.compile(r"^(%s) (%s)( \(NFL\)| \(football\))?$" % (NFL_CITIES, NFL_NICK))
PRO_OTHER_RE = re.compile(r"CFL|Canadian Football|USFL|XFL|World League|NFL Europe|Arena Football|AFL\)|"
                          r"Argonauts|Alouettes|Tiger-Cats|Roughriders|Stampeders|Eskimos|Elks|Blue Bombers|"
                          r"BC Lions|Redblacks|Rough Riders|Renegades|Barcelona Dragons|Frankfurt Galaxy|"
                          r"Rhein Fire|Amsterdam Admirals|Scottish Claymores|Berlin Thunder|Cologne Centurions|"
                          r"London Monarchs|UFL|Alliance of American Football|Spring League|United Football League|"
                          r"Stars\b|Outlaws|Breakers|Bandits|Gamblers|Generals\b|Express\b|Blitz|Wranglers|"
                          r"Invaders|Federals|Showboats|Maulers|Stallions|Gunslingers|VooDoo|Cobras|Arena", re.I)
HS_RE = re.compile(r"high school|\bHS\b|academy\b(?!.*football)|prep\b|catholic\b|preparatory", re.I)

def role_class(role, fmt):
    r = role.lower()
    if fmt == "college" and not r.strip():
        return "HC"
    if re.search(r"interim|acting", r) and ("hc" in r or "head coach" in r):
        return "interim HC"
    if re.search(r"(?<!assistant )(?<!associate )(?<!a)\bhead coach\b|^hc\b|\bhc\b", r) and not re.search(r"\bahc\b|assistant head|associate head", r):
        return "HC"
    if re.search(r"\b(co-?\s*)?(oc|dc)\b|offensive coordinator|defensive coordinator", r):
        return "coordinator"
    if re.search(r"\bga\b|graduate assistant|analyst|\boa\b|\bda\b|quality control|\bqc\b|volunteer|intern|"
                 r"student assistant|director|recruiting coordinator|\brc\b|consultant|aoqc", r):
        return "support"
    if r.strip():
        return "position"
    return "unknown"

def norm(s):
    return re.sub(r"\s+", " ", s.replace("–", "-").replace("’", "'")).strip().lower()

# ------------------------------------------------------------------- data
def pct(w, l, t):
    g = w + l + t
    return (w + 0.5 * t) / g if g else None

def parse_record(s):
    s = disp(clean(s or "")).replace("-", "–")
    m = re.search(r"(\d+)\s*–\s*(\d+)(?:\s*–\s*(\d+))?", s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)

def load_repo():
    T = list(csv.DictReader(open(AM / "all_tenures.csv")))
    S = list(csv.DictReader(open(AM / "seasons.csv")))
    for r in S:
        for k in ("cid", "year", "games", "w", "l", "t"):
            r[k] = int(r[k])
    canon = json.load(open(AM / "canon.json"))
    return T, S, canon

# --------------------------------------------------------------- the build
def build():
    T, S, canon = load_repo()
    by = defaultdict(list)
    for r in T:
        by[r["cid"]].append(r)
    firsts = []
    for cid, v in by.items():
        f = min(v, key=lambda r: (int(r["first_year"]), r["school"]))
        if 1970 <= int(f["first_year"]) <= 2025:
            firsts.append(f)
    firsts.sort(key=lambda r: (int(r["first_year"]), r["school"]))
    print("first FBS head jobs 1970-2025:", len(firsts), file=sys.stderr)

    sy = defaultdict(list)  # (school, year) -> season rows
    for r in S:
        sy[(r["school"], r["year"])].append(r)
    fbs_schools = {r["school"] for r in S}
    canon_rev = {}
    for s, c in canon.items():
        if c:
            canon_rev[c] = s
    alias = {norm(s): s for s in fbs_schools}
    # plain-text names, copied from data/almamater/scripts/parse.py ALIAS plus a few found here
    alias.update({"north carolina state": "NC State", "n.c. state": "NC State", "mississippi": "Ole Miss",
        "southern california": "USC", "pitt": "Pittsburgh", "louisiana state": "LSU", "miami (fl)": "Miami",
        "miami (florida)": "Miami", "miami (oh)": "Miami (OH)", "miami (ohio)": "Miami (OH)", "brigham young": "BYU",
        "texas christian": "TCU", "southern methodist": "SMU", "connecticut": "UConn", "central florida": "UCF",
        "southern mississippi": "Southern Miss", "appalachian state": "App State", "hawaii": "Hawai'i",
        "san jose state": "San José State", "texas-el paso": "UTEP", "alabama-birmingham": "UAB",
        "nevada-las vegas": "UNLV", "west point": "Army", "naval academy": "Navy", "memphis state": "Memphis",
        "north texas state": "North Texas", "southwest texas state": "Texas State", "southwestern louisiana": "Louisiana",
        "northeast louisiana": "UL Monroe", "louisiana-monroe": "UL Monroe", "louisiana-lafayette": "Louisiana",
        "fiu": "Florida International", "umass": "Massachusetts", "pacific (ca)": "Pacific", "ole miss": "Ole Miss",
        "lsu": "LSU", "usc": "USC", "middle tennessee state": "Middle Tennessee", "fau": "Florida Atlantic",
        "louisiana tech": "Louisiana Tech", "texas a&m": "Texas A&M", "virginia tech": "Virginia Tech"})
    names = {r["cid"]: "%s %s" % (r["first"], r["last"]) for r in S}

    pages = fetch([r["wiki"] for r in firsts if r["wiki"]])
    parsed = {}
    links = set()
    for r in firsts:
        p = pages.get(r["wiki"]) if r["wiki"] else None
        text = p["text"] if p else None
        if not text:
            parsed[r["cid"]] = None; continue
        name, f = infobox(text)
        rows, fmt = coaching_rows(f)
        for x in rows:
            if x["link"]:
                links.add(x["link"])
        parsed[r["cid"]] = dict(text=text, box=name, rows=rows, fmt=fmt, title=p["title"])
    res = resolve(sorted(links))

    def school_of(row, page_rows, year):
        """Map an infobox row to (cfbd_school or None, resolved_link_or_None)."""
        tgt = res.get(row["link"], row["link"]) if row["link"] else None
        if not tgt:  # plain text: borrow a link with the same display text elsewhere in the list
            for o in page_rows:
                if o["link"] and norm(o["display"]) == norm(row["display"]):
                    tgt = res.get(o["link"], o["link"]); break
        if not tgt and NFL_RE.match(row["display"]):
            tgt = row["display"]
        sch = None
        if tgt:
            sch = canon_rev.get(tgt) or canon_rev.get(tgt + " football") or \
                (canon_rev.get(tgt[:-9]) if tgt.endswith(" football") else None)
        if not sch:
            d = norm(row["display"].split(" / ")[0])
            sch = alias.get(d) or alias.get(norm(row["display"]))
            if sch and tgt and not tgt.endswith(" football") and tgt not in canon_rev:
                # a linked page that is not a college football program (e.g. an NFL club named like a school)
                if NFL_RE.match(tgt) or PRO_OTHER_RE.search(tgt):
                    sch = None
        return sch, tgt

    def level_of(row, sch, tgt, year):
        label = tgt or row["display"]
        if sch:
            return "FBS" if (sch, year) in sy else "nonFBS-college"
        if tgt and NFL_RE.match(tgt):
            return "NFL"
        if PRO_OTHER_RE.search(label) or PRO_OTHER_RE.search(row["display"]):
            return "pro-other"
        if HS_RE.search(label) or HS_RE.search(row["display"]):
            return "HS"
        if tgt and (tgt.endswith(" football") or re.search(r"University|College|Institute|State", tgt)):
            return "nonFBS-college"
        if not tgt and re.search(r"University|College|State|Tech", row["display"]):
            return "nonFBS-college"
        if row["fmt"] == "college" and tgt:
            return "nonFBS-college?"  # a linked program in a college-coach infobox that is not FBS/NFL/pro/HS
        return "unknown"

    out = []
    season_titles = {}
    pending = []  # rows that need a Wikipedia team-season lookup for the boss
    for r in firsts:
        cid = int(r["cid"])
        hc_school, hc_year = r["school"], int(r["first_year"])
        base = dict(coach=r["coach"], cid=cid, first_hc_school=hc_school, first_hc_year=hc_year,
                    prior_school="", prior_level="", prior_role="", boss="", boss_win_pct_during="",
                    parse_confidence="low", source_note="", prior_years="", prior_role_class="",
                    first_hc_interim="", gap_years="", boss_seasons="", wiki=r["wiki"],
                    first_hc_seasons=r["seasons"], first_hc_win_pct=r["win_pct"],
                    prior5_pct=r["prior5_pct"], change_vs_prior5=r["change_vs_prior5"])
        P = parsed.get(r["cid"])
        if P is None:
            base["source_note"] = "no Wikipedia page matched in all_tenures" if not r["wiki"] else "Wikipedia page missing"
            out.append(base); continue
        rows = P["rows"]
        if not rows:
            base["source_note"] = "infobox (%s) has no coaching-career list" % (P["box"] or "none")
            out.append(base); continue
        flags = []
        # a one-season first tenure of <= 4 games is an interim/bowl stint whatever the infobox says
        g1 = sum(x["games"] for x in sy.get((hc_school, hc_year), []) if x["cid"] == cid)
        if int(r["seasons"]) == 1 and g1 <= 4:
            base["first_hc_interim"] = "yes"
            flags.append("first FBS head job is an interim stint (%d games in data)" % g1)
        for x in rows:
            x["school"], x["tgt"] = school_of(x, rows, x["start"] or 0)
        # 1) locate the first FBS head job in the infobox
        cand = [i for i, x in enumerate(rows) if x["school"] == hc_school and x["start"]
                and x["start"] <= hc_year <= (x["end"] or x["start"])]
        if not cand:
            cand = [i for i, x in enumerate(rows) if x["school"] == hc_school and x["start"]
                    and abs(x["start"] - hc_year) <= 1]
            if cand:
                flags.append("HC row matched within 1 yr (infobox %s vs data %d)" % (rows[cand[0]]["span"], hc_year))
        if not cand:
            base["source_note"] = "infobox: could not find %s %d row" % (hc_school, hc_year)
            out.append(base); continue
        hcs = [i for i in cand if role_class(rows[i]["role_text"], rows[i]["fmt"]) in ("HC", "interim HC")]
        if not hcs:
            # CFBD often credits a bowl game to the incoming coach, so the infobox HC row can start a year later
            near = [i for i, x in enumerate(rows) if x["school"] == hc_school and x["start"]
                    and abs(x["start"] - hc_year) <= 1 and role_class(x["role_text"], x["fmt"]) in ("HC", "interim HC")]
            if near:
                hcs = near[:1]
                flags.append("HC row starts %s, data first year %d" % (rows[near[0]]["start"], hc_year))
        hi = (hcs or cand)[0]
        hrow = rows[hi]
        hrc = role_class(hrow["role_text"], hrow["fmt"])
        if hrc not in ("HC", "interim HC", "unknown"):
            flags.append("matched HC row has role '%s'" % hrow["role_text"])
        if hrc == "interim HC" or re.search(r"interim|acting", hrow["role_text"], re.I):
            if int(r["seasons"]) <= 1:
                if base["first_hc_interim"] != "yes":
                    flags.append("first FBS head job is an interim stint")
                base["first_hc_interim"] = "yes"
            else:
                base["first_hc_interim"] = "then permanent"
        hstart = hrow["start"]
        if hstart < hc_year - 1:
            flags.append("head tenure began %d, before the program appears as FBS in the data (%d)" % (hstart, hc_year))
        # 2) the row immediately before it
        pi = hi - 1
        while pi >= 0 and rows[pi]["start"] is None:
            pi -= 1
        order_ok = pi >= 0 and rows[pi]["start"] <= hstart
        if not order_ok:
            earlier = [i for i, x in enumerate(rows) if i != hi and x["start"] and x["start"] < hstart]
            if not earlier:
                base["source_note"] = "infobox: no coaching row before first head job (first listed job)"
                base["prior_role"] = "none listed"
                out.append(base); continue
            pi = max(earlier, key=lambda i: (rows[i]["end"] or 0, rows[i]["start"], i))
            flags.append("infobox rows out of order; prior chosen by year")
        prow = rows[pi]
        pend = min(prow["end"] or prow["start"], max(hstart - 1, prow["start"]))
        gap = hstart - (prow["end"] or prow["start"])
        base["gap_years"] = gap
        if gap > 1:
            flags.append("gap of %d yrs between prior job and head job" % gap)
        sch, tgt = prow["school"], prow["tgt"]
        lvl = level_of(prow, sch, tgt, pend)
        prc = role_class(prow["role_text"], prow["fmt"])
        if prow["fmt"] == "college" and prc == "HC" and lvl in ("NFL", "pro-other", "HS", "unknown"):
            prc = "HC"
        base.update(prior_school=sch or (tgt or prow["display"]), prior_level=lvl,
                    prior_role=prow["role_text"] or ("HC (unlabeled row)" if prow["fmt"] == "college" else ""),
                    prior_role_class=prc, prior_years="%s-%s" % (prow["start"], prow["end"]))
        if prc == "unknown":
            flags.append("role not stated")
        if "interim" in prow["role_text"].lower():
            flags.append("prior job is an interim head-coach stint")
        if lvl == "unknown":
            flags.append("level not identified")
        if lvl == "nonFBS-college?":
            lvl = "nonFBS-college"; base["prior_level"] = lvl
            flags.append("level inferred (linked program, not FBS/NFL/pro/HS)")
        # 3) the boss
        yrs = list(range(prow["start"], pend + 1))
        boss_note = ""
        if prc in ("HC", "interim HC") and "interim" not in prow["role_text"].lower():
            base["boss"] = "(none: he was head coach)"
        elif lvl == "FBS":
            last = yrs[-1]
            cs = [x for x in sy.get((sch, last), []) if x["cid"] != cid]
            if not cs and len(yrs) > 1:  # the data credits that year to him (bowl game): use the year before
                yrs = yrs[:-1]; last = yrs[-1]
                cs = [x for x in sy.get((sch, last), []) if x["cid"] != cid]
            if not cs:
                flags.append("no FBS head coach found for %s %d" % (sch, last))
            else:
                b = max(cs, key=lambda x: x["games"])
                if len(cs) > 1:
                    flags.append("two head coaches at %s in %d; took %s (more games)" % (sch, last, names[b["cid"]]))
                w = l = t = 0; n = 0
                for y in yrs:
                    for x in sy.get((sch, y), []):
                        if x["cid"] == b["cid"]:
                            w += x["w"]; l += x["l"]; t += x["t"]; n += 1
                base["boss"] = names[b["cid"]]
                base["boss_cid"] = b["cid"]
                base["boss_win_pct_during"] = round(pct(w, l, t), 3)
                base["boss_seasons"] = n
                boss_note = "boss from repo seasons.csv"
        elif lvl in ("NFL", "nonFBS-college") and tgt:
            pending.append((base, tgt, yrs, lvl))
        base["_flags"] = flags
        base["_P"] = P
        base["_prow"] = prow
        base["_boss_note"] = boss_note
        out.append(base)

    # 4) team-season pages for NFL and non-FBS bosses
    def season_title(tgt, y, lvl):
        if lvl == "NFL":
            return "%d %s season" % (y, re.sub(r" \((NFL|football)\)$", "", tgt))
        stem = tgt[:-9] if tgt.endswith(" football") else tgt
        return "%d %s football team" % (y, stem)
    want = [season_title(tgt, y, lvl) for _, tgt, yrs, lvl in pending for y in yrs]
    sp = fetch(want)
    for base, tgt, yrs, lvl in pending:
        recs = []
        for y in yrs:
            p = sp.get(season_title(tgt, y, lvl))
            if not p or not p["text"]:
                recs.append((y, None, None)); continue
            _, f = infobox(p["text"])
            c = f.get("head_coach") or f.get("coach") or ""
            lm = LINK.search(clean(c))
            coach = disp(lm.group(2) or lm.group(1)) if lm else disp(clean(c))
            coach = re.sub(r"\s*\(.*?\)", "", coach).strip()
            multi = len(LINK.findall(clean(c))) > 1
            recs.append((y, coach or None, parse_record(f.get("record")), multi))
        last = recs[-1]
        if last[1] is None:
            base["_flags"].append("no %s season page for %d; boss unresolved" % (lvl, yrs[-1]))
            base["_boss_note"] = "season page '%s' not found" % season_title(tgt, yrs[-1], lvl)
            continue
        boss = last[1]
        if boss and base["coach"].split()[-1] in boss and base["coach"].split()[0] in boss:
            base["_flags"].append("season page lists the coach himself as head coach")
            continue
        w = l = t = 0; n = 0
        for rec in recs:
            if rec[1] == boss and rec[2]:
                w += rec[2][0]; l += rec[2][1]; t += rec[2][2]; n += 1
        if len(last) > 3 and last[3]:
            base["_flags"].append("season page lists more than one head coach in %d; took first" % yrs[-1])
        base["boss"] = boss
        if n:
            base["boss_win_pct_during"] = round(pct(w, l, t), 3)
            base["boss_seasons"] = n
        else:
            base["_flags"].append("boss record not parsed")
        base["_boss_note"] = "boss from Wikipedia '%s' infobox" % season_title(tgt, yrs[-1], lvl)

    # 5) body-text cross-check and confidence
    for b in out:
        if "_P" not in b:
            continue
        P, prow, flags = b.pop("_P"), b.pop("_prow"), b.pop("_flags")
        body = body_of(P["text"])
        bdisp = disp(clean(body))
        keys = {prow["display"]}
        if prow["tgt"]:
            keys.add(prow["tgt"]); keys.add(re.sub(r" football$", "", prow["tgt"]))
        if b["prior_school"]:
            keys.add(b["prior_school"])
        keys = {k for k in keys if k and len(k) > 2}
        sents = [s for s in re.split(r"(?<=[.!?])\s+", bdisp) if any(k in s for k in keys)]
        sents += [s for s in re.split(r"(?<=[.!?])\s+", body) if prow["tgt"] and prow["tgt"] in s]
        body_note = ""
        if not sents:
            flags.append("body text does not mention prior school")
            body_note = "body: prior school not mentioned"
        else:
            ys = {int(y) for s in sents for y in re.findall(r"(?<!\d)(19\d\d|20\d\d)(?!\d)", s)}
            span = set(range(prow["start"] - 1, (prow["end"] or prow["start"]) + 2))
            if ys and not ys & span:
                flags.append("body years %s do not overlap infobox %s" % (sorted(ys)[:4], prow["span"]))
                body_note = "body: mentions school, years disagree"
            else:
                body_note = "body: corroborates school" + (" and years" if ys & span else "")
            if b["boss"] and not b["boss"].startswith("(") and b["boss"].split()[-1] in " ".join(sents):
                body_note += " and boss"
        need_boss = b["prior_role_class"] not in ("HC",) and b["prior_level"] in ("FBS", "NFL", "nonFBS-college")
        info_only = ("first FBS head job is an interim", "HC row starts", "two head coaches at", "head tenure began")
        serious = [f for f in flags if not f.startswith(info_only)]
        if need_boss and b["boss_win_pct_during"] == "":
            serious.append("boss win% missing")
        b["parse_confidence"] = "high" if not serious else ("med" if len(serious) <= 2 else "low")
        if any(f.startswith("infobox rows out of order") or f.startswith("level not") for f in flags) and len(serious) >= 2:
            b["parse_confidence"] = "low"
        src = "infobox (%s, %s) row '%s %s'" % (P["box"], P["fmt"], disp(prow["raw"])[:60], prow["span"])
        parts = [src, body_note, b.pop("_boss_note", "")] + flags
        b["source_note"] = "; ".join(p for p in parts if p)
    return out

COLS = ["coach", "cid", "first_hc_school", "first_hc_year", "prior_school", "prior_level", "prior_role",
        "boss", "boss_win_pct_during", "parse_confidence", "source_note",
        # extras for the analysis and for auditing
        "prior_years", "prior_role_class", "first_hc_interim", "gap_years", "boss_seasons", "wiki",
        "first_hc_seasons", "first_hc_win_pct", "prior5_pct", "change_vs_prior5"]

# ---------------------------------------------------------------- analysis
def sig2(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    if x == 0:
        return "0"
    v = float("%.2g" % x)
    d = max(0, 1 - int(math.floor(math.log10(abs(v)))))
    return "%.*f" % (d, v)

def pts(x):
    """win-percentage difference (a fraction) -> signed points, 2 sig figs."""
    s = sig2(100 * x)
    return ("+" if x > 0 else "") + s

def boot_ci(a, b, rng, n=10000):
    import numpy as np
    a, b = np.asarray(a), np.asarray(b)
    da = rng.choice(a, (n, len(a))).mean(1); db = rng.choice(b, (n, len(b))).mean(1)
    d = da - db
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))

def perm_p(a, b, rng, n=10000):
    import numpy as np
    x = np.concatenate([a, b]); k = len(a); obs = abs(np.mean(a) - np.mean(b))
    hits = 0
    for _ in range(n):
        rng.shuffle(x)
        if abs(x[:k].mean() - x[k:].mean()) >= obs - 1e-12:
            hits += 1
    return (hits + 1) / (n + 1)

def compare(label, a, b, rng, L, unit="pts"):
    import numpy as np
    a = np.array(a, float); b = np.array(b, float)
    if len(a) < 5 or len(b) < 5:
        L.append("  %-44s n=%d vs %d -- too few to test" % (label, len(a), len(b))); return None
    d = a.mean() - b.mean(); lo, hi = boot_ci(a, b, rng); p = perm_p(a, b, rng)
    if unit == "pts":
        L.append("  %-44s n=%d vs %d | means %s vs %s pts | diff %s pts (95%% CI %s to %s) | perm p=%s" % (
            label, len(a), len(b), pts(a.mean()), pts(b.mean()), pts(d), pts(lo), pts(hi), sig2(p)))
    else:
        L.append("  %-44s n=%d vs %d | means %s%% vs %s%% | diff %s pts (95%% CI %s to %s) | perm p=%s" % (
            label, len(a), len(b), sig2(100 * a.mean()), sig2(100 * b.mean()), pts(d), pts(lo), pts(hi), sig2(p)))
    return d, lo, hi, p

def ols_adjusted(rows, cut, rng, n=5000):
    """win% = a + b*prior5 + c*[boss>=cut]; bootstrap CI for c."""
    import numpy as np
    y = np.array([float(r["first_hc_win_pct"]) for r in rows])
    p5 = np.array([float(r["prior5_pct"]) for r in rows])
    g = np.array([float(r["boss_win_pct_during"]) >= cut for r in rows], float)
    X = np.column_stack([np.ones_like(y), p5, g])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    bs = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        bs.append(np.linalg.lstsq(X[i], y[i], rcond=None)[0][2])
    return beta[2], np.percentile(bs, 2.5), np.percentile(bs, 97.5), beta[1]

def stratified(rows, cut, rng, n=5000, k=5):
    """Difference in first-job win% within prior-5 quintiles, weighted by stratum size."""
    import numpy as np
    p5 = np.array([float(r["prior5_pct"]) for r in rows]); y = np.array([float(r["first_hc_win_pct"]) for r in rows])
    g = np.array([float(r["boss_win_pct_during"]) >= cut for r in rows])
    edges = np.quantile(p5, np.linspace(0, 1, k + 1)); st = np.clip(np.searchsorted(edges, p5, side="right") - 1, 0, k - 1)
    def est(idx):
        tot = 0; wsum = 0
        for q in range(k):
            m = idx[st[idx] == q]
            a = y[m][g[m]]; b = y[m][~g[m]]
            if len(a) and len(b):
                tot += len(m) * (a.mean() - b.mean()); wsum += len(m)
        return tot / wsum
    allidx = np.arange(len(y)); d = est(allidx)
    bs = [est(rng.integers(0, len(y), len(y))) for _ in range(n)]
    return d, np.percentile(bs, 2.5), np.percentile(bs, 97.5)

def analyze(out):
    import numpy as np
    rng = np.random.default_rng(20261029)
    L = []
    hi = [r for r in out if r["parse_confidence"] == "high"]
    L.append("COACHING DNA -- do assistants of winners win?  (scripts/coach_tree.py)")
    L.append("Universe: first major-college head job (CFBD/FBS records) beginning 1970-2025.")
    L.append("Outcome: first head job's win% minus the program's win% over the 5 seasons before the hire")
    L.append("(the Issue #185 baseline). Differences are in percentage points. 2 significant digits.")
    L.append("Bootstrap 95% CIs (10,000 resamples); two-sided permutation p (10,000 shuffles); seed 20261029.")
    L.append("Change scores assume a prior-5 slope of 1; the OLS and quintile-match lines do not (fitted slope")
    L.append("is printed), which matters because winners' assistants inherit better programs.\n")

    def usable(rows, need_boss=True):
        return [r for r in rows if r["prior5_pct"] != "" and r["first_hc_win_pct"] != ""
                and r["first_hc_interim"] != "yes"
                and (not need_boss or (r["boss_win_pct_during"] != ""))]
    base = usable(hi)
    L.append("Main sample: high-confidence rows with a boss record, a prior-5 baseline, not interim: n=%d" % len(base))
    L.append("(excluded: %d high-confidence rows whose prior job was itself a head job or HS/pro-other with no boss record)\n"
             % len([r for r in hi if r["boss_win_pct_during"] == ""]))

    for cut in (0.650, 0.700, 0.750):
        a = [r for r in base if float(r["boss_win_pct_during"]) >= cut]
        b = [r for r in base if float(r["boss_win_pct_during"]) < cut]
        L.append("CUT: boss won %s or better during the assistant's stint" % ("%.3f" % cut).lstrip("0"))
        compare("change vs prior 5, winner's staff vs others", [float(r["change_vs_prior5"]) for r in a],
                [float(r["change_vs_prior5"]) for r in b], rng, L)
        compare("raw win%, winner's staff vs others", [float(r["first_hc_win_pct"]) for r in a],
                [float(r["first_hc_win_pct"]) for r in b], rng, L, unit="pct")
        compare("prior-5 baseline inherited ('better jobs')", [float(r["prior5_pct"]) for r in a],
                [float(r["prior5_pct"]) for r in b], rng, L, unit="pct")
        c, lo, hi_, slope = ols_adjusted(base, cut, rng)
        L.append("  %-44s coef %s pts (95%% CI %s to %s); prior-5 slope %s" % (
            "OLS win% ~ prior5 + winner's staff", pts(c), pts(lo), pts(hi_), sig2(slope)))
        d, lo, hi_ = stratified(base, cut, rng)
        L.append("  %-44s diff %s pts (95%% CI %s to %s)" % ("same-baseline match (prior-5 quintiles)", pts(d), pts(lo), pts(hi_)))
        # everyone else, including prior head coaches and HS/pro hires with no boss
        allr = usable(hi, need_boss=False)
        a2 = [r for r in allr if r["boss_win_pct_during"] != "" and float(r["boss_win_pct_during"]) >= cut]
        b2 = [r for r in allr if not (r["boss_win_pct_during"] != "" and float(r["boss_win_pct_during"]) >= cut)]
        compare("vs ALL other hires (incl. no boss)", [float(r["change_vs_prior5"]) for r in a2],
                [float(r["change_vs_prior5"]) for r in b2], rng, L)
        L.append("")

    L.append("SENSITIVITY (cut .700)")
    medhi = usable([r for r in out if r["parse_confidence"] in ("high", "med")])
    for lab, rows in (("high+med confidence", medhi),
                      ("high, first job lasted >= 3 seasons", [r for r in base if int(r["first_hc_seasons"]) >= 3]),
                      ("high, hired 1990-2025", [r for r in base if int(r["first_hc_year"]) >= 1990]),
                      ("high, boss on staff >= 2 seasons", [r for r in base if r["boss_seasons"] and int(r["boss_seasons"]) >= 2])):
        a = [float(r["change_vs_prior5"]) for r in rows if float(r["boss_win_pct_during"]) >= .7]
        b = [float(r["change_vs_prior5"]) for r in rows if float(r["boss_win_pct_during"]) < .7]
        compare(lab, a, b, rng, L)
    L.append("")

    L.append("BY PRIOR ROLE (high confidence, prior-5 baseline, not interim)")
    allr = usable(hi, need_boss=False)
    co = [r for r in allr if r["prior_role_class"] == "coordinator"]
    po = [r for r in allr if r["prior_role_class"] == "position"]
    compare("coordinators vs position coaches: change", [float(r["change_vs_prior5"]) for r in co],
            [float(r["change_vs_prior5"]) for r in po], rng, L)
    compare("coordinators vs position coaches: raw win%", [float(r["first_hc_win_pct"]) for r in co],
            [float(r["first_hc_win_pct"]) for r in po], rng, L, unit="pct")
    for lab, grp in (("coordinators only", co), ("position coaches only", po)):
        g = [r for r in grp if r["boss_win_pct_during"] != ""]
        compare("%s: boss>=.700 vs others, change" % lab, [float(r["change_vs_prior5"]) for r in g if float(r["boss_win_pct_during"]) >= .7],
                [float(r["change_vs_prior5"]) for r in g if float(r["boss_win_pct_during"]) < .7], rng, L)
    L.append("")
    L.append("BY PRIOR LEVEL (high confidence)")
    cnt = Counter(r["prior_level"] for r in allr)
    L.append("  counts: " + ", ".join("%s %d" % kv for kv in cnt.most_common()))
    nfl = [r for r in allr if r["prior_level"] == "NFL"]
    col = [r for r in allr if r["prior_level"] == "FBS"]
    compare("NFL assistant vs FBS assistant: change", [float(r["change_vs_prior5"]) for r in nfl if r["prior_role_class"] != "HC"],
            [float(r["change_vs_prior5"]) for r in col if r["prior_role_class"] != "HC"], rng, L)
    compare("NFL assistant vs FBS assistant: raw win%", [float(r["first_hc_win_pct"]) for r in nfl if r["prior_role_class"] != "HC"],
            [float(r["first_hc_win_pct"]) for r in col if r["prior_role_class"] != "HC"], rng, L, unit="pct")
    g = [r for r in nfl if r["boss_win_pct_during"] != ""]
    compare("NFL only: boss>=.700 vs others, change", [float(r["change_vs_prior5"]) for r in g if float(r["boss_win_pct_during"]) >= .7],
            [float(r["change_vs_prior5"]) for r in g if float(r["boss_win_pct_during"]) < .7], rng, L)
    phc = [r for r in allr if r["prior_role_class"] == "HC"]
    rest = [r for r in allr if r["prior_role_class"] != "HC"]
    compare("prior job a head job (lower level) vs assistants", [float(r["change_vs_prior5"]) for r in phc],
            [float(r["change_vs_prior5"]) for r in rest], rng, L)
    L.append("")

    L.append("TOP 5 'LAST-STOP' TREES (bosses whose staff was the immediate prior job of the most")
    L.append("first-time FBS head coaches; high+med confidence; one-season interims excluded;")
    L.append("change = mean of first-job win% minus program's prior 5)")
    trees = defaultdict(list)
    for r in out:
        if r["parse_confidence"] in ("high", "med") and r["boss"] and not r["boss"].startswith("(") \
                and r["first_hc_interim"] != "yes":
            trees[r["boss"]].append(r)
    top = sorted(trees.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:8]
    for boss, rs in top:
        ch = [float(r["change_vs_prior5"]) for r in rs if r["change_vs_prior5"] != ""]
        L.append("  %-22s %2d assistants | mean change %s pts (n=%d with baseline) | %s" % (
            boss, len(rs), pts(sum(ch) / len(ch)) if ch else "n/a", len(ch),
            ", ".join("%s (%s %d)" % (r["coach"], r["first_hc_school"], r["first_hc_year"]) for r in rs)))
    L.append("\nNote: a 'tree' here counts only the job held immediately before the first head job, so a")
    L.append("coach who left Saban for two other stops before his first head job is not in Saban's tree.")
    return "\n".join(L) + "\n"

def coverage(out):
    L = []
    n = len(out); c = Counter(r["parse_confidence"] for r in out)
    L.append("COVERAGE -- data/coachtree/prior_jobs.csv")
    L.append("coaches: %d | high %d (%.0f%%) | med %d | low %d" % (n, c["high"], 100 * c["high"] / n, c["med"], c["low"]))
    L.append("prior level (all): " + ", ".join("%s %d" % kv for kv in Counter(r["prior_level"] or "(none)" for r in out).most_common()))
    L.append("prior role class (all): " + ", ".join("%s %d" % kv for kv in Counter(r["prior_role_class"] or "(none)" for r in out).most_common()))
    L.append("interim first jobs flagged: %d" % sum(r["first_hc_interim"] == "yes" for r in out))
    L.append("\nWhy not high (first flag on each non-high row, grouped):")
    why = Counter()
    for r in out:
        if r["parse_confidence"] == "high":
            continue
        parts = r["source_note"].split("; ")
        fl = [p for p in parts if not p.startswith(("infobox (", "body: corrob", "boss from", "body: mentions school, years disagree"))] or parts
        key = re.sub(r"\d{4}", "YYYY", re.sub(r"'[^']*'", "'...'", fl[-1] if fl else ""))[:90]
        why[key] += 1
    for k, v in why.most_common(25):
        L.append("  %4d  %s" % (v, k))
    return "\n".join(L) + "\n"

def morris_kinne(out):
    _, S, _ = load_repo()
    L = ["ERIC MORRIS and G.J. KINNE -- head-coaching records", ""]
    pg = fetch(["Eric Morris (American football)", "G. J. Kinne"] +
               ["%d Incarnate Word Cardinals football team" % y for y in range(2018, 2023)])
    L.append("FCS (Incarnate Word, Southland) -- from Wikipedia team-season infoboxes:")
    tot = defaultdict(lambda: [0, 0, 0])
    for y in range(2018, 2023):
        p = pg["%d Incarnate Word Cardinals football team" % y]
        if not p["text"]:
            L.append("  %d: season page missing" % y); continue
        _, f = infobox(p["text"])
        c = disp(clean(f.get("head_coach", ""))); rec = parse_record(f.get("record"))
        L.append("  %d  %-14s %s" % (y, c, "%d-%d" % rec[:2] if rec else f.get("record")))
        who = "Morris" if "Morris" in c else ("Kinne" if "Kinne" in c else c)
        if rec:
            for i in range(3):
                tot[who][i] += rec[i]
    for who in ("Morris", "Kinne"):
        w, l, t = tot[who]
        L.append("  %s at Incarnate Word: %d-%d (%s%%)" % (who, w, l, sig2(100 * pct(w, l, t))))
    L.append("  (2020 was the COVID spring season; the season page's record is used as printed.)")
    L.append("\nFBS -- from data/almamater/seasons.csv (CFBD records, through 2025):")
    for last in ("Morris", "Kinne"):
        rows = [r for r in S if r["last"] == last and r["first"] in ("Eric", "G.J.", "GJ", "G. J.")]
        for sch in sorted({r["school"] for r in rows}):
            rs = sorted([r for r in rows if r["school"] == sch], key=lambda r: r["year"])
            w = sum(r["w"] for r in rs); l = sum(r["l"] for r in rs)
            L.append("  %s at %s %d-%d: %d-%d (%s%%)  seasons: %s" % (last, sch, rs[0]["year"], rs[-1]["year"], w, l,
                     sig2(100 * pct(w, l, 0)), ", ".join("%d %d-%d" % (r["year"], r["w"], r["l"]) for r in rs)))
    for t, who in (("Eric Morris (American football)", "Morris"), ("G. J. Kinne", "Kinne")):
        _, f = infobox(pg[t]["text"])
        L.append("  %s 2026 to date (Wikipedia infobox current_record, live, not verified): %s at %s" % (
            who, disp(clean(f.get("current_record", ""))), disp(clean(f.get("current_team", "")))))
    L.append("  Note: Morris's current_record reads as 2026 only; Kinne's reads as his whole Texas State tenure")
    L.append("  (23-16 through 2025 in the CFBD data). Both are live Wikipedia fields; verify before printing.")
    L.append("\nPrior job before each head job (Wikipedia infobox coaching list; boss from repo seasons.csv):")
    sy = defaultdict(list)
    for r in S:
        sy[(r["school"], r["year"])].append(r)
    for t in ("Eric Morris (American football)", "G. J. Kinne"):
        _, f = infobox(pg[t]["text"]); rows, _ = coaching_rows(f)
        for i, x in enumerate(rows):
            if role_class(x["role_text"], x["fmt"]) == "HC" and i:
                p = rows[i - 1]
                boss = ""
                if p["role_text"]:
                    sch = p["display"]
                    yrs = range(p["start"], p["end"] + 1)
                    last = [z for z in sy.get((sch, p["end"]), [])]
                    if last:
                        b = max(last, key=lambda z: z["games"])
                        rs = [z for y in yrs for z in sy.get((sch, y), []) if z["cid"] == b["cid"]]
                        w = sum(z["w"] for z in rs); l = sum(z["l"] for z in rs); tt = sum(z["t"] for z in rs)
                        boss = "under %s %s (%d-%d, %s%%)" % (b["first"], b["last"], w, l, sig2(100 * pct(w, l, tt)))
                L.append("  %-12s head coach at %-16s %s  <- prior: %s (%s) %s %s" % (
                    t.split(" (")[0], x["display"], x["span"], p["display"], p["role_text"] or "HC", p["span"], boss))
    for r in out:
        if r["coach"] in ("Eric Morris", "G.J. Kinne", "GJ Kinne", "G. J. Kinne"):
            L.append("  prior_jobs.csv: %s -> %s %d; prior %s (%s, %s) under %s, boss win%% during %s; %s" % (
                r["coach"], r["first_hc_school"], r["first_hc_year"], r["prior_school"], r["prior_role"],
                r["prior_level"], r["boss"], r["boss_win_pct_during"], r["parse_confidence"]))
    return "\n".join(L) + "\n"

def main():
    global OFFLINE
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--sample", type=int, default=0, help="print N random rows for hand-checking")
    a = ap.parse_args()
    OFFLINE = a.offline
    OUT.mkdir(parents=True, exist_ok=True)
    out = build()
    with open(OUT / "prior_jobs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore"); w.writeheader(); w.writerows(out)
    cov = coverage(out)
    open(OUT / "coverage.txt", "w").write(cov)
    print(cov)
    c = Counter(r["parse_confidence"] for r in out)
    if c["high"] / len(out) < 0.6:
        msg = "High-confidence coverage %.0f%% is under 60%%; analysis NOT run.\n" % (100 * c["high"] / len(out))
        open(OUT / "analysis.txt", "w").write(msg); print(msg)
    else:
        txt = analyze(out)
        open(OUT / "analysis.txt", "w").write(txt); print(txt)
    mk = morris_kinne(out)
    open(OUT / "morris_kinne.txt", "w").write(mk); print(mk)
    if a.sample:
        rnd = random.Random(20261029)
        for r in rnd.sample(out, a.sample):
            print({k: r[k] for k in ("coach", "first_hc_school", "first_hc_year", "prior_school", "prior_level",
                                     "prior_role", "prior_years", "boss", "boss_win_pct_during", "parse_confidence", "wiki")})

if __name__ == "__main__":
    main()
