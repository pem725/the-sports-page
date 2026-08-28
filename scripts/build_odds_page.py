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
.tile.pin{background:#fbf7ec;border-color:var(--rust);box-shadow:inset 3px 0 0 var(--rust)}
.pinflag{font-family:'Roboto Mono',monospace;font-size:.6rem;letter-spacing:.1em;text-transform:uppercase;color:var(--rust);margin-left:.6rem;vertical-align:.25em}
.pinflag.dim{color:var(--muted)}
.tile:focus-visible{outline:2px solid var(--rust);outline-offset:1px}
.tile .ab{font-family:'Roboto Mono',monospace;font-size:.72rem;font-weight:600;letter-spacing:.08em}
.tile .pc{font-family:'Roboto Mono',monospace;font-size:.66rem;color:var(--muted);float:right}
.tile svg{width:100%;height:34px;display:block;margin-top:.15rem}
.readout{border:2px solid var(--ink);background:var(--cream);padding:1.1rem 1.3rem 1rem;margin:1.4rem 0 0}
.readout .rt{font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:700;line-height:1.2}
.readout .rr{font-family:'Roboto Mono',monospace;font-size:.7rem;color:var(--muted);letter-spacing:.08em;margin-bottom:.5rem}
.readout .hint{font-family:'Roboto Mono',monospace;font-size:.7rem;color:var(--muted);letter-spacing:.06em;margin:.6rem 0 .1rem}
.rgrid{display:grid;grid-template-columns:1fr 1fr;gap:1.4rem;margin:.7rem 0 0}
@media(max-width:520px){.rgrid{grid-template-columns:1fr}}
.rgrid .lab{font-family:'Roboto Mono',monospace;font-size:.64rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);display:block}
.rgrid .big2{font-family:'Playfair Display',serif;font-size:2rem;font-weight:900;line-height:1.1}
#big{width:100%;height:auto;display:block;margin:.4rem 0 0;cursor:crosshair;touch-action:none}
.wkrow{display:flex;flex-wrap:wrap;gap:1.1rem;font-family:'Roboto Mono',monospace;font-size:.74rem;border-top:1px solid var(--div);padding-top:.5rem;margin-top:.1rem;align-items:baseline;min-height:1.9rem}
.wkrow .wk{font-weight:600;letter-spacing:.08em;text-transform:uppercase;font-size:.68rem;color:var(--rust)}
.wkrow .wv{font-weight:600}
.wkrow .wl{color:var(--muted)}
.hope{font-family:'Roboto Mono',monospace;font-size:.72rem;margin:.35rem 0 .1rem;color:var(--ink)}
.hope .hl{letter-spacing:.1em;text-transform:uppercase;font-size:.64rem;color:var(--muted)}
.hope b{font-size:.95rem;color:var(--rust);margin:0 .35rem}
.rhead{font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:700;line-height:1.25;margin-bottom:.5rem}
.rhead .vs{font-family:'Roboto Mono',monospace;font-size:.7rem;color:var(--muted);letter-spacing:.1em;margin:0 .2rem}
.rgrid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.4rem;margin:.2rem 0 .3rem}
.rgrid2 .cn{font-family:'Roboto Mono',monospace;font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase}
.rgrid2 .cr{font-family:'Roboto Mono',monospace;font-size:.7rem;color:var(--muted);margin-bottom:.2rem}
.rgrid2 .cv{font-family:'Playfair Display',serif;font-size:1.9rem;font-weight:900;line-height:1.05}
.rgrid2 .cv2{font-family:'Roboto Mono',monospace;font-size:.76rem;margin-top:.1rem}
.rgrid2 .cl{font-family:'Roboto Mono',monospace;font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.rgrid2 .cn2{font-family:'Roboto Mono',monospace;font-size:.66rem;color:var(--muted);margin-top:.3rem}
.smoothnote{font-family:'Roboto Mono',monospace;font-size:.66rem;color:var(--muted);line-height:1.5;border-top:1px solid var(--div);padding-top:.4rem;margin-top:.4rem}
.tile.pin2{background:#fbf7ec;border-color:#b83a1e;box-shadow:inset 3px 0 0 #b83a1e}
.bar{height:7px;background:var(--aged);position:relative;margin-top:.15rem}
.bar span{position:absolute;left:0;top:0;bottom:0}
.footer{display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;font-family:'Roboto Mono',monospace;
font-size:.62rem;color:var(--muted);letter-spacing:.08em;border-top:3px double var(--ink);margin-top:2rem;padding-top:.8rem}
.footer a{color:var(--rust);text-decoration:none}
"""

JS = """
const D=DATA,W=D.dates.length;
let sel=[];                                   // up to two pinned clubs
const first=document.querySelector('.tile').dataset.id;
const COL=['#2c4a6e','#b83a1e'];
const fmt=v=>(v>=0.999?'>99%':v<=0.001?'<1%':(v*100).toFixed(v<0.1?1:0)+'%');
const MON=['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const nice=s=>{const p=s.split('-');return MON[+p[1]]+' '+(+p[2]);};
const gbTxt=g=>g>0?'+'+g.toFixed(1)+' ahead':g<0?Math.abs(g).toFixed(1)+' back':'level';

// Gaussian kernel smoother. Bandwidth in weeks; every point contributes,
// weighted by distance, so the curve does not lurch at the ends the way a
// boxcar moving average does.
function smooth(a,bw){
  const out=[];
  for(let i=0;i<a.length;i++){
    let num=0,den=0;
    for(let j=0;j<a.length;j++){
      const w=Math.exp(-((i-j)*(i-j))/(2*bw*bw));
      num+=w*a[j]; den+=w;
    }
    out.push(num/den);
  }
  return out;
}
const BW=2.0;
const resid=a=>{const sm=smooth(a,BW);return a.map((v,i)=>v-sm[i]);};
const sd=a=>{const m=a.reduce((x,y)=>x+y,0)/a.length;
  return Math.sqrt(a.reduce((x,y)=>x+(y-m)*(y-m),0)/a.length);};

const CW=660,CH=250,L=46,R=16,Tp=18,Bt=42;
const px=i=>L+(i/(W-1))*(CW-L-R);
const py=v=>Tp+(1-v)*(CH-Tp-Bt);
function chart(list){
  let g='';
  for(const v of [0,.25,.5,.75,1]){
    g+='<line x1="'+L+'" y1="'+py(v).toFixed(1)+'" x2="'+(CW-R)+'" y2="'+py(v).toFixed(1)+
       '" stroke="#c8b99a" stroke-width="1"'+(v===0||v===1?'':' stroke-dasharray="2 4"')+'/>'+
       '<text x="'+(L-8)+'" y="'+(py(v)+3.5).toFixed(1)+'" text-anchor="end" font-family="Roboto Mono,monospace" font-size="10" fill="#6b5e4a">'+(v*100)+'%</text>';
  }
  for(let i=0;i<W;i+=3)
    g+='<text x="'+px(i).toFixed(1)+'" y="'+(CH-Bt+18)+'" text-anchor="middle" font-family="Roboto Mono,monospace" font-size="10" fill="#6b5e4a">'+nice(D.dates[i])+'</text>';
  const poly=(a,c,w,extra)=>'<polyline fill="none" stroke="'+c+'" stroke-width="'+w+'" stroke-linejoin="round" '+(extra||'')+' points="'+
    a.map((v,i)=>px(i).toFixed(1)+','+py(v).toFixed(1)).join(' ')+'"/>';
  list.forEach((t,k)=>{
    const c=COL[k];
    g+=poly(t.dv,c,1.4,'stroke-dasharray="4 4" opacity=".45"');       // division, faint dashed
    g+=poly(t.po,c,1.2,'opacity=".38"');                              // raw weekly, thin
    for(let i=0;i<W;i++) g+='<circle cx="'+px(i).toFixed(1)+'" cy="'+py(t.po[i]).toFixed(1)+'" r="2.2" fill="'+c+'" opacity=".45"/>';
    g+=poly(smooth(t.po,BW),c,3.4);                                   // the trend, bold
  });
  g+='<line id="guide" x1="0" y1="'+Tp+'" x2="0" y2="'+(CH-Bt)+'" stroke="#1a1208" stroke-width="1" opacity="0"/>'+
     '<rect id="hit" x="'+L+'" y="'+Tp+'" width="'+(CW-L-R)+'" height="'+(CH-Tp-Bt)+'" fill="transparent"/>';
  return '<svg id="big" viewBox="0 0 '+CW+' '+CH+'" role="img" aria-label="Season trajectory for '+list.map(t=>t.name).join(' and ')+'">'+g+'</svg>';
}
function weekLine(list,i){
  let h='<span class="wk">'+nice(D.dates[i])+'</span>';
  list.forEach((t,k)=>{
    const r=t.rec[i];
    h+='<span class="wv" style="color:'+COL[k]+'">'+t.abbr+' '+r[0]+'-'+r[1]+'</span>'+
       '<span class="wl">'+gbTxt(r[2])+'</span>'+
       '<span class="wv" style="color:'+COL[k]+'">'+fmt(t.po[i])+'</span>';
  });
  return h;
}
function show(ids){
  const list=ids.map(i=>D.teams[i]).filter(Boolean);
  if(!list.length)return;
  document.querySelectorAll('.tile').forEach(e=>{
    const k=sel.indexOf(e.dataset.id);
    e.classList.toggle('on',ids.includes(e.dataset.id));
    e.classList.toggle('pin',k===0); e.classList.toggle('pin2',k===1);
    e.setAttribute('aria-pressed',k>=0);
  });
  let head='',body='';
  list.forEach((t,k)=>{
    const po=t.po[W-1],dv=t.dv[W-1];
    const rs=resid(t.po), early=sd(rs.slice(0,Math.floor(W/2))), late=sd(rs.slice(Math.floor(W/2)));
    const auc=t.po.reduce((a,b)=>a+b,0)/W;
    body+='<div class="col"><div class="cn" style="color:'+COL[k]+'">'+t.name+'</div>'+
      '<div class="cr">'+t.w+'-'+t.l+' &middot; '+gbTxt(t.rec[W-1][2])+'</div>'+
      '<div class="cv">'+fmt(po)+' <span class="cl">playoffs</span></div>'+
      '<div class="cv2">'+fmt(dv)+' <span class="cl">division</span> &middot; hope '+(auc*100).toFixed(0)+'</div>'+
      '<div class="cn2">week-to-week wobble: &plusmn;'+(early*100).toFixed(0)+' pts early, &plusmn;'+(late*100).toFixed(0)+' late</div></div>';
  });
  const hint = sel.length===0 ? 'click a club to pin it &middot; pin a second to compare'
             : sel.length===1 ? 'pinned &middot; click another club to overlay it, or click again to release'
             : 'comparing two &middot; click either tile to drop it';
  document.getElementById('readout').innerHTML=
    '<div class="rhead">'+list.map((t,k)=>'<span style="color:'+COL[k]+'">&#9632;</span> '+t.name).join(' <span class="vs">vs</span> ')+
      '<span class="pinflag'+(sel.length?'':' dim')+'">'+hint+'</span></div>'+
    '<div class="rgrid2">'+body+'</div>'+
    '<div class="smoothnote">Thick line: a smoothed trend. Faint line and dots: the raw weekly numbers. Dashed: chance of winning the division. The distance between thin and thick is the noise.</div>'+
    chart(list)+
    '<div class="wkrow" id="wkrow">'+weekLine(list,W-1)+'</div>';
  wire(list);
}
function wire(list){
  const svg=document.getElementById('big'),hit=document.getElementById('hit'),
        guide=document.getElementById('guide'),row=document.getElementById('wkrow');
  if(!svg||!hit||!guide||!row)return;
  const at=ev=>{const b=svg.getBoundingClientRect();if(!b.width)return null;
    const x=((ev.clientX-b.left)/b.width)*CW;
    const i=Math.round(((x-L)/(CW-L-R))*(W-1));
    return Number.isFinite(i)?Math.max(0,Math.min(W-1,i)):null;};
  const move=ev=>{const i=at(ev);if(i===null)return;
    guide.setAttribute('x1',px(i));guide.setAttribute('x2',px(i));
    guide.setAttribute('opacity','.45');row.innerHTML=weekLine(list,i);};
  hit.addEventListener('mousemove',move);
  hit.addEventListener('touchmove',e=>{if(e.touches[0])move(e.touches[0]);},{passive:true});
  svg.addEventListener('mouseleave',()=>{guide.setAttribute('opacity','0');row.innerHTML=weekLine(list,W-1);});
}
function toggle(id){
  const k=sel.indexOf(id);
  if(k>=0) sel.splice(k,1);
  else if(sel.length<2) sel.push(id);
  else sel=[sel[1],id];
  show(sel.length?sel:[first]);
}
document.querySelectorAll('.tile').forEach(e=>{
  const id=e.dataset.id;
  e.addEventListener('mouseenter',()=>{if(!sel.length)show([id]);});
  e.addEventListener('focus',()=>{if(!sel.length)show([id]);});
  e.addEventListener('click',()=>toggle(id));
  e.addEventListener('keydown',ev=>{if(ev.key===' '||ev.key==='Enter'){ev.preventDefault();toggle(id);}});
});
const board=document.getElementById('board');
if(board)board.addEventListener('mouseleave',()=>{if(!sel.length)show([first]);});
show([first]);
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
  <div id="board">{grid}</div>
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
