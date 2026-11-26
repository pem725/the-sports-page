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

## Running backs (2026-11-26, second pass)

`4_build_rb.py` → `5_rb_same_player.R` → `6_rb_constructs.R` → `7_rb_omega.R` → `8_rb_rank.R` →
`9_rb_judges.R` → `10_rb_today.R`. College: CFBD player season stats (36 calls), backs with 100+
carries. NFL: nflverse season stats plus Next Gen Stats (yards over expected, from 2018), 100+ carries.
Sacks never touch a back's carries, so the definitional trap above is absent here.

**1. The same back gains a yard and a half less in the NFL.** 75 backs with 200+ carries in each
league (linked by ESPN id, with a name-plus-college fallback for CFBD's older ids): college 5.9
yards a carry, NFL 4.4; drop 1.5 [1.3, 1.7]. 74 of 75 dropped. About 0.9 of it is the league (all
college backs 5.3 vs all NFL backs 4.3, which matches the team-level gap counted the NFL way, 0.8);
the rest is selection, since these backs sat at the 79th percentile of college seasons.

**2. College yards per carry barely predicts NFL yards per carry:** r = .21 [.02, .37]. Each extra
college yard buys about 0.1 in the NFL. (Range restriction, since only backs who reached the NFL and
got 200 carries are in, pushes this down; it is a floor.)

**3. Constructs (EFA, 375 RB-seasons 2018–2025).** Scree elbow after 1; parallel analysis 6; MAP 1.
Five interpretable factors: breakaway (yards over expected, 10+ and 20+ yard runs), chain-mover
(first downs, TD rate, EPA), receiving (yards per catch, after the catch), patience (time to the line,
dancing: style, not quality) and role (8-man boxes vs targets). Yards per carry, EPA and yards after
the catch loaded above 1: they are composites of the other indicators, so they were dropped from the
measurement model and kept as criteria. Receiving stats did not cohere as one construct; fumbles load
zero (noise). Final model: breakaway + chain-mover, r = .58; CFI .94, SRMR .04, RMSEA .16 (few df).
Omega hierarchical for the rushing items: .66–.71: about two-thirds of a rushing line is one general
ability.

**4. One season is mostly not the back.** Same back, consecutive seasons (212 pairs): breakaway .26,
chain-mover .18, yards per carry .29, rushing yards .38. A season's rate is mostly line, scheme,
opponents and luck. So a one-season ranking put Blake Corum first in 2025 on 145 carries.

**5. Human judges (AP All-Pro, 2018–2025, 15 backs; Wikipedia, one source).** How well each number
picks the All-Pros (AUC): scrimmage yards .98 [.95, .99], rushing yards .97, yards per carry .90,
breakaway .89, rate score .87 [.81, .93]. The voters reward volume, and carries are themselves a
coach's judgment. But rate adds to volume (p = .005): given the workload, the efficient back gets the vote.

**6. Today's backs, pooled 2024–2026 and shrunk** by Spearman-Brown on a season reliability of .19:
Derrick Henry and Jahmyr Gibbs top the list and are the only 2 of 46 active backs whose 95% interval
clears average. Corum, the one-season leader, is third with an interval running from below average.
The model agrees with the eye only after it admits how little one season says.

## Running backs: the editor's attenuation challenge (2026-11-26, third pass)

`11_rb_history.py`, `12_rb_sustain.R`, `13_rb_schedule.R`, `14_rb_espn_check.py`; plots in `fig/`.
The editor: careers are short, so the correlations are attenuated; plot them (the quartet); look at
established backs. What the data say:

- **Careers are short.** Backs whose first 100-carry season came 1999–2015: median two such seasons;
  36% had exactly one.
- **Reliability rises with carries.** Same back, next season, yards per carry: r = .24 (100+ carries
  both years, n = 741), .29 (200+), .32 (250+), .42 (300+, n = 49). Rushing yards per game: .52.
- **Chance is most of a season.** One NFL run: mean 4.5, median 3, SD 6.3 (137,000 runs, 2016–25).
  At the typical 176 carries, chance alone is about 56% of the spread in a season's yards per carry.
  Half signal needs about 230 carries; 80% needs about 900.
- **A 1,000-yard season (scaled to 16 games) repeats 47% [42, 52] of the time**; a track record does
  not raise it (47% after one, 44% after two, 48% after three); 36% at 29 and older.
- **The link was rebuilt on every carry** (it had used only 100-carry seasons). 92 backs with 200+
  carries in each league: drop 1.5 [1.4, 1.7], 90 of 92 lower, r = .22 [.01, .40]. ESPN as a second
  feed, on the 68 backs it carries in both leagues: drop 1.5, 66 of 68, r = .24. Darrell Henderson,
  both feeds: 8.2 on 431 college carries, 4.2 on 442 NFL carries (4.6 was his 100-carry seasons only).
- **Neither a schedule nor the scouts rescue the college number.** Conference-relative college ypc:
  r = .20. Draft round predicts NFL carries (r = .40), not NFL ypc (r = −.12).

## Defensive linemen: what is a tackle for loss? (2026-11-26)

`15_build_dl.py` → `16_dl_explore.R`. 2018–2025, 300+ snaps, per 100 defensive snaps; 830 edge and
907 interior player-seasons. Play-by-play, snap counts and PFR's charting (pressures, hurries,
knockdowns), all via nflverse.

**Two traps.** (1) Most sacks also carry tackle-for-loss credit (2024: 1,076 of 1,314), so raw TFL
contains sacks; the run-stuff measure counts TFL on non-sack plays only. Officially, 58% of an edge
rusher's TFL and 47% of an interior lineman's are sacks. (2) nflverse's `position` is a player's
current label (Garrett and Hendrickson are now "LB"); PFF's role label (ED edge, DI interior) is used,
with PFR's season label as fallback. PFR "pressures" = hurries + knockdowns + sacks, so only the parts
enter the factor model; batted passes exist only from 2024 and are left out.

**Two constructs, in both groups:** pass rush (hurries, knockdowns, sacks, forced fumbles) and run
defense (tackles on runs, run stuffs, fewer missed tackles). Parallel analysis: 2 interior, 4 edge;
MAP 1. They correlate negatively (−.29 edge, −.38 interior): linemen specialize.

**A run stuff is run defense, not quickness.** Non-sack TFL correlates −.01 to .06 with sacks,
hurries and knockdowns, and loads with run tackles.

**What repeats (same player, next season, 1,078 pairs):** pressures .68, run tackles .60, knockdowns
.48, hurries .46, sacks .43, run stuffs .24, forced fumbles .23. Pressure is the skill; the sack is the
finish, and it depends on the quarterback and the coverage too. The pass-rush construct is far more
the player than a back's yards per carry (.2–.3).

**Not here:** the Sack Exchange era. Sacks became official in 1982 and this data starts in 1999.

## Next

- More running indicators; defense; within-league year-to-year invariance.

## Files

`0_fetch_teams.sh` → `1_build_teams.py` → `2_explore_leagues.R` → `3_invariance_leagues.R`.
Raw files are gitignored (`data/raw/`).
