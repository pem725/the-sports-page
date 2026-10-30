# Reader Questions — intake log

One row per question that arrives. The point of the log is to make the
**vetting step visible**: most questions are already answered somewhere in the
archive, and saying so quickly is a good outcome, not a failure.

Status values: `new` → `checked` (against archive) → `queued` / `answered-by-link`
/ `declined` (with reason) → `published`.

**Never record contact details here.** First name and team allegiance is the most
this file should ever hold; the email itself stays in the inbox.

| date | who | question (compressed) | status | outcome |
|---|---|---|---|---|
| 2026-08-30 | Patrick jr | Can we have an unbiased regular-season strength of schedule that does not cater to the SEC? The rating systems are an interested party. | published | Issue #146 `146-sec-schedule-bias` — SEC wins by 0.4 pts; top league never separable from second in 5 seasons |
| 2026-08-11 | Patrick sr | "Cleveland is where players go to die... the stats are going to prove me right about this." Do some franchises actually ruin players? | published | Issue #185 `149-where-players-die` — "We Were Wrong About Cleveland." (log updated 2026-10-25) |
| 2026-08-30 | Patrick jr | Rank the coaching: how does a coach fare against an AP top-10 team vs a top-25 team? "Choke artist" made measurable. | queued | candidate `coach-vs-ranked`, NEWSINESS 5.40 |
| 2026-08-30 | Patrick jr | You can never fire a coach after one season — a first year is a jumping-off point, not a verdict. True? | answered-by-link | Issue #37 `029-cfb-coaching-stabilization` (year one tells you ~60%) and #200 `170-inherited-roster` (inherited roster costs about one win). Found by `archive_match.py`, checked by hand 2026-10-25 |
| 2026-08-30 | Patrick jr | Broadcasters cherry-pick stats for drama, not prediction. Can that be shown rather than asserted? | held | candidate `cherry-picked-stat` — needs a logged sample of real stat claims first. **That sample is now being built** (water-cooler numbers project, `tracking/water-cooler-numbers.md`, 2026-10-25) |
| 2026-08-30 | Patrick jr | Offensive linemen are not produced in the South. Is that actually true? | published | Issue #147 `147-talent-addresses` — half right; South makes OL 2.4x faster than anywhere, but only 0.63 per DL |
| 2026-08-30 | Patrick jr | Where do the freakish ones come from — is there a stock, a subpopulation, a gene? (the sports-gene question) | published | Issue #147 — answer is institutional, not ancestral: Gini 0.838 across 8,018 high schools; Nevada more concentrated than Hawaii |
| 2026-08-24 | Gene (Bears) | If a team wins 75% over a season, why is the probability different on one last play? Also: Bayesian vs frequentist, and why do quoted probabilities keep changing? | published | Concept No. 27 `nomothetic-vs-idiographic` + Issue #140 `140-one-kick` |
| 2026-06-15 | Sean | (audience research, not a question — kept for reference) | — | hover-primer mechanism, tiered concept pages |
| 2026-08-?? | Tim | velocity caveat on the Skenes piece | published | amended #125, answered in #126 |
| 2026-10-26 | Tim | In 2026, what share of Angel Reese's rebounds came off her own missed shots? (He sent an AI-written PDF with ranges.) | checked | Computed from ESPN play-by-play, which matches the box score (206 OREB / 315 DREB): **58 of 521 (11%) of all rebounds, 58 of 206 (28%) of offensive rebounds**; 20 of the 58 followed her own blocked shot. The PDF's 20-25% of OREB was wrong and its ranges contradicted its own counts. League baseline (`scripts/self_rebounds.py`, 328 of 330 games; ESPN 404s two MIN games): 22% of all WNBA offensive rebounds are the rebounder's own miss; median 18% among 23 players with 60+ OREB; Reese 5th by share (Stewart 40% leads), 1st by count and by share of all rebounds. Her 28% is ordinary for a post player, so the 'mebound padding' story does not hold. Needs a second PBP source before print. |
| 2026-09-27 | Sean | Wisconsin beat No. 13 Penn State as a ~24% underdog. How unlikely was that, really? | published | Issue #198 `171-calibration-wisconsin` — "Twenty-Four Times in a Hundred. This Was One of Them." |
| 2026-09-27 | Sean | A 104 mph fastball at Triple-A — how often does a pitcher climb A to AAA in a season, and does height explain velocity? | published | Issue #194 `169-fastball-denominator` — "He Threw 104. The Box Score Said He Climbed Three Levels. It Did Not." |
| 2026-09-27 | Sean | When does an inherited team become the new coach's team? | published | Issue #193 `173-whose-team` (co-bylined with Sean) and #200 `170-inherited-roster`. The Amato piece (`185-coaches-came-home`, queued 10/26) adds the five-years-before baseline |
| 2026-10-23 | Patrick sr | Do bye weeks help? What is the probability of winning off a bye? | queued | `184-bye-week` Wed 10/28 — about one point; about none after a loss |
| 2026-10-25 | Patrick sr | What is an RBI really a sign of? Stats as proxies for constructs (power, clutch, hustle) — one stat per issue, building toward DAGs and SEM | queued | series `Box Score Anatomy`, plan in `tracking/box-score-anatomy.md`; No. 1 `186-rbi` Thu 10/29; Concept No. 28 |
| 2026-10-30 | Gene (Bears) | How many blockbuster trades pan out, in MLB and the NFL? | checked | not in archive (#123 is the famous lopsided ones, i.e. survivorship, not a base rate); build under way: Retrosheet trades + bWAR, nflverse trades + AV |

## The three-part test (from `ask.html`)

1. There is a number in it, or there could be.
2. It could not be settled at the table.
3. A reasonable person could be wrong about it.

A question failing all three is usually trivia. A question passing all three is
usually about something larger than the game it came from.
