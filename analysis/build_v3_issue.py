"""Rewrite queue/075 with the apples-to-apples comparison."""
from pathlib import Path
import json

ANALYSIS = Path(__file__).parent
QUEUE = Path("/home/pem725/GitTemp/the-sports-page/queue")
chart = (ANALYSIS / "predictability_v3_chart.svg").read_text()
d = json.load(open(ANALYSIS / "predictability_v3.json"))

html = f"""<!-- PUBLISH-META
topic: Methods
tags: Methods, Reader's Defense, Prediction, Inference, ENSO, Cross-Validation
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
  <div class="datebar"><span>Vol. I, No. __</span><span>Predictability, Part II</span><span>June __, 2026</span></div>
</header>

<main class="paper">

  <h2 class="hed">A Fair Fight Was Asked For. <em>We Ran Two. Snow Lost Both.</em></h2>
  <p class="deck">Yesterday's piece pitted snowfall at a single ski resort against thirty teams' worth of pooled baseball. A reader caught it: one cohort had been averaged smooth, the other had not. To find out whether the comparison's verdict survived, we built a Colorado-region snowfall index from five ski-belt stations and re-ran every test side by side at matching scales. The bigger fight is fairer. The bigger fight is also more lopsided.</p>
  <p class="byline">The Sports Page &middot; Predictability, Part II &middot; Sources: NOAA GHCN-Daily, ENSO ONI, MLB Stats API</p>

  <div class="stat-row">
    <div class="sc"><div class="v bad">&minus;0.01</div><div class="l">CO ski region lag-1 r</div></div>
    <div class="sc"><div class="v good">+0.70</div><div class="l">MLB league OPS lag-1 r</div></div>
    <div class="sc"><div class="v good">+48%</div><div class="l">League profile vs climatology</div></div>
  </div>

  <p>The reader's objection was correct and worth taking seriously. Yesterday we computed a Pearson r of 0.49 for baseball by pooling more than a thousand year-over-year team pairs across all of Major League Baseball. We compared that to an r of 0.007 for snowfall at a single weather station in Steamboat Springs. Both numbers are honest; the comparison between them is not, because pooling thirty teams smooths a great deal of single-team noise while one station's worth of snow gets no comparable benefit.</p>

  <p>The fair comparisons go at the same level on both sides. <strong>Single unit on single unit</strong>: one ski station against one baseball team. <strong>Aggregate on aggregate</strong>: a regional snowfall index against the leaguewide hitting environment. We built both today, then ran each through the same two tests &mdash; last-year-predicts-this-year (the persistence channel) and profile-match-against-climatology (the conditional channel).</p>

  <h3 class="sh">Building the regional snow index</h3>

  <p>We picked five long-running NOAA stations along the Colorado ski belt: Steamboat Springs, Aspen, Crested Butte, Telluride, and Vail. Each one contributes its Nov-through-Apr seasonal snowfall total for each year that the station reports for at least 150 days of the season. The regional index is the mean of those stations for each year in which at least three of the five report. Thirty-seven seasons since 1985 clear that bar.</p>

  <p>The result on the aggregate side: a regional snowfall index that smooths over micro-climates within Colorado but still describes the snow you would experience by skiing the state for the whole winter. That index averages 3,948 millimeters per season, with a one-standard-deviation spread of about 850 millimeters. It is a perfectly cromulent thing to predict.</p>

  <div class="chart-wrap">
    <div class="chart-label">Figure 1 &middot; Predictability scoreboard &middot; lag-1 persistence + conditional model lift, both levels</div>
{chart}
  </div>

  <h3 class="sh">The persistence test, at both scales</h3>

  <p>At the <strong>single-unit</strong> scale, the snow station in Steamboat Springs has a lag-one autocorrelation of <strong>0.007</strong>. The Mets have one of <strong>0.407</strong>. Both numbers are noisy by virtue of being one place or one team, but the Mets clearly carry sixty times more memory than Steamboat does.</p>

  <p>At the <strong>aggregate</strong> scale, the Colorado regional snowfall index has a lag-one autocorrelation of <strong>negative 0.010</strong> &mdash; that is, slightly negative and statistically indistinguishable from zero. Aggregating the snow across five ski-belt stations does not reveal any hidden persistence. There is none to reveal. Major League Baseball's leaguewide OPS, by contrast, has a lag-one r of <strong>0.697</strong>. Pooled, smoothed, and viewed across whole seasons, baseball gets <em>more</em> autocorrelated, not less, because the era-level trends in offense (the home-run revolution, the strikeout revolution, the rule-change adjustments) are now visible without being masked by team-specific noise.</p>

  <p>This is interesting on its own. Aggregating a noisy single series sometimes reveals a hidden signal; sometimes it doesn't. For baseball, smoothing reveals the trend. For Colorado snow, smoothing reveals that there was no trend.</p>

  <h3 class="sh">The conditional test, at the aggregate scale</h3>

  <p>The second test is the one the reader explicitly pointed at. <em>Pattern matching is not the same as persistence.</em> Last year might tell you nothing, but maybe the El Ni&ntilde;o-Southern-Oscillation state of the upcoming winter tells you a great deal. Maybe baseball's analog year matters for the same reason.</p>

  <p>To find out, we did the same thing on both sides. For each season, hold it out. Build a model on the remaining seasons. Predict the held-out year. Compute the root-mean-square error. For snow we tested the ENSO-conditional model (mean of held-out years sharing the same La Ni&ntilde;a / Neutral / El Ni&ntilde;o classification). For baseball we tested the three-nearest-neighbor profile match using a seven-feature standardized vector. Then we compared each model's RMSE to a climatology baseline that predicts every year as the mean of all the others.</p>

  <p>The ENSO model loses to climatology by 5.4 percent on the regional snow index. (It did about the same losing at Steamboat alone.) The three groups &mdash; La Ni&ntilde;a, Neutral, El Ni&ntilde;o &mdash; have nearly identical means at the Colorado regional scale: 4,092, 3,987, and 3,845 millimeters respectively. The information ENSO carries about Colorado snow is real but small. After fitting on a sample this size, the model is overfitting the noise rather than capturing the signal.</p>

  <p>The profile model <em>beats</em> climatology by 48.4 percent on MLB OPS. The era effects are large, the seven-feature profile encodes them, and three nearest neighbors give a much better OPS prediction than the long-run mean. The same kind of pattern matching that fails ski seasons works enormously well for baseball.</p>

  <div class="pull">
    <p>At single unit and at aggregate, by persistence and by profile match, baseball is more predictable than the snow. The reader's correction does not save the snow. It deepens the loss.</p>
    <cite>Predictability, Part II</cite>
  </div>

  <h3 class="sh">Why aggregation rescues one and not the other</h3>

  <p>The asymmetry is itself a finding. Pooling thirty MLB teams or the league's whole hitter population <em>increases</em> the apparent predictability, because what is left after the team-specific noise washes out is era-level trend. Pooling five Colorado ski stations <em>does not</em> increase predictability, because there is no underlying trend at all: snow is genuinely a fresh draw, every year, at every elevation, in every state.</p>

  <p>That distinction shows up in one of the oldest debates in forecasting science: which systems are <em>structurally</em> predictable and which are not? Baseball, when smoothed properly, looks like a slow trend with persistence layered on top. Colorado winter snowfall, even when smoothed, looks like white noise around a long-run mean. Different physics; different epistemic situations; different attitudes warranted from the people watching the systems.</p>

  <h3 class="sh">A note on the framework</h3>

  <div class="box">
    <h3>The two-axis question</h3>
    <p>When a friend or a pundit says one thing is "more predictable" than another, two clarifications usually need to happen. <em>Predictable how</em> &mdash; via persistence, via conditional profile, via mechanistic model, via market price? And <em>at what scale</em> &mdash; a single instance, a regional aggregate, a national average? Reasonable answers to one question can flip the answer to the other. Yesterday we matched the wrong scale and ended up overstating baseball's edge for the wrong reason. Today the edge is, if anything, larger &mdash; but it is for the right reason now.</p>
    <p>That is the lesson worth keeping. Match the scale. Then match the method. Then check the lift over the simplest possible baseline.</p>
  </div>

  <hr>

  <div class="box" style="background:var(--ink)">
    <h3>Notes &amp; sources</h3>
    <p style="color:#c8b99a">Snow: five NOAA GHCN-Daily stations in the Colorado ski belt &mdash; Steamboat Springs (USC00057936), Aspen 1 SW (USC00050372), Crested Butte (USC00051959), Telluride 4 WNW (USC00058204), Vail (USC00058575). Each station's seasonal total runs Nov 1 through Apr 30 and is included only when at least 150 days are reported. The regional index is the mean of all stations reporting that season, conditional on at least three reporting. Result: 37 valid seasons since 1985 producing 35 lag-1 pairs.</p>
    <p style="color:#c8b99a">ENSO state: NOAA Oceanic Ni&ntilde;o Index, DJF average. La Ni&ntilde;a if ONI ≤ &minus;0.5; El Ni&ntilde;o if ≥ +0.5; Neutral otherwise. Regional buckets: 13 La Ni&ntilde;a, 10 Neutral, 14 El Ni&ntilde;o seasons.</p>
    <p style="color:#c8b99a">Baseball: MLB Stats API 1985&ndash;2025, full population of hitters per season. League OPS is PA-weighted across the population. The seven-feature profile used in the conditional test: K-per-PA, BB-per-PA, HR-per-PA, ERA, K-per-9, BB-per-9, HR-per-9. League OPS is excluded from the profile because it is the target. Standardization for the conditional test is computed using only earlier years (no look-ahead). Lag-1 r on league OPS is computed across all 40 year pairs.</p>
    <p style="color:#c8b99a">All RMSE figures use leave-one-out cross-validation. Percent reduction = (RMSE_baseline &minus; RMSE_model) / RMSE_baseline. Negative numbers indicate the conditional model is worse than predicting every year as the climatological mean &mdash; a real outcome when the covariate carries less information than the model burns in degrees of freedom.</p>
  </div>

  <div class="footer">
    <span>The Sports Page &middot; Issue No. __</span>
    <span>Predictability, Part II</span>
    <span>June __, 2026 &middot; New York, NY</span>
  </div>
</main>

</body>
</html>
"""

dest = QUEUE / "075-prediction-frameworks.html"
dest.write_text(html)
print(f"Rewrote {dest}")
