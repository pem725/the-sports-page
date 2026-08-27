#!/usr/bin/env python3
"""Regenerate odds.html from data/playoff-odds-trajectory.json.

    python3 scripts/build_odds_page.py

The page is a grid of 30 small multiples, one per club, grouped by division.
Each tile draws two curves -- chance of reaching the playoffs, and chance of
winning the division -- across every week of the season. Hovering a tile fills a
readout panel with the club's record and both current numbers.

Deliberately a GENERATOR rather than a hand-written page: the data changes daily,
so the page has to be rebuildable in one command. Refresh the JSON, run this,
commit. Everything is inlined, so the page has no external dependency and works
offline and inside an email client's browser.
"""
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "playoff-odds-trajectory.json"
OUT = REPO / "odds.html"

DIVS = [(201, "AL East"), (202, "AL Central"), (200, "AL West"),
        (204, "NL East"), (205, "NL Central"), (203, "NL West")]

CSS = """
:root{--ink:#1a1208;--cream:#f5f0e8;--aged:#e0d8c5;--rust:#b83a1e;--steel:#2c4a6e;
--gold:#c9962a;--muted:#6b5e4a;--div:#c8b99a;--card:#ede5d2;--green:#2a6e3f}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--aged);color:var(--ink);font-family:'Libre Baskerville',Georgia,serif;
font-size:16px;line-height:1.7;padding:1.5rem 1rem 3rem}
.masthead{max-width:1000px;margin:0 auto;text-align:center;border-top:4px solid var(--ink);padding:.5rem 0 0}
.kicker{font-family:'Roboto Mono',monospace;font-size:.68rem;letter-spacing:.22em;text-transform:uppercase;color:var(--muted)}
.title{font-family:'Playfair Display',serif;font-size:clamp(1.6rem,4vw,2.6rem);font-weight:700;
letter-spacing:.04em;text-transform:uppercase;margin:.1rem 0}
.title a{color:inherit;text-decoration:none}
.tagline{font-family:'Playfair Display',serif;font-style:italic;font-size:.95rem;color:var(--muted);margin:.2rem 0 .4rem}
.datebar{display:flex;justify-content:space-between;font-family:'Roboto Mono',monospace;font-size:.65rem;
color:var(--muted);letter-spacing:.1em;border-top:1px solid var(--ink);border-bottom:3px double var(--ink);
padding:.3rem 0;margin-top:.3rem}
.paper{max-width:1000px;margin:.8rem auto 0;background:var(--cream);padding:2rem 2.2rem 2.4rem;
box-shadow:0 6px 40px rgba(0,0,0,.2);border:1px solid var(--div)}
@media(max-width:600px){.paper{padding:1.2rem 1rem}}
h1{font-family:'Playfair Display',serif;font-size:clamp(1.7rem,4vw,2.4rem);font-weight:900;line-height:1.12;margin-bottom:.4rem}
h1 em{color:var(--rust);font-style:italic}
.deck{font-family:'Libre Baskerville',serif;font-style:italic;font-size:1.02rem;color:var(--muted);
border-left:3px solid var(--rust);padding-left:.9rem;margin:.7rem 0 1.4rem;line-height:1.5}
.key{font-family:'Roboto Mono',monospace;font-size:.7rem;letter-spacing:.06em;color:var(--muted);
margin:0 0 1.2rem;display:flex;gap:1.4rem;flex-wrap:wrap;align-items:center}
.key i{display:inline-block;width:16px;height:3px;vertical-align:middle;margin-right:.4rem}
.divname{font-family:'Roboto Mono',monospace;font-size:.68rem;letter-spacing:.18em;text-transform:uppercase;
color:var(--rust);font-weight:600;border-bottom:1px solid var(--div);padding-bottom:.25rem;margin:1.5rem 0 .7rem}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:.55rem}
@media(max-width:820px){.grid{grid-template-columns:repeat(3,1fr)}}
@media(max-width:520px){.grid{grid-template-columns:repeat(2,1fr)}}
.tile{background:var(--card);border:1px solid var(--div);padding:.45rem .5rem .3rem;cursor:pointer;
transition:background .12s,border-color .12s;position:relative}
.tile:hover,.tile.on{background:#fbf7ec;border-color:var(--ink)}
.tile:focus-visible{outline:2px solid var(--rust);outline-offset:1px}
.tile .ab{font-family:'Roboto Mono',monospace;font-size:.72rem;font-weight:600;letter-spacing:.08em}
.tile .pc{font-family:'Roboto Mono',monospace;font-size:.66rem;color:var(--muted);float:right}
.tile svg{width:100%;height:34px;display:block;margin-top:.15rem}
.readout{border:2px solid var(--ink);background:var(--cream);padding:1rem 1.2rem;margin:1.4rem 0 0;min-height:118px}
.readout .rt{font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:700;line-height:1.2}
.readout .rr{font-family:'Roboto Mono',monospace;font-size:.7rem;color:var(--muted);letter-spacing:.08em;margin-bottom:.5rem}
.readout table{width:100%;border-collapse:collapse;font-family:'Roboto Mono',monospace;font-size:.76rem}
.readout td{padding:.16rem 0}
.readout td:last-child{text-align:right;font-weight:600}
.readout .hint{font-family:'Roboto Mono',monospace;font-size:.7rem;color:var(--muted);letter-spacing:.06em}
.bar{height:7px;background:var(--aged);position:relative;margin-top:.15rem}
.bar span{position:absolute;left:0;top:0;bottom:0}
.footer{display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;font-family:'Roboto Mono',monospace;
font-size:.62rem;color:var(--muted);letter-spacing:.08em;border-top:3px double var(--ink);margin-top:2rem;padding-top:.8rem}
.footer a{color:var(--rust);text-decoration:none}
"""

JS = """
const D=DATA,W=D.dates.length;
const fmt=v=>(v>=0.999?'>99%':v<=0.001?'<1%':(v*100).toFixed(v<0.1?1:0)+'%');
const nice=s=>{const[y,m,d]=s.split('-');return ['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+m]+' '+(+d);};
function spark(a,col,w,h){
  if(!a.length)return '';
  const pts=a.map((v,i)=>[(i/(W-1))*w,h-v*h]);
  return '<polyline fill="none" stroke="'+col+'" stroke-width="1.8" stroke-linejoin="round" points="'+
    pts.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ')+'"/>'+
    '<circle cx="'+pts[pts.length-1][0].toFixed(1)+'" cy="'+pts[pts.length-1][1].toFixed(1)+'" r="2.2" fill="'+col+'"/>';
}
function show(id){
  const t=D.teams[id];
  document.querySelectorAll('.tile').forEach(e=>e.classList.toggle('on',e.dataset.id===id));
  const po=t.po[W-1],dv=t.dv[W-1],po0=t.po[0];
  const delta=po-po0, arrow=delta>0.02?'&#9650;':delta<-0.02?'&#9660;':'&#8213;';
  const col=delta>0.02?'var(--green)':delta<-0.02?'var(--rust)':'var(--muted)';
  document.getElementById('readout').innerHTML=
    '<div class="rt">'+t.name+'</div>'+
    '<div class="rr">'+t.w+'-'+t.l+'</div>'+
    '<table><tr><td>Reach the playoffs</td><td>'+fmt(po)+'</td></tr>'+
    '<tr><td colspan="2"><div class="bar"><span style="width:'+(po*100).toFixed(1)+'%;background:var(--steel)"></span></div></td></tr>'+
    '<tr><td>Win the division</td><td>'+fmt(dv)+'</td></tr>'+
    '<tr><td colspan="2"><div class="bar"><span style="width:'+(dv*100).toFixed(1)+'%;background:var(--gold)"></span></div></td></tr>'+
    '</table><div class="hint" style="margin-top:.5rem;color:'+col+'">'+arrow+' '+
    nice(D.dates[0])+': '+fmt(po0)+' &rarr; '+nice(D.dates[W-1])+': '+fmt(po)+'</div>';
}
document.querySelectorAll('.tile').forEach(e=>{
  e.addEventListener('mouseenter',()=>show(e.dataset.id));
  e.addEventListener('focus',()=>show(e.dataset.id));
  e.addEventListener('click',()=>show(e.dataset.id));
});
show(document.querySelector('.tile').dataset.id);
"""


def build() -> str:
    D = json.loads(DATA.read_text())
    teams = D["teams"]
    tiles = []
    for div, label in DIVS:
        members = sorted((t for t in teams.values() if t["div"] == div),
                         key=lambda x: -x["po"][-1])
        ids = [k for k, v in teams.items() if v["div"] == div]
        ids.sort(key=lambda k: -teams[k]["po"][-1])
        tiles.append(f'<div class="divname">{label}</div><div class="grid">')
        for tid in ids:
            t = teams[tid]
            w, h = 100, 34
            po = ('<polyline fill="none" stroke="#2c4a6e" stroke-width="1.8" points="' +
                  " ".join(f'{i/(len(t["po"])-1)*w:.1f},{h-v*h:.1f}' for i, v in enumerate(t["po"])) + '"/>')
            dv = ('<polyline fill="none" stroke="#c9962a" stroke-width="1.5" opacity=".85" points="' +
                  " ".join(f'{i/(len(t["dv"])-1)*w:.1f},{h-v*h:.1f}' for i, v in enumerate(t["dv"])) + '"/>')
            tiles.append(
                f'<div class="tile" data-id="{tid}" tabindex="0" role="button" '
                f'aria-label="{t["name"]}, {t["w"]}-{t["l"]}, playoff chance {t["po"][-1]*100:.0f} percent">'
                f'<span class="ab">{t["abbr"]}</span><span class="pc">{t["po"][-1]*100:.0f}%</span>'
                f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true">'
                f'<line x1="0" y1="{h/2}" x2="{w}" y2="{h/2}" stroke="#c8b99a" stroke-width=".8" stroke-dasharray="2 3"/>'
                f'{dv}{po}</svg></div>')
        tiles.append("</div>")
    grid = "\n".join(tiles)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Sports Page &mdash; Playoff Odds, Week by Week</title>
<meta name="description" content="Every major league club's chance of reaching the playoffs and of winning its division, tracked weekly across the 2026 season. Hover any club to read the numbers.">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Roboto+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
<script data-goatcounter="https://thesportspage.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</head>
<body>
<div class="masthead">
  <div class="kicker">The Odds Board &middot; Updated {D["generated"]}</div>
  <div class="title"><a href="https://thesportspage.net/">The Sports Page</a></div>
  <div class="tagline">Making the numbers mean something since the first pitch</div>
  <div class="datebar"><span>Playoff Odds</span><span>{D["generated"]}</span><span>30 Clubs &middot; {len(D["dates"])} Weeks</span></div>
</div>
<div class="paper">
  <h1>Thirty Seasons at Once. <em>Hover Any One of Them.</em></h1>
  <div class="deck">Each tile is one club's season. The blue line is its chance of reaching the playoffs, week by week; the gold line is its chance of winning the division. A flat line means the season was never in doubt &mdash; in either direction.</div>
  <div class="key">
    <span><i style="background:#2c4a6e"></i>chance of reaching the playoffs</span>
    <span><i style="background:#c9962a"></i>chance of winning the division</span>
    <span>dashed line = 50%</span>
  </div>
  {grid}
  <div class="readout" id="readout"></div>
  <p style="font-size:.8rem;color:var(--muted);margin-top:1.2rem;line-height:1.6">
    Odds come from simulating every remaining game 20,000 times from the real standings and the real
    schedule as they stood on each date. Team strength is a blend of record and run differential,
    regressed toward .500. Ties are broken at random rather than by the real tiebreaker rules, so
    treat a number near a coin flip as a coin flip.
  </p>
  <div class="footer">
    <span>The Sports Page &middot; The Odds Board</span>
    <span><a href="https://thesportspage.net/">&larr; Back to the Archive</a></span>
  </div>
</div>
<script>const DATA={json.dumps(D, separators=(",", ":"))};{JS}</script>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  ({OUT.stat().st_size:,} bytes)")
