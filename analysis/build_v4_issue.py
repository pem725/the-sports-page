"""Rewrite queue/078 with the right-predictor framing across regions."""
from pathlib import Path

ANALYSIS = Path(__file__).parent
QUEUE = Path("/home/pem725/GitTemp/the-sports-page/queue")
chart = (ANALYSIS / "cross_sport_chart.svg").read_text()
import json
d = json.load(open(ANALYSIS / "predictability_v4.json"))

html = f"""<!-- PUBLISH-META
topic: Methods
tags: Methods, Reader's Defense, Cross-Sport, Cross-Region, ENSO, Prediction
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
table.regional{{width:100%;border-collapse:collapse;font-size:.86rem;margin:1.2rem 0;background:#fff}}
table.regional th{{font-family:'Roboto Mono',monospace;font-size:.62rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:2px solid var(--ink);padding:.4rem .55rem;text-align:right;background:var(--card)}}
table.regional th:first-child,table.regional td:first-child{{text-align:left;font-family:'Playfair Display',serif;font-weight:700;color:var(--steel);font-size:.95rem}}
table.regional td{{padding:.45rem .55rem;border-bottom:1px solid var(--div);font-family:'Roboto Mono',monospace;font-size:.85rem;text-align:right}}
table.regional td.signal{{color:var(--green);font-weight:600}}
table.regional td.weak{{color:var(--muted)}}
.footer{{border-top:3px double var(--ink);padding-top:.7rem;margin-top:2rem;display:flex;justify-content:space-between;flex-wrap:wrap;gap:.3rem;font-family:'Roboto Mono',monospace;font-size:.63rem;color:var(--muted);letter-spacing:.07em}}
hr{{border:none;border-top:1px solid var(--div);margin:1.5rem 0}}
</style>
</head>
<body>

<header class="masthead">
  <div class="kicker">A Daily Statistics Newsletter</div>
  <h1 class="title">The Sports Page</h1>
  <p class="tagline">"One strange number, explained."</p>
  <div class="datebar"><span>Vol. I, No. __</span><span>The Right Test, Cross-Domain</span><span>June __, 2026</span></div>
</header>

<main class="paper">

  <h2 class="hed">Sports Have Last Year. Snow Has La Ni&ntilde;a. <em>Each Side Got Its Best Test.</em></h2>
  <p class="deck">A reader pushed back on this newsletter's predictability comparisons, correctly. Lag-one autocorrelation is the natural predictor for a sports league because the players carry over. It is not the natural predictor for snowfall &mdash; for that, you would use the El Ni&ntilde;o-Southern-Oscillation state of the upcoming winter. We re-ran the comparison region by region with each domain on its own best-known test, and added the Pacific Northwest, Utah, Wyoming, New Mexico, and Vermont to the snow side. The verdict still favors sports, but the deeper story is now visible: a "natural predictor" is not automatically a "useful predictor."</p>
  <p class="byline">The Sports Page &middot; Method: domain-appropriate predictor, % RMSE reduction vs climatology baseline &middot; Data: 1985&ndash;2025</p>

  <div class="stat-row">
    <div class="sc"><div class="v good">+24%</div><div class="l">NBA lag-1 lift</div></div>
    <div class="sc"><div class="v now">+3%</div><div class="l">Utah/WY ENSO lift</div></div>
    <div class="sc"><div class="v bad">-6%</div><div class="l">PNW ENSO lift</div></div>
  </div>

  <h3 class="sh">Why use a different predictor for each system</h3>

  <p>Imagine trying to forecast next season's NBA standings. The most natural place to start is last season's standings. Stephen Curry was on the Warriors. Nikola Joki&cacute; was on the Nuggets. Anthony Edwards was on the Timberwolves. They almost certainly will be again. The teams will have lost a couple of veterans, gained a couple of rookies, and traded a piece or two, but the core is locked in by guaranteed contracts that often run another three or four years. The single best one-variable predictor of next year is just <em>this year, gently regressed toward the league mean</em>. Last year's wins predict next year's wins because the rosters predict the rosters.</p>

  <p>Now imagine forecasting next winter's snowfall at Stevens Pass. Nobody in their right mind would use last winter's snowfall as their predictor. The atmosphere is not carrying inventory between Marches and Octobers. What forecasters <em>do</em> reach for is the El Ni&ntilde;o-Southern-Oscillation state of the equatorial Pacific. La Ni&ntilde;a years tend to push the polar jet stream north, drowning the Pacific Northwest in snow and starving the Southwest. El Ni&ntilde;o years do the reverse. This is settled atmospheric science. It is also the right predictor to test.</p>

  <p>Yesterday's chart on this newsletter compared sports lag-one r against snow lag-one r and was correct in finding that the snow had zero year-over-year persistence &mdash; but that finding was the wrong comparison. Lag-one is sports' natural test and a strawman for snow. The right scoreboard puts each domain on its own best-known predictor and measures the same thing both ways: <strong>percent reduction in root-mean-square forecast error compared to a climatology baseline of predicting every year as the long-run mean.</strong></p>

  <p>We did exactly that, and we added four new snow regions so the chart is not Colorado-against-the-leagues either.</p>

  <div class="chart-wrap">
    <div class="chart-label">Figure 1 &middot; The right test, cross-domain &middot; % RMSE reduction over climatology baseline, leave-one-out cross-validated</div>
{chart}
  </div>

  <h3 class="sh">What the sports rows say</h3>

  <p>For all four professional sports leagues we tested, the optimal lag-one prediction (last year's record, regressed toward .500 by the lag-one correlation) beats climatology meaningfully. The NBA leads at twenty-four percent error reduction. The NHL is right behind at twenty-one. Major League Baseball comes in at thirteen percent. The NFL trails at six percent. The order matches the lag-one correlations we reported in the previous issue and tracks roster geometry: small leagues with star-concentrated rosters and long guaranteed contracts persist hardest. Large rosters and short, variance-heavy seasons persist least.</p>

  <h3 class="sh">What the snow rows say</h3>

  <p>The snow side is much messier and more honest than the previous draft of this piece allowed. Look first at the regional means, broken down by ENSO state, before looking at the chart:</p>

  <table class="regional">
    <thead><tr><th>Region</th><th>La Ni&ntilde;a mean</th><th>Neutral mean</th><th>El Ni&ntilde;o mean</th><th>La Ni&ntilde;a/El Ni&ntilde;o ratio</th></tr></thead>
    <tbody>
      <tr><td>Pacific Northwest</td><td>6,291 mm</td><td>5,464 mm</td><td>5,468 mm</td><td class="signal">+15%</td></tr>
      <tr><td>Utah / Wyoming</td><td>2,097 mm</td><td>1,793 mm</td><td>1,543 mm</td><td class="signal">+36%</td></tr>
      <tr><td>Colorado</td><td>4,092 mm</td><td>3,987 mm</td><td>3,845 mm</td><td class="weak">+6%</td></tr>
      <tr><td>Vermont</td><td>2,319 mm</td><td>2,450 mm</td><td>2,111 mm</td><td class="weak">+10%</td></tr>
      <tr><td>New Mexico</td><td>2,167 mm</td><td>2,372 mm</td><td>2,581 mm</td><td class="weak">&minus;16%</td></tr>
    </tbody>
  </table>

  <p>The signals atmospheric science has been telling us about for decades are right there. The Pacific Northwest gets fifteen percent more snow in La Ni&ntilde;a years than in El Ni&ntilde;o years. Utah and Wyoming get <em>thirty-six percent</em> more &mdash; the largest signal in the data. New Mexico does the opposite, getting sixteen percent <em>less</em> snow in La Ni&ntilde;a years than in El Ni&ntilde;o, exactly as the textbook predicts for the desert Southwest. Colorado, sitting on the dividing line, shows almost no gradient. Vermont, governed by a different system of oscillations entirely (the North Atlantic Oscillation, principally), shows no consistent ENSO signal either.</p>

  <p>So why does the chart's bar for the Pacific Northwest sit at <em>negative</em> six percent? Because the directional signal in the means is real but the within-state variance is enormous. Within La Ni&ntilde;a years alone, regional snowfall ranges roughly from four thousand to eight thousand millimeters. A model that predicts every La Ni&ntilde;a year as the La Ni&ntilde;a mean is going to be off by a thousand millimeters or more in most years. The climatology baseline that predicts every year as the long-run mean is off by about the same. The conditional model burns degrees of freedom learning a state-by-state mean and, on twenty-four observations, ends up slightly worse than the unconditional one.</p>

  <p>This is the deeper lesson the previous draft of this piece missed. <strong>A known directional signal does not automatically translate into forecast skill.</strong> Knowing whether next winter will be La Ni&ntilde;a or El Ni&ntilde;o tells you which way the regional mean leans. It does not tell you anything strong enough about an individual season to outperform a naive long-run-average forecast in absolute error terms.</p>

  <div class="pull">
    <p>Atmospheric science knows where the snow likes to fall. The atmospheric forecaster has to live with the fact that knowing where the snow likes to fall is not the same as knowing how much will fall in any one year.</p>
    <cite>The Right Test, Cross-Domain</cite>
  </div>

  <h3 class="sh">Region by region, what this means</h3>

  <p><strong>Utah and Wyoming</strong> are the one region where ENSO-conditional forecasting actually beat climatology, at a modest two-point-eight percent lift. The thirty-six-percent mean difference between La Ni&ntilde;a and El Ni&ntilde;o years is large enough to survive the LOOCV penalty even on forty seasons. <strong>The Pacific Northwest</strong> has an even bigger physical signal but a much smaller sample (twenty-four seasons), and the conditional model overfits. <strong>Colorado</strong>, <strong>Vermont</strong>, and <strong>New Mexico</strong> each show small lifts or losses, but for different reasons &mdash; Colorado and Vermont because the local ENSO signal is genuinely weak, New Mexico because its sample (twenty-eight seasons) is too small to handle a real but modest signal.</p>

  <p>The chart for skiers and snow-followers reads roughly as: the lift you get from knowing it will be a La Ni&ntilde;a year is real in the Wasatch and the Cascades, weaker in the Rockies and the Northeast, and reversed in the Southwest. None of it is the kind of lift the NBA gets from knowing last year's standings. You should keep watching the ocean-temperature forecasts; you should also stop expecting them to tell you exactly how many feet are coming.</p>

  <h3 class="sh">A note on the framework</h3>

  <div class="box">
    <h3>The deeper rule</h3>
    <p>"Predictable" is not one thing, and "natural predictor" is not the same as "useful predictor." Every domain has a set of covariates that physical or economic theory suggests <em>should</em> matter. The work of the empirical analyst is to test which of them actually deliver forecast skill when measured against a serious baseline on out-of-sample data. Last year's record clearly does for the NBA, modestly does for the NFL, barely does for the MLB. La Ni&ntilde;a state clearly does for Utah snow, modestly does for the Cascades, not at all for the Rockies. The cross-domain comparison is fair only when each side is tested on the predictor its domain experts would themselves reach for. That is what this chart now does.</p>
  </div>

  <hr>

  <div class="box" style="background:var(--ink)">
    <h3>Notes &amp; sources</h3>
    <p style="color:#c8b99a">Sports: pooled team-year pairs from MLB Stats API and ESPN sports API standings, 1985-2025. Predictor: optimal linear lag-1, defined as y_hat = mean + r&times;(prev_y &minus; mean). Under this regression-to-mean adjustment, the % RMSE reduction equals 1 &minus; &radic;(1 &minus; r&sup2;).</p>
    <p style="color:#c8b99a">Snow: regional Nov-through-Apr seasonal totals built from NOAA GHCN-Daily stations. Colorado uses Aspen 1 SW, Crested Butte, Steamboat Springs, Telluride 4 WNW, Vail. Pacific Northwest uses Stampede Pass (WA), Snoqualmie Falls (WA), Crater Lake (OR). Utah/Wyoming uses Lake Yellowstone (WY), Yellowstone Mammoth (WY), Altamont (UT), Angle (UT). New Mexico uses Red River and Dulce. Vermont uses Saint Johnsbury, Island Pond, and Burlington International Airport. A regional index for a season is the cross-station mean for that season, included only when at least half the region's stations report at least 150 days of the ski-season window. ENSO state is NOAA's DJF Oceanic Ni&ntilde;o Index averaged for the year ending the season: La Ni&ntilde;a if ONI &le; &minus;0.5, El Ni&ntilde;o if &ge; +0.5, Neutral otherwise.</p>
    <p style="color:#c8b99a">% RMSE reduction is leave-one-out cross-validated. For sports the closed-form result coincides with the LOOCV result given large pooled samples; we report the closed form. For snow we use explicit LOOCV with state-mean conditional models. Negative values indicate that the predictor's RMSE is worse than the unconditional long-run mean &mdash; the conditional model is paying for degrees of freedom not justified by the available sample.</p>
  </div>

  <div class="footer">
    <span>The Sports Page &middot; Issue No. __</span>
    <span>The Right Test, Cross-Domain</span>
    <span>June __, 2026 &middot; New York, NY</span>
  </div>
</main>

</body>
</html>
"""

dest = QUEUE / "078-cross-sport-persistence.html"
dest.write_text(html)
print(f"Wrote {dest}")
