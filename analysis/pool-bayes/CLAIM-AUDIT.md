# Confidence-pool claim audit

Scope: the Weeks 1–3 crowd-ordering backtest, Issue 163, the Week 4 method note,
and the draft Issue 164. This is not an audit of every sports statistic in the
newsletter archive.

## Claim map

| Claim | Kind | Reproducible result | Appropriate method |
|---|---|---:|---|
| 28 of 45 picks were correct | observed arithmetic | confirmed | assertion in `run_models.R` |
| Actual confidence score was 202 | observed arithmetic | confirmed | assertion in `run_models.R` |
| Non-favorites-first scored 213 | observed counterfactual arithmetic | confirmed | deterministic re-ranking |
| Least-popular-first scored 219 | observed counterfactual arithmetic | confirmed | deterministic re-ranking |
| Random ordering has conditional mean 224 | exact finite-population result | confirmed: 28 × mean(1:15) | exact combinatorics in `scripts/pool_crowd_backtest.py` |
| Non-favorites went 7/12; favorites 21/33 | observed arithmetic | confirmed | assertion plus group model |
| Non-favorites are better future picks | population/generalization claim | not supported by Weeks 1–3 | Beta-binomial posterior and hierarchical logistic model |
| Lower CBS popularity predicts more correct picks | population/generalization claim | estimated with large uncertainty | hierarchical logistic model |
| Crowd-aware weights improve expected score | model-dependent decision claim | estimated, not established | posterior expected scores under common fitted probabilities |
| Crowd-aware weights can improve realized score | predictive claim | estimated, highly variable | paired posterior predictive scores |
| Ordering adds exactly zero expected points | theorem only under equal game probabilities, or weights independent of probabilities | confirmed under that null; not universally true | algebra, not MCMC |
| 92 versus 36 for eight correct picks | arithmetic boundary | confirmed: sum(8:15)=92; sum(1:8)=36 | exact arithmetic |
| Contrarian weighting raises weekly win probability to 22% | simulation claim | not independently reproducible from stored inputs | parameterized Stan simulator supplied; original opponent-pick and opponent-weight rules were not stored |
| “Copy exactly” turns a 12-point lead into a 3.8% chance | deterministic/model claim | contradicted if “exactly” means identical future picks and weights | identical future scores preserve a 12-point lead with probability 1 |
| A weekly score has SD about 18 | null-model claim | depends on game dependence and pick probabilities | under 15 independent fair games and weights 1:15, SD = sqrt(sum(w²)/4) = 17.61 |
| Ten-week pairwise gap SD is about 78 | null-model claim | approximately plausible only with positive player-score correlation | independent players give sqrt(2 × 10) × 17.61 = 78.76 |
| Walk-forward YPP coefficient 5.1, r=.47, residual SD 18.9, N=1,441 | empirical model claim | not reproducible from committed data | requires the exact historical game-level design matrix and inclusion rules |
| YPP side went 50.2% ATS over 2,278 games; r=.73 with spread | empirical backtest claim | not reproducible from committed data | requires the exact historical game-level design matrix, closing-line selection, and push rules |

## Why two Bayesian accuracy models?

The group model directly asks the headline question: are picks below 50% CBS
support more likely to be right than picks at or above 50%? It is transparent,
but throws away information by cutting 49% and 50% into different bins.

The hierarchical logistic model retains the full CBS percentage and gives each
week a partially pooled intercept. Its slope is the change in log odds of a
correct pick for each ten-point increase in CBS support. With only three weeks,
the week variance is weakly identified; that is precisely why it is regularized.

## Priors

The default group priors are independent `Beta(1,1)`. The logistic intercept is
`Normal(0,1)`. The popularity slope is `Normal(0,0.5)` per ten percentage
points; that puts 95% prior mass on odds ratios of roughly 0.38 to 2.66 for a
ten-point change. The week SD has a half-`Normal(0,0.5)` prior.

Every prior hyperparameter is passed through the Stan `data` block. Change the
values in `run_models.R` and rerun; no Stan edit is required.

## What the competition simulator does—and does not do

`weekly_competition_simulator.stan` is a generated-quantities simulator. It
takes game-level true probabilities, crowd pick probabilities, the user’s pick,
each user weighting rule, and each opponent’s weights. It returns user scores,
opponent scores, margins over the best opponent, and tie-split win credit.

It deliberately does not hide a crowd model inside the Stan file. The missing
assumptions behind the published 22% and 15% figures are substantive, not
computational: how opponent picks co-move, how opponents rank confidence, and
how ties count. Those must be stated before the numbers can be “confirmed.”

## What must be archived next

The YPP claims need a frozen row-per-game file containing season, week, teams,
pregame YPP margins, final margin, selected closing spread, push status, and all
exclusion flags. An API-fetching script alone is not enough: upstream data and
lines can change. Once that file exists, a robust Stan regression and Bayesian
ATS calibration model can be fitted without ambiguity.
