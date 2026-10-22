import json, csv, re, pathlib, sys
from collections import defaultdict
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from wiki import load, resolve, fetch
D = pathlib.Path(__file__).resolve().parent
SEARCH = json.load(open(D/'wiki/search.json')) if (D/'wiki/search.json').exists() else {}
fetch([t for v in SEARCH.values() for t in v])
pages = load(); canon = json.load(open(D/'canon.json'))
teams = {x['school']:x for x in json.load(open(D/'cache/teams.json'))}
coached = defaultdict(set); names = {}
for r in csv.DictReader(open(D/'seasons.csv')):
    coached[int(r['cid'])].add(r['school']); names[int(r['cid'])] = (r['first'], r['last'])
# plain-text aliases
ALIAS = {"north carolina state":"NC State","n.c. state":"NC State","nc state":"NC State","mississippi":"Ole Miss","ole miss":"Ole Miss",
 "southern california":"USC","usc":"USC","pitt":"Pittsburgh","louisiana state":"LSU","lsu":"LSU","miami (fl)":"Miami","miami (florida)":"Miami",
 "miami (oh)":"Miami (OH)","miami (ohio)":"Miami (OH)","brigham young":"BYU","texas christian":"TCU","southern methodist":"SMU",
 "connecticut":"UConn","central florida":"UCF","southern mississippi":"Southern Miss","appalachian state":"App State","hawaii":"Hawai'i",
 "san jose state":"San José State","texas-el paso":"UTEP","alabama-birmingham":"UAB","nevada-las vegas":"UNLV","army":"Army","west point":"Army",
 "naval academy":"Navy","virginia military institute":"VMI","memphis state":"Memphis","north texas state":"North Texas","southwest texas state":"Texas State",
 "southwestern louisiana":"Louisiana","northeast louisiana":"UL Monroe","louisiana-monroe":"UL Monroe","fiu":"Florida International","umass":"Massachusetts"}
def norm(s): return re.sub(r"\s+"," ",s.replace("–","-").replace("’","'")).strip().lower()
for s in canon: ALIAS.setdefault(norm(s), s)
canon_rev = {}
for s,c in canon.items():
    canon_rev[c] = s; canon_rev[c[:-len(" football")]] = s
DISAMB = re.compile(r"\{\{\s*(disambig|hndis|human name disambiguation|dab|surname)", re.I)
def infobox_fields(text):
    f = {}
    i = text.find("{{Infobox")
    if i < 0: return f
    depth=0; j=i
    while j < len(text):
        if text.startswith("{{",j): depth+=1; j+=2; continue
        if text.startswith("}}",j):
            depth-=1; j+=2
            if depth==0: break
            continue
        j+=1
    box = text[i:j]
    # split on top-level pipes at line start
    for m in re.finditer(r"\n\s*\|\s*([A-Za-z_0-9]+)\s*=(.*?)(?=\n\s*\|\s*[A-Za-z_0-9]+\s*=|\n?\}\}$)", box, re.S):
        f[m.group(1).strip()] = m.group(2).strip()
    return f
LINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]")
def team_mentions(val):
    out = []
    for m in LINK.finditer(val): out.append(("link", m.group(1).strip(), (m.group(2) or m.group(1)).strip()))
    rest = LINK.sub("", val); rest = re.sub(r"<ref.*?(</ref>|/>)","",rest, flags=re.S)
    rest = re.sub(r"\{\{.*?\}\}|<[^>]+>|\(.*?\)","",rest)
    for p in re.split(r"[,\n*;]|<br", rest):
        p = p.strip(" '*")
        if p: out.append(("text", None, p))
    return out
def valid(text, schools):
    if not text or DISAMB.search(text[:3000]) or "may refer to" in text[:1500]: return False
    for s in schools:
        c = canon[s]
        if c in text or c[:-9] in text: return True
        if s in teams and f"{s} {teams[s]['mascot']}" in text: return True
    return False
rows = []; linkset = set(); unresolved = []
for cid,(f,l) in names.items():
    n = f"{f} {l}".strip()
    chosen = None
    for v in (f"{n} (American football coach)", f"{n} (American football)", n):
        p = pages.get(v)
        if p and valid(p["text"], coached[cid]): chosen = (v, p); break
    if not chosen:
        for v in SEARCH.get(str(cid), []):
            p = pages.get(v)
            if l.split()[-1].lower() in v.lower() and p and valid(p["text"], coached[cid]): chosen = (v, p); break
    if not chosen:
        unresolved.append((cid, n, sorted(coached[cid]))); continue
    title, text = chosen[1]["title"], chosen[1]["text"]
    fb = infobox_fields(text)
    play = []  # (field, years, mentions)
    for k,v in fb.items():
        m = re.fullmatch(r"(player|playing)_team(\d*)", k)
        if m:
            yrs = fb.get(f"{m.group(1)}_years{m.group(2)}", "") or fb.get(f"player_years{m.group(2)}", "")
            play.append(("player_team", yrs, team_mentions(v)))
        elif k == "college":
            yrs = " ".join(re.findall(r"\d{4}\s*[–-]\s*\d{2,4}|\d{4}", v))
            play.append(("college", yrs, team_mentions(v)))
        elif k == "alma_mater":
            play.append(("alma_mater", "", team_mentions(v)))
    prose = None
    if not any(p[0] in ("player_team","college") for p in play):
        body = re.sub(r"\{\{Infobox.*?\n\}\}", "", text, count=1, flags=re.S)[:6000]
        pm = re.search(r"(played|lettered|starred|was a [a-z ]+)[^.]{0,80}?(?:college football |football )?(?:at|for) (?:the )?(\[\[[^\]]+\]\])", body)
        if pm:
            play.append(("prose", "", team_mentions(pm.group(2)))); prose = pm.group(0)[:150]
    for _,_,ms in play:
        for kind,t,_ in ms:
            if kind=="link": linkset.add(t)
    rows.append(dict(cid=cid, name=n, wiki=title, play=play, prose=prose))
res = resolve(sorted(linkset))
UNI = {"miami university":"Miami (OH)","university of miami":"Miami","pennsylvania state":"Penn State","virginia polytechnic institute and state":"Virginia Tech",
 "virginia tech":"Virginia Tech","georgia institute of technology":"Georgia Tech","united states military academy":"Army","united states naval academy":"Navy",
 "united states air force academy":"Air Force","u.s. military academy":"Army","u.s. naval academy":"Navy","california, los angeles":"UCLA","california, berkeley":"California",
 "bowling green state":"Bowling Green","alabama at birmingham":"UAB","texas at el paso":"UTEP","nevada, las vegas":"UNLV","nevada, reno":"Nevada",
 "louisiana at lafayette":"Louisiana","louisiana at monroe":"UL Monroe","texas at san antonio":"UTSA","north carolina at charlotte":"Charlotte",
 "massachusetts amherst":"Massachusetts","connecticut":"UConn","hawaii at manoa":"Hawai'i","hawaiʻi at mānoa":"Hawai'i","boston college":"Boston College",
 "virginia military institute":"VMI","the citadel":"The Citadel","texas a&m":"Texas A&M","college of william & mary":"William & Mary","william & mary":"William & Mary",
 "college of william and mary":"William & Mary","michigan state":"Michigan State","florida state":"Florida State","texas christian":"TCU","southern methodist":"SMU",
 "colorado state":"Colorado State","appalachian state":"App State","illinois urbana-champaign":"Illinois","illinois at urbana-champaign":"Illinois",
 "minnesota twin cities":"Minnesota","minnesota, twin cities":"Minnesota","wisconsin-madison":"Wisconsin","wisconsin–madison":"Wisconsin","maryland, college park":"Maryland",
 "missouri-columbia":"Missouri","nebraska-lincoln":"Nebraska","nebraska–lincoln":"Nebraska","tennessee, knoxville":"Tennessee","texas at austin":"Texas","pittsburgh":"Pittsburgh",
 "middle tennessee state":"Middle Tennessee","san jose state":"San José State","san josé state":"San José State","georgia southern":"Georgia Southern"}
def uni_norm(x):
    x = norm(x).replace("–","-")
    if x in UNI: return UNI[x]
    y = re.sub(r"^the ","",x)
    y = re.sub(r"^university of ","",y); y = re.sub(r" university$","",y)
    if y in UNI: return UNI[y]
    return ALIAS.get(y)
def schools_of(ms, uni=False):
    out=set()
    for kind,t,disp in ms:
        got=None
        if kind=="link":
            r = res.get(t,t)
            if r in canon_rev: got=canon_rev[r]
            elif r.endswith(" football") and r[:-9] in canon_rev: got=canon_rev[r[:-9]]
            if not got and uni: got = uni_norm(r) or uni_norm(t)
        if not got: got = ALIAS.get(norm(disp)) or (uni_norm(disp) if uni or kind=="link" else None)
        if got: out.add(got)
    return out
final=[]
for r in rows:
    played=set(); played_yrs={}; att=set(); src={}
    for kind,yrs,ms in r["play"]:
        sc = schools_of(ms, uni=(kind=='alma_mater'))
        if kind in ("player_team","college","prose"):
            for s in sc: played.add(s); played_yrs.setdefault(s, yrs); src.setdefault(s, kind)
        else: att |= sc
    r2 = dict(cid=r["cid"], name=r["name"], wiki=r["wiki"], played=sorted(played), played_years=played_yrs, src=src,
              alma=sorted(att), has_play_field=any(k in ("player_team","college","prose") for k,_,_ in r["play"]),
              raw_play=[(k,y,[m[2] for m in ms]) for k,y,ms in r["play"]], coached=sorted(coached[r["cid"]]))
    final.append(r2)
json.dump(final, open(D/'wiki_parsed.json','w'), indent=1)
json.dump(unresolved, open(D/'unresolved.json','w'), indent=1)
print("resolved", len(final), "unresolved", len(unresolved))
print("no playing info:", sum(1 for x in final if not x["has_play_field"]))
