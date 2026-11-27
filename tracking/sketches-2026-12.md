# Sketches: the next two weeks (written 2026-11-27)

Five pieces in the order they need work. Each says the question, the number it rests on,
the data, the trap, and when. No betting tenor in any of them: spreads are the crowd's prior.

---

## 1. Scorecard No. 3 + the Brier line (Sunday 034, Sat night 11/28; Judges' No. 3 Wed 12/2)

**Built:** `scripts/brier_scorecard.py`. Season so far, 476 college games across the 8 weeks
we froze (2, 3, 7-12, plus Thanksgiving week's early games):

| forecaster | Brier (lower is better) | share of a coin flip's error removed |
|---|---|---|
| always 50 in 100 | .25 | 0 |
| ours (frozen SP+) | .19 | about 23 in 100 |
| the crowd (frozen point spread) | .18 | about 28 in 100 |

The gap is small and real: ours minus crowd is +.003 to +.017 (95%, games resampled).
**The crowd beat us.** That is the Good Judgment Project's finding, reproduced in our own
ledger: an aggregate of many people reacting to news (injuries, weather, who is playing)
outscores a rating that sees only past games. Say it plainly; it is rule 3 of the headline
rules (admit error when you have earned it).

**Saturday night:** `python3 scripts/brier_scorecard.py --refresh --week 13` after the last
game, paste the week line and the season line into Sunday 034's scorecard. Weeks 1, 4, 5, 6
had no frozen snapshot: print "not scorable", never back-fill.
**Wednesday 12/2:** Judges' Scorecard No. 3 per its runbook (research/cfp-committee/judges/
SCORECARD-3-RUNBOOK.md); its Brier line now has the crowd beside the coin. Queue as
221-judges-scorecard-3.html ahead of 216 in QUEUE_ORDER Tuesday night after the ranking.

---

## 2. The week after rivalry weekend: running order

| date | piece | topic |
|---|---|---|
| Sat 11/28 | 211 time of possession | NFL |
| Sun 11/29 | **Sunday Edition 034** (built with the editor Sat night) | Sunday |
| Mon 11/30 | 214 yard gap | CFB |
| Tue 12/1 | 215 Henderson | NFL |
| **Wed 12/2** | **221 Judges' Scorecard No. 3** (insert Tue night, after the ranking) | CFB |
| Thu 12/3 | 216 what repeats: hitters (pushed one day) | MLB |
| Fri 12/4 | 217 what repeats: quarterbacks | NFL |
| Sat 12/5 | 218 what repeats: pitchers (conference title day) | MLB |
| Sun 12/6 | Sunday Edition 035 (Selection Day: confirm the date and release time on the CFP calendar first) | Sunday |
| Mon 12/7 | **open: Selection Day piece** (committee's final 12 vs our math) | CFB |
| Wed 12/9 | **the coach piece** (sketch 3) | CFB |

Wed-is-CFB means Tue and Thu must not be: holds above. Run `queue_health.py` after each insert.
The Selection Day piece is the series' last scorecard: it publishes Monday because the
committee's final word is Sunday, not Tuesday.

---

## 3. "Keep the Coach or Fire Him? Count Every Risk." (target Wed 12/9; carousel is now)

**Question:** after a bad year, does firing the coach make next year better, and is the
answer the same at one year and five?

**Data:** `data/cfb-coaches.csv`, 6,717 coach-seasons, 1970-2025, with wins, losses, SP+
and SRS for every season. A change = a school's coach in year t+1 differs from year t
(mid-season changes: assign the season to whoever coached most games; say so).

**Design (real cases only, no hypotheticals):**
- Trigger: a season in a program's bottom band against its own last 5 years (say 3+ wins
  under its trailing average), coach in year 2+. Programs that changed vs kept.
- Match on what the AD saw: the bad year's SP+, the trailing 5-year SP+, tenure, conference
  tier. Otherwise "changed" is just "worse to begin with".
- Outcomes, three horizons, each as **relative risk** with a 95% interval, plus one odds
  ratio so the two can be contrasted on the page:
  1. next season worse than the bad one (risk of sinking further)
  2. 5-year win % below the pre-slump 5-year win % (risk of a lost era)
  3. bowl-eligible within 2 years (the postseason-money proxy; no dollar figures)
- The figure: three paired bars (kept vs changed) with error bars, one per horizon.

**The lesson it carries:** RR vs OR (they agree when outcomes are rare and part ways when
they are common; show both on the same data), and that a decision has several outcomes at
once, so the answer is a trade-off table, not a verdict.

**Traps, write them in the methods box:**
- **Regression to the mean hits both arms.** A bad year is partly bad luck; both groups
  bounce. The question is only the *difference* in bounce.
- **Selection:** kept coaches are the ones the AD believed in, often for reasons the data
  lacks (recruiting, injuries). Matching shrinks this, never removes it.
- Two-digit numbers only. Builds on #029 (coaching stabilization); link it.

**Steps:** build the panel (1 day, local data, no CFBD calls), match + bootstrap (1 day),
draft, the checks, cold_read. Draft by Fri 12/4 so the board sees it.

---

## 4. "It Rained. The Forecast Was Still Right." (concept primer: y-hat is not y)

**Question:** if a 99-in-100 team loses, was the number wrong?
**Number:** 2006-2025, teams that reached a 99-in-100 chance: about 21 expected to lose,
19 did (`research/thanksgiving/calibration.py`). Add our own college calibration from the
Brier data: bin our frozen chances in tenths and plot predicted vs observed (the 476
games already scored give ~50 per bin).
**Shape:** the rain forecast first, Dallas second, our own calibration curve third: the
paper admitting how its own forecasts land, misses advertised.
**When:** any time after Sunday 034, which introduces the idea; a primer keeps.
Check `concepts/registry.json` (communicating-uncertainty exists; this is calibration).

---

## 5. The three primers: one ladder

They teach better as a sequence than as three separate pieces. Order:

1. **"18 in 100 Is a Count, a Chance, and a Guess."** Binomial for the count, beta for the
   rate; the interval shrinks as the count grows. Real case: a hitter's 18 hits in 100,
   then 180 in 1,000. Then Poisson (stolen bases) and the zero-heavy interception counts,
   negative binomial, plotted against Poisson so the misfit is visible.
2. **"Three Stats Said the Same Thing. Which One Gets the Credit?"** Multicollinearity
   on the constructs data we already hold (research/constructs/), with a scatter of the
   correlated predictors. Always plot.
3. **"The Chart Was True. The Picture Lied."** One real press graphic from the
   water-cooler ledger, redrawn honestly beside the original: pictogram area vs height,
   chopped axis. Darrell Huff, *How to Lie with Statistics* (1954). Real graphic only.

Each closes with the standing habits: plot it; ask for the figure behind a correlation;
ask for the numerator and denominator behind a ratio. Pace them one per week from mid-
December, when the queue needs `keeps` pieces again.
