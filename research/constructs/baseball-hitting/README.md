# What do hitting stats measure? First pass, 2026-11-13

The editor's question: baseball has dozens of hitting stats. Do they measure a few
underlying things (constructs), the way a psychological test's items do? This is the first
sport in an empirical glossary, built in the tradition of Cattell, then tested with
Jöreskog and Sörbom's confirmatory models.

**Status: preliminary. Nothing here is published, and the model does not fit well yet.**

## The test design

Exploring and confirming on the same data proves nothing, so three samples are used:

| sample | who | n | job |
|---|---|---|---|
| A | half of 2021–25 hitters (split by a hash of player id) | 278 | explore |
| B | the other half | 250 | confirm the explored model |
| C | 2016–19 hitters who do **not** appear in 2021–25 | 239 | final test, after any revision made on B |

Unit: one player, with every season of 300+ plate appearances pooled. Only primitives go
in: singles, doubles, triples, home runs, unintentional and intentional walks, hit by
pitch, strikeouts, sac bunts and flies (each per PA, square-rooted), steal attempts per
time on base, double plays, pitches seen per PA, and ground-to-air outs (logged). AVG,
OBP, SLG, OPS and BABIP are left out because they are sums of these. Runs and RBI are held
out of the model and treated as *outcomes* afterward.

## What we found

**1. How much of each stat is the player?** Correlation between one season and the next,
same player, 800 pairs:

| stat | year to year | | stat | year to year |
|---|---|---|---|---|
| strikeouts | .82 | | hit by pitch | .58 |
| steal attempts | .81 | | intentional walks | .45 |
| pitches seen | .77 | | double plays | .44 |
| ground/air | .71 | | triples | .43 |
| walks | .69 | | runs, RBI | .43, .42 |
| bunts | .65 | | **doubles** | **.22** |
| singles | .63 | | **sac flies** | **.10** |
| home runs | .62 | | | |

Strikeouts are very much the hitter. Doubles and sac flies are mostly the season around him.

**2. How many constructs?** Parallel analysis said 5 and Velicer's MAP said 2. They
disagree, and we say so. The five that came out of sample A:

- **Patience**: walks, pitches seen per trip
- **Contact**: singles up, strikeouts down
- **Speed**: steal attempts, triples, bunts, *fewer* double plays
- **Power**: home runs, intentional walks, *fewer* bunts
- **Launch**: ground balls versus fly balls

**3. Did it hold?** Only partly.

| model | sample B (CFI / RMSEA) | sample C (CFI / RMSEA) |
|---|---|---|
| one general "hitting" factor | .50 / .20 | — |
| three factors | .56 / .20 | — |
| four factors, revised on B (no launch factor) | .85 / .15 | **.91 / .12** |
| five factors, revised on B | .81 / .16 | .85 / .14 |

A single "good hitter" factor fails badly. Four factors beat it by a lot. But even the best
model, on the fresh sample, misses the usual bar (CFI ≥ .95, RMSEA ≤ .06). Some
two-indicator factors also produce Heywood cases (standardized loadings above 1).

**4. The strongest pattern is a trade-off.** Contact and power correlate −.83 on sample C.
Hitters choose a side: swing hard, hit home runs and strike out, or put the ball in play.
That may be one bipolar dimension and not two factors. Speed is the cleanest construct and
replicates in every sample.

**5. RBI looks like the hitter; runs look more like his teammates.** On sample C the five
constructs explain about 69% of the spread in RBI per trip, but only about 41% of the
spread in runs. A run needs the hitters behind you. (The individual coefficients are not
interpretable: the factor scores are too correlated.)

## What would make this better (the next tests)

- Pitch-level data (Statcast: exit velocity, swing rate, chase rate) gives each construct
  three or more indicators instead of two. Most of the misfit is two-indicator factors.
- Measurement invariance across eras (2016–19 against 2021–25) and across positions.
- A bifactor model: a general hitting factor plus specific ones.
- A Bayesian CFA (blavaan isn't installed yet) with small-variance priors on cross-loadings, in
  place of the all-or-nothing zeros used here.
- Then pitching, then football, then basketball: the same design, sport by sport.

## Files

`0_build_data.py` (MLB Stats API, no key) → `1_explore.R` → `2_confirm.R` →
`3_fresh_sample.R`. `4_your_model.R` is the editor's hypothesis, to be tested the same way.
