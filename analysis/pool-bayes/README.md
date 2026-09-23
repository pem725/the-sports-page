# Bayesian audit of the CBS confidence-pool project

This directory separates three things that are easy to mix up:

1. observed arithmetic, which is checked exactly;
2. uncertainty about whether crowd popularity predicts correct picks;
3. competition simulations, whose answers depend on explicit behavioral rules.

Start with [`CLAIM-AUDIT.md`](CLAIM-AUDIT.md), then inspect the Stan files in
[`stan/`](stan/). Generated summaries are written to [`results/`](results/).

## Reproduce

Requirements: R, `rstan` 2.32 or later, and `jsonlite`.

```bash
Rscript analysis/pool-bayes/run_models.R .
```

The run uses four chains, 1,000 warmup iterations, 2,000 retained iterations per
chain, and seed `20260923`. It writes CSV summaries, diagnostics, a readable
posterior report, and RDS fit objects containing all posterior draws.

## Change the assumptions

The prior hyperparameters live in the two data lists in `run_models.R`. Useful
challenges include:

- replace `Beta(1,1)` with `Beta(10,10)` to express a stronger fair-coin prior;
- widen the popularity-slope prior from `Normal(0,0.5)` to `Normal(0,1)`;
- remove the week effects, or add team/opponent effects once more weeks exist;
- replace the linear popularity effect with a spline after the sample is large
  enough to estimate one without wishful thinking.

The threshold model and continuous model answer different questions. Agreement
is reassuring; disagreement is diagnostic, not an invitation to choose the
friendlier result.

## Files

- `crowd_group_beta_binomial.stan`: direct comparison of crowd non-favorites and
  favorites, with posterior predictive future records.
- `crowd_popularity_score.stan`: week-hierarchical logistic regression plus
  expected and posterior predictive confidence scores for all three rankings.
- `weekly_competition_simulator.stan`: editable fixed-parameter tournament
  simulator for claims about winning rather than merely scoring.
- `run_models.R`: rebuilds inputs from the canonical JSON, checks the arithmetic,
  fits both inferential models, and writes diagnostics and results.

## Interpretation guardrail

Weeks 1–3 were used to notice and construct the rule. Their posterior is an
exploratory posterior, not prospective validation. Week 4 and later weeks must
be appended without changing the sealed rule if the goal is a clean test.
