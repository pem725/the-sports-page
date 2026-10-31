# Sunday Edition — Next Centerpiece Brief

**Teed up: 2026-10-31 (Sat). For the Sunday Edition built the morning of 2026-11-01.**
Set by the editor: *"put the coin-flip pool thing in Sunday's edition."*

> Planning brief, NOT finished copy. The Sunday Edition is built FRESH Sunday
> morning. Every number below is a Saturday-morning snapshot taken BEFORE week 9
> was played; re-read the pool's overall standings Sunday morning (weeks 1-9) and
> recompute. **The repository is public: no names of pool members, no ranking of
> the family** (see the learn-not-keep-score rule). Aggregates only, plus our own
> entry, which is ours to grade.

## Where it goes

Block 3 of the football-season shape, **the improbability lesson**. It is the
reason the edition exists on a week with little to grade.

## The finding (snapshot through week 8)

- The family confidence pool: 15 college games a week against the spread,
  confidence points 15 down to 1. A perfect week scores **120**.
- **A coin scores 60 on average** (each pick wins half the time; half of 120).
  Its weekly spread is wide: standard deviation **about 18 points**
  (sqrt of 0.25 x (1^2 + ... + 15^2) = sqrt 310). So a coin's ordinary weeks
  run from about 25 to 95.
- **The whole pool, every entry in every week anyone played: 3,667 points over
  61 entries = 60.1 a week.** Exactly a coin. Recompute with week 9.
- Highest and lowest single weeks so far (94 and 17) both sit inside a coin's
  ordinary range.
- Over eight weeks a coin's total has a standard deviation of about 50 points,
  so the leaders' 511 against a coin's 480 is well inside luck.

**The lesson:** a short leaderboard measures attendance and luck before it
measures skill. Against the spread a real forecaster beats 50% by a few points,
worth two or three pool points a week, smaller than one ordinary Saturday swing.

**Honest caveat to print:** entries are not independent (everyone picks the same
games, and the lines are the same), so the 60.1 has a wider range than the
naive 61-entry figure (+/- 4.5) suggests. Say so.

## THE_MISS candidate: our own attendance

The Sports Page's own entry is 9th of 10 on total points (251), and **63 a week
in the four weeks it actually played**, as good as the leaders' rate. It is low
because it **scored zero in weeks 1, 2, 4 and 8**: week 4's picks were sealed
but never entered, week 8 was never built. That is a real miss and a dull one;
say it plainly, in one line. Week 9 was built and sealed (`seal.py --list`,
digest committed 608dfdf) and entered.

## Week 9 to grade

`python3 scripts/seal.py --reveal --week 9` after it unlocks, then grade the
sheet against Saturday's results. Biggest edge: Kansas State -2.5 at Colorado
(15 points). Baylor at UCF was final before the sheet existed and is ungraded.
