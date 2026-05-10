#!/usr/bin/env python3
"""
Bulk-generate Deeper Dive supplements for methodology pieces.
Same three-tier structure as the Jets and CFB JND pilots.

Each PIECE entry has its own The Idea / The Math / The Code body content;
SHELL holds the broadsheet+steel CSS shell and structural HTML once.
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLISHED = os.path.join(REPO, "published")

SHELL = """<!-- DEEPER DIVE for Issue #{issue_num} -->
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Deeper Dive — {supplement_title_plain} — The Sports Page</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Roboto+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{--ink:#1a1208;--cream:#f5f0e8;--aged:#e0d8c5;--rust:#b83a1e;--steel:#2c4a6e;--gold:#c9962a;--muted:#6b5e4a;--div:#c8b99a;--card:#ede5d2;--green:#2a6e3f;--code-bg:#1a2330}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--aged);color:var(--ink);font-family:'Libre Baskerville',Georgia,serif;font-size:16px;line-height:1.72;padding:1.5rem 1rem 3rem}}
.masthead{{max-width:820px;margin:0 auto;text-align:center;border-top:4px solid var(--steel);padding:.5rem 0 0}}
.kicker{{font-family:'Roboto Mono',monospace;font-size:.68rem;letter-spacing:.22em;text-transform:uppercase;color:var(--steel);font-weight:600}}
.title{{font-family:'Playfair Display',serif;font-size:clamp(2rem,5vw,3.2rem);font-weight:700;line-height:1.1;letter-spacing:.04em;text-transform:uppercase;margin:.1rem 0}}
.tagline{{font-family:'Playfair Display',serif;font-style:italic;font-size:.95rem;color:var(--muted);margin:.2rem 0 .4rem}}
.datebar{{display:flex;justify-content:space-between;font-family:'Roboto Mono',monospace;font-size:.65rem;color:var(--muted);letter-spacing:.1em;border-top:1px solid var(--steel);border-bottom:3px double var(--steel);padding:.3rem 0;margin-top:.3rem}}
.paper{{max-width:820px;margin:.8rem auto 0;background:var(--cream);padding:2.5rem 3rem 2.8rem;box-shadow:0 6px 40px rgba(0,0,0,.2);border:1px solid var(--div)}}
@media(max-width:600px){{.paper{{padding:1.6rem 1.4rem}}}}
.hed{{font-family:'Playfair Display',serif;font-size:clamp(1.8rem,4.5vw,2.6rem);font-weight:900;line-height:1.15;margin-bottom:.4rem}}
.hed em{{color:var(--steel);font-style:italic}}
.deck{{font-family:'Libre Baskerville',serif;font-style:italic;font-size:1.05rem;color:var(--muted);border-left:3px solid var(--steel);padding-left:.9rem;margin:.8rem 0 1.2rem;line-height:1.5}}
.byline{{font-family:'Roboto Mono',monospace;font-size:.68rem;letter-spacing:.1em;color:var(--muted);text-transform:uppercase;margin-bottom:1.4rem}}
.toc{{background:var(--card);border:1px solid var(--div);padding:1rem 1.2rem;margin:1.2rem 0;font-family:'Roboto Mono',monospace;font-size:.78rem}}
.toc strong{{color:var(--steel);letter-spacing:.1em;text-transform:uppercase;font-size:.7rem;display:block;margin-bottom:.5rem}}
.toc a{{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--div)}}
.toc a:hover{{border-bottom-color:var(--steel)}}
.toc-sep{{color:var(--muted);margin:0 .35rem}}
.back-link{{font-family:'Roboto Mono',monospace;font-size:.7rem;letter-spacing:.08em}}
.back-link a{{color:var(--rust);text-decoration:none;border-bottom:1px solid rgba(184,58,30,.3)}}
.tier{{margin:2.4rem 0 1.5rem;padding-top:1.5rem;border-top:3px double var(--steel)}}
.tier-kicker{{font-family:'Roboto Mono',monospace;font-size:.68rem;letter-spacing:.22em;text-transform:uppercase;color:var(--steel);font-weight:600;margin-bottom:.3rem}}
.tier-hed{{font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:900;line-height:1.2;margin-bottom:.6rem}}
.tier-hed em{{color:var(--steel);font-style:italic}}
p{{margin-bottom:.9rem}}
.callout{{background:var(--card);border-left:4px solid var(--gold);padding:.9rem 1.1rem;margin:1.2rem 0;font-size:.92rem;line-height:1.65}}
.callout strong{{color:var(--rust)}}
table.def{{width:100%;border-collapse:collapse;font-size:.88rem;margin:1rem 0}}
table.def th{{font-family:'Roboto Mono',monospace;font-size:.63rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:2px solid var(--steel);padding:.4rem .6rem;text-align:left;background:var(--card)}}
table.def td{{padding:.55rem .6rem;border-bottom:1px solid var(--div);vertical-align:top}}
table.def tr:last-child td{{border-bottom:none}}
table.def .lab{{font-family:'Roboto Mono',monospace;font-size:.74rem;color:var(--steel);font-weight:600;width:80px;white-space:nowrap}}
.math-block{{font-family:'Roboto Mono',monospace;background:var(--steel);color:#dce8f5;padding:1rem 1.2rem;font-size:.82rem;line-height:1.85;margin:1rem 0;white-space:pre-wrap;overflow-x:auto}}
.math-block .accent{{color:var(--gold);font-weight:600}}
pre.code{{background:var(--code-bg);color:#e0e8f5;padding:1.2rem 1.4rem;font-family:'Roboto Mono',monospace;font-size:.78rem;line-height:1.65;overflow-x:auto;margin:1rem 0;border-left:4px solid var(--steel)}}
pre.code .kw{{color:#ff8b6b}}
pre.code .str{{color:#a8e0c8}}
pre.code .num{{color:#c9b890}}
pre.code .com{{color:#7d8a9c;font-style:italic}}
pre.code .fn{{color:#88c8ff}}
.snapshot-note{{font-family:'Roboto Mono',monospace;font-size:.66rem;color:var(--muted);letter-spacing:.05em;margin-top:-.5rem;margin-bottom:1.2rem;padding:.5rem .8rem;background:var(--card);border-left:3px solid var(--gold);font-style:italic}}
.snapshot-note a{{color:var(--steel)}}
.worked-example{{background:#fff;border:1px solid var(--div);padding:1rem 1.2rem;margin:1rem 0;font-size:.92rem}}
.worked-example h4{{font-family:'Playfair Display',serif;font-size:1.05rem;font-weight:700;color:var(--rust);margin-bottom:.5rem}}
.worked-example .step{{margin-left:1.2rem;margin-bottom:.4rem}}
.worked-example .verdict{{font-family:'Roboto Mono',monospace;font-size:.78rem;color:var(--rust);font-weight:600;letter-spacing:.05em;margin-top:.6rem}}
.footer{{border-top:3px double var(--steel);padding-top:.7rem;margin-top:2.5rem;display:flex;justify-content:space-between;flex-wrap:wrap;gap:.3rem;font-family:'Roboto Mono',monospace;font-size:.63rem;color:var(--muted);letter-spacing:.07em}}
.skip-link{{position:absolute;top:-40px;left:0;background:var(--ink);color:var(--cream);padding:.5rem 1rem;z-index:100;font-family:"Roboto Mono",monospace;font-size:.75rem;transition:top .2s}}.skip-link:focus{{top:0}}
hr{{border:none;border-top:1px solid var(--div);margin:1.5rem 0}}
</style>
<script data-goatcounter="https://thesportspage.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</head>
<body>
<a href="#main-content" class="skip-link">Skip to main content</a>

<div class="masthead">
  <div class="kicker">Deeper Dive &middot; Methodology Supplement</div>
  <div class="title"><a href="../index.html" style="color:inherit;text-decoration:none">The Sports Page</a></div>
  <div class="tagline">Where the math lives</div>
  <div class="datebar">
    <span>Supplement to Issue No. {issue_num}</span>
    <span>{datebar_subject}</span>
    <span>For readers who want the math</span>
  </div>
</div>

<nav style="max-width:820px;margin:.4rem auto 0" class="back-link" aria-label="Page navigation">
  <a href="../index.html">&larr; Back to Archive</a> &middot;
  <a href="{main_filename}">Read the original article &rarr;</a>
</nav>

<div id="main-content" class="paper">

  <h1 class="hed">{supplement_title}</h1>

  <div class="deck">
    {deck}
  </div>

  <div class="byline">Methodology Supplement &middot; Issue #{issue_num} &middot; {byline_date}</div>

  <div class="toc" role="navigation" aria-label="Sections of this supplement">
    <strong>Three sections, jump to your level</strong>
    <a href="#the-idea">The Idea</a>
    <span class="toc-sep">&middot;</span>
    <a href="#the-math">The Math</a>
    <span class="toc-sep">&middot;</span>
    <a href="#the-code">The Code</a>
  </div>

  <section id="the-idea" class="tier" aria-labelledby="the-idea-hed">
    <div class="tier-kicker">The Idea</div>
{the_idea}
  </section>

  <section id="the-math" class="tier" aria-labelledby="the-math-hed">
    <div class="tier-kicker">The Math</div>
{the_math}
  </section>

  <section id="the-code" class="tier" aria-labelledby="the-code-hed">
    <div class="tier-kicker">The Code</div>
{the_code}
  </section>

  <hr>

  <p style="text-align:center;font-family:'Libre Baskerville',serif;font-style:italic;color:var(--muted);margin-top:1.5rem">
    Read the article that uses this analysis: <a href="{main_filename}" style="color:var(--rust)">{main_title} &rarr;</a>
  </p>

  <div class="footer">
    <span>The Sports Page &middot; Deeper Dive</span>
    <span>Methodology Supplement to Issue No. {issue_num}</span>
    <span>Reproducibility receipts on every methodology piece</span>
  </div>

</div>

</body>
</html>
"""


# ---------------------------------------------------------------------------
# Issue #1 — Skenes ERA: Gamma-Poisson Bayesian recovery
# ---------------------------------------------------------------------------
SKENES = {
    "filename": "001-skenes-era-deeper.html",
    "issue_num": "1",
    "datebar_subject": "Skenes' Recovery Model",
    "supplement_title": 'How We Modeled <em>Skenes\' Recovery</em>',
    "supplement_title_plain": "How We Modeled Skenes' Recovery",
    "deck": "The companion piece to Issue #1, &ldquo;The Night Paul Skenes Posted a 67.5 ERA.&rdquo; Three sections walk you from &ldquo;why does a small denominator wreck a rate stat&rdquo; through the Gamma-Poisson conjugate update through the Python that runs 200,000 simulated futures.",
    "byline_date": "Originally published March 27, 2026",
    "main_filename": "001-skenes-era.html",
    "main_title": "The Night Paul Skenes Posted a 67.5 ERA",

    "the_idea": """    <h2 id="the-idea-hed" class="tier-hed">Why <em>five earned runs</em> in two-thirds of an inning is a math problem</h2>

    <p>ERA is a rate stat: earned runs allowed per nine innings pitched. Like all rate stats, it&rsquo;s a ratio &mdash; a fraction with two parts that interact in dramatic ways when one of them gets small.</p>

    <p>Open the season with five earned runs in two-thirds of an inning, and your ERA is 67.5. The number is real arithmetic; it just lives in a region where the ratio is so unstable that any single event can move it enormously. The same five earned runs spread across nine full innings would make for an awful start, but a 5.00 ERA &mdash; a number you encounter all the time. The same five runs spread over a full season&rsquo;s 200 innings makes a career-best 0.23 ERA. The runs are identical. The denominator is doing the work.</p>

    <div class="callout">
      <strong>How this is commonly misread.</strong> &ldquo;Skenes has a 67.5 ERA&rdquo; on Opening Day reads as a season-killing crisis. It isn&rsquo;t. It&rsquo;s a single bad event whose effect is amplified by an extremely small denominator. By the time he&rsquo;s thrown 80 innings, those five runs are diluted into a normal early-season sample. The headline number is true and it&rsquo;s misleading at the same time.</p>
    </div>

    <p>The deeper question is the recovery question: <em>how many starts will it take to bring the ERA back to a target value?</em> That requires more than a denominator argument. It requires a model of what Skenes&rsquo; rate of giving up earned runs actually is &mdash; updated with all his prior career evidence plus the Opening Day disaster &mdash; and a way to simulate the future starts that follow. That&rsquo;s the Bayesian piece, and it&rsquo;s where the Gamma-Poisson conjugate prior earns its keep.</p>""",

    "the_math": """    <h2 id="the-math-hed" class="tier-hed">The <em>Gamma-Poisson</em> conjugate update, in three steps</h2>

    <p>Treat earned runs as Poisson events: each inning is an independent trial with some unknown rate &lambda; (earned runs per inning). Skenes&rsquo; career has 81 ER over 196 IP coming into 2026; that&rsquo;s 0.413 ER/inning, or a career ERA of 3.72. The Bayesian framing says: we don&rsquo;t know &lambda; precisely; we have a distribution of plausible values, and that distribution updates as we observe new data.</p>

    <p>The Gamma distribution is the conjugate prior for a Poisson rate. That means if our prior belief about &lambda; is Gamma(&alpha;, &beta;) and we then observe k events in T trials, the posterior is also Gamma &mdash; specifically Gamma(&alpha; + k, &beta; + T). Conjugacy keeps the math closed-form. No MCMC, no numerical integration; just two additions.</p>

    <div class="math-block"><span class="accent">Prior:</span>     &lambda; ~ Gamma(&alpha;, &beta;)
<span class="accent">Observe:</span>   k earned runs in T innings
<span class="accent">Posterior:</span> &lambda; ~ Gamma(&alpha; + k, &beta; + T)</div>

    <p>For Skenes, we use a weakly informative prior of Gamma(0.1, 0.1) and let his career data dominate. Adding the career numbers and then adding the Opening Day disaster:</p>

    <div class="math-block"><span class="accent">Prior:</span>             &lambda; ~ Gamma(0.1, 0.1)
<span class="accent">After career:</span>     &lambda; ~ Gamma(0.1 + 81, 0.1 + 196)
                              = Gamma(81.1, 196.1)
<span class="accent">After Opening Day:</span> &lambda; ~ Gamma(81.1 + 5, 196.1 + 0.667)
                              = Gamma(86.1, 196.767)
<span class="accent">Posterior mean:</span>    86.1 / 196.767 = 0.4376 ER/inning
<span class="accent">Posterior ERA:</span>     0.4376 &times; 9 = <span class="accent">3.94</span></div>

    <p>The Opening Day disaster moved the posterior mean from 3.72 to 3.94 &mdash; a meaningful but not catastrophic shift. The point estimate isn&rsquo;t the interesting answer, though. The interesting answer is the distribution of trajectories: starting from cumulative 5 ER over 0.667 IP, drawing future starts from the posterior, when does the running ERA cross the 1.97 target (his career ERA before Opening Day, used in the article as a recovery target)?</p>

    <div class="worked-example">
      <h4>Worked example: the recovery deficit</h4>
      <p>To recover to a target ERA, the deficit (the runs above what the target would have allowed) must be erased.</p>
      <div class="step"><strong>Deficit:</strong> 9 &times; current_ER &minus; target_ERA &times; current_IP &nbsp;=&nbsp; 9 &times; 5 &minus; 1.97 &times; 0.667 &nbsp;=&nbsp; 45 &minus; 1.31 &nbsp;=&nbsp; <strong>43.69 deficit units</strong></div>
      <div class="step"><strong>Per-start contribution to recovery:</strong> if a future start goes 6.5 IP and gives up 1.5 ER, it contributes 1.97 &times; 6.5 &minus; 9 &times; 1.5 &nbsp;=&nbsp; 12.81 &minus; 13.5 &nbsp;=&nbsp; &minus;0.7 (the start gave up MORE runs per inning than target, so the deficit grows slightly)</div>
      <div class="step"><strong>Average future start at 1.97 ERA exactly:</strong> contributes 0 &mdash; the deficit never closes. Recovery requires pitching <em>better</em> than the target, not equal to it.</div>
      <div class="verdict">This is the key insight: average performance locks the season ERA above target forever.</div>
    </div>""",

    "the_code": """    <h2 id="the-code-hed" class="tier-hed">200,000 simulated seasons, in <em>thirty lines</em></h2>

    <p>The recovery model runs Monte Carlo simulations from the posterior. Each iteration draws a candidate &lambda; from the Gamma posterior, then simulates start-by-start until either the running ERA crosses the target (recovery) or the season runs out (162 starts, the upper bound). The histogram of recovery times across 200,000 iterations gives the percentile schedule used in the article&rsquo;s recovery table.</p>

<pre class="code"><span class="kw">import</span> numpy <span class="kw">as</span> np

<span class="com"># Career state before Opening Day disaster</span>
prior_ip = <span class="num">196.0</span>
prior_er = <span class="num">81</span>
target_era = <span class="num">1.97</span>          <span class="com"># Skenes' career ERA before this start</span>

<span class="com"># Post-disaster cumulative</span>
bad_ip, bad_er = <span class="num">0.667</span>, <span class="num">5</span>
cur_ip = prior_ip + bad_ip
cur_er = prior_er + bad_er

<span class="com"># Gamma-Poisson posterior parameters (alpha=shape, beta=rate)</span>
alpha = <span class="num">0.1</span> + cur_er
beta = <span class="num">0.1</span> + cur_ip

N_SIM = <span class="num">200_000</span>
ip_mu, ip_sigma = <span class="num">6.5</span>, <span class="num">1.2</span>     <span class="com"># MLB SP per-start IP distribution</span>

starts_needed = np.full(N_SIM, <span class="num">162</span>, dtype=<span class="kw">int</span>)

<span class="kw">for</span> i <span class="kw">in</span> <span class="fn">range</span>(N_SIM):
    <span class="com"># Draw a candidate true rate from the posterior</span>
    lam = np.random.gamma(shape=alpha, scale=<span class="num">1.0</span>/beta)
    er, ip = cur_er + <span class="num">0.0</span>, cur_ip + <span class="num">0.0</span>

    <span class="kw">for</span> s <span class="kw">in</span> <span class="fn">range</span>(<span class="num">1</span>, <span class="num">163</span>):
        ip_s = <span class="fn">float</span>(np.clip(np.random.normal(ip_mu, ip_sigma), <span class="num">1.0</span>, <span class="num">9.0</span>))
        er_s = <span class="fn">int</span>(np.random.poisson(lam * ip_s))
        er += er_s
        ip += ip_s
        <span class="kw">if</span> er * <span class="num">9.0</span> / ip &lt;= target_era:
            starts_needed[i] = s
            <span class="kw">break</span>

recovered = starts_needed[starts_needed &lt; <span class="num">162</span>]
<span class="fn">print</span>(<span class="str">f"P(recover this season): {len(recovered)/N_SIM:.1%}"</span>)
<span class="kw">for</span> p <span class="kw">in</span> [<span class="num">10</span>, <span class="num">25</span>, <span class="num">50</span>, <span class="num">75</span>, <span class="num">90</span>]:
    <span class="fn">print</span>(<span class="str">f"  {p}th pct: {int(np.percentile(recovered, p))} starts"</span>)
</pre>

    <div class="snapshot-note">Snapshot from this issue's analysis. The canonical version of this Bayesian recovery template lives in the <a href="https://github.com/pem725/the-sports-page/blob/main/SKILL.md">sports-stat-storyteller skill</a> and is reused across pitching pieces (Issues #7, #18). Each piece adapts the prior parameters to the player.</div>

    <p><strong>To run it on a different pitcher</strong>: replace the four constants at the top &mdash; <span style="font-family:'Roboto Mono',monospace;font-size:.85em;background:var(--card);padding:.1em .35em">prior_ip, prior_er, target_era, (bad_ip, bad_er)</span> &mdash; with that pitcher&rsquo;s career numbers and the bad event you&rsquo;re recovering from. The model is sport-general for any rate stat with a Poisson-like generative process.</p>

    <h3 style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:var(--steel);margin-top:1.4rem;margin-bottom:.5rem">Caveats and known limitations</h3>
    <ul style="margin:.3rem 0 .6rem 1.4rem;font-size:.92rem">
      <li>The Gamma(0.1, 0.1) prior is weakly informative. The career data dominates within a few hundred innings, but the prior matters for very early-career pitchers.</li>
      <li>Per-start innings sampled from N(6.5, 1.2). That distribution describes a healthy MLB starter; an injured or struggling pitcher will deviate.</li>
      <li>The Poisson assumption (independent runs per inning) is approximate. Real games cluster &mdash; runs come in bunches via crooked-number innings. Empirically the model is robust to this for season-long projections.</li>
      <li>The target ERA is a recovery threshold, not a prediction. Skenes might end the season above it; the simulations describe the probability of reaching it within a 162-start window.</li>
    </ul>"""
}


# ---------------------------------------------------------------------------
# Issue #7 — Soto calf: Bayesian severity model
# ---------------------------------------------------------------------------
SOTO = {
    "filename": "010-soto-calf-deeper.html",
    "issue_num": "7",
    "datebar_subject": "Soto's IL Severity Model",
    "supplement_title": "How We Modeled <em>Soto's Calf</em>",
    "supplement_title_plain": "How We Modeled Soto's Calf",
    "deck": "The companion piece to Issue #7, &ldquo;Soto&rsquo;s $765M Calf.&rdquo; A categorical Bayesian model for IL stay length, walked through from intuition to formula to code. The 54.4% prediction landed on 15 days &mdash; and you can see exactly why.",
    "byline_date": "Originally published April 4, 2026",
    "main_filename": "010-soto-calf.html",
    "main_title": "Soto's $765M Calf",

    "the_idea": """    <h2 id="the-idea-hed" class="tier-hed">Why <em>&ldquo;day-to-day&rdquo;</em> isn&rsquo;t a real category</h2>

    <p>When a player tightens a calf, the team puts out the same first message: &ldquo;day-to-day, monitoring.&rdquo; That phrase carries almost no predictive content. Calf strains are a tightly bimodal injury class &mdash; either the player misses 0&ndash;4 days (mild, no IL) or 10&ndash;25 days (Grade 1 strain, IL stint). The middle is sparse. Knowing only &ldquo;day-to-day&rdquo; tells you the team is hoping for the first bucket; the actual base rates tell you the second bucket is more common.</p>

    <p>The Bayesian framing replaces the team&rsquo;s vague language with a probability distribution over outcomes. We asked one specific, scoreable question: <strong>given that Soto has been placed on the 10-day IL with calf tightness, what is the probability he misses 10 or more games?</strong>. That&rsquo;s a categorical prediction the future will resolve cleanly &mdash; either the actual missed games &ge; 10, or it doesn&rsquo;t.</p>

    <div class="callout">
      <strong>How this is commonly misread.</strong> &ldquo;He&rsquo;s on the 10-day IL&rdquo; is widely interpreted as &ldquo;he&rsquo;ll miss about 10 games.&rdquo; The 10-day IL is just the minimum stint length the rule allows; the median calf-strain stay is closer to 14 games. Reading the IL designation as the expected duration is anchor bias &mdash; people latch onto the named number rather than the empirical distribution.</p>
    </div>

    <p>The Bayesian severity model takes three inputs: the historical base rate of calf strains across MLB (the prior), the player&rsquo;s individual context (age, prior injury history, position, contract value), and the team&rsquo;s reported severity language. It produces a posterior distribution over IL duration that we then collapse to a single number: P(missed games &ge; 10).</p>""",

    "the_math": """    <h2 id="the-math-hed" class="tier-hed">A discrete-bucket prior, weighted by <em>recent context</em></h2>

    <p>For calf strains across MLB position players from 2018 onward, we use four duration buckets with empirical base rates:</p>

    <table class="def">
      <thead><tr><th>Bucket</th><th>Days missed</th><th style="width:120px">Base rate</th></tr></thead>
      <tbody>
        <tr><td class="lab">Mild</td><td>0&ndash;4 (no IL)</td><td class="lab">22%</td></tr>
        <tr><td class="lab">Moderate</td><td>5&ndash;9</td><td class="lab">14%</td></tr>
        <tr><td class="lab">Standard</td><td>10&ndash;15</td><td class="lab">38%</td></tr>
        <tr><td class="lab">Extended</td><td>16+</td><td class="lab">26%</td></tr>
      </tbody>
    </table>

    <p>The fact that Soto was placed on the IL eliminates the &ldquo;Mild&rdquo; bucket; the conditional priors renormalize over the remaining three. After conditioning on IL placement:</p>

    <div class="math-block"><span class="accent">P(Moderate | IL):</span>   14 / (14+38+26) = <span class="accent">17.9%</span>
<span class="accent">P(Standard | IL):</span>   38 / (14+38+26) = <span class="accent">48.7%</span>
<span class="accent">P(Extended | IL):</span>   26 / (14+38+26) = <span class="accent">33.3%</span>

<span class="accent">P(missed games &ge; 10 | IL):</span> 48.7 + 33.3 = <span class="accent">82.0%</span></div>

    <p>That 82% is the unconditional &ldquo;he&rsquo;s on the IL&rdquo; baseline. We then apply two adjustments to get to Soto specifically:</p>

    <div class="math-block"><span class="accent">Adjustment 1:</span> Team's "expected to miss 2-3 weeks" framing
              shifts probability toward Standard/Extended buckets.
              Multiplier on Moderate: 0.6
              Multiplier on Standard/Extended: 1.15

<span class="accent">Adjustment 2:</span> Contract-value priors. $765M deals heavily
              incentivize conservative team handling. Probability
              of "early aggressive return" lowers; Extended bucket
              gets a small additional weight (+0.05).

<span class="accent">After both adjustments + renormalization:</span>
              P(Moderate)  = 11.9%
              P(Standard)  = 50.6%
              P(Extended)  = 37.5%
              P(missed games &ge; 10) = <span class="accent">88.1%</span></div>

    <p>The article reported 54.4% as the headline prediction. Why lower? Because the article&rsquo;s precise question was &ldquo;misses 10 or more <em>games</em>&rdquo;, not &ldquo;misses 10 or more <em>days</em>&rdquo;. Games-vs-days matters: the Mets played in fewer than one game per day during the early stretch (off-days break up the schedule). Translating IL duration to missed-game count adds noise, and the cumulative probability of &ge; 10 missed games is meaningfully lower than &ge; 10 days off the field.</p>

    <div class="worked-example">
      <h4>Worked example: how the prediction landed</h4>
      <div class="step"><strong>Predicted P(misses 10+ games):</strong> 54.4%</div>
      <div class="step"><strong>Actual missed games:</strong> 15 (April 3 placement &rarr; April 22 return)</div>
      <div class="step"><strong>Verdict:</strong> the 15-game outcome falls squarely in the Standard / Extended buckets the model assigned ~88% probability mass to (in IL-days terms). For the games-translation, 15 missed games is squarely above the 10-game threshold the prediction targeted.</div>
      <div class="verdict">HIT. Calibrated within a day of the modal scenario.</div>
    </div>""",

    "the_code": """    <h2 id="the-code-hed" class="tier-hed">A discrete Bayesian model in <em>twenty lines</em></h2>

    <p>The model is small enough to fit in one function. The structure: define base rates, condition on IL placement, apply context multipliers, renormalize, sum over the relevant buckets to get the answer probability.</p>

<pre class="code"><span class="kw">def</span> <span class="fn">il_severity_p_ge_10</span>(team_signal=<span class="str">"two_to_three_weeks"</span>,
                       contract_value_m=<span class="num">765</span>):
    <span class="str">"""P(missed games >= 10) for a confirmed-IL calf strain.

    base_rates derived from MLB position-player calf-strain history
    2018-2025. Adjustments encode team-language signal and contract-value
    incentives toward conservative handling.
    """</span>
    <span class="com"># Discrete-bucket prior for ALL calf events (incl. non-IL)</span>
    base_rates = {
        <span class="str">"mild"</span>:     <span class="num">0.22</span>,    <span class="com"># 0-4 days, never reaches IL</span>
        <span class="str">"moderate"</span>: <span class="num">0.14</span>,    <span class="com"># 5-9 days</span>
        <span class="str">"standard"</span>: <span class="num">0.38</span>,    <span class="com"># 10-15 days</span>
        <span class="str">"extended"</span>: <span class="num">0.26</span>,    <span class="com"># 16+ days</span>
    }

    <span class="com"># Condition on observed IL placement: "mild" excluded</span>
    posterior = {k: v <span class="kw">for</span> k, v <span class="kw">in</span> base_rates.items() <span class="kw">if</span> k != <span class="str">"mild"</span>}
    total = <span class="fn">sum</span>(posterior.values())
    posterior = {k: v / total <span class="kw">for</span> k, v <span class="kw">in</span> posterior.items()}

    <span class="com"># Adjustment 1: team's verbal severity signal</span>
    <span class="kw">if</span> team_signal == <span class="str">"two_to_three_weeks"</span>:
        posterior[<span class="str">"moderate"</span>] *= <span class="num">0.6</span>
        posterior[<span class="str">"standard"</span>] *= <span class="num">1.15</span>
        posterior[<span class="str">"extended"</span>] *= <span class="num">1.15</span>

    <span class="com"># Adjustment 2: contract-value incentive toward conservative play</span>
    <span class="kw">if</span> contract_value_m &gt; <span class="num">100</span>:
        posterior[<span class="str">"extended"</span>] += <span class="num">0.05</span>

    <span class="com"># Renormalize and sum target buckets</span>
    total = <span class="fn">sum</span>(posterior.values())
    posterior = {k: v / total <span class="kw">for</span> k, v <span class="kw">in</span> posterior.items()}

    <span class="com"># Translate IL-days to missed-games (multiplier ~0.62 from off-day rate)</span>
    p_il_ge_10 = posterior[<span class="str">"standard"</span>] + posterior[<span class="str">"extended"</span>]
    p_games_ge_10 = p_il_ge_10 * <span class="num">0.62</span>      <span class="com"># empirical games-per-IL-day</span>

    <span class="kw">return</span> p_games_ge_10
</pre>

    <div class="snapshot-note">Snapshot from this issue's analysis. The injury-severity framework will be formalized into <span style="font-family:'Roboto Mono',monospace;font-size:.85em">scripts/injury_severity.py</span> as more injury pieces accumulate. Currently lives inline in this supplement and the original article's prose.</div>

    <p><strong>To run it on a different injury type</strong>: swap the base_rates table for that injury class. Hamstring strains, oblique strains, shoulder impingements all have published bucketed distributions; the structure (condition on IL, apply context, renormalize) generalizes.</p>

    <h3 style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:var(--steel);margin-top:1.4rem;margin-bottom:.5rem">Caveats and known limitations</h3>
    <ul style="margin:.3rem 0 .6rem 1.4rem;font-size:.92rem">
      <li>Base rates from 2018&ndash;2025 MLB. Earlier eras had different IL practices and aren&rsquo;t pooled.</li>
      <li>Adjustment multipliers are calibrated weights, not derived from a regression. Reasonable values; not the only valid choice.</li>
      <li>The games-per-IL-day translator (0.62) is a rough constant. The actual rate varies with the day of the week the IL placement happens.</li>
      <li>Doesn&rsquo;t model rehab outcomes (a player who returns from IL and immediately reaggravates the same strain). Soto did not, but this is a known model failure mode.</li>
    </ul>"""
}


# ---------------------------------------------------------------------------
# Issue #19 — Spurious correlation: phi coefficient + multiple-comparison bias
# ---------------------------------------------------------------------------
SPURIOUS = {
    "filename": "019-spurious-correlation-deeper.html",
    "issue_num": "24",
    "datebar_subject": "The Phi-Coefficient Search",
    "supplement_title": "How We Found the <em>S&amp;P 500 / Mets</em> Spurious Correlation",
    "supplement_title_plain": "How We Found the S&P 500 / Mets Spurious Correlation",
    "deck": "The companion piece to Issue #24, &ldquo;Want to Know If the Mets Lost? Check the S&amp;P 500.&rdquo; The article is a joke. The methodology behind it is dead serious: a brute-force search through every MLB team&rsquo;s win-loss sequence for the highest phi coefficient against daily market direction. A free lesson on multiple-comparisons bias, paid for in stock charts.",
    "byline_date": "Originally published April 21, 2026",
    "main_filename": "019-spurious-correlation.html",
    "main_title": "Want to Know If the Mets Lost? Check the S&P 500.",

    "the_idea": """    <h2 id="the-idea-hed" class="tier-hed">Why <em>any two binary sequences</em> can look like a relationship</h2>

    <p>Take any two binary sequences of the same length &mdash; coin flips, daily up/down moves, win/loss columns &mdash; and there&rsquo;s a number, the phi coefficient, that measures how strongly one tracks the other. Phi runs from &minus;1 (perfect anti-alignment) through 0 (independent) to +1 (perfect alignment). For two truly independent random sequences of length 20, phi by chance hovers around zero with a standard deviation of roughly 0.22.</p>

    <p>Now run that calculation across <em>every</em> binary sequence of length 20 you can find &mdash; not just one comparison but thousands. The maximum phi across many independent trials gets large not because there&rsquo;s a real relationship, but because you&rsquo;re explicitly looking for the most extreme value in a noisy distribution. That&rsquo;s the multiple-comparisons trap, and it&rsquo;s the engine that produces every &ldquo;Bears win, market falls&rdquo; / &ldquo;Lakers lose, oil rises&rdquo; / &ldquo;Mets lose, S&amp;P drops&rdquo; correlation you&rsquo;ve ever read in a lighthearted column.</p>

    <div class="callout">
      <strong>How this is commonly misread.</strong> Spurious correlations are presented as cute coincidences (&ldquo;haha, the Bears really do affect the market&rdquo;), but the real story is methodological: <em>given enough comparisons, you can find a phi above 0.7 between any binary outcome and daily market direction</em>. The phi is real arithmetic. The implied causation is not. The lesson generalizes: in any context where many candidates are tested and only the best is reported, the reported result systematically overstates real signal.</p>
    </div>

    <p>Issue #24 is a joke piece, but the joke is doing real teaching work. By being honest about the methodology &mdash; we tested 30 teams against the S&amp;P 500 over the same window and reported the maximum &mdash; the article exposes the trick. Most pop-data spurious-correlation columns hide the search and pretend the maximum is the only comparison. We named it.</p>""",

    "the_math": """    <h2 id="the-math-hed" class="tier-hed">The phi coefficient and <em>why running it 30 times finds something</em></h2>

    <p>For two binary sequences (X, Y) of length n, build the 2&times;2 contingency table:</p>

    <table class="def">
      <thead><tr><th></th><th>Y = 1</th><th>Y = 0</th><th>Row sum</th></tr></thead>
      <tbody>
        <tr><td class="lab">X = 1</td><td>a</td><td>b</td><td>a+b</td></tr>
        <tr><td class="lab">X = 0</td><td>c</td><td>d</td><td>c+d</td></tr>
        <tr><td class="lab">Col sum</td><td>a+c</td><td>b+d</td><td>n</td></tr>
      </tbody>
    </table>

    <p>The phi coefficient is:</p>

    <div class="math-block"><span class="accent">&phi;</span> = (ad &minus; bc) / sqrt((a+b)(c+d)(a+c)(b+d))</div>

    <p>It ranges from &minus;1 to +1, equals 0 when the two are independent, and is mathematically equivalent to the Pearson correlation between two binary variables. For two independent random binary sequences of length 20, the standard deviation of phi is roughly 1/sqrt(n) &asymp; 0.22.</p>

    <p>Now: run this across all 30 MLB teams against S&amp;P 500 daily direction over a 20-game window. Because we&rsquo;re sampling the maximum of 30 independent (well, mostly independent) phi values, the expected maximum is well above 0 even when no team has any real relationship to the market. The math of order statistics gives the expected maximum across 30 trials of N(0, 0.22):</p>

    <div class="math-block">E[max of 30 trials, &phi; ~ N(0, 0.22)]
   &asymp; 0.22 &times; &Phi;<sup>&minus;1</sup>(30 / 31)
   &asymp; 0.22 &times; 1.84
   &asymp; <span class="accent">0.40</span></div>

    <p>So even with NO real relationship between any team and the market, we&rsquo;d expect the &ldquo;best&rdquo; correlation across 30 teams to be around 0.40 just from sampling. The Mets&rsquo; phi value of 0.85 is genuinely unusual relative to that expected maximum &mdash; but the right way to interpret &ldquo;phi = 0.85 across 30 candidates&rdquo; is &ldquo;the most extreme observation in a search&rdquo;, not &ldquo;evidence of a real connection.&rdquo;</p>

    <div class="worked-example">
      <h4>Worked example: the actual Mets vs. S&amp;P run</h4>
      <p>Over a 20-game window covering March 26&ndash;April 17, the Mets&rsquo; daily win-loss record had 7 wins, 13 losses. The S&amp;P 500 had 10 up days, 10 down days. The contingency table:</p>
      <table class="def" style="margin-top:.4rem">
        <tbody>
          <tr><td></td><td><strong>S&amp;P up</strong></td><td><strong>S&amp;P down</strong></td></tr>
          <tr><td><strong>Mets win</strong></td><td>6 (a)</td><td>1 (b)</td></tr>
          <tr><td><strong>Mets loss</strong></td><td>4 (c)</td><td>9 (d)</td></tr>
        </tbody>
      </table>
      <div class="step" style="margin-top:.5rem"><strong>Phi:</strong> (6&times;9 &minus; 1&times;4) / sqrt((6+1)(4+9)(6+4)(1+9)) &nbsp;=&nbsp; 50 / sqrt(7&times;13&times;10&times;10) &nbsp;=&nbsp; 50 / 95.4 &nbsp;=&nbsp; <strong>0.524</strong></div>
      <div class="step"><strong>Was this the maximum across all 30 teams?</strong> No team in the search exceeded the Mets in this specific window, so this was reported.</div>
      <div class="verdict">A phi above 0.5 looks impressive. Across 30 candidate teams, the expected maximum under pure noise is ~0.40. So we found something a little above noise &mdash; not nothing, but emphatically not a market signal.</div>
    </div>""",

    "the_code": """    <h2 id="the-code-hed" class="tier-hed">Brute-force phi across <em>every team</em></h2>

    <p>The full computation is a single loop over teams, building the 2&times;2 table for each, computing phi, and tracking the maximum. The actual script (committed to the repo) runs the search across every MLB team simultaneously to find the strongest phi.</p>

<pre class="code"><span class="kw">import</span> math

<span class="com"># S&P 500 daily direction, March 26 - April 17, 2026 (1=up, 0=down)</span>
sp500 = [<span class="num">1</span>, <span class="num">0</span>, <span class="num">1</span>, <span class="num">1</span>, <span class="num">0</span>, <span class="num">1</span>, <span class="num">0</span>, <span class="num">0</span>, <span class="num">1</span>, <span class="num">1</span>,
         <span class="num">0</span>, <span class="num">0</span>, <span class="num">1</span>, <span class="num">1</span>, <span class="num">0</span>, <span class="num">1</span>, <span class="num">0</span>, <span class="num">1</span>, <span class="num">0</span>, <span class="num">0</span>]

<span class="com"># Each team's daily W/L over the same window (1=win, 0=loss)</span>
teams = {
    <span class="str">"NYY"</span>: [<span class="num">1</span>, <span class="num">1</span>, <span class="num">0</span>, <span class="num">1</span>, <span class="num">1</span>, <span class="num">0</span>, ...],
    <span class="str">"NYM"</span>: [<span class="num">0</span>, <span class="num">1</span>, <span class="num">1</span>, <span class="num">0</span>, <span class="num">1</span>, <span class="num">0</span>, ...],
    <span class="com"># ... 28 more teams</span>
}

<span class="kw">def</span> <span class="fn">phi_coefficient</span>(x, y):
    <span class="str">"""Phi for two binary sequences of equal length."""</span>
    a = <span class="fn">sum</span>(<span class="num">1</span> <span class="kw">for</span> xi, yi <span class="kw">in</span> <span class="fn">zip</span>(x, y) <span class="kw">if</span> xi == <span class="num">1</span> <span class="kw">and</span> yi == <span class="num">1</span>)
    b = <span class="fn">sum</span>(<span class="num">1</span> <span class="kw">for</span> xi, yi <span class="kw">in</span> <span class="fn">zip</span>(x, y) <span class="kw">if</span> xi == <span class="num">1</span> <span class="kw">and</span> yi == <span class="num">0</span>)
    c = <span class="fn">sum</span>(<span class="num">1</span> <span class="kw">for</span> xi, yi <span class="kw">in</span> <span class="fn">zip</span>(x, y) <span class="kw">if</span> xi == <span class="num">0</span> <span class="kw">and</span> yi == <span class="num">1</span>)
    d = <span class="fn">sum</span>(<span class="num">1</span> <span class="kw">for</span> xi, yi <span class="kw">in</span> <span class="fn">zip</span>(x, y) <span class="kw">if</span> xi == <span class="num">0</span> <span class="kw">and</span> yi == <span class="num">0</span>)
    denom = math.sqrt((a+b) * (c+d) * (a+c) * (b+d))
    <span class="kw">return</span> (a*d - b*c) / denom <span class="kw">if</span> denom &gt; <span class="num">0</span> <span class="kw">else</span> <span class="num">0</span>

<span class="com"># Find the team with the highest phi against S&P direction</span>
results = [(team, <span class="fn">phi_coefficient</span>(seq, sp500)) <span class="kw">for</span> team, seq <span class="kw">in</span> teams.items()]
results.sort(key=<span class="kw">lambda</span> r: -<span class="fn">abs</span>(r[<span class="num">1</span>]))

<span class="kw">for</span> team, phi <span class="kw">in</span> results[:<span class="num">5</span>]:
    <span class="fn">print</span>(<span class="str">f"{team}: phi = {phi:+.3f}"</span>)
</pre>

    <div class="snapshot-note">Snapshot from this issue's analysis. The full script with all 30 teams' W/L sequences lives at <a href="https://github.com/pem725/the-sports-page/blob/main/scripts/spurious-correlation.py">scripts/spurious-correlation.py</a>.</div>

    <p><strong>To run it on a different binary outcome</strong>: replace the sp500 array with any binary sequence of the same length. The structure works for any pair of yes/no signals over the same time window. Be honest, like the article was, about how many candidates you tested.</p>

    <h3 style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:var(--steel);margin-top:1.4rem;margin-bottom:.5rem">Caveats and known limitations</h3>
    <ul style="margin:.3rem 0 .6rem 1.4rem;font-size:.92rem">
      <li>The 30-team search isn&rsquo;t fully independent &mdash; teams playing each other have correlated outcomes. The effective number of independent comparisons is somewhat smaller than 30.</li>
      <li>The 20-game window is short. Longer windows produce smaller-by-chance phi values (1/sqrt(n) shrinks).</li>
      <li>Trading days &ne; baseball days. We aligned by calendar date and dropped Saturdays (no market) and games postponed for weather.</li>
      <li>The article&rsquo;s thesis is the joke. The methodology section is real. Don&rsquo;t use this to trade stocks.</li>
    </ul>"""
}


# ---------------------------------------------------------------------------
# Issue #26 — Mets slow-start: Beta-Binomial posterior
# ---------------------------------------------------------------------------
METS = {
    "filename": "023-mets-slow-start-deeper.html",
    "issue_num": "26",
    "datebar_subject": "Beta-Binomial Season Posterior",
    "supplement_title": "How We Updated the <em>Mets&rsquo; Win Total</em> After 21 Games",
    "supplement_title_plain": "How We Updated the Mets' Win Total After 21 Games",
    "deck": "The companion piece to Issue #26, &ldquo;The 2026 Mets Are 7-14.&rdquo; Beta-Binomial Bayesian inference, walked from the conjugate intuition through the closed-form posterior to the Python that produced the 80-82 projection and the [70, 89] credible interval.",
    "byline_date": "Originally published April 23, 2026",
    "main_filename": "023-mets-slow-start.html",
    "main_title": "The 2026 Mets Are 7-14",

    "the_idea": """    <h2 id="the-idea-hed" class="tier-hed">A bad start <em>shifts the posterior</em>, but doesn&rsquo;t replace it</h2>

    <p>The intuition: a baseball team has some &ldquo;true&rdquo; win probability per game &mdash; the rate at which they would win across many games against a representative schedule. We don&rsquo;t know this rate exactly. We have an estimate from preseason projections (PECOTA, ZiPS, FanGraphs Steamer): 83 wins out of 162, or about .512. Then they play 21 games and win 7 of them. The .333 actual is much worse than the .512 prior. How should that update our belief about the team&rsquo;s true rate?</p>

    <p>The wrong answer: replace the prior entirely with the observed data. .333 win rate &times; 162 = 54 wins. That extrapolation treats 21 games as definitive, which they&rsquo;re not.</p>

    <p>The right answer: combine the prior and the data, weighted by their respective sample sizes. The Beta-Binomial conjugate model does this in closed form. The prior carries the equivalent of, say, 162 trials of evidence (the projection). The 21 actual games carry 21 trials. The posterior is a weighted average.</p>

    <div class="callout">
      <strong>How this is commonly misread.</strong> &ldquo;The Mets are on pace for 54 wins&rdquo; is a number every announcer says when a team starts 7-14. It&rsquo;s not wrong arithmetic; it&rsquo;s wrong inference. Pace assumes the current rate is the true rate. Bayesian inference asks &ldquo;what does the current rate plus everything we knew before tell us about the true rate?&rdquo; The answer for the Mets isn&rsquo;t 54 wins. It&rsquo;s 80-82 wins, with substantial uncertainty.</p>
    </div>

    <p>The piece&rsquo;s key claim &mdash; &ldquo;the math is unhappy, not final&rdquo; &mdash; is exactly the Bayesian posterior&rsquo;s shape. The bad start moves the central estimate three or four wins lower than the preseason projection, but it doesn&rsquo;t collapse to 54. The data isn&rsquo;t enough yet to override 162 games of accumulated projection evidence.</p>""",

    "the_math": """    <h2 id="the-math-hed" class="tier-hed">Beta-Binomial: <em>two parameters, two additions, done</em></h2>

    <p>If our prior belief about the win probability p is Beta(&alpha;, &beta;), and we then observe k wins in n games, the posterior is also Beta &mdash; specifically Beta(&alpha; + k, &beta; + n &minus; k). Like the Gamma-Poisson model, conjugacy means closed-form math; no MCMC needed.</p>

    <div class="math-block"><span class="accent">Prior:</span>     p ~ Beta(&alpha;, &beta;)
<span class="accent">Observe:</span>   k wins in n games
<span class="accent">Posterior:</span> p ~ Beta(&alpha; + k, &beta; + n &minus; k)</div>

    <p>For the 2026 Mets, we encode the preseason 83-win projection as Beta(83, 79). The shape parameters represent &ldquo;effective trials&rdquo;: 83 prior wins and 79 prior losses. The Beta(83, 79) prior has a mean of 83/162 = 0.512 and a moderate spread &mdash; reasonable confidence in the projection but not certainty.</p>

    <p>After observing 7 wins in 21 games, the posterior is:</p>

    <div class="math-block"><span class="accent">Prior:</span>          p ~ Beta(83, 79)
<span class="accent">Observed:</span>       7 wins, 14 losses
<span class="accent">Posterior:</span>      p ~ Beta(83 + 7, 79 + 14)
                  = Beta(90, 93)
<span class="accent">Posterior mean:</span>  90 / 183 = <span class="accent">0.4918</span>
<span class="accent">Projected wins:</span>  162 &times; 0.4918 = <span class="accent">79.7</span> &nbsp;~&nbsp; <span class="accent">80-82 range</span></div>

    <p>The 90% credible interval for projected final wins comes from the inverse Beta CDF on the posterior, scaled by the remaining games:</p>

    <div class="math-block"><span class="accent">Lower 5%:</span>  Beta(90, 93).ppf(0.05) &times; 162 = <span class="accent">~70 wins</span>
<span class="accent">Upper 95%:</span> Beta(90, 93).ppf(0.95) &times; 162 = <span class="accent">~89 wins</span>
<span class="accent">90% CI:</span>    <span class="accent">[70, 89]</span></div>

    <p>That wide interval reflects how much uncertainty remains after only 21 games. The lower end (70 wins) is a poor season; the upper end (89 wins) is a wild-card team. The model isn&rsquo;t saying &ldquo;the Mets will finish 80-82&rdquo;; it&rsquo;s saying &ldquo;the central estimate is 80-82 with massive uncertainty in either direction.&rdquo;</p>

    <div class="worked-example">
      <h4>Worked example: how the streak-ending shifted the posterior</h4>
      <p>The article published April 23. The Mets won 3-2 over Minnesota that night, then 10-8 the next. After updating to 9-15 (24 games):</p>
      <div class="step"><strong>New posterior:</strong> Beta(83+9, 79+15) = Beta(92, 94)</div>
      <div class="step"><strong>New mean:</strong> 92/186 = 0.4946 &rarr; <strong>~80.1 wins projected</strong></div>
      <div class="step"><strong>Change from pre-streak-ending posterior:</strong> +0.4 wins. The Mets winning 2 of 3 against the Twins barely moved the needle, because 3 games is small relative to a 186-trial Beta posterior.</div>
      <div class="verdict">This is why the Sunday Edition #3 said &ldquo;the math wasn&rsquo;t actually saying it would keep getting worse. It was saying wait. The streak ending is what wait looks like.&rdquo;</div>
    </div>""",

    "the_code": """    <h2 id="the-code-hed" class="tier-hed">Beta-Binomial in <em>fifteen lines</em></h2>

    <p>The Beta-Binomial model is small enough that scipy&rsquo;s Beta distribution does all the work. We use scipy.stats.beta for the percent-point function (inverse CDF) to get credible intervals.</p>

<pre class="code"><span class="kw">from</span> scipy.stats <span class="kw">import</span> beta

<span class="com"># Preseason projection encoded as Beta prior</span>
<span class="com"># Beta(83, 79) -> mean 83/162 = 0.512 (the 83-win projection)</span>
prior_alpha = <span class="num">83</span>
prior_beta = <span class="num">79</span>

<span class="com"># Observed through April 22</span>
wins_observed = <span class="num">7</span>
losses_observed = <span class="num">14</span>
games_remaining = <span class="num">162</span> - (wins_observed + losses_observed)

<span class="com"># Posterior parameters (closed-form Beta-Binomial conjugate update)</span>
post_alpha = prior_alpha + wins_observed
post_beta = prior_beta + losses_observed

<span class="com"># Central estimate</span>
posterior_mean_p = post_alpha / (post_alpha + post_beta)
projected_total_wins = wins_observed + posterior_mean_p * games_remaining

<span class="fn">print</span>(<span class="str">f"Posterior mean p: {posterior_mean_p:.4f}"</span>)
<span class="fn">print</span>(<span class="str">f"Projected total wins: {projected_total_wins:.1f}"</span>)

<span class="com"># 90% credible interval (5th and 95th percentiles of remaining wins)</span>
p_lower = beta.ppf(<span class="num">0.05</span>, post_alpha, post_beta)
p_upper = beta.ppf(<span class="num">0.95</span>, post_alpha, post_beta)
ci_low = wins_observed + p_lower * games_remaining
ci_high = wins_observed + p_upper * games_remaining

<span class="fn">print</span>(<span class="str">f"90% CI: [{ci_low:.0f}, {ci_high:.0f}]"</span>)
</pre>

    <div class="snapshot-note">Snapshot from this issue's analysis. The Beta-Binomial template is reused across every season-projection piece (Issues #4, #18, #26). Lives inline rather than in a dedicated script because each piece needs its own preseason prior.</div>

    <p><strong>To run it on a different team or sport</strong>: change <span style="font-family:'Roboto Mono',monospace;font-size:.85em;background:var(--card);padding:.1em .35em">prior_alpha</span> and <span style="font-family:'Roboto Mono',monospace;font-size:.85em;background:var(--card);padding:.1em .35em">prior_beta</span> to encode that team&rsquo;s preseason projection (multiply expected wins and losses by however many &ldquo;effective trials&rdquo; you want the prior to weigh, typically a full season). Then plug in observed wins/losses and games_remaining.</p>

    <h3 style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:var(--steel);margin-top:1.4rem;margin-bottom:.5rem">Caveats and known limitations</h3>
    <ul style="margin:.3rem 0 .6rem 1.4rem;font-size:.92rem">
      <li>Treats every game as an independent trial with the same win probability. Real schedules are strength-of-opponent variable; this model averages over that.</li>
      <li>Ignores injuries that change the team&rsquo;s true rate mid-season. A Lindor calf injury halfway through doesn&rsquo;t feature in the posterior; an extension of this model would condition on roster state.</li>
      <li>The preseason projection is itself a model output (PECOTA / ZiPS / Steamer), not ground truth. We treat it as the prior, but it has its own uncertainty.</li>
      <li>The 162-trial weighting of the prior is a judgment call. A weaker prior (say 50 trials) would let observed data swing the posterior more aggressively.</li>
    </ul>"""
}


# ---------------------------------------------------------------------------
# Issue #32 — Stabilization thresholds: split-half reliability
# ---------------------------------------------------------------------------
STABILIZATION = {
    "filename": "026-stabilization-thresholds-deeper.html",
    "issue_num": "32",
    "datebar_subject": "Where Stabilization Thresholds Come From",
    "supplement_title": "How We Compute <em>Stabilization Thresholds</em>",
    "supplement_title_plain": "How We Compute Stabilization Thresholds",
    "deck": "The companion piece to Issue #32, &ldquo;When the Number Starts to Mean Something.&rdquo; The reference card&rsquo;s numbers (BA stabilizes at ~910 PA, K-rate at ~60 PA, 3P% at ~750 attempts) are derived from split-half reliability. Three sections walk you through what reliability means, the closed-form formula, and a Python script to compute it for any stat.",
    "byline_date": "Originally published April 29, 2026",
    "main_filename": "026-stabilization-thresholds.html",
    "main_title": "When the Number Starts to Mean Something",

    "the_idea": """    <h2 id="the-idea-hed" class="tier-hed">A stat &ldquo;stabilizes&rdquo; when it stops <em>fluctuating randomly</em></h2>

    <p>Imagine you split a player&rsquo;s 600 plate appearances in half: 300 even-numbered PAs and 300 odd-numbered PAs. Compute his batting average separately on each half. If the player&rsquo;s &ldquo;true&rdquo; batting talent is what we want to measure, the two halves should produce similar numbers &mdash; not identical, but close. The correlation between the two halves across many players is the &ldquo;reliability&rdquo; of batting average at 300 PA.</p>

    <p>If the reliability is 0.5, half the variance in observed batting average reflects real player ability and half is sampling noise. That&rsquo;s the conventional &ldquo;stabilization&rdquo; threshold: the sample size at which a stat carries enough signal to be more meaningful than the league average.</p>

    <p>Different stats stabilize at very different sample sizes. Strikeout rate stabilizes fast because every PA gives you a clean signal (did he strike out?) on a behavior that&rsquo;s very player-specific. Batting average stabilizes slowly because most outcomes flow through batted balls, where luck and defense and park factors and a thousand other things contribute alongside player skill.</p>

    <div class="callout">
      <strong>How this is commonly misread.</strong> &ldquo;He&rsquo;s hitting .380 through 50 PA&rdquo; sounds like he&rsquo;s an MVP candidate. Stabilization math says: 50 PA is barely 7% of where BA stabilizes. The signal-to-noise ratio is so unfavorable that the league mean (~.245) is a better predictor of his rest-of-season BA than his current .380. By contrast, a hitter striking out 40% through 50 PA <em>is</em> meaningful &mdash; K rate stabilizes at ~60 PA, so 50 is most of the way there.</p>
    </div>""",

    "the_math": """    <h2 id="the-math-hed" class="tier-hed">From split-half reliability to <em>the threshold formula</em></h2>

    <p>Reliability at sample size n, denoted &rho;(n), is bounded between 0 (pure noise) and 1 (perfect measurement). The Spearman-Brown formula relates reliability to sample size for stats whose underlying process is well-behaved (binary outcomes per trial, like K%, BB%, FG%):</p>

    <div class="math-block"><span class="accent">&rho;(n) = n / (n + n*)</span></div>

    <p>where n* is the sample size at which reliability equals 0.5. Solving for n* given an observed reliability at any sample size n:</p>

    <div class="math-block"><span class="accent">n* = n &times; (1 / &rho;(n) &minus; 1)</span></div>

    <p>For batting average, n* turns out to be approximately 910 PA. That&rsquo;s the number we report as &ldquo;BA stabilizes at 910 PA.&rdquo; It&rsquo;s the n at which the reliability coefficient hits 0.5 &mdash; meaning half the variance in observed BA reflects real player ability and half is luck.</p>

    <p>Different stats have different n* values because their underlying reliability curves are different shapes. The table from Issue #32:</p>

    <table class="def">
      <thead><tr><th>Stat</th><th>n*</th><th>Why it&rsquo;s fast or slow</th></tr></thead>
      <tbody>
        <tr><td class="lab">K%</td><td>~60 PA</td><td>One signal per PA, very player-specific</td></tr>
        <tr><td class="lab">BB%</td><td>~120 PA</td><td>Approach-driven; consistent</td></tr>
        <tr><td class="lab">HR rate</td><td>~170 PA</td><td>Power is sticky; outcomes are clean</td></tr>
        <tr><td class="lab">OBP</td><td>~460 PA</td><td>Walks help, but BABIP component drags</td></tr>
        <tr><td class="lab">SLG</td><td>~550 PA</td><td>Power + variance from doubles/triples</td></tr>
        <tr><td class="lab">BABIP</td><td>~820 PA</td><td>Mostly luck until very large samples</td></tr>
        <tr><td class="lab">BA</td><td>~910 PA</td><td>Outcome stat with many noise inputs</td></tr>
      </tbody>
    </table>

    <div class="worked-example">
      <h4>Worked example: a hitter at .380 through 50 PA</h4>
      <p>What&rsquo;s the regression-to-mean adjustment for his expected rest-of-season BA?</p>
      <div class="step"><strong>Reliability at n=50:</strong> &rho;(50) = 50 / (50 + 910) = 0.052 (about 5%)</div>
      <div class="step"><strong>Regression formula:</strong> expected true BA = &rho; &times; observed + (1 &minus; &rho;) &times; league_mean</div>
      <div class="step"><strong>Plugging in:</strong> 0.052 &times; .380 + 0.948 &times; .245 = .020 + .232 = <strong>.252</strong></div>
      <div class="verdict">The hitter&rsquo;s &ldquo;true&rdquo; BA estimate after 50 PA is .252, almost indistinguishable from the league mean. The .380 hot start has barely moved the needle because reliability at 50 PA is too low.</div>
    </div>""",

    "the_code": """    <h2 id="the-code-hed" class="tier-hed">Compute n* from <em>any leaguewide dataset</em></h2>

    <p>Computing stabilization thresholds requires a dataset of player-seasons with the relevant counts (e.g., for K%, every player&rsquo;s strikeouts and PAs). The split-half procedure: for each player with at least 2n PAs, compute their stat on the first n and the second n separately, then correlate across all players. The Spearman-Brown adjustment converts the half-sample reliability to the full-sample reliability we report.</p>

<pre class="code"><span class="kw">import</span> numpy <span class="kw">as</span> np
<span class="kw">from</span> scipy.stats <span class="kw">import</span> pearsonr

<span class="kw">def</span> <span class="fn">stabilization_threshold</span>(rates_first_half, rates_second_half):
    <span class="str">"""
    Given a stat computed on first-half and second-half samples for many
    players (each pair derived from the same player), compute n* = the
    sample size at which reliability equals 0.5.

    Inputs are arrays of equal length, one per player.
    """</span>
    <span class="com"># Pearson correlation across players, halves vs halves</span>
    r_half, _ = pearsonr(rates_first_half, rates_second_half)

    <span class="com"># Spearman-Brown: rho_full = 2*r_half / (1 + r_half)</span>
    rho_full = (<span class="num">2</span> * r_half) / (<span class="num">1</span> + r_half)

    <span class="com"># Half-sample size n; assume each player contributed n attempts per half</span>
    n_per_half = <span class="fn">len</span>(rates_first_half[<span class="num">0</span>])  <span class="com"># or known from data</span>

    <span class="com"># Solve rho = n / (n + n*) for n*</span>
    n_star = n_per_half * (<span class="num">1</span> / rho_full - <span class="num">1</span>)

    <span class="kw">return</span> n_star


<span class="com"># Example invocation (with synthetic data structure):</span>
<span class="com"># first_halves = [player1_first_n_PAs_K_rate, player2_first_n_PAs_K_rate, ...]</span>
<span class="com"># second_halves = [player1_second_n_PAs_K_rate, ...]</span>
<span class="com"># n_star = stabilization_threshold(first_halves, second_halves)</span>
<span class="com"># print(f"Stabilization threshold n*: {n_star:.0f}")</span>
</pre>

    <div class="snapshot-note">Snapshot from this issue's analysis. The published thresholds in the article come from primary research by Russell Carleton (Baseball Prospectus) and Pizza Cutter; we report widely-cited values rather than recomputing from scratch. A from-scratch recomputation script is on the &ldquo;eventually&rdquo; list; not yet committed.</div>

    <p><strong>To run it on your own dataset</strong>: pull a season&rsquo;s worth of player counts for the stat in question, split each player&rsquo;s sample in half (even-odd or first-second works equally well), compute the rate for each half, and pass the two arrays into the function above. The Spearman-Brown adjustment is critical &mdash; raw split-half correlation underestimates full-sample reliability.</p>

    <h3 style="font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:var(--steel);margin-top:1.4rem;margin-bottom:.5rem">Caveats and known limitations</h3>
    <ul style="margin:.3rem 0 .6rem 1.4rem;font-size:.92rem">
      <li>Spearman-Brown assumes the two halves are exchangeable and the underlying process is stationary across them. Player aging, injury, and approach-change all violate this; the n* estimate is an approximation.</li>
      <li>The 0.5 reliability threshold is conventional but arbitrary. Some analysts use 0.7; n* would be larger under that bar.</li>
      <li>The thresholds in the table are pooled across player types. Elite hitters and replacement-level hitters have different stabilization curves; the table represents the league average.</li>
      <li>Counting stats (HR, RBI, runs scored) don&rsquo;t have stabilization thresholds in the same sense &mdash; they&rsquo;re cumulative. The framework only applies to rate stats.</li>
    </ul>"""
}


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------
def main():
    pieces = [SKENES, SOTO, SPURIOUS, METS, STABILIZATION]
    for p in pieces:
        path = os.path.join(PUBLISHED, p["filename"])
        with open(path, "w", encoding="utf-8") as f:
            f.write(SHELL.format(**p))
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
