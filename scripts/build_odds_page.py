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


# Club colours. Where a club's primary is too pale to read on cream (#f5f0e8),
# the darker of its official pair is used -- Milwaukee navy over gold, San Diego
# brown over gold -- because legibility beats fidelity when the two conflict.
TEAM_COLORS = {
    "108": "#BA0021",  # Angels red
    "109": "#A71930",  # D-backs sedona red
    "110": "#DF4601",  # Orioles orange
    "111": "#BD3039",  # Red Sox red
    "112": "#0E3386",  # Cubs blue
    "113": "#C6011F",  # Reds red
    "114": "#00385D",  # Guardians navy
    "115": "#33006F",  # Rockies purple
    "116": "#0C2340",  # Tigers navy
    "117": "#002D62",  # Astros navy
    "118": "#004687",  # Royals blue
    "119": "#005A9C",  # Dodgers blue
    "120": "#AB0003",  # Nationals red
    "121": "#FF5910",  # Mets orange (navy would collide with half the league)
    "133": "#003831",  # Athletics green
    "134": "#4A4239",  # Pirates -- black lightened so it is not just ink
    "135": "#4A342A",  # Padres brown
    "136": "#005C5C",  # Mariners teal
    "137": "#FD5A1E",  # Giants orange
    "138": "#C41E3A",  # Cardinals red
    "139": "#092C5C",  # Rays navy
    "140": "#003278",  # Rangers blue
    "141": "#134A8E",  # Blue Jays blue
    "142": "#D31145",  # Twins red (navy collides with Yankees/Rays)
    "143": "#E81828",  # Phillies red
    "144": "#CE1141",  # Braves scarlet
    "145": "#3E3B36",  # White Sox -- black lightened
    "146": "#00A3E0",  # Marlins blue
    "147": "#0C2340",  # Yankees navy
    "158": "#12284B",  # Brewers navy
}

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
.tile.pinned{background:#fbf7ec}
.tabs{display:flex;gap:.4rem;border-bottom:3px double var(--ink);margin:0 0 1.2rem;padding-bottom:.5rem;flex-wrap:wrap}
.tabs button{font-family:'Roboto Mono',monospace;font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;
font-weight:600;padding:.45rem .9rem;border:1px solid var(--div);background:var(--card);color:var(--muted);cursor:pointer}
.tabs button[aria-selected="true"]{background:var(--ink);color:var(--cream);border-color:var(--ink)}
.pane[hidden]{display:none}
.cfb-row{display:grid;grid-template-columns:2.1rem minmax(140px,1fr) minmax(120px,1.5fr) repeat(4,3.4rem);
gap:.5rem;align-items:center;border-bottom:1px solid var(--div);padding:.5rem 0}
@media(max-width:760px){.cfb-row{grid-template-columns:1.8rem 1fr repeat(2,3.2rem);row-gap:.3rem}
.cfb-fig{grid-column:1/-1;order:9} .cfb-st:nth-of-type(n+3){display:none}}
.cfb-rk{font-family:'Playfair Display',serif;font-size:1.25rem;font-weight:900;color:var(--muted);text-align:right}
.cfb-nm{font-family:'Playfair Display',serif;font-size:1.02rem;font-weight:700;line-height:1.15}
.cfb-sub{display:block;font-family:'Roboto Mono',monospace;font-size:.62rem;font-weight:400;color:var(--muted);letter-spacing:.03em;margin-top:.1rem}
.cfb-fig{width:100%;height:26px;display:block}
.cfb-st{text-align:right}
.cfb-st b{display:block;font-family:'Playfair Display',serif;font-size:1.02rem;font-weight:900;line-height:1}
.cfb-st span{font-family:'Roboto Mono',monospace;font-size:.54rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.bk-flag{font-family:'Roboto Mono',monospace;font-size:.64rem;letter-spacing:.06em;color:var(--rust);
  border:1px solid var(--rust);padding:.3rem .6rem;display:inline-block;margin-bottom:1rem}
.bk-lg{font-family:'Roboto Mono',monospace;font-size:.7rem;letter-spacing:.18em;text-transform:uppercase;
  color:var(--rust);font-weight:600;border-bottom:1px solid var(--div);padding-bottom:.25rem;margin:1.6rem 0 .8rem}
.bk-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:1rem}
.bk-hd{font-family:'Roboto Mono',monospace;font-size:.58rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);margin-bottom:.4rem}
.bk-series{border:1px solid var(--div);background:var(--card);margin-bottom:.6rem}
.bk-team{display:grid;grid-template-columns:1.4rem 1fr auto;grid-template-areas:'seed nm spark' 'seed rec odds' 'seed sp sp';
  gap:.1rem .45rem;align-items:center;padding:.45rem .55rem;border-bottom:1px solid rgba(200,185,154,.5)}
.bk-team:last-child{border-bottom:none}
.bk-seed{grid-area:seed;font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:900;color:var(--muted)}
.bk-nm{grid-area:nm;font-family:'Playfair Display',serif;font-weight:700;font-size:.95rem;line-height:1.1}
.bk-spark{grid-area:spark;width:74px;height:20px}
.bk-rec{grid-area:rec;font-family:'Roboto Mono',monospace;font-size:.66rem;color:var(--muted)}
.bk-sp{grid-area:sp;font-family:'Roboto Mono',monospace;font-size:.58rem;color:var(--muted);letter-spacing:.02em}
.bk-odds{grid-area:odds;font-family:'Playfair Display',serif;font-weight:900;font-size:1rem;text-align:right;color:var(--steel)}
.bk-odds.dim{color:var(--muted)}
.bk-bye{grid-area:odds;font-family:'Roboto Mono',monospace;font-size:.6rem;color:var(--gold);text-align:right;letter-spacing:.06em}
.bk-cond{font-size:.76rem;padding:.3rem 0;border-bottom:1px solid rgba(224,216,197,.7);line-height:1.35}
.bk-cond b{font-family:'Roboto Mono',monospace;color:var(--steel)}
.fieldbar{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem;margin:.2rem 0 .8rem}
.fbl{font-family:'Roboto Mono',monospace;font-size:.64rem;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);margin-right:.2rem}
.fieldbar button{font-family:'Roboto Mono',monospace;font-size:.64rem;letter-spacing:.06em;
  padding:.3rem .6rem;border:1px solid var(--aged);background:transparent;color:var(--ink);
  cursor:pointer;border-radius:2px;transition:background .12s,border-color .12s}
.fieldbar button:hover,.fieldbar button:focus{background:#fbf7ec;border-color:var(--ink);outline:none}
.fieldbar button.fbc{color:var(--muted)}
.fgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:.1rem .9rem;margin:.5rem 0 .2rem}
.frow{display:grid;grid-template-columns:3.6rem 1fr 3rem 3rem 3.6rem;align-items:baseline;
  gap:.3rem;padding:.14rem 0;border-bottom:1px solid rgba(224,216,197,.6);font-size:.76rem}
.fab{font-family:'Roboto Mono',monospace;font-weight:600;font-size:.66rem}
.fnm{font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.frec,.fpo,.fhope{font-family:'Roboto Mono',monospace;font-size:.66rem;text-align:right}
.fpo{font-weight:600}.fhope{color:var(--muted)}
/* NFL uses a three-letter code where college uses a rank, so the first column
   needs more room and a smaller face or the code collides with the club name. */
#nfl-list .cfb-row{grid-template-columns:3.1rem minmax(140px,1fr) minmax(120px,1.5fr) repeat(4,3.4rem)}
@media(max-width:760px){#nfl-list .cfb-row{grid-template-columns:2.8rem 1fr repeat(2,3.2rem)}}
.nfl-rk{font-size:.88rem;letter-spacing:.03em;font-weight:700;color:var(--ink)}
.cfb-div{font-family:'Roboto Mono',monospace;font-size:.6rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:.9rem 0 .2rem;border-bottom:1px solid var(--aged);padding-bottom:.15rem}
.cfb-row{cursor:pointer;border-radius:3px;transition:background .12s}
.cfb-row:hover,.cfb-row:focus,.cfb-row.on{background:#fbf7ec;outline:none}
.cfb-row.on{box-shadow:inset 3px 0 0 var(--rust)}
.cfb-bar{transition:opacity .1s}
.cfb-bar.dim{opacity:.28}
/* The schedule panel sticks to the bottom of the viewport so it stays readable
   while the cursor is twenty rows up the list. */
.cfb-detail{position:sticky;bottom:0;background:var(--cream);border-top:2px solid var(--ink);
  margin-top:1rem;padding:.7rem 0 .5rem;min-height:2.4rem;z-index:5;
  box-shadow:0 -10px 16px -8px rgba(26,18,8,.22)}
.cfb-detail:empty{border-top:1px dashed var(--aged)}
.cfb-detail:empty::before{content:'Hover a club above to see its schedule and the odds on every game.';
  font-family:'Roboto Mono',monospace;font-size:.66rem;color:var(--muted);letter-spacing:.04em}
.cd-hd{font-family:'Playfair Display',serif;font-weight:900;font-size:1.05rem;margin-bottom:.45rem}
.cd-hd span{font-family:'Roboto Mono',monospace;font-size:.62rem;font-weight:400;color:var(--muted);
  letter-spacing:.05em;margin-left:.5rem}
.cd-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:.3rem .5rem}
.cd-g{border-left:3px solid var(--aged);padding:.15rem 0 .15rem .4rem;font-size:.72rem;line-height:1.3}
.cd-g.win{border-left-color:#2a6e3f}.cd-g.loss{border-left-color:#b83a1e}
.cd-g.hot{background:#f2ead9;border-left-color:var(--gold)}
.cd-o{font-weight:700;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cd-m{font-family:'Roboto Mono',monospace;font-size:.6rem;color:var(--muted);letter-spacing:.03em}
.cd-p{font-family:'Roboto Mono',monospace;font-weight:600}
@media(max-width:760px){.cfb-detail{position:static}.cd-grid{grid-template-columns:repeat(auto-fit,minmax(104px,1fr))}}
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
.bar{height:7px;background:var(--aged);position:relative;margin-top:.15rem}
.bar span{position:absolute;left:0;top:0;bottom:0}
.footer{display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;font-family:'Roboto Mono',monospace;
font-size:.62rem;color:var(--muted);letter-spacing:.08em;border-top:3px double var(--ink);margin-top:2rem;padding-top:.8rem}
.footer a{color:var(--rust);text-decoration:none}
"""

JS = """
const D=DATA,W=D.dates.length;
let sel=[];                                   // pinned clubs
const MAXSEL=12;                              // a full playoff field, both leagues
const MANY=t=>t>2;                            // past two, the chart drops to trend lines only
const first=document.querySelector('.tile').dataset.id;
const FALLBACK=['#2c4a6e','#b83a1e'];
// sRGB -> CIE Lab, so we can tell when two clubs are too close to distinguish
function lab(h){
  let r=parseInt(h.slice(1,3),16)/255,g=parseInt(h.slice(3,5),16)/255,b=parseInt(h.slice(5,7),16)/255;
  const f=v=>v>0.04045?Math.pow((v+0.055)/1.055,2.4):v/12.92; r=f(r);g=f(g);b=f(b);
  let X=(r*.4124+g*.3576+b*.1805)/.95047,Y=r*.2126+g*.7152+b*.0722,Z=(r*.0193+g*.1192+b*.9505)/1.08883;
  const t=v=>v>0.008856?Math.cbrt(v):7.787*v+16/116; X=t(X);Y=t(Y);Z=t(Z);
  return [116*Y-16,500*(X-Y),200*(Y-Z)];
}
function dE(a,b){const p=lab(a),q=lab(b);
  return Math.hypot(p[0]-q[0],p[1]-q[1],p[2]-q[2]);}
// colours for the current selection: club colours, unless they clash
function colours(list){
  const c=list.map(t=>TCOL[t.id]||FALLBACK[0]);
  if(c.length===2&&dE(c[0],c[1])<26) return {cols:c,clash:true};
  return {cols:c,clash:false};
}
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

const CW=660,CH=250,L=46,R=44,Tp=18,Bt=42;
const px=i=>L+(i/(W-1))*(CW-L-R);
const py=v=>Tp+(1-v)*(CH-Tp-Bt);
function chart(list){
  const {cols,clash}=colours(list);
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
  const many=MANY(list.length);
  // Twelve seasons on one axis is only readable if each line is ONE line. Past
  // two clubs we drop the division line, the raw weekly line and the dots, and
  // draw the smoothed trend alone.
  const ends=list.map(t=>py(smooth(t.po,BW)[W-1]));
  if(many){
    // Half a playoff field sits at >99%, so their end labels land on the exact
    // same pixel. Place them properly: sort by height, then walk down enforcing
    // a minimum gap. Comparing each label only against the ones before it is
    // not enough -- a label can clear its neighbours and still land back on a
    // third one.
    const GAP=10, order=list.map((t,k)=>k).sort((a,b)=>ends[a]-ends[b]);
    for(let n=1;n<order.length;n++){
      const a=order[n-1], b=order[n];
      if(ends[b]-ends[a]<GAP) ends[b]=ends[a]+GAP;
    }
    // if the stack ran off the bottom, lift the whole column back inside
    const over=ends[order[order.length-1]]-(CH-Bt);
    if(over>0) order.forEach(k=>{ends[k]-=over;});
  }
  list.forEach((t,k)=>{
    const c=cols[k];
    const dash=(clash&&k===1)?' stroke-dasharray="9 5"':'';           // only if the pair is too close to tell apart
    if(!many){
      g+=poly(t.dv,c,1.4,'stroke-dasharray="3 4" opacity=".38"');     // division, faint dotted
      g+=poly(t.po,c,1.2,'opacity=".34"');                            // raw weekly, thin
      for(let i=0;i<W;i++) g+='<circle cx="'+px(i).toFixed(1)+'" cy="'+py(t.po[i]).toFixed(1)+'" r="2.2" fill="'+c+'" opacity=".42"/>';
    }
    g+=poly(smooth(t.po,BW),c,many?2.0:3.4,many?'opacity=".88"':dash);
    // label the line itself, so identity never rests on colour alone
    let yEnd=ends[k];
    if(!many){
      const off=(list.length===2&&Math.abs(ends[1-k]-yEnd)<14)?(k===0?-8:8):0;
      yEnd+=off;
    }
    g+='<text x="'+(CW-R+4)+'" y="'+(yEnd+4).toFixed(1)+'" font-family="Roboto Mono,monospace" font-size="'+(many?9:10.5)+'" font-weight="700" fill="'+c+'">'+t.abbr+'</text>';
  });
  g+='<line id="guide" x1="0" y1="'+Tp+'" x2="0" y2="'+(CH-Bt)+'" stroke="#1a1208" stroke-width="1" opacity="0"/>'+
     '<rect id="hit" x="'+L+'" y="'+Tp+'" width="'+(CW-L-R)+'" height="'+(CH-Tp-Bt)+'" fill="transparent"/>';
  return '<svg id="big" viewBox="0 0 '+CW+' '+CH+'" role="img" aria-label="Season trajectory for '+list.map(t=>t.name).join(' and ')+'">'+g+'</svg>';
}
function weekLine(list,i){
  const {cols}=colours(list);
  let h='<span class="wk">'+nice(D.dates[i])+'</span>';
  if(MANY(list.length)){
    // ranked by where they stood THAT week, which is the thing worth reading
    list.map((t,k)=>({t,k})).sort((a,b)=>b.t.po[i]-a.t.po[i]).forEach(({t,k})=>{
      h+='<span class="wv" style="color:'+cols[k]+'">'+t.abbr+' '+fmt(t.po[i])+'</span>';
    });
    return h;
  }
  list.forEach((t,k)=>{
    const r=t.rec[i];
    h+='<span class="wv" style="color:'+cols[k]+'">'+t.abbr+' '+r[0]+'-'+r[1]+'</span>'+
       '<span class="wl">'+gbTxt(r[2])+'</span>'+
       '<span class="wv" style="color:'+cols[k]+'">'+fmt(t.po[i])+'</span>';
  });
  return h;
}
function show(ids){
  const list=ids.filter(i=>D.teams[i]).map(i=>Object.assign({id:i},D.teams[i]));
  if(!list.length)return;
  const {cols,clash}=colours(list);   // must precede the tile loop below, which reads it
  document.querySelectorAll('.tile').forEach(e=>{
    const k=sel.indexOf(e.dataset.id);
    e.classList.toggle('on',ids.includes(e.dataset.id));
    e.classList.toggle('pinned',k>=0);
    if(k>=0){ e.style.borderColor=cols[k]; e.style.boxShadow='inset 3px 0 0 '+cols[k]; }
    else { e.style.borderColor=''; e.style.boxShadow=''; }
    e.setAttribute('aria-pressed',k>=0);
  });
  const many=MANY(list.length);
  let head='',body='';
  if(many){
    // twelve full cards is a wall of text; one compact line each, ordered by
    // hope -- the area under the curve, not just where they finished
    list.map((t,k)=>({t,k,auc:t.po.reduce((a,b)=>a+b,0)/W}))
        .sort((a,b)=>b.t.po[W-1]-a.t.po[W-1]||b.auc-a.auc)
        .forEach(({t,k,auc})=>{
      body+='<div class="frow"><span class="fab" style="color:'+cols[k]+'">&#9632; '+t.abbr+'</span>'+
        '<span class="fnm">'+t.name+'</span>'+
        '<span class="frec">'+t.w+'-'+t.l+'</span>'+
        '<span class="fpo">'+fmt(t.po[W-1])+'</span>'+
        '<span class="fhope">hope '+(auc*100).toFixed(0)+'</span></div>';
    });
  } else {
  list.forEach((t,k)=>{
    const po=t.po[W-1],dv=t.dv[W-1];
    const rs=resid(t.po), early=sd(rs.slice(0,Math.floor(W/2))), late=sd(rs.slice(Math.floor(W/2)));
    const auc=t.po.reduce((a,b)=>a+b,0)/W;
    body+='<div class="col"><div class="cn" style="color:'+cols[k]+'">'+t.name+'</div>'+
      '<div class="cr">'+t.w+'-'+t.l+' &middot; '+gbTxt(t.rec[W-1][2])+'</div>'+
      '<div class="cv">'+fmt(po)+' <span class="cl">playoffs</span></div>'+
      '<div class="cv2">'+fmt(dv)+' <span class="cl">division</span> &middot; hope '+(auc*100).toFixed(0)+'</div>'+
      '<div class="cn2">week-to-week wobble: &plusmn;'+(early*100).toFixed(0)+' pts early, &plusmn;'+(late*100).toFixed(0)+' late</div></div>';
  });
  }
  const hint = many ? (fieldSettled(ids) ? 'the settled field &middot; click any tile to drop it'
                                         : 'projected field &mdash; not yet clinched &middot; click any tile to drop it')
             : sel.length===0 ? 'click a club to pin it &middot; pin a second to compare'
             : sel.length===1 ? 'pinned &middot; click another club to overlay it, or click again to release'
             : 'comparing two &middot; click either tile to drop it';
  const title = many
    ? (fieldSettled(ids)?'The playoff field':'The projected playoff field')+
      ' <span class="vs">'+list.length+' clubs</span>'
    : list.map((t,k)=>'<span style="color:'+cols[k]+'">&#9632;</span> '+t.name).join(' <span class="vs">vs</span> ');
  const note = many
    ? 'One smoothed trend per club, so twelve seasons stay readable; the raw weekly points and the division line are hidden at this many. Clubs are listed by where they stand now, and &ldquo;hope&rdquo; is the area under the whole curve &mdash; how much of the season a club spent believing.'
    : (clash?'These two clubs wear nearly the same colour, so the second trend is dashed. ':'')+'Thick line: a smoothed trend. Faint line and dots: the raw weekly numbers. Dashed: chance of winning the division. The distance between thin and thick is the noise.';
  document.getElementById('readout').innerHTML=
    '<div class="rhead">'+title+
      '<span class="pinflag'+(sel.length?'':' dim')+'">'+hint+'</span></div>'+
    '<div class="'+(many?'fgrid':'rgrid2')+'">'+body+'</div>'+
    '<div class="smoothnote">'+note+'</div>'+
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
  else if(sel.length<MAXSEL) sel.push(id);
  else sel=sel.slice(1).concat(id);
  show(sel.length?sel:[first]);
}
// ---- the playoff field, overlaid ----------------------------------------
// Asked for by a reader: once the field is set, put those seasons on one axis.
// Six clubs per league make the field, so we take the six highest-probability
// clubs and say plainly whether they are settled or still projected.
function fieldOf(lg){
  return Object.keys(D.teams)
    .filter(i=>D.teams[i].lg===lg)
    .sort((a,b)=>D.teams[b].po[W-1]-D.teams[a].po[W-1])
    .slice(0,6);
}
function fieldSettled(ids){return ids.every(i=>D.teams[i].po[W-1]>=0.999);}
function pickField(which){
  sel = which==='both' ? fieldOf(103).concat(fieldOf(104))
      : fieldOf(which==='al'?103:104);
  show(sel);
  document.getElementById('board').scrollIntoView({block:'nearest'});
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
document.querySelectorAll('.fieldbar button').forEach(b=>{
  b.addEventListener('click',()=>{
    const w=b.dataset.field;
    if(w==='clear'){sel=[];show([first]);}
    else pickField(w);
  });
});
show([first]);
// tab switching. Panes use the hidden attribute so a hidden pane is also removed
// from the accessibility tree, not merely painted out.
document.querySelectorAll('.tabs button').forEach(b=>{
  b.addEventListener('click',()=>{
    document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-selected', x===b));
    document.querySelectorAll('.pane').forEach(p=>{p.hidden = p.id!==b.getAttribute('aria-controls');});
  });
});

// ---- college football: the whole schedule, on hover ----------------------
// Asked for by a reader who wanted the strip to say WHICH games it was drawing.
// A 26-pixel bar can show that a game is hard; it cannot say who it is against.
function wireSchedule(listId, panelId, DATA){
  const panel=document.getElementById(panelId), list=document.getElementById(listId);
  if(!panel||!list||!DATA||!DATA.length) return;
  // Match the server-side formatter exactly, so the strip tooltip and the panel
  // never disagree about the same game.
  const pf=v=>v>=0.995?'&gt;99%':v<=0.005?'&lt;1%':(v*100).toFixed(0)+'%';
  let pin=null, shown=null;

  function card(ti,hot){
    const t=DATA[ti];
    let g='<div class="cd-hd">'+t.team+'<span>'+(typeof t.rank==='number'?'no. '+t.rank:t.rank)+' &middot; '+t.proj.toFixed(1)+
          ' projected wins &middot; schedule '+(t.sos>=0?'+':'')+t.sos.toFixed(1)+
          (pin===ti?' &middot; pinned, click again to release':'')+'</span></div><div class="cd-grid">';
    t.sched.forEach((x,i)=>{
      const cls=x.w===true?'win':x.w===false?'loss':'';
      const mark=x.w===true?'W &middot; ':x.w===false?'L &middot; ':'';
      g+='<div class="cd-g '+cls+(i===hot?' hot':'')+'">'+
         '<span class="cd-o">'+(x.s==='away'?'at ':'vs ')+x.o+'</span>'+
         '<span class="cd-m">'+nice(x.d)+'</span> <span class="cd-p">'+mark+pf(x.p)+'</span></div>';
    });
    return g+'</div>';
  }
  function draw(ti,hot){
    if(ti===null){panel.innerHTML='';shown=null;
      list.querySelectorAll('.cfb-row').forEach(r=>r.classList.remove('on'));
      list.querySelectorAll('.cfb-bar').forEach(b=>b.classList.remove('dim'));return;}
    panel.innerHTML=card(ti,hot); shown=ti;
    list.querySelectorAll('.cfb-row').forEach(r=>r.classList.toggle('on',+r.dataset.t===ti));
    const row=list.querySelector('.cfb-row[data-t="'+ti+'"]');
    if(row) row.querySelectorAll('.cfb-bar').forEach(b=>b.classList.toggle('dim',hot!=null&&+b.dataset.g!==hot));
  }
  list.querySelectorAll('.cfb-row').forEach(row=>{
    const ti=+row.dataset.t;
    row.addEventListener('mouseenter',()=>{if(pin===null)draw(ti,null);});
    row.addEventListener('focus',()=>{if(pin===null)draw(ti,null);});
    row.addEventListener('click',()=>{pin=(pin===ti)?null:ti;draw(pin===null?ti:pin,null);});
    row.addEventListener('keydown',e=>{
      if(e.key===' '||e.key==='Enter'){e.preventDefault();pin=(pin===ti)?null:ti;draw(pin===null?ti:pin,null);}
      if(e.key==='Escape'){pin=null;draw(null);}
    });
    const fig=row.querySelector('.cfb-fig');
    if(fig){
      fig.addEventListener('mousemove',e=>{
        if(pin!==null&&pin!==ti)return;
        const g=e.target&&e.target.dataset?e.target.dataset.g:null;
        draw(ti,g==null?null:+g);
      });
      fig.addEventListener('mouseleave',()=>{if(shown===ti)draw(ti,null);});
    }
  });
  list.addEventListener('mouseleave',()=>{if(pin===null)draw(null);});
}
wireSchedule('cfb-list','cfb-detail',typeof CFB!=='undefined'?CFB:null);
wireSchedule('nfl-list','nfl-detail',typeof NFLD!=='undefined'?NFLD:null);
"""


CFB_DATA = REPO / "data" / "cfb-odds.json"


def pfmt(p):
    """Never print 100%. No game is certain, and a strip that says so teaches
    the reader the wrong lesson about what a model can know."""
    if p >= 0.995:
        return "&gt;99%"
    if p <= 0.005:
        return "&lt;1%"
    return f"{p*100:.0f}%"


def cfb_rows():
    """One row per top-25 club: rank and name left, season strip centre, numbers right.

    Each row carries its index so the browser can pull the full schedule out of
    the embedded CFB blob on hover. The bars keep a native <title> as well, so
    the information survives with scripting off.
    """
    if not CFB_DATA.exists():
        return "", "", "{}"
    D = json.loads(CFB_DATA.read_text())
    W, H = 300, 26
    out = []
    for ti, t in enumerate(D["teams"]):
        n = len(t["sched"])
        cw = W / max(n, 1)
        bars = ""
        for i, g in enumerate(t["sched"]):
            x = i * cw
            h = max(2.0, g["p"] * H)
            if g["won"] is True:
                c = "#2a6e3f"
            elif g["won"] is False:
                c = "#b83a1e"
            else:
                c = "#8fa8bd" if g["p"] >= .5 else "#d8b9ae"
            bars += (f'<rect class="cfb-bar" data-g="{i}" x="{x:.1f}" y="{H-h:.1f}" '
                     f'width="{cw-1.6:.1f}" height="{h:.1f}" fill="{c}">'
                     f'<title>{g["opp"]} ({g["site"]}) {pfmt(g["p"])}</title></rect>')
        bars += f'<line x1="0" y1="{H/2:.1f}" x2="{W}" y2="{H/2:.1f}" stroke="#c8b99a" stroke-width=".8" stroke-dasharray="2 3"/>'
        rp = "&mdash;" if t["ret"] is None else f'{t["ret"]*100:.0f}%'
        out.append(
            f'<div class="cfb-row" data-t="{ti}" tabindex="0" role="button" '
            f'aria-label="Show the full schedule for {t["team"]}">'
            f'<div class="cfb-rk">{t["rank"]}</div>'
            f'<div class="cfb-nm">{t["team"]}<span class="cfb-sub">SP+ {t["sp"]:+.1f} &middot; talent {t["talent"]:.0f} &middot; returning {rp}</span></div>'
            f'<svg class="cfb-fig" viewBox="0 0 {W} {H}" preserveAspectRatio="none" aria-label="Game by game win probability for {t["team"]}">{bars}</svg>'
            f'<div class="cfb-st"><b>{t["proj"]:.1f}</b><span>proj wins</span></div>'
            f'<div class="cfb-st"><b>{t["ten_plus"]*100:.0f}%</b><span>10+ wins</span></div>'
            f'<div class="cfb-st"><b>{t["undefeated"]*100:.1f}%</b><span>unbeaten</span></div>'
            f'<div class="cfb-st"><b>{t["sos"]:+.1f}</b><span>sched</span></div>'
            f'</div>')
    slim = [{"team": t["team"], "rank": t["rank"], "proj": t["proj"], "sos": t["sos"],
             "sched": [{"o": g["opp"], "s": g["site"], "d": g["date"], "p": g["p"], "w": g["won"]}
                       for g in t["sched"]]}
            for t in D["teams"]]
    return "".join(out), D.get("method", ""), json.dumps(slim, separators=(",", ":"))



BRACKET_DATA = REPO / "data" / "bracket.json"


def bracket_pane():
    """October, laid out as a bracket, with each club's season drawn inside its tile.

    The sparkline is the SAME playoff-odds trajectory the tiles above use, so a
    reader can see at a glance which clubs were never in doubt and which ones
    arrived late. That contrast is most of the fun of a bracket.
    """
    if not BRACKET_DATA.exists() or not DATA.exists():
        return "", ""
    B = json.loads(BRACKET_DATA.read_text())
    TR = json.loads(DATA.read_text())["teams"]
    W, H = 74, 20

    def spark(tid):
        t = TR.get(str(tid))
        if not t:
            return f'<svg class="bk-spark" viewBox="0 0 {W} {H}" aria-hidden="true"></svg>'
        po = t["po"]; n = len(po)
        pts = " ".join(f'{i/(n-1)*W:.1f},{H-v*H:.1f}' for i, v in enumerate(po))
        return (f'<svg class="bk-spark" viewBox="0 0 {W} {H}" preserveAspectRatio="none" '
                f'aria-label="Playoff odds across the season">'
                f'<line x1="0" y1="{H/2}" x2="{W}" y2="{H/2}" stroke="#c8b99a" stroke-width=".6" stroke-dasharray="2 3"/>'
                f'<polyline fill="none" stroke="#2c4a6e" stroke-width="1.6" points="{pts}"/></svg>')

    def tile(c, note=""):
        return (f'<div class="bk-team">'
                f'<span class="bk-seed">{c["seed"]}</span>'
                f'<span class="bk-nm">{c["name"]}</span>'
                f'{spark(c["id"])}'
                f'<span class="bk-rec">{c["w"]}-{c["l"]}</span>'
                f'<span class="bk-sp">OPS {c["ops"] or "--"} &middot; ERA {c["era"] or "--"}</span>'
                f'{note}</div>')

    out = []
    flag = "" if B["settled"] else f'<div class="bk-flag">{B["note"]}</div>'
    out.append(flag)
    for lgid in ("103", "104"):
        b = B["brackets"][lgid]
        seeds = {c["seed"]: c for c in b["seeds"]}
        wc = [m for m in b["matchups"] if m["round"] == "Wild Card"]
        out.append(f'<div class="bk-lg">{b["league"]}</div><div class="bk-grid">')
        out.append('<div class="bk-col"><div class="bk-hd">Wild Card &middot; best of 3</div>')
        for m in wc:
            out.append('<div class="bk-series">')
            out.append(tile(seeds[m["hi"]], f'<span class="bk-odds">{m["p"]*100:.0f}%</span>'))
            out.append(tile(seeds[m["lo"]], f'<span class="bk-odds dim">{(1-m["p"])*100:.0f}%</span>'))
            out.append('</div>')
        out.append('</div>')
        out.append('<div class="bk-col"><div class="bk-hd">Byes &middot; into the Division Series</div>')
        for s in (1, 2):
            out.append('<div class="bk-series">' + tile(seeds[s], '<span class="bk-bye">bye</span>') + '</div>')
        out.append('</div>')
        ds = [m for m in b["matchups"] if m["round"] == "Division Series"]
        out.append('<div class="bk-col"><div class="bk-hd">Division Series &middot; if they meet</div>')
        for m in ds:
            out.append(f'<div class="bk-cond">{m["hi_name"]} over {m["lo_name"]} '
                       f'<b>{m["p"]*100:.0f}%</b></div>')
        out.append('</div></div>')
    return "".join(out), B["note"]

NFL_DATA = REPO / "data" / "nfl-odds.json"


def nfl_rows():
    """Same row shape as the college pane, grouped by division.

    Reusing the .cfb-* classes on purpose: one hover behaviour, one stylesheet,
    one place to fix a bug. The list id is what the script keys on, so the two
    panes get independent panels without a second copy of the code.
    """
    if not NFL_DATA.exists():
        return "", "", "{}"
    D = json.loads(NFL_DATA.read_text())
    W, H = 300, 26
    order = ["AFC East", "AFC North", "AFC South", "AFC West",
             "NFC East", "NFC North", "NFC South", "NFC West"]
    byteam = {t["team"]: t for t in D["teams"]}
    out, ti, slim = [], 0, []
    for div in order:
        mem = [t for t in D["teams"] if t["div"] == div]
        mem.sort(key=lambda t: -t["po"])
        out.append(f'<div class="cfb-div">{div}</div>')
        for t in mem:
            n = len(t["sched"]); cw = W / max(n, 1)
            bars = ""
            for i, g in enumerate(t["sched"]):
                x = i * cw
                h = max(2.0, g["p"] * H)
                c = ("#2a6e3f" if g["won"] is True else "#b83a1e" if g["won"] is False
                     else "#8fa8bd" if g["p"] >= .5 else "#d8b9ae")
                bars += (f'<rect class="cfb-bar" data-g="{i}" x="{x:.1f}" y="{H-h:.1f}" '
                         f'width="{cw-1.6:.1f}" height="{h:.1f}" fill="{c}">'
                         f'<title>{g["opp"]} ({g["site"]}) {pfmt(g["p"])}</title></rect>')
            bars += (f'<line x1="0" y1="{H/2:.1f}" x2="{W}" y2="{H/2:.1f}" stroke="#c8b99a" '
                     f'stroke-width=".8" stroke-dasharray="2 3"/>')
            out.append(
                f'<div class="cfb-row" data-t="{ti}" tabindex="0" role="button" '
                f'aria-label="Show the full schedule for the {t["name"]}">'
                f'<div class="cfb-rk nfl-rk">{t["team"]}</div>'
                f'<div class="cfb-nm">{t["name"]}<span class="cfb-sub">rating {t["rating"]:+.1f} '
                f'&middot; schedule {t["sos"]:+.1f}</span></div>'
                f'<svg class="cfb-fig" viewBox="0 0 {W} {H}" preserveAspectRatio="none" '
                f'aria-label="Game by game win probability for the {t["name"]}">{bars}</svg>'
                f'<div class="cfb-st"><b>{t["proj"]:.1f}</b><span>proj wins</span></div>'
                f'<div class="cfb-st"><b>{t["po"]*100:.0f}%</b><span>playoffs</span></div>'
                f'<div class="cfb-st"><b>{t["dv"]*100:.0f}%</b><span>division</span></div>'
                f'<div class="cfb-st"><b>{t["played"]}</b><span>played</span></div>'
                f'</div>')
            slim.append({"team": t["name"], "rank": t["team"], "proj": t["proj"], "sos": t["sos"],
                         "sched": [{"o": g["opp"], "s": g["site"], "d": g["date"],
                                    "p": g["p"], "w": g["won"]} for g in t["sched"]]})
            ti += 1
    return "".join(out), D.get("method", ""), json.dumps(slim, separators=(",", ":"))


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
    cfb, cfb_method, cfb_json = cfb_rows()
    nfl, nfl_method, nfl_json = nfl_rows()
    bracket, bracket_note = bracket_pane()
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
  <div class="tabs" role="tablist">
    <button role="tab" id="t-mlb" aria-controls="p-mlb" aria-selected="true">Baseball</button>
    <button role="tab" id="t-cfb" aria-controls="p-cfb" aria-selected="false">College Football</button>
    <button role="tab" id="t-nfl" aria-controls="p-nfl" aria-selected="false">NFL</button>
    <button role="tab" id="t-bk" aria-controls="p-bk" aria-selected="false">October</button>
  </div>
  <div class="pane" id="p-mlb" role="tabpanel">
  <div class="fieldbar">
    <span class="fbl">Overlay the playoff field:</span>
    <button type="button" data-field="al">American League</button>
    <button type="button" data-field="nl">National League</button>
    <button type="button" data-field="both">All twelve</button>
    <button type="button" data-field="clear" class="fbc">Clear</button>
  </div>
  <div id="board">{grid}</div>
  <div class="readout" id="readout"></div>
  <p style="font-size:.8rem;color:var(--muted);margin-top:1.2rem;line-height:1.6">
    Odds come from simulating every remaining game 20,000 times from the real standings and the real
    schedule as they stood on each date. Team strength is a blend of record and run differential,
    regressed toward .500. Ties are broken at random rather than by the real tiebreaker rules, so
    treat a number near a coin flip as a coin flip.
  </p>
  </div>

  <div class="pane" id="p-cfb" role="tabpanel" hidden>
    <h1 style="font-size:clamp(1.4rem,3.5vw,2rem);margin-bottom:.3rem">The Top Twenty-Five, <em>Game by Game.</em></h1>
    <div class="deck">Each strip is one club&rsquo;s season, left to right. Bar height is the chance of winning that game; green and red are results already in. A tall flat strip is a schedule that asks nothing. <strong>Hover any club</strong> &mdash; or tab to it &mdash; to read the whole schedule underneath.</div>
    <div id="cfb-list">{cfb}</div>
    <div class="cfb-detail" id="cfb-detail" aria-live="polite"></div>
    <p style="font-size:.8rem;color:var(--muted);margin-top:1.2rem;line-height:1.6">
      {cfb_method}. SP+ is a points-above-average rating, so the difference between two clubs is an
      expected margin and converts to a win probability at any gap &mdash; unlike a rank-difference
      model, which breaks when the gap is large. Strength of schedule is the mean SP+ of the
      opponents faced; Notre Dame&rsquo;s +3.0 against Texas&rsquo;s +13.7 is most of why their
      unbeaten chance is so much higher despite a lower rating.
    </p>
  </div>

  <div class="pane" id="p-nfl" role="tabpanel" hidden>
    <h1 style="font-size:clamp(1.4rem,3.5vw,2rem);margin-bottom:.3rem">Thirty-Two Clubs, <em>Priced by the Market.</em></h1>
    <div class="deck">Each strip is one club&rsquo;s season, left to right; bar height is the chance of winning that game. Before a season starts we have no results, so the ratings come from the betting market rather than from our opinion of anybody. <strong>Hover any club</strong> to read the schedule underneath.</div>
    <div id="nfl-list">{nfl}</div>
    <div class="cfb-detail" id="nfl-detail" aria-live="polite"></div>
    <p style="font-size:.8rem;color:var(--muted);margin-top:1.2rem;line-height:1.6">
      {nfl_method}. A published spread is a statement about a difference &mdash; the home club
      minus the away club, plus home advantage &mdash; so a hundred-odd of them form a linear
      system in thirty-two unknowns that solves for a rating per club. We did not impose the home
      advantage; it fell out of the fit at about a point and a half, which is close to what the
      modern game is measured at, and is the main reason to trust the rest. Ties are broken at
      random rather than by the real tiebreaker rules, so treat anything near a coin flip as one.
    </p>
  </div>

  <div class="pane" id="p-bk" role="tabpanel" hidden>
    <h1 style="font-size:clamp(1.4rem,3.5vw,2rem);margin-bottom:.3rem">The Bracket, <em>With Every Season Inside It.</em></h1>
    <div class="deck">Each club carries the line it drew all year &mdash; its chance of reaching October, week by week. Some were never in doubt; some arrived in the last fortnight. The percentages are series odds, not game odds.</div>
    {bracket}
    <p style="font-size:.8rem;color:var(--muted);margin-top:1.2rem;line-height:1.6">
      Series odds combine club strength by log5 and then add home field <strong>in log-odds</strong>,
      which is the only space where the two adjustments can simply be added: a home edge worth a few
      points to a .500 club is worth less to a .700 one, and adding it in probability space can push
      a number past 1. The home edge is a single constant, +0.14 in log-odds, from the .535 home win
      rate between evenly matched clubs. Strength blends record with the Pythagorean estimate from
      runs scored and allowed, regressed toward .500 by a prior worth 69 games. Best-of-three is
      played entirely at the higher seed; best-of-five splits 2&ndash;2&ndash;1.
    </p>
  </div>

  <div class="footer">
    <span>The Sports Page &middot; The Odds Board</span>
    <span><a href="https://thesportspage.net/">&larr; Back to the Archive</a></span>
  </div>
</div>
<script>const DATA={json.dumps(D, separators=(",", ":"))};const TCOL={json.dumps(TEAM_COLORS, separators=(",", ":"))};const CFB={cfb_json};const NFLD={nfl_json};{JS}</script>
</body>
</html>
"""


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  ({OUT.stat().st_size:,} bytes)")
