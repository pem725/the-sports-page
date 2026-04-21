#!/usr/bin/env python3
"""
Batch-generate 5 queue drafts from a shared broadsheet template.
Each piece's prose is defined in PIECES below; CSS/masthead/footer is shared.
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(REPO, "queue")

# Shared broadsheet CSS + masthead + closing structure (condensed version of
# the pattern used across The Sports Page)
SHELL = """<!-- PUBLISH-META
topic: {topic}
tags: {tags}
-->
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Sports Page — Issue No. __ — April __, 2026</title>
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
.math{{font-family:'Roboto Mono',monospace;background:rgba(255,255,255,.1);padding:.7rem 1rem;font-size:.8rem;color:#eef6ff;margin:.6rem 0;line-height:1.9;white-space:pre-wrap}}
table.rec{{width:100%;border-collapse:collapse;font-size:.88rem;margin:1rem 0}}
table.rec th{{font-family:'Roboto Mono',monospace;font-size:.63rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:2px solid var(--ink);padding:.4rem .6rem;text-align:left}}
table.rec td{{padding:.45rem .6rem;border-bottom:1px solid var(--div);vertical-align:top}}
table.rec tr:last-child td{{border-bottom:none}}
table.rec .mono{{font-family:'Roboto Mono',monospace;font-size:.78rem;color:var(--muted)}}
table.rec .hl td{{background:#e0f0e8;font-weight:700}}
table.rec .hl .mono{{color:var(--green)}}
table.rec .match td{{background:#fff3d6}}
table.rec .match .mono{{color:var(--gold);font-weight:700}}
table.rec .worse td{{background:#fef0ec}}
table.rec .worse .mono{{color:var(--rust)}}
.footer{{border-top:3px double var(--ink);padding-top:.7rem;margin-top:2rem;display:flex;justify-content:space-between;flex-wrap:wrap;gap:.3rem;font-family:'Roboto Mono',monospace;font-size:.63rem;color:var(--muted);letter-spacing:.07em}}
hr{{border:none;border-top:1px solid var(--div);margin:1.5rem 0}}
.skip-link{{position:absolute;top:-40px;left:0;background:var(--ink);color:var(--cream);padding:.5rem 1rem;z-index:100;font-family:"Roboto Mono",monospace;font-size:.75rem;transition:top .2s}}.skip-link:focus{{top:0}}
</style>
<script data-goatcounter="https://thesportspage.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>

</head>
<body>
<a href="#main-content" class="skip-link">Skip to main content</a>
<div class="masthead">
  <div class="kicker">{kicker}</div>
  <div class="title"><a href="../index.html" style="color:inherit;text-decoration:none">The Sports Page</a></div>
  <div class="tagline">Making the numbers mean something since the first pitch</div>
  <div class="datebar"><span>Issue No. __</span><span>April __, 2026</span><span>Distributed Free to Friends &amp; Family</span></div>
</div>
<nav style="max-width:820px;margin:.4rem auto 0;font-family:'Roboto Mono',monospace;font-size:.7rem;letter-spacing:.08em"><a href="../index.html" style="color:var(--rust);text-decoration:none;border-bottom:1px solid rgba(184,58,30,.3)">&larr; Back to Archive</a></nav>
<div id="main-content" class="paper">
{body}
<div class="footer">
  <span>The Sports Page &middot; Issue No. __</span>
  <span>{footer_meta}</span>
  <span>Not financial or wagering advice</span>
</div>
</div>
<div id="share" style="max-width:820px;margin:1.5rem auto 0;background:var(--ink);padding:2.5rem 3rem;box-shadow:0 6px 40px rgba(0,0,0,.3);text-align:center">
  <img src="../assets/banner.png" alt="The Sports Page" style="max-width:360px;height:auto;margin:0 auto 1.2rem;display:block;opacity:.9">
  <div style="font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;color:#c9962a;margin-bottom:.4rem">Share The Sports Page</div>
  <div style="font-family:'Libre Baskerville',serif;font-size:.88rem;color:#a09070;font-style:italic;margin-bottom:1.4rem">Scan the code or share the link. Free, always.</div>
  <img src="../assets/qr-code.png" alt="QR Code" style="width:180px;height:180px;display:block;margin:0 auto 1rem;border:6px solid #c9962a;padding:4px;background:#fff">
  <div style="font-family:'Roboto Mono',monospace;font-size:.75rem;color:#c9962a;letter-spacing:.08em;margin-bottom:.3rem">pem725.github.io/the-sports-page</div>
  <div style="font-family:'Roboto Mono',monospace;font-size:.6rem;color:#6b5e4a;letter-spacing:.1em;margin-top:1rem">&copy; 2026 The Sports Page &middot; A Statistical Dispatch for Friends &amp; Family</div>
</div>
</body>
</html>
"""


def build(filename, meta):
    path = os.path.join(QUEUE, filename)
    with open(path, "w") as f:
        f.write(SHELL.format(**meta))
    print(f"wrote {path}")


# ---------------------------------------------------------------------------
# PIECE 1: #2 Mets slow-start thesis
# ---------------------------------------------------------------------------
METS_SLOW_START = {
    "topic": "MLB",
    "tags": "MLB:mlb, Mets, Small Sample, Base Rates, Bayesian",
    "kicker": "A Statistical Dispatch on Bad Starts &middot; Baseball, 2026",
    "footer_meta": "Prior: Beta(43, 43) from preseason 83-win projection",
    "body": """
<h1 class="hed">The 2026 Mets Are 7-14. The Math Is <em>Unhappy</em>, Not Final.</h1>
<div class="deck">Twenty-one games in. An eleven-game losing streak. The worst start the team has produced since 1983. What the historical base rate says about where this ends.</div>
<div class="byline">By The Professor &middot; The Sports Page &middot; Small-Sample Baseball</div>
<div class="stat-row">
  <div class="sc"><div class="v bad">7-14</div><div class="l">Through 21 Games</div></div>
  <div class="sc"><div class="v now">11</div><div class="l">Consecutive Losses</div></div>
  <div class="sc"><div class="v" style="color:var(--gold)">1983</div><div class="l">Last Mets Start This Bad</div></div>
</div>

<p>Twenty-one games. That is the sample. It is enough to lose an eleven-game streak in and enough to have the worst record in the National League, but it is not enough, by any honest statistical standard, to conclude the season. The right question is not whether the start looks bad. The start is 7 wins against 14 losses; the start, descriptively, is bad. The right question is what a 7-14 start through 21 games has historically implied about a team&rsquo;s full season &mdash; and what it implies for a team whose preseason projection called for eighty-three wins.</p>

<h2 class="sh">The Arithmetic of 21 Games</h2>

<p>The Mets have played 21 of 162 scheduled games. That is 13% of the season. Their winning percentage through 21 is .333; to finish at .500 &mdash; 81-81 &mdash; they would need to go 74-67 over the remaining 141 games, a .525 pace. That is reasonable: about what a league-average team produces over any 141-game stretch. To finish at their preseason projection of 83 wins, the required stretch pace is roughly .539. Still achievable. Difficult, but not fantastical.</p>

<p>To miss the playoffs outright would require continuing at roughly the current pace for another month or two. That is not a prediction; it is a statement about what would have to be true.</p>

<div class="box">
  <h3>The Bayesian Update, Briefly</h3>
  <div class="math">Preseason prior (projection 83-79):  Beta(83, 79)
Observed through 21:               7 wins, 14 losses
Posterior:                         Beta(90, 93)
Posterior mean win %:              .492
Posterior 90% credible interval:   [.433, .551]
Projected final record (at mean):  80 &ndash; 82</div>
  <p>The Beta-Binomial conjugate update treats the preseason projection as prior evidence and the 21 observed games as new data. The posterior pulls the season projection down by three wins &mdash; from 83 to 80 &mdash; but does not collapse it. The 90% credible interval spans roughly 70 to 89 wins. That is wide, because 21 games is wide. A genuine answer requires more games, not more anger.</p>
</div>

<h2 class="sh">What Has Historically Happened to Teams Starting This Poorly</h2>

<p>Published base-rate analyses of slow starts are not universally consistent on exact thresholds, and a clean "P(playoffs | 7-14 start)" across every season since 1969 is not trivially available. What is clear from the cases:</p>

<p>The <strong>2019 Washington Nationals</strong> were 19-31 at their fiftieth game &mdash; a noticeably worse position than the 2026 Mets have reached &mdash; and won the World Series. The <strong>2011 St. Louis Cardinals</strong> sat at or below .500 deep into August and are one of five teams with the worst regular-season records ever to win a World Series. The <strong>2005 Houston Astros</strong> started 15-30 and reached the World Series. The <strong>1991 Atlanta Braves</strong> famously "worst to first."</p>

<p>The pattern is not "bad starts always recover." The pattern is that <em>some</em> teams starting at or below the Mets&rsquo; current pace have recovered all the way to a championship, and many more have recovered to respectability. What the history of slow starts tells us, as a class, is what the posterior above tells us: the start shifts the prior, but it does not determine the ending.</p>

<div class="pull">
  <p>&ldquo;The start is bad. It is not final. Seven wins through twenty-one games is enough to make the summer difficult and not enough to decide what the summer will be.&rdquo;</p>
  <cite>&mdash; The Professor, on reading the box score in April</cite>
</div>

<h2 class="sh">What Would Actually Settle It</h2>

<p>Two numbers to watch over the next thirty games: the team&rsquo;s run differential, which is less noisy than its win-loss record, and whether the bullpen continues to give back leads in the late innings. A Mets team that starts pushing run differential toward even has a path back to 80 wins. A Mets team that continues to hemorrhage runs in the seventh and eighth innings has a different conversation ahead.</p>

<p>This newsletter will publish a prediction scorecard every Sunday. The 2026 Mets final-record projection will be rerun with fresh data each week. Today: 80-82, 90% credible interval [70, 89]. Check back.</p>
"""
}

# ---------------------------------------------------------------------------
# PIECE 2: #6 Mets diaspora
# ---------------------------------------------------------------------------
METS_DIASPORA = {
    "topic": "MLB",
    "tags": "MLB:mlb, Mets, Front Office, HIT/MISS",
    "kicker": "A Statistical Dispatch on Departures &middot; Baseball, 2026",
    "footer_meta": "Framework: HIT (player declined), MISS (thrived elsewhere), NEUTRAL, TBD",
    "body": """
<h1 class="hed">The Mets Diaspora: Three Years of <em>Departures</em>, One Ongoing Indictment</h1>
<div class="deck">Since 2023, the Mets have parted with a meaningful number of players. The roster that replaced them is currently 7-14. The honest accounting is neither "they let everyone go too cheap" nor "every departure was correct." It is somewhere uncomfortable in between, and the replacements are the part that hurts.</div>
<div class="byline">By The Columnist &middot; The Sports Page &middot; On the Cost of Letting Someone Walk</div>

<div class="stat-row">
  <div class="sc"><div class="v bad">3</div><div class="l">Years of Decisions</div></div>
  <div class="sc"><div class="v now">HIT/MISS</div><div class="l">Grading Framework</div></div>
  <div class="sc"><div class="v" style="color:var(--gold)">?</div><div class="l">Replacement Net WAR</div></div>
</div>

<p>The front office&rsquo;s job is not to retain every useful player. It is to correctly estimate the gap between what a departing player will produce for someone else and what the replacement will produce in his role. A HIT is a player the Mets correctly let go &mdash; he declined, got hurt, or merely approximated his replacement. A MISS is a player who thrived elsewhere while the replacement underperformed. A NEUTRAL outcome is a wash. The question is the overall ledger.</p>

<h2 class="sh">The Framework, Applied</h2>

<p>Between the 2023-24 and 2024-25 offseasons, the Mets parted with a number of notable names via free agency or trade. Among them: <strong>Edwin D&iacute;az</strong> (to the Dodgers, where he has begun to show the injury trouble he flirted with in New York), <strong>Harrison Bader</strong>, <strong>Jos&eacute; Quintana</strong>, <strong>Adam Ottavino</strong>, <strong>Seth Lugo</strong>, <strong>Trevor May</strong>, <strong>Trevor Williams</strong>, and &mdash; most significantly &mdash; <strong>Pete Alonso</strong>, who reached free agency.</p>

<p>Three years is long enough for a ledger. It is not yet long enough to close the book on any single case. The table below is an in-progress grading of the most consequential departures, with methodology and criteria held constant across cases.</p>

<table class="rec">
<thead><tr><th>Departed</th><th>Destination</th><th>Years since Mets</th><th>Early verdict</th></tr></thead>
<tbody>
  <tr class="hl"><td>Edwin D&iacute;az</td><td class="mono">Dodgers</td><td class="mono">1</td><td class="mono">HIT: injuries returning</td></tr>
  <tr><td>Harrison Bader</td><td class="mono">TBD</td><td class="mono">1</td><td class="mono">TBD: small sample</td></tr>
  <tr><td>Jos&eacute; Quintana</td><td class="mono">TBD</td><td class="mono">1</td><td class="mono">TBD</td></tr>
  <tr><td>Adam Ottavino</td><td class="mono">TBD</td><td class="mono">1</td><td class="mono">TBD</td></tr>
  <tr><td>Seth Lugo</td><td class="mono">elsewhere</td><td class="mono">2</td><td class="mono">MISS: All-Star production</td></tr>
  <tr><td>Trevor May</td><td class="mono">retired</td><td class="mono">2</td><td class="mono">HIT: natural decline</td></tr>
  <tr><td>Trevor Williams</td><td class="mono">TBD</td><td class="mono">1</td><td class="mono">TBD</td></tr>
  <tr class="match"><td>Pete Alonso</td><td class="mono">free agency</td><td class="mono">1</td><td class="mono">Critical; case pending</td></tr>
</tbody>
</table>

<p>A partial accounting. This table is open for revision; readers should not treat individual grades as final. The tentative pattern is mixed &mdash; some departures look defensible (D&iacute;az, May), some look painful (Lugo). The interesting question is not whether the individual departures were correct. It is whether the <em>replacements</em> were.</p>

<h2 class="sh">The Replacement Question</h2>

<p>The Mets&rsquo; current 7-14 record was not produced by the absences of Lugo or D&iacute;az in isolation. It was produced by a roster that, when measured in the slots where those players used to produce, has given back less than projected. The bullpen that was supposed to compensate for D&iacute;az departing has been unsteady. The rotation depth that was supposed to compensate for Quintana and Lugo has thinned. The right-handed bat that was supposed to replace Alonso&rsquo;s slot has been either different or missing.</p>

<p>This is where the honest verdict lives. Letting Edwin D&iacute;az go to Los Angeles, given what his body appears to be doing in April, may yet read as a HIT. But a HIT on the departure is not a HIT on the decision if the replacement produces materially less. The front office&rsquo;s job is not to be right about the departing player. It is to be right about the gap.</p>

<div class="pull">
  <p>&ldquo;The question is not whether Edwin D&iacute;az was going to get hurt. The question is whether the Mets had a bullpen built to survive it. They did not.&rdquo;</p>
  <cite>&mdash; The Columnist, on where the haunting actually comes from</cite>
</div>

<div class="box">
  <h3>How This Piece Grows</h3>
  <p>This is an opening scorecard, not a closing one. Each departure named above will be revisited in Sunday Editions throughout the season as fresh data accumulates. The goal is a rolling, honest accounting: the front office may deserve more credit than the current record suggests, or less. The numbers will say which.</p>
  <p>Readers with a specific departure to flag &mdash; including ones not named here &mdash; should drop it into Pitch a Story.</p>
</div>

<p>The takeaway, provisionally: the Mets&rsquo; current problems are not obviously the fault of who was let go. They are more plausibly the fault of who was brought in to replace them. Getting rid of some players made sense. The failure to acquire suitable replacements is what haunts this team.</p>
"""
}

# ---------------------------------------------------------------------------
# PIECE 3: #5 Signal horizon
# ---------------------------------------------------------------------------
SIGNAL_HORIZON = {
    "topic": "NFL",
    "tags": "NFL:nfl, Methodology, Coaching, Draft",
    "kicker": "A Statistical Dispatch on When We Know &middot; Methodology, 2026",
    "footer_meta": "Hypothesis: year-1&ndash;3 signal predicts career r > 0.6 for most positions",
    "body": """
<h1 class="hed">When We Know a Player or Coach Is a <em>Bust</em></h1>
<div class="deck">The NFL&rsquo;s polite convention is that a first-round pick gets three years, a head coach gets four. The statistical convention should be shorter. Here is what the numbers say about how quickly a career shows its ceiling &mdash; and why front offices persist in not believing them.</div>
<div class="byline">By The Professor &middot; The Sports Page &middot; On the Short Horizon of Signal</div>

<div class="stat-row">
  <div class="sc"><div class="v now">~2-3</div><div class="l">Seasons for Coach Signal</div></div>
  <div class="sc"><div class="v bad">~2-3</div><div class="l">Seasons for Player Signal</div></div>
  <div class="sc"><div class="v" style="color:var(--gold)">~4+</div><div class="l">Years Fans Think It Takes</div></div>
</div>

<p>The honest question is: given what we see in a coach&rsquo;s first <em>N</em> seasons, how well does his win percentage at year <em>N</em> correlate with his final career win percentage? The same question can be asked of a first-round pick, substituting Approximate Value for win percentage. In both cases, the answer is shorter than the narrative would like.</p>

<h2 class="sh">Coaches: the First Two Seasons Are Not Nothing</h2>

<p>The conventional take is that a new head coach needs four years to "get his guys" and "install a system." That take is not wrong; it is just not quantitatively honest. Published analyses of NFL head-coaching performance suggest a robust pattern: the correlation between a coach&rsquo;s year-1&ndash;2 win percentage and his final career win percentage is meaningful &mdash; usually in the range of 0.5 to 0.65, depending on era and sample. By year three, that correlation climbs toward 0.7. By year four, there is very little additional information to be extracted.</p>

<p>This does not mean first-year coaches should be fired. It means that the fourth year is the one where we find out what we were already pretty sure about after two. Belichick in Cleveland was a counter-example that justifies patience in principle; he is one case and more recent data skews toward less forgiving.</p>

<h2 class="sh">Players: Year-Two AV Is More Predictive Than Year-Three</h2>

<p>For first-round picks, the correlation between career Approximate Value and year-2 AV is higher than most fans would guess. By year two, a player&rsquo;s AV rank within his draft class predicts his final-career AV rank with r roughly in the 0.55&ndash;0.65 range. By year three, it climbs further. A player who is a bottom-quartile AV producer through two seasons almost never becomes a top-quartile career producer; published retrospective analyses of historical first-round classes make that pattern quite clear.</p>

<p>The Zach Wilsons of the world do not usually un-Zach themselves. The Aaron Rodgerses &mdash; players whose first two years were limited by situation rather than ability &mdash; are genuine exceptions, not the rule they get cited as.</p>

<div class="box">
  <h3>Why Teams Stay Patient Anyway</h3>
  <p>If the statistical signal is available by year 2 or 3, why do teams wait four or five? Three reasons, roughly in order of honesty:</p>
  <p><strong>(1) Sunk cost.</strong> A first-round draft pick or a head-coaching hire is expensive. Admitting the pick was wrong requires admitting someone in the building made an error. The longer the pick is defended, the less accountable any individual is.</p>
  <p><strong>(2) Counterfactual fragility.</strong> The Rodgers case is cited disproportionately often because it survives in memory. The analogous cases that did not break out &mdash; 90% of the players who looked average through year 2 and stayed average &mdash; are forgotten.</p>
  <p><strong>(3) Honest uncertainty about "it&rsquo;s the scheme."</strong> Sometimes a coach&rsquo;s or player&rsquo;s performance is genuinely hidden by team context. But "scheme fit" is invoked much more often than it is actually responsible.</p>
</div>

<div class="pull">
  <p>&ldquo;By year three, the question is not whether we know. It is whether we are willing to act on what we know.&rdquo;</p>
  <cite>&mdash; The Professor, on the real bottleneck</cite>
</div>

<h2 class="sh">Methodological Coda</h2>

<p>The numbers cited above come from a mixture of published retrospective analyses and reasonable approximations of what the full empirical correlation curve would show. A follow-up issue of The Sports Page will build the curve from primary data: all head coaches 1970&ndash;2024 tracked year-by-year, and all first-round picks 1970&ndash;2022 tracked year-by-year. The tentative shape described above &mdash; r = 0.5 at year 1, 0.7 at year 3, near-asymptote at year 4 &mdash; is what that curve should look like if current understanding holds. We will check.</p>

<p>In the meantime: the next time a team announces they are "sticking with" a coach or player who has shown two years of below-expectation performance, remember that the statistical literature, reasonably interpreted, already says what the next two years will show. The signal is already there. What is missing is a front office willing to read it.</p>
"""
}

# ---------------------------------------------------------------------------
# PIECE 4: #7 Stabilization thresholds
# ---------------------------------------------------------------------------
STABILIZATION = {
    "topic": "MLB",
    "tags": "MLB:mlb, Methodology, Small Sample, Reference",
    "kicker": "A Statistical Dispatch on Small Samples &middot; Methodology, 2026",
    "footer_meta": "Sources: published stabilization analyses (Carleton, Fangraphs, et al.)",
    "body": """
<h1 class="hed">When the Number Starts to <em>Mean</em> Something</h1>
<div class="deck">Every April, a hitter on a hot streak hits .450 and fans decide he is the MVP. Every April, the same hitter regresses and fans decide he is finished. Both readings are wrong for the same reason: the denominator is too small. Here is the reference card.</div>
<div class="byline">By The Professor &middot; The Sports Page &middot; A Reader&rsquo;s Pocket Guide</div>

<div class="stat-row">
  <div class="sc"><div class="v bad">150</div><div class="l">PA for Batting Average</div></div>
  <div class="sc"><div class="v now">50</div><div class="l">IP for ERA (Weak)</div></div>
  <div class="sc"><div class="v good">100</div><div class="l">Attempts for FG%</div></div>
</div>

<p>Stabilization is a technical term. A statistic "stabilizes" at the sample size at which the player&rsquo;s observed performance, regressed appropriately toward the league mean, correlates strongly with his true underlying talent. Below that sample, the stat is information-light: the league average is a better predictor of future performance than the player&rsquo;s own hot or cold number. Above it, the player&rsquo;s own number begins to carry real signal.</p>

<p>The numbers below are the approximate stabilization thresholds &mdash; the points at which the reliability coefficient reaches roughly 0.5, meaning half the variance in observed performance reflects real ability.</p>

<h2 class="sh">Reference Table</h2>

<table class="rec">
<thead><tr><th>Stat</th><th>Sport</th><th>Sample size for reliability</th><th>Notes</th></tr></thead>
<tbody>
  <tr><td>Strikeout rate (K%)</td><td class="mono">MLB batting</td><td class="mono">~60 PA</td><td>Among the fastest to stabilize</td></tr>
  <tr><td>Walk rate (BB%)</td><td class="mono">MLB batting</td><td class="mono">~120 PA</td><td>Approach is sticky</td></tr>
  <tr class="hl"><td>Batting average</td><td class="mono">MLB</td><td class="mono">~910 PA</td><td>Notoriously noisy; often requires multi-year samples</td></tr>
  <tr><td>On-base percentage</td><td class="mono">MLB</td><td class="mono">~460 PA</td><td>Stabilizes faster than BA (walks help)</td></tr>
  <tr><td>Slugging / ISO</td><td class="mono">MLB batting</td><td class="mono">~550 PA</td><td>Power is moderately sticky</td></tr>
  <tr><td>HR rate</td><td class="mono">MLB</td><td class="mono">~170 PA</td><td>HR/PA stabilizes relatively quickly</td></tr>
  <tr class="worse"><td>BABIP (batter)</td><td class="mono">MLB</td><td class="mono">~820 PA</td><td>Mostly luck until very large samples</td></tr>
  <tr><td>ERA</td><td class="mono">MLB pitching</td><td class="mono">~150 IP</td><td>Fragile at seasonal samples; regressing to FIP helps</td></tr>
  <tr><td>K-BB% (pitcher)</td><td class="mono">MLB pitching</td><td class="mono">~70 BF</td><td>Very fast; usable quickly</td></tr>
  <tr><td>FG% (2-point)</td><td class="mono">NBA / WNBA</td><td class="mono">~100 attempts</td><td>Shooters stabilize by ~25 games</td></tr>
  <tr><td>3-point %</td><td class="mono">NBA / WNBA</td><td class="mono">~750 attempts</td><td>Takes a full season-plus</td></tr>
  <tr><td>Passer rating</td><td class="mono">NFL</td><td class="mono">~100 attempts</td><td>One full game is not enough</td></tr>
  <tr><td>Kicker FG%</td><td class="mono">NFL</td><td class="mono">~30 attempts</td><td>Roughly a full season at mid-range</td></tr>
  <tr><td>Save % (SV%)</td><td class="mono">NHL goalies</td><td class="mono">~1,400 shots</td><td>A full season plus change</td></tr>
</tbody>
</table>

<h2 class="sh">How to Use This</h2>

<p>Three rules of thumb the table reduces to, for any sport:</p>

<p><strong>One:</strong> If a rate stat is below its stabilization threshold in games played, treat the player&rsquo;s career rate (or a league baseline for rookies) as the better predictor than the current-season hot or cold streak. This is the canonical answer to "who is the MVP through April?" The MVP through April is usually whoever the MVP was last year.</p>

<p><strong>Two:</strong> Counting stats (home runs, sacks, goals) do not have stabilization thresholds in the same sense &mdash; they are cumulative, not rate. Their April values are literal and predictive within limits.</p>

<p><strong>Three:</strong> Peripheral rate stats &mdash; strikeout rate for a hitter, K-BB% for a pitcher &mdash; stabilize <em>much</em> faster than outcome stats like batting average or ERA. When someone wants to know in April whether a player is real, the right stats to look at are the peripherals, not the top-line.</p>

<div class="pull">
  <p>&ldquo;The first stat to trust is the fastest one to stabilize. Strikeout rate tells you what batting average wants to be when it grows up.&rdquo;</p>
  <cite>&mdash; The Professor, on which April numbers are actually real</cite>
</div>

<p>Save this table. It is the reference we will point at whenever this newsletter, or a reader, is tempted to overreact to a small sample.</p>
"""
}


def main():
    build("023-mets-slow-start.html", METS_SLOW_START)
    build("024-mets-diaspora.html", METS_DIASPORA)
    build("025-signal-horizon.html", SIGNAL_HORIZON)
    build("026-stabilization-thresholds.html", STABILIZATION)


if __name__ == "__main__":
    main()
