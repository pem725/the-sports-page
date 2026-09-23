# Bayesian audit results

Generated 2026-09-23 18:26 EDT with seed 20260923; 4 chains, 2000 post-warmup draws per chain.

## Bottom line

The observed sample is 7/12 correct on crowd non-favorites and 21/33 on crowd favorites. Under independent Beta(1,1) priors, the posterior probability that the non-favorite rate is higher is **36.9%**.
The posterior risk difference (non-favorite minus favorite) is **-0.053 [-0.352, 0.234]**.
In the continuous model, the log-odds slope per 10 percentage points of CBS support is **0.032 [-0.316, 0.385]**.

These results do not confirm a durable contrarian accuracy edge. They quantify substantial uncertainty around a small, post-hoc, three-week sample.

## Score implications under the fitted popularity model

Posterior expected score, actual weights: **221.2 [170.7, 267.7]**.
Posterior expected score, non-favorites first: **219.7 [167.3, 266.8]**.
Posterior expected score, least popular first: **218.8 [164.2, 268.6]**.
P(expected non-favorites-first score > actual order): **43.1%**.
P(expected least-popular-first score > actual order): **43.1%**.
Posterior predictive P(non-favorites-first realized score > actual order): **44.8%**.
Posterior predictive P(least-popular-first realized score > actual order): **44.9%**.

The expected-score comparisons are in-sample and exploratory. The replicated-score comparisons use the same simulated game outcomes for all three rankings, preserving the paired design.

## Sampling diagnostics

                         model max_rhat min_bulk_ess divergences
           group_beta_binomial 1.000364     3108.584           0
 hierarchical_popularity_score 1.000773     2861.541           0
 max_treedepth_hits
                  0
                  0

See `CLAIM-AUDIT.md` for the deterministic checks and the claims that cannot be identified from the stored data.
