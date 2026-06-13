"""Assemble queue/075-prediction-frameworks.html with inline SVG chart."""
from pathlib import Path

ANALYSIS = Path(__file__).parent
QUEUE = Path("/home/pem725/GitTemp/the-sports-page/queue")
chart = (ANALYSIS / "predictability_v2_chart.svg").read_text()

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
.framework{{display:grid;grid-template-columns:repeat(2,1fr);gap:1rem;margin:1.4rem 0}}
@media(max-width:560px){{.framework{{grid-template-columns:1fr}}}}
.fw{{border:1px solid var(--div);background:var(--card);padding:1.1rem 1.2rem}}
.fw h4{{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;color:var(--steel);margin-bottom:.35rem}}
.fw .ques{{font-family:'Roboto Mono',monospace;font-size:.62rem;letter-spacing:.1em;color:var(--rust);text-transform:uppercase;margin-bottom:.4rem;font-weight:600}}
.fw p{{font-size:.88rem;line-height:1.55}}
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

  <h2 class="hed">"Predictability" Is a Family of Questions. <em>The Snow Is Failing More Than One.</em></h2>
  <p class="deck">Yesterday a reader pointed out, correctly, that yesterday's piece tested only one kind of prediction: does last year predict next year? But that is not the only way to ask. There is also: does an in-year profile &mdash; La Niña, the league's hitting environment, anything that can be measured before the outcome &mdash; predict it? We re-ran the comparison with the better test. The verdict on snow got worse, not better.</p>
  <p class="byline">The Sports Page &middot; A Reader's Defense Companion &middot; Steamboat snowfall + ENSO vs MLB OPS + profile match</p>

  <div class="stat-row">
    <div class="sc"><div class="v bad">&minus;5%</div><div class="l">Snow RMSE lift from ENSO</div></div>
    <div class="sc"><div class="v good">+48%</div><div class="l">Baseball RMSE lift from profile</div></div>
    <div class="sc"><div class="v now">2</div><div class="l">Prediction tests, two losses for snow</div></div>
  </div>

  <p>Yesterday's piece argued that snowfall at Steamboat Springs has lag-one autocorrelation near zero (r = 0.007) and that Major League Baseball, by comparison, autocorrelates at r = 0.49. We declared baseball seventy times more "predictable." The reader who wrote in &mdash; their note arrived overnight &mdash; called the framing too narrow. <em>Autocorrelation is only one kind of predictability.</em> The other kind, the one that powers most amateur analog-matching and most professional weather forecasting, is conditional prediction: knowing some in-season profile, can you do better than the climatological mean?</p>

  <p>The reader's specific challenge was La Niña. Maybe snowfall does not repeat year over year &mdash; but maybe it does respond to the El Niño / La Niña / Neutral state of the equatorial Pacific. That is a real, measurable covariate. NOAA publishes it. The Pacific Northwest gets reliably more snow in La Niña years; the Southwest reliably less. Colorado sits in between, but you might still expect some signal.</p>

  <h3 class="sh">Four ways to mean "predictable"</h3>

  <p>Before we ran the data, we wrote down the framework. "Prediction" is not one thing. It is a family of related but distinct claims, each with its own test:</p>

  <div class="framework">
    <div class="fw">
      <div class="ques">What is the question</div>
      <h4>1. Persistence</h4>
      <p>Does last year's value predict this year's? Tested by lag-one autocorrelation. Yesterday's piece. Captures the "memory" of the system. The Mets won this test.</p>
    </div>
    <div class="fw">
      <div class="ques">What is the question</div>
      <h4>2. Conditional</h4>
      <p>Does some in-year profile (La Niña, opening-day roster, league hitting environment) predict the outcome better than the long-run average? Tested by leave-one-out RMSE against a climatology baseline. Today's piece.</p>
    </div>
    <div class="fw">
      <div class="ques">What is the question</div>
      <h4>3. Mechanistic</h4>
      <p>Can a structural model (Pythagorean expectation, jet-stream physics, log5) predict the outcome? Tested by held-out forecast error. The standard in actuarial work. We will tackle this in a future piece.</p>
    </div>
    <div class="fw">
      <div class="ques">What is the question</div>
      <h4>4. Adversarial</h4>
      <p>Can a well-informed bettor beat the market line on the outcome? Tested in dollars. The only test that matters to the sportsbook, the only test that matters to the futures trader.</p>
    </div>
  </div>

  <p>Today we tested type two: conditional prediction. For each system, we built two models. The first is a <em>climatology baseline</em> &mdash; predict every year as the mean of all the others. The second uses a profile to do better, if the profile carries any information. For Steamboat snowfall, the profile is the ENSO state of the upcoming winter (La Niña / Neutral / El Niño, scored by NOAA's standard Niño 3.4 index averaged over December through February). For Major League Baseball, the profile is the seven-feature league rate vector we used in yesterday's <em>analog year</em> piece: walks per plate appearance, strikeouts per plate appearance, home runs per plate appearance, ERA, and three K/BB/HR per-nine-innings rates.</p>

  <p>For each year of data, we held that year out, fit the conditional model on the rest, then asked: how far off was the prediction? We did that across the whole dataset. The metric: <strong>root-mean-square error</strong>, summarized as percent reduction from the climatology baseline. Positive means the profile is useful. Zero means the profile is noise. Negative means the profile is worse than no information at all.</p>

  <div class="chart-wrap">
    <div class="chart-label">Figure 1 &middot; Left: snowfall by ENSO state &middot; Right: % RMSE reduction by conditional model</div>
{chart}
  </div>

  <h3 class="sh">Steamboat is unmoved by El Niño</h3>

  <p>The left panel of the chart is the answer to the reader's question, before any modeling. We grouped the 31 ski seasons at Steamboat into the three ENSO buckets and plotted them as a strip. The three clouds are indistinguishable. La Niña years average 4,200 mm of snow. El Niño years average 4,060. Neutral years average 3,625. The differences are smaller than the year-to-year noise within any single bucket. If you give a forecaster nothing but the ENSO state for the upcoming season, they do not gain a foothold against the climatological mean.</p>

  <p>The leave-one-out test confirms it. Predicting each year from the mean of all other years gives a root-mean-square error of 1,232 millimeters. Predicting each year from the mean of other years <em>in the same ENSO state</em> gives an RMSE of 1,293 millimeters &mdash; <em>slightly worse</em>. The ENSO model is not just unhelpful; it is overfitting noise. The right panel of the chart records this as a minus-five-percent lift.</p>

  <p>Colorado meteorology turns out to have known this. The El Niño signal in snowfall is largest in the Pacific Northwest (where La Niña reliably means more snow) and in the desert Southwest (where La Niña reliably means less). Colorado sits at the dividing line. The ENSO signal is small, mixed, and often masked by local effects. Tim's twenty years of mental analog-matching was even more thorough folly than yesterday's piece let on. The most obvious, professional-grade covariate in atmospheric science gets him nothing.</p>

  <h3 class="sh">Baseball just gives up half its error</h3>

  <p>Run the same test on baseball &mdash; predict each season's league OPS using the three years that are closest in the standardized feature space, where the candidates are drawn only from seasons that occurred earlier &mdash; and the RMSE falls from .0249 (climatology baseline) to .0128. That is a <strong>forty-eight-percent reduction</strong>. The profile carries enormous information for baseball. The right panel of the chart shows the bar.</p>

  <p>The mechanism is intuitive. Baseball's last fifteen years have been a single coherent trend: strikeout rates climbing, then plateauing; walks oscillating around a small range; home-run rates moving with the ball. The eight-feature profile we use is essentially encoding "where in the trend are we" plus a few year-specific perturbations. When we hand the model 2026 and ask for its three most similar prior seasons, it returns 2021, 2023, and 2018 &mdash; all of which are in the same "modern" plateau. Their average OPS is going to be a good guess for 2026's OPS, because all four years are governed by similar underlying rule sets and supplier physics.</p>

  <div class="pull">
    <p>Two prediction tests. Snow lost the first. Snow lost the second. Baseball won both. We are getting closer to a real answer about what predictability actually means.</p>
    <cite>Predictability, Part II</cite>
  </div>

  <h3 class="sh">The civic-mission point</h3>

  <p>This whole exercise is really about a single question: <em>what should a careful reader do when somebody claims something is predictive of something else?</em> The framework above gives a checklist. Ask which kind of prediction is being claimed. Ask what the baseline is. Ask whether the lift has been measured against that baseline, or whether the speaker is comparing a model to itself.</p>

  <p>It is depressingly common for a prediction claim to fail this checklist. "Veteran teams play better in October" is a persistence claim that has not been measured against a climatology baseline. "Cold-weather defenses dominate in playoff games" is a conditional claim whose covariate (game-time temperature) has rarely been tested for lift. "Pitching wins championships" is somewhere between mechanistic and adversarial, and rarely gets either test. Most of what gets called prediction in sports talk is in the same statistical bucket as Tim's twenty years of believing his ski seasons rhymed.</p>

  <p>This newsletter intends to be useful. The Reader's Defense series is supposed to give you the vocabulary to interrogate prediction claims at the source. Yesterday we gave you autocorrelation. Today we gave you lift-over-climatology. Tomorrow, somebody will tell you a thing they think predicts a thing. <em>Make them name the test.</em></p>

  <hr>

  <div class="box" style="background:var(--ink)">
    <h3>Notes &amp; sources</h3>
    <p style="color:#c8b99a">Snow: NOAA GHCN-Daily station USC00057936 (Steamboat Springs, CO). 31 ski seasons since 1985 with at least 150 reported days each. ENSO state assigned via NOAA's Oceanic Ni&ntilde;o Index for December-February of the year ending the season. La Ni&ntilde;a if DJF ONI ≤ &minus;0.5, El Ni&ntilde;o if ≥ +0.5, Neutral otherwise. Resulting buckets: 13 La Ni&ntilde;a, 7 Neutral, 11 El Ni&ntilde;o.</p>
    <p style="color:#c8b99a">Baseball: League OPS aggregated across all qualified hitters per year, 1985 through 2025, PA-weighted. Seven covariates used in the profile: K-per-PA, BB-per-PA, HR-per-PA, ERA, K-per-9, BB-per-9, HR-per-9. League OPS itself is excluded from the profile (it would be circular). Standardization performed using only years prior to the held-out target year. Profile prediction: mean OPS of three nearest historical neighbors in the standardized space. n=31 years passed the warm-up filter.</p>
    <p style="color:#c8b99a">Leave-one-out cross-validation: for each year, the model is refit using all other years (and, for baseball, restricted to earlier years to avoid look-ahead bias). RMSE is computed over the held-out predictions. Percent reduction is (RMSE_baseline &minus; RMSE_conditional) / RMSE_baseline. A negative number means the conditional model is worse than the climatology mean &mdash; a real possibility when the covariate carries no information and the conditional model burns degrees of freedom learning noise.</p>
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
print(f"Wrote {dest}")
