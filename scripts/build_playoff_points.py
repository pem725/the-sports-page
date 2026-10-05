#!/usr/bin/env python3
"""How good do you have to be to make the playoffs, in points?

    python3 scripts/build_playoff_points.py
    python3 scripts/build_playoff_points.py --report     # numbers only, no write

THE EDITOR, 2026-10-05, on the win-probability page: "The metric we care about
is not the probability of winning a game. All you gotta do is make the playoffs.
What winning percentage is required, historically? And then -- how many points do
you need to score to win that proportion of games? If you have a stingy defense,
how stingy? Which one matters more? Is defense compensatory?"

WHY THIS BELONGS ON THAT PAGE SPECIFICALLY. The page carries a correction: its
two ogives cross at 50% by identity, not by measurement, because every game one
team scored 24 is the game the other allowed 24. It had once read that crossing
as proof that offense and defense are worth the same, and had to retract it.

This section makes that claim legitimately. At TEAM-SEASON level the constraint
is gone -- the page already reports that points scored and points allowed
correlate only -0.15 across 861 seasons, and their sum runs from 462 to 1,011.
Nothing forces a club to trade one for the other. So the question "are they worth
the same" is answerable here and was not answerable there.

WHAT THE DATA SAYS, and it is cleaner than expected:

  1. The playoff cut is a CLIFF, not a slope. Below .500 almost nobody gets in;
     by .688 it is 99%. Even money sits near .594 -- lower than the 75% a fan
     would guess, because 12 of 32 clubs qualify (14 since 2020).

  2. Offense and defense are worth the SAME to three decimal places. A point
     scored is +2.749 points of win percentage; a point prevented is +2.849.

  3. Therefore only MARGIN matters. Regressing win rate on points-for and
     points-against separately buys +0.0003 of R-squared over margin alone
     (0.8310 vs 0.8307). Knowing HOW a club got to +7 tells you essentially
     nothing that knowing +7 did not.

  4. So yes, defense is compensatory, and the exchange rate is one-for-one.
     "Defense wins championships" is not false so much as not special: offense
     wins exactly as many.

SOURCE. nflverse game results, which carry game_type, so postseason appearance
is read rather than inferred -- a club in any WC/DIV/CON/SB game made the field.
Primary feed, per the rule that nothing grading a forecast may come from a search.

HONEST LIMITS, stated on the page too. This is descriptive, not causal: it says
what the clubs that made the playoffs looked like, not what a given club should
buy. Margin is also measured across a whole season, so it cannot see a club that
banked its points in three blowouts. And the field grew from 12 to 14 in 2020,
which moves the cut down slightly; the thresholds here pool both eras.
"""
import argparse
import collections
import csv
import json
import math
import pathlib
import statistics
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
CACHE = REPO / "data" / "nfl" / "nflverse-games.csv"
PAGE = REPO / "interactive" / "win-probability.html"
SRC = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
MARK = "<!-- PLAYOFF_POINTS -->"


def load(refresh=False):
    if refresh or not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(SRC, timeout=120) as r:
            CACHE.write_bytes(r.read())
    return [r for r in csv.DictReader(open(CACHE))
            if r["home_score"] not in ("", "NA", None)]


def team_seasons(rows):
    reg = collections.defaultdict(lambda: dict(w=0, t=0, pf=0, pa=0, g=0))
    post = set()
    for r in rows:
        s = int(r["season"])
        h, a = r["home_team"], r["away_team"]
        hs, as_ = int(float(r["home_score"])), int(float(r["away_score"]))
        if r["game_type"] != "REG":
            post.add((s, h)); post.add((s, a))
            continue
        for t, pf, pa in ((h, hs, as_), (a, as_, hs)):
            d = reg[(s, t)]
            d["pf"] += pf; d["pa"] += pa; d["g"] += 1
            d["w"] += pf > pa; d["t"] += pf == pa
    out = []
    for (s, t), d in sorted(reg.items()):
        # A season still in progress has no postseason yet; grading it would
        # record every club as having missed.
        if d["g"] < 14:
            continue
        out.append(dict(season=s, team=t, g=d["g"],
                        wp=(d["w"] + .5 * d["t"]) / d["g"],
                        pf=d["pf"] / d["g"], pa=d["pa"] / d["g"],
                        playoff=(s, t) in post))
    done = {s for s in {x["season"] for x in out}
            if any(x["playoff"] for x in out if x["season"] == s)}
    return [x for x in out if x["season"] in done]


def ols(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)
    a0 = my - b * mx
    yh = [a0 + b * v for v in xs]
    ss = sum((c - h) ** 2 for c, h in zip(ys, yh))
    tot = sum((c - my) ** 2 for c in ys)
    return a0, b, 1 - ss / tot


def ols2(T):
    """win% ~ a + b1*pf + b2*pa, by Gauss-Jordan on the normal equations."""
    n = len(T)
    X = [(1.0, x["pf"], x["pa"]) for x in T]
    y = [x["wp"] for x in T]
    A = [[sum(X[k][i] * X[k][j] for k in range(n)) for j in range(3)] for i in range(3)]
    b = [sum(X[k][i] * y[k] for k in range(n)) for i in range(3)]
    for i in range(3):
        p = A[i][i]
        for j in range(3):
            A[i][j] /= p
        b[i] /= p
        for r in range(3):
            if r != i:
                f = A[r][i]
                for j in range(3):
                    A[r][j] -= f * A[i][j]
                b[r] -= f * b[i]
    a0, b1, b2 = b
    yh = [a0 + b1 * x["pf"] + b2 * x["pa"] for x in T]
    my = statistics.mean(y)
    ss = sum((x["wp"] - h) ** 2 for x, h in zip(T, yh))
    tot = sum((v - my) ** 2 for v in y)
    return a0, b1, b2, 1 - ss / tot


def thresholds(T):
    """Win rate at which the playoff field becomes even money, and near-certain."""
    pts = []
    lo = 0.30
    while lo < 0.95:
        g = [x for x in T if lo <= x["wp"] < lo + 1 / 17]
        if len(g) >= 20:
            pts.append((lo + 0.5 / 17, sum(x["playoff"] for x in g) / len(g), len(g)))
        lo += 1 / 34
    def cross(target):
        for (w0, p0, _), (w1, p1, _) in zip(pts, pts[1:]):
            if p0 < target <= p1:
                return w0 + (target - p0) / (p1 - p0) * (w1 - w0)
        return None
    return pts, cross(0.5), cross(0.9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()

    T = team_seasons(load(a.refresh))
    yrs = sorted({x["season"] for x in T})
    a0, b1, b2, r2_sep = ols2(T)
    m0, mb, r2_mar = ols([x["pf"] - x["pa"] for x in T], [x["wp"] for x in T])
    bands, even, lock = thresholds(T)
    mar_even, mar_lock = (even - m0) / mb, (lock - m0) / mb

    print(f"  {len(T)} team-seasons, {yrs[0]}-{yrs[-1]}, "
          f"{sum(x['playoff'] for x in T)} made the playoffs\n")
    print(f"  win% = {a0:.4f} + {b1:.5f}*scored {b2:+.5f}*allowed      R2 {r2_sep:.4f}")
    print(f"  win% = {m0:.4f} {mb:+.5f}*margin                          R2 {r2_mar:.4f}")
    print(f"  separating offense from defense buys {r2_sep - r2_mar:+.4f} of R-squared")
    print(f"  exchange rate: a point prevented is worth {abs(b2/b1):.3f} of a point scored\n")
    print(f"  even money at win% {even:.3f}  ->  margin {mar_even:+.2f} per game")
    print(f"  90% certain at    {lock:.3f}  ->  margin {mar_lock:+.2f} per game")

    if a.report:
        return 0

    rows = [[x["team"], x["season"], round(x["pf"], 2), round(x["pa"], 2),
             round(x["wp"], 4), 1 if x["playoff"] else 0] for x in T]
    blob = dict(rows=rows, a0=round(a0, 5), b1=round(b1, 6), b2=round(b2, 6),
                m0=round(m0, 5), mb=round(mb, 6),
                r2sep=round(r2_sep, 4), r2mar=round(r2_mar, 4),
                even=round(even, 4), lock=round(lock, 4),
                marEven=round(mar_even, 2), marLock=round(mar_lock, 2),
                bands=[[round(w, 4), round(p, 4), n] for w, p, n in bands],
                yrs=[yrs[0], yrs[-1]], n=len(T))
    html = SECTION.replace("__DATA__", json.dumps(blob, separators=(",", ":")))
    page = PAGE.read_text(encoding="utf-8")
    if MARK in page:
        head, _, tail = page.partition(MARK)
        end = tail.find("<!-- /PLAYOFF_POINTS -->")
        tail = tail[end + len("<!-- /PLAYOFF_POINTS -->"):] if end >= 0 else tail
        page = head + MARK + html + "<!-- /PLAYOFF_POINTS -->" + tail
    else:
        anchor = page.rindex("</div>\n<script>") if "</div>\n<script>" in page \
            else page.rindex("</div>")
        page = page[:anchor] + MARK + html + "<!-- /PLAYOFF_POINTS -->\n" + page[anchor:]
    PAGE.write_text(page, encoding="utf-8")
    print(f"\n  injected into {PAGE.relative_to(REPO)} ({len(html):,} bytes)")
    return 0


SECTION = r"""
<hr style="border:none;border-top:3px double var(--ink);margin:2.2rem 0 1.4rem">
<div class="kick">Part Two &middot; The Only Number That Matters</div>
<h1 style="font-size:clamp(1.3rem,3.8vw,1.9rem)">How Good Do You Have To Be?</h1>
<p class="deck">Winning a single game is the wrong target. <em>All you have to do is make the
playoffs</em> &mdash; and the bar for that is lower than almost anyone guesses. Here is what it
costs, in points, across every season since 1999.</p>

<div id="pp-bands" class="read"></div>

<div class="controls">
  <label class="yr" style="font-size:.72rem;letter-spacing:.1em">COMPARE</label>
  <select id="pp-a" style="font-family:'Roboto Mono',monospace;font-size:.75rem;padding:.4rem"></select>
  <select id="pp-b" style="font-family:'Roboto Mono',monospace;font-size:.75rem;padding:.4rem"></select>
  <button id="pp-clear" class="ghost">Clear</button>
</div>

<svg id="pp" viewBox="0 0 880 870" role="img"
  aria-label="Points scored against points allowed for every NFL team season since 1999. Diagonal lines mark the margin needed to be even money for the playoffs and to be ninety percent certain."></svg>

<div class="key">
  <span><i style="border-color:#2a6e3f"></i>made the playoffs</span>
  <span><i style="border-color:#b83a1e"></i>missed</span>
  <span><i style="border-color:#1a1208"></i>even money</span>
  <span><i style="border-color:#c9962a"></i>90% certain</span>
</div>
<p class="read" id="pp-read"></p>

<p class="note"><b>Read the diagonals, not the axes.</b> Both threshold lines run at
forty-five degrees. That is the whole finding: move one point left and one point down and you
stay exactly where you were. A point you prevent is worth a point you score, and the exchange
rate is one&ndash;for&ndash;one.<br><br>

<b>Which matters more?</b> Neither, and the margin of the result is almost comic. Predicting win
rate from points scored and points allowed <em>separately</em> explains <b id="pp-r2a"></b> of the
variation. Predicting it from the <em>difference alone</em> explains <b id="pp-r2b"></b>. Knowing
how a club reached +7 &mdash; whether by scoring 31 and allowing 24, or scoring 17 and allowing 10
&mdash; buys you <b id="pp-gain"></b> of R-squared.<br><br>

<b>So is defense compensatory?</b> Completely. A stingy defense offsets a dull offense point for
point, and a prolific offense offsets a leaky defense exactly as well. &ldquo;Defense wins
championships&rdquo; is not wrong so much as not special &mdash; offense wins precisely as many.
That is a claim this page could not honestly make from the curves above, where the crossing is an
identity. It can make it here, because across these seasons a club&rsquo;s points scored and points
allowed correlate only &minus;0.15: nothing forces the trade, so the trade can be measured.<br><br>

<b>What this does not say.</b> It is descriptive. It reports what the clubs that reached January
looked like, not what any club should go out and buy &mdash; a front office cannot order three
points of margin. Season-long margin also cannot see a club that banked its points in three
blowouts and squeaked through the rest. And the field grew from twelve clubs to fourteen in 2020,
which nudges the bar down; both eras are pooled here.</p>

<script>
(function(){
  const D=__DATA__;
  const S=document.getElementById('pp'), RD=document.getElementById('pp-read');
  // THE PLOT BOX MUST BE SQUARE. Both axes carry the same quantity in the same
  // units, and the entire argument is that the threshold lines run at 45
  // degrees -- move a point left and a point down and you have not moved. With
  // a 792x482 box those lines rendered at slope -0.609 and the note underneath
  // claiming forty-five degrees was simply false on screen. Height is now
  // derived from width so the geometry cannot drift from the sentence again.
  const W=880,L=64,R=24,TP=26,BT=52;
  const PLOT=W-L-R, H=PLOT+TP+BT;
  const xs=D.rows.map(r=>r[2]), ys=D.rows.map(r=>r[3]);
  const lo=Math.floor(Math.min(...xs,...ys)-1), hi=Math.ceil(Math.max(...xs,...ys)+1);
  const X=v=>L+(v-lo)/(hi-lo)*(W-L-R), Y=v=>H-BT-(v-lo)/(hi-lo)*(H-TP-BT);
  const teams=[...new Set(D.rows.map(r=>r[0]))].sort();
  const selA=document.getElementById('pp-a'), selB=document.getElementById('pp-b');
  [[selA,'— first club —'],[selB,'— second club —']].forEach(([s,ph])=>{
    s.innerHTML='<option value="">'+ph+'</option>'+teams.map(t=>'<option>'+t+'</option>').join('');
  });

  function draw(){
    const A=selA.value, B=selB.value;
    let g='';
    for(let v=lo+((5-lo%5)%5); v<=hi; v+=5){
      g+='<line x1="'+X(v)+'" y1="'+TP+'" x2="'+X(v)+'" y2="'+(H-BT)+'" stroke="#e7dcc4"/>'
       + '<line x1="'+L+'" y1="'+Y(v)+'" x2="'+(W-R)+'" y2="'+Y(v)+'" stroke="#e7dcc4"/>'
       + '<text x="'+X(v)+'" y="'+(H-BT+16)+'" font-size="10" fill="#6b5e4a" text-anchor="middle">'+v+'</text>'
       + '<text x="'+(L-8)+'" y="'+(Y(v)+3)+'" font-size="10" fill="#6b5e4a" text-anchor="end">'+v+'</text>';
    }
    // the two thresholds: allowed = scored - margin
    [[D.marEven,'#1a1208','even money'],[D.marLock,'#c9962a','90% certain']].forEach(([m,c,lab])=>{
      const x1=lo+m, x2=hi;
      g+='<line x1="'+X(x1)+'" y1="'+Y(lo)+'" x2="'+X(x2)+'" y2="'+Y(x2-m)+'" stroke="'+c+'" stroke-width="2"/>'
       + '<text x="'+(X(x2)-6)+'" y="'+(Y(x2-m)-7)+'" font-size="11" font-weight="600" fill="'+c+'" text-anchor="end">'
       + lab+' &nbsp;+'+m.toFixed(1)+'</text>';
    });
    D.rows.forEach(r=>{
      const hot = (A&&r[0]===A)||(B&&r[0]===B);
      const dim = (A||B)&&!hot;
      const c = r[5] ? '#2a6e3f' : '#b83a1e';
      g+='<circle cx="'+X(r[2]).toFixed(1)+'" cy="'+Y(r[3]).toFixed(1)+'" r="'+(hot?4.4:2.6)+'" fill="'+c
       + '" fill-opacity="'+(dim?.07:(hot?1:.34))+'"'+(hot?' stroke="#1a1208" stroke-width="1.1"':'')+'>'
       + '<title>'+r[0]+' '+r[1]+' — scored '+r[2].toFixed(1)+', allowed '+r[3].toFixed(1)
       + ', won '+(r[4]*100).toFixed(0)+'%'+(r[5]?' — made the playoffs':' — missed')+'</title></circle>';
    });
    g+='<text x="'+(W/2)+'" y="'+(H-14)+'" font-size="11" fill="#1a1208" text-anchor="middle">points SCORED per game &rarr;</text>'
     + '<text transform="translate(16,'+(H/2)+') rotate(-90)" font-size="11" fill="#1a1208" text-anchor="middle">&larr; points ALLOWED per game</text>';
    S.innerHTML=g;

    let t='';
    [A,B].filter(Boolean).forEach(tm=>{
      const rs=D.rows.filter(r=>r[0]===tm);
      const made=rs.filter(r=>r[5]).length;
      const mar=rs.reduce((s,r)=>s+r[2]-r[3],0)/rs.length;
      t+='<b>'+tm+'</b> — '+rs.length+' seasons, made it '+made+' times ('
        +Math.round(made/rs.length*100)+'%), average margin <b>'+(mar>=0?'+':'')+mar.toFixed(1)+'</b> a game<br>';
    });
    RD.innerHTML = t || 'Pick a club to light up its seasons. Every dot is one team-season; '
      +'the diagonals are what it took to reach January.';
  }
  selA.addEventListener('change',draw); selB.addEventListener('change',draw);
  document.getElementById('pp-clear').addEventListener('click',()=>{selA.value='';selB.value='';draw();});

  document.getElementById('pp-bands').innerHTML =
    '<b>The cut is a cliff, not a slope.</b> Share of clubs reaching the playoffs, by record:<br>'
    + D.bands.filter((b,i)=>i%2===0).map(b=>
        'win '+(b[0]*100).toFixed(0)+'% &rarr; <b>'+(b[1]*100).toFixed(0)+'%</b> made it').join(' &nbsp;&middot;&nbsp; ')
    + '<br>Even money arrives at a <b>'+(D.even*100).toFixed(1)+'%</b> record — about <b>'
    + (D.even*17).toFixed(1)+' wins in 17</b> — and ninety-percent certainty at <b>'
    + (D.lock*100).toFixed(1)+'%</b>.';
  document.getElementById('pp-r2a').textContent=(D.r2sep*100).toFixed(2)+'%';
  document.getElementById('pp-r2b').textContent=(D.r2mar*100).toFixed(2)+'%';
  document.getElementById('pp-gain').textContent='+'+((D.r2sep-D.r2mar)*100).toFixed(2)+' points';
  draw();
})();
</script>
"""


if __name__ == "__main__":
    sys.exit(main())
