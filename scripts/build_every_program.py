#!/usr/bin/env python3
"""Build every-program.html: every major college football program since 1869, as a time-lapse.

    python3 scripts/build_every_program.py            # build from the cached pages
    python3 scripts/build_every_program.py --fetch    # re-download the source first (once a year)

The editor's idea, 2026-10-27, after Julian Critchlow's Channel-swim map
(https://channel-swims.info/crossed; Julian gave his blessing the same day). Each
dot is a program: across, all-time games played; up, all-time winning percentage.
Behind the dots sits the funnel where a coin flip would land. Early on everyone is
scattered; after a thousand games, a coin would sit near .500 and almost every
real program does not. Julian's best idea is borrowed outright: a second clock
that starts every program at its own season 1, the way his map starts every
swimmer at hour zero.

Source: James Howell's College Football Historical Scores, one page per program.
Two properties to know before quoting anything from it:
  - Results as played on the field. Vacated wins stay in; forfeits stay as played.
    Alabama is 999-319-42 here, not the official 985-345-43.
  - Major-college seasons only. Howell drops a season in which a program was not
    playing at the major level, so Notre Dame enters in 1899, not 1887, and Yale
    leaves after 1981.

Checked 2026-10-27 against two other sources:
  - CollegeFootballData, 2005-2025 regular season (data/cfb-team-games.csv):
    31,525 of 31,553 Howell games match to the exact score. The rest are one-point
    score typos or games in a school's move-up year; none flips a result.
  - Sports-Reference, Yale 1872-1981: 717-203-53 there, 718-203-52 here.

Writes data/cfb-alltime-seasons.json and every-program.html. The chart's code is
assets/every-program.js; this script inlines it with the data so the page needs
nothing but itself.
"""
import argparse, html, json, math, pathlib, re, sys, time, urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
CACHE = pathlib.Path.home() / ".cache" / "sports-page" / "howell"
BASE = "https://www.jhowell.net/cf/scores/"
DATA = REPO / "data" / "cfb-alltime-seasons.json"
OUT = REPO / "every-program.html"
JS = REPO / "assets" / "every-program.js"
UA = "TheSportsPage-research/1.0 (+https://thesportspage.net/)"
Y0 = 1869
BIG = 1000          # "a thousand games": the cut the page and Issue text quote

HDR = re.compile(r'<a name=(\d{4})>(\d{4})-(.+?) \(([^)]*)\)</a>')
TOT = re.compile(r'align="center">(\d+)-(\d+)-(\d+)</td><td[^>]*>&nbsp;</td><td[^>]*>(\d+)</td><td[^>]*>(\d+)</td>')


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read()


def fetch():
    """One page per program, a second apart. About five minutes; Howell updates once a year."""
    (CACHE / "pages").mkdir(parents=True, exist_ok=True)
    idx = get(BASE + "byname.htm").decode("latin-1")
    pages = sorted(set(re.findall(r'href="([^"/]+\.htm)"', idx)) - {"ScoresIndex.htm"})
    for i, p in enumerate(pages, 1):
        (CACHE / "pages" / p).write_bytes(get(BASE + p))
        print(f"\r  {i}/{len(pages)} {p:<40}", end="", flush=True)
        time.sleep(1)
    print()


def parse():
    """{page: {year: {name, w, l, t}}} from each program's season-total rows."""
    out = {}
    for f in sorted((CACHE / "pages").glob("*.htm")):
        s = f.read_text(encoding="latin-1")
        hs = list(HDR.finditer(s))
        seasons = {}
        for i, h in enumerate(hs):
            seg = s[h.end(): hs[i + 1].start() if i + 1 < len(hs) else len(s)]
            m = TOT.search(seg)
            if m:
                w, l, t = map(int, m.groups()[:3])
                seasons[int(h.group(1))] = dict(name=html.unescape(h.group(3)), w=w, l=l, t=t)
        if seasons:
            out[f.stem] = seasons
    return out


def summarize(teams):
    """The figures the page's text quotes, computed here so the words cannot drift from the data."""
    rows = []
    for t in teams:
        w, l, ti = (sum(s[k] for s in t["s"]) for k in (1, 2, 3))
        n = w + l + ti
        rows.append(dict(name=t["n"], n=n, p=(w + ti / 2) / n))
    big = [r for r in rows if r["n"] >= BIG]
    inside = [r for r in big if abs(r["p"] - .5) <= 1 / math.sqrt(r["n"])]   # .500 +/- 2 SD
    last = max(t["s"][-1][0] for t in teams) + Y0
    return dict(programs=len(teams), seasons=sum(len(t["s"]) for t in teams), last=last,
                active=sum(t["s"][-1][0] + Y0 == last for t in teams),
                big=len(big), inside=len(inside), outside=len(big) - len(inside))


CSS = """
:root{--ink:#1a1208;--cream:#f5f0e8;--aged:#e0d8c5;--rust:#b83a1e;--steel:#2c4a6e;--gold:#c9962a;
--muted:#6b5e4a;--div:#c8b99a;--card:#ede5d2;
/* tokens the chart reads */--paper:#f5f0e8;--rule:#d6cbb3;--funnel:#e6dcc6;--gone:#a99d86}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--aged);color:var(--ink);font-family:'Libre Baskerville',Georgia,serif;font-size:16px;line-height:1.7;padding:1.5rem 1rem 3rem}
.masthead{max-width:1000px;margin:0 auto;text-align:center;border-top:4px solid var(--ink);padding:.5rem 0 0}
.kicker{font-family:'Roboto Mono',monospace;font-size:.68rem;letter-spacing:.22em;text-transform:uppercase;color:var(--muted)}
.title{font-family:'Playfair Display',serif;font-size:clamp(1.6rem,4vw,2.6rem);font-weight:700;letter-spacing:.04em;text-transform:uppercase;margin:.1rem 0}
.title a{color:inherit;text-decoration:none}
.tagline{font-family:'Playfair Display',serif;font-style:italic;font-size:.95rem;color:var(--muted);margin:.2rem 0 .4rem}
.datebar{display:flex;justify-content:space-between;gap:.6rem;flex-wrap:wrap;font-family:'Roboto Mono',monospace;font-size:.65rem;color:var(--muted);letter-spacing:.1em;border-top:1px solid var(--ink);border-bottom:3px double var(--ink);padding:.3rem 0;margin-top:.3rem}
.paper{max-width:1000px;margin:.8rem auto 0;background:var(--cream);padding:2rem 2.2rem 2.4rem;box-shadow:0 6px 40px rgba(0,0,0,.2);border:1px solid var(--div);display:grid;gap:1.1rem}
@media(max-width:600px){.paper{padding:1.2rem 1rem}}
h1{font-family:'Playfair Display',serif;font-size:clamp(1.8rem,4.4vw,2.7rem);font-weight:900;line-height:1.1;text-wrap:balance}
h1 em{color:var(--rust)}
.deck{font-style:italic;font-size:1.02rem;color:var(--muted);border-left:3px solid var(--rust);padding-left:.9rem;line-height:1.55;max-width:66ch}
.bar{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:center;border-top:2px solid var(--ink);border-bottom:1px solid var(--div);padding:10px 0}
button,select,input{font-family:'Roboto Mono',monospace;font-size:13px;color:var(--ink);background:var(--cream);border:1px solid var(--muted);border-radius:3px;padding:6px 10px}
button{cursor:pointer}
button.primary{background:var(--ink);color:var(--cream);border-color:var(--ink);font-weight:600;min-width:7.5em}
button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.seg{display:inline-flex}
.seg button{border-radius:0}.seg button:first-child{border-radius:3px 0 0 3px}.seg button:last-child{border-radius:0 3px 3px 0;border-left:0}
.seg button[aria-pressed="true"]{background:var(--steel);color:var(--cream);border-color:var(--steel)}
.slider{flex:1 1 220px;display:flex;align-items:center;gap:10px;min-width:0}
.slider input{flex:1;min-width:0;padding:0;border:0;accent-color:var(--rust)}
.clock{font-family:'Playfair Display',serif;font-weight:900;font-size:34px;line-height:1;font-variant-numeric:tabular-nums;min-width:3.2ch}
@media(max-width:600px){.clock{font-size:26px}}
.counts{display:flex;flex-wrap:wrap;gap:6px 22px;font-family:'Roboto Mono',monospace;font-size:13px;color:var(--muted)}
.counts b{color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums}
.chartbox{position:relative;width:100%;aspect-ratio:16/10;max-width:100%}
@media(max-width:600px){.chartbox{aspect-ratio:4/5}}
canvas{width:100%;height:100%;display:block;touch-action:none}
.tip{position:absolute;pointer-events:none;background:var(--ink);color:var(--cream);font-family:'Roboto Mono',monospace;font-size:12px;padding:6px 8px;border-radius:3px;white-space:nowrap;transform:translate(-50%,calc(-100% - 10px))}
.tip[hidden]{display:none}
.find{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.find input{width:14em;max-width:100%;font-family:'Libre Baskerville',serif;font-size:14px}
.chip{display:inline-flex;align-items:center;gap:6px;font-family:'Roboto Mono',monospace;font-size:12px;padding:3px 4px 3px 9px;border:1px solid var(--rust);color:var(--rust);border-radius:20px}
.chip button{border:0;padding:0 6px;background:transparent;color:var(--rust);font-size:14px;line-height:1}
.legend{display:flex;flex-wrap:wrap;gap:6px 20px;font-family:'Roboto Mono',monospace;font-size:12px;color:var(--muted)}
.sw{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:-1px}
.cols{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.3fr);gap:28px}
@media(max-width:760px){.cols{grid-template-columns:minmax(0,1fr)}}
h2{font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;border-bottom:2px solid var(--rust);padding-bottom:.2rem;margin-bottom:.7rem}
table{width:100%;border-collapse:collapse;font-size:14px}
td{padding:4px 0;border-bottom:1px dotted var(--div)}
td.num{font-family:'Roboto Mono',monospace;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.gone{color:var(--muted);font-style:italic}
.notes p{margin:0 0 .8rem;max-width:65ch}
.src{font-family:'Roboto Mono',monospace;font-size:11.5px;line-height:1.6;color:var(--muted);border-top:1px solid var(--div);padding-top:10px}
.src a,.notes a{color:var(--steel)}
.foot{display:flex;justify-content:space-between;flex-wrap:wrap;gap:.3rem;border-top:3px double var(--ink);padding-top:.7rem;font-family:'Roboto Mono',monospace;font-size:.63rem;color:var(--muted);letter-spacing:.07em}
.foot a{color:var(--rust);text-decoration:none}
"""

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Sports Page &mdash; Every Program Since 1869</title>
<meta name="description" content="Every major college football program since 1869, as a time-lapse: games played against all-time winning percentage, with the funnel where luck alone would land.">
<meta property="og:title" content="Every Program Since 1869">
<meta property="og:description" content="Every major college football program, 1869 to @@LAST@@. Press play and watch luck run out.">
<meta property="og:url" content="https://thesportspage.net/every-program.html">
<meta property="og:type" content="website">
<meta property="og:site_name" content="The Sports Page">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Roboto+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>@@CSS@@</style>
<script data-goatcounter="https://thesportspage.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<script src="assets/sitenav.js" defer></script>
</head>
<body>
<div class="masthead">
  <div class="kicker">College Football &middot; 1869&ndash;@@LAST@@</div>
  <div class="title"><a href="https://thesportspage.net/" target="_blank" rel="noopener">The Sports Page</a></div>
  <div class="tagline">Making the numbers mean something since the first pitch</div>
  <div class="datebar"><span>Every Program Since 1869</span><span>@@PROGRAMS@@ Programs &middot; @@SEASONS@@ Seasons</span><span>Records through @@LAST@@</span></div>
</div>
<div class="paper">
  <h1>Every Program Since 1869. <em>Press Play.</em></h1>
  <p class="deck">Each dot is one major college football program. It moves right as the program plays more games, and up or down with its all-time winning percentage. The tan funnel is where a coin flip would land. Early on, a record is mostly luck. After a thousand games, luck has nowhere left to hide.</p>

  <div class="bar">
    <button id="play" class="primary" type="button">&#9654; Play</button>
    <div class="slider"><span class="clock" id="clock">@@LAST@@</span><input id="t" type="range" min="0" max="1" step="1" value="1" aria-label="Year"></div>
    <div class="seg" role="group" aria-label="Clock">
      <button type="button" id="m-cal" aria-pressed="true">By year</button>
      <button type="button" id="m-own" aria-pressed="false">From season 1</button>
    </div>
    <select id="speed" aria-label="Speed"><option value="4">Slow</option><option value="8" selected>Normal</option><option value="20">Fast</option></select>
  </div>

  <div class="counts" id="counts"></div>
  <div class="chartbox" id="box"><canvas id="cv" role="img" aria-label="Scatter of every program: games played across, all-time winning percentage up, with a funnel showing where coin flips would land"></canvas><div class="tip" id="tip" hidden></div></div>

  <div class="legend">
    <span><i class="sw" style="background:var(--steel)"></i>still playing major football</span>
    <span><i class="sw" style="border:1.5px solid var(--gone)"></i>stopped: dropped down, merged, or folded</span>
    <span><i class="sw" style="background:var(--rust)"></i>teams you picked, with their trail</span>
    <span><i class="sw" style="background:var(--funnel);border-radius:2px"></i>where a coin flip would land, 19 times in 20</span>
  </div>

  <div class="find">
    <input id="q" list="names" placeholder="Find a program&hellip;" aria-label="Find a program" autocomplete="off">
    <datalist id="names"></datalist>
    <span id="chips" class="find"></span>
  </div>

  <div class="cols">
    <section>
      <h2 id="lead-h">Best all-time records</h2>
      <table id="lead"></table>
      <p class="src" style="border:0;padding:6px 0 0">Programs with at least 300 games by that point. A tie counts as half a win.</p>
    </section>
    <section class="notes">
      <h2>How to read it</h2>
      <p><b>The tan funnel is luck.</b> If every game were a coin flip, a team&rsquo;s record would still wander away from .500. After 10 games it could easily sit anywhere from .200 to .800. After 1,000 games it would almost never leave .470 to .530. That shape is the funnel.</p>
      <p><b>Dots outside the funnel are real.</b> @@BIG@@ programs have played 1,000 or more major games. Only @@INSIDE@@ of them sit inside the funnel. The other @@OUTSIDE@@ have been too good or too bad, for too long, to be luck.</p>
      <p><b>Switch the clock.</b> &ldquo;From season 1&rdquo; starts every program at once, the way Julian Critchlow&rsquo;s <a href="https://channel-swims.info/crossed" target="_blank" rel="noopener">map of English Channel swims</a> starts every swimmer at hour zero. Yale&rsquo;s first season was 1872 and Boise State&rsquo;s was 1996. On this clock they kick off together.</p>
      <p><b>Click any dot</b> to follow that program, or type a name in the box.</p>
    </section>
  </div>

  <p class="src">Records: James Howell&rsquo;s <a href="https://www.jhowell.net/cf/scores/ScoresIndex.htm" target="_blank" rel="noopener">College Football Historical Scores</a>, results as played on the field. Howell counts a program only in seasons it played at the major-college level, so Notre Dame enters in 1899 and Yale leaves after 1981, and his totals will not match a school&rsquo;s official record. Vacated wins stay in; games against smaller schools count. Checked against CollegeFootballData for 2005&ndash;2025 (31,525 of 31,553 games match to the exact score) and Sports-Reference for Yale. The funnel is .500 plus or minus two standard deviations of a coin flip, 1/&radic;games. Idea and second clock borrowed, with thanks, from Julian Critchlow&rsquo;s <a href="https://channel-swims.info/crossed" target="_blank" rel="noopener">Across the Channel</a>.</p>

  <div class="foot">
    <span>The Sports Page</span>
    <span><a href="https://thesportspage.net/" target="_blank" rel="noopener">&larr; Back to the Archive</a></span>
    <span>One Question Per Issue, Answered With Numbers.</span>
  </div>
</div>
<script>const TEAMS=@@DATA@@;
@@JS@@</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fetch", action="store_true", help="re-download Howell's pages first")
    a = ap.parse_args()
    if a.fetch:
        fetch()
    if not (CACHE / "pages").exists():
        sys.exit("No cached pages. Run with --fetch first.")
    seasons = parse()
    teams = []
    for k, v in seasons.items():
        ys = sorted(v)
        teams.append(dict(n=v[ys[-1]]["name"], s=[[y - Y0, v[y]["w"], v[y]["l"], v[y]["t"]] for y in ys]))
    teams.sort(key=lambda t: t["n"])
    DATA.write_text(json.dumps(teams, separators=(",", ":")) + "\n", encoding="utf-8")
    S = summarize(teams)
    page = PAGE.replace("@@CSS@@", CSS).replace("@@JS@@", JS.read_text(encoding="utf-8"))
    for k, v in S.items():
        page = page.replace(f"@@{k.upper()}@@", f"{v:,}" if k != "last" else str(v))
    page = page.replace("@@DATA@@", json.dumps(teams, separators=(",", ":")))
    from add_emblem import stamp  # every page carries the emblem (2026-10-15)
    OUT.write_text(stamp(page)[0], encoding="utf-8")
    print(f"  {S['programs']} programs, {S['seasons']:,} seasons, {S['active']} playing in {S['last']}")
    print(f"  {S['big']} with {BIG:,}+ games; {S['inside']} inside the coin-flip funnel, {S['outside']} outside")
    print(f"  wrote {DATA.relative_to(REPO)} and {OUT.relative_to(REPO)} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
