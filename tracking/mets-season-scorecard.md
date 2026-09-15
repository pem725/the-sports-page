# The Mets season scorecard — held until the regular season ends

**Status:** brief only, not drafted. **Do not write it before 2026-09-30.**

The Mets were mathematically eliminated on 2026-09-15 at 69–81 with twelve games
left. The obvious piece is a full-season accountability table: every Mets forecast
this paper published, graded. The editor's instruction on 15 September was to
**hold it until the season ends**, and the reason is the piece's own subject —
grading a season with twelve games unplayed repeats exactly the impatience the
piece is about.

## The trigger

Write it when the regular season is complete (final game 2026-09-30 or the
following days if rescheduled). Two preconditions, both hard:

1. **Final record confirmed** from the MLB Stats API, not a projection.
2. **Payroll verified from a named source.** Working figure is ~$375M and it is
   NOT sourced — it comes from session notes. Cost-per-win is the line everyone
   will quote, so it needs two independent confirmations per the headline rule.
   Sites returned 403 during earlier attempts; see [[project_payroll_wins]] notes
   in the #103/#104 work for what worked.

## The receipts, already assembled

Pulled 2026-09-15. Re-verify the final column against the primary feed before
publishing; everything else is quoted from our own published archive.

| issue | date / state | what we said | where it landed |
|---|---|---|---|
| `004-mets-500` | Apr, 3–3 | Beta-Binomial on a **preseason prior of ~90 wins** | off by ~16 |
| `sunday-004` | Apr, 7–14 | **80–82 wins**, 90% credible interval **[70, 89]** | point off ~7; **interval held** |
| `048-pythagorean-mets` | May, 20–26 | 76-win pace, then *"plausibly climbs from 76 wins back into the low-to-mid 80s"* | worst call of the year |
| `sunday-008` | Jun, 25–33 | *"on pace for approximately 72 wins"* | **closest of the season** |
| `137-schedule-leverage` (#158) | Sep 2 | *"The Mets Must Pass Seven Teams"* | passed **zero**, fell further |

**State at elimination:** 69–81 (.460), 13th of 15 in the NL, runs 644–679 for a
differential of **−35**, Pythagorean about 71–79 — meaning they underperformed
even that by 2.4 wins. 18.5 back in the division, 13 in the wild card.

## The finding, which is what makes it a piece

Read that table top to bottom: **our most pessimistic number was our most
accurate, and every upward revision was wrong.**

The mechanism is a prior that would not die. We anchored on ~90 wins in March and
every update afterwards dragged the posterior back toward it, so each bad month
read as noise worth regressing away. `048` is the clean case — it computed a
76-win pace from actual runs and then talked itself up into the low-to-mid 80s on
mechanisms it expected to arrive. The unadorned number was right; the reasoning
laid on top of it was the error.

And note what *did* work: the **interval**. [70, 89] contained the answer when the
point estimate inside it did not. That is the argument for publishing error bars
instead of numbers, made at our own expense, which is the best kind of argument
this paper gets to make.

Working headline, subject to `check_headline.py`:
**"We Said Ninety Wins. They Won Seventy-Four. Our Gloomiest Number Was Our Best One."**
Three beats, but the third is short and lands the twist, so it should clear the
rule-8 punchline exemption. Confirm rather than assume.

## Related

[[tracking/mets-buy-or-sell-watch.md]] for the deadline-window tracking, and the
Sunday Edition scorecard convention for the grading vocabulary (HIT / MISS /
PARTIALLY HIT / PENDING).
