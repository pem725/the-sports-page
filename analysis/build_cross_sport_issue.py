"""Assemble queue/078-cross-sport-persistence.html."""
from pathlib import Path

ANALYSIS = Path(__file__).parent
QUEUE = Path("/home/pem725/GitTemp/the-sports-page/queue")
chart = (ANALYSIS / "cross_sport_chart.svg").read_text()

html = f"""<!-- PUBLISH-META
topic: Methods
tags: Methods, Reader's Defense, Cross-Sport, Persistence, NBA, NFL, NHL, MLB
-->
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Sports Page &mdash; Issue No. __ &mdash; June __, 2026</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Roboto+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{--ink:#1a1208;--cream:#f5f0e8;--aged:#e0d8c5;--rust:#b83a1e;--steel:#2c4a6e;--gold:#c9962a;--muted:#6b5e4a;--div:#c8b99a;--card:#ede5d2;--green:#2a6e3f}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--aged);color:var(--ink);font-family:'Libre Baskerville',Georgia,serif;font-size:16px;line-height:1.72;padding:1.5rem 1rem 3rem}}
.masthead{{max-width:820px;margin:0 auto;text-align:center;border-top:4px solid var(--ink);padding:.5rem 0 0}}
.kicker{{font-family:'Roboto Mono',monospace;font-size:.68rem;letter-spacing:.22em;text-transform:uppercase;color:var(--muted)}}
.title{{font-family:'Playfair Display',serif;font-size:clamp(2rem,5vw,3.2rem);font-weight:700;line-height:1.1;letter-spacing:.04em;text-transform:uppercase;margin:.1rem 0}}
.tagline{{font-family:'Playfair Display',serif;font-style:italic;font-size:.95rem;color:var(--muted);margin:.2rem 0 .4rem}}
.datebar{{display:flex;justify-content:space-between;font-family:'Roboto Mono',monospace;font-size:.65rem;color:var(--muted);letter-spacing:.1em;border-top:1px solid var(--ink);border-bottom:3px double var(--ink);padding:.3rem 0;margin-top:.3rem}}
.paper{{max-width:820px;margin:.8rem auto 0;background:var(--cream);padding:2.5rem 3rem 2.8rem;box-shadow:0 6px 40px rgba(0,0,0,.2);border:1px solid var(--div)}}
@media(max-width:600px){{.paper{{padding:1.6rem 1.4rem}}}}
.hed{{font-family:'Playfair Display',serif;font-size:clamp(2rem,5vw,3rem);font-weight:900;line-height:1.12;margin-bottom:.4rem}}
.hed em{{color:var(--rust);font-style:italic}}
.deck{{font-family:'Libre Baskerville',serif;font-style:italic;font-size:1.1rem;color:var(--muted);border-left:3px solid var(--rust);padding-left:.9rem;margin:.8rem 0 1.2rem;line-height:1.5}}
.byline{{font-family:'Roboto Mono',monospace;font-size:.68rem;letter-spacing:.1em;color:var(--muted);text-transform:uppercase;margin-bottom:1.4rem}}
.stat-row{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--div);border:1px solid var(--div);margin:0 0 1.8rem}}
@media(max-width:460px){{.stat-row{{grid-template-columns:1fr 1fr}}}}
.sc{{background:var(--card);padding:1rem .8rem;text-align:center}}
.sc .v{{font-family:'Playfair Display',serif;font-size:2.2rem;font-weight:900;line-height:1}}
.sc .v.bad{{color:var(--rust)}} .sc .v.now{{color:var(--steel)}} .sc .v.good{{color:var(--green)}}
.sc .l{{font-family:'Roboto Mono',monospace;font-size:.63rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-top:.25rem}}
.sh{{font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;border-bottom:2px solid var(--rust);padding-bottom:.2rem;margin:2rem 0 1rem}}
.pull{{border-top:2px solid var(--ink);border-bottom:2px solid var(--ink);padding:.9rem 0;margin:1.8rem 0;text-align:center}}
.pull p{{font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:700;font-style:italic;color:var(--steel);line-height:1.45}}
.pull cite{{font-family:'Roboto Mono',monospace;font-size:.65rem;color:var(--muted);letter-spacing:.1em;display:block;margin-top:.5rem}}
.box{{background:var(--steel);color:#dce8f5;padding:1.5rem 1.8rem;margin:1.8rem 0}}
.box h3{{font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:.8rem}}
.box p{{font-size:.92rem;color:#c8daed;line-height:1.65;margin-bottom:.7rem}}
.box p:last-child{{margin-bottom:0}}
.chart-wrap{{background:var(--card);border:1px solid var(--div);padding:1.2rem;margin:1.5rem 0}}
.chart-label{{font-family:'Roboto Mono',monospace;font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:.6rem}}
svg.chart{{width:100%;height:auto;display:block}}
.footer{{border-top:3px double var(--ink);padding-top:.7rem;margin-top:2rem;display:flex;justify-content:space-between;flex-wrap:wrap;gap:.3rem;font-family:'Roboto Mono',monospace;font-size:.63rem;color:var(--muted);letter-spacing:.07em}}
hr{{border:none;border-top:1px solid var(--div);margin:1.5rem 0}}
</style>
</head>
<body>

<header class="masthead">
  <div class="kicker">A Daily Statistics Newsletter</div>
  <h1 class="title">The Sports Page</h1>
  <p class="tagline">"One strange number, explained."</p>
  <div class="datebar"><span>Vol. I, No. __</span><span>Cross-Sport Predictability</span><span>June __, 2026</span></div>
</header>

<main class="paper">

  <h2 class="hed">The NBA Repeats. The NFL Doesn't. <em>Both Are More Predictable Than the Snow.</em></h2>
  <p class="deck">A reader asked the right next question: this newsletter's predictability work has so far been Major League Baseball against Colorado snowfall. What happens if you point the same test at football, hockey, basketball? The chart below is the answer. The four North American sports separate by more than a factor of two. The order is not random. It tracks how much of a roster carries over from one season to the next.</p>
  <p class="byline">The Sports Page &middot; Method: pooled lag-1 Pearson r of team win pct &middot; Data: 1985&ndash;2025 final standings, all four leagues, plus NOAA regional snowfall</p>

  <div class="stat-row">
    <div class="sc"><div class="v good">+.649</div><div class="l">NBA lag-1 r</div></div>
    <div class="sc"><div class="v bad">+.343</div><div class="l">NFL lag-1 r</div></div>
    <div class="sc"><div class="v now">~0</div><div class="l">Colorado snow lag-1 r</div></div>
  </div>

  <p>The test is the same one we ran for Major League Baseball in Issue #74 and for Colorado snowfall in Issue #75. Pull final standings for every team, every year, between 1985 and the present. Pair each team's year with the team's record the following year. Compute the Pearson correlation between this-year and next-year winning percentages. The result is the system's lag-one autocorrelation &mdash; a single number summarizing how much memory the system carries from one season to the next.</p>

  <p>We are showing five rows on the chart. Four of them are professional sports leagues, each represented by a pool of every team-to-team year-over-year pair across forty seasons. The fifth is the Colorado ski-belt regional snowfall index from Issue #75 &mdash; the average across five long-running NOAA stations, the apples-to-apples aggregate-to-aggregate comparison the methodology demands. Comparing one weather station to a whole league would be exactly the kind of unfair smoothing we corrected in Issue #75. Five rows; five aggregates.</p>

  <p>Four leagues plus one snow region, run head to head:</p>

  <div class="chart-wrap">
    <div class="chart-label">Figure 1 &middot; Cross-sport predictability scoreboard &middot; lag-1 r, 1985&ndash;2025</div>
{chart}
  </div>

  <h3 class="sh">Why the NBA wins</h3>

  <p>The National Basketball Association has the highest year-over-year persistence of any sport we tested. The correlation of .649 says, roughly, that knowing a team's win percentage last season explains about <strong>forty-two percent</strong> of the variance in its win percentage this season. That is enormous for a competitive league. It is essentially the highest figure that any North American team sport could produce given roster turnover and luck.</p>

  <p>The cause is roster geometry. Five players are on the floor at any time. The top one accounts for nearly thirty percent of a team's offensive load. Stars on max contracts are locked in for four or five years. The draft is a lottery weighted toward bad teams, but the rookie scale lets good teams retain stars cheaply for their first decade. When LeBron James, Stephen Curry, or Nikola Joki&cacute; spends ten years in a uniform, that uniform's win-loss record carries an enormous fraction of his quality with it. A bad NBA team next year is, more often than not, a bad NBA team this year too &mdash; because it had the same five players starting and the same one stuck-on-the-bench rookie.</p>

  <h3 class="sh">Why the NFL loses</h3>

  <p>The National Football League sits at the bottom of the sports scoreboard with a lag-one r of .343. That is still more than ten times more predictable than Steamboat Springs's snow, but it is meaningfully lower than the other three leagues. Knowing last year's NFL record gives you about <strong>twelve percent</strong> of next year's variance.</p>

  <p>Three structural features push the number down. <strong>First</strong>, the season is sixteen or seventeen games. Variance grows when sample sizes shrink. A .500 NFL team is often a .500 team for the season but a .700 team for any six-week stretch within it, and which stretch happens to fall on which weeks matters a great deal for the final record. <strong>Second</strong>, the salary cap is hard. The Patriots-of-the-2010s dynasty type is not impossible (the Chiefs of the 2020s exist), but the league's compensation rules force aggressive roster cycling. Teams that win in the cap-strapped era have to let veterans walk; teams that lose can stockpile draft picks. <strong>Third</strong>, the draft delivers immediate impact &mdash; rookie quarterbacks, in particular, can transform a roster's expected wins in a single offseason. A wholesale turnover of expected outcomes year-over-year is built into the league.</p>

  <p>That is why every September a football column can plausibly argue that any team has a chance, and why those columns are usually wrong about <em>which</em> team will surprise. The variance is there. The predictability of who carries it is low.</p>

  <h3 class="sh">Baseball and hockey, in between</h3>

  <p>Major League Baseball comes in at r = .490, lower than the NBA or NHL because rosters are deep (a single player accounts for less of the team's identity) and because the 162-game schedule, ironically, contains more single-game variance than fans of the more popular sports usually credit it for. Two great teams are basically indistinguishable over fifteen games, and there are nine sets of fifteen games in a season; that produces a lot of expected-record drift even between teams whose underlying talent has not changed.</p>

  <p>The National Hockey League sits at r = .618 &mdash; closer to the NBA than to the MLB. Hockey is closer to a small-roster, star-anchored sport than its 23-man dressed lineup suggests; a top line, a top defensive pair, and a starting goaltender can carry an outsized share of run-prevention, and those positions tend to stay together for long stretches. The NHL also has fewer competitive teams than fans like to admit &mdash; the gap between contenders and rebuilders, year over year, is unusually persistent.</p>

  <div class="pull">
    <p>The NBA's persistence is the league's superstar economics. The NFL's volatility is the league's draft and cap economics. The snow simply has no year-over-year memory to test.</p>
    <cite>Cross-Sport Persistence</cite>
  </div>

  <h3 class="sh">A word on the snow row</h3>

  <p>The Colorado snow row sits at the bottom of the chart for the reason Issue #75 already showed: at the regional level, with five stations averaged, the lag-one autocorrelation is essentially zero, and conditioning on the El Ni&ntilde;o-Southern-Oscillation state in Issue #75's leave-one-out test made the prediction <em>worse</em>, not better. The two predictability tests this newsletter has carried out on snowfall have agreed, in two different ways, that the signal a casual analog-matcher would expect is not actually there in the data. We are not invoking ocean-temperature regimes as a hidden predictor that would rescue the snow; we already checked. The snow row is in the chart as the honest baseline against which the sports rows can be read.</p>

  <h3 class="sh">What this means for fans</h3>

  <p>A few practical takeaways. When a basketball columnist tells you in October that the season's eventual champion is "wide open," they are wrong by an unusually wide margin. The NBA's r-squared on the prior year is forty-two percent &mdash; before training camp, before injury news, before a single game. When a football columnist tells you the same thing, they are statistically much closer to right. The NFL's r-squared is twelve percent. A reasonable preseason model is mostly going to be wrong about who finishes where.</p>

  <p>Persistence is also a useful predictor of <em>narrative</em> shape. The NBA generates dynasty stories because there really are dynasties. The NFL generates upset stories because there really are upsets. Baseball lives in the middle &mdash; long enough seasons to have something like dynasties (the Yankees of the late nineties, the Astros of the late 2010s), short enough roster turnover to keep them from being purely structural. The reason every sport has a different shape of fandom is partly because the seasons themselves have different memory.</p>

  <h3 class="sh">A note on the framework</h3>

  <div class="box">
    <h3>What the reader should hear</h3>
    <p>"Predictable" is not a property of a sport. It is a property of a sport's economics combined with its sample sizes combined with its rules. Change the cap; the NBA gets more like the NFL. Change the schedule length; the NFL gets more like the NBA. Change roster construction philosophy; baseball moves up or down on the scoreboard. The number on the chart is a snapshot of how a system happens to be designed right now.</p>
    <p>This is the part of the cross-domain comparison we have been building toward. The same statistical test gives wildly different answers across systems that look superficially similar (four sports leagues, all with thirty teams, all with playoffs) because the underlying economics are different. We will follow this piece with several more in the same vein &mdash; regression to the mean as the universal predictor, mechanistic models that beat statistical ones, and the measurement-first essay.</p>
  </div>

  <hr>

  <div class="box" style="background:var(--ink)">
    <h3>Notes &amp; sources</h3>
    <p style="color:#c8b99a">MLB: MLB Stats API regular-season standings 1985&ndash;2025, 1,158 same-team year-over-year pairs. NFL: ESPN sports API regular-season standings 1986&ndash;2025, 1,195 pairs. NBA: ESPN sports API 1985&ndash;2025, 1,140 pairs. NHL: ESPN sports API 1985&ndash;2025, with winning percentage computed as (wins + 0.5*ties) / games played; 1,073 pairs.</p>
    <p style="color:#c8b99a">Snowfall: Colorado ski-belt regional index, the average across five long-running NOAA GHCN-Daily stations (Aspen, Crested Butte, Steamboat Springs, Telluride, Vail). 35 lag-1 pairs since 1985. Each season's index is included only when at least three of the five stations report at least 150 days of the Nov-through-Apr ski-season window. The single-station Steamboat-only series from Issue #74 produced the same answer (r ≈ 0) and is omitted here as a duplicate.</p>
    <p style="color:#c8b99a">Pearson r computed as a pooled correlation across all eligible (team, year, year+1) triples. The strike-shortened 1994 MLB season and pandemic-shortened 2020 across all four sports are included on the basis that winning percentage is a fraction comparable across game counts. Excluding those years moves no league's r by more than 0.02.</p>
  </div>

  <div class="footer">
    <span>The Sports Page &middot; Issue No. __</span>
    <span>Cross-Sport Persistence</span>
    <span>June __, 2026 &middot; New York, NY</span>
  </div>
</main>

</body>
</html>
"""

dest = QUEUE / "078-cross-sport-persistence.html"
dest.write_text(html)
print(f"Wrote {dest}")
