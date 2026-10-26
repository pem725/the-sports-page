# The water-cooler numbers — which stats does the press lean on?

Started 2026-10-25 on the editor's brief:

> "What are the numbers that people use to argue their points? ... go through every single sports
> page or article and find out what number it is that they're leaning on. My suspicion is there's
> like a fad during a period of time in sports writing. Everybody gets hot and bothered about home
> runs, Sammy Sosa and Mark McGwire ... but there were guys hitting triples and doubles ... and look
> no further than Barry Bonds simmering in the background."

## Two halves

**1. Now, going forward: the ledger.** `scripts/water_cooler.py` (runs every morning from the
workstation via `scripts/aibox_desk.py`) reads new items from ESPN, CBS, Yahoo and MLB Trade Rumors,
and the AI box records every number each article uses: what it counts (a canonical stat family),
who it is about, whether it is used to *argue* or just to *describe*, and the one number the piece
leans on hardest. Ledger: `data/watercooler/claims.jsonl`. Article text is never stored.

**2. Then, going back: the fad curve.** A daily ledger only starts today. The fad question needs
decades of sports pages. Plan, in order of quality:

| Source | Covers | Cost | Status |
|---|---|---|---|
| NYT Article Search API (sports desk; headline, abstract, lead paragraph) | 1851–now | free key, 10 calls/min, 4,000/day | **needs a key from the editor** (developer.nytimes.com → `NYT_API_KEY` via `set_secret.py`) |
| Chronicling America (Library of Congress OCR newspapers) | to 1963 | free, no key | possible for the Ruth era |
| Google Books Ngram | to 2022 | free, no key | first look done; books are a weak proxy (see below) |

**First look from Ngram (books, not sports pages — treat as a hint only):** mentions of on-base
percentage per mention of batting average went from about 1 in 95 (1980) to 1 in 7 (2005), the
Moneyball turn. RBI per mention of home runs fell by more than half over the same years. Raw counts
are useless: every phrase "peaks" in 2014, which is a change in the books corpus, not in baseball.
Ratios between stats survive that; absolute counts do not.

## The questions this can answer (each one is an issue)

1. **The 1998 question.** In the summer of McGwire and Sosa, what share of baseball's numbers were
   home runs? Who was producing value in stats nobody printed (doubles, walks, on-base) — Bonds?
2. **The Moneyball turn.** When did on-base percentage enter the sports page, and did it arrive
   before or after the book?
3. **The Statcast fad.** Exit velocity and launch angle, from zero to everywhere: is it explaining
   anything, or decorating?
4. **Argument vs description.** Which stats are used as *evidence* for opinions? Our bet: the
   composites (RBI, QB wins, pitcher wins) carry the most arguments per unit of meaning.
5. **What the box score hides.** Stats that matter (by their year-to-year reliability and their
   link to winning) but almost never appear in print. That gap is the Box Score Anatomy slate.
6. **The cherry-picked broadcast stat** (Patrick jr's held reader question): the ledger is the
   sample it was waiting for.

## How it feeds the paper

- **Box Score Anatomy order.** Dissect the stats the press leans on hardest first. The ledger ranks them.
- **Weekly line for the Sunday Edition or the board:** "This week the press leaned on ___ most."
- **Every number from the ledger that reaches print is re-checked against a primary feed.** The
  ledger records what an article *said*, not what is true.

## First audit — 2026-10-25 (250 articles, 4,307 numbers, mostly Oct 20–26)

- **Are the numbers real?** 15 articles re-fetched at random: 273 of 284 recorded numbers appear
  verbatim. The 11 misses were rewordings (*seventh* stored as *7th*), not inventions.
- **Are the labels right?** 40 claims read by hand: about **7 of 40 wrong** (roughly one in six).
  The pattern matters more than the rate: **every betting number gets filed as "point spread"**
  (a Kalshi share price, a +105 touchdown prop), and non-performance counts slip in (a year, "10,000
  simulations"). Add `moneyline`, `prop odds`, `prediction-market price` families before any tally.
- **Count articles, not numbers.** One NFL betting table supplied 147 of 229 "point spread" arguments.
  `--report` now counts each family once per article.
- **The first hint, per article:** the number the press *argues* with most is the betting line —
  24 of 70 NFL articles, 11 of 47 CFB. Baseball argues with playoff odds and contract money; home
  runs appear in 5 of 97. Week of the World Series and Week 7, so it is a snapshot, not a trend.
  **Not publishable as a percentage until the families are fixed and a second audit comes in under
  one wrong in ten.**

## Limits, stated now so nobody forgets

- Feeds are a convenience sample: four outlets, whatever they syndicate. Not "the press."
- The extractor is a 20B local model. Spot-check its labels (first run filed a 76-year drought
  under "attendance"; a `drought` family was added the same day). Report its error rate before
  publishing any tally.
- Paywalled or video-only items are skipped (under 120 words of text), which tilts the sample
  toward free writing.
