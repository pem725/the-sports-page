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
| 2026-08-11 | Patrick sr | "Cleveland is where players go to die... the stats are going to prove me right about this." Do some franchises actually ruin players? | queued | candidate `where-players-go-to-die` — needs a within-player design; naive version is pure selection bias |
| 2026-08-30 | Patrick jr | Rank the coaching: how does a coach fare against an AP top-10 team vs a top-25 team? "Choke artist" made measurable. | queued | candidate `coach-vs-ranked`, NEWSINESS 5.40 |
| 2026-08-30 | Patrick jr | You can never fire a coach after one season — a first year is a jumping-off point, not a verdict. True? | queued | candidate `first-year-baseline`, NEWSINESS 5.68 |
| 2026-08-30 | Patrick jr | Broadcasters cherry-pick stats for drama, not prediction. Can that be shown rather than asserted? | held | candidate `cherry-picked-stat` — needs a logged sample of real broadcast graphics first |
| 2026-08-30 | Patrick jr | Offensive linemen are not produced in the South. Is that actually true? | published | Issue #147 `147-talent-addresses` — half right; South makes OL 2.4x faster than anywhere, but only 0.63 per DL |
| 2026-08-30 | Patrick jr | Where do the freakish ones come from — is there a stock, a subpopulation, a gene? (the sports-gene question) | published | Issue #147 — answer is institutional, not ancestral: Gini 0.838 across 8,018 high schools; Nevada more concentrated than Hawaii |
| 2026-08-24 | Gene (Bears) | If a team wins 75% over a season, why is the probability different on one last play? Also: Bayesian vs frequentist, and why do quoted probabilities keep changing? | published | Concept No. 27 `nomothetic-vs-idiographic` + Issue #140 `140-one-kick` |
| 2026-06-15 | Sean | (audience research, not a question — kept for reference) | — | hover-primer mechanism, tiered concept pages |
| 2026-08-?? | Tim | velocity caveat on the Skenes piece | published | amended #125, answered in #126 |
| 2026-09-27 | Sean | Wisconsin beat No. 13 Penn State as a ~24% underdog. How unlikely was that, really? | queued Fri 9 Oct | full draft submitted. **Every fact verified against CFBD**: score, AP No. 13, 17-0 deficit, both TD passes at 3:31 and 1:13, three interceptions, and 1981/1984/1985/2007 comparisons with their rankings. The 24% is correctly de-vigged from +300/-380. Needs: headline with pull, grade 8.1 -> 6, and second person |
| 2026-09-27 | Sean | A 104 mph fastball at Triple-A — how often does a pitcher climb A to AAA in a season, and does height explain velocity? | queued | Tue 6 Oct. **His own reporting beat the box score**: a season line reading High-A/AA/AAA looks like three levels climbed, but MLB transactions show 2026-08-11 was a REHAB assignment to Wilmington after a 60-day IL stint, and the only real promotion was 2026-09-15 Harrisburg to Rochester. Susana verified 6'6" 235 age 22 via Stats API |
| 2026-09-27 | Sean | When does an inherited team become the new coach's team? | held | strong concept — attribution, counterfactual, regression to the mean. **HELD ON SOURCING**: rests on three academic citations (Adler/Berry/Doherty SSQ 2013; Humphreys/Paul/Weinbach Research in Economics 2016; Johnson et al. JSB 2023) that no feed we hold can verify. Both drafts came via ChatGPT. Resolve the DOIs against the journals before running — this is the shape of the Sunday 022 failure |

## The three-part test (from `ask.html`)

1. There is a number in it, or there could be.
2. It could not be settled at the table.
3. A reasonable person could be wrong about it.

A question failing all three is usually trivia. A question passing all three is
usually about something larger than the game it came from.
