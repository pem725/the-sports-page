# Hitters and pitchers: constructs, reliability, and the human judges (2026-11-26)

Same treatment as the running backs and defensive linemen in `../football/`. Unpublished.

## Data

- **Box score:** MLB Stats API season hitting and pitching, 2015–2025, reusing `../baseball-hitting/data/raw/`. Hitters need 300+ plate appearances. Starters need half their games started and 100+ innings; relievers need 2 or fewer starts and 40+ innings. The 2020 thresholds are scaled to 60 games.
- **Tracking:** Baseball Savant custom leaderboards (exit velocity, launch angle, chase, zone swing, whiff, sprint speed, fastball velocity, ground-ball rate), merged on MLBAM id. All 3,048 hitter-seasons and 3,369 pitcher-seasons matched.
- **Human judges:** BBWAA MVP and Cy Young ballots, 2015–2025, from bbwaa.com, the voting body's own pages. That is 44 ballots of 30 voters each. All 44 winners match MLB Stats API `/awards`. Vote shares rest on BBWAA alone.
- **Spot checks:** Judge 2024 (58 HR, .322), Witt .332, Arraez .314, Skubal 2.39 ERA with 228 K, Clase 0.61 ERA.

## Hitters

**The measurement model uses primitives only.** AVG, OBP, SLG and OPS are criteria. Barrel and hard-hit rates are composites of exit velocity and launch angle. Intentional walks and sac bunts are the manager's calls.

**Exploring half A (1,484 seasons, split by player id).** Parallel analysis and MAP both say 5. They disagreed (5 vs 2) before Statcast was added. The five constructs:
- swing eagerness: chase, zone swing, fewer walks, fewer pitches seen
- swing-and-miss: strikeouts, whiff, fewer singles
- power: exit velocity, home runs
- lift: launch angle, fly balls
- speed: sprint, steal attempts, triples, fewer double plays

Doubles load zero.

**Confirmation.** As explored, half B gave CFI .77. The revision was made on A only: home runs and singles also load on lift, pitches seen also on swing-and-miss. Tested unchanged on B: CFI .84, SRMR .11. That is below the usual .95. Launch angle still loads 1.1, a Heywood case.

**Omega hierarchical .47.** There is no strong single "good hitter" factor. Power and swing-and-miss correlate .49: that is the old contact–power trade-off, now split into two constructs.

**Same player, next season (1,625 pairs):**

| stat | r |
|---|---|
| sprint | .95 |
| whiff | .88 |
| chase | .84 |
| strikeouts | .83 |
| exit velocity | .77 |
| construct score | .74 |
| home runs | .64 |
| OPS | .49 |
| batting average | .47 |

The process repeats; the outcome much less.

**MVP (top-5 finishers).**
- OPS picks them best: AUC .96 [.95, .97].
- Runs .92, home runs .90, construct score .92.
- The construct adds to OPS plus playing time (p = .0003).

**2025 hitters, pooled 2023–25 and shrunk by Spearman-Brown (season reliability .74).** The top five are Judge, Soto, Betts, Acuña and Ohtani. 71 of 277 hitters clear average and 35 fall below it.

The construct score weights the constructs equally. That is a convenience, not a finding.

## Pitchers (starters and relievers separately)

**Three constructs in both groups:** stuff (strikeouts, whiff, velocity, chase), command (walks, wild pitches, fewer chases) and grounders (ground-ball rate, fewer home runs).

- **Hits on balls in play and exit velocity allowed load on nothing.** That is DIPS: Voros McCracken's finding, recovered without asking for it.
- **CFA on half B:** starters CFI .95, SRMR .09; relievers .94. There are Heywood loadings: whiff 1.35 and strikeouts 1.10 for starters, with a residual between them.
- **Omega hierarchical:** starters .05, relievers .34. Three nearly independent skills, with no general "good pitcher" factor for starters.

**Same pitcher, next season:**

| stat | starters (641 pairs) | relievers (761 pairs) |
|---|---|---|
| velocity | .93 | .95 |
| ground balls | .79 | .78 |
| strikeouts | .75 | .63 |
| walks | .58 | .55 |
| home runs | .27 | .11 |
| hits on balls in play | .23 | .10 |
| ERA | .28 | **.05** |

**Reliever ERA is essentially noise.**

**Cy Young top-5 (starters; 107 of 110 matched).**
- ERA picks them best: AUC .94.
- Strikeouts .88, construct score .86, wins .85, innings .82.
- The construct adds to ERA plus innings (p = .000002).

**2025 starters, pooled 2023–25 and shrunk (season reliability .57).** The top five are Crochet, Gilbert, Skubal, Sánchez and Kirby; Skenes is ninth. Only 14 of 125 clear average and 10 fall below it.

The command-heavy weighting lifts Gilbert and Kirby. A human judge would put Skubal and Skenes higher, and that gap is the disagreement to test.

## Traps

1. **Savant's `min` parameter scales nonlinearly** (min=100 returned only 125 pitchers), so everything is pulled with min=1 and filtered here.
2. **Composites masquerading as measures:** barrel and hard-hit (from exit velocity and launch angle), and OPS. They are kept out of the factor models.
3. **Two-indicator factors and Heywood loadings recur:** lift for hitters, stuff for starters. A third indicator per construct is the fix (bat speed exists from 2024; spin and extension for pitchers).
4. **Pairs touching 2020 are dropped from the reliabilities.**

## Limits

- The same player appears in many seasons, so fit indices are descriptive.
- The construct weights behind the single ranking score are judgment.
- Vote shares come from one source.
- The 2015 Savant sprint and whiff data are less complete than later years, though no missing values survived the merge.

## Figures (`fig/`, crisp SVG via `../hs_scatter.py`)

- `reliability.svg`: every reliability above, with 95% intervals.
- `hit_strikeouts_next.svg`, `hit_avg_next.svg`, `hit_construct_next.svg`
- `sp_strikeouts_next.svg`, `sp_era_next.svg`, `sp_hbip_next.svg`, `rp_era_next.svg`

## Files

- `0_votes.py`: BBWAA ballots.
- `1_build.py`: merge.
- `2_hit_explore.R`, `3_hit_confirm.R`, `3b_hit_revise.R`, `4_hit_validate.R`: hitters.
- `5_pitch.R`, `6_pitch_validate.R`: pitchers.
- `7_figures.py`, `8_reliability_chart.py`: figures.

Raw downloads are in `raw/` (gitignored).
