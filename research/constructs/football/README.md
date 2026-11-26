# Is yards per carry the same measure in college and the NFL? First pass, 2026-11-26

The editor's question: do the leagues share one measurement model, or does the same
stat measure something different in each? This is a **measurement invariance** test,
the way a psychologist asks whether a questionnaire means the same thing in two
countries.

**Status: preliminary, unpublished.** The model fits respectably; the run factor has only
two indicators, which limits what it can say (see the limits).

## Data

Team-seasons, 2014–2025, offense only, regular season. 1,523 FBS team-seasons
(CFBD `/stats/season`, 12 calls) and 384 NFL team-seasons (nflverse `stats_team`).
Rates per play: yards per carry, rushing TDs per carry, passing yards per attempt,
completion rate, passing TDs per attempt, interceptions per attempt, sack rate.

**The definitional trap.** College counts a sack as a run; the NFL counts it as a pass.
So `ypc` here uses the *college* definition in both leagues (NFL: rushing yards plus
sack yards, over carries plus sacks), and `ypc_nfl` is the NFL's own.

**A data trap we hit:** in CFBD's team stats, `passesIntercepted` is the *defense's*
interceptions; the offense's own are `interceptions`. The first run used the wrong one, and
the giveaway was that college "interceptions" rose with running the ball (+.63). Checked
by arithmetic: turnovers = fumbles lost + interceptions for every team-season but one (2020).

## Findings

**1. Measured the same way, a college carry gains a yard more than an NFL carry.**

| | yards per carry (95% interval) |
|---|---|
| college, as recorded (sacks included) | 4.38 [4.34, 4.42] |
| NFL, as recorded (sacks left out) | 4.27 [4.23, 4.32] |
| NFL, college definition | 3.37 [3.32, 3.43] |

The two published averages look alike. Defined the same way, the gap is 1.0 yard
[0.94, 1.07], and it appears in all 12 seasons (NFL college-style 3.21–3.54; college
4.27–4.53). The NFL's sacks are more frequent, too: 6.5 per 100 dropbacks against 5.4.

**2. The same two constructs show up in both leagues.** Exploratory analysis in each
league separately finds a passing factor and a running factor, with Tucker congruence of
.90 (passing) and .96 (running). A third, "style" factor (how often a team runs) is less
alike (.70).

**3. The ladder: shape holds, loadings hold, intercepts do not.**
Model: passing = yards per attempt, completions, TD rate, interceptions, sacks;
running = yards per carry, rushing TD rate; plus two **bookkeeping** residuals,
set on principle rather than chased: passing and rushing TDs compete for the same
drives, and a pass is either complete or intercepted.

| step | college def of a carry: CFI / RMSEA / SRMR | each league's own def |
|---|---|---|
| configural (same shape) | .947 / .11 / .045 | .941 / .12 / .046 |
| metric (same loadings) | .944 / .11 / .055 | .935 / .11 / .052 |
| scalar (same intercepts) | **.825** / .17 / .118 | **.785** / .19 / .151 |

The loadings match (ΔCFI −.003): a stat *tracks* its construct about as strongly in both
leagues. The intercepts don't: the same underlying strength comes out as different numbers.

**4. Where the scalar break sits.** Largest score tests:
- Completion rate, in both versions. At equal passing strength, college passers complete
  fewer passes (raw: 59.9% vs 63.9%). The stat is on a different scale in each league.
- The running pair (yards per carry, rushing TD rate): score test 50 under the shared
  definition, **188** under each league's own. Using two definitions nearly quadruples
  the running misfit and puts it level with completion rate as the worst break.

So the answer to the editor's question is **no, and partly for a boring reason**: the
leagues don't define a carry the same way. Fix the definition and yards per carry still
doesn't transfer one for one, because college carries gain more.

## Limits

- The running factor has two indicators, so the test can't say *which* of yards per carry
  or rushing TD rate moved; it can only say the pair disagrees. More running indicators
  (runs of 10+ yards, stuffs, first downs per carry) would separate them. nflverse has
  them; CFBD's team-season feed doesn't (play-by-play does, at a quota cost).
- RMSEA stays above .10 even in the configural model: with 7 indicators there are few
  degrees of freedom, and RMSEA punishes that.
- The college ML fit has a near-boundary loading (rushing TD rate .98).
- Team-seasons mix quality with style and with game script (leading teams run).
- Offense only; college includes games against FCS teams.

## Next

- Player level: running backs in both leagues (sacks don't touch an RB's carries, so the
  definitional trap vanishes there; this is the cleaner test of "is a yard a yard").
- More running indicators; defense; within-league year-to-year invariance.

## Files

`0_fetch_teams.sh` → `1_build_teams.py` → `2_explore_leagues.R` → `3_invariance_leagues.R`.
Raw files are gitignored (`data/raw/`).
