"""Assemble queue/074-predictability.html with the inline SVG chart."""
from pathlib import Path

ANALYSIS = Path(__file__).parent
QUEUE = Path("/home/pem725/GitTemp/the-sports-page/queue")

# Read the chart
chart = (ANALYSIS / "predictability_chart.svg").read_text()

# Article HTML
html = f"""<!-- PUBLISH-META
topic: Methods
tags: Methods, Predictability, Autocorrelation, Reader's Defense, Weather, Mets:mlb
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
.hed{{font-family:'Playfair Display',serif;font-size:clamp(2rem,5vw,3.1rem);font-weight:900;line-height:1.12;margin-bottom:.4rem}}
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
  <div class="datebar"><span>Vol. I, No. __</span><span>Predictability</span><span>June __, 2026</span></div>
</header>

<main class="paper">

  <h2 class="hed">The Mets Are Seventy Times More Predictable <em>Than the Snow</em>.</h2>
  <p class="deck">A reader, having watched yesterday's analog-year piece, asked a question we did not expect: <em>is the weather more predictable than the Mets?</em> Most fans would answer yes without thinking. We checked. The numbers are not close. Most fans would be very wrong.</p>
  <p class="byline">The Sports Page &middot; A Reader's Defense Companion &middot; Steamboat Springs snowfall vs. all of Major League Baseball</p>

  <div class="stat-row">
    <div class="sc"><div class="v bad">0.007</div><div class="l">Snowfall yr-over-yr r</div></div>
    <div class="sc"><div class="v good">0.490</div><div class="l">MLB win-pct yr-over-yr r</div></div>
    <div class="sc"><div class="v now">70&times;</div><div class="l">Baseball's edge</div></div>
  </div>

  <p>The question came in by way of friend of the newsletter Tim, who arrived at it confessionally. Tim has spent twenty years of his life trying to match this ski season's snowfall against last year's, the year before last's, the great years of his childhood. He used the same kind of nearest-neighbor analogy that Wall Street uses against 1994 and that we used yesterday against 2021. Tim's read of his own history: <em>folly.</em> Snow seasons, he said, do not seem to repeat themselves. Each year arrives fresh, owing the previous year nothing.</p>

  <p>That is a falsifiable claim. We can ask, of any time series, how much last year's value predicts next year's. The standard answer is the lag-one autocorrelation &mdash; the Pearson correlation between the value in year t and the value in year t plus one. If the autocorrelation is high, the system has memory: this year's reading tells you something about next year's. If it is low, each year is a coin flip drawn from the same urn.</p>

  <h3 class="sh">Two histograms, one chart</h3>

  <p>The chart below shows the two systems side by side. On the left: total seasonal snowfall (November through April) at Steamboat Springs, Colorado, every season from 1985 onward, plotted as this year's value against next year's. The Steamboat record at NOAA station USC00057936 covers more than a hundred years; we used the modern subset that overlaps with the MLB data on the right.</p>

  <p>On the right: every team-to-team year-over-year pair in Major League Baseball from 1985 to 2025. Each dot is one team in one year, plotted against the same team in the next year. Win pct on both axes. We drew a random sample of three hundred dots so the cloud is readable, but the correlation reported is over all eleven hundred fifty-eight pairs.</p>

  <div class="chart-wrap">
    <div class="chart-label">Figure 1 &middot; Year-over-year persistence &middot; Steamboat snowfall vs. MLB win pct</div>
{chart}
  </div>

  <h3 class="sh">What the numbers say</h3>

  <p>The snow scatter on the left is a cloud. The correlation is <strong>0.007</strong>. That is statistically zero. The line through the dots is flat. If you tell me that Steamboat got two thousand millimeters of snow last year, I have learned almost nothing about how much snow it will get next year. Tim was right about his own twenty years of mental analog-matching: it was folly. Each ski season is, statistically, a fresh draw.</p>

  <p>The baseball scatter on the right is something else entirely. The dots tilt up from left to right. A team that posted a .400 winning percentage last year is much more likely to post a .400 this year than a .600. A team that won ninety-five games last year is more likely to be near ninety this year than near seventy. The correlation is <strong>0.490</strong>. By the standard rule of thumb, last year's record explains roughly <em>twenty-four percent</em> of the variance in next year's. That is enormous compared to the snow.</p>

  <div class="pull">
    <p>If you want to predict next season, bet on baseball. Tim's twenty years of ski matching had nothing to lean on. Twenty years of baseball matching would have done quite a bit better.</p>
    <cite>Predictability</cite>
  </div>

  <p>And the New York Mets specifically? Their own year-over-year autocorrelation is <strong>0.407</strong> &mdash; slightly less than the league average, but only by a hair. The Mets are not the most volatile team in baseball. They are roughly as predictable as the average major-league franchise, which is to say, seventy times more predictable than the snow at Steamboat.</p>

  <h3 class="sh">Why the gap?</h3>

  <p>The economic answer is straightforward. A baseball roster is mostly the same year over year. Players are signed to multi-year contracts. Front offices, when they are good, stay good for a while; when they are bad, they tend to stay bad. Talent, infrastructure, scouting, and player development do not get replaced overnight. So last year's wins encode last year's roster, and a healthy share of last year's roster is going to be the team you watch this year.</p>

  <p>The atmospheric answer for snowfall is the opposite. Total Colorado-mountain winter precipitation depends on jet-stream meanders, on El Ni&ntilde;o-Southern-Oscillation states, on stochastic pressure differentials over the Pacific that have no preference for last year's value. There is no contract structure for the atmosphere. Each ski season inherits very little from the one before.</p>

  <p>This is exactly what makes analog-matching a useful exercise for baseball and a misleading one for skiing. <em>Pattern-matching works only where the patterns persist.</em> Yesterday's piece found 2026 in the neighborhood of 2021 because the league is the kind of system that builds neighborhoods. The same exercise on Tim's ski history would have built nothing &mdash; or worse, built a sense of seasonal narrative that the data does not support.</p>

  <h3 class="sh">A defensive reader's takeaway</h3>

  <div class="box">
    <h3>The trap</h3>
    <p>When somebody &mdash; pundit, gambler, ski-resort marketing department, market strategist &mdash; tells you that a year resembles some prior year and that you should accordingly expect similar things to happen, your first question should not be "is the resemblance close?" Your first question should be: <em>how autocorrelated is the underlying system?</em> If the lag-one r is close to zero, the resemblance is meaningless even when it is real, because the next year is going to draw from the same hat no matter what was drawn last time.</p>
    <p>This newsletter does analog-matching for MLB because MLB has the persistence to make it informative. We will not be doing it for ski seasons. Tim got there first.</p>
  </div>

  <hr>

  <div class="box" style="background:var(--ink)">
    <h3>Notes &amp; sources</h3>
    <p style="color:#c8b99a">Snowfall: NOAA GHCN-Daily station USC00057936 (Steamboat Springs, CO). "Season" defined as November 1 through April 30; only seasons with at least 150 days reported are included. Resulting series: 31 ski seasons since 1985, producing 27 lag-1 pairs after gaps.</p>
    <p style="color:#c8b99a">Baseball: MLB Stats API standings 1985&ndash;2025 inclusive, all teams in both leagues, regular season records. Strike-shortened 1994 and pandemic-shortened 2020 included on the basis that the win-pct fraction is comparable across game counts. 1,158 team-year-pairs total. Mets-only series: 40 pairs.</p>
    <p style="color:#c8b99a">Lag-1 autocorrelation is the Pearson correlation between the value in year t and the value in year t+1, taken across all eligible adjacent-year pairs in the series. For pooled MLB, pairs are stratified by team (so the Yankees in 1995 contribute a pair with the Yankees in 1996, not the Tigers in 1996). The chart on the right shows a uniform random sample of 300 of the 1,158 team-pairs for legibility; the reported r is over all 1,158 pairs.</p>
  </div>

  <div class="footer">
    <span>The Sports Page &middot; Issue No. __</span>
    <span>Predictability</span>
    <span>June __, 2026 &middot; New York, NY</span>
  </div>
</main>

</body>
</html>
"""

dest = QUEUE / "074-predictability.html"
dest.write_text(html)
print(f"Wrote {dest}")
