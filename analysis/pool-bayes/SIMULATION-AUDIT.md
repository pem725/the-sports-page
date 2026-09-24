# Weekly competition simulation audit

The published pool draft reports weekly win rates of 22.2%, 19.4%, and 14.7%
for contrarian-heavy, random, and consensus-heavy confidence ordering. The later
methods note states these assumptions:

- 15 independent games with true win probability 0.5;
- one focal player and nine opponents;
- the focal player differs from the crowd on 8 of 15 games;
- each opponent takes the crowd side independently with probability 0.75;
- each opponent ranks confidence at random;
- a tie for first counts as a loss.

`run_weekly_simulator.R` encodes those assumptions in
`stan/weekly_competition_documented.stan` and uses common random outcomes and
opponents for all three focal-player strategies. Four fixed-parameter chains of
30,000 draws each (seed 20260923) produced:

| strategy | mean score | P(win) | mean score minus best opponent |
|---|---:|---:|---:|
| contrarian-heavy | 60.04 | 16.33% | -23.36 |
| random | 60.06 | 13.74% | -23.34 |
| consensus-heavy | 60.12 | 10.54% | -23.29 |

Monte Carlo standard errors for the three win probabilities are about 0.11,
0.10, and 0.09 percentage points. Simulation noise cannot explain the gap from
the published 22.2%, 19.4%, and 14.7%.

The qualitative claim survives: contrarian-heavy ranking raises tournament win
probability without raising expected score. The reported absolute percentages
do not survive the assumptions now printed in the article. Reproducing them
requires another rule—most plausibly dependence among opponents, a different
tie convention, fewer effective opponents, or non-random opponent weights.
Until that rule is recovered, the defensible quantities are the direction and
the paired contrasts, not the old percentages.

## Additional deterministic audit

Issue 163 says the non-favorites-first gain “came from four games” and that
Northwestern alone was worth ten points. Northwestern's +10 is confirmed. The
four-game attribution is not identified by the stored scoring decomposition:
21 correct picks changed weight, with seven positive and fourteen negative
contributions netting to +11. A four-game account may be possible under a
specific swap decomposition, but that decomposition was not archived.
