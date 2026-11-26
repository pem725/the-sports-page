# The One-Tool Newsroom: codebook

**The question (editor, 2026-11-26):** of our published issues, how many decisions would change
if every one had been analyzed with a single tool, the t-test and ANOVA, used the way they are
too often used: Fisher's analysis of variance read superficially, his *Design of Experiments*
never opened?

## The one-tool analyst (code as if you were this person, then judge them)

- Knows the two-sample t-test, the paired t-test, one-way and factorial ANOVA. Nothing else.
- Reads p < .05 as "real" and p >= .05 as "no difference / no effect".
- Turns any continuous predictor into groups by a median split or tertiles ("high payroll vs low").
- Treats every row as an independent observation (no repeated measures, no clustering).
- Never asks about design: groups that formed on their own are compared as if randomized.
- Never asks about measurement: assumes every stat means the same thing everywhere and is
  measured without error.
- Has no tool for a probability of a single future event, a forecast, a ranking, a simulation,
  a time-to-event, or a rate built on a small denominator. Faced with one, the analyst either
  finds groups to compare or reports nothing.

## What counts as the issue's "decision"

The conclusion a reader is meant to take away and act on: what to believe, expect or do.
One line, in your words. Example: "Skenes's 67.5 ERA after one start tells you almost nothing;
expect him to be back under 2 within about N starts."

## Fields to code (one JSON object per issue)

| field | values |
|---|---|
| `issue` | the issue number given |
| `decision` | the issue's conclusion, one line |
| `question_type` | `group-difference`, `association`, `forecast-probability`, `small-sample-rate`, `count-model`, `trend`, `ranking`, `causal`, `measurement`, `descriptive-history` |
| `original_tool` | short phrase: what the issue actually used (Bayesian Gamma-Poisson, simulation, logistic regression, correlation, bootstrap interval, base rates, descriptive counts, factor analysis, ...) |
| `anova_analysis` | the exact t-test/ANOVA the one-tool analyst would run (groups, outcome), or "none possible" |
| `verdict` | `SAME`, `SAME-WRONG-REASON`, `CHANGED`, `CANNOT-ASK` (definitions below) |
| `failure_mode` | for any verdict except SAME, the main one from the list below |
| `confidence` | `high`, `medium`, `low` |
| `why` | one sentence |

### Verdicts

- **SAME**: the one-tool analyst would reach the same decision, for essentially the same reason.
- **SAME-WRONG-REASON**: same decision, but reached by an invalid route (e.g. "p = .3, so there
  is no effect" where the issue showed the effect is small with an interval).
- **CHANGED**: the decision would flip, or change materially in direction, size or certainty
  (e.g. "money buys wins" from a significant high-vs-low payroll t-test, where the issue said
  payroll explains about 15% of wins).
- **CANNOT-ASK**: the tool cannot pose the question at all (a forecast, the chance of one
  event, a ranking, how long a recovery takes), so the decision is lost, not changed.
  A reader would get no answer.

### Failure modes (pick the main one)

`dichotomizing` (a median split throws away the information) · `dependence` (repeated measures
or clusters treated as independent) · `error-structure` (counts, proportions, skewed or bounded
outcomes analyzed as normal) · `no-design` (self-formed groups read as causal; confounding) ·
`significance-not-size` (huge n makes a trivial gap "significant") · `null-not-absence` (a
non-significant result read as proof of no effect) · `multiple-comparisons` · `selection`
(range restriction, survivors) · `regression-to-mean` (a drop or rise read as an effect) ·
`measurement` (different rulers, unreliable measures) · `no-forecast` (the tool cannot express
the chance of a future event)

## Rules for coders

- Code from the core text you are given; open the full issue (`published/<file>`) whenever the
  core does not make the decision or method clear. Never guess a number.
- Be fair to the one-tool analyst. If a sensible t-test really would give the same answer,
  code SAME. The point is an honest count, not a hit piece.
- A purely historical or descriptive issue with no inference (a record, a timeline) is usually
  SAME (no analysis to get wrong) or CANNOT-ASK only if the issue's point is a probability.
- One verdict per issue: the main decision, not every sentence.
