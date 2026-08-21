# The Bometer and The Stack

Two metrics, built 2026-08-21, calibrated using the logic in **Sechrest, L.,
McKnight, P., & McKnight, K. (1996). Calibration of measures for psychotherapy
outcome studies. *American Psychologist*, 51(10), 1065–1071**
([PMID 8870543](https://pubmed.ncbi.nlm.nih.gov/8870543/)), with the three
quantitative procedures from *Calibration of psychological measures: An
illustration of three quantitative methods* (McKnight).

The rule that governs both: **a measure needs inherent meaning.** Calibrate it
against behaviours and real events, establish just-noticeable differences, and
report the **unstandardized** equation so a reader can convert the number into
something they already understand. A correlation is not a calibration — the
correlation between a mile and a kilometre is exactly 1.0, and it tells you
nothing about how to convert one into the other.

---

## Part 1 — The Bometer, and the finding that killed it

**The question.** How boring is a week in baseball? Snooze-fest to nail-biter.

**The metric.** Share of a week's games *still in doubt at the end* — final margin
of one run, or extra innings, or a walk-off. No invented weights; it is a
percentage of games, which is already a behaviour a fan can check.

**The data.** All 14,060 completed regular-season MLB games, 2021–2026, from the
MLB Stats API. Validity check before any analysis, against known league rates:

| | measured | known MLB range |
|---|---|---|
| Walk-offs | 7.9% | ~8–9% |
| Extra-inning games | 8.8% | ~8–9% |
| One-run games | 28.2% | ~28–30% |
| Median margin | 3 runs | 3 |

All four land where they should, so the extraction is sound.

### The result: there is no such thing as a boring week

Pooled rate across six seasons: **31.4%** of games end in doubt.

| Level of aggregation | groups | χ²/df | z | verdict |
|---|---|---|---|---|
| Calendar week | 143 | 0.88 | −0.98 | no signal |
| Season | 6 | 0.73 | −0.43 | no signal |
| Month | 7 | 0.67 | −0.57 | no signal |
| Day of week | 7 | 0.81 | −0.33 | no signal |
| ISO week-of-year | 25 | 0.72 | −0.98 | no signal |
| **Team-week** | 4,280 | 0.98 | −0.94 | **no signal** |

Every χ²/df is at or below 1.0. Variance decomposition on the weekly series:

- observed variance **20.15**
- variance expected from sampling alone **23.05**
- between-week variance **−2.91** → effectively **zero**
- **share of the week-to-week spread that is real: 0%**

**The entire observed range of the bometer, 17.8 to 45.3, is coin-flipping.**
Baseball delivers the same ~31% every week, every month, every season, on every
day of the week. A "boring week" is not a property of the schedule.

### The JND kills the weekly version outright

Method of just noticeable differences: the smallest difference two observers
would reliably agree on. Thurstone's criterion is 75% agreement — halfway between
chance and certainty.

We have no panel of judges, so the honest operationalisation is the noise floor:
a difference is not noticeable if it is smaller than what sampling produces by
itself. With ~95 games in a league week the sampling SD is **4.8 points**, so a
JND is on the order of **±10 points** — and the real between-week differences are
**0**.

> **The JND is larger than the entire range of the thing being measured.**
> Reporting a weekly bometer score is reporting noise with a decimal point on it.

That is the calibration result, and it is the finding. The metric is not broken;
the phenomenon is absent.

### Where the boring week actually lives: in you

A fan does not watch 95 games a week. They watch one team's six. At n = 6 the
sampling SD is **18.7 points**, and here is what that produces:

| Games in doubt, out of 6 | Share of team-weeks |
|---|---|
| **0 — a genuine dud week** | **10.2%** |
| 1 | 29.7% |
| 2 | 33.4% |
| 3 | 19.0% |
| 4 | 6.2% |
| 5 | 1.4% |
| 6 | 0.0% |

**One fan-week in ten contains nothing worth staying up for.** That experience is
completely real. It is also entirely luck — the team-week χ²/df is 0.98, so
teams do not have boring weeks either.

The calibrated statement, in the form the 1996 paper asks for — behavioural, and
in the reader's own experience:

> The league is a constant. Your week is a coin flip. If this week felt dull, it
> was dull *for you*, and nothing about the schedule caused it.

---

## Part 2 — The Stack: newsworthiness measured in paper

The bometer measures whether a game was close. It says nothing about whether
anyone *cared*. That is a different quantity and it needs a different unit.

**The unit: printed pages.** One page means almost nobody read it. A stack means
the world stopped. This is calibration by **cross-modal equivalent** — the third
approach named in the 1996 abstract — expressing an abstract quantity in a
physical object a person can picture.

### The scale

**One page = one thousand people who would plausibly read the story.**

Physical constants, and their honest provenance:

| | value | source quality |
|---|---|---|
| Sheets per ream | 500 | exact, by definition |
| Ream thickness | ~2 inches (20 lb stock) | standard, approximate |
| **Sheets per tree** | **8,333** | widely used practical average, **not** a forestry measurement — flag it whenever it is printed |

Which gives a ladder anyone can see:

| Pages | Physical object | Readers | Sports equivalent |
|---|---|---|---|
| 1 | a single sheet | 1,000 | a September game between two eliminated clubs |
| 500 | **one ream**, 2 inches | 500,000 | a pennant-race game that matters to two cities |
| 8,333 | **one tree** | 8.3 million | a World Series game |
| ~115,000 | **~14 trees**, a 38-foot stack | ~115 million | a Super Bowl |

### The finding hiding in the unit

Run the scale to its end and the punchline arrives on its own. The largest event
in American sport is **about fourteen trees.** A copse. You could walk past it.

"A planet's worth of trees" is not the top of the sports scale — nothing in sport
reaches it, and the metric is more useful for saying so. A unit that cannot
express how small the biggest thing is was not calibrated properly.

### Status: method built, anchors NOT yet verified

The readership figures above are illustrative. **Every one must be verified
against three independent sources before it appears in an issue**, per the
standing rule. The metric is ready; its anchors are not.

---

## Part 3 — Boring vs newsworthy: the funniest null in the file

**The question.** Are dull teams more newsworthy in aggregate, or are they dull
*and* ignored?

**Neither.** The two have nothing to do with each other.

Attention needs a proxy, and it has to be a **behaviour** — the 1996 paper is
insistent on that. Two independent ones, both free and verifiable:

| Proxy | What it measures | Source |
|---|---|---|
| English Wikipedia pageviews, 2021–2026 | somebody went and looked the club up | Wikimedia REST API |
| Mean home attendance, 2021–2026 | somebody bought a ticket | MLB Stats API |

| Relationship | r | 95% CI | verdict |
|---|---|---|---|
| bometer vs Wikipedia pageviews | **−0.10** | −0.44 to +0.27 | nothing |
| bometer vs home attendance | **−0.18** | −0.51 to +0.19 | nothing |
| **the two proxies vs each other** | **+0.50** | **+0.17 to +0.73** | **real** |

That third row is what makes the first two believable. The proxies agree with
each other, so they are measuring a common thing. They simply have no
relationship to whether a club's games are close.

The magnitudes are the joke:

- **Attention varies 4.3-fold** across clubs — 1.8M pageviews for the Rockies,
  7.8M for the Yankees.
- **Excitement varies by 8 points** on a 100-point scale, 28.1% (Royals) to
  36.2% (Mariners), SD **1.78**.

So one quantity swings by a factor of four, the other barely moves, and the line
between them is flat. **Newsworthiness in baseball is market and history. It is
not the games.** The Yankees at 30.9% and the Rockies at 31.2% play nearly
identically watchable baseball; one is looked up four times as often.

Figure: `assets/fig/bometer-vs-attention.svg`.

### On "is there a hype-o-meter online?"

There is no single canonical one. What exists and is free, stable and citable:

- **Wikipedia pageviews API** — clean, per-article, per-day, no key. The best
  single attention proxy available.
- **GDELT DOC 2.0** — worldwide news-article volume for any query, and it returns
  the article URLs, so "links to the story" is directly measurable. Good for
  event-level spikes rather than season-level team attention.
- Google Trends has no supported public API and its numbers are already
  normalised, which destroys the metric — exactly the problem the 1996 paper
  warns about. Avoid it as a calibration anchor.

For **The Stack**, GDELT article counts are the natural input: pages ≈ stories
written. That is the next thing to build, and its anchors still need verifying.

---

## What to do with these

0. **The boring-vs-newsworthy null is the best issue in here** — a real question,
   two verified proxies that agree with each other, and a flat line.
1. **The bometer finding is publishable now.** It rests entirely on 14,060 games
   we extracted and validated ourselves, and it is exactly the newsletter's
   civic-mission shape: a thing everybody believes, tested, and absent.
2. **The Stack needs its anchors verified** before it can carry an issue.
3. **Do not report a weekly bometer score.** The JND exceeds the range. If a
   Sunday Edition wants to say the week was quiet, the honest sentence is that it
   felt quiet, and that the schedule was the same as always.

*Rebuild: `scripts/bometer.py`. Cache and fetch in the session scratchpad; the
MLB Stats API is the only source.*
